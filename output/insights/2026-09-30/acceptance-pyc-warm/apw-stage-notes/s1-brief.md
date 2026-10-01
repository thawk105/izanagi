# 段 1 brief — acceptance-pyc-warm (md_7)

- 研究前進: 土台。dev-wave (2026-09-29 裁定で研究の主経路) の全 wave が払う受入全走の shard wall を、初回受入で約 40 秒/shard 縮める。完了判定 = 事前登録した同時刻対照で H の pre が温の峰に入り、受理集合 (observed_universe・login universe・merge 判定) が K と一致。
- scope: `tools/run_tests.py` の shard mode (IZANAGI_ACCEPTANCE_SHARDS≥2、空 argv、Pegasus LOGIN) だけ。login collection (`_collect_login_universe` と同じ command・env・exclusions・timeout 規律) を、preflight (未 stage 削除検査 `git ls-files --deleted`・RuleOps・submodule・queue hint) と dispatch 準備の前に subprocess として起動し、`acceptance_shards.run_parallel` に渡す `collect_login` は「その process の回収 + log 書込 + parse」にする。`tools/acceptance_shards.py` は変えない (run_parallel の start→collect_login→wait 順序 test を保つ)。test は `orchestrator/tests/test_run_tests_shards.py` (必要なら `test_run_tests_preflight.py`)。
- 設計択一 (md_7 項 1) の provisional 裁定 (P1): (c) 前倒し起動を採る。実測根拠 (job dir `probe/`、md_2 の対照生記録):
  - 起動→投入意図は 4 走とも 101〜102 秒 (md_2 の区間分解は投入意図起点で、この区間を測っていない)。うち `git ls-files --deleted` が 34.2 / 88.7 秒、RuleOps 2.6 / 8.1 秒、queue 1.1 秒 (本 worktree、login、2 回)。
  - 冷の login collection は投入意図から 85〜108 秒 (4 走)。計算ノード job は投入後約 9 秒で起動 (compute-visible.json)。
  - 素朴 (a) = shard が login collection の完了を待つ: 待ち約 70〜90 秒 > 得 (冷 137 → 温 65 の 72 秒、実際の H は既に 110) なので悪化見込み。却下候補。
  - (b) 計算ノード子に pyc を書かせる: D918 が F52 を理由に却下済み。48 worker が同時に冷で collection するので初回には効かない。
  - (c) の見込み: collection が約 100 秒の git 区間と重なり、shard 開始時に pyc が揃う → H pre 110 → 65 前後。待ちは増えない。
- (P2) 検査順序の変更で結果は変わらない: collection は tree + env の純関数、preflight は tree を書かない (RuleOps check が何も書かないことは未確認、攻撃対象)。preflight が赤なら collection は kill + reap して従来と同じ rc で返る。
- (P3) pyc の量は現行と同じ: 同じ collection が同じ env で書く pyc 集合で、書く時刻が早まるだけ。撤去 tool の証拠量は増えない (md_2 雛形変更後の常態)。呼出し側が PYTHONDONTWRITEBYTECODE=1 を立てる場合は効果 0 (現行どおり、変えない)。
- 確定済み裁定: D918 (子の bytecode 書き込み禁止を緩めない・外部 cache 新設しない)、D1473 (login collection は臨界経路外)、D2046 (pre は短縮しない = 集合縮小・絞り込み禁止。本件は集合不変)、D711 gate 3 (独立 login collection と shard universe の一致) は不変、D987 (run_tests.py blob 変更 → 走行中 wave の再受入、land 順は調整役)。
- 不変条件: 受理集合・判定・rc 体系・deadline 5100 秒・login collection の command/env/exclusions・log 名 `login-collection.log` (create-only)・非 shard 経路の挙動は byte 不変。孤児 process を残さない (preflight 赤・例外・signal)。
- 成果物: run_tests.py + test (Codex author)、一次資料 `output/insights/2026-09-30/acceptance-pyc-warm/README.md`、spool fragment (worklog / decisions)。
- 対照 (段 4 で事前登録): 同 commit 系の fresh 木 2 本ずつ、K = base (d79fd3524 系 main)、H = wave tip、`IZANAGI_ACCEPTANCE_SHARDS=3 python3 tools/run_tests.py` を同時起動 × 2 対。指標 = 起動→統合 junit (outer)、shard 別 pre、W_max、login collection 完了と shard 起動の順序。計算見込み 2 対 ≈ 1.2 node 時間 + 受入 1〜2 走 ≈ 0.4〜0.7 → 2 node 時間未満。
- 実測環境: Pegasus login (collection・preflight) + 計算ノード (shard)。runner は md_2 の `meas/run-pair.sh`・`make-trees.sh` (Codex author 製) を K/H 別 commit 用に Codex が改修。
- DW-G05: 放置時は受理集合・台帳の値は変わらず、初回受入の wall が約 40 秒/shard 長いまま (成果物の値は不変、所要だけ)。
- 分割: 段 2 plan 1 本、段 3 相談 2 本 (レンズ: 正しさ・受理集合と process 寿命 / 費用と効果の実在)、段 5 実装子 1 本 (run_tests.py + test) + 計測 runner 子 1 本、段 6 review 2 本。
- 条件 dispatch 判定: O08/O09/O10 非成立 (凍結・proof chain・凍結 bytes に触れない)。O11 非成立 (削除なし)。O13: 新 gate は作らない (既存 gate 3 の入力の起動時刻だけ変える) → 非成立として段 2 へ、plan で覆れば再評価。
