# [T-1942] 床値 official 実測の投入前ゲート再実測 — 塞いでいるのは compiler input ではなく transport と適格性の矛盾である

- 日付: 2026-09-01 (JST)
- 対象 commit: `08a17b3b3` (wave base、worktree `dev-wave-t1942-floor-gate-recheck`)。
  記録時点で local main は `834efe61f` まで進み、本 wave はそれを取り込んでいる。
- 目的: [T-2027] が着地した後の投入前ゲートを実測し直し、緑なら現行 Pegasus・workload 別の
  床値を official 経路で実測する。
- 結論: **投入していない。実装もしていない。** ユーザー指示の停止条件が成立した。
  2026-08-29 に塞ぎ要因と特定されていた compiler input の赤とは**別の**、より上流の構造的矛盾が
  official 経路を塞いでいる。迂回すると正しさ防壁 (規律 2) を緩めることになるため、
  記録して停止した。

---

## 1. 何を測ったか

| # | 測ったこと | 結果 |
|---|---|---|
| 1 | 落ちた job 952631 の manifest の schema | **`s8b-compiler-input/v1`** (root タグ 0 件) |
| 2 | 現行 main の manifest schema と根クラス | v3、4 クラス (両消失クラスを覆う形) |
| 3 | 使い捨て入場鍵の現況と、fresh 予約の実際の衝突対象 | 旧 marker は衝突対象外。判定対象は別 |
| 4 | D1161 の予算承認は走行の前提か | **前提ではない。走行後の段の閂** |
| 5 | official 経路が起動できるか | **できない。transport と適格性が矛盾している** |
| 6 | 現行 Pegasus の workload 別 between-run 床値の在否 | **read-heavy だけあり、他 2 つが無い** |

---

## 2. G-A — compiler input の赤 (測定 1・2)

2026-08-29 の一次資料
(`output/insights/2026-08-29_t1942-floor-gate-compiler-input/README.md`) は、落ちた job 952631 が
残した build cache の `completion.json` を現行 validator へ通して赤を再現し、「主経路は無条件で
未解消」と結論していた。

**その再走は現行経路の生死を測っていない。** 実測したところ、その manifest は
schema `s8b-compiler-input/v1` であり、588 件の入力すべてが root タグを持たない
(549 件が絶対 path、39 件が snapshot 相対)。`s8b_compiler_input.py` の module docstring は
「v1 と v2 は厳格な read-only 互換形式であり、その入力は移行も緩和もしない」と明記している。
つまり v1 manifest は**設計として**赤のままであり、現行 v3 collector が同じ入力をどう扱うかとは
無関係である。

現行 main の v3 は根クラスを 4 つ持つ (`s8b_compiler_input.py:44-45`)。消える根の第 1 クラス
(build cache staging `.staging-<PID>-<nonce>/_deps/masstree-src/*.hh` 31 件) は
`fetchcontent-masstree`、第 2 クラス (`/scr/0_<jobid>/...` 7 件) は [T-2027] が入れた
`dependency-prefix` が覆う形になっている。

床値 campaign の構成では、再束縛先が staging 破棄後も生き残る連鎖が存在する。

- `buildcache.py:2639-2666` — `effective_root` は staging の CMakeCache が記録する masstree 根、
  `validation_root = canonical_compiler_input_masstree_root or effective_root`。
- `s8b_floor_campaign.py:4217-4223` — `dependency_binding` が非 None なら
  `current_compiler_input_masstree_root = dependency_binding.source_root` を渡す。
- `同:4392-4394` — 受領書発行時も同じ根を渡す。
- `同:4013, 4057` — `dependency_binding` は `prepare_fn is prepare_cell` かつ `sort_best` セルが
  あれば作られる。`s8b_floor_contract.py:674` は各 holdout に `sort_best` を必須としている。

**ただしこれはすべてコード読解であり、実測ではない。** 実測は行っていない。理由は §5 の矛盾により
official 経路そのものが起動できず、測る対象の経路が存在しないためである。

**落ちた job 952631 は床値 campaign ではなく別 wave (`dev-wave-t1981-holdout-oneshot-removal`) の
probe である。** したがって 2026-08-29 の「無条件赤」を床値 campaign の構成へそのまま
一般化してはならない。

---

## 3. G-B — 使い捨て入場鍵 (測定 3)

D811 の着手条件は「pilot 走行が消費した使い捨て入場鍵の状態を実測し、official 走行が同じ cell を
claim できることを確かめる」である。

共有 admission root は `<git common dir>/izanagi/s8b-holdout-admission-v1/`。現況は次のとおり。

| directory | 件数 |
|---|---|
| `claims/` (旧) | 36 |
| `consumed/` (旧) | 228 |
| `receipts/` | 0 |
| `measurement-generation-claims/` | 24 |
| `measurement-generation-consumed/` | 192 |

旧 `consumed/` 228 件の内訳は `observation_role=floor_campaign` が 96 件
(すべて campaign_run_id `20260824T205358Z-2c8cf9be` = 2026-08-25 pilot、12 セルへ均等に 8 件ずつ)、
`n_pilot` が 132 件 (`t1142-run-1`) である。

**親は最初これを判定対象と読み、誤っていた。** fresh reservation は旧 effect-key claim を明示的に
無視し (`s8b_holdout_admission.py:1618-1620`)、衝突は
`measurement-generation-claims/<generation_claim_digest>-<sha256(attempt_id)>.json` の
`O_EXCL` 失敗で決まる (`同:1636-1647`)。generation digest は `observation_role + campaign_run_id`
から導かれる (`同:782-802`) ので、新しい `campaign_run_id` を持つ official は同じ 6 項目
cell effect key でも別の claim identity になる。

**親は attempt registry の残枠も判定根拠に使おうとし、これも誤っていた。**
`floor-attempt-registries/` に登録簿が 1 本あり `max_consumptions_per_budget_key = 10`、
budget key は `(freeze_holdout_key, configuration_id)` である。しかしその登録簿の holdout key は
`rr23` / `rr79`、`process_identity.execution_uuid` は `campaign-fixture-execution` であって、
実 holdout の `rr20` / `rr80` ではない。**これはテスト fixture が共有耐久領域へ書いたものである。**
さらに現物の path は `<freeze>/<protocol>/registry.jsonl` だが、現行 consumer の canonical path は
`<freeze>/registry.jsonl` である (`s8b_attempt_profile.py:378`)。registry は scheduler recovery が
retry を開く場合だけ読まれ (`s8b_holdout_admission.py:4960, 5173`)、budget 10 もその replay 内で
だけ検査される (`同:5195`)。**したがって registry を G-B の予算根拠に使ってはならない。**

G-B の verdict は原理的に「ある時点で identity 衝突がない」までしか言えない。fresh reservation は
resume marker の全件検査 (`同:1612`)、12 claim の逐次 `O_EXCL` 作成 (`同:1636`)、その後の ledger
全体検証と追記 (`同:1742`) を行い、collision 以外の任意の `OSError` でも拒否する (`同:1094`)。
さらに最初の attempt 消費は現行 generation の consumed 全体を走査して claim・main ledger・
attempt ledger と再照合する (`同:4827, 4847, 4877`)。read-only の観測は claim 成功を保証しない。

**G-B は判定していない。** §5 の矛盾により official 走行が起動できないため、判定する意味が無い。

---

## 4. G-C — D1161 の予算承認 (測定 4)

D1161 (2026-08-27 ユーザー裁定) は「床値 official 経路の残る閂は
`output/s8b-freeze-budget-approvals/g1.json` の人間による承認だけ」と書く。実測すると
その directory は存在せず、`s8b_holdout_freeze.py:52` の `BUDGET_APPROVAL_SHA256` は `None` のままである。

**この承認は official 走行そのものの前提ではない。** 唯一の production consumer は
`build_v2_g1_candidate(*, floor_result_path, budget_path, ...)` (`s8b_holdout_freeze.py:2013-2040`) で、
**official 走行の結果を入力に取る**。承認 pin の fail-closed は `同:1298`。D589 (2026-08-20) も
承認 artifact・pin・official result 不在を v2 candidate 生成の三条件として並べており、こちらが
実装と一致する。D1161 の「official 経路」は「official 結果の freeze 昇格までを含む経路」と
限定解釈するのが正しい。

AI に許されるのは `tools/s8b_budget_approval_preflight.py:157` の `draft-not-an-approval` skeleton と
read-only 検証までで、canonical candidate と pin の確定はユーザー手番に残る。

---

## 5. G-D — 塞いでいる実体 (測定 5)

**official 床値走行は現行 main では起動できない。D926 を実装しても起動できない。**

- `tools/pegasus/floor_campaign.sh:1231` は `--fetchcontent-base-dir "$FETCHCONTENT_STAGING"` を
  **無条件で** driver へ渡す (`FETCHCONTENT_STAGING` は同 715 行)。
- `fetchcontent_base_dir` は refreeze 不適格 seam 18 名の一員である
  (`orchestrator/campaign/s8b_floor_contract.py:42-50`)。
- official mode は非既定 seam があれば**承認 gate の手前で**拒否する
  (`orchestrator/campaign/s8b_floor_campaign.py:6990-6994`)。
- `_derive_refreeze_eligibility` は「official かつ resume なし かつ非既定 seam ゼロ」だけを
  適格にする (`同:6906-6919`)。

**由来を特定した。** `1488fe683` ([T-1461]、2026-08-22) が**同じ commit で**
(a) staged transport を job script へ無条件配線し、(b) `fetchcontent_base_dir` を
`REFREEZE_DISQUALIFYING_SEAM_NAMES` へ登録した。commit message は両方を明記し、
`DW-G01` の生死実験で offline build の成功も確認している。**しかし official が起動不能になること・
refreeze 不適格が確定することには触れていない。**
`git log -S'"fetchcontent_base_dir"' -- s8b_floor_contract.py` の hit はこの 1 commit だけである。

**副次的な帰結:** 正規 job script を通る走行は pilot でも `eligible_for_refreeze` になれない。
D811 が pilot 値の発効を禁じた事実と整合するが、禁止の理由は裁定だけでなく機構にもある。

解消の選択肢は 3 つで、いずれもこの wave の権限を超える (§7 の裁定パッケージへ回した)。

---

## 6. 現行 Pegasus の workload 別 between-run 床値 (測定 6)

T-1942 は「判定床に使っている 0.030 は旧環境の write-heavy / balanced 由来で read-heavy を
含まない」と書いている。`between_run_noise` の成果物を全件数えると 4 件しかない。

| 環境 | rr5 (write-heavy) | rr50 (balanced) | rr95 (read-heavy) |
|---|---|---|---|
| linux-baremetal (旧) | あり | あり | あり |
| pegasus (現行) | **なし** | **なし** | あり |

- **旧環境については誤りである。** read-heavy も 2026-07-11 に測ってある。
- **現行 Pegasus で欠けているのは write-heavy と balanced のほうである。**
- 現行 Pegasus の rr95 は within 0.996% / between 0.223% で、どちらも 0.030 を大きく下回る
  (`output/env/pegasus/calibration/between_run_noise_t48_skew0p9_rr95_rmw0.json`)。

**ただしこの値で「read-heavy は較正済み」と無限定に書いてはならない。** 成果物自身が
cold-boot・温度ドリフトを含まない**下限**だと明記しており、`s8a_trigger_sweep.py:44-49` も
genuine-between は未較正だと書いている。genuine な cross-campaign / between-block floor は
どの workload でも未較正である。

---

## 7. 何をしていないか

- official campaign を投入していない。qsub していない。
- D926 を実装していない (`DW-G04`: 発火経路を書けない条件付き機能は実装しない)。
- G-A / G-B を実測していない (測る対象の経路が起動できないため)。
- 床値も性能も測っていない。build もしていない。
- 実装面の差分はゼロ。Codex 実装子は起動していない。

## 8. 子の構成

codex-cli の `gpt-5.6-sol` / xhigh を、段 2 plan 1 本、段 3 敵対相談 2 本 (lane sol / luna) の
計 3 本。全件 `check_codex_output.py` 緑。段 5・6 の子は段 4 裁定により起動していない。
