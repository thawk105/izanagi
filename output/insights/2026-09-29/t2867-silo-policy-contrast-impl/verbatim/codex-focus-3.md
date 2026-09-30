## 総括

**NO-GO。** fix 5 は、焦点 2 巡目の所見 1・2 と F14・N2 の再開時の衝突を解消した。一方、driver の実行環境エラーまで schema 不合格として A を消費し、auditor の digest 不一致も schema 却下として報告する経路が残る。これらは台帳と report の成果物を変える。静的検査のみで、実行テストは行っていない。

## 対応表

| 焦点 2 巡目の項目 | 判定 | 根拠 |
|---|---|---|
| 所見 1：不正な役割出力で round が停止 | **closed** | coder・auditor の JSON／schema 不合格は [round.py](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2867-silo-contrast-impl/tools/silo_policy_contrast_round.py:158) と [同ファイル](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2867-silo-contrast-impl/tools/silo_policy_contrast_round.py:215) から `rejected` へ進む。[終端確認](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2867-silo-contrast-impl/tools/silo_policy_contrast_round.py:45) により、同じ a の逐次再実行では重複しない。driver エラーの分類には下記の新しい所見がある。 |
| 所見 2：別プロセス再開で attempt dir が衝突 | **closed** | [親](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2867-silo-contrast-impl/tools/pegasus/silo_policy_contrast_parent.py:41) が既存の最大番号と `exit.json` の失敗回数を引き継ぐ。 |
| F14：保存済み役割出力を使った再開 | **closed** | 上記の番号衝突が解消され、[親の手順](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2867-silo-contrast-impl/tools/pegasus/silo_policy_contrast_parent.md:7) は同じ `out` の完了済み出力を再利用する。 |
| N2：確定終端と未終端での再開 | **closed** | [親](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2867-silo-contrast-impl/tools/pegasus/silo_policy_contrast_parent.py:46) は確定終端を先に返し、未終端では次の attempt 番号へ進む。 |

## 新しい所見

1. **must-fix — driver の異常終了を schema 却下として A に計上する。** [round の check](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2867-silo-contrast-impl/tools/silo_policy_contrast_round.py:171) と [finalize](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2867-silo-contrast-impl/tools/silo_policy_contrast_round.py:235) は、構造化 JSON のない非 0 終了を無条件に `_schema_reject` へ送る。例えば [driver](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2867-silo-contrast-impl/orchestrator/campaign/p3_s4_loop_policy.py:980) の compiler 不在でもこの経路に入る。**成果物への影響:** 正常な提案を拒否し、[台帳](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2867-silo-contrast-impl/orchestrator/campaign/silo_policy_contrast.py:103) の A と停止時点、選ばれる endpoint を変え得る。**最小の直し:** schema 不合格と判定できた例外だけを `rejected` にし、driver 自体の異常終了は終端を記録せず異常として返す。

2. **should-fix — auditor の digest 不一致が `auditor-schema` として報告される。** [照合](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2867-silo-contrast-impl/orchestrator/campaign/auditor_gate.py:180) は不一致で例外を出すため preview は構造化 JSON を返さず、[finalize](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2867-silo-contrast-impl/tools/silo_policy_contrast_round.py:235) が `auditor-schema` を記録する。**成果物への影響:** A の消費は正しいが、[report の拒否内訳](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2867-silo-contrast-impl/orchestrator/campaign/silo_policy_contrast_report.py:131) が digest 不一致を schema 不合格として数える。**最小の直し:** digest 不一致を識別できる構造化拒否として返し、専用の拒否 subtype を記録する。

構造化された auditor veto は [共通 gate](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2867-silo-contrast-impl/orchestrator/campaign/p3_s4_loop_policy.py:249) を通る。静的に追った経路では、veto や digest 照合を迂回して `proposed` に至る分岐、または同じ a の逐次実行で終端を重複させる分岐は確認しなかった。