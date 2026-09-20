# 段 1 brief — [T-2629] 旧分岐の compiler 非対称の到達条件と既存の拒否を実測する

基準: local main `b7f970dfa` (fresh worktree `.claude/worktrees/dev-wave-t2629-legacy-compiler-reach`)。
起点: 台帳 entry 1498 (`docs/archive/worklog-phase3-0914-1498.md:698`)、insight
`output/insights/2026-09-14/t1643-has-include-real-pair/README.md` §9 (R-1)、裁定 D2044 項 24。

## 研究前進 (1 行)

論文の安全主張「variant identity (src_token) は build と同じ compiler で確定し、compiler 差は fails-closed」の
被覆範囲を、production の全呼び手について明記して閉じる (土台項目。開いたままだと規律 2 の identity gate に
「静的な穴」が台帳に残り続ける)。完了判定 = 到達条件の表 + 既存の拒否の実測 + 修正要否の裁定 (D)。

## scope

- 本題: `pipeline.py:1992` `common is None` (= `env_contract is None`) の旧分岐が `buildcache.build()` を
  cc/cxx 無し (既定 `gcc-13`/`g++-13`、`buildcache.py:622`) で呼ぶ一方、事前 evidence (`pipeline.py:1790`)
  は `compilers_for_current_site()` を使う非対称の、(1) 到達条件、(2) 既存の拒否、(3) 修正要否。
- scope 外 (引数で明示): 新 gate・台帳・一般化の追加。checker (`source_digest`) の変更。

## 確定済みユーザー裁定・既裁定

- D2044 項 24: 到達条件と既存の拒否を確かめてから修正の要否を決める。限界として閉じる場合も確認した呼び手の
  範囲を明記する。
- D293 (2026-08-11): 旧分岐の `g++-13` 固定要求は「現に効いている fail-closed 障壁」。compiler の site 依存化は
  calibration 由来の toolchain 束縛検査と同じ commit でしか入れない。**→ 旧分岐へ site compiler を渡す「修正」は
  D293 が禁じる方向であり、候補にしない。**
- 修正するなら Codex author (D95) + 変異 (正例・負例)。規律 2 を緩めない。

## brief 前の実測 (静的読取 + login 実測)

- 非対称の成立条件は 2 条件の積: (A) `env_contract is None` かつ (B) `site_policy.current_site() == PEGASUS_COMPUTE`。
  (B) 以外の site では `compilers_for_current_site()` (`buildcache.py:1863`) が既定 (= 旧分岐の既定) を返し対称。
  login 実測 (pegasus02、2026-09-20): site=`PEGASUS_LOGIN`、`compilers_for_current_site()=('gcc-13','g++-13')`、
  `which g++-13 = None`。
- 呼び手 (AST 走査、`orchestrator/` + `tools/` の非 test、`loop.run_campaign` / `pipeline.evaluate` /
  `pipeline._prepare_evaluation` の 25 呼び出し):
  - env_contract を常に渡す (11): b10_backoff_shape_sweep:4470、b10_backoff_static_tail_formal:761、
    backoff_extended_sweep:1446、backoff_sweep:484 (+ screening 339/364)、p2_2:376、paper_story_a1_paired:7178/7428、
    paper_story_a2_certification:3803、t126_driver:623、s8b_oracle_driver:1781、manual_probes/test_t2397_a1_source:96。
  - site 条件付き (2): p3_s4_loop:2012、p3_s4_loop_trigger_gating:811 — `resolved_site == PEGASUS_COMPUTE` のとき
    contract を渡す (= (B) のとき (A) が偽)。
  - 渡さない (12、すべて ENV_TAG `linux-baremetal`): backoff_repro:172、demo:57/67、p3_kickoff:152/159、
    p3_s4_loop_sort:413、p3_s4_red:207/217、s6_sort_sweep:413 (+ screening 321/421)、s8a_trigger_sweep:515
    (+ screening 421/523)、sanity_silo:59、s1_direct_comparison:1281。
- 既存の拒否 (静的):
  - (R-a) `pipeline.py:1738` / `loop.py:177` `execution_guard.require_certified_writer_authorization`:
    `execution_guard.py:137` 計算ノードでは attestation required な唯一の契約 (pegasus) 以外を拒否
    → `linux-baremetal` の 12 呼び手は evidence・build より前に落ちる。
  - (R-b) 計算ノードに `g++-13` 不在 (2026-09-14 bnode009 実測、T-1643 §3) → 旧分岐 fresh build は cmake configure
    失敗 → `_run` RuntimeError → `build-error` abort。cache hit 側は `_recheck_source_evidence(cxx='g++-13')` が
    `preprocess を起動できない` RuntimeError。どちらも fails-closed。
  - (R-c) `buildcache.py:3630` `_recheck_source_evidence` は build compiler で再計算した SourceEvidence 全体の
    exact 一致を要求 → compiler 差で identity がずれれば TOCTOU として reject。受理側へ倒れる経路は無い。
- 発生記録: worklog / failures に旧分岐 × 計算ノードの発生記録は無し (T-2629 本文も「静的に確認済み、発生記録なし」)。

## (P1) 親の provisional 裁定 — 攻撃対象

(P1) 非対称は production の呼び手では到達不能 (pegasus 契約 × env_contract 無しの呼び手は 0)。到達したとしても
(R-b) で fails-closed。したがって**修正しない**。限界として閉じ、確認した呼び手の範囲 (上の 25 件) を明記する。
(P2) 「対称化のために事前 evidence も既定 `g++-13` にする」変更は abort の reason を `build-error` から
`pre-build evidence 確定不能` へ変えるだけで受理集合を変えない → DW-G05 により実装しない。

## 不変条件

- 規律 2: 受理集合を広げない。probe は checker・build・gate を変えない (読み取り + 実呼び出しのみ)。
- 共有 build cache を汚さない: probe の `cache_root` は job dir。
- probe は Codex author が書く (D95)。repo に残さない (T-1643 の型、job dir へ退避)。

## 成果物の形

- insight `output/insights/2026-09-20/t2629-legacy-compiler-reach/README.md` (到達条件表、呼び手表、実測結果、裁定)。
- decisions fragment (D: 修正しない・限界として閉じる・呼び手範囲)、worklog fragment。
- probe 出力 JSON (login + compute) は job dir、README に要約。

## 並列分割方針 (軽量版)

- 段 2 省略。段 3 相談 1 本 (2 レンズ: 「到達不能の反証」「fails-closed の反証」)。
- 段 5 Codex author 1 本: `tools/t2629_legacy_compiler_reach_probe.py` (≤ 150 行)。実測項目:
  1. site / `compilers_for_current_site()` / `shutil.which('g++-13')` / `which('g++')`。
  2. (R-a) `require_certified_writer_authorization(authorize('linux-baremetal'), env_tag='linux-baremetal',
     clocks_per_us=<登録値>, numactl=<登録値>, env_contract=None)` の例外型と本文; 同じく `'pegasus'` で通ること。
  3. (R-b) 実 `source_digest.resolve_evidence(stock genome, submodule HEAD, cxx=<site cxx>)` の成功と
     `cxx='g++-13'` の例外本文。
  4. (R-b) 実 `buildcache.build(stock, trace=True, cache_root=<job dir>, admission/build_context/source_evidence
     は production API で導出)` を cc/cxx 無しで呼び、例外型・本文 (cmake configure 失敗) を記録。
  各項目は `{"observed": ..., "exception": {"type","message"}}` の JSON で `--output` へ。
- 段 6: 独立 read-only レビュー 1 本 (README + probe 出力)。
- 受入・land は共通手順。
