"""SME labelling portal with durable Google Sheets event storage.

Each submitted rating is appended to the configured Google Sheet. The newest
event for a (rater, review_id) pair is authoritative, so a rater can edit a
previous response without deleting the audit record.
"""

from datetime import datetime, timezone
import os
import uuid

import gspread
from google.oauth2.service_account import Credentials
import pandas as pd
import streamlit as st


st.set_page_config(page_title="SME Rater - Active Learning", layout="wide")

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_FILE = os.path.join(BASE_DIR, "data.xlsx")
RATINGS_SHEET_NAME = "Ratings"
RATING_COLUMNS = [
    "event_id", "rater", "review_id", "relevance_rating", "level_fit_rating",
    "language_fit_rating", "business_fit_rating", "actionable_rating",
    "feedback_notes", "submitted_at",
]
RATING_FIELDS = [
    "relevance_rating", "level_fit_rating", "language_fit_rating",
    "business_fit_rating", "actionable_rating",
]


@st.cache_data
def load_data():
    df = pd.read_excel(DATA_FILE)
    for column in [
        "relevance_label", "level_fit", "language_fit", "business_fit",
        "actionable", "review_notes",
    ]:
        if column not in df.columns:
            df[column] = ""
    return df


def configured_spreadsheet_id():
    """Read the Sheet ID from deployment secrets, never source control."""
    return st.secrets.get("GOOGLE_SHEETS_SPREADSHEET_ID") or os.getenv(
        "GOOGLE_SHEETS_SPREADSHEET_ID"
    )


@st.cache_resource
def ratings_worksheet(spreadsheet_id):
    """Connect using the Streamlit-hosted Google service-account secret."""
    service_account = dict(st.secrets["gcp_service_account"])
    credentials = Credentials.from_service_account_info(
        service_account,
        scopes=["https://www.googleapis.com/auth/spreadsheets"],
    )
    client = gspread.authorize(credentials)
    return client.open_by_key(spreadsheet_id).worksheet(RATINGS_SHEET_NAME)


@st.cache_data(ttl=20, show_spinner=False)
def load_rating_events(spreadsheet_id):
    """Return the append-only rating event log from Google Sheets."""
    records = ratings_worksheet(spreadsheet_id).get_all_records(
        expected_headers=RATING_COLUMNS
    )
    return pd.DataFrame(records, columns=RATING_COLUMNS)


def latest_ratings(events):
    """Keep only the latest submitted response for every rater and case."""
    if events.empty:
        return events.copy()
    latest = events.copy()
    latest["submitted_at"] = pd.to_datetime(latest["submitted_at"], utc=True)
    return latest.sort_values("submitted_at").drop_duplicates(
        subset=["rater", "review_id"], keep="last"
    )


def rating_index(value):
    """Map a saved ordinal value to its displayed option index."""
    try:
        return {2: 0, 1: 1, 0: 2}[int(value)]
    except (KeyError, TypeError, ValueError):
        return None


def append_rating(spreadsheet_id, rater, review_id, ratings, notes):
    """Append rather than overwrite, preserving a complete correction history."""
    event = [
        str(uuid.uuid4()), rater, str(review_id),
        *(ratings[field] for field in RATING_FIELDS), notes,
        datetime.now(timezone.utc).isoformat(),
    ]
    ratings_worksheet(spreadsheet_id).append_row(event, value_input_option="RAW")
    load_rating_events.clear()


def main():
    st.title("SME Evaluation Portal")
    st.markdown(
        "Platform penilaian tingkat kesesuaian untuk Phase 2 Active Learning. "
        "Setiap penilaian tersimpan di Google Sheets setelah tombol "
        "**Simpan Penilaian** dipilih."
    )

    spreadsheet_id = configured_spreadsheet_id()
    if not spreadsheet_id or "gcp_service_account" not in st.secrets:
        st.error(
            "Penyimpanan Google Sheets belum dikonfigurasi. Hubungi administrator "
            "sebelum melakukan penilaian; aplikasi tidak akan menyimpan data secara lokal."
        )
        st.stop()

    try:
        df = load_data()
        events = load_rating_events(spreadsheet_id)
    except Exception as error:
        st.error(f"Google Sheets tidak dapat diakses. Tidak ada penilaian yang disimpan. ({error})")
        st.stop()

    results = latest_ratings(events)
    rater_name = st.sidebar.selectbox("Pilih rater", ["Rater 1", "Rater 2"])
    rated_ids = set(
        results.loc[results["rater"] == rater_name, "review_id"].astype(str).tolist()
    )
    unrated = df[~df["review_id"].astype(str).isin(rated_ids)]

    if "last_rater" not in st.session_state or st.session_state.last_rater != rater_name:
        st.session_state.last_rater = rater_name
        st.session_state.current_idx = int(unrated.index[0]) if not unrated.empty else 0

    progress_value = len(rated_ids) / len(df) if len(df) else 1.0
    st.sidebar.progress(progress_value)
    st.sidebar.write(f"Progres {rater_name}: {len(rated_ids)} / {len(df)}")
    st.sidebar.caption("Progres dimuat dari Google Sheets dan dapat dilanjutkan dari perangkat lain.")
    own_results = results[results["rater"] == rater_name]
    st.sidebar.download_button(
        "Unduh penilaian saya (CSV)",
        own_results.to_csv(index=False).encode("utf-8"),
        file_name=f"sme_ratings_{rater_name.replace(' ', '_')}.csv",
        mime="text/csv",
    )

    if df.empty:
        st.warning("Data kosong.")
        return

    current_idx = max(0, min(st.session_state.get("current_idx", 0), len(df) - 1))
    st.session_state.current_idx = current_idx
    col_prev, col_idx, col_next = st.columns([1, 2, 1])
    with col_prev:
        if st.button("⬅️ Sebelumnya", use_container_width=True) and current_idx > 0:
            st.session_state.current_idx -= 1
            st.rerun()
    with col_idx:
        st.markdown(
            f"<h3 style='text-align: center; margin-top: 0;'>Kasus {current_idx + 1} dari {len(df)}</h3>",
            unsafe_allow_html=True,
        )
    with col_next:
        if st.button("Selanjutnya ➡️", use_container_width=True) and current_idx < len(df) - 1:
            st.session_state.current_idx += 1
            st.rerun()

    row = df.loc[current_idx]
    review_id = str(row["review_id"])
    existing = results[
        (results["rater"] == rater_name) & (results["review_id"].astype(str) == review_id)
    ]
    existing_rating = existing.iloc[0] if not existing.empty else None
    if existing_rating is not None:
        st.success("✅ Kasus ini sudah Anda nilai. Anda dapat mengubahnya jika perlu.")

    col1, col2 = st.columns(2)
    with col1:
        st.subheader("Konteks Pekerjaan")
        st.write(f"**Job Title:** {row.get('job_title', '-')}")
        st.write(f"**Signal Text:** {row.get('competency_signal_text', '-')}")
        st.write(f"**Responsibility:** {row.get('responsibility_text', '-')}")
    with col2:
        st.subheader("Rekomendasi Kursus")
        st.write(f"**Course Name:** {row.get('course_name', '-')}")
        st.write(f"**Level:** {row.get('course_level', '-')}")
        st.write(f"**Source:** {row.get('course_source', '-')}")

    st.divider()
    st.subheader("Prediksi AI")
    st.info(
        f"**Relevance:** {row.get('relevance_label', '-')} | "
        f"**Level:** {row.get('level_fit', '-')} | "
        f"**Language:** {row.get('language_fit', '-')} | "
        f"**Business:** {row.get('business_fit', '-')} | "
        f"**Actionable:** {row.get('actionable', '-')}\n\n"
        f"**AI Rationale:** {row.get('review_notes', '-')}"
    )

    st.divider()
    st.subheader(f"Evaluasi {rater_name}")
    st.markdown("Evaluasi kualitas rekomendasi kursus terhadap kompetensi (Skala 0-2).")
    options = ["2 - Agree", "1 - Partially Agree", "0 - Disagree"]
    defaults = {
        field: rating_index(existing_rating[field]) if existing_rating is not None else None
        for field in RATING_FIELDS
    }
    notes_default = (
        str(existing_rating["feedback_notes"])
        if existing_rating is not None and pd.notna(existing_rating["feedback_notes"])
        else ""
    )

    with st.form("rating_form"):
        rating_rel = st.radio(
            "Tingkat relevansi (Relevance):", options=options,
            index=defaults["relevance_rating"],
            help="Sejauh mana materi inti kursus relevan dengan kompetensi dan tanggung jawab pada profil pekerjaan target.",
        )
        rating_lev = st.radio(
            "Kesesuaian level jabatan (Level Fit):", options=options,
            index=defaults["level_fit_rating"],
            help="Kesesuaian tingkat kesulitan kursus dengan tingkatan atau senioritas jabatan.",
        )
        rating_lan = st.radio(
            "Kesesuaian bahasa (Language Fit):", options=options,
            index=defaults["language_fit_rating"],
            help="Kesesuaian bahasa pengantar kursus dengan konteks geografi atau tuntutan bahasa pada pekerjaan tersebut.",
        )
        rating_bus = st.radio(
            "Kesesuaian konteks bisnis (Business Fit):", options=options,
            index=defaults["business_fit_rating"],
            help="Kecocokan studi kasus atau pendekatan kursus dengan fungsi, industri, atau budaya departemen target.",
        )
        rating_act = st.radio(
            "Tingkat kemudahan aplikasi (Actionable):", options=options,
            index=defaults["actionable_rating"],
            help="Seberapa praktis materi tersebut untuk langsung dipraktikkan dalam pekerjaan sehari-hari.",
        )
        notes = st.text_area("Catatan opsional:", value=notes_default)
        submitted = st.form_submit_button("Simpan Penilaian")

        if submitted:
            choices = [rating_rel, rating_lev, rating_lan, rating_bus, rating_act]
            if any(choice is None for choice in choices):
                st.error("Pilih nilai untuk semua lima kriteria sebelum menyimpan.")
                st.stop()
            ratings = {
                "relevance_rating": int(rating_rel.split(" ", maxsplit=1)[0]),
                "level_fit_rating": int(rating_lev.split(" ", maxsplit=1)[0]),
                "language_fit_rating": int(rating_lan.split(" ", maxsplit=1)[0]),
                "business_fit_rating": int(rating_bus.split(" ", maxsplit=1)[0]),
                "actionable_rating": int(rating_act.split(" ", maxsplit=1)[0]),
            }
            try:
                append_rating(spreadsheet_id, rater_name, review_id, ratings, notes)
            except Exception as error:
                st.error(f"Penilaian gagal disimpan. Silakan coba lagi. ({error})")
                st.stop()
            if current_idx < len(df) - 1:
                st.session_state.current_idx += 1
            st.rerun()


if __name__ == "__main__":
    main()
