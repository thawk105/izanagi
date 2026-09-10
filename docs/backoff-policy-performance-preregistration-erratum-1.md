# adaptive backoff の step policy 腕 — 事前登録 v1 の正誤表 1

`docs/backoff-policy-performance-preregistration.md` (v1、sha256
`2f5170c99dda9dd70647a611bff798b6e54c5e29b60e872cd755e5b8515cc25c`) の **§3.2「腕の間で許す差」に
満たしえない要求が 2 つ**あった。本書はその訂正であり、v1 の bytes は 1 byte も変えない
(18 成果物が v1 の sha256 を束縛として記録しているため)。

## 0. いつ、どうやって見つけたか

**2026-09-08、18 block の測定が完走した直後、事前登録した解析を当てた 1 回目で構造検査が
拒否して判明した。**

- 拒否の逐語: `artifact-invalid: ...: source bytes differ between policy arms`
- **この時点で throughput の値は 1 つも観測していない。** 拒否は構造検査であり、推定値・CI・
  判定語のいずれも計算されていない。訂正の内容も outcome に依存しない。
- 訂正で変えるのは**成果物を受理するかどうかの identity 述語だけ**である。推定量・等価域・
  臨界値・判定語・仮説・層・欠測規則・seed・巡回・block 数は v1 のまま 1 文字も変えない。

**これは事前登録を結果に合わせて緩める操作ではない。** 訂正後の述語は全 18 成果物に一律に効き、
腕にも block にも非対称な影響を持たない。受理されるのは 18 件全部か 0 件かのどちらかである。

## 1. 誤り 1 — 「腕をまたいで source bytes が一致」は原理的に成立しない

v1 §3.2 は、腕の間で許す差を `BACKOFF_STEP_POLICY` と p2 の `BACKOFF_STEP_POLICY_SEED` だけとし、
「それ以外の source bytes ... は 3 腕で一致することを要求する」と書いた。実装はこれを
「`source_bytes_sha256` が 3 腕で一致すること」と読んだ。

**しかし step policy は `patches/cicada-adaptive-counterfactual.patch` による source の置換であり、
腕ごとに source bytes が変わるのが設計である。** v1 自身の §2 も
「seed は p2 の genome と binary を変える」と書いており、§3.2 の文言と矛盾していた。

実測 (18 block、全 72 座標):

| 腕 | source_bytes_sha256 の異なり数 (18 block 通算) |
|---|---|
| `cw-as-dyn-p0` | 1 |
| `cw-as-dyn-p1` | 1 |
| `cw-as-dyn-p2` | 18 (block ごとの seed に対応) |

3 腕は互いに異なる source hash を持つ。

## 2. 誤り 2 — 「block 間で p0 / p1 の binary identity が一定」も成立しない

v1 §3.2 は「block 間では p0 / p1 の genome と binary identity が一定であることを要求し」と書いた。

**しかしこの build は byte 再現的ではない。** 実測では、p0 の source bytes と genome は 18 block を
通じて完全に一定なのに、`binary_sha256` と `build_cache_key` は 18 block すべてで異なる。
build は job 固有の `$TMPDIR` 配下で行われ、その path が成果物へ入るためである。

| 腕 | source | genome | binary | build_cache_key |
|---|---|---|---|---|
| `cw-as-dyn-p0` | 1 | 1 | 18 | 18 |
| `cw-as-dyn-p1` | 1 | 1 | 18 | 18 |
| `cw-as-dyn-p2` | 18 | 18 | 18 | 18 |

**bytes を束縛にしたのが誤りで、束縛すべきは意味である。** 同じ program が全 block で走ったことを
保証するのは source bytes と genome であり、build path を含む binary の bytes ではない。

## 3. 訂正後の identity 述語

v1 §3.2 の identity 要求を次で置き換える。**これ以外の v1 の記述はすべて有効である。**

### 3.1 block の中 (腕をまたぐ)

**一致を要求する:**

- ccbench の pin (`ccbench_commit` / `ccbench_head`)
- 順序付き patch stack と `patch_stack_sha256`
- compiler の identity (`cc` / `cxx`)
- trace mode の証拠 — `backoff_trace` が偽、`build_trace_enabled` が偽、
  診断 symbol 数と文字列数がともに 0、build cache key が `_t0` 終端
- `records` / `extime_s` / `reps_per_job` / `stage` / `kind` / `throughput_scope`

**相異を要求する (v1 に無かった正の対照を足す):**

- 3 腕の `source_bytes_sha256`・`genome`・`binary_sha256` は**互いに異なる**こと。
  一致していたら step policy の define が効いていない (inert) ことを意味するので拒否する。
  driver は既に job 内で「3 腕が同じ binary を作ったら停止」を実装しており、本述語はそれを
  成果物の側からも確かめる。

**要求しない:** 腕をまたぐ `source_bytes_sha256` / `genome` / `binary_sha256` / `build_cache_key` /
`build_admission_receipt_sha256` の一致 (§1 のとおり成立しえない)。

### 3.2 block の中 (1 つの腕の中)

同じ腕の 72 座標のうちその腕に属する 24 座標は、`genome`・`binary_sha256`・`build_cache_key`・
`build_admission_receipt_sha256`・`source_evidence` が完全に一致すること (1 job につき腕ごとに
1 回だけ build するため)。**これは v1 のまま有効で、実測でも成立している。**

### 3.3 block をまたぐ

- **p0 と p1**: `source_bytes_sha256` と `genome` が 18 block を通じて一定であること。
  **`binary_sha256` の一定性は要求しない** (§2 のとおり成立しえない)。
- **p2**: `genome` がその block の事前登録 seed に対応すること (v1 のまま)。
- 全腕: `repo_head` / `driver_sha256` / `pbs_sha256` / ccbench pin / patch stack / compiler が
  18 block で一定であること (v1 のまま)。

## 4. 訂正が測定の意味を弱めていないこと

- 弱めた要求 (腕をまたぐ source/binary 一致、block をまたぐ binary 一致) は、**どちらも成立しえない
  ものであり、成立を要求している間は 18 成果物が 1 件も受理されない。** 実質的な保護を提供して
  いなかった。
- 代わりに足した「3 腕は互いに異なる」は v1 に無い保護であり、**define が inert なまま測った**
  という失敗を捕まえる。この方向では訂正後のほうが強い。
- outcome に関わる規定 (§4 主推定量、§5 等価域と検出力、§6 仮説と層、§7 欠測規則、§8 seed と
  停止規則) は 1 文字も変えていない。

## 5. 本書の位置づけ

- 本書は v1 と対で読む。v1 は凍結されたまま変えない。
- 18 成果物が記録する `backoff_policy_performance_prereg_sha256` は v1 の sha256 のままであり、
  本書の発行によって成果物の束縛は変わらない。
- 解析 module は v1 の sha256 と本書の sha256 の**両方**を逐語 pin し、渡された 2 文書の bytes と
  照合する。
- **この訂正が結果を見た後の後付けでないことを保証するのは、Git 履歴と本書 §0 の記述だけである。**
  repo 内の検査は、gate と検査を同じ主体が変更できる限り、意図的な弱体化への完全な防壁ではない。
  この限界は主張せず明記する。
