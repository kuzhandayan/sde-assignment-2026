# Supervisor view snapshot — D8 00:00

## Loop health

```json
{
  "now": "D8 00:00",
  "ingest_events_last_sim_day": 13705,
  "ingest_events_per_wall_s": 33937.0,
  "decision_lag_s_p50": 0.1970682144165039,
  "decision_lag_s_max": 0.272747278213501,
  "decisions_last_sim_hour": 1,
  "credits_remaining": 200.0,
  "credits_used": 0.0,
  "peak_rss_mb": 306.14453125,
  "pending_approvals": 0,
  "chunks_ingested": 201,
  "alerts_page": []
}
```

## kestrel_finance

### ks_cancel — primary engagement_rate, config v16, prompt P1

- KPIs today: {'pickup_rate': None, 'engagement_rate': None, 'dials': 0} · before controller: {'pickup_rate': 0.2521, 'engagement_rate': 0.4931, 'dials': 65155}
- Caller IDs: {'D1': 'healthy', 'D2': 'healthy', 'D3': 'healthy'}
- Cohorts: time.age=18-30, time.age=31-45, time.age=46-60, time.age=60+

| cohort | dim | status | live split |
|---|---|---|---|
| default | voice | exploring | V1 34%, V2 9%, V3 34%, V4 23% |
| default | welcome_message | exploring | W1 67%, W2 33% |

## northwind_life

### nw_kyc — primary pickup_rate, config v8, prompt P1

- KPIs today: {'pickup_rate': None, 'engagement_rate': None, 'dials': 0} · before controller: {'pickup_rate': 0.2652, 'engagement_rate': 0.594, 'dials': 27230}
- Caller IDs: {'D1': 'probing', 'D2': 'healthy', 'D3': 'healthy'}
- Cohorts: time.age=18-30, time.age=31-45, time.age=46-60, time.age=60+

| cohort | dim | status | live split |
|---|---|---|---|
| default | voice | promoted — V2 | V1 5%, V2 95% |
| default | welcome_message | promoted — W2 | W1 5%, W2 95% |

### nw_renewal — primary engagement_rate, config v12, prompt P1

- KPIs today: {'pickup_rate': None, 'engagement_rate': None, 'dials': 0} · before controller: {'pickup_rate': 0.2694, 'engagement_rate': 0.5475, 'dials': 48811}
- Caller IDs: {'D1': 'healthy', 'D2': 'healthy', 'D3': 'healthy', 'D4': 'probing'}
- Cohorts: time.age=18-30, time.age=31-45, time.age=46-60, time.age=60+

| cohort | dim | status | live split |
|---|---|---|---|
| default | voice | exploring | V1 24%, V2 22%, V3 43%, V4 12% |
| default | welcome_message | exploring | W1 71%, W2 29% |