import os
import subprocess
import tempfile
from common.sheets import read_pending_rows, update_row
from common.archive import upload_file

TAB_NAME = "MissAV"

def download_hls(title, hls_url):
    tmp_dir = tempfile.mkdtemp()
    output_file = os.path.join(tmp_dir, f"{title}.mp4")

    cmd = [
        "ffmpeg",
        "-loglevel", "error",
        "-nostats",
        "-i", hls_url,
        "-c", "copy",
        output_file
    ]

    subprocess.run(cmd, check=True)
    return output_file, tmp_dir

def main():
    rows = read_pending_rows(TAB_NAME)

    for r in rows:
        row_num = r["row"]
        title = r["Title"]
        link = r["Link"]
        identifier = r["Identifier"]

        try:
            video_path, tmp_dir = download_hls(title, link)

            success, msg = upload_file(video_path, identifier)
            if not success:
                raise Exception(msg)

            # ✅ IMMEDIATE WRITE AFTER SUCCESS
            update_row(
                TAB_NAME,
                row=row_num,
                status="DONE",
                assigned_number="",
                error_message=""
            )

        except Exception as e:
            # ✅ IMMEDIATE WRITE AFTER FAILURE
            update_row(
                TAB_NAME,
                row=row_num,
                status="FAILED",
                assigned_number="",
                error_message=str(e)
            )

        finally:
            if "tmp_dir" in locals():
                subprocess.run(["rm", "-rf", tmp_dir])

if __name__ == "__main__":
    main()
