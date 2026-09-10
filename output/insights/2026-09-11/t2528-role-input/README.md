# T-2528 — role入力例を実射影の5fieldへ訂正

authority: none
default_effect: no-state-change

D1936項23・25に従う文書訂正。実装anchorは `7f537f45f603d506b4effe49daa0e114366a49d7`。

## 訂正と境界

coder-v4-autonomous・sort・trigger-gatingとplanner-v4のwhiteboard例を
`iteration / direction / magnitude / result / delta_pct`へ揃えた。
plannerの「leading-indicatorsだけ」という説明をcurrent_perf・leading_indicators・whiteboard、
任意policy_hintという実入力へ訂正した。delta_pctはnullを維持する。

親が4role Markdownを編集し、隔離されたCodex authorが既存review_ledgerの4source pinと
originless互換baselineを追随した。親によるstatic adapter同期はD1936項25に従い、
既存 `expected_adapters()` の出力だけを用いた。全14adapterの期待bytesとの一致を独立監査した。
schema・manifest・renderer・productionの受理集合を変更していない。
native 0 / static 14 / runtime blockedを維持する。新しいsemantic pin・gate・検査は追加していない。

起動時の登録worktree・handoff・稼働workerを照合し、対象4roleの所有重複は確認されなかった。
並行T-2551は段4job shell/test、T-2397はA-1、T-2518はinert precheckを所有していた。

## 初回の見落としと修正

親briefは互換baselineのplanner hashだけを数え、trigger-gating hashの7箇所を落とした。
初回単独走job991683の1FAILで検出した。両roleそれぞれjournal 6箇所＋report 1箇所を
固定old/new hashで追随し、既存assertion・比較対象・非揮発leaf/key集合は保持した（F433再発）。
独立focus監査は、T2528 helperと呼出しだけを除いたtest全体のASTがHEADと一致することを確認した。

fix子はコードを変更したが必須見出しを欠き、CLI rc=0でもlauncherはF43としてrc=1で未受理にした。
親は完了扱いせず、別read-only focus子に現物diffと固定hashを監査させて採用した。
author/fix/focusはすべてgpt-6-astra・medium。実装子のpytestはqstat preflight rc=16で未実走。
親が以下を実測した。

## 検査

| 検査 | 実測 |
|---|---|
| 変更test単独走（修正後、job991691） | 2 passed、14.63s、rc=0 |
| 関連8file（job991696） | 939 passed、4 skipped、15.73s、rc=0 |
| 4roleの例を既存validate_whiteboardへ入力 | 4正例受理、3field/非None deltaの8負例拒否 |
| check_codex_agents / check_docs / diff --check | rc=0 |
| anchor全史provenance（job991699） | 9631件、新規違反なし、既知違反は既存台帳で分離 |

関連8fileはtest_codex_agents、test_codex_role_runtime、test_p3_s4_loop、
test_p3_autonomous_workload_trial、test_s8c_generation_projection、test_claude_transport、
test_effort_levels、test_role_session_isolation。
修正後単独走はrunnerのbounded local cap OOM後、既存の自動dispatchで計算ノードへ移った。
OOMをテストの意味的な赤として数えていない。

## 変異

`mutation-spec.json` と `mutation-ledger.json` が事前登録と実測。
既存harnessを専用wave worktreeで実行し、共有mainを変異させていない。
baselineは2 passed。M1はT2528 helper呼出しを1箇所だけ除去し、
`test_originless_default_preserves_every_nonvolatile_leaf_and_closed_key_set`だけが失敗した。
1/1 KILLED、期待node完全一致、MISMATCH/SURVIVED/TIMEOUTは0。終了後のtracked差分は0。

fix後のM1はplannerとtrigger-gating両方の追随を外すので、planner単独の寄与とは解釈しない。
既存の固定baseline比較が追随漏れを検出するという証拠である。
全surface協調改変に対する独立semantic防壁は新設していない（D1936項24）。

## 終端の範囲

最終受入は記録commit後の `dev_wave_wait.py acceptance` がtested main/tipを束縛する。
受入・landの実行receiptはrepo外の専用job directory
`/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2528-role-input/`へ保存する。
改善実装・次wave・pushは行わない。
