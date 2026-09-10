## 総括

A は closed、B/C は partial です。変更は [test_floor_pair_driver.py:582](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2166-floor-pair-driver/orchestrator/tests/test_floor_pair_driver.py:582) のみです。regressed は確認されていませんが、テストは未実走です。

B/C は strict validator の先行検査により、指定された単一理由入力が実装上到達不能です。stub を使った見せかけのテストは追加していません。

## A

- 状態: closed、実装済み・未実走
- nodeid: `orchestrator/tests/test_floor_pair_driver.py::test_tracked_calibration_declared_sha_mismatch_is_rejected_for_sha_only`
- 対象実装: [floor_pair_driver.py:539](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2166-floor-pair-driver/orchestrator/campaign/floor_pair_driver.py:539)

単一理由性の根拠:

- spec 自体の期待 SHA は生成した bytes から計算するため、spec の SHA と HEAD 検査 [floor_pair_driver.py:1094](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2166-floor-pair-driver/orchestrator/campaign/floor_pair_driver.py:1094) を通ります。
- 誤った宣言値は 64 桁 lowercase hex なので構文検査 [floor_pair_driver.py:402](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2166-floor-pair-driver/orchestrator/campaign/floor_pair_driver.py:402) を通ります。
- calibration の実 bytes は変更せず、その SHA を明示確認しています。HEAD fixture にも同じ bytes を渡しています [test_floor_pair_driver.py:587](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2166-floor-pair-driver/orchestrator/tests/test_floor_pair_driver.py:587)。
- したがって拒否理由は宣言 SHA との不一致だけです。対象検査を除去した場合、直後の HEAD blob 比較 [floor_pair_driver.py:543](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2166-floor-pair-driver/orchestrator/campaign/floor_pair_driver.py:543) も通り、`pytest.raises` が失敗します。

## B

- 状態: partial
- nodeid: なし
- 対象実装: [floor_pair_driver.py:988](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2166-floor-pair-driver/orchestrator/campaign/floor_pair_driver.py:988)

到達不能の根拠:

- floor driver は対象検査より先に real strict validator を呼びます [floor_pair_driver.py:970](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2166-floor-pair-driver/orchestrator/campaign/floor_pair_driver.py:970)。
- validator 自身が `subject.trace is not False` を拒否します [s8b_binary_admission.py:351](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2166-floor-pair-driver/orchestrator/campaign/s8b_binary_admission.py:351)。
- よって `subject.trace=true` の receipt が strict validator を通り、floor 側検査だけで赤になる入力は存在しません。

## C

- 状態: partial
- nodeid: なし
- 対象実装: [floor_pair_driver.py:984](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2166-floor-pair-driver/orchestrator/campaign/floor_pair_driver.py:984)

到達不能の根拠:

- strict validator は `subject.binary_sha256` と `record["binary_sha256"]` の一致を要求します [s8b_binary_admission.py:397](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2166-floor-pair-driver/orchestrator/campaign/s8b_binary_admission.py:397)。
- record 側を spec と一致させ、subject 側だけを不一致にすると、この validator が先に拒否します。
- 両方を不一致にして validator を通すと、今度は floor 側の手前の record 検査 [floor_pair_driver.py:979](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2166-floor-pair-driver/orchestrator/campaign/floor_pair_driver.py:979) が先に拒否します。

## テスト実行

走ったテストの nodeid はありません。

指定ランナーは Pegasus dispatch を試みましたが、`qstat -Q` preflight で失敗し、`child_started=false` でした。テストおよび計算ノード job は起動していません。生成された dispatch 一時ファイルは除去済みで、現在の変更は対象 test file だけです。

B/C を closed にするには、冗長な floor 側検査を変異対象外とするか、禁止されている実装変更または validator stub の許可が必要です。