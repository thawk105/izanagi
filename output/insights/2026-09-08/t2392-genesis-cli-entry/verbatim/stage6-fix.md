## 変更した行

[orchestrator/tests/test_trial_registry.py](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2392-genesis-cli-entry/orchestrator/tests/test_trial_registry.py:6823) の `test_genesis_cli_*` だけを修正しました。

- stdout の期待値を production の `R._canonical_json_bytes` から独立したテスト helper `_canonical` に変更。
- generation 不一致では全 slot を `3` に統一し、各 `schedule_row_sha256` を再導出。
- strict JSON 例を妥当な slot 集合ベースに変更し、期待エラーに `[json]` gate を明記。
- production、既存 fixture、既存テスト、docs は未変更です。

## 実走した検査 (nodeid と結果)

実装済み・未実走です。

- 範囲 `orchestrator/tests/test_trial_registry.py -k test_genesis_cli_`
  - runner が計算ノードへ dispatch しようとしたものの、`qstat -Q preflight rc=1`、`child_started=false`、rc=16。テスト本体は未起動。
- nodeid `orchestrator/tests/test_trial_registry.py::test_genesis_cli_derives_manifest_digest_and_creates_canonical_registry`
  - exact nodeid でも同じ dispatch infrastructure failure。未実走。
- `git diff --check -- orchestrator/tests/test_trial_registry.py`
  - 成功。

ローカルでの直接 pytest は実行していません。

## 各拒否例が単独理由になったことの根拠

- 再作成: 実体の `R.main` を再実行し、create-only エラーと既存 bytes 不変を検査する既存形を維持。
- generation: 全 slot が一様に generation `3` で、hash も整合。CLI 引数 `2` との不一致だけが外側 gate の拒否理由です。
- top-level object: strict JSON としては妥当で、array gate だけが拒否。
- duplicate key: 全必須 field を持つ slot に同値の `slot_id` を重複。通常の last-wins `json.loads` では元の妥当な slots と一致することも assert。
- non-UTF-8: 妥当な slot の `slot_id` だけを raw `0xff` に変更。Latin-1 の寛容 decode では妥当な `"ÿ"` の slot になることを assert。
- non-finite: 妥当な slot の数値 field `replicate_index` に `NaN` を配置。他の field と残りの slots が元入力と一致することを assert。
- strict decoder の3例はいずれも `[json]` を含む具体的エラーを assert。
- 必須引数欠落: argparse の `SystemExit(2)` を検査する既存形を維持。

## 波及可能性の静的列挙

- 所有外 caller: production の `R.main` や registry creator は未変更なので受理集合への波及なし。
- 共有 fixture: `_genesis_cli_fixture` と `_attempt_slots` は未変更。
- consumer test: 変更は当該 `test_genesis_cli_*` 内のローカル入力・期待値だけ。他の consumer test へのデータ変更なし。
- 自走 harness: 同一 test file の通常収集対象のままで、登録変更なし。
- `git status --short` では `orchestrator/tests/test_trial_registry.py` だけが変更されています。

## 総括

変更前は canonical stdout が自己 oracle、generation 不一致が mixed-generation と過剰決定、strict JSON 例が不完全な slot でした。変更後は独立 canonical bytes、一様で妥当な generation `3` の slots、妥当な slot 集合へ照準した decoder 拒否例になっています。

production の受理・拒否挙動および指示外の受理集合は変更していません。commit、add、checkout は行っていません。