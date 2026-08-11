# [T-804] 段 1 brief — spec_sha256 の schema 伝播

base main `856f4d4c` / branch `worktree-dev-wave-t804-spec-sha256`。

## 確定済みユーザー裁定 (worklog 419)

[T-804] = **(B)**。cell 集合以外の approved spec 迂回を、manifest schema へ `spec_sha256` を
持たせ driver / report / judge の全層で再検証する wave で閉じる。oracle 結線 wave へは送らない。
関連 = [T-803] (a) pinned literal 恒久承認、[T-750] P-2 cell-product 検査は事後承認済み。

## 並走ガード 3 条件 (`docs/phase3-8b-restart-runbook.md` §並走ガード、必須記載)

1. **ノード同居なし** — 計算ノードを使う場合は単独性確認と静穏 preflight をノード上で行う。
2. **[T-139] の pilot / 本走 job 走行中はキュー投入を控える** — 起動時 qstat = `903065 izdw-e68`
   (RUN)、`903068 izdw-f28` (PRR) の汎用 dispatch 2 本のみ。**投入直前に毎回 qstat で再確認する**。
3. **裁定帯域は A ([T-139] 本走線) 優先** — 本 wave の裁定要求は A の後ろに並べる。

## 段 1 実測 (承認済み裁定の前提検査、DW-S01)

- `spec_sha256` は本番コードに不在。新設 field である (同名は変異台帳 JSON の別 namespace)。
- reviewed spec の唯一の消費側 = `s8b_oracle_manifest.build_approved_manifest`
  (`s8b_oracle_manifest.py:1127`)。spec から manifest を組むが **どの spec 由来かを manifest に
  一切残さない**。これが A-9 残余の機序。
- `verify_manifest` (`:986`) は spec を一切参照しない。cell 集合は freeze の
  holdout×configuration product と完全一致必須 ([T-750] の choke point) だが:
  - **`n` (総 replicate 数) / `master_seed` / `block_sizes` は完全に自由。** schedule は
    自己整合 (`schedule_sha256` は再計算一致) なので、別 `n` の schedule も通る。
  - **`campaign_ids` は自由** (block と 1:1・非空・非重複のみ)。
  - **run contract は裁定文より狭い。** `verify`/`screening`/`bench_max_rounds` は literal 固定、
    `reps`/`extime` は `s8b_experiment_numbers.APPROVED_*` と完全一致必須。定義済み 9 key のうち
    自由なのは `ccbench_pin` / `env_tag` / `clocks` / `contract_sha256` の 4 つ。→ **裁定を覆さず
    軸を狭める新事実**。
    **【段 3 で訂正】** 「自由なのは 4 つ」は逐語では不正確 — 部分集合判定と
    `copy.deepcopy(dict(...))` の全保存により **任意の余剰 key も自由**である。また実走時は
    driver が `env_tag` / contract hash / clocks を外部 authority へ束縛するため、この 3 つは
    「manifest 検証時点で自由」であって「実走まで自由」ではない。
  - 追加の新事実: `verify_manifest` の run_contract key 検査は **部分集合** (`<=`) 判定で、
    spec 側 `validate_reviewed_spec` の**完全一致**判定より緩い。余剰 key が manifest だけ通る。
- 層の実態: driver は `verify_manifest` を 2 箇所 (`:450` 単体 gate、`:1124` run flow) で呼ぶ。
  report は main 1 箇所 (`:1757`)。**judge は `verify_manifest` を呼ばない** — 純関数で、report が
  作った observations の `manifest_sha256` 文字列と `expected_cells` しか見ない。
- 伝播欠落が隠れる場所 = `seal_verifier` の wrapper (`:112`)。引数を明示列挙しており、
  新パラメータを足し忘れると **黙って落ちる**。
- **凍結 output bytes への影響 (DW-O09) = ゼロ。** `test_frozen_artifacts.py` が pin するのは
  `output/s8b-freeze/*` と insights のみ。`output/s8b-oracle-spec/` と
  `output/s8b-oracle-manifest-candidates/` は**実在しない**。`APPROVED_SPEC_SHA256 = None` で
  approved 経路は現状 fail-closed。→ **live artifact の移行は無い** (DW-O10 も producer 出力の
  移行対象ゼロ)。
- **【段 3 で訂正】 test / review の pin 閉包は非ゼロ。** 上の記述を「pin 閉包 = 影響ゼロ」と
  無限定に書いたのは誤りだった。`orchestrator/tests/test_s8b_oracle_manifest.py` の
  `PIN_GATE_SPEC_RAW` / `PIN_GATE_SPEC_SHA256` は **role 名を key にした pin** で、
  `artifacts` / `judge` / `report` / `materializer` / `outcome_stage_contract` の source SHA-256 を
  埋め込む。実装子 B が report / judge / artifacts を編集すればこの golden が動く。
  親は path のみを検索して 0 件を「pin なし」と結論した — これは **DW-O09 が名指しで警告する
  踏み外し方 (F30) そのもの**である。以後「凍結 output bytes への影響」と「test/review pin 閉包」を
  分けて記録する。

## scope と成果物影響 (DW-G05)

1. **manifest schema に `spec_sha256` を追加** (`_MANIFEST_KEYS` は exact 集合、`manifest_id` は
   document から算出のため両方変わる)。未実装なら certified 選択の試行数・WAL 所有・report 数値が
   approved spec と無関係な manifest で決まりうる (受理集合が広いまま)。
2. **`verify_manifest` が approved spec に対して内容を再導出照合する** — schedule (= n /
   master_seed / block_sizes)、campaign_ids、run_contract、binding_identity、
   allowed_excluded_reasons、generator_versions。未実装なら 1 は**恒真**になり、受理集合は 1 bit も
   狭まらない (記録するだけの hash は迂回者が正しい値を書けば通る)。
3. **driver 2 経路 + report が spec を渡す。judge は observations 経由で `spec_sha256` を検査。**
   未実装なら層を 1 つ迂回するだけで 2 の検査が効かなくなり、verdict が別 spec 由来の
   observations から出る。
4. **伝播欠落の機械検査。** 未実装なら将来の新 consumer が spec 引数を落としても緑のままになり、
   受理集合が黙って戻る。

## 不変条件

- 方向は**受理集合の縮小のみ**。既存の検査を 1 件も緩めない (規律 2)。
- `spec_sha256` を「記録するだけ」で終わらせない。**内容再導出との対**でのみ意味を持つ。
- 恒真な保証を作らない — 検査が発火しない状態 (spec 不在時に素通り) を作らない。
- freeze と同じ TOCTOU 契約に揃える: 検証済み単一 object を caller が渡し、被検証側は disk を
  再読しない。
- `APPROVED_SPEC_SHA256 is None` のあいだ機構全体が fail-closed で止まる性質は [T-803] 裁定どおり維持。
- 凍結成果物の bytes を変えない (実在しないため自明に成立。段 6 で `test_frozen_artifacts.py` 緑を確認)。

## 親の provisional 裁定 (攻撃対象)

- **(P1)** `verify_manifest` に **required keyword** `approved_spec: ReviewedSpec` を足し、
  `seal_verifier` wrapper も同時に更新する。optional / default 付きは fail-open なので採らない。
  exact type 検査は同一 module namespace から行う (二重 import 事故の既往あり)。
- **(P2)** manifest schema version は `8b-oracle-manifest/v1` のまま**上げない**。live artifact も
  legacy 互換要求も無く、`_MANIFEST_KEYS` の exact 判定が旧形を機械拒否するため。
  → 反論余地あり (schema 変更に version 据え置きは慣行違反か)。
- **(P3)** observations schema (`8b-oracle-observations/v1`) にも `spec_sha256` を足し、judge は
  `s8b_oracle_spec.APPROVED_SPEC_SHA256` との一致を検査する。judge の純関数性は module 定数参照で
  壊れない (`INPUT_SCHEMA` と同型)。
- **(P4)** 伝播欠落の機械検査は 2 本立て — (i) `verify_manifest` を呼ぶ module 集合の pin
  (新 consumer は検査を赤にしないと足せない)、(ii) 各層 (driver 単体 gate / driver run flow /
  report / judge) について「spec と食い違う入力を拒否する」層別 negative test。
  静的 pin だけでは恒真になるので (ii) が本体。
- **(P5)** run_contract の key 検査を `verify_manifest` 側も**完全一致**へ揃える (段 1 実測の
  新事実)。受理集合の縮小方向であり、2 の再導出照合と重複しない独立の穴。

## 分割方針

- 実装子 A = `s8b_oracle_manifest.py` + `s8b_oracle_spec.py` (schema / verify / builder / seal wrapper)。
- 実装子 B = `s8b_oracle_driver.py` + `s8b_oracle_report.py` + `s8b_oracle_judge.py` +
  `s8b_oracle_artifacts.py` (層の伝播と observations schema)。
- 所有分離: A は manifest/spec、B は driver/report/judge/artifacts。テストは各自の対象 module 分。
- 機械検査 (P4) は A が置く (choke point 側)。

## 段 dispatch の判断

DW-C00 の軽量版条件に**該当しない** — 正しさ防壁に触り、受理集合が変わり、設計択一 (P1/P2/P3/P5) が
割れうる。よって段 2・3 と段 6 の敵対レビュー子を省かない。規模は裁定文どおり t750 wave 同等以上。
DW-G01 (生死実験先行) は非該当 — 新探索軸ではなく既存機構の hardening。
