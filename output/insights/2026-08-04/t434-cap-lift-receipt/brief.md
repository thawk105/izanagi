## 段 1 brief

- **scope**: cap-lift receipt (対象 revision・前提条件 10 件の status・裁定参照・witness hash の
  束縛) の schema と、consumer 結線 6 面 (runbook / 事前登録 / journal / report / 層 3 /
  producer + completeness gate) の設計案を**起草し裁定パッケージで返す**。実装ゼロ・コード変更ゼロ。
- **確定済みユーザー裁定**: (175) の [T-434] 起草指示。D150 (NOT_IMPLEMENTED/NOT_CLAIMED 二分、
  決定 (2-b) 遷移契約、決定 (6)(c) receipt 不在、決定 (7) 変えない境界)。D121 決定 (7) 前提 10 件
  (P1〜P10)。D114 承認上限 1 (3 入口 + completeness 2 consumer)。択一 2 既裁定 (機械束縛は独立 wave)。
- **不変条件**: `MAX_APPROVED_GENERATIONS = 1` 不変 / 機械 gate・status field 新設なし /
  `docs/phase3-main-experiment.md` bytes 不変 / 正しさゲート・proof chain・受理集合不変 /
  実装面の編集ゼロ (docs-only、子は read-only のみ)。
- **成果物の形**: `output/insights/2026-08-04_t434-cap-lift-receipt/` に design draft と
  段 3/4 の逐語、rulings-inbox へ裁定パッケージ、spool fragment (worklog)。新 D は立てない
  (裁定待ちの案のため。D 化は裁定後)。
- **成果物影響 (DW-G05)**: 起草しない場合、cap-lift は D150 決定 (6)(c) のまま「判定結果を
  どこからも再検証できない」人間 gate に留まり、多世代開放の承認が生えたとき receipt 不在のまま
  通る経路が残る。本 wave 自体は certified 選択・受理集合・proof chain を 1 bit も変えない。
- **DW-G01/G04**: 新機構の実装はゼロ。設計メモに留める運用は G04 の既定どおり。
- **並列分割**: 段 2 = codex read-only 起草 1 本。段 3 = codex 敵対 2 本
  (レンズ A: 恒真化・偽 receipt・self-attestation — D150 決定 (6)(a) の穴の再生産検査 /
  レンズ B: 結線 6 面の実在性・凍結衝突・D96/遷移契約との整合)。
- **provisional 前提 (親の provisional 裁定であり攻撃対象)**:
  - (Q1) receipt は機械 gate ではなく人間承認の成果物として設計し、評価器・機械束縛は
    択一 2 既裁定の独立 wave へ送る。
  - (Q2) consumer 結線は「receipt が無ければ・不整合なら cap=1 のまま fail-closed」の方向のみで、
    受理集合を広げる結線を含まない。
  - (Q3) [T-433] (P6 意味的充足契約、並行起草中) と独立に起草できる — P6 の status は
    D138 4 値型 + D150 の 2 語彙への参照で足り、T-433 の未 land 成果物は読まない。
- **受入環境**: docs-only のため実測なし。検査 = `tools/check_docs.py` + 関連テスト (worklog 記録時)。
