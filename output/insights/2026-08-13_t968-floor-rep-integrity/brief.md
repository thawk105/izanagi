# [T-968] brief — 床値 session の rep 完備性 (rc + counter) を記録・検査する

## scope
床値 campaign (`orchestrator/campaign/s8b_floor_campaign.py` + `s8b_floor_stats.py` +
`orchestrator/calibrator/runner.py`) に、**rep ごとの rc と perf counter 完備性**を記録し、
不備のある rep を含む session が有効 throughput として median に入らないようにする。
新しい除外区分を追加する形で行う (ユーザー裁定 2026-08-13 第 7 束)。

**scope 外 (触らない):** [T-967] 測定条件 perf の有無の伝播 (official 化 wave 同梱と裁定済み)。
`s8b_oracle_*` / silo ladder / T-810 測定装置。凍結 artifact の bytes 変更・再 seal。

## 確定済みユーザー裁定
- T-968 = **採用 (除外区分の追加で)**。控え: `rulings-inbox/2026-08-13-rulings8-batch.md`「perf 系 4 件」。
- 既知赤 1 件 (`test_s8c_preregistration_invariant.py::test_candidate_freeze_matches_contract_and_generation_chain`)
  のみなら land 可。控え: `rulings-inbox/2026-08-13-known-red-octopus-merge.md`。

## 実測した現状 (段 1 の一次資料)
1. `runner.py:461` の `run_once` は floor 経路では `strict_returncode=False`、`rep_returncodes=None`、
   `require_complete_metrics=False` で呼ばれる (`s8b_floor_campaign.py:3418-3429` が
   `measure_point` へこれらを渡さない)。したがって **rep の rc は捨てられ、counter 欠落も検査されない**。
2. `run_once` は rc を見ずに `parse_bench_stdout` が成功すれば metrics を返す (`runner.py:383-397`)。
   perf が壊れて counters が全 None でも `tps` は `pt.throughputs` に積まれる (`runner.py:485-486`)。
3. `_count_exec_failures` は note 文字列 `"N/M reps failed to execute"` の正規表現だけを見る
   (`s8b_floor_campaign.py:1058-1069`)。rc 異常・counter 欠落は note を出さないので `exec_failures=0`。
4. 結果、`len(throughputs)==reps` かつ全値有限正なら `assess_session` は有効と判定し
   (`s8b_floor_stats.py:142-152`)、session median が cell へ入る。**これが T-968 の穴**。
5. 既存 seam は存在する — `measure_point(require_all_reps=, require_complete_metrics=,
   rep_returncodes=)` (`runner.py:409-412`)。ただし前 2 者は `RuntimeError` を投げて
   **測定点全体を落とす** ため、現行 precedence では `launch_failure` に化け原因が潰れる
   (`s8b_floor_campaign.py:2428-2431`)。新区分が要るのはここ。

## (P1) 親の provisional 裁定であり攻撃対象 — 裁定の前提を覆しうる新事実
**`allowed_excluded_reasons` の 4 理由表は、ユーザーが seal した凍結 artifact の中身である。**
- `output/s8b-freeze/floor_protocol.json` (774 bytes, sha256 `261cec1c…`) が
  `allowed_excluded_reasons: [competing_process, launch_failure, nonfinite_or_partial_output,
  performance_anomaly]` を持つ。`FROZEN_MANIFEST` の HELD 側に登録済み
  (`orchestrator/tests/test_frozen_artifacts.py:48,97,123`)。bytes 照合は現在 hold 中だが、
  **`s8b_floor_contract.validate_protocol` の `_pinned` 相当検査 (同 file:202) は hold ではない**。
- したがって `s8b_floor_contract._APPROVED_REASONS` に 5 番目を足すと、seal 済み protocol (4 理由) が
  `validate_protocol` に**拒否され、床値 campaign が起動できなくなる**。単一源設計により
  `s8b_floor_stats.ALLOWED_EXCLUDED_REASONS` → `s8b_approved.APPROVED_REASONS` →
  builder 出力 (`s8b_floor_campaign.py:560`) まで波及する。
- **(P1) 親の provisional 裁定: 「除外区分の追加」は protocol document の
  `allowed_excluded_reasons` を変えない形で実装する。** 凍結 bytes と再 seal (人間手番) には触らない。
  実装候補は段 2 で file:line 粒度に落とす:
  - (B1) session 理由表 (`ALLOWED_EXCLUDED_REASONS`) にだけ 5 番目を足し、protocol 側の
    approved 4 理由 (`_APPROVED_REASONS`) と意図的に分離する。単一源が割れるのが弱点。
  - (B2) **rep 階層に新区分を置く** (`exec_failures` の兄弟、例: 完備性違反 rep 数)。違反 rep の tps は
    throughputs に積まない → `len != reps` → 既存 `nonfinite_or_partial_output` で session 全体が無効。
    凍結表も単一源も無傷。「区分の追加」は rep 階層で満たす。
  親は現時点で **(B2) を推す**が、段 3 の敵対レンズが (B2) を「rep を黙って捨てる抜け道」と攻撃しうる。
  段 4 で確定する。

## (P2) 記録面の schema 影響
新しい rep 完備性の記録は `SessionRecord` / journal / result の session 行に載る。
`_REQUIRED_SESSION` (`s8b_floor_stats.py:406-408`) は必須キーの閉集合であり、既存 artifact との
互換 (追加キーを必須にすると過去 journal の resume が壊れる) を段 2 で確認する。
producer が書くのは run_dir 配下の `journal.jsonl` / `manifest.json` / `result.json` / `result.md` /
`launch_certificate.json` のみで、いずれも凍結 artifact ではない (DW-O10 棚卸し)。

## 不変条件 (緩めない)
- **規律 2:** 除外条件は「rc == 0」と「counter 完備」という機械的事実だけに基づく。
  throughput・median・性能値を条件に入れる実装は不採用。
- **fail-closed:** 完備性が判定不能な場合 (rc を採れない、counters が判定できない) は有効側に倒さない。
- **positive control 必須:** 壊れた rep (rc != 0 / counter 欠落) の tps が median に混入したら
  **赤になる**テストを足す。緑のまま通る「恒真な保証」を作らない。
- 凍結 artifact の bytes を変えない。再 seal しない。

## 成果物の形 (DW-G05: 実装しない場合の成果物影響)
実装しないと、床値 (certified 選択の分母) が **perf 破損 rep 込みの median** で確定しうる。
すなわち selected/tie の判定値そのものが汚染され、レポートの床値と proof chain の
throughput が実測でない値を指す。これは受理集合を直接動かす。

## 並列分割方針
- 段 2: codex read-only 1 本 (plan、file:line 粒度、(P1) の 3 案を比較して 1 案へ)。
- 段 3: codex read-only 2 本 (レンズ A = 規律 2 抜け道 / 凍結・単一源破壊、
  レンズ B = 完備性判定の穴・fail-open・positive control の恒真性)。
- 段 5: codex author 1 本 (実装面は D95 により Codex author が書く。編集面が
  runner.py / floor_campaign.py / floor_stats.py + tests に集中するため分割しない)。
- 段 6: 敵対レビュー 2 本 + fix + 変異 matrix + 受入全走。
