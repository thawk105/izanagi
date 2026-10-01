# [T-2853] R2 fig10 — B-7 (fixed 5 µs × 3 workload) を現行の certification driver・現行 policy (5 node)・現行 CCBench pin で Pegasus に測り直す

`authority: none` / `default_effect: no-state-change`

- 作成: 2026-10-01 JST。wave `t2853-r2-fig10` (背景 job、branch `worktree-t2853-r2-fig10`)、着手時の基準 = local main `5f9e8c549`、投入 checkout = local main `db710338d`。
- 前段: `output/insights/2026-09-27/t2853-repro-rest/README.md` §3.3 (投入単位 = 図 1 本、fig10 = B-7 fixed 5 µs × 3 workload、5 node、3.40 node 時間)、
  `output/insights/2026-09-23/t2853-figure-rerun-plan/README.md` (fig10 の経路)、先例 `output/insights/2026-09-29/t2853-r2-fig11/README.md`・`output/insights/2026-09-29/t2853-r2-fig6/README.md`。
- 計算の承認: D2305 項 9 (ユーザー裁定、fig10 の 3.40 node 時間を承認、1 図 1 タスク)。
- 原 attempt: `b7f5-20260919a` (tracked 成果物 `output/insights/2026-09-19_t1998-b7-fixed5-three-workload/`、結果稿 `docs/paper-story/results/2026-09-19-b7-fixed5-three-workload-regression.md`、
  図 `docs/paper-story/figures/fig10_b7_fixed5_three_workload_regression.*`)。

## 0. R2 attempt の地位 — 結果より前に固定する (投入前に commit)

**この節は R2 の job を投入する前に書き、commit してから投入する。** 以後この節は書き換えない (訂正は追記で行う)。

1. **地位。** attempt `b7f5-r2-20261001a` は、B-7 の測定設計 (policy `orchestrator/campaign/paper_story_b7_fixed5_regression.v2.json`、sha256 `c6b24050…`、study `paper-story-b7-fixed5-regression`、
   3 workload rr5 (write-heavy)・rr50 (balanced)・rr95 (read-heavy) の各々で stock (`BACK_OFF=0`, `BACKOFF_FIXED=-1`) 対 fixed 5 µs (`BACK_OFF=1`, `BACKOFF_FIXED=5`)、
   48 thread・1,000,000 record・Zipf 0.9・read-modify-write 無効・max operations 10・3 秒・各 cell 5 標本の中央値比較、正しさは legacy 1 + performance 5) を、
   固定 genome・LLM なしで 1 回測り直す**再現パッケージの試行**である。原 attempt `b7f5-20260919a` の置換・追認・反復ではない。
2. **形。** 現行 repo の driver `tools/pegasus/submit_paper_story_a2_certification.sh` を、local main `db710338d` の detached checkout から現行 policy (`scheduler.nodes = 5`、gen_S、walltime 12:00:00) で投げる。
   driver は workload ごとに 1 request を出す (3 request × 5 node、job 名 `paper-b7-fixed5`)。driver・job body・policy・生成器は変えない。
3. **原 attempt と条件が違う点 (結果の前に列挙する)。** 原 attempt は izanagi source `c18a80967`・CCBench pin `511c953`・5 node × 3 request (2026-09-19) で走った。
   R2 は source `db710338d`・CCBench pin `6810666` で走る。`511c953..6810666` の CCBench 差分は `cc/mocc/transaction.cc` だけで、silo の source と adopted cell に当てる
   `patches/silo-backoff-fixed.patch` の対象 (`cmake/Options.cmake`・`include/backoff.hh`) は同じだが、R2 は原 attempt と同じ build・同じ node・同じ日時ではない。
   これらの差は R2 を「同一条件の再走」と呼ばない理由として書き、差の効果は推定しない。
4. **合成しない。** 原 attempt と R2 の標本・中央値・効果・床値判定・outer status を互いに合成しない。統合 verdict、プール推定、attempt をまたぐ有意水準の保証を作らない。
   数値の近さ・符号の一致・判定の一致を再現精度として評価しない。
5. **attempt 数と停止基準。** attempt 数は 1。停止基準は「この 1 attempt (3 request) の結果を、outer status が `certified` でも `reject` でも、indeterminate でも、一部 request だけの完走でも、未完走でも、そのまま報告する」。
   起動時の検査で測定前に落ちた request (campaign の build・bench が 1 つも始まっていないもの) に限り、原因が driver・policy・依存元の変更を要しないなら、新しい attempt id で同じ形のまま 1 回だけ投げ直してよい。
   落ちた request ID・attempt id・理由は記録し、取り下げない。測定が始まった後の失敗は投げ直さず、その結果を報告する。
   **費用の条件:** 本走の見積りは原 attempt の NQSV 会計 Elapse (386 + 841 + 1,218 s) × 5 node = **3.40 node 時間** (承認量と同じ)。受入 1 回の見積りは約 0.26。
   測定前に落ちた request の Elapse × 5 node を実費として足し、投げ直した後の見込み (実費 + 3.40) が承認量 3.40 を大きく超える (1.2 倍の 4.08 を超える) ときは、投げ直す前に land 調整役へ示し直す。
6. **正しさ。** 正しさは job 内の trace 有効 build の別走で判定し (規律 1)、anomaly が出た cell は即 reject とする (規律 2)。性能は trace 無効 build で測る。
   検査を緩めて描く・記録することはしない。
7. **床値判定の規則 (結果より前に固定)。** R2 の各 workload の床値判定は、原 attempt・生成器と同じ規則「効果 (adopted 中央値 / stock 中央値 − 1) < −floor (厳密) なら regression、そうでなければ no-regression」で、
   floor は生成器が pin する同じ 3 file `output/env/pegasus/calibration/between_run_noise_t48_skew0p9_{rr5,rr50,rr95}_rmw0.json` (sha256 `25b4d2a0…`・`a94dc83e…`・`23c024e4…`) の `between_run.cv` とする。
   R2 には結果稿が無いので、親が collect 後に R2 の `certification.json` の `effects` と上の floor から生成器とは別の計算で判定を出して本 insight に記録し、それを描画時の「記録された判定」とする。
   床値判定は有意差の判定ではなく、床値の測定 (2026-09 上旬、別 binary・別 node) と R2 の同一性は設定上のものである (原 attempt の結果稿と同じ限定)。
8. **図と表。** 原 fig10 と同じ生成器 `tools/plotting/plot_b7_fixed5_regression.py` (sha256 `f78da66d…`、bytes 不変) を repo 外の wrapper から呼んで R2 の図を描き、原 attempt と R2 を同じ生成器の読み込み関数 `load_evidence` (全検査つき) で
   attempt ごとに別々に読んだ対照表を並べる。wrapper が差し替えてよいのは、R2 の入力を指す識別子 (attempt id・certification / raw-manifest の sha256。sha256 は collect 後の bytes を本 insight に記録した定数とし、入力から自己計算しない)、
   項 7 の「記録された判定」、caption の地位・役割語だけで、測定値の受理条件 (hash 照合・schema・study・cell・5 標本・正しさ・source binding・trace 無効の性能標本) とレイアウト検査は変えない。
   生成器が R2 の入力を検査で拒否した場合は検査を外して描かず、拒否理由と得られた値を表で記す。
9. **原成果物は不変。** 原 attempt の tracked 成果物・結果稿・既存 fig10 は凍結物のまま保持し、R2 の結果で書き換えない (規律 7)。R2 の `collect` は repo 外の空 dir を `--repo-root` にして materialize し、
   policy の `tracked_destination` (原 attempt の tracked leaf) へは書かない。
10. **主張の範囲を増やさない。** outer status は protocol の 3 workload の連言の答えであって、有意差・研究の成否・B-7 の充足判定 (D2044 項 3) を判定しない。性能は認証しない。
    R2 の値を他の機体・pin・protocol・採用値へ外挿しない。
11. **trace 保全口 (D2233) は使わない。** driver の `qsub -v` は job へ渡す環境変数を固定で列挙し、`IZANAGI_TRACE_ARCHIVE_ROOT` を渡す口が無い。driver は変えないので、R2 の trace は保全されず R1 (保存 trace の再判定) の入力にならない。
12. **待ち行列の扱い。** 投入の直前に `qstat` を見て、生成器対照の本走 (job 名 `izs4loop` 系) に待ち (QUE) があれば、投入後に本 wave の request の優先度を `qalter -p` で下げる (本走を追い越さない)。

## 結論 (§0 の後に、結果を見てから書いた)

1. **fig10 の測定 (B-7、3 workload × stock 対 fixed 5 µs、各 5 標本) を、現行 repo の certification driver で Pegasus に 1 回投げて測り直した。** attempt `b7f5-r2-20261001a`、3 request
   (`40685` rr5・`40686` rr50・`40687` rr95、各 5 node、2026-10-01 10:30〜10:56 JST) はすべて完走し (driver_rc 0)、finish-group と collect も終了コード 0 だった。投げ直しは無い (§2)。
   計測に使った CCBench pin は **`6810666`** (投入 checkout の gitlink、`compute-result.json` の `current_pin`)。投入後の 10:54 に main の pin は `25898d00` へ変わったが、R2 には関係しない。
2. **R2 の outer status は `reject`、効果 (adopted 中央値 / stock 中央値 − 1) は rr5 +62.3973%・rr50 +13.9000%・rr95 −11.4495%。** 床値判定 (§0 項 7 の規則) は rr5・rr50 が no-regression、rr95 が regression。
   6 cell すべて正しさ `certified` (legacy 1・performance 5、trace 有効の別走)、source binding `bound` (§3)。原 attempt (`reject`、+67.8968%・+12.6717%・−11.3787%、判定も同じ並び) と並べるが、§0 項 4 のとおり合成せず、近さ・一致を再現精度として評価しない。
3. **原 fig10 と同じ生成器 (bytes 不変) で R2 の図を描いた。** 生成器の受理検査・閉包検査・レイアウト検査はすべて通った。repo 外の wrapper が差し替えたのは §0 項 8 の範囲 (attempt id・入力の所在と期待 hash・記録された判定・caption の地位語 3 箇所) だけである (§5)。
   同じ wrapper で原 attempt を原 metadata のまま描くと、既存 fig10 の provenance と `artist_series` が完全一致した (陽性対照)。
4. **原 attempt と R2 を並べた表**を、同じ生成器の `load_evidence` (全検査つき) を attempt ごとに別々に呼んで作った (§4)。
5. **計算は承認量 3.40 node 時間の約 1.9 倍の 6.39 node 時間を使った。** 原因は、全 node 共有の bench lock で R2 自身の 3 job の性能検証と bench が 1 列に並んだことだと、WAL の時刻から推定する (§7、PID では未確認)。途中で land 調整役へ示し、診断の後に継続の承認を得た (§6)。
   lock 取得後・bench 開始前の既存の競合 probe は競合を検出せず (待ちの間を連続して監視したものではない)、bench の追加 round も無く、bench 本体の所要は原 attempt と同程度だった (性能への影響が皆無だとは主張しない)。

## 1. 経路と投入前の前提

- **投入 checkout。** local main `db710338d` の detached worktree `/work/1/SFC/tanab/tmp/t2853-r2-fig10-20261001/submit-tree` (submodule 再帰初期化、CCBench `68106660`) から投げた。
  job が照合する HEAD と repo root が wave の branch の進みで動かないようにするためである。投入直前に untracked を含めて clean (`verbatim/precheck-patch.log` の `submit_tree_dirty_incl_untracked=0`)。
- **依存元。** `--dependency-prefix-source /work/1/SFC/tanab/izanagi-a2-deps`。third-party は永続 cache から `tools/pegasus/fetch_third_party.py hydrate` で repo 外の新 staging
  `/work/1/SFC/tanab/izanagi-measurements/t2853-r2-fig10-20261001/thirdparty-src` を作って渡した。5 本とも head = policy pin (`verbatim/hydrate.log`)。
- **patch の事前確認。** login で driver と同じ素の `git apply --check` により、静的 backoff patch が pin `6810666` の木へ当たることを確かめた (`verbatim/precheck-patch.log`、rc 0)。condition gate・実 compiler・兄弟 node への検証 fanout は job 自身の測定前検査に任せた (通った)。
- **待ち行列。** 投入直前 (10:29) の `qstat` に `izs4loop` 系の request は無く、`qalter -p` は使っていない (§0 項 12)。
- **collect の書き先。** collect は `<repo_root>/<tracked_destination>` へ materialize するので、`--repo-root` に repo 外の空 dir `/work/1/SFC/tanab/izanagi-measurements/t2853-r2-fig10-20261001/collect-root` を渡した。
  原 attempt の tracked leaf (`output/insights/2026-09-19_t1998-b7-fixed5-three-workload/`) は変えていない。collect は submission receipt が policy の絶対 path を束縛するので submit-tree の module から呼んだ。

## 2. 投入と完走

| workload | request | 確保 | host (allocation receipt) | 開始〜終了 (JST) | Elapse (s) | driver_rc |
|---|---|---|---|---|---|---|
| rr5 | `40685.nqsv` | 5 node | bnode034・069・073・079・080 | 10:30:34 〜 10:56:01 | 1,531 | 0 |
| rr50 | `40686.nqsv` | 5 node | bnode081〜085 | 10:30:55 〜 10:56:18 | 1,527 | 0 |
| rr95 | `40687.nqsv` | 5 node | bnode086〜090 | 10:30:59 〜 10:56:36 | 1,541 | 0 |

- 投入は 10:29:38〜10:30:07 (`verbatim/submit.log`)。会計は `verbatim/elapse.log` (各 job.stderr の NQSV 会計行の抜粋、Number of Jobs 5)。完了待ちは `tools/dev_wave_wait.py compute` で 3 本とも rc 0 (`verbatim/wait-compute.log`)。
- 起動時検査での失敗・投げ直しは無い。3 request は互いに別の 5 node で、同時刻に走っていた fig2c wave の `b10_back` request (bnode074・076・077) とも node は重ならない。
- finish-group (10:56:51、rc 0) が completion と acquisition の receipt を作り、collect (10:56:55、rc 0) が collect-root に materialize した (`verbatim/finish-group.log`・`verbatim/collect.log`)。
- attempt root: `/work/1/SFC/tanab/izanagi-measurements/dev-wave-paper-story-b7-fixed5-20260919/b7f5-r2-20261001a/`。

## 3. R2 の certification — 本番 CLI の出力

collect-root の `output/insights/2026-09-19_t1998-b7-fixed5-three-workload/` (repo 外。名前は policy の `tracked_destination` をそのまま使ったもので、原 attempt の tracked leaf とは別の場所) に次が出た。

| 成果物 | sha256 |
|---|---|
| `certification.json` | `88a3a6bbd2eddecd95f715c00618612d676224811d0e53d15d3edd219284d2f0` |
| `raw-manifest.json` | `7918298a24d5124018b59ea8dd6c0a6bd67731209390ff351c4a73242a68ff8f` |
| `artifact-manifest.json` | `63caf0e97376ad1b39df59e04e2651bdda9575a9c185bf1c1e52be0a0fae6937` |
| `COMPLETE.json` | `13bd17714b5233e9ef24fc31d5f13fe87255c6df0d15bf5d0da1539e3fa5bfbe` |
| `acquisition-receipt.json` | `43fa51ea0d188005c40f03d04d5b9d8dfb1fc412ad00cbaee5cedb3fddd3627d` |
| `submission-receipt.json` | `f46b8d6a5cbf8d524cfa597a334af393c783f0c5c467f5ab90a18b29b81628ab` |
| `completion-receipt.json` | `d5dcba60c5410339597fcca0e064f32304dcfa96212ac538ebd69a21078596db` |
| `condition-gate-rr5.admissions.jsonl` | `33e6cc3b8a1e1d17dad156a700377ea1294c7d344b0dede4ba82cbbbce5a529a` |
| `condition-gate-rr50.admissions.jsonl` | `689da44f9a655b1de1f2fc6261bae3abca9eefc6a9cd80d1f245488e8b78ab99` |
| `condition-gate-rr95.admissions.jsonl` | `35154dfc51249859dd22eb2d768ed385e18eddb5255a15c4b9ca4cc4cc1fed1a` |

- `certification.json`: study `paper-story-b7-fixed5-regression`、attempt `b7f5-r2-20261001a`、**status `reject`**、`a4_noise_floor_status` `open`、
  `effects` = rr5 0.6239734604583511・rr50 0.1389998460596873・rr95 −0.11449452408913763、`current_pin` `6810666`、`source_commit` `db710338dd443d30a5b7c06da2e2a06afb092175`、
  protocol SHA-256 `5653d439…` (原 attempt と同じ。preimage は pin を含まない)、policy SHA-256 `c6b24050…`。
- 6 cell とも `correctness.status = certified` (disposition・legacy・performance がすべて pass)、`source_binding_status = bound`、`performance.status = complete`。
  正しさは job 内の trace 有効 build の別走、性能は trace 無効 build (job body の既存経路、規律 1)。生成器の読み込み検査 (raw の verdict が全行 serializable、trace 有効、trace binary 一致) も通った。
- **床値判定 (§0 項 7)。** 親が jq で、生成器とは別に計算した (10:57 JST)。floor は pin された 3 file の `between_run.cv`。

  | workload | 効果 | −floor | 判定 |
  |---|---|---|---|
  | rr5 | +0.6239734604583511 | −0.009536033056996148 | no-regression |
  | rr50 | +0.1389998460596873 | −0.00725042525457718 | no-regression |
  | rr95 | −0.11449452408913763 | −0.0022283754708938273 | regression |

  この判定と collect 後の 2 file の sha256 を `r2-record.json` (sha256 `0a060c638d6bd84d4f85ef1f498a42841e79220b58f66d4763ba121e84f2d72b`) に記録し、描画時の期待値にした。生成器自身の判定計算はこれと一致した (一致しなければ生成器が `judgment mismatch` で拒否する)。

## 4. 原 attempt と R2 の対照表

同じ生成器の `load_evidence` (全検査つき) を、原 attempt は生成器の固定 hash 表で、R2 は `r2-record.json` の hash で別々に呼んで書いた表である (`figures/fig10_comparison.md`、sha256 `150b13468309f5caa8efc7e90071e6eb80d33c292dc0b6c0defdb62ad46c207f`、段 6 の fix 後。fix 前の `0f0a06e4…` とは scope 文書の path と再現コマンドの 2 行だけが違う)。
値は attempt ごとに計算し、合成・差・比を作っていない。

| attempt | workload | request | source commit | CCBench pin | 確保 node (policy; receipt) | 効果 | 床値判定 | outer status |
|---|---|---|---|---|---|---|---|---|
| 原 `b7f5-20260919a` | rr5 | `10807.nqsv` | `c18a80967` | `511c953` | 5; 5 | +0.6789675418265144 | no-regression | reject |
| 原 | rr50 | `10808.nqsv` | `c18a80967` | `511c953` | 5; 5 | +0.12671651401806727 | no-regression | reject |
| 原 | rr95 | `10809.nqsv` | `c18a80967` | `511c953` | 5; 5 | −0.11378696258180376 | regression | reject |
| R2 `b7f5-r2-20261001a` | rr5 | `40685.nqsv` | `db710338d` | `6810666` | 5; 5 | +0.6239734604583511 | no-regression | reject |
| R2 | rr50 | `40686.nqsv` | `db710338d` | `6810666` | 5; 5 | +0.1389998460596873 | no-regression | reject |
| R2 | rr95 | `40687.nqsv` | `db710338d` | `6810666` | 5; 5 | −0.11449452408913763 | regression | reject |

| attempt | cell | trace 無効性能 5 標本 (tps) | 中央値 | 平均 ± t 95% CI 半幅 (自由度 4) | 正しさ |
|---|---|---|---|---|---|
| 原 | rr5-stock | 2328992, 2423324, 2354846, 2347564, 2371395 | 2354846 | 2365224.2 ± 44535.9 | certified |
| 原 | rr5-fixed5 | 4049702, 3954525, 3731893, 3942414, 3953710 | 3953710 | 3926448.8 ± 145372.3 | certified |
| 原 | rr50-stock | 4135929, 3769412, 3813768, 3878461, 3832768 | 3832768 | 3886067.6 ± 180111.0 | certified |
| 原 | rr50-fixed5 | 4378198, 4318443, 4308209, 4333385, 4306001 | 4318443 | 4328847.2 ± 36793.0 | certified |
| 原 | rr95-stock | 10680928, 10171152, 10334445, 10334945, 10351729 | 10334945 | 10374639.8 ± 231409.6 | certified |
| 原 | rr95-fixed5 | 9282678, 9137295, 9158963, 9119021, 9190899 | 9158963 | 9177771.2 ± 80040.2 | certified |
| R2 | rr5-stock | 2688859, 2541285, 2521822, 2516911, 2496722 | 2521822 | 2553119.8 ± 96252.1 | certified |
| R2 | rr5-fixed5 | 4207721, 4152503, 4095372, 4068650, 4066885 | 4095372 | 4118226.2 ± 75528.1 | certified |
| R2 | rr50-stock | 4006501, 3754702, 3622265, 3743909, 3755777 | 3754702 | 3776630.8 ± 174116.1 | certified |
| R2 | rr50-fixed5 | 4396895, 4248262, 4276605, 4301120, 4271456 | 4276605 | 4298867.6 ± 71926.5 | certified |
| R2 | rr95-stock | 10550235, 10287147, 10031996, 10253434, 10287587 | 10287147 | 10282079.8 ± 228383.2 | certified |
| R2 | rr95-fixed5 | 9348620, 9133531, 9093970, 9109325, 9040000 | 9109325 | 9145089.2 ± 147562.7 | certified |

- 確保 node は「policy の `scheduler.nodes`; reservation に束縛された allocation qstat の Execution Hosts の数」。host 名は `figures/fig10_comparison.md` にある。
- CI は標本の記述であって、効果・中央値・床値判定の区間ではない。有意差の判定はしない。生成器は代表反復の abort rate と anomaly の件数を返さないので、表には載せていない (再構成しない)。

## 5. 図 — 原 fig10 と同じ生成器で描いた R2 の図

- **描けた。** 生成器 `tools/plotting/plot_b7_fixed5_regression.py` (sha256 `f78da66d…`、既存 fig10 の provenance が記録する生成器と同一、描画の前後で不変) を repo 外の wrapper から R2 の入力に対して呼んだ。
  出力後に生成器の `validate_external_sources` と `validate_repo_closure` を通した (`verbatim/draw-r2-fix1.log`、段 6 の fix 前の初回は `verbatim/draw-r2.log`)。
  - `figures/fig10_r2_b7_fixed5_three_workload.png` (sha256 `b91335719138c2acedba2b1c691c0b0f9ab5b84eb818e3671d328d93b8ffa51e`)
  - `figures/fig10_r2_b7_fixed5_three_workload.provenance.json` (sha256 `f54adb4802bc2df63a3effb9f53d75855878acb9aecd564cee011c85d0619353`、段 6 の fix 後。fix 前は `83c67065…`)。入力の sha256、cell・標本・正しさ、描いた点列 (`artist_series`)、caption、再現コマンド (`reproduction`) を持つ。
  - 原本 (PNG・PDF・provenance・表) は repo 外 `/work/1/SFC/tanab/izanagi-measurements/t2853-r2-fig10-20261001/figure/` にある。PDF は `0c9fc8f9…` (fix 前 `398e2967…`)。insight の写しは原本と bytes 一致。PNG は段 6 の fix の前後で bytes 一致 (caption は画像に描かれない)。fix 前の出力は `figure-superseded-v1/` に残した。
- 図の見た目: 上段は 3 workload の各 cell の 5 標本・中央値・平均と CI、灰色の破線が stock 中央値。下段は効果 (+62.3973%・+13.9000%・−11.4495%) と −floor の破線、判定ラベル (rr95 だけ「regression (below -floor)」)。
- 原 fig10 (`docs/paper-story/figures/`) は変えていない。R2 の図は論文図ではなく、再現パッケージの記録である。

### 5.1 wrapper (repo 外の使い捨て)

- 段 5 の Codex 実装子が書き、repo には入れていない。保管先 `/work/1/SFC/tanab/izanagi-measurements/t2853-r2-fig10-20261001/tools/t2853_r2_fig10_plot.py` (sha256 `a1a1c3ad597d26d8f5d9b4099d64f069035b2083f9eeae59baa2258d61c8e629`、段 6 の fix 後。fix 前の `4674508a…` は同 dir の `superseded-v1/`)。
  生成器の sha256 が上の値と違えば描かずに止まる。実装子の報告は `verbatim/s5-author.md`、fix 子の報告は `verbatim/s6-fix1.md`。
- **差し替えたもの (R2 の描画だけ、§0 項 8 の範囲):** 生成器の `ATTEMPT_ID` (record の値)、certification / raw-manifest の所在 (collect-root の絶対 path。provenance の `tracked_inputs` に `repo_tracked_leaf: false` と実の所在を記録) と期待 hash (record の値、wrapper は入力から自己計算しない)、
  `RECORDED_JUDGMENT` (record の値、wrapper は判定を計算しない)、caption の地位・役割語の 3 箇所 (各 1 回の出現を assert、外れたら描かない。逐語は `verbatim/s6-fix1.md` の表)。初版は 4 箇所で、outer status の説明を原 attempt に帰属させる置換が R2 の status の意味を弱めていたため、段 6 で外した (§10)。同じ差し替えを provenance の閉包検査にも wrapper 内で適用した。
- **差し替えていないもの:** 測定値の受理条件 (hash 照合・schema・study・cell の順と identity・5 標本・正しさ・source binding・trace 無効の性能標本・raw と certification の一致・floor の条件)、レイアウト検査、数値と説明文。
- **provenance が束縛する文書。** caption の source は `r2-record.json` (sha256 `0a060c63…`、絶対 path は wave worktree のもので、撤去後は repo 相対 `output/insights/2026-10-01/t2853-r2-fig10/r2-record.json` に読み替える)。
  R2 の地位・規則の文書として束縛するのは `verbatim/s0-snapshot.md` (sha256 `70c11b46…`) である。これは §0 だけの版 (commit `e92aeea8f`) の README の bytes そのもので、以後変えない。
  本 README は追記で hash が変わるので、閉包の再検査が現行の木で成り立つよう、段 6 で snapshot を参照する形に描き直した (§10)。
- **陽性対照:** 同じ wrapper で原 attempt を原 metadata のまま (caption 差し替えなし・固定 hash 表・生成器の RECORDED_JUDGMENT) 描き、`artist_series` が既存 fig10 の provenance と完全一致した (親の実行、`verbatim/draw-r2.log` の control 行)。
- **負例:** 実装子が 1 件だけ実走した。見立て record の certification hash を 1 文字変えると生成器が `SHA-256 mismatch` で拒否し、図を作らない (rc 2)。

## 6. 費用

- 測定: 5 node × (1,531 + 1,527 + 1,541) s = 22,995 node 秒 = **6.39 node 時間** ((a) Elapse、`verbatim/elapse.log`)。承認量 3.40 の約 1.9 倍。投げ直しは無い。
- 経緯: 10:49 に経過が元 attempt の Elapse を大きく超えたので、land 調整役へ超過見込みを示した。診断の依頼を受け、10:53 に「stock cell の bench は 3 本とも完了済みで計測は進んでいる」と返し、見込み約 6.7 node 時間で継続の承認を得た。原因は §7。
- 開発の検査 (受入全走など) の実測は記録後に別途数える (本節には未記入、受領証と shard の会計に残る)。
- Codex 子 4 本 (段 5 実装子、段 6 の read-only レビュー 2 本、fix 子 1 本)、Claude の調査子 1 本 (read-only、§7 の初期調査)。collect・描画・表は login で数秒ずつ。

## 7. 見積りが外れた原因 (推定) — 全 node 共有の bench lock で 3 job が 1 列に並んだ

- **見積りの前提。** 3.40 は原 attempt の 3 request の Elapse (386・841・1,218 s) の和 × 5 node。原 attempt の 3 request は待ち行列の待ちでずれて始まり、rr5 (22:36〜22:42) は単独、
  rr95 (22:49〜23:09) と rr50 (22:59〜23:13) は約 10 分だけ重なった (結果稿の request 表)。重なった区間では原 attempt にも同じ形の待ちが出ている (rr95 の cell 2 の 165 s。rr50 の stock bench は rr95 の bench 完了 23:09:18 の直後 23:09:18〜35 に走った)。
  R2 は 3 request が待ちなしで同時に始まり、2 巡とも 3 job の性能検証と bench が 1 列に並ぶ時刻になった (段の時刻からの読みで、全期間の連続観測ではない)。
- **何が起きたか (各 campaign の WAL の段の時刻だけを抽出、PID・node 上の process 状態は見ていない)。** bench 本体の所要は 16.8 s で原 attempt と同じだった。遅れたのは「最後の検証完了 → bench 開始」の空きである。

  | attempt | 空き (秒、cell 1 / cell 2) |
  |---|---|
  | R2 rr5 | 603.9 / 592.2 |
  | R2 rr50 | 478.5 / 464.7 |
  | R2 rr95 | 33.8 / 33.7 |
  | 原 rr5・rr50・rr95 | 0 / 0、16.9 / 0、0 / 165.3 |

  (bench_done までで数えると R2 の cell 1 は 621・496・51 s。land 調整役への途中報告はこの値だった。)
- **仕組み。** pipeline は bench を `bench_lock()` の中で回し、全規模の性能検証 (head の rep0 と兄弟 4 node への配布、その完了待ちまで) も同じ `bench_lock()` の中で回す (`orchestrator/campaign/pipeline.py` 1482 行と 2758〜2762 行、D36 決定 4-4)。
  lock の既定 path は `~/.izanagi/bench.lock` (`orchestrator/campaign/lock.py`) で、`/home` は全 node 共有の Lustre である。certification の job body (`tools/pegasus/paper_story_a2_certification.sh`) は `IZANAGI_BENCH_LOCK` を設定しないので、別 node の 3 job がこの 1 本の lock を取り合った。
  (`tools/pegasus/b10_backoff_grid.sh`・`p3_s4_loop_pegasus.sh`・`a5_second_boot_backoff_sweep.sh` は node ローカルの `$TMPDIR/bench.lock` を使っており、この形にはならない。)
- **lock の持ち主。** PID では確かめていない。ssh は鍵で拒否され、node 上の process 状態は見られなかった。ただし WAL の時刻は「R2 自身の 3 job が待ち始めた順に 1 本ずつ取った」1 列で説明できる。
  巡 1 では rr5 検証 (10:31:53〜10:33:23) → rr50 検証 (〜10:35:45) → rr95 検証 (〜10:43:27、約 7.7 分) → rr5 bench (10:43:27〜) → rr50 bench (10:43:44〜) → rr95 bench (10:44:01〜) と並んだ。巡 2 も同じ順だった。
  2 巡とも、rr5 の bench 開始は rr95 の検証完了と 0.1 秒以内で一致する。別 job が持っていた可能性は、この一致からは低いが排除はしていない。
- **測定への影響について観測したこと。** lock は izanagi の bench・全規模検証どうしの排他を強める向きに働く。bench 前の競合 probe は競合を検出しなかった。WAL の `bench_done` は 6 cell とも rounds 1、`bench_wall_s` は 16.8 s 前後で原 attempt と同程度だった。
  `settled` は各 workload の cell 1 が true・cell 2 が null で、原 attempt の 6 cell と同じ形。これらは通常の受理条件を満たしたという観測であって、待ちが性能値に影響しなかったことの証明ではない (lock は孤児化した子や他者が起動した ycsb を捕まえない。pipeline.py 2764 行の注記)。
- **次への案 (本 wave では実装しない。driver・job body の変更で範囲外)。**
  1. job body で `IZANAGI_BENCH_LOCK` を node ローカル (`$TMPDIR/bench.lock`) にすれば、3 job は互いを待たない。R2 の Elapse から WAL の空き (2 cell 分) を引いた試算では、
     rr5 1,531 − 1,196 ≈ 335 s、rr50 1,527 − 943 ≈ 584 s、rr95 1,541 − 67 ≈ 1,474 s、× 5 node で約 3.3 node 時間 (試算、未実測) になり、原 attempt の見積り 3.40 とほぼ同じになる。
     (初版はここに「約 2.2 node 時間」と書いていた。算式が合わず、段 6 で誤りとして直した。)
  2. 性能検証の rep1〜4 はすでに兄弟 4 node へ配られ、head の rep0 と並行に走っている (`pipeline.py` 2644〜2662 行)。律速は head の rep0 とその完了待ちで、rr95 では 1 cell 約 7.7 分になる。
     ユーザーの指示 (2026-09-30、計算 job は 1 本あたり 5 分を目安に分割し、多数を並行に投げる) に近づけるには、workload × cell 単位の別 job に割る形を検討し、無理ならその理由を書く。分け方は直す wave で設計する。
  land 調整役がこの 2 案を、直す dev-wave の投げ文に反映済みである (同調整役の連絡による。2.2 の誤りの訂正も伝え、差し替え済み)。

## 8. 言わないこと

- **R2 は原 attempt の置換でも、B-7 の attempt 系列への追加でもない** (§0)。2 つの outer status・効果・判定・標本を合成しない。「2 回とも reject で判定も同じ並びだった」を統合判定や再現精度として読まない。
- R2 は現行 driver・pin `6810666`・source `db710338d` の測定であり、原 attempt (pin `511c953`・source `c18a80967`) と同じ build・同じ node・同じ日時の再実行ではない。値の差を build・pin・node・日時のどれかに帰属させない。
- outer status `reject` は protocol の 3 workload の連言の答えであり、有意差・研究の成否・B-7 の充足 (D2044 項 3) を判定しない。床値判定は有意差の判定ではなく、床値の測定と R2 の同一性は設定上のものである。性能は認証していない。他の機体・pin・protocol へ外挿しない。
- 計算ノードの割当ては専有の保証ではない。単独性は job body の既存の測定前 probe に拠る。
- §7 の lock の持ち主は時刻からの推定で、PID では確かめていない。案 1・2 の node 時間は試算で、実測していない。
- trace は保全していない (§0 項 11)。R1 (保存 trace の再判定) の入力にならない。

## 9. 出所

- `verbatim/request.md` — 依頼の逐語。`verbatim/startup-gate.log` — 開始 gate (rc 0)。`verbatim/s1-brief.md` — 段 1 brief (軽量版。段 2・3 は省いた)。
- `verbatim/precheck-patch.log` — 投入前の patch の厳密 check。`verbatim/hydrate.log` — third-party の hydrate。
- `verbatim/submit.log` — 投入。`verbatim/wait-compute.log` — 完了待ち。`verbatim/elapse.log` — NQSV 会計。`verbatim/finish-group.log`・`verbatim/collect.log` — 完走後の receipt と collect。
- `verbatim/lock-timeline.log` — §7 の根拠 (WAL の段・時刻・bench 所要・settled だけを jq で抽出したもの)。
- `verbatim/s5-author.md` — wrapper の実装子の報告。`verbatim/draw-r2.log` — 陽性対照・R2 描画・表の親の初回実行 (fix 前)。`verbatim/draw-r2-fix1.log` — fix 後の親の実行 (最終の図と表)。
- `verbatim/s4-ruling.md` — 段 4 裁定。`verbatim/s6-review-a.md`・`verbatim/s6-review-b.md` — 段 6 の敵対レビュー 2 本 (Codex、read-only)。`verbatim/s6-fix1.md` — fix 子の報告。`verbatim/s0-snapshot.md` — §0 だけの版の README の snapshot。`r2-record.json` — R2 の期待 hash と記録された判定。
- repo 外: attempt root `/work/1/SFC/tanab/izanagi-measurements/dev-wave-paper-story-b7-fixed5-20260919/b7f5-r2-20261001a/`、出力親 `/work/1/SFC/tanab/izanagi-measurements/t2853-r2-fig10-20261001/` (collect-root・figure・tools・thirdparty-src)。
  submit-tree は一時置き場 `/work/1/SFC/tanab/tmp/t2853-r2-fig10-20261001/submit-tree` (wave の終わりに撤去)。

## 10. 段 6 レビュー

commit `068f664dd` を対象に、Codex の read-only レビューを 2 本並列で行った (`verbatim/s6-review-a.md`・`verbatim/s6-review-b.md`、どちらも受理検査 rc 0)。

- **A (一次資料との照合・正しさ境界): NO-GO (must-fix 2・should-fix 3)。** 数値と判定の食い違いは 0 件だった。レビュー子は両 attempt の全 12 cell について、raw の 5 標本から中央値・平均・95% CI を再計算し、効果・床値判定・NQSV 会計 (6.3875 node 時間) と一致することを確かめた。
  R2 の正しさ記録 36 件がすべて trace 有効・certified・serializable・anomaly 0 で、性能が trace 無効 binary であることも確かめた。§0 の commit (10:28:52) は投入 (10:29:38) より前で、以後は追記だけだった。原成果物・結果稿・既存 fig10・生成器・policy・driver は不変。
  wrapper は期待 hash と判定を record から読み、自己計算していない。lock の主張と空き秒数は、コードと WAL から再現できた (rr95 の検証完了 → rr5 の bench 開始は 2 巡で 0.02 秒差)。
- **B (過剰・削除): GO (should-fix 3・nit 2)。** 変更は insight 配下と `docs/phase3.md` の追記だけで、範囲外の実装・gate・台帳は無い。§7 は実際の費用超過の原因の記録として範囲内で、案を実装したふりもしていない。

| ID | 所見 | 判定 | 処置 |
|---|---|---|---|
| A-F1 / B-F1 | 「測定値の汚染は無い」「延びたのは時間だけ」は観測を超える断定 | real (must-fix) | 結論 5 と §7 を、観測したこと (競合 probe が検出なし・rounds 1・bench 所要が原 attempt と同程度・settled の形が同じ) に限定した。影響が皆無だとは主張しないと明記し、節題と結論の原因を「推定」に直した |
| A-F2 / B-F2 | 「約 2.2 node 時間」の試算は算式が合わない | real (must-fix) | 削除した。待ちを除いた算式 (約 3.3 node 時間、試算) に置き換え、初版の誤りを §7 に書いた。land 調整役へ訂正を送り、直す wave の投げ文の値も差し替えられた |
| A-F3 | rep の兄弟 node への配布は既に行われており、「1 本 5 分」の根拠が無い | real (should-fix) | 案 2 を、既存の rep 配布と workload × cell 単位の別 job への分割を区別する形に書き直した。5 分はユーザーの指示 (2026-09-30) の目安として書いた (land 調整役の補足による) |
| A-F4 / B-F4 | caption の置換 2 が、outer status の説明を原 attempt だけに帰属させ、R2 の status の意味を弱めている | real (should-fix) | fix 子 1 回目が置換 2 を削除した (原文は R2 にもそのまま成り立つ)。残り 3 置換は不変。親が R2 実データで描き直した (PNG は bytes 不変、caption と provenance が変わった) |
| A-F5 | provenance が描画時の README の hash を束縛し、現行の木では閉包を再検査できない | real (should-fix) | §0 だけの版を `verbatim/s0-snapshot.md` に置き、それを束縛する形で描き直した。閉包検査は現行の木で通る (`verbatim/draw-r2-fix1.log`) |
| B-F3 | 費用の式が「3 request ×」を余計に掛けている (結果の値は正しい) | real (should-fix) | 式を `5 node × (1,531 + 1,527 + 1,541) s` に直した |
| B-F5 | 非合成・限定の記述の反復 | real (nit) | 前例 fig11 と同じ構成で、冒頭の結論から主要結果へ直接たどれるので、このまま受け入れる。§0 は変えない |

変異 matrix は、repo の実装面の差分が 0 (wrapper は repo 外。repo の変更は insight・phase 行・worklog fragment だけ) なので、段 4 裁定どおり免除した。


焦点再レビュー (Codex、read-only、commit `78b3ff4c9` が対象、受理検査 rc 0、`verbatim/s6-focus.md`) は **GO**。A-F2・A-F3・A-F4・A-F5・B-F2・B-F3・B-F4 は closed、B-F5 は受容、A-F1・B-F1 は次の新規所見を残して partial、回帰は無し。
レビュー子は §7 案 1 の算式 (空きの合計 1,196.1・943.3・67.5 s、差引き約 3.32 node 時間) と §6 の式 (22,995 node 秒 = 6.3875 node 時間) を WAL と会計から再計算して一致を確かめた。
図・表・provenance の sha256、snapshot と `e92aeea8f` の README の bytes 一致、wrapper の差分が置換 2 の 8 行削除だけであることも確かめた。
新規所見 F-F1 (should-fix): 競合 probe は lock 取得後・bench 開始前の 1 時点の観測なのに、結論 5 が「待ちの間も」と書き、§7 が「全区間で取り合い」と書いていた。real と裁定し、両方を観測した時点・範囲に限る文言へ直した。これで A-F1・B-F1 も closed とする。
