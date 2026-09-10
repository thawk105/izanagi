## 実装

- [s8b_verdict.py](/work/1/SFC/tanab/izanagi/.codex/worktrees/t2067a-v/orchestrator/campaign/s8b_verdict.py:829): ratified freeze の load 直後、historical reverify 前に選択 identity 強制を追加。
- 外部 `--freeze` の byte/hash load は従来どおり先行。
- `RatifiedFreezeError` は既存 catch 対象だったため変更不要。
- [test_s8b_verdict.py](/work/1/SFC/tanab/izanagi/.codex/worktrees/t2067a-v/orchestrator/tests/test_s8b_verdict.py:1001): 実 g1、走査中立な earlier result、記録 stub を追加。

## テスト

追加・拡張した nodeid は次の3件です。

- `test_verdict_cli_real_g1_rule_mismatch_preserves_selection_reason`
  - `build_production_emitter_g1` の実 g1を使用。
  - earlier bytes は `b"{}"`。
  - 実選択強制による rc=2、`floor-selection-rule-mismatch`、規則名を固定。
- `test_verdict_cli_valid_real_g1_reaches_reverify_after_actual_selection_gate`
  - 無変異の実 g1で実強制本体を通し、後段 reverify sentinel への到達を固定。
- `test_cli_preserves_freeze_and_floor_source_wiring`
  - `freeze → ratified → selection → reverify` の順序、object 同一性、Path 完全一致を固定。

## 既存テストの扱い

- `test_cli_rejects_non_verdict_oracle_schema_without_output`
- `test_cli_rejects_freeze_identity_mismatch_before_consumers`

両方とも loader が返す `loaded_ratified` を保存し、選択 assert を次の記録 stub にしました。

```python
lambda candidate, candidate_root: selection_calls.append(
    (candidate, candidate_root)
)
```

各テストで以下を照合しています。

```python
selection_calls == [(loaded_ratified, cli_root)]
selection_calls[0][0] is loaded_ratified
type(selection_calls[0][1]) is type(cli_root)
selection_calls[0][1] == cli_root
```

wiring test も同じ記録方式を選択しました。このテストは全 authority I/O を synthetic seam で検査する配線テストであり、実強制本体は新しい実 g1正例・負例が担当するためです。

## 単一帰属の確認

強制行を一時削除し、負例 node を runner へ投入しました。しかし `qstat -Q` が `NQSconnect ... Can't create socket (errno: 1)` となり、rc=16、child未起動でした。

したがって、強制行削除時の rc=0受理は実測確認できていません。強制行は直後に復元済みです。負例では downstream seam を実 historical reverify より後ろだけに置いていますが、裁定が要求する実測証明には数えていません。

## 実走

期待する赤集合は、強制行削除変異時の負例 node 1件だけです。restored 実装では期待赤はありません。verdict は generator source 外なので pin test の赤も期待しません。

実行を試みた範囲:

- 新規・変更した5 nodeidの焦点走: rc=16、child未起動。
- `test_s8b_verdict.py` の collect-only: rc=16、child未起動。
- 強制行削除中の負例単独走: rc=16、child未起動。
- 2ファイルの AST parse: 成功。
- `git diff --check`: 成功。

結論は「実装済み・未実走」です。

## 波及

- `s8b_verdict.main()` の repo 内直接 caller は所有 test file 内のみ。
- 共有 fixture `test_s8b_ratified_freeze.py` と `s8b_holdout_freeze.py` は読み取り利用のみ。
- `test_real_repo_serialization.py` は親の焦点走対象だが、裁定どおり新規登録は不要。
- `test_s8b_oracle_manifest.py` の再 pin は不要。verdict source は `_GENERATOR_SOURCES` 外。
- official-perf closure、manifest consumer inventory、artifact schema test は静的には変更対象外。

## 総括

選択強制と所定の実 g1テスト、既存偽陽性対策を実装しました。  
所有外ファイルは編集していません。  
Pegasus dispatch が起動不能なため、必須の単一帰属実測は未確認です。  
強制行は復元済みで、現在の変更は所有2ファイルだけです。