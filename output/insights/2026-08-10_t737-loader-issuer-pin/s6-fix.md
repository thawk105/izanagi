指定された [test_env_contract_activation.py](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t737-loader-issuer-pin/orchestrator/tests/test_env_contract_activation.py) だけを編集しました。production、docs、既存期待値は変更せず、commit も作成していません。

## 対応表

| 所見 / 修正 | 状態 | 対応 |
|---|---|---|
| C-01 / D-01 / FIX-1 | `closed` | calibration 検証を通らない leaf 入口の負例を2本追加。G/P 縮退時に受理へ反転する semantic kill を固定 |
| C-02 / FIX-2 | `closed` | issuer 負例2本にも `issuer.__file__` patch を追加。issuer 3本すべてで `sys.path` を `finally` 復元 |
| C-03 / FIX-3 | `closed` | 既存 `_entry_names(directory)` の署名を維持し、新規 `_entry_sha256s(directory)` による `{名前: sha256}` 前後比較へ強化 |
| FIX-4 | `partial` | AST 構文検査と静的85 node算定は成功。pytest本走は実行基盤障害で未実走 |
| Regression | なし | production-loader 2 node、既存期待値、helper署名は不変 |

## 追加・変更した nodeid

- `test_loader_leaf_rejects_generation_skip_at_last_of_65_envs`
  - 追加。
  - activation leaf 層で、65件目の `successor_rows` を検査する量化点 G を pin。
  - `exactly +1`、最終 env_tag、`g1 -> g3` を要求。

- `test_loader_leaf_rejects_invalid_successor_at_last_of_65_changed_envs`
  - 追加。
  - activation leaf 層で、65件目の `changed` に successor 述語を適用する量化点 P を pin。
  - `ec.is_valid_successor` を最終 env_tagだけ拒否する形で patch。

- `test_issue_main_rejects_generation_skip_at_last_of_65_envs_without_publishing`
  - 変更。
  - issuer integration 層の量化点 G。`__file__`、`sys.path` 復元、SHA-256 authority guardを追加。

- `test_issue_main_rejects_invalid_successor_at_last_of_65_changed_envs_without_publishing`
  - 変更。
  - issuer integration 層の量化点 P。同じ隔離・復元・guardを追加。

- `test_issue_main_accepts_65_env_plus_one_and_publishes`
  - 変更。
  - issuer integration 層で65 envすべての `+1` 受理、すなわち過剰拒否防止を pin。
  - authority guardをSHA-256写像比較へ強化。

## 検査結果

`python3 tools/run_tests.py orchestrator/tests/test_env_contract_activation.py -q` を実行しましたが、Pegasusの `qstat -Q` preflight失敗で `rc=16` となり、pytestは起動されませんでした。local admissionも予約台帳を安全に更新できず、規律上直接pytestへ迂回していません。

したがって結果は **実装済み・未実走** です。

静的検査では以下を確認しました。

- AST parse成功。
- 必須関数5本と新helperの存在を確認。
- `_entry_names(directory)` の署名は不変。
- parameterize展開を含む静的node数は85。
- 実authorityの現行entryは通常ファイル1件で、SHA-256 guardの入力条件を満たす。

既存83 nodeで通常実行時に赤化すると予測されるものはありません。ただし変更したissuer 3 nodeは、実authorityの既存同名ファイルが実行中に書き換わる、または読取不能になる場合、強化したfail-closed guardにより意図的に赤くなります。

## 総括

(a) C-01/D-01、C-02、C-03は実装上 `closed`。FIX-4のみ実走不能のため `partial`、`regressed` はありません。

(b) **実装済み・未実走**です。pytestはdispatch infrastructure failure（rc=16）で起動されていません。

(c) 親は実行可能な環境で対象85 nodeを全走し、G/P縮退時の新leaf 2 nodeのsemantic killと、issuer変異時に「SystemExitが起きない」単一理由で赤くなることを確認してください。