"""Cross-version compatibility layer for Pydantic v1/v2 and optional SDKs (astrapy, openai, playwright)."""

import json
from typing import Any
from urllib.parse import urlsplit

import pydantic

PYDANTIC_V2 = getattr(pydantic, "__version__", "1.").startswith("2.")

if PYDANTIC_V2:
    from pydantic import (
        BaseModel,
        ConfigDict,
        Field,
        HttpUrl,
        JsonValue,
        SecretStr,
        ValidationError,
        field_validator,
        model_validator,
    )
    from pydantic_settings import BaseSettings, SettingsConfigDict
else:
    from pydantic import (
        BaseModel as _BaseModel,
        BaseSettings as _BaseSettings,
         Extra,
        Field as _Field,
        HttpUrl,
        SecretStr,
        ValidationError,
        root_validator,
        validator,
    )

    JsonValue = Any

    def Field(*args: Any, **kwargs: Any) -> Any:
        if "pattern" in kwargs:
            kwargs["regex"] = kwargs.pop("pattern")
        if kwargs.get("default_factory") is list or "items" in str(kwargs):
            if "min_length" in kwargs:
                kwargs["min_items"] = kwargs.pop("min_length")
            if "max_length" in kwargs:
                kwargs["max_items"] = kwargs.pop("max_length")
        kwargs.pop("allow_inf_nan", None)
        return _Field(*args, **kwargs)

    def ConfigDict(**kwargs: Any) -> dict[str, Any]:
        return kwargs

    def SettingsConfigDict(**kwargs: Any) -> dict[str, Any]:
        return kwargs

    def field_validator(*fields: str, **kwargs: Any):
        mode = kwargs.get("mode", "after")
        return validator(*fields, pre=(mode == "before"), allow_reuse=True)

    def model_validator(*, mode: str = "after"):
        def decorator(fn):
            raw_fn = fn.__func__ if isinstance(fn, classmethod) else fn
            if mode == "before":
                @root_validator(pre=True, allow_reuse=True)
                def _pre(cls, values):
                    return raw_fn(cls, values)
                return _pre
            else:
                @root_validator(pre=False, allow_reuse=True)
                def _post(cls, values):
                    instance = cls.construct(**values)
                    res = fn(instance)
                    if isinstance(res, _BaseModel):
                        return res.__dict__
                    return values
                return _post
        return decorator

    class BaseModel(_BaseModel):
        class Config:
            extra = Extra.forbid

        def model_dump(self, **kwargs: Any) -> dict[str, Any]:
            exclude_none = kwargs.get("exclude_none", False)
            return json.loads(self.json(exclude_none=exclude_none))

        def model_dump_json(self, **kwargs: Any) -> str:
            return self.json()

        def model_copy(self, *, update: dict[str, Any] | None = None) -> Any:
            return self.copy(update=update)

        @classmethod
        def model_validate(cls, obj: Any) -> Any:
            if isinstance(obj, cls):
                return obj
            return cls.parse_obj(obj)

        @classmethod
        def model_validate_json(cls, data: str | bytes) -> Any:
            return cls.parse_raw(data)

        @classmethod
        def model_json_schema(cls) -> dict[str, Any]:
            schema = cls.schema()
            schema["additionalProperties"] = False
            return schema

    class BaseSettings(_BaseSettings):
        class Config:
            env_file = ".env"
            env_file_encoding = "utf-8"
            case_sensitive = False
            extra = Extra.ignore

        def model_dump(self, **kwargs: Any) -> dict[str, Any]:
            return self.dict()
