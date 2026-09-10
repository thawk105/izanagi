実装可能です。要点は、`_verify_entry_calibration` をそのまま残し、外側に用途別の strict wrapper を置くことです。S1 と S2〜S4 は編集所有を完全に分離できます。

### 静的に確認した現状

| 集合 | 全 entry | `attestation_mode=required` |
|---|---:|---:|
| active view `ec.REGISTRY` | 2 | 1 |
| ever-active | 2 | 1 |
| registered catalog | 3 | 2 |
| registered catalog ∪ ever-active | 3 | 2 |

- Pegasus g1: 48 標本、帯外 1 件 `3080.935`、`quality.status=accepted`。
- Pegasus g2: 48 標本、帯外 0 件、`quality.status=accepted`。
- g1/g2 とも acquisition receipt の qsub/PBS ID、known-values、clean pin、HT-off 束縛は現 schema を通る。
- floor protocol index は legacy anchor 1 件、versioned protocol 0 件。現 path は `output/s8b-freeze/floor_protocol.json`、SHA-256 は `261cec1c...e74aac`。
- active serial は 1。追加 activation record は存在しない。
- `git status --short` は空、HEAD は `98df871bf6af`。

## 変更面アンカー表

| 現在の `path:line` | 変更内容 |
|---|---|
| `orchestrator/campaign/s8b_floor_campaign.py:868` | `scan_floor_protocol_index` の直後に、index と current contract から唯一の `IndexedFloorProtocol` を選ぶ零選択面 resolver を追加する。 |
| `orchestrator/campaign/certified_writer_admission.py:206` | literal path を削除し、上記 resolver が返す `record.path` だけをロードする。receipt へ path/hash field は追加しない。 |
| `orchestrator/campaign/calibration_verify.py:159` | typed `VerifiedCalibration` の effective-clock 標本を既存 canonical predicate へ投影する自己整合 helper を追加する。method field は渡さない。 |
| `orchestrator/campaign/env_contract.py:382` | registered catalog と ever-active hash の和集合を一意な `GenerationEntry` 列へ解決する走査 helper と、g1 の exact 例外 1 組を追加する。 |
| `orchestrator/campaign/env_contract.py:417` | 現在の構造的 `_is_valid_activation_successor` は残し、その直後に artifact admission まで行う production 用 composite callback を追加する。 |
| `orchestrator/campaign/env_contract.py:441` | active 検証 cache と別に historical-strict 検証 cache を追加し、active cache による strict 検査の迂回を防ぐ。 |
| `orchestrator/campaign/env_contract.py:486` | `_verify_entry_calibration` 本体は無変更。その直後に historical、activation、catalog 用の三つの名前付き wrapper を追加する。 |
| `orchestrator/campaign/env_contract.py:519` | activation chain load 後、current mapping 構築前に registered catalog ∪ ever-active の production audit を実行する。 |
| `orchestrator/campaign/env_contract.py:551` | fork/reset/test reset で historical-strict cache も破棄する。 |
| `orchestrator/campaign/env_contract.py:601` | `_ensure_calibration_verified` を historical-strict cache と wrapper に切り替える。 |
| `orchestrator/campaign/ident.py:217` | current chain 読込みを catalog audit 済みの env-contract seam へ委譲する。 |
| `orchestrator/campaign/ident.py:304` | recorded activation prefix の production callback を composite admission へ切り替える。 |
| `tools/issue_env_contract_activation.py:205` | record の create-only publish 前検査に composite activation admission を渡す。 |
| `orchestrator/tests/calibration_freeze_authority_execution.py:137` | production successor の模擬実行を composite callback に追随させる。 |
| `orchestrator/tests/test_env_contract.py:839` | 自己整合走査を active 2 件から catalog union 3 件へ変更し、exact 件数を固定する。 |
| `orchestrator/tests/test_env_contract.py:884` | policy mutation を未 active g2 にも適用する正負例を追加する。 |
| `orchestrator/tests/test_env_contract_activation.py:1258` | structural successor と artifact admission を別々に固定する新規テスト群を置く。 |
| `orchestrator/tests/test_env_contract_activation.py:1641` | loader が受け取る callback identity の期待値を composite admission に更新する。 |
| `orchestrator/tests/test_env_contract_activation.py:2254` | issue tool が渡す callback identity の期待値を同様に更新する。 |
| `orchestrator/tests/test_s8b_protocol_builder.py:1044` | protocol index 由来の current-path resolver の正例、零選択面、複数候補拒否を追加する。 |
| `orchestrator/tests/test_campaign.py:4943` | floor admission が literal でなく resolver 結果を消費する統合テストを追加する。 |

## 実装順と依存関係

1. S2/S3/S4 共通基礎

   `calibration_verify.py:159` に canonical self-comparison helper を追加する。既存の `execution_guard.effective_clock_comparison_passes` を遅延 import し、入力は `samples_mhz` と `tolerance_pct` のみに限定する。D329 対象の `effective_clock.method` は参照しない。

2. S2 historical resolver

   - production 例外は `(contract_sha256, calibration_sha256)` の exact singleton、すなわち Pegasus g1 の `e576e9cd...` と `753f535a...` の組にする。
   - historical wrapper は無変更の `_verify_entry_calibration` を先に通し、同じ hash-bound artifact を再ロードして自己整合を検査する。
   - 自己不整合は exact g1 組だけ許可し、それ以外は `EnvContractError`。
   - `_ensure_calibration_verified` は専用 strict cache を見る。active cache に hash があっても strict 検査を省略しない。
   - 二度目の読込みも同じ SHA-256 を再検査するため、共有 verifier の変更なしで TOCTOU を fail-closed に保てる。

3. S4 catalog audit

   - `GENERATIONS` の全 3 entry を基礎集合とし、activation state の ever-active hash が全て一意に解決できることも確認する。
   - 各 entry に無変更の `_verify_entry_calibration` を適用するため、content-addressed path、quality、acquisition receipt、policy exact equality が全て production で発火する。
   - self-consistency は通常 0 failure 必須。ever-active かつ exact g1 組だけ historical exception を適用する。
   - active mapping の既存 `_verify_entry_calibration` 呼出しは残す。active 権限経路の意味を置換しない。

4. S3 activation admission

   - structural `_is_valid_activation_successor` の後段に composite callback を置く。
   - successor artifact に対し、無変更の共有 verifierと自己整合 0 件を要求する。ここでは g1 例外を一切使わない。
   - これにより根拠は `quality.status=accepted` に加え、content-addressed path、typed acquisition receipt の内部束縛、policy equality、自己整合になる。
   - production loader、campaign identity、issue tool の全 callback を composite へ寄せる。
   - `env_contract_activation.py:395` は serial 1 では transition callback を呼ばないため、現 serial 1 はそのまま通る。

5. S1 floor protocol seam

   - `scan_floor_protocol_index` の結果から、各 record の `env_tag` に対する current contract hash と一致する record を exact 1 件だけ選ぶ。
   - index は既に同一 contract hash の複数 path を拒否するため、ccbench の current pin を新しい選択条件にしない。現 protocol は `d706...`、現 approved pin は `511c...` であり、pin 選択にすると今日の受理を落とす。
   - resolver の引数は `root` だけとし、path、contract hash、ccbench pin、env tag を caller に渡させない。
   - admission は resolver の返した path をロードし、従来どおり `validate_protocol_against_current` を行う。

S1 の最終統合は S2 後です。将来 g2 が active になった際、index は historical g1 も走査するため、明示 grandfather が先に必要です。

## 並列単位と所有

| 単位 | 所有ファイル | 順序 |
|---|---|---|
| A: S2/S3/S4 | `calibration_verify.py`、`env_contract.py`、`ident.py`、`issue_env_contract_activation.py`、`test_env_contract.py`、`test_env_contract_activation.py`、`calibration_freeze_authority_execution.py` | 内部は基礎 → S2 → S4 → S3 の直列 |
| B: S1 | `s8b_floor_campaign.py`、`certified_writer_admission.py`、`test_s8b_protocol_builder.py`、`test_campaign.py` | A の strict API 確定後に開始可能。編集所有は A と素集合 |

統合順は A → B。B の実装自体は A の所有ファイルを編集しないため、A の API確定後は並行作業できます。

## 新規テスト nodeid 案と今日の静的な赤理由

| scope | nodeid 案 | 今日落ちる理由 |
|---|---|---|
| S1 | `orchestrator/tests/test_s8b_protocol_builder.py::test_current_floor_protocol_resolver_selects_exact_index_record` | resolver が存在せず、現在は admission 内の literal しかない。 |
| S1 | `orchestrator/tests/test_s8b_protocol_builder.py::test_current_floor_protocol_resolver_has_no_selection_arguments` | path/hash/env を受けない API 自体が未実装。 |
| S1 | `orchestrator/tests/test_campaign.py::test_floor_admission_uses_authority_resolver_not_legacy_literal` | resolver seam を sentinel path へ差し替えて legacy path を壊すと、現行 `:206-208` は必ず literal を読み拒否する。 |
| S2 | `orchestrator/tests/test_env_contract.py::test_historical_resolver_rejects_non_grandfathered_self_inconsistent_calibration` | schema-valid、accepted、canonical path の合成 artifact に帯外標本を入れても、現 `_ensure_calibration_verified` は自己比較せず受理する。 |
| S2 | `orchestrator/tests/test_env_contract.py::test_active_cache_cannot_bypass_historical_self_consistency` | 現 `:603-605` は active cache に hash があれば即 return するため、strict historical 検査が発火しない。 |
| S2 | `orchestrator/tests/test_env_contract.py::test_historical_self_inconsistency_exception_is_exact_g1_pair` | production 例外集合が無く、g1 に似た別 contract/calibration 組も現 resolver では自己不整合を理由に拒否されない。 |
| S3 | `orchestrator/tests/test_env_contract_activation.py::test_activation_admission_rejects_each_missing_basis[self-consistency]` | 現 callback は generation と contract 差分だけを見て、artifact の帯外標本を開かない。 |
| S3 | `...::test_activation_admission_rejects_each_missing_basis[content-address]` | 現 structural successor は path と SHA が共に変われば、非 content-addressed path でも true になり得る。 |
| S3 | `...::test_activation_admission_rejects_each_missing_basis[acquisition-receipt]` | qsub/PBS ID 束縛を壊した artifact も、現 structural callback は読まない。 |
| S3 | `...::test_real_pegasus_g2_passes_activation_admission_without_advancing_head` | composite admission が未実装。テストは g2 の成功に加え、source head が serial 1、record 追加 0 件を固定する。 |
| S3 | `...::test_serial1_never_calls_forward_activation_admission` | loader が新しい callback identity を受け取る配線がまだ無い。 |
| S4 | `orchestrator/tests/test_env_contract.py::test_registered_and_ever_active_audit_covers_three_real_entries` | 現検査は `REGISTRY` の 2 件しか列挙せず、期待 3 件に届かない。 |
| S4 | `orchestrator/tests/test_env_contract.py::test_registered_never_active_g2_policy_drift_is_rejected` | g2 のみ tolerance を変えて hash/path を再束縛しても、現 active loader は g2 を読まないため拒否が発火しない。 |

等価変異ではありません。走査を `REGISTRY` に戻す変異では、全 entry が `3→2`、required が `2→1` となり、実在する未 active g2 `94a4b79...` が丸ごと脱落します。さらに g2-only の policy/self-consistency mutation が生存するため、検査内容が明確に変わります。

## 既存テストで期待値変更が必要なもの

| nodeid | 変更 | 緩和でない理由 |
|---|---|---|
| `test_registry_effective_clock_self_failures_are_exact_known_exception` | `checked_entries: 2→3`、`required_entries: 1→2`。failure 集合は g1 exact singleton のまま。 | 未 active g2 を追加走査し、件数を厳しく固定する純粋な検出拡大。 |
| `test_production_loader_passes_source_head_constants_to_leaf` | callback identity を structural から composite admission へ変更。serial/head の期待は不変。 | artifact gate を追加した強い callback への置換。 |
| `test_issue_main_passes_production_successor_adapter_by_identity` | 同じ callback identity 変更。発行成功、record bytes、inactive warning は不変。 | publish 前の拒否条件を追加する変更。 |

この3件以外の既存期待値は変えません。特に g1 lookup、現 floor admission、実 g2 serial-2 正例、historical g1 resolver 正例は維持します。skip、xfail、削除、反転はありません。

## 実装しない方がよい点

- `execution_guard.py:295-317` の `effective_clock.method` 比較は変更しない。D329 の再裁定対象であり、本 wave の helper に method を渡さない。
- `_verify_entry_calibration` は変更しない。active 経路との共有を保ち、strict wrapper を外側に追加する。
- `env_contract_activation.py` の純粋 chain schemaや callback signatureは変更しない。既存 callback seam で serial 2 以降だけを強化する方が serial 1 を安全に保存できる。
- floor receipt に `protocol_path` や hash を追加しない。caller-selected authority を作るため、既存 protocol index resolver を使う。
- acquisition receipt の外部 source provenance を新設しない。現 artifact 内の型付き束縛までは使い、外部 job-resultや human approval の追加束縛は T-657 上位束へ残す。
- activation record、head literal、`FROZEN_MANIFEST`、凍結 artifact bytes は一切変更しない。
- current ccbench pin を floor path 選択条件にしない。現 legacy protocol を即時拒否するためである。

pytest、build、実機 campaign は実行していません。以上は read-only の静的検査結果であり、緑を確認したとは扱いません。

## 総括

- S1〜S4 は、現行受理を保ったまま実装できる。
- S2 は g1 の exact 1 組だけを historical grandfather とし、他を fail-closed にする。
- S3 は serial 2 以降の production callback にだけ artifact admission を追加する。
- S4 は走査対象を実在 2 件から3件へ増やし、未 active g2 を初めて検査する。
- S1 は既存 protocol index を単一 authority seam とし、caller の path 選択面を作らない。
- 実装単位 A と B の編集所有は完全に素集合で、統合順は A → B。
- method 比較、凍結 bytes、activation head、既存テストの強度は変更しない。