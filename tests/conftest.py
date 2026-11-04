"""Offline fixtures implement Astra atomic operations, not external API calls."""

import asyncio
import copy
from types import SimpleNamespace

import pytest
from astrapy.exceptions import DataAPIErrorDescriptor, DataAPIResponseException

from config.settings import Settings
from database.astra_db import AstraMemory


class Collection:
    def __init__(self):
        self.documents = {}

    async def find_one(self, query):
        await asyncio.sleep(0)
        return copy.deepcopy(self.documents.get(query["_id"]))

    async def insert_one(self, document):
        await asyncio.sleep(0)
        if document["_id"] in self.documents:
            raise DataAPIResponseException(
                "duplicate",
                command={},
                raw_response={},
                error_descriptors=[
                    DataAPIErrorDescriptor(
                        {"errorCode": "DOCUMENT_ALREADY_EXISTS", "message": "duplicate"}
                    )
                ],
                warning_descriptors=[],
            )
        self.documents[document["_id"]] = copy.deepcopy(document)

    async def replace_one(self, query, document):
        await asyncio.sleep(0)
        old = self.documents.get(query["_id"])
        matched = old is not None and old["revision"] == query["revision"]
        if matched:
            self.documents[query["_id"]] = copy.deepcopy(document)
        return SimpleNamespace(matched_count=int(matched))

    async def delete_one(self, query):
        self.documents.pop(query["_id"], None)


@pytest.fixture
def settings(tmp_path):
    profiles = tmp_path / "profiles.json"
    profiles.write_text("[]")
    return Settings(
        _env_file=None,
        astra_db_api_endpoint="https://example.apps.astra.datastax.com",
        astra_db_application_token="test-token",
        session_hash_key="a" * 32,
        openai_api_key="test-openai",
        meta_access_token="test-meta",
        meta_verify_token="test-verify",
        meta_app_secret="test-secret",
        meta_phone_number_id="123456",
        meta_api_version="v23.0",
        rapidapi_key="test-rapid",
        google_places_api_key="test-places",
        google_routes_api_key="test-routes",
        amadeus_client_id="test-id",
        amadeus_client_secret="test-amadeus",
        booking_profiles_path=str(profiles),
        inbox_path=str(tmp_path / "inbox.sqlite3"),
    )


@pytest.fixture
def memory(settings):
    service = AstraMemory(settings)
    service._collection = Collection()
    return service
