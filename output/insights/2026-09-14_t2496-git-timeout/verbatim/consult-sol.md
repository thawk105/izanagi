## 受理集合の向き

- [real] **指定 2 モジュール内では、提案変更が受理を広げる経路は無い。** `_git` が例外を送出すると、終了コード・空出力による分岐には到達しない。特に `_blob_at_commit` の「不存在なら `None`」も通らない（`orchestrator/campaign/trial_registry.py:1294`, `:1330`, `:1337`）。timeout から部分的な履歴・blob を返す処理や、自動 retry はない。

- [real] `TrialRegistryError` を `False` にする捕捉はあるが、対象は JSON decode だけである。Git 読取りはその前に完了しており、timeout を「genesis ではない」に変換できない（`orchestrator/campaign/trial_registry.py:606`, `:2560`, `:2576`, `:2617`, `:2634`）。

- [real] 上位の失敗処理は成功復帰しない。`run_trial` は再送出または `mark_experiment_indeterminate` に進み、後者も最後に `raise cause` する。後始末で別の Git 操作を試す場合も、失敗した検査の retry による成功復帰ではない（`orchestrator/campaign/p3_autonomous_workload_trial.py:4945`, `:5088`, `:5226`, `:4611`）。

- [real] **部分結果として返る経路はある。** `run_origin_trial` は例外を `OriginPreflightFailure` / `OriginPartialTrialReport` に変換するが、`OriginCompletedTrialReport` には変換しない（`orchestrator/campaign/p3_autonomous_workload_trial.py:5307`, `:5330`, `:5331`）。また `_finish_trial` の例外捕捉は `fatal_error` を設定し、complete 条件から外す（同 `:3611`, `:3765`）。

- [疑い] 部分結果の**内部 payload**には注意が必要。report 保存後の terminal 記録で timeout になると、既存の `"status": "complete"` を含む report が `OriginPartialTrialReport` に包まれる可能性がある（同 `:3934`, `:5219`, `:5317`, `:5330`）。指定範囲では受理ではないが、外側の型を無視する consumer まで安全とは断言できない。

## 規律 2 への抵触

- [real] **提案コード自体に抵触は認めない。** `check=False` と正常終了時の返却を保持し、timeout だけを例外化するため、従来拒否された内容を受理する分岐は追加されない（`plan.md:16`, `:21`, `:24`）。

- [real] 非 0 終了と timeout は一部で同じ `TrialRegistryError`・`[git-operational]` に分類されるが、それによる受理はない。祖先検査は rc=1 とその他を従来どおり区別し、timeout はその分岐に入らない。timeout 固有の診断と `__cause__` も残る（`orchestrator/campaign/trial_registry.py:1295`, `:1297`, `:1300`; `plan.md:24`）。

## 正例の恒真性

- [real] **提案正例は、timeout 指定の削除に対して赤になる。** `timeout=` だけを削除すると、有限の 2 秒 sleep が終了して `CompletedProcess` が返り、期待した `TrialRegistryError` が出ない。捕捉変換だけを削除すれば、期待型と異なる `TimeoutExpired` が漏れる（`plan.md:96`, `:106`）。変更全体を戻した場合は未知の `timeout_s` による `TypeError` になるため、変異検査では前者の削除を使うべきである。

- [real] 偽 Git は実際の `_git` 経路に入る設計である。PATH は許可環境に残り、実行コマンドの先頭は `"git"`。shim の通常の起動失敗だけでは、期待する `TimeoutExpired` cause を満たさない（`orchestrator/campaign/trial_registry.py:260`, `:953`, `:972`; `plan.md:96`）。

- [real] **本番既定値の検査が欠ける。** 全追加テストが `timeout_s` を明示するため、既定値だけを `None` にする誤実装はこれらを通過できる。本番 16 呼出しは二引数なので、この変異では本番の timeout が無効になる（`plan.md:13`, `:96`, `:98`, `:111`）。既定値 300.0 の束縛と、その経路での `subprocess.run` への伝達を別途検査する必要がある。

## 負例の恒真性

- [real] 負例は恒真ではない。一律拒否、stdout/stderr の破壊を排除する具体的な assertion があり、排除対象も明記されている（`plan.md:97`, `:100`）。

- [real] **「終了コードを壊す変異を排除する」は広すぎる。** 追加負例はいずれも rc=0 のため、返却 rc を常に 0 に書き換える変異や `check=True` への変更を検出できない（`plan.md:97`, `:98`, `:100`）。既存の rc=128 / rc=2 テストも、その対象コマンドでは `_git` 自体を置換している（`orchestrator/tests/test_trial_registry.py:5239`, `:6570`）。即時 shim を rc=0・1・128 で検査し、非 0 でも同じ bytes と終了コードを返す負例を加えるのが局所的な補強になる。

## 親 brief の誤りと誇張

- [real] **指定された行番号の不一致は無い。** 呼出し 16 箇所はすべて一致する（`brief.md:17`）。捕捉 10 箇所も、`trial_registry.py` の 613 / 645 / 1138 / 1895 / 2462 / 2578 / 3044 / 4674 / 5687 / 6609 と一致する。2578 以外は再送出または CLI エラー終了である。

- [real] 履歴 loop の説明は概ね一致する。ただし正確な関数名は `_assert_attempt_registry_history_append_only`。全 commit の tree を列挙し、blob エントリごとに `cat-file` を実行する（`brief.md:53`; `orchestrator/campaign/trial_registry.py:2587`, `:2543`, `:2553`, `:2560`, `:2611`）。10,369 は記載された観測値であり、コード上の上限ではない。

- [real] **「集約の終端は協調的な `max_wall_s` のまま」は補足不足。** この履歴 loop に deadline 検査はない。さらに登録 attempt の予約は `started_monotonic` 設定より前に行われる（`brief.md:56`; `orchestrator/campaign/p3_autonomous_workload_trial.py:1585`, `:4849`, `:5021`）。「履歴走査中には予算を確認せず、起動時の走査には計時開始前のものもある」と明記すべきである。

- [real] 全体上限を保証しないという限定は妥当だが、**本番の per-call timeout が有効であることの検査まで省略してよい理由にはならない**（`brief.md:55`; `plan.md:96`, `:144`）。

## scope の穴

- [real] **提案コードどおりなら、16 呼出しに timeout を渡すための追加実装層は不要。** 共通 `_git` の既定値が全呼出しに適用される（`orchestrator/campaign/trial_registry.py:967`; `plan.md:13`, `:111`）。欠けているのは、その本番経路を保証する検査である。

- [疑い] 裁定パッケージ候補は、**「全 Git 呼出しが 300 秒未満でも履歴集約が長時間進まないケースを、本 wave の解決対象に含めるか」**。含めるなら per-call timeout だけでは不足するが、現 scope は集約予算の変更を明示的に除外している（`brief.md:20`, `:55`; `orchestrator/campaign/trial_registry.py:2611`）。本 wave で解決済みと扱わず、親段 4 で対象外か追加課題かを裁定すべきである。

## 総括

[real] **受理拡大の経路は指定範囲で見つからず、提案実装は fail-closed。ただしテスト計画には、本番既定値と非 0 終了コードの検査漏れがある。** この 2 点と `max_wall_s` の説明を補強するのが主要な指摘である（`plan.md:96`, `:100`, `:144`; `brief.md:56`）。

指定 5 ファイルは読取り可能だった。静的検査のみで、pytest・編集・commit・push は実施していない。