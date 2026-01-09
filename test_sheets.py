import os
import json
import gspread
from google.oauth2.service_account import Credentials

# Load credentials from GitHub secret
creds_json = json.loads(os.environ["GSHEETS_CREDENTIALS"])

scopes = ["https://www.googleapis.com/auth/spreadsheets"]
creds = Credentials.from_service_account_info(creds_json, scopes=scopes)

client = gspread.authorize(creds)

# Open sheet
sheet_id = os.environ["GSHEET_ID"]
sheet = client.open_by_key(sheet_id).sheet1

# Read first row
headers = sheet.row_values(1)
print("Headers:", headers)

# Write test status in row 2 (safe)
sheet.update_cell(2, headers.index("Status") + 1, "TEST_OK")

print("Sheet read/write successful")
