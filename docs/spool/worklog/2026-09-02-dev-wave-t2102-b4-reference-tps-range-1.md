---
schema: izanagi-spool-v1
ledger: worklog
authored: 2026-09-02
wave: dev-wave-t2102-b4-reference-tps-range
seq: 1
title: [T-2102] B-4 reference_tps の実値域を測り、凍結側改訂を証拠不在で却下した — 狭める実装はユーザー裁定へ返す (docs のみ、branch worktree-dev-wave-t2102-b4-reference-tps-range、実装面 0・変異 matrix 免除)
---

## 本文

- 実測と裁定の全文は `output/insights/2026-09-02_t2102-b4-reference-tps-domain/`。
  設計判断は {{D:b4-reference-tps-finite-decimal}}。
- **引数の前提が起動時検査で覆った。** 引数は「稼働中の t441-grammar-version-canon が
  p3_b4 系 test file を触っている」ので重なるなら実測と裁定案で止めよ、としていたが、
  T-441 wave は着手時点で完了・land 済みだった (branch 0 件、worktree 不在、
  job dir の usage.json が同日 02:08、main に merge commit 群)。編集面の重複は 0 で、
  条件は不成立。よって裁定案でなく裁定の確定まで出した。
- **段 3 の 3 レンズが一致して親の実測の恒真性を突いた。これは正しい指摘だった。**
  JSON の十進 token も IEEE-754 の float も定義上必ず有限十進になるので、
  その表現を母集合にする限り「非有限十進 0 件」は自明に出る。
  親は当初これを結論の根拠に据えており、そのままなら恒真な保証を成果物にしていた。
- 親は批判を受けて母集合を 2 つの軸で広げ直した。(1) key 名を指定せず throughput 系の
  全 field を拾う上位集合、(2) 走査 root をこの user が読める data filesystem 全域へ拡大、
  (3) 封印済み registry の exact 比を wire 形のまま数える恒真でない列挙。
  どれも非有限十進 0 件だった。
- **恒真性批判の含意を潰したのは、丸める前の exact 前身が記録に不在だという実測である。**
  高精度版 throughput の材料 `commit_counts_` と `actual_extime` は campaign 成果物の
  全域でそれぞれ 0 件で、exact 比としての読み替えは遡っても再構成できない。
  追加実測を渡した再検証子はこの含意を無効化と判定した。
- **refuted:** 「恒真なゼロの背後に正当な非有限 exact 値が隠れうる」。
  「caller が任意の有理数を渡せるから非有限十進は正当な upstream 出力になりうる」
  (issuer 自身が caller schedule の非束縛を明記しており、transport 経路であって
  upstream 出力ではない)。「封印済み registry が無ければ原理的に測れない」。
  「closure member の bytes を固定値 pin した現存成果物がある」(検索 0 件)。
  「4 境界案なら非有限十進が先頭 201 件の選抜後まで残る」(親が独立に検算し、
  `generate_analysis_manifest` が先頭で完全性検査を呼ぶことを確認)。
- **段 3 が挙げた real で、実装 wave の must-fix にしたもの:** 既存の変異検査 M12 は、
  registry で先に拒否すると producer の十進 token 化へ到達しなくなり、
  丸め禁止の分岐を一切検査しない恒真な保証になる。単純な移設を禁じた。
- **セッション異常:** Write tool で作った runner `.sh` に実行権が付かず、
  直接 exec した段 2 の初回投入が rc=126 で即死した。子は 1 度も起動していない。
  launcher から `bash <path>` で呼び、`--job-id` と `.done`/`.pid`/`.log` の名前を
  変えて再投入した。段 8 で F103 の再発として台帳へ送った。
  `DW-C01` への 1 行追記は単節予算 1000 bytes に対し現行 996 bytes で入らず、
  節全体が exact pin されているため見送っている。
- **エージェント工数** (receipt.json より): 段 2 plan 25 model call / 379 秒、
  段 3 sol 31 / 561 秒、段 3 luna 32 / 551 秒、段 3b 再検証 19 / 357 秒。
  合計 107 model call。段 3 の 2 本は並列。
- 実装面の差分は 0 なので変異 matrix は免除 (DW-S04)。受入全走は免除せず親が実走した。

## 次の一手差分

### 更新

- [T-2102] **P2・ユーザー裁定待ち**: 非有限十進の `reference_tps` の扱い。実測は完了した
  — `reference_tps` が指す量の production 値域は 443,911 観測で非有限十進 0 件、
  実在する封印済み registry の exact 比も 2,010 値で 0 件 (全件 fixture 由来)。
  凍結側改訂は証拠不在で却下済み ({{D:b4-reference-tps-finite-decimal}})。
  残る裁定は 1 つ。**α** 値域の実測をもって D1344 の条件が満たされたと見なし
  registry を狭める実装へ進むか、**β** 上流を束縛する producer が実装され
  完全な pre-seal batch を列挙できるまで待つか。α なら
  {{T:b4-registry-finite-decimal-narrowing}} を起動する。
  一次資料 = `output/insights/2026-09-02_t2102-b4-reference-tps-domain/`。
  base: 138ebe6fc0a08aaed30441df24a380416e2bfd5a7d1de84d1043e7f4dd402606

### 新規

- {{T:b4-registry-finite-decimal-narrowing}} **P2・新規・[T-2102] の α 裁定が前提**:
  B-4 registry の `reference_tps` 受理値域を有限十進有理数へ狭める。述語・配置の択一・
  正例と負例・must-fix は {{D:b4-reference-tps-finite-decimal}} と
  `output/insights/2026-09-02_t2102-b4-reference-tps-domain/verbatim/s4-ruling.md` §5 が正本。
  M12 を producer 側の直接検査へ再定義しないまま registry 拒否へ移設してはならない。
