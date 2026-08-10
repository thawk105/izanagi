---
schema: izanagi-spool-v1
ledger: decisions
authored: 2026-08-10
wave: dev-wave-t730-t732-nul-lease-merge
seq: 1
---

## {{D:guard-input-exact-str}}. 証拠 path の防壁は、検査する前に exact `str` を作り、その値だけを使う

**決定:** 証拠 path を検査する防壁は、入力を一度 exact な `str` へ固定してから検査し、
以後の canonical 化・git への引き渡し・返却も**その固定した値**で行う。`_safe_path` と
`read_blob_at` の 2 層に適用する。防壁が拒否する制御文字は NUL / CR / LF の 3 つで、
C0 一般へは広げない (ユーザー裁定で不採用)。

**理由:**
- `str` サブクラスは `__format__` (D267 で実測) だけでなく `__contains__` も偽装でき、
  「検査時は安全に見え、使うときだけ危険」という値を作れる。検査対象と使用対象が
  同じ object であることを型で保証しない限り、層ごとの検査は独立に閉じない。
- 固定した値を返すことで、下流の cache key・dataclass field・proof chain の参照 path が
  検査済みの値と一致することまで含めて保証できる。返却だけ元の object に戻す実装は、
  検査を通っても保証を失う。
- NUL は git の要求行を切り詰めるため、path 文字列と実際に読む blob が乖離する。
  CR / LF と機序が同じであり、同じ層で同じ理由コードで拒否するのが一貫する。

**却下した選択肢:**
- **C0 制御文字一般の拒否** — 証拠同一性の観点では過剰で、TAB を含む正当な path を落とす。
  層ごとに TAB の正例を置き、この過剰一般化が入ったら赤くなるようにした。
- **非 `str` 入力 (bytes / PathLike) の意味まで守る** — 受理集合が変わるため裁定へ返す。
  現行の保証は「単一文字列化した後の値が API 上の path である」に限定する。
- **凍結発行・検証層への同じ検査の追加** — 承認された 2 層の外側であり、裁定へ返す。

## {{D:lease-waiter-internal-merge}}. 受入 lease の main 取り込みは待ち手 script の中で行う

**決定:** 受入 lease を `acquired` にした待ち手は、その直後に自分で local main を取り直し、
`HEAD..main` が非 0 のときだけ `--no-ff` の merge commit として取り込み、再検査してから
受入全走を投入する。claim の loop・取り直し・merge・投入は同じ script に置く。
判定は claim の JSON の `state` と固定 literal の exact 比較で行い、各段の rc を個別に見る。
lease の粒度 (受入と land の終端で解放) は D239 のまま変えない。

**理由:**
- 取り込みを親の事前作業にすると、待機時間が取り込みの鮮度を超える区画で原理と機構が
  両立しない。並行 wave が飽和した区画では `acquired` の時点で必ず追い越されており、
  取るたびに lease を捨てることになる (24 分待って 15 commit 遅れ、別 wave で 4 回空振り)。
- `--ff-only` は wave branch が自前 commit を持った時点で使えない。取り込みは merge commit
  でなければならず、その provenance は通常 commit と同じ規約に従う必要がある。
- 出力全体への部分一致で `acquired` を判定すると、`state` 以外の field や診断文で
  偽陽性になる。逆に `status` の見た目に合わせた文字列一致は永久に一致しない。

**却下した選択肢:**
- **lease 粒度を「受入 + land」へ広げる** — 保持時間が伸び、飽和を悪化させる。
  D239 は既に「受入と land の終端で解放」と定めており、拡大の必要もない。
- **正本の待ち手 script を `tools/` へ新設する** — 実装面の新機構であり、
  runbook 改訂の範囲外。散文手順のままにする実効性の限界は裁定へ返す。
- **fencing token で残余 race を閉じる** — D239 が受容済みの限界であり、本決定では変えない。
  再検査から投入までの間に main が進む race は残る。
