---
schema: izanagi-spool-v1
ledger: worklog
authored: 2026-09-04
wave: dev-wave-a2-reject-results-section
seq: 1
title: A-2 正式 certification (outer reject) を論文の結果節・表・negative result・図 5 へ落とした — 判定の再解釈は不要だが、意味関門が本走行に未適用である限定を結果節へ入れた (コード + docs + 図 + insight、branch worktree-dev-wave-a2-reject-results-section、変異 16/16 KILLED)
---

## 本文

- 完走済み A-2 4-cell certification (attempt `t2022-20260828c`、outer `reject`) を、新しい測定なしに論文材料へ落とした。
  成果物は `docs/paper-story/results/2026-09-04-a2-certification-reject.md` (結果節の統制稿、表 1、negative result の枠、限定 11 件)、
  `docs/paper-story/figures/fig5_a2_certification_reject.{png,pdf,provenance.json}` と生成器 `tools/plotting/plot_a2_certification.py`、
  README 3 件 (paper-story / figures / plotting) の節。一次資料 = `output/insights/2026-09-04_a2-reject-results-section/`。
- **起動時の確認 (command の指示):** [T-2226] の inert 比較修正と [T-2228] の関門 2 層目は、D1198 の関門族が [T-1999] で 2026-09-01 に
  義務化されたもので、A-2 実走 (08-28) より後である。**判定 `reject` の再解釈は不要** (当時の protocol 出力として不変、規律 7)。
  ただし段 3 レンズ B が「再解釈不要」の断定は T-2228 未完了の下では強すぎると指摘し、裁定で「意味関門の証拠範囲は本走行について未確立、
  後日の緑は遡及的に認証しない、逆の結果が出れば append-only の results file で改める」へ弱めた。結果節・caption・README の stale 注記に実文で入れた。
- **段 3 の 2 レンズは 20 件すべて real だった。** 主なもの: 旧値 (+38.3% / +11.3%) を結果の前に置くと comparator に読まれる → 結果節を
  「A-2 の性能 → 別走行の correctness → 旧系列との関係」の順へ組み替え、旧値の数値を本文・図から外した。限定は登録表だけでなく本文の所定位置へ実文で置いた。
  D12 の「材料レポート」呼称は誤り (手書きの散文を含む) → 「一次資料に束縛した執筆者向け統制稿」へ再分類。生成器の過剰 hardening (path containment、
  TOCTOU、3 file commit protocol) は落とし、生成器 561 行 / テスト 447 行に収めた。
- **設計判断 1 件:** results 系列 (`docs/paper-story/results/`) の新設は {{D:paper-story-results-series}}。両レンズが「未裁定の一般化」と指摘したが、
  D1013 と同型の AI 側の設計判断で可逆 (directory 1 つ) なので、ユーザー裁定待ちにせず決定として記録した。
- **段 6 の所見:** レビュー A (実装) must-fix 4 + nit 1、レビュー B (docs) must-fix 2 + nit 2、親 1 (provenance の再現 argv が worktree 絶対 path を含む)。
  B の 1 件 (決定 fragment の既存 D 番号) は spool 規則が実番号表記を要求するため refuted。残りは fix 子 1 本と親 docs 編集で閉じた。
  変異は M4b を build id / variant / nested build id の 3 件へ分割し、M11 / M12 を実 CLI の subprocess 経路へ変えた。
- **受入全走 1 回目 (tip A + post-claim merge) は 1 件赤:** 新 test file に自走 harness が無く plain-runner の meta-test が落ちた (本変更に帰属、
  実装子の F42 洗い出し漏れ)。fix 子 2 本目が `__main__` 4 行を足して閉じた (焦点走 26 件緑)。生成器と test 関数本体は不変なので変異は再走しない。
- **変異:** baseline PASSED、16/16 KILLED (kill 15 + diagnostic pin M7)、SURVIVED 0、MISMATCH 0、期待 node 完全一致。probe を全件 SURVIVED 期待で走らせ
  観測 node を本登録した。M1 は 18 node の過剰決定 (冗長 gate と明記)、M8 / M9 は同一投影の 2 node、他は単一 node。
  probe 1 回目は既定 queue-wait では混雑で空振りするため投入前に止め、D612 上書き (3600/600) で再投入した。
- **検査:** 焦点走 3 回 (計算ノード dispatch、97 / 99 / 26 passed)。受入全走 1 回目は 20420 passed / 68 skipped / 1 failed (上記)。
  記録 commit 後の最終受入は land の receipt が束縛する。full provenance 監査 (commit A 後) 8142 件、新規違反なし。
- **逐語の可逆正規化 1 件:** `verbatim/s6-review-b.md` の行末空白 16 行 (`git diff --check` 抵触)。原文 sha256 `ed17063931918d8b1b97bd103c8e1a9fab1d82b47fde5c6524cd905dc7154ee1` (8688 bytes) →
  `8a6ab124469203d01064d7a602b8b10d6181057bb217d69e3be586420bc25746` (8656 bytes)。復元は各変更行末へ空白 2 個。可視文字不変。
- **裁定パッケージ候補 (実装せず):** results 文書の表を provenance と機械照合する test、生成器の一般 hardening、T-2228 が A-2 経路で赤を出した場合の results 系列の改訂手順。
- **agent 工数:** codex 子 8 本 (plan 1、consult 2、author 1、review 2、fix 2)。焦点走 3、変異 probe 1 (+ 投入前停止 1) + 本走 1、受入全走 1 (+ 記録後に 1)。
- [T-1647] は実走が [T-2022] (worklog 1071) で完了していたので閉じた。

## 次の一手差分

### 完了

- [T-1647] A-2 4-cell certification の実走は [T-2022] (2026-08-28、outer reject) で完了しており、投入側の分割 (workload 単位 job、finish-group) も着地済み。
  結果の論文化は本 wave の新規項へ引き継いだ。
  remaining: none
  base: 90013efed2feedb016cb8ee409af314396df32e5115053fe631e2b3ca6f2ab41

### 新規

- {{T:a2-reject-paper-results}} **P2・本 wave で結果節・表・図 5 まで着地。残件は論文本文への英語化と、T-2228 の結果待ち**: A-2 outer `reject` の結果節は
  `docs/paper-story/results/2026-09-04-a2-certification-reject.md`、図は `figures/fig5_a2_certification_reject`。英語化は事実命題を足さず表と一次資料へ再照合する。
  T-2228 が A-2 経路の意味関門で本走行の条件差を示した場合だけ、新しい日付の results file で改める (append-only)。read-heavy は A-6 のまま。
