"""Dependency-free contract tests. They do not call the live Poe service."""

from __future__ import annotations

import asyncio
import importlib
import os
import sys
import types
import unittest
from dataclasses import dataclass, field
from unittest.mock import patch


@dataclass
class FakeMessage:
    role: str
    content: str
    attachments: list = field(default_factory=list)


@dataclass
class FakeRequest:
    query: list
    access_key: str = "user-poe-key"

    def model_copy(self, *, update):
        return FakeRequest(query=update["query"], access_key=self.access_key)


class FakePoeBot:
    pass


class FakeResponse:
    def __init__(self, **kwargs):
        self.__dict__.update(kwargs)


class BotTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        fake = types.ModuleType("fastapi_poe")
        fake.PoeBot = FakePoeBot
        fake.QueryRequest = FakeRequest
        fake.ProtocolMessage = FakeMessage
        fake.SettingsRequest = object
        fake.SettingsResponse = FakeResponse
        fake.PartialResponse = FakeResponse
        fake.ErrorResponse = FakeResponse
        fake.make_app = lambda *a, **kw: (a, kw)
        cls.old = sys.modules.get("fastapi_poe")
        sys.modules["fastapi_poe"] = fake
        cls.fake = fake
        cls.bot = importlib.import_module("poe_astra.bot")

    @classmethod
    def tearDownClass(cls):
        sys.modules.pop("poe_astra.bot", None)
        if cls.old is None:
            sys.modules.pop("fastapi_poe", None)
        else:
            sys.modules["fastapi_poe"] = cls.old

    def test_forwards_verbatim_history_and_attachments(self):
        attachment = object()
        original = [FakeMessage("user", "最初の目的", [attachment]), FakeMessage("bot", "前の回答"), FakeMessage("user", "勝手に条件を追加しない")]
        request = FakeRequest(query=original)
        forwarded = self.bot.forward_request(request)
        self.assertEqual(forwarded.query[0].role, "system")
        self.assertEqual(forwarded.query[1:], original)
        self.assertIs(forwarded.query[1].attachments[0], attachment)
        self.assertEqual(request.query, original)
        self.assertEqual(len(request.query), 3)

    def test_settings_declare_one_poe_dependency(self):
        obj = self.bot.PoeAstraBot(model="GPT-5.4")
        settings = asyncio.run(obj.get_settings(None))
        self.assertEqual(settings.server_bot_dependencies, {"GPT-5.4": 1})
        self.assertTrue(settings.allow_attachments)

    def test_user_poe_key_is_used_for_inference(self):
        captured = []
        async def stream(request, model, key):
            captured.append((request, model, key))
            yield FakeResponse(text="返答")
        self.fake.stream_request = stream
        request = FakeRequest(query=[FakeMessage("user", "こんにちは")], access_key="payer-key")
        async def collect():
            return [msg async for msg in self.bot.PoeAstraBot().get_response(request)]
        output = asyncio.run(collect())
        self.assertEqual([msg.text for msg in output], ["返答"])
        self.assertEqual(captured[0][2], "payer-key")
        self.assertEqual(captured[0][0].query[1].content, "こんにちは")

    def test_empty_query_returns_retryable_error(self):
        async def collect():
            return [msg async for msg in self.bot.PoeAstraBot().get_response(FakeRequest(query=[]))]
        results = asyncio.run(collect())
        self.assertTrue(results[0].allow_retry)

    def test_unconfigured_app_refuses_public_endpoint(self):
        with patch.dict(os.environ, {}, clear=True):
            with self.assertRaises(RuntimeError):
                self.bot.create_app()

    def test_authenticated_app_uses_only_environment_credentials(self):
        with patch.dict(os.environ, {"POE_ACCESS_KEY": "server-key", "POE_BOT_NAME": "PoeAstra"}):
            _, kwargs = self.bot.create_app()
        self.assertEqual(kwargs, {"access_key": "server-key", "bot_name": "PoeAstra"})

    def test_missing_request_key_does_not_invoke_model(self):
        async def fail(*args):
            raise AssertionError("should not be called")
            yield None
        self.fake.stream_request = fail
        async def collect():
            return [msg async for msg in self.bot.PoeAstraBot().get_response(FakeRequest(query=[FakeMessage("user", "a")], access_key=""))]
        results = asyncio.run(collect())
        self.assertTrue(results[0].allow_retry)


if __name__ == "__main__":
    unittest.main()
