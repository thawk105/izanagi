# T-1998 balanced stock-inline 対 — 事前登録

論文の性能主張のうち **balanced workload の「無 backoff 対 静的 fixed 5 µs」**の 1 対を、
現行 Pegasus 環境で prospective に測り直すための事前登録である。
D1874 (2026-09-09、ユーザー裁定) が、本書で実値を固定したうえで正式測定を認可した。

**本書が対象とするのは balanced の 1 対だけである。** write-heavy と read-heavy、
最適な backoff 量の探索、機序の一般化は本書の対象外であり、未取得のまま残る。

## 0. 本書の版

**本書は v1 であり、これが初版である。** 改訂履歴はまだ無い。

本書はまだ 1 度も測定に使われていない。**発効後は本文の bytes を書き換えない。**
文面の瑕疵が見つかった場合も、本書の末尾へ `## N. Erratum` として追記する形でだけ訂正し、
既存の行を書き換えない。理由は §1 に書く。

## 1. 事前登録の効力とその限界

本書の bytes は、解析器が sha256 で pin する束縛である。

- **成果物側の束縛。** 成果物が記録する `repository_commit` における本書の blob の sha256 が、
  解析器の `MEASUREMENT_TIME_PREREGISTRATION_SHA256` と一致することを要求する。
  これが「その成果物は本書のどの版の下で測られたか」を決める。
- **解析規則側の束縛。** 解析器へ渡された作業木の本書の bytes の sha256 が、
  解析器の `CURRENT_PREREGISTRATION_SHA256` と一致することを要求する。
  これが「いま適用している解析規則はどの版か」を決める。

この 2 つは**独立した定数**である (D1790)。初版では同じ値になるが、それは正しい状態であって、
2 つを 1 つにまとめてよいという意味ではない。本書を改訂すると解析規則側だけが動き、
本書 v1 の下で測られた成果物は成果物側の定数で引き続き解析できる。
**どちらの側も「任意の値を受理する」形や「複数版のいずれかを受理する」形へ緩めない。**
その帰結として解析器は本書の版に専用となる。**将来の版のための互換層は作らない。**

**本書が閉じないもの。**

- 本書は、`consume_balanced_stock_inline_pair` を呼ばずに人が数値を主張する経路を塞がない。
  閉じているのは、その consumer を通る解析だけである。
- 本書は、正式測定を人が起動することそのものを封じるものではない。認可は D1874 が与えている。

## 2. 何を測る対照か

CCBench の silo を素材とし、balanced workload (`ycsb_zipf_skew=0.9`、`ycsb_rratio=50`、
`ycsb_rmw=0`) で、次の 2 点だけを比較する。

| arm | 意味 | genome |
|---|---|---|
| baseline | backoff を使わない対照 | `BACK_OFF=0`、`BACKOFF_FIXED=-1` |
| target | 静的 fixed 5 µs | `BACK_OFF=1`、`BACKOFF_FIXED=5` |

両 arm とも `NO_WAIT_LOCKING_IN_VALIDATION=1`、`NO_WAIT_OF_TICTOC=0`、`WAL=0` を共有する。

**この 2 点は結果を見る前から確定している。** 旧 headline の balanced 対照が
`BACK_OFF=0` の無 backoff と `BACK_OFF=1, BACKOFF_FIXED=5` の fixed-5 であることは、
2026-08-28 の precheck で既存の genome と既定値から確定した。本書はそれを写しただけであり、
2026-09-07 に取れた生値から選んだものではない。

**producer は 8 点を測る。本書が読むのはそのうちの 2 点だけである。**
残り 6 点を推定量へ代入しない。測定後に最良点を選ぶ (argmax) ことをしない。

## 3. 登録前に既知だった材料の開示

**2026-09-07 に、A-5 経路で balanced の対の生値が取れている**
(無 backoff 3,803,883 tps / fixed 5 µs 4,294,095 tps。原典は
`output/insights/2026-09-07_t2320-backoff-sweep-gate-layer2/README.md` §4.1)。

**この値を本書の主張へ転用しない (D1874)。** 文脈としてだけ残す。理由は 2 つある。

- その走行は 8 genome を commit した後、finalizer の前に rc=1 で落ちており `result.json` が無い。
  本書の consumer では `producer-artifact-missing` になる。
- その走行は本書より前の測定である。事前登録の前に取れた値を後から主張へ入れることは、
  prospective の看板を下ろすことになる。

同様に、旧 headline の +11.3% という数値も既知だが、本書はそれを期待値として固定しない。
固定するのは §4 の identity だけであり、効果量は測ってから読む。

## 4. 固定する identity

次の値を、測定を 1 度も走らせる前に固定する。機械可読な正本は §5 の block である。

| 対象 | 値 |
|---|---|
| CCBench gitlink (hex40) | `511c9538e4e8efa54b45cda62e72389ed3b706ec` |
| 環境契約 digest (`pegasus`) | `e576e9cd1369bba3ae8faca084d1b7256bf919a7dd2e5d6facb093cd9e242c01` |
| job body script の sha256 | `dff913cb1044858b56f25721f2d0aac6539bbcf2a7ddb63b9e6b4bbcac7aecd8` |
| baseline の source bytes sha256 | `2d691b45afd02a7979b1872eeb0a5c5c58223550892331b31641599aa239a2c6` |
| target の source bytes sha256 | `678b7203aa1f9fdca4c35f9b3219d0b9662b60b22331484027adfc6c34580b12` |

### 4.1 job body script の digest

`tools/pegasus/a5_second_boot_backoff_sweep.sh` の bytes の sha256 である。
T-1998 の投入器はこの job body を 1 byte も変えずに再利用し、投入時に実 file を hash して
成果物の `reservation.binding.script_sha256` へ運ぶ。

**この値は 2026-09-09 に変わった。** T-2354 が job 本体の終了処理から共有 submodule gitdir への
`git worktree prune --expire now` を撤去したためである。撤去前の bytes の sha256 は
`0ef4d41ee1ddf8ecd7a86a32a3b9dbaf128279125ef4820c54421973ee281d84` であり、
**その値を持つ過去の成果物 (2026-09-04 と 2026-09-06 の submit / reservation 記録) は
当時の bytes に束縛されたまま有効である。書き換えない。**
本書が固定するのは撤去後の値だけであり、旧値を受理しない。

### 4.2 arm 別の source bytes digest

正式 producer は `patches/silo-backoff-fixed.patch` を作業木へ適用した状態で campaign を走らせ、
build 証拠はその状態から解決される。したがって本書が固定する値も **patch 適用下**で導いたものである。

導出手順は次のとおりで、測定を伴わない。

1. `external/ccbench` が pin `511c953` で clean であることを確認する。
2. `patchharness.applied("patches/silo-backoff-fixed.patch", "511c953")` の内側で、
3. 各 arm の genome について `source_digest.resolve_evidence(genome, "511c953", cxx="g++")` を呼ぶ。

`cxx="g++"` は Pegasus の計算ノードで `buildcache.compilers_for_current_site()` が返す値である。

**baseline の値は patch 適用の有無で変わらない。** patch は `BACKOFF_FIXED` が負のとき
stock 枝を選ぶ設計で、前処理後のソースが原本と同一になる (inert)。`src_token` は `stock` のままである。
**target の値は patch 適用下でだけ正しい。** patch を当てずに計算した値
`6454d9f34b04fdb148bc3324c5b07786d933dcc1ab0f7267aa0b91d414f70a84` は、
本書の起草中に一度誤って使われかけたが、**正しくない。本書はこれを受理しない。**

### 4.3 repository commit

**本書は自身が入る commit を literal で書かない。** 自己参照になるためである。
束縛は次の規則で行う。

- 成果物が記録する `repository_commit` (`result.json`、`reservation.json` の `source_binding`、
  `campaign.lock` の `authority.contract_loader_commit` の 3 者が一致していること) を取り、
- **その commit における本書の blob の sha256** が解析器の成果物側定数と一致することを要求する。

これにより、受理される `repository_commit` は「本書のその版を含む commit」に限られる。
本書が着地する前の commit も、本書を改訂した後の commit も受理されない。

## 5. 機械可読 spec

以下の JSON が identity の**正本**である。解析器はコードの定数ではなくこの block を parse して
期待 identity を組み立てる。**block に入れるのは、解析器が実際に成果物と比較する field だけである。**
§6 の規則は散文であって、この block には入れない (入れると「書いてあるが発火しない保証」になる)。

<!-- IZANAGI-T1998-SPEC-BEGIN -->
```json
{
  "schema_version": "izanagi-t1998-balanced-stock-inline-preregistration/v1",
  "common": {
    "ccbench_gitlink_commit": "511c9538e4e8efa54b45cda62e72389ed3b706ec",
    "environment_contract_sha256": "e576e9cd1369bba3ae8faca084d1b7256bf919a7dd2e5d6facb093cd9e242c01",
    "launcher_script_sha256": "dff913cb1044858b56f25721f2d0aac6539bbcf2a7ddb63b9e6b4bbcac7aecd8"
  },
  "baseline": {
    "canonical_genome": "silo|BACKOFF_FIXED=-1,BACK_OFF=0,NO_WAIT_LOCKING_IN_VALIDATION=1,NO_WAIT_OF_TICTOC=0,WAL=0",
    "source_bytes_sha256": "2d691b45afd02a7979b1872eeb0a5c5c58223550892331b31641599aa239a2c6"
  },
  "target": {
    "canonical_genome": "silo|BACKOFF_FIXED=5,BACK_OFF=1,NO_WAIT_LOCKING_IN_VALIDATION=1,NO_WAIT_OF_TICTOC=0,WAL=0",
    "source_bytes_sha256": "678b7203aa1f9fdca4c35f9b3219d0b9662b60b22331484027adfc6c34580b12"
  }
}
```
<!-- IZANAGI-T1998-SPEC-END -->

`repository_commit` はこの block に無い。§4.3 の規則で決まる。

## 6. 判定の規則 — これは記述であって、block には入れない

次の規則は **consumer の module 定数と計算がすでに固定している**。本書はそれを人が読める形で
書き写しているだけであり、§5 の block には入れない。**本書のこの節の値と実装の定数が食い違ったら、
それは実装の側を直す理由になるが、本書が発火する gate ではない。**

- workload は `balanced`、target の静的 backoff は 5 µs。
- producer は 8 点を測り、本書は baseline と target の 2 点だけを読む。
- 各 arm の sample 数は 5。arm の要約量は 5 sample の median。
- 効果量は `ratio = target の median / baseline の median`、
  `improvement_percent = (ratio - 1) * 100`。
- **どちらか一方でも `unstable` なら、対全体を `inconclusive` とし、`ratio` と
  `improvement_percent` を `null` にする。** 片側だけを採用しない。
- 事後に最良点を選ぶことをしない。8 点のうち他の 6 点を推定量へ入れない。
- 拒否は code だけでなく、対象 field・期待値・実際の値・対象 arm を伴う。

## 7. 実行

- 正式測定は、本書が着地した commit の checkout から起動する。
- 投入は `tools/pegasus/submit_t1998_balanced_stock_inline.sh` を 1 回だけ使う。
  balanced の 1 job だけを出し、fan-out しない。
- 性能計測は trace-disabled build で行う。正しさ検証は別走・別ビルドである (絶対規律 1)。
- verifier が anomaly を出した variant は即 reject する (絶対規律 2)。本書はこの gate を緩めない。

## 8. 報告に必ず含めるもの

- 受理・拒否・inconclusive のいずれであったか。拒否なら code / field / 期待値 / 実際の値 / arm。
- 両 arm の 5 sample、median、`unstable` の判定。
- 成果物が記録した `repository_commit`、gitlink、環境契約 digest、job body script digest、
  arm 別 source digest。
- 本書の版と、成果物側・解析規則側の 2 つの sha。
- **事前登録前に取れた値 (§3) を混ぜない。**

## 9. 本書が閉じないもの

- **compiler の同一性。** §4.2 の source digest は、この論文環境のログインノードの `g++` で
  導いた。計算ノードの `g++` が同一の前処理結果を与えることは証明していない。
  版はどちらも GNU 11.4.0 だが、版の一致は header 閉包の一致ではない。
  **食い違えば `source-identity-unbound` で fail-closed に落ちる。** 偽の緑は生まれないが、
  そのときは測定が成立しないという形で現れる。
- **投入器の同一性。** 成果物から復元できるのは job body までである。どの投入器から出したかは
  成果物に残らない。投入器の provenance は投入器が書く receipt に残る。
- **A-5 (論文の但し書き 3)。** 「計算機を別に起動し直して取り直す」ことは D1525 により
  Pegasus では充足しないと確定しており、本書はそれを外さない。本書が扱うのは別の穴である。
- **write-heavy と read-heavy。** 本書は balanced の 1 対だけを扱う。
- **診断 build の完全な排除。** genome と configure command に診断 knob が現れたら拒否するが、
  それだけでは診断 build を排除できない。排除の本体は §4.2 の arm 別 source digest との一致である。
