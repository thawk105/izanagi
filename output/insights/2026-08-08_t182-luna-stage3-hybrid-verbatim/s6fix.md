実装完了。編集は指定された 2 ファイルのみで、docs の親差分には触れず、commit もしていません。

主な変更:

- [tools/check_docs.py:264](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t182-luna-stage3/tools/check_docs.py:264)
  - `CODEX_DEV_WAVE_STAGE_MODEL_LITERAL`
  - `CODEX_DEV_WAVE_STAGE_MODEL_LENS_LITERAL`
  - 対応する 2 finding
  - workers／operations のファイル単位 slug finding
  - `DW-O01` cardinality／`-m <model>` finding
  - 一般化した `DEV_WAVE_MODEL_SLUG_RE`
- [tools/check_docs.py:3418](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t182-luna-stage3/tools/check_docs.py:3418)
  - `_check_dev_wave_model_pins()` を更新。
  - dispatcher の可視テキスト上で両 literal を `str.count() == 1` 検査。
  - workers／operations 全体の可視テキストから具体的な `gpt-<digit>...` slug を拒否。
  - `DW-O01` の節一意性と `-m <model>` 1 件を別 finding に分離。
- [tools/check_docs.py:3652](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t182-luna-stage3/tools/check_docs.py:3652)
  - `_check_command_docs_guard()` からの既存 caller を維持。
- [test_check_docs.py:496](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t182-luna-stage3/orchestrator/tests/test_check_docs.py:496)
  - `_build_min_repo()` を両 dispatcher literal と `DW-O01` placeholder を満たす baseline に更新。
- [test_check_docs.py:5058](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t182-luna-stage3/orchestrator/tests/test_check_docs.py:5058)
  - section mutation helper と公開経路 negative 群を追加。
  - 必須 8 ケースに加え、既存の backtick、S02、dispatcher drift 等も維持。
  - 既存 negative は削除していません。O01 concrete-model ケースは placeholder finding の併発を避け、slug finding だけを固定する追加方式へ変更しました。

変更前は hidden／重複 dispatcher literal、別節・見出しの slug、別 model family、`-m <model>` 欠落を受理しました。変更後はそれぞれ単独 finding で拒否します。現行 docs と説明用の `gpt-5.6-*`／`gpt-6-*` 表記は受理します。

検証結果:

- `python3 tools/check_docs.py`: 成功、`違反なし`
- `python3 tools/check_codex_agents.py`: 成功
- Python AST parse、`git diff --check`: 成功
- pytest: **実装済み・未実走**
  - `orchestrator/tests/test_check_docs.py -k dev_wave_model_pin` を2回試行
  - `orchestrator/tests/test_check_docs.py::test_dev_wave_model_pin_rejects_dispatcher_literal_in_html_comment` を1回試行
  - すべて `tools/run_tests.py` の Pegasus `qstat -Q` preflight が `rc=16` となり、pytest 本体は起動していません。

波及可能性は、所有外 caller `_check_command_docs_guard()`、共有 fixture `_build_min_repo()`、共有 helper `_visible_markdown_text()`／`_reference_id_sections()`／`_assert_findings()`です。後三者の実装は変更していません。旧 finding 定数名の in-repo consumer は残っていませんが、test file 全走は親側で必要です。

## 総括

- F1: dispatcher の段別 model とレンズ割当てを、可視テキスト上の各 exact 1 件へ強化。
- F2/F4: `DW-O01` の一意性と `-m <model>` exact 1 件を別 finding で固定。
- F3/F5: workers／operations 全体から、別 family を含む具体的 `gpt-` slug を拒否。
- 必須 negative 8 種と既存 negative、実 docs positive を公開経路で固定。
- standalone 検査は緑、pytest は Pegasus infra `rc=16` のため未実走。