---
schema: izanagi-spool-v1
ledger: worklog
authored: 2026-08-05
wave: dev-wave-token-economy
seq: 1
title: 次の一手 carry 行を compact 化し起動読み込みを 1 エントリあたり 5,099 bytes 減らした — 最大の削減候補 2 件は裁定へ返す (コード + docs、branch worktree-dev-wave-token-economy)
---

## 本文

- **ユーザー依頼は「トークンの使用量を品質を落とさずに節約する」** (command 引数)。
  探索の結果、セッション起動時に読む約 72KB のうち**最大の無情報ブロック**は
  worklog の持ち越し行だった。`docs/worklog.md` 98,391 bytes の **64% (1,671 行 / 63,498 bytes)**、
  末尾エントリ 15,168 bytes の **59% (237 行 / 9,006 bytes)** が
  `- [T-NNN] 変わらず ((N) 参照)` の機械生成定型である。archive 累計では 830,541 bytes。
- **`- [T-NNN] (N)` へ縮めた。** carry 短縮 5,214 bytes − 見出し凡例 +115 bytes =
  **正味 5,099 bytes/エントリ** (末尾エントリの 33%)。判断は {{D:compact-carry-format}}。
- **親 brief の中心的前提が段 3 で反証された。** 親は「`((N) 参照)` の N は常に直前エントリで
  構成上導出可能」と書いたが、レンズ A が **exact carry 23,635 行中 1,316 行が
  `参照先 != エントリ番号 - 1`** を指すと実測した。`_global_ordinal_entries` は欠番・単調性を
  固定しない。よって ID 単独行案は却下し ordinal を行内に残した。
- **親の計数も 3 点訂正した。** archive の 1,061,487 bytes は部分一致の値で exact は 830,541、
  繰り越しは 237 件でなく **245 件** (237 は carry 行数)、「rotation が約 2.5 倍の頻度」は
  導出不能で実比 1.52 倍 — **撤回した**。
- **`tools/check_docs.py` は無改変。** D70 保存則の受理集合は変えていない
  (`TASK_ID_AT_HEAD_RE` は `(?=$|[ \t])` を持ち ID 単独行を元から受理する)。
  レンズ A が「ID 脱落は現に赤になる」ことを確認し、実効性低下は refuted。
- **読者契約の是正。** クラス 3 は worklog 末尾だけを読むため、compact 行の意味が末尾から
  辿れない問題を段 6 レビュー B が摘出した。親は当初「CLAUDE.md は変更しない」と裁定したが、
  レビュー B が **CLAUDE.md を触らない代替案 (生成見出しへの固定凡例)** を出したため採用した。
  `.claude/commands/rulings.md` は旧語句 literal を書式非依存へ **byte 中立 (4,988 のまま)** で置換。
- **段 3 敵対 2 レンズ、段 6 敵対 2 レンズ、焦点再レビュー 1 本。** 段 6 は 2 本とも NO-GO で
  must-fix 計 6 件。fix を 2 巡した後の焦点再レビューは **GO**、8 所見が
  closed 7 / partial 1 (到達不能 guard の nit) / regressed 0。
- **scope 外の real 所見 2 件を実装せず裁定へ返す。どちらも本 wave より削減が大きい。**
  (a) `.agents/skills/dev-wave/SKILL.md` が単独段 worker/reviewer も無条件にクラス 3 起動させ、
  **reviewer 1 本あたり 25,663 bytes** 余分 (本 wave の約 5 倍)。
  (b) campaign の固定 prompt prefix は 4 役計 36,713 bytes、既定 3 workload で
  初回以外 **73,426 bytes** が同一。ただし prefix cache の提供能力・hit・token 会計の証拠が
  repo 内に無いため実現済み削減として数えない。session 再利用と出力 cache は
  fresh context の構造遮断 (D39/D45/D47) を壊すので引き続き禁止。
- **繰り越しの滞留を実測した。** 全 182 エントリ走査で、末尾の繰り越し 245 件のうち
  **129 件が 50 エントリ以上連続で無変化**、最長 109 連続、今回更新は 8 件のみ。
  見送り台帳は D70 の正当な sink なので整理すれば carry 件数自体が減るが、
  1 件ずつの意味判断を要するため自動削減の対象にしない。
- **セッション異常。** 段 6 焦点再レビューで、**出力 `.md` (13,253 bytes) は書かれたのに
  完了マーカー `.done` が作られない**状態が起きた。ジョブ中断で detached wrapper が
  `echo $? > .done` の前に落ちたためである。`DW-O01` の「完了は `.done` と exit code だけで
  判定する」に従い成果物を採用せず再走した (F24 の再発)。孤児成果物は証跡として保存。
- **受入全走を 1 回やり直した。** 初回 (request 889879) は 4 failed / 6,194 passed で、
  失敗はすべて `test_s8b_floor_campaign.py` の `assert repo_before == _real_output_snapshot()`。
  `DW-O18` に従い単独再走したところ 199 passed / 2 skipped / 0 failed で再現せず、
  **原因は親自身が走行中に `output/insights/` を書いたこと**と判明した ({{F:acceptance-repo-write-race}})。
  当初「別 wave の全走との干渉」を疑ったが誤りだった。記録 commit でツリーを固定して取り直した。
- **エージェント工数。** codex 子 9 本 (段 2 プラン 1、段 3 レンズ 2、段 5 実装 1、
  段 6 レビュー 2、fix 2、焦点再レビュー 1 + 中断による再走 1)。
- **実測 (2026-08-05、worktree `dev-wave-token-economy`)。** 対象テスト = **366 passed / 0 failed**。
  `python3 tools/check_docs.py` = 違反なし。`check_ai_provenance.py` = 1,261 件で違反なし。
  変異 matrix の逐語と受入全走は `output/insights/2026-08-05_token-economy-compact-carry/`。

## 次の一手差分

### 新規

- {{T:devwave-worker-class1-branch}} **P1・ユーザー裁定待ち**: 単独段 worker/reviewer が
  `.agents/skills/dev-wave/SKILL.md` から無条件にクラス 3 起動する経路を分岐させ、
  親から dispatch 済みの子はクラス 1 + 親 prompt の必読だけに従わせるか。
  reviewer 1 本あたり 25,663 bytes。段構成・裁定境界の変更のため実装せず裁定へ返した。
- {{T:campaign-prefix-cache-feasibility}} **P2・ユーザー裁定待ち**: campaign の固定 prompt prefix
  (初回以外 73,426 bytes) に byte-identical prefix cache を効かせられるか、
  提供能力・hit・token 会計の証拠を先に取るか。session 再利用と出力 cache は禁止のまま。
- {{T:next-action-backlog-triage}} **P2・ユーザー裁定待ち**: 50 エントリ以上無変化の繰り越し
  129 件を見送り台帳 (D70 の正当な sink) へ整理するか。1 件ずつの意味判断を要する。
