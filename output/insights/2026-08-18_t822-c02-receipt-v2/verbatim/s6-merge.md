## 合成の検証

`git diff --cached` と `git diff HEAD` は一致し、未 staged の上書きはありませんでした。三者比較でも両側の変更はすべて保存されています。

- main 側:
  - §5 欄名を「反復単位対比の判定パラメータ…」へ更新
  - `field_hash = 8ad36a...`
- wave 側:
  - path 件数 `40`
  - evidence contract hash `c62656...`
  - 制御文字 variant 3 hash
  - `DECIDER_VERSION == "s8c-decider/v3"` の test 名と期待値 3 箇所

index の再計算結果も一致しました。

- §5 field hash: `8ad36ad8...`
- evidence contract hash: `c626566e...`
- protected hash: `5f066f83...`
- runtime decider: `s8c-decider/v3`

§5 欄名は Markdown parser の field hash にだけ影響し、evidence JSON 由来の path 件数・contract hash・制御文字 hash には影響しません。両 corpus が別方向へ動いた形跡もありません。

## 変更点

変更は加えていません。[test_s8c_preregistration_core.py](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t822-c02-receipt-v2/orchestrator/tests/test_s8c_preregistration_core.py) の staged 合成内容はそのままです。docs 編集・commit・merge 操作も行っていません。

焦点 nodeid を `tools/run_tests.py` で投入しましたが、Pegasus の `qstat -Q` preflight が失敗し、runner が `rc=16`、pytest child は未起動でした。したがって **実装済み・未実走**です。

## 残る不整合

g7 発行だけでは現在の履歴を修復できません。

- `MERGE_HEAD` は g6、`s8c-decider/v2` として正常に検証されます。
- 一方、wave 親 `a0e11a64` は evidence contract を変更しながら g5 のままであり、`validate_condition_freeze_at(HEAD)` が `record-protected-mismatch: evidence_contract_sha256` で拒否しました。
- validator は最終 tip だけでなく全祖先 commit の record と protected bytes を照合します。そのため、現在の merge commit に正しい g7を追加しても、不正な `a0e11a64` が祖先として残る限り拒否されます。

解決には、main の有効な g6 を基点として wave の実装変更を再適用し、evidence contract の変更と g7 を同じ commit で導入するなど、無効な `a0e11a64` を祖先に含めない履歴の再構成が必要です。これは所有 test file 外かつ親の merge/履歴操作なので修正していません。

## 総括

対象 test file の合成自体は健全で、両側の意図と値は欠落なく保存されています。ただし、リポジトリ全体の merge は g7 追加だけでは成立しない祖先履歴上の不整合があるため、現状のまま健全とは結論できません。