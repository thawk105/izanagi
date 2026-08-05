---
schema: izanagi-spool-v1
ledger: worklog
authored: 2026-08-05
wave: dev-wave-t450-t412-preface
seq: 1
title: [T-450] の DW-O15 残骸を削除し、[T-412] 前置として受入形の削除検査を trigger 非依存の fail-closed にした — 剪定は 0 bytes 回収と確定 (コード + docs、受入 6489 passed/20 skipped、変異 12/12 KILLED、branch worktree-dev-wave-t450-t412-preface)
---

## 本文

- **[T-454] の前置 2 件を 1 wave で実行した。** 裁定の出所は archive (184)。
  設計判断は {{D:acceptance-deletion-gate-fail-closed}}、裁定パッケージは
  `output/insights/2026-08-05_t450-t412-preface/README.md`
- **段 3 の敵対レンズ 2 本が同じ blocker に独立到達し、親は 14 件すべてを real と裁定した
  (refuted 0)。** 内容は「残余義務を完全に機械化した」という主張が実装を上回るというもの。
  親の段 1 前提 (P1)「stage が緑への唯一経路」は反証された — 意図しない削除を**復元**しても
  次回 preflight は緑になる。これを受けて成果の射程を runner-local へ狭め、
  `DW-O11` 第 2 文は残した。**したがって [T-412] の剪定は 0 bytes 回収で確定した**
- **段 6 の焦点再レビューが NO-GO を出し、親はこれを real と認めた。** 親の段 4 裁定 §3 が
  「child env に legacy key が現れない」と書きながら、実 child env の排除 (`_job_run` 側) を
  scope 外一覧に入れていなかった。**裁定文の誤りとして訂正**し、射程を「親 dispatcher が
  新規生成する request の `environment` field」へ限定して、残余は裁定パッケージへ送った。
  訂正の根拠は (a) 現行 `run_tests.py` に reader が無く成果物影響がゼロ (`DW-G05`)、
  (b) dispatch の信頼境界という別機構で D96 の独立 D と境界テストが要る、
  (c) 未知 key を拒否するか黙って落とすかの択一が段 2/3 で一度も攻撃されていない、
  (d) 裁定時点で dispatch job が 3 件 RUN 中で、拒否方式は他 session の job を落としうる
- **erratum 3 件。** (1) commit `0ccf85ba` の題名「must-fix 2 件を閉じ」は過大で、
  焦点再レビューの判定では C1 は `partial` である (本文と実装は一致)。(2) 変異は 2 回走らせた —
  初回は 12/12 検出・SURVIVED 0 だが 4 件が MISMATCH で、いずれも**事前登録 node が実 node の
  真部分集合**だった (取りこぼしではない)。実測に合わせて事前登録を更新し再走して 12/12 KILLED。
  初回台帳も消さず残す。(3) 段 1 brief の「task-run 台帳 14 件」は top-level entry 数で、
  実 task-run directory は 10 件。また `DW-G04` の発火 path は既存 deletion fixture で書けたので、
  「台帳が空だから書けない」という brief の理由付けは誤りだった
- **子の工数。** codex 子 8 本 (plan 1、段 3 敵対 2、実装 2、段 6 レビュー 2、fix 1) +
  焦点再レビュー 1 = 9 本。うち fix は 1 巡で閉じた。受入全走は 2 回、targeted 走は 2 回、
  変異走行は 2 回 (計 28 dispatch)。受入は本 wave の実装が揃った tip `a2f8b48b` で
  6460 passed/20 skipped、land 対象 tip での再走が 6489 passed/20 skipped。
  差 29 件は取り込んだ local main が持ち込んだテストで、本 wave の差分由来ではない
- **[T-166] の 3 limb のうち 1 つを閉じた。** task-run 台帳の bypass 使用 field は、
  bypass が reader ごと消えたため実装しても全 run で false になる恒真な監査 field になる。
  残る 2 limb (隔離 checkout への modules cache 複製、rc 13/14 の診断粒度) は据え置き

## 次の一手差分

### 完了

- [T-450] `DW-O15` 節 (55 bytes) を `docs/dev-wave/operations.md` から削除し、入口の条件 15 は
  `DW-M07` 単独で残した。`tools/check_docs.py` の `_OPERATION_NUMBERS` と literal pin も追随。
  `DW-O07` と同じく復活には新規裁定が要る旨をコメントに残した。変異 A-M1〜A-M5 で 5/5 KILLED。
  remaining: none
  base: fef37ea5827e5b9e864908227217cf16075ec2dfde57c28e170d85a3a2673c77

### 更新

- [T-412] **P2・前置は完了。剪定は 0 bytes と確定 → [T-287] §5 (a) は依然未解決**:
  `DW-O11` の残余義務のうち機械化できる面 (受入形での bypass 全廃と git 検査不能の fail-closed 化) は
  land した。しかし受入形の判定が argv の構文的代理でしかなく、受入結果と landed tip を結ぶ
  receipt も無いため、第 2 文は削除できない。**回収 bytes は 0**。必要枠 270 bytes は
  [T-454] のテスト化 pass へ持ち越す
  base: e5f4c1708db08f31d6f9ee0cc9bcaff3021d733cc60d9aa83d9f299af4537373
- [T-454] **P2・前置 2 件が完了 → テスト化 pass を起票可**: [T-450] は完了、[T-412] 前置は
  runner-local まで完了した。ただし前置で空いたのは [T-450] 分の 55 bytes だけで、
  [T-412] の剪定は 0 bytes だった。pass の scope (待ち手規約 3 条 + (217) の 3 候補 +
  `DW-S06-B` への F112/F124 追記) は不変
  base: 4b843e1c4766c43a0770de1f4a930abc0a2b1cad7e1f87d9ea5119986178ee74
- [T-166] **P3・3 limb のうち 1 つを閉じた**: task-run 台帳の bypass 使用 field は
  {{D:acceptance-deletion-gate-fail-closed}} により不要 (恒真な監査 field になる) として閉じた。
  残るのは隔離 checkout への modules cache 複製と、rc 13/14 の診断粒度の区別の 2 件
  base: e35427b4c86843f9bacacbc03be226280e7115faa199b513951aaded359d1695

### 新規

- {{T:acceptance-mode-and-receipt}} **P2・新規・ユーザー裁定待ち (択一 3 案)**:
  `DW-O11` 第 2 文を機械化するには、argv 形状の代理をやめた明示 acceptance mode、
  受入コマンド・rc・tip SHA・index/worktree fingerprint を束ねた receipt、
  それを land / 記録側が消費する配線の 3 点が要る。択一と親の推奨 (見送り) は
  `output/insights/2026-08-05_t450-t412-preface/README.md` §3 R1
- {{T:staged-delete-tree-identity}} **P3・新規・ユーザー裁定待ち (択一 3 案)**:
  `git rm --cached` は index から消えて worktree に残るため deletion gate をすり抜け、
  測った tree と commit する tree が食い違う。preflight 後 pytest 起動前の TOCTOU も残る。
  択一と親の推奨 (残余として記録) は同 README §3 R2
- {{T:dispatch-request-env-revalidation}} **P3・新規・ユーザー裁定待ち (択一 3 案)**:
  `tools/pegasus/dispatch_compute.py` の `_job_run` が request の `environment` を allowlist で
  再検査せず `child_env.update()` する。親側 allowlist から key を外しても既存 request と
  ambient 経路は残る。現行 reader が無いため成果物影響はゼロ。択一 (拒否 / 黙って落とす /
  現状維持) と親の推奨 (落とす) は同 README §3 R3
