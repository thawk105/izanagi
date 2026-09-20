# 段 4 裁定 — [T-2304] (2026-09-20 13:4x JST、段 2/3 省略の軽量版)

## 裁定 inbox の再走査
- `/work/1/SFC/tanab/dev-wave-jobs/rulings-inbox/` の最新は 2026-09-20 の第 25 回 (D2174) と t2724 A/X 控え。pin 前進に触れる新裁定なし。D2150 項 1 が最新の正本。

## provisional 裁定の確定
- (P1) clang 14 未確認は限界として記録し再検査しない — real / 採用 (D2150 項 1 (iii) のとおり)。
- (P2) `docs/phase3-8b-restart-runbook.md` P1 行への前進注記 — real / 採用 (人間 preflight の期待値が現行 gitlink と食い違うと restart 手順が偽赤で止まる。新 gate ではなく既存行の注記)。
- (P3) 段 2/3 省略、段 6 敵対レビュー 2 本維持 — 採用 (受理集合が変わるため独立検証子は残す、DW-C00)。

## plan v2 (file:line)
1. gitlink `external/ccbench` → `e9e477ca1b55348ab4530de0b1cf663ce4555290` (author は submodule 内で `git checkout <sha>` し親が `git add external/ccbench`。DW-C01: add/commit は親)。
2. `orchestrator/campaign/s8b_approved.py:67` `CCBENCH_FULL_SHA = "e9e477ca1b55348ab4530de0b1cf663ce4555290"`、同 file 29/66 行の説明の現行値を更新。
3. `orchestrator/campaign/pin.py:28` `CURRENT_PIN = "e9e477c"`。docstring の履歴 (dff0f1e → 028f34d → d706650 → 511c953) は保持し、511c953 → e9e477c (mocc trace v2 hook + T-1943 lineage witness + TRACE=0 include identity fix、D2150 項 1) を 1 段追記。`PREVIOUS_PIN` は「直前の pin」の定義に従い `"511c953"` へ更新するか据え置くかは author が docstring の定義文に合わせて判断し理由を報告 (参照用のみ、consumer なし → 据え置き可)。
4. `orchestrator/campaign/buildcache.py:1055-1062` docstring: 再実測結果を受けて pin 記述を追記 (旧 pin の実測事実は残す)。
5. ⑦ test 追随: `test_s8b_approved.py` (gitlink 実読、変更不要のはず)、`test_p3_s4_loop_sort.py:781`、`test_p3_s4_loop_trigger_gating.py:2170`、`test_p3_build_authority_cli.py:196`、`test_s6_sort_sweep.py:390`、`test_s8a_trigger_sweep.py:108,485` を候補とし、author は焦点走で赤になった test を「現行 pin 一致を主張する test か」で判定して追随。旧 pin control (`test_mocc_proof_surface.py`、`test_mocc_trace_*.py` BASE_OID、A-1 v3 `canonical_pin`、a2 fixture `current_pin`、`b10_backoff_shape_locks`、plot fixture) は据え置き。判定表を report に残す。
6. ④ probe: author が `tools/dev-wave-probe/t2304_buildcache_shape_probe.py` (worktree 内、親が実行前に job dir へ退避し worktree からは削除) を書く。内容: 引数 `--ccbench-commit <sha> --ccbench-root <path> --out <json>`。候補 sha を `git archive` でなく `git worktree add --detach` した一時 checkout (または既存 `patchharness.checkout`) から source snapshot を作り、build dir を snapshot 外に置き `cmake -G "Unix Makefiles" -DFETCHCONTENT_FULLY_DISCONNECTED=ON` で configure (FetchContent base-only、third_party 供給は `tools/pegasus/fetch_third_party.py` の既存経路 / 環境変数を再利用し新経路を作らない)、`buildcache._assert_fetchcontent_fully_disconnected_effective(build_dir)` と `buildcache._masstree_source_root_from_cmake_cache(build_dir)` を呼び、結果 (返り値 / 例外文字列、CMakeCache の該当 3 行、DependInfo の pairs block、cmake/g++ version) を JSON に書く。100 行程度。
7. docs-only (親): `docs/phase3.md:2696` の `e9e477ca` literal → 「候補 (D2150 項 1 の commit、現行値は `pin.CURRENT_PIN`)」形へ。`docs/phase3-8b-restart-runbook.md:161` P1 に「2026-09-20 [T-2304] で `e9e477ca…` へ前進」注記 — ただし LIVING_DOCS 外なので literal 可。

## 変異事前登録 (DW-M01、実装前に固定。spec は実装後に `old` 文字列を実体から写す)
| id | category | 位置 | 置換 | 期待 | 期待 killer (node) | 単一理由 |
|---|---|---|---|---|---|---|
| MUT-1 | negative | `orchestrator/campaign/s8b_approved.py` `CCBENCH_FULL_SHA` | 新 40 桁 → 旧 `511c9538…` | KILLED | `test_s8b_approved.py::test_ccbench_full_sha_matches_real_gitlink` (gitlink 実測 ≠ 承認定数) と `::test_ccbench_full_sha_is_40hex_and_current_pin_is_prefix` (prefix 不成立) | 承認定数の値退行 |
| MUT-2 | negative | `orchestrator/campaign/pin.py` `CURRENT_PIN` | `"e9e477c"` → `"511c953"` | KILLED | `test_s8b_approved.py::test_ccbench_full_sha_is_40hex_and_current_pin_is_prefix`、`::test_ccbench_full_sha_matches_real_gitlink`、`test_p3_s4_loop_sort.py::test_default_cfg_axis_is_sort_marker`、`test_p3_s4_loop_trigger_gating.py::test_default_cfg_wires_s2_verify_and_axis`、`test_s6_sort_sweep.py::test_public_sweep_reaches_pipeline_with_exact_stock_and_machine_classes`、`test_s8a_trigger_sweep.py::test_public_sweep_reaches_pipeline_with_exact_stock_and_machine_classes`、`test_p3_build_authority_cli.py` の `_EXPECTED_REPO_STOCK_PIN` 比較 node (実装後に node id を確定) | 現行 pin 値の退行 (独立 literal を持つ test が拘束する) |
| MUT-3 | positive (等価) | `orchestrator/campaign/pin.py` の comment 1 行 | 語句の等価な言い換え | SURVIVED (expected_nodes 空) | なし | harness の SURVIVED 検出の正例 |

過剰拒否の正例 (受理集合が移る): `test_build_admission.py` の STOCK_BASELINE 正例が `pin.CURRENT_PIN` 記号参照で緑のまま (焦点走で確認)。

## 段 6 追補 (14:3x JST) — レビュー B must-fix「policy sha の波及」の裁定 (相談 D / X の 2 レンズを経て親が決定)
- 新事実 A (real): `build_admission._new_policy()` の preimage が `repo_stock_pin=CURRENT_PIN` を含み、pin 前進で admission policy sha が `949ddcc2…` → `db6bc9ea…` へ移る。現行 policy を要求する live 経路 (binary admission receipt 照合、`LaunchValidatedFreeze`、floor の旧 binary 再利用・resume、`ident.py` の旧 lock 拒否、`p3_s4_loop.py` の policy 束縛) は、旧 policy の binary / lock を新 main から消費できない。D2150 項 1 の「独立 full OID の driver と旧凍結の保持で影響を受けない」は、**pin 前進前の superproject + 対応 submodule + 旧契約の固定 checkout (submit-tree) での継続と旧証拠の保持についてだけ成立**し、新 main での live 消費には成立しない。
- 新事実 B (real): `resolve_current_floor_protocol()` は新 gitlink の checkout で候補 2 件 (anchor d706650 / versioned 511c9538)・head exact 0 件となり fail-closed で raise する。新 pin の successor protocol は材料 ⑤ (AI reseal) で、D2150 のとおり新系列の着手時。
- 決定 = **O2 (訂正版)**: wave は tested tip まで完成させる (epoch golden 以外の実 repo 由来の赤も ⑦ として直す。skip / xfail / assert 削除で隠さない)。land は並行 wave [T-2724] (凍結 v2 g1 の A/X) の **land 完了 tip `AX_DONE` が local main に含まれる** (`git merge-base --is-ancestor AX_DONE main` rc=0) ことを確認してから、その main を post-claim merge で取り込んだ tip の受入を経て行う。待機は policy 問題の解決ではなく、「旧 pin + A/X を含む pin 前進前の commit を歴史再開の起点として先に確定する」ための順序。
- 記録: decisions fragment で新 D を起こし、D2150 項 1 の承認対象・実装範囲・②③⑤ の時期は変更せず、「影響を受けない」の射程を上記のとおり限定する事実を追記する (D2150 の逐語は書き換えない、ユーザー再裁定を受けたとは書かない)。帰結は「旧系列は pin 前進前の superproject・対応 submodule・旧契約で継続」「新 main への移行は系列ごとに ②(登録・identity) ③(driver) ⑤(successor protocol) と source / admission の整合が要る。旧 binary の再 admission だけでは旧 lock の継続も source pin の不一致も解消しない」と書く。置き場 = insight・worklog 本文・decisions fragment・runbook P1 行の既存注記。新 gate / 検査 / 台帳は足さない。
- 採らない案の最も強い形: O3 (停止・ユーザー再裁定) は DW-S04 / DW-STOP の文面では最も保守的だが、候補の正しさは否定されておらず、ユーザーの恒久指示 (相談して親が決める) の下では事実訂正と順序調整で処理できる。O1 (今すぐ land) は T-2724 の残工程 (実 repo 真値・gate-check・受入) に新しい拒否原因を持ち込む。O4 (policy から pin を切り離す) は受理集合・identity の設計変更で scope 外。
