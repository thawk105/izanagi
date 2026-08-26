# MoCC の TRACE=1 / TRACE=0 pilot を同一 source の対として取り直した — および 3 本中 1 本で出た G2 anomaly

- 日付: 2026-08-26
- wave: dev-wave-mocc-trace-pair (branch `worktree-dev-wave-mocc-trace-pair`)
- environment: Pegasus `gen_S`、Intel Xeon Platinum 8468、48 physical cores、HT off
- outer source: `97906410e71ed818598df0421772546603435c78`
- ccbench source: `058d0c4e5f237d88ec1c2ebe0739113d82906e47` (base `511c9538…`)
- pair receipt: `output/insights/2026-08-26_mocc-trace-pair-receipt.json`
  (`mocc-trace-pair-receipt/v2`、`status=accepted`、`n_per_trace_mode=2`)

## この成果物の射程 — 先に限界を書く

**この結果を headline の根拠に格上げしてはならない。** クロスプロトコル比較は 2026-07-03 の
協議改訂 (a') が移植・クロスプロトコルを「主実験後の拡張予約」へ降格して以降、現在の論文の
必要条件ではない。ユーザーは本 wave の依頼でも同じ制約を「2026-07-27 裁定で Silo ベースに
固定済み」として再確認した。**本 wave はその制約に従う。**

- **certified な選択・floor・oracle・fitness の根拠に使わない。**
- **全 leg の receipt は `official_certification=false` かつ `eligible_for_refreeze=false` である。**
  pair receipt 自身も同じ 2 値を false で持ち、`prohibited_uses` に headline /
  certified_selection / floor / oracle / fitness の 5 項を true で持つ。
- **`prohibited_uses` は宣言であって強制ではない。** pair receipt を必須入力として読む consumer は
  repo 内に 1 つも存在しない (checker 自身とその test を除く)。下流利用を機械的に止めるものは
  無い。consumer gate の新設は proof chain と oracle gate に触るため本 wave の scope 外とし、
  裁定パッケージへ回した。
- **pair checker の `checker.sha256` は自己申告であり外部 trust anchor ではない。**
  receipt 自身が `self_reported_not_external_trust_anchor: true` を持つ。
- **live verifier / identity checker の TOCTOU は塞いでいない。** job は判定前に outer HEAD と
  clean を 1 度検査するだけで、判定後の再検査は無い。本 wave は「実行された判定器の実体 path と
  SHA-256 を receipt へ記録する」ところまでで止めた。
- **TRACE=1 の receipt は `workload.completed_txns` と `workload.elapsed_s` を持つ。**
  そこから throughput を算術で導出できるが、**導出して性能値として扱ってはならない** (規律 1)。
  pair receipt の TRACE=1 leg には性能 field を一切作っていない。

## 何が問題だったか

前版までの C-1 の現況は「mocc は trace-hook (TRACE=1) と性能 (TRACE=0) の pilot が各 1 本あるが、
どちらも `official_certification=false` の単一観測であり、性能と正しさの対でもない」だった。

**実測すると、対でない理由は source の不一致だった。** 既存 TRACE=1 証拠は ccbench `ef9328a3`、
既存 TRACE=0 証拠は `058d0c4e` である。`058d0c4e` は `ef9328a3` の子で trace hook を保持している
ため、同一 source での対取得は原理的に成立する。

## N>=2 を阻んでいた 3 つの障害 (すべて実測)

**(a) 共有 hydrate 先の in-place 汚染。** hydrate 先は
`output/env/pegasus/silo_ladder_rung1/job-staging/thirdparty-src` という repo 内の共有 path
(`orchestrator/campaign/silo_ladder_rung1.py` の `THIRD_PARTY_STAGING_RELATIVE`) だった。
masstree は autotools で source tree を in-place ビルドするので ignored artifact が残り、
次 job の `fetch_third_party.py` が
`ignored artifacts are forbidden in hydrated source: masstree` で fail-closed する。
本 wave の TRACE=0 probe `949578.nqsv` が実際に 19 秒で rc=1 になった。
**この共有のため複数 job の同時走行も衝突する。**
これは `output/insights/2026-08-24_t1582-mocc-trace0-pilot.md` が
「本 pilot 値を変えない scope 外所見」として専用 handoff へ送った既知型である。
対を N 本取る本 wave では回避不能な一次の障害だった。

**(b) 1 本目の成果物が 2 本目の clean-tree 検査を塞ぐ。** `submit_mocc_trace.sh` は clean-tree を
検査した**後**に preflight capture を repo 内 `output/env/pegasus/mocc-trace/attempts/` へ書く。
よって 1 本目が残した artifact が 2 本目の投入を rc=2 で止める。

**(c) PBS stdout/stderr が submit directory (= repo root) へ落ちる。** `qsub` に `-o` / `-e` が
無かった。`mocc_trace_pilot.sh` が `REPO_ROOT=$(cd "$PBS_O_WORKDIR" && pwd -P)` なので、
submit directory を repo 外へ動かす回避はできない。`--attempts-root` は submitter 側だけの flag で
job 側は repo 内固定 path を読むため、そのままでは使えなかった。

いずれも `docs/pegasus-runbook.md` §8 の投入前チェックリストに既に項目がある事故型で、
submit script 側が未充足だった。

## 実装したもの

**pair checker (`orchestrator/campaign/mocc_trace_pair.py`) を新設した。** 既存の verifier と
TRACE=0 preprocess identity checker の受理集合は一切変更していない。checker はそれらの出力を
消費する事後 gate である。

同一性は receipt に実在する field だけで判定する — outer commit、ccbench base/new OID、
cmake target、workload tuple、`mocc_trace` から `trace_mode` を除いた projection。
tracked policy 全体の byte identity は現行 receipt に該当 field が無く到達不能なので採らず、
裁定へ回した。

**規律 1 の観測者効果の分離を双方向で機械化した。** TRACE=1 側は throughput artifact 参照と
SHA が null であること、receipt 内に `throughput_txns_per_s` などの性能 key が再帰的に
存在しないこと。TRACE=0 側は verifier artifact 参照と SHA が null で `verifier_rc` が
`not-run` であること、receipt 内に verifier verdict key が再帰的に存在しないこと。

**job が証拠 bytes を hash して receipt へ束縛するようにした。** 実装前は receipt に
filename か null しか無く、**実 job が生成していない合成 JSON を「certified」として
pair へ通せた。** 段 3 の 2 レンズが独立に同じ穴を突いたのが本 wave 最大の所見である。
現在は job 側が `verifier.json` / `throughput.json` / `trace0-preprocess-identity.json` の
SHA-256 と、実行した verifier / identity checker の実体 path と SHA-256 を receipt へ記録し、
checker が渡された bytes をその値と照合する。receipt schema は必須 field を増やしたので v3 へ上げた。

**同一 mode の binary SHA 一致は gate にしていない。** 同じ ccbench source の TRACE=0 ビルドが
異なる binary SHA を出すことを実測したためである — 本 wave の対の 2 leg (`949965` / `949966`) が
`60ffd3e1…` と `f6f9af97…` で、pair receipt の `same_mode_binary_sha256_equal` は `false` である。
機序は build source が jobid 依存の `/scr/0_<jobid>/...` に在り、`ycsb_mocc.cc` の `ERR` が
`debug.hh` の `NNN` 経由で `__FILE__` を binary へ入れる一方、prefix-map が無いこと。
**この gate を採っていたら本 wave の対はそれ自身に拒否されていた。**
D-番号は本 wave の decisions fragment を参照。binary SHA は記録に留め、
「同一 mode の binary SHA が違う正例が accepted になる」positive control を変異登録した。

## 結果 — 6 走の全部を書く

同一 outer commit `97906410`、同一 ccbench source `058d0c4e`、同一 workload
(records=10,000、threads=48、zipf skew=0.9、read ratio=50、RMW=0、max operations=10、extime=3 秒) で
TRACE=1 を 3 本、TRACE=0 を 3 本、並行投入した。

| mode | request | 結果 |
|---|---|---|
| TRACE=1 | `949961.nqsv` | certified serializable / anomaly 0 / integrity clean / txns 756,277 |
| TRACE=1 | `949963.nqsv` | certified serializable / anomaly 0 / integrity clean / txns 740,190 |
| TRACE=1 | `949964.nqsv` | **non-serializable。G2 anomaly 1 件。job は rc=1 で fail-closed** |
| TRACE=0 | `949965.nqsv` | 325,805.8487030072 txns/s |
| TRACE=0 | `949966.nqsv` | 340,965.08455582213 txns/s |
| TRACE=0 | `949967.nqsv` | 333,300.74 txns/s |

**対に入れたのは 4 leg である** — TRACE=1 は certified した 2 本、TRACE=0 は正規化 job ID の
小さい方から 2 本 (`949965` / `949966`)。checker は `n_trace0 == n_trace1 >= 2` を要求するので
数を揃える必要があり、TRACE=0 の 3 本目 `949967` は対から外れた。**外した理由は値ではなく
数合わせである。** 外した値も上表に書いた。

**除外規則をデータの後で決めていない。** TRACE=1 側は「certify したものすべて」であり、
TRACE=0 側は job ID 順という値に依存しない規則である。

**`n_trace0 == n_trace1 >= 2` をデータに合わせて緩めなかった。** この述語は段 4 で
実装前に決めたものである。certified な TRACE=1 が 2 本しか無かったからといって事後に
`>= 1` へ落とすのは、規律 2 が禁じる方向 (正しさゲートを緩める変異) と同型である。
**追加の TRACE=1 を投げて 3 本目の certified を取りに行くこともしなかった。**
正しさの run を緑が出るまで回して緑だけを報告するのは selection bias であり、
規律 2・3 の趣旨に反する。

TRACE=0 の 3 本の相対幅は `(max-min)/min = 0.0465` (対に入れた 2 本では同じ式で計算し、
pair receipt の `throughput_dispersion_by_trace_mode` に記録した)。**閾値で拒否していない。**
拒否の閾値を置く根拠が無いためである。

## 3 本中 1 本で出た G2 anomaly — 構造化して残す

`949964.nqsv` の verifier 出力は次だった。

```json
{"phenomenon": "G2", "length": 2, "cycle": [515615, 515616],
 "edges": [{"from": 515615, "to": 515616, "types": ["rw"],
            "reasons": [{"type": "rw", "key": "0000000000000004",
                         "u_ver": [53, 2866], "v_ver": [53, 2869]}]},
           {"from": 515616, "to": 515615, "types": ["rw"],
            "reasons": [{"type": "rw", "key": "0000000000000000",
                         "u_ver": [53, 2867], "v_ver": [53, 2868]}]}]}
```

同 run の integrity は clean だった — orphan_reads 0、version_dups 0、dup_txids 0、
missing_txids 0、write_version_mismatch 0、malformed_keys 0、framing_violations 0、
lock_coverage_violations 0、write_intent_violations 0、permutation_violations 0。
txns 733,287、edges 10,343,211。

**これが何を意味するかを断定しない。** 少なくとも次の 2 つの読みがあり、本 wave はどちらとも
確定していない。

1. **MoCC の実装またはこの workload 設定で本当に G2 が起こりうる。** その場合これは
   CCBench 側の所見であり、`CLAUDE.md` の作業の進め方 4 に従って上流 PR / push の判断は人間に委ねる。
2. **izanagi 側の trace hook (trace v2、[T-816] 由来、D579 が限定認可) が、
   並行時に版や順序を取り違えて偽のサイクルを作った。** integrity 検査が clean であることは
   この可能性を下げるが、消しはしない。integrity は framing と参照整合を見るのであって、
   「記録された版番号が実際に読まれた版と一致するか」を独立に確かめるものではない。

**判定に必要な次の一手は、同じ trace を独立に再検査することではなく、
同一 workload で TRACE=1 を反復して G2 の再現率を測ることである。** 本 wave の観測は
「本 wave の 3 本中 1 本」であり、probe を含めても「同一 source での 4 本中 1 本」にすぎない。
前 wave の TRACE=1 (`934607.nqsv`、ccbench `ef9328a3`) は certified だった。

**この anomaly を理由に verifier を緩めていない。** job は rc=1 で fail-closed し、
throughput も生成していない。この run は対に入っていない。

## 実機で確かめたこと / 確かめていないこと

**確かめた:** 6 本の並行投入が全部通った。修正前は 2 本目が clean-tree 検査で止まり、
共有 hydrate 汚染でも落ちていた。pair checker は実 job が生成した 4 leg を rc=0 で受理した。
実装 commit を含む同一 clean tip から全 leg を取っている。

**確かめていない:** `--attempts-root` を repo 外へ向けた実投入。compute node から
attempts root が見えるかの検査は実装していない (現状も job 側が 60 秒で fail-closed する)。
pair receipt が持つ leg の絶対 path は退避後に stale になる — 束縛として生きているのは
SHA-256 だけである。pair receipt の sidecar 名は出力ファイル名から導出されず固定名なので、
同一 directory に 2 つ目の pair receipt を作ると `FileExistsError` になる。

## repo 外一次資料

`/work/1/SFC/tanab/dev-wave-jobs/dev-wave-mocc-trace-pair/evidence/` に退避した。

- `paired-97906410/` — 本対の 6 走 (786MB)。`0:949964.nqsv` に G2 anomaly の trace 一式を含む。
- `probe-949555/` — DW-G01 生死確認の TRACE=1 (outer は wave base、対には入れていない)。
- `probe-949585/` — 同 TRACE=0。
- `probe-949578-failed/` — 共有 hydrate 汚染で落ちた run と、汚染された `thirdparty-src`。

## 変異 matrix

事前登録した 19 変異を、記録 commit `6131b309` を固定 HEAD として本走した
(spec: `output/insights/2026-08-26_mocc-trace-pair-mutation-spec-final.json`、
sha256 `b199da0791dbce2a47cc83a7063427d0619d3d76ae4e3ccce7607ed59287d971`)。

**baseline PASSED・19/19 KILLED・SURVIVED 0・MISMATCH 0**、期待 node は 19 件すべて完全集合で一致した。

内訳は negative 17 件と positive control 2 件である。positive control は
`DW-M01` の「受理集合を縮小する wave では、承認外の過剰拒否を検出する正例も登録する」に当たる。

- 本数条件を `>= 2` から `>= 3` へ強めて過剰拒否させる変異。正例を含む 5 node を落とす。
- 同一 mode の binary SHA 一致を必須へ戻す変異。**本 wave の対がまさにその形なので、
  これを入れると accepted が reject へ倒れる。**

**probe 走を先に回している。** `DW-M07` は「KILLED 期待で期待 node が空の spec は起動前に中止する」
と定めるので、全件 SURVIVED 期待の probe を先に回して観測 node を集めた。
probe の結果は 19 件すべて MISMATCH (= 実際には全件が失敗 node を出した) で、
その node 集合をそのまま本走の期待にした。

**段 6 のレビュー 2 レンズが、変異が生存する箇所を先回りで 3 件特定していた。** M09 の負例が
複数述語を同時に壊していて二重防壁になっていた件、TRACE=0 側の証拠 SHA 検査に負例が無かった件、
hydrate の検査が mock 境界で止まっていて実 `_hydrate` を観測していなかった件である。
いずれも本走前に fix したので、本走では生存しなかった。
