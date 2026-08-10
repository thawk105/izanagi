---
schema: izanagi-spool-v1
ledger: worklog
authored: 2026-08-11
wave: dev-wave-t739-freeze-nul
seq: 1
title: 凍結発行・検証層へ証拠 path の NUL 検査を広げた — 裁定 (a) を実装、変異 6/6 KILLED で期待 node 完全一致 (コード + テスト、受入 8210 passed / 20 skipped / 516.99 秒 / rc=0、branch worktree-dev-wave-t739-freeze-nul)
---

## 本文

- **裁定前提の実測 (段 1)。** `evidence_contract_sha256(NUL 入り契約)` は拒否せず
  `524df6b941de655b213c86aa8fa2de7437290a89aa93bf7cbf8eb16f132f0e30` を返した。同じ契約を
  `load_contract_bytes` へ渡すと `contract-path-control-char` で拒否される。穴は実在し、裁定の
  前提を覆す新事実はなかった。
- **NUL は raw byte では到達しない。** strict JSON が生の制御文字を拒否するため、NUL は必ず
  ` ` escape で入る。**bytes 走査では検出できない**ので検査は parse 後の値に対して行う。
  段 3 レンズは「UTF-8 decode が拒否するのではなく JSON parser が拒否する」と機序を訂正した。
- **設計は {{D:freeze-layer-nul-gate}}。** 段 2 の起草は「v1 schema の 2 位置だけ列挙」を主張し
  親案 (key 名での再帰走査) に反対したが、段 3 レンズが malformed shape の反例を出したため
  親案へ戻した。一方、検査位置は起草の反対を採り canonical 化の後へ移した (親の当初案を撤回)。
- **敵対レンズは段 3・段 6 とも 2 本 (`gpt-5.6-sol` / `gpt-5.6-luna`) で全 4 本が NO-GO。**
  段 6 で採った must-fix は「拒否テストが NUL をすべて末尾に付けており、`endswith` 実装が生き残る」
  1 件。中間 NUL のテスト 2 件を足し、変異 `M6-nul-position` を追加登録した。
- **格下げした must-fix 1 件。** 「幅広 JSON で走査 stack が O(n log n) にメモリ増幅し凍結台帳を
  発行できなくなる」という所見を親が実測した。追加割当は raw の 12.13 倍 (width 10k) →
  11.56 倍 (width 100k) と**幅に対して平坦** (O(n) であって O(n log n) ではない)。手前の
  parse + canonical 化のピークが約 17 倍で先に立ちはだかり、読取経路は `MAX_BLOB_BYTES` = 16 MiB
  で上限がある (最悪でも合計 460 MB 程度)。成果物影響が到達不能な条件下でしか成り立たないため
  nit とし、防御的な書き換えは見送った。
- **変異 6/6 KILLED、しかも期待 node 集合と実測が完全一致した** (両方向の差分 0)。
  `M1-remove-gate` 47 / `M2-first-only` 40 / `M3-over-reject` 1 / `M4-order` 1 /
  `M5-nul-to-cr` 49 / `M6-nul-position` 2。`M1` は wave 前の実コードの形そのもの、
  `M3` は承認外の過剰拒否を検出する正例である。台帳は
  `output/insights/2026-08-11_t739-freeze-nul/mutation-ledger.json`。
- **実装子と fix 子は sandbox から pytest を起動できなかった** (`tools/run_tests.py` が Pegasus の
  dispatch preflight `qstat -Q rc=1` で停止)。テストを弱める迂回をせず事実を報告したので、
  親が計算ノードで実走した (実装後 231 passed、fix 後 234 passed、いずれも rc=0)。
- **本 wave が変えるのは受理集合の 1 点だけである。** parse と canonical 化の両方に成功する入力の
  うち、key `path` の値が `str` で U+0000 を含むものだけが新たに拒否される。path の CR/LF、
  `path` 以外の field の NUL、NUL を含まない schema 違反は従来どおり通る。現行契約の hash
  `c4f3740202de302c9dafc9cecac39165bc2213ebf425d2da8cf7ede91b264471` と既発行 g1 record の
  `protected_sha256` `853e6c44442780f180997b86819efaa8cbf245ae15d1a37a83e5b9a4ee99286e` は不変。
- **成果物への波及で 1 点だけ訂正がある。** 親 brief は「core module の編集は成果物に影響しない」と
  書いたが、正しくは `protected_sha256` と C 述語の静的解析に影響しないという意味である。
  activation report の `core_module_blob_sha256` と report digest は module bytes が変わる以上変わる。
  これは commit ごとに変わる揮発値なので、期待値へ焼き込むテストは作らなかった。

## 次の一手差分

### 完了

- [T-739] 凍結発行・検証層へ NUL 検査を広げる裁定 (a) を実装した。単一 choke point
  (`evidence_contract_sha256`) に key 名で再帰走査する検査を置き、契約の全 path 位置 38 箇所・
  中間位置・malformed shape・理由語順序・凍結発行 2 経路・履歴検証・activation report を
  テストで固定した。設計は {{D:freeze-layer-nul-gate}}。変異 6/6 KILLED (期待 node 完全一致)、
  受入 8210 passed / 20 skipped / 516.99 秒 / rc=0。
  remaining: none
  base: b3216e58e74ca7d31139ea64cb8cd2870265baf4beb5eb8e21cea9460063ac5d

### 新規

- {{T:freeze-layer-crlf-gate}} **P2・新規・ユーザー裁定待ち**: 凍結発行・検証層には CR/LF の
  同型の穴が残る。valid な契約の path に CR/LF があると凍結発行・履歴検証は通り、発効時だけ
  `contract-path-control-char` で倒れる。[T-739] と**同じ性質**だが、裁定が NUL-only だったため
  本 wave では実装していない。選択肢 = (a) NUL と同じ扱いで CR/LF も凍結層で拒否する /
  (b) 現状維持。成果物影響 = (b) のままなら凍結台帳・proof chain の受理集合に CR/LF path 契約が
  残る。現行契約には 0 件。段 3・段 6 の両レンズが独立に real と判定した。
- {{T:artifact-control-char-scan}} **P3・新規 (段 8 自己改善候補、予算超過で起票)**: 制御文字を
  話題にする job artifact へ生の制御 byte が混入する。本 wave では brief・handoff・敵対 prompt・
  段 4 裁定の 4 件で実際に混入し、1 件が逐語凍結まで到達して defang と erratum を要した。混入すると
  grep が binary 扱いして検索から落ちる。恒久対応の案 = `DW-O02` へ「制御文字を話題にする artifact は
  作成直後に生の制御 byte を機械走査して除去する」1 行を足す。**実際に足したところ
  `docs/dev-wave/**` の L1.5 予算を 228 bytes 超過した** (9794 > 9566) ため revert した。
  予算値の変更は自己改善の範囲外なので起票する。選択肢 = (a) 同節の既存文を縮約して枠を作る /
  (b) 予算を独立審査にかける / (c) 実施しない。成果物影響 = 未実施なら逐語凍結時の erratum が
  再発しうるが、受理集合・台帳の値は変わらない。
