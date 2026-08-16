---
schema: izanagi-spool-v1
ledger: decisions
authored: 2026-08-17
wave: dev-wave-t1268-scope-cap-page-align
seq: 1
---

## {{D:scope-cap-exact-or-page-floor}}. bounded scope の cap attest は要求値と page 切り捨て値のちょうど 2 値だけを受理する

**決定:** cgroup の `memory.max` を要求 cap と照合する 3 箇所
(`tools/run_tests.py` と `tools/check_ai_provenance.py` の `_scope_properties_are_enforced`、
`tools/mutation_fanout.py` の `_bounded_scope_cgroup`) は、観測値が
`str(cap)` または `str(cap - cap % P)` の**ちょうど 2 値**のときだけ受理する。
`P` は `os.sysconf("SC_PAGE_SIZE")` が返す正の `int` で、取得できない・型や符号が不正な場合は
`{str(cap)}` のみへ fail-closed する。`cap <= 0` に対する挙動は変更しない。

**理由:**
- kernel は `memory.max` を page 境界へ**切り捨てて**保持する (実測: `getconf PAGESIZE` = 4096 の
  login node で `2913920000` → `2913918976`、cgroup へ直接 write しても同じ)。
  厳密文字列比較は、page 整列していない cap の走行を**決定的に**拒否していた。
- 任意の正の `P` について `cap - cap % P <= cap` が恒真なので、この受理集合は
  **要求より緩い実効上限を 1 つも通さない**。上限の意味は保たれる。
- 予算算出側 (`ceil(peak * 5/4)`) を page 整列させる案は却下した。予約台帳へ記録する
  budget 値と受理集合が変わり、下限付近の既存 LOCAL 期待を壊す。観測側の照合を直せば
  台帳値は保守的なまま `rc=16` が実結果へ戻る。
- 観測値から `P` を逆算する形は採らない。guard が観測を自己正当化して恒真化する。
  production に page size を焼き込むのも採らない (別 page size の環境で誤った上限を通す)。

**却下した選択肢:**
- `floor <= v <= cap` の区間比較 — 上限は緩まないが、切り捨て値でも要求値でもない
  中間値 (例 `P=4096, cap=9216` に対する `8193`) を「要求どおり」と認めてしまう。
- `abs(v - cap) < P` の page 近傍 — 上方向丸めの kernel へ可搬になる代わりに
  `v = cap + 1` を受理し、要求より緩い上限を明示的に通す。上方向丸めは本環境で観測されない。
- 検査そのものを外す・環境変数で無効化する — 正しさ防壁を緩める方向であり採らない。
- 3 箇所を共有 module へ括り出す — 2 つの tool は単独起動される入口で、
  共有化は新しい import failure 面を増やす。代わりに逐語同型の 2 実装へ、
  有限入力表に対する挙動 parity のメタテストを置いた。
