## 所見対応表

`closed` は静的レビュー上の判定であり、pytest の独立再実行を意味しない。

| 所見 | 判定 | 根拠 file:line | 影響 1 行 |
|---|---|---|---|
| R1-1 / F1: validator の型破損 | `closed` | container を演算前に検査し、SHA・kind も型確認後に regex／集合照合する。[check_ai_provenance.py:184](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t614-provenance-ledger/tools/check_ai_provenance.py:184) [同:196](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t614-provenance-ledger/tools/check_ai_provenance.py:196) [同:211](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t614-provenance-ledger/tools/check_ai_provenance.py:211) `RuntimeError` は rc=2 に捕捉される。[同:2051](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t614-provenance-ledger/tools/check_ai_provenance.py:2051) 3 型の test も rc=2 を固定する。[test_check_ai_provenance.py:1488](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t614-provenance-ledger/orchestrator/tests/test_check_ai_provenance.py:1488) | 未修正なら台帳破損が rc=2 でなく未捕捉例外の rc=1 となり、receipt が新規違反と区別できない。 |
| R1-2 / F2: off-HEAD 偽 stale | `regressed` | epoch は依然 current `HEAD` から検索する。[check_ai_provenance.py:634](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t614-provenance-ledger/tools/check_ai_provenance.py:634) fix は epoch が `None` なら stale 対象から外す。[同:1019](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t614-provenance-ledger/tools/check_ai_provenance.py:1019) [同:1146](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t614-provenance-ledger/tools/check_ai_provenance.py:1146) 新 test 自身が、対象 commit は policy epoch の子なのに current HEAD では epoch が見えず、known 公開なしの「違反なし」を期待している。[test_check_ai_provenance.py:1720](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t614-provenance-ledger/orchestrator/tests/test_check_ai_provenance.py:1720) [同:1723](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t614-provenance-ledger/orchestrator/tests/test_check_ai_provenance.py:1723) | checker の expected finding 生成が壊れた場合、本来 stale rc=2 の commit が rc=0・known=0 となり受理集合が拡大する。 |
| R1-3 / F6: bounded 子の二重警告 | `partial` | 実 bounded pair では子を抑止する。[run_tests.py:1664](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t614-provenance-ledger/tools/run_tests.py:1664) ただし helper は値や cgroup attestation を見ず、環境変数名 2 個の存在だけを信頼する。[同:1228](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t614-provenance-ledger/tools/run_tests.py:1228) | 偽装・偶発 marker pair により非受入警告が 1 行から 0 行になり、stderr receipt の値が変わる。 |
| R1-4: PR-A02 の rc/stdout 契約 | `partial` | 文書は「rc は新規だけ」「既知は常に stdout」と断言する。[audit.md:23](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t614-provenance-ledger/docs/provenance/audit.md:23) stale は `HistoryAudit` を返す前に例外となり、main は rc=2・stderr のみで終了する。[check_ai_provenance.py:1165](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t614-provenance-ledger/tools/check_ai_provenance.py:1165) [同:2051](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t614-provenance-ledger/tools/check_ai_provenance.py:2051) | selected-stale の文書上の出力値と実際の rc=2／stdout 空が一致しない。 |
| R1-5: default `--ancestry-path` 盲点 | `未対応（親が nit と裁定）` | 文書は全履歴検査に見えるが、既定列挙は `--ancestry-path`。[audit.md:15](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t614-provenance-ledger/docs/provenance/audit.md:15) [check_ai_provenance.py:820](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t614-provenance-ledger/tools/check_ai_provenance.py:820) | policy 前 fork 上の新規違反が後日 merge された場合、期待 rc=1 が rc=0 になり得る。 |
| R1-6: 文字列 kind による過剰吸収説 | `closed` | lookup は full commit key と構造化 kind の連言である。[check_ai_provenance.py:997](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t614-provenance-ledger/tools/check_ai_provenance.py:997) | 現状態では吸収による finding 数・rc の変化なし。所見は refuted/nit。 |
| R1-7: rc=0/1・known=0 時の既存逐語破壊説 | `closed` | message-file は history 台帳を通らず、known は空のまま。[check_ai_provenance.py:2017](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t614-provenance-ledger/tools/check_ai_provenance.py:2017) known がある正常 history だけ qualifier と公開行を足す。[同:2068](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t614-provenance-ledger/tools/check_ai_provenance.py:2068) | stale/F2 を除けば既存 rc・逐語・受理集合は変わらない。所見は refuted/nit。 |
| R1-8: pin 内の恒真 assertion | `未対応（親が nit と裁定）` | `commits` は依然 production ではなくローカル `expected` から導出する。[test_check_ai_provenance.py:1357](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t614-provenance-ledger/orchestrator/tests/test_check_ai_provenance.py:1357) | 直前の production tuple 完全一致が同じ drift を検出するため、現行 gate 値は変わらない。 |
| R2-1 / F3: M1 killer 不在 | `closed` | 2 SHA は先頭 **8 桁**を共有し、subject/path も同一。[test_check_ai_provenance.py:1415](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t614-provenance-ledger/orchestrator/tests/test_check_ai_provenance.py:1415) production の照合 seam を直接通し、同 seam は `_audit_history()` から実際に呼ばれる。[同:1437](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t614-provenance-ledger/orchestrator/tests/test_check_ai_provenance.py:1437) [check_ai_provenance.py:1159](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t614-provenance-ledger/tools/check_ai_provenance.py:1159) | M1を「先頭8桁照合」と具体化すれば、別 SHA の finding が消えて exact result が破れる。 |
| R2-2 / F4: M4 control が恒真 | `closed` | 同一 node がまず production の新規0・既知6を確認し、その後に空台帳で新規6を確認する。[test_check_ai_provenance.py:1785](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t614-provenance-ledger/orchestrator/tests/test_check_ai_provenance.py:1785) | production tuple を空にする M4 は最初の `production.findings == []` で確実に赤になる。 |
| R2-3 / F6: marker 経路・早期位置の未固定 | `partial` | bounded 経路は追加されたが、assert は stderr 全体の完全一致でなく対象行の `count == 1` に留まる。[test_run_tests_preflight.py:329](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t614-provenance-ledger/orchestrator/tests/test_run_tests_preflight.py:329) [同:361](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t614-provenance-ledger/orchestrator/tests/test_run_tests_preflight.py:361) preflight 前の位置と rc は別 test が固定する。[同:374](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t614-provenance-ledger/orchestrator/tests/test_run_tests_preflight.py:374) | 余分な stderr 行や偽 marker による警告欠落があっても bounded test が通り、receipt 値の退行を見逃す。 |
| R2-4 / F5: correction/waiver composition 不在 | `closed` | correction は相殺後の target を stale、他 finding を維持する exact seam result を固定する。[test_check_ai_provenance.py:2154](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t614-provenance-ledger/orchestrator/tests/test_check_ai_provenance.py:2154) waiver も同じ三分離を固定する。[同:2827](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t614-provenance-ledger/orchestrator/tests/test_check_ai_provenance.py:2827) | 相殺順が変わると stale／known／残存 finding のいずれかが変わり、両 exact assert が破れる。 |
| R2-5: test 名一意性 meta-test 不在 | `未対応（親が nit と裁定）` | collection config test は ini 範囲だけを検査し、AST 重名検査はない。[test_pytest_collection_config.py:94](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t614-provenance-ledger/orchestrator/tests/test_pytest_collection_config.py:94) | 将来同名定義が入ると先の killer が上書きされ、収集全走が赤にならない可能性がある。 |
| R2-6: negative control 単独では恒真 | `partial` | M4 は同一 node の正負対になったが、outside-range と selected-stale、acceptance と nonacceptance は別 node のまま。[test_check_ai_provenance.py:1605](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t614-provenance-ledger/orchestrator/tests/test_check_ai_provenance.py:1605) [同:1662](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t614-provenance-ledger/orchestrator/tests/test_check_ai_provenance.py:1662) | 現在は正例が別 node で守るが、その node が将来消えると negative 単独では機構削除を検出しない。残余は nit。 |
| R2-7: 揮発値焼き込み | `closed` | production SHA/ruling は固定契約値で、人工履歴は生成 SHA から期待値を組み立てる。[test_check_ai_provenance.py:1323](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t614-provenance-ledger/orchestrator/tests/test_check_ai_provenance.py:1323) [同:1742](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t614-provenance-ledger/orchestrator/tests/test_check_ai_provenance.py:1742) | 通常 commit の追加では期待件数・payload・rc は変わらない。所見は refuted/nit。 |
| R2-8: 既存期待値の緩和 | `closed` | pre-fix patch との差分は新 helper/seam/test の追加で、既存 assert の反転・部分一致化・skip・削除はない。既存等価性には known 比較が追加されている。[test_check_ai_provenance.py:4520](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t614-provenance-ledger/orchestrator/tests/test_check_ai_provenance.py:4520) | 既存拒否条件の緩和による受理集合拡大はない。 |
| R2-9: 正例3件の固定 | `closed` | 既知のみ rc=0、未台帳 `3f2c…` rc=1、台帳外 range rc=0 をそれぞれ固定する。[test_check_ai_provenance.py:1749](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t614-provenance-ledger/orchestrator/tests/test_check_ai_provenance.py:1749) [同:1801](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t614-provenance-ledger/orchestrator/tests/test_check_ai_provenance.py:1801) [同:1679](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t614-provenance-ledger/orchestrator/tests/test_check_ai_provenance.py:1679) | 過剰拒否または未裁定違反の吸収で対応する rc／出力が変わり赤になる。 |

## 退行

1. 最重要の退行は F2 である。新 test の `target` は実装 path を Claude author だけで変更し、実際には implementation policy 違反である。それにもかかわらず unrelated `HEAD` から epoch が見えないことを理由に、known 公開すらない `1 件、違反なし` を固定している。対象 commit の lineage から policy を決めるべきであり、current `HEAD` の欠落を stale 除外理由にしてはならない。

2. F6 は実 bounded 子では二重表示を止めるが、空文字を含む marker pair でも警告を先に抑止する。その後の `_bounded_scope_membership()` は rc=16 で拒否しても、親が存在しない直接走行では非受入警告が失われる。helper は警告条件以外には使われておらず、pytest argv・acceptance 判定・rc の既存処理自体は変えていない。

3. snapshot と現差分の比較では、post-fix に既存 test の反転・部分一致化・skip・削除はない。ただし新設された off-HEAD test が fail-open な期待値を新たに固定している。

4. seam 化そのものは、correction の相殺を ledger より先に処理し、waiver 適用後の finding を照合する順序を保つ。[check_ai_provenance.py:993](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t614-provenance-ledger/tools/check_ai_provenance.py:993) `--message-file` は引き続き seam／validator を通らない。新しい挙動差は `stale_eligible_commits` の絞り込みに集中している。

5. 提示された既定全走の「既知6／新規1」は、通常 HEAD では implementation epoch が見えるため静的経路と整合する。しかし off-HEAD 分岐を通らないので、F2 の退行を否定する証拠にはならない。

## 変異別の検出力

M1 は曖昧さをなくすため、matrix 上で「先頭8桁による照合」と具体化する必要がある。

| 変異 | 赤くなる nodeid | 破れる assert | 再判定 |
|---|---|---|---|
| M1: full SHA exact → 先頭8桁一致 | `orchestrator/tests/test_check_ai_provenance.py::test_known_violation_exact_sha_with_shared_eight_digit_prefix` | exact `KnownViolationAudit`。[test_check_ai_provenance.py:1443](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t614-provenance-ledger/orchestrator/tests/test_check_ai_provenance.py:1443) | KILL。N 未指定のまま、または N>8 の mutant と解釈するとこの pair は衝突しないため、その定義では殺せない。 |
| M2: kind 検査を外す | `…::test_known_violation_expected_kind_coexists_with_other_new_finding` | CAB finding の exact list。[同:1563](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t614-provenance-ledger/orchestrator/tests/test_check_ai_provenance.py:1563) | KILL |
| M3: entry 当たり1件制限を外す | `…::test_known_violation_suppresses_only_one_expected_finding` | 2件目を残す `audit.findings == ["duplicate-kind"]`。[同:1601](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t614-provenance-ledger/orchestrator/tests/test_check_ai_provenance.py:1601) | KILL |
| M4: production 台帳を空 tuple | `…::test_empty_registry_restores_all_six_real_findings` | 空化前の `production.findings == []`。[同:1786](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t614-provenance-ledger/orchestrator/tests/test_check_ai_provenance.py:1786) | KILL |
| M5: rc を既知＋新規で決める | `…::test_known_violation_stdout_is_public_on_rc0_and_rc1` | 既知のみ range の `main(...) == 0`。[同:1749](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t614-provenance-ledger/orchestrator/tests/test_check_ai_provenance.py:1749) | KILL |
| M6: known stdout を削る | `…::test_known_violation_stdout_is_public_on_rc0_and_rc1` | rc=0 と rc=1 の exact stdout。[同:1753](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t614-provenance-ledger/orchestrator/tests/test_check_ai_provenance.py:1753) [同:1765](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t614-provenance-ledger/orchestrator/tests/test_check_ai_provenance.py:1765) | KILL |
| M7: stale 検出を外す | `…::test_known_violation_selected_clean_entry_is_stale_rc2` | `main(...) == 2`。[同:1621](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t614-provenance-ledger/orchestrator/tests/test_check_ai_provenance.py:1621) | KILL。ただしF2が追加した missing-codex の epoch 欠落経路は別途 fail-open。 |
| M8: 非受入警告を削る | `orchestrator/tests/test_run_tests_preflight.py::test_nonacceptance_main_warns_once_on_stderr_and_preserves_rc` | exact stderr。[test_run_tests_preflight.py:283](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t614-provenance-ledger/orchestrator/tests/test_run_tests_preflight.py:283) | KILL |
| M9: 受入形でも警告する | `…::test_acceptance_main_does_not_emit_nonacceptance_warning` | `capsys.readouterr() == ("", "")`。[同:297](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t614-provenance-ledger/orchestrator/tests/test_run_tests_preflight.py:297) | KILL |

M1を N=8 と事前登録すれば M1〜M9 に survivor はない。N を一般量化したままなら、M1 の N>8 版は明示的な survivor である。

## 残る must-fix

1. **F2:** policy epoch／guard を監査対象 commit の lineage から導出する。off-HEAD の実違反は known として公開し、同じ guard 下で expected finding だけを消した場合は stale rc=2 になる正負対が必要。

2. **F6:** marker の存在だけで警告を抑止しない。少なくとも malformed／unattested pair では警告を維持し、bounded test は対象行の count ではなく stderr 全体を exact 1 行で固定する。

3. **R1-4:** PR-A02 を「正常完了した rc=0/1 では新規だけで rc を決定」に限定し、validator/stale の rc=2 と stdout 非公開を明記する。

## 総括

F1・F3・F4・F5 は静的には closed、F6 は partial である。  
F2 は偽 stale 解消と引き換えに正当な stale を見逃す規律2違反の退行で、受理前の must-fix である。  
M1を先頭8桁 mutant と明記すれば M1〜M9 はすべて対応 assert を持つ。  
pytest は実行しておらず、提示された 479 passed や全走結果を独立確認したとはしていない。