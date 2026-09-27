## 所見

1. **should-fix** — [p3_s4_loop_policy.py:633](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2865-stage-f/orchestrator/campaign/p3_s4_loop_policy.py:633)。`drive_iteration` が予算切れで `stopped-before` を返しても、pair 経路は stock を評価し、rc=0 で終了する。  
   **成果物への影響:** 候補 attempt が無い job が成功扱いになり、E2E の成否と stock 比の判断を誤り得る。  
   **修正案:** 候補の `ran=False` は pair として拒否し、stock を起動せず非ゼロで終了させる。予算内で候補 attempt ができた正例では、現行どおり同じ authorization session で stock を評価する。

2. **should-fix** — [tools/pegasus/README.md:453](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2865-stage-f/tools/pegasus/README.md:453)。共通の投入準備手順は `p3_s4_loop.PIN` への checkout を指示するが、方策 mode の job body は別の `axis_silo_function_policy.PIN` を要求する。現行値も前者 `511c…`、後者 `6810666` と異なる。  
   **成果物への影響:** 手順どおりに準備した方策 job は PIN 照合で rc=2 となり、E2E と trace 保全まで到達しない。  
   **修正案:** 方策 mode の準備手順では方策 module から PIN を読み、CCBench をその commit に合わせると明記する。正例は方策 PIN `6810666` を解決した commit に CCBench HEAD を置いて stock job を投入する場合。

3. **should-fix** — [tools/pegasus/README.md:486](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2865-stage-f/tools/pegasus/README.md:486)。方策用の記述は旧 qsub command から env を「外し、次を足す」とする断片で、実行可能な方策用 qsub 例になっていない。  
   **成果物への影響:** 旧 env を残した投入は方策 mode の排他検査で rc=2 となり、E2E を開始できない。  
   **修正案:** stock・pair・replay の少なくとも pair について、旧 proposal・K2・stock-control env を含まない完全な `qsub -v` 例を置く。正例は `IZANAGI_S4_POLICY_MODE=pair`、FORM、PROPOSAL_PATH、TRACE_ARCHIVE_ROOT と共通の必須 env だけを渡す投入。

4. **nit** — [p3_s4_loop_pegasus.sh:242](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2865-stage-f/tools/pegasus/p3_s4_loop_pegasus.sh:242)、[test_p3_s4_loop_job_contract.py:1515](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2865-stage-f/orchestrator/tests/test_p3_s4_loop_job_contract.py:1515)。方策 mode での T-2849/B-5 関連 env の走査は、既存の「各 mode が無ければ関連 env を拒否する」検査と重なる。対応する排他 test の T-2849/B-5 ケースも同じ拒否を再確認している。  
   **成果物への影響:** 削除しても受理集合・履歴・比は変わらず、検査量だけが減る。  
   **修正案:** 既存検査が覆う T-2849/B-5 の走査と重複 test ケースを削り、既存検査で覆わない `IZANAGI_S4_T2849_PROTOCOL` と K2・従来 proposal 等の排他を残す。正例の方策 pair env は引き続き受理し、方策 mode に旧 proposal env を混ぜた入力は拒否する。

## 総括

NO-GO。方策 job を実際に投入できる手順への修正と、候補を走らせなかった pair の成功扱いの修正が必要です。計測契約、stock の同一 attempt からの baseline、R2 の共有 gate、trace 保全口については、静的確認の範囲で本題に必要な配線を確認しました。pytest・build は依頼どおり実行していません。