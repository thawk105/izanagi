## 所見

1. **must-fix — 性能動作点が campaign identity に入っていない。** [p3_s4_loop_policy.py](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2865-silo-policy-stage-e/orchestrator/campaign/p3_s4_loop_policy.py:87) の `search_config` は形と verify mode を含む一方、[同:102](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2865-silo-policy-stage-e/orchestrator/campaign/p3_s4_loop_policy.py:102) の `PerfConfig` を含まない。反例は、同じ `cfg` に異なる `perf` を渡す `drive_iteration` 呼出し。`run_campaign` は渡された `perf` から性能 verify を作るため、異なる動作点の結果と自系列履歴が同じ campaign に入る。**影響:** certified 選択・レポート・台帳の比較対象が混ざる。**代案:** records、threads、workload、extime、reps を正規化して `search_config` に束縛し、実行時の `perf` との一致を検査する。

2. **must-fix — 次の coder に verify 失敗の理由が届かない。** [p3_s4_loop_policy.py:214](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2865-silo-policy-stage-e/orchestrator/campaign/p3_s4_loop_policy.py:214) は結果を `certified`／`aborted` と `{verdict, certified, aborted}` に縮め、[同:172](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2865-silo-policy-stage-e/orchestrator/campaign/p3_s4_loop_policy.py:172) がそれだけを履歴へ射影する。反例は性能 verify で `non-serializable` になった候補と、trace timeout で abort した候補。既存の [critic digest](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2865-silo-policy-stage-e/orchestrator/critic/digest.py:1367) には workload、cycle の辺、integrity 理由があるが、`--emit-coder-input` は [critic 診断を渡さない](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2865-silo-policy-stage-e/orchestrator/campaign/p3_s4_loop_policy.py:273)。**影響:** 次手が「なぜ壊れたか」を区別できず、規律 3 の帰属と探索記録が弱くなる。**代案:** 当該候補の admitted WAL から workload tag、reject reason、構造化 verifier anomaly／integrity を閉じた射影で履歴に加え、次回入力へ接続する。

3. **should — 事前登録した変異の一部は単一理由の kill を示せない。** [test_p3_s4_loop_policy.py:155](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2865-silo-policy-stage-e/orchestrator/tests/test_p3_s4_loop_policy.py:155) の M-E1 相当入力で構文拒否だけを無効化すると、`compiled is None` を [policy gate](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2865-silo-policy-stage-e/orchestrator/campaign/p3_s4_loop_policy.py:126) が compile 拒否にする。赤は subtype の違いであり受理集合の kill ではない。M-E7 の bool `StateRef.index`／`Const.value` も [validate_ir](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2865-silo-policy-stage-e/orchestrator/campaign/silo_policy_ir.py:200) に重ねて拒否される。M-E4 の [test](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2865-silo-policy-stage-e/orchestrator/tests/test_p3_s4_loop_policy.py:81) は loader の 26 上限を見ており、実際の veto 呼出しを 21 に変える変異を検出しない。**影響:** 変異台帳が gate の検出力を過大評価する。**代案:** M-E1 は診断 pin に移すか冗長 gate と明記する。M-E7 は両層変異を事前登録する。M-E4 は型 22 の verdict を実 `policy_gate` に通す。

## 実装子の報告の主張の検証

構造・effect 検疫、構文、単独 TU、auditor digest と deny-only veto、書込後 digest の順序はコード上で確認できる。IR も描画後に同じ本文 gate を通る。compiler 不在・compile timeout・例外が build 受理へ変わる経路は見つからなかった。preview は同じ本文を検査して diff digest を出すが、auditor veto は実行しないため「全 gate が同一」という主張には留保が要る。

`VERIFY_LEGACY_PLUS_PERFORMANCE` は `run_campaign` から性能 `perf` に基づく追加 verify へ接続され、legacy と併走する。proposal の重複 key・未知 key・形違い、IR の exact key／型、auditor 既定上限 21 と policy 上限 26 も静的には整合する。projection は `binary` と `scope` だけを出し、履歴から justification を落とす。role 本文と coder spec に具体的な偵察順位・既知最良は見当たらず、spec の署名は API header と一致する。既存 3 軸の受理集合を広げる変更も確認できない。実 compiler・pytest の結果はこのレビューでは主張しない。

## 変異 M-E1〜M-E11 の単一理由性の見立て

M-E1 は subtype だけが変わる可能性が高く kill 不適格。M-E4 は期待 test が実 veto の変異位置を覆わない。M-E7 は `validate_ir` に遮られ単独変異が生存しうる。M-E2・3・5・6・8〜11 は対応する拒否または key／cfg assertion があり、静的には単一理由を狙えている。ただし期待失敗 node の完全集合と変異注入後の実走は未確認であり、DW-M08 の kill 証拠にはまだならない。

## 再発しうる失敗の型

`docs/failures.md` の型タグでは、変異の赤を受理境界の証拠と取り違える **[恒真ゲート]**、verify の詳細を次手入力から落とす **[ドリフト]** が該当する。検査未実走を緑と数える **[捏造/幻覚]** は、実装子の報告では明示的に避けられている。

## 総括

**NO-GO。** must-fix は、性能動作点を campaign identity に束縛すること、verify／liveness 失敗の構造化理由を当該系列の次回 coder 入力へ届けることの 2 件。静的レビューであり、親の commit 後テスト結果は未確認。