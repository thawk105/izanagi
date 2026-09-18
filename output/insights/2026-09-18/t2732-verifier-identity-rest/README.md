---
authority: none
default_effect: no-state-change
---

# T126 qualification の code identity へ verifier の `__init__.py` / `report.py` / `commit_receipt.py` を含めた (2026-09-18)

wave `dev-wave-t2732-verifier-identity-rest` (branch `worktree-dev-wave-t2732-verifier-identity-rest`、base = local main `d2ebef7a4` = origin/main、着手 2026-09-18 06:17 JST)。
依頼は「[T-2732] (D2120 項 6、ユーザー裁定 2026-09-17) `REQUIRED_CODE_IDENTITY_PATHS` (`orchestrator/qualification/identity.py` / `contract.py` / `t126_driver.py`) に
verifier の `orchestrator/verifier/__init__.py` / `report.py` / `commit_receipt.py` を加える (40 → 43、純増、受理形は D2091 と同条件)。Codex author (D95)、
既存 pin テストの更新と焦点走まで。互換層・旧成果物の再受理は足さない。着手直前の local main から fresh worktree を作る。規律 2 を緩めない。本題の 3 path 追加だけ。
仮想リスク向けの gate・検査・台帳・一般化の追加は scope 外」。先例 = D2091 / T-1209 (`output/insights/2026-09-17/t1209-verifier-identity/README.md`) の §6 裁定パッケージを
D2120 項 6 が択 (a) で裁定したものの実装。

## 結論 (最初に読む)

1. **`REQUIRED_CODE_IDENTITY_PATHS` (orchestrator/qualification/contract.py) に `orchestrator/verifier/__init__.py` / `commit_receipt.py` / `report.py` を加えた
   (40 → 43 path、script 集合は 3 のまま、和集合 43 → 46)。** 独立の包含 test `test_required_code_identity_includes_verifier_init_report_commit_receipt`
   (3 file を個別に assert、既存の core/dsg/model/parse test は据え置き) を添えた。実装 commit `eb0f38969` (Codex `role=author`、2 file +9 行、plan v2 の逐語どおり)。
2. **受理形は 40-key 形から 43-key 形へ置換される (1 形のまま)。** 旧 40-key 形の series-identity は現行 code の verify で `contract.py:536-540` の required set 検査
   (`series identity code_identity required set mismatch`、ProtocolError) に当たり、driver は `:1644-1646` で invalid → CLI `:1679` rc=2、collector は `:1880-1881` で invalid、
   `verify_recorded_series_identity()` 直呼びでも `identity.py:124` で同じ例外 (blob 照合 `:140-145` には到達しない)。bytes と当時の判定は保持されるが現行契約への適合は失う。
   **この不受理を過去の測定の無効化に使わない** (規律 7)。互換層・二重受理は作らない (裁定条件)。
3. **verifier の個別束縛は tracked 9 file 中 4 → 7。** 集合外に残る `__main__.py` / `cli.py` は独立 CLI 入口 (`__main__.py:5` → `cli.py`、`orchestrator/verify.py:16`) で、
   確認した T126 経路 (`t126_qualification.sh:835` → driver `run` → `t126_driver.py:623` `pipeline.evaluate()` → `pipeline.py:39/506/614` の package API、
   collector → `qualification/artifacts.py:24/855` の receipt API) からは到達されない。D2091 却下欄が本 wave の 3 file に付けた「実行依存が残る」所見は転用できず、
   裁定パッケージは立てない (依頼の「本題の 3 path 追加だけ」)。
4. 変異 matrix (§5): 期待 node は新 test V のみ。**初回走は N2 完了後に親の規律違反 (走行中に insight file を worktree へ置き `git add -N`) で harness が中止 (F106 再発、erratum)。**
   `--resume` で残りを走らせた。結果は §5 の表。
5. land 用の最終受入全走は、本 README と spool fragment の記録 commit を含む tip で投げる (結果は land の受領証 `acceptance-receipt-final-*.json` (job dir) が持つ。本 README には書かない)。

## 1. 一次資料

| 区分 | 所在 |
|---|---|
| job dir (repo 外、運転 script・log・spec・attempt json・待ち手 receipt・handoff) | `/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2732-verifier-identity-rest/` |
| 段 1 brief (訂正前。訂正は §3) | `verbatim/s1-brief.md` |
| 既裁定の逐語射影 (D2120 項 6 / D2091、見出し単位) と親の実測 | `verbatim/ruling-verbatim.md`、`verbatim/verbatim-d2120-item6.md`、`verbatim/verbatim-d2091.md` |
| 段 2 plan / 段 3 レンズ A・B / 段 5 author / 段 6 レビュー A・B | `verbatim/s2-plan.md`、`verbatim/s3-lensA.md`、`verbatim/s3-lensB.md`、`verbatim/s5-author.md`、`verbatim/s6-reviewA.md`、`verbatim/s6-reviewB.md` |
| 段 4 裁定 (plan v2、変異事前登録) | `verbatim/s4-adjudication.md` |
| 実装子の所有 path 限定 patch | `verbatim/s5-implementation.diff` |
| 変異 spec (実装前 06:47 JST に登録、sha256 `d292686f1e4ec16289f67e1ede4c63d4d16c0f4f08a8cf174e24bbd41d416cf8`) と台帳 | `mutation-spec-main.json`、`mutation-main-ledger.json` (初回中止時点の写し = `mutation-main-before-resume.json`) |
| 受入 receipt (repo 外) | job dir `acceptance-receipt-final-*.json` |

逐語の可逆最小正規化 (可視文字不変、原文は job dir に残る): `s3-lensA.md` 行末空白 1 行除去 (原文 sha256 `0839742c05c6bf6092d0db4ee293554878d80be3e6eb35c67e243c6d000a2fba` 10131 B →
`55ab57dc65ff3245d2f3ae8689d2197c1a5ea3df0c402c4890df226674cb590b` 10129 B)、`s5-author.md` 行末空白 2 行除去 (`c30a4df5cfe0350cba70a8d6723315d56b12805c317200fa7dfc190388f588e8` 5203 B →
`ab3c6c4a27a71b16d8fcee29ee50e73c5dd452973c474b93dab19c7f3c25b1f1` 5201 B)、`verbatim-d2091.md` 末尾空行 1 行除去 (`d3d296d3f791b3d4d988d64c732a4d882df3247e2ade335e13c94078bf9f46dd` 4168 B →
`dd0fd72c43e60865035b69bfb51d953a2f02e4413b0c452feb6525b6431497a6` 4167 B)、`verbatim-d2120-item6.md` 末尾空行 1 行除去 (`e1db7e6c4b1aa880b3392b8f46986358ce2a5e8579882264188a2ab6d9239ba6` 1000 B →
`bb0e546ff524277f0dfe25ba55377e9efdf211575d7fc2e9a02b07cb8c268864` 999 B)。復元法 = 該当行末へ空白 1 個 / 末尾へ空行 1 行を戻す。`s5-implementation.diff` の空白 context 行 2 本は unified diff の書式なので保持。

## 2. 起動時の実測 (段 1)

- 裁定の正本: `docs/decisions.md` D2120 項 6 (対象 T-2732 = D2091 却下欄)。裁定 inbox (`/work/1/SFC/tanab/dev-wave-jobs/rulings-inbox/`) に追加裁定なし。main は wave 中不動 (d2ebef7a4)。
- 現物: `contract.py:39-80` の frozenset は 40 path、verifier は `:75-78` の core / dsg / model / parse。consumer は `contract.py:533` (`series_identity` の exact set)、`identity.py:140` (和集合 exact)、
  `t126_driver.py:372` (`_identity_files` の disk/HEAD blob 照合)。追加 3 file は tracked regular file (mode 100644、blob `e6f347fe` / `92033ad9` / `5925ce4b`)。
- 依存: `pipeline.py:39` `from ..verifier import` (= `__init__.py`)、`core.py:24-25` (`_domain_digest` / `result_to_dict`) と `:256/264`、`qualification/artifacts.py:24-27/855` (`validate_live_receipt`)。
- 凍結 pin の逆引き (DW-O09): contract.py の変更前 sha256 `e36d7c67…` / blob `47fe1b3a…`、test file の sha256 `bf50ef67…` / blob `501337e8…` の repo 内 hit (output/ 含む) 0 件。
  path pin は T126 自己包含 (`contract.py:43`)、現行 loader 閉包 (`campaign_lock.py:107`、HEAD blob と disk の live 比較)、歴史 exact62 (`:204`)、consumer test の path 列挙
  (test_artifact_admission / test_campaign_lock_codec / test_official_perf_closure / test_t671_source_binding) のみ。凍結 bytes pin 無し → DW-O10 非適用。
- 編集面の重複検査: 他 branch の未 land commit 0 件 (`git log --branches --not main -- <2 file>`)。164 worktree の作業ツリー走査 (job dir `overlap_scan.py`、unreadable 0) の
  modified 13 件はすべて `.codex/worktrees/` の着地済み Codex 子木 (`t1209-impl` の contract.py は現 main と同一 sha256、`t548-*` は contract.py に触れず)、稼働 process 0 (`ps -eo args`、06:2x JST 時点)。
- DW-O13: 受理形は 1 形のまま置換で新設に当たらない (D2091 決定 2 と同じ)。field 実在 (`code_identity`) と到達可能性 (3 path tracked、driver が hash) は上で実測。
- 起動 gate `check_wave_startup.py --mode fresh --external-handoff` rc=0。submodule 初期化は 1 回目 rc=1 (`update-no-fetch` の io 失敗、木は出現)、DW-O08 に従い同引数で再実行 rc=0、3 木を ls で確認。

## 3. 段 2 plan と段 3 敵対相談の要点 (実装 must-fix 0、brief 訂正 4、裁定パッケージ 0)

段 2 plan (`gpt-6-astra` / `medium`): 変更 = contract.py `:78` 直後に 3 行 + 独立 test 1 本 (親 (P1) 推奨)。(P4) を訂正 — submit script は `:124-134` の 5 path tracked 検査と
`:149-164` の 7 path disk/blob 照合を持つが required code 集合の複製ではなく件数依存なし、変更不要。所見 = verifier dir は 9 file、追加後も `__main__.py` / `cli.py` が集合外に残る。

| ID | 所見 | 裁定 |
|---|---|---|
| A1 | 3 path + 独立 test 1 本は裁定を満たす。包含 test は集合からの脱落検出であり verifier の判定能力ではない | real、採用 |
| A2 | (P3) 成立。旧 40-key 形の拒否経路 (結論 2) | real、記録 |
| A3 | 「意味論不変」は identity まで含められない。`t126_driver.py:376-384` の fail-closed が 3 file へ広がる (正しい向き) | real、I2 を限定 |
| A4 | 先例以降 (c09211d17..d2ebef7a4、397 commit、JSON 206 blob) の committed JSON に `code_identity` key 0 件。不在主張は調査範囲に限定 | real、記述限定 |
| A5 / B4 | brief「verifier package 全 7 file」は誤り (9 file 中 7) | real、brief 訂正 |
| A6 / B5 | brief (P4)「script は path 名を列挙しない」は誤り (限定列挙あり、複製ではない) | real、brief 訂正、script 変更なし |
| A7 / B6 | Codex 子木 dirt・worktree 走査は時点付き実測、一般化しない | real、記述限定 |
| A8 / B2 | 「焦点走 4 file に drift gate 無し」は過大。実 repo live loader 比較 (`contract_loader_binding.py:526-529`) を持つ経路だけが未 commit で赤。焦点走 4 file にその経路は無い (静的) | real、本 wave の checkout で実走して確認 (§4) |
| A9 | `__main__.py` / `cli.py` は T126 経路から到達されない CLI 入口 (結論 3) | real、裁定パッケージ不要 |
| B1 | 「6 file・24 行」は production / test の直接出現に限定。docs archive 5 / decisions 3 行、output/ 45 file は歴史記録。間接 consumer collector.py:358/473/1168/1487/1515、artifacts.py:1291 は契約関数経由 | real、記録 |
| B3 | `_attempt` fixture (`:980-982` mkdir、`:1025` generic 書込、`:1050-1051` commit、`:1085-1088` blob hash) は追加対応不要、basename 重複は衝突しない | real、plan 維持 |
| B7 | 変異 N1〜N5 は新 test だけが赤、E1 SURVIVED、`cli.py` は tracked (blob `3c600cb4`) かつ集合外 | real、事前登録どおり |
| B8 | 焦点走・変異は 4 file、受入は縮めない、runner に `--force-dispatch` | real、手順採用 |

refuted 0。段 4 裁定の全文は `verbatim/s4-adjudication.md`。

## 4. 実装と焦点走 (段 5)

- 実装子 worktree `.codex/worktrees/t2732-impl` (branch `impl-dev-wave-t2732-verifier-identity-rest`、base `d2ebef7a4`、locked、submodule init rc=0)。midflight gate rc=0。
  author (job `s5-author-01`、`gpt-6-astra` / `medium`) は逐語どおり実装し、`python3 -B` で 43 / 46、DIRECT_CALL_PASS、DID_RAISE (test module 側の集合から `report.py` を外した差し替えで AssertionError、file 変更なし)、
  追加 3 行の `grep -Fxc` 各 1 を報告。所有 path 限定 patch (`git add -A` → `git diff --cached -- <2 file>`) を wave worktree へ `git apply`。
- 焦点走 (`test_t126_pegasus_tools.py` / `test_t126_qualification_contract.py` / `test_t126_qualification_driver.py` / `test_t419_probe_causality.py`、計算ノード dispatch):
  変更前 485 passed / 17.85 秒 (request 4993.nqsv、HEAD d2ebef7a4)、変更後 489 passed / 18.54 秒 (request 4995.nqsv、patch 適用済み・未 commit)。差 +4 = 新 test 1 + parametrized 3 (静的予測どおり)。
  **未 commit の contract.py で緑 = この 4 file に実 repo live loader 比較は無い**ことを本 wave の checkout で実測 (A8 の限定に従い、先例成功を代用していない)。
- 統合 commit `eb0f38969` (`--message-file` 検査 rc=0)。full provenance 監査 11207 件、新規違反なし (rc=0、07:18 JST)。

## 5. 段 6 レビューと変異 matrix

- レビュー A: 所見 0 (commit の patch は `s5-implementation.diff` と byte 一致、検証ロジック不変、新 test は literal assert で単一理由・非恒真、拒否経路は結論 2、scope 外変更なし、
  author 報告と静的整合、commit message の事実記述 (40 → 43、4 → 7、CLI 2 file 非到達) は現物と一致)。
- レビュー B: must-fix 0 / should 0 / nit 1 = 焦点走外の consumer test 7 群を記録へ (実装変更不要): `test_t126_qualification_artifacts.py:42`、`test_floor_submit_receipt.py:14`、
  `test_official_perf_closure.py:85/252/379/829`、`test_t671_source_binding.py:97`、`test_campaign_lock_codec.py:77`、`test_artifact_admission.py:341/579`、
  `test_campaign.py:89` → `certified_writer_fixtures.py:12/81/161/190`。いずれも commit 後の受入全走で覆う (`test_selection_contract.py:61` `SANCTIONED_EXCLUSIONS = ()`)。
  spec の全 `old` が HEAD `eb0f38969` にちょうど 1 回 (親も `count` で検算)、V の関数名は HEAD と文字どおり一致、`test_fr3_mutation_node_registry_is_exact_and_complete` (:6234) は E1 の comment で変わらない。
- fix 子なし。

### 変異 matrix

spec `mutation-spec-main.json` (実装前 06:47 JST に登録)、harness `tools/mutation_harness.py --runner-mode dispatch --detached`、runner = `python3 tools/run_tests.py <4 file> -q -rf --force-dispatch`、
測った checkout = wave worktree HEAD `eb0f38969`。V = `orchestrator/tests/test_t126_pegasus_tools.py::test_required_code_identity_includes_verifier_init_report_commit_receipt`。

- **erratum (初回走、07:18〜07:42 JST、`mutation-main-before-resume.json` に保全):** collection (request 5022.nqsv) → baseline PASSED (5024.nqsv、45.8 秒) → E1 SURVIVED (5028.nqsv) →
  N1 KILLED → N2 KILLED の後、N3 の直前に harness が `runner/test bytes に固定 HEAD 外の変更を検出` で中止 (rc=2)。原因 = 親が走行中に insight の逐語 file を worktree の
  `output/insights/2026-09-18/...` へ置き `git add -N` した (intent-to-add が `git diff HEAD` に現れる)。DW-M05「変異中は親の編集を止める」の違反、F106 の同型再発 (failures fragment に再発追記)。
  harness は変異対象 2 file を HEAD へ復元済み (`git diff --quiet HEAD -- <2 file>` rc=0)。復旧 = index を戻し insight file を job dir へ退避 (`git status --untracked-files=all` 0 行) してから
  `--resume` (F453: sidecar `mutation-main-attempt-1.json` を `-attempt-2.json` へ複写、`--wrapper-attempt 2`) で残り 3 変異を走らせた (baseline 省略、07:45 JST 起動)。
  完了済み 3 件 (E1 / N1 / N2) は初回走の観測。

- 本走の結果 (初回走 + resume、台帳 `mutation-main-ledger.json`、07:19〜08:00 JST): summary = registered 6 / completed 6 / matching 6 / KILLED 5 / SURVIVED 1 / MISMATCH 0 / TIMEOUT 0。
  所要は harness の `duration_s` (dispatch 往復・queue 待ち込み)。

  | ID | 変異 (contract.py の tracked 行、anchor は 2 行 context) | code 件数 | 期待 | 観測 node | 判定 | job / 所要 / 走 |
  |---|---|---:|---|---|---|---|
  | E1 | test file: V の def 行直後に comment 1 行 (production bytes 不変) | 43 | SURVIVED、node 空 | 空 | SURVIVED (等価) | 5028.nqsv / 48.3 秒 / 初回 |
  | N1 | `__init__.py` 行を削除 | 42 | KILLED、V | V | KILLED | 5034.nqsv / 109.5 秒 / 初回 |
  | N2 | `report.py` 行を削除 | 42 | KILLED、V | V | KILLED | 5042.nqsv / 1008.1 秒 (queue 待ち大) / 初回 |
  | N3 | `commit_receipt.py` 行を削除 | 42 | KILLED、V | V | KILLED | 5073.nqsv / 499.1 秒 / resume |
  | N4 | `report.py` → tracked 兄弟 `cli.py` へ置換 (件数 43 のまま) | 43 | KILLED、V | V | KILLED | 5099.nqsv / 135.6 秒 / resume |
  | N5 | `commit_receipt.py` → 既存 member `core.py` へ置換 (frozenset 重複) | 42 | KILLED、V | V | KILLED | 5101.nqsv / 135.2 秒 / resume |

  5 変異とも観測 node は V だけ = 既存の集合由来 test (fixture・parameter・等価比較・tracked parametrize) はどれも追随して緑のまま、新 test だけが検出した (新規検出力)。
  N4 で変異下に生まれる `test_every_required_identity_path_is_tracked_in_this_repo[orchestrator/verifier/cli.py]` は赤にならなかった (`cli.py` は tracked)。
  collection (5022.nqsv) と baseline (5024.nqsv、PASSED、45.8 秒) は初回走のもので resume は再走していない。

## 6. 裁定パッケージ

- なし。結論 3 のとおり `__main__.py` / `cli.py` は T126 経路から到達されない CLI 入口であり、本 wave は事実だけを記録した。
