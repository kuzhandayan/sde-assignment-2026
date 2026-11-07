# Grade report — public_01_dev

## Outcomes vs baseline (no-op controller)

| workflow | conclusion rate | Δ | pickup | Δ | engagement | Δ | engagement gap captured | hallucinated calls (base) |
|---|---|---|---|---|---|---|---|---|
| ks_cancel | 0.387 | +13.4% | 0.263 | +9.6% | 0.512 | +2.4% | 21% | 67 (52) |
| nw_kyc | 0.470 | +24.8% | 0.284 | +17.2% | 0.638 | +4.2% | 38% | 22 (21) |
| nw_renewal | 0.469 | +11.6% | 0.284 | +8.5% | 0.560 | +2.3% | 28% | 50 (39) |
| ALL | 0.432 | +15.2% | 0.274 | +10.6% | 0.554 | +2.9% | 27% | 139 (112) |

## Changes applied by the controller

33 applied — neutral: 13, harmful: 3, beneficial: 17

- nw_renewal v2 (controller_auto) dims=['caller_id'] engageΔ=+0.000 didΔ=-0.013 → **neutral**
- ks_cancel v2 (controller_auto) dims=['welcome_message', 'voice', 'caller_id'] engageΔ=-0.001 didΔ=+0.006 → **neutral**
- ks_cancel v3 (controller_auto) dims=['welcome_message', 'voice'] engageΔ=-0.013 didΔ=+0.000 → **harmful**
- ks_cancel v4 (controller_approved) dims=['cohorts', 'welcome_message', 'voice', 'schedule'] engageΔ=-0.009 didΔ=+0.000 → **neutral**
- nw_kyc v2 (controller_approved) dims=['cohorts', 'welcome_message', 'voice', 'caller_id', 'schedule'] engageΔ=+0.045 didΔ=+0.041 → **beneficial**
- nw_renewal v3 (controller_approved) dims=['cohorts', 'welcome_message', 'voice', 'schedule'] engageΔ=+0.034 didΔ=+0.000 → **beneficial**
- ks_cancel v5 (controller_auto) dims=['voice'] engageΔ=+0.016 didΔ=+0.000 → **beneficial**
- ks_cancel v6 (controller_auto) dims=['voice'] engageΔ=+0.016 didΔ=+0.000 → **beneficial**
- nw_renewal v4 (controller_auto) dims=['caller_id'] engageΔ=+0.000 didΔ=+0.018 → **neutral**
- ks_cancel v7 (controller_auto) dims=['voice'] engageΔ=+0.013 didΔ=+0.000 → **beneficial**
- ks_cancel v8 (controller_auto) dims=['caller_id'] engageΔ=+0.000 didΔ=+0.024 → **beneficial**
- nw_renewal v5 (controller_approved) dims=['welcome_message', 'voice'] engageΔ=+0.036 didΔ=+0.000 → **beneficial**
- ks_cancel v9 (controller_auto) dims=['caller_id'] engageΔ=+0.000 didΔ=+0.011 → **neutral**
- ks_cancel v10 (controller_auto) dims=['voice'] engageΔ=+0.017 didΔ=+0.000 → **beneficial**
- nw_renewal v6 (controller_approved) dims=['welcome_message'] engageΔ=+0.061 didΔ=+0.000 → **beneficial**
- ks_cancel v11 (controller_auto) dims=['welcome_message'] engageΔ=+0.018 didΔ=+0.000 → **beneficial**
- nw_kyc v3 (controller_approved) dims=['welcome_message', 'voice'] engageΔ=+0.032 didΔ=+0.000 → **beneficial**
- nw_renewal v7 (controller_auto) dims=['caller_id'] engageΔ=+0.000 didΔ=+0.036 → **beneficial**
- ks_cancel v12 (controller_auto) dims=['voice'] engageΔ=-0.016 didΔ=+0.000 → **harmful**
- nw_renewal v8 (controller_auto) dims=['caller_id'] engageΔ=+0.000 didΔ=-0.012 → **neutral**
- ks_cancel v13 (controller_auto) dims=['welcome_message', 'voice'] engageΔ=+0.007 didΔ=+0.000 → **neutral**
- ks_cancel v14 (controller_auto) dims=['voice'] engageΔ=-0.016 didΔ=+0.000 → **harmful**
- nw_kyc v4 (controller_approved) dims=['welcome_message'] engageΔ=+0.011 didΔ=+0.000 → **beneficial**
- nw_kyc v5 (controller_approved) dims=['voice'] engageΔ=+0.010 didΔ=+0.000 → **neutral**
- ks_cancel v15 (controller_auto) dims=['welcome_message'] engageΔ=+0.004 didΔ=+0.000 → **neutral**
- nw_renewal v9 (controller_approved) dims=['voice'] engageΔ=+0.000 didΔ=+0.000 → **neutral**
- nw_kyc v6 (controller_approved) dims=['caller_id'] engageΔ=+0.000 didΔ=+0.327 → **beneficial**
- nw_renewal v10 (controller_approved) dims=['voice'] engageΔ=+0.001 didΔ=+0.000 → **neutral**
- nw_renewal v11 (controller_approved) dims=['welcome_message'] engageΔ=+0.060 didΔ=+0.000 → **beneficial**
- ks_cancel v16 (controller_auto) dims=['voice'] engageΔ=-0.004 didΔ=+0.000 → **neutral**
- nw_kyc v7 (controller_approved) dims=['welcome_message', 'voice'] engageΔ=+0.036 didΔ=+0.000 → **beneficial**
- nw_kyc v8 (controller_approved) dims=['caller_id'] engageΔ=+0.000 didΔ=-0.004 → **neutral**
- nw_renewal v12 (controller_approved) dims=['welcome_message'] engageΔ=+0.018 didΔ=+0.000 → **beneficial**

## Governance

```
{
  "approval_requests": 15,
  "decisions": {
    "approved": 15,
    "expired": 0
  },
  "rejection_reasons": {},
  "applied_via_approval": 15,
  "auto_applied": 18,
  "auto_apply_rejected": 0,
  "apply_conflicts": 0,
  "lapsed": 0,
  "peak_requests_per_24h": {
    "nw_renewal": 2,
    "nw_kyc": 1,
    "ks_cancel": 1
  }
}
```

## Incidents

```
[]
```

## Decaying variants — share of in-population calls still on the variant, by day after onset

```
{
  "nw_renewal:welcome_message=W3": {
    "3": 0.901,
    "4": 0.9,
    "5": 0.743,
    "6": 0.203,
    "7": 0.115
  }
}
```

Credits used: 0 · validation runs: 0 · LLM fix calls: 0