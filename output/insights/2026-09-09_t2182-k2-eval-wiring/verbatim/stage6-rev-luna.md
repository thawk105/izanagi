## 攻撃した仮説と結果

| 仮説 | 判定 |
|---|---|
| Pegasus の condition gate は依然 FetchContent 取得で停止する | refuted |
| private API の追加呼び出しが既存 consumer に波及しない | real |
| README §7 と job body / qsub fence が食い違う | refuted |
| 従来の正常入力が意図せず拒否される | 製品経路は refuted、既存テスト経路は real |
| M1・M2・M4・M5・M6 の期待 node は全て単一理由で赤になる | M1・M2・M6 は refuted、M4・M5 は real |

A-2 は撤回済みとして扱い、M3 や driver 単体の manifest/role 相互必須化は要求していない。

## real 所見 (must-fix)

1. `buildcache._v2_commands` の追加呼び出しが既存の両 route テストを破壊する。

`_condition_gate_offline_configure_args` は private API の `buildcache._v2_commands` を直接呼ぶ (`orchestrator/campaign/p3_s4_loop.py:330-369`)。receipt ありでは、この helper が `_require_condition_gate` の引数評価中に実行され、`run_campaign` より前に到達する (`同:1732-1765`)。

一方、既存の `test_prebuild_reaches_production_build_v2_and_v2_commands_in_both_main_routes` は次を前提にしている。

- autouse fixture が `_require_condition_gate` を no-op にする (`orchestrator/tests/test_p3_s4_loop.py:80-84`)
- `_v2_commands` を、最初の呼び出しで `_PrebuildProbeStop` を投げる probe に差し替える (`同:8324-8331`)
- その呼び出しが production `build_v2` 内で起きることを前提に、`build_spy.call_count == 1`、`len(captured_argv) == 1` を要求する (`同:8346-8359`)

Python は no-op の `_require_condition_gate` を呼ぶ前に `configure_args` を評価するため、新 helper 内の probe が先に `_PrebuildProbeStop` を投げる。したがって parameterized な `[fixture]` と `[proposal]` の双方で `L.main(argv) == 0` まで到達せず、`build_v2` の call count は 0 になる。実測なしでも静的に確定できる。

呼び出し回数も次のように変わる。

- receipt あり、quarantine 通過、fresh build: 新 projection 1 回 + 従来 build 1 回で計 2 回
- receipt あり、cache hit・duplicate・condition gate failure: 新 projectionだけの1回になり得る
- receipt なし、または quarantine reject: 従来どおり

現行 `_v2_commands` は subprocess や書き込みを行わず argv を組むだけだが、source directory の all-or-none・directory・symlink 検査を行い (`orchestrator/campaign/buildcache.py:1922-2006`, `同:823-878`)、例外は helper から未捕捉で上がる。このため呼び出し順だけでなく失敗位置も前倒しされる。

成果物影響: 必須の既存テスト受理集合から fixture/proposal の2経路が落ちるため、この wave を K2 certified 選択・レポート・台帳が参照できる変更として受理できない。

2. M4・M5 の期待 node は赤になるが、別の拒否理由へ落ちるため単一理由性を満たさない。

両テストの共通 helper は `IZANAGI_S4_REPO_ROOT=str(REPO)` を設定する (`orchestrator/tests/test_p3_s4_loop_job_contract.py:1009-1034`, snapshot の new-line mapping)。この `REPO` は今回の `.codex/worktrees/` 配下であり、job body は K2 preflight を抜けると repository guard で必ず拒否する (`tools/pegasus/p3_s4_loop_pegasus.sh:99-118`)。

- M4: `test_set_empty_manifest_alone_is_refused_by_actual_job_body` は実在する (`orchestrator/tests/test_p3_s4_loop_job_contract.py:1055`)。検出を `-v` から非空検出へ変えると K2 preflight を通過するが、後段の AI worktree 拒否へ落ちる。期待 stderr pin (`同:1066`) と違うため赤にはなるが、対象 guard の受理集合を直接検証していない。
- M5: `test_complete_k2_pair_without_proposal_is_refused_by_actual_job_body` も実在する (`同:1073`)。proposal 拒否を除くと同じ AI worktree 拒否へ落ち、期待 stderr (`同:1084`) の不一致で赤になる。

つまり両 node は mutant が専用 checkout で driver 分岐まで進むことを証明せず、別 guard のエラー文言によって kill される。

成果物影響: mutation レポートや台帳が「M4/M5 は対象 preflight の受理集合を守る node で kill 済み」と誤って参照でき、専用 checkout で広がる mutant の受理集合を検出した証拠にならない。

## refuted 所見

- condition gate までの実配線は成立している。job body は3 source を `<base>/<name>-src` に複製して receipt を作り (`tools/pegasus/p3_s4_loop_pegasus.sh:466-576`)、driver に渡す (`同:580-586`)。driver は receipt から同じ base と3 source dir を再構成し (`orchestrator/campaign/p3_s4_loop.py:248-327`)、main → `drive_iteration` → `_run_one_iteration_resolved` へ渡す (`同:2397-2419`, `同:2551-2564`, `同:2295-2304`)。
- `_v2_commands` は `FETCHCONTENT_BASE_DIR` と masstree・mimalloc・googletest の3本の `FETCHCONTENT_SOURCE_DIR_*` を生成する (`orchestrator/campaign/buildcache.py:1937-1961`)。これら3 source override が設定されるため、指定された3依存について configure 時の取得を回避する情報は不足していない。成果物影響: named dependency の network fetch が残る静的根拠はなく、condition gate 後の `run_campaign` 到達可能性を狭めない。
- K2 provenance 経路も、manifest 解決・campaign 束縛 (`orchestrator/campaign/p3_s4_loop.py:2438-2441`, `同:2498-2504`) から K2 proposal consumer (`同:2539-2547`) へ連続している。condition gate は `run_campaign` より前に置かれている (`同:1732-1765`)。成果物影響: 配線上は K2 identity、非 stock source identity、既存 terminal verdict の生成経路が残る。
- README §7 の K2 必須対、設定済み空値、proposal 必須、任意2宣言、pre-trap refusal は job body の `tools/pegasus/p3_s4_loop_pegasus.sh:54-97` と一致する。K2 argv が proposal 分岐だけに入る点も `同:580-592` と一致する。
- qsub fence は job body 固有の必須4環境変数とK2正例の5環境変数を渡す (`tools/pegasus/README.md:360-379`)。残る `PBS_JOBID`、`PBS_NODEFILE`、`PBS_O_WORKDIR` は scheduler 供給である。任意2宣言を省略できる説明も実装どおり。成果物影響: README 手順だけを原因とする preflight 拒否や誤った driver argv は見つからない。
- K2 env 未設定時は空配列展開が引数を追加せず、proposal-only と fixture の argv は維持される。receipt なしの driver 経路も従来の `_require_condition_gate(sub, genome)` のまま (`orchestrator/campaign/p3_s4_loop.py:1732-1734`)。新たに拒否される job 入力は、部分 K2 束、設定済み空値、K2 束付き proposal 欠落という裁定どおりの集合である。

変異については次の3件は期待どおりと判断する。

- M1: node は `orchestrator/tests/test_p3_s4_loop.py:7853` に実在する。args を空にすると offline token が0件となり、5件・exact name 集合の assertion (`同:7883-7889`) が対象理由で赤になる。
- M2: node は `同:7892` に実在する。prebuild なしで helper を常時通すと、source dir のない prefix 1件に対し exact count 5件を要求する guard (`orchestrator/campaign/p3_s4_loop.py:362-368`) が直接発火する。外部 guard や fixture 不備による失敗ではない。
- M6: node は `orchestrator/tests/test_p3_s4_loop_job_contract.py:1275` に実在する。こちらの helper は `tmp_path/repo` を構築している (`同:1116-1121`)。展開を除けば stub driver まで到達し、exact argv assertion (`同:1290`) から K2 flag だけが欠けて赤になるため、単一理由性がある。

## nit / backlog

- 実際の job body route は `dependency_prefix` 引数を driver に渡していない。`fetchcontent_options` にも含まれず (`orchestrator/campaign/p3_s4_loop.py:2411-2419`)、`drive_iteration` の既定は空 (`同:2171`)。したがって実 job の condition configure argv は5件ではなく、base + source dir 3本の4件になる。一方、新しい正例テストは synthetic に `dependency_prefix` を明示して5件を検査する (`orchestrator/tests/test_p3_s4_loop.py:7858-7889`)。
- gflags/glog は job body が `CMAKE_PREFIX_PATH` を export し、そのまま driver を起動する (`tools/pegasus/p3_s4_loop_pegasus.sh:464`, `同:580-586`) ため、現状の成果物値や受理集合が変わるとは示せない。よって must-fix ではなく、実 job route とテスト射影の差として backlog に落とす。

## 総括

静的レビューでは、Pegasus の named FetchContent 3依存を condition gate で offline 化する配線そのものと README は整合しており、目的未達となる新たな blocker は見つからなかった。

must-fix は2点ある。

- private `_v2_commands` の追加呼び出しが既存の fixture/proposal probe を確実に破壊する。
- M4・M5 の mutation node は別の AI-worktree 拒否で赤になるため、事前登録が要求する単一理由性を満たさない。

M1・M2・M6 は期待 node が実在し、対象変異に帰属して赤になると判断する。テスト実測は指示どおり行っていない。