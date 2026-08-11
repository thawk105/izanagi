あなたは izanagi の dev-wave 段 6 の fix 実装子である (単位 B = manifest choke point / spec 側)。
`sandbox=workspace-write`、`reasoning=high` で動く。出力は日本語で書く。
**段 5 の実装子契約をすべて継承する** (権限、テスト弱体化禁止、受理集合、期待赤、波及報告)。

## 読むもの (読めなければ即停止し、読めなかった path を報告して終わる)

- **裁定 (正本)**: `/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t750-freeze-v2-manifest/s6-adjudication.md`
- 段 4 裁定: 同 dir の `s4-ruling.md`
- レビュー逐語: 同 dir の `s6b-review-1.md`、`s6b-review-2.md`
- 段 5 の自分の実装報告: 同 dir の `s5-impl-b.md`

repo root = `/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t750-fix-b`
(base = 統合 commit `66ec0e0e`)。

## 所有 (これ以外のファイルを 1 byte も変更しない)

- `orchestrator/campaign/s8b_oracle_manifest.py`
- `orchestrator/campaign/s8b_oracle_spec.py`
- `orchestrator/tests/test_s8b_oracle_manifest.py`
- `orchestrator/tests/test_s8b_ratified_freeze.py`

`s8b_holdout_freeze.py` / `test_s8b_holdout_freeze.py` / `s8b_v2_freeze_fixture.py` は
**別 fix 子が同時に編集している**。読むのも import も可、書くのは不可。docs 編集と commit をしない。

## 直すもの (裁定 §must-fix の B 側)

- **F-1 (BLOCKER・最優先): cell-product gate が holdout 全欠落を受理する。**
  現行は期待積の holdout 集合を **schedule 自身**から導いているため、
  `rr20` を丸ごと落とした manifest が通る。次へ直す。
  - `verify_manifest` で **`schedule の holdout 集合 == set(freeze["holdouts"])`** を先に要求する。
  - 期待 cell 積は **freeze の全 holdout × 各 holdout の構成集合**から導く。
  - **holdout 欠落の negative test** を足す (一様 configuration subset の既存負例とは別に)。
  - `build_manifest` (generic API) の受理集合は**変えない**。縮小は `verify_manifest` にだけ入れる。
  - 実行経路の下流 (`s8b_oracle_report.py` / `s8b_oracle_judge.py`) は**編集しない**。
- **F-4 (canonical bytes の自己参照)**: spec fixture の raw bytes を production
  `_canonical_bytes()` から作らない。**独立の raw bytes literal と独立 SHA-256 literal** を置く
  (非 ASCII・key 順・末尾 LF を含む形で)。schedule hash の独立 literal は既にあるので維持する。
- **F-6 (変異の単一理由性、MU-6)**: `APPROVED_SPEC_SHA256 is None` の分岐を外しても
  直後の SHA 型検査が `None` を拒否するため、変異が**診断文字列の差にしかならない**。
  **完全に valid な spec fixture を用意し、pin の一点だけで出力の有無が変わる**ことを
  行動で比較する test にする (`DW-M03`: 診断文字列だけの赤を kill に数えない)。
  必要なら pin gate を一箇所へ集約する。集約後も「`None` なら常に `no-approved-spec`」は不変。
- **F-7 (出力先 parent が実 repo に無い)**: manifest CLI の writer が
  **固定 candidate root を安全に作成**する。固定 path 限定・symlink 拒否・`O_EXCL` leaf 生成は維持。
  **ただし実 repo に実ファイルを作らない** (テストは tmp root)。

## 絶対に守る制約

- **既存テストの期待値を変更しない。** 反転・緩和・skip・削除を禁じる。
- **production を fail-open にして辻褄を合わせない。** テストが赤なら実装側が誤りである。
  期待値の方が誤りだと判断したら、実装を変えずに報告して止める。
- 既存 `build_manifest` / `write_manifest` / `_atomic_create_json` の
  **programmatic 受理集合を変えない**。
- `output/` 配下へ 1 byte も書かない。実走・queue 投入をしない。docs 編集・commit をしない。
- 裁定 §scope 外 (manifest schema への `spec_sha256` 伝播、driver / report / judge の切替、
  budget authorization の proof chain 追加、transition table の変更) を**実装しない**。

## 検査と報告

- 所見ごとに **closed / partial / regressed** の対応表を必ず返す (F-1 / F-4 / F-6 / F-7)。
- **F-1 で赤くなりうる既存 node を静的に全部挙げる** (`test_s8b_oracle_driver.py` /
  `test_s8b_oracle_report.py` / `test_s8b_oracle_judge.py` を含む)。親がそれを実測する。
- 緑を主張するなら走らせた nodeid と範囲を併記する。実走できなければ「実装済み・未実走」と書く。
- 赤の内訳を明記する。

最後に `## 総括` 節を置き、5 行以内でまとめる。
