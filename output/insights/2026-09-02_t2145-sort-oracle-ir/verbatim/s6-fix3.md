## 実装

- G1: tokenizerをASCII C++字句分割へ変更し、語彙外tokenを後段判定へ渡しました。[sort_swo_oracle.py](/work/1/SFC/tanab/izanagi/.codex/worktrees/t2145-fix2/orchestrator/campaign/sort_swo_oracle.py:660)
- 既存non-IR 6件は全件拒否され、79正準値は79件すべて受理されることを直接検算しました。
- G2: sort admission後は追加indentなしで正準bytesを再挿入します。[p3_s4_loop.py](/work/1/SFC/tanab/izanagi/.codex/worktrees/t2145-fix2/orchestrator/campaign/p3_s4_loop.py:399)
- G3: role source 2件、coder description、originless baselineの実在driftを追随しました。[review_ledger.py](/work/1/SFC/tanab/izanagi/.codex/worktrees/t2145-fix2/orchestrator/codex_roles/review_ledger.py:18)
- G4: 2 fixtureを正準comparatorへ変更し、最終計算値 `6f6a8cf1` へcampaign goldenを更新しました。[test_p3_s4_loop_sort.py](/work/1/SFC/tanab/izanagi/.codex/worktrees/t2145-fix2/orchestrator/tests/test_p3_s4_loop_sort.py:960)
- 最終oracle contract golden 2件も、実装計算値 `xcc26c432...-a091abb17ccad` へ更新しました。

## 検査

指定された2コマンドを各3回実行しましたが、全6走がtest開始前の `qstat -Q preflight rc=1` による `rc=16` でした。

- `test_sort_swo_oracle.py`: 実行不能。104件の維持は未確認。
- 指定6 file: 実行不能。passed/failed/skipped件数は取得不能。
- `git diff --check`: 問題なし。
- 直接検算: G2の物理holeは `comparator + "\n"` とbyte exactでした。
- `tools/check_codex_agents.py`: adapter byte parity driftで失敗しました。

## 未完・残赤

`.codex/role-adapters` が本sandboxでは読取専用のため、期待diffを確認した次の2ファイルを更新できませんでした。

- `.codex/role-adapters/auditor.json`
- `.codex/role-adapters/coder-v4-autonomous-sort.json`

また、G2と既存G4 assertionには不整合が残ります。pytest未実走ですが、同じproduction経路の直接検算で次が偽になることを確認しました。

- nodeid: `orchestrator/tests/test_p3_s4_loop.py::test_effect_scanner_runs_only_after_structure_and_sees_exact_written_hole_bytes`
- assertion: `assert line.startswith(harness_indent)`
- 実値: `harness_indent == '    '`、正準hole先頭は `'  sort(write_set_.begin(), write_set_.end(),'`
- assertion変更は禁止されているため触れていません。[test_p3_s4_loop.py](/work/1/SFC/tanab/izanagi/.codex/worktrees/t2145-fix2/orchestrator/tests/test_p3_s4_loop.py:376)

## 波及可能性

- 所有外caller: `p3_s4_loop_sort`、`s1_direct_comparison`、`s6_sort_sweep`。
- 共有fixture: `test_p3_s4_loop.py` のsort template、oracle environment registry。
- consumer: critic digest、S8b receipt、dependency material、real-repository serialization。
- role側: dormant adapter parity、originless provenance baseline、role collection。
- contract ID回転はcampaign identity、receipt、critic current-generation読取へ波及します。

## 禁止対象

`docs/`、authority、freeze、effect gate、`CANDIDATES`は変更していません。歴史記録の `081dd46f` も未変更です。commit、skip、xfail、assertion削除・緩和、`PASS`への倒し込みは行っていません。

## 総括

1. G1 tokenizer、G2正準bytes、G3 writable pin、G4 comparator fixtureと許可済みgoldenを修正しました。  
2. 指定2suiteは各3回ともtest開始前 `rc=16` で、104件および指定6 fileの件数は実走不能です。  
3. 未完は読取専用adapter 2件と、G2 byte exactに矛盾するG4 assertion 1件です。  
4. 波及先はsort caller群、critic/receipt、共有fixture、role adapter・serialization・originlessです。