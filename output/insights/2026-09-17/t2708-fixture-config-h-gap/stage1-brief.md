## 段 1 brief (2026-09-17 21:55 JST)

- 研究前進: 論文主張を直接進める wave ではない。土台 = t080 e2e (T-080 receipt 発行の production scanner を stub せず走らせる、規律 2 の防壁の e2e) の fixture 忠実性。実 repo で scan される 1 file (`orchestrator/tests/fixtures/sort_swo_masstree/config.h`) が fixture で欠ける。止めている研究は無い (判定不変を静的確認済み)。完了判定 = 忠実性の増分と所要増分の実測値つき採否裁定パッケージを insight + worklog fragment で返す。
- scope: 影響測定と裁定パッケージだけ。実装差分ゼロ (fixture 構築 `_build_t080_stub_free_e2e_repo` は変えない)。probe は repo 外 (job dir)。T-2710 (受入床の設計裁定) の scope には入らない。
- 確定済みユーザー裁定: D2068 (高速化 3 案不採用、単発測定は根拠にならない、同一 tree 内の交互対比較だけ使う)、D2086 (fixture の検出責任は「構築時点の可視集合」)、D747 (テスト削除で速くしない)、規律 2。
- 不変条件: 規律 2 を緩めない (fixture の scan 集合を減らす方向の案は出さない)。実 repo の凍結成果物・receipt の bytes を変えない。tracked file を一時変異しない。
- 成果物: `output/insights/2026-09-17/t2708-fixture-config-h-gap/` (README + stage1〜4 逐語 + probe 数値)、`docs/spool/worklog/t2708-fixture-config-h-gap.md`。decisions fragment は「実装しない/する」の裁定が本 wave で確定する場合だけ (ユーザー裁定へ返す場合は fragment を書かない)。
- 変更面 (実アンカー表): 実装面ゼロ。docs のみ: 上記 2 path (新規)。参照だけ: `orchestrator/tests/test_s8b_oracle_driver.py:1364-1455` (`_build_t080_stub_free_e2e_repo`、`add -A` は :1451)、`orchestrator/campaign/s8b_holdout_freeze.py:370-385` (`enumerate_repository_files`)、同 :608-676 (scan 本体、`search.file_count`)、`orchestrator/campaign/t080_freeze_migration.py:1735-1738` (`file_count` は受理集合外)。
- 実測環境: login node (Pegasus)、repo 外 tmp に fixture 相当の tree を組む。所要増分は同一 tree 内で現行/取り込みを交互に測る対比較 (D2068 の作法)。fixture 構築全体の A/B は行わない (外乱 28 倍、増分が ms 級なら分離不能)。
- (P1) 同型の穴は config.h の 1 件だけ。根拠 = 実 repo の `ls-files -ci --exclude-standard` 419 件のうち 418 件は root `.gitignore:25` 由来で fixture は root `.gitignore` を複製しないので一致側。親の provisional 裁定・攻撃対象。
- (P2) 取り込んでも判定は不変。根拠 = config.h に三軸語 0 件、known-axes glob は `output/campaigns/` 限定、`_live_scan_sha256` は `search` を含まず `file_count` は受理集合外と production 注記。攻撃対象 (他の束縛経路があるか)。
- (P3) 所要増分は ms 級 (add -f 1 file + 13 scan × 10 KB read/decode)。攻撃対象 (13 scan の実回数、regex prefilter の係数)。
- (P4) 採用する場合の最小差分は `add -A` 直後に実 repo の `git ls-files -z -ci --exclude-standard -- orchestrator output` 集合を `git add -f --pathspec-from-file` する 1 手 (一般解、件数非依存)。代替 = path hard-code の `add -f` 1 行。攻撃対象 (実 repo 読み直しは D2086 の session snapshot 化と整合するか)。
- DW-G05: 放置時の成果物影響 = certified 選択・レポート・台帳は変わらない (判定不変)。fixture の検出力が実 repo scan より 1 file 狭いだけ。must-fix ではなく裁定パッケージ (採用なら別 wave で Codex author)。
- 並列分割: 軽量版 + 段 2 plan 1 + 段 3 consult 2 (fixture の可視集合 = 防壁 e2e の検査対象集合に触るため敵対検証子を省かない)。段 5・6 は「実装しない」裁定なら飛ばす。

