# 段6 focused review 第3巡 — 最終判定

- 固定 integrated patch SHA-256:
  `1f98a868d24b0009b017abb9d7204651ba9b6aa0e63964e94c040ce0b90105b7`
- read-only `gpt-5.6-sol` / reasoning=max の reviewer は exit 0、
  `tools/check_codex_output.py` green、開始・終了 SHA 一致。
- 判定は `closed 8 / partial 1 / regressed 0`、**NO-GO**。
- R1〜R4、R6〜R9 は closed。fix3 起因の regression はない。
- R5 `Group Name` 束縛は fresh lookup / raw再parse / candidate receipt / per-job monitor では
  closed したが、次の 2 consumer が partial:
  1. 既存 submit receipt がある resume 分岐は `group_name` を持たず、matched WAL を
     `job_id_normalized` だけで選び、group/accountを再検証せず monitor / qdel へ渡し得る。
  2. accounting footer parser は `Group Name` を非空文字列としてしか検査せず、
     monitor と final 再検証の双方で policy group と exact 比較しない。
- 成果物影響: wrong-group 既知 job が受理集合へ入り monitor/qdel 対象になり得る。
  また wrong-group accountingを含む dispatch receiptを `CHILD_RESULT` として封印できる。
- fresh lookup / per-job wrong-group expected-red は実 production branchへ到達するが、
  resume / accounting の 2 経路を制約する expected-red はない。
- 実装/test 22 paths は U1〜U4 owner worktreeと byte一致し、親・非author由来の
  implementation hunkはない。
- pytest、build、qsub、qstat、qdel、mutationは未実走であり、green / KILLEDは主張しない。

## 親の最終裁定

上記 2 経路は成果物影響が具体的で、同一識別子の consumer閉包が欠けているため real / scope内 /
must-fix とする。`DW-O16` の3巡上限に達したため第4 fixは作らず、commit・mutation・計算ノード受入・
段7〜9へ進まない。次の fresh `$dev-wave` はこの R5 resume/accounting closure だけを scope にし、
wrong-group resume と wrong-group accounting の expected-red、same-group positive controlを
事前登録する。
