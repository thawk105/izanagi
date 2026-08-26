---
schema: izanagi-spool-v1
ledger: worklog
authored: 2026-08-26
wave: dev-wave-b4-prereg-enactment
seq: 3
title: B-4 事前登録の発効準備 — 必須配線は実装したが §5 は 1 欄も埋まらず、文書は発効しない (コード + docs、branch worktree-dev-wave-b4-prereg-enactment、変異 matrix = baseline PASSED・15/15 KILLED・SURVIVED 0・MISMATCH 0)
---

## 本文

- 依頼は (i) 事前登録 §5 の欄を実走前に埋めて commit、(ii) §6 前提条件 3 の段 4 driver 必須配線の実装。
  **(ii) は実装した。(i) は実測の結果 1 欄も埋められないことが確定し、埋めなかった。**
  なぜ埋まらないかを欄ごとに §10 と {{D:b4-prereg-fields-stay-empty}} へ記録し、裁定へ返す。
- **親の段 1 の裁定が 1 つ誤っていた。** 「対象 driver と軸」の欄は配線 probe を計測 wave へ送れば
  埋まると考えたが、段 3 の敵対レンズが refuted した。§5.1 (ii) は「next synthesis と
  primary / secondary outcome を生成も閲覧もしない配線 probe に限る」と定めるのに対し、
  **build を伴う sanctioned CLI はまさにその outcome を生成する**。費用の問題ではなく禁止の問題だった。
  `--no-build` 経路は切替点を通らない。**条件を満たす CLI は現存しない**ため、この欄は
  永久に埋まらない。§10 の最上位項目として新設した。
- **段 3 と段 6 の敵対レンズが独立に同じ核心へ到達した。** 親が段 4 で採用した「決定 → proposal の
  束縛」は、実装しても**通行券のままだった** — proposal が持つ receipt hash は自己申告であり、
  valid な receipt を取得して legacy critic 由来の proposal へ書き写せば通る。
  親は主張を実態まで狭め、因果的束縛を未了として §10 へ残した ({{D:b4-wiring-binds-invocation-not-proposal}})。
  **狭めても到達点はある** — 以前は閉じた critic を一度も起動せずに off アームを名乗れたが、
  以後は当該 campaign・arm・iteration・digest の certified な起動が実在し一度だけ消費されることが要り、
  停止挙動を変える 1 bit も自己申告できない。
- **本 wave が自分で開けた注入口を段 6 レビューが見つけた。** 公開した検証関数が任意の layout を
  受け取り `root` だけ照合して `wal_file` を信頼していたため、生の WAL 照合・一度きりの消費・
  正規配置の 3 つを同じ 1 箇所から迂回できた。しかも**テスト自身が duck-typed な object を渡して
  その署名を固定していた** (テストのために防壁へ穴を開けた形)。fix で厳密な型を要求し、
  campaign 識別子から layout を再構成して呼び手の値を消費経路へ到達させない形にした。
- **変異 matrix (本走): 登録 15 件すべて KILLED、生存ゼロ、MISMATCH ゼロ、baseline 緑。**
  期待ノードは probe 走で実観測した完全集合を使った。**15 変異に対し期待ノード総数 16** で、
  各変異は自分の狙ったテストだけを落とした (M11 の一度きり消費だけが逐次 replay と並行書込みの
  2 本)。段 6 レビュー A が指摘した M13 の過剰決定は fix で単一理由へ作り替えた。
- **並行 wave と編集面が衝突し、相手が先に着地したので取り込んだ。** 段 1 の走査 (F606 の 3 面) は
  09:38 時点で 0 件だったが、相手はその後に起動しており、**段 1〜4 の間 repo へ書かない期間は
  どの走査面にも現れない**という F606 の構造的な穴に当たった。競合 3 箇所を Codex 実装子が解消し、
  どちらの検査も落とさずに合成した。相手が `create_b4_closed_critic_pair` へ既定値なしの必須引数を
  足していたため、本 wave が追加した 3 driver の CLI 経路も全数え上げして追随させた。
- **取り込みで最も重かったのは期待値の意味の衝突である。** 相手の admission record は projection
  closure のハッシュを**単一の期待値**として持つが、本 wave の変更で closure は driver ごとに
  異なる値になった。期待値を「当該 driver の closure」と解して照合する形で成立し、
  **相手の schema は変えていない。** 1 record で複数 driver を同時に認可したい場合は driver 別
  期待値が要り、別途裁定が要る。
- **相手が着地させたテストが受領証 schema を v2 で固定していた。** 本 wave は決定の束縛のために
  v3 へ上げている。親は**弱体化ではなく追随**と裁定し、集合比較の厳密さを保ったまま版を追随させ、
  実在するようになった 3 field だけを exact key 集合へ足した。fix 子は契約に従い自分では直さず
  親へ返した。
- **`/tmp/.git` に起因する 44 件の赤を非帰属と判定した** ({{F:shared-tmp-git-marker-reds}})。
  空の directory が断続的に現れ、当たった走行だけが落ちる。専用 TMPDIR で 43 件は消えたが
  1 件はパス直書きで残り、撤去して初めて全消えした。**監視を掃除役に変えた走行で「一度も出現せず、
  それでも赤が残る」ことを確かめ**、残った赤が環境でなく別の構造に由来すると特定できた。
- **その別の構造が {{F:merge-validation-before-commit}} である。** merge を commit する前に
  テストで検証しようとして 109 件の偽の赤を踏んだ。契約 loader が作業ツリーと HEAD blob を
  照合するため、merge 未確定の間は必ずずれる。表示は合成の破壊に見え、実際に一度そう疑った。
  commit 直後の同一範囲は 516 passed で全消えした。
- **§5 の値セルを 1 行も触っていないことを差分で機械確認した。** 差分中に「未記入」を含む行は
  2 つあるが、いずれも §6 の散文である。`docs/phase3-main-experiment.md` は差分ゼロ。
- 親の焦点走の実測: 段 5 巡 1 後 335 passed、fix 後 1067 passed (test file 11 本)、
  取り込み確定後 516 passed。**段 5 / 段 6 の Codex 子は pytest を一度も起動できなかった**
  (`qstat -Q` preflight rc=1)。親 (login node) からは rc=0 で通る。緑の判定はすべて親の実走による。

## 次の一手差分

### 新規

- {{T:b4-nonsampling-probe}} **P1・critical path**: §5.1 (ii) を満たす非標本 probe を設計・実装する。
  outcome を生成しないことを機械保証する必要がある。**これが無い限り「対象 driver と軸」の欄は
  埋まらず、B-4 事前登録は発効しない。** 設計自体が裁定を要する。
- {{T:b4-analysis-contract}} **P1・ユーザー裁定待ち**: 赤 precursor 母集合・最小重要効果・n・
  primary outcome の純関数を一括で凍結する。分析契約であり既成事実化しない。
- {{T:b4-decision-proposal-binding}} **P2・新規**: critic の決定と proposal 本文の因果的束縛。
  決定を入力とする sanctioned な proposal producer と、生成後の proposal bytes を含む
  handoff receipt が要る。現状は receipt hash の自己申告で通る。
- {{T:b4-pair-completeness}} **P2・新規**: pair の完全性と receipt shopping の遮断。
  precursor hash・on/off receipt・proposal・block id を束縛する manifest と完全性 consumer。
  同一 receipt の再消費だけは本 wave で閉じた。
- {{T:b4-run-owner-assignment}} **P3・ユーザー裁定待ち**: §5 の実行責任者を指名する。
  計測に依存しない欄であり、指名がないことだけが空欄の理由である。
- {{T:tmp-git-marker-source}} **P2・新規**: 共有 `/tmp` へ断続的に現れる空の `.git` の作成元を
  特定し恒久遮断する。全 wave の受入を確率的に赤にする。repo 内に作成コードは無いことは確認済み。
