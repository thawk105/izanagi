実装済み・未実走です。指定されたコード・テスト 2 ファイルのみ変更し、docs 編集・commit・pytest 実行は行っていません。

### 対応状況

- fix-1: `closed`
  - fuse なしの private validator [`_validate_generations_without_bootstrap_fuse()`](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t419-u2-contract-generation/orchestrator/campaign/env_contract.py:278) を抽出。
  - 構造、連番、key 一致、hash 一意性、隣接検査を直接テスト。
  - tuple 負例は有効な `GenerationEntry` 入りの非空 list に変更。
  - 有効な二世代列を private validator が受理する正例も追加。
- fix-2: `closed`
  - 異なる `env_tag` の一世代列を二本作り、property seam で同一 hash にした collision guard テストを追加。
  - docstring に、異なる preimage の SHA-256 collision を狙う検査であることを明記。
- fix-3: `closed`
  - module-level `validate_generations(GENERATIONS)` が `_CONTRACT_SHA256_INDEX` と `REGISTRY` より前に一度だけ存在することを AST で固定。
- fix-4: `closed`
  - `REGISTRY` の反復順序を完全一致で固定。
  - 未知 tag、`None`、非 hashable な list の完全な例外文字列を固定。

### M1 / M6 の帰属

M1 は [`test_validate_generations_synthetic_two_generation_negative_table()`](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t419-u2-contract-generation/orchestrator/tests/test_env_contract.py:456) の `invalid-successor` が担当します。fixture は exact tuple、連番、key 一致、hash 一意を満たしています。`is_valid_successor` 呼出しを削除すると private validator が入力を受理し、`pytest.raises` だけが赤になります。bootstrap fuse は呼ばれません。

M6 は [`test_validate_generations_rejects_cross_env_contract_hash_collision()`](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t419-u2-contract-generation/orchestrator/tests/test_env_contract.py:493) が担当します。各列は一世代なので隣接検査も fuse も発火しません。hash 一意性検査を削除すると入力が受理され、当該 `pytest.raises` だけが赤になります。

### 静的な波及確認

production の `lookup()` caller 21 箇所は未編集です。対象は T-419 probe、T-126 driver、s8b floor/oracle/report/ratified freeze、silo ladder、pipeline、loop、Pegasus floor scoping、P3 S4 gating です。

共有 fixture・consumer test では、`test_buildcache_v2.py`、`test_execution_guard.py`、`test_s8b_floor_campaign.py`、`test_s8b_oracle_driver.py`、`test_p3_s4_loop_trigger_gating.py` が raw contract、lookup identity、object identity に依存します。該当する型・関数・object 構築は変更していません。

新設 test 名やファイル内件数を exact pin する meta-test はありません。収集範囲の meta-test と real-repo node 制約を静的検索し、今回の新 node に個別更新が不要であることを確認しました。test の改名はありません。

### 不変性と検査

`ExecutionEnvironmentContract`、`_canonical_obj()`、`contract_sha256`、`lookup()`、`REGISTRY` 構築は未変更です。public validator の受理・拒否集合および production の g1-only 初期化経路も維持されています。

基準 hash は維持されています。

- Pegasus: `e576e9cd1369bba3ae8faca084d1b7256bf919a7dd2e5d6facb093cd9e242c01`
- linux-baremetal: `1b2ee85346a4c867754bda497b23d649e66027011167cfb0f9c7f9a1a5fa1dc7`

`git diff --check` と両ファイルの `python3 -m py_compile` は成功しました。pytest・受入全走・変異走行は未実走であり、緑とは主張しません。

## 総括

- fix-1〜fix-4 はすべて `closed`。
- M1 は fuse なしの隣接受理集合へ再照準した。
- M6 は異なる env の SHA-256 collision seam へ再照準した。
- import-time validation の順序を AST で固定した。
- 外部契約、golden hash、production caller は変更していない。
- 変更は指定 2 ファイルのみ。commit・pytest は未実施。