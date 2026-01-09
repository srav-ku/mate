import gspread
import os
import json
from oauth2client.service_account import ServiceAccountCredentials

GSHEET_ID = os.environ["GSHEET_ID"]
GSHEETS_CREDENTIALS = os.environ["GSHEETS_CREDENTIALS"]

# scope for Sheets API
SCOPES = ['https://www.googleapis.com/auth/spreadsheets']

def get_sheet(tab_name):
    creds_json = json.loads(GSHEETS_CREDENTIALS)
    creds = ServiceAccountCredentials.from_json_keyfile_dict(creds_json, SCOPES)
    client = gspread.authorize(creds)
    sheet = client.open_by_key(GSHEET_ID).worksheet(tab_name)
    return sheet

def read_pending_rows(tab_name):
    sheet = get_sheet(tab_name)
    data = sheet.get_all_records()
    pending_rows = []
    for idx, row in enumerate(data, start=2):  # gspread rows start at 1 + header
        if not row.get("Status"):
            pending_rows.append({"row": idx, **row})
    return pending_rows

def batch_update(tab_name, updates):
    """
    updates: list of dicts
        row -> row number in sheet
        Status -> DONE/FAILED
        Assigned Number -> optional
        Error Message -> optional
    """
    sheet = get_sheet(tab_name)
    for u in updates:
        row_num = u["row"]
        if "Status" in u:
            sheet.update(f'D{row_num}', u["Status"])
        if "Assigned Number" in u:
            sheet.update(f'E{row_num}', u["Assigned Number"])
        if "Error Message" in u:
            sheet.update(f'F{row_num}', u["Error Message"])
