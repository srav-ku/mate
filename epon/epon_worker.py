import os
import subprocess
import tempfile
import shutil

from common.sheets import (
    read_pending_rows,
    get_max_assigned_number,
    update_row
)
from common.archive import upload_file

TAB_NAME = "EPON"
COOKIES_FILE = "momvids_cookies.txt"


# ---------- DOWNLOADERS ----------

def download_momvids(url, output_path):
    cmd = [
        "yt-dlp",
        "--cookies", COOKIES_FILE,
        "--impersonate", "chrome",
        "--referer", "https://www.momvids.com/",
        "--no-check-certificate",
        "--no-part",
        "-o", output_path,
        url
    ]
    subprocess.run(cmd, check=True)


def download_eporner_ytdlp(url, output_path):
    cmd = [
        "yt-dlp",
        "--no-part",
        "--no-warnings",
        "--user-agent", "Mozilla/5.0",
        "--referer", "https://www.eporner.com/",
        "-o", output_path,
        url
    ]
    subprocess.run(cmd, check=True)


def download_aria2(url, output_dir, filename):
    cmd = [
        "aria2c",
        "-x", "16",
        "-s", "16",
        "--file-allocation=trunc",
        "--auto-file-renaming=false",
        "--allow-overwrite=true",
        "--dir", output_dir,
        "-o", filename,
        "--header=User-Agent: Mozilla/5.0",
        "--header=Referer: https://www.eporner.com/",
        url
    ]
    subprocess.run(cmd, check=True)


# ---------- CORE LOGIC ----------

def epon_download_logic(title, link, number, identifier):
    temp_dir = tempfile.mkdtemp(prefix="epon_")
    filename = f"{number:02d} - {title}.mp4"
    output_path = os.path.join(temp_dir, filename)

    try:
        # 1️⃣ MomVids FIRST
        try:
            download_momvids(link, output_path)
            return upload_file(output_path, identifier)
        except Exception:
            pass

        # 2️⃣ EPON yt-dlp
        try:
            download_eporner_ytdlp(link, output_path)
            return upload_file(output_path, identifier)
        except Exception:
            pass

        # 3️⃣ aria2 fallback
        download_aria2(link, temp_dir, filename)
        return upload_file(output_path, identifier)

    except Exception as e:
        return False, str(e)

    finally:
        shutil.rmtree(temp_dir, ignore_errors=True)


# ---------- MAIN ----------

def main():
    rows = read_pending_rows(TAB_NAME)
    current_number = get_max_assigned_number(TAB_NAME)

    for r in rows:
        row_num = r["row"]
        title = r["Title"]
        link = r["Link"]
        identifier = r["Identifier"]

        next_number = current_number + 1

        success, msg = epon_download_logic(
            title, link, next_number, identifier
        )

        if success:
            update_row(TAB_NAME, row_num, "DONE", next_number, "")
            current_number += 1
        else:
            update_row(TAB_NAME, row_num, "FAILED", "", msg)


if __name__ == "__main__":
    main()
