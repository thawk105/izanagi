---
schema: izanagi-spool-v1
ledger: worklog
authored: 2026-09-16
wave: dev-wave-fig5-a2-identity-reissue
seq: 1
title: 旧 A-2 attempt の条件記述を訂正した図 fig7 を足し、旧 fig5 の凍結 bytes は保った (コード + docs、branch worktree-dev-wave-fig5-a2-identity-reissue、変異 matrix = baseline PASSED・5/5 KILLED・期待 node 完全一致)
---

## 本文

- ユーザー依頼は「論文図 5 を D1645 の訂正に合わせて作り直す。図が支持する命題と caption を改訂稿
  `docs/paper-story/results/2026-09-07-a2-certification-reject.md` の表現へ合わせ、provenance JSON の
  `tracked_inputs` を新しい一次資料へ差し替える。本題の図 1 枚と caption だけ」。
- **段 1 の実測が依頼の前提を更新した。** 依頼は D1645 (2026-09-05) だけを引いていたが、
  D1993 (2026-09-14) 決定 1 が「D1645 の解除条件は attempt `t2364-20260907b` が満たす」と裁定済みで、
  その図 `fig6_a2_certification_observed_positive` は 2026-09-07 に着地していた。旧 fig5 の用途制限は
  D1936 項21 + D1993 決定 5 で**期限なし**になっており、`figures/README.md` の追補が
  「旧画像・PDF・provenance JSON・キャプション正文は保持する」と明記し、append-only の results 2 稿が
  provenance の SHA-256 `30113d50…` を記録していた。D1753 は「新しい図の filename を `fig5` 系にする」を
  却下済みだった。**「図 5 を in-place で作り直す」は 4 つの現行裁定と正面衝突する。**
- **段 3 の 2 レンズは独立に in-place を refuted と判定し、「凍結解除も用途制限の撤回も求めずに
  依頼の目的を満たす経路がある」と結論した。ユーザー裁定へ返す択一は無かった。**
  採ったのは、同じ権威 bytes から条件記述を訂正した新しい番号の図を 1 枚作る経路である
  (D1645 自身が results 系列へ課した「旧稿を変えず新しい日付の稿で改める」と同型)。
- **親の段 1 brief の一般化が段 2・3 で崩れた。** 「caption 訂正と凍結 bytes 保持は両立しない」は、
  legacy caption を**一律**変える場合にだけ正しい。出力 prefix で分岐すれば両立する。
  設計は allow-list ではなく**凍結 prefix の列挙**にして既定を訂正側へ置いた ({{D:legacy-figure-condition-description-default-corrected}})。
- **段 2 プランの「目盛は保持」を段 3 の両レンズが real な不履行と判定し、親が裁定で覆した。**
  x 軸の目盛は `cell_id` ではなく `plot_a2_certification.py` が組み立てる
  `"no backoff"` / `f"fixed {BACKOFF_FIXED} us"` であり、**caption だけ直すと絵そのものが
  誤った条件を述べ続ける。** PDF を論文へ貼った時点で別 file の erratum は付いてこない。
- **段 6 のレビュー B が実在の被覆穴を出した。** 段 5 の実装子が既存 CLI テストの出力 prefix を
  凍結名へ変えた結果 (仮 repo に改訂稿が無いと `build_provenance` が落ちるため)、既定経路を CLI から
  通す検査が消え、**`main` が prefix によらず常に凍結側を渡す欠陥**をどの assertion も捕まえられなく
  なっていた。その欠陥が入ると caption は訂正済み・provenance は 3 行なのに**絵だけが旧目盛**の図を
  新規生成しても検査が通る。fix 1 巡で閉じた (`_publish_outputs` へ委譲する観測 wrapper で `main` を
  通し、描かれた目盛を検査する)。
- **レビュー A の所見 1 件は不採用にした。** 「新 caption が改訂稿に無い精密日時を持つ」。当該日時の
  権威は `tracked_inputs` の権威 bytes 2 行であり、`caption_source` 行は `authority_scope` を
  条件記述に限ると明示している。削れば出所のある provenance を減らす。**この所見は親の prompt が
  「改訂稿を唯一の照合先」と読める書き方をしたために生まれたもので、レンズの誤りではない。**
- **親の変異事前登録は 5 件中 3 件の期待 node と赤理由が誤っており、両レンズが独立に指摘した。**
  M1 は共有列挙が `build_provenance` も読むため単一理由にならず、M2 の期待 node は 2 件でなく 5 件、
  M5 の README 逐語一致は変異で変わらないので赤理由にならない。**推測で再登録せず probe 走で
  観測 node を実測した。** 訂正後の期待 node は 5 件すべて probe の観測と完全一致した。
- 変異本走は **baseline PASSED・5/5 KILLED・期待 node 完全一致**。
- **編集面の重複を段 1 で表に出した。** `docs/paper-story/` は B-7 の wave
  (`worktree-dev-wave-t2670-b7-three-run-materials`) が同時に触っており、同 wave は
  `docs/paper-story/README.md` に未 commit の変更と新規 results file を持つ。本 wave は
  `docs/paper-story/figures/` 配下だけを触り、直接の衝突は無い。ただし
  `docs/paper-story/README.md` の恒久 erratum 節が fig7 を指していないので、
  B-7 の着地後に別 wave で足す ({{T:paper-story-readme-fig7-pointer}})。
- **主張しないこと。** 新しい測定は 1 件も行っていない。値・median・効果・outer status・cell identity は
  fig5 と同一である。本図は採用静的 backoff についての結果ではない (D1936 項21・D1993 決定 5、期限なし)。
  着地 closure は `tracked_inputs` の**行の削除自体を拒否しない** (記載行の hash は束縛する)。
  `caption_source` に `.md` を束縛したので同稿を 1 byte でも直すと着地 fig7 が赤になる。
- 工数: codex 子 6 本 (plan 1、consult 2、author 1、review 2、fix 1)。

## 次の一手差分

### 新規

- {{T:paper-story-readme-fig7-pointer}} **P3・新規**: `docs/paper-story/README.md` の恒久 erratum 節
  (fig2 → fig2b の乗り換え指示と同じ枠) に、旧 attempt の条件記述を訂正した図が
  `fig7_a2_builtin_backoff_onoff_reject` であることを足す。本 wave の時点で同 file は B-7 の wave が
  未 commit で保持していたため触っていない。着地後に当てる。
