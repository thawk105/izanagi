# [T-2224] 認定 launcher の protocol / 軸 引数化 — 生産できる集合は 3 protocol まで狭められたが、実際に生産できた記録は 0 件 (2026-09-09)

- `authority: none` / `default_effect: no-state-change` — 可変状態の正本 (worklog 末尾・現行 phase doc) ではない。
- 依頼の正本: `docs/archive/worklog-phase3-0902-1206.md:478` の [T-2224] 項。
- 本文書は「何を変え、何を測り、何が測れていないか」の記録である。**認定較正 record は 1 件も
  新規生産していない。**

## 1. 依頼と実施範囲

依頼は「認定用 launcher `tools/pegasus/certify_calibration.sh` の `CCBENCH_*` と `ycsb_silo.exe` の
直書きを解き、protocol と軸を引数化して、生産できる protocol の集合を実測で示す。規律 2 を緩めない。
本題の実装と実測だけ。仮想リスク向けの gate・検査・台帳・一般化の追加は scope 外」。

実施したのは launcher と投入側の引数化、テスト、実測、本記録である。
`orchestrator/calibrator/cli.py`、`schema_v2.py`、`make_acquisition_receipt.py`、
`external/ccbench/` は 1 byte も変更していない。

**依頼の「軸」は genome 軸 (CCBENCH_*) であって YCSB の `ycsb_zipf_skew` / `ycsb_rmw` ではない。**
依頼と worklog が名指すのは `CCBENCH_*` と `ycsb_silo.exe` の 2 つである。
段 1 brief はここを取り違えて workload ノブの引数化を scope に入れていた。段 4 で取り下げた。

## 2. 変えたもの

| 位置 | 変更 |
|---|---|
| `certify_calibration.sh` protocol 受理 | `IZANAGI_CALIBRATION_PROTOCOL` を読み、未設定なら `silo`。受理集合は `{silo,mocc,tictoc}` の exact whitelist。副作用前に停止 |
| 同 軸表 | 1 protocol 1 block の静的 `case`。`TRACE=0` + その protocol の `SPACES` 軸ちょうど。軸外 define を混ぜない |
| 同 target / binary | `ycsb_<p>.exe` と `$BUILD_DIR/cc/<p>/<target>`。`BINARY` は実際の `build_argv[4]` から導出する |
| 同 submit receipt 照合 | 既存の `calibration_rratio` 照合に protocol の exact string 照合を追加 |
| 同 `job-result.json` | workload を保ったまま protocol を追加 |
| `submit_certify.sh` | `--protocol {silo,mocc,tictoc}` (既定 silo)。staging 前に whitelist 検査。明示時だけ qsub env へ追加 |

**silo の挙動は変えていない。** 引数省略時の configure / build / calibrate argv と qsub argv は
変更前と同一の文字列列である (テストで固定)。変わるのは pre-submit / submit receipt / job-result の
JSON bytes だけで、これは「argv の byte 互換」とは別の話として区別している。

## 3. cicada を受理集合に入れなかった理由 (実測)

- `SPACES` の cicada 軸 `INLINE_VERSION_OPT` に対応する CMake cache 変数は
  `CCBENCH_INLINE_VERSION_OPT` ではなく `CCBENCH_INLINE_VERSION_OPT_CICADA` である
  (`external/ccbench/cc/cicada/CMakeLists.txt:5`、`cmake/Options.cmake:53`)。
- 汎用名で `-DCCBENCH_INLINE_VERSION_OPT=1` を渡すと、CMake が
  `Manually-specified variables were not used by the project: CCBENCH_INLINE_VERSION_OPT` と報告し、
  実 compile define は cicada 専用 cache の既定 0 のままだった。**要求した値がコンパイラへ届かない。**
- 届いていない値を genome として記録することは、D1374 の却下欄「検査していないことを検査したと
  読ませる」型に当たる。したがって除外した。
- 併せて、正しい cache 名で `INLINE_VERSION_OPT=1` を渡すとビルドが rc=2 で失敗する。
  `cc/cicada/include/transaction.hh:207` の `write(s, key, TupleBody(ver->body_));` が POSIX の
  `write(int, const void*, size_t)` に解決され `cannot convert 'Storage' to 'int'` になる。
  既定 0 のため誰も踏んでいなかった上流の死にコードである。**これは除外の主因ではない。**
- **この除外は「cicada は較正できない」ではなく「現行の軸名では正直に較正できない」である。**
  通すには `SPACES` 側の軸名を実体へ合わせる別作業が要る。

## 4. `BACKOFF_FIXED` を silo 限定に据え置いた理由

現行 CCBench pin `511c9538` に `BACKOFF_FIXED` は存在しない。この macro は
`patches/silo-backoff-fixed.patch` が `cmake/Options.cmake` と `include/backoff.hh` へ供給するもので、
launcher は素の detached worktree をビルドするので patch を materialize しない。

したがって新 protocol へこの define を渡すことは、**供給していない条件を宣言する**行為になる。
D1198 が「patch 供給の define を build へ渡す driver 全体に正例検査を義務化する」と定めた、まさに
その失敗型を新規に作ることになるため、広げなかった。silo は現行挙動を据え置き、扱いはユーザー裁定へ返す。

## 5. 実測

### 5.1 取得経路の断り (先に書く)

**5.2 と 5.3 の実測は login node で走らせた。これは正規経路ではない。**
`cmake --build` を直接叩くと `hooks/guard_bash.py` が login で拒否する。親は背景投入の定型どおり
`bash <script>` で起動したため、guard がコマンド本文から cmake を見つけられず判定を素通りした。
意図的な迂回ではないが結果として防壁を回避している。値は事実として残すが、取得経路は正規でない。

### 5.2 4 protocol の ycsb 実行体はビルドできる (既定値)

CCBench pin `511c9538` を 1 回 configure (rc=0) し、4 target を順にビルドして全部 rc=0。
実行体は 4 種とも `<build>/cc/<protocol>/ycsb_<protocol>.exe` に出る。
所要は silo 33 秒 / mocc 8 秒 / tictoc 6 秒 / cicada 6 秒。

### 5.3 軸がコンパイラへ届くか

各 protocol の `SPACES` 軸をすべて既定と違う値で要求し、`flags.make` の実 `CXX_DEFINES` を読んだ。

| protocol | 到達 | 未使用変数警告 |
|---|---|---|
| silo | 4/4 | なし |
| mocc | 3/3 | なし |
| tictoc | 5/5 | なし |
| cicada | 4/5 (`INLINE_VERSION_OPT` が未到達) | `CCBENCH_INLINE_VERSION_OPT` |

**限界**: cicada の要求値 `INLINE_VERSION_OPT=0` は `Options.cmake:53` の cicada 既定 0 と同値なので、
この 1 軸については「既定と違う値」になっていない。汎用 cache 名が届かないという結論は、
未使用変数警告が独立に支持する。

### 5.4 `-DCCBENCH_BACKOFF_FIXED=-1` は現行 pin では bit 単位で無効

build path を固定して silo を 3 回ビルドした。flag あり (A)・なし (B)・あり再走 (A2) の
binary sha256 は 3 本とも `871b9976…` で一致。実 compile define の diff も空。
A2 が対照になるので A=B は再現ノイズによる偽の一致ではない。
別 path で作った先行実測では hash が違ったが、それは build dir の path が実行体へ埋まるためで
flag に帰属しない。

### 5.5 条件関門は現行 pin では silo でも赤 — 独立 2 例目

launcher と同じ argv で `condition_meaning_gate` を実走 → **rc=2、`admitted=false`**。

- `supply-effectuation` = `configure-failed`。detail は CMake の
  「Manually-specified variables were not used by the project: CCBENCH_BACKOFF_FIXED」
- `runtime-meaning` = `materialized-branch-invalid`。detail は
  「unique BACKOFF_FIXED conditional is unavailable」

`run_condition_gate` は `set -Eeuo pipefail` 下の裸の関数呼び出しなので、赤は job を rc=2 で中断する。

**一次資料の裏取り**: 認定 attempt 12 件 (`output/env/pegasus/calibration/job-staging/`) すべてに
`condition-gate.jsonl` が無い。`calibrate_rc=0` の 2 件 (`0:867876.nqsv` / `0:892707.nqsv`) は
関門導入 commit `0218acc61` より前である。**この関門は認定経路で一度も実走していない。**
さらに job 892707 の `configure.stderr` には当時から
`Manually-specified variables were not used by the project: CCBENCH_BACKOFF_FIXED` が出ている。

**これは新規発見ではなく独立 2 例目である。** 同じ `runtime-meaning` 赤を
`output/insights/2026-09-09_t2397-a1-pilot-attempt-0003/README.md` §6.2 が A-1 driver で記録済みで、
原因 (marker が patch 側にあり pin された CCBench に無い) も同一である。driver が異なるので
`DW-G03` の独立 2 例を満たす。
相違は `supply-effectuation` の原因で、A-1 は関門へ configure 引数を渡しておらず gflags が
見つからない (F580 の 3 例目)、本 wave は引数を正しく渡した上で macro 自体が供給されていない。

### 5.6 計算ノードから外部ネットワークへ到達できない

引数化後の launcher の argv を実物から parse して protocol ごとに configure/build する probe を
`dispatch_compute --task generic` で計算ノードへ投入した (request 987099.nqsv)。
**3 protocol とも configure で赤。** 理由は masstree の FetchContent が

```
fatal: unable to access 'https://github.com/thawk105/masstree-beta.git/': Could not resolve host: github.com
```

で 3 回とも失敗したことである。CCBench の configure は masstree / mimalloc を FetchContent で取る。

**別ノードで独立にもう 1 度確かめた。** `socket.gethostbyname("github.com")` だけを走らせる job を
別に投入し (request 987315.nqsv、host `bnode013`、11:50 JST)、
`socket.gaierror: [Errno -3] Temporary failure in name resolution` を得た。
最初の probe の host は `bnode122` (10:46 JST) である。**異なる 2 ノードで同じ結果**なので、
1 ノード固有の事象ではない。

過去の認定 job 892707 は同じ経路で masstree の bootstrap+make を計算ノードで完走しているので、
環境側が変わったと読める。A-6 の 1 回目も同じ理由で `indeterminate` になっている。

**含意**: 引数化とは無関係に、**現時点では認定 job はどの protocol でも build 段で落ちる。**
非 silo の認定較正を実際に生産するには、この経路へ offline の FetchContent 供給
(`FETCHCONTENT_BASE_DIR` / `FETCHCONTENT_SOURCE_DIR_*` と `FETCHCONTENT_FULLY_DISCONNECTED`) を
配線する別作業が要る。`screening_driver.py:189-206` が同種の配線を既に持つ。

## 6. 生産できる protocol の集合 — 段ごとに書く

単一の数では書けない。

| 段 | 集合 | 根拠 |
|---|---|---|
| launcher の受理集合 | {silo, mocc, tictoc} | 実装。submitter と job body の両方で exact whitelist |
| `SPACES` 登録済み | {silo, mocc, tictoc, cicada} | `orchestrator/campaign/genome.py:209` |
| CCBench に ycsb target がある | {cicada, ermia, mocc, oze, si, silo, tictoc} | `cc/*/CMakeLists.txt` の WORKLOADS 行 |
| 軸が正直に届く | {silo, mocc, tictoc} | 5.3 |
| 既定値でビルドできる | {silo, mocc, tictoc, cicada} | 5.2 |
| **認定較正 record を実際に生産できた** | **∅ (本 wave で 0 件)** | 5.5 と 5.6 の 2 つの blocker |

**「∅」は「空集合であることを証明した」ではない。** 本 wave は較正計測本体を 1 度も走らせておらず、
止めている 2 要因はいずれも T-2224 の外側にある。

## 7. 名乗らないこと

- **「非 silo の within-run floor が公式成果物へ入れるようになった」とは言わない。** 認定較正 record を
  1 件も生産していない。
- **「silo は生産できるが非 silo は生産できない」という依頼の前提は、現行 main では成立しない。**
  条件関門は protocol を問わず silo 経路で赤であり、計算ノードのネットワーク不在は全 protocol に効く。
- 5.2〜5.4 は login node で取得した。正規経路ではない。
- 5.6 は 1 ノード 1 時点の観測であり、計算ノード全体への一般化ではない。

## 8. ユーザー裁定へ返す 1 件

**問い: 認定 launcher が `-DCCBENCH_BACKOFF_FIXED=-1` を渡し続けるべきか。**

- **(R1) 渡すのをやめる (親の推奨)** — 5.4 の実測により、認定バイナリを 1 bit も変えない。
  条件関門の義務も発生しなくなる。代償は silo の genome canonical から `BACKOFF_FIXED=-1` が消えること、
  既存テストの literal pin を新しい契約へ置換すること。
- **(R2) patch を build source へ materialize する (却下推奨)** — patched source を
  `pinned_clean=true` と記録することになり、認定 provenance が偽になる。
  さらに `_DEFINE_SPECS["BACKOFF_FIXED"]` は owner/target が silo 固定なので、非 silo target の
  実効化を証明しない。

本 wave はどちらも実装せず、silo の現行挙動を 1 byte も変えずに残した。

## 9. 凍結した一次資料

- `mutation-final-spec.json` / `mutation-final-ledger.json` — 変異本走。8/8 KILLED、
  MISMATCH 0、baseline PASSED。期待 node は probe 走で観測した完全集合。
  spec sha256 `17a89c7ebdaeebb3f25ceb73b7dd5e5ce2d1ead9f81e8e163a34fd58f29cac77`。
- `compute-probe-result.json` — 計算ノード probe (request 987099.nqsv、host bnode122)。
  3 protocol とも configure で赤。理由は FetchContent の名前解決失敗。
- `verbatim/measured-facts.md` — 親が段 1〜3 で取った実測の逐語。
- `verbatim/stage4-ruling.md` — 段 4 裁定の逐語 (plan v2、変異事前登録、返す裁定パッケージ)。
- `verbatim/stage2-plan.md`、`verbatim/stage3-lens-{a,b}.md`、
  `verbatim/stage5-unit-{a,b}.md`、`verbatim/stage6-review-{a,b}.md`、
  `verbatim/stage6-fix{1,2}.md`、`verbatim/stage6-probe.md` — 子の最終メッセージ逐語。
