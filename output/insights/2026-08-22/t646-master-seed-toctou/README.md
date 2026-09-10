# [T-646] floor_protocol.json master_seed TOCTOU — holdout freeze producer 残存経路

## 要旨

carry [T-646] (`docs/archive/worklog-phase3-0808-306.md:469-473`、2026-08-08 起票) は
「qsub 投入後に working tree だけ書き換えた `output/s8b-freeze/floor_protocol.json` の
`master_seed` が、job 側の dirty 検査 (`output/` 除外) をすり抜け、driver が別 schedule を
走らせてしまう」という TOCTOU (Time-of-check to time-of-use) の指摘だった。

着手前に現行 driver 構造での再現を実測したところ、**主経路 (`run_campaign`/CLI、
`s8b_ratified_freeze.py`、`s8b_holdout_admission.py`) は commit `cca78d3d`
(2026-08-17、[T-419](3)/[T-1255] 「床値 protocol の権威を固定 commit へ戻し、live consumer を
resolver へ配線する」) で既に working-tree-only mutation を fail-closed 拒否していた。**
T-646 起票の 9 日後に、無関係な別 wave が副次的にこの TOCTOU を閉じており、carry は以後の
worklog fold 7 回 (entry 805〜811) をこの事実に気づかないまま素通りしていた。

段2 codex (read-only plan) の独立調査で、`s8b_holdout_freeze.py:1348-1378`
(`_validate_floor_inputs`、`build_v2_g1_candidate` の producer write-path) **だけ**が
raw working tree 読込みのまま残っていることが判明した。同ファイル内の
`measurement_closure`/`known_axes_freeze`/`generator`/`design_source` は既に
`_blob_at_head` で captured HEAD blob 束縛済みだったが、floor protocol の読込みだけこの
idiom から漏れていた。本 wave はこの1経路だけを最小差分で修正した。

## 経緯 (段別)

1. **段1 brief**: `verbatim/stage1-brief.md`。P1 (主経路は再現しない、暫定) / P2
   (holdout freeze producer 未確認) を分けて提示。
2. **段2 codex plan (read-only)**: `verbatim/stage2-plan.md`。P1 を追試し、P2 を
   `s8b_holdout_freeze.py:1362` の raw working tree 読込みと特定、fix 案を提示。
3. **段3 敵対相談 2 レンズ (read-only)**: `verbatim/stage3-lensA-sol.md` (fix 健全性)、
   `verbatim/stage3-lensB-luna.md` (実効性・網羅性・scope)。lens A は fix 実装案自体の
   3 つの追加硬化余地 (HEAD commit 未検証・mode 未検査・replace object 未衛生化) を real と
   判定したが、scope 外 (下記決定参照)。lens B の指摘 (網羅性・一般化可能性) は親が
   `s8b_ratified_freeze.py`/`s8b_holdout_admission.py` の独立コード読解と、実 repo に対する
   非破壊 `resolve_current_floor_protocol()` 呼出しで追加裏取りした。
4. **段4 裁定**: `stage1-brief-and-stage4-adjudication.md` (裁定本文と根拠の一次資料)。
   P1 refuted (再現しない)・P2 real (採用)・lens A 所見は scope 外 backlog
   ({{D:t646-holdout-freeze-head-binding-scope}} 相当、`docs/decisions.md` 参照)。
5. **段5 実装 (codex author、workspace-write)**: `verbatim/stage5-author.md`。
   `_validate_floor_inputs` に `head` 必須引数を追加し、既存 `_blob_at_head` で captured
   HEAD blob と working tree bytes を byte-exact 比較、不一致は `FreezeError`。
6. **段6 敵対レビュー 2 レンズ (read-only)**: `verbatim/stage6-reviewA.md`、
   `verbatim/stage6-reviewB.md`。いずれも real 所見 0 件。
7. **変異事前登録・実測**: `mutation-spec.json`/`mutation-out.json`。

## 変異 matrix

- `t646.m1-disable-head-binding-check` (負例、check 無効化): KILLED
  (新設回帰テスト `test_v2_candidate_rejects_worktree_only_floor_protocol_master_seed_mutation`
  が唯一検出)。
- `t646.m2-always-reject-positive-control` (正例、常時拒否): KILLED
  (既存 17 test が正当な受理経路の破壊を検出。過剰拒否が無いことの実測裏取り)。
- baseline: PASSED。SURVIVED 0・MISMATCH 0。

## 焦点走

`orchestrator/tests/test_s8b_holdout_freeze.py` (計算ノード): 121 passed, 2 skipped
(既存 2 skip は GROWTH_HOLD 対象、本 wave と無関係)。

## scope 外・次の一手

- [T-647] (bench を走らせない correctness-only の COMMIT を計測契約束縛の対象と数えるか) は
  独立の未裁定論点のため scope 外 (ユーザー指示)。
- lens A が指摘した `_blob_at_head`/`head` 捕捉共有基盤の硬化 (HEAD commit 未検証・mode 未検査・
  replace object 未衛生化) は、`docs/worklog.md` の carry (新規登録分) と
  `docs/decisions.md` の該当決定を参照。
