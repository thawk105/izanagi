単独段 dispatch: stage=author; sandbox=workspace-write; parent=/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2647-b10-tail-fig8

## 必読事項の射影

次の絶対パスを読む。**この射影に挙げた file が読めなければ即停止**する。これは射影 file 限定の停止規則であり、自分が推測して探した path が不在でも停止理由にしない。

- `/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2647-b10-tail-fig8/s4-adjudication.md` — **親の段 4 裁定 (確定指示)。§2 が生成器の実装仕様、§3 が test の仕様、§4 が変異 matrix の事前登録、§5 が受理集合。** brief と食い違うときは裁定が勝つ
- `/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2647-b10-tail-fig8/brief.md` — 親の段 1 brief (背景・実測済み事実)
- `/work/1/SFC/tanab/izanagi/.codex/worktrees/t2647-fig8-impl/tools/plotting/FIGURE_CONVENTIONS.md` — 作図規約 (§1・§2・§6・§8・§9・§10 と「新しい図種を足すとき」)
- `/work/1/SFC/tanab/izanagi/.codex/worktrees/t2647-fig8-impl/tools/plotting/plot_a2_certification.py` — 924 行。雛形 (読むだけ、編集しない): `_sha256` 85、`_figure_number` 604〜608、`_caption_prefix` 610〜617、`check_figure_layout` 757〜793、`build_provenance` 795〜828、`_publish_outputs` 830〜857、`validate_external_sources` / `validate_repo_closure` 859〜889、`main` 899〜921 (`expected_hashes` seam)
- `/work/1/SFC/tanab/izanagi/.codex/worktrees/t2647-fig8-impl/tools/plotting/plot_b10_extended_backoff.py` — 1196 行。雛形 (読むだけ、編集しない): 定数 31〜73、`_validate_text_bboxes` 784〜807、`make_figure` 809〜880、`build_provenance` 898〜955
- `/work/1/SFC/tanab/izanagi/.codex/worktrees/t2647-fig8-impl/orchestrator/tests/test_plot_b10_extended_backoff.py` — 424 行。test の雛形 (読むだけ、編集しない): `_load_module` 74〜82、実寸 fixture `_campaign` 84〜143、本物の Figure を検査へ通す 284〜314、`_run` 自走 harness 404〜末尾
- `/work/1/SFC/tanab/izanagi/.codex/worktrees/t2647-fig8-impl/orchestrator/tests/test_plot_a2_certification.py` — 1666 行。`_assert_named_landed_bundle` 1238〜1245 と `test_landed_fig7_repo_closure_and_caption_when_present` 1650〜1660 だけ読む (着地 test の型)
- `/work/1/SFC/tanab/izanagi/.codex/worktrees/t2647-fig8-impl/docs/paper-story/results/2026-09-16-b10-static-tail-not-observed.md` — results 稿。§1.2 (格子・動作点)、§2.1〜§2.3 (値)、§4.1 (3 file の SHA-256 表。test `test_pinned_input_hashes_match_results_document` はこの表を grep で読む) を読む
- `/work/1/SFC/tanab/b10-backoff-grid-t2500-formal/group-report-20260915/t2500-backoff-static-tail-formal.json` — 実データ (359 KB、読むだけ。**全文 cat しない**。`python3 -c` か `jq` で構造を見る)
- `/work/1/SFC/tanab/b10-backoff-grid-t2500-formal/group-report-20260915/t2500-backoff-static-tail-formal.dat` — 実データ (121 行、読むだけ)
- `/work/1/SFC/tanab/b10-backoff-grid-t2500-formal/group-report-20260915/t2500-backoff-static-tail-formal-complete.json` — 実データ (読むだけ)

repo root は `/work/1/SFC/tanab/izanagi/.codex/worktrees/t2647-fig8-impl` とする。上記以外も repo 内を読んでよい。

**大きい file を全文 `cat` しないこと。** `grep -n <語> <file>` で位置を出し、`sed -n '<開始>,<終了>p' <file>` で 200 行以内ずつ読む。

## この段の仕事

裁定 §2・§3 を実装する。新規 file 2 本だけを書く:

1. `tools/plotting/plot_b10_static_tail_formal.py` — B-10 静的 backoff 右 tail の 09-15 正式 cohort (group `b10-backoff-grid-20260915T061814Z-545445`) を描く新図種の生成器。裁定 §2.1〜§2.5 のとおり。
2. `orchestrator/tests/test_plot_b10_static_tail_formal.py` — 裁定 §3 の test。`_run()` 自走 harness 付き。

必ず守る点:

1. **触らない file**: 上記 2 本以外はすべて。特に `tools/plotting/plot_a2_certification.py`、`plot_b10_extended_backoff.py`、`plot_backoff.py`、`FIGURE_CONVENTIONS.md`、`tools/plotting/README.md`、`docs/**`、`orchestrator/tests/README.md`、`orchestrator/tests/conftest.py`、`.claude/**`、`hooks/**`。docs 編集・commit・`git add`・図の実データ生成 (成果物の `docs/paper-story/figures/` への配置) は親が行う。
2. 生成器は既存生成器を import しない (自己完結。標準 lib + numpy + matplotlib `Agg` だけ)。
3. **判定はコピー、統計は再計算** (裁定 §2.2 の 6〜7): verdict・workload state・interval state・qhat・qL・qU・L・U・U_flat は JSON からコピーし、再計算して上書きしない。一致検査 (`L == 1 − 2**qU` 等) だけ行う。平均・CI・abort 率・変動係数・端点比は reps の生値から再計算し、JSON `statistics` とは fail-closed で相互検算する。
4. **規律 2**: `performance_certified` が `False` 以外なら拒否、`correctness[].payload.certified` が 1 件でも `True` でなければ拒否、`anomalies != 0` も拒否。図は性能の認証ではない。caption に `performance_certified: false` の literal を残す。
5. **言い方**: 裁定 §2.1 の `FIXED_WORDING` を逐語で caption に入れ、"does not saturate" / "no saturation point" / "never saturates" / "saturation-free" / "saturates" を生成器の文字列にも caption にも書かない。生成器の中に「自分の caption に禁止句が無いか」を検査する gate は置かない (恒真なので)。検査は test 側だけ。
6. pin 表 (`PINNED_SHA256`・`GROUP_ID`・`EXPECTED_VERDICT`) は生成器の定数とし、CLI から渡せない。test は `load_measurements(..., expected_hashes=...)` / `main(..., expected_hashes=...)` の注入 seam で合成 fixture の実 SHA-256 を渡す (monkeypatch で定数を書き換えない)。
7. fixture は実寸 (3 workload × 8 点 × 5 反復、`.dat` 120 行、intervals 6 件 × 3、`statistics` は fixture の reps から同じ式で計算)。§10 のとおり、生成器が定数で持つ格子から組み立てる。少なくとも 1 本の test で**本物の matplotlib Figure** を `check_figure_layout` へ通す。
8. fixture に現行 hash を差し込むなど、テストを甘くして緑にしない。期待値へ揮発 payload (生成時刻・working tree hash) を焼き込まない。
9. 新規 test の parametrize id は ASCII だけ (`pytest.param(..., id="ascii-id")`)。
10. `_run()` は pytest 無しで全 test を拾って走らせる (雛形: `test_plot_b10_extended_backoff.py` 末尾)。`tmp_path` を要する test には tempfile の一時 dir を注入する。`skiputil.Skip` は SKIP として数える。
11. caption の英文は裁定 §2.4 の項 1〜11 の順序と内容で組み立て、値 (job id・件数・L の範囲・端点比・verdict) は data から書式化する。`Figure <N>.` は prefix `fig<N>_` から導く。
12. 生成器の x tick label が 8 個で重なるなら 45° 回転で解く。layout check は保存前に必ず走らせ、赤なら 3 成果物を 1 つも出さない (tmp → `os.replace` の順、失敗時に tmp を消す)。

## test の実走

- `tools/run_tests.py` と `python -m pytest` は sandbox から走らない (rc=16 / guard 拒否)。**`PYTHONPATH=. python3 orchestrator/tests/test_plot_b10_static_tail_formal.py`** (末尾の `_run` 自走 harness) を走らせ、緑には実走 nodeid・件数・範囲を併記する。走らなければ「実装済み・未実走」と書き、`closed` と書かない。親が統合後に `tools/run_tests.py` で実走する。
- 生成器の実データ実走 (`python3 tools/plotting/plot_b10_static_tail_formal.py --measurement-root /work/1/SFC/tanab/b10-backoff-grid-t2500-formal /tmp/<任意>/fig8_b10_static_tail_not_observed`) は sandbox 内の書込み可能な場所 (repo 内の `output/` 配下や `/tmp`) へ試してよいが、その成果物は repo に残さない (生成物は削除する。`docs/paper-story/figures/` には書かない)。実走できたら rc と 3 成果物の有無を報告に書く。
- 実データ test (`test_real_root_loads_and_matches_results_document_when_present`) は root が読めれば走る。skip になったらそう書く。

## 完了報告に必ず含める

- 変更 file と関数の一覧 (file:line)。
- 実走した nodeid と結果 (passed / failed / skipped 件数)。未実走があればそう書く。
- 実データ実走の rc と 3 成果物の有無 (試した場合)。
- caption の全文 (親が README に収録するので逐語で)。
- 所有外 caller・共有 fixture・consumer test への波及可能性の静的列挙 (`test_plain_runner_coverage` の allowlist 検査、`orchestrator/tests/README.md` の制約 meta-test、`tools/check_docs.py` に関係する path があるか)。
- 受理集合が裁定 §5 の列挙に収まることの自己申告 (収まらない点があれば名指しで書く)。
- 変異 matrix (裁定 §4) の M0〜M12 について、実装後の対象 file:line と anchor になる逐語 (1〜3 行)、その変異を単独で殺すと予想する test node (probe 走で親が確定するので予想でよい)。

## 出力形式

**出力は file に書かず、最終メッセージの本文に全文を書け** (親の launcher が保存する)。見出しはすべて `##` (H2) で書き、最後の節は必ず `## 総括` とする。`### 総括` と書いてはならない。予算が尽きそうなら、その時点の結論を出力形式どおりに書いて終われ (無出力が最悪)。

節の順:

## 変更一覧
## 実走結果
## caption 全文
## 波及の静的列挙
## 受理集合の自己申告
## 変異 matrix の anchor
## 総括
