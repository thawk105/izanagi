# 段 1 brief — [T-1222] 成長比例テストの母集合を REAL_REPO_SERIAL_NODES の外へ広げる

wave: dev-wave-t1222-growth-hold-sweep / branch: worktree-dev-wave-t1222-growth-hold-sweep
base main: 98df871b / submodule external/ccbench: 511c9538 / 作成 2026-08-16 18:35 JST

## scope

1. **母集合の棚卸し**: `REAL_REPO_SERIAL_NODES` (conftest.py:170) にも
   `GROWTH_TEST_HOLDS` (growth_test_holds.py:99 `_HOLD_ROWS`) にも入っていないテスト node のうち、
   実行コストが repository の成長 (commit 数・tracked file 数・docs bytes・output artifact) に
   比例するものを、**探索 primitive を明示した全件走査**で列挙する。
   primitive には glob/rglob/walk・read・Git command に加えて **`shutil.copytree` 系**と
   **実 ROOT を引数に取る production 列挙関数** (`enumerate_repository_files` /
   `search_repository` / `check_docs.py` の subprocess 起動) を含める。
2. **判定と登録**: 比例が実測で裏付いた node を `_HOLD_ROWS` へ追加する。裏付かないものは
   **refuted として理由付きで記録**し、登録しない。
3. **提示**: 正しさゲートを担う保留は D335 に従いユーザー提示用一覧へ書く。

## 確定済みユーザー裁定 (緩めない)

- D335 (authority: user): 成長比例テストは**削除せず恒久保留**。解除は
  `release_condition="explicit-user-command-only"` のみ。可視 skip 印 + 機械可読な理由。
  正しさゲート該当は保留一覧でユーザー提示。
- D451: 保留すると**その防壁を守る既定走行 node がゼロになる**場合は保留しない。
  比例源が別軸で除去できるならそちらを先に行う。保留しなかった事実と理由も一覧へ書く。
- D452: 変異の期待赤 node は既定 skip されず failure として記録され `xdist_group` に属さない node に限る。

## 不変条件

- I1. 既存 56 件の保留を**解除しない・axis を書き換えない**。追加のみ。
- I2. 追加する node は `enforce_held_functions` の guard binding を持てること
  (= その test file を `spec_from_file_location` 等で **standalone 読み込みする正規 consumer が無い**)。
  持てないなら登録しない。2026-08-16 entry 592 の受入差し戻し (`test_s8b_floor_campaign.py`) の再発を防ぐ。
- I3. **成長比例の検出器テストを新設しない。** repo 全体を走査する「母集合が閉じている」検査は
   それ自体が D335 違反になる。棚卸しの結果は台帳 (`_HOLD_ROWS`) と docs へ置く。
- I4. 編集する file の **pin 閉包を先に検索する** (path key・識別子 key・加工後 hash の 3 方向)。
   `tools/codex_reasoning_ab.py:97-101` が `orchestrator/tests/test_check_docs.py` の sha256 を
   持つが、値は歴史 pin であり現行 bytes と一致しない (親実測: 現行 `098f3dfd…` 対 pin `38675b06…`) ため
   本 wave の編集では発火しない。**他の pin が無いことは子が全件検索で示す。**
- I5. 台帳追加は `test_growth_test_holds_contract.py` の
   `_EXPECTED_HOLD_COUNT` / `_EXPECTED_KEY_SHA256` / `_EXPECTED_ROW_CONTRACT_SHA256` と
   独立ミラーの同時更新を要する。片側だけ直さない。

## 親の前提実測 (2026-08-16 18:40〜19:00 JST、本 worktree、並行 wave 7 本が稼働中)

pytest は login node で hook 拒否、bounded local も cgroup attest 不能のため、
node が呼ぶ production 関数を repo 外 probe で直列に測った (probe は job tmp、repo へ入れない)。

- `enumerate_repository_files(ROOT)` = **1.58 秒 / 13,062 file**。
  2026-08-12 の同種実測は 12,084 file だったので **4 日で +978 file**。
- `search_repository(ROOT, files=全列挙)` = **15.93 秒** (positive control hit 82)。
  → `test_s8c_preregistration_invariant.py::test_wave_files_do_not_contaminate_production_holdout_scan`
  の実費は約 **17.5 秒**で、tracked file 数に比例する。
- `tools/check_docs.py` 単発 = **5.33 秒** (rc=0)。
  → `test_check_docs.py::test_real_repo_clean` はこれを subprocess で丸ごと払う。docs bytes に比例。
- copytree 系 fixture の写す部分木: `.claude/agents` 13 file **0.016 秒** /
  `.codex/role-adapters` 13 file **0.009 秒** / `orchestrator/codex_roles` 8 file **0.007 秒** /
  `tools/task_runs` 7 file **0.008 秒**。**いずれも repository 成長ではなく role/tool 追加に比例し、
  実費は 2 桁ミリ秒**である。
- `test_s8b_ratified_verify.py` は実 ROOT を `_REAL_V1` (固定 1 file) しか読まず、
  git 操作も `search_repository` も tmp root か monkeypatch である (grep 全件)。
- silo ladder 2 件 (`test_silo_ladder_rung1_evidence.py::test_silo_ladder_rung1_commit_witness_matches_committed_raw_data`
  / `::test_silo_ladder_rung1_committed_evidence_rebinds_content_not_head`) は
  **列挙 primitive を 1 つも持たず**、固定 path の凍結 artifact を sha256 pin と突き合わせる。
  除外理由は 2026-08-12 worklog 483「t816 が同 node へ分離検査を新設済み。t816 land 後に再評価」であり、
  t816 手順 4 は 2026-08-12 に land 済み → **再評価の条件は満たされている**。

## 親の provisional 裁定 (P) — 攻撃対象

- **(P1) 名指し 5 候補のうち 3 群は refuted。** `test_s8b_ratified_verify.py` 全 node、
  silo ladder 2 件、copytree 系 fixture 2 file は成長比例でない。上の実測が根拠。
  子は「refuted が誤りである経路」を探して反証せよ。
- **(P2) `test_s8c…::test_wave_files_do_not_contaminate_production_holdout_scan` は比例が真だが、
  D451 で保留できない可能性が高い。** 実 repo 全体を `search_repository` で走査する既定 node は
  現状この 1 本だけで、もう 1 本 (`test_s8b_repo_scan_invariant.py::test_real_repository_scan_matches_known_hits_and_has_positive_control`)
  は既に保留済みである。保留すると holdout 漏洩を検出する既定走行がゼロになる。
  子は (a) この結論の可否、(b) 比例源を別軸で下げる contained な道があるか、を判定せよ。
- **(P3) `test_check_docs.py::test_real_repo_clean` は保留可能と見る。** 同じ防壁は
  land 経路 (`tools/dev_wave_land.py:2214` が生成 canonical を check_docs で検証) と
  wave checker (`tools/dev_waves/checker.py`) が独立に持つ。子は「land 経路が実際に
  同じ検出をするか」を file:line で確かめ、しないなら P3 を覆せ。
- **(P4) 未名指しの候補が本体である。** 名指し 5 候補は先行 wave の残件であって母集合ではない。
  子は tests 配下 (約 200 file) を primitive 別に全件走査し、実 ROOT に到達する node を
  file:line 付きで列挙せよ。**head で切った検索を「0 件」の根拠にしない。**

## 成果物の形

- `orchestrator/tests/growth_test_holds.py` の `_HOLD_ROWS` への追加行 (0 件もありうる)。
- `orchestrator/tests/test_growth_test_holds_contract.py` の 3 pin と独立ミラーの更新。
- 新規保留 file への `enforce_held_functions(globals(), __file__, plain_runner=…)` binding。
- 棚卸し結果 (採用・refuted・保留見送りの 3 分類、各件に file:line と実測または構造根拠) を
  `output/insights/2026-08-16_t1222-growth-hold-sweep/` へ。
- worklog / decisions fragment (spool)。

## 成果物影響 (DW-G05)

放置すると受入全走の wall に repository 成長比例の項が残り続ける
(現時点で s8c 1 node = 17.5 秒、check_docs = 5.3 秒)。逆に誤って保留すると、
certified 選択の holdout 漏洩検査 (受理集合そのもの) を守る既定走行が消える。
本 wave が変えるのは**受入全走の走行集合**であり、campaign の数値・proof 参照は変えない。

## 分割方針

段 2 = plan (sol, read-only) が全件走査と file:line 台帳。
段 3 = consult 2 本 (sol / luna) が P1〜P4 を別レンズで攻撃。
段 5 = author 1 本 (workspace-write) が台帳追加 + pin 更新 + guard binding。
段 6 = review 2 本 + 変異 matrix + 受入。
