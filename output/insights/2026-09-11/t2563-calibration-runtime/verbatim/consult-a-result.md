## 総括

**real：gflags のバグと、生成停止だけでは configure が壊れる指摘。refuted：「追加比較にも進めない」という結論への一般化。** 契約を維持して比較できる最小候補は、**3依存コピーだけの並列化**です。ただし短縮効果は未証明で、予約式の不整合も解消しません。

1. **real — gflags_nothreads は単純な未使用targetではありません。**
   [config.cmake.in:81](/work/SFC/tanab/github/gflags/cmake/config.cmake.in:81) の `PACKAGE_NAME@_static` は先頭の `@` が欠落しています。現行の static 構成では自動選択が nothreads 側へ進み、生成だけ止めると106行のfatalに到達します。glog は component 無指定で検索し、選ばれた `gflags` を PUBLIC リンクします。[glog:78](/work/SFC/tanab/github/glog/CMakeLists.txt:78)、[glog:596](/work/SFC/tanab/github/glog/CMakeLists.txt:596)
   ただし、これはソースからの判定です。989271の保存ログには選択targetを直接確定する証拠がなく、最終バイナリへの nothreads オブジェクト取り込みまで断定できません。

2. **refuted —「小さい既存フラグでは configure を閉じられない」。ただし等価な削減とは未証明です。**
   gflags 側の `-DBUILD_gflags_nothreads_LIB=OFF` と、glog 側の `-DGFLAGS_NOTHREADS=OFF` により、問題の自動判定を避けて threaded static を選択できます。[生成条件:458](/work/SFC/tanab/github/gflags/CMakeLists.txt:458)、[選択条件:72](/work/SFC/tanab/github/gflags/cmake/config.cmake.in:72)
   しかし、これは glog の依存先変更です。両targetには `NO_THREADS` の差があり、CCBench自身は `libgflags` を検索します。[差分:475](/work/SFC/tanab/github/gflags/CMakeLists.txt:475)、[Findgflags.cmake:5](/work/1/SFC/tanab/izanagi/.codex/worktrees/dev-wave-t2563-calibration-runtime/external/ccbench/cmake/Findgflags.cmake:5)
   **今回の「生成待ちだけを変える」契約に、そのまま等価として採用できません。** glog のgflags機能停止も同様です。

3. **real — 独立コピー並列化は契約内。唯一の比較候補にします。**
   [certify_calibration.sh:607](/work/1/SFC/tanab/izanagi/.codex/worktrees/dev-wave-t2563-calibration-runtime/tools/pegasus/certify_calibration.sh:607) の masstree・mimalloc・googletest の `timeout 120 cp -a` だけを並列化します。各コピーのtimeout、コピー先、3回という処理数を維持し、**全終了・全成功を確認してから、既存pristine検証を1回実施**します。失敗時も全コピーを回収して終了する必要があります。
   buildとの重畳は加えません。job-private fresh build と、測定前の子孫終了確認を維持できます。[検証:620](/work/1/SFC/tanab/izanagi/.codex/worktrees/dev-wave-t2563-calibration-runtime/tools/pegasus/certify_calibration.sh:620)、[子孫確認:726](/work/1/SFC/tanab/izanagi/.codex/worktrees/dev-wave-t2563-calibration-runtime/tools/pegasus/certify_calibration.sh:726)
   親による同条件比較で全体所要・既存受理結果を確認する価値はあります。I/O競合による悪化もあり得るため、効果不明なら差分を残さない判断です。

4. **real — 時点の異なるprobeは再利用できません。**
   wrapperのbuild前／後と、CLIのcooldown前／後、測定後は観測区間が違います。CLIはcooldown前後のstatic比較と、測定後の再取得を明示しています。[cli.py:852](/work/1/SFC/tanab/izanagi/.codex/worktrees/dev-wave-t2563-calibration-runtime/orchestrator/calibrator/cli.py:852)、[cli.py:1005](/work/1/SFC/tanab/izanagi/.codex/worktrees/dev-wave-t2563-calibration-runtime/orchestrator/calibrator/cli.py:1005)
   各測定groupの前後probeも独立した境界です。[sweep.py:221](/work/1/SFC/tanab/izanagi/.codex/worktrees/dev-wave-t2563-calibration-runtime/orchestrator/calibrator/sweep.py:221) 保存結果の流用を、等価な二重処理削減とは認められません。

5. **real — 予約式の不足。refuted — それを実時間短縮不能の証明にすること。**
   planの `60×3＋120×3＋900×2＝2340`、`6610−1080＋2340＝7870` は正しい工程枠の計算です。コピー並列化でもこのbuild鎖は短くならず、**固定7200秒との整合を要求する正式完了は未解決**です。[plan-result.md:18](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2563-calibration-runtime/plan-result.md:18)
   一方、これは実所要ではありません。既存記録の298秒、static→preの30秒、pre→postの263秒からコピー単独の費用は分離できません。mtimeやtimeoutを使った補完、短縮秒数の提示はできません。

編集・テスト・測定・子agent起動は行っていません。以上は静的確認と既存ログの再読であり、検査成功の報告ではありません。
