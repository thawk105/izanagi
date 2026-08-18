## 所見

- [RA-1] 主張: 通常の `Exception` はクラッシュ処理へ届かず、`partial` として成功系に残る。根拠: [p3_autonomous_workload_trial.py:2663](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-s8c-c12-c04-c11/orchestrator/campaign/p3_autonomous_workload_trial.py:2663)、[p3_autonomous_workload_trial.py:2791](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-s8c-c12-c04-c11/orchestrator/campaign/p3_autonomous_workload_trial.py:2791)。影響: `report.status` と terminal ledger が `partial` となり、indeterminate、残存セル、原因記録が不一致になる。現行の certified 選択は非認証 producer のため増えないが、レポートと台帳の値は変わる。最小の是正: 実験全体のクラッシュを `_finish_trial` から再送出して helper へ通すか、C04 の対象をセル内エラー除外として明文化し machine proof も狭める。自信度: 高。

- [RA-2] 主張: 元例外の再送出は `finally` の provider close 例外で上書きされ得る。根拠: [p3_autonomous_workload_trial.py:2093](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-s8c-c12-c04-c11/orchestrator/campaign/p3_autonomous_workload_trial.py:2093)、[p3_autonomous_workload_trial.py:3898](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-s8c-c12-c04-c11/orchestrator/campaign/p3_autonomous_workload_trial.py:3898)。影響: caller が見る例外型、note、trace が元原因でなくなり、クラッシュ報告の参照が変わる。最小の是正: close 失敗を副次障害として原因へ note 記録し、元例外を優先して再送出する。自信度: 高。

- [RA-3] 主張: `do_build=False` と caller 提供 `drive` の組み合わせでは、実際の site が Pegasus でも予約検査を回避できる。根拠: [p3_autonomous_workload_trial.py:2167](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-s8c-c12-c04-c11/orchestrator/campaign/p3_autonomous_workload_trial.py:2167)、[p3_autonomous_workload_trial.py:3663](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-s8c-c12-c04-c11/orchestrator/campaign/p3_autonomous_workload_trial.py:3663)、[p3_autonomous_workload_trial.py:2994](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-s8c-c12-c04-c11/orchestrator/campaign/p3_autonomous_workload_trial.py:2994)。影響: 未予約の compute が実行され、raw report や campaign artifact が汚染され得る。最小の是正: 実行 site を `do_build` と独立に確定して検査するか、予約必須 site で caller 提供 drive を拒否し、`do_build=False` を実行不能な dry path に限定する。自信度: 中から高。

- [RA-4] 主張: C04 の machine evaluator は予約済み trial の `reject_started_trial` 到達性を検査していない。根拠: [s8c_preregistration_evidence.py:1611](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-s8c-c12-c04-c11/orchestrator/campaign/s8c_preregistration_evidence.py:1611)、[test_s8c_preregistration_invariant.py:71](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-s8c-c12-c04-c11/orchestrator/tests/test_s8c_preregistration_invariant.py:71)。影響: preflight の重複拒否呼び出しを削除しても machine report の状態と proof reference が変わらず、C04 の受理根拠が過大になる。最小の是正: evaluator の reachable target と、削除時に `UNSATISFIED` となる負の対照を追加する。自信度: 高。

- [RA-5] 主張: `restart_forbidden` は設定されるだけで production code の拒否判定に使われない。nit。根拠: [trial_registry.py:1946](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-s8c-c12-c04-c11/orchestrator/campaign/trial_registry.py:1946)、[trial_registry.py:1965](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-s8c-c12-c04-c11/orchestrator/campaign/trial_registry.py:1965)。影響: 現在は start row 検査が拒否するため、現行の受理集合、レポート、台帳値は変わらない。最小の是正: 実際の再実行拒否 consumer を追加するか、flag を保証として主張しない。自信度: 高。

- [RA-6] 主張: note 付与自体が失敗すると、`raise cause` まで到達せず元例外を失う入力がある。根拠: [p3_autonomous_workload_trial.py:3463](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-s8c-c12-c04-c11/orchestrator/campaign/p3_autonomous_workload_trial.py:3463)、[p3_autonomous_workload_trial.py:3474](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-s8c-c12-c04-c11/orchestrator/campaign/p3_autonomous_workload_trial.py:3474)。影響: 特殊な `BaseException` で `TypeError` 等に置換され、原因参照が変わる。最小の是正: note 付与を二重に保護し、付与失敗後も必ず元例外を再送出する。自信度: 中。

## 殺せない変異

- `M-C12-registered-order`: 予約検査を `record_trial_start_once` 後へ移す変異。追加の予約拒否テストは exploratory で lifecycle token が無く、開始 row 不在を検査しないため生存する。
- `M-C04-post-start-handler-removed`: 実行開始後の `except BaseException` から `mark_experiment_indeterminate` を削除する変異。追加 crash テストは namespace failure による最初の handler だけを通り、後段 handler を実行しない。
- `M-C04-body-noop-static`: helper 本体を no-op にしても、現行 library evaluator は symbol と到達性だけを見て `EVIDENCE_UNDEFINED` のままになる。runtime テストでは検出できるが、判定器単独では生存する。
- `M10` は残時間の負例だけなら API の `required_s` 検査でも赤くなり得るが、追加された有効予約の p2 正例があるため全体では生存変異とは判定しない。

## 総括

予約検査の job、boot、残時間の拒否経路は例外握り潰しなしで発火する。  
一方、通常の workload 例外は `partial` 化され、C04 の indeterminate 保証を迂回する。  
provider close と note 付与にも元例外を隠す経路が残る。  
予約 gate の実行順と C04 evaluator の検出力には、明確な生存変異がある。  
pytest は依頼指示どおり実行しておらず、以上はコードと静的なテスト形状に基づく判定である。