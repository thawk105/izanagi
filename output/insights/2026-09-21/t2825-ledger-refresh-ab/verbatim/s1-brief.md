# [T-2825] 段 1 brief (親、2026-09-21 08:40 JST、基準 local main `21641fee777d24642d54119b660a7b7880636e71`)

**研究前進:** 受入 wall (全体 5 分上限の律速 = shard-0) に対し、T-2817 が律速と同定した「ledger 未収載 → 後方 rank → 別 worker の直列」への
最安の策 (D2107 の refresh の運用) の実効果を、同一条件の隣接対で実測して確定する (D1936 項 35「効果を先に測る」)。完了判定 = 有効 3 対の
対表・判定が insight に載り、新 ledger が local main に入る。実効果の上下限は置かない。

**scope:** (1) `tools/update_acceptance_duration_ledger.py --refresh` で `orchestrator/tests/acceptance_duration_ledger.json` を
最新緑走 1 走の 3 shard JUnit から再生成 (Codex author が実行、親は検算だけ)。(2) 固定 2 tree の隣接対で実受入を直接投入して測る。
(3) 記録と land。**scope 外:** gate・台帳・一般化の追加、conftest / `tools/acceptance_shards.py` / 生成器の変更、modify 複合区間 (T-2826)、
post 10 秒 (T-2827)。

**確定済み裁定:** D2107 (refresh 契約: 凍結 8 suite 据え置き、非凍結は 1 走 JUnit から全再生成、入力は「最新で collection が main と一致する緑走」、
land で main 台帳が進んでいたら main 現物を base に同じ JUnit で再走し落ちた node を insight に記録)、D357 (3 走以上・中央値・1 走差 10 % 未満は
変化なし・測定中に自分の他 job を走らせない)、D1936 項 35、D2177 (code が変わる比較は固定 2 tree の隣接対、D2068 の同一 tree 条件は満たさない)、
T-2766 事前登録の形、依頼の門番 (他 session の受入 leader ≤ 1 ∧ load1 ≤ 60)。

**前提の実測 (brief 前、login、read-only):**
- 入力走 = session `9d955ce29586a8e16c500cc56faa7a22` (08:14〜08:20 JST、dev-wave-dwm08-selfrun-probe の受入、tested_main `5efd69367`)。
  3 shard 緑 (tests 4149 / 10309 / 12350 = 26,808、failures 0、errors 0、skipped 53 / 7 / 9)。`git diff 5efd69367 21641fee7 -- orchestrator tools hooks external .claude`
  は空 (間は docs / fold のみ) → collection は現 main と一致する見込み (段 5 で main の collect-only と `--coverage-against` で検算)。
- 試走 (job dir の複製へ `--refresh --output`、repo 不変): preserved_frozen 426 / replaced 23813 / added 2366 / removed 140 / excluded_frozen_suite 629、
  entry 24379 → 26605、凍結 426 entry は値一致、`…explicit_binding@real-repo` 0.19 は残る。T-2724 の 8 node は全部 added
  (active_v2_delegation 190.0 / active_v2_preserves 190.0 / delegated[changed] 190.0 / delegated[missing] 39.0 / rejects_late_hit 44.0 /
  failed_launch 48.0 / v1_gate 41.0 / shared_base 0.004)。added の 2366 は全 shard の node 数で、T-2817 の「shard-0 の未収載 334 unit」とは単位が違う。
- 台帳の consumer は 2 つ: conftest `_reorder_acceptance_items_by_duration` (shard 内の順序) と `tools/acceptance_shards.py::allocate`
  (shard への割付重み)。**refresh は shard-0 の構成 (どの node が shard-0 に入るか) も変えうる。**
- 実台帳を読む test: `test_acceptance_schedule_order.py` (被覆 ≥ 0.90、`@real-repo` 0.19)、`test_update_acceptance_duration_ledger.py`
  (schema、T-1574 の凍結差分 exact)、`test_paper_story_a1_headline.py` (固定区間の非接触、今回の変更は区間外)。現 sha256 `1edbb792…` の出現は
  T-2766 の歴史記録 2 件だけで pin なし (規律 7 で記録は残す)。

**不変条件:** 凍結 426 entry は byte 一致。受理集合 (selected / hold / group / unit 境界) は不変 (ledger は順序と割付の重みだけ)。
値の合成・手編集なし。測定は 2 tree とも clean・HEAD 固定、投入前後に照合。記録 commit は測定後。参考値 (model 差 19.5 秒、観測 `O_max − L`
中央値 62.7 秒 / Job B 65.0 秒) は別欄に持ち、閾値・上下限・期待値に使わない。

**割れうる前提 (親の provisional 裁定・攻撃対象):**
- (P1) 測定形は D2177 型の固定 2 tree: A = `21641fee7` の clean worktree (新設、`.codex/worktrees/t2825-base-a`)、B = wave worktree
  (`21641fee7` + ledger commit 1 本、docs なし)。T-2766 の同一 SHA + env 切替は bytes 変更に使えない。
- (P2) 主指標 = shard-0 の W (依頼の指定)。W_max と argmax shard は補助で併記し、shard-0 が最遅でなくなった走は明記する。判定は T-2766 形
  (有効 3 対、全対 ΔW > 0 かつ med r ≥ 10 % → (i)、全対 > 0 で < 10 % → (ii)、他 → (iii))、10 % は保守基準で有意差ではない。
- (P3) 「L 自身が伸びる」は各対の ΔL = L_B − L_A と、T-2724 8 node の (worker、rank、開始 t、所要) で観測する。copy 配置の内訳は実受入に
  計器が無いので測らない (帰属は計器の分解能まで)。
- (P4) 投入は `IZANAGI_ACCEPTANCE_SHARDS=3 python3 tools/run_tests.py` の直接投入 (待ち手・lease・merge なし、D2177)。land 用の最終受入だけ
  `tools/dev_wave_wait.py acceptance`。
- (P5) 軽量版: 段 2 省略 (本 brief に plan を含める)、段 3 read-only 相談 1 本 (2 レンズ)、段 5 author 2 単位 (ledger 生成 / 測定 probe)、段 6 review 1 本。
  変異 matrix は code・test の防壁を変えないので適用外 (段 4 で理由を書く)。

**成果物:** 新 ledger (commit 1)、job dir の probe (launcher / series / warm / 集計器、Codex author、repo へは `.md` 逐語だけ)、
insight `output/insights/2026-09-21/t2825-ledger-refresh-ab/` (走表・対表・判定・item 列・参考値欄・落ちた node)、spool fragment (worklog、必要なら decisions)。

**分割:** author-L (ledger 生成 + 検算出力、wave worktree) と author-P (probe、別 unit worktree → 親が job dir へ退避) は所有 file が重ならないので並列。

**条件表の評価 (brief 前、DW-O08/O09/O10/O13):** 08 成立 (台帳は T-1574 の凍結 8 suite pin を含む) — 初期化 tool rc=0 と木の中身を確認済み。
09 成立 — pin 閉包: path 検索で consumer 2 (conftest / `tools/acceptance_shards.py`)・test 3 本・生成器、現 sha256 `1edbb792…` の出現は歴史記録 2 件
(T-2766 の 2 README) のみ、凍結 426 entry は試走で値一致。10 成立 — producer (`update_acceptance_duration_ledger.py`) が書く file は
`--output` の 1 file だけ (stdout は件数)。13 不成立 — gate・検証の新設なし (測定用 probe は repo 外で判定器ではない)。
