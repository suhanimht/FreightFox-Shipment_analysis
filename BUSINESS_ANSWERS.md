**Shipment Analytics Project**

_Dataset: shipments_cleaned.csv | 5,000 shipments, 28 columns_

*Note: For full in depth analysis report refer to the Project_Report in the Reports Folder that has all the methodology, visualization and statistical modelling.*

## Executive Summary

This phase answers the five business questions Ops asked for, using the analytics-ready dataset produced in Phase 1.

- Central is the region with the worst, most reliably-measured delivery performance: a 15.9% delay rate (vs. 14.1% national average) that persists across almost every carrier, pointing to a regional operating issue rather than one bad partner.
- Freight cost and distance are strongly linear once you control for shipment mode (r ≈ 0.98 within FTL/LTL/PTL) - but CARR_07 breaks that relationship completely, billing roughly 10× the per-km rate of every other carrier on identical lanes.
- Delay is concentrated in a small set of customers whose delay rate is far higher than their region/carrier mix would predict - led by CUST_066 at 40% (vs. an expected 14%) - meaning the driver is account-specific, not network-wide.
- The single biggest data-quality finding in this phase: South region is missing actual_delivery_date on 84.5% of Delivered/Delayed shipments, vs. 0% everywhere else - a regional tracking gap that makes South's on-time rate un-measurable until it's fixed.
- Recommended weekly metric: Weekly On-Time Delivery Rate, tracked alongside a Delivery-Data Completeness rate so a reporting gap is never mistaken for a performance win.

# Q1 - Which region has the worst on-time delivery performance, and what's driving it?

## Method

On-time performance was measured two ways to cross-check each other: (a) a date-based on_time_flag (actual_delivery_date vs. promised_delivery_date) restricted to analysis_ready rows, and (b) a status-based delay rate (Delayed ÷ \[Delivered + Delayed\]) using every shipment, which doesn't depend on actual_delivery_date being populated. The second method matters because, as Q4 details, actual_delivery_date is missing for 84.5% of Delivered/Delayed shipments in the South - so a date-based comparison alone would silently exclude most of that region and produce a misleading ranking.

**Answer:** Central has the numerically lowest on-time rate (48.3%), South the highest (52.4%) — but the gap is under 4 percentage points, confidence intervals across regions overlap heavily, and a chi-square test of region vs. on-time outcome found no significant association (χ² = 1.88, p = 0.757). Breaking performance down by distance band shows no region  consistently underperforms as shipments get longer, ruling out route mix as an explanation. What *does* separate shipments is carrier: within every region, on-time rates across carriers span 15–20+ percentage points — far more than the spread between regions.

**Caveat:** South's numbers are unstable — only 124 of its shipments are analysis-ready (a regional data-completeness issue, see Q4), so its rate should be read as directional only.

**Driving factor:** carrier execution, not geography.

**Finding:** Central has the worst delay rate at 15.9%, against a 14.1% national average. North is second at 15.0%. South cannot be reliably ranked - its 13.4% delay rate is computed on a badly incomplete slice of data (see chart: the red line shows the % of Delivered/Delayed shipments missing an actual delivery date by region).

| **Region** | **Delay rate (status-based)** | **On-time rate (date-based, analysis-ready only)** | **Sample reliability**               |
| ---------- | ----------------------------- | -------------------------------------------------- | ------------------------------------ |
| Central    | 15.9%                         | 48.3%                                              | Reliable - 84% of rows usable        |
| North      | 15.0%                         | 49.6%                                              | Reliable - 82% of rows usable        |
| West       | 13.8%                         | 51.3%                                              | Reliable - 81% of rows usable        |
| South      | 13.4%                         | 52.4%\*                                            | Unreliable - only 13% of rows usable |
| East       | 12.3%                         | 50.3%                                              | Reliable - 83% of rows usable        |

\*South's date-based on-time rate is shown for completeness but should not be trusted - it is computed on just 124 of 971 South shipments.

## What's driving Central's underperformance

The gap is not concentrated in one carrier or one shipping mode. Comparing each carrier's delay rate inside Central against that same carrier's national average delay rate shows the majority of carriers underperform their own national number when operating in Central (average gap: +1.75 percentage points), which points to a regional factor - hub congestion, last-mile infrastructure, or handling capacity - rather than a single underperforming partner.

**Why it matters:** Overall, the evidence suggests that carrier selection—not geographic region—is the dominant operational factor influencing delivery performance. Regional performance is broadly consistent across the network, whereas carrier-level differences provide far greater explanatory power and represent a more actionable opportunity for operational improvement.

**Next steps:** Investigate Central's hub/handling capacity and long-haul routing specifically (highest-delay segment); pull dock-level or handoff-level timestamps if available to isolate where within the Central network the delay accumulates; re-run this comparison after the South data-capture issue is fixed, since South may reveal itself to be worse once measurable.

# Q2 - Is there a relationship between freight cost and distance? Which carrier(s) deviate, and by how much?

## Method

A simple pooled correlation between freight_cost and distance_km across all 5,000 shipments returns a weak r = 0.30 (R² = 0.09) - but pooling hides the fact that FTL, LTL, and PTL have structurally different cost bases per km. Re-running the correlation within each mode shows a very different picture.

The relationship between freight cost and distance was first assessed using Pearson and Spearman correlation coefficients together with a simple linear regression model:
Freight Cost = β₀ + β₁ × Distance
Where:
β₀ = intercept (baseline freight cost)
β₁ = coefficient representing the change in freight cost for each unit increase in distance
Distance = shipment distance (independent variable)
Freight Cost = predicted freight cost (dependent variable)
where:
Expected Freight = Intercept + (Slope × Distance)
Residual = Actual Freight − Expected Freight
Residuals were then aggregated by carrier to determine whether carriers consistently priced shipments above or below the expected freight cost predicted by distance alone.
Finally, freight cost outliers were identified using the IQR rule, allowing the analysis to determine whether carrier-level pricing differences were caused by a few extreme shipments or reflected broader pricing behavior.

| **Segment**                  | **Correlation (r)** | **R²** | **Interpretation**                                                    |
| ---------------------------- | ------------------- | ------ | --------------------------------------------------------------------- |
| All shipments, pooled        | 0.30                | 0.09   | Weak - mode mix and one outlier carrier obscure the real relationship |
| FTL only                     | 0.985               | 0.97   | Near-perfect linear relationship                                      |
| LTL only                     | 0.985               | 0.97   | Near-perfect linear relationship                                      |
| PTL only                     | 0.984               | 0.97   | Near-perfect linear relationship                                      |
| All modes, excluding CARR_07 | 0.73                | 0.53   | Strong once the outlier carrier is removed                            |

**Finding:** Yes - freight cost is very tightly, linearly tied to distance within each shipment mode (r ≈ 0.98). The apparent weak overall relationship was an artifact of mixing three different cost structures and one carrier's pricing anomaly into a single scatter.

## Which carrier deviates - and by how much

CARR_07 is a clear, severe outlier. Its average cost per km is ₹159, against ₹16-17 for every other carrier - roughly 10× the market rate, and the gap holds consistently across every mode and every distance band (FTL: ₹249 vs. ₹25; LTL: ₹118 vs. ₹12; PTL: ₹79 vs. ₹8, all ≈10× multiples). All 342 of CARR_07's shipments (100%) fall above ₹56/km, while no other carrier's shipments approach that level.

- CARR_07's overall deviation from the fitted cost-distance line is +547% on average - over 5x the predicted cost for its distance.
- The ~10x multiplier is uniform across mode and distance band, which is more consistent with a systematic billing, currency, or unit-conversion error than a legitimate premium/express surcharge (a real premium tier would typically show more variation and a smaller, more defensible multiplier).
- Excluding CARR_07, every other carrier sits within a normal ±3% band of the fitted cost-distance line - no other carrier shows meaningful deviation.

**Why it matters:** At CARR_07's average freight cost of ₹206,161 versus a market-implied cost of roughly ₹20,600 for the same distance/mode mix, this represents a very large cost exposure across 342 shipments if the billed amounts are real and being paid as invoiced.

**Next steps:** Pull CARR_07's raw invoices and contract rate card to confirm whether ₹/km is being recorded in the wrong currency or unit, or whether this is a genuine (and probably renegotiable) premium-service contract; freeze further CARR_07 bookings pending that check given the scale of the gap.

# Q3 - Which customer(s) are experiencing the most delivery delays? Is that carrier-driven, region-driven, or something else?

## Method

Only analysis-ready shipments (completed deliveries with valid delivery dates and no invalid date sequences) were included to ensure delivery metrics were calculated consistently. The analysis followed a progressive drill-down approach:
Customer-level delivery performance summary (shipment volume, average delay, transit time, on-time and late rates).
Identification of high-delay customers using average delay and late rate rankings.
Operational drill-downs by carrier, region, transport mode, and distance band to investigate potential drivers.
Shipment-level operational profile and route sanity check for a representative high-delay customer.
Statistical validation using Levene's Test, One-Way ANOVA, Kruskal-Wallis Test, and effect size (ε²) to determine whether observed customer differences were statistically and practically meaningful.

**Finding:** Customer-level summaries initially identified several customers (including CUST_079, CUST_119, CUST_026, CUST_071, and CUST_116) with higher average delivery delays and late rates than the network average. However, all customers had comparable shipment volumes (18–44 shipments), indicating that rankings were not driven by extremely small sample sizes.
Successive operational drill-downs found no evidence that higher customer delays were consistently associated with a particular carrier, region, transport mode, or distance band. While individual combinations occasionally showed higher delays, these patterns were based on small shipment counts and did not remain consistent across operational segments.
A shipment-level review of CUST_119 further validated these findings. Despite above-average delays, shipments were distributed across multiple carriers, regions, transport modes, distance bands, and origin–destination pairs, with no dominant operational pattern or recurring shipment corridor explaining the customer's overall performance.

Several customers exhibited descriptively higher average delivery delays and late rates than the network average.
These differences were not explained by shipment volume, carrier allocation, geographic region, transport mode, shipment distance, or shipping corridor.
Shipment-level investigation of a representative high-delay customer (CUST_119) found no recurring operational pattern responsible for poorer performance.
Statistical testing confirmed that delivery delays do not differ significantly across customers.

**Is it carrier- or region-driven?:** No. shipments are spread across all 5 regions and no single carrier handles more than the other - the same pattern holds for the other flagged customers. If a carrier or region were the true cause, delay would concentrate there; instead it travels with the customer regardless of who ships it or where.

This points to something specific to the customer relationship or their shipment profile - e.g., delivery address complexity (rural/hard-to-access locations), consignee availability at drop-off, special handling requirements, or account-level SLA/documentation issues - rather than a network problem.

**Why it matters:** These 15 customers alone account for a disproportionate share of delayed shipments relative to their volume. Because the cause travels with the account rather than the carrier or lane, carrier renegotiation or regional fixes won't move these numbers - an account-level review is needed.

**Next steps:** Open a root-cause review with CUST_119 specifically (delivery address type, receiving-dock hours, special handling flags); check whether these accounts share a customer segment, product type, or delivery instruction pattern; consider a proactive SLA check-in for accounts running >2x the expected delay rate.

# Q4 - Before trusting any of the above, what data quality issues did you find, and how did you handle them?

The data quality assessment was conducted in two complementary phases:

Phase 1 – Initial Data Audit

A comprehensive audit of the raw dataset was performed to evaluate:
- Dataset structure
- Missing values
- Duplicate records
- Data types
- Invalid numeric values
- Text consistency
- Business rule validation
- Date chronology
- Outlier detection

Shipment status reliability

Phase 2 – Analytical Validation

As the business questions were investigated, additional quality checks were performed whenever unusual patterns emerged. This ensured that important operational issues hidden within aggregated statistics were identified before drawing business conclusions.

Throughout the project, the cleaning philosophy followed three principles:
- Preserve original business records whenever possible
- Create audit flags instead of modifying source data
- Exclude records only from analyses where they would produce invalid business metrics


## New finding: South region has a systemic delivery-confirmation gap

84.5% of Delivered/Delayed shipments in the South are missing actual_delivery_date, versus exactly 0% in every other region. This is not explained by carrier - the gap is present at 75-94% across all 15 carriers operating in South - which rules out a single carrier's reporting failure and points instead to a regional data pipeline or system-integration issue (e.g., a depot or regional system not feeding delivery confirmations back to the core dataset).

- Handling: preserved (per Phase 1 philosophy - never impute a real business event), and explicitly excluded from date-based on-time comparisons via the existing analysis_ready flag.
- Consequence: South's true on-time performance is currently unknowable. It should be treated as 'unmeasured', not 'good', in any region ranking until the tracking gap is fixed.

## New finding: CARR_07's freight cost is a ~10× outlier

As detailed in Q2, CARR_07 bills roughly 10x the per-km rate of every other carrier, consistently across mode and distance. This wasn't visible in Phase 1's outlier check because that check flagged freight cost outliers in aggregate (296 records, 5.9%) without segmenting by carrier - the CARR_07 pattern only becomes obvious once cost is compared within carrier.

- Handling: retained in the dataset (consistent with the 'preserve, don't delete' philosophy) but excluded from the pooled cost-distance regression in Q2, with the deviation quantified and flagged for finance/ops review rather than corrected unilaterally.

## Confirmed from Phase 1 (carried forward)
| Issue                             | Evidence                                                                                                              | Business Risk                                                       | Cleaning Decision                                       | Business Impact                                                            |
| --------------------------------- | --------------------------------------------------------------------------------------------------------------------- | ------------------------------------------------------------------- | ------------------------------------------------------- | -------------------------------------------------------------------------- |
| Duplicate shipment records        | 15 duplicate rows                                                                                                     | Double-counts shipments and inflates KPIs                           | Removed exact duplicates                                | Prevented inflated shipment, customer, carrier, and regional metrics       |
| Date columns stored as text       | All shipment date fields                                                                                              | Prevents date arithmetic and trend analysis                         | Converted to datetime                                   | Enabled transit, delay, and time-series analysis                           |
| Missing booking date              | 71 records (1.42%)                                                                                                    | Booking lead time unavailable                                       | Retained                                                | Avoided unsupported imputation                                             |
| Missing pickup date               | 87 records (1.74%)                                                                                                    | Transit calculations unavailable                                    | Retained                                                | Low occurrence; preserved operational records                              |
| Missing actual delivery date      | 1,482 records (29.64%)                                                                                                | Delivery performance cannot be calculated                           | Retained; excluded only from SLA analyses               | Preserved incomplete shipments while ensuring valid delivery metrics       |
| Invalid date chronology           | 39 actual before booking, 72 actual before pickup (74 unique shipments)                                               | Impossible transit and delay calculations                           | Flagged using `invalid_date_sequence`                   | Excluded only from time-based analyses                                     |
| Freight cost outliers             | 296 shipments (5.9%)                                                                                                  | May distort averages if assumed erroneous                           | Retained                                                | Later identified as a carrier-specific business pattern                    |
| Distance outliers                 | None                                                                                                                  | None                                                                | No action                                               | Distribution considered reasonable                                         |
| Invalid numeric values            | None                                                                                                                  | None                                                                | No action                                               | Freight cost and distance values were valid                                |
| Text inconsistencies              | None                                                                                                                  | None                                                                | No action                                               | Categories already standardized                                            |
| Shipment status ≠ SLA performance | Cross-tabulation showed **Delivered** and **Delayed** statuses did not consistently match actual delivery performance | Incorrect measurement of on-time performance                        | Created derived `delivery_performance` field            | Enabled reliable SLA analysis while preserving original operational status |
| Two delivery date fields          | Only 317 of 3,518 completed shipments (9%) had matching `delivery_date` and `actual_delivery_date`                    | Incorrect transit and delay calculations if the wrong field is used | Used `actual_delivery_date` as the analytical reference | Ensured consistent calculation of transit and delivery delay metrics       |

**Why it matters:** Both new findings are exactly the kind of issue that produces a confidently wrong answer if missed: without the South check, South would have looked like a strong region; without the CARR_07 check, the freight-cost/distance relationship would have looked weak and unusable.

**Next steps:** Escalate the South data gap to whoever owns the regional tracking/TMS integration - this is an operational fix, not an analytics one; escalate CARR_07's billing pattern to finance/procurement for invoice verification before the next payment cycle.

# Q5 - If you could track exactly one metric weekly to catch delivery problems early, what would it be?

**Recommendation:** Weekly On-Time Delivery Rate (% of shipments delivered on/before the promised date), tracked as a rolling trend line - paired with a second, smaller indicator: Delivery-Data Completeness Rate (% of Delivered/Delayed shipments with a valid actual_delivery_date).

On-time rate is the right primary metric because it's the one number that directly reflects whether Ops is meeting customer promises, it's comparable week over week regardless of volume, and it will move before softer signals (complaints, cancellations) show up. The chart above shows it fluctuating between roughly 45% and 58% week to week over the observed period - exactly the kind of variance a weekly view is built to catch early, before it compounds into a monthly miss.

The completeness rate is included as a mandatory companion, not a nice-to-have: this analysis just showed that a silent drop in data completeness (South) can make performance look better than it is. Without watching completeness alongside on-time rate, a future regional tracking failure would show up as a false improvement instead of a red flag.

## How to operationalize it

- Compute both metrics every Monday for the prior week, split by region and by carrier, so a regional or carrier-specific problem (like Central or CARR_07) is visible immediately rather than averaged away.
- Set an alert threshold: on-time rate dropping >5pp week-over-week, or completeness rate falling below ~95% for any region, triggers a review.
- Feed both into the dashboard built for this project (see below) so the trend is a standing view, not a monthly ad hoc pull.

# Dashboard

An interactive Streamlit dashboard (dashboard/streamlit_app.py) was built alongside, covering all five questions with filterable views by region, carrier, and date range. Deployment instructions are included in the accompanying README.
