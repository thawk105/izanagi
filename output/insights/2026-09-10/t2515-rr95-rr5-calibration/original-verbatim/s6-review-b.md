静的レビューの結論は must-fix 0 件です。対象 2 shell の `bash -n` は rc=0。pytest は実行していません。

## Consumer test 閉包

| Consumer test file | 参照経路 | 静的な赤判定 |
|---|---|---|
| `orchestrator/tests/test_pegasus_calibration_workload.py` | `ROOT` から `SUBMIT` / `JOB` / `README` を構築し、直接読取・fixture 複写・実起動 (`:19-23,46-154,547-754`) | 期待値と実物は一致。赤要因なし |
| `orchestrator/tests/test_pegasus_tools.py` | `TOOL_DIR` 定数経由の直接読取、`copytree(TOOL_DIR, ...)` 経由の submitter 実起動 (`:23-25,124-180,1628-1678`) | 抽出 block、PBS、policy、perf、binding の対象部分は不変 |
| `orchestrator/tests/test_ccbench_spawn_sites.py` | production directory の `rglob` から shell build sink を抽出 (`:835-856,2626-2639`) | build sink は残る。追加 3 行による sink 行移動はこの file の certify 用期待値に固定されていない |
| `orchestrator/tests/test_official_perf_closure.py` | `orchestrator` / `tools` の全 `.py` / `.sh` を走査 (`:518-545,890-897`) | 新しい ratio gate 行は `perf` predicate ではない |
| `orchestrator/tests/test_hooks.py` | admission registry の path、全 `tools/pegasus` entry の shebang・mode・存在を走査 (`:3038,3088,4383-4409`) | path、mode、shebang、class は不変 |
| `orchestrator/tests/test_pegasus_policy_registry.py` | `git ls-files` から全 production `.py` / `.sh` を読み、移動済み policy key を探索 (`:46-58,327-350,485-493`) | 新しい policy 読取はない |
| `orchestrator/tests/test_campaign_import_invariant.py` | tracked/untracked operational `.sh` を全読取し、shell 内 legacy namespace を走査 (`:1002-1051,1074-1089`) | ratio literal は legacy namespace に該当しない |
| `orchestrator/tests/test_login_headroom.py` | `git ls-files` の全 text を読んで memory ceiling literal を探索 (`:1602-1622`) | 対象 literal の追加なし |
| `orchestrator/tests/test_s8b_repo_scan_invariant.py` | `s8b_holdout_freeze.search_repository()` が全 tracked file を読む (`:24-34`) | `ycsb_rratio=80/20` と skew/rmw の三軸 conjunction は増えない |
| `orchestrator/tests/test_s8c_preregistration_invariant.py` | 同じ holdout repository scan を再利用 (`:622-645`) | 上と同じく hit 集合不変 |
| `orchestrator/tests/test_pegasus_floor_tools.py` | `floor_campaign.sh` 内の `certify_calibration.sh` 出典コメントを delimiter として参照 (`:1064-1070,4135-4141`) | 出典は commit 付き過去 anchor。現在の certify 行番号とは比較しない |
| `orchestrator/tests/test_check_docs.py` | admission docs / README の path・表・fenced command を検査 (`:1880-1955,2079-2110`) | 現 README は 5 値へ更新済み。shell bytes は比較しない |
| `orchestrator/tests/test_acceptance_schedule_order.py` | 変更後の collected node と duration ledger を全体 coverage で結合 (`:660-717`) | 新 node は unknown-cost fallback 対象。台帳完全一致は要求しない |

`test_pegasus_calibration_workload.py` 以外で、この差分により赤くなると静的に判断した file はありません。

## 所見

[1] 間接 consumer に旧 3 値期待は残っていない / 上表の直接読取・全 production scan・docs scan を 2 段追跡し、旧 `20|50|80` または旧 error を期待する assert は対象 test 以外にない (`orchestrator/tests/test_pegasus_tools.py:124-180`, `orchestrator/tests/test_ccbench_spawn_sites.py:835-856`, `orchestrator/tests/test_official_perf_closure.py:518-545`) / 新 literal が perf、policy、holdout、legacy-import predicate に一致すれば別 file が赤くなるが、追加されたのは exact ratio 比較だけである / 成果物影響: 別 consumer による受理集合の巻戻しや成果物拒否は起きない / 自己判定: refuted / nit

[2] 実装報告と異なり collected test node は 11 増える / 負例が 1 node から 8 parameter node、dry-run が 1 node から 5 parameter nodeになる (`artifacts/s5-diff.patch:125-150,174-200`) 一方、報告は「新規・改名 test はない」とする (`artifacts/s5-author-out.md:19`) / 親が function 名だけを見て node 数不変と扱うと、追加所要と ledger miss を見落とす / 成果物影響: 対象 file の collection は 30 node から 41 nodeへ増えるが、production の成果物値は変わらない / 自己判定: real / nit

[3] duration ledger の編集は不要だが、旧 function entry は parameter node の fallback にはならない / ledger は旧 unsuffixed 2 entryを持つ (`acceptance_duration_ledger.json:1353-1354,12801`)。consumer は parameter suffix を保持して exact lookupし (`conftest.py:1550-1591`)、miss は 96 番目の既知 costへ送る (`conftest.py:1615-1654`)。現 ledger 22,157 値の 96 位は 30.0 秒 / 13 個の新 parameter node に exact duration がないが、30 秒の unknown-cost として安全側に先行配置される。`test_job_rechecks...` は同一 nodeid のため旧 0.001 秒を使う / 成果物影響: 実行順の精度だけが落ち、受理集合、test collection、成果物値は変わらない / 自己判定: refuted / nit

[4] 対象 file の直列所要は概算 2.9〜3.9 秒増える / dry-run の既存実測 0.71 秒が 1 回から5回となり約 +2.84 秒 (`acceptance_duration_ledger.json:1354`, `test_pegasus_calibration_workload.py:677-700`)。負例は既存 0.005 秒が 1 回から8回となり約 +0.035 秒 (`acceptance_duration_ledger.json:12801`, `test_pegasus_calibration_workload.py:501-526`)。job body は 2.53 MB、88 file の directory 複写と短い policy parseを1回追加する (`test_pegasus_calibration_workload.py:105-143`) / 高負荷時は copytree と git fixture の所要が伸びるが、追加量は秒単位であり受入全体の支配項にはならない / 成果物影響: 受入 wall timeだけが増え、calibration JSONや shell の受理集合は変わらない / 自己判定: real / nit

[5] login node の subprocess timeout による赤はない / 対象 test file の `subprocess.run` に `timeout=` はなく、追加 job body は invalid `+5` gateで policy parse直後に終了する (`test_pegasus_calibration_workload.py:128-154`, `certify_calibration.sh:150-163`) / 短い timeout が負荷時に発火する経路はない。逆に filesystem command 自体が停止すれば上限なしで待つが、本差分固有の deterministic failureではない / 成果物影響: timeout起因で受入集合が縮むことはない / 自己判定: refuted / nit

[6] job body 実起動テストは `/scr` や wave treeを汚さない / child は `PBS_JOBID=invalid-rratio-fixture`、`PBS_O_WORKDIR=<tmp_path>/job-repo` を受ける (`test_pegasus_calibration_workload.py:127-139`)。実物が要求する `/scr/invalid-rratio-fixture` の `mkdir` (`certify_calibration.sh:24-31`) は PATH先頭の shim が成功だけ返し作成しない (`test_pegasus_calibration_workload.py:113-130`)。実際の書込先は `<tmp_path>/job-repo/output/env/pegasus/calibration/{attempts,job-staging/invalid-rratio-fixture/failure.json}` (`certify_calibration.sh:33-45,50-76`) / shimが選ばれなければ `/scr/invalid-rratio-fixture` が残りうるが、PATH prependと完全一致条件によりその経路には入らない。CCBench変数は空なので EXIT trapも worktreeを触らない (`certify_calibration.sh:95-104`) / 成果物影響: wave output、共有 `/scr`、共有 git metadataに残留物は作られない / 自己判定: refuted / nit

[7] `--rratio 95` は既存 preflightを通れば qsubまで到達する / submitter の新 gateは95を受理 (`submit_certify.sh:40-44`)。以後は job/policy存在、clean HEAD、4 preflightという既存条件だけで (`submit_certify.sh:52-98,129-188`)、`qsub_cmd` を構築・実行する (`submit_certify.sh:190-215`) / dirty tree、preflight非0、または投入 cwdがsubmit-tree rootでなければ停止・job側REPO_ROOT不一致になるが、これは新条件ではなく、親裁定も各 submit-treeへ `cd` 後に投入するよう要求する (`ruling.md:43-50`) / 成果物影響: 規定手順なら rr95 jobが新たに止まらず、失敗時だけ accepted calibrationが生成されない / 自己判定: refuted / nit

[8] qsub export、receipt、job側再照合の field名と型は一致する / qsub は `IZANAGI_CALIBRATION_RRATIO=95` を文字列で export (`submit_certify.sh:190-196`)。pre-submitだけが `request.calibration_rratio` を整数化し (`submit_certify.sh:164-176`)、submit receiptは `calibration.workload.ycsb_rratio` を文字列化する (`submit_certify.sh:240-258`)。job側は envの exact文字列を受理し (`certify_calibration.sh:154-164`)、receiptの同 fieldを `str(rratio)` と比較する (`certify_calibration.sh:199-230`) / 型またはfieldがずれれば `submit binding mismatch` で停止するが、95では int 95から receipt文字列 `"95"`、env文字列 `"95"`へ一致する。既定 protocolも receipt `"silo"` とjob既定 `"silo"`で一致する / 成果物影響: rr95 workloadは `ycsb_rratio=95` として calibrator argvと job-resultへ伝わり、別 ratioへの誤登録はない / 自己判定: refuted / nit

[9] 親裁定の所有・docs・commit・一般化境界への違反は差分にない / author差分の headerは所有対象3 fileだけ (`artifacts/s5-diff.patch:1-4,214-217,235-238`)。README、ledger、production gate新設、commit操作は含まれず、author報告もcommit・docs編集なしとする (`artifacts/s5-author-out.md:1,19`)。追加 helperは2 shellの既存 gate literalを読むtest側関数である (`test_pegasus_calibration_workload.py:36-43`) / README変更をauthor差分へ混ぜる、CLI gateを一般化する、ledgerを更新する、といった違反シナリオはいずれも発生していない / 成果物影響: sanctioned shell経路だけが exact `{5,20,50,80,95}` へ広がり、所有外の受理面は変わらない / 自己判定: refuted / nit

## 総括

must-fix は 0 件です。  
実在する nit は collected node が +11 になる点と、直列所要が概算 2.9〜3.9 秒増える点だけです。  
consumer test、台帳 fallback、tmp隔離、qsub/receipt/job bindingに静的な破れは見つかりませんでした。