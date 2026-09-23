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

def get_index_from_val(val):
    if pd.isna(val): return 1
    val = int(val)
    if val == 2: return 0
    if val == 1: return 1
    if val == 0: return 2
    return 1

def main():
    st.title("SME Evaluation Portal")
    st.markdown("Platform penilaian tingkat kesesuaian (Inter-Rater Reliability / QWK) untuk Phase 2 Active Learning.")
    
    df = load_data()
    
    # Load state
    if 'results' not in st.session_state:
        if os.path.exists(SAVE_FILE):
            existing_df = pd.read_csv(SAVE_FILE)
            for new_col in ['level_fit_rating', 'language_fit_rating', 'business_fit_rating', 'actionable_rating']:
                if new_col not in existing_df.columns:
                    existing_df[new_col] = None
            st.session_state.results = existing_df
        else:
            st.session_state.results = pd.DataFrame(columns=[
                'review_id', 'rater', 'relevance_rating', 'level_fit_rating', 
                'language_fit_rating', 'business_fit_rating', 'actionable_rating', 'feedback_notes'
            ])
            
    rater_name = st.sidebar.selectbox("Pilih rater", ["Rater 1", "Rater 2"])
    
    # Reset tracking index if rater changes
    if 'last_rater' not in st.session_state or st.session_state.last_rater != rater_name:
        st.session_state.last_rater = rater_name
        rated_ids = st.session_state.results[st.session_state.results['rater'] == rater_name]['review_id'].tolist()
        unrated = df[~df['review_id'].isin(rated_ids)]
        if len(unrated) > 0:
            st.session_state.current_idx = int(unrated.index[0])
        else:
            st.session_state.current_idx = 0
            
    # Calculate progress
    rated_ids = st.session_state.results[st.session_state.results['rater'] == rater_name]['review_id'].tolist()
    progress_val = len(rated_ids) / len(df) if len(df) > 0 else 1.0
    st.sidebar.progress(progress_val)
    st.sidebar.write(f"Progres {rater_name}: {len(set(rated_ids))} / {len(df)}")
    
    # Download Button
    csv = st.session_state.results.to_csv(index=False)
    b64 = base64.b64encode(csv.encode()).decode()
    href = f'<a href="data:file/csv;base64,{b64}" download="sme_ratings_{rater_name.replace(" ", "_")}.csv">Unduh hasil CSV</a>'
    st.sidebar.markdown(href, unsafe_allow_html=True)
    
    if len(df) == 0:
        st.warning("Data kosong.")
        return
        
    # Navigation UI
    col_prev, col_idx, col_next = st.columns([1, 2, 1])
    with col_prev:
        if st.button("⬅️ Sebelumnya", use_container_width=True) and st.session_state.current_idx > 0:
            st.session_state.current_idx -= 1
            st.rerun()
            
    with col_idx:
        st.markdown(f"<h3 style='text-align: center; margin-top: 0;'>Kasus {st.session_state.current_idx + 1} dari {len(df)}</h3>", unsafe_allow_html=True)
        
    with col_next:
        if st.button("Selanjutnya ➡️", use_container_width=True) and st.session_state.current_idx < len(df) - 1:
            st.session_state.current_idx += 1
            st.rerun()

    # Current Row Data
    row = df.loc[st.session_state.current_idx]
    review_id = row['review_id']
    
    # Check existing rating
    existing_rating = st.session_state.results[
        (st.session_state.results['rater'] == rater_name) & 
        (st.session_state.results['review_id'] == review_id)
    ]
    
    is_rated = not existing_rating.empty
    if is_rated:
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
    
    # Pre-fill defaults
    def_rel = get_index_from_val(existing_rating['relevance_rating'].iloc[0]) if is_rated else 1
    def_lev = get_index_from_val(existing_rating['level_fit_rating'].iloc[0]) if is_rated else 1
    def_lan = get_index_from_val(existing_rating['language_fit_rating'].iloc[0]) if is_rated else 1
    def_bus = get_index_from_val(existing_rating['business_fit_rating'].iloc[0]) if is_rated else 1
    def_act = get_index_from_val(existing_rating['actionable_rating'].iloc[0]) if is_rated else 1
    def_notes = str(existing_rating['feedback_notes'].iloc[0]) if is_rated and not pd.isna(existing_rating['feedback_notes'].iloc[0]) else ""
    
    with st.form("rating_form"):
        options = ["2 - Agree", "1 - Partially Agree", "0 - Disagree"]
        
        rating_rel = st.radio(
            "Tingkat relevansi (Relevance):", options=options, index=def_rel,
            help="Sejauh mana materi inti kursus relevan dengan kompetensi dan tanggung jawab pada profil pekerjaan target."
        )
        rating_lev = st.radio(
            "Kesesuaian level jabatan (Level Fit):", options=options, index=def_lev,
            help="Kesesuaian tingkat kesulitan kursus (mis. Dasar/Menengah/Mahir) dengan tingkatan atau senioritas jabatan."
        )
        rating_lan = st.radio(
            "Kesesuaian bahasa (Language Fit):", options=options, index=def_lan,
            help="Kesesuaian bahasa pengantar kursus dengan konteks geografi atau tuntutan bahasa pada pekerjaan tersebut."
        )
        rating_bus = st.radio(
            "Kesesuaian konteks bisnis (Business Fit):", options=options, index=def_bus,
            help="Seberapa cocok studi kasus atau pendekatan kursus dengan fungsi spesifik, industri, atau budaya departemen target."
        )
        rating_act = st.radio(
            "Tingkat kemudahan aplikasi (Actionable):", options=options, index=def_act,
            help="Seberapa praktis/aplikatif materi tersebut untuk langsung dipraktikkan dalam pekerjaan sehari-hari (bukan sekadar teori konseptual)."
        )
        
        notes = st.text_area("Catatan opsional:", value=def_notes)
        
        submitted = st.form_submit_button("Simpan Penilaian")
        
        if submitted:
            # Remove old rating to prevent duplicates
            st.session_state.results = st.session_state.results[
                ~((st.session_state.results['rater'] == rater_name) & (st.session_state.results['review_id'] == review_id))
            ]
            
            new_row = {
                'review_id': review_id,
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
            
            # Auto advance
            if st.session_state.current_idx < len(df) - 1:
                st.session_state.current_idx += 1
            st.rerun()

if __name__ == "__main__":
    main()
