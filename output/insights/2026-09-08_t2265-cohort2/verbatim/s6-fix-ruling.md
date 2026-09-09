# 段 6 fix 裁定 — dev-wave t2265-cohort2

段 6 レビュー A (`s6-revA.md`、正しさ防壁・凍結・受理集合) と B (`s6-revB.md`、unit 間整合・
consumer 波及・計測経路)、および親の焦点走 (2 failed / 2575 passed / 4 skipped) を突き合わせて裁定した。

## 共通契約 (fix 子はこれに従う。逸脱しない)

**raw trace v3 は terminal event を 0 件または末尾に 1 件だけ持つ。**

- terminal が **1 件**のとき: summary は `updates = 通常 event 数`、`retained = updates`、
  `dropped = 0`、`flushes = 1`。`len(events) == updates + flushes`。
- terminal が **0 件**のとき: summary は `updates = len(events)`、`retained = len(events)`、
  `dropped = 0`、`flushes = 0`。
- **terminal が 0 件になるのは 2 通りある。** (a) `BACKOFF_TRACE_TERMINAL_US == 0` の build
  (cohort 1 と legacy の全診断走行)、(b) cohort 2 で terminal 期限後に count 閾値へ到達しなかった run
  (事前登録が `inconclusive` と定める非閉鎖)。**どちらも成果物として成立させる。**
- terminal が 2 件以上、または末尾以外にある形は従来どおり拒否する。

## real と裁定した所見 (着地前に直す)

### FX1 — terminal 0 件を producer から解析まで通す (レビュー A 所見 1・B 所見 1/2、焦点走の赤 1)

**最重要。** 現状 parser は raw v3 に terminal 1 件を必須としており、
**cohort 1 と legacy の全診断走行が成果物を作れない**。かつ事前登録が定める terminal 非閉鎖の
`inconclusive` 経路が到達不能である。**上の共通契約どおりに parser と plot を直す。**
**凍結した事前登録は変更しない。** 矛盾しているのは実装契約側なので、そちらを訂正する。

### FX2 — terminal define の必須契約を trace 無効 build から外す (レビュー A 所見 2)

`#ifndef BACKOFF_TRACE_TERMINAL_US` と値域検査が `#if BACKOFF_TRACE` の外にあり、
**trace 無効を含む全 build が新 define を要求する**。`#if BACKOFF_TRACE` の内側へ移す。
**trace 無効かつ define を供給しない前処理が通ることを test で確かめる** (現行の検査は
define を必ず供給するので漏れを検出しない)。

### FX3 — terminal 記録後に制御器が止まる挙動を除く (レビュー A 所見 3)

現状 `terminal_recorded_` が真だと呼び出し元が `return` し、**run 終了まで controller・LCG・割当が
止まる**。凍結した事前登録はここまで定めていない。**terminal を記録したその呼び出しだけ更新を止め、
以後は controller と LCG を通常どおり進めつつ、trace record の追加だけを抑止する。**

### FX4 — cohort 1 metadata 分岐へ terminal 軸を足す (レビュー A 所見 5)

`_artifact_contract_metadata` の cohort 1 分岐に `backoff_trace_terminal_us == 0` を追加し、
**その 1 軸だけを変えた負例**を足す。

### FX5 — cohort 2 解析器が `patch_stack_sha256` を検査する (レビュー A 所見 7)

現状 aggregate の欠落・不一致を受理する。個別 patch pin と同じ厳しさで exact 検査する。

### FX6 — `patches/README.md` の記述を実態へ直す (レビュー A 所見 6)

「認証の exact 2 cell 契約は 1 byte も変えていない」は誤り。
「exact 2 cell から exact 4 cell への制御された拡張」と書く。

### FX7 — 件数 pin の追随 (焦点走の赤 2)

`test_define_sink_cross_product_classifies_t2155_production_sinks_exactly` の
`proven-unreachable` が 33 から 34 になった。新しい define が 1 つ増えた分である。**現物から数え直す。**

### FX8 — 恒真な検査を歯のある形へ (レビュー A 所見 9、B 所見 9)

少なくとも次の 2 つを足す。

- **emitter から parser までの正例で terminal 0 件を通す** (現行の結合 test は
  `flushes=0` を parser へ渡して必ず赤になる。FX1 の後は緑になるべき正例である)。
- **trace 無効かつ terminal define を供給しない compile / 前処理の正例** (FX2 の歯)。

### FX9 — plot 利用文書の追随 (レビュー B 所見 6)

`tools/plotting/README.md` が schema v2 / v3 しか案内していない。v4 と実際の入力条件を書く。

## scope 外と裁定した所見 (実装せず、ユーザーへの裁定パッケージへ回す)

- **レビュー A 所見 4: published group receipt の再受理が exact でない。** 再検査が
  `certified_requests` だけを見て、件数・claim limitations・未認証 marker・各 row の状態・
  `trace_dir` を確認せず、その `trace_dir` を `shutil.rmtree` へ渡す。
  **本 wave が作った欠陥ではない** (`certified_requests` の再検査経路は unit B の差分に含まれない)。
  本 wave はこの受理形を 2 cell から 4 cell へ広げたので**露出は増える**が、修正は防壁の強化であり
  「仮想リスク向けの gate 追加は scope 外」というユーザー指示に当たる。**裁定パッケージへ回す。**
- **レビュー B 所見 3: cohort 2 の図を実際に描くには extime 6 の performance 成果物が 6〜7 本要る。**
  本 wave はそれを測らない。**ユーザーの残件は「図が新 cell と新 event 項目を理解する改修」であり、
  図を出力することではない。** 解析・identity・event 項目の理解までを本 wave の成果とし、
  **図の出力には別途 performance 計測が要ることを insight に明記して閉じる。**
- **レビュー B 所見 5: ring 容量 (65,536) 到達時に `seq` と summary の契約が壊れる。**
  ただし fail-closed で拒否されるため、誤った値が成果物になることはない。
  cohort 2 の実測 event 数は 1,000 前後で容量の 1.5% であり到達しない。**記録して閉じる。**

## 親の記録を訂正する点 (fix ではなく worklog / insight の訂正)

- 段 4 裁定の「terminal は 1 秒の余裕で必ず入る」は不正確。**terminal は期限経過に加えて
  count 閾値到達も要求する。** 到達しなければ非閉鎖であり、事前登録どおり主判定は inconclusive。
- 段 4 裁定の「既存 cell の挙動は変わらない」は `clocks_per_us_ > 0` のときだけ正しい。
  0 のとき旧式は即時発火、新式は永久 false になる。**実運用では 0 にならないが、記録では区別する。**
- 段 4 裁定は 3 unit としたが、実際は **unit D を足して 4 unit** になった。
- 認証 job 数は **48** (2 cell x 3 workload x 8 slot)。裁定の「49」は performance 成果物 1 本を
  足した数だったが、その 1 本の実行機構は実装に無い。**48 と記す。**

## fix の所有分割 (3 子、互いに素)

- **fix-1** (patch C 系): `patches/cicada-adaptive-counterfactual.patch`、`patches/README.md`、
  `orchestrator/tests/test_dynamic_backoff_transitions.py` → FX2、FX3、FX6、FX8 の前処理側と結合正例
- **fix-2** (driver 系): `tools/pegasus/probes/t2187_adaptive_const_probe.py`、
  `orchestrator/tests/test_t2187_adaptive_const_probe.py`、
  `orchestrator/tests/test_ccbench_spawn_sites.py` → FX1 の parser 側、FX4、FX7
- **fix-3** (解析器と plot): `orchestrator/campaign/backoff_counterfactual_cohort2_analysis.py`、
  `orchestrator/tests/test_backoff_counterfactual_cohort2_analysis.py`、
  `tools/plotting/plot_dynamic_backoff.py`、`orchestrator/tests/test_plot_dynamic_backoff.py`、
  `tools/plotting/README.md` → FX1 の plot 側、FX5、FX9
