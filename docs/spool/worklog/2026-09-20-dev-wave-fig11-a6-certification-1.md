---
schema: izanagi-spool-v1
ledger: worklog
authored: 2026-09-20
wave: dev-wave-fig11-a6-certification
seq: 1
title: A-6 read-heavy certification reject (attempt a6-20260908b) の exact 2 cell 図 fig11 を、fig6 と同じ生成器の in-place 一般化で作り、README と稿の限定 11 への追補と共に着地する (コード + docs、branch worktree-dev-wave-fig11-a6-certification)
---

## 本文

- ユーザー依頼 (2026-09-20、dev-wave 引数、台帳 ID 未起票) の範囲で 1 wave: 権威 bytes `output/insights/2026-09-08_t2411-paper-story-a6-certification/{certification.json,raw-manifest.json}`
  と raw-manifest 束縛の durable authority 6 file (5 標本) から、fig6 (A-2) と同型の exact 2 cell 図 fig11 (stock `BACK_OFF=0` 対 採用静的 backoff fixed 2 µs、
  median 比 −5.7841%、outer `reject`、correctness は別走行で 2/2 certified) を描き、単独稿 `results/2026-09-18-a6-certification-reject.md` を caption_source として
  SHA-256 束縛する (F36 型)。性能の `reject` と正しさの `certified` は caption でも別文 (D1993 項 2)。B-10 の近接条件 3 block ([T-2430]) は「履歴的照合・独立再現でない・pool しない」の
  1 文で触れるだけ。一次資料は `output/insights/2026-09-20/fig11-a6-certification/README.md`。
- **稿の bytes は変えていない。** 稿は results 系列の凍結物で、fig11 の provenance が現 SHA-256 `34a96842…` で束縛する。依頼文の「単独稿の限定 11「図は無い」を更新」は
  `docs/paper-story/README.md` の results 表の A-6 行 (「図は無い」→ 図 11) と、同系列規則の後ろの「A-6 単独稿の限定 11 への追補 (2026-09-20)」段落で行った
  (T-1998 単独稿の読解上の追補・C14a 追記と同じ型。レビュー A / B とも妥当と判定)。
- 生成器は新 file でなく `tools/plotting/plot_a2_certification.py` の in-place 一般化 (Codex author): 受理 study は `STUDY_PROFILES` の exact 2 件 (A-2 / A-6)、pin 表は 3 leaf、
  workload 数 N は embedded policy から導き 6 × N file 閉包・N 個の request / 時刻一意・2 行 × N 列の layout check、A-6 の caption / suptitle / 脚注、A-6 のみ caption_source を
  provenance へ。**着地済み fig5 / fig6 / fig7 の bytes・caption・artist 射影は不変** (fig6 の landed provenance を閉包に通す test が守る)。**再生成する current-full の
  provenance には top-level `study` が加わる** (着地済み provenance は key を持たず、読取側は無ければ A-2 と扱う)。test は 87 → 111 node (A-6 実寸 fixture = 1 workload × 2 cell × 5 標本・
  verify 12 記録・6 file、実データ test、着地 closure と権威 bytes との直接照合、既存の期待値は不変)。
- 軽量版 (段 2・3 省略。受理集合が広がるので段 6 レビュー 2 本は残した)。段 5 Codex author 1 本 (110 passed / 期待赤 1、実データ生成 rc=0)。段 6 レビュー 2 本
  (A: 過剰・削除 NO-GO must-fix 1 = 変異 m1 / m6 の単一理由性、B: 正しさ境界・整合 NO-GO must-fix 1 = abort 率が「5 rep のうち median に最も近い rep の 1 観測」である旨の欠落)
  → fix 1 本 (caption の 4 点 + 着地 test の直接照合) → 図を再生成 (PNG 不変) → 焦点再レビュー (closed 8 / partial 1 = A-2 の書き分けを plotting README へ、後で閉じた / regressed 0)。
  不採用: `check_figure_layout` の冗長条件の削除 (害なし)、producer 迂回・fixture 一般化。
- 変異 11 件 (positive 1 + negative 10、m6 は段 6 で legacy 経路 (m6a) と current-full の受理縮小 (m6b) に分割、m1 は既存 m11 (pin 表不在で手前拒否) を検出根拠から外した):
  登録 worktree `mut-fig11-a6` (anchor `bb3a2f590`) に harness を直接当て dispatch 本走。期待 node は同経路の probe (anchor `02fa41e25`) で観測した赤 node の完全集合。
  **baseline PASSED、m0 SURVIVED、negative 10 件すべて KILLED、期待 node 完全一致 11/11、MISMATCH / PARSE_ERROR / TIMEOUT 0** (14:53〜15:23 JST)。焦点走 4 走 (110+1 期待赤 / 111 / 111 / 828+3 skip、skip は本 wave の test に無い既存 file 由来)。
- 受入前までに local main を 3 度固定 SHA で取り込んだ (`d4af98f15` = T-2610 docs wave: figures README の一覧 fig10 行と末尾の fig10 追補が本 wave の fig11 行・節と衝突し両側保持で解決、
  `4726b6493` = S-1a 稿 wave: 衝突なし、`4fe49200e` = T-2802 wave: 実装面は `s8b_holdout_admission.py` とその test で本 wave の編集面と重ならず衝突なし)。本 wave の実装面の差分は生成器と test の 2 file だけ。
- 工数: codex 5 本 (author 1、review 2、fix 1、focus 1、全て gpt-6-astra / medium)、計算ノード job = 焦点走 4 + 変異 26 + 受入。作図は login (計測機の外)。

## 次の一手差分
