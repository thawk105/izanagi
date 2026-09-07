---
schema: izanagi-spool-v1
ledger: worklog
authored: 2026-09-07
wave: dev-wave-t2228-driver-gate-liveness
seq: 1
title: [T-2228] 残り 3 driver の関門を実測した — 通ったのは 1 箇所だけで、通らなかった 3 箇所は同じ原因だった (probe + PBS + テスト + insight、branch worktree-dev-wave-t2228-driver-gate-liveness、変異 7/7 KILLED)
---

## 本文

- ユーザー依頼は「`backoff_sweep` / `backoff_repro` / `s1_direct_comparison` の inert 経路が
  driver ごとに実際に通るかを実測する。結果は insight へ構造化。条件差が出た場合だけ [T-2329] が
  新しい日付の results file で改める。関門を通すためだけの修正で偽の緑を作らない。本題の実測だけ」。
  起動時に稼働中の 2 wave と対象 4 file の bytes を照合し、編集面の重複が 0 件であることを確認した。
- **答えは driver ごとに違った。** `backoff_sweep` の driver 段の関門は inert 経路まで緑で通った。
  同じ driver の screening 段にある 2 つ目の関門は赤。`backoff_repro` は赤。
  `s1_direct_comparison` は関門へ到達せず、しかも凍結入力に inert cell が 1 件も無いため
  **inert 経路は production では構築されない** (緑でも赤でもない)。
- **通らなかった 3 箇所の原因は 1 つに揃った。** 関門の CMake configure へ準備済みの
  FetchContent base を渡さない呼び出しで、owner TU の preprocess が
  `config.h: No such file or directory` で落ちる。通った 2 例 (A-2 と sweep の driver 段) は
  どちらも `prepare_masstree_fetchcontent` を呼び `-DFETCHCONTENT_BASE_DIR` を渡している。
  修正は規律 2 に触れるため実装せず裁定へ返した。
- **段 2 plan の s1 設計を親が実測で反証した。** plan と段 3 の 2 本はいずれも凍結入力に
  inert cell があるか確かめておらず、plan の s1 runner は `StopIteration` になる設計だった。
  親が凍結成果物を直接読み、18 cell を 4 role の schedule で展開して 0 件を確定し、
  段 4 で測定対象を差し替えた。計算資源を使う前に潰せた。
- **実測設計を 1 job・1 node・1 process へ変えた。** 親 brief の「別ノードへ並行投入」と
  段 2 plan の `afterany` 直列化はどちらも不採用。段 3 lens B が「別 job だと node・compiler・
  network が揃わず driver 間の緑/赤の差を driver に帰属できない」と指摘したため。
  結果として 3 driver は同一ノード・同一 compiler・network 不通という同条件で走った。
- **実測はレビューと fix の後に取り直した。** 1 回目はレビュー前の probe が出した証拠なので、
  段 6 の must-fix 9 件を閉じてから別ノードで再走し、同じ結果を得た。job は 1 回 2 分で終わる。
- 段 6 レビューの must-fix は A が 5 件、B が 4 件 (1 件重複)。すべて Codex fix 子が閉じ、
  親はコードを直していない。変異は 2 巡した。1 巡目で M3 が SURVIVED になり、
  初回照準が冗長 gate (手前の絞り込みが同じ入力を先に弾く) だったと判明したので実効 gate へ
  再照準した。初回台帳は消さず erratum として insight へ残した。
- 計算ノード: 実測 2 回 (各約 2 分)、焦点走 3 回、変異走行 2 回。gen_S の混雑は無し。
  詳細は `output/insights/2026-09-07_t2228-driver-gate-liveness/`。
- 段 8 の改善候補は 3 件挙げて 1 件を自己反証した。(a) `dev_wave_codex.py` へ `--reasoning` を
  誤って渡し rc=2 で 1 回空振りしたが、禁止側は `DW-C01` が既に書いており
  (「他段指定/必須段無指定は rc=2」)、docs の欠落ではなく親の読み落としだった。docs は変えない。
  (b) 隔離 worktree セッションで共有 checkout へ `cd` すると以後の Bash が全部拒否される件は
  エージェント側の作法なので repo docs へは入れない。
  (c) `tools/pegasus/` へ実行体を 1 つ足すと 5 箇所の同期が要り 1 投入で 1 件しか露見しない件は
  insight の §5 へ書いた。台帳への一般化は今回の依頼の scope 外なので行わない。

## 次の一手差分

### 更新

- [T-2228] **P2・進行中**: 3 driver の関門を実測した (attempt `t2228-20260907b`)。
  `backoff_sweep` の driver 段は緑、screening 段は赤、`backoff_repro` は赤、
  `s1_direct_comparison` は到達不能かつ inert 経路が production では構築されない。
  残りは、赤 3 箇所への対処 (FetchContent base の供給 / pin の整合 / freeze の再生成) を
  裁定してから直すこと。
  base: 31256c47d1b5658154a2c7a2642414ebec120bd772622f90d5defb2fddba6647
