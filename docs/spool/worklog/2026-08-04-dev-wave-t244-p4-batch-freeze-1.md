---
schema: izanagi-spool-v1
ledger: worklog
authored: 2026-08-04
wave: dev-wave-t244-p4-batch-freeze
seq: 1
title: [T-244] D121 P4 batch freeze は独立 leaf 実装を差し戻す — U-D 第一級裁定の下で P3 実装 wave と不可分、設計択一 5 件を裁定へ返す (docs のみ、branch worktree-dev-wave-t244-p4-batch-freeze)
---

## 本文

- **裁定は {{D:t244-p4-batch-freeze-defer}}。** プラン・敵対レンズ 2 本・段 4 裁定の逐語 =
  `output/insights/2026-08-04_t244-p4-batch-freeze/`。実装差分はゼロ (docs のみ) で、
  **DW-S04 に従い変異 matrix と受入全走は対象外** (変異させる位置が存在しない)
- **段 2 の planner が親 brief の stale 前提を検出した。** 親は起動時 snapshot の worklog
  (169)(170) と archive (165) を読み「U-A〜U-D は裁定待ち」と書いたが、worktree 作成前に
  (171) が land 済みで **U-A〜U-G は全件裁定済み** (U-D = batch 第一級) だった。worktree 自体は
  (171) を含んでおり、親が worktree 内で worklog 末尾を再読しなかったことが原因 (F31 と同型の
  一次記録参照漏れ)。brief へ erratum 1 を追記し、段 2 プランは訂正済み前提で起草されていたため
  巻き戻しなしで続行した
- **段 3 の敵対 2 レンズがいずれも NO-GO を返した** (blocker はレンズ A 7 件 / レンズ B 4 件)。
  収束した決め手は 3 点: (1) U-D (batch 第一級) の下で独立 FSM leaf は将来の第一級実装との
  二重実装または非発火 prototype になる、(2) batch member identity (distinct wire set か
  query/replicate ordinal 込みか) が未裁定で、択一 1 の `Q >= 1 + 32R + E_min` を distinct set
  (最大 32) では表現できず commitment preimage が決まらない、(3) DW-G04 の発火 artifact path /
  計測 ID を 1 件も書けず、D149 (P1) は一般例外を作らない。D147 (P3 差し戻し) と同型の帰結
- **レンズ A の「DW-O08 成立・段 1 巻き戻し」要求は却下した。** DW-O08 本文の義務は freeze 族の
  submodule 初期化と skip の正直な報告であり、wave startup (brief 起草前) に履行済み。
  新規 golden の新設は freeze 族・oracle gate・proof chain の機構に触れない。ただし入口条件表の
  trigger 文言 (freeze / oracle gate / proof chain) と節本文 (submodule init) の乖離が誤読を
  招いた事実は real とし、段 8 候補として記録した (下記)
- **裁定パッケージ (ユーザーへ返す 5 件、推奨は {{D:t244-p4-batch-freeze-defer}} 本文):**
  - **W1 = P4 の実装先。** 推奨 = P3 実装 wave の中で U-D 第一級の batch event / reducer として
    設計・実装する。producer・ledger・driver・consumer (P7)・proof chain の結線順と各層の
    受理条件も同 wave の設計に含める
  - **W2 = batch member identity。** distinct wire set か query/replicate ordinal 込みか。
    推奨 = ordinal 込み (択一 1 の 32R replicate を表現するため)
  - **W3 = 結果の evidence 束縛。** 二値 outcome + 自己申告 class hash か evidence digest 束縛か。
    推奨 = evidence digest 束縛 (proof chain が未裏付け outcome を受理しないため)
  - **W4 = abort / tombstone。** 推奨 = 早期停止時は残 member を tombstone として消費し
    公開 transcript 長を固定する (設計本文 §4③-5 の既定どおり)
  - **W5 = floor / Kmax の authority。** 推奨 = origin-total の計数は P3 ledger、batch 層は
    authority receipt 由来の policy だけ受理、class referent の検証は P7 consumer 側の義務
- **brief の erratum 4 件を凍結した** (逐語 = insight の brief.md / s4-adjudication.md):
  (1) U-A〜U-G 裁定済み、(2) 並列分割が D149 の golden/実装の所有分離を欠いた、
  (3) 「純増検出力 = テスト全部」は過大 (検出力は独立系譜と fault class で数える。T-126 系に
  部分重複あり)、(4) DW-O13 記載は gate 入力実在の証明にならない
- **段 8 の自己改善候補 2 件は `docs/dev-wave/**` の byte 予算逼迫 ((170) で残 4 bytes) のため
  実装せず候補記録に留めた** ([T-328] 裁定 (c) の [T-313] 先行路線に従う)。(i) 入口条件表 08 の
  trigger 文言と DW-O08 節本文の乖離の解消、(ii) worktree 作成後に worklog 末尾を worktree 内で
  再読する義務 ((170) 候補 (i) の変種 — 本 wave は main 取り込み自体は最新だったが、親の読みが
  snapshot に残った)
- 工数: codex 子 3 本 (plan 1 / 敵対レンズ 2)。段 5・6 は「実装しない」裁定によりスキップ
  (`4→7→8→9`)
- **受入 (2026-08-04、worktree `dev-wave-t244-p4-batch-freeze`):** `python3 tools/check_docs.py` =
  違反なし。実装差分ゼロのため対象テストなし。`python3 tools/check_ai_provenance.py` は
  全 commit 後に再走して違反なし

## 次の一手差分

### 更新

- [T-244] **P1・P4 の実装先と設計択一 5 件 (W1〜W5) はユーザー裁定待ち。P3 は U-A〜U-G 裁定済みで実装 wave 再起票可、P5 は 2/3 実装 + 残余裁定済み**:
  **P4**: {{D:t244-p4-batch-freeze-defer}} で独立 leaf 実装を差し戻した。敵対 2 レンズが
  独立に NO-GO — U-D (batch 第一級) の下で独立 FSM leaf は二重実装または非発火 prototype に
  なり、member identity が未裁定のため commitment preimage も golden も決まらない。
  **W1** 実装先 (推奨 = P3 実装 wave 内で第一級 batch event として設計) / **W2** member identity
  (推奨 = query/replicate ordinal 込み) / **W3** evidence 束縛 (推奨 = evidence digest) /
  **W4** abort 時の tombstone + transcript 長固定 (推奨 = 採用) / **W5** floor・Kmax の
  authority (推奨 = origin-total は ledger 計数 + authority receipt 由来 policy のみ受理) の
  5 件がユーザー裁定待ち。**P4 実装・充足・prototype のいずれも名乗らない。**
  逐語 = `output/insights/2026-08-04_t244-p4-batch-freeze/`。
  **U2**: D150 が「実装が無いゆえの非適用」を cap-lift の失敗と定め、
  択一 3 の既裁定により **P4 を条件付き義務から無条件義務へ移した** (無条件義務は
  P1・P2・P3・P4・P5・P7・P9・P10 の 8 件)。条件付き義務は P6 だけになり、非適用は
  `NOT_IMPLEMENTED` = 失敗 / `NOT_CLAIMED` = 免責の 2 語に固定した。状態の分類 (事実) と
  承認の可否 (判断) を分け、認定基準が無い間は状態を再分類せず承認を保留する。
  **V1 (`NOT_CLAIMED` の射程 = global 免責か per-run gate か) はユーザー裁定待ち**で、
  P6 実装の裁定と同時に決める。V2=[T-433]、
  V3=[T-434]、V4=[T-435] を前提として追跡する。
  **前提条件 10 件のうち満たされているのは P10 (予算値・origin authority・軸 (iii)) の 1 件だけ。**
  **P1**: `orchestrator/campaign/reflux_ir.py` (固定 5-bit IR・正準 wire codec・正準 C++ emitter) と
  独立 golden 32 点、テストを land した。**production へ wiring しないため候補表現は閉じておらず、
  受理集合は任意の 1 行 C++ のまま**で production 到達性はゼロである。次段は wiring wave
  (自由 `implementation` の拒否、wire→mask→predicate の唯一経路化、raw mask と source digest /
  variant ID の束縛、WAL/provenance/report での同束縛、binding 欠落 artifact の proof chain からの拒否)
  で、**受理集合の縮小なので D96 手続が要る**。
  **P5**: provider 注入の拒否 (実 Claude 試行に限る) と role 間 session 共有の拒否 (実行時 +
  成果物再検証の 2 層) を実装し D148 に記録した。**P5 全体は未充足**だが、残余 3 件は
  2026-08-04 の /rulings でユーザー裁定済み — **U-1** `drive` / `preview` 注入は塞ぐ方向
  (既存 2 テストの注入手段を別 seam へ移す設計を伴う別 wave)、**U-2** 未予約 token は P3 の
  予約 receipt に依存させる (P3 実装後。自前 token は発明しない)、**U-3** provider executable の
  許可 digest registry は要求しない (「session 共有を閉じた」とは名乗らない扱いを維持)。
  **P3**: (165) の裁定パッケージは 2026-08-04 の /rulings で **U-A〜U-G 全件が親推奨どおり
  裁定済み** — U-A origin_id を authority manifest digest へ束縛 / U-B cell key で同一 cell の
  2 件目を拒否 / U-C authority root 単一固定 (注入は test fixture に限る) / U-D batch 第一級 /
  U-E committed bytes 照合 (static authority record と mutable runtime head の分離込み) /
  U-F floor 必須化 / U-G 充足は producer 結線と P7 まで含めて数える。
  **実装 wave を再起票できる** (変異事前登録候補 6 件を持ち越す。W1 採用時は本 wave の
  W2〜W5 推奨を同 wave の設計入力にする)。
  一次控えは rulings-inbox 2026-08-04。
  **cap-lift は依然 FAIL** で D114 の上限 1 も不変。P2 / P7 / P9 は未着手。
  逐語は `output/insights/2026-08-04_t244-p1-ir-emitter/`、
  `output/insights/2026-08-04_t244-p5-injection-gate/`、
  `output/insights/2026-08-04_t244-u2-na-bifurcation/`、
  `output/insights/2026-08-04_t244-p4-batch-freeze/`
  base: e12a68bab048c5d27aa40a6bbf4f9e46b9bf4deb4dbeff2943111223136cd2c6
