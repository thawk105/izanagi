---
schema: izanagi-spool-v1
ledger: worklog
authored: 2026-08-21
wave: t1462-red-attribution-doc
seq: 1
title: [T-1462] 自分の変更に起因しないテスト失敗でwaveが失敗扱いになる件を調査した (docsのみ、branch worktree-t1462-red-attribution-doc)
---

## 本文

- ユーザーが別セッション (`dev-wave-t1461-lease-window` の handoff 内) へ直接伝えた依頼:
  「自分のwaveで起こしたわけではないテスト失敗でウェーブ失敗するの許さない。これ何度も
  言ってるけど起きてる。どうにかしてくれ。自分が起こしたわけではないテスト失敗は既知の赤
  として登録し、裁定や新しいdev-waveで解決していく」。当該セッションは本件を仮
  「T-1462」としてscope外のまま自 wave (T-1461) を継続し、`/rulings` がこの handoff を
  発見して索引化、ユーザーが「(a) 手順書明記(②)を先に、実測(①)を後に」という rulings 自身の
  推奨を裁定した (2026-08-21)。
- **①非帰属checkerの信頼性を実測 (今回の新規知見)**: 現行コードを file:line で確認した。
  `tools/dev_wave_wait.py:3733-3735` (`_verify_red_check_receipt` 内) は
  `tools/check_acceptance_reds.py` の rc が非 0 なら理由を問わず (帰属あり rc=1、判定不能
  rc=2、Pegasus dispatch 自体の infra 失敗のいずれでも) 同じ `_StageFailure("acceptance-red-check", ...)`
  を送出する。同ファイル `:1192-1205` の「pytest が判定を1つも出さなかった」場合だけを対象と
  する内部再試行 (no-verdict retry) は、`normalized_child_rc == 1` (テストは失敗という判定が
  既に出ている) の後で始まる acceptance-red-check 段には及ばない。つまり checker 自身が
  Pegasus 混雑等で infra 的に落ちた場合、その acceptance 試行全体が硬く失敗し、待ち手を
  最初から (新しい attempt として) 再投入するのがユーザー/セッション側の回復手段になる
  (これは本 rulings セッションが本日 `tools/check_ai_provenance.py` の queue-wait-timeout に
  対して実際に取った回復手順と同型)。
  **なお `check_acceptance_reds.py` 自身の dispatch timeout は 2026-08-13 の [T-1027]
  (`output/insights/2026-08-13_t1027-acceptance-reds-checker/README.md` R1) で 120 秒→5100 秒
  へ既に引き上げ済みであり、今回本セッションが `check_ai_provenance.py` で実測した 480〜900 秒
  クラスの queue-wait-timeout よりかなり耐性が高い。したがって「checker 起動が不安定」という
  仮説 (a) は、[T-1027]/[T-1087] (2026-08-13/15) の既存投資により **checker 自身の実装としては
  かなり軽減済み**であり、今回追加で実装すべき対策は見当たらなかった。残るギャップは
  「acceptance-red-check 段の infra 失敗は no-verdict retry の対象外」という制御フロー上の
  事実の**周知不足**(②) に絞られる。
- **②手順書への明記は docs 予算超過で今回は着地できない**: `docs/dev-wave/operations.md`
  DW-O18 (`tools/check_acceptance_reds.py` の rc=1/rc=2 の扱いを既に定めている節) へ
  「rc=0 かつ `status=non-attributable-only` は受理成功であり、赤の存在だけで wave 失敗と
  早合点しない」旨を追記しようとしたが、`tools/check_docs.py` の L2 単節予算 (1000 bytes) に
  対し同節は追記前で既に 995 bytes、追記後 1148 bytes で 148 bytes 超過した。既存文の圧縮
  (rc=1/rc=2 の2文を1文へ統合しても新規节 133 bytes、57 bytes 超過) でも収まらず、実装せず
  撤回した。**同節は既に [T-1451] (本 fragment 未合流当時の T-1446 束ね参照) も候補地として
  挙げている** — DW-O18 は既に複数の未着地追記候補が集中している hotspot であり、次にこの
  節を触る wave は両方をまとめて設計し直す (圧縮 + 統合追記) 価値が高い。

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
  2026-08-04起票、2026-08-21 rulings発見で合流)・[T-1462]由来 (DW-O18へ「rc=0かつ
  `status=non-attributable-only`は受理成功、赤の存在だけでwave失敗と早合点しない」旨を追記する
  候補、148 bytes不足、[T-1451]と編集面が重複するため次に触るwaveは両方を1回で設計し直すのが
  望ましい、一次資料=本worklog entry、2026-08-21起票)。他の docs 予算超過候補 ([T-1430] 等) と
  同じ「独立審査へ回す」枠へ合流させ、次に手が空いた小 wave でまとめて処理する
  (2026-08-21 ユーザーがこの対応方針を「推奨通りで」と明示的に確認した)。一次資料 =
  rulings-inbox `2026-08-11-t657-stage0-followups.md` §2・
  `2026-08-11-t665-waiter-self-match-second-instance.md`・worktree
  `dev-wave-t989-realrepo-worker-diag` の
  `docs/spool/worklog/2026-08-20-dev-wave-t989-realrepo-worker-diag-3.md`・worklog entry
  767/768/772 (2026-08-20/08-20/08-20)。
  base: 2f7e6880f04a3da4972d234f970a9d19b6a5de7cb0c9b6100dada702d4a55425

### 新規

- {{T:t1462-acceptance-red-attribution-investigation}} **P3・裁定済み・調査完了 (2026-08-21
  ユーザー裁定「1推奨通り」)**: 「自分のwaveで起こしていないテスト失敗でwave失敗扱いに
  なる」というユーザーの繰り返しの指摘 (原文は本文参照) を調査した。**結論 = checker 自身
  ([T-1027]/[T-1087] が2026-08-13/15に既に硬化済み) への追加実装は不要、残るギャップは
  「acceptance-red-check段のinfra失敗はno-verdict retryの対象外」という制御フロー事実の
  手順書への明記だけであり、それは [T-1446] の docs 予算超過枠へ合流させた** (本項目自体は
  これで終端、追加のユーザー手番なし)。「既知の赤の永続台帳」(ユーザー原文が触れた案) は
  [T-1116] (2026-08-17終端、`docs/archive/worklog-phase3-0817-622.md`) が同種の仕組みを
  検討し「防ぎたかった問題自体が発生しない」と実測で確認済みのため、今回は新設を推奨しなかった
  (ユーザーはこの推奨を含め「1推奨通り」で裁定済み)。一次資料は本 worklog entry、
  `tools/dev_wave_wait.py:1192-1205,3733-3735`、
  `output/insights/2026-08-13_t1027-acceptance-reds-checker/README.md`、
  `output/insights/2026-08-15_t1087-acceptance-red-check/README.md`、
  `docs/archive/worklog-phase3-0817-622.md` ([T-1116])。
