"""Every tunable number in the controller, in one place, with the reason it has that value.

Nothing here is read from a scenario file. These are design choices; SUBMISSION.md section 5 explains them.
"""

# ---- loop -------------------------------------------------------------------------------------------------
STEP_MINUTES = 30            # sim minutes per /sim/advance. Approvals have a 2h apply window, so 30 min leaves
                             # three chances to apply; incidents are noticed within one step.
DID_REVIEW_EVERY_MIN = 60    # caller-ID health check cadence (sim minutes)

# ---- experiments (welcome_message x voice) -----------------------------------------------------------------
EXP_HALF_LIFE_DAYS = 1.5     # discounting of old evidence, so a decaying winner shows up within ~1 day
EXP_MIN_ARM_N = 300          # connected calls an arm needs before it can be promoted
EXP_PROMOTE_PBEST = 0.95     # posterior P(best) needed to promote
EXP_ALPHA = 0.05             # family-wise error for promotion tests (Holm across arms)
EXP_DROP_ALPHA = 0.01        # an arm significantly worse than the best at this level is dropped (harm stop)
EXP_DROP_MIN_N = 150
EXP_START_CONTROL_SHARE = 0.5  # first exploration keeps half the traffic on the business default ...
EXP_START_CONTROL_SHARE_GUARDRAIL = 0.7  # ... and 70% where engagement is only the guardrail (pickup-primary)
EXP_FLOOR = 0.05             # share kept on each live non-winning arm after promotion (decay detection)
EXP_MIN_CHANGE_TV = 0.15     # don't spend an approval / config version on an exploring move smaller than this
EXP_DECAY_ALPHA = 0.01       # winner's recent rate vs its rate at promotion
EXP_DECAY_MIN_REL_DROP = 0.06
EXP_DECAY_WINDOW_DAYS = 1

# ---- segment cohorts for variants --------------------------------------------------------------------------
SEG_MIN_CONNECTED = 400      # a candidate segment needs this many connected calls before it is tested
SEG_MIN_SHARE = 0.04         # ... and at least this share of the workflow's connected calls
SEG_ALPHA = 0.05             # Bonferroni-corrected across every (segment, dim) tested in a review
SEG_MAX = 6                  # at most this many variant segment cohorts per workflow
SEG_START_DAY = 1            # earliest sim day segment discovery runs

# ---- call-time schedule ----------------------------------------------------------------------------------
SCHED_MAX_CELLS = 12         # cohorts used for call-time (leaves room for SEG_MAX within the 20-cohort cap)
SCHED_MIN_CELL_DIALS = 1200  # history dials a cell needs to get its own hour table
SCHED_SHRINK_K = 60          # pseudo-dials pulling a cell's hour profile toward the population profile
SCHED_GAMMA = 3.0            # sharpening of relative hour advantage into weights
SCHED_W_MIN, SCHED_W_MAX = 0.25, 4.0   # never 0: an hour with weight 0 can leave capacity unused
SCHED_MIN_CHANGE_L1 = 0.20   # re-propose tables only if they moved this much
SCHED_HALF_LIFE_DAYS = 7.0
GUARDRAIL_CHECK_MIN_DIALS = 1500

# ---- caller ID -------------------------------------------------------------------------------------------
DID_PROBE_SHARE = 0.05       # share per unknown caller ID while it is being measured
DID_PROBE_MAX_TOTAL = 0.15
DID_PROBE_MIN_DIALS = 250    # dials before a probed number is judged
DID_BAD_RATIO = 0.80         # pickup relative to the other numbers below which a number is pulled ...
DID_BAD_Z = -3.0             # ... if the difference is also this significant
DID_HEALTHY_RATIO_LB = 0.85  # lower 95% bound of the ratio a probed number must clear to be promoted
DID_WINDOWS_H = (3, 6, 24)   # rolling windows checked (hours)
DID_MIN_WINDOW_DIALS = 150
DID_REPROBE_SHARE = 0.03     # smaller share when re-testing a number that failed before
DID_REST_HOURS = 48         # a pulled number is re-probed after resting this long (load-driven
                             # degradation recovers; a genuine spam flag fails the probe again, cheaply)

# ---- hallucination incidents -----------------------------------------------------------------------------
HAL_WINDOW_MIN = 240         # rolling window of connected calls used for detection
HAL_MIN_CONNECTED = 200
HAL_RATE_MULT = 2.0          # flag rate must exceed max(MULT x baseline, baseline + ABS)
HAL_RATE_ABS = 0.012
HAL_P = 1e-4                 # one-sided binomial p-value vs baseline
HAL_RESOLVED_MULT = 1.5      # after a fix: flag rate under this multiple of baseline ...
HAL_VERIFY_MIN_CONNECTED = 300  # ... over at least this many connected calls
HAL_KNOWN_GOOD_MIN_CONNECTED = 800
VALIDATION_N = 500           # 5 credits; enough for the Wilson lower bound to clear 0.97 at a ~1% fail rate
VALIDATION_MARGIN = 0.005    # we require pass_rate >= policy minimum + this, stricter than the approver
CREDIT_RESERVE = 20          # routine work never spends below this; incidents may

# ---- governance ------------------------------------------------------------------------------------------
INCIDENT_SLOTS_RESERVED = 1  # approval requests per 24h kept free for incidents
SUBMIT_END_MARGIN_MIN = 60   # don't send routine requests in the last hour of approver time
REPROPOSE_AFTER_REJECT_MIN = 120
SUPERVISOR_FREEZE_MIN = 24 * 60   # dims a supervisor edited are left alone this long
IMPACT_FULL_SCALE = 0.10     # a 10% projected primary-KPI lift workflow-wide scores impact 1.0

# Per-tenant preferences that are stricter than the signed policy. Stated by the client in a memo; we honour them
# because they cost little. They never loosen the policy the simulator enforces.
TENANT_PREFS = {
    "kestrel_finance": {"earliest_submit_hour": 11, "max_routine_requests_per_day": 2},
}

ALERT_CREDIT_FRACTION = 0.15
