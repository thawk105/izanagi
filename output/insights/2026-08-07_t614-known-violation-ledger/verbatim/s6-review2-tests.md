## 変異別の検出力

| 変異 | 赤くなる追加テストの nodeid | 破れる assert の file:line | 判定 |
|---|---|---|---|
| M1: full SHA exact → 前方一致 | なし | 候補テストは無関係な二つの full SHA を生成するだけで、共通 prefix を固定していないため [test_check_ai_provenance.py:1410](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t614-provenance-ledger/orchestrator/tests/test_check_ai_provenance.py:1410) と [同:1411](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t614-provenance-ledger/orchestrator/tests/test_check_ai_provenance.py:1411) は破れない | **穴（real）** |
| M2: kind 検査を外す | `orchestrator/tests/test_check_ai_provenance.py::test_known_violation_expected_kind_coexists_with_other_new_finding`、`…::test_known_violation_other_kind_does_not_hide_selected_stale` | CAB ではなく missing-codex-author が新規側に残り [同:1481](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t614-provenance-ledger/orchestrator/tests/test_check_ai_provenance.py:1481) の exact list が破れる。別種だけの commit は stale にならず rc=0 となり [同:1570](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t614-provenance-ledger/orchestrator/tests/test_check_ai_provenance.py:1570) が破れる | 検出あり |
| M3: entry 当たり 1 件制限を外す | `…::test_known_violation_suppresses_only_one_expected_finding` | 既知が重複するか、残すべき 2 件目が消え、[同:1518](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t614-provenance-ledger/orchestrator/tests/test_check_ai_provenance.py:1518) または [同:1519](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t614-provenance-ledger/orchestrator/tests/test_check_ai_provenance.py:1519) が破れる | 検出あり |
| M4: production 台帳を空 tuple にする | `…::test_known_violation_ledger_is_exactly_six_literal_entries`、`…::test_known_violation_ledger_matches_real_commit_findings` | 件数 pin [同:1356](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t614-provenance-ledger/orchestrator/tests/test_check_ai_provenance.py:1356) と、新規 finding が空という正例 [同:1380](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t614-provenance-ledger/orchestrator/tests/test_check_ai_provenance.py:1380) が破れる | 検出あり。ただし事前登録された「空 registry control」自身は赤にならない |
| M5: rc を既知＋新規で決める | `…::test_known_violation_stdout_is_public_on_rc0_and_rc1` | 既知だけの range が rc=1 となり [同:1623](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t614-provenance-ledger/orchestrator/tests/test_check_ai_provenance.py:1623) が破れる | 検出あり |
| M6: 既知 stdout を削る | `…::test_known_violation_stdout_is_public_on_rc0_and_rc1` | rc=0 側の exact stdout [同:1627](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t614-provenance-ledger/orchestrator/tests/test_check_ai_provenance.py:1627) と rc=1 側 [同:1639](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t614-provenance-ledger/orchestrator/tests/test_check_ai_provenance.py:1639) が破れる | 検出あり |
| M7: stale 検出を外す | `…::test_known_violation_selected_clean_entry_is_stale_rc2`、`…::test_known_violation_other_kind_does_not_hide_selected_stale` | clean entry は rc=0 となり [同:1539](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t614-provenance-ledger/orchestrator/tests/test_check_ai_provenance.py:1539) が破れる。別種ありは rc=1 となり [同:1570](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t614-provenance-ledger/orchestrator/tests/test_check_ai_provenance.py:1570) が破れる | 検出あり |
| M8: 非受入警告を削る | `orchestrator/tests/test_run_tests_preflight.py::test_nonacceptance_main_warns_once_on_stderr_and_preserves_rc`、`…::test_nonacceptance_reexecution_warns_in_parent_and_child_without_marker`、`…::test_nonacceptance_collect_only_main_warns` | exact stderr [test_run_tests_preflight.py:283](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t614-provenance-ledger/orchestrator/tests/test_run_tests_preflight.py:283)、二回表示 [同:326](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t614-provenance-ledger/orchestrator/tests/test_run_tests_preflight.py:326)、collect-only [同:338](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t614-provenance-ledger/orchestrator/tests/test_run_tests_preflight.py:338) が破れる | 検出あり |
| M9: 受入形でも警告する | `…::test_acceptance_main_does_not_emit_nonacceptance_warning` | `("", "")` pin [同:298](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t614-provenance-ledger/orchestrator/tests/test_run_tests_preflight.py:298) が破れる | 検出あり |

## 所見

1. **real / must-fix — M1 を決定的に殺すテストがない。**

   根拠: validator は entry を必ず 40 桁にするため、full SHA 同士の `startswith` は equality と同値である（`tools/check_ai_provenance.py:191-195`）。意味のある短縮-prefix 変異に対しても、テストが生成する `known` と `other` は共通 prefix を保証していない（`orchestrator/tests/test_check_ai_provenance.py:1402-1411`）。subject と path も別物なので、SHA 以外の誤照合も検出しない。

   影響: 先頭 N 桁照合へ退行すると、prefix が衝突した未裁定違反が既知へ吸収され、finding 数が 1 減って rc=1 が rc=0 になり得る。

   推奨対処: M1 の N を具体化し、同じ N 桁 prefix・同じ subject/path を持つ二つの人工 full SHA を audit seam へ注入して、別 SHA が必ず新規に残るテストにする。

2. **real / must-fix — M4 の事前登録 oracle が恒真である。**

   根拠: 裁定は M4 の期待赤を「実 6 件が新規へ戻る control」としている（`s4-adjudication.md:100`）。しかし当該テストは自分で registry を空にしてから（`orchestrator/tests/test_check_ai_provenance.py:1659`）6 finding を期待するため、production tuple を空にする M4 を入れても [同:1661](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t614-provenance-ledger/orchestrator/tests/test_check_ai_provenance.py:1661) は通る。全 suite では別の二テストが M4 を殺すため、全体の穴ではない。

   影響: DW-M01 の expected-node をこの control に結び付けると、M4 の mutation receipt が KILLED ではなく SURVIVED/MISMATCH になり、「単一理由」の証拠値が裁定と食い違う。

   推奨対処: 同じ node 内で「production registry なら既知6・新規0」を先に確認してから空 registry の差分を確認するか、期待赤 node を正例テストへ再裁定する。

3. **real / must-fix — (B) は marker ありの再実行と警告位置を固定していない。**

   根拠: D-5 は marker がある子では再表示しない契約である（`s4-adjudication.md:59-64`）。bounded child には実際に marker が渡る（`tools/run_tests.py:1341-1343`）が、現実装は marker 判定前に無条件で警告する（`tools/run_tests.py:1655-1660`）。追加テストは単一 OTHER 呼出しと、明示的に `without_marker` とした親子二回表示しか検査しない（`orchestrator/tests/test_run_tests_preflight.py:256-326`）。また warning 自体を event 列へ入れていないため、preflight より後へ移しても成功経路の exact 出力は通る。

   影響: bounded 非受入走行では stderr が1行から2行へ変わり、逆に早期 rc=13/15/14 や bounded return の後へ移す退行では警告が消える。task-run／dispatch 診断 payload の値が変わる。

   推奨対処: marker ありの親→bounded child を模したテストで end-to-end exactly 1 行を固定し、非受入 preflight が失敗するケースでも警告がエラーより先に出て rc を保持することを検査する。

4. **real / must-fix — 裁定済みの correction／waiver composition test が追加されていない。**

   根拠: 親裁定は synthetic registry と correction/waiver の composition test を明示要求している（`s4-adjudication.md:29`）。追加された correction assertion は `known_violations == ()` のみ（`orchestrator/tests/test_check_ai_provenance.py:2021`）で、registry と correction target を重ねていない。現実装は correction 抑止を ledger count より先に行うため（`tools/check_ai_provenance.py:1069-1092`）、順序変更で stale/known/rc が変わる面が未固定である。

   影響: 同一 finding を correction と ledger が二重吸収する退行により、rc=2 または rc=1 であるべき selected range が rc=0 へ広がり得る。

   推奨対処: correction target と synthetic registry を意図的に重ね、target missing は correction、ledger は stale、他 finding は新規に残る exact composition testを追加する。waiver overlap も同様に固定する。

5. **real / must-fix — test 名一意性の meta-test がない。**

   根拠: 現在の追加名には静的な重複はない。しかし既存 meta-test は `pytest.ini` の収集範囲だけを固定している（`orchestrator/tests/test_pytest_collection_config.py:94-122`）。collection hook も group marker 付与だけである（`orchestrator/tests/conftest.py:151-160`）。同一モジュール内の重複 `def test_*` を検出する制約や、T-614 の M1〜M9 node 集合 pin は存在しない。

   影響: 後から同名 test を定義すると先の関数が import 時に上書きされ、収集 node 集合から mutation killer が消えても受入全走が緑に見え得る。

   推奨対処: 各 test module の top-level `test_*` 定義名を AST で数え、重複ゼロと T-614 の期待 node 集合を exact pin する meta-test を置く。

6. **real / nit — 単独では機構削除を検出しない negative control がある。**

   根拠: lookup を無効化しても `test_known_violation_outside_range_is_not_stale_end_to_end`（`test_check_ai_provenance.py:1580-1602`）、`test_empty_registry_restores_all_six_real_findings`（同:1648-1664）、`test_unledgered_3f2c43d7580b_remains_new_and_rc1`（同:1667-1678）は通る。警告削除時には acceptance 側 negative test（`test_run_tests_preflight.py:289-298`）も通る。

   影響: 現在はそれぞれ selected-stale、real-six、known stdout、nonacceptance warning の正例と対になっているため、M1以外の受理集合値は守られている。ただし正例が重名で消えると防壁も消える。

   推奨対処: 正負を同一 test または mutation-node registry で不可分に結び付ける。M4 control は所見2として修正必須。

7. **refuted / nit — 揮発値の焼き込みは確認されない。**

   根拠: hard-coded SHA と日付は HEAD や現在時刻ではなく、固定台帳と裁定 ID の契約値（`test_check_ai_provenance.py:1323-1390`）。件数6/5/1は固定された commit list、singleton range、隔離 tmp repo に対する値であり、将来の通常 commit 追加では増えない。tmp repo の生成 SHA は変数から期待値を組み立てている（同:1627-1645）。

   影響: 通常の commit 追加だけでは期待 payload・件数・rc は変化しない。履歴書換えや対象 object の消失時だけ意図的に赤になる。

   推奨対処: なし。

8. **refuted / nit — 既存テストの期待値緩和はない。**

   根拠: 既存テストへの変更は全4件。文字列を `NormalFinding(text, kind)` へ置換した2件は構造追従（`test_check_ai_provenance.py:1199-1205`, `1705-1710`）。`known_violations == ()` の追加（同:2021）と worker 間等価性の追加（同:4290）は強化である。反転、部分一致化、skip、削除はない。

   影響: 既存の拒否条件・rc・出力受理集合は広がっていない。

   推奨対処: なし。

9. **refuted / nit — 正例3件は固定されている。**

   根拠: (i) 既知のみ rc=0 は `test_check_ai_provenance.py:1623-1633`、(ii) `3f2c43d7` が新規かつ rc=1 は同:1667-1678、(iii) 台帳外部分 range が rc=0 は同:1580-1602。それぞれ `main --range` 経路まで通している。

   影響: 過剰拒否へ退行すると、対応する rc=0/1 または exact stdout/stderr が変わって赤になる。

   推奨対処: なし。

## 総括

静的には M2〜M9 は少なくとも一つの追加 assert で検出されるが、M1 には決定的な killer がない。  
M4 は全 suite では検出されるものの、事前登録された空-registry control 自身は恒真である。  
(B) は bounded-child marker と早期位置の被覆が不足し、現実装も marker ありで二重表示する。  
correction/waiver composition と test 名一意性の meta-test も未充足である。  
pytest は実行しておらず、緑は主張しない。