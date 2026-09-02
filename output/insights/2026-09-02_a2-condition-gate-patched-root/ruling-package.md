# 裁定パッケージ — A-2 の inert (stock) 比較は現在の関門では構造的に通らない

wave: `dev-wave-a2-condition-gate-patched-root` / branch `worktree-dev-wave-a2-condition-gate-patched-root`

## 何を頼まれ、どこまで済んだか

依頼は「A-2 の実走が `condition_meaning_gate` に阻まれる原因を確定して直す。受理集合は広げない」だった。
原因は確定し、3 つの拒否理由を実測で消した。残り 1 つが関門本体の性質に当たるため、ここで止めて返す。

計算ノードでの実測 (2 回、いずれも rr5 = `968836.nqsv` → `968849.nqsv`)。

| 拒否理由 | 修正前 | 修正後 |
|---|---|---|
| `BACKOFF_FIXED:supply-effectuation:configure-failed` | 出る | **消えた** |
| `BACKOFF_NOINLINE:supply-effectuation:configure-failed` | 出る | **消えた** |
| `BACKOFF_FIXED:runtime-meaning:materialized-branch-invalid` | 出る | **消えた (green)** |
| `BACKOFF_NOINLINE:runtime-meaning:meaning-witness-undeclared` | 出る | 出る (後述、赤ではない) |
| `*:supply-effectuation:preprocess-failed` (masstree `config.h`) | 隠れていた | **消えた** |
| `*:supply-effectuation:preprocess-root-dependent-builtin` | 隠れていた | **残っている ← 裁定対象** |

## 裁定してほしいこと 1 — inert 比較が構造的に成立しない

**事実.**

`evaluate_define_supply_effectuation` は inert (stock) 経路で、requested 側 = patch 済みの木、
control 側 = 素の stock 木を preprocess し、**bytes が一致すること**を緑の条件にする。
このとき次の guard が入る (`condition_meaning_gate.py:1830-1848`)。

- `_dependency_closure` は、code-owned な依存 file が `__FILE__` / `__BASE_FILE__` を含むと
  その file を `root_dependent_builtin_paths` に積む (`:1531,1564-1566`)。
- inert 経路では needle に **source root と control root の絶対 path** が加わり、
  preprocess 出力にそれが現れると `preprocess-root-dependent-builtin` で赤にする。

CCBench の `include/debug.hh` は `__FILE__` を使う。silo の owner TU
(`cc/silo/transaction.cc`) の依存閉包に入る。

**構造的な帰結.** `capture_define_inputs` は stock root と source root が**別 path であること**を
要求する (`:573-577`)。したがって inert 経路では 2 つの木が必ず別 path にあり、
`__FILE__` を展開する code-owned header が 1 つでもある限り、この guard は**常に**発火する。
A-2 の stock cell (`BACKOFF_FIXED=-1`、`BACKOFF_NOINLINE=0` はいずれも inert) は
どうやっても緑にならない。

**これは本 wave の変更が作った欠陥ではない。** 変更前も source/stock は別 path だった。
configure 段で先に落ちていたため、この層まで到達していなかっただけである。

**同じ形の driver.** `backoff_sweep` / `backoff_repro` / `s1_direct_comparison` も
`stock_comparison` を使う。これらが実際に緑を得られるかは未実測である
(T-1999 / D1198 で関門が義務化されたのは 2026-08-28)。

**選択肢 (いずれも受理集合に触るため独断で実装しない).**

1. **関門側で root path を正規化してから bytes を比較する。** requested 側の source root と
   control 側の source root を、比較前に同一の logical token へ畳む。
   利点: inert 比較が本来意図した意味 (patch が inert 値で stock と同一の意味を持つ) を回復する。
   риск: 正規化は「見なかったことにする」操作なので、畳み方を誤ると差を隠す。
   D1198 が守りたい型を弱めうるので、正規化対象を root path だけに厳密に限る必要がある。
2. **inert 経路を bytes 一致でなく「差が root path のみ」で判定する。** 1 の変種。
   差分を取り、root path 由来の差だけなら緑にする。より明示的だが実装は重い。
3. **`__FILE__` を使う header を owner TU の閉包から外す。** CCBench 側の改変になるので
   D16/D18/D20 の対象。上流に対する変更であり、測定対象そのものを触るので筋が悪い。
4. **inert (stock) 比較を A-2 では使わない。** `defaults` を変えて inert 判定を外す。
   これは関門が見る命題を変えることであり、受理集合の変更にあたる。

**親の推奨は 1。** ただし「root path だけを畳む」ことをコードで担保し、正例
(patch 済み inert = stock で緑) と負例 (実際に意味が違えば赤) の両方を登録することが条件。
**この判断はユーザーのものなので実装していない。**

## 裁定してほしいこと 2 — `BACKOFF_NOINLINE` の意味が常に未確立

`evaluate_define_runtime_meaning` は declaration が無いと `unestablished` を返し
(`:2052-2058`)、`require_condition_gate_family` は `paper` でも unestablished を受理する
(`:2503-2507`)。A-2 の driver は `BACKOFF_FIXED` にしか witness declaration を作らないため、
`BACKOFF_NOINLINE` の意味 arm は**常に**未確立のまま admit される。
`MEANING_SUPPORTED_MACROS` も `{"BACKOFF_FIXED"}` だけである (`:158`)。

D1198 は「供給と意味を独立した必須節として持つ」と書いている。現状は意味節が
`BACKOFF_NOINLINE` について実質空である。厳格化は**受理集合を狭める**変更なので、
「受理集合を広げない」という指示の範囲外として実装していない。

なお、この record は赤ではないため A-2 を止めている原因ではない。
driver が非 green を一律に列挙するので拒否理由の文字列には出る。

## main 取り込み後の再確認 (2026-09-02、merge commit `0428ddcd2`)

本 wave の途中で main が 110 commit 進み、関門本体も T-2153 で大きく変わった
(意味 witness を広げ、意味の節が供給の節の compile command を受け取る形にした)。
取り込み後に上の 2 件を測り直した。**どちらも変わらず成立している。**

- 裁定 1 (root path 依存): guard は健在。`root_dependent = (b"__FILE__", b"__BASE_FILE__")`
  と `preprocess-root-dependent-builtin` は取り込み後も同じ位置にある。
- 裁定 2 (`BACKOFF_NOINLINE` の意味が未確立): `MEANING_SUPPORTED_MACROS` は 9 個へ増えたが、
  増えた 8 個はすべて `IZANAGI_BREAK_*` である。`BACKOFF_NOINLINE` は**依然として含まれない**。

```
['BACKOFF_FIXED', 'IZANAGI_BREAK_EARLY_UNLOCK', 'IZANAGI_BREAK_LOCK_COVERAGE',
 'IZANAGI_BREAK_PERMUTATION', 'IZANAGI_BREAK_PERMUTATION_SWAP',
 'IZANAGI_BREAK_WRITE_INTENT_ERASE', 'IZANAGI_BREAK_WRITE_INTENT_FORGE',
 'IZANAGI_BREAK_WRITE_INTENT_OPSWAP', 'IZANAGI_BREAK_WRITE_INTENT_PTRSWAP']
```

## 実装しなかったもの (指示どおり)

- `_run_process` の stderr 規則の緩和。今回は不要だった。patch 済みの木にすれば
  cmake は未使用変数の警告を出さない。**他に手が無い場合ではなかった。**

## 変更しなかった正しさ防壁

`condition_meaning_gate.py`、`patchharness.py`、`buildcache.py`、`tools/pegasus/` の `.sh`、
policy JSON はいずれも 1 byte も変えていない。受理・拒否の判定式も変えていない。
