結論は **NO-GO** です。read-only の静的検査のみ行い、pytest・build・実測は実行していません。worktree は clean です。

### 1. [severity: blocker] 未解除 blocker を越えて実装を開始する計画になっている

この gate は、`T-184` の canonical stage matrix、R3-3〜R3-9、R2-b oracle が未実装の現状態では、成果物の build/certification 境界で発火しません。上流は「揃うまで実装 wave を起票しない」と明記しています（[package.md:92](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t316-semantic-gate-impl/output/insights/2026-08-09_t316-semantic-gate/package.md:92)、[phase3.md:763](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t316-semantic-gate-impl/docs/phase3.md:763)、[worklog.md:2328](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t316-semantic-gate-impl/docs/worklog.md:2328)）。

具体的な未充足入力は、`stage matrix=未発行`、`sandbox_stage_receipt=不存在`、`independent_oracle=不存在` の現 repository 状態です。さらに選択済み案 2 は build 防壁を「DSL/IR または厳格 copy-out」としており、有限 lexical denylist はいずれでもありません（[s1-brief.md:8](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t316-semantic-gate-impl/s1-brief.md:8)、[s1-brief.md:37](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t316-semantic-gate-impl/s1-brief.md:37)）。

修正案: 段 4 へ進めず、第三案の採用を再裁定するか、上流 blocker と選択済み build 防壁を先に実装してください。

### 2. [severity: blocker] `L.quarantine()` は全 coder-derived source の単一 seam ではない

この gate は、coder 由来 bytes が `render_hole()` を経ず、許可対象ファイルへ直接入る条件では発火しません。`quarantine()` が単一なのは hole renderer の範囲だけです（[p3_s4_loop.py:192](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t316-semantic-gate-impl/orchestrator/campaign/p3_s4_loop.py:192)）。

具体的な経路:

- `source_digest.ALLOWLIST` 内の tracked file を手動 patch し、`--allow-coder-derived-build` authority で `run_campaign()` を呼ぶと、`CODER_AUTHORED` admission が発行されます。semantic scan はありません（[source_digest.py:79](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t316-semantic-gate-impl/orchestrator/campaign/source_digest.py:79)、[source_digest.py:824](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t316-semantic-gate-impl/orchestrator/campaign/source_digest.py:824)、[build_admission.py:462](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t316-semantic-gate-impl/orchestrator/campaign/build_admission.py:462)）。
- `p3_s4_red.py` は実在する coder-derived build authority 経路で、固定 patch を直接 `applied()` して build します（[p3_s4_red.py:136](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t316-semantic-gate-impl/orchestrator/campaign/p3_s4_red.py:136)、[p3_s4_red.py:153](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t316-semantic-gate-impl/orchestrator/campaign/p3_s4_red.py:153)）。
- `s5_permutation_coverage._build_broken()` は直接 CMake build します（[s5_permutation_coverage.py:138](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t316-semantic-gate-impl/orchestrator/campaign/s5_permutation_coverage.py:138)）。
- shell materializer と任意 binary path は明示的に admission inventory 外です（[materializer_admission.py:11](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t316-semantic-gate-impl/orchestrator/campaign/materializer_admission.py:11)、[runner.py:346](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t316-semantic-gate-impl/orchestrator/calibrator/runner.py:346)）。

修正案: scanner を caller helper ではなく build materializer 境界へ置き、source hash・policy version に束縛された結果を必須入力にしてください。それまではこれらを「scope 外・未閉鎖」と記録する必要があります。

### 3. [severity: blocker] cache・WAL・certified 選択・proof chain は gate 実行を証明しない

この gate は、同じ source bytes/admission が scanner を経ずに build された場合、cache hit・COMMIT・freeze 選択で発火しません。

具体的には、cache key は source token と build-admission receipt を含みますが semantic policy/result を含みません（[buildcache.py:130](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t316-semantic-gate-impl/orchestrator/campaign/buildcache.py:130)）。legacy/v2 cache hit は source/admission を再照合するだけです（[buildcache.py:680](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t316-semantic-gate-impl/orchestrator/campaign/buildcache.py:680)、[buildcache.py:851](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t316-semantic-gate-impl/orchestrator/campaign/buildcache.py:851)）。

WAL の `BUILD_START` と `COMMIT` も build-admission SHA しか保持しません（[pipeline.py:718](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t316-semantic-gate-impl/orchestrator/campaign/pipeline.py:718)、[pipeline.py:1071](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t316-semantic-gate-impl/orchestrator/campaign/pipeline.py:1071)）。freeze selector は COMMIT と fitness/provenance を読むだけで再 scan しません（[s1_known_axes_freeze.py:266](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t316-semantic-gate-impl/orchestrator/campaign/s1_known_axes_freeze.py:266)、[s1_known_axes_freeze.py:432](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t316-semantic-gate-impl/orchestrator/campaign/s1_known_axes_freeze.py:432)）。

標準の S6/S8a driver は cache 判定前に `L.quarantine()` を通るため、その限定経路では cache hit は迂回になりません。しかし直接 buildcache caller と下流 proof consumer は区別できません。

修正案: `source_bytes_sha256 + scanner_policy_sha256 + result + materializer site` を build/cache/WAL/COMMIT に束縛し、freeze/material report がその receipt 欠落を拒否する必要があります。これは未解決の R3-3/R3-9 に依存します。

### 4. [severity: blocker] denylist は host effect に対して閉じておらず、具体的な非発火入力がある

親 brief の「閉じた効果 denylist」は refuted です。段 2 プラン自身は有限 lexical policy にすぎないと認めています（[s2-plan-c.md:1](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t316-semantic-gate-impl/s2-plan-c.md:1)、[s2-plan-c.md:78](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t316-semantic-gate-impl/s2-plan-c.md:78)）。

具体例:

- deny table に `close`、`fsync` などがなく、それらの identifier だけを含む入力では発火しません。実コードには該当処理があります（[fileio.hh:59](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t316-semantic-gate-impl/external/ccbench/include/fileio.hh:59)、[fileio.hh:67](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t316-semantic-gate-impl/external/ccbench/include/fileio.hh:67)、[fileio.hh:106](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t316-semantic-gate-impl/external/ccbench/include/fileio.hh:106)）。
- candidate token が `File(…)` だけでも、constructor 内部は `open()` を呼びますが scanner は発火しません（[fileio.hh:48](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t316-semantic-gate-impl/external/ccbench/include/fileio.hh:48)）。この型は sort TU の include closure に存在します（`cc/silo/include/transaction.hh:10,55`）。
- loop detectorは constant-fold しないため、条件 token が `2 - 1` の無退出 loop headerでは発火しません（[s2-plan-c.md:91](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t316-semantic-gate-impl/s2-plan-c.md:91)–101）。

修正案: measured 4 種を塞ぐ defense-in-depth とだけ表現してください。host-security boundary にするには選択済み DSL/IR、厳格 copy-out、run containment が必要です。

### 5. [severity: blocker] exact-token deny table は正常 C++ に実在し、偽陽性になる

逆にこの gate は、効果を持たない local identifier `open`、`read`、`write` などにも発火します。具体的な正常入力 `bool open = false;` は拒否されます。また `while (true) { break; }` も拒否されることをプラン自身が認めています（[s2-plan-c.md:100](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t316-semantic-gate-impl/s2-plan-c.md:100)）。

実 CCBench にも deny token は多数あります。

- `open/read/write`: [fileio.hh:36](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t316-semantic-gate-impl/external/ccbench/include/fileio.hh:36)、[fileio.hh:74](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t316-semantic-gate-impl/external/ccbench/include/fileio.hh:74)、[fileio.hh:89](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t316-semantic-gate-impl/external/ccbench/include/fileio.hh:89)
- `thread`: [runner.hh:49](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t316-semantic-gate-impl/external/ccbench/common/runner.hh:49)、[runner.hh:279](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t316-semantic-gate-impl/external/ccbench/common/runner.hh:279)
- `syscall`: [cpu.hh:31](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t316-semantic-gate-impl/external/ccbench/include/cpu.hh:31)

一方、静的 token 検査では、現行 S6 sort 15 候補、`test_p3_s4_loop_sort.py` の正常 fixture、正常 backoff literal、trigger の正準 32 emission は全件 hit なしでした（[s6_sort_sweep.py:100](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t316-semantic-gate-impl/orchestrator/campaign/s6_sort_sweep.py:100)、[test_p3_s4_loop_sort.py:63](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t316-semantic-gate-impl/orchestrator/tests/test_p3_s4_loop_sort.py:63)、[reflux_ir.py:131](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t316-semantic-gate-impl/orchestrator/campaign/reflux_ir.py:131)）。`write_set_` は exact token なので `write` に誤一致しません。

修正案: scanner 入力が必ず `coder.implementation` そのものだと spy test で固定してください。`edited_text` 全体を渡す実装なら CCBench 固定部の token により恒真拒否になります。短い generic identifier は resolved-call 検査か明示的な候補文法へ置き換えるべきです。

### 6. [severity: must-fix] W-2 は既に deny-only で、新しい安全性差分になっていない

親 brief の「W-2 がなければ auditor を騙すと W-1 も迂回できる」は refuted です。現コードは machine reject を auditor より先に返し、machine pass のときだけ digest/verdict を評価しています（[p3_s4_loop_sort.py:149](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t316-semantic-gate-impl/orchestrator/campaign/p3_s4_loop_sort.py:149)、[p3_s4_loop_trigger_gating.py:415](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t316-semantic-gate-impl/orchestrator/campaign/p3_s4_loop_trigger_gating.py:415)）。W-1 を `L.quarantine()` 内へ置けば、auditor pass は既に反転できません。

具体的に、新 helper 呼出しを現在の分岐へ戻す変異では受理集合が変わらず、W-2 のテスト・変異は生存します。

さらに `DiffQuarantineResult` と `AuditorVerdict` は公開 mutable dataclass です（[diff_quarantine.py:153](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t316-semantic-gate-impl/orchestrator/campaign/diff_quarantine.py:153)、[auditor_gate.py:110](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t316-semantic-gate-impl/orchestrator/campaign/auditor_gate.py:110)）。machine result を `passed=True` として直接構成する、または valid auditor 作成後に `verdict="pass"` と violations を矛盾状態へ変える条件では、提案 helper は scanner 実行や pass-schema の再検証を証明できません。

修正案: W-2 を「既存性質の factoring/doc 修正」と分類し、新規 security credit を外してください。sink では auditor を必ず再検証し、可能なら immutable 化してください。machine gate result についても issuer 認証ではない限界を明記すべきです。

### 7. [severity: must-fix] backoff の 4 種テストは書けるが、fixture 契約テストに限られる

プラン §5.2 のテストは、既存 `_TEMPLATE` と `_mk_template_dir()` を使うなら書けます（[test_p3_s4_loop.py:61](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t316-semantic-gate-impl/orchestrator/tests/test_p3_s4_loop.py:61)、[test_p3_s4_loop.py:113](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t316-semantic-gate-impl/orchestrator/tests/test_p3_s4_loop.py:113)、[test_p3_s4_loop.py:146](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t316-semantic-gate-impl/orchestrator/tests/test_p3_s4_loop.py:146)）。

ただしこの gate は、実 backoff `run_one_iteration()` では scanner より前の `applied(..., PIN="028f34d")` で停止します（[p3_s4_loop.py:88](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t316-semantic-gate-impl/orchestrator/campaign/p3_s4_loop.py:88)、[p3_s4_loop.py:890](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t316-semantic-gate-impl/orchestrator/campaign/p3_s4_loop.py:890)）。したがって「実 backoff 軸 E2E」は書けません。

修正案:

- backoff 4 種は「synthetic template に対する seam contract test」と明記する。
- current-pin 実路の結合検査は sort のみにする。
- W-1 全無効化変異は direct `L.quarantine()` fixture と build spy で帰属する。
- deny table の各 token/category を個別に検査する。現行 4 種だけでは、例えば `read` rule を削る変異が生存します。
- compiler reject や backoff pin failure を mutation kill 理由として数えない。

### 8. [severity: must-fix] 親 probe の測定範囲が過大に一般化されている

`probe_premises.py` は `_quarantine_and_audit()` も build も呼んでいません。実際に行うのは `L.quarantine(write=False)` と `parse_auditor_dict()`、`assert_digest_matches()` だけです（[probe_premises.py:36](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t316-semantic-gate-impl/probe_premises.py:36)、[probe_premises.py:48](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t316-semantic-gate-impl/probe_premises.py:48)）。したがって M2 の「実測で build へ進んだ」は refuted、現コードからの静的推論は confirmed です。

同様に:

- M1 の sort 4/4 と M3 の value checker 4/4 は probe 範囲内。
- backoff materialization は pin mismatch で未測定（[probe_premises.py:69](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t316-semantic-gate-impl/probe_premises.py:69)）。
- trigger α 閉鎖は `parse_wire → emit_predicate` の静的結論であり、この probe では未測定。ただし標準 proposal 経路についてコード上は支持される。
- M4 の「repo に effect 検査不在」は字面どおりなら falseで、sandbox probe の effect テストは存在します。正しくは「coder-hole admission/DiffQuarantine 層に不在」です。
- bytes pin 主張は refute されませんでした。`p3_s4_loop_sort.py` の記録 SHA `9b64…` と現物 `f2b9…` は既に乖離し、T-080 の歴史 migration record です。

修正案: M2/N2/M4 をそれぞれ「静的推論」「標準 trigger proposal 経路」「semantic admission 層」に限定して記録してください。

### 9. [severity: must-fix] `forbidden_identifiers` は恒偽のまま残る

この gate の `forbidden_identifiers` 経路は、どの coder wire 入力でも発火しません。producer が常に `[]` を返し（[p3_autonomous_workload_trial.py:652](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t316-semantic-gate-impl/orchestrator/campaign/p3_autonomous_workload_trial.py:652)–672）、consumer はその truthiness を security evidence として読みます（[autonomous_trial_completeness.py:607](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t316-semantic-gate-impl/orchestrator/campaign/autonomous_trial_completeness.py:607)）。

W-1 が `passed=False` を返せば第一条件では拒否できますが、第二条件は独立した保証として死んでいます。

修正案: trigger は canonical IR のため、この field を producer/consumer/schema から削除するのが最も正直です。残すなら scanner の固定 rule ID を入れ、non-empty positive control を必須にしてください。現計画どおり scope 外にする場合は「未閉鎖」と明記してください。

### 10. [severity: must-fix] bytes 非反射テストが全漏洩面を覆っていない

現 `assert_value_literal_consistent()` は mismatch で `coder.value` と literal を、抽出不能時には `implementation!r` 全体を例外へ反射します（[p3_s4_loop.py:790](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t316-semantic-gate-impl/orchestrator/campaign/p3_s4_loop.py:790)–803）。プランは実装修正を挙げていますが、テストは「implementation bytes」のみで、value/literal の反射を明示的に覆っていません（[s2-plan-c.md:269](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t316-semantic-gate-impl/s2-plan-c.md:269)–273）。

また scanner/tokenizer が予期せず例外を投げると、S6 は `str(e)` を provenance の `error` へ保存します（[s6_sort_sweep.py:301](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t316-semantic-gate-impl/orchestrator/campaign/s6_sort_sweep.py:301)–307）。

修正案: value、literal、implementation に別々の sentinel を置き、例外、WAL、critic render、S6 provenance の全投影に一つも現れないことを検査してください。診断は固定 subtype、rule ID/category、位置、件数で十分構造化されています。

### 層別の閉鎖判定

| 層 | 判定 |
|---|---|
| backoff/sort/trigger driver と autonomous preview の `L.quarantine()` | W-1 は適用可能 |
| S6 sort fixture、S8a trigger fixture、S1 direct comparison、extime calibration | W-1 は適用可能。W-2 auditor は存在しない経路あり |
| backoff 現行 pin の実路 | 未実行。fixture 契約のみ |
| manual patch、`p3_s4_red`、直接 `run_campaign/buildcache` | scope 外・未閉鎖 |
| S3/S5 等の直接 CMake materializer | scope 外・未閉鎖 |
| `tools/pegasus/*.sh`、任意 binary を取る calibrator | scope 外・未閉鎖 |
| legacy/v2 cache hit | 標準 driver は事前 scan、直接 caller は未閉鎖。policy receipt 不在 |
| WAL replay、COMMIT、provenance、known-axes freeze、proof chain | semantic gate の positive receipt・再 scan がなく未閉鎖 |
| build copy-out、run sandbox、独立 oracle、stage receipt | 本 wave scope 外・未閉鎖 |

## 総括

- **NO-GO。**
- 上流 blocker が未解除で、有限 denylist は裁定済みの DSL/IR・厳格 copy-out の代替になっていません。
- `L.quarantine()` 外の materializer、cache/proof chain、manual coder-authority 経路が未閉鎖です。
- W-2 は既に deny-onlyで安全性差分がなく、backoff は fixture 契約へ限定して計画を書き直す必要があります。