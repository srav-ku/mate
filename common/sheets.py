import os
import json
import gspread
from google.oauth2.service_account import Credentials

GSHEET_ID = os.environ["GSHEET_ID"]
GSHEETS_CREDENTIALS = os.environ["GSHEETS_CREDENTIALS"]

SCOPES = ["https://www.googleapis.com/auth/spreadsheets"]

def _get_sheet(tab_name):
    creds_dict = json.loads(GSHEETS_CREDENTIALS)
    creds = Credentials.from_service_account_info(creds_dict, scopes=SCOPES)
    client = gspread.authorize(creds)
    return client.open_by_key(GSHEET_ID).worksheet(tab_name)

def read_all_rows(tab_name):
    sheet = _get_sheet(tab_name)
    values = sheet.get_all_values()
    headers = values[0]

    rows = []
    for idx, row in enumerate(values[1:], start=2):
        data = dict(zip(headers, row))
        data["row"] = idx
        rows.append(data)

    return rows

def read_pending_rows(tab_name):
    return [r for r in read_all_rows(tab_name) if not r.get("Status")]

def batch_update(tab_name, updates):
    sheet = _get_sheet(tab_name)
    cells = []

    for u in updates:
        r = u["row"]
        cells.extend([
            gspread.Cell(r, 4, u["Status"]),           # Status
            gspread.Cell(r, 5, u["Assigned Number"]),  # Assigned Number
            gspread.Cell(r, 6, u["Error Message"]),    # Error Message
        ])

    sheet.update_cells(cells)
