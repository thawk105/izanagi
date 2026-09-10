## 前の子の実装で確かめたこと・食い違い

残存実装について、親の確認内容はすべて現物と一致しました。

- notes regex と helper は除去済み。
- observation は exact 7-key、`_derive_rep_integrity()` は 4 値返却。
- resume gate は top-level `exec_failures` を再導出値と照合。
- terminal 本数式、矛盾条件、`None` padding、全 callsite の arity は追随済み。
- `FORMULA_ID` は `s8b-floor-stats/v2` のままです。

食い違いは B6 test の「全 producer outcome class」という主張です。実際の runner が生成できる post-spawn parse failure を列挙していませんでした。子 1 の「全 outcomes」test にも同じ抜けがあります。

## 仕上げた箇所 (file:line)

[test_s8b_floor_stats.py:311](/work/1/SFC/tanab/izanagi/.codex/worktrees/t1851-c2-s2/orchestrator/tests/test_s8b_floor_stats.py:311)

- `execution_exception` を pre-spawn と post-spawn に分離。
- post-spawn class を全 rep 組合せへ追加。
- execution failure 集計を両 exception class に追随。

B6 停止条件が成立したため、production file は追加変更していません。所有 6 file はすべて構文検査 OK、U+0300〜U+036F は 0 件です。

## B6 — FORMULA_ID gate の判定と網羅の根拠

判定は不一致です。`FORMULA_ID` 据え置きを証明できません。

実際の `measure_point()` を通した producer probe で、subprocess が rc=0 で終了した後に stdout parsing が失敗すると、次の observation が生成されました。

- `returncode=0`
- `execution_failure=True`
- `throughput=None`
- no-perf counter は `not_required`
- exact 7-key

この入力に対する改訂前後は次のとおりです。

| 値 | 改訂前 | 改訂後 |
|---|---:|---:|
| `exec_failures` | 1 | 1 |
| `rep_integrity_failures` | 0 | 1 |
| qualified throughputs | 同一 | 同一 |
| session median | `None` | `None` |

旧式は rc=0 と完備 counter だけで rep を complete とし、throughput が `None` でも integrity failure に数えません。改訂後は `execution_failure is False` が必要なため 1 件になります。

更新した B6 test は no-perf 5 class、perf 6 classの 3-rep 直積を検査しますが、post-spawn class を含む最初の反例で失敗します。一例を発見した時点で停止する指示のため、同値性の全域証明は成立していません。

`FORMULA_ID` は変更していません。凍結成果物再発行を含む親裁定が必要です。

## B7 — 旧 6-key の負例

次の負例が既にあり、直接実行で PASS しました。

- [test_s8b_floor_stats.py:1757](/work/1/SFC/tanab/izanagi/.codex/worktrees/t1851-c2-s2/orchestrator/tests/test_s8b_floor_stats.py:1757): verifier が旧 6-key を exact-key 不一致で拒否。
- [test_s8b_floor_campaign.py:1676](/work/1/SFC/tanab/izanagi/.codex/worktrees/t1851-c2-s2/orchestrator/tests/test_s8b_floor_campaign.py:1676): resume journal の旧 6-key を fail-closed で拒否。

resume の top-level `exec_failures` 不一致負例も PASS しました。

## 実走した nodeid と結果

- `test_s8b_floor_stats.py::test_formula_v2_outputs_are_unchanged_for_every_producer_outcome_class`
  - FAIL、B6 の `rep_integrity_failures` 不一致。
- `test_s8b_floor_stats.py::test_old_six_key_rep_observation_is_rejected`
  - PASS。
- `test_s8b_floor_campaign.py::test_resume_rejects_exec_failure_count_mismatch`
  - PASS。
- `test_s8b_floor_campaign.py::test_resume_rejects_old_six_key_rep_observation`
  - PASS。
- `test_s8b_terminal_evidence.py::*`
  - 76 passed in 0.52s。

指定どおりの直接実行結果:

- `python3 test_s8b_floor_stats.py`: rc=0、ただし `__main__` harness がなく収集 0。緑とは数えません。
- `python3 test_s8b_floor_campaign.py`: 同上。
- `python3 test_s8b_terminal_evidence.py`: 76 passed。

Growth hold は発生しませんでした。

## 期待どおりの赤 (所有外由来)

B6 で停止したため、所有外 fixture を含む広域走は実行していません。したがって所有外由来の赤を実測済みとはしません。

静的に予想される赤は、旧 6-key literal を持つ以下の系列です。

- `s8b_v2_freeze_fixture.py` 由来の holdout / oracle
- `test_s8b_attempt_registry.py`
- `test_s8b_floor_attempt_launcher.py`
- `test_s8b_ratified_freeze.py`
- `test_s8b_ratified_verify.py`

## 所有外への波及可能性 (静的列挙)

- `FORMULA_ID` 改版時は `s8b_floor_contract.py` と凍結 `floor_protocol.json` の bytes、固定 digestへ波及。
- 旧 journal は resume gate で前向きに拒否。
- 子 3 所有の 6-key fixture/test は 7-key 追随が必要。
- `pipeline.py` は subset consumer であり、余分な key 自体では壊れない想定ですが、B5 の固定は子 3 の責務です。
- post-spawn parse/open failure は direct と capture の両 runner 面で生成可能です。

全 `_derive_rep_integrity()` production callsite は次の 4 件で、すべて 4 値へ追随済みです。

- stats verifier
- campaign resume
- terminal snapshot
- terminal source throughput

## 総括

B7、resume count gate、全 callsite 追随は実装済みです。しかし B6 は actual producer input で反例が成立し、`rep_integrity_failures` が改訂前後で変わります。

指示に従って実装を停止し、`FORMULA_ID` と凍結成果物には触れていません。現状は「実装済みだが B6 不成立」であり、closed ではありません。