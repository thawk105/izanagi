# [T-2853] R2 fig11 — A-6 read-heavy 正式 certification (fixed 2 µs 対 stock) を現行 driver・現行 policy (5 node)・現行 CCBench pin で Pegasus に測り直す

`authority: none` / `default_effect: no-state-change`

- 作成: 2026-09-29 JST。wave `dev-wave-t2853-r2-fig11` (背景 job)、着手時の基準 = local main `035fc11fa`。
- 前段: `output/insights/2026-09-27/t2853-repro-rest/README.md` §3.3 (投入単位 = 図 1 本、fig11 は試算 1.69 node 時間で暫定確認不要)、
  `output/insights/2026-09-23/t2853-figure-rerun-plan/README.md` §2.2 (fig11 の経路)、先例 `output/insights/2026-09-28/t2853-r2-fig8b/README.md`。
- 元 attempt: `a6-20260908b` (tracked 成果物 `output/insights/2026-09-08_t2411-paper-story-a6-certification/`、結果稿 `docs/paper-story/results/2026-09-18-a6-certification-reject.md`、図 `docs/paper-story/figures/fig11_a6_certification_reject.*`)。

## 0. R2 attempt の地位 — 結果より前に固定する (投入前に commit)

**この節は R2 の job を投入する前に書き、commit してから投入する。** 以後この節は書き換えない (訂正は追記で行う)。

1. **地位。** attempt `a6-r2-20260929a` は、A-6 の測定設計 (policy `paper-story-a2-certification-policy/v2`、study `paper-story-a6-certification`、
   protocol SHA-256 `21427e71793ea744777d11bd90429ce2db1a8d3333ea9e2e0f227ecf377c25dc`、workload rr95、cell `rr95-stock` (`BACK_OFF=0`, `BACKOFF_FIXED=-1`) と
   `rr95-fixed2` (`BACK_OFF=1`, `BACKOFF_FIXED=2`)、各 5 標本の中央値比較、正しさは legacy + performance) を、固定 genome・LLM なしで 1 回測り直す
   **再現パッケージの試行**である。元 attempt `a6-20260908b` の置換・追認・反復ではない。
2. **A-6 の attempt 系列に加えない。** 結果稿 §3.2 (T-2430) は「新しい反復 attempt は行わない」と定め、D1870 は attempt に数えるには事前登録と `tracked_destination` の新 leaf が要るとする。
   R2 はそのどちらも改訂しない。R2 の結果は policy の `tracked_destination` (元 attempt の tracked leaf) へ materialize せず、repo 外の出力親へ collect する (§1)。
   R2 の値を A-6 の主張・結果稿・fig11 の判定へ遡って入れない。
3. **元 attempt との違いを結果より前に明記する。** R2 は現行 repo (`035fc11fa`) の certification driver・現行 policy (`scheduler.nodes = 5`、正しさ検査を兄弟 node へ分ける経路)・
   現行 CCBench pin `6810666` で走る。元 attempt は source `ae8a767eb`・1 node・pin `511c953` だった。`511c953..6810666` の CCBench 差分は `cc/mocc/transaction.cc` だけで silo の source は同じだが、
   R2 は元 attempt と同じ build ではない。protocol の preimage は pin を含まないので protocol SHA-256 は同じになる。
4. **合成しない。** 元 attempt と R2 の標本・中央値・効果・outer status を互いに合成しない。統合 verdict、プール推定、attempt をまたぐ有意水準の保証を作らない。
   数値の近さ・符号の一致を再現精度として評価しない。
5. **attempt 数と停止基準。** attempt 数は 1。停止基準は「この 1 request の結果を、`certified`/`reject` のいずれの outer status でも、`indeterminate` でも、未完走でも、そのまま報告する」。
   起動時の検査で測定前に落ちた場合 (campaign の build・bench が 1 つも始まっていない場合) に限り、原因が driver・policy・依存元の変更を要しないなら、新しい attempt id で同じ形のまま 1 回だけ投げ直してよい。
   落ちた request ID・attempt id・理由は記録し、取り下げない。測定が始まった後の失敗は投げ直さず、その結果を報告する。
   **費用の条件:** 本走の見積りは 1 request × 5 node で 1.47 node 時間 (同じ A-6 protocol・5 node 形の `a6-20260909b` の Elapse 1,057 s)、受入 1 回の見積りは 0.25 で、合計 1.72 (D2212 項 4 の線 2 node 時間の下)。
   測定前に落ちた request の Elapse × 5 node を実費として足し、投げ直した後の見込み合計 (実費 + 1.47 + 0.25) が 2.0 未満のときだけ投げ直す。2.0 以上ならユーザーの確認を得るまで投げない。
6. **正しさ。** 正しさは job 内の trace 有効 build の別走で判定し (規律 1)、anomaly が出た cell は即 reject とする (規律 2)。性能は trace 無効 build で測る。
   検査を緩めて描く・記録することはしない。
7. **図と表。** 元の fig11 と同じ生成器 `tools/plotting/plot_a2_certification.py` (bytes 不変) で R2 の図を描き、元 attempt と R2 を同じ生成器の読み込み関数で読んだ対照表を並べる。
   生成器が R2 の入力を検査で拒否した場合は検査を外して描かず、拒否理由と得られた値を表で記す。描くための repo 外 wrapper は caption の地位・役割語だけを差し替え、測定値の受理条件とレイアウト検査は変えない。
8. **原成果物は不変。** 元 attempt の tracked 成果物・結果稿・既存 fig11 は凍結物のまま保持し、R2 の結果で書き換えない。
9. **主張の範囲を増やさない。** outer status は当時と同じ protocol の中央値比較の答えであって、有意差・between-run floor 超の退行・研究の成否を判定しない。
   性能は認証しない (performance certification ではない)。R2 の値を他の read 比率・他の機体・他の pin・他の protocol へ外挿しない。
10. **trace 保全口 (D2233)。** 投入 driver `submit_paper_story_a2_certification.sh` は `qsub -v` へ渡す環境変数を固定で列挙し、`IZANAGI_TRACE_ARCHIVE_ROOT` を job へ渡す口が無い。driver は変えないので保全口は使わない。
    R2 の trace は保全されず、R1 (保存 trace の再判定) の入力にならない。

## 結論

1. **fig11 の測定 (A-6 read-heavy、stock 対 fixed 2 µs の 2 cell × 各 5 標本) を、現行 repo の certification driver `tools/pegasus/submit_paper_story_a2_certification.sh` で Pegasus に 1 回投げて測り直した。**
   request `35349.nqsv` (5 node、2026-09-29 15:17〜15:35 JST) は完走し (driver_rc 0)、finish-group と collect も終了コード 0 だった。測定は **1.47 node 時間** (見積り 1.47 とほぼ一致、§2)。投げ直しは無い。
2. **R2 の outer status は `reject`、効果 (adopted 中央値 / stock 中央値 − 1) は −5.2144%** (stock 中央値 10,325,830 tps、fixed 2 µs 中央値 9,787,402 tps)。正しさは別の trace 有効走で 2 cell とも `certified`・anomaly 0、source binding は 2 cell とも `bound` (§3)。
   元 attempt は `reject`・−5.7841% だった。2 つを合成せず、符号の一致を再現精度として評価しない (§0 項 4)。
3. **元の fig11 と同じ生成器 (bytes 不変) で R2 の図を描いた。** 生成器の受理検査・閉包検査・レイアウト検査はすべて通った。repo 外の wrapper は caption の地位・役割語 4 箇所だけを差し替えた (§5)。
   同じ wrapper で元 attempt を原 metadata のまま描くと、既存 fig11 の provenance と `artist_series` が完全一致した (陽性対照)。
4. **元 attempt と R2 の値を並べた表**を、同じ生成器の読み込み関数 (全検査つき) を attempt ごとに別々に呼んで作った (§4)。
5. trace 保全口 (D2233) は、この driver が環境変数を job へ渡す口を持たないので使っていない (§0 項 10)。driver は変えていない。

## 1. 経路と投入前の前提

- **投入 checkout。** 着手時の local main `035fc11fa` の detached worktree を `/work/1/SFC/tanab/tmp/t2853-r2-fig11-20260929/submit-tree` に作り (submodule 再帰初期化、CCBench = `68106660`)、そこから投げた。
  job が待ち行列にいる間に wave の branch が進んでも、job が照合する HEAD (`IZANAGI_A2_EXPECTED_HEAD`) と repo root が動かないようにするためである。untracked を含めて clean であることを投入直前に確かめた。
- **fig6 wave との分離。** 並走する fig6 wave は A-2 policy (job 名 `paper-a2-cert`、durable base `dev-wave-paper-story-a2-cert-20260824`) で、本件は A-6 policy (job 名 `paper-a6-cert`、base `dev-wave-paper-story-a6-cert-20260902`) である。
  checkout・job 名 (driver の同名 request 検査の単位)・attempt root・collect 先・wrapper の置き場はすべて別。
- **依存元。** `--dependency-prefix-source /work/1/SFC/tanab/izanagi-a2-deps` (B-7 と同じ)。third-party は永続 cache `/work/1/SFC/tanab/izanagi-thirdparty-cache` から `tools/pegasus/fetch_third_party.py hydrate` で repo 外の新 staging
  `/work/1/SFC/tanab/izanagi-measurements/t2853-r2-fig11-20260929/thirdparty-src` を作り、その `source_root` を渡した。5 本 (masstree・mimalloc・googletest・gflags・glog) とも head = policy pin (`verbatim/hydrate.log`)。
- **現行 pin での初回。** CCBench `511c953..6810666` の差分は `cc/mocc/transaction.cc` だけ (silo・CMake・依存宣言は同じ)。durable base の既存 A-6 attempt (`a6-20260908b`・`a6-20260909a`・`a6-20260909b`) の preregistration はすべて pin `511c953` で、
  insights・worklog の grep でも pin `6810666` でこの driver を投げた記録は見つからなかった (射程はこの範囲)。投入前に login で、driver と同じ素の `git apply` の `--check` で静的 backoff patch が `6810666` の木へ当たることを確かめた (`verbatim/precheck-patch.log`、rc 0)。
  condition gate・実 compiler・兄弟 node への検証 fanout は計算ノードでしか確かめられず、job 自身の測定前検査に任せた (結果は §2、通った)。
- **collect の書き先。** collect は `<repo_root>/<tracked_destination>` (policy が固定する元 attempt の tracked leaf と同じ相対 path) へ materialize し、既存の leaf を拒否する。
  元 attempt の tracked 成果物に触れないよう、`--repo-root` に repo 外の空 dir `/work/1/SFC/tanab/izanagi-measurements/t2853-r2-fig11-20260929/collect-root` を渡した (materialize は git 状態を見ない)。
  materialize は durable base の同じ (study, policy_sha256, current_pin) の兄弟の結果も調べるが、既存 attempt は pin が違うので衝突しない。collect は submission receipt が policy の絶対 path を束縛するため submit-tree の module から呼んだ。

## 2. 投入と完走

| attempt | 投入 (JST) | request | 確保 | host (campaign claim) | 開始〜終了 (JST) | Elapse (s) | driver_rc |
|---|---|---|---|---|---|---|---|
| `a6-r2-20260929a` | 2026-09-29 15:16:53〜15:17:21 (submitter) | `35349.nqsv` | 5 node (NQSV 会計の Number of Jobs 5) | `bnode087` | 15:17:25 〜 15:35:01 | 1,061 | 0 |

- 投入 argv と出力は `verbatim/submit.log`、会計は `verbatim/elapse.log` (job.stderr の NQSV 会計行の抜粋)。投入から開始まで 12 秒で、待ち行列の待ちはほぼ無かった。
- 起動時検査での失敗・投げ直しは無い (§0 項 5 の投げ直しは発動していない)。
- finish-group (15:36、終了コード 0) が completion と acquisition の receipt を作り、collect (15:36、終了コード 0) が R2 の certification を collect-root に materialize した (`verbatim/finish-group.log`・`verbatim/collect.log`)。
- attempt root: `/work/1/SFC/tanab/izanagi-measurements/dev-wave-paper-story-a6-cert-20260902/a6-r2-20260929a/` (preregistration・receipts・jobs)。

## 3. R2 の certification — 本番 CLI の出力

collect-root の `output/insights/2026-09-08_t2411-paper-story-a6-certification/` (repo 外。名前は policy の `tracked_destination` をそのまま使ったもので、元 attempt の tracked leaf とは別の場所) に次が出た。

| 成果物 | sha256 |
|---|---|
| `certification.json` | `0a6008d175f0b4a13d952b98306621e717ecd8d07e00354e5914a205d550aed0` |
| `raw-manifest.json` | `7799a0644effe5f89b932be201bba6b9c9ab879f44fbab786a274cd220653dfd` |
| `artifact-manifest.json` | `85dd2d517ecaa554563988ddb94742da4fc6c09aac85c2b2d0846fbb7df2180b` |
| `COMPLETE.json` | `73fc715de8e4c866ba033b6f0e371f99d0251053d28efc5c1544a9d12f17901b` |
| `acquisition-receipt.json` | `808401b95f6122e8a81e7c6f7e10ce1c78124658ab76005a586531bee058f25c` |
| `submission-receipt.json` | `14edbe8a7f4ba59bec3e9dcfb3f246f6e054cc97c2bd5006f17fc24a4f2ac7b6` |
| `completion-receipt.json` | `5b3f2c74e160d1fb702139d78f74c8ff8375775190e10531b72cbc757d5521a9` |
| `condition-gate-rr95.admissions.jsonl` | `71fa88dd92aef9a0542386d2d18f0abebbab1aa1e7e8330a8bf54c295e71fdce` |

- `certification.json`: schema `paper-story-a2-certification-result/v4`、study `paper-story-a6-certification`、attempt `a6-r2-20260929a`、**status `reject`**、`effects.rr95` = −0.05214379860989382、
  `current_pin` `6810666`、`source_commit` `035fc11fa601547f5d68e54f5661c5daa70b93a5`、protocol SHA-256 `21427e71…` (元 attempt と同じ)。
- cell: `rr95-stock` (stock) 中央値 10,325,830 tps、`rr95-fixed2` (adopted) 中央値 9,787,402 tps。2 cell とも `correctness.status = certified`、`source_binding_status = bound`。
- 正しさは job 内の trace 有効 build の別走、性能は trace 無効 build (job body の既存経路、規律 1)。anomaly は 0 (生成器の読み込み検査で確認)。
- §0 のとおり、この status は元 attempt の status と合成しない。性能は認証していない。

## 4. 元 attempt と R2 の対照表

同じ生成器の `load_measurements` (全検査つき) を、元 attempt は生成器の固定 hash 表で、R2 は collect 後の実 bytes の sha256 で、別々に呼んで書いた表である
(`figures/fig11_comparison.md`、sha256 `5404bea87c2a31782ce7c3d75cfe739b991ff2891f82f97ab8037a4596b682ad`)。値は attempt ごとに計算し、合成・差・比を作っていない。数値の近さを再現精度として評価しない (§0 項 4)。

| attempt | request | host | source commit | CCBench pin | 確保 node | effects.rr95 | outer status |
|---|---|---|---|---|---|---|---|
| 元 `a6-20260908b` | `982234.nqsv` | bnode031 | `ae8a767eb` | `511c953` | 1 | −0.057841193339621455 | reject |
| R2 `a6-r2-20260929a` | `35349.nqsv` | bnode087 | `035fc11fa` | `6810666` | 5 | −0.05214379860989382 | reject |

| attempt | cell | trace 無効性能 5 標本 (tps) | 中央値 | 平均 ± t 95% CI 半幅 (自由度 4) | 代表反復の abort rate | 正しさ / anomaly |
|---|---|---|---|---|---|---|
| 元 | rr95-stock | 10365808, 10103030, 10029940, 10088796, 10073679 | 10088796 | 10132250.6 ± 165646.2 | 0.1547 | certified / 0 |
| 元 | rr95-fixed2 | 9753031, 9587735, 9488225, 9494008, 9505248 | 9505248 | 9565649.4 ± 139341.9 | 0.1450 | certified / 0 |
| R2 | rr95-stock | 10632564, 10325830, 10361900, 10281088, 10315111 | 10325830 | 10383298.6 ± 176681.3 | 0.1554 | certified / 0 |
| R2 | rr95-fixed2 | 9961007, 9787402, 9778168, 9790839, 9739453 | 9787402 | 9811373.8 ± 106923.1 | 0.1445 | certified / 0 |

- 確保 node は、表の生成物では「policy 5; receipt 5」(policy の `scheduler.nodes` と、reservation に束縛された allocation qstat の Execution Hosts の数、bnode087〜bnode091)。NQSV 会計の Number of Jobs 5 (`verbatim/elapse.log`) とも一致する。
  初版の表は receipt 側を「unknown」と書いていた (wrapper が同じ行に並ぶ複数 host を数えられなかった)。段 6 の fix で直した (§9)。
- abort rate は生成器の規則どおり、throughput が中央値に最も近い反復の 1 観測であり、区間も機序の主張も持たない。
- CI は標本の記述であって、効果・判定・中央値の区間ではない。有意差の判定はしない。

## 5. 図 — 元の fig11 と同じ生成器で描いた R2 の図

- **描けた。** 生成器 `tools/plotting/plot_a2_certification.py` (sha256 `aac636595ec0b211133edcc18bc1f72f984e346f58e7146da444396ea8d86448`、既存 fig11 の provenance が記録する生成器と同一) の `main` を、repo 外の wrapper 経由で R2 の入力に対して呼んだ。
  出力後に生成器の `validate_external_sources` と `validate_repo_closure` を通した (`verbatim/draw-r2-fix1.log`、fix 前の初回は `verbatim/draw-r2.log`)。
  - `figures/fig11_r2_a6_certification.png` (sha256 `7cf4e1a71e82be2c387fb9d1dcb72dbcff9c561a19d5d000ac5af1611d676918`)
  - `figures/fig11_r2_a6_certification.provenance.json` (sha256 `ab38131624ee54a473a12b21441400ca6a03de0993b78937bfe44a2ba7cb6f3e`)。入力の sha256、cell・標本・正しさ、描いた点列 (`artist_series`)、caption、再現コマンド (`reproduction`、wrapper の呼び出し) を持つ。
  - 原本 (PNG・PDF・provenance・表) は repo 外 `/work/1/SFC/tanab/izanagi-measurements/t2853-r2-fig11-20260929/figure/` にある。PDF は `77bd83d7…`。insight の写しは原本と bytes 一致。段 6 の fix 前の出力は同 dir の `superseded-v1/` に残した (PNG は fix の前後で bytes 一致)。
- 図の見た目: 上段は各 cell の 5 標本・中央値の横棒・平均と CI、灰色の破線が stock 中央値 (効果の分母) で、fixed 2 µs 側に −5.2144% と出る。下段は代表反復の abort rate (stock 0.155、fixed 2 µs 0.145) の記述値。
- 原 fig11 (`docs/paper-story/figures/`) は変えていない。R2 の図は論文図ではなく、再現パッケージの記録である。

### 5.1 wrapper (repo 外の使い捨て)

- 段 5 の Codex 実装子が書き、repo には入れていない。保管先は `/work/1/SFC/tanab/izanagi-measurements/t2853-r2-fig11-20260929/tools/t2853_r2_fig11_plot.py` (sha256 `f8582b5090e9958d344a4347363c228aa6507cc10f376c68d553a703137d31b1`、段 6 の fix 後。fix 前の `1f94ca5d…` は同 dir の `superseded-v1/`)。
  生成器の sha256 が上の値と違えば描かずに止まる。実装子の報告は `verbatim/s5-author.md`、fix 子の報告は `verbatim/s6-fix1.md`。
  再現コマンドは provenance の `reproduction` にある。記録された `--generator` の path は本 wave の worktree で、撤去後は生成器の sha256 が `aac63659…` の任意の checkout に読み替える。
- **差し替えたもの (R2 の描画だけ):** caption の地位・役割語の 4 箇所 (各 1 回の出現を assert、外れたら描かない)。
  1. 「A-6 formal certification attempt …」→「A-6 R2 reproduction-package attempt labelled a6-r2-20260929a (…; separate from original a6-20260908b)」
  2. 「This is one attempt of five samples per cell;」→「This R2 reproduction-package attempt has five samples per cell;」
  3. 「(limitations (i) to (v) of the results note)」→ 元 attempt の結果稿の限定であることと本 insight の path を明記
  4. B-10 read-heavy の「historical concordance」の文 → 元 attempt の結果稿の記述であることを明記
  同じ差し替えを provenance の閉包検査 (caption の再計算) にも wrapper 内で適用し、`reproduction` を wrapper の実際の呼び出しにした。
- **差し替えていないもの:** 測定値の受理条件 (hash 照合・WAL / raw / certification の一致・5 標本・正しさ・source binding・condition receipt)、レイアウト検査、数値と 5 標本・中央値・効果・CI・正しさの別走・一般化の限定の説明文。
- **hash の固定。** R2 の certification / raw-manifest の sha256 は生成器の固定表に無い。wrapper は §3 の値 (`0a6008d1…`・`7799a064…`) を定数として持ち、それを期待値として生成器に渡す。入力の bytes が違えば生成器の既存の hash 検査が拒否し、図は作られない
  (fix 子の実走: 元 attempt の入力を R2 として渡すと `certification canonical SHA-256 mismatch` で rc 2・図なし)。初版の wrapper は入力 file 自身から計算した値を渡しており、hash 照合が自己照合になっていた (段 6 A-F1、§9)。
  この定数は collect 後の bytes を本 insight の記録へ束縛するもので、生成器の固定表の canonical pin ではない。R2 の provenance はこの 2 入力の `authority_scope` を「post-collect bytes pinned by wrapper constants recorded in the R2 insight; not a canonical pin of the generator's table」と記録する。
  R2 の受理の根拠は driver の receipt chain (submission → completion → acquisition → collect) と生成器の照合である。
- **陽性対照:** 同じ wrapper で元 attempt を原 metadata のまま (caption 差し替えなし・固定 hash 表) 描き、出力 provenance の `artist_series` が既存 fig11 の provenance と完全一致した (親の実行、`verbatim/draw-r2-fix1.log` の control 行。実装子・fix 子も同じ確認をした)。
  負例は新しく作っていない (段 4 裁定)。

## 6. 費用

- 測定: 1 request × 5 node × Elapse 1,061 s = 5,305 s = **1.47 node 時間** ((a) Elapse、`verbatim/elapse.log`)。見積り (5 × 1,057 s = 1.47) とほぼ一致し、投げ直しは無い。
- 開発の検査 (D2219 項 1 と同じ線で数える): 受入全走 1 回 (2026-09-29 16:10〜16:25 JST、child-green、28,065 passed・74 skipped) は 3 shard × 1 node で Elapse 329・314・299 s = 942 s = **0.26 node 時間** (NQSV 会計、request 35518・35516・35517)。
  このほか commit 後の全史 provenance 監査 1 回が計算ノード 1 本 (request 35341) で走ったが、会計の Elapse は log に残っておらず採取していない。
- 受入 2 回目: 1 回目の後に記録の commit を積み、さらに main (fig6 wave の着地後) の取り込みで docs/phase3.md が競合したため、land の条件 (landing tip = tested tip、取り込みは競合ゼロの自動 merge だけ) を満たすよう、和集合で解いた merge の tip で受入を取り直す。
  見積りは 1 回目と同じ約 0.26 node 時間。実測は tested tip の中に書けないので、受領証と shard の会計に残る。
- 合計: 測定 1.47 + 受入 1 回目 0.26 (実測) + 受入 2 回目 約 0.26 (見積り) ≈ **2.0 node 時間**に、全史監査 1 回の計算ノード分 (未採取) が乗る。D2212 項 4 の線 (2 node 時間) を越える見込みなので、受入 2 回目はユーザーの確認を得てから投げる (確認前には投げない)。
  投入前の判定に使った 1.72 (本走 1.47 + 受入 0.25) は見積りで、受入を 1 回で済ませる前提だった。
- plan・相談・実装子の Codex 子 3 本 (各 receipt は wave の作業置き場)。collect・描画・表は login で数秒ずつ。

## 7. 言わないこと

- **R2 は元 attempt の置換でも、A-6 の attempt 系列への追加でもない** (§0)。2 つの outer status・効果・標本を合成しない。「2 回とも reject だった」を統合判定や再現精度として読まない。
- R2 は現行 driver・5 node・pin `6810666` の測定であり、元 attempt (1 node・pin `511c953`) と同じ build・同じ環境の再実行ではない。値の差を build・pin・node 形・日時のどれかに帰属させない。
- outer status `reject` は protocol の中央値比較の答えであり、有意差・between-run floor 超の退行・研究の成否・read-heavy で stock が最良であることを判定しない。性能は認証していない。他の read 比率・機体・pin・protocol へ外挿しない。
- 計算ノードの割当ては専有の保証ではない。単独性は job body の既存の測定前 probe に拠る。
- trace は保全していない (§0 項 10)。R1 (保存 trace の再判定) の入力にならない。

## 8. 出所

- `verbatim/request.md` — 依頼の逐語。`verbatim/startup-gate.log` — 開始 gate (rc 0)。`verbatim/s1-brief.md` — 段 1 brief。
- `verbatim/s2-plan.md` — 段 2 プラン (Codex、read-only)。`verbatim/s3-consult.md` — 段 3 敵対相談 (2 レンズを 1 本で、Codex、read-only)。`verbatim/s4-ruling.md` — 段 4 裁定。
- `verbatim/precheck-patch.log` — 投入前の patch の厳密 check。`verbatim/hydrate.log` — third-party の hydrate。
- `verbatim/submit.log` — 投入。`verbatim/elapse.log` — NQSV 会計。`verbatim/finish-group.log`・`verbatim/collect.log` — 完走後の receipt と collect。
- `verbatim/s5-author.md` — wrapper の実装子の報告。`verbatim/draw-r2.log` — 陽性対照・R2 描画・表の親の初回実行 (fix 前)。
- `verbatim/s6-review-a.md`・`verbatim/s6-review-b.md` — 段 6 の敵対レビュー 2 本 (Codex、read-only)。`verbatim/s6-fix1.md` — fix 子の報告。`verbatim/draw-r2-fix1.log` — fix 後の親の実行 (最終の図と表)。`verbatim/s6-focus.md` — 焦点再レビュー。
- repo 外: attempt root `/work/1/SFC/tanab/izanagi-measurements/dev-wave-paper-story-a6-cert-20260902/a6-r2-20260929a/`、出力親 `/work/1/SFC/tanab/izanagi-measurements/t2853-r2-fig11-20260929/` (collect-root・figure・tools・thirdparty-src)。
  submit-tree は一時置き場 `/work/1/SFC/tanab/tmp/t2853-r2-fig11-20260929/submit-tree` (wave の終わりに撤去)。

## 9. 段 6 レビュー

commit `b97a27e90` を対象に、Codex の read-only レビューを 2 本並列で行った (`verbatim/s6-review-a.md`・`verbatim/s6-review-b.md`、どちらも受理検査 rc 0)。

- **A (一次資料との照合・正しさ境界): NO-GO (must-fix 1・should-fix 1)。** 数値と判定の食い違いは 0 件。レビュー子は NQSV 会計・driver_rc・finish-group / collect、R2 と元 attempt の 5 標本から中央値・平均・95% CI・効果を再計算して一致を確かめ、
  R2 の両 cell の正しさ 6 走がすべて pass・serializable・trace 有効、性能標本が trace 無効であること、collect 成果物・provenance・図と表の sha256、§0 の commit (15:12:21) が投入 (15:16:53) より前であること、
  `git diff 035fc11fa..HEAD` で元 attempt の tracked 成果物・結果稿・既存 fig11 が不変であることを確かめた。
- **B (過剰・削除): GO (should-fix 2・nit 1)。** 依頼範囲外の gate・台帳・一般化は無し、fig6 との分離と trace 保全口を使えない理由は insight から追える、とした。

| ID | 所見 | 判定 | 処置 |
|---|---|---|---|
| A-F1 | wrapper が R2 入力 file 自身から計算した sha256 を期待値として渡し、hash 照合が自己照合になっている | real (must-fix) | fix 子 1 回目が R2 の 2 つの sha256 を wrapper の定数に固定した。元 attempt の入力を R2 として渡すと生成器が拒否し図を作らないことを確かめた。親が R2 実データで描き直した (PNG は bytes 不変。provenance で変わったのは tracked 入力の `authority_scope`・生成時刻・出力 hash の欄で、caption・`artist_series`・`reproduction` は同一。PDF の hash は変わった) |
| A-F2 / B-F1 | 表の R2 の node 欄が「receipt unknown」 | real (should-fix) | 同じ fix で、Execution Hosts の同じ行に並ぶ複数 host を数えるようにした。表は「policy 5; receipt 5」、元 attempt は「policy 1; receipt 1」のまま |
| B-F2 | 費用の 1.72 に受入の見積りが混ざり、全 job の実測合計と読める | real (should-fix) | 受入の実測後に §6 へ実測値 (受入 1 回目 0.26) を書き、投入前の見積り 1.72 と分けた。受入 2 回目の経緯と見積りも §6 に書いた |
| B-F3 | 地位・非合成・限定の記述が重なり本題が埋もれる | real (nit) | §0 は投入前に固定した節なので変えない。冒頭の「結論」から主要結果へ直接たどれるので、このまま受け入れる |

変異 matrix は、repo の実装面の差分が 0 (wrapper は repo 外、repo の変更は insight・phase 行・worklog fragment だけ) のため段 4 裁定どおり免除した。

焦点再レビュー (Codex、read-only、commit `12cd17a2b` が対象、受理検査 rc 0、`verbatim/s6-focus.md`) は **GO**。A-F1・A-F2・B-F1 は closed、B-F2 は受入の実測待ちで partial、B-F3 は受容の判断で partial、回帰は無し。
レビュー子は wrapper の定数と collect 原本の sha256 の一致、allocation 記録の host 数 (R2 5・元 attempt 1)、fix 前後の PNG の bytes 一致を確かめた。
新規所見 1 件 (上の表の A-F1 の処置文が「再現コマンドが変わった」と書いていた) は real で、fix 前後の provenance を親が照合し (差は `generated_utc`・`outputs`・`tracked_inputs` の 3 key だけ)、処置文を訂正した。
