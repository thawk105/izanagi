## 判定

**NO-GO。承認・凍結不可。** 静的検査と算術のみ実施し、pytest・PBS は実行していない。ファイルは変更していない。

### 所見 1 — pilot の正当な受領証が schema で拒否される

[blocker] `planned_execution.runs[]` の件数要件が文書と schema で矛盾する。

- 根拠: `record-items-v2.md:39,294` は pilot を `36 × 8 = 288` run とする。一方 `receipt-schema-v1.json:691-695` は `maxItems: 36`。
- 構成例: `study_stage=pilot`、`pilot_cluster_slots=[1..8]`、各 slot 36 run、`runs[]` 288 要素。
- 影響: 正当な pilot 受領証が schema で拒否される。逆に schema だけなら 36 run の欠落 receipt が通り、試行台帳と certified 選択の受理集合が壊れる。

### 所見 2 — verification-only 段階を記録できない

[blocker] 検証割当てだけ完了した段階の受領証を構成できない。

- 根拠: `record-items-v2.md:343-346,360-361,509-512` は correctness 6件、liveness 6件、さらに pilot slot ごとの performance allocation を要求する。
- 構成例: verification allocation 1件とその6 arm/workload証拠だけを持ち、performance allocation はまだ0件。
- 影響: verification の実測事実・失敗を先に記録できず、検証割当て失敗時には材料レポートと試行台帳の参照が失われる。verification qsub failure でも correctness/liveness 6件を埋められない。

### 所見 3 — preflight の `a03` failure と `binary_rehash` が衝突する

[blocker] v2 が追加した第三分岐を、実在する allocation で記録できない場合がある。

- 根拠: `record-items-v2.md:448-465` は preflight malformed raw の `post_performance_failure` を許す。だが `record-items-v2.md:255-256`、`receipt-schema-v1.json:455-470` は全 allocation に3点×3 armの9 rehashを要求する。
- 構成例: slot 1 の allocation は取得済み、preflight `[150,160)` の raw が malformed、marker・actual run・`after_last_run` は存在しない。
- 影響: `after_last_run` を省略すれば schema 拒否、捏造すれば事実と異なる receipt。第三分岐が意図した環境 failure の試行台帳記録が不能になる。

### 所見 4 — `fallback_build_inside` が実質的に記録不能

[blocker] 割当て内 build fallback と必須 `built_outside_allocation` が両立しない。

- 根拠: `addendum-a-reissue.md:335-360` は外部 build 不成立時の割当て内 buildを許す。一方 `record-items-v2.md:203-204,229`、`receipt-schema-v1.json:220-239` は全 arm に `built_outside_allocation` を必須化する。
- 構成例: verification allocation の外部 artifact が作れず、performance allocation 内で3 armをbuildする。
- 影響: 実際には許された fallback 経路が receipt を満たせず、正当な測定が `design_not_feasible` 側へ誤写像される。

### 所見 5 — qsub failure・未完了中間状態を terminal receipt にできない

[must-fix] `attempts[]` に active/pending 状態がなく、未完了状態を既存 reason code のどれかへ誤分類する必要がある。

- 根拠: `record-items-v2.md:388-405,438-441,499-512`。全 attempt に terminal `reason_code` が必要で、各 pilot slot は performance allocationを1件以上要求する。
- 構成例: slot 3 が qsub 後まだ実行中、または qsub failure で予備2本を使い切り replacement 不可能。
- 影響: 中間の試行台帳を正直に保存できない。qsub failure＋即時 replacement（失敗側の actual 0、同一 slot の replacement）は記録可能だが、それ以外は欠測・失敗履歴が受理集合から落ちる。

### 所見 6 — `malformed_reason` の複数同時事象に優先順位がない

[must-fix] malformed raw が複数の失敗条件を同時に満たす場合、正しい単一値を決められない。

- 根拠: `record-items-v2.md:421-432,458-462` は `malformed_reason` を単一 enum とするが、複数事象の優先順位・集合表現を定めていない。
- 構成例: `stat_before` が7列未満、同時に counter 差分が負、さらに窓長も範囲外。
- 影響: producer A は `short_columns`、producer B は `negative_delta` を書き、同じ raw が異なる受理集合になる。正当な failure receiptも「exact一致」を満たせない。

### 所見 7 — schedule canonical bytes がまだ一意でない

[must-fix] `block_index` の workload-local/global 定義がない。

- 根拠: `addendum-a-reissue.md:562-590` は各 workload 6 blockを定義するが、`record-items-v2.md:546-550` は `block_index=1..12` としか定めない。
- 構成例: slot 1（W2先行）で、実装Aは W2/W1 とも block index 1..6、実装Bは W2=1..6・W1=7..12 とする。どちらも現行の範囲条件を満たす。
- 影響: `schedule_table` bytes、`schedule_sha256`、planned/actual の join、workload-switch と wait 判定が実装依存になる。

### 所見 8 — §9 に明記されていない第三分岐の偽装形

[must-fix] malformed でない raw でも、valid-shaped counter の値だけで「未実行」を作れる。

- 根拠: `record-items-v2.md:458-460` は `cpu_busy_core_equivalents ∉ [0,1]` も経路3に含めるが、§9は主に7列・負差分・窓長逸脱を明記する (`:657-665`)。
- 構成例: before/after とも8列、差分はすべて非負、窓長10秒、`total=100`・`busy=5` で値は `48×5/100=2.4`。`malformed_reason=null`、markerなし、actualなし、`post_performance_failure`。
- 影響: producerが正しい形式の raw を自作しても、試行台帳には「性能 runなし」と記録できる。§9の非保証範囲を「すべての producer-controlled raw」と明記し直す必要がある。

### 所見 9 — pilot/main の slot identity が stage 間で曖昧

[suspicion] pilot の slot 1..8 と main の slot 1..13 が同じ番号空間か stage-local か定義されていない。

- 根拠: `record-items-v2.md:268,294,583-588`、`addendum-a-reissue.md:603-605`、core `preregistration.md:173-177,200-207`。
- 構成例: pilot slot 1 と main_run slot 1 が同じ scheduleを再利用するが、`run_id`・ledger・consumer が `cluster_slot` だけで結合する。
- 影響: pilot rawを本走へ混入、または本走をpilot側へ紐付ける余地が残る。pilot非poolの共分散、`J`、certified選択、材料レポートの対象集合が変わり得る。

### 所見 10 — 時間予算の文書算術と phase mapping が不整合

[must-fix] 算術誤記に加え、8つの予算行を6 phaseへどう写すかが未定義。

- 根拠: A は `180+0+0+540+720+660+180+120=2400`（`addendum-a-reissue.md:87-103`）。B は `180+1440+360+360+180+120=2640`（`:105-119`）だが、`:132-133` は `2340` と記載。`record-items-v2.md:592-596` は6 phaseの総和だけを要求する。
- 構成例: arm gap/block gap/raw parse/publishを `run`・`teardown` のどこへ積むかで phase cap と実 elapsed の算定が変わる。
- 影響: timeout受理、phase完全性、`requested_walltime_s` の検査が実装ごとに変わり、偽拒否または過大受理になる。

### 所見 11 — 既存 driver は要求証拠を取得していない

[must-fix] 現行資産だけでは受領証 producer を実装できない。

- `t139_positive_control_probe.sh:394-452`: 全 build が `CCBENCH_TRACE=0`。correctness required の trace-enabled buildがない。
- 同 `:50-107,412-435`: compile argvは一部3 TUの集計で、全TUの `translation_units`、canonical `compile_commands`、identityを保存しない。
- 同 `:437-452` と `:351-367`: executableのinode、per-run `exec_witness`、9点 `binary_rehash`、dynamic deps、ELF interpreterを取得しない。
- 同 `:327-345`: `ps`/load1診断のみで、`exclusivity.raw` と scheduler accounting trace を受領証形式で取得しない。
- 同 `:486-523`: markerは単純な state file、actual argv raw、36観測窓、canonical schedule、wait traceを保存しない。
- `t139_r4_env_probe.py:1135-1191`: `/proc/stat` と monotonic time は取得するが、13窓の独立環境 probeであり、本走36窓のreceipt producerではない。
- 影響: 凍結後に追加collector/driverを作らない限り、実測値は certified選択へ投入できず、材料レポートの証拠参照も埋まらない。

### 所見 12 — 裁定パッケージの「exact 1:1」「承認可能」は過大

[must-fix] `package.md` の修正完了主張は schema の実体と一致しない。

- 根拠: `package.md:19-24` は「exact 1:1」「承認可能水準」とするが、所見1の `runs[] maxItems:36` が文書の288 run要件と衝突する。なお `package.md:147-159` の未解決事項は非保証として正直に列挙されている。
- 構成例: approval manifest がこの schema digestをpinし、正しい288-run pilot receiptを投入する。
- 影響: approval後の validator は正当な pilot を拒否し、また schema-only consumerなら短縮receiptを受理する。certified選択・材料レポート・試行台帳の全てが停止または汚染される。

### 所見 13 — 算術誤記は nit だが凍結前に直すべき

[nit] 検証割当ての非余裕小計 `2340` は `2640` の誤記。

- 根拠: `addendum-a-reissue.md:115,133`、`package.md:165-167`。
- 構成例: Bの internal contingency を `660` とする計算と `2340+660=3000` を混在させる。
- 影響: phase cap自体は変わらなくても、監査時の requested walltime・contingency説明・材料レポートの算術参照が分岐する。

## 既知の非保証との区別

`record-items-v2.md:657-665` が明示する「producerが preflight raw を作れば未実行に見せられる」残余は、今回の新規件数には含めていない。所見8は、その明記より広い valid-shaped counter も同じ第三分岐に入る点である。

## 総括

GO/NO-GO: **NO-GO**
blocker 件数: **4**
新しく開いた偽装経路の件数: **2**
正当な測定が記録不能になる箇所の件数: **6**