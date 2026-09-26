## 変更

- [runner](/work/1/SFC/tanab/izanagi/.claude/worktrees/author-t2273pc-probe/tools/t2273_replica_runner.py): `ab` mode、`--order AP|PA`、`--smoke none|both` を追加。A/P を順に実行し、片方が rc 非 0 でも他方を実行して記録します。
- [plugin](/work/1/SFC/tanab/izanagi/.claude/worktrees/author-t2273pc-probe/tools/t2273_replica_plugin.py): `copy.digest`、発行 child の計測用 code 変換、timeline を追加。P では controller の写しを builder 呼出しに限って差し替えます。
- [analyzer](/work/1/SFC/tanab/izanagi/.claude/worktrees/author-t2273pc-probe/tools/t2273_replica_analyze.py): `--ab-dir` と `--ab-series` に有効性判定、対差、3 対の基準判定を追加しました。

## 自己検査

- 3 ファイルの `py_compile`: 成功。
- repo 外の合成 fixture で `--ab-dir` と `--ab-series`: 正常対は有効、3 対の基準は「満たす」。digest 不一致、ready 欠落、rc 非 0 はそれぞれ無効。
- builder の child 文字列を変換して `compile()` を確認。元のトップレベル 44 文の順序を保持しました。

## 限界・未解決

P の差し替え対象は `_build_t080_stub_free_e2e_repo` の実 repo root からの複製呼出しだけです。別 caller の複製と、2527 行付近の別 child は対象外です。早期 memo は conftest の開始関数と job barrier を包んでいますが、実際の発火は未確認です。child 変換は発行 child の識別文字列と各 phase の文を目印にします。smoke と pytest 本走は**実装済み・未実走**です。

## 総括

所有する 3 ファイルだけを変更し、commit は作っていません。静的検査と合成入力による判定検査は通りました。実測値に基づく効果判定は、A/P の本走後に行う必要があります。