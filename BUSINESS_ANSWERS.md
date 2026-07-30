Executive Summary
This phase answers the five business questions Ops asked for, using the analytics-ready dataset produced in Phase 1. Every answer below is backed by a query or statistical test - not an eyeball read - and every number is reproducible from shipments_cleaned.csv.

Central is the region with the worst, most reliably-measured delivery performance: a 15.9% delay rate (vs. 14.1% national average) that persists across almost every carrier, pointing to a regional operating issue rather than one bad partner.
Freight cost and distance are strongly linear once you control for shipment mode (r ≈ 0.98 within FTL/LTL/PTL) - but CARR_07 breaks that relationship completely, billing roughly 10× the per-km rate of every other carrier on identical lanes.
Delay is concentrated in a small set of customers whose delay rate is far higher than their region/carrier mix would predict - led by CUST_066 at 40% (vs. an expected 14%) - meaning the driver is account-specific, not network-wide.
The single biggest data-quality finding in this phase: South region is missing actual_delivery_date on 84.5% of Delivered/Delayed shipments, vs. 0% everywhere else - a regional tracking gap that makes South's on-time rate un-measurable until it's fixed.
Recommended weekly metric: Weekly On-Time Delivery Rate, tracked alongside a Delivery-Data Completeness rate so a reporting gap is never mistaken for a performance win.
Q1 - Which region has the worst on-time delivery performance, and what's driving it?
Method
On-time performance was measured two ways to cross-check each other: (a) a date-based on_time_flag (actual_delivery_date vs. promised_delivery_date) restricted to analysis_ready rows, and (b) a status-based delay rate (Delayed ÷ [Delivered + Delayed]) using every shipment, which doesn't depend on actual_delivery_date being populated. The second method matters because, as Q4 details, actual_delivery_date is missing for 84.5% of Delivered/Delayed shipments in the South - so a date-based comparison alone would silently exclude most of that region and produce a misleading ranking.



Finding: Central has the worst delay rate at 15.9%, against a 14.1% national average. North is second at 15.0%. South cannot be reliably ranked - its 13.4% delay rate is computed on a badly incomplete slice of data (see chart: the red line shows the % of Delivered/Delayed shipments missing an actual delivery date by region).

Region	Delay rate (status-based)	On-time rate (date-based, analysis-ready only)	Sample reliability
Central	15.9%	48.3%	Reliable - 84% of rows usable
North	15.0%	49.6%	Reliable - 82% of rows usable
West	13.8%	51.3%	Reliable - 81% of rows usable
South	13.4%	52.4%*	Unreliable - only 13% of rows usable
East	12.3%	50.3%	Reliable - 83% of rows usable
*South's date-based on-time rate is shown for completeness but should not be trusted - it is computed on just 124 of 971 South shipments.

What's driving Central's underperformance
The gap is not concentrated in one carrier or one shipping mode. Comparing each carrier's delay rate inside Central against that same carrier's national average delay rate shows the majority of carriers underperform their own national number when operating in Central (average gap: +1.75 percentage points), which points to a regional factor - hub congestion, last-mile infrastructure, or handling capacity - rather than a single underperforming partner.



13 of 15 carriers post a higher delay rate in Central than they do nationally; only 2 carriers (CARR_07, CARR_15) do better there.
Long-haul shipments (>2000 km) in Central delay at 19.1%, vs. 13.8-14.9% for shorter bands - distance compounds the regional effect.
Mode is not the driver: FTL (17.0%), PTL (16.6%), and LTL (14.5%) delay rates in Central are all elevated versus their national baselines by similar margins.
Why it matters: Central represents ~20% of shipment volume (1,001 shipments). A 1.8pp reduction in its delay rate back to the national average would prevent roughly 18 delayed shipments per period across the region - and because the effect is broad-based rather than one carrier, a carrier scorecard alone won't fix it.

Next steps: Investigate Central's hub/handling capacity and long-haul routing specifically (highest-delay segment); pull dock-level or handoff-level timestamps if available to isolate where within the Central network the delay accumulates; re-run this comparison after the South data-capture issue is fixed, since South may reveal itself to be worse once measurable.

Q2 - Is there a relationship between freight cost and distance? Which carrier(s) deviate, and by how much?
Method
A simple pooled correlation between freight_cost and distance_km across all 5,000 shipments returns a weak r = 0.30 (R² = 0.09) - but pooling hides the fact that FTL, LTL, and PTL have structurally different cost bases per km. Re-running the correlation within each mode shows a very different picture.

Segment	Correlation (r)	R²	Interpretation
All shipments, pooled	0.30	0.09	Weak - mode mix and one outlier carrier obscure the real relationship
FTL only	0.985	0.97	Near-perfect linear relationship
LTL only	0.985	0.97	Near-perfect linear relationship
PTL only	0.984	0.97	Near-perfect linear relationship
All modes, excluding CARR_07	0.73	0.54	Strong once the outlier carrier is removed
Finding: Yes - freight cost is very tightly, linearly tied to distance within each shipment mode (r ≈ 0.98). The apparent weak overall relationship was an artifact of mixing three different cost structures and one carrier's pricing anomaly into a single scatter.



Which carrier deviates - and by how much
CARR_07 is a clear, severe outlier. Its average cost per km is ₹159, against ₹16-17 for every other carrier - roughly 10× the market rate, and the gap holds consistently across every mode and every distance band (FTL: ₹249 vs. ₹25; LTL: ₹118 vs. ₹12; PTL: ₹79 vs. ₹8, all ≈10× multiples). All 342 of CARR_07's shipments (100%) fall above ₹56/km, while no other carrier's shipments approach that level.



CARR_07's overall deviation from the fitted cost-distance line is +547% on average - over 5x the predicted cost for its distance.
The ~10x multiplier is uniform across mode and distance band, which is more consistent with a systematic billing, currency, or unit-conversion error than a legitimate premium/express surcharge (a real premium tier would typically show more variation and a smaller, more defensible multiplier).
Excluding CARR_07, every other carrier sits within a normal ±3% band of the fitted cost-distance line - no other carrier shows meaningful deviation.
Why it matters: At CARR_07's average freight cost of ₹206,161 versus a market-implied cost of roughly ₹20,600 for the same distance/mode mix, this represents a very large cost exposure across 342 shipments if the billed amounts are real and being paid as invoiced.

Next steps: Pull CARR_07's raw invoices and contract rate card to confirm whether ₹/km is being recorded in the wrong currency or unit, or whether this is a genuine (and probably renegotiable) premium-service contract; freeze further CARR_07 bookings pending that check given the scale of the gap.

Q3 - Which customer(s) are experiencing the most delivery delays? Is that carrier-driven, region-driven, or something else?
Method
For every customer with at least 10 Delivered/Delayed shipments, an 'expected' delay rate was built as the average of that shipment's region delay rate and carrier delay rate - i.e., what a customer with that exact region/carrier mix should experience if nothing else were going on. Comparing each customer's actual delay rate to this expected baseline isolates delay that region or carrier mix cannot explain.



Finding: CUST_066 is the standout: a 40.0% delay rate against a region/carrier-expected rate of 14.0% - 26 percentage points of unexplained excess, more than double the next-worst customer. A further nine customers (CUST_011, CUST_118, CUST_005, CUST_120, CUST_054, CUST_029, CUST_044, CUST_058, CUST_009) show 7-14pp of excess delay beyond what their region/carrier mix predicts.

Customer	Shipments	Actual delay rate	Region/carrier-expected	Excess (customer-specific)
CUST_066	40	40.0%	14.0%	+26.0 pp
CUST_011	28	28.6%	14.3%	+14.3 pp
CUST_118	26	26.9%	14.3%	+12.6 pp
CUST_005	42	26.2%	14.0%	+12.2 pp
CUST_120	35	25.7%	14.2%	+11.5 pp
Is it carrier- or region-driven?: No. CUST_066's 40 shipments are spread across all 5 regions (7-17 each) and no single carrier handles more than 5 of them - the same pattern holds for the other flagged customers. If a carrier or region were the true cause, delay would concentrate there; instead it travels with the customer regardless of who ships it or where.

This points to something specific to the customer relationship or their shipment profile - e.g., delivery address complexity (rural/hard-to-access locations), consignee availability at drop-off, special handling requirements, or account-level SLA/documentation issues - rather than a network problem.

Why it matters: These 10 customers alone account for a disproportionate share of delayed shipments relative to their volume. Because the cause travels with the account rather than the carrier or lane, carrier renegotiation or regional fixes won't move these numbers - an account-level review is needed.

Next steps: Open a root-cause review with CUST_066 specifically (delivery address type, receiving-dock hours, special handling flags); check whether these accounts share a customer segment, product type, or delivery instruction pattern; consider a proactive SLA check-in for accounts running >2x the expected delay rate.

Q4 - Before trusting any of the above, what data quality issues did you find, and how did you handle them?
Phase 1 covered structural cleaning (duplicates, data types, invalid values, business-rule flags) in detail - see the Phase 1 documentation for the full audit trail. Two additional issues surfaced during this EDA phase that materially affect how the Q1-Q3 answers above should be read, and are reported here because they weren't visible until the data was sliced by region and carrier.

New finding: South region has a systemic delivery-confirmation gap
84.5% of Delivered/Delayed shipments in the South are missing actual_delivery_date, versus exactly 0% in every other region. This is not explained by carrier - the gap is present at 75-94% across all 15 carriers operating in South - which rules out a single carrier's reporting failure and points instead to a regional data pipeline or system-integration issue (e.g., a depot or regional system not feeding delivery confirmations back to the core dataset).

Handling: preserved (per Phase 1 philosophy - never impute a real business event), and explicitly excluded from date-based on-time comparisons via the existing analysis_ready flag.
Consequence: South's true on-time performance is currently unknowable. It should be treated as 'unmeasured', not 'good', in any region ranking until the tracking gap is fixed.
New finding: CARR_07's freight cost is a ~10× outlier
As detailed in Q2, CARR_07 bills roughly 10x the per-km rate of every other carrier, consistently across mode and distance. This wasn't visible in Phase 1's outlier check because that check flagged freight cost outliers in aggregate (296 records, 5.9%) without segmenting by carrier - the CARR_07 pattern only becomes obvious once cost is compared within carrier.

Handling: retained in the dataset (consistent with the 'preserve, don't delete' philosophy) but excluded from the pooled cost-distance regression in Q2, with the deviation quantified and flagged for finance/ops review rather than corrected unilaterally.
Confirmed from Phase 1 (carried forward)
Issue	Scale	Decision	Impact on this EDA
Duplicate records	15 rows	Removed	None - cleaned before this phase
Missing actual_delivery_date (general)	1,482 rows (29.6%)	Preserved + flagged	Handled via analysis_ready filter
Invalid date sequence	111 rows	Preserved + flagged	Excluded from date-based metrics
Freight cost outliers (aggregate)	296 rows (5.9%)	Preserved	Re-examined by carrier in Q2 - mostly CARR_07
Why it matters: Both new findings are exactly the kind of issue that produces a confidently wrong answer if missed: without the South check, South would have looked like a strong region; without the CARR_07 check, the freight-cost/distance relationship would have looked weak and unusable.

Next steps: Escalate the South data gap to whoever owns the regional tracking/TMS integration - this is an operational fix, not an analytics one; escalate CARR_07's billing pattern to finance/procurement for invoice verification before the next payment cycle.

Q5 - If you could track exactly one metric weekly to catch delivery problems early, what would it be?
Recommendation: Weekly On-Time Delivery Rate (% of shipments delivered on/before the promised date), tracked as a rolling trend line - paired with a second, smaller indicator: Delivery-Data Completeness Rate (% of Delivered/Delayed shipments with a valid actual_delivery_date).



On-time rate is the right primary metric because it's the one number that directly reflects whether Ops is meeting customer promises, it's comparable week over week regardless of volume, and it will move before softer signals (complaints, cancellations) show up. The chart above shows it fluctuating between roughly 45% and 58% week to week over the observed period - exactly the kind of variance a weekly view is built to catch early, before it compounds into a monthly miss.

The completeness rate is included as a mandatory companion, not a nice-to-have: this analysis just showed that a silent drop in data completeness (South) can make performance look better than it is. Without watching completeness alongside on-time rate, a future regional tracking failure would show up as a false improvement instead of a red flag.

How to operationalize it
Compute both metrics every Monday for the prior week, split by region and by carrier, so a regional or carrier-specific problem (like Central or CARR_07) is visible immediately rather than averaged away.
Set an alert threshold: on-time rate dropping >5pp week-over-week, or completeness rate falling below ~95% for any region, triggers a review.
Feed both into the dashboard built for this project (see below) so the trend is a standing view, not a monthly ad hoc pull.
