"""Poe Server Bot adapter: Poe handles chat UI, model routing and chat history.

No OpenAI API client, database, or outside memory service is required here.
"""

from __future__ import annotations

import os
import logging
from typing import AsyncIterable

import fastapi_poe as fp

from .prompt import ASTRA_SYSTEM_PROMPT

log = logging.getLogger(__name__)
DEFAULT_MODEL = "GPT-5.4"  # Name shown in the official Poe Server Bot functional guide.


def model_name() -> str:
    return os.environ.get("POE_MODEL", DEFAULT_MODEL).strip() or DEFAULT_MODEL


def forward_request(request: fp.QueryRequest) -> fp.QueryRequest:
    """Preserve all Poe-provided messages and attachments verbatim.

    Only prepend the Astra principles. No app-side summary, inferred objective,
    or implicit new user requirements are added to the conversation.
    """
    system_message = fp.ProtocolMessage(role="system", content=ASTRA_SYSTEM_PROMPT)
    return request.model_copy(update={"query": [system_message, *request.query]})


class PoeAstraBot(fp.PoeBot):
    def __init__(self, *, model: str | None = None) -> None:
        super().__init__()
        self.model = model or model_name()

    async def get_settings(self, setting: fp.SettingsRequest) -> fp.SettingsResponse:
        return fp.SettingsResponse(
            server_bot_dependencies={self.model: 1},
            allow_attachments=True,
            expand_text_attachments=True,
            enable_image_comprehension=True,
            introduction_message=(
                "ASTRA FIELDのPoe実験版です。自然な会話・探索・判断の継続を試します。"
                "この会話でPoeが渡す履歴を利用しますが、別会話をまたぐ独自の長期記憶はありません。"
            ),
        )

    async def get_response(self, request: fp.QueryRequest) -> AsyncIterable[fp.PartialResponse]:
        if not request.query:
            yield fp.ErrorResponse(text="会話内容が届いていません。", allow_retry=True)
            return
        if not request.access_key or request.access_key == "<missing>":
            yield fp.ErrorResponse(text="Poeの認証情報を確認できませんでした。", allow_retry=True)
            return

        try:
            # Supplying the request's Poe access key (not a personal Poe API key)
            # charges the requesting user's Poe points for this model call.
            async for event in fp.stream_request(
                forward_request(request), self.model, request.access_key
            ):
                yield event
        except Exception as exc:
            # Avoid logging the request, credentials, or private conversation text.
            log.error("Poe model request failed (type=%s)", type(exc).__name__)
            yield fp.ErrorResponse(
                text="モデルへの接続に失敗しました。再試行してください。",
                allow_retry=True,
            )


def create_app():
    """Create an authenticated ASGI app. Never silently run an open endpoint."""
    key = os.getenv("POE_ACCESS_KEY", "").strip()
    name = os.getenv("POE_BOT_NAME", "").strip()
    if not key or not name:
        raise RuntimeError("POE_ACCESS_KEY and POE_BOT_NAME are required")
    return fp.make_app(PoeAstraBot(), access_key=key, bot_name=name)
