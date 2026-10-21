# Poe Astra — Poe専用 Astra Field（実験版）

**目的:** 既存 GitHub版 Astra Field の会話思想を、Poe Server Botへ独立して移設する。元のAstraとFloot版は変更しない。

これは **Poe接続アダプター＋会話方針の初期移設** であり、既存Web版との完全な機能互換はまだない。

## 実装内容

- Poeの画面・会話履歴・モデルを利用。モデル呼び出しには Poe Server Bot のリクエストに付属するキーを利用し、利用者のPoeポイントで推論する。
- 外部のOpenAI APIキーや専用の会話DBは不要。
- Astraの判断原則（目的を勝手に変更しない、事実と推論を分ける、訂正を継承する、8層の思考視点）を移設。
- 会話の原文と添付を変形・要約せずPoeモデルへ転送。ストリーミングで返答。
- 登録したPoeのAccess KeyとBot Nameを環境変数で検証し、未設定なら外部公開しない。

## 既存Web版との差

| 項目 | Poe Astra v0.1 |
| --- | --- |
| 会話画面 | Poe側 |
| 会話履歴 | Poeがリクエストで渡す範囲 |
| AI推論 | Poe内モデル（既定 `GPT-5.4`） |
| 長期記憶（チャット横断） | **未実装**。Poe履歴だけでは保証できない |
| CJM / SHIFT / RETURN / 8層 | 思考原則として移設。機械的な保証は未実装 |
| Machine Astra / MCP Probe | 未移植（別システムを同一視しない） |
| Web検索 | 専用検索機能なし。選択したPoeモデルの機能に依存 |
| ファイル添付 | Poe側からの受け渡しを有効化。実物での検証が必要 |
| 独自データベース | なし |

## 公開手順

Poe公式: https://creator.poe.com/docs/server-bots/quick-start

1. Poeの [Server Bot作成画面](https://poe.com/create_bot?server=1) で **Bot Name** と **Access Key** を確認。
2. Modalなど、PoeからアクセスできるHTTPSサーバーに本ボットを配置する。Server Botには外部実行環境が必要。
3. 表示された公開URLをPoeの **Server URL** へ登録する。
4. Poe側のモデル依存設定を確認し、実際の会話で動作を試す。

### Modalで配置する例

```bash
python -m pip install modal
modal token new --source poe
modal secret create poe-astra POE_ACCESS_KEY="<PoeのAccess Key>" POE_BOT_NAME="<PoeのBot Name>" POE_MODEL=GPT-5.4
modal deploy modal_deploy.py
```

Access KeyはGitHubに記録しない。Modalの料金や無料枠は別途確認する。

### ASGIホストで起動

```bash
python -m pip install -r requirements.txt uvicorn
# POE_ACCESS_KEY / POE_BOT_NAME を安全な環境変数に設定してから
uvicorn main:app --host 0.0.0.0 --port 8080
```

### ローカル検証

```bash
python -m unittest discover -s tests -v
python -m compileall -q poe_astra main.py modal_deploy.py
```

テストは外部サービスを呼ばない契約テスト。Poe実機での認証、モデル応答、ポイント消費、添付、長期会話については**未検証**。

## 参照した原本

`kw0809suzuki-oss/Astra` の `feature/astra-long-memory-vercel-v1-20261019` ブランチにある `app/api/chat/route.ts`、`src/astra-eight-layer.ts`、`src/astra-self-design.ts`（2026-10-21確認）。GitHub版はNext.jsとOpenAI Responses APIで動作するため、Poe用のPython接続口に置き換えている。

参考: [Poe Quick Start](https://creator.poe.com/docs/server-bots/quick-start) / [Functional Guides](https://creator.poe.com/docs/server-bots/server-bots-functional-guides)
