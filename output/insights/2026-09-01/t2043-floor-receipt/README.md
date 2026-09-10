# [T-2043] 床値 pilot を現行 main で 1 回投入し、受領書発行段を実機で通した (request 965563.nqsv)

## 要約

[T-2043] は「床値 job が binary admission receipt の発行段で落ちる」赤である。原因は
compiler input manifest が job 専用作業領域の入力を job id 入りの path で記録し、その領域が
消えた後の完全検証が `external compiler input is unavailable` で落ちることだった。
[T-2027] が manifest schema v3 でこの記録形を直したが、**v3 の形で受領書発行段を通した実機走行は
無かった。** 本 wave はそれを 1 回の投入で実測した。

**結果: 通った。** 現行 main `3c1156056` から投入した pilot 走行 `965563.nqsv` は
12 cell すべてで v3 manifest と admission receipt を発行し、driver は rc=0 で終端した。

## 実測の要点

**(1) 根クラス 2 の 7 件は job id を失った。** 12 completion のすべてで、job 専用作業領域の
gflags / glog ヘッダ 7 件が `root: "dependency-prefix"` へ移り、path は
`include/gflags/gflags.h` … `include/glog/vlog_is_on.h` になった。
**走行証跡に job id を含む manifest entry は 1 件も無く、絶対 path も 1 件も無い。**

**(2) 同日の v2 走行との差は、ちょうどその 84 件である。** 本日 11:30 に完走した
`964035.nqsv` (schema v2、記録は `2026-09-01_t1981-t088-consumed-cell-remeasure/`) と
root 内訳を並べると、移動した件数が過不足なく一致する。

| root | 964035 (v2) | 965563 (v3) | 差 |
|---|---:|---:|---:|
| `filesystem` | 6216 | 6132 | −84 |
| `dependency-prefix` | (v2 に無い) | 84 | +84 |
| `snapshot` | 468 | 468 | 0 |
| `fetchcontent-masstree` | 372 | 372 | 0 |
| 合計 | 7056 | 7056 | 0 |

v2 では同じ 84 件が `filesystem` 根で `scr/0_964035.nqsv/gflags-install/include/gflags/gflags.h`
のように **job id を含む path** として記録されていた。これが D1322 が根クラス 2 と名指しした集合である。

**(3) 発行段は 12 cell すべてで通った。** 各 completion は 588 input を持ち、うち
`dependency-prefix` が 7 件で一定である。

| contract entry (先頭 12 桁) | manifest sha256 | admission receipt sha256 |
|---|---|---|
| `1c622c7bfebc` | `471b3124d09d` | `12608f692f99` |
| `2b9f336a7b0c` | `2faeaf4d10b3` | `bf158d32465a` |
| `3b9c7fd409aa` | `86e3557a21e4` | `1e2fd5f2b582` |
| `5906cbf1d74e` | `5fc1a6091d59` | `8cb585cd30e8` |
| `78fb15d6a7a4` | `5fc1a6091d59` | `f1ba49e28957` |
| `8154fcfb0cec` | `471b3124d09d` | `3c14b20d480d` |
| `9b542989f121` | `5fc1a6091d59` | `652a377eea4f` |
| `9f6f99306472` | `01dca68e1e00` | `49a30505e464` |
| `a9d25015cda7` | `5fc1a6091d59` | `a8deb4736528` |
| `b35df5bc00fe` | `12d2f4a1c2e2` | `67586954bd12` |
| `f154cda217b7` | `86e3557a21e4` | `0f35c279ffed` |
| `fbc6ace19e5c` | `2faeaf4d10b3` | `2606ca4e795b` |

**(4) 投入は staging 段で一度落ちた。** `submit_floor.sh` は
`output/env/pegasus/silo_ladder_rung1/job-staging/thirdparty-src` を消費するが**自分では作らない**。
新しい作業木では `--dry-run` が rc=0 でも実投入が
`floor third-party source root is missing or unsafe` で qsub 前に止まる。
`tools/pegasus/fetch_third_party.py hydrate` で repo 外の永続 cache から供給して解消した。
この罠は `tools/pegasus/README.md` に本日既に追記されていた (commit `6398dcd2d`、2 session が
独立に実測) が、**床値の投入手順そのもの** (`docs/phase3-8b-restart-runbook.md` W-2 の順序付き
投入手順) には書かれておらず、手順を正本として辿ると必ず踏む状態だった。本走行が 3 例目である。
段 8 の自己改善で同手順へ供給の段を 1 つ足し、実施手順は `tools/pegasus/README.md` §6 を指す
ポインタにした (内容を複製しない)。

**(5) 投入元の作業木は記録用の作業木と分けなければならない。**
`tools/pegasus/floor_campaign.sh` は job 開始時に、投入元の `HEAD` が受領書の `source_commit` と
一致し、`output/` を除く作業ツリーが clean であることを要求する。投入から起動までの 26 分間、
その作業木では commit も編集もできない。本 wave は使い捨ての作業木から投入し、
記録と land は wave の作業木で行った。

## 事前に固定した判定基準と結果

結果を見る前に handoff へ書いた 4 条件をそのまま適用した。**緩めていない。**
`floor-driver / run-linked` は build と予約より前に出るので単独では合格条件にしない、という
前 wave の注意も引き継いだ。

| # | 条件 | 判定 | 証拠 |
|---|---|---|---|
| 1 | `floor_driver / failed` を書かず `job-result` へ到達 | PASS | checkpoint 14 行に `failed` transition 無し |
| 2 | `driver_rc = 0` かつ journal terminal `completed` | PASS | `job-staging/job-result.json`、journal 212 行の最終行 |
| 3 | manifest が v3・根クラス 2 が `dependency-prefix`・job id 不含 | PASS | 12 completion 全件 v3、`dependency-prefix` 84 件、job id を含む entry 0 件 |
| 4 | `floors` が実数を持つ | PASS | rr20 / rr80 とも有限値。12 cell・除外 0 件 |

不通過の述語として登録した `external compiler input is unavailable` は、走行証跡
(`job-staging` / `run-dir` / `s8b-build-cache`) に **0 件**である。driver の stderr は 0 バイト。

## 走行の諸元

- request `965563.nqsv`、nonce `2f04baea26cdd0dcba9db2dedc18513b`、mode `pilot`
- source commit `3c1156056b9f7d9606a6af1ebac6f386eea642ac`
- campaign run id `20260901T122421Z-2c8cf9be`
- 投入 2026-09-01 20:57:37 JST / 開始 21:23:55 / 終了 22:15:26、**Elapse 3096 秒**
  (elapstim 要求 36000 秒に対し残 32904 秒)
- 12 cell、96 session、除外 0 件、`formula = s8b-floor-stats/v2`
- perf は `available: false`。裁定 `perf-optional-measurement` に従い perf 無しで測った

### 床値

| workload | floor | scale_ref | floor / scale_ref |
|---|---:|---:|---:|
| rr20 | 35490.915 | 1183030.5 | 0.030 |
| rr80 | 45707.745 | 1523591.5 | 0.030 |

**両 workload とも、値は結線された最小相対床 `wired_min_rel_floor = 0.03` に一致する。**
すなわち実測した session 分散は 3% を下回り、床は測定値でなく下限で決まった。
**この 0.030 を「現行環境で較正された床」と読んではならない** — [T-1942] が
2026-09-01 に確定したとおり、cross-campaign / between-block の床はどの workload でも未較正である。

## 主張しないこと

- **cross-job の再束縛が閉じたとは主張しない。** D1220 の限界により、別 job の cache entry が
  選ばれること自体が起きない。本 wave が観測したのは、単一 job 内で v3 の記録形が発行段を
  通ることだけである。
- **v3 manifest が job をまたいで安定するとは主張しない。** 比較対象の `964035` は v2 であり、
  schema が違えば hash は構成上一致しない。cross-job の同一性は本走行では測っていない。
- **`dependency-prefix` 根の entry が origin へ帰属することを検証できるとは主張しない。**
  [T-2027] が同じ弱さを記録しており、本 wave はそこを動かしていない。
- **床値実測の主経路が全体として緑になったとは主張しない。** 通ったのは pilot 経路である。
  official 走行は D1396 のとおり staged transport が不適格 seam である限り起動できず、
  解消案 3 件はユーザー裁定へ返されたままである。
- **再凍結適格な床値が採れたとは主張しない。** `eligible_for_refreeze` は `False` であり、
  [T-748] 裁定 (c) のとおり pilot 値は再凍結へ渡せない。

## 一次資料の所在

証拠 bundle は repo 外に置いた (床値の成果物を repo へ commit しない。restart runbook W-2)。

`/work/1/SFC/tanab/dev-wave-jobs/2026-09-01_t2043-floor-receipt/evidence-bundle-965563/`

| 構成物 | 内容 |
|---|---|
| `run-dir/` | driver の run directory (journal / manifest / result) |
| `s8b-build-cache/` | contract ごとの `completion.json` (binary admission receipt 本体) |
| `job-staging/` | job script が書いた attempt directory |
| `submission/` | 投入受領書と preflight 捕獲 |
| `binaries/` | content-addressed binary store (completion が `store_path` で参照) |
| `job-evidence/` | 計算ノードが書いた `checkpoint.jsonl` |
| `claims/` | campaign run の cell claim marker (権威は共有台帳の側にある) |
| `bundle-manifest.json` | 構成 manifest。file ごとの sha256 と総量を持つ**権威**である |

**件数と総量は `bundle-manifest.json` を読む。** ここへ数値を書き写すと bundle の更新で
食い違うため書かない (初版は 913 file と書いていたが、`claims/` を後から足したので
現物と食い違った。数値の直書きをやめて manifest を権威にした)。

`run directory` だけを残すと参照が dangling になるため、6 構成物を 1 つの bundle にまとめている。
