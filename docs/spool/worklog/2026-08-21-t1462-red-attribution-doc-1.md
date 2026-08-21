---
schema: izanagi-spool-v1
ledger: worklog
authored: 2026-08-21
wave: t1462-red-attribution-doc
seq: 1
title: [T-1468] 自分の変更に起因しないテスト失敗でwaveが失敗扱いになる件を調査した (docsのみ、branch worktree-t1462-red-attribution-doc)
---

## 本文

- ユーザーが別セッション (`dev-wave-t1461-lease-window` の handoff 内) へ直接伝えた依頼:
  「自分のwaveで起こしたわけではないテスト失敗でウェーブ失敗するの許さない。これ何度も
  言ってるけど起きてる。どうにかしてくれ。自分が起こしたわけではないテスト失敗は既知の赤
  として登録し、裁定や新しいdev-waveで解決していく」。`/rulings` がこの handoff を発見して
  索引化し、ユーザーが「(a) 手順書明記(②)を先に、実測(①)を後に」という rulings 自身の推奨を
  裁定した (2026-08-21「1推奨通り」)。
- **着手時点で本 wave (`t1462-red-attribution-doc`) は独立に本件の investigation を開始した
  ([T-1461] のhandoffが仮称していた「T-1462」を wave 名の由来としたが、正式採番ではない)。
  受入投入後に local main を取り込んだところ、[T-1461] wave 自身の段7記録 (entry 793) が
  同一依頼を独自に `[T-1468]` として次の一手へ登録済みだったと判明した。二重登録
  (memory `double-registered-ids-cannot-be-withdrawn`) を避けるため、本 fragment は新規 T
  番号を起こさず [T-1468] の**更新**として結果を記録する。**したがって本 wave 名・title の
  「T-1462」は投機的な作業名であり、正式な管理番号は [T-1468] である。**
- **①非帰属checkerの信頼性を実測 (本waveの新規知見)**: 現行コードを file:line で確認した。
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
  撤回した。**同節は既に [T-1451] も候補地として挙げ、local main 取り込み後に判明した
  entry 792 (段8自己改善候補、`dev-wave-known-violation-audit` wave) も同節へ「探索目的の
  全走も隔離worktreeで行う」旨の追記候補を挙げている。** DW-O18 は複数の未着地追記候補が
  集中している hotspot であり、次にこの節を触る wave は全候補をまとめて設計し直す
  (圧縮 + 統合追記) 価値が高い。

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
  2026-08-04起票、2026-08-21 rulings発見で合流)・[T-1468]由来 (DW-O18へ「rc=0かつ
  `status=non-attributable-only`は受理成功、赤の存在だけでwave失敗と早合点しない」旨を追記する
  候補、148 bytes不足、[T-1451]・entry792と編集面が重複するため次に触るwaveは全候補を1回で
  設計し直すのが望ましい、一次資料=本worklog entry、2026-08-21起票)・entry792由来2件
  (`dev-wave-known-violation-audit` waveの段8自己改善候補: (1) `DW-S01`へ「汎用command引数
  では一次資料特定に逐語検索を先に行う」旨を追加する候補、(2) `DW-O18`または`DW-C00`へ
  「探索目的の全走も隔離worktreeで行う (shared main checkoutでの探索走は並行wave land活動と
  衝突しnear-miss赤を生む、本waveで12 failed+3 errorのうち11+3件を実測)」旨を追加する候補、
  いずれもbytes超過量未実測・2026-08-21起票)。他の
  docs 予算超過候補 ([T-1430] 等) と同じ「独立審査へ回す」枠へ合流させ、次に手が空いた小 wave
  でまとめて処理する (2026-08-21 ユーザーがこの対応方針を「推奨通りで」と明示的に確認した)。
  一次資料 = rulings-inbox `2026-08-11-t657-stage0-followups.md` §2・
  `2026-08-11-t665-waiter-self-match-second-instance.md`・worktree
  `dev-wave-t989-realrepo-worker-diag` の
  `docs/spool/worklog/2026-08-20-dev-wave-t989-realrepo-worker-diag-3.md`・worklog entry
  767/768/772 (2026-08-20/08-20/08-20)。
  base: 2f7e6880f04a3da4972d234f970a9d19b6a5de7cb0c9b6100dada702d4a55425
- [T-1468] **P3・調査完了・裁定済み (2026-08-21 ユーザー裁定「1推奨通り」)**: 自waveが原因で
  ないテスト失敗でwaveを失敗させない件。file:line 調査の結論 = 非帰属赤分類ロジック自体
  ([T-1027]/[T-1087] が2026-08-13/15に既に硬化済み) への追加実装は不要。残る唯一のギャップは
  制御フロー上の事実 (`tools/dev_wave_wait.py:1192-1205,3733-3735`: acceptance-red-check段の
  infra失敗はno-verdict retryの対象外) が手順書に未記載な点であり、`docs/dev-wave/operations.md`
  DW-O18への追記を試みたが同節のL2単節予算 (1000 bytes、追記前995 bytes) を148 bytes超過し
  着地できなかったため [T-1446] のdocs予算超過枠へ合流させた (上記参照)。「既知の赤の永続台帳」
  新設は [T-1116] の既存却下 (2026-08-17終端、同種の仕組みが検討され「防ぎたかった問題自体が
  発生しない」と実測確認済み) と整合させ推奨しなかった。ユーザーはこの一連の結論を含め
  「1推奨通り」で裁定した。追加のユーザー手番なし、実装 (DW-O18追記) は [T-1446] 側の
  独立審査枠で次の一手として持ち越す。一次資料 =
  `output/insights/2026-08-13_t1027-acceptance-reds-checker/README.md`・
  `output/insights/2026-08-15_t1087-acceptance-red-check/README.md`・
  `docs/archive/worklog-phase3-0817-622.md` ([T-1116])・
  `output/insights/2026-08-21_t1461-lease-window-design/README.md` (依頼の一次記録元)。
  base: 06d7f609846ac979f276a1ddd24762d6b59fae0b032a3d8e39c338532a3be13d
