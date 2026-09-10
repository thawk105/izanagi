## MF1 の直し方と適用結果

[`hooks/guard_bash.py`](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2146-guard-author/hooks/guard_bash.py:2498) に既存防護専用の `_existing_tree_violation()` を分離しました。

`perf` の出力値を後段の引数検査から除外する前に、次を直接検査します。

- 末端防護対象
- official / exploration campaign tree
- namespace marker
- hooks subtree
- ccbench tree
- 固定の発行主体 root

`-o FILE`、`--output FILE`、`--output=FILE` が対象です。scope 外の密着短 option `-oFILE` は追加実装せず、従来どおり allow を維持しました。

## MF2 の直し方と適用結果

[`_inside()`](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2146-guard-author/hooks/guard_bash.py:2284) で `tree == os.sep` の場合、絶対 path を内包すると判定するよう修正しました。

`decide()` 直呼び結果：

- `rm -rf /`: deny
- `rm -rf --no-preserve-root /`: deny
- `mv / /tmp/t2146-root-old`: deny
- `tar -xf /tmp/t2146.tar -C /`: deny
- `/tmp`: allow
- 兄弟 prefix `dev-wave-authority-copy`: allow
- 別 job dir: allow
- 別 worktree: allow

## 反転検査 (fix 前 6 件 / fix 後 0 件)

変更前版と同一の20ケースを比較しました。末端・campaign tree・namespace marker・hooks・ccbench を `perf` の出力先・引数・redirect 先に含めています。

fix 前の `deny → allow` は6件でした。

- official campaign 出力
- exploration campaign 出力
- namespace marker 出力
- `hooks/guard_bash.py` 出力
- `hooks/README.md` 出力
- ccbench 出力

fix 後は20ケースすべて変更前版と一致し、`deny → allow = 0`。通常の `perf` 出力先3形は引き続き allow です。

## 発行主体防護の歯の再確認

以下を実測し、すべて期待どおりでした。

- redirect / 引数 / tree / 祖先 / glob / lexical: deny
- inode / canonical alias / lexical-independent fixture: deny
- authority 文字列を含まない canonical alias の fast path: deny
- 内部例外 fallback: `rc=2`
- authority への `perf -o FILE`、`--output=FILE`: deny
- scope 外の `perf -oFILE`: allow
- `py_compile`: rc=0

加えて `tools/check_codex_agents.py` と `tools/check_docs.py` はともに rc=0、`git diff --check` も rc=0です。pytest は指示どおり実行していません。

## 波及可能性

静的な呼び出し・consumer は次のとおりです。

- `.claude/settings.json`
- `.codex/hooks.json` → `hooks/codex_guard.sh`
- `tools/check_codex_hooks.py`
- `tools/codex_worker_launch.py`
- `orchestrator/tests/test_hooks.py`
- `orchestrator/tests/test_codex_hooks.py`
- `orchestrator/tests/test_codex_worker_launch.py`

共有 fixture は `_load_hook()`、`_prepare_guard_fixture()`、`_load_guard_fixture()`、`_run_guard_subprocess()` です。`decide()` の公開 signature は変更していません。

レビューで既知の `os.walk` 総数を1に固定した tracked assertion は未変更です。authority index 追加後は2 index を各1回走査するため、親のpytestでは引き続き確認が必要です。テストを通すためのproduction緩和は行っていません。

## 総括

MF1・MF2を適用し、fix前6件の防護退化をfix後0件へ戻しました。変更は `hooks/guard_bash.py` のみで、`guard_write.py`、既存テスト、docsには触れていません。git add・commit・mergeも実行していません。