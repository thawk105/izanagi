# [T-2253] 段 1 brief — 文法の版の cache 束縛を sort 軸へ局所適用する

基準 commit: df8b9d1e7d30cfd3ffee42c186bf4aedacef6489 (local main と一致、2026-09-04)。

## scope

- 段 5 sort loop (`orchestrator/campaign/p3_s4_loop_sort.py`) が `run_campaign` を呼ぶとき、campaign 由来の契約 ID
  (`cfg.search_config["sort_swo_oracle"]`、値は `sort_swo_oracle.ORACLE_CONTRACT_ID`) を **keyword-only の明示引数**で渡し、
  `loop.run_campaign` → `pipeline.evaluate` / `_prepare_evaluation_core` → `source_digest.resolve_evidence` / `resolve` / `src_token`
  → 非 stock `src_token` のドメイン分離 hash → `buildcache.cache_key` の `|src=` と `buildcache._recheck_source_evidence` まで届かせる。
  既定は `None` で、渡さない campaign の bytes (variant id・cache key) は 1 byte も動かない (D1411 と同じ形)。
- 一般化しない。backoff の `backoff_grammar_version` 経路は 1 行も緩めず、他の軸・producer へは広げない (D1548)。
- 本題の実装だけ。仮想リスク向けの gate・検査・台帳・一般化は scope 外 (command 引数、DW-G05)。

## 確定済みユーザー裁定 (逐語は job dir `input/`)

- D1548: sort 軸に局所適用、族一般化なし、束縛は D1411 と同じ campaign 由来の明示引数。
- D1411: path 判定でなく keyword-only 引数、既定 None、既定経路の bytes 不変、同じ値が identity・WAL・source・cache へ渡る (producer 1 本)。
- D901 条項 2: 文法の版を identity・WAL・cache へ束縛する。D1412: 拒否候補 (diffq) の token は scope 外。

## DW-G05 (放置時の成果物影響)

sort 軸で oracle 契約 (IR 文法・corpus・checker) を改版しても、同じ source digest の build が cache hit して旧契約下の binary を再利用し、
certified 値がその binary で測られる。campaign.lock / WAL が持つ契約 ID と、実際に測った binary の対応が切れる。

## 不変条件

1. 版を渡さない campaign (backoff sweep、P2-4 sweep、backoff loop、trigger loop、s1 direct comparison) の variant id・cache key は不変。
2. sort campaign の `search_config` は変えない → campaign_id 不変。既存 lock `output/campaigns/p3-s5-sort-loop-s5-sort-autonomous-3be89e0d/campaign.lock` の identity 不変。
3. 規律 2: 受理集合 (verify / oracle / diff 検疫 / auditor) を変えない。変わるのは sort 軸の非 stock src_token と cache key だけ。
4. `test_campaign.py:5355` の pin (`p3_s4_loop_sort.py` の `run_campaign` 呼出し数 = 1) を守る。
5. 実装子は commit しない、docs を書かない。commit・記録は親。

## 割れうる前提 (親の provisional 裁定・攻撃対象)

- (P1) 束縛する値は `ORACLE_CONTRACT_ID` (str) とし、`SORT_IR_GRAMMAR_VERSION` (int) ではない。理由: identity・WAL が持つ値と同一にして producer を 1 本にする (D1411 の理由)。
- (P2) 既存の int 引数 `backoff_grammar_version` を流用せず、並列の keyword-only 引数 (例 `sort_oracle_contract_id: Optional[str] = None`) を各 seam に足し、
  `source_digest` の binder は別ドメイン preimage (`sort-src-token/v1\0contract=<id>\0source=<digest>`) にする。両方非 None は ValueError。
- (P3) `run_campaign` 入口で `cfg.search_config["sort_swo_oracle"]` と引数と実行中の `ORACLE_CONTRACT_ID` の exact 一致を要求する (loop.py:336-349 と同型)。
  `p3_s4_loop_sort.py` 側には `_require_sort_oracle_contract(cfg)` (p3_s4_loop.py `_require_backoff_grammar_version` と同型) を置き、run_campaign 呼出しの引数はそこから取る。
- (P4) WAL build_start payload への契約 ID 再掲と `wal.validate_*_bindings` の sort 版は scope 外 (D1548: sort は契約 ID 経由で identity と WAL に届いている)。
- (P5) `diffq_variant_id` / `record_diff_reject` への契約束縛は scope 外 (D1412 と同じ理由)。
- (P6) `s1_direct_comparison.py:481` / `s6_sort_sweep.py` の sort 系 producer は scope 外 (局所適用 = 段 5 sort loop)。cache_root を共有しても key が違うだけで偽 hit は生じない。

## 成果物の形と分割

- コード + テスト (実装子 1 本、Codex `role=author`、D95)。producer/consumer 契約が run_campaign → evaluate → source_digest → buildcache を跨ぐので分割しない。
- 段 6: 敵対レビュー 2 本 + fix、変異 matrix (段 4 で事前登録)、受入全走 (`tools/dev_wave_wait.py acceptance`)。
- insight: 本 dir に段 2〜6 の逐語、裁定、変異 spec/集計。

## 変更面の実アンカー (親が HEAD で実測。10 commit の ff は docs / test_codex_reasoning_ab.py / insights のみで、下記 file は不変)

| file | 行 | 内容 |
|---|---|---|
| `orchestrator/campaign/loop.py` | 256 | `run_campaign(..., backoff_grammar_version: Optional[int] = None, ...)` keyword-only |
| 同 | 336-349 | campaign 宣言 / 引数 / 実行中 module の exact 一致 gate (P3 の写し元) |
| 同 | 477-484 | `source_options` → `source_digest.resolve_evidence` (skip 判定用 id) |
| 同 | 558-561 | `evaluate_options` → `pipeline.evaluate` |
| `orchestrator/campaign/pipeline.py` | 902 / 1818 / 1870 | `_prepare_evaluation_core` / `evaluate` の kw と素通し |
| 同 | 1090-1098 | `source_options` → `resolve_evidence` |
| 同 | 1252-1253 / 1262-1272 | `common` (build_v2) / `build_options` (legacy build) |
| `orchestrator/campaign/source_digest.py` | 2177-2193 | `_bind_backoff_grammar_version` (binder、preimage `backoff-src-token/v1`) |
| 同 | 2198-2203 / 2206-2216 | `_resolved_src_token` / `src_token` |
| 同 | 2294-2323 / 2342-2360 | `resolve_evidence` / `resolve` |
| `orchestrator/campaign/buildcache.py` | 624-642 | `cache_key` (`|src=<src_token>`、stock は省略) |
| 同 | 2254 / 2945 / 3104 | `_build_v2_impl` / `build_v2` / `build` の kw |
| 同 | 2594-2598 / 2836-2840 / 3008-3009 / 3179 / 3244 | 素通し |
| 同 | 3308-3323 | `_recheck_source_evidence` (build 出口の再照合) |
| `orchestrator/campaign/p3_s4_loop_sort.py` | 298-305 | `default_cfg` の `search_config` (`"sort_swo_oracle": ORACLE_CONTRACT_ID`) — 変えない |
| 同 | 396-400 | `run_campaign(...)` 唯一の呼出し (ここに引数を足す) |
| 同 | 222-226 | oracle 結果の `contract_id` exact 検査 (既存の同型) |
| `orchestrator/campaign/p3_s4_loop.py` | `_require_backoff_grammar_version` / 1529-1537 | 写し元 (単一 producer 関数と run_campaign 呼出し) |
| `orchestrator/campaign/sort_swo_oracle.py` | 51-53 / 3126-3133 | `GRAMMAR_VERSION` / `SORT_IR_GRAMMAR_VERSION` / `ORACLE_CONTRACT_ID` |
| `orchestrator/campaign/wal.py` | 1595-1629 | backoff の lock 由来 version と build_start の照合 (P4、触らない) |
| `orchestrator/tests/test_p3_s4_loop.py` | 3394-3460 以降 | D1411 のテスト群 (不変。sort 版を `test_p3_s4_loop_sort.py` へ同型で足す) |
| `orchestrator/tests/test_p3_s4_loop_sort.py` | 774-775 | `search_config["sort_swo_oracle"] == ORACLE_CONTRACT_ID` |
| `orchestrator/tests/test_campaign.py` | 5355 | `p3_s4_loop_sort.py` の `run_campaign` 呼出し数 pin |

## 受入・実測環境

- 焦点テストは login node (pegasus02、負荷を見て) で親が実走。受入全走と変異 harness は `tools/dev_wave_wait.py` 経由で計算ノードへ投入。
- 実装子は pytest を実走できない可能性が高い (Pegasus dispatch)。「実装済み・未実走」と申告させ、緑は親の実走だけを数える。

## 編集面重複 (起動時検査)

- `worktree-dev-wave-t2145-sort-oracle-ir`: main の祖先 (着地済み)、差分ゼロ、dirt ゼロ → 重複なし。carry が言う「逆向き推奨の未 land fragment」は fold 済み。
- `worktree-dev-wave-t733-source-closure-transitive`: `artifact_admission.py` / `campaign_lock.py` / `contract_loader_binding.py` + tests → 本 wave の変更面と交差なし。
