結論は **NO-GO** です。段 2 の中核判断は正しい一方、durable intent の逐語根拠と、後発の Q1/Q2 裁定の扱いには補正が必要です。Web、pytest、build、qsub は実行しておらず、書込みもしていません。

## 所見

[A-01] (P1) は R3 (a) に適合せず、最終受理集合は空のまま

- 種別: 正しさ境界
- 根拠: [s1-brief.md](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t139-land2-q4/s1-brief.md:80) は #4〜#6 未実装と認めつつ、所有層の正例を代用する。R3 は [package.md](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t139-land2-q4/output/insights/2026-08-12_t139-land2-s4/package.md:67) で「受理集合が空の gate を認めない」とした。D264 も [docs/decisions.md](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t139-land2-q4/docs/decisions.md:12203) で恒真 deny stub を却下している。
- 成果物影響: `owned_layer_ready` が変わっても、driver handoff を生成する最終受理集合 `A` は `∅` のままである。
- 深刻度: blocker
- 提案: #4〜#6 を実装して実 binding を通る正例を作るか、`submit_pilot` の export と解除 decision を延期する。

[A-02] 「4 実装すべてを区別できる」は偽

- 種別: 過大主張
- 根拠: [s2-plan.md](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t139-land2-q4/s2-plan.md:202) の表どおり、正しい staged gate と「所有層の診断だけ計算し、binding を検査せず最後に P04〜P06 を定数追加して deny する gate」は区別不能である。正しい gate と `a09` / `a12` 不在で拒否する gate も、R3 の観測対象である最終 `A` ではともに常時 block である。無入力 `raise` だけは structured result 検査で区別できる。
- 成果物影響: テストが診断値 `O` の差を検出しても、恒真 deny の最終受理集合 `A=∅` を正しい gate から分離できない。
- 深刻度: blocker
- 提案: 現 scope 内でこの区別不能性を消す設計は無い。white-box の call-count や branch 検査は `A` の正例を作らず、R3 の代替にならない。

[A-03] 発火しない保証が複数残る

- 種別: 恒真
- 根拠: [s1-brief.md](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t139-land2-q4/s1-brief.md:95) と [s2-plan.md](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t139-land2-q4/s2-plan.md:261)。land 前に発火しないものは、① canonical marker 条件付き検査、②公開 resolver の canonical-positive branch、③ `dispatch_handoff_created` の正例、④公開 `submit_pilot` 経由の intent / handoff durability、⑤ genuine handoff から driver / collector までの end-to-end 束縛、⑥ decision と検査の同一 land 検査である。fixture は private parser だけを通す。
- 成果物影響: release payload、intent、handoff、同一-land参照が誤っていても、land 前の受入結果は変わらない。
- 深刻度: blocker
- 提案: 条件付き smoke を検出力に数えない。exact な projected-fold commit を隔離 repo の canonical `main` として production resolver まで通し、land 後 OID がその tested commit と一致する仕組みを用意するか、解除を延期する。

[A-04] NO-GO 骨子 3 の「認可成功後」は承認済み逐語ではない

- 種別: 事実誤り
- 根拠: [record-items-v2.md](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t139-land2-q4/output/insights/2026-08-11_t139-manifest-land1/record-items-v2.md:470) が固定する順序は「intent は qsub より前」と exact 被覆だけである。[s2-plan.md](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t139-land2-q4/s2-plan.md:217) の「最終 admission 成功後」はプラン子の設計解釈である。
- 成果物影響: 承認済み順序は `intent < qsub` であり、`authorization < intent < qsub` まで固定した参照にはならない。
- 深刻度: must-fix
- 提案: 「認可成功後」は新 gate の設計契約として別に固定する。なお deny 前に durable submission intent を書くと、exact 被覆と必須 `qsub_result` を満たす admission-reject row が無いため孤児化する、という結論自体は妥当である。

[A-05] D264 テスト期待値の緩和は規律 2 違反になる

- 種別: 規律違反
- 根拠: D264 は [docs/decisions.md](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t139-land2-q4/docs/decisions.md:12187) で gate 完成まで `submit_pilot` 非 export を固定し、D282 も [同ファイル](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t139-land2-q4/docs/decisions.md:12888) でこれを preserve している。プランは [s2-plan.md](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t139-land2-q4/s2-plan.md:180) で禁止集合から `submit_pilot` を削除する。
- 成果物影響: 公開 API 集合だけが増える一方、最終受理集合は `∅` のままで、恒真 deny stub を「実装済み」に見せる。
- 深刻度: blocker
- 提案: 実 binding 正例が通るまで export と既存期待値を変えない。`skip` / `xfail` や production fail-open の提案は見つからなかったが、この期待値変更自体が検査を甘くする変更である。

[A-06] D308 は pilot 解除の直接根拠ではない

- 種別: 事実誤り
- 根拠: D308 の決定本文は [docs/decisions.md](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t139-land2-q4/docs/decisions.md:14176) で「床値 build の compiler site 依存化」と「registered calibration の toolchain 束縛検査」に限定される。pilot の同一-land義務の直接根拠は [第 2 束控え](/work/1/SFC/tanab/dev-wave-jobs/rulings-inbox/2026-08-12-second-batch-11rulings.md:21) の Q4 である。
- 成果物影響: pilot の同一-land参照元が D308 から Q4 裁定へ変わり、D308 だけを検査しても pilot bundle の完全性は保証されない。
- 深刻度: must-fix
- 提案: D308 は一般化の類例として引用し、pilot の権威は Q4 の逐語に置く。

[A-07] 同一 land は機械執行されず、分割時の受理集合説明も不正確

- 種別: 正しさ境界
- 根拠: プラン自身が [s2-plan.md](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t139-land2-q4/s2-plan.md:104) で同居検査を追加しないとする。一方 brief は [s1-brief.md](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t139-land2-q4/s1-brief.md:128) で「解除だけなら受理集合が広がる」と断言する。
- 成果物影響: 解除だけなら canonical な許可状態は `forbidden → permitted_only_via_submit_pilot` へ動くが、gate 不在または #4〜#6 の恒真 deny 下では実 handoff の `A` は `∅` のまま。検査だけ、または mechanism だけなら許可状態も `A` も不変である。ただし後続の部分実装が release を読める規範窓は開く。
- 深刻度: blocker
- 提案: 許可状態と operational `A` を分けて記録し、decision fold・export・production gate・束縛検査の同一 transaction を OID で検査する。

[A-08] canonical resolver に replace / graft / shallow 履歴の拒否が欠ける

- 種別: 正しさ境界
- 根拠: [s2-plan.md](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t139-land2-q4/s2-plan.md:96) は環境除去と main race だけを指定する。承認済み §6.7 は [record-items-v2.md](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t139-land2-q4/output/insights/2026-08-11_t139-manifest-land1/record-items-v2.md:656) で shallow / replace ref / graft を拒否する。既存 `blobref.py` も `GIT_NO_REPLACE_OBJECTS` と safe-history 検査を持つ。
- 成果物影響: replace object 等が `refs/heads/main:docs/decisions.md` の解決結果を差し替えると、canonical fold の無い payload で P01 が satisfied へ変わる。
- 深刻度: blocker
- 提案: 既存 hardened Git resolver と safe-history 検査を再利用し、PATH shadow・replace・graft・shallow を各々変異する。

[A-09] §8 の umbrella test は署名検査だけでは恒真化できる

- 種別: 恒真
- 根拠: §8 は [record-items-v2.md](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t139-land2-q4/output/insights/2026-08-11_t139-manifest-land1/record-items-v2.md:784) で各 producer field を受理入力にしたら落とすテストを要求する。プランは [s2-plan.md](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t139-land2-q4/s2-plan.md:239) に一つの総称テスト名を置くだけである。
- 成果物影響: API 引数に field が無くても、artifact から `claim_scope`、`reason_code`、`returncode`、`fixed_inputs`、各 digest、compile 申告値を読めば `A` が producer 選択になる。
- 深刻度: must-fix
- 提案: 各 field ごとに、raw evidence を固定したまま申告値だけを反転し、受理結果が不変であることを独立変異で検査する。現プラン本文に、これらを admission 入力へ使う明示経路自体は無い。

[A-10] 「`dispatch_pilot` だけが qsub」は保証できない

- 種別: 過大主張 / 事実誤り
- 根拠: [s2-plan.md](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t139-land2-q4/s2-plan.md:140) に対し、既存 [dispatch_compute.py](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t139-land2-q4/tools/pegasus/dispatch_compute.py:1477) は一般 qsub 経路を持つ。§9 も [record-items-v2.md](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t139-land2-q4/output/insights/2026-08-11_t139-manifest-land1/record-items-v2.md:817) で台帳外投入は見えないと明記する。先行 wave の正しい境界は [README.md](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t139-land2-q4/output/insights/2026-08-12_t139-land2-s4/README.md:73) にある。
- 成果物影響: qsub 可能経路集合には direct qsub / 別 wrapper が残る。防げるのは、それらの raw output が valid run record・材料 report・certified 選択へ昇格することまでである。
- 深刻度: must-fix
- 提案: 「新設する T-139 official submitter 内では唯一」と限定し、driver preflight と下流 promotion gate を保証境界にする。なお canonical F238 は [docs/failures.md](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t139-land2-q4/docs/failures.md:5993) の別件であり、この所見の参照 ID としては誤りである。

[A-11] 第 7 束が第 2 束を後発上書きしており、現 brief の scope は stale

- 種別: 事実誤り
- 根拠: 第 2 束は [2026-08-12 control](/work/1/SFC/tanab/dev-wave-jobs/rulings-inbox/2026-08-12-second-batch-11rulings.md:15) で Q1/Q2 を「機構を新設しない」とした。第 7 束は翌日の [2026-08-13 control](/work/1/SFC/tanab/dev-wave-jobs/rulings-inbox/2026-08-13-rulings8-batch.md:18) で同じ T-139 Q1〜Q6 を明示再選択し、Q1=(a)、Q2=(a) 固定 envelope + namespaced projection、Q4=(a) とした。
- 成果物影響: scope 上の #4〜#6 は「実装禁止」から「Q1 decision 後に manifest + resolver + writer + validator + vectors として実装」へ動く。ただし canonical fold 前なので、D292 の gate authority はまだ変わらず `A=∅` である。
- 深刻度: blocker
- 提案: scope 裁定としては第 7 束が後発であり、第 2 束を上書きしたと判定する。追加のユーザー裁定は不要だが、Q1 の canonical decision → #4〜#6 の実装 session → 投入経路 session の順で brief を作り直す。外部控えを release authority として読むことは依然禁止する。

[A-12] 代案 2 は解除先行禁止には違反しないが、無断の scope 縮小である

- 種別: 正しさ境界
- 根拠: 代案 2 は [s2-plan.md](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t139-land2-q4/s2-plan.md:226) で schedule / driver / collector のみに限定し、release と export を延期する。第 2 束 Q4 が禁止するのは [control](/work/1/SFC/tanab/dev-wave-jobs/rulings-inbox/2026-08-12-second-batch-11rulings.md:23) の「解除 decision だけを先に land」である。
- 成果物影響: operational asset の参照は増えるが、canonical 許可状態と admission `A` はともに変わらない。
- 深刻度: must-fix
- 提案: 安全禁止には適合する。ただし Q4 の成果物を減らすため、親が一存で採らず明示的な再 scope として裁定する。

[A-13] M6 の pin 閉包は path 検索だけで打ち切られている

- 種別: 事実誤り
- 根拠: [s1-brief.md](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t139-land2-q4/s1-brief.md:50) は path hit 2 file を閉包とするが、[approval_payload.py](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t139-land2-q4/orchestrator/preregistration/approval_payload.py:16) は role 集合と D282 decision blob 全体を production trust root として pin する。`DW-O09` も role-key 側の検索を要求する。
- 成果物影響: 参照・pin consumer 集合が「test 2 file」から production parser / decision-blob trust root を含む集合へ増え、所有漏れで D282 解決値が変わり得る。
- 深刻度: must-fix
- 提案: path に加えて role 名、各 SHA-256、`D282_DECISIONS_REF`、全体 decision pin を検索し直す。

[A-14] M8 の production caller 0 件は字義どおりには偽

- 種別: 事実誤り
- 根拠: [s1-brief.md](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t139-land2-q4/s1-brief.md:53) に対し、非 test caller は `orchestrator/publication/approval_d291.py:18`、`approval_guard.py:15`、`addendum_p_envelope.py:9`、`tools/pegasus/run_t139_a12_stress_check.py:16` の少なくとも 4 件ある。
- 成果物影響: consumer 集合は `∅` ではなく 4 件となり、leaf module の変更に対する回帰監査対象が増える。
- 深刻度: must-fix
- 提案: 「既存 preregistration leaf の production caller は4件、pilot admission の production caller は0件」と限定する。

[A-15] `submission.py:150` の単発 write は既に解消済み

- 種別: 事実誤り
- 根拠: brief は [s1-brief.md](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t139-land2-q4/s1-brief.md:24) で単発 `os.write` とするが、現行 [submission.py](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t139-land2-q4/orchestrator/qualification/submission.py:150) は `while offset < len(data)` の short-write loop と file / directory fsync を持つ。
- 成果物影響: 既知欠陥集合から「単発 write」は消える。read-back 不在は残るが、admission 受理集合は変わらない。
- 深刻度: nit
- 提案: stale な R5 記述を削り、残余を read-back 不在に限定する。

## 段 2 NO-GO の骨子 1〜5

1. `A` と `O` の区別: **正しい**。R3 が要求するのは最終 admission の非空正例である。
2. 常時 deny との区別不能: **正しい**。純粋な固定結果は診断負例で捕捉できても、診断だけ計算して最終 deny を固定する実装は区別できない。
3. durable intent の順序: **一部誤り**。「認可成功後」は逐語ではない。ただし deny 前の durable submission intent は exact 被覆と `qsub_result` 契約に収まらない。
4. fixture と canonical fold の差: **正しい**。fixture は parser 正例であり D292 の authority 正例ではない。
5. D264 の恒真 deny stub 却下: **正しい**。逐語で明示されている。

現 scopeのまま「常に deny」との区別不能性を消す設計はありません。#4〜#6 を完成させるか、gate / export / release を延期する必要があります。

## 反証できなかった点

- D292 が列挙する spool fragment、handoff、環境変数、caller 供給 root、wave 自己申告を authority にする経路は、条件付きプラン本文にはありません。A-08 の safe-history 漏れは別の authority bypass です。
- `claim_scope`、`declared_use_class`、`reason_code`、`qsub_result.returncode`、`fixed_inputs`、`composed_core_sha256`、`schedule_sha256`、`arms.*.compile.*` を明示的に admission 入力にする設計はありません。
- D282 / D291 が承認する既存 bytes を編集する path はプランにありません。実 bytes の SHA-256 も D282 / D291 の値と一致しました。
- M1、M2、M3、M4、M5、M7 の file 実在・行数、M9 の「D番号は fold まで未確定」は一次資料と一致しました。
- §3.1 の #1 / #4〜#9 未充足は producer の `claim_scope` を除外して再検索しても一致しました。ただし「scope 外」の分類は A-11 の後発裁定により stale です。
- `skip` / `xfail` で赤を隠す提案、または production を fail-open に倒す提案は見つかりませんでした。
- schedule の純関数検査、#4〜#6 の deny 負例、直接呼び出す submitter / collector の形状検査は発火可能であり、恒真検査には含めていません。

## 判定

**NO-GO**  
理由1: #4〜#6 未実装のままでは最終受理集合が空で、R3 と D264 に違反する。  
理由2: canonical-positive・intent・同一-landの主要保証が land 前に発火しない。  
理由3: 後発の第7束が Q1/Q2/Q4 を再裁定しており、現 brief の scope と実行順が stale である。

## 総括

- 本 wave は現 brief のまま段 5 へ進めてはならない。
- 段 2 の NO-GO の中心結論は維持される。
- 所有層の ready は admission の正例ではない。
- 最終受理集合は #4〜#6 が無い限り空である。
- 恒真 deny を本物の gate から分離する in-scope 設計は無い。
- fixture decision は canonical fold の正例にならない。
- 条件付き marker 検査は land 前には検出力を持たない。
- durable intent の「認可成功後」は承認済み逐語ではなく新設契約である。
- D264 の禁止期待値を先に緩めると半実装を公開する。
- D308 は pilot の直接権威ではなく、Q4 裁定を引く必要がある。
- release だけの land は許可状態を動かすが、現時点の operational `A` は空のままである。
- direct qsub 自体を `submit_pilot` だけへ閉じる保証はできない。
- 保証できる境界は、不正経路の成果を certified 選択へ昇格させないことまでである。
- 第7束は第2束より後発で、同じ Q1〜Q6 を明示的に再裁定している。
- scope 上は第7束を後発上書きとして扱うべきである。
- ただし canonical fold 前の控えを D292 の release authority にしてはならない。
- 次は Q1 canonical decision、#4〜#6 実装、投入経路の順に組み直す必要がある。
- assets-only 代案は安全側だが、親だけで決められる scope ではない。
- Web、pytest、build、qsub、pilot 投入は実行していない。
- 本レビューは read-only の静的検査であり、未実走検査を緑とは報告していない。