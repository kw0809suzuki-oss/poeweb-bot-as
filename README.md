# Poe Astra — Poe専用 Astra Field（実験版）

**目的:** 既存 GitHub版 Astra Field の会話思想を、Poe Server Botへ独立して移設する。元のAstraとFloot版は変更しない。

これは **Poe接続アダプター＋会話方針の初期移設** であり、既存Web版との完全な機能互換はまだない。

## GitHub → Modal → Poe（ブラウザだけで接続する推奨手順）

**Windowsでコードを動かす必要はありません。** `.github/workflows/deploy-modal.yml` が GitHub Actions 上でテストして Modal に配置します。

最初だけ、ブラウザで次の設定を行います。

1. **Modal** にログインし、Workspace の Settings / API Tokens から GitHub Actions用のAPIトークンを作成。表示された **Token ID** と **Token Secret** は他人に渡さない。
2. **GitHub** の [このリポジトリのActions Secrets](https://github.com/kw0809suzuki-oss/poeweb-bot-as/settings/secrets/actions) で、次の2つを別々の *Repository secret* として登録。
   - `MODAL_TOKEN_ID` ← ModalのToken ID
   - `MODAL_TOKEN_SECRET` ← ModalのToken Secret
3. **Poe** の [Server Bot作成画面](https://poe.com/create_bot?server=1) で Bot Name と Access Key を取得。既存ボットなら編集画面から確認。
4. **Modal** のダッシュボードの **Secrets** で、名前が **`poe-astra`** のSecretを作る。中に `POE_ACCESS_KEY`（PoeのAccess Key）と `POE_BOT_NAME`（PoeのBot Name）を入れる。必要なら `POE_MODEL` にPoeのモデル名（既定 `GPT-5.4`）を入れる。このPoeキーはGitHubに登録しない。
5. **GitHub** の [Actions](https://github.com/kw0809suzuki-oss/poeweb-bot-as/actions/workflows/deploy-modal.yml) から **Deploy Poe Astra to Modal** → **Run workflow** を押す。接続情報が設定されていないときはデプロイせず警告を出す。
6. Workflow成功後に、GitHub Actionsの **Deploy Poe Astra to Modal** のログ、またはModalダッシュボードの **poe-astra** アプリから **HTTPSエンドポイントURL** を確認し、Poeの **Server URL（ボットサーバーリンク）** に貼って保存する。
7. Poeで短い会話を行い、モデル応答、履歴の扱い、ポイント消費を確認する。**公開運用・機能互換はこの実機試験まで未確認。**

設定後は、`main` のPoeコードが変わるとGitHub Actionsが再配置します。手動実行もできます。デプロイ用トークンは *GitHub Actionsにだけ* 設定し、Poeのボット認証キーは *Modal Secretsにだけ* 設定する構造です。

**注意:** GitHubが「成功」と表示しても、シークレット不足によって配置がスキップされた場合があります。ログに `Deploy Poe Astra to Modal` の実行があることを確認してください。Modalの実行料金やPoeのポイント消費は別途発生する可能性があります。

### ローカルCLIは任意

以下にある `modal deploy` 等のコマンドは開発者向けの代替手順であり、GitHub Actions方式では不要です。

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
