## 所見

- **B01 — must-fix — [s2-plan.md:63](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2847-mutation-run/s2-plan.md:63)**  
  「各 job で同じ flag の stock を一度」は、同じ job に異なる workload の patch を入れる計画と整合しない。表には `4/50/false/5`、`4/0/false/5`、`1/0/false/1` など複数の条件がある。**stock build は job ごとに共有できるが、stock run は各 workload ごとに必要**。job の割当表を先に固定し、対照 run 数と結果の対応を事前登録する。

- **B02 — must-fix — [s2-plan.md:69](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2847-mutation-run/s2-plan.md:69)、[s8a_trigger_coverage.py:225](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2847-mutation-run/orchestrator/campaign/s8a_trigger_coverage.py:225)**  
  s8a の `_build` は `buildcache.build` を使わない。compiler は `buildcache.DEFAULT_CC/CXX` を CMake と condition gate に渡し、`source_digest.resolve_evidence` は既定では `g++-13` を使う。前回の s3/s5 と同様に **`resolve_evidence(cxx=計算ノードの CXX)` の差し替えが必要**。これで得た evidence を同じ `_build` 内の `attest_generator_output`、`derive_build_admission`、`require_build_admission(expected_policy=build_context.policy, expected_source=evidence)` に渡す構造なので、admission の検査を弱める必要はない。差し替え一覧を出力 meta に残す。

- **B03 — must-fix — [s2-plan.md:71](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2847-mutation-run/s2-plan.md:71)、[s2_verify_calibration.py:329](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2847-mutation-run/orchestrator/campaign/s2_verify_calibration.py:329)**  
  V21 の追加 verify は `_verifier_run` の後、trace 削除前に実行できる。ただし元関数の返値だけが driver JSON に入る。**証人なし実行の argv、rc、構造化 verdict を別の結果欄へ保存**しなければ、検出表の「同一 trace で S」を追証できない。前回の `VerifierRecorder` は生出力を受動保存できるが、集計欄への取り込みも起動器側で定める。`--expected-commits` とその値だけを除いた CLI を使い、verifier の判定は変更しない。

- **B04 — must-fix — [s2-plan.md:75](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2847-mutation-run/s2-plan.md:75)、[patchharness.py:120](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2847-mutation-run/orchestrator/campaign/patchharness.py:120)**  
  6 job を同じ checkout から同時に走らせる設計は成立しない。`applied()` は同一 submodule の apply→build→revert を直列化するうえ、s8a は骨格・計装・misattr をその区間で重ねる。**同時投入する job ごとに pin と登録済み patch を備えた別 checkout を用意するか、同一 checkout では直列実行**と明記する。dispatcher の `generic` は argv を受けるだけで、checkout の複製は行わない。

- **B05 — should — [s2-plan.md:69](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2847-mutation-run/s2-plan.md:69)、[s8a_trigger_coverage.py:259](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2847-mutation-run/orchestrator/campaign/s8a_trigger_coverage.py:259)**  
  s8a の `CLK` 既定値は 2100、`_run_trace` は `-clocks_per_us` を付けるが `numactl` は使わず、`extime` は `MULTI_FLAGS` / `SINGLE_FLAGS` に含まれる。計算ノードで採用した CLK を事前に固定し、meta と結果 JSON に一致して記録する。`_assert_single_tenant()` は `main()` 冒頭で一度呼ばれ、出力先は `repo_output_root()/env/pegasus/calibration/...` となるので、job 固有の出力 root が要る。

- **B06 — should — [s2-plan.md:71](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2847-mutation-run/s2-plan.md:71)、[s2_verify_calibration.py:295](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2847-mutation-run/orchestrator/campaign/s2_verify_calibration.py:295)**  
  変異 build は既存の `_broken_build_and_verify` が行う fresh な直接 CMake build でよい。一方、stock trace build の手順が計画に未記載。buildcache を使うなら admission と source evidence の供給が必要になるため、**同じ pin・`STOCK_G`・TRACE=1・compiler・依存物で、直接 CMake の stock build を起動器に明示**するのがこの計画に最も近い。stock に変異マクロを渡さず、各 workload の run と証人あり verifier を対応づける。

- **B07 — should — [s2-plan.md:38](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2847-mutation-run/s2-plan.md:38)、[test_condition_meaning_gate.py:3642](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2847-mutation-run/orchestrator/tests/test_condition_meaning_gate.py:3642)**  
  登録計画は同じ test ファイルの **module docstring の固定件数検査**を見落としている。14 個の新規 macro と witness を登録するなら、docstring の「43 patch-derived defines」「Twenty-five registered macros」を現数へ直す必要があり、その変更時には当該 test も赤になる。文面を据え置くと test は緑でも説明が虚偽になる。

- **B08 — should — [s2-plan.md:83](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2847-mutation-run/s2-plan.md:83)**  
  変異 matrix の候補⑤〜⑩は、挙げられた登録 test では実装の誤りを殺せない。①〜④も検出が複数 test に重なるため、各候補の失敗を単一 gate に帰属する matrix にはならない。⑤の未定義時の pin 一致、⑥の一 patch 一機構、⑦⑧の変更方向・範囲、⑨の同一 trace 再検証、⑩の stock 分離は、それぞれ source 差分・起動器記録・実走結果で確認する。今回の依頼を超える新規の汎用 gate にしない。

- **B09 — should — [s2-plan.md:24](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2847-mutation-run/s2-plan.md:24)、[request.md:5](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2847-mutation-run/request.md:5)**  
  V24 を YCSB で走らせても node 検証箇所には到達せず、検出表の「盲点として certified」にはできない。plan 自身が未到達対照と認めている。**V24 は未発生として記録**し、今回の完了表で盲点を実証した行として数えない。V26・V27 も `zipf` による同一 key の再選択は可能だが、発火証拠がなければ certified だけで盲点と判定しない。

- **B10 — nit — [s2-plan.md:81](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2847-mutation-run/s2-plan.md:81)**  
  段 5 の patch 2 組は出力ファイルの所有が分かれており、後段の登録・起動器 author と編集先も重ならない。ただし後段は **14 patch の最終 macro 名、directive、site 数を確定してから**始める必要がある。特に V18/V35 は同じ代入を別 patch で触るため、単独適用の前提を成果物に残す。

## 赤になる test の全列挙

新規 14 patch を置き、登録・固定表を更新しない場合に赤になるものは次のとおり。

| test / 検査 | 根拠と条件 |
|---|---|
| `test_p3_s4_loop.py::test_all_naked_izanagi_macro_patches_are_registered_or_allowlisted` | [`patches/*.patch` を走査し `IZANAGI_` token を path 別の許容集合と照合](‌/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2847-mutation-run/orchestrator/tests/test_p3_s4_loop.py:8468)。14 path の許容表追加が必要。`ledger.json` に入れる案は既存 ability probe の一件契約と目的が違う。 |
| `test_ccbench_spawn_sites.py::test_patch_define_inventory_matches_condition_gate_registry` | [patch の追加 `#if` から define を独立発見し `DEFINE_SPECS` の集合・path と照合](‌/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2847-mutation-run/orchestrator/tests/test_ccbench_spawn_sites.py:2905)。registry 未登録、macro 名または patch path の不一致で赤。 |
| `test_condition_meaning_gate.py::test_v1_domain_and_claim_boundaries_are_exact` | [supply domain・意味集合・25/26 件数を固定](‌/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2847-mutation-run/orchestrator/tests/test_condition_meaning_gate.py:3392)。登録だけ増やすと赤。 |
| `test_condition_meaning_gate.py::test_compile_time_branch_registry_and_fixtures_are_bound_to_real_patches` | [witness の順序・patch 中の directive と site 数を照合](‌/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2847-mutation-run/orchestrator/tests/test_condition_meaning_gate.py:1092)。witness 登録後、期待 tuple を更新しなければ赤。 |
| `test_condition_meaning_gate.py::test_compile_time_branch_selection_accepts_each_registry_macro` | [全 witness をパラメータ化して branch 選択数を確認](‌/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2847-mutation-run/orchestrator/tests/test_condition_meaning_gate.py:1422)。site 数や contrast の期待がずれると赤。 |
| `test_condition_meaning_gate.py::test_module_claim_names_the_exact_38_define_supply_domain` | [module docstring の「43」「Twenty-five」を固定](‌/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2847-mutation-run/orchestrator/tests/test_condition_meaning_gate.py:3642)。**patch 追加だけでは赤にならず**、正しい件数へ docstring を直した際に test 更新が必要な追加漏れ。 |

`test_condition_meaning_gate.py` の `_NEW_BRANCH_EXPECTATIONS` を使う追加ケースは、表へ新 macro を入れた場合に走る。`test_ccbench_spawn_sites.py` の cross-product 検査も登録後に作用するが、新規 patch の存在だけで必ず赤とは言えない。

[`test_mocc_template_proof.py:94`](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2847-mutation-run/orchestrator/tests/test_mocc_template_proof.py:94) は全 patch を読むものの、発火条件は mocc の marker 追加であり、今回の silo patch では追加登録不要。`tools/check_docs.py` と `patches/ledger.json` に、今回の `*.patch` 追加だけで赤になる対応検査は見つからなかった。`control-silo-*` を prefix で拒む既存コードも見つからず、在庫検査は path と token の対応で判断する。

## 見積りの再計算

[前回実走](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2847-mutation-run/output/insights/2026-09-23/t2847-patch-verify/README.md:44) の Elapse は s3 140 秒、s5 134 秒、t152 185 秒、s2 209 秒、合計 668 秒だった。今回の plan の範囲をそのまま足すと、3 patch 組を 4 job × 250〜420 秒、2 patch 組を 200〜320 秒、s8a を 140〜240 秒として **1,340〜2,240 秒＝0.37〜0.62 node 時間**。plan の「0.4〜0.7」は丸めとして妥当だが実測値ではない。

この値には、workload ごとの stock **追加 run**、発火しなかった条件の再走、V21 の追加 verify を明示的に積んでいない。焦点走・変異 matrix・受入 2 回の **0.4〜0.7 node 時間には前回 Elapse による内訳がなく、総計 0.8〜1.4 node 時間という上限は裏づけられない**。段 4 では checkout 数、各 job の build 数・run 数・verifier 数、検査の実行回数を表にして再計算すべきである。2 node 時間以上になるなら [依頼の条件](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2847-mutation-run/request.md:8) に従い投入前に確認する。

## 未確認点

- patch はまだ存在しないため、14 本それぞれの `git apply`、未定義時の pin との前処理一致、発火、版衝突の有無は静的計画から確定できない。
- s8a の計算ノード CLK、6 job の実際の割当先と walltime、stock の workload 別 run 数は未確定。dispatcher の既定 walltime は [`01:00:00`](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2847-mutation-run/tools/pegasus/dispatch_compute.py:68) で、各 job 見積りには足りるが、同時実行の保証ではない。
- V21 は `quit_` が取引中に立つ schedule に依存する。証人あり I と証人なし S の組を得られなければ、期待に寄せず「未発生」と記録する必要がある。

## 総括

計画は既存の patchharness、condition gate、verifier を維持できる。ただし **job 別 checkout、workload 別 stock 対照、V21 の二つ目の verdict 保存、登録 test の固定件数**を具体化してから投入すべきである。今回のレビューは read-only の静的検査であり、test・build・計算ノード実走の結果は含まない。