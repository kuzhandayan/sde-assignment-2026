"""All tunable thresholds in one place. The reasoning behind each value is in SUBMISSION.md §5–§7."""

# loop
STEP_MINUTES = 30            # sim minutes per /sim/advance
DID_REVIEW_EVERY_MIN = 60    # caller-ID health check cadence

# experiments (welcome_message x voice)
EXP_HALF_LIFE_DAYS = 1.5     # discount old evidence
EXP_MIN_ARM_N = 300          # connected calls before an arm can win
EXP_PROMOTE_PBEST = 0.95     # P(best) needed to promote
EXP_ALPHA = 0.05             # Holm family-wise alpha for promotion
EXP_DROP_ALPHA = 0.01        # harm stop: suspend an arm worse than the best at this level
EXP_DROP_MIN_N = 150
EXP_START_CONTROL_SHARE = 0.5            # first exploration keeps this on the default ...
EXP_START_CONTROL_SHARE_GUARDRAIL = 0.7  # ... and this on pickup-primary workflows
EXP_FLOOR = 0.05             # share kept on each other arm after promotion (decay reference)
EXP_MIN_CHANGE_TV = 0.15     # smallest allocation move worth a config change
EXP_DECAY_ALPHA = 0.01
EXP_DECAY_MIN_REL_DROP = 0.06
EXP_DECAY_WINDOW_DAYS = 1

# variant segments
SEG_MIN_CONNECTED = 400
SEG_MIN_SHARE = 0.04
SEG_ALPHA = 0.05             # Bonferroni across all (segment, dim) tests
SEG_MAX = 6
SEG_START_DAY = 1

# call-time schedule
SCHED_MAX_CELLS = 12
SCHED_MIN_CELL_DIALS = 1200
SCHED_SHRINK_K = 60          # pseudo-dials toward the population hour profile
SCHED_GAMMA = 3.0            # sharpness of hour weights
SCHED_W_MIN, SCHED_W_MAX = 0.25, 4.0   # never 0, so capacity is never left unused
SCHED_MIN_CHANGE_L1 = 0.20
SCHED_HALF_LIFE_DAYS = 7.0
GUARDRAIL_CHECK_MIN_DIALS = 1500

# caller ID
DID_PROBE_SHARE = 0.05       # share per unknown number while measuring it
DID_PROBE_MAX_TOTAL = 0.15
DID_PROBE_MIN_DIALS = 250
DID_BAD_RATIO = 0.80         # pickup vs other numbers below this ...
DID_BAD_Z = -3.0             # ... and this significant -> pull or halve
DID_SEVERE_RATIO = 0.65      # below this always pull
DID_HEALTHY_RATIO_LB = 0.85  # probe passes if the ratio's lower 95% bound clears this
DID_WINDOWS_H = (3, 6, 24)
DID_MIN_WINDOW_DIALS = 150
DID_REPROBE_SHARE = 0.03
DID_REST_HOURS = 48          # rest before re-probing; doubles after each failure

# hallucination incidents
HAL_WINDOW_MIN = 240
HAL_MIN_CONNECTED = 200
HAL_RATE_MULT = 2.0          # flag rate > max(MULT x baseline, baseline + ABS) ...
HAL_RATE_ABS = 0.012
HAL_P = 1e-4                 # ... and binomial p below this
HAL_RESOLVED_MULT = 1.5
HAL_VERIFY_MIN_CONNECTED = 300
HAL_KNOWN_GOOD_MIN_CONNECTED = 800
VALIDATION_N = 500           # 5 credits
VALIDATION_MARGIN = 0.005    # stricter than the policy minimum
CREDIT_RESERVE = 20

# governance
INCIDENT_SLOTS_RESERVED = 1  # requests per 24h kept free for incidents
SUBMIT_END_MARGIN_MIN = 60
REPROPOSE_AFTER_REJECT_MIN = 120
SUPERVISOR_FREEZE_MIN = 24 * 60
IMPACT_FULL_SCALE = 0.10     # +10% projected primary KPI = impact 1.0

# client preferences stricter than their signed policy (stakeholders/04)
TENANT_PREFS = {
    "kestrel_finance": {"earliest_submit_hour": 11, "max_routine_requests_per_day": 2},
}

ALERT_CREDIT_FRACTION = 0.15
