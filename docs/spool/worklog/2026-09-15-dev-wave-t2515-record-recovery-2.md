---
schema: izanagi-spool-v1
ledger: worklog
authored: 2026-09-15
wave: dev-wave-t2515-record-recovery
seq: 2
title: [T-2515] 旧 wave branch に残っていた未着地の研究記録を回収する (docs + insights のみ、branch worktree-dev-wave-t2515-record-recovery、実装面差分ゼロ・変異免除)
---

## 本文

- 依頼は `worktree-dev-wave-t2515-calib-rr95-rr5` (tip `559bcbc29`) の 6 commit を内容で監査して
  未着地分を回収すること。**コードは 1 行も変えていない。新しい測定もしていない。**
  一次資料は `output/insights/2026-09-15/t2515-record-recovery/` と、当時の資料を足した
  `output/insights/2026-09-10/t2515-rr95-rr5-calibration/`。
- **依頼の前提 1 件が一次資料と食い違った。** 依頼は
  `output/insights/2026-09-10_t2515-rr95-rr5-calibration/` が main に無いとしたが、内容は
  `output/insights/2026-09-10/t2515-rr95-rr5-calibration/` として着地済みで、`job-evidence/` 7 file は
  blob 一致だった。コード 4 commit と fixture commit も内容で着地済みか、D1936 項 6 が
  対象ごと撤去して失効していた。**未着地は研究記録だけ**である。
- **未着地の実体は 17 file だった。** 当時の子逐語 13 本と、変異 spec / report 4 本。後者は
  `repo_head=18704ae18` に束縛された当時の実測で、既着地の再走版 (`35a740cd4` 束縛) とは
  別命題である。4 本とも blob が main に 0 件であることを全数検索で確かめた。
- **親 brief の (P1) は誤りで、段 2 と段 3 が訂正した。** 親は 3 週間故障と字面検索の
  見落としを新規 F にすると裁定していたが、F500 (同 script が裸 `python3` を呼び 3.10 構文で
  落ちる型) と F766 根本原因 (1) (台帳を主題でなくファイル名で引く) が実在した。
  **新規 F は 0 件**になり、F355 / F500 / F766 への再発追記と F934 への限定 supersede だけを land する。
  親は 4 件とも台帳の現物で裏を取ってから採用した。
- **親の監査の誤りを段 3 レンズ B が 1 件捕まえた。** 親は変異成果物を「再走版で着地済み」と
  報告していたが、`repo_head` が別で当時の実測は失われていた。親が blob 全数検索で追認して
  回収対象へ足した。
- **期間の断定を証拠の範囲へ絞った (段 3 レンズ A)。** 元 wave の「認証経路が 3 週間死んでいた」は
  証拠より強い。実測できたのは 4 時点 (成功 2026-08-06 / 3.10 構文投入 2026-08-20 /
  関門の全 driver 義務化 2026-09-01 / 発現 2026-09-10) と、確認した認定 attempt に当該関門の
  実走記録が無かったことだけである。
- **棄却 finding:** 段 3 は A が 4 件中 2 件、B が 5 件中 2 件を自ら refuted と判定した
  (回収が拒否を緑へ読み替える / 現行コード差分が未着地実装の証拠 / 既着地 dir への追加が凍結違反 /
  6 commit に未着地のコードが残る)。
- 段 4 は `DW-S04` により**変異 matrix を免除**した — 変更面は `output/insights/**` と
  `docs/spool/**` だけで実装面 (D95 決定 2) の差分がゼロ。受入全走は免除していない。
  段 5 の実装子と段 6 の review 子は起こしていない。
- **セッション異常:** 待ち手が producer 生存中に rc=0 で戻る F355 の縮退メッセージが、
  段 2 / 段 3 の 3 本すべてで出た。3 本とも `.done` 非空と成果物実在で完了を判定したので
  誤進行は無い。`EnterWorktree` は git config 読取りで失敗し、手動 `git worktree add` へ切り替えた。
  作成時は他 session の worktree 作成が 10 本並行しており、完了まで 9 分かかった。
  **親は `docs/skill-self-improvement.md` を wave 開始時ではなく段 8 の直前に初読した。**
  契約は開始時の初読と handoff への候補節作成を求めている。実害は無かったが手順の逸脱である。
- **検査結果。** 焦点走は 674 passed / 9 skipped / 0 failed (計算ノード request 998883.nqsv)。
  対象は `test_check_docs.py` / `test_s8b_repo_scan_invariant.py` /
  `test_s8c_preregistration_invariant.py` / `test_login_headroom.py` で、後ろ 3 本は段 3 レンズ B が
  「plan の consumer 導出が docs checker で止まり repo 全体走査を取りこぼしている」と指摘して足させた。
  `check_docs.py` と `check_codex_agents.py` は rc=0、凍結前の三軸語走査 (`s8b_holdout_freeze search`) も
  rc=0 で本 wave の新規 path は hit 0 件。**受入全走は tip `b357697f5` に対して
  23662 passed / 68 skipped / 0 failed (`verdict=child-green`、`red_nodeids=[]`)。**
  この検査結果を記録へ足す amend で tip が変わるため、着地 tip に対して受入をもう 1 度通した。
- **受入の 1 回目は `stage=preflight-submodule-ready` rc=2 で即死した。** 入れ子 submodule が
  未初期化だったためで、親が `git submodule status` の top-level だけを見て clean と誤読していた。
  正規 argv で初期化し直して rc=0。テスト結果ではないので赤に数えない。
- **エージェント工数:** codex 子 3 本 (plan 1 / consult 2)。全本 rc=0、採用検査 rc=0、再投入なし。
- **後続裁定で覆った当時の判断は復活させていない。** 旧 spool の decisions 2 fragment
  (patch materialize 案 / fixture 案) と新規 T 2 件は land せず、逐語 file の中に歴史資料として
  残したうえで、D1936 項 6 / 項 43 / 項 46 / 項 47 と D1986 項 1 の現在の方針を追記節へ対応表で書いた。

## 次の一手差分

### carry

- [T-2515]
