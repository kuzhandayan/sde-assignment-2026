# Grade report — public_03_load

## Outcomes vs baseline (no-op controller)

| workflow | conclusion rate | Δ | pickup | Δ | engagement | Δ | engagement gap captured | hallucinated calls (base) |
|---|---|---|---|---|---|---|---|---|
| arav_cancel_2 | 0.403 | +18.3% | 0.267 | +8.9% | 0.534 | +7.2% | 47% | 458 (383) |
| arav_kyc_1 | 0.468 | +30.7% | 0.255 | +18.5% | 0.632 | +5.4% | 33% | 417 (349) |
| arav_renewal_0 | 0.480 | +18.9% | 0.287 | +8.9% | 0.592 | +8.0% | 44% | 472 (458) |
| kest_cancel_2 | 0.407 | +20.2% | 0.268 | +9.8% | 0.540 | +8.6% | 56% | 428 (388) |
| kest_kyc_1 | 0.503 | +41.8% | 0.273 | +28.0% | 0.629 | +5.3% | 33% | 465 (309) |
| kest_renewal_0 | 0.482 | +20.1% | 0.285 | +8.6% | 0.597 | +9.4% | 49% | 442 (430) |
| nort_cancel_2 | 0.403 | +18.8% | 0.266 | +9.1% | 0.537 | +7.9% | 54% | 454 (389) |
| nort_kyc_1 | 0.461 | +30.0% | 0.256 | +20.1% | 0.621 | +4.2% | 28% | 419 (346) |
| nort_renewal_0 | 0.484 | +20.7% | 0.286 | +8.5% | 0.599 | +9.8% | 50% | 501 (431) |
| tide_cancel_2 | 0.399 | +17.6% | 0.265 | +8.1% | 0.537 | +7.6% | 50% | 412 (406) |
| tide_kyc_1 | 0.503 | +41.7% | 0.275 | +28.6% | 0.627 | +5.0% | 31% | 405 (339) |
| tide_renewal_0 | 0.480 | +19.5% | 0.285 | +8.4% | 0.591 | +8.3% | 40% | 435 (422) |
| ALL | 0.456 | +24.7% | 0.272 | +13.2% | 0.586 | +7.6% | 42% | 5308 (4650) |

## Changes applied by the controller

100 applied — neutral: 55, beneficial: 44, harmful: 1

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
- kest_cancel_2 v3 (controller_auto) dims=['welcome_message', 'voice', 'caller_id'] engageΔ=+0.009 didΔ=+0.025 → **beneficial**
- arav_renewal_0 v3 (controller_auto) dims=['caller_id'] engageΔ=+0.000 didΔ=+0.055 → **beneficial**
- tide_renewal_0 v3 (controller_auto) dims=['caller_id'] engageΔ=+0.000 didΔ=+0.055 → **beneficial**
- nort_cancel_2 v3 (controller_approved) dims=['cohorts', 'welcome_message', 'voice', 'schedule'] engageΔ=-0.006 didΔ=+0.000 → **neutral**
- tide_cancel_2 v3 (controller_approved) dims=['cohorts', 'voice', 'schedule'] engageΔ=+0.009 didΔ=+0.000 → **neutral**
- nort_cancel_2 v4 (controller_auto) dims=['voice', 'caller_id'] engageΔ=+0.012 didΔ=+0.025 → **beneficial**
- tide_cancel_2 v4 (controller_auto) dims=['welcome_message', 'voice'] engageΔ=+0.009 didΔ=+0.000 → **neutral**
- arav_cancel_2 v3 (controller_approved) dims=['cohorts', 'voice', 'schedule'] engageΔ=+0.004 didΔ=+0.000 → **neutral**
- arav_cancel_2 v4 (controller_auto) dims=['voice', 'caller_id'] engageΔ=+0.007 didΔ=+0.026 → **beneficial**
- kest_renewal_0 v5 (controller_approved) dims=['cohorts', 'welcome_message', 'voice', 'schedule'] engageΔ=+0.034 didΔ=+0.000 → **beneficial**
- kest_cancel_2 v4 (controller_approved) dims=['cohorts', 'welcome_message', 'voice', 'caller_id', 'schedule'] engageΔ=+0.010 didΔ=+0.010 → **beneficial**
- tide_kyc_1 v2 (controller_approved) dims=['cohorts', 'welcome_message', 'voice', 'caller_id', 'schedule'] engageΔ=+0.045 didΔ=+0.055 → **beneficial**
- arav_kyc_1 v2 (controller_approved) dims=['cohorts', 'welcome_message', 'voice', 'caller_id', 'schedule'] engageΔ=+0.045 didΔ=+0.056 → **beneficial**
- nort_renewal_0 v4 (controller_approved) dims=['cohorts', 'welcome_message', 'voice', 'schedule'] engageΔ=+0.034 didΔ=+0.000 → **beneficial**
- nort_renewal_0 v5 (controller_auto) dims=['caller_id'] engageΔ=+0.000 didΔ=+0.040 → **beneficial**
- kest_cancel_2 v5 (controller_auto) dims=['welcome_message'] engageΔ=+0.021 didΔ=+0.000 → **beneficial**
- nort_cancel_2 v5 (controller_auto) dims=['welcome_message', 'voice', 'caller_id'] engageΔ=+0.030 didΔ=+0.011 → **beneficial**
- tide_cancel_2 v5 (controller_auto) dims=['welcome_message', 'caller_id'] engageΔ=+0.007 didΔ=+0.029 → **beneficial**
- arav_cancel_2 v5 (controller_auto) dims=['caller_id'] engageΔ=+0.000 didΔ=+0.011 → **neutral**
- nort_kyc_1 v2 (controller_approved) dims=['cohorts', 'welcome_message', 'voice', 'caller_id', 'schedule'] engageΔ=+0.045 didΔ=+0.062 → **beneficial**
- kest_kyc_1 v2 (controller_approved) dims=['cohorts', 'welcome_message', 'voice', 'caller_id', 'schedule'] engageΔ=+0.045 didΔ=+0.064 → **beneficial**
- arav_renewal_0 v4 (controller_approved) dims=['cohorts', 'welcome_message', 'voice', 'schedule'] engageΔ=+0.034 didΔ=+0.000 → **beneficial**
- kest_cancel_2 v6 (controller_auto) dims=['welcome_message', 'voice'] engageΔ=+0.024 didΔ=+0.000 → **beneficial**
- nort_cancel_2 v6 (controller_auto) dims=['welcome_message', 'voice'] engageΔ=+0.030 didΔ=+0.000 → **beneficial**
- tide_cancel_2 v6 (controller_auto) dims=['welcome_message', 'voice', 'caller_id'] engageΔ=+0.033 didΔ=+0.012 → **beneficial**
- arav_cancel_2 v6 (controller_auto) dims=['voice'] engageΔ=+0.017 didΔ=+0.000 → **beneficial**
- kest_cancel_2 v7 (controller_auto) dims=['voice'] engageΔ=+0.016 didΔ=+0.000 → **beneficial**
- nort_cancel_2 v7 (controller_auto) dims=['welcome_message', 'voice'] engageΔ=+0.029 didΔ=+0.000 → **beneficial**
- tide_cancel_2 v7 (controller_auto) dims=['welcome_message', 'voice'] engageΔ=+0.024 didΔ=+0.000 → **beneficial**
- kest_cancel_2 v8 (controller_auto) dims=['voice'] engageΔ=+0.016 didΔ=+0.000 → **beneficial**
- arav_cancel_2 v7 (controller_auto) dims=['voice'] engageΔ=+0.016 didΔ=+0.000 → **beneficial**
- tide_cancel_2 v8 (controller_auto) dims=['voice'] engageΔ=+0.016 didΔ=+0.000 → **beneficial**
- nort_renewal_0 v6 (controller_approved) dims=['welcome_message', 'voice'] engageΔ=+0.106 didΔ=+0.000 → **beneficial**
- arav_cancel_2 v8 (controller_auto) dims=['voice'] engageΔ=+0.017 didΔ=+0.000 → **beneficial**
- nort_renewal_0 v7 (controller_approved) dims=['cohorts', 'voice', 'schedule'] engageΔ=+0.000 didΔ=+0.000 → **neutral**
- kest_renewal_0 v6 (controller_approved) dims=['cohorts', 'welcome_message', 'voice', 'schedule'] engageΔ=+0.121 didΔ=+0.000 → **beneficial**
- arav_renewal_0 v5 (controller_approved) dims=['cohorts', 'welcome_message', 'schedule'] engageΔ=+0.105 didΔ=+0.000 → **beneficial**
- kest_kyc_1 v3 (controller_approved) dims=['caller_id'] engageΔ=+0.000 didΔ=+0.535 → **beneficial**
- tide_renewal_0 v4 (controller_approved) dims=['cohorts', 'welcome_message', 'voice', 'schedule'] engageΔ=+0.034 didΔ=+0.000 → **beneficial**
- nort_cancel_2 v8 (controller_approved) dims=['cohorts', 'voice', 'schedule'] engageΔ=+0.000 didΔ=+0.000 → **neutral**
- tide_kyc_1 v3 (controller_approved) dims=['caller_id'] engageΔ=+0.000 didΔ=+0.565 → **beneficial**
- tide_cancel_2 v9 (controller_approved) dims=['cohorts', 'welcome_message', 'schedule'] engageΔ=-0.017 didΔ=+0.000 → **harmful**
- arav_cancel_2 v9 (controller_auto) dims=['welcome_message'] engageΔ=+0.006 didΔ=+0.000 → **neutral**
- arav_renewal_0 v6 (controller_approved) dims=['cohorts', 'welcome_message', 'voice', 'schedule'] engageΔ=-0.003 didΔ=+0.000 → **neutral**
- nort_cancel_2 v9 (controller_auto) dims=['voice'] engageΔ=+0.000 didΔ=+0.000 → **neutral**
- nort_renewal_0 v8 (controller_approved) dims=['cohorts', 'voice', 'schedule'] engageΔ=+0.007 didΔ=+0.000 → **neutral**
- arav_cancel_2 v10 (controller_auto) dims=['welcome_message'] engageΔ=+0.010 didΔ=+0.000 → **beneficial**
- arav_cancel_2 v11 (controller_auto) dims=['welcome_message'] engageΔ=+0.010 didΔ=+0.000 → **beneficial**
- nort_renewal_0 v9 (controller_auto) dims=['caller_id'] engageΔ=+0.000 didΔ=-0.013 → **neutral**
- kest_renewal_0 v7 (controller_approved) dims=['cohorts', 'welcome_message', 'voice', 'schedule'] engageΔ=-0.002 didΔ=+0.000 → **neutral**
- kest_renewal_0 v8 (controller_auto) dims=['caller_id'] engageΔ=+0.000 didΔ=-0.013 → **neutral**
- arav_renewal_0 v7 (controller_approved) dims=['cohorts', 'voice', 'schedule'] engageΔ=+0.003 didΔ=+0.000 → **neutral**
- nort_renewal_0 v10 (controller_auto) dims=['caller_id'] engageΔ=+0.000 didΔ=+0.013 → **neutral**
- kest_renewal_0 v9 (controller_auto) dims=['caller_id'] engageΔ=+0.000 didΔ=+0.013 → **neutral**
- arav_renewal_0 v8 (controller_auto) dims=['caller_id'] engageΔ=+0.000 didΔ=-0.012 → **neutral**
- tide_renewal_0 v5 (controller_approved) dims=['cohorts', 'welcome_message', 'voice', 'schedule'] engageΔ=+0.116 didΔ=+0.000 → **beneficial**
- tide_renewal_0 v6 (controller_auto) dims=['caller_id'] engageΔ=+0.000 didΔ=-0.012 → **neutral**
- kest_renewal_0 v10 (controller_approved) dims=['welcome_message'] engageΔ=-0.002 didΔ=+0.000 → **neutral**
- arav_renewal_0 v9 (controller_auto) dims=['caller_id'] engageΔ=+0.000 didΔ=+0.013 → **neutral**
- tide_renewal_0 v7 (controller_auto) dims=['caller_id'] engageΔ=+0.000 didΔ=+0.013 → **neutral**
- kest_kyc_1 v4 (controller_approved) dims=['welcome_message', 'voice', 'schedule'] engageΔ=+0.096 didΔ=+0.000 → **beneficial**
- nort_kyc_1 v3 (controller_approved) dims=['welcome_message', 'voice', 'caller_id', 'schedule'] engageΔ=+0.064 didΔ=+0.532 → **beneficial**
- tide_cancel_2 v10 (controller_approved) dims=['cohorts', 'voice', 'schedule'] engageΔ=-0.002 didΔ=+0.000 → **neutral**
- arav_cancel_2 v12 (controller_auto) dims=['welcome_message'] engageΔ=+0.007 didΔ=+0.000 → **neutral**
- tide_cancel_2 v11 (controller_auto) dims=['welcome_message'] engageΔ=+0.003 didΔ=+0.000 → **neutral**
- arav_kyc_1 v3 (controller_approved) dims=['cohorts', 'welcome_message', 'voice', 'caller_id', 'schedule'] engageΔ=+0.100 didΔ=+0.541 → **beneficial**
- nort_renewal_0 v11 (controller_approved) dims=['welcome_message'] engageΔ=-0.004 didΔ=+0.000 → **neutral**
- tide_kyc_1 v4 (controller_approved) dims=['cohorts', 'welcome_message', 'voice', 'schedule'] engageΔ=+0.079 didΔ=+0.000 → **beneficial**
- tide_renewal_0 v8 (controller_approved) dims=['cohorts', 'welcome_message', 'voice', 'schedule'] engageΔ=+0.005 didΔ=+0.000 → **neutral**
- tide_cancel_2 v12 (controller_auto) dims=['welcome_message'] engageΔ=-0.002 didΔ=+0.000 → **neutral**
- tide_cancel_2 v13 (controller_auto) dims=['welcome_message'] engageΔ=+0.003 didΔ=+0.000 → **neutral**
- arav_renewal_0 v10 (controller_approved) dims=['voice'] engageΔ=+0.001 didΔ=+0.000 → **neutral**
- kest_renewal_0 v11 (controller_approved) dims=['welcome_message'] engageΔ=-0.001 didΔ=+0.000 → **neutral**
- tide_cancel_2 v14 (controller_auto) dims=['welcome_message'] engageΔ=+0.003 didΔ=+0.000 → **neutral**
- arav_kyc_1 v4 (controller_approved) dims=['caller_id'] engageΔ=+0.000 didΔ=-0.009 → **neutral**
- tide_kyc_1 v5 (controller_approved) dims=['voice', 'caller_id'] engageΔ=+0.016 didΔ=-0.006 → **beneficial**
- tide_cancel_2 v15 (controller_auto) dims=['welcome_message'] engageΔ=+0.003 didΔ=+0.000 → **neutral**
- nort_kyc_1 v4 (controller_approved) dims=['cohorts', 'voice', 'caller_id'] engageΔ=+0.020 didΔ=-0.010 → **beneficial**
- kest_kyc_1 v5 (controller_approved) dims=['caller_id'] engageΔ=+0.000 didΔ=-0.006 → **neutral**
- tide_cancel_2 v16 (controller_auto) dims=['welcome_message'] engageΔ=+0.003 didΔ=+0.000 → **neutral**
- tide_cancel_2 v17 (controller_auto) dims=['welcome_message'] engageΔ=+0.003 didΔ=+0.000 → **neutral**
- nort_kyc_1 v5 (controller_approved) dims=['caller_id'] engageΔ=+0.000 didΔ=+0.007 → **neutral**
- arav_kyc_1 v5 (controller_approved) dims=['caller_id'] engageΔ=+0.000 didΔ=+0.007 → **neutral**
- tide_kyc_1 v6 (controller_approved) dims=['caller_id'] engageΔ=+0.000 didΔ=+0.004 → **neutral**
- nort_cancel_2 v10 (controller_approved) dims=['cohorts', 'voice', 'schedule'] engageΔ=-0.009 didΔ=+0.000 → **neutral**
- arav_renewal_0 v11 (controller_approved) dims=['welcome_message'] engageΔ=-0.004 didΔ=+0.000 → **neutral**
- tide_cancel_2 v18 (controller_approved) dims=['cohorts', 'voice', 'schedule'] engageΔ=+0.000 didΔ=+0.000 → **neutral**
- nort_cancel_2 v11 (controller_auto) dims=['voice'] engageΔ=+0.001 didΔ=+0.000 → **neutral**
- nort_renewal_0 v12 (controller_approved) dims=['voice'] engageΔ=+0.000 didΔ=+0.000 → **neutral**

## Governance

```
{
  "approval_requests": 55,
  "decisions": {
    "approved": 48,
    "rejected": 5,
    "expired": 0
  },
  "rejection_reasons": {
    "approver declined (judgement call)": 5
  },
  "applied_via_approval": 46,
  "auto_applied": 54,
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
    "tide_cancel_2": 2,
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
    "3": 0.856,
    "4": 0.858
  },
  "kest_renewal_0:welcome_message=W3": {
    "3": 0.868,
    "4": 0.87
  },
  "arav_renewal_0:welcome_message=W3": {
    "3": 0.868,
    "4": 0.9
  },
  "tide_renewal_0:welcome_message=W3": {
    "4": 0.908
  }
}
```

Credits used: 0 · validation runs: 0 · LLM fix calls: 0