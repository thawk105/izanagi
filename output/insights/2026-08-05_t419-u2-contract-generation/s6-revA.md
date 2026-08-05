# 敵対レビュー（レンズ A: 恒真化と偽の保証）

**判定: NO-GO（変異証拠の帰属を要修正）。** 対象2ファイルは commit `0324d627` と一致している。静的レビューのみで、pytest は実走しておらず、緑とは報告しない。現行実装そのものに成果物を直ちに変える must-fix は見つからないが、M1・M6 は裁定が要求した単一理由性を満たさず、bootstrap の import 結線削除にも検出テストがない。

## 所見

[severity: should-fix] [攻撃シナリオ] `validate_generations` の負例が後段の bootstrap fuse に遮られ、狙った検査の削除を「入力が受理されたこと」ではなく「別の例外 message になったこと」で kill している。M1 で隣接 `is_valid_successor` 呼出しを削除すると `invalid-successor` は fuse まで進んで依然拒否され、テストは regex 不一致で赤になるだけである。連番検査を削除した `non-contiguous` も同じである。また sequence shape 検査全体を削除しても、空 tuple/list は fuse が同じ `EnvContractError` を出し、message を見ないテストは緑のままになる。[根拠 `orchestrator/campaign/env_contract.py:283-318`; `orchestrator/tests/test_env_contract.py:410-483`; `/work/1/SFC/tanab/dev-wave-jobs/t419-u2-contract-generation/s4-adjudication.md:73-84`] [提案] 構造・連番・隣接検査を fuse なしの内部 validator として分離し、その受理集合を直接検査する。少なくとも M1 は spy で `is_valid_successor` の呼出しを確認し、list 負例は空 list ではなく有効な `GenerationEntry` を1件入れて tuple 型だけを狙う。

[severity: should-fix] [攻撃シナリオ] M6 の duplicate fixture も hash 一意性検査だけに帰属しない。同じ contract を g1/g2 に置いた入力は、一意性検査を削除しても no-op successor として隣接検査に拒否されるため、現在のテストは error message の変化で赤になる。さらに production は各 env が1世代で、canonical preimage に `env_tag` を含むため、異なる env 間の重複は通常の source drift では作れず、実効上は SHA-256 collision guard である。[根拠 `orchestrator/campaign/env_contract.py:97-102,145-160,297-318`; `orchestrator/tests/test_env_contract.py:444-466`] [提案] 異なる env_tag の一世代列を2本作り、`contract_sha256` を同じ値へ差し替える collision seam で検査する。そうしないなら M6 の単一理由性を取り下げ、「production では collision 時だけ発火」と明記する。

[severity: should-fix] [攻撃シナリオ] g2 を `_build_registry` に直接追加すれば、現行コードは top-level の `validate_generations(GENERATIONS)` から fuse に到達し、index/`REGISTRY` 構築前の import 時点で確かに落ちる。しかし、この top-level 呼出し自体を削除する変異を検出するテストがない。全 validator test は純関数を直接呼び、production data は全列長1なので、行339の削除だけなら静的には既存テストの観測値を変えない。[根拠 `orchestrator/campaign/env_contract.py:314-344`; `orchestrator/tests/test_env_contract.py:402-538`] [提案] module-level の `validate_generations(GENERATIONS)` が index/`REGISTRY` より前に存在することを AST で固定し、その結線削除も変異事前登録へ追加する。

[severity: nit] [攻撃シナリオ] fuse は runtime authority ではない。`_build_contract_sha256_index` は未検証の二世代 mapping も受け入れ、既存テスト自身が `_CONTRACT_SHA256_INDEX` を再束縛して public resolver に見せている。successor hash を渡せば、fuse を通していない g2 も解決可能になる。さらに Python module 属性なので `REGISTRY`/`GENERATIONS` 自体の再束縛も構文上は可能である。ただし index seam は `lookup()` の current viewを変えず、resolver の production consumer は現時点で0件なので、certified activation の迂回にはなっていない。[根拠 `orchestrator/campaign/env_contract.py:321-372`; `orchestrator/tests/test_env_contract.py:512-538`; `/work/1/SFC/tanab/dev-wave-jobs/t419-u2-contract-generation/s4-adjudication.md:100-103`] [提案] fuse を「source bootstrap の防壁」と限定して記述する。resolver を production 結線する wave では、再束縛可能な global index を authority として扱わない。

[severity: nit] [攻撃シナリオ] 「env 固有の**値**が `_build_registry` 外に存在しない」と広く主張すると偽になる。g1 の contract hash は `_CONTRACT_SHA256_INDEX` の key として計算・保持され、contract 自体も `REGISTRY` に再投影される。一方、2100/1800、calibration path、calibration SHA の production literal は実際に `_build_registry` 内だけで、外部に独立 hardcode はない。AST 実装も計算・連結値は保証外だと明記しているため、「literal の不在」という狭い保証なら成立する。[根拠 `orchestrator/campaign/env_contract.py:231-275,321-344,404-417`] [提案] 文言を常に「env 固有 literal の単一定義」に限定し、derived index/value の不存在まで保証したと表現しない。

## 変異事前登録 M1〜M7

| ID | 赤になる実在テスト | 静的判定 |
|---|---|---|
| M1 | `test_validate_generations_synthetic_two_generation_negative_table` の `invalid-successor` | **形式上 KILLED、帰属不成立。** 呼出し削除後も fuse が同じ入力を拒否し、message 不一致で赤になる。 |
| M2 | `test_is_valid_successor_leaf_pointer_table` の `attestation-mode` | **KILLED。** `/attestation_mode` を許可すると predicate が直接 `True` になる。 |
| M3 | 同テストの `sha-only` / `path-only` | **KILLED。** 対条件削除に直接帰属する。 |
| M4 | `test_validate_generations_valid_two_generation_reaches_bootstrap_fuse` | **KILLED。** fuse 削除後は有効な二世代列が例外なしで返る。 |
| M5 | `test_resolver_synthetic_index_resolves_non_current_generation` | **KILLED。** current-only index では g1 hash が未知になり、狙った解決が失敗する。 |
| M6 | `test_validate_generations_synthetic_two_generation_negative_table` の `duplicate-hash` | **形式上 KILLED、帰属不成立。** 一意性検査削除後も隣接 no-op 検査が拒否する。 |
| M7 | `test_generation_golden_has_exact_keys_nonempty_columns_and_g1_hashes` | **KILLED。** 実値との tuple 不一致に直接帰属する。`test_resolve_by_contract_sha256_resolves_all_g1_hashes` も共有 golden の未知 hash で赤になる。 |

M2 の `attestation-mode` successor は、base が既に `single_process=True` なので contract の `__post_init__` を通る。`clocks_per_us=1001`、path/SHA 負例も型・値域を満たしており、predicate より前の dataclass 検査で落ちてはいない。[根拠 `orchestrator/tests/test_env_contract.py:105-130,366-399`; `orchestrator/campaign/env_contract.py:104-143`]

## 不変性と既存検出力

- `ExecutionEnvironmentContract`、`_canonical_obj()`、canonical JSON 手順は変更されていない。g1 field 値も同一で、linux-baremetal `1b2ee853…`、Pegasus `e576e9cd…` の独立 golden は維持されている。[根拠 `orchestrator/campaign/env_contract.py:82-160,237-274`; `orchestrator/tests/test_env_contract.py:960-1032`]
- `REGISTRY` は `sequence[-1].contract` をコピーせず参照するため、`lookup()` の返り値は以前と同じ exact `ExecutionEnvironmentContract` であり、`GENERATIONS` 内 contract とも `is` 同一である。型・dataclass equality/hash も変わらない。[根拠 `orchestrator/campaign/env_contract.py:163-179,336-344,375-382`; `orchestrator/tests/test_env_contract.py:359-363`]
- 既存テストの削除・緩和はない。`KNOWN_SELF_INCONSISTENT_CALIBRATIONS`、`LEGACY_CALIBRATION_ALLOWLIST`、`checked_entries == 2`、`required_entries == 1`、env-literal AST 検査、canonical JSON golden はすべて残っている。fuse により現在の `REGISTRY` が従来と同じ二つの g1 contract なので、現時点で意味も変わらない。[根拠 `orchestrator/tests/test_env_contract.py:54-75,734-820,980-1032,1070-1127`]
- production の隣接検査は `zip(sequence, sequence[1:])` が空で一度も発火しない。連番検査は各列の g1 が `generation == 1` であることだけは検査するが、gap は synthetic 入力だけである。この制限自体は裁定とテスト docstring に明記され、隠された保証にはなっていない。[根拠 `orchestrator/campaign/env_contract.py:288-318`; `orchestrator/tests/test_env_contract.py:422-423`; `/work/1/SFC/tanab/dev-wave-jobs/t419-u2-contract-generation/s4-adjudication.md:100-103`]

## 総括

- 最重は M1 と連番負例が fuse の別拒否で赤になるだけで、狙った検査の受理集合を固定していないこと。
- 次に M6 は no-op 隣接拒否に重なり、裁定が要求した単一理由性を満たさない。
- 第三に top-level `validate_generations(GENERATIONS)` の削除を kill するテストがなく、import fuse の結線が未固定である。
- 一方、現行コードへ直接 g2 を足せば import は確実に失敗し、g1 hash・`lookup()` の型と同一性・既存テストの検出力は維持されている。