# MOCC validation fix probe summary

| arm | runs | commits mean | range | validated | A | B | recheck abort | pending overflow | committed overflow | R0 indeterminate |
|---|---:|---:|---|---:|---:|---:|---:|---:|---:|---:|
| T_F | 2 | 5635474.0 | [5633367, 5637581] | 107605099 | 13 | 22 | 0 | 0 | 0 | 0 |
| T_X | 4 | 5664686.5 | [5586440, 5722080] | 216374067 | 0 | 0 | 66 | 0 | 0 | 0 |
| N_F | 1 | 7326357.0 | [7326357, 7326357] | 69916749 | 40 | 126 | 0 | 0 | 0 | 0 |
| N_X | 1 | 7095540.0 | [7095540, 7095540] | 67725096 | 0 | 0 | 146 | 0 | 0 | 0 |
| P_F | 1 | 7145564.0 | [7145564, 7145564] | 0 | 0 | 0 | 0 | 0 | 0 | 0 |
| P_X | 1 | 7338329.0 | [7338329, 7338329] | 0 | 0 | 0 | 0 | 0 | 0 | 0 |

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
  "R0_X_indeterminate_runs": 0,
  "T_X_G2_runs": 0,
  "T_X_runs": 4,
  "T_X_N_X_commit_class_a": 0,
  "success": false,
  "T_F_G2_runs": 1,
  "T_F_G2_control_established": true,
  "T_F_N_F_commit_class_a": 53,
  "F_class_a_control_established": true,
  "F_invalid_runs": {
    "T_F": 0,
    "N_F": 0
  },
  "X_recheck_abort": 212,
  "witness_statuses": {
    "both_A": 0,
    "one_A": 0,
    "B_only": 1,
    "none": 0,
    "indeterminate": 0
  }
}
```

## T G2 witnesses

- 0006-T_F witness 1: B_only [{'reader_txid': 5249179, 'writer_txid': 5249187, 'key': '0000000000000000', 'read_version': [70, 1390], 'overwritten_version': [70, 1396], 'match': 'none'}, {'reader_txid': 5249187, 'writer_txid': 5249179, 'key': '0000000000000004', 'read_version': [70, 1389], 'overwritten_version': [70, 1395], 'match': 'B'}]
