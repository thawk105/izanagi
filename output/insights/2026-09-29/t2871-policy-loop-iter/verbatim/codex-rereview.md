## 総括

**現 HEAD の静的レビューでは、driver の受理集合や正しさゲートの順序が fix-1〜4 で変わった形跡はありません。** fix-2 の `_campaign_layout` は従来と同じ ID 式を使っています。T1〜T3 の子 process も、`run_campaign` を実物へ委譲し、指定された認可・claim・reservation・admission・auditor gate を直接差し替えていません。

ただし、**T1 は「系列 digest が 2 回目の計測 WAL 由来」という要件を十分に検査できていません。** 親から共有された T1〜T3 の `3 passed` は踏まえていますが、このレビューでは pytest と変異 probe を実行していません。

## 所見の対応表 (R1〜R14)

| 所見 | 状態 | 現 HEAD の根拠 |
|---|---|---|
| R1 digest の生成時点 | closed | 完了後 view との全文一致は外れ、候補を含み stock を含まない検査になった。[test_p3_s4_loop_policy.py:871](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2871-policy-loop-iter/orchestrator/tests/test_p3_s4_loop_policy.py:871) |
| R2 停止時の計測 ID | closed | `stopped-before` は ID 付与前に返り、独立した期待値で検査する。[p3_s4_loop_policy.py:672](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2871-policy-loop-iter/orchestrator/campaign/p3_s4_loop_policy.py:672)、[test_p3_s4_loop_policy.py:672](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2871-policy-loop-iter/orchestrator/tests/test_p3_s4_loop_policy.py:672) |
| R3 系列 dir の記述 | closed | login の record-reject WAL も明記された。[phase3-silo-policy-runbook.md:108](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2871-policy-loop-iter/docs/phase3-silo-policy-runbook.md:108) |
| R4 欠番の扱い | closed | 完了した pair の評価結果に数えず、証跡は残す記述になった。[phase3-silo-policy-runbook.md:169](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2871-policy-loop-iter/docs/phase3-silo-policy-runbook.md:169) |
| R5 digest の保存先の呼称 | closed | 「系列 dir」に統一された。[phase3-silo-policy-runbook.md:122](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2871-policy-loop-iter/docs/phase3-silo-policy-runbook.md:122) |
| R6 compiler 不在時の skip | not-applicable | 裁定で変更しないと決定。skip は残るが、親の報告では T1〜T3 は実行され 3 passed。[test_p3_s4_loop_policy.py:799](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2871-policy-loop-iter/orchestrator/tests/test_p3_s4_loop_policy.py:799) |
| R7 M5 の赤の再照準 | closed | 裁定どおり、系列 layout へ戻すと digest assert より先に admitted view 読込みで赤になる見込み。[p3_s4_loop_policy.py:479](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2871-policy-loop-iter/orchestrator/campaign/p3_s4_loop_policy.py:479) |
| R8 テスト簡略化案 | not-applicable | 裁定で不採用。T1 と T3 は独立したまま。[test_p3_s4_loop_policy.py:839](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2871-policy-loop-iter/orchestrator/tests/test_p3_s4_loop_policy.py:839)、[test_p3_s4_loop_policy.py:919](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2871-policy-loop-iter/orchestrator/tests/test_p3_s4_loop_policy.py:919) |
| R9 子の import 経路 | closed | `PYTHONPATH` に `orchestrator/tests` が加わった。[test_p3_s4_loop_policy.py:818](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2871-policy-loop-iter/orchestrator/tests/test_p3_s4_loop_policy.py:818) |
| R10 layout 呼出し箇所 | closed | pair は既存 helper を使用し、helper の式は `exploration_campaign_layout(str(ident.campaign_id(cfg)))`。[p3_s4_loop_policy.py:212](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2871-policy-loop-iter/orchestrator/campaign/p3_s4_loop_policy.py:212)、[p3_s4_loop_policy.py:659](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2871-policy-loop-iter/orchestrator/campaign/p3_s4_loop_policy.py:659) |
| R11 stock evidence と checkout | closed | 1 process で checkout は 1 回。evidence は候補 flag の有無で STOCK を分ける。[test_p3_s4_loop_policy.py:743](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2871-policy-loop-iter/orchestrator/tests/test_p3_s4_loop_policy.py:743)、[test_p3_s4_loop_policy.py:773](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2871-policy-loop-iter/orchestrator/tests/test_p3_s4_loop_policy.py:773) |
| R12 source dir の再作成 | closed | 親が pristine source を一度作り、子はそれを複製する。[test_p3_s4_loop_policy.py:808](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2871-policy-loop-iter/orchestrator/tests/test_p3_s4_loop_policy.py:808)、[test_p3_s4_loop_policy.py:777](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2871-policy-loop-iter/orchestrator/tests/test_p3_s4_loop_policy.py:777) |
| R13 模擬 pipeline の枯渇 | closed | `run_campaign` 呼出しごとに新しい模擬 pipeline を開き、実物へ委譲する。[test_p3_s4_loop_policy.py:750](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2871-policy-loop-iter/orchestrator/tests/test_p3_s4_loop_policy.py:750) |
| R14 強制終了後の source 汚染 | closed | process ごとに新しい木を複製し、通常退出時は `applied` が source bytes を戻す。[test_p3_s4_loop_policy.py:733](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2871-policy-loop-iter/orchestrator/tests/test_p3_s4_loop_policy.py:733)、[test_p3_s4_loop_policy.py:777](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2871-policy-loop-iter/orchestrator/tests/test_p3_s4_loop_policy.py:777) |

## 新しい所見

**must-fix — T1 の「2 回目の WAL 由来」検査は、1 回目の digest が残っても通り得る。** 同じ proposal を両 process に渡し、候補の模擬 source token も固定値です。[test_p3_s4_loop_policy.py:743](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2871-policy-loop-iter/orchestrator/tests/test_p3_s4_loop_policy.py:743)、[test_p3_s4_loop_policy.py:821](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2871-policy-loop-iter/orchestrator/tests/test_p3_s4_loop_policy.py:821) T1 は 2 回目の候補文字列が系列 digest にあり、stock 文字列がないことを見るだけなので、1 回目の候補のみを含む古い digest でも成立し得ます。[test_p3_s4_loop_policy.py:875](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2871-policy-loop-iter/orchestrator/tests/test_p3_s4_loop_policy.py:875) **放置時:** critic レポートが前 iteration の証跡を参照しても T1 が緑になり、系列 digest の参照先の誤りを見逃します。**最小修正案:** 子で admitted view の読込み先と実際に生成した digest を、実関数へ委譲する spy で記録し、2 回目の計測 ID と系列 dir に保存された bytes の一致を検査する。**修正後の正例:** 2 回目の計測 WAL から stock 前に生成し、系列 dir に保存した digest が通る。

## 機構を実物で通っていることの根拠

T1〜T3 は別 process から実 `P.main` を呼びます。[test_p3_s4_loop_policy.py:812](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2871-policy-loop-iter/orchestrator/tests/test_p3_s4_loop_policy.py:812) 子の `run_campaign` spy は patch 前の `loop.run_campaign` を保持して委譲します。[test_p3_s4_loop_policy.py:750](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2871-policy-loop-iter/orchestrator/tests/test_p3_s4_loop_policy.py:750) 指定された `_authorize_measurement`、`acquire_claim`、`check_reservation`、`authorization_session`、build admission、`apply_mandatory_deny_only_veto` への直接の差し替えは、この射影内にありません。実 driver は候補の `policy_gate` で auditor veto を呼び、その後 `run_campaign` に進みます。[p3_s4_loop_policy.py:178](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2871-policy-loop-iter/orchestrator/campaign/p3_s4_loop_policy.py:178)、[p3_s4_loop_policy.py:404](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2871-policy-loop-iter/orchestrator/campaign/p3_s4_loop_policy.py:404) 認可 session は候補と stock に同じ object を渡します。[p3_s4_loop_policy.py:661](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2871-policy-loop-iter/orchestrator/campaign/p3_s4_loop_policy.py:661)

代役は checkout を process ごとに新しい木とし、同じ木で候補から stock へ進みます。`applied` は通常退出時に source を戻し、stock evidence は STOCK、coder authority は候補 build だけという検査があります。[test_p3_s4_loop_policy.py:733](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2871-policy-loop-iter/orchestrator/tests/test_p3_s4_loop_policy.py:733)、[test_p3_s4_loop_policy.py:759](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2871-policy-loop-iter/orchestrator/tests/test_p3_s4_loop_policy.py:759)、[test_p3_s4_loop_policy.py:772](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2871-policy-loop-iter/orchestrator/tests/test_p3_s4_loop_policy.py:772) ただし `_mock_pipeline` の内部は今回の射影外なので、その内部の patch 対象までは断定できません。

## 変異の単一理由性の予測

| 変異 | 現 HEAD で予測する主な赤の理由 |
|---|---|
| M1 | 2 本目が同じ計測 identity を再使用し、T1 の子で `ClaimError`。 |
| M2 | 強制終了前の counter 保存がなくなり、T2 の次の子が同じ claim で `ClaimError`。 |
| M3 | stock 結果を系列 WAL から読むため、T1 の `certified-stock` が成立しない。 |
| M4 | 系列 state・履歴が系列 dir に残らず、T1 の 1 本目直後の assert が赤。 |
| M5 | 再照準した裁定どおり、系列 dir の admitted view 読込みで子が例外となり、T1 の子 rc assert が赤。digest の内容比較には到達しない。 |

いずれも**静的な予測**です。親が並行実行中の焦点走と変異 probe の結果は、この判定に含めていません。