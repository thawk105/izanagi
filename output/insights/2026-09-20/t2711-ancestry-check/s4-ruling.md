# [T-2711] 段 4 裁定 — 所見の real/refuted と plan v2、変異の事前登録

- 日時: 2026-09-20 07:28 JST (段 3 consult 1 本、codex gpt-6-astra / medium / read-only、`check_codex_output` rc=0、逐語は `verbatim/s3-consult.md`)。
- 裁定 inbox の再走査: `docs/handoff/` は README 以外 `2026-08-28-t1998-balanced-stock-inline-precheck.md` のみ (本件と無関係)。wave 開始後の main 更新は無し (段 9 で再確認)。

## 1. 所見の裁定

| # | 所見 | 裁定 | 採否 | 反映 |
|---|---|---|---|---|
| A1 must-fix | `test_t080_freeze_migration.py::test_ancestry_missing_nonancestor_ancestor_noncommit_and_git_error` (1212〜1235 行、1227 行) が production `_classify_ancestry` の missing 分岐を直接 assert 済み。M:890 の変異は全スイートでは既に KILLED | **real** (親が 1212〜1235 行を現物で確認) | 採用 | 変異 matrix の走行集合を「対象 e2e node + この unit test node」に固定し、旧版で unit test が kill・新版で e2e が加わる差分を事前登録する (§3)。研究前進の文言を「e2e の独立検算を末尾 2 件まで拡張」に改める |
| A2 must-fix | 記録 commit `2066ce6b…` / `2e20d441…` は現行 repo の object store に無い (`cat-file -t` rc=128)。実 repo test も missing 分岐を通る | **real** (親が自 worktree で rc=128 を実測。`docs/freeze-permanent-design-s2.md` 145〜156 行の表が全要素 `anchor_status=="missing"`、`disposition=="legacy-history-only"` と記録済み = 既知の設計事実) | 採用 | brief 実測 2 の「実 repo test は object 存在分岐」を撤回。実 repo test は git 導出で missing を期待し、変異 M1/M2 を旧版でも kill する → 変異走行集合に実 repo test を入れない (差分が消える)。insight に既知事実として記す。新 T・新 gate は起こさない (scope 外、既知) |
| A3 should | literal は支持。ただし「git 導出より常に強い」は過大。fixture の object 不在という前提を固定するために literal を選ぶ、と記す | real | 採用 | (P1) を条件付き支持で確定 (§2)。insight の文言を是正 |
| A4 should | report の文法検査 (R:180〜228) と report 本体の再導出比較 (R:259〜322、production 再利用) を分け、変異ごとに既存検出/新 assert の位置付けを表にする。`test_s8b_oracle_report.py` の missing 値は手作り fixture で production の分岐検査ではない | real | 採用 | §3 の変異表に採用。subject の production 変異を「e2e に独立検出を足す」主変異として追加 (M3) |
| A5 nit | dict 完全一致は妥当。未知 field 検出は R:191〜192 が既に行うので新規能力と書かない | real | 採用 | plan v2 は dict 完全一致。insight で「未知 field 検出」を成果に数えない |
| B1 should | 実測 1 の内訳は 13+2+2 (10+5 は誤り)。実測 2 の実 repo 側は末尾 2 件だけ `_independent_ancestry_item`。証拠区分 (静的/親 probe/今回の読取/未実行予測) を明記 | real | 採用 | brief は 07:2x に 13+2 へ訂正済み (job dir 写しも)。insight README に証拠区分の欄を置く |
| B2 nit | 新 assert は 2055 行直後、既存 3 検査は残す。17 件完全一致への書換えは不要 | real | 採用 | plan v2 |
| B3 nit | 本文 AST 検査はあるが call・decorator・集合・相対順序が不変。`acceptance_duration_ledger.json:17854` の key も不変 | real | 採用 | insight に記録 |
| B4 nit | assert・短い insight・fragment・変異 matrix で十分。helper の追加・docstring 修正は不要。「できないなら閉じる」に該当する障害なし | real | 採用 | **実装する** (4→5→6→7→8→9) |

棄却した所見: なし。scope 外 real 所見: A2 (記録 anchor の不在は既知の設計事実で、本 wave は記録のみ)。

## 2. (P1) の確定

**literal 2 dict、`items[15:]` と完全一致、2055 行直後。** 期待値は production の返値・M の定数から導かず、SHA 2 本・`"missing-commit"`・`None` を literal で書く。理由は「hermetic fixture (`git init` から構築、alternates/replace/shallow は M 入口で拒否、`GIT_*` は剥離) では記録 commit が object store に無い、という fixture の前提も同時に固定する」ため。git 導出 (`_independent_ancestry_item`) は本 2 変異に対して literal と同等の検出力を持つが、store に記録 commit が入ったとき期待値を追随させる性質があり、本 wave は追随でなく前提固定を選ぶ。併用は冗長なので入れない。

## 3. plan v2 (変更面 1 file 1 関数)

`orchestrator/tests/test_s8b_oracle_driver.py` の `test_t080_stub_free_draft_finalize_commit_and_public_gate_e2e_b5`、2052〜2055 行の `items[:15]` 比較の直後に次を追加する (consult 推奨の逐語):

```python
    assert items[15:] == [
        {
            "artifact": "known_axes",
            "kind": "ancestry",
            "subject": "/frozen_at_head",
            "recorded": "2066ce6b47c6a5d43ca2c8ab3cc7728d32336be1",
            "observed": None,
            "status": "missing-commit",
        },
        {
            "artifact": "holdout",
            "kind": "ancestry",
            "subject": "/frozen_at_head",
            "recorded": "2e20d441aaf7ae267e941ecda09e4b53050943cf",
            "observed": None,
            "status": "missing-commit",
        },
    ]
```

短い comment 1〜2 行 (hermetic fixture では記録 commit が不在なので `missing-commit`/None が独立期待値、report との一致 (2077〜2081 行) は同一 source なので独立検算にならない) を添えてよい。他の変更は禁止 (production・report・fixture builder・helper・他 test 関数・parametrize・nodeid 集合・既存 assert)。

## 4. 変異の事前登録 (DW-M01 / DW-M08、テスト強化だけの wave = 新旧両走)

走行集合 S (両版共通、`--force-dispatch`、計算ノード):

- e2e = `orchestrator/tests/test_s8b_oracle_driver.py::test_t080_stub_free_draft_finalize_commit_and_public_gate_e2e_b5`
- unit = `orchestrator/tests/test_t080_freeze_migration.py::test_ancestry_missing_nonancestor_ancestor_noncommit_and_git_error`

実 repo test (`test_real_freeze_gate_lists_floor_and_budget_null`) は A2 により旧版でも M1/M2 を kill するので S に入れない (差分が消える)。静的予測として insight に書く。

| id | 位置 (M = `orchestrator/campaign/t080_freeze_migration.py`) | old → new | 旧版 (b7f970dfa) 期待 | 新版 (実装 commit) 期待 | 新 assert に帰属する差分 |
|---|---|---|---|---|---|
| M1 | 890 行 `return AncestryResult("missing-commit", recorded, None)` | → `return AncestryResult("not-ancestor", recorded, validation_head)` | KILLED、node = {unit} | KILLED、node = {unit, e2e} | e2e が加わる |
| M2 | 同上 | → `return AncestryResult("ancestor", recorded, validation_head)` | KILLED、node = {unit} | KILLED、node = {unit, e2e} | e2e が加わる |
| M3 | 2314 行 `"artifact": artifact, "kind": "ancestry", "subject": "/frozen_at_head",` | → `"artifact": artifact, "kind": "ancestry", "subject": "/frozen_at_head/",` | SURVIVED、node = {} | KILLED、node = {e2e} | e2e だけが検出 |

単一理由性: M1/M2 は e2e の新 assert (status/observed の不一致) で赤、unit は 1227 行で赤。report の文法検査 (R:215〜222) は `not-ancestor`/`ancestor` + hex observed を通し、report 本体の再導出は production を再利用するので一致する → e2e の赤理由は新 assert だけ。M3 は R:197〜198 (非空 str) を通り、再導出も追随する → e2e の赤理由は新 assert だけ。unit は `_make_observation` を呼ばない → SURVIVED。置換対象は各 1 箇所 (harness が一意性を assert)。hang risk なし。baseline は両版とも 2 node 緑を要求。期待 node は完全集合で登録し、初回は probe 走で観測 node を集めてから final で本走する (DW-M07)。

所要見積: e2e 単体 ≈ 222 秒 + collection/prewarm ≈ 60 秒 + queue。1 走 ≈ 6〜8 分、(baseline + 3) × 2 版 = 8 走。旧版と新版は別 clone (D1009、main = 対象 commit) で並列に投入する。

## 5. 焦点走・受入

- 焦点走 (DW-O18/O26、計算ノード): 変更 test file 単独走 `orchestrator/tests/test_s8b_oracle_driver.py` に加え、同 file を pin する meta test `orchestrator/tests/test_real_repo_serialization.py`、`orchestrator/tests/test_growth_test_holds_contract.py`、`orchestrator/tests/test_hold_inventory.py` を同一走で走らせる。
- 受入全走: 段 6 後に `tools/dev_wave_wait.py acceptance` (門番 loop 経由) で 1 回。

## 6. 段構成の確定

段 5 Codex author 1 本 (所有 = test file 1 本)。段 6 敵対レビュー 2 本 (A: 正しさ境界・帰属、B: 過剰・削除、DW-S06-A)。段 7 記録 (insight README、worklog fragment 1、decisions fragment なし — 設計判断は既存 D の範囲、interface 変更なし)。段 8、段 9 land。
