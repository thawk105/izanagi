## 所見

1. **must-fix — `dependency_prefix` の区切りが実行経路で食い違う。** 根拠: [p3_s4_loop_policy.py](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2865-stage-f/orchestrator/campaign/p3_s4_loop_policy.py:602)、[p3_s4_loop_pegasus.sh](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2865-stage-f/tools/pegasus/p3_s4_loop_pegasus.sh:673)。job はコロン区切りの `CMAKE_PREFIX_PATH` を作るが、driver はそれを明示引数として渡し、buildcache は明示引数をセミコロン区切りで解釈する。  
   **成果物への影響:** gflags・glog の二つの prefix が一つの不正な path として扱われ、stock・pair・replay の build が失敗し得る。  
   **修正案:** 環境変数を明示引数へ渡す際に、path 要素を CMake 用のセミコロン区切りへ変換する。`/scratch/gflags:/scratch/glog` は二つの prefix `/scratch/gflags;/scratch/glog` として build に渡る正例にする。

2. **must-fix — stock の認証結果が source identity を確認していない。** 根拠: [p3_s4_loop_policy.py](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2865-stage-f/orchestrator/campaign/p3_s4_loop_policy.py:344)。`certified` と `aborted` だけで `certified-stock` を返し、既存の [stock 判定](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2865-stage-f/orchestrator/campaign/p3_s4_loop.py:2396) が確認する variant と `BUILD_START.src_token` を見ていない。  
   **成果物への影響:** 非 stock source の計測値が stock baseline として記録され、候補との比が変わる。  
   **修正案:** 同じ attempt の WAL で `src_token=STOCK` と期待する variant を確認した場合だけ `certified-stock` を受理する。それ以外は `non-stock-source` として拒否し、原型 source の stock attempt だけを通す。

3. **should-fix — stock が不成立でも job の rc は 0 になる。** 根拠: [p3_s4_loop_policy.py](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2865-stage-f/orchestrator/campaign/p3_s4_loop_policy.py:603)。`--stock-baseline` は `aborted` や `skipped` の JSON を出した後も 0 を返す。  
   **成果物への影響:** 不成立の bootstrap job が成功扱いとなり、その数値を次の coder baseline に採用し得る。  
   **修正案:** stock outcome が `certified-stock` 以外なら job を非 0 で終了させ、採用を拒否する。`certified-stock` で同じ attempt の throughput と abort 率が得られた場合は rc 0 で通す。

4. **should-fix — 実 source 判定テストは Pegasus で常に skip される。** 根拠: [test_p3_s4_loop_policy.py](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2865-stage-f/orchestrator/tests/test_p3_s4_loop_policy.py:464)。テストは `g++-13` を必須とするが、repo の Pegasus runbook は login・計算ノードの双方にそれが無く、計算ノードには `g++-12` があると記す。  
   **成果物への影響:** stock source が `STOCK` に分類されるという E2E の前提を検査しないまま、テスト一式が緑になり得る。  
   **修正案:** 実行 site で使う compiler を選んで source digest を検査する。計算ノードで `g++-12` が使える場合は skip せず、原型 source が `STOCK` を返す正例を通す。

## 総括

NO-GO。静的レビューでは、とくに prefix の区切り違いが今回の計算ノード E2E を妨げる。テスト・build は依頼どおり実行していない。