# 静的設計レビュー

結論として、提案の「小言語を parse して trusted C++ を生成する」方向は成立し得ますが、現プランのままでは受理集合と proof-chain の境界が未確定です。特に、semantic gate を通った IR・生成 C++・build 用 Genome を同一の検証済み成果物として束縛していません。

本レビューは read-only の静的検査のみです。書き込み、pytest、ビルド、実行は一切行っておらず、テストが緑であるとは主張しません。以下はすべて must-fix 相当で、nit はありません。

## 受理集合の実像

| 層・軸 | プラン採用後に実際に期待できる集合 |
|---|---|
| `DiffQuarantine` | 変更なし。hole 内で directive、marker、`//`、`/*`、行末 backslash を含まない構文クラスは引き続き受理される |
| backoff | 意図上は整数 1〜1000 の1000 IR。ただし全値が同じ C++ 本文へ render され、実際の差は別経路の Genome flag に残る |
| trigger | 8 enum 値に対する boolean 関数で `kUnset=true`。意味集合は最大128通りだが、構文上限未定義のため実受理集合は未確定 |
| sort compatibility | exact byte 比較なら受理集合は N 個の文字列だけ。ただし N と bytes がプランに存在しない |
| sort typed IR | 2 field・重複なし・非空・長さ2までなら最大12形。空配列や最大長の扱いが未定義 |

## Must-fix 所見

### 1. Critical — 「閉じる vector」は `DiffQuarantine` 自体の保証ではない

**claim:** プランの semantic gate は外側の認証経路を狭め得ますが、`DiffQuarantine` の受理集合は変わりません。また、三つの `run_one_iteration()` で gate を再実行するだけでは、raw-string API を経由する別 consumer に対する不変条件になりません。

**evidence:** hole 内の拒否分岐は directive、marker、コメント delimiter、line splice に限られ、該当しなければ passed になります（[diff_quarantine.py:459-496](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t316-role-gate/orchestrator/campaign/diff_quarantine.py:459)）。したがって無害な形の `f(x); g(y);` のような複数 statement はどの拒否分岐にも当たりません。現在の `quarantine()` と `render_hole()` は raw `str` を取ります（[p3_s4_loop.py:154-180](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t316-role-gate/orchestrator/campaign/p3_s4_loop.py:154)）。プランは `RenderedHole` 型と三 driver の再 gate を挙げますが（[s2-plan.md:164-165](/home/SFC/tanab/.claude/jobs/31b3fbdf/tmp/wave-t316/s2-plan.md:164)、[s2-plan.md:359](/home/SFC/tanab/.claude/jobs/31b3fbdf/tmp/wave-t316/s2-plan.md:359)）、raw API の build-capable consumer 閉包は示していません。

**impact:** legacy・追加 consumer が raw `quarantine()` から build へ進むと、全軸の certified 受理集合が現行の広い構造集合へ戻ります。

**suggested_fix:** production の唯一の build 入口を `ValidatedCandidate` のみにし、その内部で renderer と structural quarantine を呼ぶ構造にすること。raw string 版は preview/test 専用として build API から分離し、全 call site の census と bypass mutant を置いてください。「閉じる」は `DiffQuarantine` でなく certified pipeline の保証だと明記すべきです。

### 2. Critical — backoff の integer 保証と帰属保証が end-to-end で成立しない

**claim:** 現行 interface のまま `run_one_iteration()` で integer gate を再実行すると、正常な JSON integer と禁止する float を区別できません。さらに、異なる `BackoffSpec` が同一 C++ 本文へ render されるため、IR と Genome の束縛が別途必要です。

**evidence:** プランは float・bool・指数表記を拒否し（[s2-plan.md:174](/home/SFC/tanab/.claude/jobs/31b3fbdf/tmp/wave-t316/s2-plan.md:174)）、直接呼び出しでも gate を再実行するとします。しかし現行 `CoderProposal.value` は `float` で（[p3_s4_loop.py:105-110](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t316-role-gate/orchestrator/campaign/p3_s4_loop.py:105)）、loader は正常な JSON integer も `float(c["value"])` に変換します（[p3_s4_loop.py:717-723](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t316-role-gate/orchestrator/campaign/p3_s4_loop.py:717)）。一方 Genome は gate の返却物でなく `int(coder.value)` から作られます（[p3_s4_loop.py:629-634](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t316-role-gate/orchestrator/campaign/p3_s4_loop.py:629)）。固定 renderer は全値について同じ `BACKOFF_FIXED` 参照を生成します（[s2-plan.md:153-156](/home/SFC/tanab/.claude/jobs/31b3fbdf/tmp/wave-t316/s2-plan.md:153)）。

**impact:** integral float を許せば宣言した受理集合が広がり、拒否すれば正常 JSON integer まで落ちます。また IR と build flag がずれると別値の binary に fitness を帰属できます。

**suggested_fix:** raw JSON 上で `type(value) is int` を確認し、`CoderProposal.value` と loader を `int` のまま保つこと。NaN/Infinity は decoder の `parse_constant` でも拒否してください。gate は immutable な `{canonical_ir, genome, rendered_hole}` を一括返し、Genome を必ず canonical IR から構成させ、IR digest・rendered source digest・flag digest を同一 identity に束縛すべきです。

### 3. High — trigger の truth table は renderer の意味を検査しない

**claim:** プランの truth-table test が証明するのは parser/interpreter 側の IR だけです。renderer が演算子を取り違える、否定を落とす等の写像誤りがあっても、生成 C++ の `kUnset` 契約は検査されません。

**evidence:** プランは token/depth 上限を置くとしますが具体値・EBNF・優先順位を定義していません（[s2-plan.md:140-146](/home/SFC/tanab/.claude/jobs/31b3fbdf/tmp/wave-t316/s2-plan.md:140)）。許可演算子と enum は列挙され（[s2-plan.md:174-176](/home/SFC/tanab/.claude/jobs/31b3fbdf/tmp/wave-t316/s2-plan.md:174)、[trigger patch:56-67](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t316-role-gate/patches/silo-backoff-trigger-gating-variant.patch:56)）、test は IR の truth table だけです。C++ harness は sort にだけ明記されています（[s2-plan.md:203-205](/home/SFC/tanab/.claude/jobs/31b3fbdf/tmp/wave-t316/s2-plan.md:203)）。

**impact:** parser が受理した安全な IR と実際に build される述語が異なったまま、semantic test と `kUnset=true` assert が緑になり得ます。

**suggested_fix:** lexer、EBNF、型規則、EOF、byte/token/depth 上限を数値で固定し、IR を8 enum 値の truth-vectorへ正規化してください。そのうえで renderer 出力を C++ harness に入れ、全8値で IR evaluator と一致することを differential test するべきです。これは C++ text の意味推測ではなく、有限 IR の生成結果を実 compiler で照合するため D33 と両立します。

### 4. High — sort の「有限 exact allowlist」は内容未定義である

**claim:** 「有限」「canonical」という名称だけでは受理集合になりません。exact 比較なら N 個の byte string だけを残しますが、プランには N、識別子、bytes、digest のいずれもありません。

**evidence:** 最終 IR の概形は示されていますが、空配列、最小・最大長、field 優先順位の正規形が未指定です（[s2-plan.md:175-178](/home/SFC/tanab/.claude/jobs/31b3fbdf/tmp/wave-t316/s2-plan.md:175)）。compatibility 案は「trusted renderer が持つ有限個の exact canonical comparator」とするだけです（[s2-plan.md:357](/home/SFC/tanab/.claude/jobs/31b3fbdf/tmp/wave-t316/s2-plan.md:357)）。実 hole は comparator body を含む複数行領域です（[silo-sort-variant.patch:54-59](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t316-role-gate/patches/silo-sort-variant.patch:54)）。

**impact:** 実装者が raw C++ の空白正規化や部分 parse を導入すれば受理集合が非意図的に広がり、逆に byte exact のつもりでも何を受理するかレビュー不能です。

**suggested_fix:** 人間レビュー済みの symbolic comparator ID → exact UTF-8 bytes → SHA-256 の固定表を先に提示してください。照合前の C++ 正規化は行わず、意味的に同じ別表記も拒否するべきです。表が用意できなければ、プラン自身が述べる `sort do_build=True` 停止を必須条件にしてください。

### 5. High — sanitizer positive control に production 経路で発火する入力クラスがない

**claim:** sort の非 allowlist comparator は pre-build reject されるため sanitizer へ到達しません。到達させるため unsafe comparator を allowlist に加えると規律2違反です。また D41 は「ASan/UBSan 自体が必ず赤にする」とは決めていません。

**evidence:** プランは semantic reject 時の build spy ゼロを要求する一方（[s2-plan.md:199-207](/home/SFC/tanab/.claude/jobs/31b3fbdf/tmp/wave-t316/s2-plan.md:199)）、同じ test 群で comparator mutant を ASan/UBSan で赤にするとしています。sort は非 allowlist を pre-build reject する設計です（[s2-plan.md:357-365](/home/SFC/tanab/.claude/jobs/31b3fbdf/tmp/wave-t316/s2-plan.md:357)）。D41 は release の crash/hang と sanitizer run を区別し、別途 permutation mutant を要求しています（[decisions.md:1268-1273](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t316-role-gate/docs/decisions.md:1268)）。現行 driver も機械的 SWO test は未実装で、auditor と timeout が現状防壁だと明記します（[p3_s4_loop_sort.py:46-51](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t316-role-gate/orchestrator/campaign/p3_s4_loop_sort.py:46)）。

**impact:** test は semantic gate で止まって sanitizer を一度も試さないか、timeout を「sanitizer 赤」と数える恒真保証になるか、unsafe allowlist で受理集合を広げます。

**suggested_fix:** production allowlist と分離した test-only post-render mutation seam を設けてください。admission reject、release crash/hang、sanitizer diagnostic、permutation failure を別 oracle として記録し、timeout を sanitizer の検出力として数えないことが必要です。

### 6. High — template patch SHA 検査に独立した期待値がない

**claim:** プランは SHA 引数を追加するとしますが、期待 digest の独立した正本を定義していません。同じ path から expected と actual を計算すれば比較は恒真です。

**evidence:** 提案は SHA を `TEMPLATE_PATCH` と束縛するとだけ述べます（[s2-plan.md:301](/home/SFC/tanab/.claude/jobs/31b3fbdf/tmp/wave-t316/s2-plan.md:301)）。現行定義は backoff と sort が path string のみ（[p3_s4_loop.py:82](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t316-role-gate/orchestrator/campaign/p3_s4_loop.py:82)、[p3_s4_loop_sort.py:94](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t316-role-gate/orchestrator/campaign/p3_s4_loop_sort.py:94)）、trigger も path string のみです（[axis_trigger_gating.py:25](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t316-role-gate/orchestrator/campaign/axis_trigger_gating.py:25)）。`applied()` は path と ccbench pin だけを受け、直ちに patch を適用します（[patchharness.py:234-251](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t316-role-gate/orchestrator/campaign/patchharness.py:234)）。

**impact:** trusted template の bytes が変わっても、検査が同じ変更後ファイルを両辺に使えば semantic boundary の変更を検出しません。

**suggested_fix:** axis ごとの独立した reviewed `EXPECTED_TEMPLATE_PATCH_SHA256` 台帳を設け、`{path, expected_sha}` を `applied()` に渡してください。path を変えず patch を1 byte変更した入力が `patch_files()` より前に必ず失敗する mutation test が必要です。

### 7. Medium — typed IR 移行の pin/consumer 閉包が不足している

**claim:** 四台帳・manifest・adapter の列挙は hash pin 閉包としては概ね正しいものの、最終 typed schema の実行 consumer 閉包ではありません。

**evidence:** プランの影響表は role source、四台帳、manifest、adapter を挙げます（[s2-plan.md:305-332](/home/SFC/tanab/.claude/jobs/31b3fbdf/tmp/wave-t316/s2-plan.md:305)）。しかし unattended supervisor は role path を独自保持し、raw `implementation` schema を prompt と parser の双方に埋め込んでいます（[p3_autonomous_workload_trial.py:145-175](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t316-role-gate/orchestrator/campaign/p3_autonomous_workload_trial.py:145)、[同:305-325](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t316-role-gate/orchestrator/campaign/p3_autonomous_workload_trial.py:305)）。policy も backoff の `int|float` を独自受理します（[policy.py:461-480](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t316-role-gate/orchestrator/codex_roles/policy.py:461)）。test literal と runbook にも旧 schema が残ります（[test_codex_agents.py:853-874](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t316-role-gate/orchestrator/tests/test_codex_agents.py:853)、[phase3-s4b-runbook.md:72-74](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t316-role-gate/docs/phase3-s4b-runbook.md:72)、[phase3-s5-sort-runbook.md:73-75](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t316-role-gate/docs/phase3-s5-sort-runbook.md:73)）。

**impact:** typed IR へ移行すると supervisor が停止するか、旧 raw parser が残って semantic gate を迂回する二重契約になります。

**suggested_fix:** role 名だけでなく source path、prompt、parser、policy、tests、runbooksを含む consumer inventory を作り、typed migration wave で一括変更してください。現在 wave の compatibility grammar は role bytes/schemaを変えないため、その範囲なら pin 更新不要です。なお adapter 内の path+hash pin はプランが既に捕捉しています。静的検索上、三 role の source/schema hash を別途 pin する docs はなく、docs にあるのは schema literal です。`t080_freeze_migration.py:87-103` の path-key hash は歴史的成果物の記録なので更新対象にしてはいけません。

### 8. Medium — 実測5の「0からの純増」と P1 は一般化が過大

**claim:** `test_diff_quarantine.py` 内に deterministic semantic rejection が0本という限定事実は正しい一方、意味的に不適切な hole 内容が structural gate を通ることの既存 positive characterization は既にあります。したがって「被覆が0」は分類を分けない限り誤りで、P1の test-only方針も実測から導けません。

**evidence:** 対象ファイルには静的に38個の `test_` 定義があり、受理例は構造確認です（[test_diff_quarantine.py:190-196](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t316-role-gate/orchestrator/tests/test_diff_quarantine.py:190)）。一方、trigger sweep test は複数 statement が通ることを明示的に固定しています（[test_s8a_trigger_sweep.py:201-215](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t316-role-gate/orchestrator/tests/test_s8a_trigger_sweep.py:201)）。sort test も意味契約外 comparator が `DiffQuarantine` を通り、preset auditor reject でのみ落ちることを確認します（[test_p3_s4_loop_sort.py:152-169](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t316-role-gate/orchestrator/tests/test_p3_s4_loop_sort.py:152)）。親はこれを一括して0とし、test-onlyをP1に置いています（[brief.md:24-35](/home/SFC/tanab/.claude/jobs/31b3fbdf/tmp/wave-t316/brief.md:24)）。

**impact:** 「semantic gate の新規検出力」と「既知の脆弱境界 characterization」を混同し、通常テストで広い受理集合を将来契約として固定します。

**suggested_fix:** baseline を「structural pass characterization は既存」「deterministic semantic reject + build-zero は0」に分けてください。P1を採らず、プランの [s2-plan.md:367-369](/home/SFC/tanab/.claude/jobs/31b3fbdf/tmp/wave-t316/s2-plan.md:367) どおり semantic reject/build-zero integration、または coder-derived build 停止を完了条件にすべきです。

### 9. Medium — 親 P2 の load-bearing 判定は意味受理集合について成立しない

**claim:** sandbox は host containment には load-bearing ですが、candidate の意味的正しさや certification の受理集合には load-bearing ではありません。親P2は二つの性質を混同しています。

**evidence:** 親は sandbox 側を load-bearing、表現制限を defense-in-depth とします（[brief.md:36-40](/home/SFC/tanab/.claude/jobs/31b3fbdf/tmp/wave-t316/brief.md:36)）。しかしプラン自身が sandbox 内の任意計算、measurement/reward 経路、arbitrary C++ の certification を閉じないと認めています（[s2-plan.md:258-267](/home/SFC/tanab/.claude/jobs/31b3fbdf/tmp/wave-t316/s2-plan.md:258)）。

**impact:** P2のまま裁定すると、hostから隔離されただけの任意候補を「意味 gate 済み」と誤って certified 集合へ入れます。

**suggested_fix:**保証を「host side-effect containment」と「certified semantic admission」に分離し、前者は sandbox、後者は bounded IR + renderer を load-bearing と明記してください。

## D33・auditor・規律2・親実測3の判定

**D33:** 小言語を parse して内部 renderer だけから C++ を生成する構成はD33と両立します。ただし sort raw text を空白・式の同値性で正規化し始めると部分的 C++ 意味判定へ退化します。compatibility 期間は exact byte lookup に限定すべきです。

**auditor:** 親P3とプランの位置づけは妥当です。`assert_digest_matches()` は同じ diff を見たことだけを検査し（[auditor_gate.py:64-75](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t316-role-gate/orchestrator/campaign/auditor_gate.py:64)）、残りも verdict の型・自己整合検査です（[auditor_gate.py:105-157](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t316-role-gate/orchestrator/campaign/auditor_gate.py:105)）。意味真偽の独立防壁には数えられません。

**規律2:** 推奨案(c)に意図的な受理集合拡大は見当たりません。ただし sanitizer mutant を production allowlistへ入れる、raw `quarantine()` fallbackを残す、sort textを「等価だから」と正規化する実装は規律2違反になります。

**親実測3:** sort 軸でも一般化は成立します。`transaction.cc` は `transaction.hh` を含み（[transaction.cc:1-7](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t316-role-gate/external/ccbench/cc/silo/transaction.cc:1)）、そこから `backoff.hh`（[transaction.hh:3-10](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t316-role-gate/external/ccbench/cc/silo/include/transaction.hh:3)）、`util.hh`（[backoff.hh:9-12](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t316-role-gate/external/ccbench/include/backoff.hh:9)）、POSIX系header（[util.hh:3-9](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t316-role-gate/external/ccbench/include/util.hh:3)）へ到達します。

## 総括

**最大の論理的穴:** semantic gate が build の唯一の choke pointではなく、backoffでは validated IR・rendered C++・Genomeが一体化されていません。したがって「閉じた受理集合」が経路不変条件になっていません。

**親 brief の誤り:** 実測5は deterministic semantic rejection と既存 vulnerability characterization を混同し、P1を支えません。P2も host containment と意味 admission を混同しています。実測3とP3は静的コードと整合します。

**必須修正:** axis別の厳密な grammar/allowlist、独立 template-patch pin、IRからのみ生成される immutable candidate、parser–renderer differential test、全 consumer閉包を仕様化してください。それができない軸は coder-derived build を fail-closed で停止する必要があります。