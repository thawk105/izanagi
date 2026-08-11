---
schema: izanagi-spool-v1
ledger: worklog
authored: 2026-08-11
wave: dev-wave-t781-spool-feasibility
seq: 1
title: [T-781] 案 A の実現可能性を実測した — spool bytes の独立取得は可能だが lineage は閉じず、択を軸別 4 問へ再構成した (docs + insights のみ、実装差分ゼロ、branch worktree-dev-wave-t781-spool-feasibility)
---

## 本文

- **ユーザー裁定 (2026-08-11 /rulings、worklog 404)「択は保留し調査先行」への返答である。**
  裁定パッケージ本体 = `output/insights/2026-08-11_t781-spool-feasibility/package.md`
  (`authority: none` / `default_effect: no-state-change`)。逐語と probe 生ログは同 dir の `verbatim/`。
- **起票時の前提が誤りだったことを実測で確定した。** Pegasus のスケジューラは PBS ではなく
  **NEC NQSV** で、`qcat -i <RequestID>` が spool 済み request script を返す。計算ノードからも使える。
  D86 §4 が要求する「独立取得」の手段は**実在する**。
- **しかし取得できるのは caller が指定した live request の入力であって、現プロセスの同定ではない。**
  決定的な新事実として `qattach command = Enable` を実測した — 同一 uid の攻撃者は真正 request の
  **外**から任意 command を request 内へ注入できる。よって案 A 単独では A-1 を閉じない。
  実装しない裁定とし、D86 は 1 項も覆さない。official の受理集合は空集合のまま。
- **親の provisional 裁定 3 件のうち 1 件を撤回、2 件を訂正した。** (P3)「User Attributes は
  D86(3) に直接は当たらない」は**裁定の先取り**であり撤回する (属性は外部 authority を運ぶ器には
  なれるが発生源にはなれない)。(P1) は「取得 primitive は実現可能」まで狭め、(P2) は `qattach` の
  実測で強化した。段 3 の 2 レンズが独立にこの 3 点を指摘し、両レンズとも **NO-GO** を返した。
- **択を軸別 4 問 Q1〜Q4 へ再構成した** (元の (A)〜(D) は判断軸が異なり択一ではなかった)。
  起票時は「親の推奨は無い」だったが、実測が揃ったため**全問 (a) を推奨する** — Q1 = official は
  空集合のまま維持し実測事実だけ記録、Q2 = User Attributes は観測 assertion に限定、
  Q3 = proof chain 拡張は先送り維持 (D86(5))、Q4 = T-139 / A 系列の後まで保留。
- **本 wave 自身の手続き不備を自己申告する** (段 3 レンズが指摘し、親が real と裁定した)。
  (i) 計算ノードへ投入した request は 2 本ではなく **3 本** (901499 / 901501 / 901512)。
  (ii) F49 (ii) の 3 点検査のうち、**901512 は投入直後の親側 `qstat` を実施していない**
  (marker と `.e`/`.o` は 3 組とも実在、ポイント消費は `racctjob` が sudo を要求するため未取得)。
  (iii) 並走ガード (i) は**形式的に未充足** — ノード同居は実測上無い (他 wave = bnode034、
  probe = bnode042 / bnode046) が、計算ノード上の単独性確認と静穏 preflight は行っていない。
  性能値は一切採っていないため計測汚染は生じない。(iv) **probe 2 は read-only ではない** —
  JSV jobfile dir へ `touch` → `rm` を行った。(v) `user_script` の unlink / 差し替え検査は
  権限層に拒否されたため**実施しておらず、迂回もしていない**。推論と実測を区別して記録した。
- 段 3 レンズ A は 1 回目が harness の evidence 検査で不採用 (rc=1、`evidence_status=invalid`、
  内容は 16KB で `## 総括` あり)。**不採用成果物はレビュー結果に数えず**、probe 2 の実測を足した
  新 artifact 名で 1 回だけ再投入して採用した。
- 実装差分ゼロの「実装しない」裁定のため変異 matrix は `DW-S04` により免除。
  **受入全走は免除していない** — `docs/worklog` / `docs/spool` / `output/insights` を読む実 repo
  テストが実在する (`test_check_docs.py` / `test_spool_fold.py` / `test_frozen_artifacts.py` /
  `real_repo_ratified_memo.py` 等) ため実走した。
  **1 走目 (tip `51f5dd75`、本行の追記前) = 8487 passed / 20 skipped / 552.85 秒 / rc=0。**
  land は wave HEAD と tested tip の完全一致を要求するため、本行を含む記録 commit の後に
  最終 tip で 2 走目を実走する (本記録の時点では未実施であり、結果は land 後の報告に記す)。

## 次の一手差分

### 更新

- [T-781] **P1・調査完了、択を Q1〜Q4 へ再構成してユーザー裁定待ち (B 系)**: 案 A の
  「実装手段が無い」は誤りで、NQSV の `qcat -i` が spool bytes を返す (計算ノードでも可、
  出力は投入 bytes + 末尾 `\n` 1 個)。しかし `qattach command = Enable` により真正 request へ
  外部から command を注入でき、spool 証拠は lineage を閉じない。**親推奨は全問 (a)** =
  official は空集合のまま維持 / User Attributes は観測 assertion に限定 / proof chain 拡張は
  先送り維持 / T-139・A 系列の後まで保留。実測・費用・受理集合の表・裁定に足りない数字は
  `output/insights/2026-08-11_t781-spool-feasibility/package.md` §1〜§4。
  実装差分ゼロで D86 は 1 項も覆していない
  base: 428ebbfcf4d1a97f438c40df9baa1f968d38c518335cedf8d22743a4346bb625
