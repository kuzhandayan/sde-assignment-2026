# Supervisor view snapshot — D5 00:00

## Loop health

```json
{
  "now": "D5 00:00",
  "ingest_events_last_sim_day": 840029,
  "ingest_events_per_wall_s": 76330.0,
  "decision_lag_s_p50": 1.2468500137329102,
  "decision_lag_s_max": 1.8808033466339111,
  "decisions_last_sim_hour": 1,
  "credits_remaining": 400.0,
  "credits_used": 0.0,
  "peak_rss_mb": 748.109375,
  "pending_approvals": 2,
  "chunks_ingested": 148,
  "alerts_page": []
}
```

## aravalli_general

### arav_cancel_2 — primary engagement_rate, config v12, prompt P1

- KPIs today: {'pickup_rate': None, 'engagement_rate': None, 'dials': 0} · before controller: {'pickup_rate': 0.2628, 'engagement_rate': 0.4978, 'dials': 349822}
- Caller IDs: {'D1': 'healthy', 'D2': 'healthy', 'D3': 'healthy'}
- Cohorts: time.tier=1.age=18-30, time.tier=1.age=31-45, time.tier=1.age=46-60, time.tier=1.age=60+, time.tier=2.age=18-30, time.tier=2.age=31-45, time.tier=2.age=46-60, time.tier=2.age=60+, time.tier=3.age=18-30, time.tier=3.age=31-45, time.tier=3.age=46-60, time.tier=3.age=60+

| cohort | dim | status | live split |
|---|---|---|---|
| default | voice | promoted — V4 | V1 5%, V2 9%, V3 7%, V4 79% |
| default | welcome_message | promoted — W2 | W1 10%, W2 90%, W3 0% |

### arav_kyc_1 — primary pickup_rate, config v5, prompt P1

- KPIs today: {'pickup_rate': None, 'engagement_rate': None, 'dials': 0} · before controller: {'pickup_rate': 0.2649, 'engagement_rate': 0.5954, 'dials': 345124}
- Caller IDs: {'D1': 'bad', 'D2': 'healthy', 'D3': 'healthy'}
- Cohorts: seg.lang=en, time.tier=1.age=18-30, time.tier=1.age=31-45, time.tier=1.age=46-60, time.tier=1.age=60+, time.tier=2.age=18-30, time.tier=2.age=31-45, time.tier=2.age=46-60, time.tier=2.age=60+, time.tier=3.age=18-30, time.tier=3.age=31-45, time.tier=3.age=46-60, time.tier=3.age=60+

| cohort | dim | status | live split |
|---|---|---|---|
| default | voice | exploring | V1 70%, V2 30% |
| default | welcome_message | promoted — W2 | W2 100% |
| seg.lang=en | voice | promoted — V2 | V2 100% |

### arav_renewal_0 — primary engagement_rate, config v11, prompt P1

- KPIs today: {'pickup_rate': None, 'engagement_rate': None, 'dials': 0} · before controller: {'pickup_rate': 0.2823, 'engagement_rate': 0.5476, 'dials': 353132}
- Caller IDs: {'D1': 'healthy', 'D2': 'healthy', 'D3': 'healthy', 'D4': 'bad'}
- Cohorts: seg.age=18-30, seg.age=60+.value=low, seg.lang=en.age=60+, seg.lang=hi, seg.tier=2, seg.tier=3, time.tier=1.age=18-30, time.tier=1.age=31-45, time.tier=1.age=46-60, time.tier=1.age=60+, time.tier=2.age=18-30, time.tier=2.age=31-45, time.tier=2.age=46-60, time.tier=2.age=60+, time.tier=3.age=18-30, time.tier=3.age=31-45, time.tier=3.age=46-60, time.tier=3.age=60+

| cohort | dim | status | live split |
|---|---|---|---|
| default | voice | exploring | V1 33%, V2 37%, V3 15%, V4 15% |
| default | welcome_message | promoted — W3 | W2 5%, W3 95% |
| seg.age=18-30 | welcome_message | promoted — W3 | W2 10%, W3 90% |
| seg.age=60+.value=low | voice | promoted — V3 | V3 100% |
| seg.lang=en.age=60+ | voice | promoted — V3 | V3 100% |
| seg.lang=hi | welcome_message | promoted — W3 | W2 5%, W3 95% |
| seg.tier=2 | welcome_message | promoted — W3 | W2 5%, W3 95% |
| seg.tier=3 | welcome_message | promoted — W3 | W2 5%, W3 95% |

## kestrel_finance

### kest_cancel_2 — primary engagement_rate, config v8, prompt P1

- KPIs today: {'pickup_rate': None, 'engagement_rate': None, 'dials': 0} · before controller: {'pickup_rate': 0.2618, 'engagement_rate': 0.5006, 'dials': 350218}
- Caller IDs: {'D1': 'healthy', 'D2': 'healthy', 'D3': 'healthy'}
- Cohorts: time.tier=1.age=18-30, time.tier=1.age=31-45, time.tier=1.age=46-60, time.tier=1.age=60+, time.tier=2.age=18-30, time.tier=2.age=31-45, time.tier=2.age=46-60, time.tier=2.age=60+, time.tier=3.age=18-30, time.tier=3.age=31-45, time.tier=3.age=46-60, time.tier=3.age=60+

| cohort | dim | status | live split |
|---|---|---|---|
| default | voice | promoted — V4 | V1 5%, V2 5%, V3 5%, V4 85% |
| default | welcome_message | promoted — W2 | W1 15%, W2 83%, W3 1% |

### kest_kyc_1 — primary pickup_rate, config v5, prompt P1

- KPIs today: {'pickup_rate': None, 'engagement_rate': None, 'dials': 0} · before controller: {'pickup_rate': 0.2658, 'engagement_rate': 0.5981, 'dials': 344718}
- Caller IDs: {'D1': 'bad', 'D2': 'healthy', 'D3': 'healthy'}
- Cohorts: time.tier=1.age=18-30, time.tier=1.age=31-45, time.tier=1.age=46-60, time.tier=1.age=60+, time.tier=2.age=18-30, time.tier=2.age=31-45, time.tier=2.age=46-60, time.tier=2.age=60+, time.tier=3.age=18-30, time.tier=3.age=31-45, time.tier=3.age=46-60, time.tier=3.age=60+

| cohort | dim | status | live split |
|---|---|---|---|
| default | voice | promoted — V2 | V1 5%, V2 95% |
| default | welcome_message | promoted — W2 | W2 100% |

### kest_renewal_0 — primary engagement_rate, config v11, prompt P1

- KPIs today: {'pickup_rate': None, 'engagement_rate': None, 'dials': 0} · before controller: {'pickup_rate': 0.2833, 'engagement_rate': 0.5471, 'dials': 353168}
- Caller IDs: {'D1': 'healthy', 'D2': 'healthy', 'D3': 'healthy', 'D4': 'bad'}
- Cohorts: seg.age=31-45, seg.age=60+, seg.lang=hi, seg.lang=ta, seg.tier=1, seg.value=low, time.tier=1.age=18-30, time.tier=1.age=31-45, time.tier=1.age=46-60, time.tier=1.age=60+, time.tier=2.age=18-30, time.tier=2.age=31-45, time.tier=2.age=46-60, time.tier=2.age=60+, time.tier=3.age=18-30, time.tier=3.age=31-45, time.tier=3.age=46-60, time.tier=3.age=60+

| cohort | dim | status | live split |
|---|---|---|---|
| default | voice | exploring | V1 30%, V2 21%, V4 48% |
| default | welcome_message | promoted — W3 | W3 100% |
| seg.age=31-45 | welcome_message | exploring | W1 10%, W2 46%, W3 44% |
| seg.age=60+ | voice | promoted — V3 | V3 100% |
| seg.lang=hi | welcome_message | exploring | W1 8%, W2 50%, W3 42% |
| seg.lang=ta | welcome_message | exploring | W3 100% |
| seg.tier=1 | welcome_message | exploring | W2 29%, W3 71% |
| seg.value=low | welcome_message | promoted — W3 | W3 100% |

Waiting for approval:
- seg.age=31-45/welcome_message: {W1 10%, W2 46%, W3 44%} -> {W2 62%, W3 38%}; seg.lang=hi/welcome_message: {W1 8%, W2 50%, W3 42%} -> {W2 68%, W3 32%} (impact 0.022, 4761 leads)

## northwind_life

### nort_cancel_2 — primary engagement_rate, config v11, prompt P1

- KPIs today: {'pickup_rate': None, 'engagement_rate': None, 'dials': 0} · before controller: {'pickup_rate': 0.2628, 'engagement_rate': 0.4996, 'dials': 350323}
- Caller IDs: {'D1': 'healthy', 'D2': 'healthy', 'D3': 'healthy'}
- Cohorts: seg.tier=2.age=46-60, seg.value=high, time.tier=1.age=18-30, time.tier=1.age=31-45, time.tier=1.age=46-60, time.tier=1.age=60+, time.tier=2.age=18-30, time.tier=2.age=31-45, time.tier=2.age=46-60, time.tier=2.age=60+, time.tier=3.age=18-30, time.tier=3.age=31-45, time.tier=3.age=46-60, time.tier=3.age=60+

| cohort | dim | status | live split |
|---|---|---|---|
| default | voice | promoted — V4 | V1 1%, V2 10%, V3 1%, V4 88% |
| default | welcome_message | promoted — W2 | W1 7%, W2 86%, W3 6% |
| seg.tier=2.age=46-60 | voice | promoted — V1 | V1 95%, V3 5% |
| seg.value=high | voice | exploring | V1 70%, V2 7%, V3 7%, V4 16% |

### nort_kyc_1 — primary pickup_rate, config v5, prompt P1

- KPIs today: {'pickup_rate': None, 'engagement_rate': None, 'dials': 0} · before controller: {'pickup_rate': 0.2632, 'engagement_rate': 0.5948, 'dials': 344906}
- Caller IDs: {'D1': 'bad', 'D2': 'healthy', 'D3': 'healthy'}
- Cohorts: seg.lang=en.age=31-45, time.tier=1.age=18-30, time.tier=1.age=31-45, time.tier=1.age=46-60, time.tier=1.age=60+, time.tier=2.age=18-30, time.tier=2.age=31-45, time.tier=2.age=46-60, time.tier=2.age=60+, time.tier=3.age=18-30, time.tier=3.age=31-45, time.tier=3.age=46-60, time.tier=3.age=60+

| cohort | dim | status | live split |
|---|---|---|---|
| default | voice | promoted — V2 | V1 34%, V2 66% |
| default | welcome_message | promoted — W2 | W2 100% |
| seg.lang=en.age=31-45 | voice | promoted — V2 | V2 100% |

Waiting for approval:
- default/voice: {V1 34%, V2 66%} -> {V2 100%} (impact 0.136, 23471 leads)

### nort_renewal_0 — primary engagement_rate, config v12, prompt P1

- KPIs today: {'pickup_rate': None, 'engagement_rate': None, 'dials': 0} · before controller: {'pickup_rate': 0.2847, 'engagement_rate': 0.5448, 'dials': 353097}
- Caller IDs: {'D1': 'healthy', 'D2': 'healthy', 'D3': 'healthy', 'D4': 'bad'}
- Cohorts: seg.age=60+, seg.lang=hi, seg.value=mid, time.tier=1.age=18-30, time.tier=1.age=31-45, time.tier=1.age=46-60, time.tier=1.age=60+, time.tier=2.age=18-30, time.tier=2.age=31-45, time.tier=2.age=46-60, time.tier=2.age=60+, time.tier=3.age=18-30, time.tier=3.age=31-45, time.tier=3.age=46-60, time.tier=3.age=60+

| cohort | dim | status | live split |
|---|---|---|---|
| default | voice | exploring | V1 24%, V2 20%, V3 18%, V4 38% |
| default | welcome_message | promoted — W3 | W2 5%, W3 95% |
| seg.age=60+ | voice | promoted — V3 | V3 100% |
| seg.lang=hi | welcome_message | exploring | W2 33%, W3 67% |
| seg.value=mid | welcome_message | promoted — W3 | W2 5%, W3 95% |

## tidewater_health

### tide_cancel_2 — primary engagement_rate, config v18, prompt P1

- KPIs today: {'pickup_rate': None, 'engagement_rate': None, 'dials': 0} · before controller: {'pickup_rate': 0.2616, 'engagement_rate': 0.5011, 'dials': 350158}
- Caller IDs: {'D1': 'healthy', 'D2': 'healthy', 'D3': 'healthy'}
- Cohorts: seg.lang=hi.age=18-30, seg.tier=2.age=60+, seg.tier=2.value=high, time.tier=1.age=18-30, time.tier=1.age=31-45, time.tier=1.age=46-60, time.tier=1.age=60+, time.tier=2.age=18-30, time.tier=2.age=31-45, time.tier=2.age=46-60, time.tier=2.age=60+, time.tier=3.age=18-30, time.tier=3.age=31-45, time.tier=3.age=46-60, time.tier=3.age=60+

| cohort | dim | status | live split |
|---|---|---|---|
| default | voice | promoted — V4 | V1 2%, V2 7%, V3 6%, V4 84% |
| default | welcome_message | promoted — W2 | W1 13%, W2 87%, W3 0% |
| seg.lang=hi.age=18-30 | welcome_message | exploring | W1 47%, W2 53% |
| seg.tier=2.age=60+ | voice | exploring | V1 66%, V2 16%, V3 18% |
| seg.tier=2.value=high | voice | exploring | V1 82%, V3 18% |

### tide_kyc_1 — primary pickup_rate, config v6, prompt P1

- KPIs today: {'pickup_rate': None, 'engagement_rate': None, 'dials': 0} · before controller: {'pickup_rate': 0.2628, 'engagement_rate': 0.5947, 'dials': 345130}
- Caller IDs: {'D1': 'bad', 'D2': 'healthy', 'D3': 'healthy'}
- Cohorts: seg.lang=en.tier=1, time.tier=1.age=18-30, time.tier=1.age=31-45, time.tier=1.age=46-60, time.tier=1.age=60+, time.tier=2.age=18-30, time.tier=2.age=31-45, time.tier=2.age=46-60, time.tier=2.age=60+, time.tier=3.age=18-30, time.tier=3.age=31-45, time.tier=3.age=46-60, time.tier=3.age=60+

| cohort | dim | status | live split |
|---|---|---|---|
| default | voice | promoted — V2 | V2 100% |
| default | welcome_message | promoted — W2 | W1 5%, W2 95% |
| seg.lang=en.tier=1 | voice | promoted — V2 | V2 100% |

### tide_renewal_0 — primary engagement_rate, config v8, prompt P1

- KPIs today: {'pickup_rate': None, 'engagement_rate': None, 'dials': 0} · before controller: {'pickup_rate': 0.2845, 'engagement_rate': 0.5488, 'dials': 353075}
- Caller IDs: {'D1': 'healthy', 'D2': 'healthy', 'D3': 'healthy', 'D4': 'bad'}
- Cohorts: seg.age=60+, seg.lang=hi, seg.tier=2, seg.value=low, time.tier=1.age=18-30, time.tier=1.age=31-45, time.tier=1.age=46-60, time.tier=1.age=60+, time.tier=2.age=18-30, time.tier=2.age=31-45, time.tier=2.age=46-60, time.tier=2.age=60+, time.tier=3.age=18-30, time.tier=3.age=31-45, time.tier=3.age=46-60, time.tier=3.age=60+

| cohort | dim | status | live split |
|---|---|---|---|
| default | voice | exploring | V1 43%, V2 32%, V3 12%, V4 13% |
| default | welcome_message | promoted — W3 | W2 5%, W3 95% |
| seg.age=60+ | voice | promoted — V3 | V3 100% |
| seg.lang=hi | welcome_message | exploring | W1 5%, W2 30%, W3 66% |
| seg.tier=2 | welcome_message | promoted — W3 | W2 5%, W3 95% |
| seg.value=low | welcome_message | promoted — W3 | W2 5%, W3 95% |