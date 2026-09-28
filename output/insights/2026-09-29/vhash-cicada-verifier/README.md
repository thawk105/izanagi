# Cicada の実行履歴を izanagi の直列化可能性の判定器に掛けられるようにした (VHash 論文の前提 G0、2026-09-29)

authority: none / default_effect: no-state-change (可変状態の正本は worklog 末尾と現行 phase doc)。
wave `dev-wave-vhash-cicada-verifier` (branch `worktree-dev-wave-vhash-cicada-verifier`)、起点 local main `51f896352` (開始 gate fresh rc 0、2026-09-29 03:2x JST)、CCBench submodule = pin C `68106660` (動かしていない)。
job dir `/work/1/SFC/tanab/dev-wave-jobs/dev-wave-vhash-cicada-verifier/` (段 1 brief・段 2 plan・段 3 相談・段 4 / 6 裁定・Codex の prompt と報告・repo 外起動器・計測の原本 JSON と raw trace・変異 harness の記録)。依頼は `/work/1/SFC/tanab/tmp/vhash-2026-09-29/md_3.txt` (同 dir `request-md_3.txt` に逐語)。
段 1〜6 の全文は `verbatim/` (依頼、段 1 brief、段 2 plan、段 3 相談 2 本、段 4 裁定 (R6 erratum・R8 追補を含む)、生死確認の要約、段 6 レビュー 2 本と裁定)。
逐語の正規化 1 件: `verbatim/s6-review-a.md` の 3・6・9 行目の行末空白 2 個 (Markdown の改行) を除いた (`git diff --check` 抵触のため、可視文字不変)。原文 sha256 `25a9608a2c87582a59c52bf0e61ab220058d0c548514fc71bc01fd866172d18e`・4,790 byte、正規化後 `532cdacb454193cecf74357a23281b3f69adf3e86e60cb9635ebb584513ccf7f`・4,784 byte。原文は job dir の `review-a.md` (復元はその file を写す)。

## 1. 依頼と結論

依頼 (VHash 論文の並行 wave md_3、ユーザー依頼により親セッションが作成): VHash / forwarding の試作は timestamp を動かす変更で、直列化可能性を壊す誤りが最も入りやすい。絶対規律 2 の正しさゲートを Cicada に対して働かせるため、Cicada の実行履歴を izanagi の判定器 (`orchestrator/verifier/`) で検査できるようにする。着手時点で `cc/cicada/` に `TRACE` の文字列は無く、判定器に `cicada` の文字列も無かった。

結論:

1. **Cicada の YCSB point read / update の履歴を、判定器を 1 byte も変えずに検査できるようになった。** `patches/instr-cicada-trace.patch` (`#if TRACE` の内側だけ) が trace v2 (C / R / W / E) を出し、現行の parser と依存グラフがそのまま読む (§2)。
2. **負例 (通るべき): stock Cicada は巡回 0。** 生死確認 4 走行と本走の対照 3 走行、計 7 走行すべてで巡回 0、integrity の数値項目 0、trace の commit 数 = ベンチマークの commit 数 (§3)。
3. **正例 (落ちるべき): 壊した Cicada 3 本すべてを巡回として検出し、壊した経路に帰属できた。** 依頼の例示 3 つ (version consistency check を飛ばす / rts を更新しない / 古い版を読んだまま commit させる) をそれぞれ 1 本の patch にし、判定器の代表 witness 20 件中 20 件が、事前登録した帰属規則を満たした。完了判定「3 本中 2 本以上」を満たす (§4)。
4. **trace を外したビルドの命令列は pin と一致した** (YCSB target の 3 TU、絶対規律 1、§5)。
5. **判定の上限は indeterminate で、certified ではない。** Cicada には Silo / mocc の X / P / I に当たる証拠面が無いので、巡回が無い履歴は indeterminate、巡回があれば non-serializable になる (si と同じ上限)。したがって「stock が正しさゲートを通った」「forwarding variant を certified で受理できる」とは書かない。今回言えるのは「実測した YCSB point read / update の履歴で、巡回を検出する経路が働く」までである (§7)。

## 2. 設計

### 2.1 trace の書式と版の表し方

判定器の入力契約は `patches/README.md` の「トレース形式」(trace v2) で、protocol に依存しない。Cicada もこの書式で出す。

| 記録 | Cicada での中身 |
|---|---|
| `C <txid> <thid> <hi> <lo> <read_count> <write_count>` | 書く txn も read-only txn も出す。版 = 自分の wts を上下 32 bit に分けた `(hi, lo)`。`thid` は整数へ変換 (Cicada の `thid_` は 1 byte 型) |
| `R <txid> <key_hex> <hi> <lo>` | 読んだ版。**読んだ時点に保存した wts** を使う (§2.3)。初期版 (`initial_wts`) は判定器の genesis `(1, 0)` に写す |
| `W <txid> <key_hex> <op> <hi> <lo>` | 書いた版 = 自分の wts。op は U / I / D |
| `E <txid>` | 終端 |

- **版の識別:** Cicada の版は `Version::wts_` (64 bit、`(rdtscp()<<8)|thid`、`cc/cicada/include/time_stamp.hh:24-40`)。版 chain は wts 順に並ぶので、`(hi, lo)` の辞書順 = 数値順 = Cicada の版順になり、判定器の ww 順・rw の直後版の復元と一致する。一次資料では版 ID を「wts による版順」と呼び、commit の時刻順とは呼ばない。
- **初期版:** 初期版の wts は起動時刻 (`param->initial_wts`、`cc/cicada/include/tuple.hh:20,77-89`) で 0 ではない。`ycsb_cicada.cc` の main で TRACE 専用の変数へ渡し、未設定のまま emit に達したら異常終了させる。
- **read-only の古い snapshot:** read-only txn は `rts_` の snapshot を読む。R にはその版がそのまま出る。判定器は R の版と後続の W から辺を作るので、正しい古い読みは巡回にならない (§3 で実測)。

### 2.2 hook の位置

- 書く txn: `writePhase()` の `cpv()` の後、read / write set を空にする前 (`cc/cicada/transaction.cc` の旧 907 行付近)。
- read-only txn: `commit()` の早期 return の前 (旧 934 行付近)。read-only の読みも `read_internal` で無条件に `read_set_` へ入る (`transaction.cc:126`) ので、R も出る。
- abort 経路は何も出さない。
- 共有 header (`include/trace.hh` ほか) は変えない。C / E は si の v2 と同じく `izanagi_trace::stream` へ直接書く。
- `#if TRACE` の `#else` 側に `#line` を置き、TRACE=0 で行番号を保つ (§5 の前処理比較で確認)。

### 2.3 読んだ時点の版の保存

commit 時に read set の `ver_->ldAcqWts()` を読み直すと、GC と版 object の再利用 (`REUSE_VERSION=1` が既定) で別の版の値を拾いうる (段 3 相談 A の指摘)。そこで `ReadElement` に TRACE 専用の `trace_read_wts_` を足し、読んだ時点の wts を保存する。emit 時に保存値と `ver_->ldAcqWts()` を比べ、食い違いの件数を終了時に `CICADA_TRACE_READ_WTS_MISMATCH n=<n>` で出す。
**実測:** stock の 7 走行では全部 0。壊し patch stale-read-ro の 2 走行では 43 と 60 (§4)。この壊しは GC の回収対象になりうる古い版を読むので、版 object の再利用が起きたと推定する (未検証。txid・key の特定はしていない)。R 行は保存値を使うので、判定と帰属の値はこの食い違いに左右されない。

### 2.4 未対応の構成を止める

- 内部の版昇格 (`INLINE_VERSION_OPT` かつ `INLINE_VERSION_PROMOTION`) は、同値 body の write を作る。D1464 はこれを workload の write と区別して判定器に見せることを求める。区別は実装していないので、その組合せを TRACE=1 で compile すると `#error` で止める (既存の `#if INLINE_VERSION_PROMOTION` の内側に `#if TRACE` を置く。新しい `#if` 条件に `TRACE` 以外の語を書かないのは、`orchestrator/tests/test_ccbench_spawn_sites.py` の定義一覧照合を変えないため)。既定は `INLINE_VERSION_OPT_CICADA=0` なので既定ビルドは止まらない。
- `SINGLE_EXEC`・`group_commit` は拒否コードを作らず、起動器が `SINGLE_EXEC=0`・`group_commit=0` に固定する (段 4 裁定)。

### 2.5 置き場

- trace hook は out-of-tree patch (`patches/instr-cicada-trace.patch`、無マクロの無条件計装) として置いた。D16 の本来の置き場は submodule の `izanagi-trace` 枝だが、gitlink を動かさない依頼の制約の下での**試作・実走用の置き場**であり、枝への移送と pin の前進は人間の判断として保留する (si の [T-2847] と同じ根拠)。D16 の T-109 一回限り例外は D579 の判断どおり流用していない。
- 壊し patch 3 本は D16 どおり永久に patch。無マクロの無条件 patch で、正例の build にだけ重ねる (条件 gate の定義一覧へ登録しない形)。
- `patches/ledger.json` には足さない (entries は 1 件固定、`orchestrator/campaign/silo_ladder_rung1_contract.py:516-517`)。登録は `patches/README.md` だけ。

### 2.6 判定器の側

判定器の production code は変えていない。parser と依存グラフは protocol に依存せず、`--protocol cicada` は X / P / I の証拠面を unavailable にする (`orchestrator/verifier/model.py`)。依頼の「検査器側の読み込みを実装する」は、**既存の読み込みが Cicada の版表現を受理・検出することを fixture テストで固定する**形で満たした (新しい読み込み機能を足したのではない):

- `orchestrator/tests/fixtures/cicada_g1_genesis_readonly/` — 初期版 `(1,0)` の読み、read-only txn の古い snapshot の読み、下位 32 bit が 2^31 以上の版、同じ key の `(1, 4294967295)` と `(2, 0)` の順序。期待: 巡回 0、integrity 0、X / P / I unavailable、indeterminate、certified でない。
- `orchestrator/tests/fixtures/cicada_g2_write_skew/` — wts 分割版での write skew。期待: non-serializable、G2、両方向の rw 理由の key と版が exact。
- fixture 一覧を固定する登録簿 2 か所 (`_V2_FIXTURE_FILES` と capacity の凍結 hash) へ追随登録した。既存 entry は変えていない。

## 3. 負例 — stock Cicada (build = pin C + instr patch、TRACE=1)

共通条件: `ycsb_tuple_num=200 ycsb_zipf_skew=0.9 extime=1 clocks_per_us=2100 group_commit=0`、CMake = `INLINE_VERSION_OPT_CICADA=0 INLINE_VERSION_PROMOTION=1 REUSE_VERSION=1 SINGLE_EXEC=0 WRITE_LATEST_ONLY=0 TRACE=1` (cache で確認)。cell K = `rratio 50, rmw false, max_ope 10`、W = `rratio 0, rmw true, max_ope 5`、R = `rratio 90, rmw false, max_ope 4`。

| job | run | 判定 | 巡回 | integrity 数値項目 | C 行 = commit 数 | READ_WTS_MISMATCH |
|---|---|---|---|---|---|---|
| L0 (l0-b) | K t1 | indeterminate | 0 | 全 0 | 191,730 = 191,730 | 0 |
| L0 | K t4 | indeterminate | 0 | 全 0 | 178,445 = 178,445 | 0 |
| L0 | W t1 | indeterminate | 0 | 全 0 | 213,879 = 213,879 | 0 |
| L0 | W t4 | indeterminate | 0 | 全 0 | 193,316 = 193,316 | 0 |
| J1 (j1-c) | K t4 | indeterminate | 0 | 全 0 | 175,139 = 175,139 | 0 |
| J1 | R t4 | indeterminate | 0 | 全 0 | 917,498 = 917,498 | 0 |
| J2 (j2-c) | R t4 | indeterminate | 0 | 全 0 | 888,783 = 888,783 | 0 |

- integrity 数値項目 = orphan_reads・version_dups・dup_txids・genesis_commits・missing_txids・write_version_mismatch・malformed_keys・framing_violations・lock_coverage_violations・write_intent_violations・permutation_violations。`integrity.clean` は証拠面が unavailable なので構造上 false で、「integrity 全体が clean」とは書かない。
- 全 run で、全 W の版が `initial_wts` より大きいこと (`all_w_after_initial`) を起動器が確かめた。
- 事象を先頭 200 件で打ち切った 1 回目の本走 (j1-a・j2-a) の対照 3 走行も巡回 0 だった。

## 4. 正例 — 壊した Cicada 3 本 (instr patch の上に重ねる)

| patch | 依頼の例示 | 壊す site (1 本 1 か所) |
|---|---|---|
| `broken-cicada-skip-read-recheck.patch` | version consistency check を飛ばす | validation の read set 再検査 (`transaction.cc:543-570`) で、読んだ版が今の可視版と違っても abort しない |
| `broken-cicada-no-rts-update.patch` | rts を更新しない | `readTimestampUpdateInValidation()` の呼出し (`transaction.cc:536`) を外す |
| `broken-cicada-stale-read-ro.patch` | 古い版を読んだまま commit させる | read-only txn の可視版選択 (`read_internal`) で、txn 内の偶数番目の読みに限り可視版の 1 つ古い committed 版を選ぶ (read-only は validation を通らないので他の検査に止められない) |

診断: 事象を thread ごとに溜め、その txn が commit したときだけ stderr の `CICADA_BREAK_EVENT slug=… tx_wts=… key=… a_wts=… b_wts=…` に出し (全件)、終了時に `CICADA_BREAK_FIRED slug=… reached=… changed=… committed=…` を出す。診断は判定器の判定に使わず、repo 外起動器の帰属解析だけに使う。

帰属規則 (段 4 裁定 R4、実走前に登録): 判定器が出す巡回の witness に、事象の txn から事象の key 上で rw 辺があり、その辺の読んだ版 (`u_ver`) が事象の読んだ版と一致すること (no-rts-update はさらに、辺の先の版の wts < 事象の txn の wts)。分類「期待した経路で検出」= non-serializable かつ規則を満たす witness が 1 つ以上、かつ同じ cell の stock 対照が巡回 0。段 6 裁定で、壊し run 自身の integrity 数値項目 0・C 行 = commit 数も条件に加えた。

| run (全件出力の再走) | 判定 | 巡回 | 帰属 witness / 代表 witness | reached / changed / committed | 自身の integrity・C = commit | 分類 |
|---|---|---|---|---|---|---|
| skip-read-recheck K t4 (j1-c) | non-serializable | 7,517 | 20 / 20 | 913,092 / 12,241 / 12,101 | 全 0・205,764 = 205,764 | 期待した経路で検出 |
| no-rts-update K t4 (j1-c) | non-serializable | 837 | 20 / 20 | 609,921 / 609,921 / 587,143 | 全 0・134,053 = 134,053 | 期待した経路で検出 |
| stale-read-ro R t4 (j2-c) | non-serializable | 3,645 | 20 / 20 | 918,919 / 343,234 / 343,234 | 全 0・767,393 = 767,393 | 期待した経路で検出 |

**親が raw で独立に照合した帰属の例 (各 1 件、trace の該当行):**

- **skip-read-recheck** — 巡回 [205730, 205731]。`C 205731 0 4865843 2048337664 …` は key `…01` を `R 205731 …01 4865843 2044294915` で読んだ。一方 `C 205730 3 4865843 2048080643 …` は `W 205730 …01 U 4865843 2048080643` を書いた。205730 の版は 205731 の読んだ版より新しく、205731 自身の版より小さい — 205731 は自分より前の時刻に確定した版を読むべきところを古い版のまま commit した。事象 `a_wts` = 読んだ版、`b_wts` = 再検査が見た可視版 = 205730 の版、`tx_wts` = 205731 の版で、trace と一致。逆向きの辺: 205730 は key `…00` を `(4865843, 2044294915)` で読み、205731 がより新しい `(4865843, 2048337664)` を書いた。rw + rw の G2 (write skew)。
- **no-rts-update** — 巡回 [133937, 133938]。133937 (版 `…3754420482`) は key `…00` を `…3751518464` で読み、自分より小さい版 `…3754361600` の 133938 が同じ key に書いた。rts を引き上げていれば 133938 の書き込みは abort された組合せ。巡回は 133937 →rw→ 133938 →ww→ 133937。
- **stale-read-ro** — 巡回 [761181, 761213]。read-only の 761213 は 1 番目の読み (key `…0a`) で 761181 の版 `…2803748608` を見たのに、2 番目の読み (key `…08`) では 761181 の版 `…2803748608` を飛ばして 1 つ古い `…2794338563` を選んだ (事象の `b_wts` = 飛ばした版 = 761181 の版)。761181 の書き込みを半分だけ見た不整合な snapshot で、巡回は 761181 →wr→ 761213 →rw→ 761181。

**1 回目の本走 (j1-a・j2-a) の記録。** 同じ 3 本とも non-serializable (巡回 7,766 / 1,292 / 2,279) だったが、帰属 witness は 3 本とも 0 件で「検出したが帰属不能」になった。原因は証拠の集め方の欠陥で、判定器は巡回のうち代表 20 件 (走行の終盤の txid) だけを witness として出す一方、事象を thread あたり先頭 200 件 (走行の序盤) で打ち切っていたため、作りとして重ならなかった。帰属規則は変えず、事象を全件出すよう直して再走した (段 6 裁定 RV-1 / B1)。

## 5. TRACE=0 の同一性 (絶対規律 1)

同じ compile command (checkout の root だけ置換して一致を確認) で「pin のまま」と「instr patch 適用」を TRACE=0 で build し、比べた (l0-b、原本 `runs/l0-b/identity/`)。

| 比較 | transaction.cc | ycsb_cicada.cc | util.cc |
|---|---|---|---|
| objdump の命令列 (address・symbol 名・注釈を除き、分岐先 address を置換) | 差分 0 byte | 差分 0 byte | 差分 0 byte |
| 前処理出力 | 空行の増減だけ (空行以外の差分行 0) | 同左 | 同左 |

binary の `nm`・`strings` は全文一致し、trace の語 (`izanagi_trace`・`CICADA_TRACE`) の残存は 0。
**範囲:** YCSB target (`ycsb_cicada.exe`) の 3 TU だけを比べた。変更した header を include する `tpcc_cicada.cc`・`bomb_cicada.cc`・`sbomb_cicada.cc` の TU は比べていない (段 6 裁定 RV-3)。

## 6. 判定器側のテストの検出力 (変異)

変異 M-V1 (`orchestrator/verifier/dsg.py` の版の圧縮 `_packed_version` で tid 成分を 31 bit に狭める) を事前登録した。login の自走 (`PYTHONPATH=. python3 orchestrator/tests/test_verifier.py`、変異は一時適用して復元、sha256 と作業木の clean を照合):

- 新 HEAD (`0c092586b`): 基準 143 passed → 変異 139 passed / 4 failed。赤 = 新テスト 2 本 (`test_cicada_g1_genesis_readonly_versions`・`test_cicada_g2_write_skew_versions_and_reasons`)、`test_capacity_all_fixture_results_match_frozen_baseline` (cicada の fixture で)、既存の `test_capacity_packed_versions_preserve_bounds_duplicates_and_notes`。
- 変更前 HEAD (`51f896352`): 基準 141 passed → 変異 140 passed / 1 failed。赤 = 既存の `test_capacity_packed_versions_preserve_bounds_duplicates_and_notes`。
- **事前登録した「変更前 HEAD では生き残る」は外れた。** 既存の境界テストが同じ変異を検出する。新テストは同じ変異を追加 3 node で検出するが、新テストだけが検出する差分は示していない。判定器は protocol に依存しないので、Cicada 形の fixture の価値は「Cicada の版表現の回帰を固定する」ことにある。実系の検出力の証拠は §4 の壊し patch 3 本である。
- **dispatch の本走** (変異 harness `tools/mutation_worktree.py`、独立 clone を最終の実装 commit `8b1272c4e` に固定、`tools/run_tests.py --force-dispatch orchestrator/tests/test_verifier.py`、spec sha256 `11c060a9a50471593bff4e1df34810e4f0cdab6dec1cc9dc94f435619f63fb0c`): 基準 143 passed (PASSED)、M-V1 は KILLED で、赤の node 集合は新 HEAD の自走で登録した 4 node と完全一致した。原本は job dir の `mutation-final-results.json`。旧 HEAD での観測は上の login 自走を使い、dispatch では繰り返していない (段 6 裁定)。

## 7. 確かめたこと・確かめていないこと

確かめたこと:
- YCSB の point read / update (cell K・W・R、thread 1・4) で、stock Cicada の履歴が巡回 0・integrity 0・commit 数一致で判定器に通る。
- 壊した Cicada 3 本の履歴を判定器が non-serializable とし、巡回を壊した経路に帰属できる。
- TRACE=0 の命令列一致 (YCSB target の 3 TU)。
- 判定器の production code を変えずに Cicada の trace を読めること (fixture テストと実走)。

確かめていないこと (未対応の範囲):
- **範囲読み取り (scan) の phantom。** scan の読みは read set に入り R として出るが、node の検証による phantom 防止は trace に表さず、検査していない。
- **insert・delete。** op の I / D は出すが、実走していない。
- **内部の版昇格** (`INLINE_VERSION_OPT=1` かつ PROMOTION): TRACE=1 で `#error` (D1464 の区別は未実装)。`INLINE_VERSION_OPT=1` かつ PROMOTION=0、`WRITE_LATEST_ONLY=1`、`REUSE_VERSION=0`、`SINGLE_EXEC=1`、`group_commit>0` は未検証。
- **YCSB 以外の workload** (TPC-C・bomb・sbomb) と、その TU の TRACE=0 同一性。
- **certified。** 証拠面 (X / P / I に当たるもの) は Cicada に無く、巡回なし = indeterminate が上限。
- **campaign の受理経路** (`orchestrator/campaign/pipeline.py` の trace 実行と検証) への接続。今回の実走は repo 外の起動器で、campaign は Cicada の trace を供給しない。
- READ_WTS_MISMATCH (stale-read-ro で 43 / 60) の機序。
- 今回の検索式と対象で見つからなかったもの (例: patch の bytes pin 0 件) は、その範囲での陰性であって全経路の不存在証明ではない。

## 8. 後続に要るもの (起票はしない、次の版の材料)

- **VHash / forwarding の試作を検査するには:** 試作を instr patch の上に重ねて同じ起動器で走らせれば、巡回の検出はできる。ただし判定の上限は indeterminate なので、「巡回が無かった」を「serializable と認定した」と書かない。certified を要する campaign の門に Cicada を入れるには、Cicada 用の証拠面の設計と campaign 側の trace 供給が別に要る (研究前進の裁定候補)。
- **pin の前進:** main の記録では pin を C から C2' へ進める計画が承認済みで、前進の wave は patch の厳密適用を最初に測る。今回の patch 4 本は pin C に対して作ったので、前進後は適用と L0 の再確認が要る。
- **置き場の移送:** trace hook を `izanagi-trace` 枝へ移すかは人間の判断 (§2.5)。
- **診断の量:** 事象を全件出す壊し patch は、no-rts-update で stderr が約 60〜90 MiB になる。正例用のビルドなので性能値としては使わない。

## 9. 計算と工程

計算ノードの job (Elapse は job の報告値):

| tag | request | 内容 | Elapse | 結果 |
|---|---|---|---|---|
| l0-a | 33768.nqsv | 生死確認 1 回目 | 30 s | 起動器が compile command を 1 件に絞れず停止 (workload 別 target が 4 件)。起動器を直した |
| l0-b | 33776.nqsv | 生死確認 | 101 s | 成立 (§3・§5)。起動器の合否集計が cicada では到達できない `clean=True` を要求して rc=1 を返した (判定とは無関係、単位 B で直した) |
| j1-a / j2-a | 33783 / 33784.nqsv | 本走 1 回目 | 82 s / 70 s | 検出したが帰属不能 (§4) |
| j1-b / j2-b | 33827 / 33828.nqsv | 本走 2 回目 | 0 (未開始) | gen_S の混雑 (QUE 86) で dispatch の全体時限 (待ちを含む) に当たり自動取消。`--overall-grace 5400` を足した |
| j1-c / j2-c | 33857 / 33858.nqsv | 本走 3 回目 | 82 s / 69 s | 3 本とも期待した経路で検出 |

合計 434 s (受入と変異の dispatch を除く)。変異の dispatch は基準 1 回・変異 1 回で、各回 `test_verifier.py` だけを走らせた (pytest の報告で基準 5.53 s)。2 node 時間を大きく下回るので、ユーザー確認の対象外。

Codex (gpt-6-sol、reasoning medium): 段 2 plan 1、段 3 相談 2、段 5 author 3 (L0・U-C・U-B) と fix 3 (U-C の登録簿追随、L0 起動器の compile command、U-B の事象全件出力)、段 6 レビュー 2。
