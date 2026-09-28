# SME Labelling Portal

This Streamlit application records every submitted rating in a shared Google
Sheet. A rater can close the browser or use another device; selecting the same
rater name resumes at that rater's first incomplete case.

## One-time Google Sheets setup

1. Create a Google Cloud service account and enable the Google Sheets API.
2. Create a JSON key for that service account.
3. Share the ratings spreadsheet with the service-account `client_email` as an
   **Editor**.
4. In Streamlit Community Cloud, open **App settings → Secrets** and paste the
   values from `.streamlit/secrets.toml.example`, replacing every placeholder.
   For local development, copy that example to `.streamlit/secrets.toml` and
   enter the same values there.
5. Set `GOOGLE_SHEETS_SPREADSHEET_ID` to the ID between `/d/` and `/edit` in
   the ratings spreadsheet URL.

Never commit the JSON key or the real `secrets.toml` file.

## Data behaviour

- A record is sent to Google Sheets only after **Simpan Penilaian** is pressed.
- Each change appends a new event; the latest event for the same rater and
  `review_id` is used for progress and exports.
- The append-only history retains an audit trail of corrections.
- The rater selector is an identifier, not authentication. Do not share a
  rater identity between people.

## Run locally

```bash
pip install -r requirements.txt
streamlit run app.py
```
