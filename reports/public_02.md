# Grade report — public_02_incidents

## Outcomes vs baseline (no-op controller)

| workflow | conclusion rate | Δ | pickup | Δ | engagement | Δ | engagement gap captured | hallucinated calls (base) |
|---|---|---|---|---|---|---|---|---|
| ks_cancel | 0.376 | +54.1% | 0.255 | +39.9% | 0.501 | +6.1% | 44% | 82 (310) |
| nw_kyc | 0.463 | +20.6% | 0.294 | +18.9% | 0.597 | -0.4% | -1% | 44 (38) |
| nw_renewal | 0.490 | +13.8% | 0.295 | +12.0% | 0.554 | +1.1% | 4% | 62 (58) |
| ALL | 0.432 | +28.7% | 0.277 | +24.0% | 0.540 | +1.8% | 26% | 188 (406) |

## Changes applied by the controller

35 applied — neutral: 21, beneficial: 10, harmful: 4

- nw_renewal v2 (controller_auto) dims=['caller_id'] engageΔ=+0.000 didΔ=+0.013 → **neutral**
- ks_cancel v2 (controller_auto) dims=['welcome_message', 'voice', 'caller_id'] engageΔ=+0.007 didΔ=+0.006 → **neutral**
- ks_cancel v3 (controller_auto) dims=['welcome_message', 'voice'] engageΔ=+0.007 didΔ=+0.000 → **neutral**
- nw_renewal v3 (controller_approved) dims=['cohorts', 'welcome_message', 'voice', 'schedule'] engageΔ=+0.021 didΔ=+0.000 → **beneficial**
- ks_cancel v4 (controller_approved) dims=['cohorts', 'welcome_message', 'voice', 'schedule'] engageΔ=+0.007 didΔ=+0.000 → **neutral**
- ks_cancel v5 (controller_auto) dims=['voice'] engageΔ=+0.005 didΔ=+0.000 → **neutral**
- nw_kyc v2 (controller_approved) dims=['cohorts', 'welcome_message', 'voice', 'caller_id', 'schedule'] engageΔ=-0.011 didΔ=+0.051 → **harmful**
- ks_cancel v6 (controller_auto) dims=['voice'] engageΔ=-0.003 didΔ=+0.000 → **neutral**
- nw_renewal v4 (controller_approved) dims=['welcome_message', 'voice'] engageΔ=+0.041 didΔ=+0.000 → **beneficial**
- nw_renewal v5 (controller_auto) dims=['caller_id'] engageΔ=+0.000 didΔ=+0.037 → **beneficial**
- ks_cancel v7 (controller_auto) dims=['caller_id'] engageΔ=+0.000 didΔ=+0.030 → **beneficial**
- nw_kyc v3 (controller_approved) dims=['voice'] engageΔ=+0.008 didΔ=+0.000 → **neutral**
- nw_renewal v6 (controller_auto) dims=['caller_id'] engageΔ=+0.000 didΔ=+0.018 → **neutral**
- ks_cancel v8 (controller_auto) dims=['caller_id'] engageΔ=+0.000 didΔ=+0.021 → **beneficial**
- ks_cancel v9 (controller_auto) dims=['caller_id'] engageΔ=+0.000 didΔ=+0.018 → **neutral**
- nw_renewal v7 (controller_approved) dims=['welcome_message', 'voice'] engageΔ=+0.087 didΔ=+0.000 → **beneficial**
- nw_kyc v4 (controller_approved) dims=['voice'] engageΔ=+0.006 didΔ=+0.000 → **neutral**
- ks_cancel v11 (controller_auto) dims=['voice'] engageΔ=+0.004 didΔ=+0.000 → **neutral**
- ks_cancel v12 (controller_approved) dims=['prompt_version'] engageΔ=+0.102 didΔ=+0.000 → **beneficial**
- ks_cancel v13 (controller_auto) dims=['caller_id'] engageΔ=+0.000 didΔ=-0.018 → **neutral**
- nw_kyc v5 (controller_approved) dims=['caller_id'] engageΔ=+0.000 didΔ=+0.259 → **beneficial**
- ks_cancel v14 (controller_auto) dims=['welcome_message'] engageΔ=+0.007 didΔ=+0.000 → **neutral**
- nw_renewal v8 (controller_approved) dims=['welcome_message'] engageΔ=+0.077 didΔ=+0.000 → **beneficial**
- nw_kyc v6 (controller_approved) dims=['voice'] engageΔ=-0.006 didΔ=+0.000 → **neutral**
- nw_renewal v9 (controller_auto) dims=['caller_id'] engageΔ=+0.000 didΔ=+0.003 → **neutral**
- nw_kyc v7 (controller_approved) dims=['caller_id'] engageΔ=+0.000 didΔ=-0.007 → **neutral**
- nw_kyc v8 (controller_approved) dims=['caller_id'] engageΔ=+0.000 didΔ=+0.005 → **neutral**
- nw_renewal v11 (controller_approved) dims=['cohorts', 'welcome_message', 'voice', 'schedule'] engageΔ=-0.013 didΔ=+0.000 → **harmful**
- ks_cancel v15 (controller_auto) dims=['caller_id'] engageΔ=+0.000 didΔ=+0.018 → **neutral**
- nw_kyc v9 (controller_approved) dims=['welcome_message'] engageΔ=+0.020 didΔ=+0.000 → **beneficial**
- nw_renewal v12 (controller_approved) dims=['welcome_message', 'voice'] engageΔ=-0.013 didΔ=+0.000 → **harmful**
- nw_renewal v13 (controller_auto) dims=['caller_id'] engageΔ=+0.000 didΔ=+0.002 → **neutral**
- nw_renewal v14 (controller_approved) dims=['welcome_message'] engageΔ=+0.002 didΔ=+0.000 → **neutral**
- nw_renewal v15 (controller_approved) dims=['voice'] engageΔ=-0.016 didΔ=+0.000 → **harmful**
- nw_kyc v10 (controller_approved) dims=['voice'] engageΔ=+0.006 didΔ=+0.000 → **neutral**

## Governance

```
{
  "approval_requests": 22,
  "decisions": {
    "approved": 20,
    "rejected": 2,
    "expired": 0
  },
  "rejection_reasons": {
    "approver declined (judgement call)": 2
  },
  "applied_via_approval": 19,
  "auto_applied": 16,
  "auto_apply_rejected": 0,
  "apply_conflicts": 0,
  "lapsed": 0,
  "peak_requests_per_24h": {
    "nw_renewal": 2,
    "nw_kyc": 2,
    "ks_cancel": 1
  }
}
```

## Incidents

```
[
  {
    "type": "did_flagged",
    "workflow": "ks_cancel",
    "at": "D2 10:00",
    "flagged_did_share_by_day": {
      "2": 0.0,
      "3": 0.009,
      "4": 0.029,
      "5": 0.027,
      "6": 0.03,
      "7": 0.017,
      "8": 0.0,
      "9": 0.0
    }
  },
  {
    "type": "supervisor_edit",
    "workflow": "ks_cancel",
    "at": "D3 11:30",
    "mttr_minutes": 300,
    "fixed_by": "controller_approved"
  },
  {
    "type": "supervisor_edit",
    "workflow": "nw_renewal",
    "at": "D5 15:00"
  }
]
```

## Decaying variants — share of in-population calls still on the variant, by day after onset

```
{
  "nw_renewal:welcome_message=W3": {
    "2": 0.892,
    "3": 0.896,
    "4": 0.781,
    "5": 0.186,
    "6": 0.22,
    "7": 0.239,
    "8": 0.205,
    "9": 0.212
  }
}
```

Credits used: 5 · validation runs: 1 · LLM fix calls: 0