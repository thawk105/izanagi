## 所見

### B-1. within-run calibration の protocol 閉包が未実装のまま残る

- 主張: プランは「protocol 別 calibration」を完了しない。将来 producer に top-level `genome` を足すだけでは成立せず、certified schema、保存先、Layer 3 の探索、calibration report consumer まで同時変更が必要である。
- 根拠:
  - プラン自身が producer 拡張を scope 外へ送っている: [plan.md:93](</work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2115-cross-protocol-impl/artifacts/dev-wave-t2115-cross-protocol-impl/plan.md:93>)。
  - 現 producer の出力に protocol/genome はない: [report.py:72](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2115-cross-protocol-impl/orchestrator/calibrator/report.py:72)。
  - certified `calibration/v2` は exact top-level key 集合を強制し、`genome` を許さない: [schema_v2.py:563](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2115-cross-protocol-impl/orchestrator/calibrator/schema_v2.py:563)、[schema_v2.py:740](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2115-cross-protocol-impl/orchestrator/calibrator/schema_v2.py:740)。
  - certified artifact は `calibration/registered/` に publish される: [cli.py:925](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2115-cross-protocol-impl/orchestrator/calibrator/cli.py:925)。実在する2件も `genome=null` だった。
  - Layer 3 は直下の `*.json` しか走査せず `registered/` を見ない: [layer3_report.py:337](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2115-cross-protocol-impl/orchestrator/campaign/layer3_report.py:337)。
  - 別 consumer は calibration JSON を読む一方、再現 build/run を `ycsb_silo` に固定する: [calibration_report.py:19](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2115-cross-protocol-impl/orchestrator/reports/calibration_report.py:19)、[calibration_report.py:27](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2115-cross-protocol-impl/orchestrator/reports/calibration_report.py:27)。
  - 上位台帳は明示的に「protocol 別 calibration」を含む: [phase3.md:360](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2115-cross-protocol-impl/docs/phase3.md:360)。
- 成り立つ場合の成果物影響: 将来の mocc Layer 3 report は `within_run.value=null` のままか、certified calibration を発見できず、source path/hash も付かない。calibration report の再現コマンドは誤って silo を指す。現時点では certified selection consumer 自体が未実装なので、今日の certified 選択集合は変わらない: [layer3_report.py:634](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2115-cross-protocol-impl/orchestrator/campaign/layer3_report.py:634)。
- 確信度: 高。

### B-2. screening の照合述語は Layer 3 と揃っていない

- 主張: プランは screening を `(protocol, workload)` にするだけで、floor の物理点を決める `records` と `threads` を照合しない。「照合キーを揃える」という説明は成立しない。
- 根拠:
  - 現 loader は workload しか比較しない: [screening_driver.py:126](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2115-cross-protocol-impl/orchestrator/campaign/screening_driver.py:126)。
  - プランの変更案にも protocol 以外の追加がない: [plan.md:62](</work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2115-cross-protocol-impl/artifacts/dev-wave-t2115-cross-protocol-impl/plan.md:62>)。
  - Layer 3 は既に records、threads、workload を全部比較し、プラン後は protocol も足す: [layer3_report.py:379](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2115-cross-protocol-impl/orchestrator/campaign/layer3_report.py:379)。
  - 3 caller の config には照合可能な records/threads が実在する: [backoff_sweep.py:103](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2115-cross-protocol-impl/orchestrator/campaign/backoff_sweep.py:103)、[s6_sort_sweep.py:194](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2115-cross-protocol-impl/orchestrator/campaign/s6_sort_sweep.py:194)、[s8a_trigger_sweep.py:289](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2115-cross-protocol-impl/orchestrator/campaign/s8a_trigger_sweep.py:289)。
  - screening は workload 値を文字列化するが、Layer 3 は dict の exact equality を使うため、正規化規則も揃っていない。
- 成り立つ場合の成果物影響: 同 protocol・同 workload で別 thread/record 点の floor が1件だけなら誤った CV を採用し、screening の候補受理集合が変わる。複数置けば不要な一意性違反になる。
- 確信度: 高。

### B-3. canonical genome の検証述語が二重化・未定義である

- 主張: `|` より前を取るだけでは canonical 検証にならない。screening と Layer 3 の両方が floor JSON を解析するのに、プランは共有契約を定めていない。
- 根拠:
  - プランは Layer 3 に「局所 helper」を置く一方、screening 側は「canonical 不正を拒否」とだけ述べる: [plan.md:65](</work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2115-cross-protocol-impl/artifacts/dev-wave-t2115-cross-protocol-impl/plan.md:65>)、[plan.md:87](</work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2115-cross-protocol-impl/artifacts/dev-wave-t2115-cross-protocol-impl/plan.md:87>)。
  - `Genome` 自体は protocol や flag key の文法を検査しない: [model.py:39](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2115-cross-protocol-impl/orchestrator/campaign/model.py:39)。
  - repository には parse、整数化、重複 key 拒否、再 canonical 化まで行う exact parser が既にある: [artifact_admission.py:744](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2115-cross-protocol-impl/orchestrator/campaign/artifact_admission.py:744)。ただし private helper である。
- 成り立つ場合の成果物影響: malformed な floor `genome` を一方の consumer だけが protocol 一致として採ると、screening の閾値または Layer 3 の floor source/value が誤帰属する。
- 確信度: 高。

### B-4. 焦点テスト集合が consumer 閉包を覆っていない

- 主張: 専用 unit test は厚いが、変更する caller と repository 内容走査型 test の焦点走が不足している。
- 根拠:
  - s6/s8a の protocol 転送を検査する nodeid がない。プランが挙げる転送検査は backoff の2件だけ: [plan.md:162](</work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2115-cross-protocol-impl/artifacts/dev-wave-t2115-cross-protocol-impl/plan.md:162>)。
  - 3 caller を横断する test は実在する: [test_screening_opt_in.py:14](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2115-cross-protocol-impl/orchestrator/tests/test_screening_opt_in.py:14)。直接 module consumer として `test_backoff_sweep.py`、`test_s6_sort_sweep.py`、`test_s8a_trigger_sweep.py` もある。
  - `between_run_floor.py` の call-site 数を全 production file から AST 走査する test がある: [test_s8b_floor_campaign.py:1588](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2115-cross-protocol-impl/orchestrator/tests/test_s8b_floor_campaign.py:1588)。
  - `screening_driver.py` と `layer3_report.py` を exact inventory で走査する test がある: [test_official_perf_closure.py:774](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2115-cross-protocol-impl/orchestrator/tests/test_official_perf_closure.py:774)。
  - production Python 全体の process launch inventory には Layer 3 が含まれる: [test_ccbench_spawn_sites.py:315](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2115-cross-protocol-impl/orchestrator/tests/test_ccbench_spawn_sites.py:315)。
  - scoping prefix の非接続性を固定する test も計画外: [test_pegasus_floor_scoping.py:187](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2115-cross-protocol-impl/orchestrator/tests/test_pegasus_floor_scoping.py:187)。
- 成り立つ場合の成果物影響: 一意の値変化には結び付けられない。特に s6/s8a の誤った protocol 転送を見逃すと、B-2 と同じ screening 受理集合の誤りになる。
- 確信度: 高。

### B-5. 「編集面4 file」と凍結影響の根拠は成立しない

- 主張: production 編集面はプランどおりなら8 file であり、追加された caller 3本は凍結成果物の内部 source hash から参照されている。トップレベル manifest に最初の4 file がないことだけでは閉包証明にならない。
- 根拠:
  - プランの production 対象は `genome.py`、`between_run_floor.py`、`screening_driver.py`、3 caller、`layer3_report.py`、schema の計8本: [plan.md:3](</work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2115-cross-protocol-impl/artifacts/dev-wave-t2115-cross-protocol-impl/plan.md:3>)、[plan.md:54](</work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2115-cross-protocol-impl/artifacts/dev-wave-t2115-cross-protocol-impl/plan.md:54>)、[plan.md:76](</work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2115-cross-protocol-impl/artifacts/dev-wave-t2115-cross-protocol-impl/plan.md:76>)、[plan.md:101](</work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2115-cross-protocol-impl/artifacts/dev-wave-t2115-cross-protocol-impl/plan.md:101>)。
  - `known_axes_freeze.json` は backoff/s6/s8a の source sha を保持する: [known_axes_freeze.json:153](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2115-cross-protocol-impl/output/s1-freeze/known_axes_freeze.json:153)、[known_axes_freeze.json:201](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2115-cross-protocol-impl/output/s1-freeze/known_axes_freeze.json:201)、[known_axes_freeze.json:52](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2115-cross-protocol-impl/output/s1-freeze/known_axes_freeze.json:52)。
  - T-080 migration と oracle test にも同じ path/hash 集合が固定される: [t080_freeze_migration.py:91](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2115-cross-protocol-impl/orchestrator/campaign/t080_freeze_migration.py:91)、[test_s8b_oracle_driver.py:146](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2115-cross-protocol-impl/orchestrator/tests/test_s8b_oracle_driver.py:146)。
  - 現在は live bytes 検査の一部がユーザー裁定で hold 中: [freeze_verification_hold.py:14](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2115-cross-protocol-impl/orchestrator/campaign/freeze_verification_hold.py:14)。
- 成り立つ場合の成果物影響: 凍結 JSON の bytes を更新すべきではないが、凍結検証の availability/held marker と migration test が影響面になる。certified 選択値そのものの変更はない。
- 確信度: 高。

### B-6. mocc は「可変3軸・YCSBで8通り」が正確で、「live 3軸」は不正確

- 主張: プランの8 genome は現 CMake から操作可能な YCSB 空間として正しい。ただし `RWLOCK` も live なコード分岐なので、親の「live 軸3本」は用語上誤りである。また `KEY_SORT` は YCSB 固有なので「effective 8」は workload 条件付きである。
- 根拠:
  - cache から操作可能なのは universal `BACK_OFF`、mocc の `TEMPERATURE_RESET_OPT`、`KEY_SORT`: [Options.cmake:20](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2115-cross-protocol-impl/external/ccbench/cmake/Options.cmake:20)、[Options.cmake:26](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2115-cross-protocol-impl/external/ccbench/cmake/Options.cmake:26)、[Options.cmake:48](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2115-cross-protocol-impl/external/ccbench/cmake/Options.cmake:48)。
  - `RWLOCK` は bare define だが実コード分岐を持つ: [mocc/CMakeLists.txt:5](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2115-cross-protocol-impl/external/ccbench/cc/mocc/CMakeLists.txt:5)、[transaction.cc:166](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2115-cross-protocol-impl/external/ccbench/cc/mocc/transaction.cc:166)。
  - anatomy はこの固定 live 分岐も数えて mocc を `2^4=16` とする一方、bare define なので cache から直交操作不能とも明記する: [ccbench-anatomy.md:95](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2115-cross-protocol-impl/docs/ccbench-anatomy.md:95)、[ccbench-anatomy.md:111](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2115-cross-protocol-impl/docs/ccbench-anatomy.md:111)、[ccbench-anatomy.md:125](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2115-cross-protocol-impl/docs/ccbench-anatomy.md:125)。
  - `KEY_SORT` の live site は YCSB header だけだが、mocc target は4 workload を持つ: [ycsb.hh:81](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2115-cross-protocol-impl/external/ccbench/include/ycsb.hh:81)、[mocc/CMakeLists.txt:3](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2115-cross-protocol-impl/external/ccbench/cc/mocc/CMakeLists.txt:3)。
- 成り立つ場合の成果物影響: YCSB の `space_for("mocc")` 受理集合は8でよい。非 YCSB に同じ空間を流用すると KEY_SORT on/off が実効重複になり、列挙台帳の raw/effective 数が誤る。現在 production caller はない。
- 確信度: 高。

### B-7. 後方互換は実在 artifact にはほぼ成立するが、説明は広すぎる

- 主張: 実在する4件の between-run JSON と v2 Layer 3 report は bytes 無変更で読める。一方、genome-less screening fixture は意図的非互換になり、実在する Layer 3 v1 report は現 readerで既に読めない。
- 根拠:
  - 実在する `between_run_noise_*.json` は4件で、全件 `silo|...`、records=1,000,000、threads=48 を持つ。linux-baremetal 3 workload + pegasus rr95 1件である。
  - プランは genome 欠落 floor を新たに拒否する: [plan.md:142](</work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2115-cross-protocol-impl/artifacts/dev-wave-t2115-cross-protocol-impl/plan.md:142)。現 test の「legacy schema without version」fixture は genome を持たない: [test_screening_driver.py:143](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2115-cross-protocol-impl/orchestrator/tests/test_screening_driver.py:143)。
  - Layer 3 reader の legacy 分岐は v2 だけ: [layer3_report.py:46](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2115-cross-protocol-impl/orchestrator/campaign/layer3_report.py:46)、[layer3_report.py:262](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2115-cross-protocol-impl/orchestrator/campaign/layer3_report.py:262)。repository には v1 report が1件、v2 report が6件実在する。
  - schema の protocol property を optional にする案は v2/v3 document を維持する: [plan.md:108](</work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2115-cross-protocol-impl/artifacts/dev-wave-t2115-cross-protocol-impl/plan.md:108>)。
- 成り立つ場合の成果物影響: 既存4 floor の値・hash、既存v2 report 6件の bytes/参照は不変。v1 1件の非可読性は本変更前からの既存問題で、今回の受理集合変化ではない。
- 確信度: 高。

## 閉包の差分表

| 面 | プランが挙げた集合 | 自分が見つけた集合 | 差分 |
|---|---|---|---|
| between-run 公式 JSON | `between_run_floor.py`、`screening_driver.py`、3 caller、`layer3_report.py` | 同じ | production direct closure は一致。ただし screening の照合 field が不足 |
| within-run flat JSON | `calibrator/report.py`、`calibrator/cli.py:1077-1085`、`layer3_report.py` | 同じ + `orchestrator/reports/calibration_report.py` | silo 固定の人間向け report consumer が欠落 |
| certified calibration JSON | 記載なし | `calibrator/cli.py::_assemble_v2/_certify_main`、`calibrator/schema_v2.py`、`calibration_verify.py`、`env_attestation.py`、`env_contract.py`、その downstream consumers | producer、exact schema、registered path、reader chain が丸ごと欠落 |
| Layer 3 discovery | calibration 直下 `*.json` | 直下のみ。実在する `registered/*.json` 2件は対象外 | certified calibration へ接続しない |
| scoping JSON | `pegasus_floor_scoping.py` | 同じ | production 差分なし。隔離契約 test が焦点走から欠落 |
| `SPACES` / `space_for` | production caller 0、`test_campaign.py` のみ | `SPACES` は定義内部だけ、`space_for()` は `test_campaign.py` だけ | プランどおり |
| `SILO_SPACE` 直接 consumer | `test_guided.py` のみを強調 | production: `p2_2.py`、`search_baselines.py`、`sanity_silo.py`、`replay.py`、`guided.py`、`s1_known_axes_freeze.py`、`tools/check_trace0_preprocess_identity.py` | SILO_SPACE 自体は不変だが回帰閉包は広い |
| caller test | backoff の転送 test 2件 | 上記 + `test_screening_opt_in.py`、各 sweep test | s6/s8a の protocol 転送実体検査がない |
| 内容走査型 test | ほぼ記載なし | `test_s8b_floor_campaign.py`、`test_official_perf_closure.py`、`test_ccbench_spawn_sites.py`、T-080/oracle freeze tests | 名前 grep から漏れた exact inventory |
| 別 floor artifact family | report 定数類を除外 | S8b `floor_protocol/result.json`、B10 `between_run_cv_pct` も確認 | T-2115 の calibration noise floor とは別契約なので変更不要 |

## プランのどこが正しいか

- 同一 workload の第2 protocol floor を追加すると、現 `load_between_run_floor()` が `matches=2` で壊れるという指摘は正しい。
- campaign protocol の一次値を WAL `build_start.payload.genome` から取る判断は正しい。実在する Layer 3 report 7 campaign の build_start を確認し、全件 canonical な `silo|...`、protocol 一意だった。
- 実在する4件の between-run JSON は全件 canonical genome を持つため、bytes を変えずに protocol を導出できる。
- legacy flat within-run JSON を implicit silo に限定する案は、既存2件の値と source hash を維持する互換策として成立する。
- mocc の現在操作可能な YCSB genome 軸を3本、8通りとすること、RWLOCK・delay・TRACE を除外することは妥当である。
- 現 pin の mocc TRACE 0件により floor production を build/measure 前に拒否すること、create-only で既存 floor bytes を保護することは本題に必要な fail-closed であり、余計な gate ではない。
- `pegasus_floor_scoping.py` は repository 外かつ `scoping_between_run_` prefixで公式 globから隔離されており、変更不要。
- tictoc/cicada をこの初手 mocc wave に同時登録しないこと自体は D1360 の段階導入と矛盾しない。ただし phase3 の task (b) 全体を完了したとは扱えず、残余として明記する必要がある。

## 親 brief の誤り

- 「編集面は4 file」は誤り。整合する実装案は production 8 file である。
- 並行 `dev-wave-t1981-t088-floor-remeasure` との tracked file 衝突は現時点で無し。同 branch と `floor-rerun` branch はともに baseからの tracked diffがなく、存在するのは別系統の untracked S8b floor outputだけだった。「重なりうる」は名前からの推測で、実測事実ではない。
- 「mocc の live 軸は3本」は不正確。可変 cache 軸は3本だが、固定された live 分岐 RWLOCK を含めると anatomy の4本になる。16と8の差はこの固定軸を列挙するか、現 CMakeで操作可能な軸だけ数えるかの差である。
- 「全14 file で protocol を取れる」は過剰一般化。calibration直下は14件あるが、`between_run_noise_*.json` は4件だけで、その4件は全て取れる。within-run 2件と registered v2 2件には genome/protocol がない。
- 「既存 layer3 report は現行 schema で読めたまま」は全実在 report については誤り。v2の6件は維持できるが、実在するv1の1件は現 readerが元から対応していない。
- 凍結影響なしの根拠は不足。最初の4 anchorがトップレベル manifestにないことは正しいが、追加 caller 3本は凍結 artifact 内の source-hash、T-080 migration、oracle testから参照される。

## 総括

最重要所見は B-1、within-run certified calibration 閉包の取り残しである。  
screening も protocol だけでは足りず、records/threads を含む exact key が必要である。  
mocc の8 genome と既存 between-run bytes の互換方針は成立する。  
production 編集面は8 fileで、並行 T-1981 との実衝突は現時点でない。  
read-only 静的検査のみで、pytest、build、測定は実走していない。