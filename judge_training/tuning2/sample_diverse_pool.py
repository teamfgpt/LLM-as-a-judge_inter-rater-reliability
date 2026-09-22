import pandas as pd
from pathlib import Path
import random

def main():
    pool_path = "/home/spirit2026/Documents/Bu-Ruktin/02_Redesign_AI-ML_pipeline/deep-research/experiment10_job_contextual_upload_20260724/9_hasil-run_codex/10_job_contextual_pipeline/evaluation_labeled/job_context_candidate_review_pool.csv"
    print(f"Loading {pool_path}...")
    df = pd.read_csv(pool_path, low_memory=False)
    
    # We want unlabeled rows
    unlabeled_df = df[df['relevance_label'].isna()].copy()
    print(f"Found {len(unlabeled_df)} unlabeled rows in the review pool.")
    
    # Sample a diverse mix of missing signals for exactly 1000 rows.
    # Group by 'competency_signal_id'
    groups = list(unlabeled_df.groupby('competency_signal_id'))
    random.seed(42)
    random.shuffle(groups)
    
    sampled_rows = []
    for _, group in groups:
        # Take 1 sample per signal to maximize signal diversity
        sampled_rows.append(group.sample(1, random_state=42))
        if len(sampled_rows) >= 1000:
            break
            
    sampled_df = pd.concat(sampled_rows)
    print(f"Sampled {len(sampled_df)} diverse rows across {sampled_df['competency_signal_id'].nunique()} distinct signals.")
    
    # Add the 'part' column for language (Assuming mostly ID, we set to 'A_TopUp')
    sampled_df['part'] = 'A_TopUp' 
    
    tuning_dir = Path(__file__).parent
    sampled_df.to_csv(tuning_dir / "phase2_diverse_sample.csv", index=False)
    print("Saved 1000 diverse samples to phase2_diverse_sample.csv")

if __name__ == "__main__":
    main()
