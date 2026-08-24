---
schema: izanagi-spool-v1
ledger: decisions
authored: 2026-08-25
wave: dev-wave-t1636-dangling-argv-batch
seq: 1
---

## {{D:git-grep-batch-dual-limit}}. 可変個 pattern の git grep は byte と本数の二重上限で分割する

**決定:** 入力に比例して pattern 数が増える `git grep -e` の呼び出しは、argv byte 予算と
batch あたり pattern 本数の**両方**を上限として greedy に分割し、batch ごとの結果を
順序保存の重複排除で合流させる。上限値は保守値であり、environment と pointer table を
含まないため execve 成功の保証ではないと定数の近傍に明記する。

**理由:**
- argv 上限に達する手前で先に壊れる。この機体の実測で、96 byte pattern は 18,034 本で
  `E2BIG` になるが、67 byte pattern 20,000 本 (argv 1.42 MB) は上限内でありながら
  72.7 秒走ったのち `SIGKILL` された。
- `git grep` の RSS は pattern 数にほぼ線形である (500 本 108 MB、2,000 本 415 MB、
  8,000 本 1,642 MB。約 205 KB/pattern)。byte 予算だけを見ると、短い pattern が本数を
  膨らませてこの OOM 領域へ入る。祖先 directory を pattern にする経路では pattern は
  探索根へ向かって短くなるため、短い pattern は現実に生じる。
- 総所要は batch 粒度にほとんど依存しない。実 repo の実測は約 4.5 ms/pattern でほぼ線形
  (100 本 0.71s、4,000 本 18.87s) であり、上限を下げても総時間は増えない。ただし
  1 回あたりの固定費が約 0.30 秒あるため、全 singleton 化は総時間を桁で悪化させる。

**却下した選択肢:**
- byte 予算だけで切る — 上の OOM 領域を塞げない。
- 単独で byte 予算を超える pattern を実行前に拒否する — 実環境の path 長は最大 334 byte
  (探索根配下 122,106 entry の実測) で予算 131,072 byte に対し到達不能な述語であり、
  受理集合と rc 契約を変えるうえ、関門が恒久的に通れなくなる型を新設する。
- 探索根を縮小する、失敗時に再試行する — 決定的な失敗であり回避にならない。
- 上限を environment 実測から動的に clamp する — 予算は `SC_ARG_MAX` の 1/16 であり、
  environment がこの余裕を食い潰す状況ではあらゆる subprocess 起動が壊れる。

## {{D:audit-ref-pinned-to-single-commit}}. 監査は symbolic ref を最初に 1 度だけ OID へ固定する

**決定:** repo 内容を複数回読む監査は、`main_ref` のような symbolic ref を入口で 1 度だけ
commit OID へ解決し、以後の全 `git grep` と全 `git show` に同じ OID を渡す。

**理由:**
- 読み取りを分割すると ref の解決回数が増え、複数 snapshot の結果が混ざる。混ざった結果は
  「どの単一 snapshot にも存在しない参照」を作りうるため、抑止判定が過剰側へ倒れる。
  抑止の過剰は、未 land の作業を載せた commit を「参照済み」と誤判定して消す向きの誤りである。
- 解決を 1 回に集約すると、分割前より観測窓が狭まる。分割の等価性は「各 batch の一致集合の和が
  分割前の一致集合と等しい」ことに依るが、この等式は全 batch が同一 tree を読むときにしか成立しない。

**却下した選択肢:**
- batch ごとに symbolic ref を渡し続ける — 上の等式が成立せず、分割の正当化ができない。
- 解決結果を呼び出し側だけで持ち、内部は symbolic のまま — `git show` が別 snapshot を読む窓が残る。
