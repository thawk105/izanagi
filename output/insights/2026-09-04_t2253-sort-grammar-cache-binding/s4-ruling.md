# [T-2253] 段 4 裁定 — plan v2 と変異の事前登録

裁定日 2026-09-04。入力: `s1-brief.md`、`verbatim/s2-plan.md`、`verbatim/s3-lens-a.md`、`verbatim/s3-lens-b.md`。
裁定 inbox 再走査: local main の先行 4 commit (rulings fragment・docs) に [T-2253]/D1548 の更新なし、編集面の file への変更なし。

## C0 親 brief の訂正 (erratum)

- E1 (lens B MF-8、real): 不変条件 2 が挙げた lock `...-3be89e0d` は oracle 導入前の歴史成果物で `sort_swo_oracle` key を持たない。
  現行の campaign ID は `p3-s5-sort-loop-s5-sort-autonomous-6f6a8cf1` (`test_p3_s4_loop_sort.py:967-969` が pin)。不変条件 2 は「`default_cfg()` の `search_config` を変えず、この ID を変えない」と読み替える。
- E2 (lens B MF-9、real): 「変わるのは非 stock の src_token と cache key だけ」は不足。非 stock の accepted candidate では `SourceEvidence.src_token`、
  `verification_variant`、WAL の variant id、`BUILD_START` payload の `src_token`、build admission receipt とその digest、cache path (legacy key / v2 digest) が変わる。
  受理集合 (verify / oracle / diff 検疫 / auditor) と campaign identity は不変。変異 spec と段 6 の期待差分はこの列挙で判定する。
- E3 (lens B nit、real): 段 5 の実経路は `resolve_evidence → _resolved_src_token`。`resolve()` / `src_token()` は通らない。
- E4 (lens B nit、real): 「他 producer と key が異なる」は非 stock に限る。stock/inert は双方 `"stock"` のままで、これは従来どおり同じ source binary。
- E5 (lens A、real): 「D1411 テスト群が署名を固定」は `run_campaign` / `evaluate` / `resolve_evidence` / `resolve` / `src_token` の 5 seam に限る。
- E6 (lens A must-fix 1、real、scope 外): `ORACLE_CONTRACT_ID` の checker hash は列挙 hash であって挙動の閉包ではない (`sort_swo_oracle.py:3020-3061` が明記)。
  P1 の「oracle 全体を覆う」は「手動 version bump を含む運用契約としての ID」に訂正する。束縛する値は identity・WAL が既に使う同じ値であり (D1411 の producer 1 本)、
  閉包の改善は sort_swo_oracle の契約設計の変更で campaign identity を動かすため、本 wave では実装せず裁定パッケージ候補へ送る (C4)。

## C1 所見の裁定

| # | 出所 | 所見 | 判定 | 採否 |
|---|---|---|---|---|
| A1 | lens A | 契約 ID は挙動の閉包でない | real | scope 外 → C4 (E6) |
| A2 | lens A | 同一意味でも ID が変わる | real / nit | 不採用 (性能上の miss のみ) |
| A3 | lens A | compiler identity の位置付け | 不確定 | C4 |
| A4-A6 | lens A | preimage 衝突・非 ASCII・既定 bytes | refuted | brief 維持 |
| A7 | lens A | `run_campaign` の三者 gate は仮想リスク向け新設 | real | **採用**: gate と `loop.py` への `sort_swo_oracle` import は実装しない (P3 の親裁定を撤回) |
| A8 | lens A | テスト計画に exact preimage / 拒否 / `verification_variant` 不変が無い | real / nit | 採用 (C2 T10, T11) |
| B1 | lens B | 一層だけ欠落すると偽停止、全層欠落で stale hit | real | 実装契約へ (全層一貫) |
| B2 | lens B | `resolve()` / `src_token()` は実経路外 | real / nit | **採用**: 両 seam は変更しない (局所適用) |
| B3 | lens B | 呼出し増加・duplicate 不整合 | refuted | 維持 |
| MF-1/2 | lens B | producer test と driver test の帰属重複、呼出し数の二重 | real | 採用 (C2 T1, T2) |
| MF-3 | lens B | gate test の単一理由化 | — | gate 不採用により不要 |
| MF-4 | lens B | signature test の帰属 | refuted | 採用 (変異には登録しない) |
| MF-5 | lens B | 相互排他 test の偽 kill | real | 採用: 相互排他は `_resolved_src_token` だけに置き、`current != baseline` の fixture で検査 |
| MF-6 | lens B | forwards test の分離 | refuted | 採用 (C2 T5) |
| MF-7 | lens B | `build_v2` wrapper と四出口が未検査 | real | 採用 (C2 T7, T8, T9) |
| MF-8/9 | lens B | 権威値は evidence token、preimage は実値から独立計算 | real | 採用 (C2 T10, T12) |
| MF-10 | lens B | None 不変は固定式と比較 | 不確定 | 採用 (C2 T11) |
| MF-11 | lens B | 四出口は legacy/v2 × hit/fresh | real | 採用 (C2 T8) |
| P4/P5/P6 | 両レンズ | scope 外の帰結 | real | scope 外を支持。P6 の `s1_direct_comparison` は C4 へ |

## C2 plan v2 (確定仕様。実装子はこれに従う)

### 変更する file

1. `orchestrator/campaign/p3_s4_loop_sort.py`
   - 新設 `_require_sort_oracle_contract(cfg: CampaignConfig) -> str`: `cfg.search_config.get("sort_swo_oracle")` が exact `str` で
     `sort_swo_oracle.ORACLE_CONTRACT_ID` と完全一致するときだけその値を返し、それ以外 (欠落・非 str・空・別値) は `ValueError`。写し元 `p3_s4_loop.py` `_require_backoff_grammar_version`。
   - `run_one_iteration()` で `ident.bind_admission_policy` より前に 1 回だけ呼ぶ (写し元 `p3_s4_loop.py:1451`)。
   - 唯一の `run_campaign(...)` 呼出し (`:397-401`) に `sort_oracle_contract_id=sort_oracle_contract_id` を足す。呼出しを増やさない。
   - `default_cfg()` と `search_config` は変えない。
2. `orchestrator/campaign/loop.py`
   - `run_campaign` の keyword-only 部へ `sort_oracle_contract_id: Optional[str] = None` (写し元 `:256`)。
   - 非 None のときだけ `source_options` (`:477-484`) と `evaluate_options` (`:558-561`) へ同名 key。
   - **入口 gate・`sort_swo_oracle` の import は足さない** (A7)。`loop.py:336-349` の backoff gate は 1 行も変えない。
3. `orchestrator/campaign/pipeline.py`
   - `evaluate` (`:1818`) と `_prepare_evaluation_core` (`:902`) の keyword-only 部へ同名引数、`evaluate` から素通し (`:1870`)。
   - 非 None のときだけ `source_options` (`:1090-1098`)、`common` (`:1252-1253`)、`build_options` (`:1262-1272`) へ同名 key。
4. `orchestrator/campaign/source_digest.py`
   - 新設 `_bind_sort_oracle_contract_id(raw_digest: str, sort_oracle_contract_id: Optional[str]) -> str`:
     None → `raw_digest`。非 None は `type(...) is str`・非空・ASCII のみ・`\0` を含まない、を満たさなければ `ValueError`。
     preimage は exact bytes `b"sort-src-token/v1\0contract=" + id.encode("ascii") + b"\0source=" + raw_digest.encode("ascii")` の SHA-256 hexdigest。写し元 `:2177-2193`。
   - `_resolved_src_token(current, baseline_digest, backoff_grammar_version, *, sort_oracle_contract_id=None)`: 既存 3 位置引数を保つ。
     両方非 None → `ValueError`。`current == baseline_digest` → `STOCK`。sort 非 None → sort binder。それ以外 → 既存 backoff binder。
   - `resolve_evidence` (`:2294-2323`) に同名 keyword-only 引数を足し `_resolved_src_token` へ渡す。
   - **`resolve()` と `src_token()` は変更しない** (B2)。`SourceEvidence` の schema/field は増やさない。
5. `orchestrator/campaign/buildcache.py`
   - `_build_v2_impl` (`:2254`)、`build_v2` (`:2945`)、`build` (`:3104`)、`_recheck_source_evidence` (`:3311`) の keyword-only 部へ同名引数。
   - `build_v2` の `common` へ非 None のときだけ (`:3008-3009`)。
   - 四出口 (v2 hit `:2594-2598`、v2 fresh `:2836-2840`、legacy `:3176-3180`、legacy `:3241-3245`) から `_recheck_source_evidence(..., sort_oracle_contract_id=...)`。
   - `_recheck_source_evidence` の `source_options` へ非 None のときだけ (`:3320-3323`)。
   - `cache_key` (`:624-642`) と `_v2_identity` (`:1295-1324`) は変更しない。鍵の権威値は両 API とも `source_evidence.src_token` (lens B 実測: legacy `:3128-3139`、v2 `:2342-2344, 2527-2531`)。

### 変更しない面

`p3_s4_loop.py`、`sort_swo_oracle.py`、`wal.py`、`s1_direct_comparison.py`、`s6_sort_sweep.py`、`diffq_variant_id` / `record_diff_reject`、`default_cfg`、既存テストの期待値。

### テスト (`orchestrator/tests/test_p3_s4_loop_sort.py` へ追加。既存テストは変更しない)

parametrize id は ASCII 英小文字・数字・ハイフンだけ。契約 ID は必ず `sort_swo_oracle.ORACLE_CONTRACT_ID` を import した実値を使う。

- T1 `test_require_sort_oracle_contract_accepts_only_running_contract`: `_require_sort_oracle_contract` が `default_cfg()` で実値を返し、key 欠落 / None / int / 空文字 / 別 str で `ValueError`。
  定数の一致は既存 `test_default_cfg_wires_s2_verify` が担当するので、ここでは再検査しない (MF-1)。
- T2 `test_sort_driver_forwards_producer_contract_to_run_campaign`: `_require_sort_oracle_contract` を sentinel を返す fake に差し替え、`run_one_iteration` の既存 1 呼出しの kwargs `sort_oracle_contract_id` が sentinel と同一であることだけを見る。呼出し数は見ない (MF-2、inventory `test_campaign.py:5355` の担当)。
- T3 `test_sort_oracle_contract_call_seams_are_keyword_only_default_none`: `run_campaign`、`evaluate`、`_prepare_evaluation_core`、`resolve_evidence`、`build`、`build_v2`、`_build_v2_impl`、`_recheck_source_evidence` の新引数が keyword-only かつ既定 None。
- T4 `test_resolved_src_token_rejects_both_bindings`: `current != baseline` の fixture で backoff と sort を両方非 None → `ValueError`。片方だけなら各 binder。
- T5 `test_run_campaign_forwards_one_sort_contract_to_resolver_and_evaluate`: resolver を bound evidence を返す spy、evaluate を結果だけ返す spy にし、両 kwargs と evidence の同一性だけを見る (写し元 `test_p3_s4_loop.py:3457-3522`)。
- T6 `test_pipeline_forwards_one_sort_contract_to_resolver_and_selected_build_api`: legacy / v2 の各経路で resolver と選ばれた build API に同じ契約が届く (写し元 `:3525-3643`)。反対側 API の非呼出しは検査しない。
- T7 `test_build_v2_wrapper_forwards_sort_contract_to_impl`: `_build_v2_impl` を spy し、`build_v2` から契約 1 件が届く。
- T8 `test_build_exits_recheck_with_sort_contract[legacy-fresh|legacy-hit|v2-fresh|v2-hit]`: `_recheck_source_evidence` を spy し、各 node で `built_fresh` と契約の 2 点だけを理由にする (MF-11)。
- T9 `test_recheck_source_evidence_forwards_sort_contract_to_resolver`: `resolve_evidence` spy が契約を受け取る。
- T10 `test_sort_binder_exact_preimage_and_rejections`: 固定 raw digest と実 `ORACLE_CONTRACT_ID` に対し期待 hash を上記 exact bytes から独立計算して一致。bound != raw、bound != `_bind_backoff_grammar_version(raw, 1)`。非 str / 空 / `\0` 入り / 非 ASCII は `ValueError`。
- T11 `test_sort_contract_none_preserves_preexisting_identities`: 省略と明示 None の両方で、非 stock raw token・`"stock"`・`verification_variant`・legacy key (`cache_key(..., src_token=raw, admission=...)` の独立計算)・v2 preimage の `src_token` field が固定式と一致 (MF-10)。
- T12 `test_bound_evidence_token_is_the_cache_authority`: `src_token=None` + bound evidence で legacy key / v2 digest が evidence token から作られ、raw token を明示して evidence と食い違わせると cache open 前に拒否される (MF-8)。
- T13 `test_bound_sort_requests_never_open_raw_token_entries`: raw token で置いた legacy / v2 entry を bound request が開かず、旧 entry を壊さない (写し元 `:3708-3842`)。

### 受入・実測

- 焦点走 (親、login node): `test_p3_s4_loop_sort.py`、`test_p3_s4_loop.py`、`test_buildcache_v2.py`、`test_build_site_gate.py`、`test_s6_sort_sweep.py`、`test_campaign.py`。
- 受入全走: 記録 commit 後の最終 tip に対し `tools/dev_wave_wait.py acceptance` で 1 回。

## C3 変異の事前登録 (実装前登録。exact の old/new bytes と期待 node は実装後に親が probe で確定する)

全件 `--runner-mode dispatch`、runner argv に `--force-dispatch`。`loop.py` / `pipeline.py` の変異は contract-loader drift の冗長 gate を伴うので較正走で `--deselect` 集合を実測する (DW-M03)。

| id | file | 変異の意図 | 単一理由の owner | 期待 |
|---|---|---|---|---|
| M1 | p3_s4_loop_sort.py | `_require_sort_oracle_contract` が `ORACLE_CONTRACT_ID` との一致検査を外す (宣言値をそのまま返す) | T1 | KILLED |
| M2 | p3_s4_loop_sort.py | `run_campaign` 呼出しから `sort_oracle_contract_id=` を落とす | T2 | KILLED |
| M3 | loop.py | `source_options` へ契約を入れない | T5 | KILLED (+冗長 gate) |
| M4 | loop.py | `evaluate_options` へ契約を入れない | T5 | KILLED (+冗長 gate) |
| M5 | pipeline.py | pre-build `source_options` へ入れない | T6 | KILLED (+冗長 gate) |
| M6 | pipeline.py | legacy `build_options` へ入れない | T6 (legacy node) | KILLED (+冗長 gate) |
| M7 | pipeline.py | v2 `common` へ入れない | T6 (v2 node) | KILLED (+冗長 gate) |
| M8 | source_digest.py | sort binder が非 None でも `raw_digest` を返す | T10 (bound != raw) | KILLED |
| M9 | source_digest.py | preimage の domain を `sort-src-token/v2` へ変える | T10 (exact preimage) | KILLED |
| M10 | source_digest.py | `_resolved_src_token` の相互排他を外す | T4 | KILLED |
| M11 | buildcache.py | `build_v2` の `common` へ入れない | T7 | KILLED |
| M12 | buildcache.py | v2 hit 出口の `_recheck_source_evidence` 呼出しから契約を落とす | T8[v2-hit] | KILLED |
| M13 | buildcache.py | legacy fresh 出口から契約を落とす | T8[legacy-fresh] | KILLED |
| M14 | source_digest.py | 等価変異 (生成 bytes が変わらない書換え、例: 一時変数の導入) | なし | SURVIVED (harness 正例) |

## C4 scope 外 / 裁定パッケージ候補 (実装しない)

- C-ID-CLOSURE: `ORACLE_CONTRACT_ID` の権威境界 — 列挙 hash を維持し列挙外変更では `CONTRACT_VERSION` の手動 bump を運用正本にするか、top-level 判定・timeout 定数まで manifest へ含めて現行 ID と campaign ID の移行を受け入れるか (lens A)。
- ORACLE-RUNTIME: compiler path/version を realized contract に含めるか、receipt の環境証跡に留めるか (lens A)。
- P6-S1-BINDING: `s1_direct_comparison.py` は config に契約 ID を持つが `resolve()` / `evaluate()` へ渡さない同種の分断が残る。独立の後続 task として切る (lens B)。
- P4-PER-ATTEMPT: `BUILD_START` 単体から平文契約 ID を復元できない。per-attempt 監査が要るなら別裁定 (lens B)。

## C5 DW-G05 (放置時の成果物影響、再掲)

sort 軸で oracle 契約が改版されても、同じ source digest の build が cache hit して旧契約下の binary を再利用し、certified 値がその binary で測られる。
