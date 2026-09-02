## 所見 1 — README 編集は T-2177 の所有面と衝突する

- **所見:** must-fix。段2プランの README 置換は、T-2177 が所有する r5/D799 の訂正面へ踏み込みながら、その必須区別を落としている。

- **根拠 (file:line):** 親 brief は T-2177 を明示的に除外する一方、同じ行の編集も要求しており、内部に所有範囲の矛盾がある（[brief.md:8](</work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2176-dense-cycle4-fixture/brief.md:8>)、[brief.md:11](</work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2176-dense-cycle4-fixture/brief.md:11>)、[brief.md:55](</work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2176-dense-cycle4-fixture/brief.md:55>)）。段2案は当該行を「r9 がこの穴を担う」へ置換する（[s2-plan.md:143](</work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2176-dense-cycle4-fixture/artifacts/t2176-dense-cycle4-fixture/s2-plan.md:143>)）。しかし T-2177 の論点は r5 が長さ4のグラフ検出を担う一方、unclean のため certified 遷移を担わないこと（[worklog-1176-carry.md:11](</work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2176-dense-cycle4-fixture/refs/worklog-1176-carry.md:11>)）。現行 D1466 もこの区別を落とさない訂正を要求している（[docs/decisions.md:45922](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2176-dense-cycle4-fixture/docs/decisions.md:45922)）。

- **失敗する具体例:** 計画どおり置換すると、単純な「長さ4以上を無視する」変異は既存 r5 でも赤になる事実を伏せたまま、r9 が一般的な長周期穴を単独で塞いだように読める。正しくは、r5 がグラフ検出、r9 が clean 入力からの certified 誤遷移を担う。

- **提案:** 段4へ返す。厳密な線引きは、T-2176 が README 表の r9 行だけを追加し、現行179行と r5/D799 の説明は T-2177 が担当する形。偽記述を同時に残せない場合は、両 task の統合を親が明示裁定し、「r5＝グラフ事実、r9＝clean certified 経路」を併記する。

## 所見 2 — 在庫・pin の機械的閉包は `_V2_FIXTURE_FILES` だけで足りる

- **所見:** 親が挙げた在庫閉包に機械的な漏れはない。新しい2ファイルの `_V2_FIXTURE_FILES` 登録は必須だが、checker 本体その他の pin 更新は不要。

- **根拠 (file:line):**

  - **更新が要る:** `_V2_FIXTURE_FILES` に `r9_dense_cycle4/trace_0.log` と `trace_1.log` を追加する。既存 checker は fixture root を再帰走査し、実ファイル集合と tuple を完全一致で比較する（[test_verifier.py:226](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2176-dense-cycle4-fixture/orchestrator/tests/test_verifier.py:226)、[test_verifier.py:257](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2176-dense-cycle4-fixture/orchestrator/tests/test_verifier.py:257)）。README 表への1行追加も文書在庫として必要（[fixtures/README.md:14](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2176-dense-cycle4-fixture/orchestrator/tests/fixtures/README.md:14)）。
  - **更新不要:** `test_all_v2_fixture_files_have_clean_framing` 自体は tuple から対象 directory を導出する（[test_verifier.py:263](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2176-dense-cycle4-fixture/orchestrator/tests/test_verifier.py:263)）。素の runner も全 `test_*` 関数を動的収集する（[test_verifier.py:1939](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2176-dense-cycle4-fixture/orchestrator/tests/test_verifier.py:1939)）。
  - **更新不要:** g5/g6/r8 の実 emitter 3件、skip 不可 role、byte hash 辞書は「実 emitter 由来」専用であり、手製 r9 はその集合へ入らない（[test_verifier.py:1404](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2176-dense-cycle4-fixture/orchestrator/tests/test_verifier.py:1404)、[test_skip_classification.py:327](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2176-dense-cycle4-fixture/orchestrator/tests/test_skip_classification.py:327)、[orchestrator/tests/README.md:204](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2176-dense-cycle4-fixture/orchestrator/tests/README.md:204)、[output/README.md:19](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2176-dense-cycle4-fixture/output/README.md:19)）。
  - **更新不要:** receipt の赤例 `r1/r2`、campaign の赤注入 `r1` は代表例で、赤 fixture 在庫ではない（[test_t1286_commit_receipt.py:214](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2176-dense-cycle4-fixture/orchestrator/tests/test_t1286_commit_receipt.py:214)、[p3_s4_red.py:13](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2176-dense-cycle4-fixture/orchestrator/campaign/p3_s4_red.py:13)）。
  - **更新不要:** 新テストは duration ledger に未登録となるが、未知 node は既知第96位相当の scheduling hint として扱われ、受理判定には使われない（[conftest.py:1567](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2176-dense-cycle4-fixture/orchestrator/tests/conftest.py:1567)、[docs/decisions.md:29077](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2176-dense-cycle4-fixture/docs/decisions.md:29077)）。同 wave での ledger 更新は不要。
  - **更新不要:** `VerifyResult` schema/dataclass と capability の result hash は実行結果から動的生成されるため、fixture 純増では変わらない（[core.py:186](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2176-dense-cycle4-fixture/orchestrator/verifier/core.py:186)、[report.py:96](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2176-dense-cycle4-fixture/orchestrator/verifier/report.py:96)）。trace の `-text` 属性も wildcard 適用済み（[.gitattributes:1](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2176-dense-cycle4-fixture/.gitattributes:1)）。
  - `tools/` に追加在庫 pin はなく、`output/insights/` の言及は過去時点の逐語成果物なので更新不要。

- **失敗する具体例:** 2ファイルを追加して tuple を更新しない、または片方だけ登録すると、実集合29ファイルと期待 tuple が不一致になり `test_all_v2_fixture_files_have_clean_framing` が赤になる。

- **提案:** 段2案の tuple 2行追加を維持する。それ以外の role/group、件数、byte hash、duration ledger、schema pin は増やさない。

## 所見 3 — HEAD blob 束縛の対象外であり、production 変更も計画されていない

- **所見:** 問題なし。段2の全編集 path は `CONTRACT_LOADER_RELATIVE_PATHS` の外で、`orchestrator/verifier/*.py` の変更もない。

- **根拠 (file:line):** 束縛は exact 24 path で、verifier 側は `core.py`、`dsg.py`、`model.py`、`parse.py`、`__init__.py`、`report.py`、`commit_receipt.py` に限定される（[campaign_lock.py:47](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2176-dense-cycle4-fixture/orchestrator/campaign/campaign_lock.py:47)）。capture は各対象について HEAD blob と live disk bytes を一致検査する（[contract_loader_binding.py:348](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2176-dense-cycle4-fixture/orchestrator/campaign/contract_loader_binding.py:348)）。段2の編集一覧は2 trace、`test_verifier.py`、fixtures README のみ（[s2-plan.md:172](</work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2176-dense-cycle4-fixture/artifacts/t2176-dense-cycle4-fixture/s2-plan.md:172>)）。

- **失敗する具体例:** author が `dsg.py` を実装対象へ加えれば未commit時は disk/HEAD drift、記録済み binding に対しては commit blob/digest 不一致となる。一方、test file・fixture・README は exact key 集合に存在せず、再帰的にも取り込まれない。

- **提案:** 現行4 path のままにし、production verifier と campaign lock の path 集合は変更しない。

## 所見 4 — 壊れた `certified=True` は全 downstream 層を通過するが、T-2176 の scope 外である

- **所見:** 実在する層境界である。campaign、receipt/proof、admission、oracle、report は verifier の意味判定を独立再計算せず、発行された `certified` を整合的に運ぶ。そのため verifier 自身が長さ4巡回を落として `certified=True` を返すと、同じ壊れ方は downstream を通る。

- **根拠 (file:line):** `total_cycles==0` が `serializable=True` を作り（[core.py:142](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2176-dense-cycle4-fixture/orchestrator/verifier/core.py:142)）、clean・非空なら `certified=True` になる（[model.py:224](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2176-dense-cycle4-fixture/orchestrator/verifier/model.py:224)）。pipeline はその値を WAL へ書き、false の場合だけ abort する（[pipeline.py:1471](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2176-dense-cycle4-fixture/orchestrator/campaign/pipeline.py:1471)、[pipeline.py:1505](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2176-dense-cycle4-fixture/orchestrator/campaign/pipeline.py:1505)）。receipt は `serializable/true` と result digest を束縛するが、グラフを再計算しない（[commit_receipt.py:223](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2176-dense-cycle4-fixture/orchestrator/verifier/commit_receipt.py:223)）。artifact admission も WAL の `serializable`、`certified=True`、`anomalies=0` と receipt の一致を見る（[artifact_admission.py:705](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2176-dense-cycle4-fixture/orchestrator/campaign/artifact_admission.py:705)）。oracle は certified/non-aborted を committed とし（[s8b_oracle_driver.py:859](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2176-dense-cycle4-fixture/orchestrator/campaign/s8b_oracle_driver.py:859)）、oracle report も bool を pass と読む（[s8b_oracle_report.py:1301](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2176-dense-cycle4-fixture/orchestrator/campaign/s8b_oracle_report.py:1301)）。Layer 3 は admitted campaign/receipt/epoch を要求するが DSG を再検証しない（[layer3_report.py:888](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2176-dense-cycle4-fixture/orchestrator/campaign/layer3_report.py:888)）。

- **失敗する具体例:** 段2が定義する mutant が clean な長さ4 SCC を落とすと `total_cycles=0 → serializable=True → certified=True` になり、pipeline は COMMIT、receipt は正しい形式でその誤判定を束縛し、admission/oracle/report は一貫した certified 証拠として受理する。

- **提案:** **scope 内**は r9 の verifier test と mutation KILLED までで十分。既存 pipeline test は non-certified の伝播を既に固定している（[test_campaign.py:7098](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2176-dense-cycle4-fixture/orchestrator/tests/test_campaign.py:7098)）。**scope 外・要裁定候補**は「downstream に verifier から独立した長周期意味検査を要求するか」。本 wave へ gate・production・proof-chain test を追加せず、必要なら別 task として裁定する。推奨は、T-2176 を producer 境界の回帰検査に限定すること。

## 所見 5 — 編集 path と scope は README の衝突を除き適正

- **所見:** fixture 内の2 trace、`test_verifier.py`、fixtures README で過不足ない。2 thread 化は親の provisional な1-file案を realizability 根拠で修正したもので、fixture directory の所有範囲内である。

- **根拠 (file:line):** 親は fixture directory、test、在庫登録、README の純増だけを許可する（[brief.md:6](</work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2176-dense-cycle4-fixture/brief.md:6>)）。1 file は provisional な検討事項だった（[brief.md:54](</work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2176-dense-cycle4-fixture/brief.md:54>)）。段2は2 thread が必要な理由を示し（[s2-plan.md:1](</work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2176-dense-cycle4-fixture/artifacts/t2176-dense-cycle4-fixture/s2-plan.md:1>)）、編集対象を許可された4 path に閉じている（[s2-plan.md:172](</work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2176-dense-cycle4-fixture/artifacts/t2176-dense-cycle4-fixture/s2-plan.md:172>)）。

- **失敗する具体例:** 1 file に戻すと、単一 thread の逐次実行で「T3 が genesis を読み、その間に T0→T1→T2 が commit」という提示スケジュールを表現できない。逆に parser/DSG の production 修正や新しい一般 gate を加えれば明示 scope 違反になる。

- **提案:** 2 trace 構成と test 内の局所的な exact edge/count assertions は維持する。README の対象行だけ所見1の所有境界へ戻す。

## 所見 6 — `r9_dense_cycle4` は命名規約・番号とも衝突しない

- **所見:** 問題なし。代案は不要。

- **根拠 (file:line):** 現行の赤 fixture は `r1_write_skew` から `r8_silo_broken_norw` まで連番で、すべて `r<number>_<lower_snake_case>` 形式（[fixtures/README.md:22](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2176-dense-cycle4-fixture/orchestrator/tests/fixtures/README.md:22)）。repo 全体の directory・本文検索でも既存の `r9_dense_cycle4`、`r9_`、`dense_cycle4` は0件だった。

- **失敗する具体例:** 既存 `r9_*` があれば番号再利用になり、README順序・fixture path・test名が衝突するが、その実在例はない。

- **提案:** `r9_dense_cycle4` と `test_dense_cycle4_clean_g2` をそのまま採用する。

## 総括

1. 最重要の must-fix は README の所有衝突。段2案は T-2177/D1466 の r5「グラフ検出」と r9「clean certified 遷移」の区別を落としている。
2. 在庫・pin の必須更新は `_V2_FIXTURE_FILES` の2行と README 表だけ。既存 checker、role/group、byte hash、duration ledger、schema/dataclass、output 履歴は更新不要。
3. verifier が誤って `certified=True` を発行すれば downstream 全層は通すが、これは本 wave の scope 外。T-2176 は verifier 境界の mutation KILLED に限定するのが妥当。

pytest その他は実走しておらず、以上は静的検査結果である。