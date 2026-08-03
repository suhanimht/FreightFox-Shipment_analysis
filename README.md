# FreightFox-Shipment_analysis
# Shipment Delivery Performance Analytics

An end-to-end analytics project on a 5,000-record freight shipment dataset — from raw data audit to a deployed interactive dashboard — answering 5 core operations questions for the business.

**Live app:** _add your deployed Streamlit URL here_ https://freightfox-shipmentanalysis-5bgas3emhjwuxx2xh6ukeh.streamlit.app/ 
**Written answers:** [BUSINESS_ANSWERS.md](./BUSINESS_ANSWERS.md)

---

## Tools & Frameworks

| Layer | Tool |
|---|---|
| Data cleaning & analysis | Python, Pandas, NumPy |
| Statistical validation | SciPy (Chi-square, ANOVA, Kruskal-Wallis, regression) |
| Exploratory analysis | Jupyter Notebook, Plotly |
| Dashboard | Streamlit |
| Visualization | Plotly Express / Graph Objects |
| Version control & deployment | Git, GitHub, Streamlit Community Cloud |

---

## Project Methodology
Phase 0 — Project Setup
Phase 1 — Understand Dataset → Data Quality Audit → Data Cleaning
Phase 2 — Exploratory Data Analysis → Feature Engineering
Phase 3 — Business Question 1 → 2 → 3 → 4 → 5
Phase 4 — Extra Analysis
Phase 5 — Build Dashboard
Phase 6 — Deploy → GitHub → Executive Summary

---

### Phase 0 — Project Setup
Set up a local Python virtual environment and repo structure before touching the data, so cleaning, analysis, and dashboard code stay reproducible from day one.

### Phase 1 — Understand, Audit, Clean
- **Understand dataset:** Reviewed all 15 raw columns, data types, and shipment lifecycle logic (booking → pickup → delivery) before any cleaning, to avoid fixing things that weren't actually broken.
- **Data quality audit:** Checked missing values, duplicates, invalid chronology, outliers, and — critically — whether the `status` column could be trusted as an on-time indicator. It couldn't (65% accuracy vs. calculated SLA outcome), which shaped every downstream decision.
- **Data cleaning:** Removed 15 exact duplicates. Converted all date columns to datetime. **Did not impute** missing booking/pickup/delivery dates — they represent real business events, not data entry errors — and flagged them instead. Preserved freight cost outliers after confirming they reflected a real carrier pricing pattern, not noise. Decision principle throughout: *preserve original records, flag uncertainty, never fabricate.*

### Phase 2 — EDA & Feature Engineering
- **EDA:** Explored distributions, correlations, and category-level splits (region, carrier, customer, mode) to form hypotheses before jumping to the business questions — avoided naming a "worst performer" prematurely.
- **Feature engineering:** Derived `delivery_performance` (On Time / Late) independently from `promised_delivery_date` vs `actual_delivery_date`, since the raw `status` field measures operational lifecycle, not SLA outcome. Also created `analysis_ready` flag so SLA analyses only use the 3,444 shipments with valid, complete delivery data, while volume/pricing analyses still use the full 5,000.

### Phase 3 — Business Questions
Each question followed the same evidence chain: descriptive stats → visualization → statistical test → business interpretation. No conclusion was drawn from a single chart or ranking alone.
1. **Regional performance:** Central lowest, South highest — but the gap is small and not statistically significant (χ² p = 0.757). Carrier-level differences within regions are far larger than between them.
2. **Freight cost vs distance:** Weak overall fit (R²=0.09) traced to one carrier's (CARR_07) systematically inflated pricing; excluding it lifts R² to 0.54.
3. **Customer delays:** Some customers look worse descriptively, but ANOVA/Kruskal-Wallis found no statistically significant customer effect — delays are shipment-level, not customer-level.
4. **Data quality:** Documented every issue and the reasoning for preserving vs. flagging vs. removing (full table in BUSINESS_ANSWERS.md).
5. **Weekly KPI:** Recommended Weekly SLA Compliance Rate, paired with a Data Completeness Rate as a trust gate on the primary metric.

### Phase 4 — Extra Analysis
Additional cuts (distance bands, transport mode, time trends) run to stress-test the Phase 3 conclusions rather than take them at face value — e.g. confirming regional performance holds even when segmented by shipment distance.

### Phase 5 — Build Dashboard
Built a single-file Streamlit app that recomputes every statistic live from `shipments_cleaned.csv` rather than hardcoding numbers, so sidebar filters (region/carrier/mode/date) stay consistent across all six tabs. Chose Streamlit over a no-code builder for full control over the statistical tests shown alongside each chart — the assignment asked for reasoning, not just visuals.

### Phase 6 — Deploy, GitHub, Executive Summary
Deployed on Streamlit Community Cloud (fastest free option with GitHub-native CI). Repo structured with a public GitHub history and full documentation. Executive Summary tab added to the dashboard itself as a one-glance entry point for a non-technical stakeholder.

---

## Setup — Run Locally

```bash
git clone https://github.com/suhanimht/FreightFox-Shipment_analysis.git
cd FreightFox-Shipment_analysis
python -m venv .venv
source .venv/Scripts/activate      # Windows Git Bash
pip install -r Dashboard/requirements.txt
streamlit run Dashboard/app.py
```
App opens at `http://localhost:8501`.

## Deploy (Streamlit Community Cloud)

1. Push repo to GitHub (public).
2. [share.streamlit.io](https://share.streamlit.io) → **New app** → select repo/branch.
3. Main file path: `Dashboard/app.py`
4. Deploy — no secrets or database required, app reads the local CSV directly.
