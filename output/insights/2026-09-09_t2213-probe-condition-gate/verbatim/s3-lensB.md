## blocker

1. 段 2 の `prepare_masstree_fetchcontent()` 呼び出し計画は、必須引数が不足している。

   [s2-plan.md:12](/home/SFC/tanab/.claude/jobs/33d0016c/tmp/artifacts/t2213-probe-condition-gate/s2-plan.md:12) は一時 `FETCHCONTENT_BASE_DIR` を用意して呼ぶとだけ定めるが、実 API は [buildcache.py:2009](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2213-probe-condition-gate/orchestrator/campaign/buildcache.py:2009) で `expected_toolchain_manifest`、configure / target timeout を必須とする。probe は現在 `cc,cxx` しか取得していない。

   成果物影響: このまま実装すると性能経路は build 前に例外終了し、certify 経路は rejected JSON になり、新成果物の受理集合が空になる。

   通る正例: [buildcache.py:1270](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2213-probe-condition-gate/orchestrator/campaign/buildcache.py:1270) の `observed_toolchain_manifest(cc,cxx)` を cell loop 前に一度固定し、その同じ値を prebuild へ渡す。必須 kwargs の exact 検査も足す。

2. 要求された `runtime meaning` は実装されず、全 13 macro が `unestablished` のまま admission を通る。

   プラン自身が [s2-plan.md:83](/home/SFC/tanab/.claude/jobs/33d0016c/tmp/artifacts/t2213-probe-condition-gate/s2-plan.md:83) でこの状態を認めている。実際、meaning registry は [condition_meaning_gate.py:245](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2213-probe-condition-gate/orchestrator/campaign/condition_meaning_gate.py:245) の集合だけで、今回の 13 macro は含まれない。`declare_define_runtime_meaning()` は `None` を返し、[condition_meaning_gate.py:3300](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2213-probe-condition-gate/orchestrator/campaign/condition_meaning_gate.py:3300) が `unestablished` record を発行する。それでも [condition_meaning_gate.py:4063](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2213-probe-condition-gate/orchestrator/campaign/condition_meaning_gate.py:4063) は `green | unestablished` を admission 成功とする。`certified-selection` でも判定は強化されない。

   成果物影響: certified receipt、性能 JSON、診断 JSON が「3 要素の関門を通った」と扱われても、実行時意味を確かめた証拠は無い。親 brief の「本当に実行時の挙動を変えたかを機械で確かめる」は成立しない。

   通る正例: 実際に使う各 non-stock requestについて `runtime-meaning/green` の production-issued recordを得る。現行 API で不可能なら、受理集合を緩めず、台帳解除を保留して meaning witness 整備を別裁定へ返す。

3. 「既存成果物を無効にしない」は archival な意味では正しいが、この変更が既存測定へ関門証拠を遡及付与するという意味では誤りである。

   既存 dynamic-backoff 図は [dynbackoff.provenance.json:343](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2213-probe-condition-gate/output/insights/2026-09-05_dynamic-backoff-mechanism/figures/dynbackoff.provenance.json:343) で旧 `repo_head` と `driver_sha256=8004de49...` を固定している。新しい実行は [t2187_adaptive_const_probe.py:916](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2213-probe-condition-gate/tools/pegasus/probes/t2187_adaptive_const_probe.py:916) で変更後 bytes の hash を記録する。plotter は [plot_dynamic_backoff.py:1274](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2213-probe-condition-gate/tools/plotting/plot_dynamic_backoff.py:1274) で全入力の common identity 完全一致を要求するため、新旧を混ぜられない。新 certify も [t2187_adaptive_const_probe.py:1997](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2213-probe-condition-gate/tools/pegasus/probes/t2187_adaptive_const_probe.py:1997) で performance artifact の `repo_head` を現在値と照合する。

   反実仮想についても、解析器は [backoff_counterfactual_analysis.py:20](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2213-probe-condition-gate/orchestrator/campaign/backoff_counterfactual_analysis.py:20) の測定時 v1 sha と [backoff_counterfactual_analysis.py:582](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2213-probe-condition-gate/orchestrator/campaign/backoff_counterfactual_analysis.py:582) の解析 v2 sha を固定する一方、現在の producer は [t2187_adaptive_const_probe.py:3119](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2213-probe-condition-gate/tools/pegasus/probes/t2187_adaptive_const_probe.py:3119) で現行 v2 sha を記録する。変更後の gated run は既存 12 件 cohort に加入できない。

   成果物影響: 既存成果物は歴史的主張のまま存続するが、condition-gated へ昇格できない。新しい gated 主張には homogeneous な再測定一式が必要になる。

   通る正例: この変更を prospective-only と明記し、既存 reportを昇格させない。新規成果物を使う場合は、新 driver hash / repo head / exact axes で揃えた cohortと、発効後変更を明記した新事前登録または erratumを用意する。

4. (P1) の併走許可は止めるべきである。

   親自身が [brief-t2213.md:71](/home/SFC/tanab/.claude/jobs/33d0016c/tmp/brief-t2213.md:71) で、T-2417 が同じ probe を 315 行変更し、同じ 2 ledger entry の lineと理由文を変更すると記録している。T-2213 はその entry を削除し、probe の同じ sink直前へ挿入するため、単なる隣接変更ではない。T-2417 が先に成果物を生成すれば、その成果物は ungated のまま残る。後から機械的に統合すれば、T-2417 側の `sink_lineno` は挿入分だけ古くなり、[test_ccbench_spawn_sites.py:2710](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2213-probe-condition-gate/orchestrator/tests/test_ccbench_spawn_sites.py:2710) の live-sink exact 検査が赤になる。

   成果物影響: policy-arm 性能成果物が gate 前 driverで確定するか、ledger pinが誤った sinkを指す。どちらも T-2213 完了後の受理根拠に使えない。

   通る正例: T-2213 と T-2417 を直列化し、後着 waveを先着 commitへ rebaseする。統合後 bytesで sinkを再列挙し、probe deferred 0、両 sink `covered`、各 gate-call 除去変異が対応 sinkだけを赤にすることを確認する。

## must-fix

1. production 正例を両層 stub にしない。

   [s2-plan.md:121](/home/SFC/tanab/.claude/jobs/33d0016c/tmp/artifacts/t2213-probe-condition-gate/s2-plan.md:121) は [test_t2187_adaptive_const_probe.py:180](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2213-probe-condition-gate/orchestrator/tests/test_t2187_adaptive_const_probe.py:180) の fixtureで新 helperも stubにする。ここでは既に build自体が [test_t2187_adaptive_const_probe.py:209](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2213-probe-condition-gate/orchestrator/tests/test_t2187_adaptive_const_probe.py:209) の fakeである。閉包検査も helper内に3個の関数名が在ることを静的に見るだけで、実 CMake経路を通さない。

   成果物影響: root、toolchain manifest、FetchContent、configure argvの結線が壊れていてもテストが緑になり、実行時には成果物が一件も完成しない。

   通る正例: 共通 fixture外に、patched checkoutと最大13 macroを持つ cohort2 policy2 genomeを実 helperへ渡す正例を1件置き、production evaluator発行の supply recordと family admissionを確認する。main build / measurementは spyのままでよい。

2. gate対象 `genome` と実 build対象 `genome` の同一性を main-path testで固定する。

   `_require_requests_match_build_arguments()` は helperへ渡された genome内部しか比較しない。閉包検査も [test_ccbench_spawn_sites.py:1700](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2213-probe-condition-gate/orchestrator/tests/test_ccbench_spawn_sites.py:1700) で wrapper callを見た時点で source macro全体を coveredにするため、「gate(base_genome) の後で build(policy_genome)」でも通りうる。T-2417 統合時に特に現実的な事故である。

   成果物影響: policy binaryとは別の条件集合で family admissionが成立し、誤った性能・診断・certification成果物が受理される。

   通る正例: sink 1 / 2 それぞれで gate spyと build spyが受けた `Genome` の object identityまたは canonical bytes完全一致を要求し、gate引数だけ別 genomeへ替える変異を赤にする。

3. sink 1 の timing / budget意味を裁定する。

   sink 2 は gate後へ `build_started` を動かす計画だが [s2-plan.md:14](/home/SFC/tanab/.claude/jobs/33d0016c/tmp/artifacts/t2213-probe-condition-gate/s2-plan.md:14)、sink 1 は [t2187_adaptive_const_probe.py:3333](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2213-probe-condition-gate/tools/pegasus/probes/t2187_adaptive_const_probe.py:3333) で計時開始済みの `_run_build_with_deadline` 内へ gateを入れる。したがって `build_phase` と900秒 hard deadlineに13 request分の gateを混ぜる。

   成果物影響: certificationの `build_phase` 値と timeout受理集合だけが性能経路と異なる意味に変わり、従来通った requestが `trace-build-budget-exceeded` で rejectedになりうる。

   通る正例: gate時間を build budgetへ含めるのか独立 phaseとするのかを親が明記し、両 sinkで同じ意味を採用する。独立させるなら gate固有の有界 timeoutを持たせ、build計時は `buildcache.build()` 直前から始める。

## nit

- consumer 台帳は数え直した。各 probe entryは、宣言 [test_ccbench_spawn_sites.py:911](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2213-probe-condition-gate/orchestrator/tests/test_ccbench_spawn_sites.py:911)、exact tuple [test_ccbench_spawn_sites.py:2671](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2213-probe-condition-gate/orchestrator/tests/test_ccbench_spawn_sites.py:2671)、理由文 tuple [test_ccbench_spawn_sites.py:2688](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2213-probe-condition-gate/orchestrator/tests/test_ccbench_spawn_sites.py:2688) の3箇所、2 entry合計6表現を持つ。プランは変更が必要な3群を全て挙げている。

- 件数関連は `len(matches) <= 1` が :947、各 live sinkの `len(matches) == 1` が :2717、全体の動的長さ比較が :2720。固定の「7件」assertは無い。`_deferred_member` の呼び手は :2580、:2718、:2730、:2810 の4箇所で、いずれも一般式なので変更不要。プランが後二者を列挙していない点は inventory上の軽微な漏れだけである。成果物影響: なし。

- probe line pinは `3375` が :922 と :2674、`3749` が :934 と :2678 の各2箇所だけである。`orchestrator/tests/` の probe path検索では、この台帳外に sink line literalを持つ検査は無い。`test_hooks.py` と `test_plot_dynamic_backoff.py` は pathだけを持つ。

- production分類 exact testは実在し、[test_ccbench_spawn_sites.py:2895](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2213-probe-condition-gate/orchestrator/tests/test_ccbench_spawn_sites.py:2895) からである。現在の期待値は S1 が `covered=4, proven-unreachable=34`、S8B が `covered=38`。現状 probeは sink 1 が `proven-unreachable=38`、sink 2 が `deferred=14, proven-unreachable=24`。計画形をメモリ上で静的分類すると、両 sinkとも `covered=14, proven-unreachable=24` になった。

- 14件は実 genome由来13 macroに、[t2187_adaptive_const_probe.py:3283](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2213-probe-condition-gate/tools/pegasus/probes/t2187_adaptive_const_probe.py:3283) の positive-control metadataだけに現れる `IZANAGI_BREAK_NOREAD_VALIDATION` を加えた数で、24は registry 38との差である。14番目を `covered` と呼ぶのは静的解析上の過大分類だが、実 request-set testが13件を exact固定する限り、現行成果物の受理集合は変わらない。

- reviewed defaults 13件は [screening_driver.py:51](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2213-probe-condition-gate/orchestrator/campaign/screening_driver.py:51) と一致する。`BACKOFF_STEP_POLICY_SEED=11400714819323198485` は `2**64` 未満で、gateの一般 request値検査は [condition_meaning_gate.py:881](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2213-probe-condition-gate/orchestrator/campaign/condition_meaning_gate.py:881) の exact int/string化であり、signed 64-bit上限を課さない。patch側も数値 literalではなく十進文字列を `uint64_t` へ読む。値は受理される。

- `use_class` は [condition_meaning_gate.py:3442](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2213-probe-condition-gate/orchestrator/campaign/condition_meaning_gate.py:3442) に `raw-measurement` と `certified-selection` の両方が実在する。sink 1 / 2 の用途ラベルとしては整合する。ただし blocker 2 のとおり、ラベルは admission強度を変えない。

- 現行 driver shaや旧 `8004de49...` を source bytesの固定値と照合するテストは無い。probe testは実行時に `hashlib.sha256(DRIVER.read_bytes())` を計算し、plot testの `DRIVER_SHA="4"*64` は合成 fixture値である。

## 親 brief への指摘

- **(P1) 不同意。** 同じ sink、同じ ledger entry、同じ producerを変更するため直列化が必要である。T-2417 の成果物生成が先なら ungated artifactが残り、統合が先なら line pinと delete-versus-editの再裁定が要る。

- **(P2) 不同意。** 正しく統合された同一 `genome` については flags由来要求が新しい policy値も覆う、という限定点には同意する。しかし、それは gate前に既に生成された成果物、merge時の gate/build genome取り違え、T-2417 の line pinを救わない。静的閉包も引数同一性を証明しない。

- **(P3) 同意。** entry 2 は独立した live `buildcache` sinkであり、performance、diagnostic、T-2417 の policy-arm経路を実際に生む。解除文言が無いことは「永久繰延べ」の根拠ではなく、entry 2だけ残すと当該成果物を ungatedで受け入れるため不適切である。

- trusted factsから二重発火する経路は確認できない。現実の競合は、gate未発火の旧成果物、stale ledger、または別 genomeを gateしたまま閉包が通る経路である。関門除去負例の14件中1件は metadata由来だが、残る13件も failureになるため負例全体が恒真というわけではない。

## 総括

- 現プランは必須 toolchain manifest不足のため、そのままでは実行不能である。
- 最大のscope不足は、runtime meaningが全件 `unestablished` のまま admissionされる点である。
- 既存成果物は保存できるが、新しい関門証拠を遡及取得したことにはならない。
- T-2417 は同一 producerと台帳を変更するため、着地順を直列化して再分類すべきである。
- ledger consumer、追加 line pin、13 defaults、2 use classの具体値はプラン記載どおりだった。
- pytestは実走していない。実施したのは全文読解、`rg`、AST分類の読み取り専用検査だけである。