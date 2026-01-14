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

# Hardcoded cookies.txt content (you can change later)
COOKIES_CONTENT = """# Netscape HTTP Cookie File
# https://curl.haxx.se/rfc/cookie_spec.html
# This is a generated file! Do not edit.
.momvids.com	TRUE	/	TRUE	1768450998	kt_rt_sub	100001
www.momvids.com	FALSE	/	FALSE	1783916600	kt_rt_fist	false
www.momvids.com	FALSE	/	FALSE	1768969401	kt_tcookie	1
.momvids.com	TRUE	/	TRUE	1768450998	kt_qparams	id%3D109053%26dir%3Dstepmom-feed-milk-pamela-rios%26utm_source%3DPBWeb%26utm_medium%3DPBWeb%26sub%3D100001
.momvids.com	TRUE	/	TRUE	1768450998	kt_ips	37.203.37.93%2C89.111.28.75
.momvids.com	TRUE	/	FALSE	0	PHPSESSID	f74354a02102865caf29fd77c1b952dc
.momvids.com	TRUE	/	TRUE	1783916603	cf_clearance	4Or80HBSuFPA8eVSCV3bg_.GCiAAyMNKt7quiBBugY0-1768364603-1.2.1.1-oi10_PMNEk2GQA.9aspW.NY.9LLTz.fS0Sklx3cF6MSu.DAif9cotX_qut3ePrB9nrW7hZP0zU6B0R7SLobRzzDN16fQhlC9BB5AXtfMnkFyO.b5i.Vv.kvbBS8CEjR6.uwX6W2VdbfiPexTjR1zlZWtXf7WAM.04Jy0JllVa2Ox.v0.LwDGka1zpesWIU3V0._HykG4NLBuOWddZ1FTQPOigqUWNIDLuJyF08DwT7k"""

# Write cookies to a temp file once
COOKIES_PATH = "/tmp/momvids_cookies.txt"
with open(COOKIES_PATH, "w", encoding="utf-8") as f:
    f.write(COOKIES_CONTENT)

def download_with_ytdlp(url, output_path):
    """First attempt: yt-dlp with eporner referer"""
    cmd = [
        "yt-dlp",
        "--no-part",
        "--no-warnings",
        "--user-agent", "Mozilla/5.0 (Windows NT 10.0; Win64; x64)",
        "--referer", "https://www.eporner.com/",
        "-o", output_path,
        url
    ]
    subprocess.run(cmd, check=True, capture_output=True, text=True)


def download_with_aria2_standard(url, output_dir, filename):
    """Second attempt: standard aria2c"""
    cmd = [
        "aria2c",
        "-x", "16", "-s", "16",
        "--file-allocation=trunc",
        "--auto-file-renaming=false",
        "--allow-overwrite=true",
        "--dir", output_dir,
        "-o", filename,
        "--header=User-Agent: Mozilla/5.0 (Windows NT 10.0; Win64; x64)",
        "--header=Referer: https://www.eporner.com/",
        "--header=Accept: */*",
        url
    ]
    subprocess.run(cmd, check=True, capture_output=True, text=True)


def download_with_aria2_xtits_aggressive(url, output_dir, filename):
    """Third attempt: aggressive aria2c with xtits.xxx referer"""
    cmd = [
        "aria2c",
        "-x", "16", "-s", "16",
        "--file-allocation=trunc",
        "--summary-interval=2",
        "--console-log-level=info",
        "--show-console-readout=true",
        "--auto-file-renaming=false",
        "--allow-overwrite=true",
        "--dir", output_dir,
        "-o", filename,
        "--header=User-Agent: Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36",
        "--header=Referer: https://www.xtits.xxx/",
        "--header=Accept: */*",
        "--header=Accept-Language: en-US,en;q=0.9",
        "--header=Connection: keep-alive",
        "--check-certificate=false",
        "--remote-time=true",
        url
    ]
    subprocess.run(cmd, check=True, capture_output=True, text=True)


def download_with_ytdlp_cookies_fallback(title, url, output_path):
    """
    4th & strongest fallback:
    Uses yt-dlp with momvids cookies + impersonate
    If link is /get_file/..., tries to convert to video page URL first
    """
    # If it's a /get_file/... link, try to guess the video page
    video_page_url = url
    if "/get_file/" in url:
        # Extract ID from /get_file/.../ID/...mp4
        import re
        match = re.search(r'/(\d{5,6})/[^/]+\.mp4', url)
        if match:
            video_id = match.group(1)
            # Guess title from original title or make slug
            slug = title.lower().replace(" ", "-").replace("'", "").replace(",", "")
            video_page_url = f"https://www.momvids.com/videos/{video_id}/{slug}/"

    cmd = [
        "yt-dlp",
        "--cookies", COOKIES_PATH,
        "--impersonate", "chrome",
        "--user-agent", "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36",
        "--referer", "https://www.momvids.com/",
        "--no-check-certificate",
        "--force-generic-extractor",
        "-o", output_path,
        video_page_url
    ]

    try:
        result = subprocess.run(cmd, check=True, capture_output=True, text=True)
        print(f"Success with yt-dlp + cookies fallback: {os.path.basename(output_path)}")
        print("Output:", result.stdout.strip()[:300])
        return True
    except subprocess.CalledProcessError as e:
        print("yt-dlp cookies fallback failed:", e.stderr.strip()[:300])
        return False


def epon_download_logic(title, link, number, identifier):
    temp_dir = tempfile.mkdtemp(prefix="epon_")
    filename = f"{number:02d} - {title}.mp4"
    output_path = os.path.join(temp_dir, filename)

    success = False
    error_msg = ""

    try:
        # 1. Try yt-dlp first (eporner style)
        try:
            download_with_ytdlp(link, output_path)
            success = True
            print(f"Success with yt-dlp (eporner): {filename}")
        except subprocess.CalledProcessError as e:
            error_msg = f"yt-dlp failed: {e.stderr.strip() or str(e)}"
            print(error_msg)

        # 2. Standard aria2c
        if not success:
            try:
                download_with_aria2_standard(link, temp_dir, filename)
                success = True
                print(f"Success with standard aria2c: {filename}")
            except subprocess.CalledProcessError as e:
                error_msg += f" | standard aria2c failed: {e.stderr.strip() or str(e)}"
                print(error_msg)

        # 3. Aggressive aria2c (xtits)
        if not success:
            try:
                download_with_aria2_xtits_aggressive(link, temp_dir, filename)
                success = True
                print(f"Success with xtits-aggressive aria2c: {filename}")
            except subprocess.CalledProcessError as e:
                error_msg += f" | xtits-aggressive aria2c failed: {e.stderr.strip() or str(e)}"
                print(error_msg)

        # 4. NEW: yt-dlp with momvids cookies + video page fallback
        if not success:
            if download_with_ytdlp_cookies_fallback(title, link, output_path):
                success = True

        if success:
            return upload_file(output_path, identifier), ""
        else:
            return False, error_msg

    except Exception as e:
        return False, f"Unexpected error: {str(e)}"

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

        success, msg = epon_download_logic(
            title,
            link,
            next_number,
            identifier
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
            print(f"Row {row_num} marked DONE - number {next_number}")
        else:
            update_row(
                TAB_NAME,
                row_num,
                "FAILED",
                "",
                msg
            )
            print(f"Row {row_num} FAILED: {msg}")


if __name__ == "__main__":
    main()
