## 総括

**現時点では採用不成立、実装・追加測定へ進めない判断です。** 最小候補の「gflags_nothreads 生成停止」は未使用の前提が成立せず、単独差分で configure を壊す静的根拠があります。さらに、この削減では固定7200秒と予約式の不整合も解消しません。あらゆる短縮案が不可能だと証明したわけではありません。

**実測済（既存記録の再読）**

- 989271 は開始→完了記録298秒、static→pre 30秒、pre→post 263秒です。scheduler Elapse302秒とは終端の範囲が異なります。[開始記録](/work/1/SFC/tanab/izanagi/.codex/worktrees/dev-wave-t2563-calibration-runtime/output/env/pegasus/calibration/job-staging/0:989271.nqsv/reservation.json:9)、[完了記録](/work/1/SFC/tanab/izanagi/.codex/worktrees/dev-wave-t2563-calibration-runtime/output/env/pegasus/calibration/job-staging/0:989271.nqsv/job-result.json:10)
- gflags は同じ3ソースを2種類のtargetとして計6回compileし、archiveを2個生成・installしています。これは同一成果物の二重buildではありません。[buildログ](/work/1/SFC/tanab/izanagi/.codex/worktrees/dev-wave-t2563-calibration-runtime/output/env/pegasus/calibration/job-staging/0:989271.nqsv/gflags-build.stdout:1)
- sweepは3点×3rep、noiseは10rep、scaleはnot-measured。代表 `walltime_s` や移送後mtimeから工程合計は復元できません。コピー85秒・検証22秒はlogin→NFS側の観測であり、compute→`/scr` の短縮見積りには使えません。[既存測定の場所](/work/1/SFC/tanab/izanagi/.codex/worktrees/dev-wave-t2563-calibration-runtime/output/insights/2026-09-10/t2535-certify-offline-fetch/README.md:73)

**静的確認と推定：親briefへの修正**

1. **P1の「未使用」は撤回が必要です。**
   指定pinの [gflags設定:81](/work/SFC/tanab/github/gflags/cmake/config.cmake.in:81) は `PACKAGE_NAME@_static` と先頭の `@` が欠けています。staticのみ・component指定なしではnothreads選択へ進み、削除後は同ファイル106行のfatalに到達する読みです。glogは [componentなしのfind_package](/work/SFC/tanab/github/glog/CMakeLists.txt:78) を行います。両checkoutのHEADは指定pinと一致し、対象ファイルのHEAD差分はありません。
   CCBench自身は `libgflags` を探しますが、それだけではglogのconfigure時依存を否定できません。「3compile＋1archive削減」は処理数の候補に留まり、単独差分として採用できません。

2. **P2は当該候補について支持できます。**
   gflagsは60秒×3工程、glogは120秒×3工程、CCBenchは900秒×2工程なので、直列build関連枠は **2340秒**です。[gflags工程](/work/1/SFC/tanab/izanagi/.codex/worktrees/dev-wave-t2563-calibration-runtime/tools/pegasus/certify_calibration.sh:492)、[glog工程](/work/1/SFC/tanab/izanagi/.codex/worktrees/dev-wave-t2563-calibration-runtime/tools/pegasus/certify_calibration.sh:557)、[CCBench工程](/work/1/SFC/tanab/izanagi/.codex/worktrees/dev-wave-t2563-calibration-runtime/tools/pegasus/certify_calibration.sh:706)
   receipt式の1080秒をこれだけ正すと **6610−1080＋2340＝7870秒**。コピー・検証・条件関門等の追加計上前から7200秒を超えます。これは予約上限の計算であり、実時間の予測ではありません。target削減でも個別timeoutは変わらず、この不足は閉じません。

3. **既存検査の緑だけでは式の整合を証明できません。**
   現行テストは旧1080・6610の文字列を固定しています。[test_pegasus_tools.py:212](/work/1/SFC/tanab/izanagi/.codex/worktrees/dev-wave-t2563-calibration-runtime/orchestrator/tests/test_pegasus_tools.py:212)
   またscaleが実行されない事実から予約分720秒を勝手に差し引けません。CLIの予約式・receipt consumerとの整合が必要です。[cli.py:222](/work/1/SFC/tanab/izanagi/.codex/worktrees/dev-wave-t2563-calibration-runtime/orchestrator/calibrator/cli.py:222)

**独立並列・再利用の評価**

3依存のコピー同士、またコピーとgflags/glog準備は依存上は並列可能です。ただし全コピーの成功確認→pristine検証→消費の順序、失敗時の回収、測定前の全子孫終了を保つ必要があります。30秒内の費用が不明で、並列化を採る実時間上の根拠はありません。

gflags install→glog→CCBenchの依存、job-private fresh build、複製先pristine検証は維持します。共有成果物の再利用はcold/fresh契約を破り、masstreeはsourceへ生成物を書くため共有staging直参照も不可です。[再利用境界](/work/1/SFC/tanab/izanagi/.codex/worktrees/dev-wave-t2563-calibration-runtime/output/insights/2026-09-10/t2535-certify-offline-fetch/README.md:56)

**未確定・後続への短縮計画**

工程別秒数、989271のglogが実際に選んだimport target、候補の全体短縮効果は未確定です。今回は差分を残さず、この不成立根拠を親裁定へ渡すのが最小です。固定条件で成立する構成が静的に得られた場合だけ、既存submitによる同条件before/after各1回を最初の比較とし、全体所要・処理数・既存受理結果を確認します。効果不明なら採用しません。

ファイル変更・テスト・計測・子agent起動は行っていません。検査成功の報告ではありません。
