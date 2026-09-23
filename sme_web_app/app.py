import streamlit as st
import pandas as pd
import os
import base64

st.set_page_config(page_title="SME Rater - Active Learning", layout="wide")

# Configuration
import os
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_FILE = os.path.join(BASE_DIR, "data.xlsx")
SAVE_FILE = os.path.join(BASE_DIR, "sme_ratings_progress.csv")

@st.cache_data
def load_data():
    df = pd.read_excel(DATA_FILE)
    # Ensure all required columns exist
    for col in ['relevance_label', 'review_notes']:
        if col not in df.columns:
            df[col] = ""
    return df

def save_data(results_df):
    results_df.to_csv(SAVE_FILE, index=False)

def main():
    st.title("🎓 SME Evaluation Portal (Phase 2 Active Learning)")
    st.markdown("Aplikasi ini dibuat untuk memudahkan proses penilaian *Inter-Rater* (QWK) oleh Tim Pakar (SME).")
    
    # Rater selection
    rater_name = st.sidebar.selectbox("Pilih Rater:", ["Rater 1", "Rater 2"])
    
    # Load dataset
    df = load_data()
    
    # State management for progress
    if 'results' not in st.session_state:
        if os.path.exists(SAVE_FILE):
            st.session_state.results = pd.read_csv(SAVE_FILE)
        else:
            # Initialize empty results dataframe
            st.session_state.results = pd.DataFrame(columns=[
                'review_id', 'rater', 'relevance_rating', 'feedback_notes'
            ])
            
    # Filter out already rated rows by this rater
    rated_ids = st.session_state.results[st.session_state.results['rater'] == rater_name]['review_id'].tolist()
    
    # Find next unrated row
    unrated_df = df[~df['review_id'].isin(rated_ids)]
    
    st.sidebar.progress(len(rated_ids) / len(df))
    st.sidebar.write(f"**Progress {rater_name}:** {len(rated_ids)} / {len(df)} selesai.")
    
    if len(unrated_df) == 0:
        st.success(f"🎉 Luar biasa! {rater_name} telah menyelesaikan seluruh penilaian.")
        
        # Download button
        csv = st.session_state.results.to_csv(index=False)
        b64 = base64.b64encode(csv.encode()).decode()
        href = f'<a href="data:file/csv;base64,{b64}" download="sme_ratings_{rater_name.replace(" ", "_")}.csv">Unduh Hasil Penilaian (CSV)</a>'
        st.markdown(href, unsafe_allow_html=True)
        return

    # Get the current row
    current_idx = unrated_df.index[0]
    row = df.loc[current_idx]
    
    st.header(f"Kasus #{len(rated_ids) + 1}")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("📌 Profil & Kompetensi Pekerjaan")
        st.write(f"**Job Title:** {row.get('job_title', '-')}")
        st.write(f"**Signal Text:** {row.get('competency_signal_text', '-')}")
        st.write(f"**Responsibility:** {row.get('responsibility_text', '-')}")
        
    with col2:
        st.subheader("📚 Rekomendasi Kursus (Course)")
        st.write(f"**Course Name:** {row.get('course_name', '-')}")
        st.write(f"**Level:** {row.get('course_level', '-')}")
        st.write(f"**Source:** {row.get('course_source', '-')}")

    st.divider()
    
    st.subheader("🤖 Prediksi AI Saat Ini")
    st.info(f"**AI Relevance Label:** {row.get('relevance_label', 'N/A')}\n\n**AI Rationale:** {row.get('review_notes', '-')}")
    
    st.divider()
    
    st.subheader(f"✍️ Penilaian {rater_name}")
    st.markdown("Pilih tingkat persetujuan Anda terhadap rekomendasi ini berdasarkan **Relevance** (Skala 0-2):")
    
    with st.form("rating_form"):
        rating = st.radio(
            "Tingkat Relevansi Kursus dengan Kompetensi:",
            options=[
                "2 - Agree (Sangat Relevan)", 
                "1 - Partially Agree (Cukup Relevan)", 
                "0 - Disagree (Tidak Relevan)"
            ],
            index=1
        )
        
        notes = st.text_area("Catatan Tambahan (Opsional, jika ada koreksi atau alasan khusus):")
        
        submitted = st.form_submit_button("Simpan & Lanjut ➡️")
        
        if submitted:
            # Parse rating
            rating_val = int(rating.split(" ")[0])
            
            # Save to state
            new_row = {
                'review_id': row['review_id'],
                'rater': rater_name,
                'relevance_rating': rating_val,
                'feedback_notes': notes
            }
            
            st.session_state.results = pd.concat([st.session_state.results, pd.DataFrame([new_row])], ignore_index=True)
            save_data(st.session_state.results)
            st.rerun()

if __name__ == "__main__":
    main()
