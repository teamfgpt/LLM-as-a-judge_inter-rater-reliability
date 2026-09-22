# Session Summary: 2026-09-22 (Phase 3 & Master Plan)

## 1. Phase 3 Results: Alternative Base Models
We successfully evaluated the specialized models on the Indonesian holdout test set to see if a different architecture could bridge the language and data gap without overfitting.

**Test Set QWK Scores:**
- **Prometheus-2-7B (P3-A):** `0.492`
- **SeaLLM-v3-7B-Chat (P3-B):** `0.417`

**Conclusion:** Both models performed significantly worse than our baselines. They suffered from the exact same structural issue: the validation set (8 signals) is too small, causing the models to overfit rapidly and fail to generalize on the test set.

🏆 **Final Best Models:**
- English: **`Mistral-7B-Instruct-v0.3-EN`** (3 epochs) -> **0.699 QWK**
- Indonesian: **`Llama-3.1-8B-Instruct-ID`** (3 epochs) -> **0.622 QWK**

## 2. Third-Party API Proxy Testing (AgentRouter)
We attempted to test `deepseek-v4-flash` using a third-party proxy (`agentrouter.org`). 
- **Result:** Failed. The provider's aggressive Web Application Firewall (WAF) actively blocked our automated evaluation scripts, returning `400 content-blocked` and ultimately `401 unauthorized client detected`. 
- **Decision:** Ignored. We will stick to our local best models which we fully control.

## 3. The "Master Plan": Active Learning (Bootstrapping)
To break through the "data starvation" ceiling (currently only 49 training signals), we have agreed on a brilliant 4-step pipeline:

1. **AI-Assisted Sampling (Phase 2):** 
   - Extract a subset of unlabeled rows that represent a diverse mix of all missing signals.
   - Run our best fine-tuned models (Mistral for EN, Llama3.1 for ID) to predict the labels and generate rationales.
   - Export this into a fresh Excel sheet (`SME_SAMPLING_SHEET_PHASE2.xlsx`).
2. **Human Review (SMEs):** 
   - The interraters review the AI-generated spreadsheet. Because it is pre-filled, they only need to approve or correct the labels, which drastically reduces their workload and speeds up data collection.
3. **Retrain (Final Model):** 
   - Combine the original seed dataset with this newly verified Phase 2 data.
   - Retrain the models. With a larger, highly representative dataset, the structural overfitting issue will be resolved, and the models will become highly accurate and stable.
4. **Mass Inference:** 
   - Deploy the retrained, production-ready models to automatically label the remaining tens of thousands of rows in the pipeline without human intervention.

**Next Steps for the Next Session:**
- Write the script to sample the unlabeled data and generate `SME_SAMPLING_SHEET_PHASE2.xlsx`.

**Update (End of Session):**
- We extracted **1,000 completely diverse rows** representing 1,000 distinct `competency_signal_id` values from the main pool (`job_context_candidate_review_pool.csv`).
- We ran `Llama-3.1-8B-Instruct-ID` on this subset to generate predicted labels and rationales.
- The output was saved as `SME_SAMPLING_SHEET_PHASE2_DIVERSE.xlsx` and is now ready for SME review.

**Update (Web App Creation):**
- Built a Streamlit web app (`sme_web_app`) to allow 2 SMEs to easily rate the 1,000 diverse samples using a (2=Agree, 1=Partially Agree, 0=Disagree) scale.
- If QWK indicates high agreement and validity, the final tuned AI will execute the **Mass Inference** on the entire 366k+ pipeline dataset, cementing the data foundation for the dissertation.
