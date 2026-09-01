## 受理集合

**F-01 — duplicate reader が既存の受理可能な WAL snapshot を過剰拒否する**

- 根拠: [p3_s4_loop.py:1107](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t441-grammar-version-canon/orchestrator/campaign/p3_s4_loop.py:1107) で、従来の `validate_commit_contract_bindings()` が完全な `_validate_attempt_topology()` に置換されている。duplicate snapshot は完全位相を前提としないため、親の実走でも既存5テストが `AttemptTopologyError` になった（[s6-parent-measurement.md:18](/work/1/SFC/tanab/dev-wave-jobs/2026-09-01_t441-grammar-version-canon/s6-parent-measurement.md:18)）。
- 修正案: ここでは `wal.validate_backoff_grammar_bindings(...)` と従来の `wal.validate_commit_contract_bindings(...)` を呼ぶ。正式 admission 用の `_validate_attempt_topology()` 内配線は [wal.py:1523](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t441-grammar-version-canon/orchestrator/campaign/wal.py:1523) に維持する。
- **成果物影響:** 既存 certified duplicate が aborted 扱いとなり、whiteboard・試行台帳・certified 選択が誤って変わる。
- 深刻度: **must-fix**

文法自体の受理集合には追加の異常を認めない。合成経路では structural gate、host-effect gate、文法判定を通過した後の [p3_s4_loop.py:321](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t441-grammar-version-canon/orchestrator/campaign/p3_s4_loop.py:321) でのみ正準化される。直接 validator の [backoff_hole_grammar.py:581](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t441-grammar-version-canon/orchestrator/campaign/backoff_hole_grammar.py:581) も変更されていない。

## 恒真な保証

**F-02 — R-11 の「一続き」テストが production 配線を通っていない**

- 根拠: [test_p3_s4_loop.py:437](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t441-grammar-version-canon/orchestrator/tests/test_p3_s4_loop.py:437) は、テスト自身が `Genome(... BACKOFF_FIXED=int(coder.value))` を構築し、別途 `quarantine()` を呼んでいる。production の genome 構築点 [p3_s4_loop.py:1263](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t441-grammar-version-canon/orchestrator/campaign/p3_s4_loop.py:1263) を壊しても緑のままである。
- 実効な注入点: `run_one_iteration(do_build=True)` から呼ばれる `run_campaign` を観測 seam にし、渡された genome、適用中 file bytes、版引数を同一呼出し内で固定する。
- **成果物影響:** `BACKOFF_FIXED` と canonical source がずれてもテストが検知せず、異なる実装値の binary が coder value に帰属して certified され得る。
- 深刻度: **should-fix**

**F-03 — canonicalizer の「accepted literal 消失」分岐は独立した防壁ではない**

- 根拠: [backoff_hole_grammar.py:725](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t441-grammar-version-canon/orchestrator/campaign/backoff_hole_grammar.py:725) で validator を通した後、同じ tokenizer・`_cpp_number_value()` を使う `attribution_numeric_literals()` を再実行している。validator の exact declaration/initializer 成立後に [backoff_hole_grammar.py:733](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t441-grammar-version-canon/orchestrator/campaign/backoff_hole_grammar.py:733) の `not present or value is None` へ到達する通常経路はない。
- **成果物影響:** 実装結果は変えない。独立した保証に見える到達不能な defensive assertion である。
- 深刻度: **nit**

## 版の単一性

**F-04 — reject identity と WAL の版を意図的にずらしても fail-closed にならない**

- 根拠: [p3_s4_loop.py:401](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t441-grammar-version-canon/orchestrator/campaign/p3_s4_loop.py:401) に `backoff_grammar_version=2` を渡すと variant ID は v2 で導出されるが、`start_payload` には版がない。WAL writer は [wal.py:647](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t441-grammar-version-canon/orchestrator/campaign/wal.py:647) で lock の値、例えば v1、を自動挿入するため比較が発火しない。その後の reader は lock v1／record v1 と見て受理する。
- 修正案: variant ID を導出する前に、明示された版と campaign lock の版を exact 比較する。少なくとも versioned lock 下で版省略または不一致を許さない負例を追加する。
- **成果物影響:** 試行台帳の variant identity は v2、WAL は v1という分裂が残り、duplicate 参照と critic 入力が別版へ帰属する。
- 深刻度: **must-fix**

通常の accepted production 経路では `_require_backoff_grammar_version()` と `run_campaign()` の二段 gate、および source/cache への伝播があり、静的には同じ値へ収束している。

## 既定経路の不変性

**F-05 — 共有 reject helper の既定 v1 が sort/trigger の variant ID まで変更する**

- 根拠: [p3_s4_loop.py:378](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t441-grammar-version-canon/orchestrator/campaign/p3_s4_loop.py:378) と [p3_s4_loop.py:401](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t441-grammar-version-canon/orchestrator/campaign/p3_s4_loop.py:401) の既定値が `None` ではなく backoff v1。版を持たない sort/trigger も [s6_sort_sweep.py:360](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t441-grammar-version-canon/orchestrator/campaign/s6_sort_sweep.py:360)、[s8a_trigger_sweep.py:462](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t441-grammar-version-canon/orchestrator/campaign/s8a_trigger_sweep.py:462)、[p3_s4_loop_sort.py:225](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t441-grammar-version-canon/orchestrator/campaign/p3_s4_loop_sort.py:225) から既定呼出しする。
- `SORT_LOOP` / `TRIGGER_LOOP` に版 key がないことをテスト自身も [test_p3_s4_loop.py:2468](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t441-grammar-version-canon/orchestrator/tests/test_p3_s4_loop.py:2468) で固定している。にもかかわらず reject identity だけが backoff v1 に束縛される。
- 修正案: 両 helper を `Optional[int] = None` とし、`None` なら従来の pre-image を exact に維持する。backoff の `run_one_iteration()` だけが campaign 由来版を明示する。
- **成果物影響:** sort/trigger の既存 reject variant と再実行時 variant が分裂し、重複検出不能・台帳の重複・参照切れを起こす。
- 深刻度: **must-fix**

それ以外の `None` 経路は静的に不変である。`_bind_backoff_grammar_version(raw, None) == raw`、stock 判定は束縛より先、loop/pipeline/buildcache の追加 kwargs も非 `None` 時だけ生成される。

## 固定値の非改変

所見なし。

- `integrated.diff` の変更対象は9ファイルだけで、禁止された `test_artifact_admission.py`、`test_critic.py`、`test_campaign.py`、`s1_expected_goldens.py` は含まれない（[integrated.diff:1](/work/1/SFC/tanab/dev-wave-jobs/2026-09-01_t441-grammar-version-canon/integrated.diff:1)）。
- 既存 literal の置換は裁定済み4 campaign IDだけである。[test_p3_s4_loop.py:3294](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t441-grammar-version-canon/orchestrator/tests/test_p3_s4_loop.py:3294)、[test_p3_b4_closed_critic.py:3070](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t441-grammar-version-canon/orchestrator/tests/test_p3_b4_closed_critic.py:3070)。
- skip、xfail、テスト削除、既存拒否期待の緩和はない。

## 拒否射影

所見なし。

新設された version gate、WAL validator、canonicalizer assertion の例外文は固定文字列であり、候補の identifier・literal・正準値・統計を投影していない。拒否候補は正準化されず、既存の固定 `rule_id` / reason が維持される。

## テストの実効性と変異

**F-06 — 正本どおりの変更に追随していない既存期待値が2件残る**

- 根拠: [test_p3_s4_loop.py:236](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t441-grammar-version-canon/orchestrator/tests/test_p3_s4_loop.py:236) は canonical `20` ではなく raw `20.0` を要求する。[test_p3_s4_loop.py:2648](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t441-grammar-version-canon/orchestrator/tests/test_p3_s4_loop.py:2648) は versioned `BUILD_START` の追加 key を欠く。親の実走でもこの2件が失敗している（[s6-parent-measurement.md:49](/work/1/SFC/tanab/dev-wave-jobs/2026-09-01_t441-grammar-version-canon/s6-parent-measurement.md:49)）。
- 修正は、前者の綴りを `20` にすることと、後者の BUILD_START key 集合へ `backoff_grammar_version` を1個加えることだけに限定する。他の assert は維持する。
- **成果物影響:** 正本と回帰参照が矛盾したままとなり、canonical source と新WAL schemaを受入済みとして検証できない。
- 深刻度: **must-fix**

**F-07 — 凍結変異 M2 は現在のテストでは殺せない**

- 根拠: [test_p3_s4_loop.py:2508](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t441-grammar-version-canon/orchestrator/tests/test_p3_s4_loop.py:2508) は signature だけ、[test_p3_s4_loop.py:2526](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t441-grammar-version-canon/orchestrator/tests/test_p3_s4_loop.py:2526) は helper と cache identity を直接検査するだけである。[loop.py:459](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t441-grammar-version-canon/orchestrator/campaign/loop.py:459) または [pipeline.py:1092](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t441-grammar-version-canon/orchestrator/campaign/pipeline.py:1092) から版引数を除いても緑のまま。
- 実効な注入点: `test_p3_s4_loop.py:2508` 付近で、`run_campaign` の resolver/evaluate seamと、pipeline の resolver/build・build_v2 seamに exact spyを置き、同じ campaign 版が全段へ渡ることを確認する。
- **成果物影響:** campaign IDだけが版付きで、source/cacheが旧版のまま再利用される回帰を許し、certified 母集合を汚す。
- 深刻度: **must-fix**

**F-08 — 凍結変異 M12 は identity 比較だけでは殺せない**

- 根拠: [test_p3_s4_loop.py:2558](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t441-grammar-version-canon/orchestrator/tests/test_p3_s4_loop.py:2558) は raw/bound keyが異なることだけを検査する。実装の cache lookup [buildcache.py:2495](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t441-grammar-version-canon/orchestrator/campaign/buildcache.py:2495)、[buildcache.py:3086](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t441-grammar-version-canon/orchestrator/campaign/buildcache.py:3086) に旧 key fallback を追加してもテストは緑である。
- 実効な注入点: `test_p3_s4_loop.py:2526` 付近で legacy/v2 の旧 unbound entry を poison して配置し、bound-v1 request がその entry を一度も開かず、新規 build 側へ進むことを両 API で固定する。
- **成果物影響:** 版導入前の binary が新文法の cache hit として再利用され、試行台帳と certified 成果物の版帰属が偽になる。
- 深刻度: **must-fix**

変異の判定は以下。

| 変異 | 判定 | 主な根拠 |
|---|---|---|
| M1 | KILLED | `test_p3_s4_loop.py:2463-2481` |
| M2 | **SURVIVES** | F-07 |
| M3 | KILLED | `test_p3_s4_loop.py:2484-2505` |
| M4 | KILLED | `test_p3_s4_loop.py:1516-1533` |
| M5 | KILLED | `test_p3_s4_loop.py:1536-1593` |
| M6 | KILLED | `test_p3_s4_loop.py:392-417` |
| M7 | KILLED | write=True の canonical file exact 検査 |
| M8 | KILLED | `test_p3_s4_loop.py:2531-2535` |
| M9 | KILLED | `test_p3_s4_loop.py:420-434` |
| M10 | KILLED | `test_p3_s4_loop.py:2536` |
| M11 | KILLED | 既存 `.v1` rule corpus `test_p3_s4_loop.py:628-768` |
| M12 | **SURVIVES** | F-08 |

## 総括

現状は受入不可。**must-fix 6件、should-fix 1件、nit 1件**である。

最優先は duplicate reader の過剰拒否、共有 reject helper による非backoff identity変更、reject identity/WAL版の不一致許容である。加えて親実走の2期待値を限定修正し、凍結変異 M2・M12 の実効テストを追加する必要がある。文法の accepted/rejected 集合、R-5固定資産、拒否射影そのものには追加の逸脱を認めない。