## 変更点

指定 2 file のみ、119 行追加。commit・既存期待値の変更なし。

`orchestrator/campaign/reflux_formal_consumer.py`（23 行追加）には、裁定 §2 と逐語一致する helper を追加しました。

```python
def _wal_terminal_shape_valid(records: Sequence[dict]) -> bool:
    terminal = records[-1]
    if {"variant", "stage", "env_tag", "ts", "payload"} != set(terminal):
        return False
    if type(terminal["variant"]) is not str:
        return False
    if type(terminal["env_tag"]) is not str:
        return False
    terminal_ts = terminal["ts"]
    if type(terminal_ts) not in (int, float):
        return False
    if type(terminal_ts) is float and not math.isfinite(terminal_ts):
        return False
    if type(terminal["payload"]) is not dict:
        return False
    terminal_count = sum(
        record.get("stage") in (STAGE_COMMIT, STAGE_ABORT)
        for record in records
    )
    return terminal_count == 1
```

指定位置へ次の 1 行を追加。helper と呼出しを除く consumer 全文は HEAD と一致しました。

```python
_require(FormalReasonCode.FC07, _wal_terminal_shape_valid(wal_records))
```

`orchestrator/tests/test_reflux_formal_consumer.py`（96 行追加）には次を追加しました。

| test 名 | node 数 |
|---|---:|
| `test_fc07_rejects_terminal_root_attempt_shadow` | 1 |
| `test_fc07_rejects_terminal_extra_root_key` | 1 |
| `test_fc07_rejects_terminal_missing_root_key` | 3 |
| `test_fc07_rejects_terminal_invalid_outer_type` | 4 |
| `test_fc07_rejects_payload_only_terminal_stage` | 1 |
| `test_fc07_rejects_duplicate_abort_terminals` | 1 |
| `test_fc07_rejects_commit_before_abort_terminal` | 1 |
| `test_fc07_accepts_float_timestamp_abort_terminal_shape` | 1 |
| `test_fc07_accepts_nonterminal_extra_root_key` | 1 |

合計 9 関数・14 node（負例 12、正例 2）。すべて手順 R を使用し、parametrize id は指定どおり ASCII。既存関数・クラスの AST 不変も確認しました。

## anchor 一意性

consumer 全文の文字列出現回数を検査しました。

| 変異 | `old` | 回数 |
|---|---|---:|
| M01 | `_require(FormalReasonCode.FC07, terminal.get("stage") == STAGE_ABORT)` | 1 |
| M02 | `_require(FormalReasonCode.FC07, _wal_terminal_shape_valid(wal_records))`／M01 の `old` | 各 1 |
| M03 | `if {"variant", "stage", "env_tag", "ts", "payload"} != set(terminal):` | 1 |
| M04 | `if type(terminal_ts) not in (int, float):` | 1 |
| M05 | `return terminal_count == 1` | 1 |
| M06 | `_require(FormalReasonCode.FC07, _wal_terminal_shape_valid(wal_records))` | 1 |
| M07 | `if type(terminal["variant"]) is not str:` | 1 |
| M08 | `if type(terminal["env_tag"]) is not str:` | 1 |
| M09 | `if type(terminal_ts) not in (int, float):` | 1 |

## 受理・拒否の含意

**scope 前：** 上流と既存 outcome 判定を満たせば、余分・欠落 outer key、root attempt shadow、不正な outer 型、先行 terminal を含む projection が FC07 を通り得ました。末尾 root stage の不一致や既存 payload 条件違反は拒否していました。

**scope 後：** 末尾の exact 5 key・指定型・有限 timestamp と、projection 内の root commit／abort が計 1 件であることを要求します。これらの違反を FC07 で拒否し、非 terminal の余分 key と terminal payload の追加 key は今回の gate では拒否しません。

正例は既存 production commit 形（`ts=0`、payload に attempt と `verify_configs=["legacy","s2"]`）。既存判定上の到達先は引き続き `P6Unavailable` です。

## 波及の静的列挙

- `_validate_wal_outcomes` の caller は `evaluate_formal_origin` の 1 箇所。既存の evidence 解決・bijection・topology 検査後という順序は不変です。
- 共有 fixture builder の `_wal_records` は trigger＋abort の 2 record。末尾は exact 5 key、文字列 variant／env_tag、整数 timestamp、dict payload、terminal 計 1 件で gate を満たします。
- `test_p3_autonomous_workload_trial` は共有 fixture の WAL bytes と records を保ったまま参照先を移設しており、新 gate 違反を追加しません。
- `test_trial_registry` は projection 値の構築・検査、`test_reflux_origin_client` は共有 fixture と typed decision／receipt を使用しており、新 gate に入る不正 record は静的調査で認めませんでした。
- `test_reflux_originless_compatibility` の origin 有効側は上記 p3 fixture 経路、originless 側は FC07 の対象外です。
- `test_reflux_campaign_issuer` の二重 abort 例は `result_evidence_context=None` の originless 経路です。FC07 入力として新たに落ちる record は認めませんでした。
- 制約検査を探索し、対象 test 本数を固定する meta-test は見つかりませんでした。構造検査の 15 production file 目録は不変で、helper に禁止構文・定義はありません。
- duration ledger の新 node 未登録は既存 allocator が重み 1 秒で扱います。所有外の目録更新は不要です。

以上は静的確認であり、回帰実走の代替ではありません。

## 実走

**実装済み・未実走。**

試行範囲：

```text
python3 tools/run_tests.py --force-dispatch orchestrator/tests/test_reflux_formal_consumer.py -q -rf
```

`qstat -Q preflight rc=1` により dispatch が rc=16 で終了し、`child_started=false`。実走できた nodeid はありません。runner が生成した一時成果物は除去しました。

静的には、両 file の構文解析、逐語・anchor・既存 AST 不変検査、`git diff --check` を通過しました。親の計算ノードによる 12 file 焦点走は未実施です。

## 総括

指定の exact gate と 9 関数・14 node を実装しました。
変更は所有する 2 file の追加差分のみです。
逐語一致・anchor 一意性・構造制約を静的確認しました。
pytest は dispatch preflight 失敗で未起動のため、完了判定は保留です。
