# [T-1851] 契約 v3.1 の erratum 1 — opened の本数式は 2 量を再結合していた

**対象:** `output/insights/2026-09-08_t1851-unit-c1b-sealed-terminal-evidence/contract-v3.1.md`
の 1.4 節と 2 節。

**発行者:** 単位 C2 の wave (branch `worktree-dev-wave-t1851-unit-c2`)。
**発行日:** 2026-09-08。

**規律 7 に従い、v3.1 の本文は 1 文字も削除・改変しない。** 本文書は追記による訂正である。

---

## 1. 訂正する条項

契約 v3.1 は opened の不変条件を 2 箇所で次のように固定している。

- 1.4 節: 「不変条件は `len(throughputs) + nonfinite_count + exec_failures == reps_expected`」
- 2 節: 「opened のとき `len(throughputs) + nonfinite_count + exec_failures == reps_expected`」

**この式は誤りである。** 単位 C2 の段 3 敵対レンズ A が反例を出し、親が現物で裏取りした。

## 2. 反例 (実測)

`reps_expected = 2` で次の rep 証跡を考える。

- rep 0: `returncode=0`、`throughput=100.0`、counter は `not_required`
- rep 1: **`returncode=7`** (非 zero 戻り値)、`throughput=101.0`、counter は `not_required`

これは実行例外ではないので `exec_failures = 0` である。一方 rep 1 は戻り値が非 zero なので
証跡不備であり `rep_integrity_failures = 1`、qualified は `(100.0,)` の 1 本になる。
これは契約 3 節が「`exec_failures` と `rep_integrity_failures` は別の量である」と定めた
まさにその状態である。

ところが旧式は `1 + 0 + 0 = 1 != 2` となり、**この正当な分離状態を拒否する。**

さらに悪いことに、rep 1 の `execution_failure` を偽って `True` にすると
`1 + 0 + 1 = 2` で**通ってしまう**。つまり旧式は

- 非 execution の証跡不備を持つ session を sealed terminal へ運べなくし、
- 偽の実行失敗申告なら運べるようにする

という向きの穴を持っていた。**`exec_failures` を「欠格 rep すべての代理」として使っていたのが
原因である。これは契約 3 節が禁じた再結合そのものである。**

## 3. 訂正後の不変条件

opened のとき、sink の各 rep を次の 4 分類へ**互いに素**に割り当て、本数の和が
`reps_expected` に一致することを要求する。

1. 有限 throughput を持つ qualified rep (`len(throughputs)`)
2. 非有限 throughput を持つ rep (`nonfinite_count`)
3. 実行例外を捕捉した rep (`exec_failures`)
4. **上記以外の証跡不備 rep** (`other_integrity_failures = rep_integrity_failures - exec_failures`)

併せて `exec_failures <= rep_integrity_failures` を要求する
(実行例外を捕捉した rep は必ず証跡不備でもあるため)。この不等式が破れる入力は拒否する。

実装は `orchestrator/campaign/s8b_terminal_evidence.py` の
`_assert_mutual_consistency()` にある。

## 4. 射程 — この erratum が変えないもの

- **`failure` 非 null 側の分岐は変えない。** 「計測なし ∧ `exec_failures == reps_expected`」
  という unavailable projection の規定はそのままである。
- **`launch_failures_count > 0` ∧ `exec_failures == 0` を矛盾として拒否する条項も変えない。**
- 1.4 節の他の規定 (`throughputs` は有限値だけの列、`assess_session` へ有限のみの列と元の
  `reps_expected` を渡す、落とした本数の分だけ `reps` を減らさない) は**すべてそのまま**である。

## 5. 未解決として残す穴 (本 wave では閉じない)

段 6 のレビュー B が指摘し、親が裏取りした。

`returncode=0` ∧ `execution_failure=False` ∧ **`throughput=None`** という rep
(実行は成功したが throughput が得られなかった) は、4 分類のいずれにも入らないため
本数の和が `reps_expected` に届かず、sealed terminal を作れない。

**これは本 wave が持ち込んだ穴ではない。** 旧式でも同じ rep は
`len(throughputs) + nonfinite_count + exec_failures = 0 != reps_expected` で拒否される
(その rep は complete と判定されるので `rep_integrity_failures` にも入らない)。
**改訂前後で挙動が同じ**であり、本 wave の変更に帰属しない。

閉じるなら、この outcome を 5 つ目の分類として明示するか、complete の定義から外すかの
どちらかになる。**どちらも受理集合を動かすので、単位 C2 の scope 外とし、
後続単位の裁定へ送る。**
