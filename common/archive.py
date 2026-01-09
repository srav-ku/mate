import os
from internetarchive import upload

ARCHIVE_ACCESS_KEY = os.environ["ARCHIVE_ACCESS_KEY"]
ARCHIVE_SECRET_KEY = os.environ["ARCHIVE_SECRET_KEY"]

def upload_file(file_path, identifier):
    filename = os.path.basename(file_path)

    metadata = {
        "mediatype": "movies",
        "title": filename.rsplit(".", 1)[0],
    }

    try:
        result = upload(
            identifier=identifier,
            files={filename: file_path},  # IMPORTANT: no overwrite
            metadata=metadata,
            access_key=ARCHIVE_ACCESS_KEY,
            secret_key=ARCHIVE_SECRET_KEY,
            retries=5,
            retries_sleep=2,
            delete=False,
        )

        if result and result[0].status_code == 200:
            return True, ""
        return False, str(result)

    except Exception as e:
        return False, str(e)
