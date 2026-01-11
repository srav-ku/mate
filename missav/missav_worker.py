import os
import subprocess
import shutil
from common.sheets import read_pending_rows, update_row
from common.archive import upload_file

TAB_NAME = "MissAV"

def download_hls(title, hls_url, temp_dir):
    output_file = os.path.join(temp_dir, f"{title}.mp4")

    cmd = [
        "ffmpeg",
        "-loglevel", "error",
        "-stats",
        "-i", hls_url,
        "-c", "copy",
        output_file
    ]

    subprocess.run(cmd, check=True)
    return output_file

def main():
    rows = read_pending_rows(TAB_NAME)

    for r in rows:
        row_num = r["row"]
        title = r["Title"].strip()
        link = r["Link"].strip()
        identifier = r["Identifier"].strip()

        temp_dir = f"/tmp/missav_{row_num}"
        os.makedirs(temp_dir, exist_ok=True)

        try:
            # 1. Download HLS → MP4
            video_file = download_hls(title, link, temp_dir)

            # 2. Upload to Archive
            success, msg = upload_file(video_file, identifier)
            if not success:
                raise Exception(msg)

            # 3. Immediate sheet update
            update_row(
                TAB_NAME,
                row_num,
                status="DONE",
                assigned_number="",
                error_message=""
            )

        except Exception as e:
            update_row(
                TAB_NAME,
                row_num,
                status="FAILED",
                assigned_number="",
                error_message=str(e)
            )

        finally:
            shutil.rmtree(temp_dir, ignore_errors=True)

if __name__ == "__main__":
    main()
