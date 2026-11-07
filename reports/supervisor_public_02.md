# Supervisor view snapshot — D10 00:00

## Loop health

```json
{
  "now": "D10 00:00",
  "ingest_events_last_sim_day": 13707,
  "ingest_events_per_wall_s": 34558.0,
  "decision_lag_s_p50": 0.21196651458740234,
  "decision_lag_s_max": 0.2943766117095947,
  "decisions_last_sim_hour": 1,
  "credits_remaining": 195.0,
  "credits_used": 5.0,
  "peak_rss_mb": 305.91015625,
  "pending_approvals": 0,
  "chunks_ingested": 251,
  "alerts_page": [
    {
      "minute": 5220,
      "workflow_id": "ks_cancel",
      "summary": "ks_cancel: hallucination spike on prompt P2",
      "action": "controller is preparing a validated rollback; check approvals for ks_cancel"
    }
  ]
}
```

## kestrel_finance

### ks_cancel — primary engagement_rate, config v15, prompt P1

- KPIs today: {'pickup_rate': None, 'engagement_rate': None, 'dials': 0} · before controller: {'pickup_rate': 0.2501, 'engagement_rate': 0.5067, 'dials': 65056}
- Caller IDs: {'D1': 'healthy', 'D2': 'bad', 'D3': 'healthy'}
- Cohorts: time.age=18-30, time.age=31-45, time.age=46-60, time.age=60+

| cohort | dim | status | live split |
|---|---|---|---|
| default | voice | exploring | V1 25%, V2 16%, V3 46%, V4 13% |
| default | welcome_message | exploring | W1 28%, W2 45%, W3 27% |

## northwind_life

### nw_kyc — primary pickup_rate, config v10, prompt P1

- KPIs today: {'pickup_rate': None, 'engagement_rate': None, 'dials': 0} · before controller: {'pickup_rate': 0.2611, 'engagement_rate': 0.601, 'dials': 27199}
- Caller IDs: {'D1': 'probing', 'D2': 'healthy', 'D3': 'healthy'}
- Cohorts: time.age=18-30, time.age=31-45, time.age=46-60, time.age=60+

| cohort | dim | status | live split |
|---|---|---|---|
| default | voice | exploring | V1 37%, V2 63% |
| default | welcome_message | promoted — W1 | W1 95%, W2 5% |

### nw_renewal — primary engagement_rate, config v15, prompt P1

- KPIs today: {'pickup_rate': None, 'engagement_rate': None, 'dials': 0} · before controller: {'pickup_rate': 0.2741, 'engagement_rate': 0.5463, 'dials': 48795}
- Caller IDs: {'D1': 'healthy', 'D2': 'probing', 'D3': 'healthy', 'D4': 'healthy'}
- Cohorts: seg.age=46-60.value=low, time.age=18-30, time.age=31-45, time.age=46-60, time.age=60+

| cohort | dim | status | live split |
|---|---|---|---|
| default | voice | exploring | V1 24%, V2 33%, V3 20%, V4 23% |
| default | welcome_message | exploring | W1 37%, W2 46%, W3 17% |
| seg.age=46-60.value=low | welcome_message | exploring | W2 59%, W3 41% |