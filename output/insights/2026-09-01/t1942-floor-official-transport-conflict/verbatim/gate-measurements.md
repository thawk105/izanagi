# [T-1942] 投入前ゲートの棚卸し (親の実測、2026-09-01 18:12 JST)

official 床値走行の前に立ちはだかるものを、実測で 3 つに分けた。

## G-A — s8b compiler input manifest の赤 (ユーザー指示のゲート)

- 2026-08-29 に「主経路は未解消・赤は無条件」と実測されていた
  (`output/insights/2026-08-29_t1942-floor-gate-compiler-input/README.md`)。
- 消える根は 2 クラス。第 1 = build cache の staging (`.staging-<PID>-<nonce>/_deps/masstree-src/*.hh`
  31 件)、第 2 = job 専用作業領域 (`/scr/0_<jobid>/...` 7 件)。
- 現行 main は manifest schema v3。根クラスは snapshot / fetchcontent-masstree / filesystem /
  dependency-prefix (`s8b_compiler_input.py:44-45`)。第 1 クラスは `fetchcontent-masstree`、
  第 2 クラスは `dependency-prefix` で覆われる形になっている。
- 受領書発行側の再束縛配線は `s8b_floor_campaign.py:4392-4398` と
  `s8b_binary_admission.py:232-244` に実在する。
- `dependency_binding` は `production_floor_path` かつ `sort_best` セルがあるとき非 None
  (`s8b_floor_campaign.py:4013, 4057-4096`)。official の 12 セルには `sort_best` が含まれるので
  条件は成り立つ。
- **落ちた job 952631 の manifest は schema `s8b-compiler-input/v1`** で、588 件すべてが
  root タグ無しの絶対 path。v1 は「厳格な read-only 互換形式で移行も緩和もしない」と
  module docstring が明記しているので、**旧 manifest の再走では現行経路の生死を測れない。**
- 状態: **未実測。** 実測手段は段 2 プランが設計する。上記はすべてコード読解である。

## G-B — D811 の着手条件 (使い捨て入場鍵)

- 共有 admission root: `<git common dir>/izanagi/s8b-holdout-admission-v1/`。
- consumed 228 件 = floor_campaign 96 件 (campaign_run_id `20260824T205358Z-2c8cf9be`、
  12 セルへ均等に 8 件ずつ) + n_pilot 132 件 (`t1142-run-1`)。claims 36 件、receipts 0 件。
- budget key = `(freeze_holdout_key, configuration_id)` (`s8b_attempt_profile.py:405-408`)。
- `floor-attempt-registries/` の登録簿は 1 本だけで、`max_consumptions_per_budget_key = 10`、
  193 event (freeze 1 + start 96 + pre-observation-seal 96)。
  **ただしその登録簿の holdout key は `rr23` / `rr79`、`execution_uuid` は
  `campaign-fixture-execution`** であり、実 holdout `rr20` / `rr80` ではない。
  `rr23` / `rr79` は `orchestrator/tests/test_holdout_observation.py` などの fixture 値である。
  → **テスト fixture が共有耐久領域へ書いたもので、実 pilot の 96 件を数えている登録簿は無い。**
- 親の推論: official 走行の (freeze, protocol) 対に対する枠は 0 から始まる見込み。
  **推論であって実測ではない。** 段 3 レンズ B に検査させる。
- 副産物の所見: テストが共有耐久領域へ書いている。scope 外なので裁定パッケージへ回す候補。

## G-C — D1161 の予算承認 (人間手番)

- D1161 (2026-08-27 ユーザー裁定): 「床値 official 経路の残る閂は
  `output/s8b-freeze-budget-approvals/g1.json` の人間による承認だけ。AI は自分を承認者にしない」。
- 実測: `output/s8b-freeze-budget-approvals/` は**存在しない**。
  `s8b_holdout_freeze.py:52` の `BUDGET_APPROVAL_SHA256` は `None` のまま。
- 消費側は `build_v2_g1_candidate(*, floor_result_path, budget_path, ...)`
  (`s8b_holdout_freeze.py:2013-2040`)。**official 走行の結果 `floor_result_path` を入力に取る。**
- → **承認は走行の前提ではなく、走行結果を新しい freeze へ昇格させる段の閂である。**
  D589 (2026-08-20) が挙げた v2 candidate 生成の 3 条件のうち (c) が「official result.json 不在」で
  あることとも整合する。
- 結論: **G-C は official 走行を止めない。** 走行後にユーザー手番として残る。

## 順序

1. D926 実装 (この wave の実装面)
2. G-A / G-B を実測 → 両方緑なら投入
3. official campaign 走行 (10 時間) → 床値
4. AI が予算承認文書を起草 → **ユーザー承認** (G-C)
5. v2 g1 candidate → 新 freeze

## G-A の連鎖 (親の読解、2026-09-01 18:20 JST)

`orchestrator/campaign/buildcache.py:2639-2666` が要である。

- `effective_root = _masstree_source_root_from_cmake_cache(staging)` — staging の CMakeCache が
  記録する masstree の source root。第 1 クラスの消える path
  (`.staging-<PID>-<nonce>/_deps/masstree-src/*.hh`) はこの根の下にある。
- `validation_root = canonical_compiler_input_masstree_root or effective_root` —
  **canonical が渡っていれば、検証はそちらを根にする。**
- 床値 campaign は `dependency_binding is not None` のとき
  `build_kwargs["current_compiler_input_masstree_root"] = str(dependency_binding.source_root)`
  を渡す (`s8b_floor_campaign.py:4217-4223`)。この source_root は run 単位で用意され、
  staging 破棄後も生き残る。
- 受領書発行時も同じ根を渡す (`s8b_floor_campaign.py:4392-4394`)。

したがって、床値 campaign の構成では第 1 クラスの根が staging 破棄後も解決できる。
**ただし再束縛先の bytes が一致することが条件**である (`_hash_relative_nofollow` が
現在の根の下で再 hash して記録値と比較する)。

**落ちた job 952631 は床値 campaign ではなく別 wave の probe** であり、canonical 根が
渡っていたかは未確認である。つまり 2026-08-29 の「無条件赤」は、床値 campaign の構成でも
同じとは限らない。この点は段 3 レンズ B に検査させる。

## 18 名 seam 集合 (D926 が「変更しない」と名指し)

`orchestrator/campaign/s8b_floor_contract.py:42-50` に実在し、ちょうど 18 件:
measure_fn, probe_fn, sleep_fn, monotonic_fn, prepare_fn, now_fn, host_provenance_fn,
process_identity_fn, execution_receipt_fn, build_fn, repo_root, fetchcontent_base_dir,
after_certificate_issued_fn, durable_root_policy, _floor_preflight_fn, perf_preflight_fn,
_holdout_repo_root, _holdout_signature_source。

## G-D — staged transport と official 適格性の構造的矛盾 (親の実測、2026-09-01 18:45 JST)

段 2 プランが「実在する blocker」として報告し、親が独立に裏取りした。

- `tools/pegasus/floor_campaign.sh:1231` は `--fetchcontent-base-dir "$FETCHCONTENT_STAGING"` を
  **無条件で** driver へ渡す (`FETCHCONTENT_STAGING` は同 715 行、`$TMPDIR/izanagi-floor-fetchcontent`)。
  この配線は 2026-08-22 の `1488fe683` ([T-1461]) が入れた。
- `s8b_floor_campaign.py:6891` の seam 分類は `fetchcontent_base_dir is not None` を非既定 seam と
  数える。18 名集合の一員である (`s8b_floor_contract.py:42-50`)。
- `s8b_floor_campaign.py:6990-6994` は official mode で非既定 seam があれば
  **承認 gate の手前で**拒否する。
- `_derive_refreeze_eligibility` (`同:6906-6919`) は
  「official かつ resume なし かつ 非既定 seam ゼロ」だけを適格にする。
- したがって **正規 job script 経由の走行は、pilot でも official でも
  `eligible_for_refreeze` になれない。** official に至っては起動すらできない。
- 既定 (legacy) 経路 = `fetchcontent_base_dir=None` は `_canonical_floor_fetchcontent_base` が
  `TMPDIR` に新しい base を作り (`同:2997-3048`)、`_prepare_floor_oracle_dependency` が
  `masstree_source_dir` 等を渡さずに `prepare_masstree_fetchcontent` を呼ぶ (`同:3202-3247`) —
  つまり FetchContent が外部から取得する形になる。
- `docs/pegasus-runbook.md:811-825` は「計算ノードは直結の外部 network 不可 (proxy はあるが
  FetchContent が honor するかは未確定)」「依存ソースはログインノードで pinned staging し
  `FETCHCONTENT_SOURCE_DIR_*` で渡す運用を維持する」と定めている。

**D926 を実装してもこの矛盾は解けない。** 解くには (i) staged transport を外して legacy 経路が
実機で通ることを実測する、(ii) 18 名集合か適格性の判定式を変える、のどちらかが要る。
(ii) は D926 が明示的に禁じている。(i) は runbook の運用方針に反し、offline 条件で通る根拠がない。

段 3 の 2 レンズの判定を待って段 4 で裁定する。

### G-D の由来 (親の実測)

`1488fe683` ([T-1461]、2026-08-22) が **1 つの commit で**
(a) `floor_campaign.sh` へ staged transport を無条件配線し、
(b) `fetchcontent_base_dir` を `REFREEZE_DISQUALIFYING_SEAM_NAMES` へ登録した。
commit message は両方を明記しており、`DW-G01` の生死実験で offline build 成功も確認している。
**しかし official が起動不能になること・refreeze 不適格が確定することは記録にない。**
`git log -S'"fetchcontent_base_dir"' -- s8b_floor_contract.py` の hit はこの 1 commit だけである。
