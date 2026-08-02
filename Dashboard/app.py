"""
Shipment Delivery Performance Analytics Dashboard
FreightFox Take-Home Assignment

Data source of truth: data/shipments_cleaned.csv
All metrics reproduce the logic documented in the EDA notebook /
project documentation (analysis_ready flag, delivery_performance field,
carrier residual analysis, weekly SLA KPI, etc.)
"""

import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
from scipy import stats

# ----------------------------------------------------------------------
# PAGE CONFIG
# ----------------------------------------------------------------------
st.set_page_config(
    page_title="Shipment Delivery Performance Analytics",
    page_icon="🚚",
    layout="wide",
    initial_sidebar_state="expanded",
)

PRIMARY = "#1F4E79"
ACCENT = "#2E86AB"
GOOD = "#2E7D32"
BAD = "#C62828"
NEUTRAL = "#757575"

px.defaults.color_discrete_sequence = px.colors.qualitative.Bold


# ----------------------------------------------------------------------
# DATA LOADING
# ----------------------------------------------------------------------
@st.cache_data
def load_data(path="data/shipments_cleaned.csv"):
    df = pd.read_csv(path)

    date_cols = [
        "booking_date", "pickup_date", "delivery_date",
        "promised_delivery_date", "actual_delivery_date",
    ]
    for c in date_cols:
        df[c] = pd.to_datetime(df[c], errors="coerce")

    bool_cols = [
        "missing_booking_date", "missing_pickup_date",
        "missing_actual_delivery", "invalid_date_sequence", "analysis_ready",
    ]
    for c in bool_cols:
        df[c] = df[c].astype(bool)

    return df


df = load_data()

# ----------------------------------------------------------------------
# SIDEBAR — GLOBAL FILTERS
# ----------------------------------------------------------------------
st.sidebar.markdown("## 🚚 Filters")

regions = sorted(df["region"].dropna().unique())
carriers = sorted(df["carrier_id"].dropna().unique())
modes = sorted(df["mode"].dropna().unique())

sel_regions = st.sidebar.multiselect("Region", regions, default=regions)
sel_carriers = st.sidebar.multiselect("Carrier", carriers, default=carriers)
sel_modes = st.sidebar.multiselect("Mode", modes, default=modes)

min_d, max_d = df["booking_date"].min(), df["booking_date"].max()
date_range = st.sidebar.date_input(
    "Booking date range", value=(min_d.date(), max_d.date()),
    min_value=min_d.date(), max_value=max_d.date(),
)

st.sidebar.markdown("---")
st.sidebar.caption(
    "Built on the cleaned, analytics-ready shipment dataset "
    "(5,000 shipments, 28 columns). SLA metrics use the derived "
    "`delivery_performance` field, not the raw operational `status` "
    "field — see Data Quality tab for why."
)

mask = (
    df["region"].isin(sel_regions)
    & df["carrier_id"].isin(sel_carriers)
    & df["mode"].isin(sel_modes)
)
if len(date_range) == 2:
    start, end = pd.to_datetime(date_range[0]), pd.to_datetime(date_range[1])
    mask &= df["booking_date"].between(start, end)

fdf = df[mask].copy()               # filtered, full (operational) dataset
ready = fdf[fdf["analysis_ready"]].copy()   # filtered, SLA-eligible dataset

if fdf.empty:
    st.warning("No shipments match the current filters. Adjust filters in the sidebar.")
    st.stop()

# ----------------------------------------------------------------------
# HEADER
# ----------------------------------------------------------------------
st.markdown(
    f"<h1 style='color:{PRIMARY}; margin-bottom:0;'>Shipment Delivery Performance Analytics</h1>"
    f"<p style='color:{NEUTRAL}; margin-top:4px;'>Answers to the 5 operational business questions, "
    f"backed by the cleaned dataset and statistical validation.</p>",
    unsafe_allow_html=True,
)

tabs = st.tabs([
    "📊 Executive Summary",
    "🌍 Q1 · Regional Performance",
    "💰 Q2 · Freight Cost vs Distance",
    "👥 Q3 · Customer Delays",
    "🧹 Q4 · Data Quality",
    "📈 Q5 · Weekly Monitoring KPI",
])

# ========================================================================
# TAB 0 — EXECUTIVE SUMMARY
# ========================================================================
with tabs[0]:
    st.subheader("Executive Summary")

    total_shipments = len(fdf)
    analysis_ready_n = len(ready)
    analysis_ready_pct = analysis_ready_n / total_shipments * 100 if total_shipments else 0
    on_time_rate = (ready["on_time_flag"] == 1).mean() * 100 if len(ready) else np.nan
    avg_delay = ready["delivery_delay_days"].mean() if len(ready) else np.nan
    avg_transit = ready["transit_days"].mean() if len(ready) else np.nan
    avg_freight = fdf["freight_cost"].mean()
    n_carriers = fdf["carrier_id"].nunique()
    n_customers = fdf["customer_id"].nunique()

    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Total Shipments", f"{total_shipments:,}")
    c2.metric("Analysis-Ready", f"{analysis_ready_n:,}", f"{analysis_ready_pct:.1f}% of total")
    c3.metric("On-Time Rate", f"{on_time_rate:.1f}%" if not np.isnan(on_time_rate) else "n/a")
    c4.metric("Avg Delivery Delay", f"{avg_delay:+.2f} days" if not np.isnan(avg_delay) else "n/a")

    c5, c6, c7, c8 = st.columns(4)
    c5.metric("Avg Transit Time", f"{avg_transit:.1f} days" if not np.isnan(avg_transit) else "n/a")
    c6.metric("Avg Freight Cost", f"₹{avg_freight:,.0f}")
    c7.metric("Carriers", f"{n_carriers}")
    c8.metric("Customers", f"{n_customers}")

    st.markdown("---")
    colL, colR = st.columns(2)

    with colL:
        st.markdown("**Delivery Performance Mix (analysis-ready shipments)**")
        perf_counts = ready["delivery_performance"].value_counts().reset_index()
        perf_counts.columns = ["delivery_performance", "count"]
        fig = px.pie(perf_counts, names="delivery_performance", values="count", hole=0.45,
                     color="delivery_performance",
                     color_discrete_map={"On Time": GOOD, "Late": BAD})
        fig.update_layout(margin=dict(t=10, b=10, l=10, r=10))
        st.plotly_chart(fig, use_container_width=True)

    with colR:
        st.markdown("**Operational Status (full dataset)**")
        status_counts = fdf["status"].value_counts().reset_index()
        status_counts.columns = ["status", "count"]
        fig = px.bar(status_counts, x="status", y="count", color="status", text="count")
        fig.update_layout(showlegend=False, margin=dict(t=10, b=10, l=10, r=10))
        st.plotly_chart(fig, use_container_width=True)

    st.info(
        "**Headline takeaways** — Regional differences in on-time performance are small and "
        "statistically insignificant (χ² p = 0.757); carrier-level differences are the dominant "
        "driver. One carrier, **CARR_07**, prices ~6× above the network norm for comparable "
        "distances. Customer-level delay differences are not statistically significant "
        "(ANOVA p = 0.737) — delays are shipment-level, not customer-level, phenomena. "
        "See each tab for full evidence."
    )

# ========================================================================
# TAB 1 — BUSINESS QUESTION 1: REGIONAL PERFORMANCE
# ========================================================================
with tabs[1]:
    st.subheader("Q1 · Which region has the worst on-time delivery performance, and what's driving it?")

    reg_summary = (
        ready.groupby("region")
        .agg(shipments=("shipment_id", "count"),
             on_time_rate=("on_time_flag", "mean"),
             avg_delay=("delivery_delay_days", "mean"))
        .reset_index()
    )
    reg_summary["on_time_rate"] *= 100
    reg_summary = reg_summary.sort_values("on_time_rate")

    c1, c2 = st.columns([1.3, 1])
    with c1:
        st.markdown("**On-Time Rate by Region (95% CI)**")
        cis = []
        for _, row in reg_summary.iterrows():
            n = row["shipments"]
            p = row["on_time_rate"] / 100
            se = np.sqrt(p * (1 - p) / n) if n > 0 else 0
            cis.append(1.96 * se * 100)
        reg_summary["ci"] = cis

        fig = go.Figure()
        fig.add_bar(x=reg_summary["region"], y=reg_summary["on_time_rate"],
                     error_y=dict(type="data", array=reg_summary["ci"]),
                     marker_color=PRIMARY, text=reg_summary["on_time_rate"].round(1))
        fig.add_hline(y=(ready["on_time_flag"] == 1).mean() * 100, line_dash="dash",
                       annotation_text="National Avg", line_color=NEUTRAL)
        fig.update_layout(yaxis_title="On-Time Rate (%)", margin=dict(t=10))
        st.plotly_chart(fig, use_container_width=True)

    with c2:
        st.markdown("**Regional Summary Table**")
        show = reg_summary[["region", "shipments", "on_time_rate", "avg_delay"]].copy()
        show.columns = ["Region", "Analysis-Ready Shipments", "On-Time Rate (%)", "Avg Delay (days)"]
        st.dataframe(show.round(2), use_container_width=True, hide_index=True)

        # Chi-square test region vs on_time_flag
        ct = pd.crosstab(ready["region"], ready["on_time_flag"])
        if ct.shape[0] > 1 and ct.shape[1] > 1:
            chi2, p, dof, _ = stats.chi2_contingency(ct)
            st.metric("Chi-square p-value", f"{p:.3f}",
                       "No significant association" if p > 0.05 else "Significant association")

    st.markdown("**On-Time Rate by Region × Distance Band**")
    heat = ready.pivot_table(index="region", columns="distance_band",
                              values="on_time_flag", aggfunc="mean") * 100
    fig = px.imshow(heat, text_auto=".1f", color_continuous_scale="RdYlGn", aspect="auto")
    fig.update_layout(margin=dict(t=10))
    st.plotly_chart(fig, use_container_width=True)

    st.markdown("**Carrier On-Time Rate vs National Average, by Region**")
    carrier_reg = (
        ready.groupby(["region", "carrier_id"])
        .agg(on_time_rate=("on_time_flag", "mean"), n=("shipment_id", "count"))
        .reset_index()
    )
    carrier_reg["on_time_rate"] *= 100
    national = (ready["on_time_flag"] == 1).mean() * 100
    carrier_reg["above_national"] = np.where(carrier_reg["on_time_rate"] >= national, "Above", "Below")
    fig = px.bar(carrier_reg, x="carrier_id", y="on_time_rate", color="above_national",
                 facet_col="region", facet_col_wrap=3,
                 color_discrete_map={"Above": GOOD, "Below": BAD}, height=650)
    fig.add_hline(y=national, line_dash="dash", line_color="black")
    fig.update_xaxes(matches=None, tickangle=45)
    fig.update_layout(margin=dict(t=40))
    st.plotly_chart(fig, use_container_width=True)

    st.success(
        "**Conclusion:** Region is *not* the primary driver of delivery performance. The best "
        "(South/West) and worst (Central) regions differ by under ~4 points, confidence intervals "
        "overlap substantially, and the chi-square test found no significant association "
        "(p = 0.757). South's apparent volatility reflects its small analysis-ready sample "
        "(124 shipments) — a data quality gap, not a real effect — and is excluded from "
        "comparative conclusions. Carrier-level gaps within each region (often 15–20 points) are "
        "far larger than regional gaps, pointing to **carrier execution**, not geography, as the "
        "actionable lever."
    )

# ========================================================================
# TAB 2 — BUSINESS QUESTION 2: FREIGHT COST VS DISTANCE
# ========================================================================
with tabs[2]:
    st.subheader("Q2 · Is there a relationship between freight cost and distance? Which carrier(s) deviate, and by how much?")

    pearson_r, pearson_p = stats.pearsonr(fdf["distance_km"], fdf["freight_cost"])
    spearman_r, spearman_p = stats.spearmanr(fdf["distance_km"], fdf["freight_cost"])

    c1, c2, c3 = st.columns(3)
    c1.metric("Pearson r (linear)", f"{pearson_r:.2f}")
    c2.metric("Spearman ρ (monotonic)", f"{spearman_r:.2f}")

    # Regression: full data vs excluding worst-deviation carrier
    slope, intercept, r_value, _, _ = stats.linregress(fdf["distance_km"], fdf["freight_cost"])
    r2_full = r_value ** 2
    c3.metric("Regression R² (all carriers)", f"{r2_full:.2f}")

    st.markdown("**Freight Cost vs Distance** (color = carrier)")
    fig = px.scatter(fdf, x="distance_km", y="freight_cost", color="carrier_id",
                      opacity=0.55, trendline="ols", trendline_scope="overall",
                      labels={"distance_km": "Distance (km)", "freight_cost": "Freight Cost"})
    fig.update_layout(margin=dict(t=10))
    st.plotly_chart(fig, use_container_width=True)

    # Carrier residual analysis
    fdf["expected_freight"] = intercept + slope * fdf["distance_km"]
    fdf["residual"] = fdf["freight_cost"] - fdf["expected_freight"]

    carrier_profile = (
        fdf.groupby("carrier_id")
        .agg(shipments=("shipment_id", "count"),
             avg_distance=("distance_km", "mean"),
             avg_freight=("freight_cost", "mean"),
             avg_cost_per_km=("cost_per_km", "mean"),
             avg_residual=("residual", "mean"))
        .reset_index()
        .sort_values("avg_cost_per_km", ascending=False)
    )

    worst_carrier = carrier_profile.iloc[0]["carrier_id"]

    colL, colR = st.columns(2)
    with colL:
        st.markdown("**Avg Cost per KM by Carrier**")
        fig = px.bar(carrier_profile, x="carrier_id", y="avg_cost_per_km",
                     color="avg_cost_per_km", color_continuous_scale="Reds")
        fig.update_layout(margin=dict(t=10), coloraxis_showscale=False)
        st.plotly_chart(fig, use_container_width=True)
    with colR:
        st.markdown("**Avg Freight Residual (Actual − Expected) by Carrier**")
        fig = px.bar(carrier_profile, x="carrier_id", y="avg_residual",
                     color="avg_residual", color_continuous_scale="RdYlGn_r")
        fig.update_layout(margin=dict(t=10), coloraxis_showscale=False)
        st.plotly_chart(fig, use_container_width=True)

    # Outlier share by carrier (IQR method on freight_cost)
    q1, q3 = fdf["freight_cost"].quantile([0.25, 0.75])
    iqr = q3 - q1
    upper = q3 + 1.5 * iqr
    fdf["is_outlier"] = fdf["freight_cost"] > upper
    outlier_share = fdf[fdf["is_outlier"]]["carrier_id"].value_counts(normalize=True) * 100
    outlier_rate_within = fdf.groupby("carrier_id")["is_outlier"].mean() * 100

    st.markdown(f"**Outlier concentration** — carrier **{worst_carrier}** stands out as the "
                f"clearest pricing anomaly (highest avg cost/km & residual).")
    oc1, oc2 = st.columns(2)
    with oc1:
        st.metric(f"Share of all freight outliers from {worst_carrier}",
                   f"{outlier_share.get(worst_carrier, 0):.1f}%")
    with oc2:
        st.metric(f"% of {worst_carrier}'s own shipments that are outliers",
                   f"{outlier_rate_within.get(worst_carrier, 0):.1f}%")

    # Robustness: regression excluding worst carrier
    rest = fdf[fdf["carrier_id"] != worst_carrier]
    slope_r, intercept_r, r_value_r, _, _ = stats.linregress(rest["distance_km"], rest["freight_cost"])
    r2_excl = r_value_r ** 2
    st.metric(f"Regression R² excluding {worst_carrier}", f"{r2_excl:.2f}",
               f"+{(r2_excl - r2_full):.2f} vs full model")

    st.dataframe(carrier_profile.round(2), use_container_width=True, hide_index=True)

    st.success(
        f"**Conclusion:** Distance is positively related to freight cost (Spearman ρ = {spearman_r:.2f}), "
        f"but distance alone explains little variance (R² = {r2_full:.2f}) because of one carrier's "
        f"pricing behavior. **{worst_carrier}** charges far above the network norm for comparable "
        f"distances — its shipments account for the large majority of freight-cost outliers, and "
        f"removing it from the regression raises R² substantially "
        f"(from {r2_full:.2f} to {r2_excl:.2f}). This is a systematic pricing pattern, not a handful "
        f"of extreme shipments — worth a commercial review (premium service vs. mispricing)."
    )

# ========================================================================
# TAB 3 — BUSINESS QUESTION 3: CUSTOMER DELAYS
# ========================================================================
with tabs[3]:
    st.subheader("Q3 · Which customers experience the most delivery delays — carrier, region, or something else driven?")

    cust_summary = (
        ready.groupby("customer_id")
        .agg(shipments=("shipment_id", "count"),
             avg_delay=("delivery_delay_days", "mean"),
             on_time_rate=("on_time_flag", "mean"))
        .reset_index()
    )
    cust_summary["on_time_rate"] *= 100
    cust_summary["late_rate"] = 100 - cust_summary["on_time_rate"]
    top_delayed = cust_summary.sort_values("avg_delay", ascending=False).head(15)

    c1, c2 = st.columns([1.4, 1])
    with c1:
        st.markdown("**Top 15 Customers by Average Delivery Delay**")
        fig = px.bar(top_delayed, x="customer_id", y="avg_delay",
                     color="avg_delay", color_continuous_scale="Reds",
                     hover_data=["shipments", "on_time_rate"])
        fig.update_layout(margin=dict(t=10), coloraxis_showscale=False, xaxis_tickangle=45)
        st.plotly_chart(fig, use_container_width=True)
    with c2:
        st.markdown("**Volume vs Avg Delay**")
        fig = px.scatter(cust_summary, x="shipments", y="avg_delay",
                          hover_name="customer_id", opacity=0.6,
                          labels={"shipments": "# Shipments", "avg_delay": "Avg Delay (days)"})
        fig.update_layout(margin=dict(t=10))
        st.plotly_chart(fig, use_container_width=True)

    st.caption("Delay differences are not explained by shipment volume — high- and low-delay "
               "customers span the same volume range.")

    focus_customers = top_delayed["customer_id"].head(6).tolist()
    st.markdown(f"**Operational profile of top-delayed customers vs carrier & region**")
    sub = ready[ready["customer_id"].isin(focus_customers)]
    colA, colB = st.columns(2)
    with colA:
        ct = pd.crosstab(sub["customer_id"], sub["carrier_id"])
        fig = px.imshow(ct, aspect="auto", color_continuous_scale="Blues",
                          labels=dict(color="Shipments"))
        fig.update_layout(margin=dict(t=10), title="Customer × Carrier")
        st.plotly_chart(fig, use_container_width=True)
    with colB:
        ct2 = pd.crosstab(sub["customer_id"], sub["region"])
        fig = px.imshow(ct2, aspect="auto", color_continuous_scale="Purples",
                          labels=dict(color="Shipments"))
        fig.update_layout(margin=dict(t=10), title="Customer × Region")
        st.plotly_chart(fig, use_container_width=True)

    # Statistical validation: ANOVA / Kruskal on delay across customers (top N with enough volume)
    groups = [g["delivery_delay_days"].dropna().values
              for _, g in ready.groupby("customer_id") if len(g) >= 15]
    if len(groups) > 2:
        f_stat, p_anova = stats.f_oneway(*groups)
        h_stat, p_kw = stats.kruskal(*groups)
        c1, c2 = st.columns(2)
        c1.metric("One-Way ANOVA p-value", f"{p_anova:.3f}",
                   "Not significant" if p_anova > 0.05 else "Significant")
        c2.metric("Kruskal-Wallis p-value", f"{p_kw:.3f}",
                   "Not significant" if p_kw > 0.05 else "Significant")

    st.dataframe(
        top_delayed[["customer_id", "shipments", "avg_delay", "on_time_rate", "late_rate"]]
        .round(2).rename(columns={
            "customer_id": "Customer", "shipments": "Shipments",
            "avg_delay": "Avg Delay (days)", "on_time_rate": "On-Time Rate (%)",
            "late_rate": "Late Rate (%)"}),
        use_container_width=True, hide_index=True,
    )

    st.success(
        "**Conclusion:** A handful of customers show descriptively higher delays, but those "
        "shipments are spread across many carriers, regions, and modes with no dominant pattern — "
        "and formal testing (ANOVA / Kruskal-Wallis) finds customer identity is **not** a "
        "statistically or practically significant driver of delay. Delays are better explained "
        "at the shipment level (carrier execution, route, timing) than at the customer level, so "
        "customer-specific escalation is not the right lever; shipment-level operational "
        "monitoring is."
    )

# ========================================================================
# TAB 4 — BUSINESS QUESTION 4: DATA QUALITY
# ========================================================================
with tabs[4]:
    st.subheader("Q4 · Data quality issues found, and how they were handled")

    st.markdown("**Analysis-Ready Funnel**")
    raw_n = 5015
    dedup_n = 5000
    ready_n = int(df["analysis_ready"].sum())
    fig = go.Figure(go.Funnel(
        y=["Raw records", "After duplicate removal", "Analysis-ready (SLA-eligible)"],
        x=[raw_n, dedup_n, ready_n],
        marker={"color": [NEUTRAL, ACCENT, PRIMARY]},
    ))
    fig.update_layout(margin=dict(t=10))
    st.plotly_chart(fig, use_container_width=True)

    st.markdown("**Missing Values (raw dataset scope)**")
    miss_tbl = pd.DataFrame({
        "Field": ["booking_date", "pickup_date", "actual_delivery_date"],
        "Missing Count": [71, 87, 1482],
        "Missing %": [1.42, 1.74, 29.64],
        "Decision": ["Preserved + flagged", "Preserved + flagged", "Preserved (excluded from SLA analysis only)"],
    })
    st.dataframe(miss_tbl, use_container_width=True, hide_index=True)

    colL, colR = st.columns(2)
    with colL:
        st.markdown("**Data Quality Issue Log**")
        dq_tbl = pd.DataFrame({
            "Issue": ["Duplicate records", "Date fields stored as text",
                      "Invalid date chronology", "Freight cost outliers",
                      "Status ≠ SLA performance", "delivery_date vs actual_delivery_date mismatch"],
            "Count": ["15 rows", "5 columns", "74 shipments", "296 (5.9%)",
                       "1,742 mismatches", "Only 9% agreement"],
            "Handling": ["Removed", "Converted to datetime", "Flagged, excluded from time-based analysis",
                         "Retained (real pricing pattern)", "Derived new `delivery_performance` field",
                         "Used actual_delivery_date as ground truth"],
        })
        st.dataframe(dq_tbl, use_container_width=True, hide_index=True)

    with colR:
        st.markdown("**Operational Status vs Derived Delivery Performance**")
        ct = pd.crosstab(fdf["status"], fdf["delivery_performance"])
        fig = px.imshow(ct, text_auto=True, color_continuous_scale="Blues", aspect="auto")
        fig.update_layout(margin=dict(t=10))
        st.plotly_chart(fig, use_container_width=True)
        st.caption(
            "Shipments marked 'Delivered' were frequently late, and some marked 'Delayed' arrived "
            "on time — confirming `status` tracks operational lifecycle, not SLA outcome."
        )

    st.markdown("**Region-level analysis-ready coverage** (South is under-covered — treat its "
                "regional metrics cautiously)")
    cov = (
        df.groupby("region")
        .agg(total=("shipment_id", "count"), ready=("analysis_ready", "sum"))
        .reset_index()
    )
    cov["ready_pct"] = cov["ready"] / cov["total"] * 100
    fig = px.bar(cov, x="region", y="ready_pct", color="ready_pct",
                 color_continuous_scale="RdYlGn", text=cov["ready_pct"].round(1))
    fig.update_layout(margin=dict(t=10), coloraxis_showscale=False, yaxis_title="Analysis-Ready %")
    st.plotly_chart(fig, use_container_width=True)

    st.success(
        "**Conclusion:** The dataset is structurally sound but requires disciplined handling: "
        "15 exact duplicates were removed; missing operational dates were preserved and flagged "
        "rather than imputed; 74 shipments with impossible chronology were flagged and excluded "
        "only from time-based analyses; and — most importantly — the raw `status` field was found "
        "unreliable as an SLA indicator, motivating the derived `delivery_performance` field used "
        "throughout this dashboard. The South region's low analysis-ready coverage (~13%) means "
        "its metrics should be read as directional, not conclusive."
    )

# ========================================================================
# TAB 5 — BUSINESS QUESTION 5: WEEKLY MONITORING KPI
# ========================================================================
with tabs[5]:
    st.subheader("Q5 · What single metric should be tracked weekly to catch delivery problems early?")

    st.markdown("### Recommended KPI: **Weekly SLA Compliance Rate**")
    st.latex(r"\text{Weekly SLA Compliance Rate} = \frac{\text{On-Time Deliveries}}{\text{Completed Deliveries}}")

    weekly = ready.copy()
    weekly["week"] = weekly["promised_delivery_date"].dt.to_period("W").apply(lambda p: p.start_time)
    weekly_sla = (
        weekly.groupby("week")
        .agg(on_time_rate=("on_time_flag", "mean"), shipments=("shipment_id", "count"))
        .reset_index()
    )
    weekly_sla["on_time_rate"] *= 100

    # Completeness rate: analysis-ready share among Delivered/Delayed status shipments per week
    full_weekly = fdf.copy()
    full_weekly["week"] = full_weekly["promised_delivery_date"].dt.to_period("W").apply(lambda p: p.start_time)
    completeness = (
        full_weekly[full_weekly["status"].isin(["Delivered", "Delayed"])]
        .groupby("week")["analysis_ready"].mean().reset_index()
    )
    completeness["analysis_ready"] *= 100

    fig = go.Figure()
    fig.add_scatter(x=weekly_sla["week"], y=weekly_sla["on_time_rate"],
                     mode="lines+markers", name="Weekly SLA Compliance %", line=dict(color=PRIMARY, width=3))
    fig.add_hline(y=(ready["on_time_flag"] == 1).mean() * 100, line_dash="dash",
                   line_color=NEUTRAL, annotation_text="Overall Avg")
    fig.update_layout(margin=dict(t=10), yaxis_title="On-Time Rate (%)", xaxis_title="Week")
    st.plotly_chart(fig, use_container_width=True)

    st.markdown("**Supporting metric: Weekly Data Completeness Rate** (share of "
                "Delivered/Delayed shipments with a usable actual delivery date)")
    fig = px.bar(completeness, x="week", y="analysis_ready", color="analysis_ready",
                 color_continuous_scale="RdYlGn")
    fig.update_layout(margin=dict(t=10), yaxis_title="Completeness (%)", coloraxis_showscale=False)
    st.plotly_chart(fig, use_container_width=True)

    c1, c2 = st.columns(2)
    c1.metric("Weekly SLA volatility (std dev)", f"{weekly_sla['on_time_rate'].std():.1f} pts")
    c2.metric("Avg weekly shipment volume", f"{weekly_sla['shipments'].mean():.0f}")

    st.success(
        "**Conclusion:** Weekly SLA Compliance Rate is the single best early-warning metric — it "
        "uses the validated `delivery_performance` field (not the misleading `status` field), "
        "reacts fast enough to catch emerging problems (weekly variability is materially higher "
        "than monthly), and is simple enough for ops to act on immediately. It should always be "
        "read alongside **Weekly Data Completeness Rate**: if completeness drops, the SLA number "
        "itself becomes unreliable (as seen with the South region), so completeness acts as a "
        "trust gate on the primary KPI."
    )

st.markdown("---")
st.caption("Shipment Delivery Performance Analytics Dashboard · Built with Streamlit & Plotly · "
           "Data: shipments_cleaned.csv (5,000 shipments)")
