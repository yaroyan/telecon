import asyncio
import logging
import time
from pathlib import Path
import os
import yaml
from dotenv import load_dotenv
from telethon import TelegramClient
from telethon.errors import SessionPasswordNeededError, FloodWaitError, RPCError

# ────── ロギング ──────
logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger(__name__)

# ────── 設定ロード ──────
CONFIG_PATH = Path(__file__).parent.parent / "config" / "config.yml"
SECRETS_PATH = Path(__file__).parent.parent / "secrets" / ".env"

# YAML設定
with open(CONFIG_PATH, "r", encoding="utf-8") as f:
    config = yaml.safe_load(f)

# シークレット
load_dotenv(SECRETS_PATH)
API_ID = int(os.getenv("API_ID"))
API_HASH = os.getenv("API_HASH")
PHONE = os.getenv("PHONE")

BASE_DIR = Path(config["base_dir"])
DOWNLOAD_LIMIT = config["download_limit"]
MAX_CONCURRENT = config["max_concurrent"]
PART_SIZE_KB = config["part_size_mb"] * 1024
BOT_USERNAME = config["bot_username"]

client = TelegramClient("telecon_session", API_ID, API_HASH)


# ────── 認証 ──────
async def login():
    await client.connect()
    if not await client.is_user_authorized():
        await client.send_code_request(PHONE)
        code = input("Telegramから送られたコードを入力してください: ")
        try:
            await client.sign_in(PHONE, code)
        except SessionPasswordNeededError:
            password = input("2FAパスワードを入力してください: ")
            await client.sign_in(password=password)
    logger.info("ログイン完了")


# ────── ダウンロード関数 ──────
async def download_message_file(message, save_dir: Path, sem: asyncio.Semaphore) -> bool:
    if not message.media:
        return False

    filename = getattr(message.file, "name", None) or f"{message.id}"
    file_path = save_dir / filename
    if file_path.exists():
        logger.info("[SKIP] %s", file_path)
        return False

    async with sem:
        start_time = time.time()

        def progress(current: int, total: int):
            elapsed = time.time() - start_time
            speed = current / 1024 / 1024 / elapsed if elapsed > 0 else 0
            if total:
                pct = current / total * 100
                eta = (total - current) / (speed * 1024 * 1024) if speed > 0 else 0
                print(f"\r{pct:.2f}% ({current/1024/1024:.1f}MB/"
                      f"{total/1024/1024:.1f}MB) {speed:.2f}MB/s ETA: {eta:.1f}s", end="")
            else:
                print(f"\r{current/1024/1024:.1f}MB downloaded, {speed:.2f}MB/s", end="")

        try:
            await client.download_file(
                message.media,
                file=str(file_path),
                part_size_kb=PART_SIZE_KB,
                progress_callback=progress
            )
            print()
            logger.info("[OK] ダウンロード完了: %s", file_path)
            return True
        except FloodWaitError as e:
            logger.warning("FloodWait %ds 発生。待機中...", e.seconds)
            await asyncio.sleep(e.seconds)
            return await download_message_file(message, save_dir, sem)
        except RPCError as e:
            logger.error("RPCError: %s", e)
            return False
        except Exception:
            logger.exception("予期せぬエラー")
            return False


# ────── メイン ──────
async def download_bot_files():
    BASE_DIR.mkdir(parents=True, exist_ok=True)
    sem = asyncio.Semaphore(MAX_CONCURRENT)
    total_downloaded = 0

    await login()  # 認証処理

    try:
        bot_entity = await client.get_input_entity(BOT_USERNAME)
    except RPCError as e:
        logger.error("ボット取得失敗: %s", e)
        return

    async for message in client.iter_messages(bot_entity, limit=DOWNLOAD_LIMIT * 5):
        if not message.media:
            continue
        downloaded = await download_message_file(message, BASE_DIR, sem)
        if downloaded:
            total_downloaded += 1
        if total_downloaded >= DOWNLOAD_LIMIT:
            break

    logger.info("合計 %d 件をダウンロードしました", total_downloaded)


# ────── 実行 ──────
if __name__ == "__main__":
    asyncio.run(download_bot_files())
