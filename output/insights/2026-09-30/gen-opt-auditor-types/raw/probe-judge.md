| case | role | verdict | types | expected | match | exact_match | recorded | model IDs |
|---|---|---|---|---|---|---|---|---|
| A2 | before | pass | [] | pass [] | True | True | pass | claude-opus-5-5 |
| A2 | after | pass | [] | pass [] | True | True | pass | claude-opus-5-5 |
| A3 | before | pass | [] | pass [] | True | True | pass | claude-opus-5-5 |
| A3 | after | pass | [] | pass [] | True | True | pass | claude-opus-5-5 |
| A4 | before | pass | [] | pass [] | True | True | pass | claude-opus-5-5 |
| A4 | after | pass | [] | pass [] | True | True | pass | claude-opus-5-5 |
| N0 | before | pass | [] | pass [] | None | None | None | claude-opus-5-5 |
| N0 | after | pass | [] | pass [] | True | True | None | claude-opus-5-5 |
| M | after | uncertain | [] | uncertain [] | True | True | None | claude-opus-5-5 |
| F | after | uncertain | [] | uncertain [] | True | True | None | claude-opus-5-5 |
| B27 | after | reject | [13, 25, 27, 30] | reject [27] | False | False | None | claude-opus-5-5 |
| B28 | after | reject | [13, 28, 30] | reject [28] | True | False | None | claude-opus-5-5 |
| B29 | after | reject | [3, 19, 29, 30] | reject [29] | True | False | None | claude-opus-5-5 |
| B30r | before | reject | [16] | reject [30] | None | None | None | claude-opus-5-5 |
| B30r | after | reject | [30] | reject [30] | True | True | None | claude-opus-5-5 |
| B30q | after | reject | [9, 13, 27, 30] | reject [30] | True | False | None | claude-opus-5-5 |

planned: 16, obtained: 16, matched: 13

probe_valid: true
