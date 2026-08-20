---
schema: izanagi-spool-v1
ledger: worklog
authored: 2026-08-21
wave: rulings-20260821-self-improve
seq: 1
title: /rulings all (第四回) で entry772・T-287裁定パッケージ・T-1434 handoff由来の計3件の裁定待ち未追跡を発見し新規5件を起票、[T-1446]を更新した (docsのみ、branch worktree-rulings-20260821-self-improve)
---

## 本文

- `/rulings all` を実行し、直近セッション (entry 774「rulings-20260820-third」) 以降の収集を、
  worklog 末尾の直接精査と 3 並列 fork (rulings-inbox 66 件・repo 内外 handoff 28 件・
  phase3.md 現行チェックポイント/見送り台帳/条件付き延期項) で行った。
- entry 774 は自称「764〜770 を精査」だったが、774 自身の branch が受入投入中に local main を
  取り込んだ結果、771〜773 (entry772 の T-1141 自己改善候補、entry773 の T-1434 Wave C) が
  未再走査のまま main へ着地していたと実測した。entry772 本文を直接読み、DW-G03 (受入の
  自動main取り込みが同一fileの非重複行域変更でも `merge-message-provenance` (rc=70) で誤reject
  しうる件) の独立2例目相当が「ユーザー裁定へ返す」と明記されたまま [T-1446] へ未合流だったと
  確認した。
- fork (handoff sweep) が `dev-wave-jobs/handoff/2026-08-20-t1434-wave-c-supervise-collect.md`
  (Wave C 自体は entry773 で着地済み) に、本文へも [T-1446] へも吸収されなかった段8自己改善候補
  2件を発見。うち1件は [T-1452] と同一系列の独立2例目の実証 (新規合流不要)、もう1件
  (変異harness/受入のpre-run clean-tree検査と段7 spool fragment起草のタイミング衝突を
  `DW-M05` か段6の U 節へ明記する候補) は未合流だった。
- `docs/decisions.md` の D607 (2026-08-20、entry763/[T-415]) の「scope外」注記を辿り、
  `output/insights/2026-08-04_t287-checkpoint-values/adjudication-package.md`
  ([T-287] 裁定パッケージ、2026-08-04起票、checkpoint値チャネルの残余4件) のうち D607 が
  閉じたのは §2 (layer3_report 独立readerの値域検査) だけで、§1 (producer側値域検査の
  自己汚染checkpoint非対称)・§3 (in-domain改竄への origin束縛/integrity)・§4 (既存エラーが
  未信頼文字列を下流へ運ぶ、規律6関連)・§5 (`DW-G05` 予算不足候補) の4件が一度も worklog の
  T番号を持たず、2026-08-04 から2週間超 D70 保存則の追跡対象外のまま放置されていたと確認した。
  §6 (受入全走省略条件、waiver W1) は [T-407] の land で自動失効済みと確認し新規起票を見送った。
- `docs/phase3.md` 見送り台帳の [T-1090] (2026-08-15) の再訪条件「[T-1116] の実装完了」を
  [T-1116] 自身の終端記録 (`docs/archive/worklog-phase3-0817-622.md`:「非帰属checkerのR2は
  一度も発効していないと実測で確定し、本項を終端した」) と突き合わせ、[T-1116] は実装でなく
  R2 非発火の実測終端で閉じており「既知赤registryが入ると再走回数の見積りが無効になる」という
  [T-1090] の懸念自体が (registry 自体が作られないため) 別経路で解消済みと判明。台帳の再訪条件
  文言と実態が乖離している。
- fork (rulings-inbox 66件) と fork (phase3.md 起点) はいずれも新規裁定待ち0件を確認した
  (詳細は各 fork の報告、本 fragment には残さない)。
- **自己改善 gate 発火 (収集漏れ2件を実測)**: (a) 前回セッションが自称した既読 entry 範囲
  (「764〜770」) を無検証で信頼し、自 branch が受入中に取り込んだ後続 entry (771〜773) の
  再走査を怠る経路がある。(b) `docs/decisions.md` の「scope外・独立のユーザー裁定を要する」
  注記は現行収集手順のどの項にも収集源として挙がっておらず、そこにしか書かれない残余項目が
  T番号を得ないまま可視性を失う経路がある。`.claude/commands/rulings.md` の該当2箇所
  (収集手順 1・3) を是正したいが、同ファイルは現在 4988/5000 bytes (`COMMAND_LIMITS`) で
  残り12 bytesしかなく、意味を保った追記が収まらない。契約 (`docs/skill-self-improvement.md`
  「予算値を上げる変更は通常の自己改善に含めず、理由付きの独立審査対象にする」) に従い、
  是正は実施せず本 fragment へ候補として記録し独立審査へ回す。

## 次の一手差分

### 更新

- [T-1446] **P3**: docs 予算超過で実装できないまま滞留していた段8自己改善候補の束ね。
  内訳 = `DW-S06-A` (段3の破れ方を段6レビュー観点へ渡す、45 bytes 不足、2026-08-11 起票)・
  `DW-M01` (短絡連結の変異を全体潰し形へ再照準、2026-08-11 起票)・`DW-C00` (待ち手の自己一致
  禁止を汎用待ち手条項へ、150 bytes 不足、DW-G03 の独立2例目、2026-08-11 起票)・`DW-C01`
  (`--reasoning` の段別必須制約、105 bytes 超過、2026-08-20 起票)・[T-1451] (受入投入は段7
  記録commit完了後に行うと明示する候補、`docs/dev-wave/operations.md`のDW-O18近辺または
  `docs/dev-wave/core.md`のDW-S07近辺、一次資料=worklog entry 767、2026-08-20起票)・[T-1452]
  (段5 authorのprompt作成時に`## 総括`見出し必須をDW-S05-Cのprompt必須項目リストへ明示統合
  する候補、一次資料=worklog entry 767、2026-08-20起票、2026-08-20 T-1434 handoffで独立2例目
  を実証済み)・DW-O13関連 (段2投入前の読了を怠り段6直前に気づいた場合、実体等価な既存検証で
  機械的再実行を代替してよいかの手続き方針、一次資料=worklog entry 768、2026-08-20起票)・
  entry772由来 (DW-G03の独立3例目相当、受入自動main取り込みが同一fileの非重複行域変更でも
  `merge-message-provenance`(rc=70)で誤rejectしうる件、一次資料=worklog entry 772、
  2026-08-20起票、2026-08-21 rulingsが未合流を発見し本fragmentで合流)・T-1434 handoff由来
  (変異harness/受入のpre-run clean-tree検査と段7 spool fragment起草のタイミング衝突を
  `DW-M05` か段6の U 節へ明記する候補、一次資料=`dev-wave-jobs/handoff/2026-08-20-t1434-wave-c-supervise-collect.md`、
  2026-08-21 rulings発見で合流)・[T-287]裁定パッケージ§5 (`DW-G05`に「その変更が実際に影響を
  止める経路に限る」旨の確認義務を足す候補、274 bytes、一次資料=
  `output/insights/2026-08-04_t287-checkpoint-values/adjudication-package.md`§5、
  2026-08-04起票、2026-08-21 rulings発見で合流)。他の docs 予算超過候補 ([T-1430] 等) と
  同じ「独立審査へ回す」枠へ合流させ、次に手が空いた小 wave でまとめて処理する。一次資料 =
  rulings-inbox `2026-08-11-t657-stage0-followups.md` §2・
  `2026-08-11-t665-waiter-self-match-second-instance.md`・worktree
  `dev-wave-t989-realrepo-worker-diag` の
  `docs/spool/worklog/2026-08-20-dev-wave-t989-realrepo-worker-diag-3.md`・worklog entry
  767/768/772 (2026-08-20/08-20/08-20)。
  base: 611b047ec8314d0652a1b7713da0d0aa1f9befe4bc23cd5ca09e8f344477e959

### 新規

- {{T:t287-producer-value-domain}} **P2・新規 (2026-08-21 rulings発見)**: [T-287] 裁定パッケージ
  §1。core/sort/trigger の 3 driver の `load_proposal_file` が direction/magnitude を値域未検査の
  まま checkpoint へ永続化し、次回 resume 時にだけ driver 自身がそれを拒否する非対称
  (自己汚染checkpoint) が残る。択一 = (a) 各 driver の ingress で検査 (b) `project_whiteboard()`
  で一括検査 (c) 現状維持。一次資料の親推奨は (b)。一次資料 =
  `output/insights/2026-08-04_t287-checkpoint-values/adjudication-package.md` §1。
- {{T:t287-origin-binding-integrity}} **P2・新規 (2026-08-21 rulings発見)**: [T-287] 裁定パッケージ
  §3。値域検査では in-domain 改竄 (許可値の範囲内で `rejected`→`fail`+`increase`+`small` に
  書き換える等) を防げない。択一 = (a) iteration単調性+entry件数上限 (b) campaign/run origin
  束縛 (c) checkpoint自体にHMAC等のintegrity (d) 実施しない (計測規律が並行実行を禁じ改竄は
  運用外)。一次資料の親推奨は (a)→(b)。一次資料は同 package §3。
- {{T:t287-untrusted-string-redaction}} **P2・新規 (2026-08-21 rulings発見)**: [T-287] 裁定パッケージ
  §4。`state_from_dict` 等の既存 (本 wave 導入以前からの) 検査エラーが未信頼文字列を素通しで
  例外に含め、`attempts.jsonl`/`report.json` の error message へ保存される (規律6 = 信頼境界の
  射程)。certified 受理集合は不変。択一 = (a) 診断側で未信頼値をredact (既存テスト期待値変更を
  伴う) (b) 長さ上限付きrepr+制御文字除去 (c) `p3_autonomous_workload_trial` の保存側だけで
  redact (d) 実施しない。一次資料の親推奨は (c)。一次資料は同 package §4。
- {{T:t1090-deferred-condition-stale}} **P3・新規 (2026-08-21 rulings発見)**: `docs/phase3.md`
  見送り台帳の [T-1090] (1 dispatch job で複数node を扱う設計、有界並列化の不採用) の再訪条件
  「[T-1116] の実装完了」は、[T-1116] が実装でなく「R2 は一度も発効していないと実測で確定」する
  終端で閉じた (`docs/archive/worklog-phase3-0817-622.md`) ため文言と実態が乖離している。
  [T-1090] が懸念した「既知赤registryが入ると再走回数の見積りが無効になる」の前提
  (registryが作られる) 自体が別経路で解消済み。台帳の文言修正のみに留めるか、この機会に
  元の設計問い自体を取り上げるかの判断が要る。
- {{T:rulings-command-budget-full}} **P3・新規 (2026-08-21 rulings発見)**: `.claude/commands/rulings.md`
  の収集手順に2件の是正 (前回セッションの既読entry範囲を無検証で信頼しない/`docs/decisions.md`
  の「scope外・独立のユーザー裁定を要する」注記を収集源に加える) が要るが、同ファイルは
  4988/5000 bytes (`tools/check_docs.py` の `COMMAND_LIMITS`) で残り12 bytesしかなく収まらない。
  他の docs 予算超過候補と同じ「独立審査へ回す」枠へ合流させる。一次資料は本 worklog entry。
