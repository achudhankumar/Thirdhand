"""Regression coverage for audited simulator and startup vulnerabilities."""

from unittest.mock import AsyncMock, patch

import httpx
import pytest
from fastapi import FastAPI
from pydantic import SecretStr, ValidationError

from config.settings import Settings, get_settings
from routers.simulator import initialize_simulator, router


def development(settings, tmp_path):
    return settings.model_copy(
        update={
            "environment": "development",
            "enable_simulator": True,
            "simulator_token": SecretStr("s" * 40),
            "simulator_path": str(tmp_path / "simulator.json"),
        }
    )


@pytest.mark.parametrize("path", ["/", "/simulator", "/api/simulate"])
async def test_production_simulator_inaccessible(settings, path):
    app = FastAPI()
    app.state.settings = settings
    app.include_router(router)
    app.state.simulator_orchestrator = AsyncMock()
    async with httpx.AsyncClient(
        transport=httpx.ASGITransport(app=app), base_url="http://127.0.0.1"
    ) as client:
        response = await (
            client.post(path, json={"text": "reset"})
            if path == "/api/simulate"
            else client.get(path)
        )
    assert response.status_code == 404
    app.state.simulator_orchestrator.handle_interactive_turn.assert_not_awaited()


async def test_simulator_boundary_and_no_caller_identity(settings, tmp_path):
    app = FastAPI()
    app.state.settings = development(settings, tmp_path)
    app.include_router(router)
    service = AsyncMock()
    service.handle_interactive_turn.return_value = {"reply": "local reply"}
    app.state.simulator_orchestrator = service
    auth = {"Authorization": "Bearer " + "s" * 40}
    async with httpx.AsyncClient(
        transport=httpx.ASGITransport(app=app), base_url="http://127.0.0.1"
    ) as client:
        assert (
            await client.post("/api/simulate", json={"text": "reset"})
        ).status_code == 403
        assert (
            await client.post(
                "/api/simulate",
                json={"from": "919876543210", "text": "reset"},
                headers=auth,
            )
        ).status_code == 400
        assert (
            await client.post(
                "/api/simulate",
                json={"text": "reset"},
                headers=auth | {"Origin": "https://evil.invalid"},
            )
        ).status_code == 403
        assert (
            await client.post("/api/simulate", json={"text": "x" * 8001}, headers=auth)
        ).status_code == 400
        assert (
            await client.post("/api/simulate", json={"text": "hello"}, headers=auth)
        ).status_code == 200
        first = service.handle_interactive_turn.call_args.args[0]
        assert first.startswith("sim:")
        await client.post("/api/simulate", json={"text": "reset"}, headers=auth)
        assert service.handle_interactive_turn.call_args.args[0] == first
        assert (
            await client.get("/simulator", headers={"Host": "evil.invalid"})
        ).status_code == 404
    async with httpx.AsyncClient(
        transport=httpx.ASGITransport(app=app, client=("192.0.2.1", 1234)),
        base_url="http://127.0.0.1",
    ) as remote:
        assert (
            await remote.post("/api/simulate", json={"text": "reset"}, headers=auth)
        ).status_code == 404
    async with httpx.AsyncClient(
        transport=httpx.ASGITransport(app=app), base_url="http://127.0.0.1"
    ) as other:
        await other.post("/api/simulate", json={"text": "hi"}, headers=auth)
        assert service.handle_interactive_turn.call_args.args[0] != first


async def test_simulator_has_separate_real_storage_and_no_checkout(
    settings, tmp_path, memory
):
    config = development(settings, tmp_path)
    async with httpx.AsyncClient() as http:
        simulator = await initialize_simulator(config, http)
        await memory.update_profile("919876543210", {"private": "production"})
        assert (await simulator.memory.get_session("919876543210")).profile == {}
        await simulator.memory.append_message("sim:test", "user", "local")
        assert (await memory.get_session("sim:test")).history == []
        from services.http import UpstreamError

        with pytest.raises(UpstreamError, match="disabled"):
            await simulator.booking.handle("sim:test", "checkout", "movie", {}, True)
        await simulator.client.close()


@pytest.mark.parametrize(
    "change",
    [
        {"demo_fallback": True},
        {"use_local_memory_fallback": True},
        {"enable_simulator": True},
        {
            "session_hash_key": "thirdhand_default_session_secret_key_change_in_prod_2026"
        },
    ],
)
def test_production_rejects_demo_and_published_defaults(settings, change):
    with pytest.raises(ValidationError):
        Settings(**{**settings.model_dump(), **change}, _env_file=None)


def test_invalid_environment_never_creates_demo_defaults(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    with patch.dict("os.environ", {}, clear=True):
        get_settings.cache_clear()
        with pytest.raises(ValidationError):
            get_settings()
    get_settings.cache_clear()


@pytest.mark.parametrize(
    "field,value",
    [
        ("meta_app_secret", "demo-app-secret"),
        ("meta_verify_token", "thirdhand_verify_2026"),
        ("meta_access_token", "demo-whatsapp-token"),
        ("meta_api_version", ""),
    ],
)
def test_runtime_rejects_missing_or_published_credentials(settings, field, value):
    setattr(settings, field, SecretStr(value) if field != "meta_api_version" else value)
    with pytest.raises(ValueError):
        settings.validate_startup()


def test_local_launcher_creates_private_explicit_config_without_printing_secrets(
    tmp_path, monkeypatch, capsys
):
    from unittest.mock import Mock

    from dotenv import dotenv_values

    import run_thirdhand

    monkeypatch.setattr(run_thirdhand, "ROOT", tmp_path)
    monkeypatch.chdir(tmp_path)
    monkeypatch.setenv("THIRDHAND_ENV_FILE", str(tmp_path / ".env.development"))
    command = Mock()
    monkeypatch.setattr(run_thirdhand.subprocess, "run", command)
    with patch.dict(
        "os.environ",
        {"PATH": "", "THIRDHAND_ENV_FILE": str(tmp_path / ".env.development")},
        clear=True,
    ):
        get_settings.cache_clear()
        run_thirdhand.main(["--local"])
        first = (tmp_path / ".env.development").read_bytes()
        run_thirdhand.main(["--local"])
        assert (tmp_path / ".env.development").read_bytes() == first
    get_settings.cache_clear()
    values = dotenv_values(tmp_path / ".env.development")
    assert (
        values["ENVIRONMENT"] == "development"
        and values["USE_LOCAL_MEMORY_FALLBACK"] == "true"
    )
    assert (
        len(values["SESSION_HASH_KEY"]) >= 32 and len(values["SIMULATOR_TOKEN"]) >= 32
    )
    output = capsys.readouterr().out
    assert (
        values["SIMULATOR_TOKEN"] not in output
        and values["SESSION_HASH_KEY"] not in output
    )
    args = command.call_args.args[0]
    assert args[args.index("--host") + 1] == "127.0.0.1"
