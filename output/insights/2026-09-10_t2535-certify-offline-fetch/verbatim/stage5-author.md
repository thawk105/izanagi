## 総括

段 4「plan v2」を指定 3 file のみに実装しました。submit は hydrate・clone・git を起動せず、job が staging root を自導出し、copy root と `FETCHCONTENT_BASE_DIR` を分離します。commit・git 状態変更・計算ノード投入は行っていません。

copy 3 本と pristine verifier は各 120 秒上限です。約 77 MiB の既知規模に十分な余裕を持たせつつ、既存 CCBench 900 秒 envelope 内で有限停止させるためです。walltime 式は変更していません。

## 変更した file と行

- [certify_calibration.sh](/work/1/SFC/tanab/izanagi/.codex/worktrees/t2535-author/tools/pegasus/certify_calibration.sh:170)
  - 170–185: staging root と三子の構造検査。
  - 551–588: 分離した二 directory、timeout 付き `cp -a`、pristine verifier。
  - 629–640: 指定順の FetchContent 5 token。
- [submit_certify.sh](/work/1/SFC/tanab/izanagi/.codex/worktrees/t2535-author/tools/pegasus/submit_certify.sh:51)
  - 51–64: job script 検査前の staging 構造 precheck。
- [test_pegasus_calibration_workload.py](/work/1/SFC/tanab/izanagi/.codex/worktrees/t2535-author/orchestrator/tests/test_pegasus_calibration_workload.py:115)
  - fixture 変数、gate argv snapshot、exact argv pin を更新。
  - 新規 6 テストは 539–823 付近。
  - submit dry-run fixture に有効な staging layout を追加。

## 変異 M1-M7 をどのテストが殺すか

| 変異 | 殺すテスト |
|---|---|
| M1 | offline contract 共通性、実 CMake configure |
| M2 | 実 CMake configure の正例・解決 path 照合 |
| M3 | ignored artifact 拒否 |
| M4 | copy loop exact pin、実 CMake、copy 正例 |
| M5 | condition gate が受け取る slice の snapshot |
| M6 | 実 CMake の分離負例と coupled-base 対照 |
| M7 | missing/malformed staging test。submit と job 両方を実走 |

## 実走した検査 (nodeid と範囲)

`PYTHONPATH=.` の自走 harness で実行しました。pytest の緑は主張しません。

- 新規 6 nodeid: 全件 PASS。
- 実 CMake configure:
  - 三 local source 正例。
  - SOURCE_DIR 三本の各欠落が非ゼロ。
  - `FULLY_DISCONNECTED` 欠落時の `.invalid` 取得が非ゼロ。外部 `timeout` は5秒。
  - source root と BASE_DIR を結合した対照では mimalloc token 欠落が成功し、M6 の差を確認。
- production copy+verifier fragment:
  - pristine 正例 PASS。
  - ignored artifact 負例 rc=2。
  - upstream bytes/inode 不変と copy 側書込みを確認。
- 同 test file の全27 test 定義、parametrize 展開込み35呼出しを自走。
- exact qsub pin、protocol 3種、既定 silo、scheduler path の既存検査を確認。
- `test_calibration_shell_scripts_parse` PASS。
- 固定 anchor、walltime 文字列、qsub argv、変更禁止の2テストを HEAD と静的照合。
- `git diff --check` PASS。変更 file は指定された3件のみ。

## 実装済み・未実走

- `tools/run_tests.py` と pytest は、指定された sandbox 制約に従い未実走です。
- 実 CCBench configure/build、計算ノード job、qsub、較正、record publish は未実走です。
- condition gate への5 token転送は shell stub の snapshot までです。Python gate 側の消費は未実走です。
- `test_pegasus_tools.py` など所有外 consumer test は未実走です。

## 現行の受理・拒否挙動と変えた点

- protocol `{silo,mocc,tictoc}`、ratio `{20,50,80}`、既定 silo は不変です。
- 不正 ratio/protocol の副作用前拒否も不変です。
- 有効 protocol でも staging root または三子が欠落・symlink・非 directory なら、新たに rc=2 で拒否します。
- job 側は `third_party_source` failure を記録します。
- submit は構造検査のみで、hydrate・clone・git は追加していません。
- qsub export spec、argv、receipt schema/field は不変です。
- 条件関門の判定式・受理集合・既定値は不変です。有効な offline source により、従来 FetchContent で前段停止した呼出しだけ到達可能になります。

## 所有外 caller・共有 fixture・consumer test への波及 (静的列挙)

- `run_condition_gate`: `${configure_argv[@]:5}` を通じて5 tokenを受領。
- CCBench `ThirdParty.cmake`: masstree・mimalloc・googletest を local source から解決。
- acquisition receipt: `ccbench.build_argv` の token が増えるだけで schema は不変。
- calibrator genome 復元: `-DCCBENCH_` 以外を無視するため不変。
- toolchain binding、silo provenance、layer3 report:既存抽出対象外。
- downstream calibration consumers: `loop.py`、`screening_driver.py`、`env_contract.py`、floor/oracle/freeze drivers、`silo_ladder_rung1.py`、`floor_pair_driver.py`、`certified_writer_admission.py`、`t126_driver.py`、`p2_2.py`。
- 未実走 consumer tests: `test_pegasus_tools.py`、`test_calibrator_certify.py`、`test_schema_v2.py`、`test_silo_ladder_rung1_evidence.py`、`test_s8b_floor_campaign.py`、`test_ccbench_spawn_sites.py`、`test_official_perf_closure.py`。

## 期待される赤

- SOURCE_DIR 各欠落、`FULLY_DISCONNECTED` 欠落、ignored artifact、missing/symlink staging は意図どおり非ゼロでした。
- sandbox で `tools/run_tests.py` を走らせれば既知の `qstat EACCTAUTH Unknown user-id` が予想されるため未実行です。
- silo の実認定は pristine masstree に `config.h` がない条件関門問題で赤になり得ます。T-2534 の裁定対象です。

## 未解決

- 計算ノードでの実 CCBench configure/build と較正 record publish。
- T-2534 の silo 条件関門。
- submit が検査した checkout と job の `PBS_O_WORKDIR` を束縛しない既存 P4。
- receipt が第三者 pin を記録しない既存契約。
- 6910 / 6610 の既存 walltime 不一致。今回は1 byteも変更していません。