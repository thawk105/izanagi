単独段 dispatch: stage=plan; sandbox=read-only; parent=/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-mocc-xp-pin-candidate

必読事項の射影 (各 path を読めなければ即停止して、その旨だけを `## 総括` に書いて終わること):
- 親 brief (研究前進、段 1 実測、provisional 裁定 (P1)〜(P6)、不変条件、条件表): /work/1/SFC/tanab/dev-wave-jobs/dev-wave-mocc-xp-pin-candidate/s1-brief.md
- 依頼文の逐語: /work/1/SFC/tanab/dev-wave-jobs/dev-wave-mocc-xp-pin-candidate/verbatim-request.md
- 既裁定の逐語 (同 dir): /work/1/SFC/tanab/dev-wave-jobs/dev-wave-mocc-xp-pin-candidate/verbatim/D16.md, D297.md, D579.md, D1603.md, D1686.md, D1687.md, D2114.md, D2150.md (項 1 のみ), D2153.md, carry-T2294-T2295-entry1240.md
- 段 1 の親の実測 (逐語 log、repo 外): /work/1/SFC/tanab/dev-wave-jobs/dev-wave-mocc-xp-pin-candidate/probe/p1-patch-merge.log, p2-d297-asis.log, p3-minimal-variant.log, p4-keep-line17.log, p5-proof-surface.log (probe script は同 dir の .sh / .py)
- e9e477c を含む tracked file の一覧 (43 行、docs/worklog・decisions・failures・archive・spool と output/insights を除外した `git grep -l e9e477c` の結果): /work/1/SFC/tanab/dev-wave-jobs/dev-wave-mocc-xp-pin-candidate/verbatim/e9e477c-tracked-files.txt
- 先例 insight (repo 内、worktree の path):
  /work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-mocc-xp-pin-candidate/output/insights/2026-09-07/t2294-mocc-lock-instrumentation/README.md (X/P 計装の設計・実測)、
  /work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-mocc-xp-pin-candidate/output/insights/2026-09-17/t2756-pin-evidence/README.md (D1603 材料 3 点の型、§2〜§4)、
  /work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-mocc-xp-pin-candidate/output/insights/2026-09-20/t2304-pin-advance/README.md (前回 pin 前進の実装・波及、§0〜§3)、
  /work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-mocc-xp-pin-candidate/output/insights/2026-09-19/mocc-witlight-arm-run/README.md (§2・§7 = hook commit の作り方と保全)、
  /work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-mocc-xp-pin-candidate/output/insights/2026-09-19/t2773-mocc-template-wave2/README.md (§1 = 計装 template 版と登録簿閉包の先例)
- repo 内コード (read-only、worktree の path。行番号は親が base d99c556df で読んだ現物):
  `external/ccbench/cc/mocc/transaction.cc` (submodule、HEAD = e9e477ca)、`patches/instr-mocc-lock-coverage.patch` (+65 行、`#line` 7)、`patches/broken-mocc-{lockskip-validation,permutation-erase,early-unlock,hot-update-unlock}.patch`、
  `patches/mocc-temperature-predicate-variant.patch`、`patches/instr-mocc-lock-coverage-temperature.patch`、`patches/README.md`、
  `orchestrator/campaign/s3_mocc_lock_coverage.py` (735 行: PIN :42、INSTRUMENTATION_PATCH :63、CHECK_KEYS :71、`_require_condition_gate` :274 (driver_id 固定 :283)、`_build_variant` :314、`_apply_owned_patch` :430、`_trace0_record` :444、`compute_checks` :493、`_parser` :594、`main` :609 (checkout(PIN) と計装 patch 適用 :644-707))、
  `orchestrator/campaign/patchharness.py` (`checkout` :346、`assert_pinned_clean` :174、`apply_patch` :204)、
  `orchestrator/verifier/model.py` (emitter pattern :45-56、`certification_gate_satisfied` :77、`capture_compiled_protocol_source_snapshot` :192、`assess_compiled_protocol_source_snapshot` :258。sha を campaign.lock・receipt 群が pin しているので変更しない)、
  `tools/check_trace0_preprocess_identity.py` (`_mocc_trace_include_addition_index` :421、`_compare_include_activity` :476、`_compare_file` :515。変更しない)、
  `orchestrator/tests/test_mocc_proof_surface.py` (1010 行: `_materialize` :65、`_source_root` :98、`_assessment` :112、`_preprocess_trace_zero` :123、`_logical_nonempty_rows` :162、`_assert_instr_x_p_structure` :256、`_assert_instr_source_contract` :370、X/P 面 test :410、TRACE=0 行列 test :435、負例 test :454-593、fixture test :595-645、JSON consumer :957)、
  `orchestrator/campaign/materializer_admission.py` (:78 / :93 に `s3_mocc_lock_coverage._build_variant` / `_install_dependency`)、`orchestrator/campaign/condition_meaning_gate.py` (DefineSpec :204-219、witness :276-287)、
  `orchestrator/tests/test_ccbench_spawn_sites.py` (:27、:63、:217、:4169)、`orchestrator/tests/test_p3_build_authority_cli.py` (:164、:183、:186)、
  `orchestrator/campaign/s3_mocc_mutation_proof.py` (:22 import、:49)、`orchestrator/campaign/s3_mocc_template_proof.py` (:20 import)、`orchestrator/campaign/axis_mocc_temperature.py` (PIN / PROOF_PIN)、
  `tools/pegasus/mocc_trace_v1_policy.json`、`tools/pegasus/mocc_trace_pilot.sh` (D2153 の receipt v2 が X/P patch の path/hash と適用後 source hash を束縛)、
  `orchestrator/campaign/s8b_approved.py` (`CCBENCH_FULL_SHA` :67)、`orchestrator/campaign/pin.py` (`CURRENT_PIN` :31)、`docs/ai-provenance.md`、`docs/phase3.md` (見送り台帳の [T-167] 行)。

## 前置き — この依頼の性質

これは研究用 repo (並行性制御の自動合成) の**検証計装を pin 候補へ載せる設計レビュー**であり、セキュリティや攻撃の話ではない。
MOCC の lock 被覆 (X) / permutation 保存 (P) の `#if TRACE` 計装は T-2294 で izanagi 側の patch として完成しているが、verifier の certification gate は
「実際にコンパイルされる pinned source の `#if TRACE` 内に X と P の emitter がある」ことを要求するため、pin (e9e477ca) の mocc は certified になれない。
本 wave は計装を e9e477ca の子 commit C として submodule の hook 系統 branch に載せ、正例・負例と D1603 の材料 3 点 (候補 commit・D297 検査・波及範囲) を揃える。
gitlink・`CCBENCH_FULL_SHA`・`CURRENT_PIN` の更新、push、pin 再承認の提示、探索開始は scope 外。仮想リスク向けの gate・検査・台帳・一般化も scope 外。
あなたは read-only の plan 起草者で、実装・テスト実行はしない。書込可能 tmp が無いので静的読解でよい。**親の brief と実測の一般化も検査対象である。**

## plan に必ず含める項目

1. **(P1) 候補の中身。** 親の provisional = T-2294 patch から `#include <set>` の 1 行だけを除き、`std::multiset<const void*>` 2 箇所を `std::unordered_multiset<const void*>` に替え、`#line 17` を含む他の行は byte 不変。
   (a) multiset 等価性の意味論 (pointer の hash・等値、重複の扱い、`operator==` の計算量) と D1686 の P の主張「size と rcdptr_ multiset の保存」との同値、
   (b) `<unordered_set>` が同じ `#if TRACE` 内の `include/trace.hh` (:33) から供給されることへの依存の是非と、対案 (`std::vector` + `std::sort` + 比較、`<algorithm>` は transaction.cc :2 で直接 include) の比較、
   (c) `-O3 -Wall -Wextra -Werror -std=c++20` で落ちる箇所の有無、(d) `#line 17` を残すことの意味 (e9e477ca の論理行番号との対応、負例 2 本の文脈)、
   (e) D297 検査器 (`_compare_file`) の各判定をこの差分が通る理由を行単位で。親の probe (p4) は GCC 11.4 / 12.3 で pass を観測した — その一般化の限界も書く。
2. **(P2) 正例・負例の実走経路。** 親の provisional = 既存 driver に候補 mode を足す (候補 OID を CLI で受け、`checkout(C)` の上では計装 patch を当てず、負例 patch を C に直接当て、
   TRACE=0 は base = e9e477ca / inst = C を等長 dir で比較、新 JSON は C の OID・親 OID・tree・`cc/mocc/transaction.cc` の blob と候補 patch の sha に束縛)。対案 = 新規 driver file。
   どちらが登録簿 (materializer :78 / :93、condition gate の driver_id :283、spawn sites :63 / :217、build authority :164-186) と既存 test (`CHECK_KEYS` exact、JSON consumer :957、後続 driver 2 本の import) を動かさずに済むかを code で比べ、確定案を書く。
   CLI の形、check key の集合 (既存 14 key との対応、候補固有に足す key = 例: C の tree が e9e477ca の tree と transaction.cc 1 path だけ違う・その blob が候補 patch 適用結果と一致)、出力 path、schema 名、compute で 1 走する時の argv。
3. **(P3)/(P4) submodule commit の作り方。** branch 名 (親 provisional `izanagi-mocc-xp-instrumentation`、GitHub の既存名 `izanagi-mocc-pin-e9e477ca` の命名先例は t2304 §0)、witlight 先例の一時 worktree + `commit -F`、
   commit message と trailer (`docs/ai-provenance.md` と witlight の W-commit-message の先例)、submodule の checkout を gitlink のまま clean に保つ手順、bundle 保全、主 checkout の submodule git dir への fetch の時期 (land 前 / 後)。
4. **(P5) test の可搬性。** 他の wave の worktree の submodule は C の object を持たない (C は gitlink でないので `git submodule update` で取得されない、と親は読んでいる — 読みの当否も検査せよ)。
   repo の test を C の object に依存させない案 (候補の中身を `patches/` に e9e477ca 基準の patch として置き、test は e9e477ca + その patch で検査) と、D16 (trace-hook は branch、patches/ は broken / variant / 診断) との緊張を比べよ。
   T-2294 の計装 patch 自体が patches/ にある先例 (`patches/README.md`) も踏まえて、確定案と、その場合に test が C との束縛をどう持つか (JSON field か、親の実測か) を書く。
   新 test の一覧 (静的正例・負例: X/P 証拠面 C 相当 = present / e9e477ca = absent、構造 helper の再利用、TRACE=0 論理行列、負例 4 本の厳密適用、fixture の certified / indeterminate 振り分け、JSON consumer)、新 file か既存 file への追記か、既存 helper の import 可否。
5. **D297 の実走計画 (親が login で行う)。** `tools/check_trace0_preprocess_identity.py --repo <C を持つ submodule> --old e9e477ca --new C --cxx <3 種> --expect-paths cc/mocc/transaction.cc` の argv、
   負例対照 (patch をそのまま commit した C' が include 規則で拒否される = probe p2 と同型) の作り方、report の保存先、clang 14 の既知限界 (t2756 §3.3) の扱い。
6. **波及表 (D1603 材料 (3))。** 43 file を 1 行ずつ「pin を C へ進めた時: 追随 / 据置 (歴史・control・凍結) / 衝突」に分類し、文字列外の依存を列挙する。少なくとも:
   計装 patch・template・計装 template 版の preimage が e9e477ca であること (C では二重適用や文脈不一致になる)、`axis_mocc_temperature.PIN = pin.CURRENT_PIN` と PROOF_PIN、
   mocc trace pilot と D2153 receipt v2 (X/P patch の束縛)、`mocc_trace_v1_policy.json` の base/new、build admission policy の epoch (t2304 §0 の 4)、s3_* driver の自前 PIN、fixture。
   既知の件数は逐語 (43) から数え、hit 0 を依存なしと断定する前に key 側 (定数名・関数名) でも検索する。
7. **I 面 ([T-2295])。** 現行 pin で I emitter を持つ protocol が 0 であること (親の grep) の当否、mocc で I を閉じるのに要るもの (write-intent shadow の設計要素、silo の `izanagi-trace-t152` branch c9c1a9c2 が pin 系統外であること) を静的に書く。本 wave では実装しない前提。
8. **変異候補。** 段 4 で事前登録する変異 (正例・負例の両向き。例: 候補 patch の P 比較を恒真化、X 入口検査の削除、`#line` 1 つの ±1、JSON の OID 1 文字、driver 候補 mode の負例 patch 適用を省く、tree 差分検査の緩和) と期待 KILLED node の見込み。
9. **author 分割と所有 file 表。** 親 provisional = A (候補 patch の作成のみ) → 親が C を commit → B (driver 候補 mode + test + 登録簿の必要最小限 + `patches/README.md`)。重複なしの所有表。

## 出力形式

- 見出しは `#` 1 段だけを使い、`##` は最後の `## 総括` のみ。`### 総括` と書いてはならない。
- 各項目は file:line を添え、(P1)〜(P6) ごとに「支持 / 反証 / 条件付き」を明記する。
- 実行できない検査 (pytest・build) は「未実走・静的読解」と明記する。sandbox は read-only で書込可能 tmp が無いため緑は要求しない。
- 予算が尽きそうなら途中結論を出力形式どおり書いて終われ (無出力が最悪)。
- **出力は file に書かず、最終メッセージの本文に全文を書け** (親の launcher が保存する)。
- 末尾に `## 総括`: (P1)〜(P6) の判定一覧、確定設計の要約 (10 行以内)、author に渡す所有 file 表、未確定事項 (親裁定が要るもの) の列挙。
