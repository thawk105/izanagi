## 修正

- 1 件目: `orchestrator/tests/conftest.py:95-116` の予約 fixture は `requested_s=3600` として期限を構成しており、検査時に必ず経過時間分だけ不足する。修正案は要求値を超える予約時間にすることだが、4 件目の矛盾を確認したため未編集。
- 2・3 件目: `orchestrator/campaign/p3_autonomous_workload_trial.py:3455-3465` は `BaseException.add_note` がない Python 3.10 で注記追加を黙って失敗させる。`__notes__` への互換 fallback が必要だが未編集。
- 4 件目: 同 `:3667-3687` で `reject_started_trial` は既に `run_root.mkdir` より前に呼ばれている。テスト `:6186-6187` は現在の root でなく、1 回目に成功して残る `first_root` を観測しているため、順序を変えても `[False, True]` になる。期待値を満たすには成果物を削除・隠蔽する必要があり、実装側の正しい修正ではない。

## 恒真化していないことの確認

fixture は未変更で、負の対照も未実走。`orchestrator/tests/test_p3_autonomous_workload_trial.py:2034-2087` は期限を現在時刻の約 1 秒後に再構成し、job・boot・残時間不足を独立に検査するため、fixture を延長しても残時間不足の拒否は維持できる設計である。

## 実走

未実走。4 件目の期待値が実装契約と矛盾すると判定したため、pytest は投入していない。

## 停止・未達

期待値を変更せず、既存 report/journal を削除する実装も採らず停止した。コード、テスト、docs の変更および commit はない。

## 総括

- 必読資料と焦点走ログを確認した。
- 4 件目は実装の late call ではなくテスト観測対象の誤りである。
- 指示に従い、期待値を緩めず実装も変更しなかった。
- 親側でテスト観測を `kwargs["run_root"]` に直す裁定が必要である。