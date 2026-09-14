## consumer への波及

- [real] **例外処理中の attempt 終端記録が timeout すると、後続の lifecycle 後始末を飛ばす。** `p3_autonomous_workload_trial.py:5233` の `_record_attempt_terminal_for_run` は独立した捕捉がなく、失敗すると `:5238` の `mark_experiment_indeterminate` に届かない。初期化失敗側の `:5096` も同型。経路は同ファイル `:4494` → `trial_registry.py:3512` → `:3468` → `:2945`／`:2951` → `_git`。元の例外は context に残るが、表面の例外は timeout に置き換わる。**非 0 rc による `TrialRegistryError` でも既存の問題であり、この差分固有の新規退行ではない。** timeout が新しい発火条件になる。
- [real] 16 呼び出しすべてで、非 0 rc は従来から上位の例外に変換されていた。「返り値だけを扱うため、例外化で初めて契約が壊れる」直接 caller は無し。対象は `trial_registry.py:996,1160,1177,1189,1198,1214,1238,1303,1339,1358,2552,2569,2615,4592,5312,5351`。特に `:1303` の ancestry 判定では timeout が rc=1 相当の非祖先判定に化けず、`:1339` の blob 検査でも不存在扱いにならない。
- [real] `finally` 自体への新しい Git 呼び出し混入は無し。registry の FD 解放は `trial_registry.py:3051,4681,6492`、producer の context 復元・provider close は `p3_autonomous_workload_trial.py:5224,5257`。また `mark_experiment_indeterminate` 内では restart 禁止と terminal 記録を独立捕捉するため、ここまで到達すれば timeout でも両方を試す（同ファイル `:4571,4576`）。

## 既存テストへの波及

- [real] **keyword-only 追加による既存 monkeypatch の破損は無し。** `test_trial_registry.py:5239` の `fail_merge_base` と `:6657` の `fail_parent_query` は二引数のままだが、上記 production 16 箇所もすべて二引数。置換関数から元関数への委譲も二引数（同ファイル `:5242,6662`）。明示的な `timeout_s=` は追加正例 `:5262` に限定され、別テストの monkeypatch と併用されない。
- [real] 後始末の既存テストは関連するが、上記の二重失敗経路を直接証明しない。`test_p3_autonomous_workload_trial.py:9326` は **lifecycle** terminal 書込み失敗を注入するテストであり、先行する **attempt** terminal の Git timeout は注入しない。`:8672` は通常経路の attempt 終端失敗を扱う。追加 4 node も `_git` 単体なので、この consumer 経路は未検証。
- [疑い] その他の破損候補は後掲の参照先テスト群。実行していないため失敗の有無は未確認。単なる同名 helper や定数参照を timeout consumer とみなしてはいない（例：`test_holdout_observation.py:264` は定数比較）。

## spawn-site 登録簿

無し。

[real] `test_ccbench_spawn_sites.py:284` の `("campaign/trial_registry.py", "<module>._git"): 1` は静的に一致する。

- process API 集合が `subprocess.run` を含む（同ファイル `:292`）。
- 初期 scope は `<module>`（`:327`）、関数訪問で `_git` を追加する（`:347,369`）。
- process API の `Call` ごとに Counter を 1 増やす（`:378,386`）。
- `try/except` 専用の scope 変更はなく、通常の AST 再帰で訪問する。実装の該当 API は `trial_registry.py:975` の一つだけ。例外生成と `_git_env()` は process API ではない。追加既定値 `_GIT_TIMEOUT_S` も callable 注入に該当しない。

これは静的照合であり、登録簿テストの実走結果ではない。

## 所要

- [疑い] **追加 4 node の増分は通常環境で 1 秒前後〜数秒、計画上の余裕は合計 5 秒が妥当。確定上限ではない。** 正例は `exec sleep 2` により shell を置換し、約 0.25 秒で timeout する（`test_trial_registry.py:5255,5262`）。成功・非 0 rc shim は shell の `printf` と `exit` のみ（`:5274,5299`）。T4 は recorder で実 process を起動しない（`:5323,5328`）。
- [real] 追加 node に実 repo 初期化はなく、確認した autouse fixture も環境・module 状態の隔離である（`orchestrator/tests/conftest.py:239,750,766,779`）。ただし process 生成、共有 FS、collection の遅延は静的検査では上限を保証できない。探索した `orchestrator/conftest.py` とルート `conftest.py` は不在で未確認。
- [疑い] 5 秒なら 300 秒枠の約 1.7% の増分。ただし既存全走が枠内に収まるとは未確認。本番既定値 300 秒を消費する実 Git 停滞は、追加 shim の所要とは別である（`trial_registry.py:264,982`）。

## 記述の正確さ

- [real] `trial_registry.py:985` の文言は単一の **git command** の timeout と読め、全 trial の deadline 達成を主張していない。非 0 rc 側の `merge-base ... rc=...`（`:1310`）や `rev-list --parents failed`（`:1244`）とも区別できる。
- [real] **分類には十分だが、停止箇所の診断は弱い。** 全 16 箇所が同じメッセージになるため、例外文字列だけでは subcommand・repository・commit が分からない。`from exc` によって argv を持つ cause は保持するが、origin 境界は型名とメッセージを取り出す（`p3_autonomous_workload_trial.py:5306`）。文字列だけの報告では情報が落ちる。
- [real] 保証は一回の `subprocess.run` の timeout 設定まで。履歴反復（`trial_registry.py:2620,2626`）、flock（`:2964`）、通常 I/O、孫 process、trial 全体の上限は保証しない。attempt 予約（`p3_autonomous_workload_trial.py:4850`）も計時開始（`:5021`）より前。これらは裁定の記録要件と整合する（`verdict.md:75`）。

## scope 逸脱

無し。

[real] 提示 patch は `trial_registry.py:264,968` と `test_trial_registry.py:5249` からの追加 4 node のみ。他 module、watchdog、新しい gate・台帳、`max_wall_s` の変更は含まれない。裁定 `verdict.md:72` の範囲内である。

## 焦点走に入れるべき file

[real] production の `_git` symbol 検索と import／属性参照の追跡では、変更対象 helper の module 外直接利用は見つからなかった。例えば `paper_story_a1_source.py:61` は `patchharness._git`、`s8c_preregistration_evidence.py:706` は preregistration 側の helper であり別物。主要な波及は registry の関数と producer を介する。

以下はいずれも `orchestrator/tests/` 配下。参照根拠から選んだ候補であり、全件の焦点走所要は未計測。

| 優先 | file:line | 参照根拠 |
|---|---|---|
| 必須 | `test_trial_registry.py:5237` | `_git` の直接差替えと追加 4 node |
| 必須 | `test_p3_autonomous_workload_trial.py:8554` | formal reserve／terminal facade、後始末経路 |
| 必須 | `test_ccbench_spawn_sites.py:284` | `_git` の exact inventory |
| 次点 | `test_attempt_registry_core_equivalence.py:15` | registry facade を import |
| 次点 | `test_attempt_registry_core_s8b_profile.py:16` | registry facade を import |
| 次点 | `test_reflux_origin_binding.py:16,20` | producer と registry の両方を import |
| 次点 | `test_reflux_originless_compatibility.py:12,13` | producer と既存 producer テストを利用 |
| 次点 | `test_layer3_report.py:2824` | 実 producer を選択 |
| 次点 | `test_autonomous_trial_completeness.py:25,931` | producer／registry を利用 |
| 拡張候補 | `test_campaign.py:10761` | exploratory admission を呼ぶ |
| 拡張候補 | `test_layer3_admission_diagnosis.py:22` | producer を import |
| 拡張候補 | `test_claude_transport.py:21` | producer を import |
| 拡張候補 | `test_p3_exploration_namespace.py:32` | producer を import |
| 拡張候補 | `test_p3_s4_loop_trigger_gating.py:801,1165` | producer を import |
| 拡張候補 | `test_role_session_isolation.py:19` | producer を import |

## 総括

[real] signature、spawn-site 件数、実装 scope に差分起因の不整合は無し（`trial_registry.py:968`、`test_ccbench_spawn_sites.py:284`）。

[real] 残る重要所見は、**例外処理中の attempt 終端失敗が lifecycle 後始末を遮断する既存経路**への timeout の波及（`p3_autonomous_workload_trial.py:5233`）。新規退行とは区別して記録すべきであり、この経路の耐性を追加 4 node から主張できない。

静的レビューのみ実施。pytest、所要計測、commit・push・編集は行っていない。