静的焦点再レビューの判定は **GO** です。pytest・変異は実走しておらず、緑や KILLED の実測は主張しません。

## 総括

### 残存 must-fix の数値追跡

M07 で [cli.py:551](/work/1/SFC/tanab/izanagi/.claude/worktrees/wave-t419-attestation-clock/orchestrator/calibrator/cli.py:551) を `5.0` に固定すると、fixture の標本 `[2390.0, 2410.0]` の中央値は `2400.0`、最大偏差は `10.0` です。

- 5% の許容差: `120.0` → self-comparison は pass
- 2% の許容差: `48.0` → pass
- 7.5% の許容差: `180.0` → pass

したがって mutation 後も [test_calibrator_certify.py:626](/work/1/SFC/tanab/izanagi/.claude/worktrees/wave-t419-attestation-clock/orchestrator/tests/test_calibrator_certify.py:626) の `rc == 0` は維持され、別理由で先に赤くなりません。artifact には `5.0` が保存され、次の assert が最初に落ちます。

| node | 落ちる assert | 比較 |
|---|---|---|
| `test_cli_artifact_preserves_effective_clock_tolerance_argument[pegasus-2pct]` | [test_calibrator_certify.py:631](/work/1/SFC/tanab/izanagi/.claude/worktrees/wave-t419-attestation-clock/orchestrator/tests/test_calibrator_certify.py:631) | `5.0 == 2.0` → false |
| `test_cli_artifact_preserves_effective_clock_tolerance_argument[nondefault-7_5pct]` | 同上 | `5.0 == 7.5` → false |

最初の assert を除いても、registered artifact の [line 636](/work/1/SFC/tanab/izanagi/.claude/worktrees/wave-t419-attestation-clock/orchestrator/tests/test_calibrator_certify.py:636) が同じ比較で落ちます。

### closed / partial / regressed

| 所見 | 判定 | 根拠 |
|---|---|---|
| 残存 must-fix: tolerance の `5.0` 固定化が生存 | **closed** | 上記 2 node がともに line 631 で赤くなる |
| `_invoke` の既存 caller への回帰 | **closed** | 新引数は keyword-only・既定値 `"5"`。旧 literal `"5"` と現在の `str("5")` は同一 argv。静的集計で既存 15 関数・23 node はすべて新引数を省略 |
| 既存テスト期待値の変更 | **closed** | snapshot と現在差分の照合では、既存 assert の変更・削除・緩和なし。fix2 は helper 2 箇所と新規テストの追加だけ |
| 新規 parametrize の恒真性 | **closed** | 期待値は出力ではなく独立した `[2.0, 7.5]`。fixture は tolerance `100.0` から始まり、CLI→parser→production 代入を通る。早期 reject は line 626、attempt 誤値は line 631、registered のみの誤値は line 636 が捕捉 |
| mutation spec の anchor/node | **closed** | 全指定 `old` が逐語で各 1 箇所。全 expected node の定義または明示 param ID が存在 |

`partial`・`regressed` はありません。成果物影響も閉じています。固定化を見逃した場合の Pegasus 入力 `2.0`→artifact `5.0` による serialized hash／登録名、runtime receipt の受理集合、certified 選択・材料レポート・台帳参照の変化を、M07 が検出します。

### 変異 spec anchor

| ID | anchor 開始位置 | 出現数 |
|---|---|---:|
| M01 | [cli.py:608](/work/1/SFC/tanab/izanagi/.claude/worktrees/wave-t419-attestation-clock/orchestrator/calibrator/cli.py:608) | 1 |
| M02 | [execution_guard.py:196](/work/1/SFC/tanab/izanagi/.claude/worktrees/wave-t419-attestation-clock/orchestrator/campaign/execution_guard.py:196) | 1 |
| M04 | [execution_guard.py:183](/work/1/SFC/tanab/izanagi/.claude/worktrees/wave-t419-attestation-clock/orchestrator/campaign/execution_guard.py:183) | 1 |
| M05 | [execution_guard.py:194](/work/1/SFC/tanab/izanagi/.claude/worktrees/wave-t419-attestation-clock/orchestrator/campaign/execution_guard.py:194) | 1 |
| M06 | [cli.py:608](/work/1/SFC/tanab/izanagi/.claude/worktrees/wave-t419-attestation-clock/orchestrator/calibrator/cli.py:608) | 1 |
| M07 | [cli.py:551](/work/1/SFC/tanab/izanagi/.claude/worktrees/wave-t419-attestation-clock/orchestrator/calibrator/cli.py:551) | 1 |

Expected node の基底関数はそれぞれ [test_calibrator_certify.py:531](/work/1/SFC/tanab/izanagi/.claude/worktrees/wave-t419-attestation-clock/orchestrator/tests/test_calibrator_certify.py:531)、[test_execution_guard.py:360](/work/1/SFC/tanab/izanagi/.claude/worktrees/wave-t419-attestation-clock/orchestrator/tests/test_execution_guard.py:360)、[test_env_contract.py:436](/work/1/SFC/tanab/izanagi/.claude/worktrees/wave-t419-attestation-clock/orchestrator/tests/test_env_contract.py:436)、[test_calibrator_certify.py:580](/work/1/SFC/tanab/izanagi/.claude/worktrees/wave-t419-attestation-clock/orchestrator/tests/test_calibrator_certify.py:580) に存在します。M07 の関数は [line 618](/work/1/SFC/tanab/izanagi/.claude/worktrees/wave-t419-attestation-clock/orchestrator/tests/test_calibrator_certify.py:618)、両 ID は [line 616](/work/1/SFC/tanab/izanagi/.claude/worktrees/wave-t419-attestation-clock/orchestrator/tests/test_calibrator_certify.py:616) に明示されています。

**回帰: なし。land 判定: GO（親による対象テスト・M07 を含む変異 matrix・受入の実走成功後に land 可）**。現時点では未実走のため、無条件のテスト成功とは扱いません。