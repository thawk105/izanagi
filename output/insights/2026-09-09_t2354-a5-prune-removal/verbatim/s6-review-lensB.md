## 総括

変異 M1 / M1b / M2 / M3 / M4 の old 逐語はいずれも変更後 bytes にちょうど 1 回あり、DW-M04 停止条件には該当しない。期待 KILL node も静的に追えた。  
M1b は正規化後も regex を通過し、Bash 上では実際に `prune` という 1 引数へ連結される。  
real 所見は、追加 2 node の台帳未登録と、job body digest 変更による T-1998 事前登録の更新要求。直接参照 test の焦点走漏れ、docs 不整合、self-run 収集漏れはない。  
pytest・変異実走はしていない。以下の赤化判定は変更後 bytes に対する静的追跡である。

## 変異事前登録の再検証

| ID | old 逐語の一意性 | 通過性・期待 KILL node | mask / 単一理由性 |
|---|---|---|---|
| M1 | `return "$cleanup_rc"` は 1 回だけ（[job:160](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2354-a5-prune-removal/tools/pegasus/a5_second_boot_backoff_sweep.sh:160)）。 | literal `worktree prune` が [静的 regex](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2354-a5-prune-removal/orchestrator/tests/test_a5_second_boot_job_contract.py:387) に掛かり、`test_current_scripts_are_a_positive_example_of_the_complete_contract` が赤。さらに欠落 sibling 登録が prune され、[保存 assert](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2354-a5-prune-removal/orchestrator/tests/test_a5_second_boot_job_contract.py:521) も赤。 | 裁定どおり静的・runtime の二重 KILL。単独 gate の証拠ではないが、別原因による mask はない。 |
| M1b | M1 と同じ old が 1 回。 | 指定の二段正規化（[364–366](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2354-a5-prune-removal/orchestrator/tests/test_a5_second_boot_job_contract.py:364)）を変更後 file 全体へ適用した結果、行は `worktree "pr""une"` のまま、regex match は `None`。したがって静的 node は通過し、runtime sibling 保存 node だけが [521](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2354-a5-prune-removal/orchestrator/tests/test_a5_second_boot_job_contract.py:521) で赤。 | Bash 字句 probe は `arg1=<worktree> arg2=<prune>`。隣接する quoted fragment は同一 word に連結されるため、実コマンド argv は `git … worktree prune --expire now` になる。代案は不要。 |
| M2 | 同じ `return "$cleanup_rc"` が 1 回。 | `return 0` にすると locked remove 後も cleanup 失敗が呼出側へ返らず、job rc 0 ケースの [completed rc 比較](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2354-a5-prune-removal/orchestrator/tests/test_a5_second_boot_job_contract.py:584) が赤。期待 node は `test_a5_cleanup_failure_records_remaining_paths_and_preserves_exit_precedence` のみ。 | 最初の赤理由は cleanup rc の握り潰し。他の静的層はこの逐語を固定しておらず、mask なし。 |
| M3 | `[[ "$command_rc" -eq 0 ]] && JOB_CCBENCH=""` は 1 回だけ（[job:137](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2354-a5-prune-removal/tools/pegasus/a5_second_boot_backoff_sweep.sh:137)）。 | locked CCBench remove が失敗しても path が空になるため、receipt の期待 2 path [571–574](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2354-a5-prune-removal/orchestrator/tests/test_a5_second_boot_job_contract.py:571) が赤。期待 node は runtime 失敗 node のみ。 | rc 伝播と登録残置自体は変わらず、赤理由は `remaining_ccbench_path` の欠落に限定される。 |
| M4 | original/cleanup rc 条件は 1 回だけ（[job:171](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2354-a5-prune-removal/tools/pegasus/a5_second_boot_backoff_sweep.sh:171)）。 | job rc 23 側で cleanup rc に上書きされ、[終了 rc / failure receipt 不在 assert](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2354-a5-prune-removal/orchestrator/tests/test_a5_second_boot_job_contract.py:589) が赤。期待 node は runtime 失敗 node のみ。 | 2 assert が観測するが、原因は「元の非 0 rc の優先順位を失う」一つ。cleanup rc が偶然 23 でも余分な failure receipt により KILL される。 |

M1 と M1b は同じ一意 anchor への挿入なので、裁定どおり非累積の別走行にすれば競合しない。

## real 所見

1. **追加 2 node が段 4 で要求された acceptance duration ledger に未登録。**

   新規 node は [test:463](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2354-a5-prune-removal/orchestrator/tests/test_a5_second_boot_job_contract.py:463) と [test:526](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2354-a5-prune-removal/orchestrator/tests/test_a5_second_boot_job_contract.py:526)。台帳の既存 A-5 7 node は [ledger:35–41](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2354-a5-prune-removal/orchestrator/tests/acceptance_duration_ledger.json:35) にあるが、この 2 名は存在しない。台帳は合計 22,155 node を宣言する（[ledger:22159](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2354-a5-prune-removal/orchestrator/tests/acceptance_duration_ledger.json:22159)）。

   `nodeid_count` は ledger map の件数との整合性検査にだけ使われる（[conftest:1427–1435](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2354-a5-prune-removal/orchestrator/tests/conftest.py:1427)）。90% gate の分母は別 subprocess が収集した実 collection の `len(rows)`、分子は ledger key との積集合である（[gate:673–707](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2354-a5-prune-removal/orchestrator/tests/test_acceptance_schedule_order.py:673)）。したがって `22155 + 2 = 22157` を機械的に live 分母と断定してはならない。

   一方、現在 HEAD の最新記録は、旧 `19935/22155` の限界状態の後に main 台帳が 22,123 node へ更新され、被覆が約 99.9% に回復したとしている（[failures:23466–23477](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2354-a5-prune-removal/docs/failures.md:23466)）。同じ collection に今回の 2 nodeだけを加える保守計算でも `22123/22157 = 99.8465%` であり、段 4 の「今も余裕 1 node 未満」は古い状態を参照している。

   未登録 node を含む unit は unknown cost となり、既知 cost から作る既定値で整列される（[conftest:1631–1659](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2354-a5-prune-removal/orchestrator/tests/conftest.py:1631)）。

   **成果物影響:** 現在記録された余裕なら 90% gate の即時赤化は見込まれないが、新規 2 node の shard 所要見積りが実測値ではなくなるうえ、段 4 の三ファイル実装指示を満たしていない。

   **修正案:** 実走 JUnit を得た段で `tools/update_acceptance_duration_ledger.py --add-only` により登録する。省略するなら、[F902 の余裕がある場合だけの延期規則](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2354-a5-prune-removal/docs/failures.md:23474)を、live gate の実分数とともに明示して裁定を更新する。

2. **job body digest の変更は T-1998 事前登録へ実在する波及を持つ。**

   HEAD bytes の SHA-256 は `0ef4d41e…281d84`、working tree は `dff913cb…7aecd8`。T-1998 submitter は実際の job file を hash する（[submitter:91–92](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2354-a5-prune-removal/tools/pegasus/submit_t1998_balanced_stock_inline.sh:91)）一方、consumer は reservation の digest と事前登録値を exact 比較する（[consumer:915–919](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2354-a5-prune-removal/orchestrator/campaign/t1998_stock_inline_pair.py:915)）。

   repo 内の旧 digest hit は過去の A-5 reservation / manifest と insight の記録であり、live な新 T-1998 事前登録ではない。既存 unit test も実 digest を pin せず、synthetic `_SCRIPT_SHA` を使う（[test:53](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2354-a5-prune-removal/orchestrator/tests/test_t1998_stock_inline_pair.py:53)）。

   **成果物影響:** 旧 digest で新しい T-1998 走行を事前登録すると `launcher-script-identity-mismatch` で拒否される。過去成果物の歴史的 digest は書き換えてはならない。

   **修正案:** 着地後の確定 bytes から新しい事前登録を作る。裁定どおり本 wave のコード変更には含めない。

docs は不整合なし。正本 D1700 は「自 path の `worktree remove --force` のみ、共有 prune なし、失敗時は残置明示」と規定しており（[decisions:51786–51792](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2354-a5-prune-removal/docs/decisions.md:51786)）、実装の 2 remove と receipt（[job:128–160](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2354-a5-prune-removal/tools/pegasus/a5_second_boot_backoff_sweep.sh:128)）に一致する。runbook の該当箇所は `dispatch-required` 分類だけで cleanup semantics は記述していない（[runbook:484–493](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2354-a5-prune-removal/docs/pegasus-runbook.md:484)。`docs/failures.md` の prune 記述は旧事故の履歴で、現行仕様の主張ではない。

self-run harness も取り残しなし。2 関数は引数なしの `test_` prefix で、`sorted(globals().items())` の callable filter と呼出し loop（[test:593–602](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2354-a5-prune-removal/orchestrator/tests/test_a5_second_boot_job_contract.py:593)）に確実に入る。

## 焦点走に足すべき file

**追加なし。**

production file 名の exact 参照を `orchestrator/tests/` 全体から列挙すると次の 4 file だけで、すべて親の集合に含まれている。

- [test_a5_second_boot_job_contract.py:13](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2354-a5-prune-removal/orchestrator/tests/test_a5_second_boot_job_contract.py:13)
- [test_t1998_launcher_contract.py:12](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2354-a5-prune-removal/orchestrator/tests/test_t1998_launcher_contract.py:12)
- [test_hooks.py:3034](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2354-a5-prune-removal/orchestrator/tests/test_hooks.py:3034)
- [test_official_perf_closure.py:83](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2354-a5-prune-removal/orchestrator/tests/test_official_perf_closure.py:83)

残る 3 file は直接参照ではないが、`test_acceptance_schedule_order.py` は新 node の ledger meta-gate、`test_t1998_stock_inline_pair.py` は digest consumer、`test_backoff_extended_sweep.py` は比較対象 cleanup 契約として妥当な波及集合である。

## 推測

- live collection は実走していないため、現在の正確な `covered / len(rows)` は未確定。上記 `99.8465%` は、HEAD に記録された直近実測へ今回の 2 node だけを足した反実仮想である。
- repo 外に旧 digest を使う未実施 T-1998 事前登録が存在する可能性は否定できない。repo 内検索では歴史成果物以外の該当物は見つからなかった。
- 実 Git を使った mutation run は未実施。KILL 判定は関数抽出・assert 順序・Bash の引数形成に基づく静的追跡である。

## nit

- fixture helper は各 repository に `expected` と未使用の `other` の 2 commit を作り、呼出側も `_repo_other` / `_ccbench_other` として捨てている（[test:30–52](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2354-a5-prune-removal/orchestrator/tests/test_a5_second_boot_job_contract.py:30)）。契約上の害はないが、このテストだけを見る限り second commit は不要で、実走コストと fixture 面積を少し増やしている。
- production diff は裁定対象の cleanup 部分だけ、test diff は指定 helper と 2 node だけで、これ以外の scope 膨張はない。逆方向の不足は台帳登録だけである。