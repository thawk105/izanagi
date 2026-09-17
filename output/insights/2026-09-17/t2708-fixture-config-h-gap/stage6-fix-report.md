## 変更点 (diff の要約と行番号)

[tools/t2708_fixture_gap_probe.py](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2708-fixture-config-h-gap/tools/t2708_fixture_gap_probe.py:185) のみ修正。415 行。

- 185 行以降：enforcing pytest session を作成し、rc・所要・環境・module の実体パスを記録。
- 198 行以降：session 開始 hook で完全修飾名を import。通常の collection だけでは指定名が残らなかったため追加。
- 234 行以降：準備成功時のみ既存の計測処理へ進む。
- 352・392 行以降：隠し引数 `--hold-session-only` と分岐を追加。

## 実走した検査 (argv・rc・hold session の記録値)

cwd は指定 worktree。以下の最終検査はすべて rc=0。

```bash
python3 -B -m tools.t2708_fixture_gap_probe --help

PYTHONPYCACHEPREFIX=/tmp/t2708-fix-pycache python3 -m py_compile tools/t2708_fixture_gap_probe.py

python3 -B -m tools.t2708_fixture_gap_probe --source-root /work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2708-fixture-config-h-gap --work-root /tmp/t2708-fix-selftest-20260917 --out /tmp/t2708-fix-selftest-20260917/result.json --selftest

python3 -B -m tools.t2708_fixture_gap_probe --source-root /work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2708-fixture-config-h-gap --work-root /tmp/t2708-fix-hold2-20260917 --out /tmp/t2708-fix-hold2-20260917/result.json --hold-session-only
```

selftest は `failures=[]`、pytest session なし。

[hold-only 結果](/tmp/t2708-fix-hold2-20260917/result.json) は以下のとおり。

- hostname：`pegasus02`
- pytest rc：`5`、147 件 deselected
- `elapsed_ns`：`5904901178`
- `module_loaded=true`、実体は指定 worktree の held module
- `environment_preserved=true`、`git_environment_keys=[]`
- `failures=[]`

初回 hold-only は module 不在で probe rc=1。上記 hook 追加後に解消しました。

## 未実走の項目

本走は**実装済み・未実走**。builder、取り込み計測、scan 対比較、job dir 退避後の起動は未検証です。

## 波及と既知の限界

production・test・docs・保留登録・conftest・共有 fixture の編集なし。解除 env の設定、commit なし。

pytest の plugin・module はプロセス内に残ります。発行 A/B ではないことなど、既存の計測上の限界は維持しています。

## 総括

指定の import 失敗を修正し、hold-only で成功を確認しました。本走の確認は計算ノードでの再実行待ちです。