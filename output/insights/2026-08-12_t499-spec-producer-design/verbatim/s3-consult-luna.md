静的検査のみです。pytest、producer、floor、oracle 本走は実行していません。

結論として、現案は最終承認パッケージとしては未成立です。特に active freeze 不在、official guard 閉鎖、ccbench pin の世代差、D302 択一の誤った前提、generator hash の即時失効が must-fix です。

### 所見 1 — spec 承認だけでは 8b 本走は開かない

**所見**

「spec を承認すれば manifest candidate → 本走へ進める」という筋書きは成立しません。現時点で active ratified freeze v2 は存在せず、floor/budget も null です。

**根拠**

`orchestrator/campaign/s8b_ratified_freeze.py:1214-1256` は live pointer がなければ `no-active` を送出し、`load_ratified_freeze` も同 `:1315-1334` を通じて拒否します。現 tree の `output/s8b-freeze` には v2 generation、approval、active pointer がなく、現存する freeze は v1 です。

`build_approved_manifest` は spec より先に active freeze を読むため、`orchestrator/campaign/s8b_oracle_manifest.py:1170-1188` で停止します。さらに `s8b_oracle_driver.py:469-472` は floor または budget が null なら v2 実走を拒否します。

`docs/phase3.md:77-82` は floor 再測定 → v2 再凍結 → oracle の順序を要求し、同 `:118-122` は pilot 成果物を `eligible_for_refreeze=false` としています。official floor は `orchestrator/campaign/s8b_floor_campaign.py:210-220,3691-3698` で拒否されます。8b 側の優先度低下も `docs/phase3.md:129-135` に明記されています。

**real か refuted か**

real。プランは active freeze を必要条件として列挙していますが、承認後の実行順序と現在の official gate 閉鎖を、承認判断の阻害条件として十分に強調していません。

**成果物影響**

放置すると certified 選択集合は空のままで、manifest candidate、oracle ledger、judge/report の certified 出力は生成されません。

**提案**

承認を「設計値の暫定承認」と「active freeze・binding・環境・source hash を含む最終 exact spec 承認」に分離し、後者の前提として official floor、v2 pointer、floor/budget、full verify を明記してください。

### 所見 2 — holdout/configuration は「v2 で変わりうる条件付き値」ではない

**所見**

現行 validator の下では、valid な v2 freeze は v1 の holdout と configuration 集合を変更できません。プランの「将来の active freeze から導出し、変わりうる」という表現は過度に不確定です。

**根拠**

v1→g1 の変更許可集合に holdout/configuration subtree は含まれません（`orchestrator/campaign/s8b_ratified_freeze.py:127-133`）。許可外の追加・変更・削除は `:658-675` で拒否され、snapshot も v1 の holdout 集合との一致を要求します（同 `:1044-1049`）。

現 v1 は `rr20`、`rr80` と、両 holdout の六 configuration を持ちます（`output/s8b-freeze/holdout_freeze.json:40,119,141,163,197,235,268,307,386,408,430,479,517,550`）。manifest 側も active freeze の全 holdout、sorted configuration 集合との完全一致を要求します（`orchestrator/campaign/s8b_oracle_manifest.py:1192-1213`）。

**real か refuted か**

real。現時点で active v2 がないため最終 spec は作れませんが、「valid v2 発効時に軸が変わる保証はない」という含意は refuted です。現行 transition 契約では同じ値が機械的に保証されます。

**成果物影響**

誤った条件付き表示を放置すると、ユーザーが不要に軸を選択したり、v1 と異なる軸を承認し、candidate の受理集合と holdout/configuration 参照が `cell-product-mismatch` で空になります。

**提案**

`["rr20","rr80"]` と六 configuration は「ユーザー選択値」ではなく「valid v2 lineage から強制される継承値」と表示してください。active v2 が別 lineage または validator 変更で軸を変える場合だけ、新 spec と再承認を要求します。

### 所見 3 — 現在の値草案では、ユーザーは exact spec を承認できない

**所見**

現案は design choice と最終登録値を同じ承認パッケージに置いています。しかし現在 AI が導出できるのは一部の自由値だけです。

**根拠**

プラン自身が active freeze、binding、generator hash を未確定としています（`s2-plan.md:200-214,228-244,270`）。spec validator は schedule、run contract、binding、generator の全てを検査します（`orchestrator/campaign/s8b_oracle_spec.py:105-177`）。

値の実際の自由度は次のとおりです。

- 設計選択: `n`、master seed、block ID、campaign ID。
- `n` と単一 block から拘束される値: `block_sizes`。
- validator が固定する値: `verify=legacy+s2`、`screening=off`、`bench_max_rounds=1`、`reps=5`、`extime=5`（`orchestrator/campaign/s8b_oracle_manifest.py:221-307,396-427`）。
- active freeze から強制される値: holdout/configuration、binding identity。
- 導出値: schedule SHA。
- 実行時 source から強制される値: generator_versions（同 `:430-470`）。
- active freeze と環境契約に依存する値: env_tag、clocks、contract SHA。

binding は schedule cell ごとの完全一致と hash 再計算が必要です（同 `:487-537`）。実体化には freeze entry と prepared binary が必要です（`orchestrator/campaign/s8b_materialization.py:98-145`）。

**real か refuted か**

real。`n=8`、seed、campaign ID を自由値として扱う点は妥当ですが、現在は最終 exact bytes、binding、active freeze 参照、source snapshot がないため、最終承認は不可能です。

**成果物影響**

今承認しても固定 spec を発行できず、後から値が変われば schedule SHA、binding、manifest の cell 集合、certified report の参照が全て再承認になります。

**提案**

現 wave では自由値の設計判断だけを承認対象にし、最終承認は v2 freeze、floor/budget、12 binding、環境契約、5 source hash、canonical bytes が揃った後の一回に限定してください。

### 所見 4 — ccbench pin は d706 が現 floor との比較用であり、511 必須ではない

**所見**

親の疑いのうち「現在の submodule gitlink 511 と一致しないと oracle は起動できない」は、現行 oracle 経路については refuted です。ただし、プランには「歴史的 floor pin と将来の再測定 pin」を分ける規則がありません。

**根拠**

現存する floor protocol は d706 を記録しています（`output/s8b-freeze/floor_protocol.json:1`）。一方、現在の gitlink と `pin.CURRENT_PIN` は 511 です（`orchestrator/campaign/pin.py:26-28`、`orchestrator/campaign/s8b_approved.py:65-67`）。

新しい floor protocol を組み立てる builder は current gitlink 511 との一致を要求し、protocol にもその値を書きます（`orchestrator/campaign/s8b_floor_campaign.py:432-449,477-507`）。しかし oracle の manifest validator は `ccbench_pin` を非空 identifier としか検査しません（`orchestrator/campaign/s8b_oracle_manifest.py:396-404`）。driver はその pin を isolated worktree の checkout に渡します（`orchestrator/campaign/s8b_oracle_driver.py:1433-1463`、`orchestrator/campaign/s1_direct_comparison.py:500-529`）。buildcache はその一時 worktree の HEAD と宣言 pin を比較します（`orchestrator/campaign/buildcache.py:1892-1915`）。

一方、floor 由来の binary hash は実走前に検査され、pipeline は不一致なら bench 前に abort します（`orchestrator/campaign/s8b_oracle_driver.py:927-949`、`orchestrator/campaign/pipeline.py:608-610,917-932`）。

**real か refuted か**

複合判定です。「本走は必ず 511」は refuted。「既存 floor と同じ d706 を使う意味、将来 511 で再測定した場合の再登録規則が不足」は real です。

**成果物影響**

511 を既存 d706 floor と組み合わせると binary hash mismatch で本走・ledger が止まり、d706 を新 floor の pin と誤って再利用すると certified report が異なる source provenance を参照します。

**提案**

本走 pin を次の規則で明記してください。

- 現在の frozen floor binary と比較する本走は d706。
- floor を 511 で再測定して v2 を作る場合は、511 と新 binary hash を新 freeze/spec に束縛する。
- manifest validator または active freeze projection で、oracle `run_contract.ccbench_pin` と floor artifact の pin を直接照合する。

### 所見 5 — D302 の A/B は現在の test では択一になっていない

**所見**

プランは協調 v2 を推奨していますが、現行 contract test は schema version を見ていません。したがって v1 artifact でも v2 artifact でも、file を置けば同じ assertion が落ちます。

**根拠**

`orchestrator/tests/test_s8b_oracle_manifest_contract.py:128-144` は両 directory を走査して `durable_files == []` を要求するだけで、schema 分岐がありません。プラン自身も `s2-plan.md:175-194` で B でも落ちると認めています。

D302 が直接扱うのは manifest schema であり、schema version 据え置きも明記されています（`docs/decisions.md:13993-14019`）。reviewed spec と official manifest は別 schema authority です（`orchestrator/campaign/s8b_oracle_spec.py:18`、`orchestrator/campaign/s8b_oracle_artifacts.py:20,131-146`）。

**real か refuted か**

real。P2 の「2 directory が判断対象」は正しいですが、「だから B が実効的な択一になる」は refuted です。現状の A は「空のまま維持する」場合に成立し、v1 artifact を発行する A は B と同じ test で落ちます。

**成果物影響**

この誤った択一を実装すると、schema を v2 に変えても candidate/spec の受理集合は開かず、test は赤のままです。test を無条件に緩めれば未検証 durable artifact を受け入れる方向へ受理集合が広がります。

**提案**

本 wave では空 directory と v1 authority を維持してください。将来発行する場合は「schema v2」ではなく、固定 path、receipt、pin、full verify、active freeze を検査する lifecycle gate を別タスクで設計し、その後に artifact ごとの schema version を決めます。

### 所見 6 — consumer の列挙は正しいが、「定数変更だけで追随」は不十分

**所見**

プランは指定された production consumer を列挙しており、単純な取りこぼしはありません。しかし fixture と production の差、official manifest classifier、observations/verdict schema まで含めた end-to-end 契約が必要です。

**根拠**

driver は gate と本走で spec を読む（`orchestrator/campaign/s8b_oracle_driver.py:487-517,1213-1225`）。judge と report も official manifest、active freeze、approved spec を再検証します（`orchestrator/campaign/s8b_oracle_judge.py:364-385`、`orchestrator/campaign/s8b_oracle_report.py:1753-1770`）。manifest builder も active freeze と spec を結合します（`orchestrator/campaign/s8b_oracle_manifest.py:1170-1231`）。

official manifest の schema classifier は v1 を厳密に判定します（`orchestrator/campaign/s8b_oracle_artifacts.py:20-23,131-146`）。fixture は temp root と monkeypatch pin を使い、durable path や active freeze を再現しません（`orchestrator/tests/s8b_oracle_spec_fixture.py:38-113`）。raw golden は v1 literal を保持しています（`orchestrator/tests/test_s8b_oracle_manifest.py:64-100`）。

**real か refuted か**

consumer 名の取りこぼしは refuted。だが、プランの「loader 経由なのでコード構造上追随する」は real な過小評価です。

**成果物影響**

classifier、fixture、golden、judge、report のいずれかを更新し損ねると、manifest は作れても certified observations/verdict/report が生成されず、approved spec や manifest SHA の参照が不一致になります。

**提案**

consumer ごとに入力 schema、再検証、出力 schema、SHA 参照、negative path を表にし、fixture は production 成功の証拠ではないと明記してください。

### 所見 7 — allowed exclusion reasons の意味論が未確定

**所見**

プランは floor の四理由を oracle に流用していますが、oracle validator は四理由を強制していません。リストの形だけを検査しており、driver の failure event と report の `excluded_reason` の対応も定義されていません。

**根拠**

floor 側の閉じた四理由は `orchestrator/campaign/s8b_floor_stats.py:47-53` にあります。oracle spec と manifest は非空・重複なしの文字列だけを要求します（`orchestrator/campaign/s8b_oracle_spec.py:171-177`、`orchestrator/campaign/s8b_oracle_manifest.py:736-744`）。

report は `excluded_reason` が承認リストにない場合にエラーにします（`orchestrator/campaign/s8b_oracle_report.py:386-390,994-1004`）。一方 driver は binding/prepare failure を session event の `reason` として記録し、通常の trial-result の `excluded_reason` は null です（`orchestrator/campaign/s8b_oracle_driver.py:1541-1560`）。

**real か refuted か**

real。四理由を採用する設計自体は可能ですが、「floor 由来だから oracle でも正しい」とは validator から導けません。

**成果物影響**

理由の対応を放置すると、失敗行が除外として certified 選択に残るか、逆に report の protocol violation となって受理集合・ledger の terminal reason・レポート件数が変わります。

**提案**

oracle の閉じた理由表を独立に承認し、driver event、trial-result、judge outcome、report exclusion の対応を一行ずつ定義してください。実装は別タスクです。

### 所見 8 — generator_versions の承認は次の source commit で失効する

**所見**

「schema 実装完了後の clean HEAD から hash を計算する」は開始点であって、有効期間ではありません。5 source のいずれかが次の commit で変われば、既存 spec は失効します。

**根拠**

validator は実ファイルの byte hash と spec の値を毎回比較します（`orchestrator/campaign/s8b_oracle_manifest.py:430-470`）。spec loader もその validator を通ります（`orchestrator/campaign/s8b_oracle_spec.py:258-275`）。

親 brief は直近 30 日 40 commit、直近 14 日 20 commit と報告しています（`s1-brief.md:44-46`）。静的な `git log` では同じ五本の一意 commit は 30 日で 40 件を再現でき、14 日は集計方法により 17 件（一意）または 21 件（path 別合計）でした。件数の差はあるものの、source churn が高いという結論は変わりません。

**real か refuted か**

real。プランの `s2-plan.md:338-344` は field 変更時の再承認を述べていますが、generator source change、active freeze change、floor pin change を明示的な失効条件にしていません。

**成果物影響**

承認済み spec は source hash 不一致で manifest candidate と report の受理から外れ、certified 選択・台帳参照が空になります。

**提案**

有効性を「5 source byte hash、active freeze generation/pointer、floor artifact、環境契約、ccbench pin、exact spec bytes が全て承認時 snapshot と一致する間だけ」と定義してください。どれか一つでも変われば expired として再導出・再承認し、最終承認後は発行 commit まで source を変更しない運用が必要です。

### 所見 9 — 親 brief の M1〜M10、P1〜P3 の検算

**所見**

親 brief の大半は正しいですが、P2 と P3 は修正が必要です。M9 は「manifest validator が exact に固定する」という説明が過度です。

**根拠**

- M1〜M5: durable directory 不在、spec pin が `None`、freeze のみが user commit 対象、zero-file test、candidate builder の存在はそれぞれ `s1-brief.md:25-38` と `s8b_oracle_spec.py:18-23,182-200`、`test_s8b_oracle_manifest_contract.py:128-144`、`s8b_oracle_manifest.py:1170-1231` で支持されます。
- M6: production consumer の列挙は正しいが、fixture は monkeypatch/temp root で production path を検証しません（`s1-brief.md:39-41`、`s8b_oracle_spec_fixture.py:92-113`）。
- M7: receipt + code pin の先例と、receipt 単独を trust root にしない注意はプランの `s2-plan.md:74-95` と整合します。
- M8: 30 日 40 commit は再現でき、14 日の数値だけ集計規則の明記が必要です。
- M9: `verify`、`screening`、`bench_max_rounds`、reps、extime は固定ですが、manifest の `contract_sha256` は `64hex` 形式検査に留まります（`s8b_oracle_manifest.py:396-427`）。env_tag、contract SHA、clocks の実値一致は driver 側です（`s8b_oracle_driver.py:860-887`）。
- M10: active freeze 不在による binding 導出不能は正しい。ただし valid v2 で holdout/configuration が v1 から変わるという含意は誤りです。
- P1 は正しい。`_assert_user_commit` は spec gate にありません。
- P2 は「2 directory を見る」までは正しいが、schema version 分岐があるという前提は誤りです。
- P3 は「AI が自由値を起草する」なら正しいが、「全登録値を導出できる」なら誤りです。

**real か refuted か**

M1〜M8 は概ね real、M9 は実行時には正しいが validator の帰属が部分的に誤り、M10 は binding について real・軸変更の含意は refuted。P1 は real、P2 と P3 は部分的に refuted です。

**成果物影響**

この誤差を残すと、ユーザーが自由値・強制値・未導出値を区別できず、受理されない spec を承認するか、D302 test を誤って緩める判断になります。

**提案**

brief の M9、P2、P3 を上記の区分に修正し、P4 も `no-approved-spec` だけでなく現在の先行 blocker が `no-active-ratified-freeze` であることを追記してください。

## scope 外（本 wave で実装してはいけない事項）

### 所見 10 — scope 侵入は現状の記述上はない

**所見**

producer CLI、schema v2、lifecycle gate、receipt loader、binding 生成、durable 発行、pin 設定、pytest は本 wave で実装してはいけません。

**根拠**

`output/insights/2026-08-12_t499-spec-producer-design/verbatim/s1-brief.md:8-21` が docs + insights のみ、実装差分ゼロ、contract test 緩和禁止を定めています。プランも `s2-plan.md:352-364` でこれらを別タスクへ分離しています。

**real か refuted か**

scope 違反は refuted。プランは設計提案として書いており、現 wave で実装すると明記していません。

**成果物影響**

実装を混入させなければ durable artifact、受理集合、certified 選択、台帳参照は変化しません。これは nit です。

**提案**

B の採用や lifecycle gate の必要性を、この wave の実装完了と誤読されないよう「別タスク起票」に限定してください。

## 総括

must-fix は次の六点です。

1. spec 承認だけでは official guard、active v2、floor/budget、oracle gate は開かない。
2. holdout/configuration は valid v2 では機械的に v1 継承されるため、条件付き設計値として扱わない。
3. binding、active freeze、generator hash がない現時点では exact spec を承認できない。
4. 既存 floor 比較用 pin は d706、将来再測定時の pin は新 floor と再束縛する。
5. D302 の A/B は現行 test では実効的な択一ではない。
6. generator source change を含む明示的な承認失効条件が必要である。

したがって、現段階でユーザーが承認できるのは `n`、seed、block、campaign などの設計候補までであり、oracle 本走を許す exact spec の承認ではありません。