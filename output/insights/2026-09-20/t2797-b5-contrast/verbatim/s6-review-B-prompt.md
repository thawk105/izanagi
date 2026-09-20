単独段 dispatch: stage=review; sandbox=read-only; parent=/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2797-b5-contrast

必読事項の射影 (各 path を読めなければ即停止して、その旨だけを `## 総括` に書いて終わること):
- 親の段 4 裁定 (実装仕様・変異事前登録・削除候補): /work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2797-b5-contrast/s4-adjudication.md
- author 3 本の報告 (検査対象): /work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2797-b5-contrast/codex/s5-author-A1.md, s5-author-A2.md, s5-author-A3.md
- 段 3 相談 B (過剰・削除レンズの起点、B4 / B5 / B9 / B12 / B13): /work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2797-b5-contrast/codex/s3-consult-B.md
- 親 brief と追補: /work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2797-b5-contrast/brief.md, brief-addendum-1.md
- 依頼文の逐語 (scope の正本): /work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2797-b5-contrast/verbatim/T-2797-origin.md
- 実装 (worktree の path、read-only、HEAD = 統合 commit 2 `e574815582e0516fa9e3a0ed8d351525c162fdc2`): /work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2797-b5-contrast/ 配下の
  `tools/pegasus/p3_s4_loop_pegasus.sh` (差分は /work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2797-b5-contrast/codex/a3.patch)、`tools/pegasus/b5_contrast_launch.py` (262 行、新設)、
  `orchestrator/tests/test_p3_s4_loop_job_contract.py` (差分は a3.patch)、`orchestrator/tests/test_b5_contrast_launch.py`、`orchestrator/campaign/b5_generator_contrast.py` (864 行、
  `slot_argv` :470–493、`default_runner` :499–502、`run_series` :673–790、`run_block_stock` :792–807、`main` :809–)、`orchestrator/campaign/b5_generator_contrast_report.py`、
  `orchestrator/tests/test_b5_generator_contrast.py`、`orchestrator/tests/test_b5_generator_contrast_report.py`、`orchestrator/campaign/p3_s4_loop.py` の差分 (a1.patch、同 dir)、
  `tools/pegasus/README.md:331–430`、`tools/pegasus/admission_registry.json`、`orchestrator/tests/test_hooks.py` (登録簿の固定表 :3214–3226 / :3562–3600 / :4115–4130、
  inventory 同期 test :4538)、`orchestrator/tests/test_official_perf_closure.py:44–75, :495–535`、`orchestrator/tests/test_p3_exploration_namespace.py:416–429`、
  `orchestrator/tests/test_p3_b4_wiring_probe.py:320–330`、`orchestrator/tests/test_campaign.py:5410–5430`、`orchestrator/tests/test_campaign_import_invariant.py:870–940`、
  `orchestrator/tests/test_p3_build_authority_cli.py:60–140, :680–710`、`orchestrator/tests/test_pegasus_tools.py:530–570`、`orchestrator/tests/test_plain_runner_coverage.py`。

## 前置き — この依頼の性質

対象は研究用 repo の CC 合成 campaign の実験基盤 (B-5 生成器対照の残部品と試走 launcher) である。セキュリティでも攻撃でもない。あなたは段 6 の敵対レビュー
(レンズ B = 段 3 の過剰・削除レンズを固定) であり、**実装者の報告を信じず現物で検査する**。親の裁定・brief も検査対象である。

# 依頼 — レンズ B: 過剰・削除・pin 閉包・job 契約・launcher の実効性・test の実効

各所見は **real / refuted / 根拠不足** に分け、real には must-fix / should / nit の格と、放置時に成果物 (試走の成立・台帳・既定経路の挙動・受入の赤・受理集合) がどう変わるかを
1 行で添えよ。**親が実行した分担:** 新 test 3 file (85 / 54 / 36) と TJ (184) を login で実走して緑。`test_hooks.py::test_bash_pegasus_execution_inventory_is_synchronized` は
launcher 未登録で赤 (fix1 が並行して登録中: `admission_registry.json` に `local-ok`、test_hooks の固定表 3 つ)。実機 qsub / build / bench / handshake は未実走。

## 攻撃対象 (最低限)

1. **job body (a3.patch):** 既存 3 経路の argv・rc が bytes 不変か (現物で `candidate_rc=0` 以降を照合)。B-5 mode の拒否 (未設定だけ off、空値・不正値・部分設定・旧 mode 併用・
   K2 の条件) が repository path 解決・`trap` より前か。B-5 分岐が prebuild の後・旧分岐の前に 1 箇所か、`exit "$b5_rc"` が EXIT trap の compute-result.json と両立するか。
   `IZANAGI_S4_B5_LEDGER_ROOT` の repository 内拒否 (`realpath -m`)。`:95–96` の proposal-path 必須条件の例外が B-5 llm だけか。TJ の pin (B5 pins、stage order、変異 fragment、
   実 shell test) が B-5 経路を実際に検査しているか (static 文字列だけで済ませていないか)。`test_pegasus_tools.py:530–570` の SH 逐語 pin と `README.md` の fence 数 test に掛かるか。
2. **launcher (`b5_contrast_launch.py`):** `validate_submit_tree` の検査 (HEAD full OID・tracked clean (submodule 除外)・CCBench HEAD == `p3_s4_loop.PIN`・CCBench clean・
   `.claude/worktrees/` / `.codex/worktrees/` 配下拒否) が job body の同じ検査と食い違わないか。`qsub_argv` の `-v` 列挙 (10 + llm 4)・`-l elapstim_req` (08:00:00 / 03:00:00)・`-o` / `-e`・
   `-q` / `-A` / `-b` を script 指示行に任せる点 (既存 K2 投入 `/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2795-k2-pair/qsub-submit-pair.sh` と同型か)。`,` や空白を含む path の拒否。
   `--dry-run` が subprocess / mkdir を呼ばないこと、`--submit` が attempt dir に mkdir 以外を置かないこと (job body は `allocation-qstat.*` 等の fresh を要求)。
   cap 検査 (`3*(1+10+5)+5 = 53 ≤ 60`) が定数だけでなく実 schedule に効いているか。**guard_bash の分類:** 登録前に login で `python3 tools/pegasus/b5_contrast_launch.py --dry-run` を
   打つと拒否されるか (登録後の class `local-ok` で通るか)。
3. **module の CLI と subprocess (`b5_generator_contrast.py`):** `slot_argv` の逐語 (裁定 §2.2 の argv と一致するか、K2 4 引数、`--machine-generated-proposal`、stock の argv)、
   `default_runner` (`sys.executable -B -m orchestrator.campaign.p3_s4_loop`、cwd = repo_root、env、timeout の有無 — timeout があるなら値と分類)、`main` の subcommand
   (`run-series` / `run-block-stock` / `weights-material` / `expected-inputs`) と job body の `b5_argv` の一致。`_header` の git 読取り (subprocess を増やしていないか)。
   `PYTHONDONTWRITEBYTECODE` / `-B`。計算ノードは外部ネットワーク不在 — module が network を要する処理を持たないか。
4. **pin 閉包 (D2186 項 5 の inventory 4 群 + consult B9):** `test_official_perf_closure.py` の述語に新 3 module が掛からないこと (author は掛からないと報告 — 現物の `if` 条件で検算)、
   `test_p3_exploration_namespace.py` の p3_s4_loop pin (layout 11 / run_campaign 2 / runtime 1)、`test_p3_b4_wiring_probe.py` の import 閉包 49、`test_campaign.py` の caller inventory、
   `test_campaign_import_invariant.py` の campaign CLI 形 (新 2 module の `__main__` / 相対 import)、`test_p3_build_authority_cli.py` の issuer 閉包 (新 module が authority 名を import /
   呼出ししていないか)、`test_plain_runner_coverage.py` (新 test 3 file の `__main__` harness)、`test_hooks.py` の module 分類 (新 3 module / 新 launcher)。author が「通過」と書いた test の
   nodeid が実在するか。
5. **過剰実装と削除 (裁定 §1 の削除候補):** hash8 事前網羅・純 verifier adapter・新 entrypoint・alias 群・汎用 retry / 再配置・108 系列 launcher・発効 gate が入っていないこと。逆に
   依頼にあるのに欠けるもの (較正・verify の job body 配線 = module 内固定で満たすか、解析 consumer、verifier wall の実測記録 = `wal_timing` と台帳 `timing`)。module 864 行 /
   report 511 行 / launcher 262 行のうち、試走 (β) に不要で本走にも要らない部分を列挙せよ (削除提案は「意味を保って削れる」ものだけ)。
6. **test の実効 (DW-M01 / F42 / F27 / F649):** 新 test 4 file (85 / 54 / 36 / TJ 追加分) に、恒真 (実装の定数を実装から読んで比較)・依存先 stub で機構を通らない緑・揮発 payload
   の焼き込み・期待値の緩和が無いか。fake runner が `classify_slot` の実 WAL 読取りを通しているか (合成 WAL の形が実 pipeline の record と一致するか)。`__main__` harness と
   subprocess の `-B` / `PYTHONDONTWRITEBYTECODE=1`。変異 M13 / M14 / M16 / M17 / M18 の kill が単位内 test か。
7. **README / docs の差分案 (親が書く):** author の差分案が `tools/pegasus/README.md` §7 の既存文 (「較正・verify の opt-in は本 job body には配線していない — B-5 試走 (β) の launcher
   設計で足す」) と矛盾しないよう、書き換えるべき文と追記すべき env 表・qsub 例・launcher 使用例を列挙せよ (docs は書かない、案だけ)。
8. **親の派生値:** launcher の walltime 08:00:00 / 03:00:00 が「暫定管理値」であること、53 の内訳、`SESSION_BUDGET_S = 1800` (残り 30 分未満で新規 session を始めない) の根拠が
   brief の見積り (1 session ≈ 12〜14 分、外挿) とどう対応するか。

## 出力形式

- 見出しは `#` 1 段だけ (`##` は `## 総括` のみ)。所見ごとに: 対象 (file:line)、判定、格、成果物影響 1 行、根拠、代案。
- 実行できない検査は「未実走・静的読解」と明記。sandbox は read-only で pytest 緑は要求しない。予算が尽きそうなら途中結論を出力形式どおり書いて終われ。出力は最終メッセージ本文に全文。
- 末尾に `## 総括`: must-fix の一覧 (番号・1 行・file:line)、should の一覧、削除候補の一覧、GO / NO-GO、親裁定が要る未確定事項。
