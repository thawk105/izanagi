## 変更した file と行

- [trial_registry.py](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2392-genesis-cli-entry/orchestrator/campaign/trial_registry.py:6522)
  - `register`, `accept`, `genesis` 順で第3 subcommand を追加。
  - 指定された必須5引数だけを受理。
  - manifest bytes から SHA-256 を導出。
  - slots を strict UTF-8 JSON の top-level array として読み、既存 creator を呼び出す。
  - canonical JSON で `attempt_registry_path`、`manifest_sha256`、`slot_count` を出力。

- [test_trial_registry.py](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2392-genesis-cli-entry/orchestrator/tests/test_trial_registry.py:6772)
  - 正例、create-only 再実行、generation 不一致、object／重複 key／非 UTF-8／非有限数、必須引数欠落を追加。
  - generation=2 の実体を使い、manifest bytes の digest、freeze 1行、全 slots、canonical 出力を検査。
  - 新規 test file、docs、fixture golden、凍結成果物は変更していない。

## 実走した検査 (nodeid と結果)

以下を `tools/run_tests.py` に渡したが、`qstat -Q preflight rc=1` により `child_started=false`、runner `rc=16` となり、nodeid は一件も実走されなかった。

- `test_genesis_cli_derives_manifest_digest_and_creates_canonical_registry`
- `test_genesis_cli_rejects_second_creation_without_changing_bytes`
- `test_genesis_cli_rejects_slot_generation_mismatch_before_creation`
- `test_genesis_cli_rejects_non_strict_slots_without_creating_artifact[object|duplicate-key|non-utf8|non-finite]`
- `test_genesis_cli_requires_prereg_generation`

したがって状態は **実装済み・未実走**。親の commit 後の焦点走・全走を代替しない。

静的検査は以下を実行済み。

- 2ファイルの AST parse: `rc=0`
- `git diff --check`: `rc=0`
- `git status --short --untracked-files=all`: 上記2ファイルの変更だけ
- test-file 列挙 meta-test を検索したが、`test_trial_registry.py` を名指しする Python 側の列挙はなし。既存同一ファイルへの追加なので新規 harness／台帳行は不要。

## 変更前後の受理・拒否挙動

変更前:

- CLI は `register` と `accept` のみ受理し、`genesis` は argparse の invalid choice。
- library creator は形式上妥当な caller-supplied `manifest_sha256` を受け取るため、manifest bytes と不一致でも作成時には検出しない。

変更後:

- 新たに `genesis` と必須5引数だけを受理。
- `--manifest-sha256`、`--registry`、`--retryable-failure-reasons` は引き続き拒否。
- manifest digest は CLI 内で実 bytes から導出。
- slots の object root、重複 key、非 UTF-8、非有限数、generation 不一致を作成前に拒否。
- 同一 argv の再実行は既存 create-only gate で拒否し、既存 bytes を変更しない。
- `register`／`accept` の引数、分岐本体、出力、意味は変更なし。
- raw argv は従来どおり記録しない。受入契約・schema・retry 理由集合も変更なし。

## 波及可能性の静的列挙

- module の `__main__` から新しい `genesis` が到達可能になる。
- 既存 accept CLI subprocess test は subcommand help 集合が増えるが、accept の parser・出力は不変。
- `_init_repo`、`_write_manifest`、`_attempt_slots`、`_canonical` をテストで再利用したが、共有 fixture 自体は変更していない。
- `create_attempt_registry_genesis` とその core serializer、registry reader、formal acceptance、receipt verifierは無変更。生成 bytes は既存 creator の契約に従う。
- `trial_registry.py` は A-1 source closure に含まれるため、未commit状態で焦点受入へ進むと contract-loader-drift の可能性がある。親による commit 後の実走が必要。
- `output/s8c-preregistration/attempt-registry.jsonl` は作成していない。

## 総括

確定 plan v2 の2-path実装を完了し、commit は作成していない。差分と構文は正常だが、Pegasus dispatch infrastructure failure のためテストは未実走であり、`closed` とは申告しない。