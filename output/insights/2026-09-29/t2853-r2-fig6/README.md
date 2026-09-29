# [T-2853] R2 fig6 — A-2 (stock 対 fixed 10 / 5 µs) を現行の certification driver・現行 policy (5 node) で Pegasus に測り直す

`authority: none` / `default_effect: no-state-change`

- 作成: 2026-09-29 JST。wave `dev-wave-t2853-r2-fig6` (背景 job)、着手時の基準 = local main `035fc11fa`。
- 前段: `output/insights/2026-09-27/t2853-repro-rest/README.md` §3.3 (投入単位 = 図 1 本、fig6 は試算 1.70 で暫定不要)、
  `output/insights/2026-09-23/t2853-figure-rerun-plan/README.md` §2.2 (fig6 の経路)、先例 `output/insights/2026-09-28/t2853-r2-fig8b/README.md`。
- 原 attempt: `t2364-20260907b` (`output/insights/2026-09-07_t2364-paper-story-a2-certification/`、結果稿 `docs/paper-story/results/2026-09-07-a2-certification-observed-positive.md`、図 `docs/paper-story/figures/fig6_a2_certification_observed_positive.*`)。

## 結論

1. **fig6 の測定 (A-2 の 4 cell) を、現行 repo の driver `tools/pegasus/submit_paper_story_a2_certification.sh` と現行 policy (5 node・CCBench pin `6810666`) で
   Pegasus に投げて測り直した。** attempt `t2853r2-20260929a`、2 job (request `35310` rr5・`35327` rr50) とも完走 (driver_rc 0) した。
   §0 は投入前に commit した (`a901d51e7`)。投入はユーザーの確認 (見積り約 2.21 node 時間) を取ってから行った (§1)。
2. **R2 の outer status は `observed-positive`**。median 比の効果は rr5 (write-heavy、fixed 10 µs) +65.4129%、rr50 (balanced、fixed 5 µs) +12.8953%。
   4 cell すべて正しさ certified (legacy 1・performance 5、anomaly 0)、4 cell とも `source_binding_status = bound` (§3)。
   原 attempt (+63.5485%・+14.4213%、`observed-positive`) と同じ status だが、§0 のとおり合成せず、近さを再現精度として評価しない。
3. **原 fig6 と同じ生成器 (bytes 不変) で R2 の図を描き、同じ生成器の読み込み関数で原 attempt と R2 の対照表を作った** (§4・§5)。
   生成器の検査はどれも外していない。wrapper は repo 外の使い捨てで、原 attempt を同じ経路で描いた点列が既存 fig6 の provenance と完全一致する (陽性対照)。
4. **測定の実消費は 2.16 node 時間 ((a) Elapse 973 s + 583 s、× 5 node)** で、見積り 1.96 を 0.20 上回った。受入の見積り 0.25 を足すと約 2.41 になり、
   ユーザーに示した約 2.21 を超える見込みである (§6)。超過の主因は rr5 の Elapse (見積り元 t2489 の 680 s に対し 973 s)。原因は調べていない。
5. trace 保全口 (D2233) は driver が環境変数を渡す口を持たないので使っていない (§0 項 10)。

## 0. R2 attempt の地位 — 結果より前に固定する (投入前に commit)

**この節は R2 の job を投入する前に書き、commit してから投入する。** 結果を見てから地位・報告の仕方を変えないためである。

1. **地位。** R2 attempt は、fig6 の測定設計 (A-2 policy の 4 cell: rr5 の stock `BACK_OFF=0` 対 fixed 10 µs、rr50 の stock 対 fixed 5 µs。
   48 thread・1,000,000 record・Zipf 0.9・read-modify-write 無効・max operations 10・3 秒・5 反復、各 cell で legacy 1 + performance 5 の正しさ検査) を、
   固定 genome・LLM なしで 1 回測り直す**再現パッケージの試行**である。原 attempt `t2364-20260907b` の置換でも取り消しでもない。
2. **形。** 現行 repo の driver `tools/pegasus/submit_paper_story_a2_certification.sh` を、現行 main の detached checkout から、現行 policy
   `orchestrator/campaign/paper_story_a2_certification.v2.json` (`scheduler.nodes = 5`) と現行 CCBench pin `6810666` で投げる (2 job: rr5・rr50)。
   driver・job body・policy・生成器は変えない。
3. **原 attempt と条件が違う点 (結果の前に列挙する)。** 原 attempt は 1 node の policy・CCBench pin `511c953`・izanagi source `31ec382a7` で走った。
   R2 は 5 node の policy (正しさ検査を兄弟 node へ分ける経路) と pin `6810666` で走る。`511c9538..68106660` の CCBench 差分は `cc/mocc/transaction.cc` だけで、
   silo の source と adopted cell に当てる `patches/silo-backoff-fixed.patch` の対象 (`cmake/Options.cmake`・`include/backoff.hh`) は同一である。
   性能の bench は head node で行い、原 attempt と同じく trace 無効 build で測る。これらの差は R2 を「同一条件の再走」と呼ばない理由として書き、差の効果は推定しない。
4. **合成しない。** R2 と原 attempt の標本・median・効果・outer status を合成しない。統合 status、プール推定、attempt をまたぐ有意水準の保証を作らない。
   数値の近さ・符号の一致を再現精度として評価しない。
5. **原 attempt は不変。** 原 attempt の成果物 (`output/insights/2026-09-07_t2364-…/`)・fig6・結果稿は凍結物のまま保持し、R2 の結果で書き換えない (規律 7)。
   R2 の値は本 insight で原 attempt の値と並べて記録するだけである。R2 の `collect` は repo 外の一時 root へ書かせ、repo の tracked destination へは書かない。
6. **結果にかかわらず報告する。** R2 の outer status が `observed-positive` でも `reject` でも indeterminate でも、1 job だけの完走でも、未完走でも、そのまま本 insight に書く。
   失敗した job は取り下げず、得られた観測値と失敗理由を記述的に開示する。起動時の検査で測定前に落ちた job (campaign・WAL・測定なし) は、
   新しい attempt ID で同じ形のまま投げ直し、落ちた attempt ID・request ID と理由を記録する。
7. **正しさ。** anomaly が出た cell は即 reject (規律 2)。正しさ検査は原 attempt と同じく job 内の trace 有効 build の別走で行い、
   計測は trace 無効 build で行う (規律 1、driver の既存経路)。検査を緩めて描く・記録することはしない。
8. **図と表。** 原 fig6 と同じ生成器 `tools/plotting/plot_a2_certification.py` (bytes 不変) を repo 外の wrapper から呼び、R2 の certification・raw manifest の sha256 だけを
   生成器の既存の差し替え口 (`main(..., expected_hashes=...)`) に渡して描く。対照表 (原 attempt と R2) も同じ生成器の読み込み関数 `load_measurements` (全検査つき) で作る。
   生成器が R2 の入力を検査で拒否した場合は検査を外して描かず、拒否理由と得られた値を表で記録する。図の caption は生成器が記録から組む既定文のまま変えない。
9. **主張の範囲を増やさない。** outer status は protocol の status であって研究の成功宣告ではない。性能の certification は正しさの certification と別の段で、
   R2 の性能 status も原 attempt と同じく他の workload・機体・pin へ転移すると言わない。
10. **trace 保全口 (D2233) は使わない。** driver の `qsub -v` は job へ渡す環境変数を固定で列挙しており、`IZANAGI_TRACE_ARCHIVE_ROOT` を渡す口が無い。
    有効化には driver の変更が要り、本 wave の範囲外である。R2 の trace は保全されず、R1 (保存 trace の再判定) の入力にはならない。

## 1. 費用の見積りと確認 (投入前)

- 投入形: 2 job (rr5・rr50) × 5 node、gen_S、walltime 6 h (予約上限 60 node 時間)。
- 見積り ((a) Elapse): 同じ A-2 policy・同じ 5 node 形の probe attempt `t2489-20260918a` (request `4978` / `4979`、`output/insights/2026-09-18/t2489-a2-nodes5-probe/README.md` §2) の
  Elapse 680 s + 728 s に node 数 5 を掛けて 7,040 node 秒 = **1.96 node 時間**。repro-rest の 1.70 (B-7 の Elapse を当てた試算) より直接の値なので、こちらを使う。
- 開発の検査: 受入全走 1 回 ≈ 0.25 node 時間 (見積り、DW-S04 は受入を免除しない)。
- 合計 ≈ **2.21 node 時間** で線 (2 node 時間) を越えるので、投入前にユーザーの確認を取る。
- (投入後に追記) 確認: 2026-09-29 14:52 JST、ユーザーが「投入してよい」を選んだ (この見積り・投入形・walltime の予約上限・gen_S の待ち 82 本を示した問い)。
  投入前の login 検査 (`verbatim/precheck.log`): 投入元 HEAD `035fc11fa`・tracked clean、CCBench `68106660…`・clean、依存物 3 本、gen_S ENA/ACT、quota 可、同じ study の既存 request 0 本。
  policy と job body の sha256 (`f8a77806…`・`2a3205cf…`) は見積り元 t2489 と同一 bytes で、違うのは CCBench pin と izanagi source だけである。

## 2. 投入と完走

| workload | Request ID | host (head) | 開始〜終了 (JST) | Elapse (s) | driver_rc |
|---|---|---|---|---:|---|
| rr5 (write-heavy) | `35310.nqsv` | bnode104 | 09-29 14:53:35 〜 15:09:43 | 973 | 0 |
| rr50 (balanced) | `35327.nqsv` | bnode084 | 09-29 15:00:23 〜 15:10:02 | 583 | 0 |

- 投入: 2026-09-29 14:52:44〜14:53:48 JST、終了コード 0 (`verbatim/submit.log`)。起動時検査での失敗・再投入は無い。rr50 は約 7 分 queue で待った。
- 各 request の兄弟 4 node は job body の gate で即終了した (`job.stderr` に `nonzero PBS job number exits without running compute body` が 4 行ずつ)。
- 会計の逐語は `verbatim/elapse.log`。host と記録時刻は certification の campaign claim から (§4 の表)。
- 正しさ検査の出力: 各 job の `job.stdout` に `verify[legacy]` 1 行 + `verify[performance]` 5 行 × 2 cell = 12 行があり、12 行とも `serializable (… 0 anomalies)`。
- 終了後: 投入元 checkout から `finish-group` (rc=0、`verbatim/finish-group.log`) → `collect` (rc=0、`verbatim/collect.log`)。collect の `--repo-root` は repo 外の
  `/work/1/SFC/tanab/izanagi-repro-archive/t2853-r2-fig6-20260929/collect-root` とし、repo の `output/insights/2026-09-07_t2364-…/` には書いていない (原 attempt の tracked 成果物は変化なし)。

## 3. certification — 本番 producer の出力

`collect-root/output/insights/2026-09-07_t2364-paper-story-a2-certification/` (dir 名は policy の `tracked_destination` の写しで、中身は R2 の attempt)。

| 成果物 | sha256 |
|---|---|
| `certification.json` (`paper-story-a2-certification-result/v4`) | `89934470746055dcd505cd542bf451016a03d7b30056d458f2e957927f2af034` |
| `raw-manifest.json` | `309188a98a1b083613e180094541f46fc3690ff43fb800fc0dd97c87c0e910b2` |
| `acquisition-receipt.json` | `34c7d432d1aad8d6054029c3ee5f2cbdb025a226b2ef543ceda5cb7366198b8a` |
| `completion-receipt.json` | `a1132d0e2d2e0610e412bb499b51d0215731913e23d8e0043b9b0e3cd96fcfc9` |
| `submission-receipt.json` | `5c5edf21d85f288fd5b81e44a970d27eba7b14925386d45108001d8e1ba26a8e` |

- `status` = **`observed-positive`**、`effects` = rr5 `0.6541289006210069`・rr50 `0.12895328955649732`。
- `attempt_id` = `t2853r2-20260929a`、`current_pin` = `6810666`、`source_commit` = `035fc11fa601547f5d68e54f5661c5daa70b93a5`、
  `protocol_sha256` = `d99f08bc…7f9c` (原 attempt は `136b823e…`。差は 09-07 以後の policy 改版で、t2489 の insight が同じ値を記録している)。
- cell: `rr5-stock` (`src_token = stock`)、`rr5-fixed10` (`16c29935…`)、`rr50-stock` (`stock`)、`rr50-fixed5` (`678b7203…`)。4 cell とも `bound`・正しさ `certified`。
  adopted cell の `src_token` が原 attempt (`955b452a…`・`21def77c…`) と違うのは、token が pin + patch に束縛されており pin が違うためである。
- 性能は認証していない。outer status は protocol の status であって研究の成功宣告ではない (§0 項 9)。

## 4. 原 attempt と R2 の対照表

原 fig6 と同じ生成器の読み込み関数 `load_measurements` (全検査つき) で 2 attempt を別々に読み、wrapper の `table` が書いた表である
(`figures/fig6_comparison_table.md`、sha256 `a57bef97…`)。値は attempt ごとに独立に読んだもので、合成していない。数値の近さを再現精度として評価しない (§0 項 4)。

| workload | cell | 原 attempt median (tps) | 原 mean ± t95 CI 半幅 | 原 abort | R2 median (tps) | R2 mean ± t95 CI 半幅 | R2 abort |
|---|---|---:|---:|---:|---:|---:|---:|
| rr5 | `rr5-stock` | 2,438,295 | 2,462,838.6 ± 99,765.6 | 0.7845 | 2,405,931 | 2,436,289.4 ± 113,267.5 | 0.788 |
| rr5 | `rr5-fixed10` | 3,987,794 | 4,004,505.0 ± 45,583.8 | 0.3833 | 3,979,720 | 3,981,584.2 ± 46,261.3 | 0.3837 |
| rr50 | `rr50-stock` | 3,756,230 | 3,808,422.0 ± 138,475.2 | 0.685 | 3,813,280 | 3,881,173.4 ± 187,725.8 | 0.684 |
| rr50 | `rr50-fixed5` | 4,297,929 | 4,302,525.0 ± 58,456.7 | 0.4615 | 4,305,015 | 4,329,303.6 ± 59,543.5 | 0.4623 |

| workload | 原 attempt の効果 (median 比) | R2 の効果 (median 比) |
|---|---:|---:|
| rr5 (fixed 10 µs) | +63.5485% | +65.4129% |
| rr50 (fixed 5 µs) | +14.4213% | +12.8953% |

- 両 attempt とも生成器の独立再計算 (`effect_crosschecks.computed`) が certification の値と一致した。
- 原 attempt の行は結果稿 §2.1 の表と一致する (mean・CI 半幅・abort の表示桁で照合)。
- 条件の違い (§0 項 3): 原 attempt は 1 node の policy・pin `511c953`・source `31ec382a7`、R2 は 5 node の policy・pin `6810666`・source `035fc11fa`。toolchain は両方 gcc/g++ 11.4.0・cmake 3.22.1。

## 5. 図 — 原 fig6 と同じ生成器で描いた R2 の図

- `figures/fig6_r2_a2_certification.png` (sha256 `376dada9…`)、provenance `figures/fig6_r2_a2_certification.provenance.json` (`7b15113f…`)。
  PDF (`f00f786d…`) を含む原本は repo 外 `/work/1/SFC/tanab/izanagi-repro-archive/t2853-r2-fig6-20260929/figure/` にあり、insight の 2 file は原本と bytes 一致。
- 並べて見る相手は原 fig6 `docs/paper-story/figures/fig6_a2_certification_observed_positive.png` (変えていない)。形・軸・注記は同じ生成器の既定のままである。
- 生成器 `tools/plotting/plot_a2_certification.py` の sha256 は `aac63659…8448` (wave 開始時の main と同一、変更なし)。生成器の全検査 (入力 hash・schema・embedded policy・WAL と raw cell の照合・効果の再計算・正しさ 4/4・layout) を通り、
  出力後に生成器の `validate_external_sources` と `validate_repo_closure` も通った (`verbatim/draw.log`)。
- caption は生成器が記録から組んだ既定文のままで、attempt ID・request・host・時刻・効果・pin `6810666` は R2 の値である。ただし末尾の
  「The older series is not a comparator, and the cause of the sign difference has not been identified.」は、原 fig6 で旧 attempt (fig5) との関係を述べる生成器の定型文で、
  R2 について特定の旧系列を指す意味は無い。caption は変えていない (段 4 裁定 (P2))。
- provenance の `reproduction` は生成器の直接起動の argv を記録するが、R2 の certification は生成器の repo 内 pin 表に無いので、その argv のままでは入力 hash 検査で止まる。
  再生成は wrapper 経由で行う:
  `python3.10 /work/1/SFC/tanab/izanagi-repro-archive/t2853-r2-fig6-20260929/tools/t2853_r2_fig6_plot.py --generator <repo>/tools/plotting/plot_a2_certification.py --expected-generator-sha256 aac636595ec0b211133edcc18bc1f72f984e346f58e7146da444396ea8d86448 draw --measurement-root /work/1/SFC/tanab/izanagi-measurements/dev-wave-paper-story-a2-cert-20260824/t2853r2-20260929a --certification <collect-root>/output/insights/2026-09-07_t2364-paper-story-a2-certification/certification.json --raw-manifest <同 dir>/raw-manifest.json --out-prefix <出力 dir>/fig6_r2_a2_certification`
  (`<collect-root>` = `/work/1/SFC/tanab/izanagi-repro-archive/t2853-r2-fig6-20260929/collect-root`)。対照表は同じ wrapper の `table` (argv は置き場の README)。
- 図と同じ dir の `figures/README.md` に、caption 末尾の定型文の注意と、wrapper 経由の再生成手順を置いた (段 6 レビュー B-1・B-2)。

### 5.1 wrapper (repo 外の使い捨て)

- Codex の実装子 (段 5) が子 worktree の `scratch/` に書き、親が実行後に `/work/1/SFC/tanab/izanagi-repro-archive/t2853-r2-fig6-20260929/tools/t2853_r2_fig6_plot.py`
  (sha256 `e3367d042f5d688935cd2b431d9787d7aff893dcc70660371dda4afdfe4783c6`) へ退避した。repo には入れていない。
- 生成器を import して、既存の差し替え口 `main(..., expected_hashes=...)` / `load_measurements(..., expected_hashes=...)` に、入力 file から実行時に計算した sha256 を渡すだけである。
  生成器の検査関数・定数・caption には触れない。`--expected-generator-sha256` が違えば描かずに止まる。
- 陽性対照: 原 attempt を wrapper の同じ経路で描いた `artist_series` が既存 fig6 の provenance と完全一致した (実装子と親がそれぞれ実行、`verbatim/control.log`)。
- 負例 (実装子が実行、`verbatim/s5-author-report.md`): 存在しない measurement root → rc=2・図なし、生成器 sha256 の不一致 → rc=2・図なし、
  certification を 1 byte 変えた copy → wrapper が変更後の sha256 で束縛するので hash 検査は通るが、生成器の embedded policy 検査で拒否 (rc=2・図なし)。
  最後の拒否は hash の防壁ではなく別の検査による。wrapper は入力 bytes の同一性を保証しない (入力の束縛は §3 の sha256 の記録が担う)。

## 6. 費用

- 測定: 2 job の Elapse 973 + 583 = 1,556 s、× 5 node = 7,780 node 秒 = **2.16 node 時間** ((a) Elapse、`verbatim/elapse.log`)。見積り 1.96 を 0.20 上回った。
  rr5 は見積り元 t2489 の 680 s に対し 973 s、rr50 は 728 s に対し 583 s。差の内訳は調べていない。
- 開発の検査: 受入全走 1 回 (land 前、本 insight を含む最終 tip に対して)。見積り 0.25 を足すと約 2.41 node 時間で、投入前にユーザーへ示した約 2.21 を上回る見込みである。
  受入の実測 Elapse は受領証 (`/work/1/SFC/tanab/tmp/t2853-r2-fig6-20260929/acceptance-receipt-1.json` と shard の会計) にあり、本 insight には書かない。受入の後に記録 commit を足すと受入済み tip が変わり受入をやり直すことになるためである。
- finish-group・collect・描画・表は login で数秒〜数十秒 (計算ノードは使っていない)。Codex 実装子 1 本 (約 5 分)。

## 7. 言わないこと

- **R2 は原 attempt の置換・取り消し・合成相手ではない** (§0)。2 attempt が同じ `observed-positive` だったことを統合 status や再現精度として読まない。
- R2 は原 attempt と条件が違う (5 node の policy、pin `6810666`、source `035fc11fa`) ので「同一条件の再走」とは言わない。条件差の効果も推定しない。
- 性能を認証していない。outer status は研究の成功宣告ではない。read-heavy (A-6) については何も言わない。他の workload・機体・pin への転移も言わない。
- 計算ノードの割当ては専有の保証ではない。単独性は job body の既存の測定前 probe に拠る。ノード間の性能差は測っていない。
- trace は保全していない (§0 項 10)。R1 (保存 trace の再判定) の入力にはならない。

## 8. 出所

- `verbatim/request.md` — 依頼の逐語。`verbatim/startup-gate.log` — 開始 gate (rc=0)。`verbatim/s1-brief.md` — 段 1 brief。`verbatim/s4-ruling.md` — 段 4 裁定 (段 2・3 は軽量版で省略、理由は同 file)。
- `verbatim/submodule-init.log` — submodule 初期化 tool の出力 (wave 作業木・投入元とも 1 回目 rc=1。wave 作業木は 2 回目も rc=1 だったが、`git submodule status --recursive` で 3 本とも初期化済みを確かめ、
  開始 gate が rc=0。投入元は 2 回目 rc=0)。`verbatim/hydrate.log` — third-party の hydrate (rc=0、5 本とも pin 一致)。`verbatim/precheck.log` — 投入前の login 検査。
- `verbatim/submit.log`・`verbatim/elapse.log`・`verbatim/finish-group.log`・`verbatim/collect.log` — 投入・会計・終了処理。
- `verbatim/s5-author-prompt.md`・`verbatim/s5-author-report.md` — 実装子への指示と報告 (受理検査 rc=0)。`verbatim/control.log`・`verbatim/draw.log`・`verbatim/table.log` — 親の実行。
- repo 外: 測定原本 `/work/1/SFC/tanab/izanagi-measurements/dev-wave-paper-story-a2-cert-20260824/t2853r2-20260929a/` (receipts・job root 2 本)、
  置き場 `/work/1/SFC/tanab/izanagi-repro-archive/t2853-r2-fig6-20260929/` (`collect-root/`・`figure/`・`control/`・`tools/`・`README.md`)。
  投入元 checkout は一時置き場 `/work/1/SFC/tanab/tmp/t2853-r2-fig6-20260929/submit-tree` (wave の終わりに撤去)。

## 9. 段 6 レビュー

commit `75749a951` と repo 外の成果物を対象に、Codex の read-only レビューを 2 本並列で行った (受理検査 rc=0)。

- **A (一次資料との照合・正しさ境界): GO、所見なし** (`verbatim/s6-review-a.md`)。識別子・sha256・4 cell の集計値の食い違い 0、Elapse の和から 2.161 node 時間を再計算、
  両 job の verify 出力 24 行すべて anomaly 0、raw cell が正しさ検証に trace 有効 build・性能計測に trace 無効 build を記録していること、wrapper が `expected_hashes` だけを使い検査関数・定数を差し替えていないこと、
  §0 が結果後も同一で原 attempt の tracked 成果物と fig6 に差分が無いことを確かめた。
- **B (過剰・削除): NO-GO (should-fix 2・nit 1)** (`verbatim/s6-review-b.md`)。追加の gate や台帳を求める所見は無い。

| ID | 所見 | 判定 | 処置 |
|---|---|---|---|
| B-1 | provenance の `reproduction` をそのまま実行すると入力 hash 検査で止まる | real | 図と同じ dir に `figures/README.md` を置き、wrapper 経由の実行できる手順を書いた。provenance は生成器の出力のまま変えない |
| B-2 | caption 末尾の「符号差」の定型文が、図だけを読む人を誤解させる | real | caption は生成器の既定のまま (段 4 (P2)) とし、`figures/README.md` に「R2 と原 attempt の効果はどちらも正で符号差は無い、この文は原 fig6 の定型文」と注記した |
| B-3 | 受入の実測が worklog にまだ無い | real (nit) | 受入は land 前の最終 tip に対して走らせるので、その値を同じ tip の中へ書くことはできない (書けば tip が変わり受入のやり直し)。§6 と worklog fragment に受領証の置き場を書き、実測値は wave の最終報告で示す |

焦点再レビュー (Codex、read-only、commit `297a20555` が対象、受理検査 rc=0、`verbatim/s6-focus.md`) は **NO-GO**。B-1・B-2 は partial、B-3 は open (受入後に記録する予定をそう書いていることは確認)、新規 1 件。

| ID | 所見 | 判定 | 処置 |
|---|---|---|---|
| F-1 (B-1 の残り) | 再生成手順の `--out-prefix <出力 dir>/…` は shell でリダイレクトとして解釈され、そのまま実行できない | real | `OUT=$(mktemp -d)` を定義して `"$OUT/…"` を渡す形にした (`figures/README.md` と置き場の README)。親が置き場の README の code block をそのまま抜き出して実行し (rc=0、`verbatim/repro-run.log`)、再生成した PNG と対照表が insight の file と bytes 一致、provenance の `artist_series` と caption も一致した |
| B-2 の残り | 注記は画像自体に無く、PNG・PDF 単体での誤読が残る | refuted | 問題の文は provenance の `caption` にだけあり、画像には描かれていない (画像内の文字は題・status 行・正しさの行・軸・脚注だけ)。画像単体で読む人はこの文を見ない |

DW-O16 に従い、F-1 は親の実機での再実行で closed とし、再レビューは重ねない。

### 9.1 逐語の可逆最小正規化

Codex の出力 2 本は markdown の行末 2 空白を含み `git diff --check` に抵触したので、**行末の 2 空白だけを除去**した (可視文字は不変)。復元は列挙した行の末尾へ 2 空白 (U+0020 ×2) を戻す。

| file | 原文 sha256 | 原文 bytes | 正規化後 bytes | 除去した行 (原文の行番号) |
|---|---|---|---|---|
| `verbatim/s6-review-a.md` | `b91b28d0ac788e9d42d3263bde9f5eb4c611ee973b35898ca30111a41b88fa18` | 831 | 829 | 7 |
| `verbatim/s6-review-b.md` | `2c085e605a70ad43431b3ae2fb0c107a5b1e97cd8c0f5eaf2aaa3d84e383f36c` | 2,470 | 2,468 | 13 |

## 所在の移動・撤去 (2026-09-30 追記)

作図の子 worktree `.codex/worktrees/t2853-r2-fig6-author` (branch `codex/t2853-r2-fig6-author`) と fig8b 系の `t2853-r2-plot-author`・`fix1`・`fix2` は、2026-09-30 の掃除 wave で回収せずに撤去する。最終 wrapper と図は `/work/1/SFC/tanab/izanagi-repro-archive/t2853-r2-fig6-20260929/` と `/work/1/SFC/tanab/b10-backoff-grid-t2853-r2-20260928/` にあり、branch は束 bundle に退避した。
判定の根拠・木ごとの退避の所在・残る写しの一覧は `output/insights/2026-09-30/cleanup-originals-migration/README.md` を正本とする。上の本文は当時の事実として書き換えない (記録された測定・判定は撤去を理由に無効にならない、規律 7)。撤去は同 wave の land の後に行う。
