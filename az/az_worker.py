import os
import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin
import subprocess
import shutil
from common.sheets import read_pending_rows, batch_update
from common.archive import upload_file
from common.telegram import send_message

TAB_NAME = "AZ"

def az_download_logic(title, link, start_number, identifier):
    temp_dir = f"/tmp/{title.replace(' ', '_')}"
    os.makedirs(temp_dir, exist_ok=True)

    base_url = "https://www.aznude.com"
    headers = {"User-Agent": "Mozilla/5.0"}

    try:
        # Step 1: extract video pages
        resp = requests.get(link, headers=headers)
        soup = BeautifulSoup(resp.text, "html.parser")
        video_pages = [urljoin(base_url, a['href']) for a in soup.find_all("a", href=True)
                       if a['href'].startswith("/azncdn/")]
        if not video_pages:
            return False, "No video pages found"

        # Step 2: extract MP4 links
        mp4_links = []
        for vp in video_pages:
            resp = requests.get(vp, headers=headers)
            subsoup = BeautifulSoup(resp.text, "html.parser")
            for a in subsoup.find_all("a", href=True):
                btn = a.find("button", class_="single-video-download-btn")
                if btn:
                    mp4_links.append(a["href"])
        if not mp4_links:
            return False, "No mp4 links found"

        # Step 3: download videos
        video_files = []
        for idx, url in enumerate(mp4_links):
            filename = f"part_{idx:02d}.mp4"
            path = os.path.join(temp_dir, filename)
            resp = requests.get(url, headers=headers, stream=True)
            with open(path, "wb") as f:
                for chunk in resp.iter_content(1024*1024):
                    f.write(chunk)
            video_files.append(path)

        # Step 4: merge videos
        file_list = os.path.join(temp_dir, "file_list.txt")
        with open(file_list, "w") as f:
            for vf in video_files:
                f.write(f"file '{vf}'\n")
        output_file = os.path.join(temp_dir, f"{start_number:02d} - {title}.mp4")
        subprocess.run(["ffmpeg", "-f", "concat", "-safe", "0", "-i", file_list, "-c", "copy", output_file], check=True)

        # Step 5: upload
        success, msg = upload_file(output_file, identifier)
        if not success:
            return False, msg

        return True, ""
    except Exception as e:
        return False, str(e)
    finally:
        shutil.rmtree(temp_dir, ignore_errors=True)

def main():
    rows = read_pending_rows(TAB_NAME)
    updates = []

    # Compute max assigned number for this tab
    max_num = max([int(r.get("Assigned Number") or 0) for r in rows], default=0)

    for r in rows:
        title = r["Title"]
        link = r["Link"]
        identifier = r["Identifier"]
        start_number = max_num + 1  # only increment after DONE

        success, msg = az_download_logic(title, link, start_number, identifier)

        updates.append({
            "row": r["row"],
            "Status": "DONE" if success else "FAILED",
            "Error Message": msg,
            "Assigned Number": start_number if success else ""
        })

        if success:
            max_num += 1  # increment only on success

        send_message(f"{title}: {'DONE' if success else 'FAILED'} {msg}")

    batch_update(TAB_NAME, updates)

if __name__ == "__main__":
    main()
