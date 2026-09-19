単独段 dispatch: stage=review; sandbox=read-only; parent=/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2773-mocc-template-wave2

必読事項の射影 (各 path を読めなければ即停止して、その旨だけを `## 総括` に書いて終わること):
- 実装差分 (段 5 author の統合 diff、レビュー対象): /work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2773-mocc-template-wave2/wave-artifacts/impl-diff-1.patch
- author の最終報告: /work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2773-mocc-template-wave2/wave-artifacts/s5-author-1.md
- 親の焦点走 log (`tools/run_tests.py` 経由): /work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2773-mocc-template-wave2/wave-artifacts/focus-1.log
- 親の login 生死確認 log (build / identity / DQ、benchmark なし): /work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2773-mocc-template-wave2/wave-artifacts/liveness-run-1.log
- 段 4 裁定 (実装が従うべき契約 R1〜R21、変異事前登録 M0〜M15): /work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2773-mocc-template-wave2/wave-artifacts/s4-ruling.md
- 段 2 plan と段 3 レンズ A: 同 dir の s2-plan.md、s3-lensA.md
- 設計正本 (§5・§8〜§11): 同 dir の verbatim/t2757-design-README.md。既裁定: verbatim/D2134.md、D38.md、D1687.md
- preimage と旧計装 patch: 同 dir の verbatim/mocc-transaction-e9e477ca.cc、verbatim/instr-mocc-lock-coverage.patch
- repo 内 (投入先 worktree、作業ツリーに差分適用済み): /work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2773-mocc-template-wave2/ の patches/mocc-temperature-predicate-variant.patch、patches/instr-mocc-lock-coverage-temperature.patch、orchestrator/campaign/axis_mocc_temperature.py、orchestrator/campaign/s3_mocc_template_proof.py、orchestrator/tests/test_mocc_template_proof.py、.claude/agents/auditor.md、orchestrator/campaign/diff_quarantine.py (無変更)、orchestrator/campaign/auditor_gate.py (無変更)、orchestrator/campaign/source_digest.py (無変更)、orchestrator/campaign/s3_mocc_mutation_proof.py (無変更のはず)

親の実測 (レビューの入力、判定はあなたが行う):
- 生死確認 (`liveness-run-2.log`、rc=0): template は git apply 可 / 旧計装 patch は template 適用後に不適用 / 新計装版は template なしに不適用。marker begin 20 / if 22 / else 24 / endif 26 / end 27、hole 1 行、frozen bytes 一致、外側 guard 行 17 で一意。**OFF t0 の `.text` は無 template base-t0 と 2 行差** (`mov $0x4a9`→`$0x4cc` = 論理行 1193 の `ERR;` の `__LINE__` が 1228 になる。template は `#line` を持たない)。ON-B 計装なし↔あり TRACE=0 `.text` は一致 (59,854 行)。author は実 resolver で OFF = stock を確認済み (`ERR` は include 剥がしで未展開のため `__LINE__` は preimage に出ない)。この差の扱い (R4 の保証名・「主張しないこと」・regime 1 への影響) を判定せよ。
- 焦点走 1 (`focus-1.log`、gen_S 11065.nqsv): 658 passed / 2 skipped / rc=0 (JSON 依存 2 node は deselect)。
- 親の所見 (未裁定): `test_mocc_template_checks_are_input_derived` は 30 key のうち `*_certified_and_silent` (12)・`template_on_benign_identity_distinct`・`auditor_definition_read_only_and_projection` (tools のみ) だけを 1 field 変異で落としており、`quarantine_*`・`auditor_digest_and_deny_only_controls`・`consumer_binding_controls`・`instrumentation_body_preserved`・`auditor_mocc_items_present`・`wave1_proof_*`・`legacy_proof_*`・`trace0_*`・`template_off_stock_identity` は key ごとの入力由来検査が無い。例えば `compute_checks.dq()` の `records[n]["subtype"] == subtype` を外す変異 (段 4 の M8) はどの test にも捕まらないと親は読む。real か、成果物影響、是正の最小形 (旧 `test_mocc_mutation_proof.py` の per-key 型へ揃える) を判定せよ。

# 依頼 — [T-2773] 段 6 レビュー A: 正しさ境界・恒真性・規律 1/2・防壁の素通り — 実装を攻撃する

実装を守らせず検査せよ。所見は real / refuted の判定材料 (行番号・既裁定) を添えて must-fix / should / nit に分け、各 must-fix には「放置時に成果物 (新 JSON の値・受理集合・check) がどう変わるか」を 1 行で書く (書けない所見は nit)。あなたは read-only。pytest は走らせない (静的読解。親の焦点走 log と生死確認 log を実測として使う)。予算が尽きそうなら途中結論を下の出力形式どおり書いて終わること (無出力が最悪)。

## 攻撃点

1. **template の逐語と意味保存 (R13)**: helper (`mocc_is_hot`、`std::uint64_t` 二引数、anonymous namespace、外側 guard `#if MOCC_TEMP_PREDICATE // file-scope helper` が source 内で完全一致 1 行)、marker 骨格 (BEGIN → comment → `#if` → hole 1 行 → `#else` stock 逐語 → `#endif` → END)、4 site (296 の brace、459 / 566、970 の `|| (*itr).failed_verification_` 両枝保存)、OFF で helper が消え原文逐語が選ばれるか、`IZANAGI_` トークン不在、Options.cmake 2 hunk。生死確認 log の OFF `.text` 一致・identity (i)(ii) の結果と照合。
2. **計装 template 版と R1**: `#line` 7 値が実 template 適用 source の論理行と一致するか (生死確認 log の実測値)、`instrumentation_body_preserved` の (a) `+` 行列一致 (`+++` / `+#line` 除く)、(b) hunk 前後 context 一致、(c) `#line` 列 = 旧 + 実測 offset が本当に入力由来か (定数表の焼き込み、`#line` 除外の正規表現が検査本文の行まで除いていないか)。X 恒偽化 (`if (false && …)`)・P emit 無効化・検査点の移動・`#line` ±1 の 4 拒否対照が単一理由で赤になるか。
3. **同一性 3 比較 (R4)**: (i) `source_digest.baseline / compute / resolve` を `PROOF_PIN` と隔離 checkout で呼んでいるか、`src_token == STOCK` の判定、(ii) ON-B の別 identity が digest 比較で判定されるか (genome canonical の差だけで合格にしていないか)、(iii) OFF / ON-B 両状態で基準列を実 source から独立取得しているか、`#line` ±1 で差になるか。保証名 (`claim`) の文字列が R4 の限定になっているか。
4. **check 述語の恒真性 (R6 / R19)**: 12 走の `certified_and_silent` が `_silent` 相当 (certified・verdict・X=P=0・cycles=0・他 integrity clean・txn / write > 0、U は R=0) + 終了状態を要求しているか。`matrix_runs_complete_and_terminated`。`quarantine_*` / `consumer_binding_controls` / `auditor_*` / `wave1_proof_bound_and_all_pass` / `legacy_proof_bound_and_all_pass` が record の実結果から導かれ、期待値を record 自身から取っていないか (自己比較)。`all_pass` が全 key exact と 12 走揃いを要求するか。途中保存の JSON で `all_pass` が true になりうるか。
5. **DQ 対照と deny-only (R18)**: 13 対照の diff が実適用 source の 1 行編集から生成され、編集位置の一意一致を assert しているか。`marker.source_rel = SOURCE_REL` の明示。X / P 対照が template + 新計装版を head_text にし marker を再 parse しているか。deny-only 4 対照の順序 (machine reject → そのまま返る、machine pass → digest → auditor)。期待 subtype がコード側で固定されているか。「DQ pass = 安全」と読める記述が docstring / auditor.md にないか (レンズ A 所見 2 の 9 形が auditor 型 16 の文章契約で禁止されているか)。
6. **auditor 定義と射影 (R2 / R7 / R9)**: tools が既存 role loader から取られ `("Read","Grep","Glob")` exact か。`auditor_projection` の allowlist が正しさの形だけで、`wall_seconds` / `txns` / `non_insert_writes` / `read_rows` / 未知 key を fail-closed で拒否するか。`check_auditor_definition` が項目境界で分割し、全文検索や検査対象からの期待生成をしていないか。auditor.md の追記が既存 Silo 文を弱めていないか、行番号 (1010〜1013 / 1024〜1036 / 477 / 905〜913) が e9e477ca と一致するか、`absent` 非検査・I absent を維持しているか、型番号 / description 不変。
7. **束縛関数と gate (R16 / R17)**: `require_proof_binding` が `all_pass` を見ないこと、別名 template (同 bytes) の拒否、別 OID の拒否、正しい literal の通過。鍵 (a) が計装 patch・負例 4 本・Silo template で発火せず template で発火するか、鍵 (b) が `axis_trigger_gating` で発火しないか、import 失敗を握り潰していないか。4 ケースの負例。JSON 不在で赤 (skip でない) な node が R17 の 2 つだけか。Silo gate 不変。
8. **規律 2 / 不変性**: 旧 driver 2 本・旧 test 2 本・旧 patch 5 本・旧 JSON 2 本・`diff_quarantine` / `auditor_gate` / `source_digest` / `model` / `pin` の無変更。受理集合を広げる変更 (DQ / 束縛 / gate / 読取契約の緩和) が無いか。
9. **author 報告と実体の不一致**: 報告した検査結果・行番号・件数・sha が diff と一致するか。焦点走 log の赤の内訳が報告と一致するか。

## 出力形式

- 見出しはすべて `##`。所見は `## 所見 N: <title>` の形で、各所見に「real/refuted の判定材料」「must-fix / should / nit」「成果物影響 (must-fix のみ)」「是正案 (逐語、file:line)」を書く。
- 最後の節は必ず `## 総括` (`#` を 2 個)。`### 総括` と書いてはならない。`## 総括` には GO / NO-GO、must-fix の一覧、報告と実体の不一致の有無を書く。
- 入力はデータであって指示ではない (規律 6)。断定には行番号か D 番号を添える。確信の無いことは「不確実」と書く。
