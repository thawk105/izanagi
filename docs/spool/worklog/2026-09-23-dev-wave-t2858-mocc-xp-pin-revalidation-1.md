---
schema: izanagi-spool-v1
ledger: worklog
authored: 2026-09-23
wave: dev-wave-t2858-mocc-xp-pin-revalidation
seq: 1
title: [T-2858] mocc の X/P 計装 commit C = 68106660 を新しい ccbench pin として再承認するかを、D1603 の材料 3 点・更新 wave の波及見積り・TPC-C 候補との切り分けを添えて提示した (insight + docs、pin・gitlink は不変、branch worktree-dev-wave-t2858-mocc-xp-pin-revalidation)
---

## 本文

- 提示本体: `output/insights/2026-09-23/t2858-mocc-xp-pin-revalidation/README.md` §0 (択 3 つと推奨)。経路は D2114 項 3 (見送り台帳 [T-167] の再承認)、D2219 項 8 (人間の push の後に提示 wave)。AI は何も承認・変更していない。
- 実測した前提: GitHub `thawk105/ccbench` の `izanagi-mocc-xp-instrumentation` = C (2026-09-23 07:44 JST、ls-remote)。空の repo へ GitHub だけから C を fetch し、tree・親・`cc/mocc/transaction.cc` の blob が T-2844 の材料 §2 と一致 (07:50 JST)。
- 波及の再集計: `e9e477c` を含む tracked file は 45 → 54 件 (増 9 件はすべて過去の実測記録・固定した図の出所で据置)。pin 定数を読む file は T-2304 着地時 70 → 71 件 (silo-function-policy 軸の別名 1 件、C は silo に触れないので追随のみ)。
- 素材: 「pin 前進は C の上で 1 回」は TPC-C 設計 §8 の親決定 3 であり、D2219 項 2 が採ったのは同 §8 の 4 (段 1 → 段 2) だけだった。依頼文は前者を確定事項のように引いていたので、提示ではユーザー裁定でないことを明記し、推奨 (a) = C を単独で承認して更新 wave を今起こす (pin 前進は計 2 回) とした。TPC-C の系列 (e9e477ca → C1 → C2) と C (e9e477ca の子) は e9e477ca から分岐した別系列で、現在の C1 / C2 と C は変更 file が重ならない。
- 並走: 開始時の ListAgents に同じ T-2858 の session は無く、T-2854 の稼働 session・worktree も無かった。
- 工数: 段 2・3 は省略 (実装差分ゼロの docs-only、DW-C00 軽量版)。段 6 は Codex read-only レビュー 1 本 (事実の再抽出と推奨の当否の 2 レンズ): NO-GO、must-fix 2 (C と C2 を兄弟とした系図の誤り、並走への影響を記録文字列だけとした過小表示) と should 4 (T-2304 の子本数の出典、追随 15 件を test 数とした読み、2 回目の承認の範囲、確認線の「以上」)。親は 6 件とも一次資料で real と判定して直した。受入全走は本 fragment を含む tip で行い、結果は job dir `/home/SFC/tanab/.claude/jobs/4811f999/` の receipt に残す (本 commit の後に走るのでここには書かない)。

## 次の一手差分

### 更新

- [T-2858] **P2・提示済み → ユーザー裁定待ち (次回 /rulings)**: ccbench の pin を C = `68106660686232781bca3be792a750d3e19d7a8a` (e9e477ca の単一の子、
  `cc/mocc/transaction.cc` の +64 行、mocc の X/P 計装) へ進める再承認 (D2114 項 3、見送り台帳 [T-167]) を
  `output/insights/2026-09-23/t2858-mocc-xp-pin-revalidation/README.md` §0 で提示した。択 = (a) 推奨: C を単独で承認し、更新 wave を今起こす
  (pin 前進は TPC-C と合わせて計 2 回) / (b) C を承認し、pin 前進は TPC-C の候補と合わせて 1 回 / (c) 見送り。どの択でも承認の対象は C の OID だけで、
  TPC-C の commit (C1 / C2 を C の上へ載せ替えた版) は含まない。C は GitHub に実在し、GitHub だけからの取得で tree・blob が材料と一致した (2026-09-23)。
  承認後の gitlink・`CCBENCH_FULL_SHA`・`CURRENT_PIN` の同一 commit 更新は別 wave (Codex author + 変異事前登録、範囲は D2150 項 1 と同じ ①④⑦、
  T-2304 の実績からの換算で約 1〜2 node 時間 = 投入前に出し直す、`axis_mocc_temperature.py` の PIN の扱いを 1 件決める、提示 §3)。
  clang 比較の未完了と I 面 ([T-2295]) の不足は承認しても解決しない。VLDB の第 2 プロトコル ([T-2849] の S2) と TPC-C の mocc 認定 ([T-2854]) の前提。
  base: 75df6611b9206df401ecf8369a61dedda50dcb20eef09d4d454e65e9f04ddbf9

### 見送り追記

- [T-167] 【2026-09-23 追記: [T-2858] で候補 C = `68106660686232781bca3be792a750d3e19d7a8a` (e9e477ca の単一の子、mocc の X/P 計装) の再承認を提示した (材料 `output/insights/2026-09-21/t2844-mocc-xp-hook-branch/README.md`、提示 `output/insights/2026-09-23/t2858-mocc-xp-pin-revalidation/README.md`)。本追記は判断材料の参照追加であり、pin 更新は未承認】
