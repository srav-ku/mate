import os
import requests
import subprocess
import shutil
import tempfile
from bs4 import BeautifulSoup

from common.sheets import (
    read_pending_rows,
    get_max_assigned_number,
    update_row
)
from common.archive import upload_file

TAB_NAME = "MISSAV"


def missav_download_logic(title, link, number, identifier):
    temp_dir = tempfile.mkdtemp(prefix="missav_")
    headers = {"User-Agent": "Mozilla/5.0"}

    try:
        # Step 1: get page
        r = requests.get(link, headers=headers, timeout=30)
        soup = BeautifulSoup(r.text, "html.parser")

        video = soup.find("video")
        if not video:
            return False, "Video tag not found"

        source = video.find("source")
        if not source or not source.get("src"):
            return False, "Video source not found"

        video_url = source["src"]

        # Step 2: download mp4
        output = os.path.join(
            temp_dir, f"{number:02d} - {title}.mp4"
        )

        subprocess.run(
            [
                "ffmpeg",
                "-loglevel", "error",
                "-i", video_url,
                "-c", "copy",
                output
            ],
            check=True
        )

        # Step 3: upload
        return upload_file(output, identifier)

    except Exception as e:
        return False, str(e)

    finally:
        shutil.rmtree(temp_dir, ignore_errors=True)


def main():
    rows = read_pending_rows(TAB_NAME)
    current_number = get_max_assigned_number(TAB_NAME)

    for r in rows:
        row_num = r["row"]
        title = r["Title"]
        link = r["Link"]
        identifier = r["Identifier"]

        next_number = current_number + 1

        success, msg = missav_download_logic(
            title, link, next_number, identifier
        )

        if success:
            update_row(
                TAB_NAME,
                row_num,
                "DONE",
                next_number,
                ""
            )
            current_number += 1
        else:
            update_row(
                TAB_NAME,
                row_num,
                "FAILED",
                "",
                msg
            )


if __name__ == "__main__":
    main()
