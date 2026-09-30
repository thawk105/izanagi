## 所見ごとの判定

判定は HEAD `5c968c978` の静的検査によるものです。patch 適用、build、実走は行っていません。

| 所見 | 判定 | 根拠 file:line | 残る問題 |
|---|---|---|---|
| F1 世代加算の窓 | **closed（静的）** | [M patch](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-cicada-certified-m/patches/instr-cicada-trace-m.patch:324)、[事象 site](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-cicada-certified-m/patches/instr-cicada-trace-m.patch:183)、[snapshot](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-cicada-certified-m/patches/instr-cicada-trace-m.patch:366)、[終了照合](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-cicada-certified-m/patches/instr-cicada-trace-m.patch:114) | 初期ロードと新規 `Version` の世代は `0`。確認した pool・inline の返却、清掃、再利用では開始と終了の加算が対になり、間にある `continue`・`goto`・`return` は終了加算の後。stock で偽の B 違反が出ないことは実走未確認。 |
| F2 母集団の等式 | **partial** | [M patch](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-cicada-certified-m/patches/instr-cicada-trace-m.patch:110)、[同](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-cicada-certified-m/patches/instr-cicada-trace-m.patch:400)、[同](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-cicada-certified-m/patches/instr-cicada-trace-m.patch:465)、[起動器](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-cicada-certified-m/launcher/launch_cicada_m.py:328) | `b_elements_checked` は終了 loop の各要素で増え、`api_checked` は比較経路で増える。abort・read-only・validation 失敗時も終了照合が clear より前にある。forwarding の `ERROR_PREEMPTIVE_ABORT` は `read_other_status` に入る。ただし両等式の stock 実測はまだなく、API の照合分岐を意図的に壊した場合の検出力もこの静的検査では確定しない。 |
| F3 E-max の hunk 位置 | **partial** | [M patch の 18 hunk](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-cicada-certified-m/patches/instr-cicada-trace-m.patch:344)、[insert](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-cicada-certified-m/patches/instr-cicada-trace-m.patch:496)、[delete](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-cicada-certified-m/patches/instr-cicada-trace-m.patch:503)、[U1 の対応表](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-cicada-certified-m/fix2-u1.md:49) | 原物の `transaction.cc` hunk は **18 本**で、insert・delete は固有の文脈になった。U1 が示す「両 stack で全 18 本の適用先関数が一致」は、書込可能な scratch がないため独立には照合できていない。 |
| S2 configure 失敗 | **partial** | [起動器 checkout](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-cicada-certified-m/launcher/launch_cicada_m.py:133)、[configure](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-cicada-certified-m/launcher/launch_cicada_m.py:517)、[例外記録](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-cicada-certified-m/launcher/launch_cicada_m.py:183)、[`.gitattributes`](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-cicada-certified-m/external/ccbench/.gitattributes:7)、[CMake](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-cicada-certified-m/external/ccbench/CMakeLists.txt:81) | `git archive` が除外する `oze` を full checkout で含める修正は、configure 失敗の観測と整合する。pin C は起動器の指定値と submodule の HEAD が一致し、両 checkout 経路で pin と clean 状態を検査する。隔離 clone は submodule の gitdir に worktree を登録しない。configure の復旧は build 未実走。失敗ログには下記の新所見が残る。 |

F2 の二つの等式について、指定された通常分岐で直ちに恒真となる経路、または偽の赤になる経路は見つかりませんでした。これは実走での成立を証明するものではありません。

### N1 失敗ログは行数だけで制限される

**重大度: should。** [起動器](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-cicada-certified-m/launcher/launch_cicada_m.py:167) は stdout・stderr の末尾を各 200 行にしますが、1 行の byte 数を制限せず、伏せ字処理もありません。[例外記録](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-cicada-certified-m/launcher/launch_cicada_m.py:183) と [実行失敗の記録](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-cicada-certified-m/launcher/launch_cicada_m.py:202) がその文字列を result に入れます。例えば改行のない巨大な診断行なら result が巨大化し、コマンドが秘密を出力すれば result に残ります。**影響:** S2 の診断用成果物のサイズと内容を制御できません。**推奨対処:** 行数に加えて byte 上限を設け、保存対象の秘密情報を除去してください。

## 総括

**NO-GO（焦点レビューの静的判定）。** F1 の窓は静的には閉じていますが、F2・F3・S2 の実測確認が残ります。U1 の「18 hunk」は原物と一致しますが、全適用先関数の一致は独立検証できていません。起動器の失敗ログには N1 の未解決問題があります。