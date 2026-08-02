## 所見

### [RA-1] caller 注入 `site` で Pegasus 経路そのものを legacy へ切り替えられる

深刻度: **BLOCKER**

根拠:

- [p3_s4_loop_trigger_gating.py:456](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t277-pegasus-measure/orchestrator/campaign/p3_s4_loop_trigger_gating.py:456) と [同:557](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t277-pegasus-measure/orchestrator/campaign/p3_s4_loop_trigger_gating.py:557) は `site` を公開 keyword として受け取る。
- [同:470](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t277-pegasus-measure/orchestrator/campaign/p3_s4_loop_trigger_gating.py:470) と [同:574](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t277-pegasus-measure/orchestrator/campaign/p3_s4_loop_trigger_gating.py:574) は非 `None` の値を実 site と照合せず信頼する。
- `resolved_site == OTHER` なら [同:488](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t277-pegasus-measure/orchestrator/campaign/p3_s4_loop_trigger_gating.py:488) で `attestation_mode="none"` の linux 契約を取得し、[同:498](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t277-pegasus-measure/orchestrator/campaign/p3_s4_loop_trigger_gating.py:498) では `env_contract` を渡さない。
- v2 identity 自体は [buildcache.py:493](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t277-pegasus-measure/orchestrator/campaign/buildcache.py:493) で実 site を使う。しかし注入値により v2 経路へ入らなければ、その保証は発火しない。
- M13 のテストは [test_buildcache_v2.py:351](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t277-pegasus-measure/orchestrator/tests/test_buildcache_v2.py:351) の buildcache 単体だけであり、driver の `site` 注入を検査しない。F14/F21/F72 型の [恒真ゲート] [防壁の射程誤認] である。

具体的な失敗シナリオ:

実際には `PEGASUS_COMPUTE` 上で、programmatic caller が `drive_iteration(..., do_build=True, site=OTHER)` を呼ぶ。Pegasus campaign 分離・required attestation・no-resume・v2 build がすべて外れ、既存 campaign に `env_tag="linux-baremetal"` の WAL `build_start` まで到達する。`g++-13` があれば計測まで進み、無ければ build-error になるが、どちらも「compute を拒否した」ことにはならない。

提案:

`site` を `run_one_iteration` / `drive_iteration` / `_run_workload` の引数から除去し、authoritative sink で一度だけ実解決する。転送が必要なら caller 値は `expected_site` として実値との完全一致検査にのみ使う。

---

### [RA-2] `run_campaign` の新設 seam は attestation・env 分離・no-resume を全部迂回する

深刻度: **BLOCKER**

根拠:

- [loop.py:46](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t277-pegasus-measure/orchestrator/campaign/loop.py:46) は公開 `run_campaign` に `env_contract` を追加したが、attestation receipt を要求しない。
- campaign ID は常に caller の `cfg` だけから導出される（[loop.py:56](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t277-pegasus-measure/orchestrator/campaign/loop.py:56)）。
- `env_contract` はそのまま `evaluate` へ渡される（[loop.py:147](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t277-pegasus-measure/orchestrator/campaign/loop.py:147)）。
- `pipeline.evaluate` は qualification opt-in でない限り contract と `env_tag`・clock・NUMA を照合せず、[pipeline.py:553](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t277-pegasus-measure/orchestrator/campaign/pipeline.py:553) で WAL を書いてから v2 build へ進む。
- [test_campaign.py:2611](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t277-pegasus-measure/orchestrator/tests/test_campaign.py:2611) は Pegasus contract を直接渡し、[同:2625](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t277-pegasus-measure/orchestrator/tests/test_campaign.py:2625) で campaign ID が未分離のままであることを正例として固定している。

具体的な失敗シナリオ:

`run_campaign(T.default_cfg(), [新規genome], perf, "pegasus", 2100, env_contract=lookup("pegasus"))` を compute 上で直接呼ぶ。attestation なしで v2 build が始まり、Pegasus record が既存 linux campaign root に混入する。既存 loop state/WAL があっても `allow_resume=False` は検査されない。

提案:

required contract の enforcement を `run_campaign` より下の唯一の measurement sink に置く。contract・env tag・clock・NUMA・campaign identity・receipt を一体で検査し、caller が個別 dataclass を組み合わせて権限を作れない形にする。

---

### [RA-3] `allow_resume=False` は reject branch と入口 stop に mask される

深刻度: **MAJOR**

根拠:

- resume 検査は [p3_s4_loop_trigger_gating.py:488](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t277-pegasus-measure/orchestrator/campaign/p3_s4_loop_trigger_gating.py:488) にある。
- その前に [同:481](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t277-pegasus-measure/orchestrator/campaign/p3_s4_loop_trigger_gating.py:481) の quarantine/auditor gate が走り、reject なら即 return する。
- reject sink は [p3_s4_loop.py:226](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t277-pegasus-measure/orchestrator/campaign/p3_s4_loop.py:226) で `BUILD_START→ABORT` を WAL に書く。
- `drive_iteration` も [p3_s4_loop_trigger_gating.py:580](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t277-pegasus-measure/orchestrator/campaign/p3_s4_loop_trigger_gating.py:580) で既存 state を読み、入口 stop なら resume 検査へ到達しない。
- M6 テストは [test_p3_s4_loop_trigger_gating.py:626](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t277-pegasus-measure/orchestrator/tests/test_p3_s4_loop_trigger_gating.py:626) で clean proposal だけを使う。`_assert_fresh_campaign_state` の monkeypatch は実際の `invoke()` の call graph に含まれず、reject branch を検査しない。

具体的な失敗シナリオ:

既存 Pegasus loop state がある状態で禁止識別子を含む proposal を渡す。resume gate より先に syntax reject が WAL を追記し、`drive_iteration` は iteration を進めて checkpoint を保存する。`ExecutionGuardError` は発生しない。また、build 中 crash で WAL だけ残り loop state が無い場合も次回 resume を許す。

提案:

no-resume は既存 artifact の検査を含め、provenance・WAL・quarantine の最初の書込みより前に置く。clean proposal だけでなく diff/syntax/auditor reject と crash-tail を負例にする。

---

### [RA-4] 兄弟 driver と 8c の COMPUTE 拒否は外側入口にしかなく、内部 sink は開いている

深刻度: **BLOCKER**

根拠:

- 8c の拒否は [p3_autonomous_workload_trial.py:1029](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t277-pegasus-measure/orchestrator/campaign/p3_autonomous_workload_trial.py:1029) の `run_trial` にしかない。
- `_run_workload` は `site` を信頼し（[同:763](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t277-pegasus-measure/orchestrator/campaign/p3_autonomous_workload_trial.py:763)）、provider を実行後（[同:837](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t277-pegasus-measure/orchestrator/campaign/p3_autonomous_workload_trial.py:837)）に compute-admitted trigger へ到達する（[同:943](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t277-pegasus-measure/orchestrator/campaign/p3_autonomous_workload_trial.py:943)）。
- coverage の拒否は `main()` の [s8a_trigger_coverage.py:205](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t277-pegasus-measure/orchestrator/campaign/s8a_trigger_coverage.py:205) にあるが、programmatic `_build` は COMPUTE を許し（[同:102](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t277-pegasus-measure/orchestrator/campaign/s8a_trigger_coverage.py:102)）、`_run_trace` も無検査である。
- s8a/s6 の `_eval_one`（[s8a_trigger_sweep.py:347](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t277-pegasus-measure/orchestrator/campaign/s8a_trigger_sweep.py:347)、[s6_sort_sweep.py:301](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t277-pegasus-measure/orchestrator/campaign/s6_sort_sweep.py:301)）と backoff の `_run_screened_workload`（[backoff_sweep.py:82](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t277-pegasus-measure/orchestrator/campaign/backoff_sweep.py:82)）にも拒否がない。
- M14 テストは全 AST 上の call 数を数えるだけ（[test_p3_s4_loop_trigger_gating.py:437](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t277-pegasus-measure/orchestrator/tests/test_p3_s4_loop_trigger_gating.py:437)）。dead branch や `main()` だけでも緑になる。F21/F60/F72 の [恒真ゲート] [テスト代表性] 再発である。

具体的な失敗シナリオ:

compute 上で `_run_workload(..., do_build=True, site=PEGASUS_COMPUTE)` を直接呼ぶと、D108 が禁じる provider 実行が先に発火する。別経路では coverage の `_build` と `_one_run`、または sweep の `_eval_one` を直接呼び、linux-baremetal 用内部経路を compute 上で実行できる。

提案:

拒否を各 authoritative measurement/build sink に置く。M14 は AST presence ではなく、全 programmatic entrypoint を COMPUTE で呼び、subprocess・provider・WAL が未到達であることを poison test する。

---

### [RA-5] ambient prefix の正準化が非単射で、異なる実 build が同一 identity になる

深刻度: **BLOCKER**

根拠:

- [buildcache.py:350](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t277-pegasus-measure/orchestrator/campaign/buildcache.py:350) は Unix の `:` で分割した後、`;` で再結合する。
- 空要素は cwd へ解決せず `""` のまま保存する（[同:355](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t277-pegasus-measure/orchestrator/campaign/buildcache.py:355)）。
- 明示 prefix は正準化せず、そのまま identity と argv に入る（[同:495](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t277-pegasus-measure/orchestrator/campaign/buildcache.py:495)）。
- テストも空要素を空のまま期待している（[test_buildcache_v2.py:279](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t277-pegasus-measure/orchestrator/tests/test_buildcache_v2.py:279)）。
- リポジトリ自身が CMake の PATH 型 `:` 分割を既知事実としている（[failures.md:283](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t277-pegasus-measure/docs/failures.md:283)）。

具体的な失敗シナリオ:

Pegasus/Linux で次の二値は同じ identity `/tmp/p;/tmp/q` になる。

- ambient `/tmp/p:/tmp/q` — CMake は二つの prefix を検索する。
- ambient `/tmp/p;/tmp/q` — CMake は一つの合法な path を検索する。

さらに `CMAKE_PREFIX_PATH=:/tmp/q` は CMake/PATH 意味論では cwd も検索するが、identity は cwd を含まない。異なる cwd で同じ cache keyになる。明示 `dependency_prefix="deps"` も cwd 非束縛なので同型である。symlink を identity 計算後に差し替える TOCTOU も残る。

提案:

identity には区切り文字列ではなく path 要素の JSON 配列を入れる。空要素は実効 cwd に解決し、明示相対 path も絶対化する。得た同じ snapshot を CMake に明示して ambient を除去し、identity 値と実 build 値を単一化する。

---

### [RA-6] trace/perf の依存物同一性は保証されない

深刻度: **MAJOR**

根拠:

- trace と perf は [pipeline.py:580](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t277-pegasus-measure/orchestrator/campaign/pipeline.py:580) 以降で順次、独立した `build_v2` 呼出しとして作られる。
- identity が持つのは prefix の path 文字列だけ（[buildcache.py:512](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t277-pegasus-measure/orchestrator/campaign/buildcache.py:512)）。
- build 間で依存 directory の内容 hash・inode・manifest を再照合しない。`_assert_trace_diff` 等は CCBench source と trace symbol を見るだけである。

具体的な失敗シナリオ:

trace build 後に別 process が `/scr/job/deps` の headers/libs を B へ置換し、perf build を続行する。prefix 文字列は同じなので両 build は通り、trace は A、fitness は B の依存物で作られる。規律1の「trace/perf は同じ依存」が成立しない。

提案:

依存 tree の immutable manifest/content digest を trace 前と perf 後に照合し、両 preimage が `trace` bit 以外で完全一致することを pipeline で assert する。これは親裁定の限定的な「文字列束縛」を超えるが、規律1の保証には必要である。

---

### [RA-7] env 分離後も trigger CLI が legacy campaign layout を参照する

深刻度: **MAJOR**

根拠:

- `drive_iteration` は compute 用 config/layout を導出する（[p3_s4_loop_trigger_gating.py:574](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t277-pegasus-measure/orchestrator/campaign/p3_s4_loop_trigger_gating.py:574)）。
- `--run-iteration` の実行後、`main()` は元の `cfg` から legacy layout を再計算する（[同:688](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t277-pegasus-measure/orchestrator/campaign/p3_s4_loop_trigger_gating.py:688)、[同:698](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t277-pegasus-measure/orchestrator/campaign/p3_s4_loop_trigger_gating.py:698)）。
- fixture main も compute layout で実行後、[同:734](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t277-pegasus-measure/orchestrator/campaign/p3_s4_loop_trigger_gating.py:734) で legacy layout に digest を書く。

具体的な失敗シナリオ:

compute 実行は Pegasus campaign に WAL/provenance を生成するが、CLI は既存 linux campaign の checkpoint・provenance を表示・検査する。古い成果物が残っていれば無関係な bytes で rc 0 になり得て、無ければ実計測済みなのに rc 1 になる。F30 型の consumer 取り残しである。

提案:

`drive_iteration` の返値に authoritative `campaign_id` / `layout_root` を含め、CLI はそれだけを参照する。compute CLI 経路の正負テストを追加する。

---

### [RA-8] M1〜M14 の変異帰属は単一理由になっておらず、M14 は意味的に kill されていない

深刻度: **MAJOR**

根拠:

- M4 の無効化は attestation 順序テスト（[test_p3_s4_loop_trigger_gating.py:539](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t277-pegasus-measure/orchestrator/tests/test_p3_s4_loop_trigger_gating.py:539)）と失敗伝播の2パラメータ（[同:595](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t277-pegasus-measure/orchestrator/tests/test_p3_s4_loop_trigger_gating.py:595)）を同時に赤くする。
- M7/M8 は専用 cache-miss テストに加え、exact manifest テスト（[test_buildcache_v2.py:475](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t277-pegasus-measure/orchestrator/tests/test_buildcache_v2.py:475)）でも赤になる。
- M11 は campaign identity 単体と measurement sink の双方で赤になる。M1〜M3にも同型の重複がある。
- M14 の字面上の call 削除は AST count で赤になるが、期待された「compute 拒否負例」は実行されない。現在の programmatic bypass 自体がテスト緑のまま存在する。
- これは [failures.md:405](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t277-pegasus-measure/docs/failures.md:405) の F28 と [同:1235](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t277-pegasus-measure/docs/failures.md:1235) の F60 の再発である。

具体的な失敗シナリオ:

helper call を `main()` の dead branchへ移しても M14 テストは通る一方、内部 measurement sink は開いたままである。変異台帳には「KILLED」と記録できるが、実防壁の受理集合は変わらない。

提案:

M1〜M13は静的には少なくとも一つの assertion が反応するが、単一帰属になるよう期待 node を再整理する。M14は behavioral mutationへ再登録する。pytest・変異実走は行っていないため、実測 kill は主張できない。

## 子の報告との食い違い

- 単位 B の「解決済み site を配線」は、実装上は caller 注入値を無照合で配線している。actual site ではない。
- 「8c compute 運転は未開放」は `run_trial` に限れば正しいが、`_run_workload` 直呼びでは開いている。
- 「全兄弟 driver が COMPUTE を拒否」は outer entrypoint に限る。内部 build/evaluate sink は拒否しない。
- 「no-resume gate は freshness を無効化しても独立して効く」は clean proposal だけの主張で、reject branch・入口 stop・WAL-only crash stateには成立しない。
- 単位 A の「実際に効いた ambient prefix を identity に束縛」は、空要素・`;` 衝突・明示相対 path・symlink TOCTOUにより裏付けられない。
- 「required attestation と env 分離」は通常の clean trigger 経路ではコード上確認できるが、公開 `run_campaign` / `evaluate` 経路には及ばない。
- 両報告の「pytest 未実走」という記載には食い違いはない。本レビューもpytestを実行していない。

## GO / NO-GO

**NO-GO。**

caller 注入 `site` と公開下位 API により、required attestation・Pegasus campaign 分離・no-resume を迂回して build/WAL へ到達できる。加えて prefix identity に決定的な衝突があり、異なる依存条件の binaryを同一 cache keyで再利用できる。

## 総括

- 通常 trigger の clean 経路では attestation は `run_campaign` より前にある。  
- しかし `site=OTHER` 注入と下位 API 直呼びで、その経路全体を外せる。  
- no-resume は reject/WAL branch より後ろにあり、独立した防壁ではない。  
- 兄弟・8c 拒否は入口限定で、M14 テストは call の存在しか見ない。  
- prefix 正準化は異なる CMake 探索集合を同一 identity に畳み込む。  
- 静的レビューのみ実施し、pytest・変異実走は行っていない。