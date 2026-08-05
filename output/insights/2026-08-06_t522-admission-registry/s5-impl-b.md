## 変更内容

### `tools/check_docs.py`

- [tools/check_docs.py:2269](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t522-admission-registry/wt-B/tools/check_docs.py:2269)
  - admission 固有 prefix を追加。
  - loader を exact path importし、`BaseException` 捕捉、`sys.modules`・`sys.dont_write_bytecode` 復元、異常時の派生 finding 停止を実装。
- [tools/check_docs.py:2366](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t522-admission-registry/wt-B/tools/check_docs.py:2366)
  - 表の header/separator/row、duplicate、escaped pipe、code span、hidden table、orphan row を fail-closed 検査。
- [tools/check_docs.py:2512](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t522-admission-registry/wt-B/tools/check_docs.py:2512)
  - runbook 投影表の集合完全一致、unknown 表、実測表を検査。
- [tools/check_docs.py:2709](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t522-admission-registry/wt-B/tools/check_docs.py:2709)
  - README §0 宣言表、site/class、本文既知 path、fenced target の literal path を検査。
  - `output/.../pegasus/` の `text` fence は実行 target でない成果物パスとして区別。
- [tools/check_docs.py:3737](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t522-admission-registry/wt-B/tools/check_docs.py:3737)
  - `main()` の検査列へ呼び出しを追加。

### `orchestrator/tests/test_check_docs.py`

- [orchestrator/tests/test_check_docs.py:46](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t522-admission-registry/wt-B/orchestrator/tests/test_check_docs.py:46)
  - canonical JSON・runbook 3表・README 宣言表を持つ合成 baseline を追加。
- [orchestrator/tests/test_check_docs.py:648](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t522-admission-registry/wt-B/orchestrator/tests/test_check_docs.py:648)
  - 合成 repo に実 loader を exact path で複製する fixture を追加。
- [orchestrator/tests/test_check_docs.py:760](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t522-admission-registry/wt-B/orchestrator/tests/test_check_docs.py:760)
  - admission finding の固定 prefix と実件数を検査する helper を追加。
- [orchestrator/tests/test_check_docs.py:817](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t522-admission-registry/wt-B/orchestrator/tests/test_check_docs.py:817)
  - registry/loader/SystemExit、投影・unknown・実測・orphan、README 宣言・変数合成、検査蒸発の各変異を追加。
- [orchestrator/tests/test_check_docs.py:5702](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t522-admission-registry/wt-B/orchestrator/tests/test_check_docs.py:5702)
  - 実 repo clean control に admission finding 0 件を追加。

## 検査結果

- `python3 -m py_compile tools/check_docs.py orchestrator/tests/test_check_docs.py`: rc=0
- `python3 tools/check_docs.py`: rc=0、`check_docs: 違反なし`
- pytest: Pegasus ログインノード制約に従い未実走。テストについて緑は主張しません。
- git 操作・commit は行っていません。

## 波及可能性

- `tools/dev_wave_land.py` と `tools/task_run_check.py` は `check_docs.py` を直接実行するため、新しい fail-closed 条件を消費します。
- `_build_min_repo()` は既存 `test_check_docs.py` 全体の共有 fixture なので、既存 consumer test への回帰可能性があります。
- `test_dev_waves_integration.py` など、docs-check を subprocess 実行する consumer に波及します。
- `tools/codex_reasoning_ab.py` は変更した2ファイルの旧 SHA-256 を固定しており、同ツール実行時に snapshot drift として拒否される可能性があります。所有外のため未変更です。

## 総括

- 裁定 B-1〜B-6 の admission registry・runbook・README 同期検査を実装しました。
- loader 異常と `SystemExit(0)` は traceback を漏らさず固定 prefix の finding になります。
- 合成 repo と実 repo、事前登録された主要変異のテストを記述しました。
- 静的検査と実 `check_docs` は rc=0 です。
- pytest は実装済み・未実走です。
- 残る主なリスクは共有 fixture の回帰と所有外の固定 hash consumer です。