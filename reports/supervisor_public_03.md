# Supervisor view snapshot — D5 00:00

## Loop health

```json
{
  "now": "D5 00:00",
  "ingest_events_last_sim_day": 840024,
  "ingest_events_per_wall_s": 86141.0,
  "decision_lag_s_p50": 1.0600247383117676,
  "decision_lag_s_max": 1.7593719959259033,
  "decisions_last_sim_hour": 1,
  "credits_remaining": 400.0,
  "credits_used": 0.0,
  "peak_rss_mb": 750.3046875,
  "pending_approvals": 2,
  "chunks_ingested": 148,
  "alerts_page": []
}
```

## aravalli_general

### arav_cancel_2 — primary engagement_rate, config v7, prompt P1

- KPIs today: {'pickup_rate': None, 'engagement_rate': None, 'dials': 0} · before controller: {'pickup_rate': 0.2628, 'engagement_rate': 0.4978, 'dials': 349822}
- Caller IDs: {'D1': 'healthy', 'D2': 'healthy', 'D3': 'healthy'}
- Cohorts: time.tier=1.age=18-30, time.tier=1.age=31-45, time.tier=1.age=46-60, time.tier=1.age=60+, time.tier=2.age=18-30, time.tier=2.age=31-45, time.tier=2.age=46-60, time.tier=2.age=60+, time.tier=3.age=18-30, time.tier=3.age=31-45, time.tier=3.age=46-60, time.tier=3.age=60+

| cohort | dim | status | live split |
|---|---|---|---|
| default | voice | promoted — V4 | V1 3%, V2 10%, V3 8%, V4 79% |
| default | welcome_message | promoted — W2 | W1 8%, W2 92%, W3 0% |

### arav_kyc_1 — primary pickup_rate, config v5, prompt P1

- KPIs today: {'pickup_rate': None, 'engagement_rate': None, 'dials': 0} · before controller: {'pickup_rate': 0.2649, 'engagement_rate': 0.5954, 'dials': 345124}
- Caller IDs: {'D1': 'bad', 'D2': 'healthy', 'D3': 'healthy'}
- Cohorts: seg.age=31-45, seg.lang=en, seg.tier=2, time.tier=1.age=18-30, time.tier=1.age=31-45, time.tier=1.age=46-60, time.tier=1.age=60+, time.tier=2.age=18-30, time.tier=2.age=31-45, time.tier=2.age=46-60, time.tier=2.age=60+, time.tier=3.age=18-30, time.tier=3.age=31-45, time.tier=3.age=46-60, time.tier=3.age=60+

| cohort | dim | status | live split |
|---|---|---|---|
| default | voice | exploring | V1 70%, V2 30% |
| default | welcome_message | promoted — W2 | W2 100% |
| seg.age=31-45 | voice | exploring | V1 70%, V2 30% |
| seg.lang=en | voice | promoted — V2 | V2 100% |
| seg.tier=2 | voice | exploring | V1 44%, V2 56% |

Waiting for approval:
- add cohorts seg.age=31-45; seg.age=31-45/voice: {V1 70%, V2 30%} -> {V1 52%, V2 48%} (impact 0.01, 2960 leads)

### arav_renewal_0 — primary engagement_rate, config v9, prompt P1

- KPIs today: {'pickup_rate': None, 'engagement_rate': None, 'dials': 0} · before controller: {'pickup_rate': 0.2823, 'engagement_rate': 0.5476, 'dials': 353132}
- Caller IDs: {'D1': 'healthy', 'D2': 'healthy', 'D3': 'healthy', 'D4': 'bad'}
- Cohorts: seg.age=46-60, seg.age=60+, seg.lang=hi, seg.tier=1, seg.tier=2, seg.value=mid, time.tier=1.age=18-30, time.tier=1.age=31-45, time.tier=1.age=46-60, time.tier=1.age=60+, time.tier=2.age=18-30, time.tier=2.age=31-45, time.tier=2.age=46-60, time.tier=2.age=60+, time.tier=3.age=18-30, time.tier=3.age=31-45, time.tier=3.age=46-60, time.tier=3.age=60+

| cohort | dim | status | live split |
|---|---|---|---|
| default | voice | exploring | V1 34%, V2 19%, V3 17%, V4 30% |
| default | welcome_message | promoted — W3 | W2 5%, W3 95% |
| seg.age=46-60 | welcome_message | promoted — W3 | W2 5%, W3 95% |
| seg.age=60+ | voice | promoted — V3 | V3 100% |
| seg.lang=hi | welcome_message | promoted — W3 | W2 5%, W3 95% |
| seg.tier=1 | welcome_message | promoted — W3 | W2 5%, W3 95% |
| seg.tier=2 | welcome_message | promoted — W3 | W2 5%, W3 95% |
| seg.value=mid | welcome_message | promoted — W3 | W2 5%, W3 95% |

## kestrel_finance

### kest_cancel_2 — primary engagement_rate, config v8, prompt P1

- KPIs today: {'pickup_rate': None, 'engagement_rate': None, 'dials': 0} · before controller: {'pickup_rate': 0.2618, 'engagement_rate': 0.5006, 'dials': 350218}
- Caller IDs: {'D1': 'healthy', 'D2': 'healthy', 'D3': 'healthy'}
- Cohorts: time.tier=1.age=18-30, time.tier=1.age=31-45, time.tier=1.age=46-60, time.tier=1.age=60+, time.tier=2.age=18-30, time.tier=2.age=31-45, time.tier=2.age=46-60, time.tier=2.age=60+, time.tier=3.age=18-30, time.tier=3.age=31-45, time.tier=3.age=46-60, time.tier=3.age=60+

| cohort | dim | status | live split |
|---|---|---|---|
| default | voice | promoted — V4 | V1 6%, V2 6%, V3 9%, V4 78% |
| default | welcome_message | promoted — W2 | W1 12%, W2 88% |

### kest_kyc_1 — primary pickup_rate, config v5, prompt P1

- KPIs today: {'pickup_rate': None, 'engagement_rate': None, 'dials': 0} · before controller: {'pickup_rate': 0.2658, 'engagement_rate': 0.5981, 'dials': 344718}
- Caller IDs: {'D1': 'bad', 'D2': 'healthy', 'D3': 'healthy'}
- Cohorts: seg.lang=en, time.tier=1.age=18-30, time.tier=1.age=31-45, time.tier=1.age=46-60, time.tier=1.age=60+, time.tier=2.age=18-30, time.tier=2.age=31-45, time.tier=2.age=46-60, time.tier=2.age=60+, time.tier=3.age=18-30, time.tier=3.age=31-45, time.tier=3.age=46-60, time.tier=3.age=60+

| cohort | dim | status | live split |
|---|---|---|---|
| default | voice | exploring | V1 43%, V2 57% |
| default | welcome_message | promoted — W2 | W1 5%, W2 95% |
| seg.lang=en | voice | promoted — V2 | V2 100% |

### kest_renewal_0 — primary engagement_rate, config v12, prompt P1

- KPIs today: {'pickup_rate': None, 'engagement_rate': None, 'dials': 0} · before controller: {'pickup_rate': 0.2833, 'engagement_rate': 0.5471, 'dials': 353168}
- Caller IDs: {'D1': 'healthy', 'D2': 'healthy', 'D3': 'healthy', 'D4': 'bad'}
- Cohorts: seg.age=60+, seg.lang=en, seg.lang=hi, seg.tier=2, seg.tier=3, seg.value=mid, time.tier=1.age=18-30, time.tier=1.age=31-45, time.tier=1.age=46-60, time.tier=1.age=60+, time.tier=2.age=18-30, time.tier=2.age=31-45, time.tier=2.age=46-60, time.tier=2.age=60+, time.tier=3.age=18-30, time.tier=3.age=31-45, time.tier=3.age=46-60, time.tier=3.age=60+

| cohort | dim | status | live split |
|---|---|---|---|
| default | voice | exploring | V1 52%, V2 27%, V4 21% |
| default | welcome_message | promoted — W3 | W2 5%, W3 95% |
| seg.age=60+ | voice | promoted — V3 | V2 5%, V3 90%, V4 5% |
| seg.lang=en | welcome_message | promoted — W3 | W2 5%, W3 95% |
| seg.lang=hi | welcome_message | exploring | W2 22%, W3 78% |
| seg.tier=2 | voice | exploring | V1 26%, V2 17%, V3 26%, V4 31% |
| seg.tier=3 | welcome_message | promoted — W3 | W2 5%, W3 95% |
| seg.value=mid | welcome_message | exploring | W2 5%, W3 95% |

## northwind_life

### nort_cancel_2 — primary engagement_rate, config v9, prompt P1

- KPIs today: {'pickup_rate': None, 'engagement_rate': None, 'dials': 0} · before controller: {'pickup_rate': 0.2628, 'engagement_rate': 0.4996, 'dials': 350323}
- Caller IDs: {'D1': 'healthy', 'D2': 'healthy', 'D3': 'healthy'}
- Cohorts: time.tier=1.age=18-30, time.tier=1.age=31-45, time.tier=1.age=46-60, time.tier=1.age=60+, time.tier=2.age=18-30, time.tier=2.age=31-45, time.tier=2.age=46-60, time.tier=2.age=60+, time.tier=3.age=18-30, time.tier=3.age=31-45, time.tier=3.age=46-60, time.tier=3.age=60+

| cohort | dim | status | live split |
|---|---|---|---|
| default | voice | promoted — V4 | V1 5%, V2 5%, V3 5%, V4 85% |
| default | welcome_message | promoted — W2 | W1 5%, W2 95% |

### nort_kyc_1 — primary pickup_rate, config v5, prompt P1

- KPIs today: {'pickup_rate': None, 'engagement_rate': None, 'dials': 0} · before controller: {'pickup_rate': 0.2632, 'engagement_rate': 0.5948, 'dials': 344906}
- Caller IDs: {'D1': 'bad', 'D2': 'healthy', 'D3': 'healthy'}
- Cohorts: time.tier=1.age=18-30, time.tier=1.age=31-45, time.tier=1.age=46-60, time.tier=1.age=60+, time.tier=2.age=18-30, time.tier=2.age=31-45, time.tier=2.age=46-60, time.tier=2.age=60+, time.tier=3.age=18-30, time.tier=3.age=31-45, time.tier=3.age=46-60, time.tier=3.age=60+

| cohort | dim | status | live split |
|---|---|---|---|
| default | voice | promoted — V2 | V2 100% |
| default | welcome_message | promoted — W2 | W2 100% |

### nort_renewal_0 — primary engagement_rate, config v11, prompt P1

- KPIs today: {'pickup_rate': None, 'engagement_rate': None, 'dials': 0} · before controller: {'pickup_rate': 0.2847, 'engagement_rate': 0.5448, 'dials': 353097}
- Caller IDs: {'D1': 'healthy', 'D2': 'healthy', 'D3': 'healthy', 'D4': 'bad'}
- Cohorts: seg.age=18-30, seg.age=60+, time.tier=1.age=18-30, time.tier=1.age=31-45, time.tier=1.age=46-60, time.tier=1.age=60+, time.tier=2.age=18-30, time.tier=2.age=31-45, time.tier=2.age=46-60, time.tier=2.age=60+, time.tier=3.age=18-30, time.tier=3.age=31-45, time.tier=3.age=46-60, time.tier=3.age=60+

| cohort | dim | status | live split |
|---|---|---|---|
| default | voice | promoted — V3 | V2 5%, V3 90%, V4 5% |
| default | welcome_message | promoted — W3 | W2 5%, W3 95% |
| seg.age=18-30 | voice | exploring | V1 46%, V2 28%, V4 26% |
| seg.age=60+ | welcome_message | promoted — W3 | W3 100% |

## tidewater_health

### tide_cancel_2 — primary engagement_rate, config v8, prompt P1

- KPIs today: {'pickup_rate': None, 'engagement_rate': None, 'dials': 0} · before controller: {'pickup_rate': 0.2616, 'engagement_rate': 0.5011, 'dials': 350158}
- Caller IDs: {'D1': 'healthy', 'D2': 'healthy', 'D3': 'healthy'}
- Cohorts: time.tier=1.age=18-30, time.tier=1.age=31-45, time.tier=1.age=46-60, time.tier=1.age=60+, time.tier=2.age=18-30, time.tier=2.age=31-45, time.tier=2.age=46-60, time.tier=2.age=60+, time.tier=3.age=18-30, time.tier=3.age=31-45, time.tier=3.age=46-60, time.tier=3.age=60+

| cohort | dim | status | live split |
|---|---|---|---|
| default | voice | promoted — V4 | V1 5%, V2 7%, V3 2%, V4 87% |
| default | welcome_message | promoted — W2 | W1 20%, W2 80% |

### tide_kyc_1 — primary pickup_rate, config v6, prompt P1

- KPIs today: {'pickup_rate': None, 'engagement_rate': None, 'dials': 0} · before controller: {'pickup_rate': 0.2628, 'engagement_rate': 0.5947, 'dials': 345130}
- Caller IDs: {'D1': 'bad', 'D2': 'healthy', 'D3': 'healthy'}
- Cohorts: seg.lang=en, seg.tier=1, time.tier=1.age=18-30, time.tier=1.age=31-45, time.tier=1.age=46-60, time.tier=1.age=60+, time.tier=2.age=18-30, time.tier=2.age=31-45, time.tier=2.age=46-60, time.tier=2.age=60+, time.tier=3.age=18-30, time.tier=3.age=31-45, time.tier=3.age=46-60, time.tier=3.age=60+

| cohort | dim | status | live split |
|---|---|---|---|
| default | voice | exploring | V1 70%, V2 30% |
| default | welcome_message | promoted — W2 | W1 5%, W2 95% |
| seg.lang=en | voice | promoted — V2 | V2 100% |
| seg.tier=1 | voice | promoted — V2 | V1 70%, V2 30% |

Waiting for approval:
- add cohorts seg.tier=1; seg.tier=1/voice: {V1 70%, V2 30%} -> {V1 5%, V2 95%} (impact 0.046, 4540 leads)

### tide_renewal_0 — primary engagement_rate, config v10, prompt P1

- KPIs today: {'pickup_rate': None, 'engagement_rate': None, 'dials': 0} · before controller: {'pickup_rate': 0.2845, 'engagement_rate': 0.5488, 'dials': 353075}
- Caller IDs: {'D1': 'healthy', 'D2': 'healthy', 'D3': 'healthy', 'D4': 'bad'}
- Cohorts: seg.age=60+, seg.lang=hi, seg.tier=1, seg.tier=3, seg.value=low, seg.value=mid, time.tier=1.age=18-30, time.tier=1.age=31-45, time.tier=1.age=46-60, time.tier=1.age=60+, time.tier=2.age=18-30, time.tier=2.age=31-45, time.tier=2.age=46-60, time.tier=2.age=60+, time.tier=3.age=18-30, time.tier=3.age=31-45, time.tier=3.age=46-60, time.tier=3.age=60+

| cohort | dim | status | live split |
|---|---|---|---|
| default | voice | exploring | V1 33%, V2 31%, V3 19%, V4 17% |
| default | welcome_message | promoted — W3 | W2 5%, W3 95% |
| seg.age=60+ | voice | promoted — V3 | V2 5%, V3 95% |
| seg.lang=hi | welcome_message | exploring | W2 5%, W3 95% |
| seg.tier=1 | welcome_message | promoted — W3 | W2 5%, W3 95% |
| seg.tier=3 | welcome_message | promoted — W3 | W1 11%, W3 89% |
| seg.value=low | welcome_message | promoted — W3 | W1 10%, W2 60%, W3 30% |
| seg.value=mid | welcome_message | promoted — W3 | W2 5%, W3 95% |