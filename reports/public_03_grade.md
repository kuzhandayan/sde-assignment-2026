# Grade report — public_03_load

## Outcomes vs baseline (no-op controller)

| workflow | conclusion rate | Δ | pickup | Δ | engagement | Δ | engagement gap captured | hallucinated calls (base) |
|---|---|---|---|---|---|---|---|---|
| arav_cancel_2 | 0.407 | +19.4% | 0.266 | +8.6% | 0.542 | +8.8% | 57% | 448 (383) |
| arav_kyc_1 | 0.468 | +30.8% | 0.255 | +18.6% | 0.632 | +5.5% | 33% | 458 (349) |
| arav_renewal_0 | 0.480 | +18.7% | 0.286 | +8.6% | 0.595 | +8.5% | 49% | 478 (458) |
| kest_cancel_2 | 0.405 | +19.8% | 0.267 | +9.3% | 0.539 | +8.4% | 54% | 441 (388) |
| kest_kyc_1 | 0.504 | +42.0% | 0.273 | +27.9% | 0.630 | +5.6% | 32% | 457 (309) |
| kest_renewal_0 | 0.485 | +20.8% | 0.287 | +9.2% | 0.596 | +9.1% | 52% | 465 (430) |
| nort_cancel_2 | 0.407 | +20.1% | 0.267 | +9.5% | 0.540 | +8.6% | 60% | 416 (389) |
| nort_kyc_1 | 0.465 | +31.3% | 0.256 | +20.1% | 0.628 | +5.3% | 33% | 388 (346) |
| nort_renewal_0 | 0.481 | +20.1% | 0.287 | +9.0% | 0.591 | +8.4% | 48% | 451 (431) |
| tide_cancel_2 | 0.409 | +20.3% | 0.266 | +8.8% | 0.544 | +9.1% | 60% | 444 (406) |
| tide_kyc_1 | 0.502 | +41.3% | 0.273 | +27.9% | 0.630 | +5.4% | 33% | 426 (339) |
| tide_renewal_0 | 0.475 | +18.3% | 0.285 | +8.6% | 0.584 | +7.0% | 35% | 437 (422) |
| ALL | 0.457 | +25.1% | 0.272 | +13.3% | 0.588 | +7.8% | 44% | 5309 (4650) |

## Changes applied by the controller

83 applied — neutral: 42, beneficial: 41

- nort_renewal_0 v2 (controller_auto) dims=['caller_id'] engageΔ=+0.000 didΔ=-0.013 → **neutral**
- nort_cancel_2 v2 (controller_auto) dims=['welcome_message', 'voice', 'caller_id'] engageΔ=-0.001 didΔ=+0.006 → **neutral**
- kest_renewal_0 v2 (controller_auto) dims=['caller_id'] engageΔ=+0.000 didΔ=-0.013 → **neutral**
- kest_cancel_2 v2 (controller_auto) dims=['welcome_message', 'voice', 'caller_id'] engageΔ=-0.001 didΔ=+0.006 → **neutral**
- arav_renewal_0 v2 (controller_auto) dims=['caller_id'] engageΔ=+0.000 didΔ=-0.013 → **neutral**
- arav_cancel_2 v2 (controller_auto) dims=['welcome_message', 'voice', 'caller_id'] engageΔ=-0.001 didΔ=+0.006 → **neutral**
- tide_renewal_0 v2 (controller_auto) dims=['caller_id'] engageΔ=+0.000 didΔ=-0.013 → **neutral**
- tide_cancel_2 v2 (controller_auto) dims=['welcome_message', 'voice', 'caller_id'] engageΔ=-0.001 didΔ=+0.006 → **neutral**
- nort_renewal_0 v3 (controller_auto) dims=['caller_id'] engageΔ=+0.000 didΔ=+0.019 → **neutral**
- kest_renewal_0 v3 (controller_auto) dims=['caller_id'] engageΔ=+0.000 didΔ=+0.019 → **neutral**
- kest_renewal_0 v4 (controller_auto) dims=['caller_id'] engageΔ=+0.000 didΔ=+0.035 → **beneficial**
- kest_cancel_2 v3 (controller_auto) dims=['voice', 'caller_id'] engageΔ=+0.005 didΔ=+0.025 → **beneficial**
- arav_renewal_0 v3 (controller_auto) dims=['caller_id'] engageΔ=+0.000 didΔ=+0.055 → **beneficial**
- tide_renewal_0 v3 (controller_auto) dims=['caller_id'] engageΔ=+0.000 didΔ=+0.055 → **beneficial**
- nort_cancel_2 v3 (controller_approved) dims=['cohorts', 'welcome_message', 'voice', 'schedule'] engageΔ=+0.013 didΔ=+0.000 → **beneficial**
- tide_cancel_2 v3 (controller_approved) dims=['cohorts', 'voice', 'schedule'] engageΔ=+0.019 didΔ=+0.000 → **beneficial**
- nort_cancel_2 v4 (controller_auto) dims=['voice', 'caller_id'] engageΔ=+0.011 didΔ=+0.025 → **beneficial**
- tide_cancel_2 v4 (controller_auto) dims=['welcome_message', 'voice'] engageΔ=+0.030 didΔ=+0.000 → **beneficial**
- arav_cancel_2 v3 (controller_approved) dims=['cohorts', 'welcome_message', 'voice', 'schedule'] engageΔ=+0.031 didΔ=+0.000 → **beneficial**
- arav_cancel_2 v4 (controller_auto) dims=['welcome_message', 'voice', 'caller_id'] engageΔ=+0.021 didΔ=+0.026 → **beneficial**
- kest_renewal_0 v5 (controller_approved) dims=['cohorts', 'welcome_message', 'voice', 'schedule'] engageΔ=+0.034 didΔ=+0.000 → **beneficial**
- kest_cancel_2 v4 (controller_approved) dims=['cohorts', 'voice', 'caller_id', 'schedule'] engageΔ=+0.005 didΔ=+0.010 → **neutral**
- tide_kyc_1 v2 (controller_approved) dims=['cohorts', 'welcome_message', 'voice', 'caller_id', 'schedule'] engageΔ=+0.045 didΔ=+0.055 → **beneficial**
- arav_kyc_1 v2 (controller_approved) dims=['cohorts', 'welcome_message', 'voice', 'caller_id', 'schedule'] engageΔ=+0.045 didΔ=+0.056 → **beneficial**
- nort_renewal_0 v4 (controller_approved) dims=['cohorts', 'welcome_message', 'voice', 'schedule'] engageΔ=+0.034 didΔ=+0.000 → **beneficial**
- nort_renewal_0 v5 (controller_auto) dims=['caller_id'] engageΔ=+0.000 didΔ=+0.040 → **beneficial**
- kest_cancel_2 v5 (controller_auto) dims=['welcome_message', 'voice'] engageΔ=+0.023 didΔ=+0.000 → **beneficial**
- nort_cancel_2 v5 (controller_auto) dims=['welcome_message', 'voice', 'caller_id'] engageΔ=+0.038 didΔ=+0.011 → **beneficial**
- tide_cancel_2 v5 (controller_auto) dims=['welcome_message', 'voice', 'caller_id'] engageΔ=+0.021 didΔ=+0.029 → **beneficial**
- arav_cancel_2 v5 (controller_auto) dims=['welcome_message', 'voice', 'caller_id'] engageΔ=+0.021 didΔ=+0.011 → **beneficial**
- nort_kyc_1 v2 (controller_approved) dims=['cohorts', 'welcome_message', 'voice', 'caller_id', 'schedule'] engageΔ=+0.045 didΔ=+0.062 → **beneficial**
- kest_kyc_1 v2 (controller_approved) dims=['cohorts', 'welcome_message', 'voice', 'caller_id', 'schedule'] engageΔ=+0.045 didΔ=+0.064 → **beneficial**
- arav_renewal_0 v4 (controller_approved) dims=['cohorts', 'welcome_message', 'voice', 'schedule'] engageΔ=+0.034 didΔ=+0.000 → **beneficial**
- kest_cancel_2 v6 (controller_auto) dims=['welcome_message', 'voice'] engageΔ=+0.022 didΔ=+0.000 → **beneficial**
- nort_cancel_2 v6 (controller_auto) dims=['voice'] engageΔ=+0.016 didΔ=+0.000 → **beneficial**
- tide_cancel_2 v6 (controller_auto) dims=['voice', 'caller_id'] engageΔ=+0.016 didΔ=+0.012 → **beneficial**
- arav_cancel_2 v6 (controller_auto) dims=['welcome_message'] engageΔ=+0.007 didΔ=+0.000 → **neutral**
- kest_cancel_2 v7 (controller_auto) dims=['welcome_message', 'voice'] engageΔ=+0.032 didΔ=+0.000 → **beneficial**
- nort_cancel_2 v7 (controller_auto) dims=['voice'] engageΔ=+0.012 didΔ=+0.000 → **beneficial**
- tide_cancel_2 v7 (controller_auto) dims=['welcome_message'] engageΔ=+0.006 didΔ=+0.000 → **neutral**
- nort_renewal_0 v6 (controller_approved) dims=['welcome_message', 'voice'] engageΔ=+0.078 didΔ=+0.000 → **beneficial**
- nort_cancel_2 v8 (controller_auto) dims=['welcome_message'] engageΔ=+0.006 didΔ=+0.000 → **neutral**
- arav_cancel_2 v7 (controller_auto) dims=['voice'] engageΔ=+0.016 didΔ=+0.000 → **beneficial**
- nort_renewal_0 v7 (controller_approved) dims=['cohorts', 'welcome_message', 'schedule'] engageΔ=+0.005 didΔ=+0.000 → **neutral**
- kest_renewal_0 v6 (controller_approved) dims=['cohorts', 'welcome_message', 'voice', 'schedule'] engageΔ=+0.122 didΔ=+0.000 → **beneficial**
- arav_renewal_0 v5 (controller_approved) dims=['cohorts', 'welcome_message', 'voice', 'schedule'] engageΔ=+0.113 didΔ=+0.000 → **beneficial**
- nort_cancel_2 v9 (controller_auto) dims=['welcome_message'] engageΔ=+0.005 didΔ=+0.000 → **neutral**
- kest_cancel_2 v8 (controller_auto) dims=['welcome_message'] engageΔ=+0.006 didΔ=+0.000 → **neutral**
- tide_cancel_2 v8 (controller_auto) dims=['welcome_message'] engageΔ=+0.006 didΔ=+0.000 → **neutral**
- kest_kyc_1 v3 (controller_approved) dims=['caller_id'] engageΔ=+0.000 didΔ=+0.535 → **beneficial**
- tide_renewal_0 v4 (controller_approved) dims=['cohorts', 'welcome_message', 'voice', 'schedule'] engageΔ=+0.034 didΔ=+0.000 → **beneficial**
- tide_kyc_1 v3 (controller_approved) dims=['caller_id'] engageΔ=+0.000 didΔ=+0.565 → **beneficial**
- arav_renewal_0 v6 (controller_approved) dims=['cohorts', 'voice', 'schedule'] engageΔ=+0.004 didΔ=+0.000 → **neutral**
- nort_renewal_0 v8 (controller_auto) dims=['caller_id'] engageΔ=+0.000 didΔ=-0.013 → **neutral**
- kest_renewal_0 v7 (controller_approved) dims=['cohorts', 'voice', 'schedule'] engageΔ=+0.006 didΔ=+0.000 → **neutral**
- kest_renewal_0 v8 (controller_auto) dims=['caller_id'] engageΔ=+0.000 didΔ=-0.013 → **neutral**
- arav_renewal_0 v7 (controller_auto) dims=['caller_id'] engageΔ=+0.000 didΔ=-0.013 → **neutral**
- nort_renewal_0 v9 (controller_auto) dims=['caller_id'] engageΔ=+0.000 didΔ=+0.013 → **neutral**
- kest_renewal_0 v9 (controller_auto) dims=['caller_id'] engageΔ=+0.000 didΔ=+0.013 → **neutral**
- arav_renewal_0 v8 (controller_auto) dims=['caller_id'] engageΔ=+0.000 didΔ=+0.013 → **neutral**
- tide_renewal_0 v5 (controller_approved) dims=['cohorts', 'welcome_message', 'voice', 'schedule'] engageΔ=+0.106 didΔ=+0.000 → **beneficial**
- tide_renewal_0 v6 (controller_auto) dims=['caller_id'] engageΔ=+0.000 didΔ=-0.012 → **neutral**
- kest_renewal_0 v10 (controller_approved) dims=['cohorts', 'voice', 'schedule'] engageΔ=-0.000 didΔ=+0.000 → **neutral**
- kest_kyc_1 v4 (controller_approved) dims=['cohorts', 'welcome_message', 'voice', 'schedule'] engageΔ=+0.096 didΔ=+0.000 → **beneficial**
- tide_renewal_0 v7 (controller_auto) dims=['caller_id'] engageΔ=+0.000 didΔ=+0.012 → **neutral**
- nort_kyc_1 v3 (controller_approved) dims=['welcome_message', 'voice', 'caller_id', 'schedule'] engageΔ=+0.100 didΔ=+0.532 → **beneficial**
- nort_renewal_0 v10 (controller_approved) dims=['welcome_message', 'voice'] engageΔ=+0.022 didΔ=+0.000 → **beneficial**
- arav_kyc_1 v3 (controller_approved) dims=['cohorts', 'welcome_message', 'voice', 'caller_id', 'schedule'] engageΔ=+0.100 didΔ=+0.541 → **beneficial**
- tide_kyc_1 v4 (controller_approved) dims=['cohorts', 'welcome_message', 'voice', 'schedule'] engageΔ=+0.096 didΔ=+0.000 → **beneficial**
- tide_renewal_0 v8 (controller_approved) dims=['cohorts', 'welcome_message', 'schedule'] engageΔ=-0.003 didΔ=+0.000 → **neutral**
- nort_renewal_0 v11 (controller_approved) dims=['cohorts', 'voice', 'schedule'] engageΔ=+0.024 didΔ=+0.000 → **beneficial**
- kest_renewal_0 v11 (controller_approved) dims=['welcome_message'] engageΔ=-0.001 didΔ=+0.000 → **neutral**
- tide_renewal_0 v9 (controller_approved) dims=['cohorts', 'welcome_message', 'voice', 'schedule'] engageΔ=-0.004 didΔ=+0.000 → **neutral**
- arav_kyc_1 v4 (controller_approved) dims=['cohorts', 'voice', 'caller_id'] engageΔ=+0.000 didΔ=-0.009 → **neutral**
- arav_renewal_0 v9 (controller_approved) dims=['voice'] engageΔ=+0.001 didΔ=+0.000 → **neutral**
- tide_kyc_1 v5 (controller_approved) dims=['caller_id'] engageΔ=+0.000 didΔ=-0.006 → **neutral**
- nort_kyc_1 v4 (controller_approved) dims=['caller_id'] engageΔ=+0.000 didΔ=-0.010 → **neutral**
- kest_kyc_1 v5 (controller_approved) dims=['caller_id'] engageΔ=+0.000 didΔ=-0.006 → **neutral**
- nort_kyc_1 v5 (controller_approved) dims=['caller_id'] engageΔ=+0.000 didΔ=+0.007 → **neutral**
- arav_kyc_1 v5 (controller_approved) dims=['caller_id'] engageΔ=+0.000 didΔ=+0.007 → **neutral**
- tide_kyc_1 v6 (controller_approved) dims=['caller_id'] engageΔ=+0.000 didΔ=+0.004 → **neutral**
- tide_renewal_0 v10 (controller_approved) dims=['voice'] engageΔ=-0.000 didΔ=+0.000 → **neutral**
- kest_renewal_0 v12 (controller_approved) dims=['voice'] engageΔ=+0.005 didΔ=+0.000 → **neutral**

## Governance

```
{
  "approval_requests": 52,
  "decisions": {
    "approved": 44,
    "rejected": 6,
    "expired": 0
  },
  "rejection_reasons": {
    "approver declined (judgement call)": 6
  },
  "applied_via_approval": 41,
  "auto_applied": 42,
  "auto_apply_rejected": 0,
  "apply_conflicts": 0,
  "lapsed": 0,
  "peak_requests_per_24h": {
    "nort_renewal_0": 2,
    "nort_kyc_1": 2,
    "nort_cancel_2": 1,
    "arav_renewal_0": 2,
    "arav_kyc_1": 2,
    "arav_cancel_2": 1,
    "tide_renewal_0": 2,
    "tide_kyc_1": 2,
    "tide_cancel_2": 1,
    "kest_renewal_0": 2,
    "kest_kyc_1": 2,
    "kest_cancel_2": 1
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
  "nort_renewal_0:welcome_message=W3": {
    "3": 0.953,
    "4": 0.957
  },
  "kest_renewal_0:welcome_message=W3": {
    "3": 0.917,
    "4": 0.915
  },
  "arav_renewal_0:welcome_message=W3": {
    "3": 0.951,
    "4": 0.951
  },
  "tide_renewal_0:welcome_message=W3": {
    "4": 0.888
  }
}
```

Credits used: 0 · validation runs: 0 · LLM fix calls: 0