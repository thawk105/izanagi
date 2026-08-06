必読資料・Git object・実行 receipt を read-only で照合した。pytest や checker の再実走はしておらず、以下の「緑」は親の実測値または既存 receipt に限る。

## P1 — 反証できなかった

結論は **real**。現行規約のまま、既存履歴を書き換えず、監査範囲を狭めず、ユーザー批准なしに、既定 full-history を緑へ戻す経路は見つからなかった。

- forward correction は汎用機構ではない。target はコード上も `6b64d217...` に固定されている。[check_ai_provenance.py:111](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-red-tests/tools/check_ai_provenance.py:111)
- 規約も担い手 `6d7141dc...` で枠を消費済み、新しい担い手や一般 allowlist を禁止する。[correction.md:5](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-red-tests/docs/provenance/correction.md:5)
- checker は selected set 内の correction candidate を exact 1 件に制限し、固定 target 以外を扱わない。[check_ai_provenance.py:855](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-red-tests/tools/check_ai_provenance.py:855)
- correction が消せるのも固定 target の「trailer 欠落」1 finding だけで、carrier 自身の通常違反や waiver は許容しない。[check_ai_provenance.py:899](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-red-tests/tools/check_ai_provenance.py:899)
- waiver は当該 commit の message と paths に対してだけ評価される。後続 commit から過去 commit を指定する構文はなく、物理行と `ratified=` が必要である。[ai-provenance.md:56](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-red-tests/docs/ai-provenance.md:56) [check_ai_provenance.py:811](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-red-tests/tools/check_ai_provenance.py:811)
- 変更の revert・削除・rename を後続 commit で行っても、checker は各元 commit の `%B` とその commit の paths を再読するため相殺されない。[check_ai_provenance.py:786](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-red-tests/tools/check_ai_provenance.py:786)
- `--range` は正規 CLI だが、既定 full-history の代替ではない。権威があるのは correction の両 commit を含む range または既定 full-history だけである。[audit.md:13](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-red-tests/docs/provenance/audit.md:13) [correction.md:23](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-red-tests/docs/provenance/correction.md:23)
- `--range X..X` のような空集合なら機械的には緑になり得るが、これは監査範囲の回避であり、既定 full-history を直す経路ではない。[check_ai_provenance.py:690](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-red-tests/tools/check_ai_provenance.py:690)

誤検出の反証も成立しなかった。

- merge commit も「すべての commit」に含まれ、AI 非関与なら `AI-Agent: none` が必要である。[ai-provenance.md:11](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-red-tests/docs/ai-provenance.md:11) [ai-provenance.md:35](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-red-tests/docs/ai-provenance.md:35)
- 5 merge commit は Git object の `%B` を直接実読し、いずれも merge subject のみで trailer がなかった。Git object には file:line がないが、親 brief の対象一覧は [s1-brief.md:24](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-red-tests/s1-brief.md:24) と一致した。
- `.py` は所在不問で実装面であり、probe・harness・凍結場所であることは免除理由にならない。[ai-provenance.md:44](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-red-tests/docs/ai-provenance.md:44) checker も suffix を prefix 判定より先に適用するため、`output/insights/**.py` は実装面になる。[check_ai_provenance.py:541](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-red-tests/tools/check_ai_provenance.py:541)

したがって、実際に緑へ戻すには次のいずれかが必要になるが、すべて今回の制約外である。

- 6 commit の message を書き換える：履歴書き換え。
- correction を一般化する：現行 gate・受理集合の変更であり、ユーザー裁定が必要。
- 既知違反 allowlist や開始点変更を入れる：gate 弱体化。
- waiver を過去 commit に付ける：履歴書き換えか、waiver 契約の変更かつユーザー批准。

## P2 — helper 単体は real、標準 wave 全体では refuted

`tools/dev_wave_land.py` 自身が行う provenance 検査は fold commit の `--message-file` preflight だけで、既存 6 件を含む full-history は実行していない。したがって「land helper 単体では止まらない」は正しい。

一方、標準 dev-wave 手順には別の停止経路がある。

- DW-O17 は `message-file → commit → 既定 full-history` を要求し、赤なら停止する。[operations.md:89](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-red-tests/docs/dev-wave/operations.md:89)
- stage 9 は commit と検査結果を固定してから land へ進む契約である。[core.md:104](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-red-tests/docs/dev-wave/core.md:104)
- supervisor を使う構成では、fixed check の非零終了が `fixed-checks` failure になる。[checker.py:317](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-red-tests/tools/dev_waves/checker.py:317) [checker.py:689](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-red-tests/tools/dev_waves/checker.py:689)
- `task_run_check.py provenance-check` を fixed check に含めれば、現在の赤がそのまま停止条件になる。ただし、その check spec が実際に採用されるかは構成依存であり、今回は未実走・未確認。

よって P2 を「land 関数の局所的性質」と解釈すれば real、「本件は wave の blocker ではない」という親の一般化は **refuted**。規約準拠の標準フローなら DW-O17 で land 前に止まる。

## P4 — 宣言済み pytest 範囲は裏付けあり、repo 全数という主張は refuted

親の実走は [run_baseline.sh:19](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-red-tests/run_baseline.sh:19) の `tools/run_tests.py -rf` で、receipt も引数 `["-rf"]`、追加 environment なしだった。ログは [baseline.log:61](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-red-tests/baseline.log:61) に `6837 passed, 20 skipped` を記録している。合計 6857 なので、少なくともその実行で収集された node は全て passed または skipped であり、deselected の記録もない。

ただし、親 brief の「4 gate が選択 flag を拒否する」は誤りである。

- runner は対象ファイルや pytest option をそのまま渡す用途を明記している。[run_tests.py:21](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-red-tests/tools/run_tests.py:21)
- `_is_full_suite` は選択走を分類して `False` を返すだけで、実行を拒否しない。[run_tests.py:310](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-red-tests/tools/run_tests.py:310)
- 最終的には user args を pytest に渡して実行する。[run_tests.py:977](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-red-tests/tools/run_tests.py:977)
- `-rf` は許可された compact option が `q/v` だけなので acceptance shape と認識されない。[run_tests.py:432](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-red-tests/tools/run_tests.py:432)
- そのため、この実走では unstaged-deletion と RuleOps の acceptance preflight が素通りした。[run_tests.py:484](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-red-tests/tools/run_tests.py:484) [run_tests.py:522](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-red-tests/tools/run_tests.py:522)

さらに、6857 件は repo 全体ではなく、明示的に `orchestrator/tests` へ閉じた集合である。

- runner の既定 target は `orchestrator/tests`。[run_tests.py:46](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-red-tests/tools/run_tests.py:46)
- `pytest.ini` も `testpaths = orchestrator/tests` で、`output` と `external` を収集除外する。[pytest.ini:10](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-red-tests/pytest.ini:10)
- これはテスト自身でも意図的な範囲として固定されている。[test_pytest_collection_config.py:93](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-red-tests/orchestrator/tests/test_pytest_collection_config.py:93)
- 収集対象外の具体例として、[test_run_probes_evaluator.py:669](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-red-tests/output/insights/2026-08-03_t361-t362-cluster-probes/driver/test_run_probes_evaluator.py:669) には静的に数えて 63 個の `test_` 関数がある。`output` 配下なので今回の6857件には入らない。凍結 evidence のテストであり正式 acceptance suite とは限らないが、未実走なので緑とも赤とも判定できない。
- `external/ccbench` の C++ test/build/format 面も pytest の集計外。今回の状態は未実走・未確認。
- 20 skipped の個別理由も、この検証では未実走のため「構造的依存物不在」とは確認していない。

したがって、「宣言済み orchestrator pytest suite に failure がなかった」は裏付けられるが、「repo に存在する全テスト本体に赤がない」は **未証明で、P4 の広い表現は refuted**。

## 数え落とされている赤候補

親の4検査以外に、少なくとも以下の機械検査面がある。いずれも今回未実走なので、赤とは断定しない。

- `tools/ruleops.py check`：production RuleOps ledger 検査。今回の `-rf` では acceptance preflight から外れた。
- `tools/audit_dangling_commits.py`：unreachable/dangling commit 監査。非零になり得る。
- `tools/check_workflow_models.py`：workflow model 設定の standalone lint。
- `tools/check_codex_output.py`：Codex 成果物の存在・サイズ・見出し検査。
- `tools/spool_fold.py --dry-run`：pending fragment と fold 可能性の検査。
- `tools/dev_wave_land.py` 自身の audit SHA、tested SHA、docs/fold/cleanliness 等の land precondition。
- `tools/dev_waves/checker.py` の fixed checks と active re-observation。
- `.claude/settings.json` の `guard_write`、`guard_bash`、`guard_read`、`guard_agent`。ただし Codex には未配線で、repo-wide health check ではなく操作時 gate。
- `external/ccbench/.github/workflows/` の build/format 面、および CMake 側の任意 test/microbenchmark。root repo には tracked な GitHub Actions、pre-commit、Makefile、tox/nox の統一 gate は見つからなかった。

## F75 の計数

「`b0a07672` は F75 型の3例目」は **正しい**。

1. F75 本体（2026-08-01）。
2. T574 の再発（2026-08-06）。
3. `b0a07672` の `output/insights/**.py`（同日、別 wave）。

ただし重要な限定がある。最初の2件は検出後に landing 前または履歴確定前に修正されており、`b0a07672` は「履歴に残存した F75 型違反」としては最初の例である。したがって「同型インシデントの3例目」は正しいが、「永続違反の3例目」ではない。[failures.md:1755](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-red-tests/docs/failures.md:1755) [failures.md:1776](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-red-tests/docs/failures.md:1776)

## 総括

1. **P1: real** — 現行規約内では、固定済み correction・非遡及 waiver・既定 full-history のため6件を前方 commitだけで緑にできない。  
2. **P2: helper単体は real、wave全体では refuted** — `dev_wave_land.py` は止めないが、DW-O17 の full-history gate は land 前に止める。  
3. **P4: 狭義は real、広義は refuted** — 6857 collected nodes に failure はないが、repo全テストではなく、収集外・skip・別runner面は未測定。  
4. 親が最初に確認すべき点①：`-rf` を外した acceptance shape で RuleOps等の preflight を別実測する。  
5. 確認点②：実運用の stage 9 が DW-O17 を実際に必須化しているか、land直前経路を追う。  
6. 確認点③：63個の収集外 output tests、20 skip、external C++面を「正式対象／凍結証拠」に分類して必要分だけ実測する。