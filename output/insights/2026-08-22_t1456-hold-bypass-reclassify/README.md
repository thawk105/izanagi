# [T-1456] hold_inventory.py の bypass_surface 誤報是正

wave: dev-wave-t1456-hold-bypass-reclassify / 2026-08-22 / base main c63c6b56

## 依頼

`tools/hold_inventory.py:107-141` の test層 `bypass_surface` が、既存の二層guard
(`enforce_held_functions`/`_wrap_held_function`) が既に拒否している4経路
(plain runner・`--noconftest`・`--confcutdir`・direct call) を `known-unresolved-bypass`
と誤報している疑いを検証し、確認できれば是正する。過去2wave が指摘のみで未着手のまま
残っていた。過去の指摘を鵜呑みにせず自分で4経路を実測して裏取りすることが求められた。

## 経緯 (git に入らない部分)

`known-unresolved-bypass` の4 entry は2026-08-12 [T-914]/D328 系で `tools/hold_inventory.py`
新設時に書かれ、`tracking: "T-930"` を持つ。2026-08-13 (515) の [T-930] wave (D360) が
まさにこの4経路を閉じる二層guardを実装した (import時 `enforce_held_functions`・呼出し時
`_wrap_held_function`、8/8 KILLED)。しかし `bypass_surface` の記述はこのとき更新されず、
以後2wave (2026-08-16 T-1222 archive 606、2026-08-21 T-1222 archive 778) が
「scope外のreal所見」として指摘したが実装しなかった (「本waveが作った穴ではない」という
理由で起票のみ)。2026-08-16に起票された先行ID [T-1267] が今回の [T-1456] と同一事案
であることを段3 luna レンズが検出した。

## 親の実測 (2026-08-22、本worktree、現HEAD)

対象: `orchestrator/tests/test_s8b_repo_scan_invariant.py` (plain_runner="manual"、
guard呼出しは:55)。

| 経路 | コマンド | 結果 |
|---|---|---|
| plain-python-runner | `python3 <file>` | rc=1、import時 `GrowthTestHoldBypassRefused` (:55→growth_test_holds.py:689) |
| pytest-noconftest | `pytest --noconftest <file>` | rc=2、collection ERROR 同exception |
| pytest-confcutdir-below-suite | `pytest --confcutdir=orchestrator/tests/__pycache__ <file>` | rc=2、同上 |
| direct-test-function-call | `python3 -c "import ...; call()"` | rc=1、importの時点で例外 (呼出しへ未到達) |
| (control) | 通常 `pytest <file>` (token未設定) | rc=0、1 skipped、`IZANAGI_GROWTH_HOLD_V1` 構造化メッセージ |

4経路すべてが現行guardで確定的に拒否されることを確認し、誤報を確定した。

`plain_runner="pytest-delegating"` の file (`test_env_attestation.py`) は `__main__` 終端が
`raise SystemExit(pytest.main([__file__, "-q"]))` で D360 のAST照合契約どおりであることを
静的に確認した (未実行)。

## 段2 codex plan → 段3 敵対相談2レンズ

段2 plan (`known-resolved-bypass`/`rejected-by-hold-guard` 案) を段3 sol レンズ
(正しさ・過大申告レンズ) が攻撃し、D360 の適用範囲 (同一process内 `__wrapped__` 直呼び・
guard再束縛は対象外) を越えて一般化していると判定 (real)。`plain_runner="pytest-delegating"`
では拒否機序が import-time raise でなく委譲後の graceful skip になる点も指摘した。
luna レンズ (見落とし・consumer整合レンズ) は [T-1267] の先行を検出し (real)、
D347抵触はどちらのレンズもrefutedとした。詳細は `verbatim/s3-sol.md`・`verbatim/s3-luna.md`。

## 段4裁定

`classification: "known-guarded-bypass"`・`effect: "blocked-by-hold-guard"` を採用し、
reasonはoutcome指向 (「exact tokenが無い限りblocked」) とした。`tracking: "T-930"` は
フィールド名を維持し、reason側で解決済みを明示する方針とした。詳細は `verbatim/s4-ruling.md`。

## 段5実装 → 段6敵対レビュー → fix

Codex `role=author` (gpt-5.6-luna, reasoning=max) が `tools/hold_inventory.py` と
`orchestrator/tests/test_hold_inventory.py` の対象2 file・4 entry を更新。reviewA
(実装忠実性レンズ) は所見ゼロ (golden-copy 3箇所のbyte-for-byte一致を確認)。reviewB
(最終文言正確性レンズ) が「T-930により解決済み」の明示が反映されていないとreal所見を
出し、fix1で4 entry全部のreasonへ「T-930 closed this bypass: 」を追加して是正した
(reviewBのnitも同時採用)。詳細は `verbatim/s5` 系・`verbatim/s6-reviewA.md`・
`verbatim/s6-reviewB.md`・`verbatim/s6-fix1.md`。

親が非pytest直接比較 (`hold_inventory() == _expected_inventory()`) で独立確認し、
Pegasus dispatch が安定した後に `tools/run_tests.py orchestrator/tests/test_hold_inventory.py`
で6/6 PASSED を実測した (dispatch経由、queue congestion発生前)。

fix1後、DW-O16の焦点再レビュー1本 (`verbatim/s6-focus.md`) を投入し、reviewAの
「所見なし」維持・reviewB real/nit双方の closed を対応表で確認した。partial/regressed
なし、残る所見なし。

## 変異matrix

`mutation-spec.json` 参照。MUT-1 (`plain-python-runner` の `classification` を
旧stale値へ差し戻す)・MUT-2 (`direct-test-function-call` の `reason` からtoken節を除去)
の2件を事前登録した。事前確認 (in-memory simulation、`verbatim/s4-ruling.md` 参照) で、
両変異とも `test_inventory_projects_exact_registered_source_sets` **のみ** を検出する
単一理由の変異であり、`test_main_dispatches_human_and_json` 等の他テストには影響しない
ことを実行前に確認した。

本走 (anchor commit `d8e3d012`、`tools/mutation_worktree.py --runner-mode dispatch`、
runner argvは `/usr/bin/python3 tools/run_tests.py orchestrator/tests/test_hold_inventory.py
-rf --force-dispatch -p no:cacheprovider`) 結果は `mutation-out.json` 参照。
**baseline PASSED (6 passed)・MUT-1 KILLED (matches_expectation=true)・MUT-2 KILLED
(matches_expectation=true)・SURVIVED 0・MISMATCH 0。** 両変異とも期待どおり
`test_inventory_projects_exact_registered_source_sets` のみを検出し、事前simulationの
予測と完全一致した (初回登録での MISMATCH なし)。

## Pegasus 計算ノード混雑 (段6後半)

`gen_S` queueが本wave段6後半で severe に混雑 (待ち70〜82件で高止まり、実行数56→66)。
「lease coordination compute saturation」セッションとの連携で、`dev_wave_wait.py
acceptance` の `preclaim-history-provenance` 段の300秒SIGKILLがPBS jobを孤児化する
設計バグが混雑要因の一つと判明した (孤児14件を別セッションがqdel済み)。本waveは
同経路を未使用と確認し、fix連絡まで新規の受入投入を控える方針で協調した。
`tools/check_ai_provenance.py` の直接呼出しは同じ孤児化経路ではないと実測で確認し
(timeoutした過去request ID 4件がqstatから既に消滅、`_best_effort_qdel`による後始末と
判断)、これをpeerへの裏取り材料として報告した。
