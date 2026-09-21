## 検査範囲

指定資料を読み、校正 6 record・本走 24 record・9 job の記録を直接走査した。平均・範囲・保全量・予算・Elapse 和を再計算した。書込み、測定、verifier の再実行は行っていない。

以下、`結果稿` は `docs/paper-story/results/2026-09-21-b8-final-candidate-longrun-verify.md`、`insight` は `output/insights/2026-09-21/t2807-b8-effective/README.md`、`run/` は指定 job dir 配下を指す。「成立」は欠陥を指摘する攻撃が成立した意味である。

## 所見

- [should] output/insights/2026-09-21/t2807-b8-effective/README.md:102 — 校正の保全量で十進・二進単位が混在し、個別値と全体値が record の合計に対応しない — 成立 — 根拠：`run/calib/<workload>/calib.json` の `rows[].preservation.files[].stored_bytes`。
  10 s の実値は write-heavy **534,242,457 bytes = 509.493 MiB**、balanced **641,639,321 bytes = 611.915 MiB**、read-heavy **1,888,746,616 bytes = 1.759 GiB**。「510 MB / 613 MB / 1.8 GB」はこの値の正確な単位換算ではない。
  6 行の合計も **4,878,177,766 bytes = 4.878 GB = 4.543 GiB**で、「4.6 GB」と一致しない。`stored_bytes` 基準の値へ統一するか、ディレクトリ使用量ならその計測方法と単位を明記する。
  10 s 合計 **2.854 GiB**と本走外挿 **22.833 GiB**は正しく、extime・予算・判定は変わらない。

- [should] docs/paper-story/results/2026-09-21-b8-final-candidate-longrun-verify.md:201 — 判定の転記元である機械集計の SHA-256 が欠けている — 成立 — 根拠：入口 README:247–248 の「転記元の SHA-256 を文書に書く」、先例結果稿 §5。
  規則・bundle・runner の hash は記載されているが、これらは観測結果を含む `summary-final.json` の bytes を同定しない。現状でも path から照合でき、実際の判定不一致は無かった。
  同行に集計の SHA-256 **`ee94bdf2044976fddf9a22c439ca78ec493dda0fd43a31e51c758668e46c5001`**を添える。新しい gate・台帳は不要。

- [nit] docs/paper-story/README.md:112 — 「draft の値を 1 つも変えず」が、採用済み M2 の表現修正を取り残している — 成立 — 根拠：draft と発効 JSON の比較では既存 field の変更は `status`、追加は `effective`。
  insight §1 と bundle の `effective.value_policy` は「実験構成の既存値は不変、status は置換」と正しく区別している。入口だけが文字どおりには偽の全称表現を残す。
  「実験構成値を維持し、`status` を `effective` に置換して承認情報を追加した」と揃える。identity や実験条件の改変は無い。

## 数値・全件主張・規則の照合

**攻撃 1 は保全量の記述について成立。攻撃 2・3・4 は不成立。** 結果稿 §3 の表の数値には不一致を認めなかった。

| 主張 | 一次 field／照合結果 |
|---|---|
| commit witness と C 行数 | 全 30 record の `bench.commit_witness == count.c_lines` |
| bench・count・preserve・verifier の時間 | `bench.wall_s`、`count.wall_s`、`preservation.wall_s`、`verify.wall_s`。校正 6 行と本走の全範囲・平均が記載の丸めと一致 |
| 本走 24 枠の完走条件 | `bench.completed`、`preservation.complete`、`verify.completed/verdict/certified/anomaly_count` が全件一致 |
| identity | 全 30 record の `bindings.source_before/source_after` の `src_token`・`source_bytes_sha256` が bundle の gate 別期待値と一致 |
| PID 非重複 | 本走 `bench.pid` の集合サイズ **24**。workload 内だけでなく全 24 枠で確認 |
| 同一 SHA | 全 30 record の `ruling_sha256`・`bundle_sha256`・`runner_sha256` が各期待値と一致 |
| verifier・toolchain・固定 checkout | 全 30 record の `bindings.verifier_module_sha256`・`toolchain`・`ccbench_pin` が bundle と一致。`repo_head` は全件 `624c84986…` |
| 判定集合 30 | `targets.plan-A.judgment_set_counts` は main **24**、calibration_completed **6**。直接走査とも一致 |
| anomaly・非 serializable・失格 0 | 全 30 record の verdict と anomaly、および `anomaly_verdict_count=0`、`disqualification_records=[]` |
| 未完走・bench 失敗・規約不適合・not_run 0 | 全 record の完走状態、9 job の completed、集計の対応する count がすべて 0。job 段失敗 record も無し |
| reverify・resume 0 | attempt は全件 1、追加 attempt／reverify directory・resume 記録無し。会計 record は予定どおり 9 件 |
| 段下げ 0 | `initial_extime=chosen_extime=10`、`stepdown_history` は 10 s の `within budget` 1 件 |

`refs/summary-final-excerpt.json` は、原集計の `targets.plan-A` から指定の 2 field を除いた値と一致した。`refs/summary-final.md` は `run/summary-final.md` と byte 同一だった。

校正は全 workload で `{6,10}` が適格、共通部分も `{6,10}`、最大値は **10 s**。生 record から再計算すると、

- **B(10)** = 8,601.179792 + 435.570024 + 42.090810 × 6 = **9,289.294676 s**
- **B(6)** = 5,071.136949 + 284.934633 + 252.544860 = **5,608.616442 s**

となり、機械集計・記述・事前登録 §4.2／§7 と一致する。

費用は dispatch log の `Elapse` を独立に加算して、段 A **1,920 S**、段 B **9,280 S ≤ 14,400 s**。runner 内部値 **1,904.705418／9,249.497640 s**とは分けて報告されており、費用基準の取り違えは無い。

## 過大主張チェックリスト

**攻撃 5 は不成立。** 事前登録 §13 の各項目を以下のとおり確認した。

| §13 の項目 | 判定 |
|---|---|
| 操作的事実に限定し、証明・保証・信頼度を主張しない | 充足。該当語は否定・限界の説明に使われている |
| 判定集合・未完走・規約不適合・extime・反復数・workload | 充足。結果稿 §3.1〜§3.3 |
| 「種」の定義と seed 未記録 | 充足。§1.2、限定 3 |
| 長時間の値と 3 s との関係 | 充足。§3.3、限定 4 |
| 案 B の 6 s は既知結果の追試 | 本 cohort は案 A。案 B の 6 s を新規結果として主張しておらず、適用対象外 |
| S-1a／S-1b の性格を変えない | 充足。限定 7 |
| 現行 pin・patch 束縛、旧 source との差、同一 binary の否定 | 充足。§1.1、限定 6 |
| verifier の版と限界 | 充足。§1.2、限定 2 |
| 失格の構造化報告 | 失格 record 0 件を直接確認。今回の報告対象無し |
| 配線・hash・lint を測定結果や機械的強制と呼ばない | 充足。pass は実走 record に基づく集計として記述 |

## 発効・ストーリー・親裁定

**攻撃 6 は不成立。** draft との構造比較で、既存値の変更は `status` のみ、追加は `effective` のみだった。承認記録・D 番号 fold・承認対象 snapshot は別 field で区別され、D2194 と整合する。発効 commit 自身の hash は bundle に埋め込まれていない。

**攻撃 7 は入口の表現についてのみ成立。** 基点 `21641fee7` からの変更は指定の 4 file で、日付版・既存結果稿・事前登録の編集は無い。仕分け (2) は独立 process の自己シードへ変更し、seed 未記録・乱数列の独立性未検証を併記している。D2186 が求めた限定の強さは適切で、結果表の pass・30 件・各 0 件も実測と一致する。

**攻撃 8 は M2 の入口への反映漏れについて成立。**

| 親裁定 | 反映状況 |
|---|---|
| H1：未完走の 2 分岐 | 結果稿 §2 項 5 に反映。両分岐の対象が無かったことも直接走査で確認 |
| M1：承認 commit の役割分け | insight・bundle に反映 |
| M2：status の置換と構成値不変の区別 | insight・bundle は反映済み。入口に nit が残る |
| M3：walltime 式は保証でなく見積り | insight:96–100 に反映 |
| M4：集計対象の混入防止 | 現存の集計対象は校正 3・本走 6 job、30 record。余分な会計・失敗 record 無し |
| M5：本走前記録と費用照合 | 校正記録 commit `c8fc23d4d`、09:14:39 JST に記録済み。本走開始 09:17:38 より前。保全量表記には上記 should |
| M6：submit-tree 再利用前確認 | 終端・hold 削除は校正 dispatch log、発効 SHA は全 record で確認。ただし再利用直前の clean／hold 確認の逐語記録は指定資料から確認できなかった |

M6 は「確認しなかった」と断定できない。実施済みとして完全に閉じるなら、親が持つ当時の確認出力への参照で補う。現在の状態を調べても投入前確認の証拠にはならない。

**攻撃 9 は不成立。** 新しい実装・gate・汎用台帳は増えていない。§12 後段の校正 6 行、extime、B(E)、walltime の根拠、容量見積り、空き容量再確認は、本走前 commit に記録されている。ただし **81 TB・使用 5% の当時の `df` 生出力**は指定資料から独立照合できなかった。

## 総括

**GO。must-fix 0 件／should 2 件／nit 1 件。** `pass`、30 件の判定集合、identity の束縛、種・長時間の限定を覆す反証は無かった。凍結前に保全量表記と集計 SHA の記載を整えることを推奨する。

| 攻撃項目 | 成立／不成立 |
|---|---|
| 1 数値・件数 | **成立**：insight の校正保全量・単位 |
| 2 全件量化 | **不成立** |
| 3 extime・予算決定 | **不成立** |
| 4 費用 | **不成立** |
| 5 §13 過大主張 | **不成立** |
| 6 発効束・承認・自己参照 | **不成立** |
| 7 ストーリー | **成立**：入口の「1 つも変えず」のみ |
| 8 親裁定の反映 | **成立**：同じ M2 の表現残存。重複計上しない |
| 9 過剰・本走前記録不足 | **不成立** |

**自分で再計算し、照合できた数値**

| 量 | 再計算値 |
|---|---|
| 本走 commit 範囲：write／balanced／read | 8,334,626–8,419,456／7,165,219–7,317,347／19,689,835–19,949,054 |
| verifier min–max／平均：write | 293.943762–296.546039／295.285199 s |
| 同：balanced | 217.381327–221.989805／219.240273 s |
| 同：read | 492.537376–500.637892／496.437797 s |
| 本走保全量：write／balanced／read | 3.973574／4.748476／14.201929 GiB |
| 本走保全量合計 | 22.923979 GiB |
| 校正 10 s 合計／8 反復外挿 | 2.854158／22.833261 GiB |
| B(10)／B(6) | 9,289.294676／5,608.616442 s |
| 本走 walltime 見込み／予約上限式 | 約 2,243.67／10,574.4 s、予約 12,600 s 内 |
| runner job 時間合計 A／B | 1,904.705418／9,249.497640 s |
| dispatch Elapse 合計 A／B | 1,920／9,280 S |
| 件数 | 校正 6、本走 24、判定集合 30、job 9、異なる本走 PID 24 |

校正 6 行の commit・各段時間、本走 bench/count/preserve の全範囲、各 job 時間、各 0 件の主張も照合済み。

**照合できなかった／記述値と一致しなかったもの**

- 校正保全量の「510 MB／613 MB／1.8 GB」「全体 4.6 GB」：記載単位では一致しない。
- 当時の空き容量「81 TB・使用 5%」：本走前の記載は確認したが、独立した生出力との照合はできなかった。
- M6 の再利用直前の clean／hold 確認：実施の逐語証拠までは確認できなかった。