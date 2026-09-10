# 段 1 brief — [T-2049 続] B-4 材料レポート生成器と正規コマンド

base commit `24014bdb2` (local main、着手直前)。worktree
`/work/1/SFC/tanab/izanagi/.codex/worktrees/dev-wave-t2049-b4-report-generator`、
branch `worktree-dev-wave-t2049-b4-report-generator`。

## scope

既に main へ着地した B-4 raw 試行記録 producer
(`orchestrator/campaign/p3_b4_raw_record_producer.py`、2076 行、commit `57e4d4cdf`) の出力から、
B-4 の材料レポートを生成する **report generator** と、それを起動する **正規コマンド (sanctioned
command)** を実装する。`p3_b4_analysis_path.py` の docstring が scope 外と宣言する 5 語のうち、
この 2 語だけを埋める。**certified-selection connection は本 wave では実装しない。**

## 確定済みユーザー裁定 (引数)

- 正式 B-4 実走・qsub・性能測定は行わない。
- 規律 2 (正しさゲートを緩める変異を許さない) は緩めない。
- 実装面は Codex `role=author` (D95) が書く。親は直接編集しない。
- 本題の 2 語の実装だけ。**仮想リスク向けの gate・検査・台帳・一般化の追加は scope 外。**
- codex 相談との不一致は解消済み — producer は 2026-08-29 に着地済みであり、carry の「新規」は古い。

## 実測で確認した前提 (brief 前の実測)

- 生死確認: `tools/run_tests.py orchestrator/tests/test_p3_b4_raw_record_producer.py
  orchestrator/tests/test_p3_b4_analysis_path.py` = **46 passed / 28.44s** (計算ノード
  request `963546.nqsv`)。producer から分析判定までの経路は現行 main で生きている。
- repo 上に実在する B-4 publication artifact は **0 件** (`output/campaigns/` に B-4 root 無し)。
  したがって report generator の実走確認はテスト fixture が生成する publication に対して行う。
- 既存の 材料レポート renderer は `orchestrator/campaign/layer3_report.py` で、正規コマンド形は
  `python3 orchestrator/campaign/layer3_report.py ...` (`main(argv)` + argparse、:786)。
  同 renderer は WAL と whiteboard しか読まず ledger を読まない
  (`docs/phase3-8c-wiring-design.md`)。**B-4 の ledger を読むレポートは純増である。**
- 編集面の重複: `p3_b4_*` / `layer3_report` / `orchestrator/reports` に触れる稼働 branch は
  t1784 (admission_record)、t1909 (wiring_probe)、t2060 (layer3_report) の 3 本。
  いずれも本 wave の新規 file とは重ならず、両者とも作業ツリーは clean。

## 不変条件

1. `p3_b4_analysis_path.py:67 _SOURCE_CLOSURE_PATHS` の 5 file を **1 byte も変更しない**
   (closure receipt が whole-file sha256 を載せ、prereg consumer が AST 形状も検査する)。
   docstring の 5 語の書き換えも行わない — 新設 module は当該 module の scope 外にあるため、
   文面は変更なしで真のままである。
2. `docs/phase3-b4-reflux-ablation-preregistration.md` を変更しない
   (`PREREGISTRATION_SECTION_5_1_1_SHA256` / `..._SEMANTIC_SHA256` が §5.1.1 の bytes を pin する)。
3. producer を変更しない。したがって producer の出力 bytes は変わらない (DW-O10 は差分ゼロで閉じる)。
4. `layer3_report.py` を変更しない (t2060 が所有)。
5. **完全射影 (D12 / D829)** — producer と ledger が出した値を view 側で正規化・削除しない。
   全 block・全 arm を無条件に載せ、file-drawer を作らない (prereg §7.1)。
6. **判定の 4 分類** (成立 / 不成立 / 判定不能 / protocol violation) を保ち、非有意を
   「還流に価値なし」と書かない (prereg §7.1)。
7. レポートは自分の**認証水準を機械可読に宣言**する (D787 の向き)。ただし D787 / D814 は
   別装置 (`tools/codex_reasoning_ab.py`、昇格経路) に対する裁定であり、本 wave へ
   新しい昇格 validator・AST 検査を新設することは scope 外である (ユーザー裁定)。

## 成果物の形

- 新規 `orchestrator/campaign/p3_b4_material_report.py` — report generator 本体 +
  `main(argv)` の正規コマンド。読む入口は publication root だけとし、判断値を caller から受け取らない
  (D162 の向き、producer と同じ)。組立ては
  `load_b4_prerun_publication` → `assemble_b4_raw_analysis` → `build_contract_binding` →
  `evaluate_b4_artifacts` の既存 API の合成に限る (新しい分析規則を作らない)。
- 出力は人間可読の `report.md` と機械可読の JSON の 2 つ。provenance (publication root、
  registry/manifest/receipt の path と sha256、issuer commitment、非保証の列挙、再現コマンド) を
  レポート自身に埋める (`docs/orchestrator-design.md` 材料レポートの出力規約)。
- 新規 `orchestrator/tests/test_p3_b4_material_report.py` — 正例 (201 block 完全) と、
  欠測・拒否・判定不能を落とさないことの負例、clean subprocess での CLI 起動 1 本。

## 割れうる前提 (段 3 の攻撃対象)

- **(P1)** 出力先は caller が `--output-root` で与える形にし、既定を publication root 配下の
  `reports/` とする。campaign root の exact-set 完全性検査を摂動させない置き場が要る。
- **(P2)** `evaluate_b4_artifacts` の `floor` は事前登録 §5 の未記入欄であり (D1060)、生成器が
  値を発明してはならない。CLI 必須引数にして出所をレポートへ刻むか、未記入なら判定を
  「判定不能」として出すかの択一。親の provisional 裁定は**必須引数 + 出所記録**。
- **(P3)** 「sanctioned command」は `python3 orchestrator/campaign/p3_b4_material_report.py` の
  module 直起動形で足り、`hooks/guard_bash.py` の `_SANCTIONED_PATHS` (計算ノード投入器の
  exact path 列挙) への登録は不要である。本 wave は qsub を起動しない。
- **(P4)** レポートの行は prereg §7.1 が要求する 11 項目を持つ。現行 artifact から取れない項目
  (model/prompt hash、予算消費など) は**捏造せず「不在」と明記して載せる**。

## DW-G05 成果物影響

- 生成器が無い間、B-4 の材料レポートは存在せず、raw 試行記録から論文材料へ至る経路が開かない。
  この wave が塞ぐのは「証拠はあるがレポートが無い」区間である。
- 完全射影を破ると (不変条件 5) 生存者バイアスがレポート生成の上流へ移り、成果物の値と受理集合が
  静かに変わる。ここが must-fix の中心。

## 並列分割方針

実装面は 1 単位 (新規 module + 新規テスト) に閉じるため、段 5 の Codex `role=author` は 1 本。
段 2 プラン 1 本、段 3 敵対相談 2 本、段 6 敵対レビュー 2 本 + fix。

## 受入・実測環境

- 焦点走・受入全走とも `python3 tools/run_tests.py` の既定自動判定に従う (§7.0.0)。
  生死確認は計算ノードへ自動 dispatch された。強制 dispatch はしない。
- 正式 B-4 実走・qsub・性能測定・build は行わない。
