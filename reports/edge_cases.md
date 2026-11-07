# Edge-case end-to-end tests

`python scripts/edge_cases.py` — every case starts from a fresh simulator run dir and a fresh controller DB, against the real simulator over HTTP.

| case | result | detail |
|---|---|---|
| 1 controller starts before simulator | PASS | exit 0, sim finished=True |
| 2 simulator unreachable | PASS | exit 1 after 5s: simulator at http://127.0.0.1:8812 not reachable |
| 3 start mid-scenario (sim already at D1 12:00) | PASS | exit 0, events ours 64119 = sim 64119 |
| 4 start after scenario finished | PASS | exit 0, proposals sent 0 |
| 5 restart on finished DB | PASS | exit 0, proposals 0->0, events 64111 |
| 6 DB from a different simulator run | PASS | exit 1: refused |
| 7 second controller on the same DB | PASS | second exit 1; first exit 0 |
| 8 hallucination incident with 2 credits | PASS | exit 0, credits left 2.0, incident [('open', 'no_fix')], pages ['ks_cancel: hallucination spike on prompt P2', 'ks_cancel: out of credits during hallucination incident', 'ks_cancel: no validated fix for hallucination spike'] |
| 9 simulator restarted under the controller | PASS | exit 1: refused to mix the old DB with the new world |

**9/9 passed.**
