# 防御側レビュー

静的監査では **must-fix はありません**。live 実測 admission は current のままです。ただし、回帰防壁に should-fix 2 件、CLI の順序表現に nit 1 件あります。pytest は未実走であり、緑は主張しません。

## must-fix

該当なし。

## should-fix

1. **ambiguous resolver の adapter-level 負例がない。** 追加 matrix は `unknown / cross-env / invalid-return` だけです。[test_s8b_floor_campaign.py:4452](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t529-impl-reraise/orchestrator/tests/test_s8b_floor_campaign.py:4452) resolver leaf 自体の ambiguous 拒否は [env_contract.py:366](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t529-impl-reraise/orchestrator/campaign/env_contract.py:366) と既存 [test_env_contract.py:636](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t529-impl-reraise/orchestrator/tests/test_env_contract.py:636) にありますが、floor adapter がそこで current fallback しないことは未固定です。

   **成果物影響:** 将来 ambiguous 時だけ fallback する退行が入ると、凍結 protocol の read-only 受理集合とレポートが参照する contract hash 世代が変わり得ます。現実装は [s8b_floor_campaign.py:313](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t529-impl-reraise/orchestrator/campaign/s8b_floor_campaign.py:313) で fail-closed なので、現在の成果物は変わりません。

2. **current admission 成功時の「lookup 1 回・同一 object」回帰試験がない。** fresh 負例は mismatch で後段へ到達しません [test_s8b_floor_campaign.py:4481](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t529-impl-reraise/orchestrator/tests/test_s8b_floor_campaign.py:4481)。また command projection 単体試験は admission object ではなく別の `ec.lookup()` を渡しています [test_s8b_floor_campaign.py:397](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t529-impl-reraise/orchestrator/tests/test_s8b_floor_campaign.py:397)。

   **成果物影響:** 後段 lookup が再導入され registry が間で変わると、calibration・execution receipt・build・計測 command receipt が別世代を参照し、試行台帳の proof chain と certified 結果の provenance が混成し得ます。成功系で sentinel object の `is` 同一性と lookup 1 回を固定すべきです。

## nit

1. **「I/O より前」を入力読込みまで含めるなら CLI は満たさない。** `main` は historical 検証後に freeze file を読み [s8b_floor_campaign.py:3557](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t529-impl-reraise/orchestrator/campaign/s8b_floor_campaign.py:3557)、current admission はその後の core [s8b_floor_campaign.py:2829](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t529-impl-reraise/orchestrator/campaign/s8b_floor_campaign.py:2829) です。ただし durable/output I/O、calibration、build、measure、journal 変更はいずれも current gate 後です。

   **成果物影響:** certified 結果・レポート・試行台帳は変わりません。変わるのは inactive protocol の `freeze.path` が拒否前に読まれ得る参照集合とエラー precedence だけです。

## live 経路の反証

- 公開 `validate_protocol` は historical resolver に固定されています [s8b_floor_campaign.py:389](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t529-impl-reraise/orchestrator/campaign/s8b_floor_campaign.py:389)。production の直接 caller は CLI `main` だけで、その返却 dict は必ず `run_campaign` へ渡されます [s8b_floor_campaign.py:3559](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t529-impl-reraise/orchestrator/campaign/s8b_floor_campaign.py:3559)。
- `run_campaign` は無条件に core を呼び [s8b_floor_campaign.py:2778](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t529-impl-reraise/orchestrator/campaign/s8b_floor_campaign.py:2778)、fresh/resume 共通分岐より前に current admission を再実行します [s8b_floor_campaign.py:2829](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t529-impl-reraise/orchestrator/campaign/s8b_floor_campaign.py:2829)。
- current mismatch は calibration [同:2837](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t529-impl-reraise/orchestrator/campaign/s8b_floor_campaign.py:2837)、output root [同:2918](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t529-impl-reraise/orchestrator/campaign/s8b_floor_campaign.py:2918)、build [同:3051](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t529-impl-reraise/orchestrator/campaign/s8b_floor_campaign.py:3051)、resume journal 読込み [同:3089](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t529-impl-reraise/orchestrator/campaign/s8b_floor_campaign.py:3089) より前に拒否されます。
- historical lane に `lookup` はなく、resolver の exact `GenerationEntry`、contract の exact type、env、hash を検査します [s8b_floor_campaign.py:308](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t529-impl-reraise/orchestrator/campaign/s8b_floor_campaign.py:308)。共有 leaf の callback 呼出しも現状ちょうど1回です [s8b_floor_contract.py:139](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t529-impl-reraise/orchestrator/campaign/s8b_floor_contract.py:139)。
- admission object は calibration・receipt [s8b_floor_campaign.py:2837](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t529-impl-reraise/orchestrator/campaign/s8b_floor_campaign.py:2837)、fresh/resume build [同:3051](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t529-impl-reraise/orchestrator/campaign/s8b_floor_campaign.py:3051)、runner [同:3179](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t529-impl-reraise/orchestrator/campaign/s8b_floor_campaign.py:3179)、command receipt [同:2196](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t529-impl-reraise/orchestrator/campaign/s8b_floor_campaign.py:2196) へ再解決なしで伝播しています。
- 既存 resume 負例は calibration 0 回・measure 0 回・journal bytes 不変を維持しています [test_s8b_floor_campaign.py:4551](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t529-impl-reraise/orchestrator/tests/test_s8b_floor_campaign.py:4551)。正例も残っています [同:4523](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t529-impl-reraise/orchestrator/tests/test_s8b_floor_campaign.py:4523)。差分に期待値反転、assert 削除、skip/xfail はありません。
- 凍結 protocol の実 SHA-256 は `261cec1c…e74aac` のままで、`FROZEN_MANIFEST` 期待値とも一致します [test_frozen_artifacts.py:45](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t529-impl-reraise/orchestrator/tests/test_frozen_artifacts.py:45)。

## 事前登録変異

以下は静的に KILL 可能です。未実走です。

| 変異 | 落とす nodeid | 失敗点 |
|---|---|---|
| M9 historical → current lookup | `orchestrator/tests/test_s8b_floor_campaign.py::test_public_validate_protocol_resolves_recorded_historical_generation_once` | g1/current g2 で current lookup を発火させ、historical 1回・current 0回の期待を破る |
| M10 historical 拒否を恒真 pass | `...::test_public_validate_protocol_historical_failures_never_fallback_to_current[unknown]`、`[cross-env]` | 無条件受理なら `pytest.raises`、fallback なら `current_lookup.assert_not_called()` が落ちる |
| M11 live admission → historical | `...::test_fresh_run_rejects_recorded_g1_when_current_contract_is_g2_before_io` および `...::test_resume_rejects_recorded_g1_when_current_contract_is_g2_before_calibration` | fresh の resolver/call-count と resume の calibration 0回・journal不変が破れる |

## 総括

1. **live admission は緩んでいない。** fresh・resume・CLI の実測はいずれも current admission を通り、g1/current g2 は calibration・build・measure・journal 変更前に拒否されます。

2. **事前登録した3変異に落とせないものはない。** M9/M10/M11 は上記 nodeid で静的に KILL 可能ですが、pytest 未実走です。

3. 親はまず上記追加3試験と resume 正負例を `python3 tools/run_tests.py` 経由で実走し、その後プラン記載の関連6ファイル、`test_frozen_artifacts.py`、Codex/docs checker を実行すべきです。