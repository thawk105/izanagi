## 所見一覧

### [重大度 must-fix] 非 canonical evidence の表示が raw・測定対象・現行実装を正確に束縛していない

- どこ: `tools/pegasus/admission_registry.json:4-8`、`docs/pegasus-runbook.md:453-460`、`measure-evidence/README.md:1-16`
- 何が食い違うか: `19.7 MiB` と `147.7 MiB` の算術は正しいが、「5 valid runs」は全走 `rc=2` だった事実を隠し、測定 commit、`limit_reached=true`、母集団、実読取量を欠く。さらに測った commit `04d85f93` の両 tool は統合 commit で計 305 行変更されており、現行 bytes の測定ではない。
- **成果物影響:** 現行 `41afc4d0` の実行体に 147.7 MiB の証拠が付いたように読め、後続の admission 判断が旧実装・不成功走を根拠にする。
- 根拠: ledger 6 走はすべて `rc=2`、選択は 25 files・4,728,545 bytes・`limit_reached=true`。母集団は 1,045 files だが総量は job 間で 1,400,124,799 bytes と 1,400,913,353 bytes に変動している。`git diff 04d85f93 41afc4d0` は ledger 266 行、collector 39 行の変更。
- 対応案: **本 wave で直す。** `valid runs` を `5 positive-delta samples; all command rc=2` とし、測定 commit、25/1,045 files、実読取 bytes、cap 到達を明記する。現行実装を再測定するまで `certified` ではなく「非 certifying な式適用値」と表現する。

### [重大度 must-fix] raw README が数値・分類・canonical 性を誤表示している

- どこ: `output/insights/2026-08-13_exec-loc-and-usage-fixes/measure-evidence/README.md:1,14-16`
- 何が食い違うか: 見出しは「§7.0 実測」、判定は `local-ok 相当`、数値は `20.6 MiB` と約 `149 MiB` だが、raw は非専有 shared-service delta、正値は 19.7 MiB と 147.7 MiB である。
- **成果物影響:** 一次資料を直接読む consumer が registry/runbook と逆の分類を引き、`unknown` の受理集合を将来 `local-ok` へ誤って広げ得る。
- 根拠: `measure-evidence/README.md:23-29` 自身が shared `nqs-jsv.service` と負 delta 混入を認める。20,635,648 bytes は 20.635648 MB だが 19.6796875 MiB。
- 対応案: **本 wave で直す。** 見出しを「非 canonical 補助観測」にし、`local-ok 相当` を削除、単位と値を訂正する。

### [重大度 must-fix] 「委任」注記が D233 の全面禁止を非 canonical 測定だけ許す規則へ狭めている

- どこ: `docs/pegasus-runbook.md:509-540`、`docs/decisions.md:10936-10939`、`docs/failures.md:4432-4464`
- 何が食い違うか: D233 は「分類の実測はユーザー端末の手番であり、AI は行わない」と方式を限定せず禁止する。一方、追加注記は AI の選択委任下で計算ノード測定を行った事実を evidence として採用し、禁止を「専有 scope 測定を自ら実行してよい意味ではない」に狭めている。これは shared-cgroup 測定なら AI が実行してよい、という抜け道になる。
- **成果物影響:** registry の evidence 参照集合へ権限外の測定結果が入り、F159 の恒久対応が同じ分類作業で再び無効になる。
- 根拠: `tools/README.md:14-16` も「AI・自動化は測らず依頼する」と全面禁止。`measure.sh:7-10`、`measure2.sh:7-10` は明示的に分類測定 job として実行されている。
- 対応案: **本 wave では evidence 採用を止める。** 委任範囲の変更は `s4-rulings-package.md` R-3 へ返し、ユーザーが当該 raw の採用を明示裁定するまで旧 `unmeasured` 相当へ戻す。少なくとも runbook に新しい例外を既成事実として置かない。

### [重大度 must-fix] rc 0/1/2/3 契約が D220 の非 gate 性と supervisor の非 0 停止契約に結線されていない

- どこ: `tools/collect_wave_usage.py:38-50,230-247`、`docs/dev-wave/core.md:107-123`、`docs/README.md:78-81`
- 何が食い違うか: helper は「正当な不実行」である確証済み login block を rc=3 にしたが、`DW-CTX` は process の非 0 終了で fail-closed 停止する。`DW-S09` は単に helper を実行せよとだけ書き、rc=3 を post-gate 記録として扱う caller は repo 内に存在しない。D220 は収集失敗を wave 完了 gate にしない。
- **成果物影響:** `blocked` artifact は保存されても外部 supervisor が次 wave を開始せず、非 gate の工数台帳が開発フローの受理集合を縮める。
- 根拠: repo 全検索で production caller は `DW-S09` の文書参照だけ。テストは helper 単体の rc を固定するが supervisor 結線を検査しない。`docs/README.md` は rc と `--project=<slug>` を記載しておらず、段 4 裁定 §3/C6 の更新要求も未履行。
- 対応案: **本 wave で docs/README と呼出し契約を直す。** 段 9 成功後の collector rc は artifact の `collection.status` と併読し、rc=3 を wave 失敗へ伝播させないことを明記・検査する。supervisor 改修が必要なら裁定パッケージへ返す。

### [重大度 must-fix] replica の selector 判定を代表 member だけで行い、wave 帰属を誤る

- どこ: `tools/claude_session_ledger.py:896-905,1207-1229`、`orchestrator/tests/test_claude_session_ledger.py:839-872`
- 何が食い違うか: root/sidechain 帰属は group 全 member を見る一方、`cwd_under`・時間窓の `_selected()` は dominance で選ばれた代表の `terminal_meta` だけを見る。member 間の cwd・timestamp 一致は検証していない。
- **成果物影響:** 対象 worktree に属する replica があっても代表が範囲外なら model call/token が欠落し、逆なら別 wave の値が混入する。
- 根拠: `planned_sidechain` は group 全体から算出するが、selector 用の component metadata は無い。既存 `test_cross_bucket_replica_is_attributed_to_root_once` は member 間で selector metadata を変えていない。
- 対応案: **本 wave で直す。** group 内の selector verdict が不一致なら fail-closed collision とするか、採用する any/all-member 規則を裁定して実装する。nodeid 案: `test_cross_file_replica_with_divergent_cwd_selection_fails_closed`、`test_cross_file_replica_with_equal_selector_identity_counts_once`。

### [重大度 should-fix] schema 意味変更の consumer 文書と比較契約が不足している

- どこ: `tools/claude_session_ledger.py:1040-1052`、`tools/collect_wave_usage.py:79-100`、`docs/README.md:78-81`
- 何が食い違うか: schema v2 の集計意味を cross-file dedup へ変更し、新フィールドを追加したが `schema_version` は 2、外側 typed artifact は v1 のまま。`dedup_algorithm_version` で旧 report と区別はできるものの、docs は新しい同一性公理・比較不能性を説明していない。
- **成果物影響:** 旧新の token 値を同じ schema 世代として比較し、dedup による段差を使用量改善と誤認し得る。
- 根拠: repo 内 reader は `collect_wave_usage.py` と関連テストだけで、独立 validator/report reader は無い。したがって取り残された production reader は見つからないが、外部 typed artifact consumer の契約も存在しない。
- 対応案: **本 wave で docs/README に公理と比較条件を追記する。** schema bump が不要なら「v2 は additive、比較可否は dedup version 必須」を明文化する。

### [重大度 should-fix] dominance の裁定文が実装・正例と自己矛盾する

- どこ: `s4-adjudication.md:73-75,86-92`、`tools/claude_session_ledger.py:871-898`、統合 commit 本文
- 何が食い違うか: 裁定と commit 本文は「支配 member が一意でなければ fatal」と書くが、等値 replica は全 member が相互に支配し、実装は複数 candidate から決定的に 1 件を選んで受理する。
- **成果物影響:** prose を正本として将来実装を直すと、実測群1の等値4 replicaが再び `message_id_collision` となり台帳が欠測する。
- 根拠: `test_replicated_message_id_with_identical_usage_counts_once` は等値4件を rc=0、1回計上として固定している。
- 対応案: **本 wave で文言を修正。** 「支配 candidate が存在しない場合は fatal。複数 candidate が同値なら deterministic tie-break」とする。実装側は裁定意図に対する改善である。

### [重大度 should-fix] evidence 真正性と一部内部保証は変異で発火しない

- どこ: `orchestrator/tests/test_check_docs.py:1244-1325`、`orchestrator/tests/test_hooks.py:1753-1759`、`orchestrator/tests/test_claude_session_ledger.py:875-911`
- 何が効かないか: registry/runbook/golden の文字列同期は検査するが、raw の base/peak/rc/input/commit は一切読まない。raw bytes を改変しても新規テストは落ちない。また request collision test は `planned_invalid.update(group)` と component 展開が同じ replica 全体を重複して invalid 化するため、一方を除去する変異が生存する。
- **成果物影響:** evidence 数値が一次資料から乖離しても公表台帳は受理され、内部の「全 replica invalid 化」保証も実際の検出力以上に強く見える。
- 根拠: 新規 check_docs test は sentinel と投影集合だけを検査する。`test_request_collision_invalidates_representative_and_all_replicas` は最終 metrics だけを観測し、invalid 集合を直接観測しない。
- 対応案: raw evidence は immutable digest＋小さい再計算 checkerで束縛するか、人手検算のみであることを明示する。後者の test は冗長実装を削るか planner の結果を直接固定する。これは本 wave で直せなければ裁定パッケージへ返す。

### [重大度 should-fix] 実 30 collision 群の全解決は未確認であり、「修正済み」と一般化できない

- どこ: `s4-adjudication.md:94-96`、`s5-unitB.md:61-68`、`tools/claude_session_ledger.py:31-42`
- 何が未達か: 正例は実測群を模した2群だけで、raw が報告した30群すべてを現行 resolverへ通していない。全母集団は1,045 filesだが CLI hard capは1,000、実測時は25 filesで cap 到達している。
- **成果物影響:** 未対応の1群でも残れば ledger rc=2、collector は `incomplete`/rc=1となり、その wave の使用量 artifact は採用不能になる。
- 根拠: 段4・実装子とも未確認を自己申告している。統合 commit の「並列 subagent の transcript を直す」は、その範囲を超えて読める。
- 対応案: 本 wave の受入結果は「合成2群で実装、実観測30群は未確認」と限定する。権限・実行場所裁定後に、固定した同一入力 snapshotで30群の結果を確認する。

## evidence 数値の検算結果

対象 argv は両 job とも `python3 tools/claude_session_ledger.py --json`。測定 commit は `04d85f93ef7b8788e75e1f4897dfa5aca0ef254c` で、統合 commit の親と当該2 toolの bytesは同じだった。

| 走 | peak − base | MiB |
|---|---:|---:|
| run1-1 | 842,317,824 − 821,682,176 = 20,635,648 B | 19.6796875 |
| run1-2 | 842,268,672 − 830,062,592 = 12,206,080 B | 11.640625 |
| run1-3 | 842,395,648 − 829,915,136 = 12,480,512 B | 11.90234375 |
| run2-1 | 4,230,475,776 − 4,211,462,144 = 19,013,632 B | 18.1328125 |
| run2-2 | 3,853,193,216 − 3,884,523,520 = −31,330,304 B | −29.87890625 |
| run2-3 | 3,690,270,720 − 3,678,195,712 = 12,075,008 B | 11.515625 |

したがって正 delta は5走、負 delta除外は1走で一致する。最大値は:

- `20,635,648 / 1,048,576 = 19.6796875 MiB` → 小数1桁で `19.7 MiB`
- SI単位なら `20,635,648 / 1,000,000 = 20.635648 MB` → `20.6 MB`
- 25% margin は `4.919921875 MiB` なので、`max(25%, 128 MiB) = 128 MiB`
- `19.6796875 + 128 = 147.6796875 MiB` → `147.7 MiB`

よって registry/runbook の `19.7 MiB` と `147.7 MiB` は算術上正しい。raw README の `20.6 MiB` と「約149 MiB」は誤りである。ただし5走すべて command rc=2であり、これは「成功した ledger 走」ではなく「正 delta を得たメモリ sample 5件」である。

入力母集団は両 ledger jobで1,045 files、総量は約1.40 GB。ただし実際の report は既定 capにより25 files、4,728,545 bytesだけを読み、`limit_reached=true` だった。この区別は現 evidence に不足している。

## 裁定からの逸脱一覧

- 外側 argv 正規化を実装していない: **裁定どおり。** split形 `--project -slug` はrc=2、等号形は正例で受理される。
- `class == unknown`: **裁定どおり。** hookの受理集合は広がっていない。
- `docs/dev-wave/core.md` 未変更: **C6の裁定どおり。** ただしrc非0と`DW-CTX`の衝突は未解消で、裁定パッケージまたはREADME契約が必要。
- s4 §3の「外側等号形とrc契約をdocs/READMEへ明記」: **要件未達。must-fix。**
- s4 §2の「message.id公理をreport schemaとdocsへ書く」: report内には入ったがdocsは未更新。**部分未達。must-fix。**
- s4 §4の evidence に「入力母集団1,045 files / 1.40 GB」を含める: **未達。must-fix。**
- dominanceの同値tie-break: literalな「一意支配」からは逸脱するが、等値replica正例を受理するための**改善**。prose修正が必要。
- 実30群の未確認: 裁定が明示した残余であり逸脱ではない。ただし完了主張へ昇格させてはならない。
- F161: rc縮小には `complete→0`、`--help→0`、通常slugの正例があり、dash拒否には `test_leading_dash_project_slug_reaches_collector_intact` がある。指定2箇所について正例欠落の再発は見つからない。

## 総括

本 wave は、内側 argv の等号化、rcのfail-closed化、replica resolver、registryの`unknown`据置と投影同期までは実装している。しかし land 前に止めるべき問題が残る。最大のものは、D233が禁止するAIによる分類測定を「非 canonical 補助証拠」として実質的に採用したこと、旧実装・全走rc=2の観測を現行toolの「5 valid runs」と表示したこと、rc非0とsupervisor停止契約が未結線なこと、replica selectorを代表memberだけで判定することの4点である。

pytestは本レビューでは実走していない。静的検査上、実1,045-file母集団で観測された30 collision群がすべて解けるとは確認できず、正直な到達点は「合成fixtureで主要2形を固定したが、実入力全群と段9運用は未完了」である。