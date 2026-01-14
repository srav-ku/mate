import os
import subprocess
import tempfile
import shutil

from common.sheets import read_pending_rows, update_row
from common.archive import upload_file

TAB_NAME = "EPON"
COOKIES_FILE = "momvids_cookies.txt"


def momvids_download_logic(title, link, identifier):
    temp_dir = tempfile.mkdtemp(prefix="momvids_")
    filename = f"{title}.mp4"
    output_path = os.path.join(temp_dir, filename)

    try:
        cmd = [
            "yt-dlp",
            "--cookies", COOKIES_FILE,
            "--impersonate", "chrome",
            "--referer", "https://www.momvids.com/",
            "--no-check-certificate",
            "--no-part",
            "--no-warnings",
            "-o", output_path,
            link
        ]

        result = subprocess.run(
            cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            check=True
        )

        return upload_file(output_path, identifier), ""

    except subprocess.CalledProcessError as e:
        error_msg = e.stderr.strip() or e.stdout.strip() or str(e)
        return False, error_msg

    except Exception as e:
        return False, str(e)

    finally:
        shutil.rmtree(temp_dir, ignore_errors=True)


def main():
    rows = read_pending_rows(TAB_NAME)

    for r in rows:
        row_num = r["row"]
        title = r["Title"]
        link = r["Link"]
        identifier = r["Identifier"]

        success, msg = momvids_download_logic(
            title,
            link,
            identifier
        )

        if success:
            update_row(
                TAB_NAME,
                row_num,
                "DONE",
                "",
                ""
            )
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
