# verbatim の可逆最小正規化 (末尾空白の除去のみ、可視文字不変、DW-S07)

`git diff --check` の末尾空白抵触を避けるため、次の file の行末の空白 (半角空白 / tab) だけを除去した。原文は job dir `/work/1/SFC/tanab/dev-wave-jobs/dev-wave-focus-run-count-diagnosis/` (codex/*.md、verbatim/*、s4-ruling.md、brief.md) にそのまま残る。復元は各行末へ記載の bytes を戻す。

| file | 原文 sha256 | 原文 bytes | 正規化後 sha256 | 正規化後 bytes | 除去 (行: 除去 bytes) |
|---|---|---|---|---|---|
| aggregate.txt | 6756f109a0c1884a431cfbff2f82e9ace22562ea8deef77c82b26d248afb7221 | 2269 | 6756f109a0c1884a431cfbff2f82e9ace22562ea8deef77c82b26d248afb7221 | 2269 |  |
| brief.md | 3296ecdbb0b1620ea3231dfe61021d5431ead3c6cd194435ebac8b9e622a90ae | 6158 | 3296ecdbb0b1620ea3231dfe61021d5431ead3c6cd194435ebac8b9e622a90ae | 6158 |  |
| changed_files.txt | 5fabd8050989387cf9c8f6964f2f057b48ea434970c4a653eba9ea55dc4505e5 | 1600 | 5fabd8050989387cf9c8f6964f2f057b48ea434970c4a653eba9ea55dc4505e5 | 1600 |  |
| classification-v1-attacked.md | 6ff304effe7a11b73adc30b691eb320a80b522cbe3c89afb665be3fa562668fc | 5687 | 6ff304effe7a11b73adc30b691eb320a80b522cbe3c89afb665be3fa562668fc | 5687 |  |
| focus_runs.jsonl | 6b5d3250b8b687361f2b1ee403bbe7cf73099f9b159fb3ff343ddc2d1d0ee122 | 14301 | 6b5d3250b8b687361f2b1ee403bbe7cf73099f9b159fb3ff343ddc2d1d0ee122 | 14301 |  |
| focus_runs_table.md | e37a77510b88ca2a1a5683bb2144529fcf195ad73f69f0c409aa472c177750ef | 4645 | e37a77510b88ca2a1a5683bb2144529fcf195ad73f69f0c409aa472c177750ef | 4645 |  |
| group_sums.txt | 12df22a87d3f9b3406dea173927fb34cd1b412be6ebc43e13cc2fb2ecc4172b4 | 838 | 12df22a87d3f9b3406dea173927fb34cd1b412be6ebc43e13cc2fb2ecc4172b4 | 838 |  |
| origin.md | 91bdf507ee4125036c5da463075a9f9d32cec41c1c09c34d30ce4b5807077fcc | 1008 | 91bdf507ee4125036c5da463075a9f9d32cec41c1c09c34d30ce4b5807077fcc | 1008 |  |
| s3-consult-A.md | e515532bbf106ad5879a0b41c39a9b9c49538395491b903ce8017215cd6e9410 | 20045 | b3c77c77324c707863d66245835096d73ef0369e049438d3229922f0009c3d04 | 19947 | 49 行、各行末の b'  ' |
| s4-ruling.md | c3c3f81143d6f1c59506a6918091dc14d6db73f88ccb3f14988898c14d7ba49f | 7168 | c3c3f81143d6f1c59506a6918091dc14d6db73f88ccb3f14988898c14d7ba49f | 7168 |  |
| s6-focus-A.md | 609a8c00aa56d253308bcf0a61989de451156a1788fad33229f032ab609becf5 | 7769 | 609a8c00aa56d253308bcf0a61989de451156a1788fad33229f032ab609becf5 | 7769 |  |
| s6-review-A.md | d4e3968ffeeecfe3a9efca5e84d7388655190f1675703d965869dbb2496877f0 | 13463 | 86e15e90eecaba1bc0ffe60b9b6aa31fca9ada45e231dcd33b94d980d158ba41 | 13433 | 15 行、各行末の b'  ' |
| scripts.sha256 | 52fba2ca740a439d1c02b0ab867600052781fce7807745b4e5a58201cbba04bd | 839 | 52fba2ca740a439d1c02b0ab867600052781fce7807745b4e5a58201cbba04bd | 839 |  |
| timeline.txt | d2ac862b85a6c920e4e3b6b18e9bb27bc300a1f063992645c33a74857f44c346 | 7652 | d2ac862b85a6c920e4e3b6b18e9bb27bc300a1f063992645c33a74857f44c346 | 7652 |  |
