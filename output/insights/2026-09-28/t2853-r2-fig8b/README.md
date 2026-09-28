# [T-2853] R2 fig8b — B-10 静的右 tail (fig8 を含む) を元の driver で Pegasus に測り直す

`authority: none` / `default_effect: no-state-change`

- 作成: 2026-09-28 JST。wave `dev-wave-t2853-r2-fig8b` (背景 job)、着手時の基準 = local main `51f896352`。
- 前段: `output/insights/2026-09-27/t2853-repro-rest/README.md` §3.3 (投入単位 = 図 1 本、fig8b は 1.40 node 時間で確認不要と確定)、
  `output/insights/2026-09-23/t2853-figure-rerun-plan/README.md` (図ごとの経路)。

## 結論

1. **fig8b の測定 (fig8 を含む、B-10 静的右 tail の 2 cohort × 各 3 job) を、元の driver `tools/pegasus/submit_b10_backoff_grid.sh --run-kind t2500-tail-formal` で Pegasus の 6 ノードに同時に投げて測り直した。**
   原 cohort が記録した source commit から投げた (R2-a = cohort 1 の `0600887d9`、R2-b = cohort 2 の `8737cacb4`、CCBench は両方 `511c9538`)。6 job とも完走し、測定は **1.40 node 時間** (見積りどおり)。
   依頼が名指しした `submit_b10_backoff_shape.sh` は fig13 の driver で、fig8b の元の driver ではない (§1.1)。
2. **R2-a・R2-b とも集団 verdict は `not-observed-in-any-workload`** で、各 group 18 区間すべて `declining`、正しさ 120 記録すべて certified・anomaly 0 (§3)。原 cohort 1・2 と同じ verdict だが、4 group は合成しない (§0)。
3. **原 cohort と R2 の値を並べた表**を、原図と同じ生成器の読み込み関数 (全検査つき) で作った (§4)。点ごとの平均は 4 group で近いが、再現精度としては評価しない。
4. **図は、fig8 形 (group ごとに 1 枚) の 2 枚を同じ生成器で描いた。fig8b 形 (2 group を 1 枚に縦に詰める形) の図は生成していない** — 生成器のレイアウト検査が R2 の値で目盛の文字枠の重なりを検出して出力を拒否し、検査は外さなかったため (§5)。
   fig8b 形の R2 図を得るには生成器のレイアウトの変更 (repo の実装変更) が要り、本 wave の範囲外として残す。
5. trace 保全口 (D2233) は、この driver が環境変数を job へ渡す口を持たず両 source commit も D2233 以前なので使っていない (§1.3)。driver の変更は要らなかった。

## 0. R2 attempt の地位 — 結果より前に固定する (投入前に commit)

**この節は R2 の job を投入する前に書き、commit してから投入する。** D2050 は、完走済み cohort のある事前登録に
次の cohort を足すとき、地位と報告方法を結果より前に明記することを求める。事前登録
`docs/b10-backoff-static-tail-preregistration.md` の 2026-09-19 追記の項 4 は「第 3 cohort の実施・地位は本追記では定めない」とする。
本節がその明記であり、事前登録の bytes は変えない (R2 の job は原 cohort と同じ事前登録 commit の文書 bytes を束縛して走るため、項 2)。

1. **地位。** R2 attempt は、fig8b の測定設計 (事前登録 §4〜§7 の格子・動作点・反復数・判定式・正しさ検査) を固定 genome・LLM なしで
   1 回測り直す**再現パッケージの試行**である。cohort 1 (主結果、group `b10-backoff-grid-20260915T061814Z-545445`) の置換でも、
   cohort 2 (独立再現、group `b10-backoff-grid-20260919T131526Z-2235286`) の置換でもない。事前登録の cohort 系列へ加える第 3・第 4 cohort としても扱わない。
2. **形。** fig8b の 2 cohort × 各 3 job に合わせ、2 group (以下 R2-a・R2-b) × 各 3 job (write-heavy / balanced / read-heavy) を、
   元の driver `tools/pegasus/submit_b10_backoff_grid.sh --run-kind t2500-tail-formal` で同時に投げる。各 group は原 cohort が記録した
   source commit の checkout から投げる: R2-a は cohort 1 の測り直しで source `0600887d9`・事前登録 commit `cad6f46d8`、R2-b は cohort 2 の測り直しで
   source `8737cacb4`・事前登録 commit `8737cacb4` (いずれも reservation.json の `repository_commit` と集団報告の束縛から)。CCBench は両方 `511c9538`。
   探索走 campaign は cohort 2 と同じ path を渡す (事前登録 2026-09-19 追記の項 6)。
3. **合成しない。** R2-a・R2-b・cohort 1・cohort 2 の 4 group の標本・区間推定・verdict を互いに合成しない。統合 verdict、プール推定、
   group をまたぐ有意水準の保証を作らない。§4.5 の結末表は group ごとに独立に適用する。数値の近さを再現精度として評価しない。
4. **原 cohort は不変。** cohort 1・2 の稿・図 (fig8、fig8b)・集団報告は凍結物のまま保持し、R2 の結果で書き換えない。
   R2 の値は本 insight で原 cohort の値と並べて記録するだけである。
5. **結果にかかわらず報告する。** R2 の verdict が原 cohort と一致しても、不一致でも、`invalid` でも、未完走でも、そのまま本 insight に書く。
   失敗した group は取り下げず、得られた観測値と失敗理由を記述的に開示する。機械生成 verdict が無い場合はその不在と理由を明記する。
   起動時の検査で測定前に落ちた job (campaign・WAL・測定なし) は、新しい nonce・新しい request で同じ group 形のまま投げ直し、落ちた request ID と理由を記録する。
6. **正しさ。** anomaly が出た候補は即 reject とし (規律 2)、正しさ検査は原 cohort と同じく job 内の trace 有効 build で行う (規律 1)。
   検査を緩めて描く・記録することはしない。
7. **図が描けない場合。** 原 cohort と同じ生成器 (`tools/plotting/plot_b10_static_tail_formal.py`、bytes 不変) が R2 の入力を検査で拒否した場合
   (verdict が `not-observed-in-any-workload` でない等)、検査を外して描かない。完走・`invalid`・未完走・描画拒否のいずれの場合も掲載し、
   図が出ないときは group ごとの集団報告・得られた値・拒否理由を表で並記する。
   R2-a が旧 commit 固有の環境要因で測定前に起動できないと判明した場合に限り、R2-a を `8737cacb4` の checkout から投げ直し、その旨と理由を記録する。
8. **主張の範囲を増やさない。** R2 の verdict ごとに事前登録 §4.5 の分類と表現制約を守る。原 cohort と同じ verdict でも「飽和しない」へ読み替えない。
   性能は未認証のまま (`performance_certified: false`)。

## 1. 経路と投入前の前提

### 1.1 元の driver

- fig8 / fig8b の原 cohort を投げた driver は `tools/pegasus/submit_b10_backoff_grid.sh --run-kind t2500-tail-formal` (job body `tools/pegasus/b10_backoff_grid.sh`) である。
  原 group 名 `b10-backoff-grid-*`、投入手順書 `docs/b10-backoff-static-tail-submission.md` §2、事前登録 2026-09-19 追記の項 6 がこれを示す。
  依頼が名指しした `tools/pegasus/submit_b10_backoff_shape.sh` は待ち方 grid (fig13) の driver で、fig8b の経路ではない。依頼の「元の driver」に合わせ、前者を使った。driver・job body は変えていない。
- git の file mode が `100644` (実行権なし) のため、手順書 §2 の書き方どおり直接起動すると `許可がありません` (rc=126、qsub 前) で止まる。`bash tools/pegasus/submit_b10_backoff_grid.sh …` で起動した
  (初回の R2-a で実測。job は出ていない)。chmod は作業ツリーの mode を変え clean 検査を落とすので使っていない。

### 1.2 投入 checkout

- 原 cohort の reservation.json が記録する source commit の detached checkout を group ごとに 1 本作り、その repo root から投げた (段 4 裁定で A′ を採用)。
  | group | 測り直す原 cohort | source commit | 事前登録 commit | job script sha256 | CCBench gitlink |
  |---|---|---|---|---|---|
  | R2-a | cohort 1 (`b10-backoff-grid-20260915T061814Z-545445`) | `0600887d92538b3f34d894f9674d202d0a29a578` | `cad6f46d86ae4dc31edadfbdfad39c65ed73d70a` | `c0635ef3…` (= cohort 1 の reservation) | `511c9538…` |
  | R2-b | cohort 2 (`b10-backoff-grid-20260919T131526Z-2235286`) | `8737cacb4bd286eb3e0784d16dba6eb85e5d6eab` | `8737cacb4bd286eb3e0784d16dba6eb85e5d6eab` | `8422011d…` (= cohort 2 の reservation・submit receipt) | `511c9538…` |
- 現行 main から投げなかった理由: 現行の `orchestrator/campaign/pin.py` は `CURRENT_PIN = "6810666"` で、formal driver はこの pin で CCBench を build する。
  `511c9538..6810666` の CCBench 差分は `cc/mocc/transaction.cc` だけ (silo の source は同一) だが、記録上の `repo_stock_pin` が変わり、原 fig8b の生成器の固定検査
  (`repo_stock_pin == "511c953"`) を通らないため、同じ生成器で描けない。原 cohort の source commit から投げれば driver・生成器とも変えずに済む (新しい測定をいつでも始められる規律 7 の範囲で、同一性を開始条件にしたのではなく、同じ生成器で描くための選択)。
- login で投入前に確かめたこと (起動時検査の鎖、3 checkout とも): HEAD が指定 commit、`git status --porcelain --untracked-files=all` が空、事前登録文書の bytes が事前登録 commit の blob と一致 (symlink でない)、
  CCBench gitlink `511c9538` の commit が submodule から読める、作業ツリーの job script と HEAD の blob の sha256 一致、凍結 tree (`output/s1-freeze` + `output/s8b-freeze`) の digest を
  job script と同じ計算で求めて `EXPECTED_FREEZE_TREES_SHA256 = c405c742…` と一致、third-party の依存元 (R2-b は hydrate 済み staging の gflags `e171aa2d…` / glog `8f9ccfe7…`、
  R2-a の旧 job body は policy の `/work/SFC/tanab/github/{gflags,glog}` で HEAD が同じ pin・clean)、探索走 campaign の実在、出力親の祖先に `.git` が無いこと。
  確定は job 自身の測定前検査 (fail-closed) である。

### 1.3 trace 保全口 (D2233) を使わなかった理由

依頼は「この経路で使えるなら有効にする」とした。`submit_b10_backoff_grid.sh` は `qsub -v` へ渡す環境変数を固定で列挙しており、`IZANAGI_TRACE_ARCHIVE_ROOT` を job へ渡す口が無い。
さらに両 source commit (`0600887d9`・`8737cacb4`) は D2233 (2026-09-23) より前で、保全口のコード自体が無い。有効化には driver の変更が要るので使っていない
(`docs/phase3.md` の T-2853 行も「job body での opt-in の有効化」を残りとしている)。正しさ検査は原 cohort と同じく job 内の trace 有効 build で行われる。

## 2. 投入と完走

| group | 投入 (JST) | job (Request ID) | host | 開始〜終了 (JST) | Elapse (s) | `completion.json` |
|---|---|---|---|---|---|---|
| R2-a `b10-backoff-grid-20260927T231112Z-3258589` | 2026-09-28 08:11:11 | 32554 / 32555 / 32556 (write-heavy / balanced / read-heavy) | bnode021 / 022 / 023 | 09-28 19:56:39 〜 20:10:31〜33 | 838 / 837 / 836 | 3 本とも `status: complete` |
| R2-b `b10-backoff-grid-20260927T231120Z-3259762` | 2026-09-28 08:11:18 | 32557 / 32558 / 32559 | bnode024 / 025 / 026 | 09-28 19:56:39 〜 20:10:31〜37 | 841 / 836 / 842 | 3 本とも `status: complete` |

- 6 job は別々の 6 ノードで同時に走った。Elapse の合計は 5,030 s = **1.40 node 時間** で、見積り (repro-rest §3.3 の 1.40、(a) Elapse) と一致した。
  `sweep_elapsed_s` は R2-a 822.21 / 821.26 / 820.24 s、R2-b 824.76 / 820.30 / 826.56 s (原 cohort 1 は 823.31 / 820.90 / 825.31、cohort 2 は 822.14 / 820.43 / 822.64)。
- 投入から開始まで約 11 時間 45 分待った。Pegasus が 2026-09-28 09:00〜21:00 のシステム保守 (login の告知) に入り、gen_S の実行が 0 本になったためで、job の失敗ではない。
  保守は告知より早い 19:56 に明けて 6 job が一斉に始まった。
- 各 job の `reservation.json` の `source_binding` は、R2-a が `0600887d9…` / CCBench `511c9538…`、R2-b が `8737cacb4…` / `511c9538…` (§1.2 の checkout と一致)。
- 起動時検査での失敗・再投入は無かった (R2-a の初回 rc=126 は qsub 前で job が出ていない、§1.1)。
- R2-b の 3 campaign id (`…-write-heavy-sweep-45feee64` / `…-balanced-sweep-d7cbfe58` / `…-read-heavy-sweep-ed0b204e`) は原 cohort 2 と同じ値である。campaign id は測定条件 (identity) の hash なので、
  同じ commit・同じ条件なら一致する。出力 root・group id・job は別で、原 cohort 2 の campaign を読んでも書いてもいない (集団報告は group id を campaign path で束縛して検査する)。

## 3. 集団報告 — 本番 CLI の出力

手順書 §4 の argv を、各 group の submit-tree の repo root で、投入時と同じ事前登録 commit で実行した (2026-09-29 02:28 JST、2 本とも終了コード 0)。
出力先は出力親 `/work/1/SFC/tanab/b10-backoff-grid-t2853-r2-20260928/` の `group-report-r2-a/`・`group-report-r2-b/`。

| 成果物 | R2-a sha256 | R2-b sha256 |
|---|---|---|
| `t2500-backoff-static-tail-formal.json` | `e8868253582664e31dd2ac8b051c4aabf0cd699cfacf30e5b93a97d7dbe73000` | `e8a8888608264ff37fcd42d0a8fe4e1e795b630d2a904fbf7bce4d1a12401b44` |
| `t2500-backoff-static-tail-formal.dat` | `14c43f03bc51980252bcfe2fc3e865ddddb83a9106807b835b3f56df6d4d94b7` | `c7f731e75f4761262450950eef87942e4ea2fd94d4d90bf8c4b0225529b7f2f8` |
| `t2500-backoff-static-tail-formal-complete.json` | `d176c97f5ba5ed7da9b679107732c6210f3f6806116abb707d5037fe1e1da8e6` | `be55381d8db7973407f37f0d5f71fad1c5c5ebf3d4d70190ba58572f12584743` |

- **R2-a・R2-b とも `verdict` = `not-observed-in-any-workload`**、`failures` = `[]`、`performance_certified` = `false`。3 workload とも `state` = `not-observed`、
  各 group の 18 区間すべて `declining`、`statistics[].gate_passed` は 24 cell とも `true`。
- 正しさ: 各 group 120 記録すべて certified・anomaly 0 (生成器の読み込み検査で確認)。検証は job 内の trace 有効 build、計測は trace 無効 build の別走 (job body の既存経路)。
- 事前登録の束縛は R2-a が commit `cad6f46d8…` / 文書 blob `8084be04…`、R2-b が `8737cacb4…` / `8511d479…`、spec sha256 は両方 `08f5849b…` (原 cohort 1・2 とそれぞれ同じ)。
- §0 のとおり、この 2 つの verdict は原 cohort の verdict と合成しない。原 cohort と同じ verdict であっても「飽和しない」へ読み替えない。
  事前登録の固定表現のとおり、この事前登録の述語の下では、現在の表現の上限 9999 µs まで飽和は観測されなかった、とだけ言う。

## 4. 原 cohort と R2 の対照表

4 group を、原 fig8 / fig8b と同じ生成器の読み込み関数 (`load_measurements`、全検査つき) で読み、wrapper (§5) が書き出した表である
(`/work/1/SFC/tanab/b10-backoff-grid-t2853-r2-20260928/figure/four_group_table.md`、sha256 `a57e2c31…`)。値は group ごとに別々に計算したもので、合成していない。
数値の近さを再現精度として評価しない (§0 項 3)。反復ごとの値と全区間の境界値は各 group の report / DAT (§3 の sha256) で辿れる。

### 4.1 group

| group | job | 事前登録 commit | 文書 blob | spec | verdict | failures | 正しさ (certified / anomaly) | source commit / CCBench |
|---|---|---|---|---|---|---|---|---|
| 原 cohort 1 `…20260915T061814Z-545445` | 998865 / 998866 / 998867 | `cad6f46d8` | `8084be04…` | `08f5849b…` | not-observed-in-any-workload | [] | 120 / 0 | `0600887d9` / `511c9538` |
| 原 cohort 2 `…20260919T131526Z-2235286` | 10752 / 10753 / 10754 | `8737cacb4` | `8511d479…` | `08f5849b…` | not-observed-in-any-workload | [] | 120 / 0 | `8737cacb4` / `511c9538` |
| R2-a `…20260927T231112Z-3258589` | 32554 / 32555 / 32556 | `cad6f46d8` | `8084be04…` | `08f5849b…` | not-observed-in-any-workload | [] | 120 / 0 | `0600887d9` / `511c9538` |
| R2-b `…20260927T231120Z-3259762` | 32557 / 32558 / 32559 | `8737cacb4` | `8511d479…` | `08f5849b…` | not-observed-in-any-workload | [] | 120 / 0 | `8737cacb4` / `511c9538` |

### 4.2 点ごとの平均 (5 反復、trace 無効) と区間

各欄は「throughput 平均 ± t 分布 95% CI 半幅 (M tps) / abort rate 平均 ± 95% CI 半幅」。1000 µs は境界参照 (区間の集合に入らない)。L は倍増あたりの減少の同時下限 (group 内 36 片側限界の Bonferroni)。

#### write-heavy: points

| backoff µs | original cohort 1 throughput M tps ± CI95 / abort rate ± CI95 | original cohort 2 throughput M tps ± CI95 / abort rate ± CI95 | R2-a throughput M tps ± CI95 / abort rate ± CI95 | R2-b throughput M tps ± CI95 / abort rate ± CI95 |
| --- | --- | --- | --- | --- |
| 1000 | 0.993 ± 0.002 / 0.0423 ± 0.0001 | 0.993 ± 0.003 / 0.0424 ± 0.0001 | 0.993 ± 0.002 / 0.0424 ± 0.0001 | 0.991 ± 0.003 / 0.0425 ± 0.0001 |
| 1250 | 0.906 ± 0.002 / 0.0377 ± 0.0001 | 0.905 ± 0.002 / 0.0377 ± 0.0001 | 0.907 ± 0.002 / 0.0376 ± 0.0001 | 0.906 ± 0.002 / 0.0377 ± 0.0001 |
| 1768 | 0.787 ± 0.002 / 0.0312 ± 0.0001 | 0.788 ± 0.002 / 0.0312 ± 0.0001 | 0.790 ± 0.001 / 0.0311 ± 0.0000 | 0.786 ± 0.003 / 0.0312 ± 0.0001 |
| 2500 | 0.684 ± 0.003 / 0.0258 ± 0.0001 | 0.683 ± 0.002 / 0.0258 ± 0.0001 | 0.685 ± 0.002 / 0.0258 ± 0.0001 | 0.684 ± 0.004 / 0.0258 ± 0.0002 |
| 3535 | 0.596 ± 0.002 / 0.0212 ± 0.0001 | 0.596 ± 0.003 / 0.0212 ± 0.0001 | 0.594 ± 0.003 / 0.0213 ± 0.0001 | 0.595 ± 0.002 / 0.0212 ± 0.0001 |
| 5000 | 0.520 ± 0.002 / 0.0174 ± 0.0001 | 0.520 ± 0.002 / 0.0174 ± 0.0001 | 0.519 ± 0.002 / 0.0174 ± 0.0001 | 0.520 ± 0.004 / 0.0174 ± 0.0001 |
| 7070 | 0.456 ± 0.001 / 0.0141 ± 0.0000 | 0.456 ± 0.001 / 0.0141 ± 0.0000 | 0.457 ± 0.001 / 0.0141 ± 0.0000 | 0.456 ± 0.003 / 0.0142 ± 0.0001 |
| 9999 | 0.402 ± 0.003 / 0.0114 ± 0.0001 | 0.403 ± 0.003 / 0.0114 ± 0.0001 | 0.403 ± 0.001 / 0.0114 ± 0.0000 | 0.402 ± 0.002 / 0.0114 ± 0.0001 |

#### write-heavy: intervals

| interval µs | original cohort 1 | original cohort 2 | R2-a | R2-b |
| --- | --- | --- | --- | --- |
| 1250→1768 | declining | declining | declining | declining |
| 1768→2500 | declining | declining | declining | declining |
| 2500→3535 | declining | declining | declining | declining |
| 3535→5000 | declining | declining | declining | declining |
| 5000→7070 | declining | declining | declining | declining |
| 7070→9999 | declining | declining | declining | declining |
| L min | 0.304 | 0.307 | 0.303 | 0.302 |
| L max | 0.325 | 0.331 | 0.339 | 0.330 |
| 1250→9999 throughput ratio | 0.444 | 0.445 | 0.444 | 0.444 |

#### balanced: points

| backoff µs | original cohort 1 throughput M tps ± CI95 / abort rate ± CI95 | original cohort 2 throughput M tps ± CI95 / abort rate ± CI95 | R2-a throughput M tps ± CI95 / abort rate ± CI95 | R2-b throughput M tps ± CI95 / abort rate ± CI95 |
| --- | --- | --- | --- | --- |
| 1000 | 0.718 ± 0.003 / 0.0588 ± 0.0003 | 0.720 ± 0.003 / 0.0586 ± 0.0002 | 0.720 ± 0.001 / 0.0586 ± 0.0001 | 0.720 ± 0.002 / 0.0586 ± 0.0002 |
| 1250 | 0.659 ± 0.002 / 0.0519 ± 0.0001 | 0.658 ± 0.001 / 0.0520 ± 0.0001 | 0.657 ± 0.002 / 0.0521 ± 0.0002 | 0.658 ± 0.001 / 0.0520 ± 0.0001 |
| 1768 | 0.571 ± 0.003 / 0.0431 ± 0.0002 | 0.570 ± 0.002 / 0.0432 ± 0.0001 | 0.568 ± 0.008 / 0.0434 ± 0.0006 | 0.571 ± 0.003 / 0.0432 ± 0.0002 |
| 2500 | 0.497 ± 0.003 / 0.0356 ± 0.0002 | 0.498 ± 0.001 / 0.0355 ± 0.0001 | 0.497 ± 0.001 / 0.0356 ± 0.0001 | 0.498 ± 0.003 / 0.0356 ± 0.0002 |
| 3535 | 0.437 ± 0.003 / 0.0290 ± 0.0002 | 0.438 ± 0.002 / 0.0290 ± 0.0002 | 0.437 ± 0.002 / 0.0290 ± 0.0001 | 0.438 ± 0.003 / 0.0290 ± 0.0002 |
| 5000 | 0.388 ± 0.002 / 0.0234 ± 0.0001 | 0.387 ± 0.002 / 0.0234 ± 0.0001 | 0.389 ± 0.001 / 0.0233 ± 0.0001 | 0.386 ± 0.002 / 0.0234 ± 0.0001 |
| 7070 | 0.348 ± 0.002 / 0.0186 ± 0.0001 | 0.349 ± 0.002 / 0.0185 ± 0.0001 | 0.349 ± 0.001 / 0.0185 ± 0.0000 | 0.348 ± 0.004 / 0.0186 ± 0.0002 |
| 9999 | 0.317 ± 0.002 / 0.0145 ± 0.0001 | 0.318 ± 0.002 / 0.0145 ± 0.0001 | 0.317 ± 0.001 / 0.0145 ± 0.0001 | 0.318 ± 0.001 / 0.0145 ± 0.0000 |

#### balanced: intervals

| interval µs | original cohort 1 | original cohort 2 | R2-a | R2-b |
| --- | --- | --- | --- | --- |
| 1250→1768 | declining | declining | declining | declining |
| 1768→2500 | declining | declining | declining | declining |
| 2500→3535 | declining | declining | declining | declining |
| 3535→5000 | declining | declining | declining | declining |
| 5000→7070 | declining | declining | declining | declining |
| 7070→9999 | declining | declining | declining | declining |
| L min | 0.299 | 0.303 | 0.261 | 0.299 |
| L max | 0.370 | 0.373 | 0.373 | 0.364 |
| 1250→9999 throughput ratio | 0.481 | 0.484 | 0.482 | 0.483 |

#### read-heavy: points

| backoff µs | original cohort 1 throughput M tps ± CI95 / abort rate ± CI95 | original cohort 2 throughput M tps ± CI95 / abort rate ± CI95 | R2-a throughput M tps ± CI95 / abort rate ± CI95 | R2-b throughput M tps ± CI95 / abort rate ± CI95 |
| --- | --- | --- | --- | --- |
| 1000 | 1.704 ± 0.006 / 0.0237 ± 0.0001 | 1.705 ± 0.005 / 0.0237 ± 0.0001 | 1.707 ± 0.001 / 0.0237 ± 0.0000 | 1.707 ± 0.004 / 0.0237 ± 0.0001 |
| 1250 | 1.545 ± 0.005 / 0.0213 ± 0.0001 | 1.544 ± 0.003 / 0.0213 ± 0.0000 | 1.544 ± 0.003 / 0.0213 ± 0.0000 | 1.548 ± 0.004 / 0.0213 ± 0.0000 |
| 1768 | 1.323 ± 0.002 / 0.0180 ± 0.0000 | 1.324 ± 0.004 / 0.0180 ± 0.0000 | 1.323 ± 0.002 / 0.0180 ± 0.0000 | 1.326 ± 0.001 / 0.0180 ± 0.0000 |
| 2500 | 1.133 ± 0.004 / 0.0152 ± 0.0001 | 1.135 ± 0.003 / 0.0152 ± 0.0000 | 1.138 ± 0.002 / 0.0151 ± 0.0000 | 1.135 ± 0.004 / 0.0152 ± 0.0001 |
| 3535 | 0.972 ± 0.005 / 0.0127 ± 0.0001 | 0.973 ± 0.005 / 0.0127 ± 0.0001 | 0.972 ± 0.005 / 0.0127 ± 0.0001 | 0.971 ± 0.003 / 0.0127 ± 0.0000 |
| 5000 | 0.835 ± 0.005 / 0.0106 ± 0.0001 | 0.832 ± 0.005 / 0.0107 ± 0.0001 | 0.832 ± 0.005 / 0.0107 ± 0.0001 | 0.834 ± 0.003 / 0.0106 ± 0.0000 |
| 7070 | 0.715 ± 0.002 / 0.0089 ± 0.0000 | 0.716 ± 0.005 / 0.0089 ± 0.0001 | 0.716 ± 0.002 / 0.0089 ± 0.0000 | 0.714 ± 0.007 / 0.0089 ± 0.0001 |
| 9999 | 0.619 ± 0.006 / 0.0073 ± 0.0001 | 0.615 ± 0.002 / 0.0074 ± 0.0000 | 0.615 ± 0.007 / 0.0074 ± 0.0001 | 0.619 ± 0.004 / 0.0073 ± 0.0000 |

#### read-heavy: intervals

| interval µs | original cohort 1 | original cohort 2 | R2-a | R2-b |
| --- | --- | --- | --- | --- |
| 1250→1768 | declining | declining | declining | declining |
| 1768→2500 | declining | declining | declining | declining |
| 2500→3535 | declining | declining | declining | declining |
| 3535→5000 | declining | declining | declining | declining |
| 5000→7070 | declining | declining | declining | declining |
| 7070→9999 | declining | declining | declining | declining |
| L min | 0.274 | 0.278 | 0.271 | 0.272 |
| L max | 0.290 | 0.289 | 0.291 | 0.296 |
| 1250→9999 throughput ratio | 0.400 | 0.398 | 0.398 | 0.400 |

## 5. 図 — 原 fig8 / fig8b と同じ生成器で描いた R2 の図

### 5.1 結果

- **fig8b の形 (v2: 2 group を 2 block × 2 行に縦に詰める) では描けなかった。** 生成器 `tools/plotting/plot_b10_static_tail_formal.py` (sha256 `96f8f5de…`、既存 fig8b の provenance が記録する生成器と同一)
  のレイアウト検査 `check_figure_layout` が、R2 の値で `text bbox overlap: '1000' / '0.07'` (x 軸の目盛 1000 と y 軸の目盛 0.07 の文字枠が重なる) として出力を拒否した
  (`verbatim/draw-r2.log`)。測定値の検査ではなく図の体裁の検査だが、§0 項 7 のとおり検査は外さなかった。原データで同じ経路を通すと描ける (§5.2 の陽性対照)。
- **fig8 の形 (v1: 1 group = 2 行 × 3 列) では、R2-a・R2-b とも描けた。** 同じ生成器の v1 経路 (`load_measurements` → `make_figure` → `_publish_outputs`) で、
  出力後に生成器の既存検査 `validate_external_sources` と `validate_repo_closure` を通した。
  - `figures/fig8_r2a_b10_static_tail.png` (sha256 `06384988…`) — R2-a (cohort 1 の測り直し)
  - `figures/fig8_r2b_b10_static_tail.png` (sha256 `4b43456f…`) — R2-b (cohort 2 の測り直し)
  - provenance は `figures/fig8_r2a_b10_static_tail.provenance.json` (sha256 `b8f00334…`)・`figures/fig8_r2b_b10_static_tail.provenance.json` (`f5342a43…`)。
    入力 3 file の sha256、group・job・区間・正しさ、描いた点列 (`artist_series`)、caption、再現コマンド (`reproduction`) を持つ。
  - 原本 (PNG・PDF・provenance) は repo 外 `/work/1/SFC/tanab/b10-backoff-grid-t2853-r2-20260928/figure/` にある。PDF は R2-a `f6bd629d…`・R2-b `70bff3b2…`。
    insight に写した PNG 2 枚と provenance 2 本は原本と bytes 一致。
  - 再現コマンド (R2-a。R2-b は `--group b10-backoff-grid-20260927T231120Z-3259762 --report-dir group-report-r2-b --label R2-b --remeasures 2` と出力名だけ違う):
    `python3.10 /work/1/SFC/tanab/b10-backoff-grid-t2853-r2-20260928/tools/t2853_r2_fig8b_plot.py --generator <repo>/tools/plotting/plot_b10_static_tail_formal.py r2-single --measurement-root /work/1/SFC/tanab/b10-backoff-grid-t2853-r2-20260928 --group b10-backoff-grid-20260927T231112Z-3258589 --report-dir group-report-r2-a --label R2-a --remeasures 1 --completed-jst 2026-09-28 --results-document output/insights/2026-09-28/t2853-r2-fig8b/README.md --out-prefix <出力 dir>/fig8_r2a_b10_static_tail`。
    `<repo>` は生成器の sha256 が `96f8f5de…` の checkout (provenance の記録は本 wave の worktree の path)。wrapper は生成器の sha256 が違えば描かずに止まる。
- 原 fig8 / fig8b (`docs/paper-story/figures/`) は変えていない。R2 の図は論文図ではなく、再現パッケージの記録である。
- 図の見た目: 3 workload とも throughput と abort rate は 1250→9999 µs で単調に下がり、各 panel に「6/6 intervals declining」と min L (R2-a 0.303 / 0.261 / 0.271、R2-b 0.302 / 0.299 / 0.272) が出る。
  R2-a の balanced 1768 µs だけ throughput の 95% CI が他の点より広い (±0.008 M tps、§4.2)。統計 gate (変動係数) はこの cell も通っている。

### 5.2 wrapper (repo 外の使い捨て)

生成器の bytes を変えずに R2 の group を描くため、repo 外の wrapper を Codex の実装子 (段 5) と fix 子 2 回 (段 6) が書いた。repo には入れていない。
保管先は R2 の出力親 `/work/1/SFC/tanab/b10-backoff-grid-t2853-r2-20260928/tools/t2853_r2_fig8b_plot.py` (測定データと同じ場所、最終 sha256 `c6aa81179999b7f5f8c89fd3de146b7e5c7dccfddf39106697a41ef940296d27`)。
fix 1 回目は fig8 形 (v1) の `r2-single` を足し、2 回目は provenance の再現コマンドを実際の wrapper 呼び出しにした (段 6 レビュー A F1、§9)。

- 差し替えたもの: 生成器の cohort 定数 (`COHORTS` の group id・日付・report dir・入力 sha256・結果稿、v1 用の `GROUP_ID`・`REPORT_JSON`・`REPORT_DAT`・`COMPLETE_JSON`・`PINNED_SHA256`)、
  それに合わせた `CLAIM_BOUNDARY_V2`、caption と図中見出しの**役割語だけ** (「formal cohort of 2026-09-15」「primary result」などを「R2 attempt R2-a, a re-measurement of original cohort 1, separate from and not pooled with the original cohorts」などへ。
  置換対象が想定回数だけ現れることを assert し、外れたら止まる)。入力の sha256 は実行時に file から計算した値を使う。
- 差し替えていないもの: 測定値の受理条件 (verdict・`gate_passed`・`failures`・`repo_stock_pin == "511c953"`・sha256・DAT の全行照合・正しさの certified と anomaly 0) とレイアウト検査。provenance 検査が固定要求する役割枠 (1 = primary、2 = reproduction) も変えていない
  (段 4 裁定 s3-a F1。v2 の provenance の役割枠は schema 上の欄で、R2 の地位ではない)。
- 陽性対照 (wrapper が値を変えないこと): 原 metadata のまま wrapper で描いた図の `artist_series` が、既存 fig8b の provenance と完全一致 (`control`)、既存 fig8 の provenance とも完全一致 (v1)。
  負例: 存在しない report dir で rc=3・図なし、sha256 の違う生成器で rc=2・図なし。provenance の再現コマンドをそのまま再実行して同じ `artist_series` が得られることも fix 子が確かめた。
  実行と結果は `verbatim/s5-author-report.md`・`verbatim/s6-fix1-report.md`・`verbatim/s6-fix2-report.md`、R2 実データでの最終描画は親が実行した (§5.1)。
- 対照表 (§4) も同じ wrapper の `table` が、4 group を生成器の `load_measurements` (全検査つき) で読んで書いた。原 cohort 1 write-heavy の 1000・1250・9999 µs の平均と CI は、Codex の子が report JSON の反復値から独立に計算して表と一致を確かめた。

## 6. 費用

- 測定: 6 job の Elapse 合計 5,030 s = **1.40 node 時間** ((a) Elapse、`verbatim/elapse.log`)。見積り 1.40 と一致し、再投入は無かった。
- 開発の検査: 受入全走 1 回。所要は**見積り**で約 0.25 node 時間 (D2219 項 1 と同じ線で数える)。受入の実測は worklog に書く。
- 測定の実測 1.40 と受入の見積り 0.25 の和は約 1.65 node 時間 (見積りを含む) で、D2212 項 4 の線 (2 node 時間) を下回る見込みである。
- 集団報告・描画・表は login で数秒ずつ (計算ノードは使っていない)。

## 7. 言わないこと

- **R2 は原 cohort の置換でも、事前登録の cohort 系列への追加でもない** (§0)。4 group の verdict・標本を合成しない。「4 回とも同じ verdict だった」を統合 verdict や再現精度として読まない。
- 「飽和しない」「飽和点が存在しない」とは言わない。事前登録の述語の下で、現在の表現の上限 9999 µs まで飽和は観測されなかった、とだけ言う。9999 µs は物理的な上限ではない。
- 性能を認証していない (`performance_certified: false`)。機序も採否も主張しない。
- R2 は原 cohort の source commit (`0600887d9`・`8737cacb4`、CCBench `511c9538`) で走らせた測定であり、現行 main (CCBench pin `6810666`) での測定ではない。現行 main で同じ値が出るとは言わない
  (silo の source は同一だが、現行 main では測っていない)。
- 計算ノードの割当ては専有の保証ではない。単独性は job body の既存の測定前 probe (自ノードの競合 process 検査) に拠る。ノード間の性能差は測っていない。
- trace は保全していない (§1.3)。R1 (保存 trace の再判定) の入力にはならない。

## 8. 出所

- `verbatim/request.md` — 依頼の逐語。`verbatim/startup-gate.log` — 開始 gate (rc=0)。`verbatim/s1-brief.md` — 段 1 brief。
- `verbatim/s2-plan.md` — 段 2 プラン (Codex、read-only)。`verbatim/s3-consult-a.md`・`verbatim/s3-consult-b.md` — 段 3 敵対相談 2 レンズ (Codex、read-only)。`verbatim/s4-ruling.md` — 段 4 裁定。
- `verbatim/precheck-*.log`・`verbatim/freeze-digest.log` — 投入前の login 検査 (submit-tree-a は A′ 採用で未使用)。
- `verbatim/submit-r2a-try0-rc126.log`・`verbatim/submit-r2a.log`・`verbatim/submit-r2b.log` — 投入。`verbatim/elapse.log` — 6 job の NQSV 会計。
- `verbatim/report-r2a.log`・`verbatim/report-r2b.log` — 集団報告。`verbatim/draw-r2.log` — v2 描画の拒否。
- `verbatim/s5-author-report.md`・`verbatim/s6-fix1-report.md`・`verbatim/s6-fix2-report.md` — wrapper の実装子・fix 子 2 回の報告。
- `verbatim/s6-review-a.md`・`verbatim/s6-review-b.md` — 段 6 の敵対レビュー 2 本 (Codex、read-only)。
- repo 外: 出力親 `/work/1/SFC/tanab/b10-backoff-grid-t2853-r2-20260928/` (receipt 2 本、job root 6 本、集団報告 2 組、図と表、`tools/` に wrapper)。submit-tree は一時置き場 `/work/1/SFC/tanab/tmp/t2853-r2-fig8b-20260928/` (wave の終わりに撤去)。

### 8.1 逐語の可逆最小正規化

Codex の出力 2 本は markdown の行末 2 空白 (改行指示) を含み `git diff --check` に抵触したので、**行末の 2 空白だけを除去**した (可視文字は不変)。
復元は列挙した行の末尾へ 2 空白 (U+0020 ×2) を戻す。

| file | 原文 sha256 | 原文 bytes | 正規化後 bytes | 除去した行 (原文の行番号) |
|---|---|---|---|---|
| `verbatim/s3-consult-a.md` | `c966bd5284414636fdacd026c9210ce449ed669239246654220e64bce9383164` | 4,214 | 4,196 | 3, 4, 5, 8, 9, 10, 13, 14, 15 (9 行 × 2 bytes) |
| `verbatim/s3-consult-b.md` | `685828f7a8aec60aa003d84c86a729e158a2f65e9c7de9a6ef8b99d50b410296` | 5,736 | 5,712 | 3, 4, 5, 8, 9, 10, 13, 14, 15, 18, 19, 20 (12 行 × 2 bytes) |

## 9. 段 6 レビュー

commit `09ec7f54f` を対象に、Codex の read-only レビューを 2 本並列で行った (`verbatim/s6-review-a.md`・`verbatim/s6-review-b.md`、どちらも受理検査 rc=0)。

- **A (一次資料との照合・正しさ境界): NO-GO (should-fix 1)。** 数値と判定の食い違いは 0 件。レビュー子は R2 の 6 job の ID・host・Elapse・sweep、集団報告 6 file の sha256、4 group の verdict・failures・gate・区間・正しさ・事前登録の束縛を一次資料と照合し、
  さらに反復値から全 96 点の平均と 95% CI、全 72 区間の状態と 36 組の L・throughput 比を再計算して README との差 0 を確かめた。wrapper が測定値の検査とレイアウト検査を緩めていないこと、
  v2 拒否後に v1 で描いたことが §0 項 7 に反しないこと、合成・「飽和しない」への読み替えが無いことも確かめた。
- **B (過剰・削除): NO-GO (must-fix 1・should-fix 2・nit 1)。**

| ID | 所見 | 判定 | 処置 |
|---|---|---|---|
| A-F1 | 図の provenance の再現コマンドが生成器の直接起動で、そのままでは R2 図を再生成できない | real | fix 子 2 回目が再現コマンドを実際の wrapper 呼び出しにし、記録どおりの再実行で同じ `artist_series` を確かめた。親が wrapper を R2 の出力親へ置いて描き直した (PNG は bytes 不変) |
| B-F1 | fig8b 形の図が成果物に無いのに、fig8b を同じ生成器で描いたと読める | real | 冒頭に「結論」を置き、fig8b 形の図は生成していないこと・理由・得るには生成器の変更が要ることを明記した |
| B-F2 | 最終描画の argv と provenance が repo 内で閉じない。wrapper の保管先が一時置き場 | real | provenance 2 本を `figures/` に置き、§5.1 に再現コマンド、§5.2 に永続の保管先を書いた |
| B-F3 | 費用の合計に受入の見積りが混ざり、実績のように読める | real | §6 で測定の実測と受入の見積りを分けた |
| B-F4 | 周辺資料が本題を埋もれさせる | real (nit) | 冒頭の「結論」で主要結果に直接たどれるようにした。逐語と投入前検査のログは出所として残す (削らない) |

焦点再レビュー (Codex、read-only、commit `7b26bb89a` が対象、受理検査 rc=0、`verbatim/s6-focus.md`) は **GO**。A-F1・B-F2・B-F3 は closed、B-F1 と B-F4 は partial、新規所見と回帰は無し。
レビュー子は Elapse 合計 5,030 s (= 1.3972、表示 1.40)、両 group の verdict と 18/18 declining、wrapper の sha256、図の PNG・provenance・PDF の sha256 と insight 側の bytes 一致、再現コマンドが R2 の出力親の wrapper と R2 の入力を指すことを確かめた。
B-F1 の partial は「fig8b 形の図そのものは未生成」という点で、これは §0 項 7 で結果前に定めた帰結である。得るには生成器のレイアウト変更 (repo の実装変更) が要り、本 wave の範囲外として T-2853 の残りに記録した。B-F4 (nit) はこのまま受け入れる。
