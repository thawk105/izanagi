# 段 1 brief — 論文結果節の図 2 枚 (fig14: A-1 sized attempt-0002 記述図 / fig15: mocc witlight 4 arm 図)

wave: `dev-wave-paper-results-figures`、worktree `/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-paper-results-figures`、
base = local main `36fb14a3d131d516dc57b02ec69f56c711927c2e` (着手時 clean、開始 gate rc=0)。台帳 ID 未起票。軽量版 + 段 2・3・6 の子を残す
(受理集合が変わる: A-1 生成器の `variance_plan_breach` 拒否を attempt 別にする、D1752 の pin 表に entry を足す)。

- **(段 4 で改訂: P7 は 1 axes の forest + 曝露の数値列、P9 = 登録しない、P10 新設、完了表現の訂正。正本は `s4-ruling.md`)**
- **研究前進:** 論文の結果節で使える図素材 2 枚 (再現・caption・provenance・README 節付き) が揃う (results 稿・版への組み込みはしない)。(1) A-1 sized attempt-0002 の単独記述図 (fig9 と同形、稿 §2.6 / L-A1S2-11 の「図は無い」を埋める)、
  (2) stock mocc の軽量 witness 4 arm (W1〜W4) の G2 signal 検出率・CP 区間・曝露量の図 (results に mocc の図は無い)。
  完了判定 = 両図が実データで login 実走 rc=0・png/pdf/provenance の 3 成果物、README 2 本に節、生成器 test 緑、fig9 の着地 bytes と
  着地閉包 test (`test_landed_fig9_repo_closure_and_caption_when_present`) が不変で緑。
- **確定済み裁定:** D2194 項 6 (2)「attempt-0002 の図は作らない。必要になれば単独図 (fig9 と同形、`caption_source` = 本稿) を先に作る」、
  D1993 項 6 (プールしない)、D1752 (pin は repo 所有・CLI は成果物を選ぶだけ・新 attempt は entry を足す commit)、D1753 (図番号は prefix から)、
  D1546 (fixture は実寸)、D1637 (2 本目の論文と共用しない)、D95 (実装面は Codex author)、F36 (稿は図の hash を持たない)。
  07:2x JST のユーザー再裁定「fig9b (2 attempt 並記図) は作らない」(job dir `dev-wave-fig9b-a1-attempt2/RESOLVED.md`)。
- **(P1) 親の provisional 裁定・攻撃対象:** 依頼 (1) は D2194 項 6 (2) の「必要になれば単独図」経路であり、並記図ではないので 07:2x の再裁定と矛盾しない。
- **(P2):** A-1 生成器の attempt 選択は CLI `--attempt {attempt-0001,attempt-0002}` (argparse choices、既定 attempt-0001)。既定を残すのは fig9 節の
  再現コマンドを変えないため。表に無い値は argparse が拒否 (D1752「既定値へ落とさない」は未知 path の話)。pin・leaf path・caption_source は
  attempt ごとの repo 所有 exact 表から引き、CLI から渡せない。
- **(P3):** 図番号 fig14 / fig15 (tracked 全体で未使用を実測)。`fig9b_` は 07:2x に作らないと決めた並記図の仮名で、`b` 接尾辞は本 repo で「後継図」を
  意味する (fig2b / fig3b / fig8b) ので使わない。A-1 生成器の prefix 正規表現 `fig([0-9]+)_` は変えない。
- **(P4):** attempt-0002 の `variance_plan_breach` (write-heavy / read-heavy が true) は、述語 `stat["variance_plan_breach"] is (sd > sigma)` の
  一致で受理し、panel と caption に workload ごとに出す (sd と planned sigma を併記、比は作らない = 稿の比 1.207 等は「本稿の派生値」)。
  attempt-0001 の既存拒否 (`variance_plan_breach true` → 拒否) は維持。
- **(P5):** mocc 生成器の入力は repo 外 `/work/1/SFC/tanab/dev-wave-jobs/dev-wave-mocc-witlight-arm-run/arm-W/` (fig13 の `--evidence-root` 先例、
  既定値 = この絶対 path) の W1〜W4 `result.json` と `summary.json` の 5 file を生成器の SHA-256 定数で束縛。smoke と `parent-accounting.json` は
  入力にしない。`summary.json.inputs` が W1〜W4 の 4 件 (path・sha256) と exact に一致することを要求し、smoke を第 5 block として数えない。
- **(P6):** mocc の値は稿 `docs/paper-story/results/2026-09-20-mocc-witlight-four-arm.md` §2 の逐語を使う = 生成器は W1〜W4 の `runs[]` から
  k / m / CP / Fisher p / commit 数平均を再計算し `summary.json` と fail-closed で照合し、稿 §2.2 / §2.3 / §2.6 と同じ書式の文字列で描く。
  稿の表セルとの逐語一致は test が照合する (fig9 の `test_real_leaf_loads_and_matches_results_document` と同型)。生成器は稿の数値を読まない。
  実測: `summary.json` は arm 別の N / m / k / failure / indeterminate / decisive_m / cp95 / discriminator_counts / identification と `inputs` (W1〜W4 の
  絶対 path と sha256) を持つが、**Fisher p と commit 数平均は持たない** (それらは入力外の `parent-accounting.json` にある)。よって Fisher p (0.500) と
  commit 数平均は生成器が `runs[]` から計算し、照合先は稿だけ (test)。設計仮定下の検出力 0.105 は稿 §1.3 の計算値で、caption の固定文として
  「計算値であり実測ではない」と併記する (生成器は計算しない)。
- **(P7):** mocc 図の形 = 2 panel: (a) arm 別の G2 signal 検出率 k/m と Clopper–Pearson 両側 95% (BACK_OFF=0 / 1 × witness on / off の 4 arm)、
  (b) arm 別の走あたり commit 数 (TRACE=1 の曝露量、性能ではない)。block 別 (W1〜W4) は caption の件数記述に留め panel にしない。
- **(P8):** mocc の着地閉包は fig13 と同じ 2 層 (repo 内: 着地 png/pdf の SHA-256・caption_source の SHA-256・README 収録 / repo 外: 5 file の SHA-256 と
  再導出 = 証拠 root が在るときだけ、無ければその 1 test だけ skip)。repo 内 verbatim 写し (`output/insights/2026-09-19/mocc-witlight-arm-run/verbatim/`、
  同一 SHA-256 を実測) への fallback は作らない (一般化)。
- **(P9):** 新規 test node の受入所要時間台帳 (`orchestrator/tests/acceptance_duration_ledger.json`) への登録は、被覆 gate の余裕を実測してから段 4 で決める
  (既定 = 登録しない、fig13 先例。足りなければ Codex author が `--add-only`)。詳細は `s1-pin-closure.md`。
- **不変条件:** fig9 png/pdf/provenance の bytes、fig9 着地 test の通過、attempt-0001 の data key 集合・値・caption 文字列・provenance 形 (現行生成器で
  作り直した caption/cells と着地 provenance の完全一致を test が要求する)。results 稿 3 本 (attempt1 / attempt2 / witlight) と版 (`docs/paper-story/2026-*.md`) の
  bytes。規律 1 (TRACE=1 の commit 数を性能として描かない)・規律 2 (verifier / discriminator 不変)。
- **過去の型 (攻撃面):** F872 (開示義務の文言が PNG/PDF に描かれず、内部値だけ見る test が緑) → fig14 の `variance_plan_breach` 表示と fig15 の
  「TRACE=1 exposure, not performance」等の軸・注記は `fig.findobj(Text)` の実 artist で検査する。F623 (描画と provenance が別経路) → provenance の
  artist 系列は描画関数が実際に渡した値から作る (既存 `fig._a1_artist_series` 型)。F812 (fixture が実寸未満) → 実寸 fixture。F653 (要素が消えても
  重なり検査は緑) → 描いた要素の存在も検査する。
- **描かないもの:** 2 attempt のプール・差・比・区間の重なり・再現判定・attempt-0001 の値 (fig14 は attempt-0002 だけ)。breach の原因帰属。
  mocc の非有意を同等性・「効果なし」・「on では出ない」として、TRACE=1 曝露量を性能として、G2 signal を根因の同定・実 anomaly の確認として描かない。
- **scope 外:** 仮想リスク向けの gate・検査・台帳・一般化 (汎用 attempt loader、verbatim fallback、図の汎用基盤)。results 稿・版の改訂。
- **成果物:** (実装面、Codex author) `tools/plotting/plot_a1_sized_paired.py` + `orchestrator/tests/test_plot_a1_sized_paired.py` の拡張 /
  新規 `tools/plotting/plot_mocc_witlight_four_arm.py` + `orchestrator/tests/test_plot_mocc_witlight_four_arm.py`。
  (親) login 実走で `docs/paper-story/figures/fig14_a1_balanced5_sized_attempt2.{png,pdf,provenance.json}` と
  `fig15_mocc_witlight_four_arm.{png,pdf,provenance.json}`、`docs/paper-story/figures/README.md` (一覧 2 行 + 節 2 つ)、
  `tools/plotting/README.md` (節 2 つ)、`docs/phase3.md` [x]、insight、spool fragment。
- **分割方針:** 段 5 は所有を分けた実装子 2 本を並列 (A = A-1 の 2 file、B = mocc の新規 2 file)。README・作図・記録は親。
- **受入・実測環境:** 作図・生成器の実走は Pegasus login (計測機の外、FIGURE_CONVENTIONS §7)。焦点走・受入は既定経路 (`tools/run_tests.py` /
  `tools/dev_wave_wait.py acceptance`)。
- **成果物影響 (DW-G05):** 放置すると論文の結果節に attempt-0002 と mocc の図が無く (稿 §2.6 / L-A1S2-11)、読者は表だけで読む。certified 選択・台帳の値は変わらない。
