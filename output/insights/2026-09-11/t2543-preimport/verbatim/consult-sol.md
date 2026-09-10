## 総括

**採用推奨。D1936項30の本体1行追加と、既存テストモジュール内の局所契約更新で足ります。** 指定資料を静的確認しました。書込み・pytest・変異検査は未実走です。

- **real：条件関門の検査が実行より遅い。** [PBS:54](/work/1/SFC/tanab/izanagi/.codex/worktrees/dev-wave-t2543-preimport/tools/pegasus/probes/t316_sandbox_backend_probe.pbs:54) の配列は4件で条件関門を含みません。一方、[probe.py:36](/work/1/SFC/tanab/izanagi/.codex/worktrees/dev-wave-t2543-preimport/tools/pegasus/probes/t316_sandbox_backend_probe.py:36) で import し、dirty 検査は同ファイル:2331です。成果物への影響は、receipt の束縛対象について、import 前の検査を保証できない点です。配列への追加で既存の dirty 検査と blob 照合がともに先行します。

- **real：既存テストだけでは shell 欠落を検出できない。** [test:1533](/work/1/SFC/tanab/izanagi/.codex/worktrees/dev-wave-t2543-preimport/orchestrator/tests/test_t316_sandbox_probe.py:1533) は Python 関数の直接呼出しです。shell の追加行を削除しても影響しません。plan の「実PBSから配列・dirty検査を抽出して実Gitに適用する」案を採用し、独立literalの対象一覧を維持してください。

- **F28型 mask：全体の拒否だけでは順序を証明できない。** shell の条件関門entryを削除しても、Python側:2331の検査が最終的に拒否しえます。dirty検査をblob照合の後へ移しても、PBS:74の不一致で拒否します。したがって `rc=3` だけを最終出口で観測する契約は不足です。抽出検査の到達markerと、実PBSの「dirty拒否→blob照合→runtime照合→probe起動」の順序assertを組み合わせる案は妥当です。

- **F820型偽kill：fixture全体実行案は不採用。** [test:1439](/work/1/SFC/tanab/izanagi/.codex/worktrees/dev-wave-t2543-preimport/orchestrator/tests/test_t316_sandbox_probe.py:1439) のfixture PBSは `exit 0` です。commit後に実PBSへ置き換えるとPBS自身のdirtyで先に落ち、別の実PBSを起動するとruntime照合が不一致になります。また:1515のhostname差替えはPython内だけで、shellには効きません。これは全体実行へ流用した場合の問題であり、**planの局所抽出案で偽killが発生しているとの指摘は refuted** です。

**最小実装と正負例**

本体は `BOUND_PATHS` に `orchestrator/campaign/condition_meaning_gate.py` を1行追加。既存fixtureの独立した5pathと既存runtime契約は維持します。

正例は「5pathすべてclean」で `rc=0`・markerあり。過剰拒否の境界として「対象外だけdirty」も同じ結果を推奨します。負例は条件関門と既存4pathを各々単独で未stage／stage済みにし、`rc=3`・markerなし。**現物の過剰拒否バグは確認しておらず、対象外dirty正例の不足を新たな本体must-fixとはしません。**

**変異期待node（以下は追加時の提案名）**

| 単一変異 | 期待node・観測 |
|---|---|
| 条件関門entry除去 | `test_execution_binding_shell_rejects_dirty_bound_path[condition_gate-unstaged/staged]` が、`rc=0`・marker到達で失敗 |
| dirty拒否をblob照合後へ移動 | `test_execution_binding_shell_check_order` が失敗 |
| statusのpath限定を除去 | `test_execution_binding_shell_allows_unrelated_dirty_path` が、予期しない拒否で失敗 |

変異killは対象assertまで到達した失敗だけを数え、fixture構築失敗は数えません。親briefの「Python起動前」はPBS:24の版確認を含むため、記録上は「probe起動・条件関門import前」が正確です。一般化や新防護機構は不要です。