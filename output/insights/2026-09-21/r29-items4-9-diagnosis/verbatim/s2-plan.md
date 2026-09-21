## 1 (b) 最小改修範囲

以下は **静的検査による起草**。実装・テスト・job 投入は行っていない。コードの基点は `d99c556dfa23e446987ef3ccbb5c018986fe10b5`。

参照の略記：

- `RT` = `tools/run_tests.py`
- `DC` = `tools/pegasus/dispatch_compute.py`
- `前回` = `output/insights/2026-09-21/focus-run-count-diagnosis/`
- `契約` = `/work/1/SFC/tanab/dev-wave-jobs/dev-wave-r29-items4-9-diagnosis/verbatim/contract/`

**確認結果：file を指定した非受入の `--force-dispatch` は、1起動→1 job→1 pytest invocation。** `RT:231` が flag を除去し、`:2620`→`:2302`→`:1307` が一つの argv を tests task に渡す。compute 側は `DC:1880` で一つの runner を起動し、`RT:2682`→`:1260` が一つの pytest command を実行する。

ただし、**「`--force-dispatch` は常に1 job」は誤り**。空 argv の受入形には shard 経路があり、既定でも eligible なら2 shardになる（`RT:267–297,2309–2352`）。今回の対象は明示 file 集合の焦点走に限定する。

**最小案：tests task のまま、焦点走専用の複数 invocation 入力を追加する。** 新 task・汎用 workflow・任意 cwd/env の機構は不要。

| 層 | 最小案・触る箇所 | 根拠／維持する境界 |
|---|---|---|
| 入力表現 | 仮称 `--focus-batch-json '<JSON>'`。要素は `argv: list[str]` と `growth_held: bool` に限定。nproc は既存 `-n`、cwd は repo root 固定。`_consume_runner_options` (`RT:231`)、help (`:338`)、新規 parser/validator | inline JSON なら共有入力 file の差替え問題を増やさない。file 入力を採る場合も login で読み切り、正規化した内容を dispatch request に載せる |
| login 受理 | `main` (`RT:2389`) に batch 分岐。各 argv を `_normalize_args` (`:456`) で正規化し、既存 preflight を適用。batch に受入形・shard 指定・再帰 batch を混ぜない | `_is_acceptance_run` (`:692`) と shard eligibility (`:267`) 自体は変更しない。batch 全体を受入証拠にしない |
| dispatch | `_default_dispatch` (`RT:1307`) から **1回だけ** tests task を呼ぶ。個別 argv を平坦化しない | 現行 `TASKS["tests"]` は `argv_policy="passthrough"` (`DC:117–135`)。新 task は不要 |
| compute 実行 | 新規逐次 loop。各要素につき新しい runner subprocess を起動し、既存の「runner→pytest」を再利用。cwd=repo root、同時実行しない | `RT:1260–1262,2692–2708`。`pytest.main()` の同一 process 内反復では D325 を満たさない |
| env 分離 | invocation ごとに base env をコピー。通常要素では held env を除去し、許された held 要素だけ exact token を設定。隣の要素へ持ち越さない | tests allowlist に held env は既存 (`DC:130`)。任意 env mapping を公開する必要はない |
| rc | 個別 rc を全件保持。通常の test failure 後も残る独立要素を実行するかを固定する。infra/中断は未実行要素を明示して停止。batch rc は成功のみ0、infra16優先、その他は最初の非0などに固定 | 最後の invocation の rc だけ返すと途中赤を隠す。単なる `cmd1; cmd2` では足りない |
| 結果 | invocation ごとに argv identity、開始・終了、rc、実行済み状態、個別 stats を記録。既存 `_RecordingSession` の sidecar を複数走で共用しない | `_RecordingSession` は「one … observation」 (`RT:1024–1042`)、`_suite_identity` は一つの argv/env を表す (`:976–995`) |
| task_run | 最小の記録案は、compute の個別結果を一つの batch 結果ファイルで返し、login が各 invocation を個別記録する。job 全体 wall は dispatch receipt に残す | `_dispatch_and_record` (`RT:1570`) は現在「親 wall と最終 rc を一度だけ」。集合＋単独を一つの suite として記録すると、単独証拠と個別時間を失う |
| transport 結果 | batch 結果の所在・内容対応を request に結び、欠落時は記録不能として扱う。既存 pytest sidecar schema に複数 invocation を押し込まない | `RT:1112–1128,1188,1570`。通常の単独 dispatch の記録契約を変えない別分岐が必要 |
| held 検査 | batch parser と compute 側で同じ token 条件を確認。今回の実測では全要素 held 無効 | runner の identity 判定は exact 比較 (`RT:998`)。実行側は `conftest.py:1936–1948` で空・未設定以外の誤 token を `UsageError` にする |

入力例は設計案であり、現行 CLI では実行できない。

```json
{
  "invocations": [
    {"argv": ["orchestrator/tests/test_a.py", "orchestrator/tests/test_b.py", "-n", "32"], "growth_held": false},
    {"argv": ["orchestrator/tests/test_a.py", "-n", "32"], "growth_held": false},
    {"argv": ["orchestrator/tests/test_b.py", "-n", "32"], "growth_held": false}
  ]
}
```

**dispatch task 契約の扱い。** 現行閉集合は tests/provenance/mutation/generic の4 task（`DC:116–162`）。D131 の「2→3」は当時の mutation 追加の記録であり、現在の task 数ではない（`契約/D130-D131.md:59–87`）。上案なら `TASKS`・`env_allowlist`・`argv_policy` の変更は不要。ただし tests の runner 入力契約は増えるので、R2 の採用裁定が不要になるわけではない。`_job_run` の全 task 共通実行・receipt を一般化する改修は避けられる。

**概算（設計見積り、実測でない）：**

- runner の既存5〜7関数と、新規3〜5関数程度。
- production 差分約250〜450行、対応テスト約200〜400行。
- `dispatch_compute` の共通処理は原則0行。既存結果 transport へ直接統合する設計を選ぶなら、この見積りを超える。
- 主な費用は parser ではなく、**個別 env・個別結果・記録主体・途中失敗の扱い**。これが「単なる flag 追加ではない」の中身。

**既存テストの追随範囲。** `rg -l 'run_tests|dispatch_compute' orchestrator/tests --glob 'test*.py'` は **36 file**。これは参照候補数であり、全36 file の編集が必要という意味ではない。

優先して仕様追加・回帰確認する既存 file は次の8本：

- `test_run_tests_nproc.py`：batch と既存 argv/nproc/受入形の分離。
- `test_run_tests_preflight.py`：個別 preflight。
- `test_run_tests_shards.py`：batch が shard へ入らないこと。
- `test_run_tests_task_run.py`：suite identity、個別 rc、sidecar。
- `test_run_tests_testops_observation.py`：記録開始・終了・二重記録。
- `test_pegasus_dispatch_compute.py`：tests の一回 dispatch、request/result 対応。
- `test_growth_test_holds_contract.py`：通常→held→通常の env 非漏出。
- `test_t2337_dispatch_timeout_overrides.py`：batch 全体に適用する timeout。

追加の回帰確認候補は `test_acceptance_launcher.py`、`test_dev_wave_wait.py`、`test_dev_wave_land.py`、`test_hooks.py`、`test_pytest_collection_config.py`、`test_site_policy.py`。具体的な新しい呼出形によって選ぶ。

**docs pin。** `tools/check_docs.py` に `run_tests` / `force-dispatch` の直接 literal hit はない。一方、DW-O26 全文は `tools/check_docs.py:618–628`、独立 fixture は `test_check_docs.py:178`、pin 検査は同 `:9534,9549` にある。dispatch の task/child 対応も同 test `:333,377,3038` 等にある。

したがって、**DW-O26 と task 集合を変えない R2 なら、その pin の書換えは必須ではない**。runner の使用説明は更新対象だが、pin 更新を最初から必須費用に数えない。

## 2 既存経路 G・L

**G：generic 1 job 内で複数 runner invocation を実行する経路は実在する。ただし tests dispatch と証拠の形は同一でない。**

| 観点 | 静的確認 |
|---|---|
| argv | `generic-v1` は非空の string list を受理 (`DC:1566–1576`)。`["bash","-c","…"]` は適合する。Python API へ shell文字列そのものを渡す形とは別 (`:3590–3599`) |
| 実行 | generic argv を `_run_isolated_child` に渡す (`DC:1880–1894`)。bash 内で runner を逐次起動できる |
| clean env | 保持は HOME/LANG/LANGUAGE/LC_ALL/LC_CTYPE/LOGNAME/PATH/TZ/USER (`DC:354–364,1661`)。`PYTEST_ADDOPTS`、`PYTEST_PLUGINS`、`PYTHONPATH`、nproc env、held env、task_run env、PBS_JOBID 等は保持されない |
| PATH | generic も sanctioned `_job_script` を通り、`:1128` で選定 interpreter の directory を先頭へ。さらに `_job_run` `:1851–1853` でも正規化。D130(4) の「手書き投入器がこの処理を写し漏らした」条件には当たらない |
| interpreter | generic の probe はPython版数のみ、tests はpytest/xdist/packagingも検査 (`DC:132,158,1020`)。したがって generic が選んだ interpreter で runner の依存が使えることは別途確認が要る |
| 再dispatch | `site_policy.py:30–46,66–84` は実 hostname を使い、env は分類に使わない。bnodeなら clean env でも compute。`RT:2620` のlogin分岐に入らない |
| xdist | compute runner はxdistのimportとloadgroup対応を要求。欠ければpipを呼ばずrc16 (`RT:2639–2656`)。generic自身のprobe通過だけでは保証されない |
| guard | `guard_bash.py:1250–1296,2813–2849` より、`bash -c` というだけでは拒否されない。防護pathと不透明構文等の組合せが問題。ここで提示する通常test path・date・runner呼出しにはその必然条件はない。ただし未知の21-file argvを含む完成commandの許可は未確認 |
| provenance | `docs/ai-provenance.md:46–63` は実装面を変更する **commit/path** の契約。fileを作らない今回の一時commandは、それだけでは実装面の変更commitにならない。一方、launcherを保存しても「repo外だから実装でない」とは言えない |

**失うもの・失わないもの：**

- **dispatch receipt、`[Pegasus dispatch]`、NQSV footerは失わない。** genericも同じdispatch/収集経路（`DC:3999,4052,4244,4397`、中継`:2061`、会計照合`:2145`）。
- 非受入警告も内側runnerが出す（`RT:2440–2445`）。
- 内側8 invocationそれぞれのdispatch receipt/footerは存在しない。**1 job分だけ**になる。
- login親の `_dispatch_and_record` を通らないので、「待ち込みの親wallをtest observationとして記録する」形は失う（`RT:1578–1628`）。
- task_runを全面的に失うとは限らない。genericがauto-record抑止envを落とすため、内側runnerは各々自動記録を試みる（`DC:1070–1073,1844–1850`、`RT:2689–2700`）。ただし既存logにも `recording-unavailable:series-invalid` があり、成功は保証しない。
- generic receiptのchildはbashであり、各pytestの成功はbashの集約と個別logで確認する。受入用runner bindingの証拠にはならない。

**L：dispatchなしの単独processも実在する。**

`python3 tools/run_tests.py orchestrator/tests/<file>.py` はloginで次を通る。

1. force/shard/bounded免除でなければ `_evaluate_login_admission`（`RT:2496–2505`）。
2. `grant_budget` が予約済み量と観測余裕・過去peak見積りを考慮する（`login_headroom.py:1043–1150`）。現在の既定は上限4GiB、下限1GiB（同`:31–32`）。
3. LOCALならbounded scopeで実行し、通常のchild rcをそのまま返す（`RT:2535–2560`）。
4. 余裕不足・観測失敗等でqueue利用可ならdispatch（`:2509–2533`）。queue不可なら `min_bytes=0` で再判定し、それでも不可なら停止。
5. CAP_OOM後はtree/submodule fingerprintが不変の場合だけdispatchへ退避（`:2567–2585`）。通常のtest赤をdispatchで再試行する分岐ではない。

したがって、**D325理由欄の「Pegasusでは実行を伴う焦点走は必ず計算ノードへdispatch」は現行コードでは成立しない**（`契約/D325.md:9–10`）。D325の別process義務まで無効になるわけではない。前回のlogin走2本も実在するが、変更testの単独充足数へ加算できる証拠ではない（`前回/verbatim/focus_runs_table.md:23–24`）。

## 3 (c) 実測 plan

**21 fileの一覧は指定された前回verbatimから特定不能。** 件数は `前回/README.md:85`、時刻・集計は `verbatim/focus_runs.jsonl` 等にあるが、完全なpytest argvがない。この欠落は同README `:129` 自身も明記する。

7 fileは `前回/verbatim/changed_files.txt:23` から確定できる。

```bash
SINGLE7=(
  orchestrator/tests/test_b5_contrast_launch.py
  orchestrator/tests/test_b5_generator_contrast.py
  orchestrator/tests/test_b5_generator_contrast_report.py
  orchestrator/tests/test_ccbench_spawn_sites.py
  orchestrator/tests/test_hooks.py
  orchestrator/tests/test_p3_s4_loop.py
  orchestrator/tests/test_p3_s4_loop_job_contract.py
)
```

以下は親が**元focus-3の投入argvから `FOCUS21` を補完した後**のcommand案。未確定の21 fileを推測して埋めない。両腕は同じ順序・同じ `-n 32` を使う。これは比較用に固定した並列度であり、過去走の並列度を再現したとの主張ではない。

**準備。**

- Cを現在の診断worktree、Sを同SHAの専用worktreeにする。現木に他のjobがなければ、新設は1本で足りる。
- `git worktree add --lock -b <専用branch> <S絶対path> d99c556dfa23e446987ef3ccbb5c018986fe10b5`。
- 新木を `python3 tools/dev_wave_submodule_init.py --worktree <S絶対path>` で再帰初期化。登録済み木を解決し、no-fetch初期化する実装は `tools/dev_wave_submodule_init.py:43–49`、義務は `契約/DW-C00-C01-STOP.md` のDW-C01。
- 両木のSHA・submodule・dirty状態を記録。計測中はcommit/mergeしない。
- login側で両腕のpytest選択env、held、shard、task-run手動指定を揃える。genericで消える `PYTHONPATH` 等にSだけ依存しないことも確認する。
- C/Sのlogと作業木別outputを分離。受入全走を隣接実行しない。

**腕C：1 job、8 invocation。** shell文字列は1行として渡す案：

```bash
python3 "$C/tools/pegasus/dispatch_compute.py" --task generic -- \
  bash -c 'suite=("${@:1:21}"); shift 21; total=0; printf "INV_BEGIN suite "; date -u +%s.%N; python3.10 tools/run_tests.py "${suite[@]}" -n 32; r=$?; printf "INV_END suite rc=%s " "$r"; date -u +%s.%N; if [ "$r" -eq 16 ]; then exit 16; fi; total=$r; for f in "$@"; do printf "INV_BEGIN %s " "$f"; date -u +%s.%N; python3.10 tools/run_tests.py "$f" -n 32; r=$?; printf "INV_END %s rc=%s " "$f" "$r"; date -u +%s.%N; if [ "$r" -eq 16 ]; then exit 16; fi; if [ "$total" -eq 0 ] && [ "$r" -ne 0 ]; then total=$r; fi; done; exit "$total"' \
  r29-c "${FOCUS21[@]}" "${SINGLE7[@]}"
```

computeで `python3.10` のpytest/xdist/packagingが使えることを最初のjob logに残す。held envは設定しない。

**腕S：集合1 job＋単独7 job、直列。**

```bash
date -u +%s.%N
python3 "$S/tools/run_tests.py" --force-dispatch "${FOCUS21[@]}" -n 32
r=$?
date -u +%s.%N
```

続けて同じshellで：

```bash
for f in "${SINGLE7[@]}"; do
  printf 'JOB_BEGIN %s ' "$f"
  date -u +%s.%N
  python3 "$S/tools/run_tests.py" --force-dispatch "$f" -n 32
  r=$?
  printf 'JOB_END %s rc=%s ' "$f" "$r"
  date -u +%s.%N
  if [ "$r" -eq 16 ]; then break; fi
done
```

集合jobがinfra16なら単独列を開始しない。通常赤は個別rcを残して比較結果を「全緑の同条件試行」と分ける。

両腕を親の同じshellから別subshellでbackground起動し、PIDと開始・終了時刻を保存して両方をwaitする。**同時投入開始であって、ノード上の同時開始ではない。** 上記はcommand案であり、新しいlauncher fileやharnessは作らない。完成commandがguardに拒否された場合はP4どおりCを取り下げ、別の書き方による迂回をしない。

**4区間の取得。**

各jobについて、wrapperの開始を \(t_0\)、NQSV Createdを \(t_c\)、Startedを \(t_s\)、Endedを \(t_e\)、wrapper終了を \(t_1\) とする。

| 区間 | 算式 |
|---|---|
| 投入前 | \(t_c-t_0\) |
| ノード開始前の待ち | \(t_s-t_c\) |
| RUN | \(t_e-t_s\) |
| collection | \(t_1-t_e\) |

C内のinvocation時間は `INV_END − INV_BEGIN`。pytest summary秒も併記し、runner起動等との違いを残す。Cのjob RUNと個別時間の合計との差はjob内固定費として扱う。

`[Pegasus dispatch]` の状態poll時刻は実際の開始時刻ではない。NQSV footerを使う（`DC:2145–2168`）。stdout中継はtail制限があるため、**元scheduler stdout/stderrとreceiptも保存**する（`:2061–2095`）。長いC logを親stdoutだけで解析しない。

**同一木直列の機序。**

- control rootは既定で `<repo>/output/pegasus-dispatch`（`DC:3623–3628`）。
- flockとhold確認（`:2303,2350,3704–3725`）、投入直前の再確認とpending hold作成（`:3980–4008`）。
- 同木の別dispatchはholdを見てrc16になる。holdを消して並行させない。
- 別木は既定control rootが別になる。ただし共有出力やテストが触る共有状態まで独立とは限らない。

D289は独立jobの並行を認める一方、**job間性能比較にはnodeをblock/randomization因子にしたprotocolを要求する**（`契約/D289.md:7–22`）。したがってP3の1対だけで因果的な「束ねの効果」を確定してはいけない。

今回の1対で報告できるのは、同SHA・同argv・同順序・同nprocでの**観測wall差と、実際に払った固定費差**。node差、warm cache、C/Sの資源競合、Sの後続jobが遭遇するqueue状態は揃わない。追加反復を勝手に増やさず、純粋な効果推定が必要なら配置の再裁定へ返す。

撤去はjob・子孫の終了とlog回収後。worktree lockを残したまま放置せず、既存cleanupの登録・所有条件に合わせて処理する。`git worktree remove` / submodule deinitを手打ちする案は入れない（`tools/check_docs.py:629–634` のDW-O28 pin）。

## 4 (a) 残件数表

**資料から証明できるのは k=22、単独確認済みs=2まで。P2のcを実数として確定する証拠は不足している。**

下表の `c確証` は「置換しても他の確認条件を失わないと、指定資料から証明できた本数」。0は「置換不可能」ではない。残件列も**証拠不足を含む値**であり、必要追加job数ではない。

| wave | k | s | c確証 | max(0,k−s−c確証) | P2候補・留保 |
|---|---:|---:|---:|---:|---|
| t2243 | 0 | 0 | 0 | 0 | 焦点走なし |
| t2804 | 3 | 0 | 0 | 3 | focus-2は最後のfix後集合確認 |
| t2803 | 1 | 1 | 0 | 0 | focus-2/8が同一変更fileの単独緑。3/5は赤→fix入力 |
| t2344 | 6 | 1 | 0 | 5 | f4単独緑。f3は契約追随、単純なmerge重複ではない |
| abstract | 0 | 0 | 0 | 0 | 焦点走なし |
| story21 | 0 | 0 | 0 | 0 | 焦点走なし |
| walldecomp | 0 | 0 | 0 | 0 | DW-S07のdocs影響確認 |
| t2814 | 1 | 0 | 0 | 1 | focus-1赤、focus-2が是正後確認 |
| t2810 | 2 | 0 | 0 | 2 | impl赤、fix2集合、held診断はそれぞれ役割あり |
| t2817 | 0 | 0 | 0 | 0 | login再走は変更test充足の加算対象でない |
| residue | 2 | 0 | 0 | 2 | f1/f3赤。f2/f4は各fix後確認 |
| t2797 | 7 | 0 | 0 | 7 | focus-2、focus-3の最大2本が条件付き候補 |
| **計** | **22** | **2** | **0** | **20** | **実際の最小残件数は未確定** |

根拠は `前回/verbatim/changed_files.txt:1–24`、`前回/README.md:63–90`。実装0の4 waveは同README`:14`。

t2797の各候補を証明済みcへ入れない理由：

- **focus/focus-2.log**：緑で後続fixがあったことは確認済み。しかし「後続fixあり」だけでは、この走の確認役割を別の走がすべて引き受けたとは証明できない。前回も事後情報に限定している（`前回/README.md:89,103`）。
- **focus/focus-3.log**：merge後走の一般的義務はないが、commit 5確認を兼ねた可能性が未解決。login実走の集合・tipが欠け、前回も「寄与未確定」とした（同`:85,90,102`）。

この2本について代替証拠が揃えば、t2797の残件は7→6→5、全体は20→19→18になる。**18を実測済み・確定残件数として出してはいけない。** ほかの緑再走の組替え可能性も、この資料だけで完全には否定できない。

**P2の評価。** 他の必要条件を失わないことを求める部分は妥当。ただし「初回診断に使った走は置換不可」と目的分類だけで除く部分は、D325からは導けない。単独走が初回診断やfix確認を兼ねてもよい。D325は「既に回す走行の形を変える」（`契約/D325.md:3–13`）のであり、無用途の走だけを転用する規定ではない。

したがってこの表は**P2に沿った保守的な証拠整理**であって、D325を満たす最小構成の計算ではない。

## 5 項 9

**(i) 5 nodeはすべて同一file。**

T-2737の生log `acceptance-child-final-1.log:3–5`：

- `test_define_sink_cross_product_classifies_t2155_production_sinks_exactly`
- `test_define_sink_cross_product_t2520_certify_entry_removal`
- `test_patch_define_inventory_matches_condition_gate_registry`

T-2797の同log`:3–4`：

- `test_reviewed_ccbench_measurement_launches_use_bounded_sites`
- `test_reviewed_process_launch_inventory_is_recursive_and_exact`

すべて `orchestrator/tests/test_ccbench_spawn_sites.py`。summaryも3 failed / 2 failedと一致する。

**(ii) fix前のmodule名検索では同fileを引けなかった。**

実行した読み取り検索：

```bash
git grep -n -e run_ss2pl_lock_study -e ss2pl-lock-protocol-study \
  '134ea235c^' -- orchestrator/tests/test_ccbench_spawn_sites.py

git grep -n -e b5_generator_contrast -e b5_contrast_launch -e p3_s4_loop \
  '517fd5451^' -- orchestrator/tests/test_ccbench_spawn_sites.py
```

両方hitなし。後者の `b5_generator_contrast` はreport名も包含する。T-2737のtests全体検索は `test_hooks.py` と `test_ss2pl_lock_study.py` を引くが、当該fileは引かない。

理由は名前参照ではなくdirectory列挙でproductionを検査するため：

- T-2737 fix前：同file`:426,476,582` がPython列挙、`:638` がpatch列挙、`:884` がbuild source列挙。
- T-2797 fix前：同file`:422,472,578,634,901`。
- 現行：`_process_launch_sites` `:422–434`、patch列挙`:628–640`、build source列挙`:904–914`。

**(iii) T-2820のproduction変更条件は両waveで発火する。**

- T-2737はcommit `0bd0895da` が `tools/pegasus/run_ss2pl_lock_study.py` とpatchを変更。
- T-2797は `前回/verbatim/changed_files.txt:24` のproduction4 fileを変更。

D2194項8は当該fileと `test_check_subprocess_bytecode_guard.py` の2 file追加を既に裁定している（`契約/D2194-item8.md:5–8`）。**適用されていれば両例を集合へ載せられる**。ただし当時の実行への遡及的な違反認定には使わない。

**(iv) directory列挙を探す既存のgrepでも拾える。**

全 `glob/rglob/iterdir/os.walk` を無条件検索すると現行で **130 test file**。tmp/output検査も大量に含むため、その130本を焦点走へ追加する案は過剰。

今回、検索を「`*.py` のglob/rglob、`os.walk(repo_root)`、`verifier_dir.iterdir()`」に絞ると **20 file**。以下は検索hitのfile:lineであり、全件を実行すべき一覧ではない。

| file（すべて `orchestrator/tests/`） | 行 |
|---|---:|
| test_campaign.py | 5328 |
| **test_ccbench_spawn_sites.py** | **428** |
| test_dev_wave_land.py | 3487 |
| test_login_headroom.py | 1630 |
| test_p3_b4_analysis_path.py | 303 |
| test_p3_build_authority_cli.py | 1226 |
| test_p3_exploration_namespace.py | 138 |
| test_p3_s4_loop.py | 2214 |
| test_pegasus_dispatch_compute.py | 2251 |
| test_reflux_ir.py | 293 |
| test_s1_known_axes_freeze.py | 641 |
| test_s8b_floor_campaign.py | 1722 |
| test_s8b_floor_stats.py | 1621 |
| test_s8b_oracle_manifest_contract.py | 49 |
| test_s8b_oracle_report.py | 5831 |
| test_s8b_ratified_freeze.py | 3074 |
| test_silo_ladder_rung1_driver.py | 1049 |
| test_t1286_commit_receipt.py | 802 |
| test_t338_submission_gate_unit5.py | 494 |
| test_t671_source_binding.py | 600 |

この絞り込みは網羅的なinventory抽出器ではない。例えば `rglob("*")` 型もある。**今回の2例を拾えるかにはYES**であり、fix前tipにも当該列挙が存在することをgit grepで確認した。

memoryの具体的な文面・版・pathは射影されていないため、「既存memoryがこの検索を正確に義務づけていた」とは認定しない。新しい目録基盤は不要で、名前検索後に列挙consumerを確認する既存操作で足りる。

**(v) 追加時間。**

1. 腕Sの `test_ccbench_spawn_sites.py` 単独jobを再利用する。別の単独jobを足さない。
2. 同node・同job内で、基準集合 \(F\) と \(F∪\{当該file\}\) を別invocationとして測る。
3. 各invocationのwallとpytest秒、node数、rcを記録。差はその配置での集合追加時間であり、単独所要との一致を要求しない。

**P5の集合操作は要修正。** 前回は21-file集合に当該fileがなかったと記す（`前回/README.md:116`）。一覧がそれを裏付ければ、比較は「21から抜いた20対21」ではなく、**元の21対追加後22**。7変更fileのリストはfix後まで含むので、過去の21-file集合と同じ集合ではない。

所要台帳は `acceptance_duration_ledger.json:3856–3902` に **47 entry、合計224.535秒、最大100.0秒**。224.5秒はその合計の丸め表示。

さらに生成器 `tools/update_acceptance_duration_ledger.py:124–143,267` は **有効数字2桁へROUND_HALF_UP** する。したがって100.0秒も未丸めの生時間ではない。これらはJUnit由来の丸め済みnode所要であり、**file単独wall・xdist集合追加時間の実測値には使えない**。

## 6 過剰・削除

今回のplanで新設しないものは、新harness、汎用batch基盤、inventory registry、新gate、新台帳。R2の入力・結果設計は採否判断用であり、今回実装しない。

実測を削れる箇所：

- k・確認済みs・過去の4区間・受入赤nodeは既存資料で足りる。
- genericのargv/env/site/hold機序は静的に分かる。個別の確認jobを多数作らず、腕Cの最初のjobに環境情報を残す。
- 項9の単独時間は腕Sの7本中1本を再利用。
- heldは走らせない。K3は既存817秒、うち固定費735秒の観測値と実装範囲だけを引く（`前回/README.md:101`）。
- P2のcは再実行では証明できない。必要なのは過去argv・tip・走行目的の証拠。
- 20候補または130候補を全部走らせない。今回の局所対象は既知の当該file。

## brief への指摘

1. **P2はD325より狭い。** 初回診断・fix確認と単独確認は兼用できる。目的分類だけから最小残件数を出せない。
2. **P3の21-file argvが欠落。** 指定verbatimでは件数までしか確定できず、完成commandには元投入argvが必要。
3. **P3の「同条件」は限定が必要。** 同SHAでもgeneric/testsのenv・記録・interpreter probeが違う。SのRUNとCの同invocation時間も等しいとは限らない。
4. **D289は並行許可だけでない。** job間性能比較のnode交絡条件もある。1対の観測差を純粋なR2効果にしない。
5. **P5は当該fileが元集合に含まれる前提を置いている。** 前回記述とは逆で、確認後は21対22になる可能性が高い。
6. **所要台帳は生時間ではない。** 224.5秒・100.0秒を新たな実測の代用にできない。
7. **D325理由欄の必須dispatchは現行コードと不一致。** bounded localは実在する。ただし今回それを実測しないP6は維持できる。
8. **genericではreceipt等を全面的に失わない。** 失うのは個別invocation単位のdispatch証拠と通常の親側記録形である。

## 総括

**G・Lとも既存経路は実在する。R2の恒久対応はflag追加だけではなく、個別env・結果・記録主体の設計が必要だが、新task追加は避けられる。**

項9は、module名検索では両例を拾えず、directory列挙検索または既裁定T-2820なら拾える。追加時間は未測定。

親へ返す未確定点は、**21-fileの完全argv、置換候補cの代替証拠、比較値を因果効果として扱わない実測protocol**。残件20は確認済み証拠からの値であり、必要追加job数の確定値ではない。