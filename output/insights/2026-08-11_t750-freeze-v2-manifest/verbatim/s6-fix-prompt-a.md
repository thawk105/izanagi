あなたは izanagi の dev-wave 段 6 の fix 実装子である (単位 A = freeze v2 producer 側)。
`sandbox=workspace-write`、`reasoning=high` で動く。出力は日本語で書く。
**段 5 の実装子契約をすべて継承する** (権限、テスト弱体化禁止、受理集合、期待赤、波及報告)。

## 読むもの (読めなければ即停止し、読めなかった path を報告して終わる)

- **裁定 (正本)**: `/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t750-freeze-v2-manifest/s6-adjudication.md`
- 段 4 裁定: 同 dir の `s4-ruling.md`
- レビュー逐語: 同 dir の `s6b-review-1.md`、`s6b-review-2.md`
- 段 5 の自分の実装報告: 同 dir の `s5-impl-a.md`

repo root = `/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t750-fix-a`
(base = 統合 commit `66ec0e0e`)。

## 所有 (これ以外のファイルを 1 byte も変更しない)

- `orchestrator/campaign/s8b_holdout_freeze.py`
- `orchestrator/tests/test_s8b_holdout_freeze.py`
- `orchestrator/tests/s8b_v2_freeze_fixture.py`

`s8b_oracle_manifest.py` / `s8b_oracle_spec.py` とその test は**別 fix 子が同時に編集している**。
読むのは可、書くのは不可。docs 編集と commit をしない。

## 直すもの (裁定 §must-fix の A 側)

- **F-2 (measurement_closure の HEAD 束縛)**: closure の各 path について
  `_blob_at_head()` の bytes と worktree bytes の**完全一致を要求**し、不一致 (dirty) なら
  candidate を拒否する。現行の「worktree hash をそのまま採る」正例テストは**拒否期待へ反転**する。
  これは受理集合の**縮小のみ**である。
- **F-3 (eager import)**: `env_contract` 等の v2 専用依存は **v2 関数内の遅延 import** へ移す。
  `env_contract` は import 時 validation と process-wide fork callback を持つため、
  v1 API (`search` / `generate` / `verify` / `verify_cli_with_t080_receipt`) の import 可否が
  v2 依存に従属してはならない。**v1 API が v2 依存の import 失敗下でも import・実行できる**ことの
  regression test を足す (subprocess か import 差し替えで、production を汚さずに測る)。
- **F-4 (canonical bytes の自己参照)**: writer 出力の期待値を production `_canonical_bytes()` で
  再計算しない。**独立の raw bytes literal と独立 SHA-256 literal** を置く
  (非 ASCII・key 順・末尾 LF を含む形で)。
- **F-5 (`-0.0`)**: 負符号ゼロの budget を拒否する。`total_bench_s` と
  `per_holdout_bench_s` の双方に negative test を足す。
- **F-6 (変異の単一理由性)**: 次の 2 点をコード側で解消する。
  - **MU-2**: 固定 path 検査が先に発火するため canonical namespace 拒否の分岐が**到達不能**に
    なっている。**死んだ分岐を残さない**形へ整理する (実効 gate 1 本にする、または
    到達可能な順序へ直す)。どちらにしても canonical namespace への書き込みは拒否のままにする。
  - **MU-5**: `BUDGET_APPROVAL_SHA256 is None` の拒否が**二箇所**にある。
    **authority gate を一箇所へ集約**し、片方だけの変異で受理集合が変わることを測れるようにする。
    集約後も「`None` ならあらゆる入力で拒否」は不変。
  - 加えて **MU-3** の期待に合わせ、parent の `O_NOFOLLOW` 違反と leaf の既存/上書きが
    **別々の negative test で落ちる**ことを確認する (必要ならテストを分割する)。
- **F-7 (出力先 parent が実 repo に無い)**: writer が**固定 candidate root を安全に作成**する。
  固定 path 限定・symlink 拒否・`O_EXCL` leaf 生成は維持する。
  「fixture だけが親 directory を作る」状態を解消し、実 repo でも機構が発火しうる形にする。
  **ただし実 repo に実ファイルを作らない** (テストは tmp root)。

## 絶対に守る制約

- **既存テストの期待値を変更しない。** 反転・緩和・skip・削除を禁じる。
  例外は本 prompt が明示した F-2 の正例反転だけであり、その 1 件も
  「受理していたものを拒否へ」の方向に限る。
- **production を fail-open にして辻褄を合わせない。** テストが赤なら実装側が誤りである。
  期待値の方が誤りだと判断したら、実装を変えずに報告して止める。
- v1 の `build_document` / `generate` / `verify_document` / `verify` /
  `verify_cli_with_t080_receipt` / `TOP_LEVEL_KEYS` / `GENERATION_SCHEMA_FIELDS` の
  **本体を変更しない**。
- `output/` 配下へ 1 byte も書かない。実走・queue 投入をしない。docs 編集・commit をしない。
- 裁定 §scope 外 (budget authorization の proof chain 追加、manifest schema への spec 伝播) を
  実装しない。

## 検査と報告

- 所見ごとに **closed / partial / regressed** の対応表を必ず返す (F-2〜F-7 の各行)。
- 緑を主張するなら走らせた nodeid と範囲を併記する。実走できなければ「実装済み・未実走」と書く。
- 所有外の caller・共有 fixture・consumer test への波及可能性を静的に列挙する。
- 赤の内訳を明記する。

最後に `## 総括` 節を置き、5 行以内でまとめる。
