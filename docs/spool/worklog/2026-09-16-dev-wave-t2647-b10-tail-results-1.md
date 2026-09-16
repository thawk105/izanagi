---
schema: izanagi-spool-v1
ledger: worklog
authored: 2026-09-16
wave: dev-wave-t2647-b10-tail-results
seq: 1
title: [T-2647] B-10 静的 backoff 右 tail 本走 (09-15 cohort) の results 稿を results 系列へ置いた — 言い方は事前登録 §4.5 の固定表現に限り、性能は未認証のまま、図は無し (docs のみ、branch worktree-dev-wave-t2647-b10-tail-results、変異 matrix = 実装面差分ゼロで免除)
---

## 本文

- **依頼の scope**: `docs/paper-story/results/` へ 09-15 cohort (group `b10-backoff-grid-20260915T061814Z-545445`、
  集団判定 `not-observed-in-any-workload`) の日付付き凍結稿を A-2 / B-7 と同型で置くこと**だけ**。言い方は
  `docs/b10-backoff-static-tail-preregistration.md` §4.5 の固定表現に限り、`performance_certified: false` のまま
  採用根拠にせず、論文図は作らず、2 本目 cohort の地位には触れず、gate・検査・台帳・一般化を足さない (ユーザー指示)。
  成果物は `docs/paper-story/results/2026-09-16-b10-static-tail-not-observed.md` (新規、限定 15 件、生標本 24 cell) と
  `docs/paper-story/README.md` の results 表への 1 行登録。README 項目 3・版・claim-evidence・figures は触っていない。
- **数値は原成果物の直読から作った**: `/work/1/SFC/tanab/b10-backoff-grid-t2500-formal/group-report-20260915/` の
  `.json` / `.dat` / `-complete.json` (SHA-256 は 3 件とも 09-16 の再導出記録と一致) を親が読み、18 区間の推定値・
  24 cell の 5 反復平均・変動係数・生標本 120 rep を再計算した。insight の表を孫引きしていない。
  レビュー A (数値・逐語検算) は 108 + 48 + 48 + 120 + 120 の値と 7 file の SHA-256 を独立に再計算し、不一致 0 と
  報告した。
- **brief 前に実測した新事実 3 件を限定へ入れた**: (a) izanagi 側の source commit は成果物のどこにも記録されて
  いない (残るのは事前登録 commit `cad6f46d8` の束縛と 3 job 一致の `freeze_trees_sha256`)。(b) 正しさ検査
  (`legacy` mode) の条件は `correctness_flags` のとおり性能測定と別の小設定 (4 thread・200 tuple・rratio 50・rmw・
  1 秒・max ope 5) で、3 campaign とも同じ。(c) `.dat` は 1 行ヘッダ + 120 行 (t2266 insight の「27 行目以降」は写して
  いない)。
- **段 2 plan は省き、段 6 に read-only レビュー 2 本 + 焦点再レビュー 1 本を当てた** (Codex gpt-6-astra、
  すべて receipt accepted)。レビュー B (主張範囲) の所見 4 件をすべて real として採用した: (1) must-fix —
  §0.3 と限定 9 の D2050 への言及は「触れない」に反するので除去、(2) 事前登録 §0 の更新契約違反 (追補の §0 未記載、
  b10-tail-formal-submit §3.2) を §1.1 へ引き継ぎ、§7-12 や `invalid` へ読み替えない両面を書いた、(3) 物理量の意味
  witness を主張しない限定 15 を新設、(4) 限定 12 に格子の位置・刻み幅と域内非飽和を結末に含める選択も探索後
  だったこと (事前登録 §0) を加えた。レビュー A の nit 1 件 (§2.2 の引用 `U ≤ 0.05` → 原文 `U_i <= 0.05`) も直した。
- **焦点再レビューが親の誤った不在断定を 1 件捕まえた** (closed 4・partial 1)。限定 15 に「campaign lock にも
  意味 witness の field は無い」と書いていたが、campaign lock の `identity_preimage` は JSON を文字列として抱えて
  おり、`\"` で終端を固定した検索がエスケープで外していた。`grep -c` で数え直すと 3 lock とも
  `meaning_witness_status` = `unestablished_for_positive_backoff_fixed_as_in_existing_sweep`、
  `meaning_witness_gate_required` = `false` を記録している。限定 15 をこの実測へ書き直した (事前登録 §3 の
  「既存 sweep と同じく未確立」と一致する)。
- **変異 matrix は免除**: 実装面 (D95 決定 2) の差分がゼロ (docs 3 file だけ) なので DW-S04 により免除。
  `python3 tools/check_docs.py` rc=0、`git diff --check` rc=0、三軸語走査 (`s8b_holdout_freeze search`) rc=0 (holdout hit 0)。
  実 repo を読むテストのうち results 系列を読むものは無い (`docs/paper-story` を参照する test は figures の provenance
  だけを見る)。
- **受入全走**は本記録 commit を含む tip に対して land 前に 1 回だけ投入し、child-green でなければ land しない。
  本エントリの作成時点では未実施である。
- 逐語 (brief・prompt 4 本・出力 3 本) は `output/insights/2026-09-16/t2647-b10-tail-results/verbatim/`、
  生 log と受領証は `/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2647-b10-tail-results/` にある。

## 次の一手差分

### 更新

- [T-2647] **P2・更新**: 静的 backoff 右 tail 本走の判定を下流へ渡す。
  09-15 cohort の結果節材料を results 系列へ置いた (`docs/paper-story/results/2026-09-16-b10-static-tail-not-observed.md`、
  README results 表に登録)。言い方は事前登録 §4.5 の固定表現「この事前登録の述語では、表現可能域である
  9999 マイクロ秒までに飽和を観測しなかった」に限り、性能は未認証のまま、機序と 9999 より右は書いていない。
  **残るのは 2 つ**: (1) 09-15 cohort を描く論文図 — `output/insights/2026-09-16/t2647-b10-tail-downstream.md` §4 の
  3 条件 (置き場所の契約、新図種の完成要件、Codex author による生成器実装) を先に解く別 wave が要る。
  (2) 版への取り込み — 次の版の契約が決める。本稿は版を改めない。
  base: 1e05e23a3b680f5c5da26d71eca96a9f17538ec3db184aebdebd9e9d58708e7c
