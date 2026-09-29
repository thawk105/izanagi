# MOCC validation fix probe summary

| arm | runs | commits mean | range | validated | A | B | recheck abort | pending overflow | committed overflow | R0 indeterminate |
|---|---:|---:|---|---:|---:|---:|---:|---:|---:|---:|
| T_F | 56 | 5657706.321428572 | [5516284, 5774873] | 3025221527 | 366 | 611 | 0 | 0 | 0 | 0 |
| T_X | 112 | 5657779.928571428 | [5520505, 5784318] | 6050250129 | 0 | 2 | 1892 | 0 | 0 | 0 |
| N_F | 28 | 7233720.857142857 | [7065066, 7418983] | 1933205054 | 1049 | 3629 | 0 | 0 | 0 | 0 |
| N_X | 28 | 7169666.428571428 | [6997798, 7428715] | 1916106993 | 0 | 0 | 4476 | 0 | 0 | 0 |
| P_F | 28 | 7200448.642857143 | [6918529, 7357668] | 0 | 0 | 0 | 0 | 0 | 0 | 0 |
| P_X | 28 | 7241786.821428572 | [7051309, 7469027] | 0 | 0 | 0 | 0 | 0 | 0 | 0 |

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
  "all_expected_runs_present": true,
  "two_job_batch_schedule_complete": true,
  "R0_X_indeterminate_runs": 0,
  "T_X_G2_runs": 0,
  "T_X_runs": 112,
  "T_X_N_X_commit_class_a": 0,
  "success": true,
  "T_F_G2_runs": 8,
  "T_F_G2_control_established": true,
  "T_F_N_F_commit_class_a": 1415,
  "F_class_a_control_established": true,
  "F_invalid_runs": {
    "T_F": 0,
    "N_F": 0
  },
  "X_recheck_abort": 6368,
  "witness_statuses": {
    "both_A": 0,
    "one_A": 3,
    "B_only": 6,
    "none": 0,
    "indeterminate": 0
  }
}
```

## T G2 witnesses

- 0011-T_F witness 1: one_A [{'reader_txid': 397536, 'writer_txid': 397547, 'key': '0000000000000000', 'read_version': [6, 2352], 'overwritten_version': [6, 2355], 'match': 'none'}, {'reader_txid': 397547, 'writer_txid': 397536, 'key': '0000000000000001', 'read_version': [6, 2352], 'overwritten_version': [6, 2354], 'match': 'A'}]
- 0026-T_F witness 1: B_only [{'reader_txid': 176755, 'writer_txid': 176766, 'key': '0000000000000000', 'read_version': [3, 2180], 'overwritten_version': [3, 2189], 'match': 'none'}, {'reader_txid': 176766, 'writer_txid': 176755, 'key': '0000000000000002', 'read_version': [3, 2175], 'overwritten_version': [3, 2187], 'match': 'B'}]
- 0111-T_F witness 1: one_A [{'reader_txid': 1236604, 'writer_txid': 1236615, 'key': '0000000000000003', 'read_version': [16, 5704], 'overwritten_version': [16, 5706], 'match': 'none'}, {'reader_txid': 1236615, 'writer_txid': 1236604, 'key': '0000000000000000', 'read_version': [16, 5699], 'overwritten_version': [16, 5705], 'match': 'A'}]
- 0131-T_F witness 1: B_only [{'reader_txid': 4509839, 'writer_txid': 4509844, 'key': '0000000000000002', 'read_version': [60, 1351], 'overwritten_version': [60, 1372], 'match': 'none'}, {'reader_txid': 4509844, 'writer_txid': 4509839, 'key': '0000000000000000', 'read_version': [60, 1367], 'overwritten_version': [60, 1371], 'match': 'B'}]
- 0026-T_F witness 1: B_only [{'reader_txid': 3903362, 'writer_txid': 3903367, 'key': '0000000000000047', 'read_version': [53, 1389], 'overwritten_version': [53, 1460], 'match': 'none'}, {'reader_txid': 3903367, 'writer_txid': 3903362, 'key': '0000000000000000', 'read_version': [53, 1454], 'overwritten_version': [53, 1458], 'match': 'B'}]
- 0026-T_F witness 2: B_only [{'reader_txid': 2363515, 'writer_txid': 2363521, 'key': '0000000000000001', 'read_version': [32, 1825], 'overwritten_version': [32, 1828], 'match': 'none'}, {'reader_txid': 2363521, 'writer_txid': 2363515, 'key': '0000000000000000', 'read_version': [32, 1825], 'overwritten_version': [32, 1827], 'match': 'B'}]
- 0065-T_F witness 1: one_A [{'reader_txid': 343878, 'writer_txid': 343882, 'key': '0000000000000051', 'read_version': [5, 2882], 'overwritten_version': [5, 3859], 'match': 'none'}, {'reader_txid': 343882, 'writer_txid': 343878, 'key': '0000000000000001', 'read_version': [5, 3854], 'overwritten_version': [5, 3858], 'match': 'A'}]
- 0106-T_F witness 1: B_only [{'reader_txid': 2865362, 'writer_txid': 2865368, 'key': '0000000000000002', 'read_version': [38, 2675], 'overwritten_version': [38, 2688], 'match': 'none'}, {'reader_txid': 2865368, 'writer_txid': 2865362, 'key': '000000000000000b', 'read_version': [38, 2632], 'overwritten_version': [38, 2687], 'match': 'B'}]
- 0111-T_F witness 1: B_only [{'reader_txid': 314868, 'writer_txid': 314879, 'key': '0000000000000002', 'read_version': [5, 2626], 'overwritten_version': [5, 2636], 'match': 'none'}, {'reader_txid': 314879, 'writer_txid': 314868, 'key': '0000000000000000', 'read_version': [5, 2633], 'overwritten_version': [5, 2634], 'match': 'B'}]
