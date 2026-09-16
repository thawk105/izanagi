# [T-2502] 既裁定と一次資料の逐語射影

親 (Claude manager) が HEAD 1042a1bc9 (= local main、2026-09-17 00:40 JST) から写した。編集していない。

## D1878 (docs/decisions.md の逐語)

`verbatim-d1878.txt` (同 dir) の 19 行が逐語。要旨は次のとおり (要旨は親の要約であり逐語ではない):
`--run-iteration` について `--knowledge-manifest` の `sources` が**非空のときだけ** `--coder-role` を必須にする。
空取得 (`completed_empty` / `sources: []`) は現状のまま通す。却下: 現状維持 (job body だけで守る)、無条件の相互必須化。

## entry 1527 の [T-2502] 持ち越し本文 (docs/archive/worklog-phase3-0916-1527.md の逐語)

`verbatim-entry1527.txt` (同 dir) の 7 行が逐語。

## 親の前提実測 (2026-09-17 00:30〜00:45 JST、worktree HEAD 1042a1bc9)

- `git log --all --grep T-2502` / `--grep D1878`: 0 件。worklog に `## … — [T-2502]` 見出し無し。最新「次の一手」に `[T-2502] (1578)` の持ち越しあり = **未着地**。
- D1878 以降に D1878 を変更・限定する裁定: `grep -n "coder-role\|coder_role\|D1878" docs/decisions.md` は D1878 自身の 2 行だけ。D1999 は K2 manifest の source 選定規律で本件の条件を変えない。
- 現物 `orchestrator/campaign/p3_s4_loop.py` (HEAD 1042a1bc9):
  - `load_proposal_file` (:2254〜) の `has_knowledge_input != has_coder_role` → `ValueError("knowledge_input と coder_role は両方指定するか両方省略する必要がある")` (:2309〜2314)。関数レベルの API 不変条件。
  - `main()` の `--run-iteration` 分岐 (:2748〜) は `load_proposal_file(..., knowledge_input=(knowledge_input if a.coder_role is not None else None), coder_role=a.coder_role)` (:2774〜2777)。**`--knowledge-manifest` あり・`--coder-role` なしのとき loader へは `knowledge_input=None` が渡り、loader の検査は素通りして legacy flattened 経路になる。** manifest の `sources` が非空でも同じ。
  - その前に `_prepare_knowledge_campaign` (:2728〜) が `cfg.search_config` へ `knowledge_level` と `knowledge_manifest_sha256` を焼き、`layout.ensure()` + `knowledge_manifest.write_receipt` を行う。つまり K2 として identity と receipt に記録されるのに、proposal は K2 consumer (schema `CODER_CONTRACT_K2`・anomaly・参照 index) を通らない。これが D1878 が閉じたい齟齬。
  - `_resolve_knowledge_manifest_argument` (:1520〜) は `knowledge_manifest.load_and_resolve_manifest` を返し、`ResolvedKnowledgeManifest.manifest.sources: tuple[KnowledgeSource, ...]`、`ResolvedKnowledgeManifest.sources: tuple[ResolvedKnowledgeSource, ...]` (同じ長さ)。
  - `knowledge_manifest._parse_value` (:294〜) は `sources` が空なら `declared_scope` と `retrieval_result.status == "completed_empty"` を要求する。空 sources の manifest は completed_empty と同義。
  - argparse: `--coder-role` は `choices=("coder-v4-autonomous-k2",)`、`default=None` (:2574〜2576)。
- 既存テスト `orchestrator/tests/test_p3_s4_loop.py`:
  - `test_main_manifest_only_accepts_legacy_flattened_proposal` (:7205) は `_resolved_empty_knowledge_fixture` (sources 空) + `coder_role=None` で `main(argv) == 0` を要求。**条件付き必須化なら壊れない (sources 空)。**
  - `test_main_manifest_and_k2_role_accept_k2_wrapper` (:7241) は sources 空 + role K2 で main == 0。
  - `_run_main_with_actual_proposal_loader` (:7159〜) は `_resolve_knowledge_manifest_argument` / `exploration_campaign_layout` / `patchharness.assert_pinned_clean` / `drive_iteration` を monkeypatch し、実 `load_proposal_file` を通す。
  - `_resolved_knowledge_fixture(tmp_path, name=...)` (sources 非空、repo source) が同 file に既にある (`test_k2_load_proposal_rejects_out_of_range_knowledge_use` :7285〜 が使用)。
- baseline 焦点走 (login node bounded、`python3 tools/run_tests.py orchestrator/tests/test_p3_s4_loop.py -k "manifest or k2 or knowledge"`): **26 passed in 21.52s, rc=0** (2026-09-17 00:40 JST、HEAD 1042a1bc9)。
- DW-O09 pin 閉包: `p3_s4_loop.py` の path は B-4 `p3_b4_closed_critic.py` の projection closure (:635、live hash)、`p3_b4_raw_record_producer._projection_paths` (:991、同 live)、`p3_b4_wiring_probe._MODULE_RELATIVE_PATHS` (:64)、`.codex/role-adapters/coder-v4-autonomous-k2.json` と `orchestrator/codex_roles/manifest.json` の consumer path に現れる。いずれも path / live 比較で、凍結 sha を pin する台帳は path 検索 0 件。変更前 sha256 = `f5efa58a796d423d88168a4a2e243a3ffcc28074dc4bfd0b6add3982519208be` の repo 全体逆引きは背景で継続中 (段 4 までに結果を brief へ追記する)。
