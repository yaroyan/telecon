# Telecon

**Telegram Concierge (telecon)** は、Telegramの操作の自動化を支援する Python ツールです。

---

## 特徴

- Telegram ボットやユーザーのチャットからファイルを自動取得
- ダウンロード進捗表示（速度・ETA付き）
- 並列ダウンロード（セマフォ制御）

---

## 前提条件

- Python 3.11+
- [Telethon](https://docs.telethon.dev/)  
- [python-dotenv](https://pypi.org/project/python-dotenv/)  
- [PyYAML](https://pypi.org/project/PyYAML/)  
- 推奨：`cryptg`

```bash
pip install telethon python-dotenv pyyaml cryptg
```

---

## インストールとセットアップ

1. **リポジトリをクローン**

2. **Python 環境を作成（推奨）**

```bash
python -m venv venv
source venv/bin/activate  # Windows: venvScriptsactivate
pip install -r requirements.txt
```

3. **設定ファイルを作成**

- `config/config.yml`  
  ```yaml
  base_dir: "./downloads"
  download_limit: 5
  max_concurrent: 2
  part_size_mb: 16
  bot_username: "example_bot"
  ```

- `.env`（シークレット管理）
  ```env
  API_ID=123456
  API_HASH=abcdef1234567890abcdef1234567890
  ```

> **注意:** `.env` と `telecon_session.session` は `.gitignore` で管理してください。

---

## 使い方

```bash
python src/telecon/downloader.py
```

- 初回実行時は電話番号と認証コードを求められます。
- 2FA（パスワード）を設定している場合は入力が必要です。

---

## ディレクトリ構成例

```
telecon/
├─ src/
│  └─ telecon/
│     └─ downloader.py
├─ config/
│  └─ config.yml
├─ secrets/
│  └─ .env
├─ downloads/          # 既定のダウンロード先のディレクトリ
├─ .gitignore
└─ README.md
```

---

## 推奨開発フロー

1. `.env` と `telecon_session.session` は Git にコミットしない
2. 必要に応じて `config.example.yml` を提供して、ユーザーが自分で `config.yml` を作成
3. 個人用環境や PyCharm 設定は `.idea/` を Git で無視

---

## 注意事項

- Telegram の利用規約（ToS）を遵守してください
- 過剰な同時ダウンロードや大きなファイルの連続取得はアカウント制限やBANのリスクがあります
- `cryptg` が導入されているとダウンロード速度が改善します

---

## 今後の予定

- Puppeteer 等によるブラウザ自動化連携
- ログや進捗のファイル出力対応
