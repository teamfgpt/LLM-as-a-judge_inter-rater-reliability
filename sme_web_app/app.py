import streamlit as st
import pandas as pd
import os
import base64

st.set_page_config(page_title="SME Rater - Active Learning", layout="wide")

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_FILE = os.path.join(BASE_DIR, "data.xlsx")
SAVE_FILE = os.path.join(BASE_DIR, "sme_ratings_progress.csv")

@st.cache_data
def load_data():
    df = pd.read_excel(DATA_FILE)
    for col in ['relevance_label', 'level_fit', 'language_fit', 'business_fit', 'actionable', 'review_notes']:
        if col not in df.columns:
            df[col] = ""
    return df

def save_data(results_df):
    results_df.to_csv(SAVE_FILE, index=False)

def main():
    st.title("SME Evaluation Portal")
    st.markdown("Platform penilaian tingkat kesesuaian (Inter-Rater Reliability / QWK) untuk Phase 2 Active Learning.")
    
    rater_name = st.sidebar.selectbox("Pilih rater", ["Rater 1", "Rater 2"])
    
    df = load_data()
    
    if 'results' not in st.session_state:
        if os.path.exists(SAVE_FILE):
            existing_df = pd.read_csv(SAVE_FILE)
            # Ensure new columns exist for legacy CSV compatibility
            for new_col in ['level_fit_rating', 'language_fit_rating', 'business_fit_rating', 'actionable_rating']:
                if new_col not in existing_df.columns:
                    existing_df[new_col] = None
            st.session_state.results = existing_df
        else:
            st.session_state.results = pd.DataFrame(columns=[
                'review_id', 'rater', 
                'relevance_rating', 'level_fit_rating', 'language_fit_rating', 
                'business_fit_rating', 'actionable_rating', 'feedback_notes'
            ])
            
    rated_ids = st.session_state.results[st.session_state.results['rater'] == rater_name]['review_id'].tolist()
    unrated_df = df[~df['review_id'].isin(rated_ids)]
    
    st.sidebar.progress(len(rated_ids) / len(df) if len(df) > 0 else 1.0)
    st.sidebar.write(f"Progres {rater_name}: {len(rated_ids)} / {len(df)}")
    
    if len(unrated_df) == 0:
        st.success(f"Penilaian selesai untuk {rater_name}.")
        
        csv = st.session_state.results.to_csv(index=False)
        b64 = base64.b64encode(csv.encode()).decode()
        href = f'<a href="data:file/csv;base64,{b64}" download="sme_ratings_{rater_name.replace(" ", "_")}.csv">Unduh hasil CSV</a>'
        st.markdown(href, unsafe_allow_html=True)
        return

    current_idx = unrated_df.index[0]
    row = df.loc[current_idx]
    
    st.header(f"Kasus {len(rated_ids) + 1}")
    
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
    
    with st.form("rating_form"):
        options = ["2 - Agree", "1 - Partially Agree", "0 - Disagree"]
        
        rating_rel = st.radio("Tingkat relevansi (Relevance):", options=options, index=1)
        rating_lev = st.radio("Kesesuaian level jabatan (Level Fit):", options=options, index=1)
        rating_lan = st.radio("Kesesuaian bahasa (Language Fit):", options=options, index=1)
        rating_bus = st.radio("Kesesuaian konteks bisnis (Business Fit):", options=options, index=1)
        rating_act = st.radio("Tingkat kemudahan aplikasi (Actionable):", options=options, index=1)
        
        notes = st.text_area("Catatan opsional:")
        
        submitted = st.form_submit_button("Simpan dan lanjut")
        
        if submitted:
            new_row = {
                'review_id': row['review_id'],
                'rater': rater_name,
                'relevance_rating': int(rating_rel.split(" ")[0]),
                'level_fit_rating': int(rating_lev.split(" ")[0]),
                'language_fit_rating': int(rating_lan.split(" ")[0]),
                'business_fit_rating': int(rating_bus.split(" ")[0]),
                'actionable_rating': int(rating_act.split(" ")[0]),
                'feedback_notes': notes
            }
            
            st.session_state.results = pd.concat([st.session_state.results, pd.DataFrame([new_row])], ignore_index=True)
            save_data(st.session_state.results)
            st.rerun()

if __name__ == "__main__":
    main()
