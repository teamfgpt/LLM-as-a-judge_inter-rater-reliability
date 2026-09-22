import pandas as pd
from pathlib import Path

def main():
    tuning_dir = Path(__file__).parent
    
    scored_csv = tuning_dir / "phase2_diverse_scored.csv"
    if not scored_csv.exists():
        print("Scored CSV not found. Wait for inference to finish.")
        return
        
    df = pd.read_csv(scored_csv)
    
    # We want to put the AI predictions into the actual columns
    df['relevance_label'] = df['pred_relevance_label']
    df['level_fit'] = df['pred_level_fit']
    df['language_fit'] = df['pred_language_fit']
    df['business_fit'] = df['pred_business_fit']
    df['actionable'] = df['pred_actionable']
    df['review_notes'] = df['pred_rationale']  # AI rationale
    
    # Remove the pred_ columns to clean up
    cols_to_drop = [c for c in df.columns if c.startswith('pred_')]
    df.drop(columns=cols_to_drop, inplace=True)
    
    out_path = tuning_dir / "SME_SAMPLING_SHEET_PHASE2_DIVERSE.xlsx"
    df.to_excel(out_path, index=False)
    print(f"Successfully generated {out_path} for SME Review.")

if __name__ == "__main__":
    main()
