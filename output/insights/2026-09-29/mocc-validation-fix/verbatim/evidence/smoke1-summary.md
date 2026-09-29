# MOCC validation fix probe summary

| arm | runs | commits mean | range | validated | A | B | recheck abort | pending overflow | committed overflow | R0 indeterminate |
|---|---:|---:|---|---:|---:|---:|---:|---:|---:|---:|
| T_F | 2 | 7214919.0 | [7110864, 7318974] | 137715830 | 62 | 296 | 0 | 0 | 0 | 2 |
| T_X | 4 | 7081315.0 | [7019546, 7181022] | 270332683 | 0 | 0 | 605 | 0 | 0 | 4 |
| N_F | 1 | 7187388.0 | [7187388, 7187388] | 68602693 | 39 | 118 | 0 | 0 | 0 | 0 |
| N_X | 1 | 7252028.0 | [7252028, 7252028] | 69239043 | 0 | 0 | 170 | 0 | 0 | 0 |
| P_F | 1 | 7126430.0 | [7126430, 7126430] | 0 | 0 | 0 | 0 | 0 | 0 | 0 |
| P_X | 1 | 7291035.0 | [7291035, 7291035] | 0 | 0 | 0 | 0 | 0 | 0 | 0 |

## R6 verdict and controls

```json
{
  "expected_runs": {
    "T_F": 56,
    "T_X": 112,
    "N_F": 28,
    "N_X": 28,
    "P_F": 28,
    "P_X": 28
  },
  "all_expected_runs_present": false,
  "two_job_batch_schedule_complete": false,
  "R0_X_indeterminate_runs": 4,
  "T_X_G2_runs": 0,
  "T_X_runs": 4,
  "T_X_N_X_commit_class_a": 0,
  "success": false,
  "T_F_G2_runs": 0,
  "T_F_G2_control_established": false,
  "T_F_N_F_commit_class_a": 101,
  "F_class_a_control_established": true,
  "X_recheck_abort": 775,
  "witness_statuses": {
    "both_A": 0,
    "one_A": 0,
    "B_only": 0,
    "none": 0,
    "indeterminate": 0
  }
}
```

## T G2 witnesses
