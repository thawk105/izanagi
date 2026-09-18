## 変更 file 一覧

- `orchestrator/tests/test_mocc_mutation_proof.py`
- `orchestrator/campaign/s3_mocc_mutation_proof.py`

## 所見ごとの是正内容

- **A1/B1:** `_source_root` を呼出しごとの system tmp に変更。共有 scratch・所有権判定・共有親の削除を除去しました。archive／init／apply 手順は維持しています。
- **A2:** `_run_checked` の許容 rc を広げ、終了状態と実 rc を保存してから異常 rc を拒否します。rc=2／-15 の記録と matrix 拒否を検査しました。verifier の mock は `M._run_checked` に限定し、timeout・起動失敗の区別を維持しています。
- **B5:** 両 process record に monotonic 差の `wall_seconds` を追加。初期値は `None`。field の有無・値で合成 baseline の判定が変わらないことを確認しました。

## 実走した検査

指定の自走 harness で実施しました。

| nodeid／範囲 | 結果 |
|---|---|
| `test_mocc_mutation_proof.py::test_*` 全11件 | 10 passed、1 failed |
| 同 `::test_mocc_mutation_verify_binds_protocol_root_and_timeout` | PASS（rc=2／-15 を含む） |
| 同 `::test_mocc_mutation_run_records_failure_and_timeout` | PASS |
| 同 `::test_mocc_mutation_checks_are_input_derived` | PASS |
| `test_mocc_proof_surface.py::test_*` 全18件 | 18 passed |
| 指定 import 確認 | `True 36` |
| `git diff --check` | PASS |

赤は `test_mocc_mutation_proof_json_is_complete_and_bound` の新 JSON 不在による `FileNotFoundError` だけです。期待値変更・skip 化はありません。

並列競合対策は**実装済み・xdist 並列では未実走**です。36走・新 JSON 生成・受入全走も未実走です。

## 波及の静的列挙

- 直接 subprocess site は `_run_trace` の1箇所。登録簿 Counter の変更は不要で、既存 pin **35／39／25／25** を維持。
- `_DEFERRED_GATE_MEMBERS` は変更対象ファイルを参照しておらず、lineno 更新不要。
- `acceptance_duration_ledger` に対象 node の登録はなく、今回も変更なし。局所 `wall_seconds` との連携は追加していません。
- nodeid と `_run()` harness は維持。plain-runner allowlist の変更不要。
- 旧14 check・旧4 patch・旧3負例 witness の受理・拒否挙動は不変。旧回帰は全件通過しました。

## 総括

must-fix 2件と should 1件を修正しました。repo 内 scratch は存在せず、commit は作成していません。

最終 `git status --short` は所有2ファイルの M だけです。

```text
 M orchestrator/campaign/s3_mocc_mutation_proof.py
 M orchestrator/tests/test_mocc_mutation_proof.py
```