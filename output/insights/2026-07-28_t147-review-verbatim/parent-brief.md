# [T-147] 段 1 brief (2026-07-28、基準 19f72e5、branch dev-wave-t147-budget-restructure)

## scope
- core.md 縮約 (S01/S04/CTX の物語断片を F ポインタ・圧縮語へ、意味保存) で予算を空ける
- payload 1: S01 へ「受入全走・実測の実行場所を brief で確定する」受け皿 1 行 (マシン固有事実は書かない)
- payload 2: C00 を「子の起動条件を先に判定 → 該当なしのときだけ軽量版」の順へ再構成 (worklog (26) 逸脱の根)
- O17 縮約 + 配置規則 (空行なし同一最終段落) の正本 ai-provenance.md への移設 (P2)
- 削除候補監査: 発火不能は O07 のみ (task-run pilot は T-012 裁定で凍結中)。削除は実装せず
  T-012 再評価と束ねて裁定パッケージへ
- scope 外: O11/O18/O20 の機械化 (新 gate 新設 → 次の一手へ送る)、財布分割 (梯子 c、不要見込み)

## 確定済みユーザー裁定
- T-127 (2026-07-28): byte 予算上限は据え置き。空けるのは陳腐化ルールの削除・縮約
  (安全義務の削除・弱化は不可)。失敗の恒久対応はテスト・機械検査を優先
- T-147 実行計画凍結 = `output/insights/2026-07-28_t147-budget-restructure-plan.md` (梯子 a→b を本 wave)

## 前提実測 (brief 前、DW-S01。すべて実ファイル読取、模擬なし)
- 財布は二重: core.md 9,000/9,000 (headroom 0) + 総量 23,991/24,000 (`DEV_WAVE_AGGREGATE_BYTES`)。
  payload は core.md 行きなので core.md 内で net ≤ 0 が必須
- 覆った前提: 計画凍結の「O18 → run_tests.py が強制」は誤り — `tools/run_tests.py` は
  `subprocess.call` に `cwd=` を渡さず `os.chdir` もない (`:377,379,441`)。O18 縮約を scope から
  除外し、機械化は次の一手へ (P1)
- O17: trailer は `check_ai_provenance.py` (git interpret-trailers --parse) が実在被覆。ただし
  「空行なし同一最終段落」の予防規則は正本 ai-provenance.md に明文が無い (「message 末尾に 1 行以上」のみ)
  → 削除でなく正本へ移設してから O17 をポインタ化 (P2)
- F1/F23/F24/F25/F29/F31/F35/F37/F41 は failures.md に実在 (ポインタ有効)
- 条件 O08/O09/O10 不成立 (freeze / oracle gate / proof chain・凍結成果物 bytes に触れない)。
  O13 は読了済み、gate 新設は本 wave でしない

## 不変条件
- 安全義務の削除・弱化ゼロ。縮約は意味保存のみとし、敵対レビュー 2 本で担保 (check_docs は byte・構造のみ)
- core.md ≤ 9,000 / 総量 ≤ 24,000 / 予算値・dispatch 節構成 (`REQUIRED_REFERENCE_SECTIONS`) 不変
- 成果物影響 (G05): docs-only。certified 選択・レポート・台帳の値・受理集合・参照は変わらない。
  実装しない場合の影響 = core.md 満杯が続き受け皿 1 行すら入らず、(26) 型の子スキップ逸脱の再発余地が残る
- 受入全走・実測の実行場所 = 本 checkout (共有ログインノード)。rc のみ比較に使い、wall は使わない (F41)

## 成果物の形・並列分割
- docs diff (core.md / operations.md / ai-provenance.md) + 逐語 2 本の凍結 + worklog + 裁定パッケージ
- 親が編集・commit (docs は親のみ編集可)。codex read-only 敵対レビュー 2 本:
  レンズ A = 意味保存・安全義務の削除/弱化検出 / レンズ B = dispatch 閉包・payload 妥当性・予算・正本整合
- (P1) O11/O18/O20 機械化の見送り、(P2) O17 配置規則の正本移設 — 親の provisional 裁定であり攻撃対象
- (P3) 第三の縮約対象を計画候補の CTX から S08 へ差し替え — S08 は入口 (wave 開始命令) と
  `skill-self-improvement.md` (段 8 preflight で全節必読) の三重複で、正本共読が構造保証されている。
  CTX は固有義務 (supervisor 停止列挙) が密で圧縮リスクが高い。provisional・攻撃対象
