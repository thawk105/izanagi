# [T-2853] R2 fig2c — B-10 拡張格子を元の driver で Pegasus に測り直す

`authority: none` / `default_effect: no-state-change`

- 作成: 2026-10-01 JST。wave `t2853-r2-fig2c` (背景 job、依頼 md_4)、着手時の基準 = local main `5f9e8c549`。
- 承認: D2305 項 9 (ユーザー裁定) — fig2c (2.98 node 時間) を 1 図 1 タスクとして投げる。
- 前段: `output/insights/2026-09-27/t2853-repro-rest/README.md` §3.1〜§3.3 (fig2c = B-10 拡張格子 3 job × 31 variant、元 job 951689〜951691、2.98 node 時間 = (a) Elapse)、
  前例 `output/insights/2026-09-28/t2853-r2-fig8b/README.md` (同じ driver 系で fig8b を測り直した形)。

## 結論

1. **fig2c の測定 (B-10 拡張格子、3 workload × 31 variant × 5 反復) を、元の driver `tools/pegasus/submit_b10_backoff_grid.sh` で Pegasus の 3 ノードに同時に投げて測り直した。**
   原 attempt が記録した source commit `78c7a2c14` (CCBench `511c9538`) の checkout から投げ、3 job とも完走した。測定は **3.01 node 時間** (Elapse 合計 10,836 s、見積り 2.98)。
2. **正しさ: 3 workload × 31 variant すべて `verify_done` が `serializable`・`certified: true`・anomaly 0** (93 / 93、参照 2 variant を含む)。原 attempt も同じく 93 / 93 (§3)。
3. **原 attempt と R2 を並べた表** (`comparison.md`) を、原図と同じ生成器の読み込み関数 (全検査つき) で作った (§4)。group ごとに別々に計算し、合成していない。
4. **図は、原図と同じ生成器で R2 の値から描けた** (`figures/fig2c_r2_b10_extended_backoff.png`)。生成器の受理検査・レイアウト検査・provenance の意味と閉包の検査をすべて通った (§5)。
   原図 (`docs/paper-story/figures/fig2c_*`) は変えていない。
5. **計算を 1 job 5 分程度に分割しなかった。** 並行 wave の共通指示の分割規則を、依頼文 (元の driver を前例と同じ形で) と両立しないと親が推論して適用せず、
   1 job 約 1 時間 × 3 本を投げた。ユーザーから指摘を受け、測定は完走させた (§6、failures に記録)。

## 0. R2 attempt の地位 — 結果より前に固定する (投入前に commit)

**この節は R2 の job を投入する前に書き、commit してから投入する。** 原 attempt (fig2c の元の測定) は事前登録を持たない記述的な測定
(provenance の `claim_boundary.claim_scope = descriptive_backoff_shape_only`、`prereg_frozen_comparison_rule: false`) であり、
追加の測定の地位と報告方法を結果より前に書いておくのは、前例 fig8b §0 と同じく、結果を見てから扱いを選ぶ余地を消すためである。

1. **地位。** R2 attempt は、fig2c の測定 (B-10 拡張格子: Silo・48 thread・100 万 record・Zipf 0.9・read 比 5 / 50 / 95%・workload あたり 31 variant
   (参照 2 = backoff なし・既定 adaptive、静的 29 点 = 0〜1000 µs)・5 反復、各 variant の正しさ検査つき) を固定 genome・LLM なしで 1 回測り直す**再現パッケージの試行**である。原 attempt
   (group `b10-backoff-grid-20260826T234647Z-783837`、job 951689 / 951690 / 951691) の置換ではない。
2. **形。** 原 attempt と同じく 1 group × 3 job (write-heavy / balanced / read-heavy) を、元の driver `tools/pegasus/submit_b10_backoff_grid.sh` で同時に投げる。
   原 attempt が記録した source commit `78c7a2c1408da05c9c6391451192d81963b84034` (3 job の reservation.json の `repository_commit`、fig2c provenance の receipt chain) の
   detached checkout から投げる。CCBench は同 commit の gitlink `511c9538e4e8efa54b45cda62e72389ed3b706ec`。この版の driver は `--output-parent` だけを取る。
3. **合成しない。** R2 と原 attempt の標本・CI・判定を互いに合成しない。プール推定・統合判定を作らない。数値の近さを再現精度として評価しない。
4. **原 attempt は不変。** 原 attempt の job dir・fig2c の図 (`docs/paper-story/figures/fig2c_b10_extended_backoff.*`)・provenance は書き換えない。
   R2 の値は本 insight で原 attempt の値と並べて記録するだけである。
5. **結果にかかわらず報告する。** 完走・未完走・正しさ検査の失敗のいずれでも、そのまま本 insight に書く。失敗した job は取り下げず、
   得られた観測値と失敗理由を記述的に開示する。起動時の検査で測定前に落ちた job (campaign・WAL・測定なし) は、
   新しい nonce・新しい request で同じ group 形のまま投げ直し、落ちた request ID と理由を記録する。
6. **正しさ。** anomaly が出た variant は即 reject とし (規律 2)、正しさ検査は原 attempt と同じく job 内の trace 有効 build で行う (規律 1、計測は trace 無効 build の別走)。
   検査を緩めて描く・記録することはしない。
7. **図が描けない場合。** 原 attempt と同じ生成器 (`tools/plotting/plot_b10_extended_backoff.py`、bytes 不変) が R2 の入力を検査で拒否した場合、
   検査を外して描かない。group id・job 番号・入力 sha256 などの原 attempt 固有の定数だけを repo 外の wrapper で差し替え、受理条件とレイアウト検査は差し替えない。
   生成器のレイアウト検査が R2 の値で拒否したら、図は作らずその事実と拒否理由を書き、表だけを残す (生成器の変更はこの wave の範囲外)。
8. **主張の範囲を増やさない。** 原 attempt と同じく記述的な形の図であり、性能は未認証、機序も採否も主張しない。

## 1. 経路と投入前の前提

### 1.1 元の driver と投入 checkout

- fig2c の原 attempt を投げた driver は `tools/pegasus/submit_b10_backoff_grid.sh` (job body `tools/pegasus/b10_backoff_grid.sh`) である
  (原 group の receipt `b10-backoff-grid-20260826T234647Z-783837.submit.jsonl` の schema `b10-backoff-grid-submit-event/v1` と、3 job の `reservation.json` の `repository_commit`)。
- 原 attempt の source commit `78c7a2c1408da05c9c6391451192d81963b84034` の detached checkout を作り、その repo root から
  `bash tools/pegasus/submit_b10_backoff_grid.sh --output-parent /work/1/SFC/tanab/b10-backoff-grid-t2853-r2-fig2c-20261001` で投げた。
  この版の driver は `--output-parent` だけを取る (fig8b の版にある `--run-kind` は後から入った)。git の file mode が `100644` なので、前例どおり `bash` で起動した。driver・job body は変えていない。
- submodule は repo の初期化ツールと同じ argv (`-c protocol.file.allow=always submodule update --init --recursive --no-fetch`) で初期化した。
  素の `git submodule update --init` は `fatal: transport 'file' not allowed` で失敗した (job は出ていない)。
- 現行 main から投げなかった理由は前例 fig8b §1.2 と同じ: 生成器 `plot_b10_extended_backoff.py` が `CCBENCH_COMMIT = 511c9538…`・`REPOSITORY_COMMIT = 78c7a2c1…`・
  `JOB_SCRIPT_SHA256 = 9579690d…` を固定で検査するので、現行 main (CCBench pin `6810666`) の測定は同じ生成器で描けない。新しい測定の開始条件に同一性を置いたのではなく、同じ生成器で描くための選択である (規律 7)。

### 1.2 login で投入前に確かめたこと

`verbatim/precheck.log`。確定は job 自身の測定前検査 (fail-closed) である。

| 項目 | 実測 |
|---|---|
| checkout の HEAD | `78c7a2c1408da05c9c6391451192d81963b84034` |
| `git status --porcelain --untracked-files=all` | 0 行 |
| CCBench gitlink / submodule の HEAD | `511c9538e4e8efa54b45cda62e72389ed3b706ec` / 同じ (commit は submodule から読める) |
| job script の sha256 (作業ツリー・HEAD の blob) | `9579690d44c49842eefc00fcf459f2717cda1dccc66857e1b0137ff5abbbeefb` (原 receipt の `job_script_sha256` と一致) |
| 凍結 tree (`output/s1-freeze` + `output/s8b-freeze`) の digest | `c405c742…` (job script の `EXPECTED_FREEZE_TREES_SHA256` と一致) |
| 依存元 `/work/SFC/tanab/github/{gflags,glog}` | HEAD `e171aa2d…` / `8f9ccfe7…` (この版の `policy.json` の pin と一致)、clean |
| 出力親 | 未作成、祖先に `.git` なし |

### 1.3 生成器の版

- 生成器 `tools/plotting/plot_b10_extended_backoff.py` の sha256 は原図の provenance と同じ `04db851a…` (現行 main でも不変)。
- 依存 `tools/plotting/plot_backoff.py` は原図の時点の `bdb3c223…` から現行の `aa168498…` へ変わっている。生成器は描画時の依存の bytes を provenance に記録するだけで固定はしない。
  影響は §5.2 の陽性対照で確かめた: 原データを現行の生成器・依存で描き直すと、描画系列 (`artist_series`、9 系列) は原図の provenance と完全一致し、
  `data` の違いは各 workload の `campaign_verifier_epoch` に現行の依存が足した欄 `verifier_assessment_basis: recorded-at-original-verifier-epoch` だけだった (親が jq で独立に照合)。

## 2. 投入と完走

| group | 投入 (JST) | job (Request ID) | host | 開始〜終了 (JST) | Elapse (s) | `completion.json` |
|---|---|---|---|---|---|---|
| R2 `b10-backoff-grid-20261001T012637Z-3721300` | 2026-10-01 10:26:35〜37 | 40679 / 40680 / 40681 (write-heavy / balanced / read-heavy) | bnode074 / 076 / 077 | 10:26:44 / 10:26:45 / 10:27:31 〜 11:27:37 / 11:26:35 / 11:27:11 | 3,658 / 3,594 / 3,584 | 3 本とも `status: complete` |

- 投入の直前に `qstat -a` を見て、生成器対照の本走 (job 名 `izs4loop`) の待ちが無いことを確かめた (`verbatim/submit.log`)。待ちが無かったので優先度は既定 (0) のまま投げた。
- 3 job は別々の 3 ノードで同時に走った。Elapse の合計は 10,836 s = **3.01 node 時間** で、見積り (repro-rest §3.1 の原 attempt の Elapse 10,741 s = 2.98) より 95 s 長い (`verbatim/elapse.log`)。
- 各 job の `reservation.json` の `source_binding` は `repository_commit = 78c7a2c1…`・`ccbench_gitlink_commit = 511c9538…`、`completion.json` の凍結 digest は `c405c742…` で、§1.2 の checkout と一致した。
- 起動時検査での失敗・再投入は無かった。
- 3 campaign id (`b10-backoff-grid-silo-write-heavy-sweep-0a386b45` / `…-balanced-sweep-9ded73c4` / `…-read-heavy-sweep-e2d75497`) は原 attempt と同じ値である。campaign id は測定条件 (identity) の hash なので、
  同じ commit・同じ条件なら一致する。出力 root・group id・job は別で、原 attempt の campaign を読んでも書いてもいない。
- submit receipt の sha256 は `994760a0c66d59a8986cf74a4e493f0ef40d4cdd24dc020283e64e8f003dcfce`。測定データは repo 外の出力親 `/work/1/SFC/tanab/b10-backoff-grid-t2853-r2-fig2c-20261001/` にある。

## 3. 正しさ

各 variant は job 内で trace 有効 build による直列化可能性の検査 (`verify_done`) を通り、計測は trace 無効 build の別走で行われた (job body の既存経路、規律 1)。
WAL の `verify_done` 行を wrapper が数えた結果 (`comparison.md` の末尾の表):

| attempt | variant | `verify_done` | `certified: true` | anomaly 合計 | verdict |
|---|---:|---:|---:|---:|---|
| 原 attempt (3 workload の計) | 93 | 93 | 93 | 0 | serializable 93 |
| R2 (3 workload の計) | 93 | 93 | 93 | 0 | serializable 93 |

workload ごとにも 31 / 31 / 31 で、内訳は同じである。anomaly が出た variant は無いので、reject した variant も無い。

## 4. 原 attempt と R2 の対照表

全表は `comparison.md` (sha256 `71b2700b…`、provenance は `comparison.md.provenance.json`)。wrapper の `table` が 2 group を生成器の `load_measurements` (全検査つき) で読んで書いた。
throughput は 5 反復の平均 ± t 分布 95% CI 半幅 (M tps)、abort rate は生成器が DAT と WAL で照合した集約値 (反復ごとの値は無く CI は付けない)。1000 µs は F718 で除外した行として残る。
値は group ごとに別々に計算したもので、合成していない。数値の近さを再現精度として評価しない (§0 項 3)。

各 group の throughput 平均が最大になった点 (記述のみ。F718 除外後の 0〜900 µs の 28 点の中で。除外行の 1000 µs を含めると原 attempt の read-heavy は 1000 µs の 10.275 が最大になる):

| workload | 原 attempt | R2 |
|---|---|---|
| write-heavy | 6 µs (3.990 ± 0.046 M tps) | 8 µs (4.036 ± 0.050 M tps) |
| balanced | 2 µs (4.424 ± 0.094 M tps) | 2 µs (4.388 ± 0.131 M tps) |
| read-heavy | 0 µs (10.248 ± 0.136 M tps) | 0 µs (10.310 ± 0.146 M tps) |

write-heavy の 3〜12 µs は隣の点との差が CI の幅と同じ程度で、最大の位置の違いを結論に使わない。

## 5. 図 — 原図と同じ生成器で描いた R2 の図

### 5.1 結果

- `figures/fig2c_r2_b10_extended_backoff.png` (sha256 `1a4cbfef…`)、PDF (`9a189bb0…`)、provenance (`0eb407dd…`)。
- 生成器 `tools/plotting/plot_b10_extended_backoff.py` (sha256 `04db851a…`、原図の provenance が記録する生成器と同一) を wrapper 経由で使い、
  `load_measurements` → `make_figure` (レイアウト検査 `_validate_text_bboxes` を含む) → 出力 → `validate_provenance_semantics`・`validate_external_sources`・`validate_repo_closure` をすべて通した (`verbatim/draw-r2.log`)。
- 図の見出しと caption は R2 の役割語 (「R2 attempt (re-measurement of the original fig2c group, separate from and not pooled with it)」) で、host は bnode074 / 076 / 077。
- 再現コマンドは provenance の `reproduction` にある。
  `python3.10 -B /work/1/SFC/tanab/b10-backoff-grid-t2853-r2-fig2c-20261001/tools/t2853_r2_fig2c_plot.py --generator <repo>/tools/plotting/plot_b10_extended_backoff.py r2 --measurement-root /work/1/SFC/tanab/b10-backoff-grid-t2853-r2-fig2c-20261001 --group b10-backoff-grid-20261001T012637Z-3721300 --out-prefix <repo 内の新しい出力先>`。
  `<repo>` は生成器 `plot_b10_extended_backoff.py` の sha256 が `04db851a…` **かつ**依存 `plot_backoff.py` の sha256 が `aa168498…` の checkout
  (provenance の `generator` と `dependencies` の欄が描画時の両方の sha256 を持つ。本 wave の基準 main `5f9e8c549` がこの組。provenance の path は本 wave の worktree)。
  依存の版が違うと描画・検査の結果が変わりうるので、生成器本体だけを合わせない。出力先は生成器の provenance 閉包の契約で repo 内に限られる。
  外部入力は上の measurement root、wrapper は §5.2 の保管先にある。
- 図の見た目 (R2 で観測した傾向の記述。F718 除外後の 0〜900 µs): write-heavy と balanced は数 µs で throughput が山になり、その後は下がる。read-heavy は 0 µs から単調に下がる。abort rate は 3 workload とも単調に下がる。
  原図とは同じ生成器本体を使った別 attempt の図であり、両者を重ねた図は作っていない。形が同じかの判定はしていない (§0 項 3)。
- R2 の図は論文図ではなく、再現パッケージの記録である。

### 5.2 wrapper (この測り直し専用、repo 外の出力親に保管)

生成器の bytes を変えずに R2 の group を描くため、repo 外の wrapper を Codex の実装子 (段 5) が書いた。repo には入れていない。
保管先は R2 の出力親 `/work/1/SFC/tanab/b10-backoff-grid-t2853-r2-fig2c-20261001/tools/t2853_r2_fig2c_plot.py` (sha256 `652f6b5cbf080372b7e77e1bb9f2b8d653b91c24de4966ddbaaa87474db23c97`)。
実装子の報告と照合結果は `verbatim/s5-author-report.md`・`verbatim/s5-verification.json`、prompt は `verbatim/s5-author-prompt.md`。

- 差し替えたもの: 原 attempt 固有の定数 (`GROUP_ID`・`SUBMIT_PATH`・`SUBMISSION_NONCE`・`WORKLOAD_SPECS` の job / host / campaign / identity・`CANONICAL_SHA256`・出力閉包用の `REAL_OUTPUT_PATHS`) と、caption・図中見出しの役割語。
  R2 の値は実行時に receipt・reservation・completion・campaign lock から読み、入力の sha256 は file から計算する。
- 差し替えていないもの: `REPOSITORY_COMMIT`・`CCBENCH_COMMIT`・`JOB_SCRIPT_SHA256` (R2 も同じ値で、生成器の検査を通った)、DAT と WAL の照合、F718 の 1000 µs 除外、固定条件・CV の検査、CI の計算、レイアウト検査、provenance の意味・外部入力・閉包の検査。
- 陽性対照 (`control`): 原 attempt を wrapper 経由で差し替えなしに描くと、`artist_series` (9 系列) は原図の provenance と完全一致 (親が jq で sha256 を照合)。
  `data` は、現行の依存 `plot_backoff.py` が足した欄 `campaign_verifier_epoch.verifier_assessment_basis` を除けば完全一致した (§1.3)。wrapper はこの差を「不一致」として rc=1 で返し、差を隠していない。
- 見立て (`r2` を原 attempt に向けたもの): rc=0、`artist_series` は control と完全一致。
- 負例 (図が出ないこと): sha256 の違う生成器 rc=2、存在しない root rc=2、存在しない group rc=2、DAT を 1 行変えた写し rc=2 (`completion artifact digest mismatch`)、
  その写しの completion の hash も合わせた場合 rc=2 (`dat throughput is not the WAL center`)。いずれも図なし。

## 6. 費用と計算の分け方

- 測定: 3 job の Elapse 合計 10,836 s = **3.01 node 時間** ((a) Elapse)。承認 (D2305 項 9) の 2.98 を 0.03 上回った。再投入は無かった。
- 開発の検査: 受入全走 1 回を予定 (この版の時点で未実施。見積り約 0.3 node 時間、land 調整役が相談不要と確認)。実測は worklog に書く。
- 図・表・集計は login で数秒ずつ (計算ノードは使っていない)。

### 6.1 計算を分割しなかったこと

当時の規則・親の判断・その後の指摘・新しい手順を分けて書く。

1. **当時の規則 (投入前に明文であったもの):** 並行 wave の共通指示は「計算 job は 1 本あたり 5 分程度に分割」を定め、
   同時に「md_N と食い違ったら md_N を優先」「2 node 時間以上は投入前に land 調整役へ 5 点を送る。ただし md_N がユーザー承認済みと書く計算量の範囲内は相談不要」とも書いていた。
   依頼 md_4 は「前例 fig8b と同じ形で、元の driver を原 cohort の source commit で使う」と指定し、job の分割には触れていない。
2. **親の判断:** 元の driver では分割できないと推論し (下の 3)、依頼と分割規則が食い違うとみなして「md_N 優先」で分割規則を適用しないと決めた。brief に 1 行書いただけで、投入前に誰にも示していない。
   計算量はユーザー承認済みなので相談不要と読み、5 点も送っていない。その結果、1 job 約 1 時間 × 3 本を投げた。
3. **分割の可否 (実測):** 原 commit の driver・job body・sweep は workload だけを引数に取り、variant の部分集合を指定する口が無い (31 variant の測定順は seed で決まり campaign identity に入る)。
   元の driver のままなら 3 job が最小単位だった。割るには部分集合 runner の新設が要り、campaign identity が変わって同じ生成器の検査と衝突する。
4. **その後の指摘:** 走行中にユーザーから「1 ジョブあたり 5 分くらいで分割したらもう終わってるのでは」と指摘され、land 調整役は「承認は計算量の承認で、分割の指示と相談を省いてよいという意味ではない」と伝えた。
   測定は 3 job とも bench が済んでいたので止めずに完走させた。
5. **振り返り:** brief は「設計択一なし」として段 2・3 を省いたが、元の driver を使う形と分割規則の両立はまさに択一 (元の形のまま / 部分集合 runner の新設 / 一部だけ先行) であり、見落とした論点である
   (原 source commit を使うこと自体は依頼の直接指定で、brief が P1 を「親の provisional 裁定」と書いたのも不正確だった)。brief は逐語のまま残す (`verbatim/s1-brief.md`)。
6. **新しい手順 (本 wave で足したもの、当時の規則ではない):** 依頼文と共通指示の計算規則が食い違うと判断したら、自分で優先を決めず、投入前に衝突と選択肢を 5 点に添えて land 調整役へ送る
   (memory `measurement-must-split-across-nodes` に追記、failures fragment)。

## 7. 言わないこと

- **R2 は原 attempt の置換ではない** (§0)。2 group の標本・CI を合成しない。表の数値の近さを再現精度として読まない。
- 性能を認証していない。機序も採否も主張しない。図は記述的な形の図 (`claim_scope = descriptive_backoff_shape_only`) のままである。
- R2 は原 attempt の source commit (`78c7a2c14`、CCBench `511c9538`) で走らせた測定であり、現行 main (CCBench pin は本 wave 中に F へ前進) での測定ではない。現行 main で同じ値が出るとは言わない。
- 計算ノードの割当ては専有の保証ではない。単独性は job body の既存の測定前検査に拠る。ノード間の性能差は測っていない (原 attempt は bnode007 / 009 / 016、R2 は bnode074 / 076 / 077)。
- trace は保全していない。この版の driver は環境変数を job へ渡す口を持たず、source commit も trace 保全口 (D2233) より前である。R1 (保存 trace の再判定) の入力にはならない。

## 8. 今後の課題

- **variant の部分集合を、原 campaign と同じ seed 順で測る runner** があれば、R 系の測り直し (fig2c・fig8b など) を 1 job 5 分程度に割って多数のノードへ同時に投げられる。
  campaign identity と生成器の検査との両立 (部分集合ごとの campaign をどう 1 つの図に束ねるか) を含めて設計が要る (land 調整役の依頼で記録)。

## 9. 出所

- `verbatim/request.md` — 依頼の逐語。`verbatim/startup-gate.log` — 開始 gate (rc=0)。`verbatim/s1-brief.md` — 段 1 brief (軽量版、段 2・3 は省略)。
- `verbatim/precheck.log` — 投入前の login 検査。`verbatim/submit.log` — 投入 (qstat の確認と receipt)。`verbatim/wait-jobs.log`・`verbatim/elapse.log` — 完了待ちと 3 job の NQSV 会計。
- `verbatim/s5-author-prompt.md`・`verbatim/s5-author-report.md`・`verbatim/s5-verification.json` — wrapper の実装子 (Codex) の prompt・報告・照合。
- `verbatim/draw-r2.log`・`verbatim/table.log` — R2 の描画と対照表の実行ログ。
- repo 外: 出力親 `/work/1/SFC/tanab/b10-backoff-grid-t2853-r2-fig2c-20261001/` (receipt、job root 3 本、`tools/` に wrapper)。submit-tree は一時置き場 `/work/SFC/tanab/tmp/t2853-r2-fig2c-2026-10-01/submit-tree` (wave の終わりに撤去)。

## 10. 段 6 レビュー

commit `0b952aa74` を対象に、Codex の read-only レビューを 2 本並列で行った (`verbatim/s6-review-a.md`・`verbatim/s6-review-b.md`、prompt は同じ dir、どちらも受理検査 rc=0)。

- **A (一次資料との照合・正しさ境界): GO (nit 1)。** レビュー子は 3 job の ID・host・開始終了・Elapse (合計 10,836 s)、6 job の source / CCBench / 凍結 digest、campaign identity、
  WAL 6 本 930 行 (186 variant すべて build→verify→bench→commit が各 1 回、93 / 93 certified・anomaly 0 が両 attempt)、対照表の全 174 点 (平均・CI 半幅・abort rate の 522 値)、
  provenance の外部入力 hash (22 / 22 × 2)、描画系列 18 系列を独立に再計算・照合して差 0 とした。wrapper の差し替えが §5.2 の列挙内であること、§0 が投入前の commit から不変であることも確かめた。
- **B (過剰・誤読・削除): NO-GO (must-fix 1・should-fix 3・nit 1)。**

| ID | 所見 | 判定 | 処置 |
|---|---|---|---|
| A-01 | 「最大」「単調」は F718 除外後の 0〜900 µs でだけ成り立つ (1000 µs を含めると原 read-heavy の最大は 1000 µs) | real (nit) | §4・§5.1 に範囲を明記 |
| B-01 | 共通指示は「md_N 優先」「承認済み計算量は相談不要」を明文で書いており、「食い違えば相談」は当時の規則に無い。failures と結論がそれを当時の義務の違反として書いている | real | §6.1 と failures fragment を、当時の規則・親の判断・その後の指摘・新しい手順に分けて書き直した。恒久対応は本件の後に足した手順と明記 |
| B-02 | 再現の checkout を生成器の sha256 だけで指定しており、依存の版を固定していない。wrapper を「使い捨て」と呼ぶ | real | §5.1 に依存の sha256 (`aa168498…`) と基準 main `5f9e8c549` を足し、生成器本体だけを合わせない旨を書いた。§5.2 の見出しを「この測り直し専用、repo 外の出力親に保管」に改めた |
| B-03 | 「原図と同じ形の図」は判定基準なしの断定で、§0 項 3 に反する | real | 削り、R2 で観測した傾向の記述と「形が同じかの判定はしていない」に改めた |
| B-04 | brief の「設計択一なし」と、分割の択一を出さなかった誤りが食い違う。P1 の原 source commit は依頼の直接指定 | real | §6.1 項 5 に振り返りとして書いた。brief は逐語のまま残す |
| B-05 | 受入全走 1 回が予定か実施済みか不明 | real (nit) | §6 に「予定 (この版の時点で未実施)」と書いた |

焦点再レビュー (Codex、read-only、commit `e9a21bef5` が対象、受理検査 rc=0、`verbatim/s6-focus.md`) は **GO**。A-01・B-01〜B-05 の 6 件すべて closed、新所見は無し。
レビュー子は修正で足した事実 (共通指示の原文、依存の sha256 `aa168498…` と基準 main `5f9e8c549`、0〜900 µs の 28 点、原 read-heavy の 1000 µs = 10.274779) を一次資料と照合した。
