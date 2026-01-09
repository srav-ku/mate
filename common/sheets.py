import os
import json
import gspread
from google.oauth2.service_account import Credentials

GSHEET_ID = os.environ["GSHEET_ID"]
GSHEETS_CREDENTIALS = os.environ["GSHEETS_CREDENTIALS"]

# Google Sheets scope
SCOPES = ['https://www.googleapis.com/auth/spreadsheets']

def get_sheet(tab_name):
    creds_dict = json.loads(GSHEETS_CREDENTIALS)
    creds = Credentials.from_service_account_info(creds_dict, scopes=SCOPES)
    client = gspread.authorize(creds)
    sheet = client.open_by_key(GSHEET_ID).worksheet(tab_name)
    return sheet

def read_pending_rows(tab_name):
    """
    Returns list of dicts with row number and columns.
    Only rows where Status is empty.
    """
    sheet = get_sheet(tab_name)
    all_values = sheet.get_all_values()
    headers = all_values[0]
    rows = []
    for idx, row in enumerate(all_values[1:], start=2):  # starts at row 2
        row_dict = dict(zip(headers, row))
        if not row_dict.get("Status"):
            row_dict["row"] = idx
            rows.append(row_dict)
    return rows

def batch_update(tab_name, updates):
    """
    updates: list of dicts with keys: row, Status, Assigned Number, Error Message
    """
    sheet = get_sheet(tab_name)
    for u in updates:
        row_num = u["row"]
        sheet.update(f'D{row_num}', [[u["Status"]]])
        sheet.update(f'E{row_num}', [[u["Assigned Number"]]])
        sheet.update(f'F{row_num}', [[u["Error Message"]]])
