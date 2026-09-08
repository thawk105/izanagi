## 所見

### 所見 1 — toolchain manifest と record digest が束縛されていない

**根拠 (file:line)**

- producer では complete toolchain manifest の canonical JSON を SHA-256 化する: `orchestrator/campaign/buildcache.py:2518-2527`。
- consumer は digest が hex64 であることと、両 arm で同じことしか検査しない: `orchestrator/campaign/t1998_stock_inline_pair.py:569-581,903-917`。
- 正例 fixture は `_TOOLCHAIN` に対して無関係な `"3" * 64` を digest として記録する: `orchestrator/tests/test_t1998_stock_inline_pair.py:56,85-89,234-241`。この manifest の canonical digest は実際には `fb534797fa4eaa063c95c782900b817701208d1954ba13c1e7cae8124a453c59` だが、正例は accepted を期待する: 同 `:374-386`。
- digest drift テストも target と baseline の文字列不一致しか検査していない: 同 `:505-512`。

**壊れる筋 (具体的な入力と、そのとき出る誤った結論)**

両 arm と `result.toolchain` を同じ偽 manifest に変え、両 arm の `toolchain_record_sha256` は同じ任意 hex64 のままにして WAL/result hash を更新する。generic admission は build_done の toolchain digestを再計算せず、consumer も arm 間一致だけを見るため `accepted` になる。「toolchain manifest と record digest が一致した」という戻り値が偽になる。現行の正例 fixture 自体がこの入力である。

**直し方の方向**

各 arm で toolchain manifest の canonical digest を再計算し、同じ arm の `toolchain_record_sha256` と一致させた後に、arm 間一致と `result.toolchain` 投影を検査する。

### 所見 2 — bench executable の検査は、性能 build receipt に対応しない command を通す

**根拠 (file:line)**

- consumer は configure の `-B` から期待 path を作り、その path が `run_cmd` のどこかにちょうど一回現れることしか見ない: `orchestrator/campaign/t1998_stock_inline_pair.py:502-517`。
- producer が保存する `perf_build_cmd` は読んでいない: `orchestrator/campaign/pipeline.py:1402-1411`。
- 正例 fixture の build_done には `perf_build_cmd` が存在しないが accepted になる: `orchestrator/tests/test_t1998_stock_inline_pair.py:234-241,374-386`。
- 既存 consumer の同型検査は configure と build の directory を突き合わせ、bench binary の実引数を検査する: `orchestrator/campaign/backoff_requested_us.py:415-448`。

**壊れる筋 (具体的な入力と、そのとき出る誤った結論)**

target の `run_cmd` を `/bin/echo /fixture/build/<variant>/perf/cc/silo/ycsb_silo.exe` に変え、WAL/result hash を更新する。期待 path は token として一回現れるので検査を通るが、実際に実行される executable は `/bin/echo` である。`perf_build_cmd` が欠落していても同様に通り、「bench executable が性能 build receipt と対応した」と誤判定する。

**直し方の方向**

`perf_configure_cmd -B` と `perf_build_cmd --build` の directory を一致させ、既知 wrapper の後に置かれた実 executable 引数がその build directory の `ycsb_silo.exe` であることを検査する。

### 所見 3 — verify_done だけ environment identity の一致検査から外れている

**根拠 (file:line)**

- consumer は exact `verify_done` を取得した直後に捨てる: `orchestrator/campaign/t1998_stock_inline_pair.py:420-432`。
- env tag の集合は start/build_done/bench_done/commit の四点だけで作る: 同 `:434-447`。
- public admission が verify_done について検査するのは verdict、certified、anomalies、workload と receipt evidence であり、env tag ではない: `orchestrator/campaign/artifact_admission.py:752-817`。
- WAL の environment contract 検査も commit の env tag だけを照合する: `orchestrator/campaign/wal.py:2104-2117`。

**壊れる筋 (具体的な入力と、そのとき出る誤った結論)**

自己整合な root の target `verify_done.env_tag` だけを別環境名へ変え、result の WAL hash を更新する。receipt evidence は verify payload の workload/verdict/certified と一致したままで public admission を通り、consumer は verify_done を env tag 集合へ入れないため `accepted` を返す。「両 arm の env tag が一致した」という結論が偽になる。

**直し方の方向**

`verify_done` を arm の env tag 集合へ含め、他の四 stage と同じ environment identity を要求する。

### 所見 4 — 1 invocation 1 job は、別 invocation と競合する F251 再発経路を残す

**根拠 (file:line)**

- 新 submitter 内の qsub は一回だけだが、並行 invocation を排他する状態はない: `tools/pegasus/submit_t1998_balanced_stock_inline.sh:87-103,176-191`。
- 再利用する job body は引き続き共有 CCBench gitdir に対して global `worktree prune --expire now` を実行する: `tools/pegasus/a5_second_boot_backoff_sweep.sh:123-169`。
- job は共有 repository/submodule へ scratch worktree を登録する: 同 `:363-376,467-484`。

**壊れる筋 (具体的な入力と、そのとき出る誤った結論)**

新 submitter を二回並行実行する、または既存 A-5 submitter の job が生きている間に新 submitter を実行する。出力 root は別なので双方の投入前検査を通るが、先に終わった job の global prune が別計算ノードの `$TMPDIR` worktree 登録を stale と判断して消し、後続 job を壊しうる。「1 job なので F251 の経路が構造的に成立しない」という結論は、単一 invocation 内にしか成立しない。

**直し方の方向**

これは既存 A-5 job body の shared gitdir ownership 問題であり、**scope 外・裁定パッケージ候補**。本 wave の三部品だけで解消済みとは扱わない。

### 所見 5 — 新 submit receipt の schema identity がどのテストにも pin されていない

**根拠 (file:line)**

- `t1998-balanced-stock-inline-submit-event/v1` は launcher の三 event にだけ現れる: `tools/pegasus/submit_t1998_balanced_stock_inline.sh:115,130,142`。
- launcher 契約テストは receipt の atomic append と一部 field を検査するが、schema literal を検査しない: `orchestrator/tests/test_t1998_launcher_contract.py:68-102`。
- 検索語 `t1998-balanced-stock-inline-submit-event/v1` の `git grep` 結果は上記三行だけで、parser、golden、registry はない。

**壊れる筋 (具体的な入力と、そのとき出る誤った結論)**

三 event の schema literal をまとめて別文字列へ変える。launcher 契約 6 test、Pegasus registry 完全一致、docs 投影はすべてその変更を検出しない。submitter provenance の成果物 identity が変わっても受入全走が緑のままになる。

**直し方の方向**

既存 launcher 契約テストで、三 event が exact `t1998-balanced-stock-inline-submit-event/v1` を使うことを固定する。

### 所見 6 — 新規 22 test node が acceptance duration ledger に未登録

**根拠 (file:line)**

- consumer test は parametrize 展開後 16 node: `orchestrator/tests/test_t1998_stock_inline_pair.py:374-557`。
- launcher test は 6 node: `orchestrator/tests/test_t1998_launcher_contract.py:19-111`。
- `orchestrator/tests/acceptance_duration_ledger.json` を両 file prefix で検索した結果は 0 entry。
- 未登録 node は duration reorder で unknown 扱いとなり、共通の代替 cost が使われる: `orchestrator/tests/conftest.py:1594-1622`。

**壊れる筋 (具体的な入力と、そのとき出る誤った結論)**

この 8 file だけで受入閉包済みとすると、親実測で約 100 秒を要した consumer test 群が測定済み duration として shard 配置されない。テスト自体が必ず赤になるわけではないが、acceptance scheduling ledger は未閉包のままである。

**直し方の方向**

予定済みの単位 C で、この 16 + 6 node の実測値を既存 ledger に追加する。他に今回新設された同型 test file はない。

## 閉包の判定表

検索語は `t1998_stock_inline_pair`、`submit_t1998_balanced_stock_inline`、`t1998-balanced-stock-inline-submit-event/v1`、`T1998PreregisteredIdentity`、`consume_balanced_stock_inline_pair`、`a5_second_boot_backoff_sweep.sh`、`submit_a5_second_boot_backoff_sweep.sh`、`admission_registry.json`、`_PEGASUS_EXPECTED_CLASSES`、`_PEGASUS_EXPECTED_ENTRIES`、`acceptance_duration_ledger`、`test_plain_runner_coverage`、`run_campaign`、`perf_configure_cmd`、`toolchain_record_sha256`。

既存物への参照 consumer は次のとおり。

- A-5 job body: 既存 submitter `tools/pegasus/submit_a5_second_boot_backoff_sweep.sh:43,175-177`、新 submitter `tools/pegasus/submit_t1998_balanced_stock_inline.sh:44-45,178-180`、A-5契約 `orchestrator/tests/test_a5_second_boot_job_contract.py:273-371`、新 launcher 契約 `orchestrator/tests/test_t1998_launcher_contract.py:30-53`、official perf 集合 `orchestrator/tests/test_official_perf_closure.py:83`、registry/hook/runbook。
- A-5 submitter: `orchestrator/tests/test_a5_second_boot_job_contract.py:177-180,273-371`、`tools/pegasus/admission_registry.json:304-309`、`orchestrator/tests/test_hooks.py:3083,3406-3411,3949-3950`、`docs/pegasus-runbook.md:542`。
- admission registry: canonical loader `tools/pegasus_admission_registry.py:80-130`、実行判定 `hooks/guard_bash.py:242-324,616`、literal 完全一致 `orchestrator/tests/test_hooks.py:3933-3973`、docs 投影 `tools/check_docs.py:4404-4438,4805-4824`。
- 新 test files: plain-runner 検査 `orchestrator/tests/test_plain_runner_coverage.py:35-86` と duration ledger が consumer。
- `test_campaign.py` の `run_campaign` caller inventory は `orchestrator/tests/test_campaign.py:5346-5372`。新 consumer は `run_campaign` を呼ばないため inventory 差分はない。
- `tools/check_codex_agents.py` は `.codex` role adapter/native profile 面だけを走査する: `tools/check_codex_agents.py:63-138,217-258`。今回の8 fileは対象外。

| 新しい名前・file | 掛かる pin / 登録簿 / 完全一致検査 | 登録済みか |
|---|---|---|
| `orchestrator/campaign/t1998_stock_inline_pair.py` | `_REVIEWED_PERF_FILES`、専用 consumer test | 登録済み |
| `WORKLOAD`、`TARGET_FIXED_US`、固定 canonical genome、T1998 identity/decision 型 | `test_t1998_stock_inline_pair.py` の固定 pair fixture と負例 | 登録済み。ただし toolchain digest と manifest の対応は未固定 |
| `tools/pegasus/submit_t1998_balanced_stock_inline.sh` | admission registry、hooks class 集合、hooks 4-field literal、local evidence 集合、runbook 投影、launcher 契約 | 登録済み |
| `t1998-balanced-stock-inline-submit-event/v1`、`$GROUP_ID.submit.jsonl` | launcher 内 literal のみ。parser/golden/exact schema assertion なし | 未登録 |
| `orchestrator/tests/test_t1998_stock_inline_pair.py` | plain-runner harness、acceptance duration ledger | harness 登録済み、ledger 16 node 未登録 |
| `orchestrator/tests/test_t1998_launcher_contract.py` | plain-runner harness、acceptance duration ledger | harness 登録済み、ledger 6 node 未登録 |
| 新 Pegasus registry entry | `_PEGASUS_EXPECTED_CLASSES`、`_PEGASUS_EXPECTED_ENTRIES`、`expected_local_evidence`、runbook path/class/evidence | 両側とも登録済み |
| 既存 A-5 job body / submitter / 契約 test | base/HEAD blob exact、既存 registry/hook/runbook pin | 変更なし |
| `run_campaign` caller inventory | `test_campaign.py` の exact Counter | 対象外。新 caller なし |
| Codex role adapter inventory | `tools/check_codex_agents.py` | 対象外 |

既存 A-5 三 file の base `c5754d1f4` と HEAD の blob ID はそれぞれ完全一致している。したがって今回の差分そのものによる A-5 受理集合変更はない。

## 裁定との対応表

| 裁定 §3 の要求 | 状態 | 対応 |
|---|---|---|
| balanced だけを 1 job 投入 | 実装済み | `WORKLOAD=balanced`、qsub 一回 |
| 既存 A-5 job body を無変更再利用 | 実装済み | job body blob は base/HEAD 同一 |
| 既存 A-5 submitter・契約・entry を変更しない | 実装済み | 三面とも既存 bytes 不変 |
| queue、quota、Pegasus info、repo 外 output、unique output、atomic receipt | 実装済み | A-5 submitter の検査を落としていない |
| output parent は既定なし、絶対 path 必須 | 実装済み | `--output-parent` 必須 |
| qsub の五つの A-5 binding | 実装済み | workload/root/nonce/HEAD/script SHA を一回渡す |
| 1 job 化で F251 を構造的に回避 | 別物 | 同一 invocation の兄弟だけ解消。別 invocation/既存 A-5 job との global prune 競合は残る |
| Pegasus registry、hooks、runbook、launcher test 同時登録 | 実装済み | path/class/4-field/evidence 投影まで一致 |
| 固定 baseline、fixed-5 target、balanced、argmax 不使用 | 実装済み | module 内定数、backoff_sweep import なし |
| preregistration を共通 identity と arm 固有 identity に分離 | 実装済み | commit/gitlink/env/script と genome/source digest を分離 |
| preregistration の実値を module に固定しない | 実装済み | 型と引数 seam のみ |
| result/reservation/lock/WAL/public certified view を読む | 実装済み | 各入力を直接検査 |
| sibling failure receipt があれば拒否 | 実装済み | `lexists` で存在を拒否 |
| result と admitted view の lock/WAL SHA 一致 | 実装済み | 両 hash を照合 |
| 40桁 gitlink exact、lock/WAL 短縮 prefix | 実装済み | `_gitlink_matches` で分離 |
| job body digest と repository commit/authority の束縛 | 実装済み | submitter identity は recoverable と主張しない |
| source digest 事前登録と diagnostic marker 拒否 | 実装済み | arm 別 source digest、genome/configure marker |
| trace-disabled performance build | 実装済み | configure の `CCBENCH_TRACE=0` を要求 |
| bench executable と性能 build receipt の対応 | 別物 | `perf_build_cmd` を読まず、期待 path が任意 token として現れれば通る |
| 両 arm の environment digest/env tag 一致 | 別物 | verify_done の env tag だけ未検査 |
| toolchain manifest と record digest の一致 | 別物 | hex shape と arm 間一致だけで、manifest digest を再計算しない |
| baseline/target ちょうど 1 attempt | 実装済み | canonical pair の build_start を各一件要求 |
| samples/median/COMMIT fitness/result projection 一致 | 実装済み | 五 samples と各投影を照合 |
| unstable arm は inconclusive | 実装済み | ratio/improvement を `None` にする |
| secondary `admit_replay_evidence()` を受理条件にしない | 実装済み | 呼出しなし |
| receipt ID は admitted COMMIT persisted payload から取得 | 実装済み | commit payload から返却 |
| 拒否に code/field/expected/actual/arm | 実装済み | `T1998PairRejected` に全 field |
| 冗長 gate をコメントし、変異証拠から外す | 実装済み | pair-cardinality/producer-rejected-variant を明記 |
| 負テストは自己整合 root から一箇所だけ変異 | 別物 | 基底 fixture の toolchain digest が manifest と不整合 |
| 実 admission/receipt 経路を使う | 実装済み | public admission と実 receipt support を使用 |
| 新 test の自走 harness | 実装済み | 両 file に `_run()` と `__main__` |
| 新 test node の acceptance ledger 登録 | 未実装 | 16 + 6 node。単位 C 待ち |
| submit receipt schema identity の回帰 pin | 未実装 | `/v1` literal を検査する consumer/golden がない |

## 総括

投入前の実装上の blocking は、toolchain digest 未束縛、bench executable の偽対応、verify_done の environment identity 漏れ、submit receipt schema 未固定の4件。acceptance bookkeeping は単位 C の22 node登録が未完である。

F251 は単一 invocation 内の兄弟競合だけを避けており、共有 job body の global prune による別 invocation 競合は残る。これは scope 外・裁定パッケージ候補として扱う必要がある。

registry と `test_hooks.py` の両側、runbook 投影、official perf 登録、plain-runner、`run_campaign` inventory、`check_docs.py`、`check_codex_agents.py` の静的参照面には、上記以外の受入全走で初めて現れる未登録 consumer は見つからなかった。file 書込み、commit、pytest、build、benchmark は行っていない。