単独段 dispatch: stage=author; sandbox=workspace-write; parent=/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2301-a1-study-id-required

必読事項の射影:
- /work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2301-a1-study-id-required/prompts/ruling-stage4.md — 段 4 裁定と変異の事前登録。読めなければ即停止。
- /work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2301-a1-study-id-required/prompts/D1619.md — ユーザー裁定 D1619 の逐語。読めなければ即停止。
- /work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2301-a1-study-id-required/docs/ai-provenance.md — provenance 規約 (読むだけ、commit はしない)。読めなければ即停止。

## 目的
D1619 に従い、A-1 対測定の driver の `submit --study-id` から既定値を無くして明示必須にし、job body と契約テストを同じ形へ直す。
これは izanagi 自身の投入器の受理集合を「既定 study を黙って選ばない」方向へ縮める変更である。作業 root は
/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2301-a1-study-id-required (以下 ROOT)。

## 現行の受理・拒否挙動 (着手前、親の実測)
- ROOT/orchestrator/campaign/paper_story_a1_paired.py 8588 行: `submit.add_argument("--study-id", default=STUDY_ID)`。3221 行 `run_submit`: `study_id = getattr(args, "study_id", STUDY_ID)`。
  したがって `submit` は `--study-id` 無しで legacy study (paper-story-a1-20260826-sized-v1) を選ぶ。
- ROOT/tools/pegasus/paper_story_a1_paired.sh 38 行: `EXPECTED_STUDY_ID="paper-story-a1-20260826-sized-v1"` の既定代入。41〜56 行の case は
  `IZANAGI_A1_STUDY_ID` 未設定を `refuse "study ID differs"` で既に拒否する (fail-closed は既存)。v2 枝だけ EXPECTED_STUDY_ID を再代入していない。
- ROOT/orchestrator/tests/test_paper_story_a1_job_contract.py 1209 行付近と 1291 行付近が上の literal を count で pin している。

## 編集対象 (所有 path、これ以外は編集禁止)
1. ROOT/orchestrator/campaign/paper_story_a1_paired.py
   - 8588 行を `submit.add_argument("--study-id", required=True)` にする。
   - 3221 行を `study_id = args.study_id` にする。
   - 行数を変えない (1:1 置換)。ROOT/orchestrator/tests/test_ccbench_spawn_sites.py が本 file の 7103 行目 (`run_measurement` 内 campaign sink) を exact に pin しており、行がずれると別 test が赤になる。
   - `complete --study-id` (8610 行) と `run_complete` (4225 行)、`load_policy` の既定は触らない (D1619 の文言外、親が所見として報告する)。
2. ROOT/tools/pegasus/paper_story_a1_paired.sh
   - 38 行の既定代入を削除し、case の v2 枝 (`paper-story-a1-20260826-sized-v1)`) に `EXPECTED_STUDY_ID="$REQUESTED_STUDY_ID"` を足す (v3 枝と同じ形)。
   - 他の gate・refuse・順序は変えない。`bash -n` で構文を確かめる。
3. ROOT/orchestrator/tests/test_paper_story_a1_job_contract.py
   - source pin を新形へ直す: 既定代入 literal が 0 件であること (`not in source`) と、legacy ID の出現数 (現 2 → 新 1) など、実際の新 bytes を数えて固定する。
   - `_shell_fixture` / `_run_shell_job` を使い、`IZANAGI_A1_STUDY_ID` を環境から除いた走行が rc=2 かつ stderr に `study ID differs` を含む負例を 1 本足す (既存挙動の正例化。attempt root が作られないことも assert)。
4. ROOT/orchestrator/tests/test_paper_story_a1_paired.py
   - 負例: `paired._parser().parse_args(["submit", "--expected-head", "a"*40, "--attempt-root", "/x"])` が `SystemExit` (code 2) を投げる。
   - 正例 (過剰拒否の防止): `--study-id` に `paired.STUDY_ID` / `paired.V3_PILOT_STUDY_ID` / `paired.V3_SIZED_STUDY_ID` を明示した submit の parse が通り `parsed.study_id` が一致する。
   - fail-closed: `study_id` 属性を持たない `SimpleNamespace(expected_head="a"*40, attempt_root="/x")` で `paired.run_submit` を呼ぶと `AttributeError` になる (既定へ退避しない)。policy を読む前に落ちることを確かめる。
   - 各 test の docstring に受理と拒否の含意を 2 文で書く。

## 禁止事項 (必ず守る)
- version control の書込み操作 (add / commit / merge / stash / checkout / reset) を一度も実行しない。commit は親が行う。
- docs を編集しない (docs/、output/insights/、docs/handoff/ への file 作成を含む)。
- ROOT/orchestrator/campaign/paper_story_a1_paired.v2.json / .v3-pilot.json / .v3-sized.json を 1 byte も触らない。
- 既存 tracked テストの期待値を反転・緩和・skip・削除しない。上記 3 の pin 更新は新 bytes への追随であり、それ以外の期待値は変えない。
- fixture へ現行 hash を差し込むなど、テストを甘くして緑にしない。機構の正例・負例は実体 (`_parser` / `run_submit` / job body) を名指しし、依存先を stub しない。
- 期待値へ揮発 payload (working tree hash 等) を焼き込まない。
- 指示外の受理集合変更をしない。新しい gate・台帳・helper module を足さない。
- 出力に結合文字 U+0300〜U+036F を使わない。

## 検査
- login node の sandbox からは pytest を dispatch できない (rc=16 になる)。走らせていない結果を書かない。
- 実走できない場合は、最低限 test module を import して足した test 関数を直接呼び (`tmp_path` は `tempfile.mkdtemp()` で代用)、fixture が成立するか確かめる。さらに実装側の変更を一時的に元へ戻して、期待どおり赤化する (DID NOT RAISE 等) ことまで確かめ、必ず元に戻す。
- `bash -n ROOT/tools/pegasus/paper_story_a1_paired.sh` を実行する。
- `python3 -c "import ast,sys; ast.parse(open(sys.argv[1]).read())" <file>` で 3 つの Python file の構文を確かめる。
- 制約 meta-test (source を count で pin する test、driver の行番号 pin、job body の文字列 pin) を自分で洗い出し、親の名指しを網羅と見なさない。`rg -n "paper-story-a1-20260826-sized-v1|EXPECTED_STUDY_ID|default=STUDY_ID|getattr\(args, \"study_id\"" ROOT/orchestrator ROOT/tools` の結果を波及節へ載せる。

## 出力形式 (最後の節は必ず `## 総括`、`#` を 2 個。`### 総括` と書いてはならない)
## 変更点
file ごとに何行目をどう変えたか。行数が変わっていないことの確認結果。
## 足した test
nodeid の完全な一覧 (file::function[param])。各 test が殺す変異 (M1 / M2 / M3 / 正例) を対応づける。
## 実走
実走した検査とその結果。実走できなかったものは「実装済み・未実走」と書く。
## 波及
所有外の caller・共有 fixture・consumer test への波及可能性を静的に列挙する (rg 結果つき)。
## 総括
受理と拒否の含意を 2 文、残課題、親が確かめるべき点。
