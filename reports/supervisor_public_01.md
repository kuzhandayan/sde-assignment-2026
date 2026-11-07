# Supervisor view snapshot — D8 00:00

## Loop health

```json
{
  "now": "D8 00:00",
  "ingest_events_last_sim_day": 13710,
  "ingest_events_per_wall_s": 32699.0,
  "decision_lag_s_p50": 0.10784196853637695,
  "decision_lag_s_max": 0.3582801818847656,
  "decisions_last_sim_hour": 1,
  "credits_remaining": 200.0,
  "credits_used": 0.0,
  "peak_rss_mb": 305.28515625,
  "pending_approvals": 0,
  "chunks_ingested": 201,
  "alerts_page": []
}
```

## kestrel_finance

### ks_cancel — primary engagement_rate, config v21, prompt P1

- KPIs today: {'pickup_rate': None, 'engagement_rate': None, 'dials': 0} · before controller: {'pickup_rate': 0.2521, 'engagement_rate': 0.4931, 'dials': 65155}
- Caller IDs: {'D1': 'healthy', 'D2': 'healthy', 'D3': 'healthy'}
- Cohorts: time.age=18-30, time.age=31-45, time.age=46-60, time.age=60+

| cohort | dim | status | live split |
|---|---|---|---|
| default | voice | exploring | V1 14%, V2 31%, V3 35%, V4 20% |
| default | welcome_message | promoted — W2 | W1 40%, W2 60% |

## northwind_life

### nw_kyc — primary pickup_rate, config v8, prompt P1

- KPIs today: {'pickup_rate': None, 'engagement_rate': None, 'dials': 0} · before controller: {'pickup_rate': 0.2652, 'engagement_rate': 0.594, 'dials': 27230}
- Caller IDs: {'D1': 'bad', 'D2': 'healthy', 'D3': 'healthy'}
- Cohorts: time.age=18-30, time.age=31-45, time.age=46-60, time.age=60+

| cohort | dim | status | live split |
|---|---|---|---|
| default | voice | promoted — V2 | V1 5%, V2 95% |
| default | welcome_message | promoted — W2 | W1 5%, W2 95% |

### nw_renewal — primary engagement_rate, config v13, prompt P1

- KPIs today: {'pickup_rate': None, 'engagement_rate': None, 'dials': 0} · before controller: {'pickup_rate': 0.2694, 'engagement_rate': 0.5475, 'dials': 48811}
- Caller IDs: {'D1': 'probing', 'D2': 'healthy', 'D3': 'healthy', 'D4': 'probing'}
- Cohorts: time.age=18-30, time.age=31-45, time.age=46-60, time.age=60+

| cohort | dim | status | live split |
|---|---|---|---|
| default | voice | exploring | V1 43%, V2 22%, V3 17%, V4 18% |
| default | welcome_message | promoted — W2 | W1 5%, W2 90%, W3 5% |