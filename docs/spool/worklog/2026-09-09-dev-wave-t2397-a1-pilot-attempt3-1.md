---
schema: izanagi-spool-v1
ledger: worklog
authored: 2026-09-09
wave: dev-wave-t2397-a1-pilot-attempt3
seq: 1
title: [T-2397] A-1 pilot attempt-0003 を投入した — F870 は閉じ 3 job は preflight と受領証取得を通ったが、条件関門が 2 つの独立した理由で測定を拒否した (docs + insight、branch worktree-dev-wave-t2397-a1-pilot-attempt3、実装面の差分ゼロ)
---

## 本文

- 一次資料は `output/insights/2026-09-09_t2397-a1-pilot-attempt-0003/README.md`。
  **pilot の測定値は依然 1 点も無い。**
- ユーザー裁定として本 wave に与えられたのは「attempt-0002 は残す」「投入元 checkout は記録を
  書かない別 worktree」「3 job の preflight 通過を確かめてから bench へ入れる」「着手直前の
  local main から fresh worktree」「規律 2 を緩めない」「本題の投入と記録だけ」「仮想リスク向けの
  gate・検査・台帳・一般化は scope 外」。
- **依頼が添えた codex 相談の見立て「A-1 は先行 fix 着地後であり現在着手不能」は、着手前に現物で
  否定した。** [T-2396] の 3 commit は local main の祖先で、`paper_story_a1_paired.py:917` が
  `os.link` を呼んでいる。着手可とする親の判断を採った。
- **F870 は実機で閉じた。** group 受領証 `receipts/submission.json` が A-1 pilot で初めて公開され、
  失敗台帳は書かれなかった。3 job は受領証を待たずに取得し、preflight (HEAD 一致・clean) を
  3 本とも通り、gflags / glog の依存 staging も完了した。
- そのうえで 3 job とも 40 秒前後で同一の理由で終わった。逐語で
  `v3 BACKOFF_FIXED condition gate rejected measurement:
  supply-effectuation:configure-failed,supply-effectuation:configure-failed,
  runtime-meaning:materialized-decoder-invalid,runtime-meaning:materialized-branch-invalid`。
  **関門は fail-closed で正しく働いており、緩めていない。**
- **止まった理由は独立に 2 件ある** (insight §6)。(a) 関門が別に走らせる configure に依存が
  届いておらず `Could NOT find gflags` で落ちる。A-1 の呼び出しは `capture_define_inputs` へ
  configure 引数を 1 つも渡しておらず、同じ関門に届く他経路は渡している。(b) 関門が読む
  `include/backoff.hh` に marker `silo-backoff-magnitude` が 0 個しかない。**(b) は build を
  要さない経路なので login node で切り分けた。(a) を直しても (b) は赤のままである。**
- **段 3 の相談子は「停止すべき」と勧告したが、親は投入を選んだ。** 子が挙げた 4 件のうち
  実測で閉じられる型は 1 件だけで、それは捨て job `986701.nqsv` で閉じた (job の shell が動く
  時点の `qstat -f` は `Current State = Running` と実値の `Started Request Time` を返し、
  production parser は `unavailable` にならない)。残る 3 件は条件付きかつ fail-closed で、
  閉じるには scope 外の実装が要る。今回はいずれも発火しなかった。
- **関門の失敗理由は compute 走の成果物から読めない。** 拒否文は reason code だけを載せ、
  arm record が持つ detail を捨てる。F855 の恒久対応が定めた形の probe job を別に 1 本投げて
  初めて名指しできた。
- 段 4 で「実装しない」と裁定したため、段 5・6 を飛ばして `4→7→8→9` で進めた。実装面の差分は
  ゼロで、変異 matrix は `DW-S04` により免除。
- 運用で 1 件: `tools/dev_wave_submodule_init.py` の内部 timeout 30 秒が負荷の高い login node で
  足りず落ちる事象が、worklog 1317 に続いて再発した (同型 2 例目)。同じ argv を長い timeout で
  先に走らせれば通り、その後 tool は rc=0 になる。

## 次の一手差分

### 更新

- [T-2397] **P1**: attempt-0003 は投入され、F870 の先へ進んだが条件関門で止まった。
  {{T:a1-gate-build-context}} と {{T:a1-gate-source-root}} の裁定後に attempt-0004 を投入する。
  片方だけ直しても同じ関門で止まる。
  base: 1346d7ce31048e961cb1e25363ea68db83d322a9d9e23d350e1de3eac8fd1fcb

### 新規

- {{T:a1-gate-build-context}} **P1・新規**: A-1 v3 の条件関門が別に走らせる configure へ依存を
  供給する。現状 `capture_define_inputs` へ configure 引数を 1 つも渡しておらず
  `Could NOT find gflags` で落ちる。何を渡すかは F855 の恒久対応 (CCBench が使わない CMake 変数を
  渡さない) と両立させる必要がある。実装は Codex `role=author`。
- {{T:a1-gate-source-root}} **P1・新規**: A-1 v3 の条件関門の runtime-meaning が読む source root を
  裁定する。現状は未 patch の CCBench submodule を渡しており、marker `silo-backoff-magnitude` が
  0 個で抽出が失敗する。関門が materialize 済みの source を前提にしているのか、呼び出し側が
  誤っているのかは設計判断である。
- {{T:condition-gate-detail-artifact}} **P2・新規**: 条件関門の拒否が reason code だけを成果物へ
  残し detail を捨てる点を裁定する。compute 走の失敗理由は、別に probe job を投げるまで名指し
  できない。
