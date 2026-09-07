## 前の子の差分の監査結果

二段 cache、atomic publish、独立 copy、crash 復旧の骨格は妥当でした。A1 で dirty な live source と descriptor の束縛、および submodule HEAD の動的 control が不足していたため補強しました。

## 直した内容

- `orchestrator/` と descriptor の dirty bytes を cache key に追加。
- ignored input を束縛できない場合は fresh rebuild へ fail-closed。
- submodule HEAD 変更の専用 control を追加。
- A7 の隔離限界を module docstring に明記。
- 所有 3 path 以外は編集していません。

## A1〜A7 の充足状況

- A1: 充足。HEAD、ccbench HEAD、3 blob SHA-256、visible path 集合 digest、live source 状態を束縛。
- A2: 充足。staging と publish は同一 filesystem、`os.rename`、返却 copytree は lock 外。
- A3: 充足。毎回 `copytree(..., symlinks=True)`。`copy.deepcopy(document)` も維持。
- A4: 充足。xdist は `popen-${worker}` の親、祖先不在時は fresh rebuild。serial は process cache。
- A5: 充足。既存 6 function / 11 node、入力、assertion は不変。
- A6: 充足。死亡 process の staging は未 publish のまま無視され、次 process が再構築。
- A7: code 内の限界明記は完了。canonical insight への記録は docs 編集禁止のため親対応。

## 事前登録変異への対応

- HEAD を key から外す変異: empty commit 後に builder 2 回・cache entry 2 個を要求する専用テストが殺す。
- copytree 完了まで lock を保持する変異: actual copytree 中の non-blocking flock 取得テストが殺す。
- lock 除去、hardlink、共有 Git metadata、document deepcopy 除去、key field 欠落、partial publish も専用 control で検出。

## 実走した検査

- 自走 harness: `11 passed in 110.85s`
- `py_compile`: 成功
- `git diff --check`: 成功
- `check_codex_agents.py`: rc=0
- `check_docs.py`: rc=0
- `tools/run_tests.py`: dispatch infrastructure failure、rc=16、child 未起動

## 波及可能性

cache key 計算に live source status 確認が増えます。nodeid と既存 correctness assertion への波及はありません。効果判定は親の同一 tip A/B が必要です。

## 未解決・前提

production の T-080 11 node 全体と受入全走は未実走です。A7 の canonical insight 記録も親へ残します。

## 総括

所有 3 path の実装と専用 control は完成し、焦点 harness は緑です。commit、`git add`、branch 操作、push、docs 編集は行っていません。