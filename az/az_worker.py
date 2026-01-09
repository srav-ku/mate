import os
import requests
import subprocess
import shutil
from bs4 import BeautifulSoup
from urllib.parse import urljoin

from common.sheets import read_all_rows, read_pending_rows, batch_update
from common.archive import upload_file

TAB_NAME = "AZ"

def az_download_logic(title, link, number, identifier):
    temp_dir = f"/tmp/az_{number}"
    os.makedirs(temp_dir, exist_ok=True)

    base_url = "https://www.aznude.com"
    headers = {"User-Agent": "Mozilla/5.0"}

    try:
        print(f"[AZ] Processing: {number:02d} - {title}")

        # 1. Collect video pages
        resp = requests.get(link, headers=headers, timeout=30)
        soup = BeautifulSoup(resp.text, "html.parser")

        video_pages = [
            urljoin(base_url, a["href"])
            for a in soup.find_all("a", href=True)
            if a["href"].startswith("/azncdn/")
        ]

        if not video_pages:
            return False, "No video pages found"

        # 2. Collect mp4 links
        mp4_links = []
        for vp in video_pages:
            r = requests.get(vp, headers=headers, timeout=30)
            s = BeautifulSoup(r.text, "html.parser")
            for a in s.find_all("a", href=True):
                if a.find("button", class_="single-video-download-btn"):
                    mp4_links.append(a["href"])

        if not mp4_links:
            return False, "No mp4 links found"

        # 3. Download parts
        parts = []
        for i, url in enumerate(mp4_links):
            part_path = os.path.join(temp_dir, f"part_{i:02d}.mp4")
            with requests.get(url, headers=headers, stream=True) as r:
                r.raise_for_status()
                with open(part_path, "wb") as f:
                    for chunk in r.iter_content(1024 * 1024):
                        f.write(chunk)
            parts.append(part_path)

        # 4. Merge (quiet)
        list_file = os.path.join(temp_dir, "files.txt")
        with open(list_file, "w") as f:
            for p in parts:
                f.write(f"file '{p}'\n")

        output_file = os.path.join(temp_dir, f"{number:02d} - {title}.mp4")

        subprocess.run(
            [
                "ffmpeg",
                "-loglevel", "error",
                "-fflags", "+genpts",
                "-f", "concat",
                "-safe", "0",
                "-i", list_file,
                "-c", "copy",
                output_file,
            ],
            check=True,
        )

        print("[AZ] Merged successfully")

        # 5. Upload
        return upload_file(output_file, identifier)

    except Exception as e:
        return False, str(e)

    finally:
        shutil.rmtree(temp_dir, ignore_errors=True)

def main():
    all_rows = read_all_rows(TAB_NAME)

    used_numbers = [
        int(r["Assigned Number"])
        for r in all_rows
        if r.get("Assigned Number", "").isdigit()
    ]

    next_number = max(used_numbers, default=0) + 1
    pending = read_pending_rows(TAB_NAME)

    updates = []

    for r in pending:
        success, msg = az_download_logic(
            r["Title"],
            r["Link"],
            next_number,
            r["Identifier"],
        )

        updates.append({
            "row": r["row"],
            "Status": "DONE" if success else "FAILED",
            "Assigned Number": next_number if success else "",
            "Error Message": msg,
        })

        if success:
            next_number += 1

    if updates:
        batch_update(TAB_NAME, updates)

if __name__ == "__main__":
    main()
