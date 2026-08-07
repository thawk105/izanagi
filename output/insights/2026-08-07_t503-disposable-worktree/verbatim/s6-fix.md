段 6 fix を実装しました。変更は指定された次の 2 ファイルのみで、commit は作成していません。

- [tools/mutation_worktree.py](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t503-disposable-worktree/tools/mutation_worktree.py)
- [orchestrator/tests/test_mutation_worktree.py](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t503-disposable-worktree/orchestrator/tests/test_mutation_worktree.py)

`tools/mutation_harness.py` は SHA-256 `65e3390d...f15597dd` のまま不変です。

主な実装修正は以下です。

- Git 2.34.1 対応として `worktree list --porcelain` の行ベース parser に変更し、`-z` を除去。
- terminal ledger を spec 件数・ID・schema・commit・spec hash・厳密な整数型・status 集計まで検証。
- `<out>.lock`、生成 container 外 artifact、派生 artifact 衝突拒否を実装。
- 保持済み container の wrapper `--resume`、HEAD・porcelain・submodule 再検査を実装。
- signal handler を preflight 前から teardown 後まで有効化し、`killpg` race を吸収。
- teardown 部分成功時も receipt の `relocated=true` を保持。
- checkout を伴う Git 呼出しに `-c core.hooksPath=` を追加。

テストは MW-05/09/11/12/14 を実 wrapper・`main` 経路へ接続し直し、19 test function、SIGINT/SIGTERM parameter を含む20 node相当になっています。

### 所見対応表

| 所見 | 状態 | 対応 |
|---|---|---|
| R1-1 | closed | spec と terminal ledger を厳密照合。非 terminal は rc=125・container保持 |
| R1-2 | closed | spec/out/派生 artifact を生成 container 全体の外へ制限 |
| R1-3 | closed | lock を同一 directory の `<out>.lock` に変更 |
| R1-4 | closed | 既存 container の wrapper resume と wrapper 再開コマンドを実装 |
| R1-5 | closed | invocation 全域の signal handler、再送耐性、`killpg` OSError 吸収 |
| R1-6 | closed | 予期しない `Exception`/`OSError` を wrapper rc=125 に正規化 |
| R1-7 | closed | evidence 退避後の削除失敗でも receipt の `relocated=true` を維持 |
| R1-8 | partial | 指示対象の hook 経路は closed。filter/lazy-fetch は裁定どおり backlog |
| R1-9 | closed | MW-04 を fresh container の単一 `mkdir(exist_ok=False)` gate に整理 |
| R1-10 | closed | MW-06 fixture を初期化済み submodule 付きに変更 |
| R1-11 | closed | receipt/evidence/lock と spec の path 衝突を拒否 |
| R1-12 | backlog | inode 束縛 teardown・stale GC は実装せず |
| R2-1 | closed | MW-03 symlink/directory 判定分離、MW-04 二重 gate 解消 |
| R2-2 | closed | HEAD 比較削除時だけ受理集合が変わる fixture に変更 |
| R2-3 | closed | 異なる scratch・同じ out の wrapper subprocess 実競合、literal `125` |
| R2-4 | closed | rc=0・非 terminal を `main` に通し、terminal 条件だけで保持 |
| R2-5 | closed | evidence 退避→teardown 失敗→literal `125` を `main` で検査 |
| R2-6 | closed | wrapper subprocess へ SIGINT/SIGTERM、実 child の受信記録を検査 |
| R2-7 | closed | source/main tracked sentinel drift、literal `125` と receipt false を検査 |
| R2-8 | closed | argv・cwd・環境変数全体・stdout/stderr を direct fake harness と完全比較 |
| R2-9 | closed | 全 test 名を observation-point 限定化し、共通 `_LIMIT` を docstring に適用 |
| R2-10 | closed | 既存 fixture 無変更、self-runner 維持。meta-test 実走のみ未了 |

`regressed` と判定した所見はありません。

### 検査結果

実施済みです。

- `python3 -m py_compile`：2ファイル成功
- `python3 tools/check_codex_agents.py`：成功
- `python3 tools/check_docs.py`：成功
- `git diff --check --no-index`：2ファイルとも指摘なし
- 全 test function の限定名/docstring静的確認：19/19
- 禁止 command、`-z`、tempfile lock の残存：なし
- `git status --short`：指定2ファイルだけが untracked

pytest は**実装済み・未実走**です。

```text
python3 tools/run_tests.py orchestrator/tests/test_mutation_worktree.py -rf
```

を dispatch しましたが、`Pegasus dispatch infrastructure failure: qstat -Q preflight rc=1` でジョブ投入前に停止しました。実行済み nodeid は0件で、緑とは申告しません。

### 所有外への波及可能性

- tracked caller：静的検索では存在しません。wrapper はまだ自動 activation されません。
- direct harness caller：従来経路は変更しておらず、V-7 admission は backlog のままです。
- artifact producer：out の親 directory に `<out>.lock` を作れる権限が新たな明示条件です。
- resume consumer：保持 container は wrapper `--resume` 経由でのみ再利用できます。
- receipt consumer：部分 teardown 時の `dispatch_evidence.relocated` が実態どおり true になります。
- shared fixture：既存 fixture/conftest は未変更。新規テスト内の一時 Git repo/submoduleだけを使用します。
- consumer test：SIGINT/SIGTERM parameter により test function 19本から20 nodeが収集される見込みです。
- Git compatibility：行ベース porcelain parser により Git 2.34.1 を受理します。

## 総括

1. 直した骨子

   - Git 2.34.1 parser、terminal ledger、artifact境界、out lockを修正しました。
   - 保持 container の安全な wrapper resume と正確な再開案内を追加しました。
   - signal・例外・部分 teardown を fail-closedな receipt/rcへ接続しました。
   - MW-05/09/11/12/14と透明性テストを本番経路へ作り直しました。

2. 未解決・未実走

   pytest は dispatch infrastructure failure のため未実走です。R1-12、R1-8のfilter/lazy-fetch、V-7 direct admissionは裁定どおり backlogです。

3. 親が最初に確認すべき3点

   1. 計算ノードで新規20 nodeを実走し、特に当初赤の3 nodeを確認する。
   2. 保持 container の partial ledger → wrapper `--resume` → terminal teardown を確認する。
   3. MW-11の `relocated=true` と MW-12のSIGINT/SIGTERM実 child転送を優先確認する。