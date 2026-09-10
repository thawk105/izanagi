## 総括

protocol と実際の build target を食い違わせる、受理可能な env / receipt 組は構成できない。束縛は端から端まで閉じている。  
最も重い所見は、単位 B が追加した 15 test node が受入所要時間台帳へ未登録であること。  
受理集合は意図どおり mocc / tictoc へ拡張され、protocol 不明・不一致 receipt に対して縮小している。cicada の迂回経路もない。  
指示どおりテストは実行せず、差分・実装・既存成果物を静的検査した。既知の build sink 回帰は所見に含めていない。

## 所見

### 1. 新規 15 test node が受入台帳に未登録

- 重大度: **must-fix**
- 成果物影響: acceptance の loadgroup scheduling で全 15 node が未知所要時間として扱われ、実測台帳による並列配置が不完全になる。
- 根拠の file:line:
  - [orchestrator/tests/test_pegasus_calibration_workload.py:192](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2224-certify-protocol-axes/orchestrator/tests/test_pegasus_calibration_workload.py:192)
  - [orchestrator/tests/test_pegasus_calibration_workload.py:376](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2224-certify-protocol-axes/orchestrator/tests/test_pegasus_calibration_workload.py:376)
  - [orchestrator/tests/test_pegasus_calibration_workload.py:468](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2224-certify-protocol-axes/orchestrator/tests/test_pegasus_calibration_workload.py:468)
  - [orchestrator/tests/test_pegasus_tools.py:1574](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2224-certify-protocol-axes/orchestrator/tests/test_pegasus_tools.py:1574)
  - [orchestrator/tests/acceptance_duration_ledger.json:22159](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2224-certify-protocol-axes/orchestrator/tests/acceptance_duration_ledger.json:22159)
  - [tools/update_acceptance_duration_ledger.py:314](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2224-certify-protocol-axes/tools/update_acceptance_duration_ledger.py:314)
  - [orchestrator/tests/conftest.py:1636](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2224-certify-protocol-axes/orchestrator/tests/conftest.py:1636)
- 再現手順または反例: 下記 15 node の関数名を台帳で検索すると全件 0 hit。被覆 producer は通常の `.py::node` を collection に取り込み、これらの suite は add-only 除外対象でもない。親の実測 JUnit を正本 producer に渡して追加する必要がある。値はここでは作らない。

### 2. README は失敗時の `job-result.json` 生成条件を誤記している

- 重大度: **nit**
- 成果物影響: calibrator 失敗の調査時に、存在するはずの `job-result.json` を「成功時だけの成果物」と誤認し得る。
- 根拠の file:line:
  - [tools/pegasus/README.md:170](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2224-certify-protocol-axes/tools/pegasus/README.md:170)
  - [tools/pegasus/certify_calibration.sh:859](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2224-certify-protocol-axes/tools/pegasus/certify_calibration.sh:859)
  - [tools/pegasus/certify_calibration.sh:864](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2224-certify-protocol-axes/tools/pegasus/certify_calibration.sh:864)
  - [tools/pegasus/certify_calibration.sh:885](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2224-certify-protocol-axes/tools/pegasus/certify_calibration.sh:885)
- 再現手順または反例: `calibrate_rc != 0` では post-attestation だけが省略される。その直後に `job-result.json` が書かれ、さらに後で非零終了する。README の「成功時だけ post-attestation と job-result」は実装と一致しない。

## 検査した 6 項目への回答

1. **protocol の端から端までの束縛**

   閉じている。submitter は値を whitelist 後、`pre-submit.json`、明示時の qsub env、`submit-receipt.json` に同じ値から書く。[submit_certify.sh:44](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2224-certify-protocol-axes/tools/pegasus/submit_certify.sh:44)、[submit_certify.sh:174](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2224-certify-protocol-axes/tools/pegasus/submit_certify.sh:174)、[submit_certify.sh:189](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2224-certify-protocol-axes/tools/pegasus/submit_certify.sh:189)、[submit_certify.sh:253](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2224-certify-protocol-axes/tools/pegasus/submit_certify.sh:253)。

   job は env の実効値を whitelist し、receipt と exact equality で比較する。[certify_calibration.sh:162](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2224-certify-protocol-axes/tools/pegasus/certify_calibration.sh:162)、[certify_calibration.sh:224](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2224-certify-protocol-axes/tools/pegasus/certify_calibration.sh:224)。同じ shell 変数から build target と binary path を導出し、実行した配列を acquisition receipt の `build_argv` に保存する。[certify_calibration.sh:589](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2224-certify-protocol-axes/tools/pegasus/certify_calibration.sh:589)、[certify_calibration.sh:593](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2224-certify-protocol-axes/tools/pegasus/certify_calibration.sh:593)、[certify_calibration.sh:704](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2224-certify-protocol-axes/tools/pegasus/certify_calibration.sh:704)。

   calibrator は `--target ycsb_<protocol>.exe` から protocol を導出し、binary basename との一致、登録済み protocol、全軸の存在を検査する。[cli.py:396](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2224-certify-protocol-axes/orchestrator/calibrator/cli.py:396)、[cli.py:415](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2224-certify-protocol-axes/orchestrator/calibrator/cli.py:415)、[cli.py:455](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2224-certify-protocol-axes/orchestrator/calibrator/cli.py:455)。測定前に binary hash も再計算する。[cli.py:843](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2224-certify-protocol-axes/orchestrator/calibrator/cli.py:843)。

   反例候補はいずれも拒否される。

   - env 未設定 + receipt `mocc` → job 既定は `silo`、receipt mismatch。
   - env `mocc` + receipt `silo` → receipt mismatch。
   - env `cicada` + receipt `cicada` → job whitelist で receipt 読取り前に拒否。
   - 通る組は「未設定+silo」「silo+silo」「mocc+mocc」「tictoc+tictoc」だけで、それぞれ同名 target/path を build する。

   `job-result.json` は canonical genome を再読取せず env 値を書くが、同じ値が target/path の唯一の導出元であり、途中に入力による再代入箇所はない。[certify_calibration.sh:864](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2224-certify-protocol-axes/tools/pegasus/certify_calibration.sh:864)。

2. **省略時と明示時の非対称**

   検査強度は同じ。省略時だけ qsub env token がなく、job の `${IZANAGI_CALIBRATION_PROTOCOL-silo}` が `silo` を採る。以後は明示 `silo` と同じ whitelist、receipt equality、target/binary、canonical genome 検査を通る。検査数に差はない。

   qsub argv は省略時だけ旧 bytes を維持し、明示 `--protocol silo` では protocol env が追加される。[submit_certify.sh:189](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2224-certify-protocol-axes/tools/pegasus/submit_certify.sh:189)。両方とも receipt には `silo` が記録される。

3. **受理集合の縮小と拡大**

   変更後に拒否されるもの:

   - matching rratio を持つが `calibration.protocol` がない submit receipt。
   - env protocol と receipt protocol が異なる組。
   - env protocol が空、cicada、ermia その他 whitelist 外の値。
   - env 未設定で receipt が mocc / tictoc の組。

   変更後に新たに受理されるもの:

   - submit CLI の明示 `--protocol silo`、`--protocol mocc`、`--protocol tictoc`。変更前はいずれも unknown argument。
   - 成果物として新たに生産可能になった protocol は mocc / tictoc。変更前の job は protocol env を無視して常に silo target を build していた。
   - protocol 省略は変更前後とも受理され、実効 target は silo。

   repo 内の歴史的成果物は 12 submit receipt とその job-staging copy 12 件、計 24 ファイルあり、全件 protocol だけでなく `calibration` 自体がない。代表例は schema 行の直後に source/nonce で文書が終わる。[submit-receipt.json:34](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2224-certify-protocol-axes/output/env/pegasus/calibration/attempts/submissions/1cf9eab79d668682919ce2364e0ceafd/submit-receipt.json:34)。したがってこれらは変更前から既存 `calibration_rratio` check で拒否される形であり、protocol check が実効受理集合をさらに狭めるものではない。

   一方、「matching rratio はあるが protocol だけない」旧 fixture 形は新たに拒否される。関連 fixture は protocol 付きへ更新済みで、残存する certify binding fixture の破損は見つからなかった。[test_pegasus_tools.py:1491](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2224-certify-protocol-axes/orchestrator/tests/test_pegasus_tools.py:1491)、[test_pegasus_tools.py:1532](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2224-certify-protocol-axes/orchestrator/tests/test_pegasus_tools.py:1532)。既存 registered calibration は submit receipt を再消費しないため影響しない。

4. **cicada の除外**

   両段で閉じている。submitter と job の双方が `{silo,mocc,tictoc}` exact whitelist を持つ。[submit_certify.sh:44](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2224-certify-protocol-axes/tools/pegasus/submit_certify.sh:44)、[certify_calibration.sh:163](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2224-certify-protocol-axes/tools/pegasus/certify_calibration.sh:163)。

   submitter を迂回して job へ `IZANAGI_CALIBRATION_PROTOCOL=cicada` を渡しても job 自身が拒否する。job を迂回して calibrator を直接呼ぶことは別の入口であり、certify job への迂回にはならない。

5. **新規 test node と受入台帳**

   15 node は通常の `.py::node` なので、producer の `--coverage-against` に collection を渡せば全件が被覆分母に入る。[update_acceptance_duration_ledger.py:285](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2224-certify-protocol-axes/tools/update_acceptance_duration_ledger.py:285)。add-only 除外対象にも該当しない。[update_acceptance_duration_ledger.py:428](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2224-certify-protocol-axes/tools/update_acceptance_duration_ledger.py:428)。

   現在の台帳には全件未登録。ただし `--coverage-against` 自体は比率を表示するだけで、不完全被覆を非零終了させる gate ではない。[update_acceptance_duration_ledger.py:323](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2224-certify-protocol-axes/tools/update_acceptance_duration_ledger.py:323)。必要な node は次節に列挙する。

6. **README と実装**

   cicada 除外理由は一致する。README の `INLINE_VERSION_OPT` 対 `CCBENCH_INLINE_VERSION_OPT_CICADA` は実物の [Options.cmake:53](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2224-certify-protocol-axes/external/ccbench/cmake/Options.cmake:53) と [cc/cicada/CMakeLists.txt:5](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2224-certify-protocol-axes/external/ccbench/cc/cicada/CMakeLists.txt:5) に合う。

   `BACKOFF_FIXED=-1` と condition gate の silo 限定も実装と一致する。[README.md:147](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2224-certify-protocol-axes/tools/pegasus/README.md:147)、[certify_calibration.sh:586](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2224-certify-protocol-axes/tools/pegasus/certify_calibration.sh:586)。現行 CCBench 全体に `BACKOFF_FIXED` がないことも静的検索で確認した。

   不一致は所見 2 の `job-result.json` 生成条件だけ。

## 受入台帳に足す必要がある node

- `orchestrator/tests/test_pegasus_calibration_workload.py::test_certify_shell_protocol_axes_match_independent_genome_spaces`
- `orchestrator/tests/test_pegasus_calibration_workload.py::test_certify_non_silo_defines_contain_no_axis_outsider[mocc]`
- `orchestrator/tests/test_pegasus_calibration_workload.py::test_certify_non_silo_defines_contain_no_axis_outsider[tictoc]`
- `orchestrator/tests/test_pegasus_calibration_workload.py::test_certify_derives_protocol_target_and_binary_path[silo]`
- `orchestrator/tests/test_pegasus_calibration_workload.py::test_certify_derives_protocol_target_and_binary_path[mocc]`
- `orchestrator/tests/test_pegasus_calibration_workload.py::test_certify_derives_protocol_target_and_binary_path[tictoc]`
- `orchestrator/tests/test_pegasus_calibration_workload.py::test_certify_keeps_backoff_fixed_and_condition_gate_silo_only`
- `orchestrator/tests/test_pegasus_calibration_workload.py::test_default_silo_build_and_calibrate_argv_are_byte_compatible`
- `orchestrator/tests/test_pegasus_calibration_workload.py::test_submitter_rejects_unregistered_protocol_before_side_effects[cicada]`
- `orchestrator/tests/test_pegasus_calibration_workload.py::test_submitter_rejects_unregistered_protocol_before_side_effects[ermia]`
- `orchestrator/tests/test_pegasus_calibration_workload.py::test_submitter_accepts_exact_protocol_whitelist_and_records_it[silo]`
- `orchestrator/tests/test_pegasus_calibration_workload.py::test_submitter_accepts_exact_protocol_whitelist_and_records_it[mocc]`
- `orchestrator/tests/test_pegasus_calibration_workload.py::test_submitter_accepts_exact_protocol_whitelist_and_records_it[tictoc]`
- `orchestrator/tests/test_pegasus_calibration_workload.py::test_submitter_omitted_protocol_is_silo_without_changing_qsub_argv`
- `orchestrator/tests/test_pegasus_tools.py::test_certify_submit_binding_requires_matching_calibration_protocol`