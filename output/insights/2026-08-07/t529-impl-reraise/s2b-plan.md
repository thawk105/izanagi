# 結論

[T-615] の未配線 site は、production の直接 caller としては **1 件**です。ただし [s8b_floor_campaign.py:308](</work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t529-impl-reraise/orchestrator/campaign/s8b_floor_campaign.py:308>) は producer・凍結 artifact 検証・live admission を兼ねるため、単純に historical resolver へ置換してはいけません。

実装は「凍結 protocol の意味検証＝historical」「発行・新規実測・resume admission＝current」の二入口へ分離する必要があります。

## 1. `validate_protocol` 呼出し元の全走査

共有 leaf は [s8b_floor_contract.py:105](</work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t529-impl-reraise/orchestrator/campaign/s8b_floor_contract.py:105>) にあり、注入 callback を [同:142](</work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t529-impl-reraise/orchestrator/campaign/s8b_floor_contract.py:142>) で呼び、protocol の記録 hash と callback の選択結果を [同:149](</work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t529-impl-reraise/orchestrator/campaign/s8b_floor_contract.py:149>) で照合します。

production の直接 caller は次の 2 件だけです。

| 直接 caller | 現在の束縛 | 判定 |
|---|---|---|
| [s8b_floor_campaign.py:308-324](</work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t529-impl-reraise/orchestrator/campaign/s8b_floor_campaign.py:308>) | callback が [同:311-317](</work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t529-impl-reraise/orchestrator/campaign/s8b_floor_campaign.py:311>) で `_env_contract.lookup(env_tag)` を呼ぶため、常に current | **残る混在 site 1 件** |
| [s8b_ratified_freeze.py:2803-2837](</work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t529-impl-reraise/orchestrator/campaign/s8b_ratified_freeze.py:2803>) | 呼出側から `contract_resolver` を必須注入 | **既に配線済み** |

`s8b_ratified_freeze` の後者は次のように正しく分離済みです。

- live の `launch_validate` は [s8b_ratified_freeze.py:3234-3239](</work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t529-impl-reraise/orchestrator/campaign/s8b_ratified_freeze.py:3234>) から current resolver [同:2769-2780](</work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t529-impl-reraise/orchestrator/campaign/s8b_ratified_freeze.py:2769>) を注入します。到達元も oracle driver の live gate [s8b_oracle_driver.py:519](</work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t529-impl-reraise/orchestrator/campaign/s8b_oracle_driver.py:519>)、[同:1074](</work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t529-impl-reraise/orchestrator/campaign/s8b_oracle_driver.py:1074>) です。
- read-only の `reverify_published_freeze` は [s8b_ratified_freeze.py:3244-3251](</work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t529-impl-reraise/orchestrator/campaign/s8b_ratified_freeze.py:3244>) から historical resolver [同:2783-2800](</work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t529-impl-reraise/orchestrator/campaign/s8b_ratified_freeze.py:2783>) を注入します。production 到達元は oracle report [s8b_oracle_report.py:1749-1759](</work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t529-impl-reraise/orchestrator/campaign/s8b_oracle_report.py:1749>) です。

混在している `s8b_floor_campaign.validate_protocol` の production 内部 caller は次の 4 経路です。

| caller | 用途 | 現状・維持すべき束縛 |
|---|---|---|
| [s8b_floor_campaign.py:410-440](</work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t529-impl-reraise/orchestrator/campaign/s8b_floor_campaign.py:410>) | 新 protocol の builder | current。producer なので historical 化しない |
| [s8b_floor_campaign.py:579-583](</work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t529-impl-reraise/orchestrator/campaign/s8b_floor_campaign.py:579>) | 発行直後の read-back | current。発行 transaction の検査 |
| [s8b_floor_campaign.py:2712-2755](</work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t529-impl-reraise/orchestrator/campaign/s8b_floor_campaign.py:2712>) | fresh run と resume の live admission | current を維持必須 |
| [s8b_floor_campaign.py:3481-3489](</work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t529-impl-reraise/orchestrator/campaign/s8b_floor_campaign.py:3481>) | 凍結 file の load 後、直ちに live run へ渡す CLI | artifact 検証を historical、run admission を current に二段化 |

また [s8b_prediction_runner.py:1457-1473](</work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t529-impl-reraise/orchestrator/campaign/s8b_prediction_runner.py:1457>) は builder を経由し、committed protocol bytes と [同:1564-1571](</work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t529-impl-reraise/orchestrator/campaign/s8b_prediction_runner.py:1564>) で比較します。これは新しい selector seal の producer 経路なので、未配線 read-only consumer には数えず current のままとします。

テストから共有 leaf を直接呼ぶ箇所は以下で、いずれも synthetic callback の明示注入です。

- `test_s8b_floor_contract.py:116,145,154,161`
- `test_s8b_experiment_numbers.py:113,118,125,131`
- `test_s8b_ratified_verify.py:411`

campaign wrapper のテスト caller は `test_s8b_floor_campaign.py:399,997,1002,1007,1016,1036,1053,1061,1075,1082,1427,2472,4799`、`test_s8b_floor_contract.py:175`、`test_s8b_protocol_builder.py:101,167,178,187,417`、`test_s8b_ratified_freeze.py:284` です。production consumer ではありませんが、現状はいずれも wrapper の current 束縛へ到達します。

なお `orchestrator/qualification/contract.py:127` の同名関数と `collector.py:376` は T-126 用の別 validator で、floor protocol の caller ではありません。

## 2. live admission との緊張点

**衝突はあります。** `s8b_floor_campaign.validate_protocol` 全体を historical 化するだけでは不正です。

D202 は、履歴解決を read-only 入口へ限定し、live admission は current のままとする決定です [docs/decisions.md:9772-9781](</work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t529-impl-reraise/docs/decisions.md:9772>)。旧 floor 証拠と current execution receipt を混成した新規実走を許す危険も明記されています [同:9783-9792](</work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t529-impl-reraise/docs/decisions.md:9783>)。

さらに D213 は floor campaign の resume を current に固定し、g1 protocol/current g2 の場合は calibration loader より前に拒否する仕様です [docs/decisions.md:10089-10098](</work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t529-impl-reraise/docs/decisions.md:10089>)。既存回帰試験も calibration・measure・journal mutation が起きないことを固定しています [test_s8b_floor_campaign.py:4455-4501](</work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t529-impl-reraise/orchestrator/tests/test_s8b_floor_campaign.py:4455>)。

したがって分離設計は次のとおりです。

1. 凍結済み protocol の意味検証は、記録 `contract_sha256` を `resolve_by_contract_sha256(..., expected_env_tag=...)` で一度だけ解決する。
2. producer・fresh run・resume は、別の current admission 関数で `lookup(env_tag)` と記録 hash の一致を要求する。
3. live admission は解決した current contract object を返し、同じ object を calibration・receipt 処理へ渡す。二度目の lookup は削除する。
4. historical 検証済み dict 自体を実行権限 token にしない。`run_campaign` は必ず current admission を再実行する。

これなら、旧 protocol の read-only 再検証は維持されますが、「現在 active でない較正で新しい実測を走らせる」ことは許しません。

## 3. file:line 単位の実装プラン

### `orchestrator/campaign/s8b_floor_campaign.py`

- [308-324](</work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t529-impl-reraise/orchestrator/campaign/s8b_floor_campaign.py:308>) を次の三層へ分割する。

  - resolver を必須引数に取る private core。共有 leaf の callback 内で resolver を一度だけ呼び、exact `ExecutionEnvironmentContract`、env_tag、記録 hash の三一致を確認する。
  - historical resolver は `_env_contract.resolve_by_contract_sha256(recorded_hash, expected_env_tag=env_tag)` を使う。unknown・ambiguous・cross-env・不正返却時に current へ fallback しない。
  - current resolver は `_env_contract.lookup(env_tag)` を使い、recorded hash と current hash の一致を要求する。

- 公開 `validate_protocol(document)` は「凍結済み artifact の read-only 意味検証」として historical core に束縛する。public live API に resolver 選択引数や `historical=True` のような切替面は追加しない。
- producer/live 用に `_validate_protocol_against_current` など用途が明白な private 関数を設け、normalized protocol と同一 current contract object を返す。
- [440](</work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t529-impl-reraise/orchestrator/campaign/s8b_floor_campaign.py:440>) の builder と [582](</work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t529-impl-reraise/orchestrator/campaign/s8b_floor_campaign.py:582>) の発行 read-back は明示的に current 関数へ変更する。
- [2750-2764](</work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t529-impl-reraise/orchestrator/campaign/s8b_floor_campaign.py:2750>) は current admission の戻り値を `protocol, contract` として受け取る。[2755](</work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t529-impl-reraise/orchestrator/campaign/s8b_floor_campaign.py:2755>) の二度目の `lookup` を削除し、その contract を calibration/receipt 全辺へ渡す。
- [3482-3489](</work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t529-impl-reraise/orchestrator/campaign/s8b_floor_campaign.py:3482>) は、load 後の public `validate_protocol` で historical artifact 検証を行い、その後 `run_campaign` 内で current admission を必ず再実行する二段構成にする。

`s8b_floor_contract.py`、`env_contract.py`、`s8b_ratified_freeze.py` は既存 seam で足りるため変更不要です。

### `orchestrator/tests/test_s8b_floor_campaign.py`

既存の整合した合成二世代 fixture [4393-4424](</work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t529-impl-reraise/orchestrator/tests/test_s8b_floor_campaign.py:4393>) を再利用します。ただし、D213 が定めるとおり activation 実装の正例とは数えません。

追加する試験は次のとおりです。

- **historical 正例:** protocol が記録する g1 を index に残し current を合法 successor g2 にした状態で、public `validate_protocol` が g1 を受理する。`resolve_by_contract_sha256` の呼出しが正確に 1 回、引数が記録 hash と `expected_env_tag` であり、`lookup` が呼ばれないことを固定する。
- **negative control:** unknown hash、cross-env hash、不正な resolver 返却をそれぞれ拒否し、current fallback が 0 回であることを固定する。単に document を返す「無条件 pass」実装ではこの試験が赤になる。
- **fresh live admission:** 同じ g1/current g2 状態で fresh run を拒否し、historical resolver、calibration loader、measure 関数が 0 回、run artifact が未作成であることを固定する。
- **resume 回帰:** 既存 [4455-4501](</work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t529-impl-reraise/orchestrator/tests/test_s8b_floor_campaign.py:4455>) を維持し、期待値の反転・緩和・skip はしない。
- **current 正例:** current が変わらない場合に fresh run/resume が従来どおり進むことを既存試験 [4427-4452](</work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t529-impl-reraise/orchestrator/tests/test_s8b_floor_campaign.py:4427>) と通常系で維持する。

変異として、少なくとも次の 3 本を事前登録できます。

- historical resolver を current lookup に戻す → g1/current g2 の historical 正例が kill。
- historical resolver の拒否を無条件 pass にする → unknown/cross-env 負例が kill。
- live admission を historical resolver に替える → fresh-run 負例と既存 resume 負例が kill。

親が実走する関連範囲は `test_s8b_floor_campaign.py`、`test_s8b_floor_contract.py`、`test_s8b_protocol_builder.py`、`test_s8b_ratified_verify.py`、`test_s8b_prediction_runner.py`、`test_frozen_artifacts.py` です。必ず `tools/run_tests.py` 経由とし、その後の全走・Codex/docs checker は wave 契約どおり親が行います。

### 凍結境界

- [output/s8b-freeze/floor_protocol.json:1](</work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t529-impl-reraise/output/s8b-freeze/floor_protocol.json:1>) は編集しない。現 SHA-256 は `261cec1c…e74aac`。
- [test_frozen_artifacts.py:38-46](</work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t529-impl-reraise/orchestrator/tests/test_frozen_artifacts.py:38>) の `FROZEN_MANIFEST` 期待値も編集しない。
- bootstrap fuse、g2 登録、activation record/receipt、active pointer は一切このプランへ含めない。

registry はコード上も 1 env 1 entry [env_contract.py:231-275](</work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t529-impl-reraise/orchestrator/campaign/env_contract.py:231>) で、fuse も複数世代を拒否します [同:316-326](</work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t529-impl-reraise/orchestrator/campaign/env_contract.py:316>)。read-only probe でも frozen pegasus hash、current hash、historical 解決先は同じ g1 object でした。したがって**今日は受理集合を 1 要素も変えません**。

## 今日の成果物への影響

**変わらない** — certified 選択結果・レポート・試行台帳の値、受理集合、contract hash 参照、凍結 bytes はすべて現状維持です。

pytest/build は read-only 制約により未実走であり、緑は主張しません。

## 総括

1. 配線すべき残り site は **1 件**、`orchestrator/campaign/s8b_floor_campaign.py:308-324` の current 固定 adapter。ただし内部の historical artifact lane と current producer/live lane を分離する。

2. live admission との衝突は **ある**。凍結 protocol の再検証だけを historical にし、fresh run・resume は別の current admission gate を必須にする。

3. 今日の受理集合は **変わらない**。registry が各 env 1 世代だけなので、historical と current は現在同じ contract を返す。