## 総括

adapter の reserve・classify・observation-start の全 3 遷移を修正しました。  
検証済み evidence profile を各 core 遷移へ伝播し、plain v2 profile による再拒否を解消しています。  
新設 3 node を含む指定 4 harness は 809 passed、0 failed、3 skipped でした。  
編集は所有された 2 path のみで、git add・commit・docs 編集は行っていません。

## 原因の確定 (file:line、B の静的指摘の検算)

B の指摘どおりでした。

- `_load_attempt_registry_with_evidence_locked()` は evidence の digest・canonical bytes・binding・durable identity・issuer を検証し、`evidence_by_digest` を返しています。
  - `orchestrator/campaign/s8b_attempt_registry.py:1501-1579`
  - 同 `:1597-1613`
- `_atomic_update_locked()` は検証済み map を transition へ渡しています。
  - 同 `:2235-2245`
- 修正前の 3 transition はその map を `_evidence_by_digest` として捨て、plain v2 profile を core へ渡していました。
- core が既存 terminal 行を再検証すると plain profile の拒否 validator が発火し、次で停止していました。

```text
[s8b-v2-terminal] v2 terminal requires the sealed evidence API
```

## 直した 3 遷移 (reserve / classify / observation-start それぞれの file:line と、直したか否か)

| 遷移 | evidence profile 構築 | core への伝播 | 状態 |
|---|---:|---:|---|
| reserve | `s8b_attempt_registry.py:2557-2565` | `:2582-2585` | 修正済み |
| classify | `s8b_attempt_registry.py:2782-2790` | `:2841-2844` | 修正済み |
| observation-start | `s8b_attempt_registry.py:3034-3042` | `:3060-3063` | 修正済み |

3 遷移すべて修正済みで、未修正のものはありません。

## 受理集合を広げていないことの論証

- evidence は transition 前に従来どおり実 file から読み、digest、canonical bytes、expected binding、durable identity、external evidence を検証します。
- core へ渡す profile は `_terminal_validating_profile()` が生成し、terminal ごとに capability の存在、private issuer、sealed row 全項目の等値を再検査します。
  - `s8b_attempt_registry.py:1478-1498`
- plain profile の拒否 validator、型検査、例外処理は変更していません。
- candidate は transition 後にも `_load_attempt_registry_with_evidence_locked()` で再検証されます。
  - 同 `:2251-2261`
- 改竄 evidence は拒否され、plain profile も従来の exact error で拒否されることを負例で実測しました。

## 新設した test (nodeid / 正例は 2 件以上の連続 attempt / 負例 2 種)

- 正例  
  `test_s8b_attempt_registry.py::test_two_clean_v2_attempts_reserve_classify_and_begin_observation`
  - 実 admission marker capability と durable claim を使用。
  - planned clean attempt 2 件を同一 registry で連続処理。
  - 1 件目を sealed terminal にした後、2 件目も reserve・classify・observation-start まで到達。
  - 最終的に start 2、classification 2、observation-start 2、terminal 1 を確認。

- 負例 1  
  `test_s8b_attempt_registry.py::test_second_clean_reservation_rejects_tampered_terminal_evidence`
  - digest 名付き実 evidence file の bytes を改竄。
  - 2 件目の予約時に `terminal evidence bytes digest differs` で拒否し、registry 不変を確認。

- 負例 2  
  `test_s8b_attempt_registry.py::test_plain_v2_profile_rejects_transition_after_sealed_terminal`
  - 実 `core.reserve_attempt_slot()` に plain v2 profile を渡す変異を直接実行。
  - `[s8b-v2-terminal] v2 terminal requires the sealed evidence API` で拒否。

依存先の stub は使用していません。新設 3 node の個別実走は `3 passed, 0 failed` です。

## 実走結果 (command と passed/failed の実数)

```text
PYTHONPATH=. python3 orchestrator/tests/test_s8b_attempt_registry.py
152 passed, 0 failed
```

```text
PYTHONPATH=. python3 orchestrator/tests/test_s8b_terminal_evidence.py
79 passed, 0 failed
```

```text
PYTHONPATH=. python3 orchestrator/tests/test_s8b_floor_attempt_launcher.py
73 passed, 0 failed
```

```text
PYTHONPATH=. python3 orchestrator/tests/test_s8b_floor_campaign.py
505 passed, 0 failed, 3 skipped
```

対象 node の個別確認:

```text
PYTEST_ADDOPTS='-k test_v5_prefix_covers_every_consumed_non_competing_session' \
PYTHONPATH=. python3 orchestrator/tests/test_s8b_floor_campaign.py

1 passed, 0 failed, 507 deselected
```

`test_v5_prefix_covers_every_consumed_non_competing_session` は緑です。

## 残った懸念

- 本修正の主張範囲は指定された 3 遷移に限定しています。他の transition は変更していません。
- floor campaign の 3 skipped は pass として数えていません。
- `git diff --check` は成功し、差分は所有された 2 file だけです。