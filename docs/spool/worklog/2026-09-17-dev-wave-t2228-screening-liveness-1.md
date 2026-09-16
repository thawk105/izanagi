---
schema: izanagi-spool-v1
ledger: worklog
authored: 2026-09-17
wave: dev-wave-t2228-screening-liveness
seq: 1
title: [T-2228] 正規 CLI から最小 screening を計算ノードで 1 走し、baseline の stock 腕が screening 関門を通過して新規 record (bench-done → commit) を得た — D1784 が保留した「関門が緑」を限定つきで初めて名乗る (docs のみ、branch worktree-dev-wave-t2228-screening-liveness、変異 matrix = 実装面差分ゼロにつき免除)
---

## 本文

- ユーザー依頼は「T-2228 の残り — 現行の正規入口 (CLI の `screening_fixed_us`、tools/pegasus の投入 script) から
  `screening_fixed_us=2` の最小 screening を計算ノードで走らせ、baseline の stock 腕まで緑 record を得る。緑 record が出るまで
  『screening 関門が緑になった』と名乗らない。実装差分は既定でゼロ。着手直前の local main から fresh worktree、計算ノードの
  単独性を確認してから投入、本題の 1 走だけ、規律 2 を緩めない」。
- 一次資料は `output/insights/2026-09-17/t2228-screening-gate-liveness/README.md`。原本 (WAL・campaign.lock) は
  `/work/1/SFC/tanab/izanagi-job-evidence/t2228/attempt-20260917b-official/`、dispatch 証拠・逐語・launcher の写しは同 insight 配下。
- **結果 (attempt b、request `2326.nqsv`、bnode010、01:39-01:49 JST):** CLI rc=0、dispatch は会計照合済み `child_rc=0`、
  `committed=2 aborted=0`。baseline (`BACK_OFF=0`/`BACKOFF_FIXED=-1`) は `build_start → build_done → verify_done (630017 commits,
  0 anomalies) → bench_done 2,388,009 tps (CV 2.48%) → commit`、候補 (fixed=2) も build → 3,406,076 tps → verify → commit。
  「関門が緑」の 6 条件 ({{D:screening-liveness-green-record}}) をすべて照合した。**緑は間接証拠** — production は arm record を
  作って捨てる (D1912)。baseline の meaning 腕は `unestablished` (declaration は非負値のみ)、成功 reason は識別不能。
  性能値は生死確認の副産物で性能主張に使わない。
- **投入形は generic dispatch + job dir の最小 launcher (bash 121 行、Codex author) + 正規 CLI** ({{D:screening-liveness-entry-form}})。
  A-5 job body は `--screening` を持たず finalize が 8 genome を要求するので実装差分なしでは使えない (段 3 レンズ A が
  「A-5 改修は不要」と裁定)。CLI が投入元 submodule へ一時 patch を当てる正規挙動を許容し、代わりに親は投入中に worktree へ
  触らず、終了後に両 tree の clean と stock 一時 worktree の撤去を login で再実測した。
- **親の誤り 2 件 (段 8 で failures へ送った)。** (1) launcher の author 仕様で `PBS_JOBID` を必須にしたが generic dispatch の
  clean env には無い — 段 6 の敵対レビュー 2 本が独立に検出し fix 1 巡 (DW-O13 型、新規
  {{F:child-required-input-absent-from-launch-env}})。(2) official root を job dir 配下に置いたが
  `/work/1/SFC/tanab/dev-wave-jobs/.git` (空 dir) が `.git` 祖先で attempt a (`2319.nqsv`) が screening 関門に到達する前に
  `layout` で赤 — brief の「`.git` 祖先なしを確認済み」は `ls | head -5` で切った不十分な実測だった (F287 の再発)。本題未到達の
  入力誤りとして 1 回だけ再投入した (段 4 裁定 4)。
- 受入全走 1 回目 (tip `9e7bc3345` = 記録 commit + main `fa24e6ea8` の取り込み、02:12-02:23 JST) は child-green、
  **24386 passed / 67 skipped**。段 8 の failures fragment を受入の前に済ませなかった順序誤りで、fragment commit 後に
  最終受入を取り直した (結果は land の受領証が持つ)。
- 段 3 の両レンズが親 brief の誤り 5 件 (prefix の記録 field は `completion.preimage.dependency_prefix`、「関門は無条件」→
  「今回の baseline は request 非空 + force=True」、prepare 3 回・build 4 回、「sweep 再開できる」→「最小 screening の生死確認」、
  「screening が赤のまま」→「最後の観測が赤で供給後は未測定」) を指摘し、段 4 で訂正した。
- 単独性: launcher が割当ノードで `pgrep -af 'ycsb_.*\.exe'`・他 uid の `%CPU>=50`・loadavg を観測 (拒否は前 2 者)。
  generic の入れ子 userns では他 uid が 65534 に見え root 除外が効かない (親が login で実測)。通過は起動前スナップショットまで。
- 変異 matrix は実装面差分ゼロにつき免除。launcher は repo 外 (D1786) で敵対レビュー 2 本 + 焦点再レビュー (GO) だけを守りとする。
- 工数: codex 8 本 (plan 1・consult 2・author 1・review 2・fix 1・focus 1、全て `launcher_rc=0`、`gpt-6-astra`)。
  計算ノード job 2 本 (attempt a 46 秒・attempt b 9 分 36 秒)。

## 次の一手差分

### 完了

- [T-2228] 現行の正規 CLI から `screening_fixed_us=2` の最小 screening を計算ノードで走らせ、baseline の stock 腕が
  screening 関門を通過して新規 record (bench-done → commit) を得た。緑は間接証拠で、限定は
  `output/insights/2026-09-17/t2228-screening-gate-liveness/README.md` §2。
  remaining: none
  base: 077b7816f0e0315148d028a4df75d8414c6b38a6e646bea66811bc1f9f14cf74

### 新規

- {{T:screening-gate-arm-record-persistence}} **P3・裁定待ち**: `backoff_sweep` の screening 関門は arm record を作って捨て
  (D1912 の名指し)、緑を直接記録できない。D1912 が DW-G03 で保留した「拒否時の arm record 保存」の横展開と、緑時の保存の
  要否を裁定パッケージで決める。実測なしに実装しない。
- {{T:dev-wave-jobs-git-marker-blocks-official-root}} **P3**: `/work/1/SFC/tanab/dev-wave-jobs/.git` (空 dir、2026-08-04) が
  `layout._has_git_ancestor` に当たり、job dir 配下を official / exploration の output root にできない。意図した防壁か残骸かを
  確かめてから撤去可否を決める (本 wave では official root を `izanagi-job-evidence/` 配下へ回避)。
