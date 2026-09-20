# [T-2711] t080 hermetic e2e の独立検算を ancestry 2 件まで拡張し 17 observation 全件にする

- wave: `dev-wave-t2711-ancestry-check` (branch `worktree-dev-wave-t2711-ancestry-check`、起点 main `b7f970dfa`、2026-09-20 07:08〜)。
- 依頼: 台帳 entry 1554 の T-2711 「t080 の report の独立検算が 17 observation のうち先頭 15 件しか覆っていない。案 B を採らなくても残る検出力の穴であり、残り 2 件の ancestry 系 observation を独立期待値と比較する形にできるかを調べる」。できるなら Codex author (D95) が test の検算 2 件を足す、できないなら理由を残して閉じる。案 B 不採用のまま、規律 2 を緩めない、本題の検算 2 件だけ。
- 結論: **できた。** `orchestrator/tests/test_s8b_oracle_driver.py` の hermetic e2e に assert 1 個 (literal 2 dict と `items[15:]` の完全一致) を足した (実装 commit `d24ec35ea`、Codex author)。新旧両版の変異 matrix で、対象 e2e 単体では追加前 SURVIVED / 追加後 KILLED となる変異 (subject drift) と、既存 unit test が既に kill する変異 (status/observed) を分けて記録した (§5)。
- 逐語の `verbatim/focus1.log` は末尾空白 3 行を可逆最小正規化した (原文 hash・復元法は `verbatim/normalization.json`)。
- 段の逐語: `s1-brief.md`、`s4-ruling.md`、`verbatim/s3-consult.md`、`verbatim/s6-review-A.md`、`verbatim/s6-review-B.md`、`verbatim/s5-author.md`。変異: `mutation/spec-old.json`、`mutation/spec-new.json`、`mutation/results-old.json`、`mutation/results-new.json`、各 wrapper receipt、`mutation/summary.txt`。段 6 裁定は `s6-ruling.md`、前提 probe の source と実走結果は `probe-source.md`。

## 1. 穴の正確な形 (段 1〜4 で確定)

M = `orchestrator/campaign/t080_freeze_migration.py`、T = `orchestrator/tests/test_s8b_oracle_driver.py`、R = `orchestrator/campaign/s8b_oracle_report.py`。行番号は起点 main `b7f970dfa` のもの。

- M `_make_observation` (2294〜2329 行) の items = source-repin 13 + generator-metadata 2 + ancestry 2 (known_axes → holdout、`subject="/frozen_at_head"`、`recorded` = M 定数 `2066ce6b…` / `2e20d441…`、`observed` = validation_head または None、`status` = `_classify_ancestry` (883〜901 行) の 5 値)。
- T の hermetic e2e (2005 行〜) は `len(items) == 17` (2033 行) と `items[:15]` の独立導出比較 (2052〜2055 行) を持つが、`items[15:]` は report との一致 (2077〜2081 行) だけ。report の `_campaign_t080_observation` は production の `_classify_ancestry` / `_make_observation` を再利用して再導出する (R 259〜322 行) ので同一 source。
- R の envelope 文法検査 (180〜228 行) は ancestry item について status ∈ {missing-commit, not-ancestor, ancestor}、`missing-commit` ⇔ observed=None、recorded = M 定数、順序、key 集合を検査するが、**hermetic fixture で `missing-commit` であるべきこと**と subject の値は検査しない。
- したがって、`_classify_ancestry` の object 不在分岐が `not-ancestor`/`ancestor` + hex observed を返す退行、および `_make_observation` の subject が変わる退行は、対象 e2e と report を通す (静的読解、段 3 consult A4 の表で確認)。

## 2. 独立期待値の形 — literal を選んだ理由 ((P1)、条件付き支持)

hermetic fixture は `git init -q` (T 1426 行) から `git add -A` で作る。M `_capture_head` (636〜654 行) は `objects/info/alternates` / grafts / replace refs / shallow を `receipt.git_error` で拒否し、M `_git_env` (559 行) と T `_sanitized_git_env` (369 行) は `GIT_*` を剥がす。fixture builder は file 内容を写すだけで主 repo の commit object を移送しない。通常の Git と正常に構築された fixture を前提に、記録 commit が fixture の store に入る経路は確認できなかった (段 3 consult A3、静的)。

- 親 probe (`probe/premise_classify_ancestry.py`、repo 外、login で実走): `git init` + 1 commit の空 repo で production `_classify_ancestry` を直接呼ぶと両 artifact とも `status='missing-commit', observed=None, refusal_reason=None`。
- literal (`"missing-commit"` / `None` / SHA 2 本の逐語) は production の返値・定数に依存しない独立 oracle であり、同時に「fixture の object 不在」という前提も固定する。test 側 git 導出 (`_independent_ancestry_item`、T 412〜439 行) は本 2 変異に対して literal と同等の検出力を持つが、store に記録 commit が入ったとき期待値を追随させる性質がある。本 wave は追随でなく前提固定を選んだ。併用は同じ 2 件の確認なので冗長として省いた。
- 「literal は git 導出より常に強い」とは主張しない (段 3 A3 で訂正)。「未知 field の検出」は R 191〜192 行の key 集合検査が既に行うので成果に数えない (A5)。

## 3. 実装 (段 5、Codex author)

- 変更 file: `orchestrator/tests/test_s8b_oracle_driver.py` の `test_t080_stub_free_draft_finalize_commit_and_public_gate_e2e_b5`。2055 行直後に comment 2 行 + `assert items[15:] == [ {...known_axes...}, {...holdout...} ]` (20 行追加、削除なし)。差分は実装 commit `d24ec35ea` (`git show d24ec35ea`) を正とし、insight には patch file を写さない (実装面の複製は Codex author を要する)。author の報告は `verbatim/s5-author.md`。
- 既存 3 検査 (17 件、`items[:15]`、report 一致) は保持。production・R・fixture builder・helper・parametrize・nodeid 集合は不変。author の sandbox では pytest が起動できない (guard) ので「実装済み・未実走」で受領し、親が計算ノードで焦点走した。

## 4. 焦点走 (段 5、計算ノード)

- 投入: `python3 tools/run_tests.py --force-dispatch` で変更 test file `orchestrator/tests/test_s8b_oracle_driver.py` と、同 file を nodeid 集合で pin する meta test 3 file (`test_real_repo_serialization.py`、`test_growth_test_holds_contract.py`、`test_hold_inventory.py`) を同一走で (DW-O18/O26)。checkout = wave worktree、patch 適用後・commit 前の tree (= `d24ec35ea` と同一内容)。
- 結果: **348 passed / 7 skipped / 0 failed / 0 error**、pytest 303.24 秒 (xdist 48 worker、355 item)。request `11855.nqsv` (gen_S)、投入 07:32:46 → 収集 07:38:15 JST。log は `verbatim/focus1.log`。受入全走ではない (log 先頭の警告どおり)。
- skip 7 のうち 6 件は log に列挙された growth hold (`test_real_freeze_gate_lists_floor_and_budget_null` を含む実 repo test 5 件 + `test_protocol_builder_repo_tree_guard_is_wired_to_real_root`)。残る 1 件は非 verbose log から node を特定できない。追加 assert に skip を生む経路は無いので本 patch への帰属根拠はない。「4 file の全 node が実行済み」とは書かない。
- 対象 e2e が緑 = hermetic fixture で `verify_receipt` の ancestry 2 件が `missing-commit` / `None` / 記録 SHA と観測された、の直接観測 (§2 の推論を実測で閉じる)。

## 5. 変異 matrix (段 6、DW-M08 の新旧両走)

走行集合 S = {e2e = `test_s8b_oracle_driver.py::test_t080_stub_free_draft_finalize_commit_and_public_gate_e2e_b5`, unit = `test_t080_freeze_migration.py::test_ancestry_missing_nonancestor_ancestor_noncommit_and_git_error`}。harness は `tools/mutation_worktree.py` (D1009 の独立 clone、旧版 = main `b7f970dfa`、新版 = main `d24ec35ea`、`--runner-mode dispatch --detached`、`run_tests.py --force-dispatch <2 nodeid> -q -rf`)。

| id | 位置 (M) | 変異 | 旧版 (b7f970dfa) 事前登録 → 実測 | 新版 (d24ec35ea) 事前登録 → 実測 | 新 assert に帰属する差分 |
|---|---|---|---|---|---|
| M1 | 890 行 | missing → `("not-ancestor", recorded, validation_head)` | KILLED {unit} → **KILLED {unit}** (1227 行、780.4 秒 = queue 待ち含む) | KILLED {unit, e2e} → **KILLED {unit, e2e}** (e2e は 2058 行の追加 assert、diff = `status='not-ancestor', observed='2359f93a…'`；171.4 秒) | e2e が加わる |
| M2 | 890 行 | missing → `("ancestor", recorded, validation_head)` | KILLED {unit} → **KILLED {unit}** (1227 行、181.6 秒) | KILLED {unit, e2e} → **KILLED {unit, e2e}** (e2e は 2058 行、diff = `status='ancestor', observed='4682fc6d…'`；196.3 秒) | e2e が加わる |
| M3 | 2314 行 | subject `/frozen_at_head` → `/frozen_at_head/` | SURVIVED {} → **SURVIVED {}** (186.1 秒) | KILLED {e2e} → **KILLED {e2e}** (2058 行、diff = `subject='/frozen_at_head/'`；155.4 秒) | e2e だけが検出 |

- 実測 (2026-09-20 07:36〜08:00 JST、計算ノード dispatch、wrapper receipt は両版とも `child_rc: 0`、`mutation/results-old.json` / `results-new.json`、要約 `mutation/summary.txt`): 旧版 = baseline PASSED (176.2 秒)、KILLED 2 / SURVIVED 1、**期待 node 完全一致 3/3**。新版 = baseline PASSED (216.7 秒)、KILLED 3 / SURVIVED 0、**期待 node 完全一致 3/3**。両版とも MISMATCH / PARSE_ERROR / TIMEOUT は 0。spec sha256: 旧 `9d33f779…`、新 `a1117814…`。
- 帰属: 新版 e2e の赤は 3 変異とも `orchestrator/tests/test_s8b_oracle_driver.py:2058: AssertionError` (追加 assert) で、先行する既存 assert (`refusals == ()`、`active-valid`、`len(items) == 17`、`items[:15]`) は通過している (各 job stdout の失敗 excerpt、`results-new.json` の `artifact.stdout`)。unit の赤は両版とも `test_t080_freeze_migration.py:1227` (`missing.status == "missing-commit" and missing.observed is None`)。
- 読み: M1/M2 (status/observed) は既存 unit test が両版で kill し、新 assert は e2e を失敗集合に加える (スイート全体の未検出を解消したのではない)。M3 (subject) は旧版で SURVIVED、新版で e2e だけが kill = **新 assert だけが検出する差分**。DW-M08 の「新テストだけが検出する差分」は M3 で示し、M1/M2 は e2e 単体の検出力の追加として記録する。
- 時間の出所: `duration_s` は harness が記録した dispatch 外側 wall (queue 待ちを含む、M1 旧の 780 秒は queue)。対象 e2e 単体の所要ではない。

## 6. 段 3 / 段 6 の所見と裁定

- 段 3 consult (codex gpt-6-astra / medium / read-only、2 レンズ): must-fix 2、should 3、nit 4。全部 real・採用 (`s4-ruling.md` §1)。棄却なし。
  - A1: `test_t080_freeze_migration.py::test_ancestry_missing_nonancestor_ancestor_noncommit_and_git_error` (1212〜1235 行) が production `_classify_ancestry` の missing 分岐を直接 assert 済み (1227 行) → M1/M2 は全スイートでは既に KILLED。本 wave の主張は「e2e の独立検算を末尾 2 件まで拡張」であって「スイート全体の未検出変異を解消」ではない。
  - A2: 記録 commit `2066ce6b…` / `2e20d441…` は現行 repo の object store にも無い (親が自 worktree で `git cat-file -t` rc=128 ×2 を実測)。`docs/freeze-permanent-design-s2.md` の anchor 表 (145〜156 行) が全要素 `anchor_status=="missing"`、`disposition=="legacy-history-only"` と記録する既知の設計事実。したがって実 repo test (`test_real_freeze_gate_lists_floor_and_budget_null`、T 3758 行〜) も現状 missing 分岐を git 導出 (`_independent_ancestry_item`) で期待しており、M1/M2 を旧版でも kill する (静的予測、S に入れない理由)。本 wave は記録のみで新 T・新 gate を起こさない (scope 外・既知)。
- 段 6 レビュー 2 本 (`s6-ruling.md`、逐語 `verbatim/s6-review-A.md` / `s6-review-B.md`): **must-fix 0、patch GO**。should 2 件 (実 repo test を S に入れない理由の言い直し、先行裁定への「訂正」表現の限定) は docs で採用、nit 2 件 (comment 2 行目の削除、M2 の削減) は不採用 (成果物不変、変異は投入済み)。fix 子・焦点再レビューは無し。初回投入 (tag A/B) は親が review 段に `--reasoning` を付けて rc=2 (DW-C01 記載済みの禁止形) → tag A2/B2 で再投入。
- 走行集合 S を {e2e, unit} に絞った理由 (レビュー A-should A1 / B-should S1 の言い直し): 既存 unit と対象 e2e で追加検出の帰属を示せる最小集合だから。実 repo test は growth hold で焦点走でも未実行 (hold 解除・比較到達時には M1/M2/M3 を全部検出すると静的予測、その場合も e2e が加わる node 集合の差分は残り、消えるのは M3 の集約 status の差だけ)。

## 7. 訂正・限界・主張しないこと

- 起点 entry 1554 §2-2 の「alternates 経由で見えると ancestry が `missing-commit` から `not-ancestor` へ変わりうる」について (レビュー B-S2 で表現を限定): M `_capture_head` の alternates 拒否は 2026-07-22 `a0e090f66` から存在し、現行 `verify_receipt` の入口で `receipt.git_error` になるため、先行裁定の条件付き観測変化をそのまま現行 e2e の実行経路の説明には使えない。先行裁定は可能性で書いており拒否経路の存在を否定してはいない (「訂正」ではなく補足)。案 B 不採用は prune risk 等の他理由で残り、本 wave は再裁定しない。
- 成果は「17 件すべてに独立比較がある」であって「17 件すべての全 field を独立検算した」ではない。先頭 15 件は従来どおり 4 field (artifact, kind, subject, observed) の比較で、recorded / status は R の文法検査 (定数一致・固定 status) に委ねている。末尾 2 件だけが 6 field の dict 完全一致。
- 実 repo test (T 3758 行〜) は 17 件全部を独立期待値と完全一致で比較するが、`_independent_ancestry_item` を使うのは末尾 2 件だけ (先頭 15 件は golden tuple)。brief 初版の「17 件全部を `_independent_ancestry_item` で比較」は不正確。
- brief 初版の「source-repin 10 + generator-metadata 5」は誤りで 13 + 2 (段 3 B1 で訂正、M 104〜119 行・R 184〜188 行)。
- 「hermetic fixture で `missing-commit`/None は構造的に決まる」は現物コードの読解と空 repo probe からの推論であり、e2e fixture そのもので `verify_receipt` を走らせた直接観測ではない。直接観測は焦点走 (§4) と新版 baseline (§5) の緑が担う (追加 assert が通った = fixture で missing-commit/None が観測された)。
- 「受入全走が速くなる」「案 B が採れるようになる」とは主張しない。案 B (fixture 高速化) は不採用のまま。

## 8. 工数

- codex 子 4 本 (consult 1、author 1、review 2)、いずれも rc=0 で受理検査 OK。レビューの初回投入 2 本は親の argv ミス (`--reasoning` を review 段に付与) で rc=2、即再投入。fix 子 0。
- 計算ノード job: 焦点走 1 (11855.nqsv)、変異 = 旧 4 走 (baseline + 3) + 新 4 走、provenance 全史監査 1、受入全走 (§9 に追記)。login の親 probe 1 本 (数秒)。
- 親の実測: 前提 probe、`cat-file -t` ×2、pin 閉包の grep、plan-only ×2。

## 9. 受入全走・land (段 9)

受入全走は DW-O12 に従い本記録 commit の後に `tools/dev_wave_wait.py acceptance` (門番 loop 経由) で投入する。本書の commit 時点では未実施であり、結果 (child-green / tested main / tested tip / 所要) は job dir `/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2711-ancestry-check/acceptance-receipt-final-N.json` と land の receipt に残り、worklog の fold 日付が land 完了を示す。本 wave は受入結果を repo 内に後書きしない (記録 commit 後の追記は tested tip を変えるため)。
