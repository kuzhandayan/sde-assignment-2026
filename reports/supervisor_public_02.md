# Supervisor view snapshot — D10 00:00

## Loop health

```json
{
  "now": "D10 00:00",
  "ingest_events_last_sim_day": 13707,
  "ingest_events_per_wall_s": 38107.0,
  "decision_lag_s_p50": 0.10549330711364746,
  "decision_lag_s_max": 0.38915348052978516,
  "decisions_last_sim_hour": 1,
  "credits_remaining": 195.0,
  "credits_used": 5.0,
  "peak_rss_mb": 305.4296875,
  "pending_approvals": 0,
  "chunks_ingested": 251,
  "alerts_page": [
    {
      "minute": 5160,
      "workflow_id": "ks_cancel",
      "summary": "ks_cancel: hallucination spike on prompt P2",
      "action": "controller is preparing a validated rollback; check approvals for ks_cancel"
    }
  ]
}
```

## kestrel_finance

### ks_cancel — primary engagement_rate, config v34, prompt P1

- KPIs today: {'pickup_rate': None, 'engagement_rate': None, 'dials': 0} · before controller: {'pickup_rate': 0.2501, 'engagement_rate': 0.5067, 'dials': 65056}
- Caller IDs: {'D1': 'healthy', 'D2': 'probing', 'D3': 'healthy'}
- Cohorts: seg.tier=1.age=31-45, time.age=18-30, time.age=31-45, time.age=46-60, time.age=60+

| cohort | dim | status | live split |
|---|---|---|---|
| default | voice | exploring | V1 20%, V2 10%, V3 35%, V4 34% |
| default | welcome_message | promoted — W2 | W1 13%, W2 80%, W3 7% |
| seg.tier=1.age=31-45 | welcome_message | exploring | W2 31%, W3 69% |

## northwind_life

### nw_kyc — primary pickup_rate, config v8, prompt P1

- KPIs today: {'pickup_rate': None, 'engagement_rate': None, 'dials': 0} · before controller: {'pickup_rate': 0.2611, 'engagement_rate': 0.601, 'dials': 27199}
- Caller IDs: {'D1': 'probing', 'D2': 'healthy', 'D3': 'healthy'}
- Cohorts: time.age=18-30, time.age=31-45, time.age=46-60, time.age=60+

| cohort | dim | status | live split |
|---|---|---|---|
| default | voice | promoted — V2 | V1 5%, V2 95% |
| default | welcome_message | exploring | W1 61%, W2 39% |

### nw_renewal — primary engagement_rate, config v19, prompt P1

- KPIs today: {'pickup_rate': None, 'engagement_rate': None, 'dials': 0} · before controller: {'pickup_rate': 0.2741, 'engagement_rate': 0.5463, 'dials': 48795}
- Caller IDs: {'D1': 'healthy', 'D2': 'probing', 'D3': 'healthy', 'D4': 'probing'}
- Cohorts: time.age=18-30, time.age=31-45, time.age=46-60, time.age=60+

| cohort | dim | status | live split |
|---|---|---|---|
| default | voice | exploring | V1 32%, V2 48%, V3 20% |
| default | welcome_message | exploring | W1 45%, W2 55% |