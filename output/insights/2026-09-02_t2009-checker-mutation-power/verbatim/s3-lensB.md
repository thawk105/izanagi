## 所見 1 — M1 は verdict 変異ではない

所見: M1 の注入は実在し一意だが、`KILLED` は診断分類の pin にすぎない。  
根拠 (orchestrator/verifier/dsg.py:245, orchestrator/verifier/core.py:142, orchestrator/verifier/core.py:149): `_classify` は SCC 数を決めた後の `Anomaly.phenomenon` 生成だけに使われ、受理判定は `total == 0` で決まる。`test_classify_branches` も `_classify` を直接検査するだけである (orchestrator/tests/test_verifier.py:1374)。  
影響: 親 brief の (P1-D) の疑いは正しい。M1 の生存は設計どおり、機械的 KILLED も DW-M03 の semantic kill ではない。  
推奨 (scope 内): M1 は mutation matrix の semantic 分母から外し、`diagnostic sensitivity pin` として別枠記録する。

## 所見 2 — M2 は有効な semantic mutation

所見: M2 の 4 anchor は各一意で、版列、DSG 構築側 rw、診断再構成側 ww/rw を同じ tid-only 順序へ変える。  
根拠 (orchestrator/verifier/dsg.py:72,101,211,226): r6 では `(1,100) < (2,1)` の ww 順、r7 では `(1,100)` の直後版 `(2,1)` が失われ、いずれも clean な G2 cycle が消える (orchestrator/tests/test_verifier.py:1797,1808)。  
影響: `test_epoch_version_order_g2` と `test_epoch_rw_successor_order_g2` は受理集合が non-serializable から certified serializable 側へ広がるため、DW-M03 の semantic KILLED になる。  
推奨 (scope 内): M2 と expected node 2 件はそのまま採用できる。

## 所見 3 — M3 は SURVIVED せず、r5 が機械的に殺す

所見: plan の「全 tracked 赤 fixture の shortest witness は長さ 2 または 3」は誤りで、`r5_nonlatest_transitive` に長さ 4 の SCC witness がある。  
根拠 (orchestrator/tests/fixtures/r5_nonlatest_transitive/trace_0.log:4): ww の `T2→T3→T4`、T4 の genesis-read(c) による `T4→T50`、T50 の旧版-read(a@T1) による `T50→T2` が `T2→T3→T4→T50→T2` を作る。M3 はこの SCC を除外し、`test_nonlatest_read_caught_via_ww_transitivity` の `assert not res.serializable` を落とす (orchestrator/tests/test_verifier.py:116)。  
影響: 現 spec の `SURVIVED / expected_nodes=[]` では harness 結果は `MISMATCH` になる。一方、txid `{1,2,3,4,50}` は 46 件の欠番を持つため、変異後も verdict は `indeterminate` で fail-closed のまま (orchestrator/verifier/parse.py:418, orchestrator/verifier/model.py:220)。これは graph sensitivity であり semantic kill ではない。  
推奨 (scope 内→裁定へ): 本走前に M3 を `KILLED`、expected node を同 node 1 件へ再登録し、semantic 証拠から外す。semantic kill に必要なのは、密な T0〜T3 が rw だけで四角形を作る clean fixture であり、その追加は本 wave の「塞がない」境界に従って裁定へ返す。

## 所見 4 — M4 は単一理由性を満たさない

所見: `framing_violations = 0` は fail-closed gate だけでなく構造化 counter も消すため、診断赤と semantic 赤を同時に生む。  
根拠 (orchestrator/verifier/core.py:65, orchestrator/tests/test_verifier.py:343): 予定した 6 node はすべて verdict assertion より前に `framing_violations == 1/2` で落ちる。5 fixture では後続の verdict/certified も変わるが、`test_cycle_verdict_takes_priority_over_framing_violation` は cycle により拒否されたままで counter だけが変わる (orchestrator/tests/test_verifier.py:513)。  
影響: 機械的 KILLED は確実だが、失敗 node 集合だけでは「fail-closed が効いたための赤」と帰属できず、DW-M01 の単一理由性に反する。  
推奨 (scope 内): `Integrity.clean()` の `self.framing_violations == 0` 条件だけを無効化する変異へ差し替える (orchestrator/verifier/model.py:170)。expected node は予定 6 件から cycle 併存 node を除いた 5 件になる。

## 所見 5 — M5 は照準ミスで、結論を一切支えない

所見: plan の hash は 63 桁であり、64 桁を返す `sha256().hexdigest()` と一致し得ない。  
根拠 (plan-out.md:231, orchestrator/tests/test_verifier.py:1413): plan は `...ee511a2`、実 fixture は `...ee511a2a`。したがって hard-code branch は全入力で到達不能である。  
影響: SURVIVED しても fixture closure や D387 overfitting を示さず、単に通常 verifier へ fall through した結果になる。さらに hash を直しても「既知 g6 は正答、未知入力は通常 verifier」という実装は受理集合を弱めないため、なお低情報量ではなく実質的に等価である。  
推奨 (scope 内): M5 は差し替える。既知 hash には正答する一方、異なる hash の clean 200-commit G2 trace を意図的に serializable にする等、具体的な未知入力で誤る mutant と、その killer input を事前登録する。

## 所見 6 — P1 は有効な正例対照

所見: P1 は唯一の構築側 rw 追加を消し、clean な赤 fixture の cycle と downstream certification を実際に反転させる。  
根拠 (orchestrator/verifier/dsg.py:98,105): r1/r2/r3/r4/r6/r7/r8 の cycle は rw を必要とする。少なくとも `test_write_skew_g2`、`test_broken_silo_norw_fixture_contract`、r6/r7、t1286 の r1/r2 parameter node は semantic に落ちる (orchestrator/tests/test_verifier.py:60,1473,1797; orchestrator/tests/test_t1286_commit_receipt.py:214)。  
影響: plan-out.md:287 の 18-node 集合は静的には妥当であり、測定系に検出力がある。ただし g4、r5、framing-cycle、g6 stats、structured-report golden、real-Silo edge/stats の 7 件は graph/golden-only で、semantic 証拠は残る 11 件が担う。  
推奨 (scope 内): P1 は維持し、失敗 node を `semantic 11 / graph・golden 7` に分類して記録する。

## 所見 7 — E1 は正しい等価対照

所見: E1 の anchor は一意で、選択された入力領域では完全な等価変異である。  
根拠 (orchestrator/verifier/dsg.py:77): `u` と `v` は parser が作る整数 txid なので、`u != v` と `not (u == v)` は同値であり adjacency、verdict、生成物を変えない。  
影響: SURVIVED は穴を意味せず、harness が注入 diff を持つ変異を生存として報告できることだけを確認する。  
推奨 (scope 内): E1 は対照として維持し、「どの入力なら落ちるか」は「正当な入力には存在しない」と明記する。

## 所見 8 — bytes node の分離は保たれている

所見: D799 決定 (4) の raw bytes node が semantic node を覆い隠す変異は、今回の 7 件にはない。  
根拠 (orchestrator/tests/test_verifier.py:1749,1788): `test_new_real_fixture_bytes_are_exact` と `test_real_silo_fixture_bytes_are_exact` は fixture bytes を直接読み、`core.py` / `dsg.py` を呼ばない。7 変異はいずれも fixture file を変更しない。  
影響: bytes SHA による偽 KILLED はない。一方、P1 では structured report、edge count、stats の verifier-derived golden node が補助赤を出す。  
推奨 (scope 内): ledger は raw-bytes、semantic、graph-only、golden/diagnostic の層を分離する。

## 所見 9 — harness の KILLED は意味論を表さない

所見: harness は rc と失敗 node の完全一致だけで `KILLED` を決め、失敗 assertion の層や受理集合の変化を記録しない。  
根拠 (tools/mutation_harness.py:1241,1997): `_failed_nodes` は nodeid のみを抽出し、`_observed_status` は `failed_keys == expected_keys` だけを見る。  
影響: M1、M3、M4、P1 の補助赤を、後処理なしで DW-M03 semantic kill と読むことはできない。  
推奨 (scope 内): matrix に `machine_status`、`failed_nodes`、`semantic_transition`、`first_failure_layer` を別項目で記す。harness の `KILLED` を insight の「穴を塞いだ」に直接変換しない。

## 所見 10 — 親 brief の provisional 前提

所見: (P1-A) は狭い正選択へ修正すべき、(P1-B) の M5 生存は現 mutant では無情報、(P1-C) の原則は正しいが M4 が未充足、(P1-D) は `_classify` が verdict に不関与という答えになる。  
根拠 (brief.md:68, orchestrator/verifier/core.py:149, orchestrator/verifier/model.py:209): behavioral 分母として必要なのは `test_verifier.py` 全体と t1286 の対象 parameterized function であり、保存 JSON consumer は source 変異を実行しない。  
影響: brief の「最大 5 箇所の穴」は過大で、M1 は診断、M5 は現状無効、M3 は clean-input 不在による semantic gap である。  
推奨 (scope 内): brief/insight では M1・M5を hole 数から外し、M3を「長さ4入力なし」ではなく「長さ4入力はあるが unclean で fail-closed 遷移を観測できない」と訂正する。

## 所見 11 — F-new1〜F-new3 とアンカー表

所見: F-new1 の pin 掲載自体は正しいが「全変異が数百件の drift 赤」は誤り、F-new2 の「長さ4 fixture なし」も誤り、F-new3 の複数形化だけが妥当である。  
根拠 (orchestrator/campaign/contract_loader_binding.py:348): drift は `capture_contract_loader_binding` / `verify_live_contract_loader_binding` を通ったときだけ発火し、推奨 selector は通らない。長さ4反例は r5 である。  
影響: brief のアンカー表では M1 の semantic 意味、M4 の照準、M5 の hash と mutant 意味論を改訂しない限り、7 件の matrix から一貫した結論を出せない。  
推奨 (scope 内): M3 の preregistration、M4/M5 の replacement、machine/semantic 二層分類を直してから親が実走する。

## 総括

(a) 帰属が成立しない変異: M1 は診断のみ、M3 は r5 に機械的に殺されるが fail-closed は不変、M4 は診断 counter と gate が共変、M5 は branch 到達不能かつ fallback が正常 verifier である。

(b) 差し替えるべき変異: M4 は `Integrity.clean()` の実効 gate へ再照準し、M5 は未知入力で実際に誤答する hash-overfit mutant へ差し替える。M3 は差し替えより先に expected status/node の訂正が必要である。

(c) 結論の制約: `KILLED/SURVIVED` は機械結果としてのみ記し、受理遷移と killer input を併記する。現状、semantic survivor として有効な負例はなく、「既存テストが落ちなかった＝穴」とは書けない。pytest は実走しておらず、緑は報告しない。