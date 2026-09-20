単独段 dispatch: stage=fix; sandbox=workspace-write; parent=/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2797-b5-contrast

## 必読事項の射影

次の絶対パスを読む。**この射影に挙げた file が読めなければ即停止**する。

- `/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2797-b5-contrast/s4-adjudication.md` §2.4 (launcher の登録は親が既存 login 側 tool の class に合わせて行う、と書いた箇所 — 本 fix はそれを Codex author として実施する)
- `/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2797-b5-contrast/codex/s5-author-A3.md` §「波及」(launcher 登録候補 = `local-ok`、先例 `submit_b10_backoff_grid.sh` / `submit_floor_pair.sh`、証拠表記候補 `static login-side submitter classification`、test_hooks の class / entry / local evidence の固定表)
- `/work/1/SFC/tanab/izanagi/.codex/worktrees/t2797-unit-fix1/tools/pegasus/admission_registry.json` — **編集対象** (`tools/pegasus/submit_b10_backoff_grid.sh` :328–333 の項が先例。key 順序は既存の並び規則 (アルファベット順) に従う)
- `/work/1/SFC/tanab/izanagi/.codex/worktrees/t2797-unit-fix1/orchestrator/tests/test_hooks.py` — **編集対象** (固定表 3 つ: class 表 :3214–3226 付近、entry 表 :3562–3600 付近、evidence 表 :4115–4130 付近。`test_bash_pegasus_execution_inventory_is_synchronized` :4538 と `test_bash_pegasus_registry_schema_and_fixed_classes` を読む)
- 読むだけ: `.../tools/pegasus/b5_contrast_launch.py` (登録対象。262 行。`--dry-run` は qsub も mkdir も行わず、`--submit` は attempt dir の mkdir と `qsub` argv list の実行だけ)、`.../hooks/guard_bash.py` (`_PEGASUS_ADMISSION_REGISTRY` の読み方、`local-ok` の意味)。

repo root は `/work/1/SFC/tanab/izanagi/.codex/worktrees/t2797-unit-fix1` とする。

## この fix の仕事

新設 login 側 launcher `tools/pegasus/b5_contrast_launch.py` を `tools/pegasus/admission_registry.json` に `local-ok` で登録し、`orchestrator/tests/test_hooks.py` の固定表 3 つを同期する。編集は上記 2 file だけ。

必ず守る点:

1. 登録項は先例と同じ 4 key (`class` / `reason` / `primary_gate` / `evidence`)。値: `class` = `local-ok`、`reason` = `login-side PBS B-5 generator-contrast pilot submitter (4 fixed jobs)`、`primary_gate` = `qsub submission; compute work stays in independent job bodies`、`evidence` = `static login-side submitter classification` (資源実測済みとは書かない)。JSON の整形 (indent、末尾改行、key 順) は既存 file と同じ。
2. `test_hooks.py` の 3 表へ同じ値で 1 項ずつ足す (既存の並び順に合わせる)。**既存 test の期待値を変えない**。反転・緩和・skip・削除は禁止。
3. 触らない file: 上記 2 file 以外のすべて (`hooks/guard_bash.py`、`tools/pegasus/b5_contrast_launch.py`、他の test、docs、`.claude/**`、`.codex/**`)。job dir へ書かない。
4. **絶対に `git add` / `git commit` / `git stash` / `git checkout` / `git reset` / `git rm` を実行しない。**
5. **実走:** `cd <repo root> && PYTHONPATH=. PYTHONDONTWRITEBYTECODE=1 python3 -B -c "import sys,pytest; sys.exit(pytest.main(['orchestrator/tests/test_hooks.py','-q','-rf','-k','pegasus_registry or pegasus_execution_inventory or pegasus_admission or local_ok or login_side']))"` (`-k` は実名に合わせる) と、`test_hooks.py` の**全件** (走らない・遅い場合はその旨)。`python3 -B -c "import json; json.load(open('tools/pegasus/admission_registry.json'))"` で JSON の妥当性。実走 nodeid・件数・結果を報告に列挙。走らないなら「実装済み・未実走」。
6. 報告は最終メッセージ本文。見出しは `##`。節: `## 変更の要約`、`## 実走結果`、`## 未了・懸念`、`## 総括`。
