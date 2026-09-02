## 定義が落とす経路

- `[real / B-unblocked]` P1 は「CCBench を起動する producer」しか層 A に入れないため、未認証の生値を受け取って公式値を新たに導出する importer を producer 件数から落とす。`s8c_result_judge` は caller 申告の `certified=True` 等を通し、raw `throughputs` を受け、issuer は非空文字列、attestation は caller が同じ値から計算できる SHA-256 だけである。`orchestrator/campaign/s8c_result_judge.py:453-459,475-492,505-529,560-573`。その結果を `judge()` が評価し、`publish_result_table()` が `official_status` と `selection_evaluation` を書く。`orchestrator/campaign/s8c_result_judge.py:1959-2028,2316-2329,2413-2443`。プランは層 B でこの seam を拾っているが、P1 の producer 件数を「全経路数」と呼ぶことはできない。
  - 成果物影響: caller が選んだ raw 値で `official_conclusion`、6 cell の `official_status`、選択評価表を変えられる。

- `[coverage]` 「同じ genome + source」は、Genome を持たない事前 build 済み binary、native CLI、shell 経路を一意に分類できない。T-810 は executable SHA、canonical argv、preregistration を束縛して CCBench stdout から throughput を導出するが、Genome は入力にない。`tools/pegasus/t810_pbs_wrapper.py:777-789,978-995`。親 P1 の逐語のままでは除外とも該当とも読め、件数が再現できない。段 2 プランの protocol/configuration/build identity への読み替えはこの穴を認識している。
  - 成果物影響: T-810 は独自 validator に閉じた dormant 経路であり、現状の certified 選択値は変えないため correctness 上は nit。ただし層 A の N は変わる。

- `[sanctioned、欠陥ではない]` calibration と sanity を層 A に残す方針は妥当だが、P1 該当をそのまま欠陥数にしてはいけない。certified calibration は trace-disabled binary を測って registered artifact を発行するが、目的は環境と noise の校正である。`orchestrator/calibrator/sweep.py:236-287`、`orchestrator/calibrator/cli.py:908-928`。qualification は逆に verify 2 件の後だけ bench を認める。`orchestrator/qualification/artifacts.py:1004-1045`。
  - 成果物影響: calibration 値自体は correctness verdict ではない。ただし downstream の環境受理や閾値は変わるので、producer 一覧には残し、欠陥数には入れない。

- floor も「consumer 影響なし」ではない。`load_between_run_floor()` は CV を読み、screening policy に渡す。`orchestrator/campaign/screening_driver.py:305-349,407-414`。その値は pre-verifier reject 閾値に直接入る。`orchestrator/campaign/pipeline.py:1553-1590`。これは D58 が認めた screening の用途であり直ちに欠陥ではないが、単なる記述的 calibration とも言えない。
  - 成果物影響: floor を小さくすると screen-reject が増え、大きくすると verify へ進む候補が増えるため、最終的に certified へ到達しうる候補集合が変わる。

## 走査が覆わない入口

- `[coverage]` プランの実行コード母集合に `output/**/*.sh` と `output/**/*.py` がない。実際に次の再実行可能入口がある。

  - 同一 bytes の T-139 shell が 2 path にあり、CCBench を直接起動して TPS を集計する。`output/env/pegasus/t139-probe/t139_probe_gap.sh:76-87`、`output/insights/2026-07-29_t139-ladder-verbatim/t139_probe_gap.sh:76-87`。
  - profile job body が既存 producer を起動する。`output/insights/2026-08-26_b10-balanced-profile/job-body.sh:191-200`。
  - requested-us job bodyも既存 producer を起動する。`output/insights/2026-08-28_t1941-backoff-requested-us/job-body.sh:381-390`。

  entry_id では少なくとも 4 入口の取りこぼしである。
  - 成果物影響: いずれも probe/profile/diagnostic 用で、現コードから certified report への consumer は確認できないため correctness 上は nit。ただし入口 N の主張は誤る。

- `[coverage]` submodule shell の検索式は狭い。`external/ccbench/cc/*/script` には直接 `.exe` を参照する shell が 116 本ある一方、プランの `ycsb_.*\.exe|grep.*throughput|grep.*latency|perf ...` は 91 file しか返さない。例えば `test_t1k.sh` は `./silo.exe` の stdout 数値を直接平均し、検索語 `ycsb_*.exe`、`grep throughput`、`perf` のいずれも持たない。`external/ccbench/cc/silo/script/test_t1k.sh:10-41`。同型は `external/ccbench/cc/ermia/script/test_t200.sh:9-40` にもある。
  - 成果物影響: upstream `.dat` を読む official consumer は見つからず correctness 上は nit。ただし shell producer 数は少なくとも検索結果だけでは閉じない。

- `external/ccbench` の native `main()` 検索は 45 hit で再現し、ここはプランが覆う。ただし microbench、`replayTest`、`testzip` まで一律 producer にすると過大計上になる。例えば `external/ccbench/cc/silo/replayTest.cc:16` は YCSB 性能 producer ではない。
  - 成果物影響: certified 値は変わらず、分類件数だけが変わるため nit。

- directory 別の確認結果:

  - `orchestrator/calibrator/` は実 producer。direct CLI に加え `python -m calibrator` がある。`orchestrator/calibrator/__main__.py:2-7`。
  - `orchestrator/manual_probes/` の現存 probe は実 build までで、CCBench run はしない。`orchestrator/manual_probes/test_t2000_legacy_build_probe.py:1853-1874`。
  - `orchestrator/qualification/` は build、legacy verify、S2 verify、bench の順を強制するため P1 の負例。`orchestrator/qualification/artifacts.py:1004-1045`。
  - `orchestrator/axis1_search/` と `orchestrator/publication/` の subprocess は Git 専用で、CCBench 起動ではない。`orchestrator/axis1_search/validator.py:75-90`、`orchestrator/publication/ledger.py:255-272`、`orchestrator/publication/report.py:137-167`。
  - test harness の real slow controls は実 binaryを build するだけで、実 bench はしない。`orchestrator/tests/test_s8b_floor_campaign.py:9757-9844`。oracle real-build control も `do_bench=False`。`orchestrator/tests/test_s8b_oracle_driver.py:6026-6088`。`measure_point` tests は fake runner/monkeypatch で condition (a) を満たさない。`orchestrator/tests/test_calibrator.py:383-460`。
  - repo root の CI/cron/service/timer は見つからない。submodule CI は「binary を実行しない」と明記し build のみ。`external/ccbench/.github/workflows/build.yml:68-83`。cron 不在は該当 file がないため file:line 根拠なし。
  - `external/ccbench/third_party/shirakami/**` には独自 benchmark shell があるが、CCBench protocol target からの参照は確認できず、vendored Shirakami 自身の producer と分類するのが妥当。`external/ccbench/third_party/shirakami/bench/bcc_2b/exps.sh:1-55`。
  - 成果物影響: 上記負例を producer に足すと N を水増しするが、certified 値は変わらないため nit。

## 呼出し形態の抜け

- `[coverage]` callable injection の実 edge が直接 caller 一覧から落ちる。

  - `run_sweep()` は既定 `measure_fn=measure_point` を `measure_fn(...)` として呼ぶ。`orchestrator/calibrator/sweep.py:77-113`。
  - `run_sessions()` も同じ既定 binding を持つ。`orchestrator/campaign/s8b_oracle_n_pilot.py:1240-1249,1348-1358`。
  - T-810 は `measurement_run` を注入し、production では `run_allowed_measurement` に束縛する。`tools/pegasus/t810_pbs_wrapper.py:978-995,1102-1108`。

  プランは `measurement_run` を文章で挙げるが、実行検索式は `measure_fn`、`measurement_run` を拾わない。
  - 成果物影響: pilot/calibration/T-810 の測定入口が N から消える。現状それ自体による certified correctness 迂回は確認できず nit。

- `[coverage]` subprocess 検索は `subprocess.*` と `os.spawn*` を拾うが、`os.exec*` を拾わない。

  - `exec_calibrate.py` は JSON の任意 argv を `os.execv` する。`tools/pegasus/exec_calibrate.py:24-43`。実運用では calibrator certified CLI に接続される。`tools/pegasus/certify_calibration.sh:778-799`。
  - generic compute dispatch は `<argv>` を許し、`os.execvpe` で起動する。`tools/pegasus/dispatch_compute.py:153-160,286-293,1311-1321`。
  - 成果物影響: 前者は registered calibration を作れる別入口なので、環境 admission の受理集合に影響しうる。後者は target 依存の unresolved dynamic entry であり、blocked と丸められない。

- `python3 -m` は `__main__` 列挙で間接的には拾えるが、shell/process 検索式には `-m` がない。実例は `tools/pegasus/b10_backoff_shape_campaign.sh:339-350` と `orchestrator/campaign/b10_backoff_shape_sweep.py:3999-4020`。
  - 成果物影響: formal producer の入口件数を過少計上しうるが、同じ内部 producerへ畳まれるため spawn 実装数は変わらず nit。

- public function 用 regex は行頭 `def` だけなので class method を拾わない。またプラン自身が「先頭 underscore は barrier ではない」としているのに、`_Runner.run()` のような method は検索外である。`orchestrator/campaign/s8b_floor_campaign.py:5847,6096,6341`。
  - 成果物影響: floor producer の entry graph が欠け、将来 refreeze eligibility の評価対象を落としうる。

- `getattr`、dynamic import、monkeypatch について、現 repo で production CCBench producerへ直結する追加例は確認できなかった。`tools/pegasus/run_probe.py:29-38` の dynamic import/getattr は固定された環境 probeであり負例。monkeypatch 経路は test synthetic である。
  - 成果物影響: 現状の certified 値への具体的影響は確認できず nit。

## 親の実測値の再現結果

- `rg -n 'trace=False' orchestrator` から `orchestrator/tests/**` だけを除くと、親記載どおり **18 hit**。内訳は 14 executable syntax と 4 comment/doc/error-string である。

  - 4 textual: `s8b_binary_admission.py:250`、`s8b_floor_campaign.py:20,29`、`between_run_floor.py:24`。
  - executable 14 のうち、親の campaign 一覧 12 件はすべて一致する。
  - 親一覧が落とした campaign code は `orchestrator/campaign/s2_verify_calibration.py:232`。
  - campaign 外の executable hit は `orchestrator/manual_probes/test_t2000_legacy_build_probe.py:1862`。
  - 「test 除外」を `manual_probes/test_*` にも適用する意味なら 17 hit になる。したがって 18 は「`orchestrator/tests/**` 除外」の条件付きで再現可能。

- `measure_point` caller は次のように再現した。

  - executable な直接 `measure_point(...)` call は **11 site**。親の `s8b_floor_campaign.py:7684,7690`、`calibrator/sweep.py:236,244`、`pipeline.py:739,747,2027`、`pegasus_floor_scoping.py:137,144`、`between_run_floor.py:213,220` と一致する。
  - `s8b_floor_attempt_launcher.py:435` は `measure_point` ではなく **`capture_measure_point` の 1 site**。
  - したがって親の表は「11 direct measure + 1 capture」の計12 siteとしては正しいが、「measure_point caller 一覧」というラベルは不正確。
  - さらに callable default 経由が少なくとも 2 edgeある。`orchestrator/calibrator/sweep.py:84,113`、`orchestrator/campaign/s8b_oracle_n_pilot.py:1245,1348`。これらを caller graph に含めると、親一覧は完全ではない。

- 成果物影響: `trace=False` の headline 18 は維持できるが、実行 site と caller graph の件数は親表のままでは undercount する。certified 値そのものへの直接影響はなく、閉包成果物の件数誤りである。

## 親の一般化への指摘

- P5 の「D1360 / D58 / certified writer admission の 3 層で全経路が塞がる」はコード構造として成立しない。`require_certified_writer_authorization` の production caller は `screening_driver`、`loop`、`s1_direct_comparison`、`pipeline` の 5 siteだけである。`orchestrator/campaign/execution_guard.py:107-140`、caller は `orchestrator/campaign/screening_driver.py:399,488`、`orchestrator/campaign/loop.py:172`、`orchestrator/campaign/s1_direct_comparison.py:1004`、`orchestrator/campaign/pipeline.py:1030`。calibrator、T-810、standalone profile、submodule shell、S8c judge はこの層を通らない。
  - 成果物影響: 3 層を全称的 barrier とすると、別 admission の producerを誤って B-blocked に分類し、公式受理集合の監査対象を落とす。

- D1360 は policy decision であって共通 code gate ではない。実行コード上の D1360 参照は genome 登録のコメントだけである。`orchestrator/campaign/genome.py:208`。従って「D1360 で塞がる」を file:line の実装根拠としては使えない。
  - 成果物影響: stock-only producerの値を拒否する具体 consumerを確認せず blocked 扱いすると、report/selector の受理集合を過大評価する。

- 別系統にはそれぞれ別の barrier がある。

  - calibration は quality 判定と registered publish。`orchestrator/calibrator/cli.py:908-928`。
  - T-810 は preregistered executable/argv、AuthorizationToken、completion validator。`tools/pegasus/t810_runner_policy.py:122-180`、`orchestrator/campaign/t810_validator.py:940-1010`。
  - qualification は verify-first topology。`orchestrator/qualification/artifacts.py:1004-1045`。
  - S8c は floor bytesだけは検証するが、observation issuerを認証しない。`orchestrator/campaign/s8c_result_judge.py:2124-2190` と同 `:453-529`。

  - 成果物影響: これらを D1360/D58/writer の三層へ丸めると、独自 barrier の欠落または外部 trust を発見できず、`official_status`、registered calibration、formal measurement の受理集合を誤判定する。

- 最も具体的な未閉包は S8c observation seam である。floor receipt の型は閉じていても、性能 observation の correctness と issuer は caller 自己申告である。従って P5 は少なくとも repo 内静的事実から `closed` と判定できず、現状は `B-unblocked` である。
  - 成果物影響: spoofした raw throughput から `official_status`、`selection_evaluation`、全体 conclusionを生成できる。

## 総括

親の 18 hit は条件付きで再現したが、閉包の N はまだ主張できない。主要な取りこぼしは、`output/` の再実行入口、external shell 検索で落ちる 25 file、`os.exec*`、callable default edge、raw値から公式表を作る S8c consumerである。

実在する correctness 関連の所見は S8c の caller-self-attested observation seam。floor/calibration、T-810、profile、upstream shellは producer 一覧には必要だが、それだけで欠陥ではない。test harness、qualification、axis1、publication、submodule CI には追加の未検証 CCBench producerを確認しなかった。

以上は read-only の静的検査のみで、build、benchmark、測定、pytest は実行していない。