## 所見

severity: must-fix
根拠: `/home/SFC/tanab/.claude/jobs/2abe6e84/tmp/t2067a/artifacts/t2067a/plan.md:37,55,78` は新規テストで production-emitter helper を使う一方、`orchestrator/tests/test_s8b_ratified_freeze.py:613-637` は `_ROOT` の freeze、calibration、known-axes、selector source を読む。`orchestrator/tests/conftest.py:258-260` は親 working tree に触る node を exact 登録対象とし、`orchestrator/tests/test_real_repo_serialization.py:50-52,1501-1535` は独立 golden との一致を要求する。
攻撃シナリオ: 新規 R/J/V node の実行中に land が `output/s8b-freeze/holdout_freeze.json` または selector source を更新すると、real-repo marker のない node が複数時点の bytes を混ぜた g1 を構築する。少なくとも実 g1 を使う負例と J/V 正例が該当し、実装時に helper を使う引数テストも同じである。
成果物への影響: 負例が誤って緑または赤になり、選択 gate を欠く実装が受入を通る可能性がある。また登録するなら `conftest.py` の inventory/parent-only 集合と `test_real_repo_serialization.py` の二つの golden が R/J/V 共通編集面になり、「4単位の編集 path は素集合」という分割も崩れる。

severity: must-fix
根拠: `/home/SFC/tanab/.claude/jobs/2abe6e84/tmp/t2067a/artifacts/t2067a/plan.md:68-85` はテスト名と期待挙動だけで、変異 ID、置換位置、`expected_nodes` の exact 集合を示していない。`orchestrator/tests/test_s8b_oracle_manifest.py:1159-1180,1369-1404` の二 node は report/judge の任意の byte 変更で必ず失敗する。
攻撃シナリオ: report の新しい選択 call を `pass` に戻す変異では、意図した report 負例に加えて二つの pin node が失敗する。意図した node だけを登録すれば exact 不一致となり、pin node だけなら本体テストが効かなくても変異が kill されたように見える。
成果物への影響: 変異証拠が選択強制の実効性を帰属できず、call 削除、root 誤渡し、object 取り違えを残した実装が受理され得る。R/J の各変異は「意図した exact node 集合 + 上記二 node」、V は意図した集合だけ、と事前に固定する必要がある。

severity: should-fix
根拠: `orchestrator/campaign/s8b_oracle_manifest.py:96-102,1019-1028` は `VerifiedManifest` を封印するが、freeze の権威性は caller 責務と明記する。`orchestrator/campaign/s8b_oracle_report.py:2312-2353` はその token から official observations を作り、`reverified_freeze` は任意である。`orchestrator/campaign/s8b_oracle_artifacts.py:61-74` の official marker 自体は provenance 検証済みを意味せず、`orchestrator/campaign/s8b_oracle_judge.py:452-469` は marker から official verdict を返す。
攻撃シナリオ: 12:00 を選択した g1に11:59の eligible resultがある入力でも、caller が `verify_manifest` へその freeze document/hash を直接渡し、続けて `build_observations`、`judge_oracle`、さらに `verify_oracle_verdict` と `judge_combined` を呼べば、三つの `main()` に追加する gateを一度も通らない。
成果物への影響: 三つの CLI は拒否しても、同じ schema の official observations、oracle verdict、combined report を library 経路で構成できる。現在の repo 内 production caller は CLI 内に閉じているが、「全層の非対称を閉じた」という主張は成立しないため、scope 外の裁定候補として残す必要がある。

## 追補の判定

1. 正 — `test_official_perf_closure.py:27-42` の `_TRACKED_CALLS` に新しい選択 call はなく、対象 predicate も `main()` ではない。
2. 正 — 同 `:44-92` は path 集合であり、対象 file の増減や改名はない。
3. 正 — 同 `:266-412` は指定関数内の `if` 式を比較し、三つの `main()` への単純 call 追加では変わらない。
4. 正 — `test_s8b_oracle_manifest_contract.py:18-36,39-104` は loader/`verify_manifest` の caller file 集合を数える。既存 caller 内への選択 call 追加では集合は不変。
5. 正 — `test_ccbench_spawn_sites.py:2900-2916` の 1788 literal は driver の sink 行であり、本案は driver を編集しない。
6. 正 — `test_s8b_oracle_artifacts.py:252-282` はトップレベル schema alias の AST だけを検査する。
7. 正 — `test_env_contract.py:83-100,1250-1263` の対象にあるのは driver であり、本案の三 file はこの検査対象外。

ただし、この 7 件が正でも pin 閉包全体は正にならない。real-repo node inventory とその独立 golden が取りこぼされている。所要時間台帳の `nodeid_count` は保存済み entry 数であり、新規未知 node は `conftest.py:1578-1626` の既定 costへ倒れるため更新必須の correctness pinではない。receipt memo、hold、schema、事前登録、AI provenance known-violation には対象 node名または三 source hashの追加 consumerを認めなかった。

## 取り残した層

- public library 経路: `verify_manifest` → `build_observations`、`judge_oracle`、`verify_oracle_verdict` → `judge_combined`。三つの CLI gateを通らず同種の official artifactへ到達できる。現在の repo 内 production callerは閉じているため、自動実装せず裁定候補とする。
- dormant load-only 経路: `p3_autonomous_workload_trial.py:4957-4964` は選択未強制の ratified freeze を C06 budgetへ渡す。ただし `:2074-2079` の schedule authority が無条件に送出するため、今日は ledger/reportへ到達不能である。残件 (b) の裁定候補に限り、本 wave の実装対象にはしない。
- 強制済み経路: manifest `s8b_oracle_manifest.py:1205-1206`、driver gate `s8b_oracle_driver.py:644-664`、driver run `:1335-1351`、s8c judge `s8c_result_judge.py:2075-2081`。
- `s8b_oracle_driver.py:496` の load は private `_gate_check_core` 内だけにあり、public v2 gate は `:644-664` で `launch_validate` を通る。独立した production入口ではない。
- production の `reverify_published_freeze` caller は report、judge、verdict の三つだけ。`tools/` と `scripts/` に callerはなく、残りは tmp fixtureを作るテスト専用 callerである。

## 親前提の判定

(P1) refuted — CLI限定の最小 scopeとしては一貫するが、`verify_manifest` が選択未強制の freezeから封印 tokenを発行し、public library coreがそれを消費できるため、全層の非対称は残る。

(P2) real — `_GENERATOR_SOURCES` は `s8b_oracle_manifest.py:65-73` の5 fileだけで verdictを含まない。現 verdict hashの repo内 literalもなく、他の receipt、proof-chain、事前登録、known-violationによる byte pinも認めなかった。

(P3) real — 三 CLI内では load直後、historical reverify前が最初の共通 fail-closed 点である。`reverify_published_freeze` 内へ移すと `s8b_ratified_freeze.py:3677-3687` の historical 意味論と全 callerを変え、後置には受理上の利点がない。

「発行済み公式 manifest 0件」も real — `s8b_oracle_spec.py:19,23` は canonical pathと `APPROVED_SPEC_SHA256=None` を示し、現物でも `output/s8b-oracle-spec/` と `output/s8b-oracle-manifest-candidates/` は存在しない。`output/s8b-freeze/holdout_freeze.json:13-14` の generator は `s8b_holdout_freeze.py` だけである。

## 総括

- 凍結 production pin 0件と追補7件の非発火判定は維持できる。
- ただし新規 node の real-repo 登録閉包と独立 goldenが計画から漏れており、分割も修正が要る。
- R/J 変異は二つの pin nodeを含む exact 期待集合の事前登録が必要である。
- P1 は全層主張として refuted、P2/P3 は real。pytest は指示どおり未実行。