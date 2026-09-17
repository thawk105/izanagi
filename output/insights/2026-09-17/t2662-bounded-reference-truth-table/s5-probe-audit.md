# 段 5 — probe の親監査と本走の事実 ([T-2662])

## probe の同定 (repo には入れない)

- 起草: Codex `role=author` (段 5 子、`s5-author-report.md` が子の最終報告の逐語)。
- 置き場: `/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2662-bounded-reference-truth-table/probe_truth_table.py`
  (子は worktree の insight dir へ書き、親が実行前に job dir へ `mv` した。repo に残さない)。
- 同定: **314 行・12,810 bytes・SHA-256 `799d91405fd03e696b53667818fa5c23804f16e8614c3c85b7b2c72a10fc700c`**。
- 依存: 標準 library のみ。対象 module は既存テストと同じ `importlib.util.spec_from_file_location` で読む。

## 親の監査 (契約との照合)

- 候補集合は段 4 契約の P0〜P14 × C0〜C14 のうち意味を持つ組を全部持つ。P11 は C0/C1 だけ、
  C11 は P0/P1 だけ、P13/P14 は C12/C13 だけ、C14 は単独。P2 は file (`/offrepo/my dir/a.py`) と
  空白入り祖先 (`/offrepo/my dir`) の 2 起点。P12 は実在 2 件と同じ形の合成 path。
- 各 content について、本番と同じ入力形 (`_reference_patterns(_ExternalMatch(path, root))` の全要素を
  `os.fsencode` した集合) を本番へ渡し、**pattern 集合の各要素につき 1 行**、helper と本番の値を並べる。
- C11 (chunk 跨ぎ) は pattern 開始 index を `READ_CHUNK_SIZE + d` (d = −(len(root)+2) … +(len(root)+2))
  に置く 21 offset × P0/P1。
- `--selftest` は既存テスト `test_bounded_path_reference_single_scan_matches_legacy_boundary_semantics` の
  6 行 (content・pattern) を逐語で写し、不一致なら rc=3。
- 実在 path: `realpath-hits.txt` の 6 行 (dir は sorted `os.walk` の最初の regular file、file はそれ自身) と
  陽性対照 `dev-wave-t2397-a1-attempt4/acceptance1.log` は存在しなければ rc=5 で止まり代役に落とさない。
  C12 の blob は `git -C <repo> cat-file -p main:orchestrator/manual_probes/test_t2397_a1_source.py`。
- 逸脱: 契約に無い組を 2 種足している (P13 × C12 = 実在の空白入り path と main blob の照合、
  P14 × C13 = 陽性対照の pattern 集合と実在 6 path の引用 content の照合)。いずれも「両方 False」の
  対照行で、結論に影響しない。契約から落とした組は無い。
- 子は `git add` / `git commit` をしていない (`git status --short` は insight dir の untracked のみ)。

## 本走 (親、login node、job dir から)

```
python3 -B <job dir>/probe_truth_table.py \
  --tool <worktree>/tools/audit_dangling_commits.py --repo <worktree> \
  --real-root /work/1/SFC/tanab/dev-wave-jobs --real-hits <job dir>/realpath-hits.txt \
  --selftest --json <job dir>/truth-table.json > <job dir>/truth-table.md 2> <job dir>/truth-table.stderr
```

- rc=0、stderr 空、先頭行 `SELFTEST OK 6/6`。
- 対象 `tools/audit_dangling_commits.py` の SHA-256 = `77251de5fd8169c23eb43242f903012432456b9396c71d6fac1b12093d7fd2ab`
  (worktree HEAD b4631a92e = main、JSON の `tool_sha256` と一致)。
- `truth-table.md` = 874 行・170,918 bytes・SHA-256 `07600bc566856bb5ab179778e3294f085043d969a79954fb19d1e9d4c7bafee8`
  → `verbatim/truth-table.md` に byte 同一で複製 (末尾空白 0・tab 0・NFC)。
- `truth-table.json` = 89,389,377 bytes・SHA-256 `780e1b3d4d6e6b1036029ba8ed7dc6c5e7ec8cc78e8ec6d6172c8a3cda18bd20`
  (C11 の 1 MiB content 84 行の repr で大きい。repo へは入れず job dir に保全)。
  **子の自己検査 JSON と byte 同一** (同 SHA-256) — 走行は決定的。
- 集計: **総行数 862・一致 718・H>P (helper だけ True) 144・P>H (本番だけ True) 0**。
  実在 path で H>P は 18 行 (6 file × 引用 3 形)。

## 実在 path の対照 (段 1 の `find` と probe の存在検査)

- 本番探索根 `/work/1/SFC/tanab/dev-wave-jobs` で名前に境界 byte を含む entry は 6 件
  (`verbatim/realpath-hits.txt`)。共通接頭辞
  `dev-wave-suite-floor-recheck/measure/run2/before-after-0_898290.nqsv/tmp/pytest-of-tanab/pytest-0/` の下:
  1. `popen-gw38/test_generation_two_rejected_b0/g2 clean scan Ω/` (dir、配下 107 file、選択 `.gitattributes`)
  2. `popen-gw31/test_deterministic_artifacts_a0/a much longer root with spaces Ω/` (dir、配下 80 file、選択 `out/env/linux-baremetal/binaries/03cf76a5…`)
  3. `popen-gw29/test_production_emitter_staged0/a much longer root with spaces Ω/` (dir、配下 173 file、選択 `repo/.gitattributes`)
  4. `popen-gw31/test_metacharacter_control_pat0/repo/output/insights/receipt[?]*.json` (file)
  5. `popen-gw3/test_chain_g2_env_tag_unchange0/g2 clean scan Ω/` (dir、配下 107 file、選択 `.gitattributes`)
  6. `popen-gw35/test_literal_pathspec_registry0/repo/:(glob)does-not-match` (file)
- 改行・tab・引用符・backtick・`{}`・`<>` を名前に含む実在 path は 0 件。
- 陽性対照: `dev-wave-t2397-a1-attempt4/acceptance1.log` は実在。main blob
  `orchestrator/manual_probes/test_t2397_a1_source.py` (7,042 bytes) は `Path("/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2397-a1-attempt4")`
  と書き、祖先 dir pattern が helper・本番とも True (R0825)、file 自身は両方 False (R0824)。
- 参考 (結論に使わない): 1 と 3 の `.gitattributes` は互いに同一 bytes (sha256 `705fd4d6…`) だが、
  repo 現行の `.gitattributes` (`f303bfb2…`) とは異なる。今日の候補 (到達不能 blob と bytes 一致) に
  なるかは本 wave で測っていない。

## P型 × C型 × 向き の集計 (JSON から再計算、行数の和 = 862)

| P型 | C型 | 向き | 行数 |
|---|---|---|---|
| P0 | C0 | = | 2 |
| P0 | C1 | = | 6 |
| P0 | C10 | = | 2 |
| P0 | C11 | = | 42 |
| P0 | C2 | = | 4 |
| P0 | C3 | = | 4 |
| P0 | C4 | = | 2 |
| P0 | C5 | = | 2 |
| P0 | C6 | = | 2 |
| P0 | C7 | = | 2 |
| P0 | C8 | = | 2 |
| P0 | C9 | = | 2 |
| P1 | C0 | = | 1 |
| P1 | C0 | H>P | 1 |
| P1 | C1 | = | 3 |
| P1 | C1 | H>P | 3 |
| P1 | C10 | = | 1 |
| P1 | C10 | H>P | 1 |
| P1 | C11 | = | 21 |
| P1 | C11 | H>P | 21 |
| P1 | C2 | = | 2 |
| P1 | C2 | H>P | 2 |
| P1 | C3 | = | 4 |
| P1 | C4 | = | 2 |
| P1 | C5 | = | 2 |
| P1 | C6 | = | 1 |
| P1 | C6 | H>P | 1 |
| P1 | C7 | = | 1 |
| P1 | C7 | H>P | 1 |
| P1 | C8 | = | 1 |
| P1 | C8 | H>P | 1 |
| P1 | C9 | = | 2 |
| P10 | C0 | = | 3 |
| P10 | C1 | = | 9 |
| P10 | C10 | = | 3 |
| P10 | C2 | = | 6 |
| P10 | C3 | = | 6 |
| P10 | C4 | = | 3 |
| P10 | C5 | = | 3 |
| P10 | C6 | = | 3 |
| P10 | C7 | = | 3 |
| P10 | C8 | = | 3 |
| P10 | C9 | = | 3 |
| P11 | C0 | = | 2 |
| P11 | C0 | H>P | 1 |
| P11 | C1 | = | 6 |
| P11 | C1 | H>P | 3 |
| P12 | C0 | = | 2 |
| P12 | C0 | H>P | 2 |
| P12 | C1 | = | 6 |
| P12 | C1 | H>P | 6 |
| P12 | C10 | = | 2 |
| P12 | C10 | H>P | 2 |
| P12 | C2 | = | 4 |
| P12 | C2 | H>P | 4 |
| P12 | C3 | = | 8 |
| P12 | C4 | = | 4 |
| P12 | C5 | = | 4 |
| P12 | C6 | = | 2 |
| P12 | C6 | H>P | 2 |
| P12 | C7 | = | 2 |
| P12 | C7 | H>P | 2 |
| P12 | C8 | = | 2 |
| P12 | C8 | H>P | 2 |
| P12 | C9 | = | 4 |
| P13 | C12 | = | 73 |
| P13 | C13 | = | 201 |
| P13 | C13 | H>P | 18 |
| P14 | C12 | = | 2 |
| P14 | C13 | = | 36 |
| P2 | C0 | = | 1 |
| P2 | C0 | H>P | 2 |
| P2 | C1 | = | 3 |
| P2 | C1 | H>P | 6 |
| P2 | C10 | = | 1 |
| P2 | C10 | H>P | 2 |
| P2 | C2 | = | 2 |
| P2 | C2 | H>P | 4 |
| P2 | C3 | = | 6 |
| P2 | C4 | = | 3 |
| P2 | C5 | = | 3 |
| P2 | C6 | = | 1 |
| P2 | C6 | H>P | 2 |
| P2 | C7 | = | 1 |
| P2 | C7 | H>P | 2 |
| P2 | C8 | H>P | 3 |
| P2 | C9 | = | 3 |
| P3 | C0 | = | 1 |
| P3 | C0 | H>P | 1 |
| P3 | C1 | = | 3 |
| P3 | C1 | H>P | 3 |
| P3 | C10 | = | 1 |
| P3 | C10 | H>P | 1 |
| P3 | C2 | = | 2 |
| P3 | C2 | H>P | 2 |
| P3 | C3 | = | 4 |
| P3 | C4 | = | 2 |
| P3 | C5 | = | 2 |
| P3 | C6 | = | 1 |
| P3 | C6 | H>P | 1 |
| P3 | C7 | = | 1 |
| P3 | C7 | H>P | 1 |
| P3 | C8 | = | 1 |
| P3 | C8 | H>P | 1 |
| P3 | C9 | = | 2 |
| P4 | C0 | = | 1 |
| P4 | C0 | H>P | 1 |
| P4 | C1 | = | 3 |
| P4 | C1 | H>P | 3 |
| P4 | C10 | = | 1 |
| P4 | C10 | H>P | 1 |
| P4 | C2 | = | 2 |
| P4 | C2 | H>P | 2 |
| P4 | C3 | = | 4 |
| P4 | C4 | = | 2 |
| P4 | C5 | = | 2 |
| P4 | C6 | = | 1 |
| P4 | C6 | H>P | 1 |
| P4 | C7 | = | 1 |
| P4 | C7 | H>P | 1 |
| P4 | C8 | = | 1 |
| P4 | C8 | H>P | 1 |
| P4 | C9 | = | 2 |
| P5 | C0 | = | 1 |
| P5 | C0 | H>P | 1 |
| P5 | C1 | = | 3 |
| P5 | C1 | H>P | 3 |
| P5 | C10 | = | 1 |
| P5 | C10 | H>P | 1 |
| P5 | C2 | = | 2 |
| P5 | C2 | H>P | 2 |
| P5 | C3 | = | 4 |
| P5 | C4 | = | 2 |
| P5 | C5 | = | 2 |
| P5 | C6 | = | 1 |
| P5 | C6 | H>P | 1 |
| P5 | C7 | = | 1 |
| P5 | C7 | H>P | 1 |
| P5 | C8 | = | 1 |
| P5 | C8 | H>P | 1 |
| P5 | C9 | = | 2 |
| P6 | C0 | = | 1 |
| P6 | C0 | H>P | 1 |
| P6 | C1 | = | 3 |
| P6 | C1 | H>P | 3 |
| P6 | C10 | = | 1 |
| P6 | C10 | H>P | 1 |
| P6 | C2 | = | 2 |
| P6 | C2 | H>P | 2 |
| P6 | C3 | = | 4 |
| P6 | C4 | = | 2 |
| P6 | C5 | = | 2 |
| P6 | C6 | = | 1 |
| P6 | C6 | H>P | 1 |
| P6 | C7 | = | 1 |
| P6 | C7 | H>P | 1 |
| P6 | C8 | = | 1 |
| P6 | C8 | H>P | 1 |
| P6 | C9 | = | 2 |
| P7 | C0 | = | 1 |
| P7 | C0 | H>P | 1 |
| P7 | C1 | = | 3 |
| P7 | C1 | H>P | 3 |
| P7 | C10 | = | 1 |
| P7 | C10 | H>P | 1 |
| P7 | C2 | = | 2 |
| P7 | C2 | H>P | 2 |
| P7 | C3 | = | 4 |
| P7 | C4 | = | 2 |
| P7 | C5 | = | 2 |
| P7 | C6 | = | 1 |
| P7 | C6 | H>P | 1 |
| P7 | C7 | = | 1 |
| P7 | C7 | H>P | 1 |
| P7 | C8 | = | 1 |
| P7 | C8 | H>P | 1 |
| P7 | C9 | = | 2 |
| P8 | C0 | = | 3 |
| P8 | C1 | = | 9 |
| P8 | C10 | = | 3 |
| P8 | C2 | = | 6 |
| P8 | C3 | = | 6 |
| P8 | C4 | = | 3 |
| P8 | C5 | = | 3 |
| P8 | C6 | = | 3 |
| P8 | C7 | = | 3 |
| P8 | C8 | = | 3 |
| P8 | C9 | = | 3 |
| P9 | C0 | = | 2 |
| P9 | C1 | = | 6 |
| P9 | C10 | = | 2 |
| P9 | C2 | = | 4 |
| P9 | C3 | = | 4 |
| P9 | C4 | = | 2 |
| P9 | C5 | = | 2 |
| P9 | C6 | = | 2 |
| P9 | C7 | = | 2 |
| P9 | C8 | = | 2 |
| P9 | C9 | = | 2 |
| — | C14 | = | 1 |
