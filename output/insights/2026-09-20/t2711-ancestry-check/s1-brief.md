# [T-2711] 段 1 brief — t080 hermetic e2e の独立検算を 17 observation 全件へ

- 日時: 2026-09-20 07:15 JST。起点 main `b7f970dfa` (fresh worktree、clean、submodule 再帰初期化済み、開始 gate rc=0)。
- 起点資料: 台帳 entry 1554 の T-2711 本文、`output/insights/2026-09-16/t2559-acceptance-floor-t080/` (README §3 案 B・§6 項 4、stage4-ruling §2-2)。

## 研究前進 (1 行)

土台。certified 選択の proof chain を守る T-080 freeze gate (`verify_receipt` → s8b oracle gate) の hermetic e2e が、observation 17 件のうち ancestry 2 件の退行を検出できない穴を塞ぐ。止めている研究は無い (P2、ユーザー指示の wave)。最小差分 = 既存 test 関数 1 本に assert 1 個 (2 item)。

## scope

- **入れる:** `orchestrator/tests/test_s8b_oracle_driver.py` の `test_t080_stub_free_draft_finalize_commit_and_public_gate_e2e_b5` 本文に、`items[15:]` (known_axes / holdout の ancestry observation) を独立期待値と比較する assert を足す。
- **入れない:** 案 B (fixture 高速化・alternates) は不採用のまま。新 gate・台帳・一般化・helper の新設・他 test への横展開・M (`t080_freeze_migration.py`) の変更・report (`s8b_oracle_report.py`) の変更は scope 外。docs は本 insight と worklog fragment だけ。

## 確定済みユーザー裁定

- できるなら Codex author (D95) が test の検算を 2 件分足す (実装面)。できないなら理由を本 insight に残して閉じる。
- 案 B 不採用のまま。規律 2 を緩めない (検出力を増やす方向のみ)。

## 段 1 前の実測 (模擬/実の別)

1. **実 (現物コード):** M `_make_observation` (2294〜2329 行) の items = source-repin 13 + generator-metadata 2 + ancestry 2 (report `s8b_oracle_report.py` 184〜189 行の expected と一致)。ancestry item は `{"artifact", "kind": "ancestry", "subject": "/frozen_at_head", "recorded": <定数 SHA>, "observed": validation_head or None, "status": _classify_ancestry の 5 値}`。
2. **実 (現物コード):** T の hermetic e2e は 2033 行 `len(items) == 17`、2052〜2055 行 `items[:15]` を fixture basis の Git blob から独立導出した期待値と比較。2077〜2081 行の report との一致は同一 source なので独立でない。実 repo test (3758 行〜) は 17 件全部を `_independent_ancestry_item` (412〜439 行) で比較済み → 穴は hermetic 側だけ。
3. **実 (現物コード):** report `_campaign_t080_observation` (`s8b_oracle_report.py` 214〜228 行) は status ∈ {missing-commit, not-ancestor, ancestor}、`missing-commit` ⇔ observed=None、recorded = M 定数、順序を検査するが、**hermetic fixture で `missing-commit` であるべきこと**は検査しない。→ 穴の正確な形: `_classify_ancestry` の object 不在分岐が `not-ancestor`/`ancestor` + hex observed を返す退行は、report も e2e も通す。
4. **実 (probe、`/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2711-ancestry-check/probe/premise_classify_ancestry.py`):** `git init` 直後 + 1 commit の空 repo で production `_classify_ancestry` を直接呼ぶと、両 artifact とも `status='missing-commit', observed=None, refusal_reason=None`。
5. **実 (現物コード):** fixture は `git init -q` (T 1426 行) から `git add -A` で作る。M `_capture_head` (636〜654 行) は `objects/info/alternates` / grafts / replace refs / shallow を `receipt.git_error` で拒否し、M `_git_env` (559 行) と T `_sanitized_git_env` (369 行) は `GIT_*` を剥がす。→ hermetic fixture で記録 commit が見える経路は無く、`missing-commit`/None は構造的に決まる。
6. **新事実 (entry 1554 の機序説明の訂正):** alternates 拒否は 2026-07-22 `a0e090f66` からあり、entry 1554 §2-2 の「alternates 経由で見えると `not-ancestor` へ変わりうる」は M の入口で拒否される。ただし案 B 不採用は prune risk 等の他理由で残り、本 wave は再裁定しない (scope 外)。本 wave の穴 (項 3) は案 B と独立に存在する。
7. **`DW-O09` pin 閉包:** 変更前 sha256 `43e852a1…c032f007` / blob `db1add3c…` は tracked にも `output/` にも 0 件。test 関数名は `test_t080_stub_free_e2e_exact_consumers_and_nodeids_b5` (1325 行、consumer 14 関数 / 20 node) と `test_real_repo_serialization.py` 1213/1230 行が nodeid 集合として pin — 既存関数の本文に assert を足すだけなら不変。conftest / growth_test_holds / hold_inventory の pin は別 nodeid。`DW-O10` 非該当 (producer 出力 bytes 不変)。

## 不変条件

- 追加は assert だけ。production・report・fixture builder・helper・他 test 関数・parametrize・nodeid 集合を変えない。
- 期待値は M の定数や production の返値から導かず、literal (SHA 2 本・`missing-commit`・None) で書く (実 repo test 3801〜3808 行が literal SHA を使っているのと同じ形)。
- `len(items) == 17` と `items[:15]` の既存 assert は残す。

## (P1) 親の provisional 裁定・攻撃対象

**(P1) 期待値の形は literal 固定 (`status="missing-commit"`, `observed=None`, `recorded=<literal SHA>`, `subject="/frozen_at_head"`, `kind="ancestry"`, artifact 順 known_axes → holdout) とし、`_independent_ancestry_item(root, …)` (test 側 git 導出) は使わない。**
理由: hermetic fixture では記録 commit の不在が構造的に決まる (実測 4・5) ので literal が「独立期待値」であり、git 導出は object store の変化 (案 B 型) に追随してしまい検出力が literal より弱い。git 導出との併用は本題 2 件を超える追加なので入れない。
攻撃点: (a) literal は fixture の構築方法に暗黙依存する (将来 fixture が実 repo の object を写すと赤) — それは意図した検出。(b) 6 field の tuple 比較 vs dict 完全一致 — dict 完全一致 (`items[15:] == [ {...}, {...} ]`) の方が未知 field の混入も検出するので **dict 完全一致を第一候補**とする。(c) items[:15] の既存比較が 4 field (artifact, kind, subject, observed) だけなのと粒度が揃わない — 本題 2 件だけなので揃えない。

## 成果物の形

- 実装 commit 1 (Codex author trailer、T 1 file)。
- `output/insights/2026-09-20/t2711-ancestry-check/` に s1/s3/s4、mutation 結果、README。worklog fragment 1。
- 変異 matrix: production M の object 不在分岐を `not-ancestor`/`ancestor` + validation_head へ変える 2 変異が **現行 main では SURVIVED、追加後 KILLED** となることを実測で示す (これが「検出力の穴を塞いだ」の証拠)。

## 段構成 (軽量版 + 敵対検証子)

正しさ防壁 (oracle gate の test) に触るので段 3 の敵対相談 1 本 (read-only codex、2 レンズ) と段 6 の敵対レビュー 1 本を残す。段 2 は親が本 brief の実アンカー表で代替 (変更面 1 file 1 関数)。段 5 Codex author 1 本。受入・変異は計算ノード (Pegasus)。

## 変更面 (実アンカー表)

| file | 箇所 | 変更 |
|---|---|---|
| `orchestrator/tests/test_s8b_oracle_driver.py` | `test_t080_stub_free_draft_finalize_commit_and_public_gate_e2e_b5` の 2052〜2055 行 (`items[:15]` 比較) の直後 | `items[15:]` を literal 期待値 2 dict と完全一致で比較する assert を追加 |
