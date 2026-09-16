---
schema: izanagi-spool-v1
ledger: worklog
authored: 2026-09-17
wave: dev-wave-t2723-floor-cell-admission
seq: 1
title: [T-2723] B-4 floor セルの読取を事前登録 §5 の admission 契約へ接続した (コード + テスト + docs、branch worktree-dev-wave-t2723-floor-cell-admission、変異 matrix = baseline PASSED・11/11 KILLED・等価 1 SURVIVED・MISMATCH 0・期待 node 完全一致)
---

## 本文

- ユーザー依頼は「material report から floor artifact issuer への floor セル読取経路が、文書全体から floor 行を
  exact prefix で探し §5 の見出し境界・他の欄・責任者・開始時刻を検査しない件を、§5 の見出し境界内の 1 行だけを
  既存の admission 契約に接続して受理する形へ直す。新しい汎用 validator は設計しない。正例 (現行の材料レポート) と
  負例 (§5 外の同 prefix 行・責任者欠落) を同じ変更単位で置く。Codex author (D95) + 変異事前登録。本題の読取経路
  だけ。仮想リスク向けの gate・検査・台帳・一般化の追加は scope 外。規律 2 を緩めない」。
- **閉じた。** 一次資料は `output/insights/2026-09-17/t2723-floor-cell-admission/README.md`。設計判断は
  {{D:floor-cell-reads-through-section5-admission-parser}}。実装 commit `8cfcd62f1` (Codex author)。
- **起票の欠陥を実文書 bytes の対照 probe で変更前後に示した。** 責任者を `未記入` にした文書は変更前 None (受理) →
  変更後 row error。§5 の floor 行を消して外側に pin を置いた文書は変更前 path_error (外側の pin を読んで loader へ
  進んだ) → 変更後 row error。無改変の実文書は両方 None (材料レポートの legacy 経路不変)。
- **段 3 レンズ A が段 2 plan の「NFKC 後で sentinel を比べる」案を追加緩和として反証した。** `未記⼊` (末尾 U+2F0A)
  が拒否から None へ変わる。裁定で strip 後 raw の比較に変え、負例 test と変異 M10 を足した。
- **親 brief の不変条件「受理集合の変化は縮小 + strip だけ」は両レンズが独立に反証した。** 外側同 prefix 行の無視は
  strip と独立の拒否→受理であり、縮小は共有 parser の全条件に及ぶ。列挙契約 (決定 3) へ置き換えた。
- **レンズ B の「実文書直読 test を real-repo 分類へ登録せよ」は不採用 (決定 4)。** 先例 `test_p3_b4_analysis_prereg_consumer.py`
  は未登録・marker 無し、親 tree への access は全 node が read で登録は正しさに効かず、依頼が台帳追加を scope 外と定める。
- **親の読解所見 1 件を fix 子で直した。** author の新規 import が絶対形 `from orchestrator.campaign.p3_b4_admission_record import`
  で、規約走査器 `scan_campaign_relative_imports` (level 0 の `orchestrator.campaign.*` を違反、既知例外 1 件) に触れる。
  該当 test は growth hold で `IZANAGI_RUN_GROWTH_HELD_TESTS` (ユーザー明示専用、D636) でしか走らないため親は実走せず、
  相対 import へ直した。
- **段 6 レビュー 2 本は must-fix 0 / GO。** nit 3 件 (行削除 test の過剰決定は単独検査の証拠から外す、admission 新
  test の label を padded に、他欄 `未記入` + 有効 pin の正例) を fix 子で反映した。
- 実走: baseline (変更前) 4 file 230 passed / 統合後 7 file 361 passed + 6 skipped (growth hold) / fix 後 6 file
  338 passed (いずれも計算ノード)。provenance full 10,809 件・新規違反なし。
- **変異 matrix (container worktree、`run_tests.py` 3 file、probe と本走で各 14 request = collection + baseline + 12 変異)。** probe 走 (全件 SURVIVED 登録) で観測 node を
  集めてから本走。本走は baseline PASSED、負例 11 件 (M1〜M11) すべて KILLED で期待 node と観測 node が完全一致、
  等価変異 M0 (docstring) は SURVIVED、MISMATCH 0。専属 killer: M2 責任者述語削除 → unrecorded-owner 負例 1 node、
  M3 label 集合検査削除 → unknown-label 負例 1 node、M8 pin の NFKC → raw pin 正例 1 node、M10 sentinel の NFKC →
  NFKC 異体負例 1 node。M11 (全欄へ述語 = 過剰拒否の正例) は実文書 test と材料レポート 33 node を含む 41 node。
- 残存 (scope 外、記録のみ): 両見出しを壊して別所へ canonical §5 を置く F423 型は admission parser の既知限界。他欄が
  `未記入` のまま有効 pin を置けば floor が present になる既存挙動。事前登録 §11.3 末尾の「生成器は本書を読まない
  (D1377)」は陳腐化しており文書の追補は別 wave。
- 工数: codex 子 7 本 (plan 1、consult 2、author 1、review 2、fix 1、全段 `gpt-6-astra` / `medium`)。親の実測は
  probe 4 本、焦点走 3 本 (計算ノード)、変異 2 走 (probe 14 request + 本走 14 request)、provenance full 1 本。

## 次の一手差分

### 完了

- [T-2723] floor セルの読取を §5 固定表の admission 解析 + 責任者行述語へ接続し、正例 (実文書 → None) と負例
  (§5 外の同 prefix 行・責任者欠落) を同じ変更単位で置いた。
  remaining: none
  base: 8a3ef12266c7529d2eb5853248f38b6f02383422465896b2e291bbf3b8a628ed
