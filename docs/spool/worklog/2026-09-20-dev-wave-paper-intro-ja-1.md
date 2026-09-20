---
schema: izanagi-spool-v1
ledger: worklog
authored: 2026-09-20
wave: dev-wave-paper-intro-ja
seq: 1
title: 本体論文 (日本語) の序論・貢献・限界の本文を、論文ストーリー 2026-09-20 版と claim-evidence 稿から新規に起草し、版・稿より後の裁定 (D2172〜D2183、pin 前進) で状態語を現在地へ揃えた (docs のみ、台帳 ID 未起票、branch worktree-dev-wave-paper-intro-ja)
---

## 本文

- ユーザー依頼 (2026-09-20、dev-wave 引数) に基づく 1 wave。着手時 local main `fec4a8187` から fresh worktree、段 6 レビュー後にピア通知を契機に
  local main `482f19b88` ([T-2304] pin 前進) を ff-only で取り込み、採用時点をそこへ揃えた。専用 handoff は背景 job の tmp。実装差分ゼロ
  (Codex 実装子なし)、軽量版 (段 2・3 省略、`DW-C00` の「一次資料から事実を再抽出する docs-only」につき段 6 read-only レビュー 1 本 + 焦点再レビュー
  2 本)。成果物は `output/insights/2026-09-20/paper-intro-ja/{intro,contributions,limitations}.md` (約 15 / 20 / 30 KB、末尾に執筆者向けの出所) と
  同 dir の `README.md` (wave 記録、状態語の更新表、限界節から移した「証拠ごとの現在地」の別表、レビュー逐語)。
- 入力: ストーリー 2026-09-20 版 §1 / §2 / §3 / §6 / §7、claim-evidence 2026-09-20 稿、README の stale 注記 3 件、figures README。数値は権威 bytes
  (A-2 / A-6 / B-7 fixed5 の certification.json、S-1 report、p2-5-summary、between_run_noise JSON) と results 稿から写し、版を数値の出所にしていない。
  相対リンク 73 本の不達 0。
- 版・稿より後に動いた状態語 10 項目を D 本文で読み直して現在地で書いた: B-7 は限定付き充足 (D2174 項 3)、床値 g1 は AI 委任の批准で発効し oracle
  gate-check は不整合 2 件で `allowed: false` のまま (D2180、[T-2810])、A-1 attempt-0002 は認可・gate 解除実装済み・未投入 (D2172 項 2 / D2178)、K2 同 job
  stock 対照は実装済み・未投入 (D2172 項 3 / D2183)、B-5 は段階実装 + 上限付き試走認可・本走未認可 (D2172 項 4)、B-8 は事前登録 v1 未発効 (D2175)、
  B-10 cohort 2 は fig8b で併記・合成しない (D2173)、mocc 追加実験は見送り (D2172 項 7)、仮説層 v3 は実装・適用済み (D2143)、ccbench pin は
  `e9e477ca` へ前進し較正・certified 系列・性能比較は含まない ([T-2304])。旧記述は執筆時点では真で、版・稿は改めていない。
- 段 6 レビュー 1 本 (gpt-6-astra / medium、24 call、441 秒): NO-GO、所見 8 (must-fix 5 / should-fix 3)、real 8 / refuted 0、状態語 9 項目と主要数値は
  すべて支持。採用した fix = A-1 の観測値の存在を認めつつ充足を否定する文へ、貢献稿に certified の保証範囲を定義、検証相の判定集合 (本走 24 + 校正完走 6、
  未完走 2 件 / 候補は verdict なし) を明記、限界 §7 の作業表を README へ移し本文は散文に (brief の P1 は不採用)、個別実験の細部を削減、実証状態を結果単位で
  7 値表示、+147.4% の出所を P2-4 稿の再計算値へ、位置づけを 1 文 + 3 条件 + 調査状態へ縮小、右 tail に過抑制の費用を併記。
- 焦点再レビュー 1 (26 call、383 秒): 前巡 8/8 closed、親の派生値・量化語はすべて一次資料と一致、新規所見 2 (must 1 = 「現行の素材コーパスの下で
  4 度到達」を旧 pin `511c9538` の下へ、should 1 = 貢献稿の pin 前進の文に「較正・certified 系列・性能比較は含まない」)。焦点再レビュー 2 (6 call、
  102 秒): 2 件とも closed、新規所見なし、GO (DW-O16 の 3 巡内)。
- 検査: `check_docs` 違反なし、`git diff --check` 緑、相対リンク 73 本の不達 0。docs のみで実装面ゼロのため変異 matrix は免除。焦点走 (check_docs の
  consumer test) と provenance 監査は記録 commit の後に実走し、結果は専用 handoff と job dir の receipt に集約する。受入・land も同じ。
- 限界・言わないこと: 3 稿は投稿本文ではなく執筆者向けの日本語草稿。英語化・関連研究節・新規実験・図の作り直しは行っていない。稼働中・未着地の
  wave の内容 (A-1 attempt-0002 の投入、K2 4 巡目、B-5 試走、[T-2810]、W-4) は完成扱いしていない。本 wave の照合は 1 主体の再計算 + レビュー 3 巡で
  独立監査ではない (D920)。
- 工数: codex 3 本 (review 1、focus 2)。計算ノード job: 焦点走と受入 (記録 commit 後)。dev-wave 改善候補は段 8 で 0 件。

## 次の一手差分
