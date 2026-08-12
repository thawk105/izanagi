# 段 1 brief — [T-499 後継] 8b oracle reviewed spec の producer 設計と D302 schema 択一

wave: dev-wave-t499-spec-producer-design / branch: worktree-dev-wave-t499-spec-producer-design
起点: 2026-08-12 第 6 束ユーザー裁定 [T-499] Q1 = (b)。控え:
`/work/1/SFC/tanab/dev-wave-jobs/rulings-inbox/2026-08-12-rulings7-batch.md`,
`.../2026-08-12-t499-approval-turns-blocked.md`

## scope (docs + insights のみ、実装差分ゼロが既定)

1. `output/s8b-oracle-spec/` へ reviewed spec を発行する **producer の設計** (手順・所在・provenance 要件)。
2. **D302 の schema 択一** — 据え置き解除か再発行か。どちらでどの consumer が壊れるかを実測で示し択一提示。
3. **事前登録値の草案** (n / master seed / block sizes / campaign IDs / holdout IDs /
   configuration IDs / generator versions / binding identity / run contract) と**承認パッケージ草案**。

## 不変条件 (破ったら停止)

- durable artifact を 1 件も発行しない (`output/s8b-oracle-spec/` と
  `output/s8b-oracle-manifest-candidates/` へ 1 byte も書かない)。
- `APPROVED_SPEC_SHA256` を書かない。contract test の期待値を緩めない。D302 の据え置きは設計提示までは不変。
- 規律 2 (正しさゲートを緩める変異を許さない)・規律 3 不変。承認判断はユーザー手番。push しない。
- 実装が要ると判断したら理由付きで別タスクへ分離する (本 wave では実装しない)。

## brief 前の親実測 (一次資料は file:line)

- M1 `output/s8b-oracle-spec/` は**不在**。canonical path 定数は
  `orchestrator/campaign/s8b_oracle_spec.py:19` の `SPEC_REL`。
- M2 gate は `s8b_oracle_spec.py:182-200` `_load_approved_spec_bytes`。
  **bytes の SHA-256 pin だけを見て git provenance を一切見ない。** `APPROVED_SPEC_SHA256 = None` は同 :23。
- M3 `_assert_user_commit` は `s8b_ratified_freeze.py:537`、呼び手は同 :1113/:1128/:1143/:1156 の
  **freeze v2 の approval / pointer / revocation / cancellation record だけ**。
  **oracle spec 経路からは呼ばれない。**
- M4 contract test の zero-file assertion (`orchestrator/tests/test_s8b_oracle_manifest_contract.py:128-144`)
  は `output/s8b-oracle-spec` と **`output/s8b-oracle-manifest-candidates` の 2 dir 両方**を対象とし、
  schema version による分岐を持たない。
- M5 下流 producer は**既に実在**する。`build_approved_manifest` (`s8b_oracle_manifest.py:1170-1232`) が
  `load_approved_spec` を消費し、`_candidate_output_parts` (:882-892) で
  `output/s8b-oracle-manifest-candidates/` 配下にしか書けない。
  → **spec を承認して本走すると、manifest candidate 発行の時点で同じ test が必ず赤になる。**
- M6 spec の production consumer は 4 module: driver (:487,:497,:1220)、judge (:372)、report (:1763)、
  manifest (:1186)。すべて `load_approved_spec` 経由で今は `no-approved-spec` の fail-closed。
  test 側は `orchestrator/tests/s8b_oracle_spec_fixture.py` + monkeypatch で durable path に依存しない。
- M7 先例: T-810 事前登録 `tools/pegasus/policies/t810_prereg_v1.json` (23205 bytes) は
  **AI-Agent trailer 付きの AI commit** (`c80513a8`, `1892d8b1`) で導入され、承認は receipt + code pin で表現。
- M8 `generator_versions` は 5 本の production source の実 byte hash を pin する
  (`s8b_oracle_manifest.py:53-61`, `_validate_generators`)。この 5 本は直近 30 日で 40 commit、
  直近 14 日で 20 commit の変更を受けている。→ **承認 spec は現在の改修速度では数日で自壊する。**
- M9 `run_contract` は自由度がほぼ無い。`verify=legacy+s2`, `screening=off`,
  `bench_max_rounds=1`, `reps=5`, `extime=5` (`s8b_experiment_numbers.py:14-15`),
  `clocks` は env 契約の `clocks_per_us` と完全一致 (`s8b_oracle_driver.py:884`),
  `contract_sha256` も env 契約と完全一致 (`s8b_oracle_manifest.py:396-424`)。
  登録済み env_tag は `linux-baremetal` (clocks 1800) と `pegasus` (clocks 2100) の 2 つ。
- M10 `binding_identity` は schedule cell と一対一で active ratified freeze から決まる
  (`s8b_oracle_manifest.py:487-532`)。freeze v2 が不在なので**現時点では導出不能**。

## 親の provisional 裁定 (攻撃対象)

- **(P1)** 裁定控えの「`_assert_user_commit` の要求を満たす形で spec bytes を配置する」は**前提の取り違え**である
  (M2/M3)。spec 承認経路に git provenance 要求は現状ない。「同等の provenance を spec にも課すか」は
  設計上の択一として提示するに留め、実装しない。
- **(P2)** D302 の択一は spec 単独でなく **spec + manifest candidate の 2 dir** で判断する (M4/M5)。
- **(P3)** 事前登録値は AI が導出・起草するが、値そのものは承認対象であり本 wave は草案に留める。
- **(P4)** 成果物影響 (DW-G05): 本 wave を実装しない場合、8b oracle 本走は `no-approved-spec` で
  fail-closed のまま = certified 選択の 8b 系レポートは 1 件も生成されない。受理集合は変えない。

## 成果物の形

`output/insights/2026-08-12_t499-spec-producer-design/` に
(a) producer 設計、(b) D302 択一の実測票、(c) 事前登録値草案 + 承認パッケージ草案、(d) `verbatim/` に子出力。
`docs/spool/` へ worklog fragment と新規タスク起票 fragment (採番は fold に任せる)。

## 分割

段 2 プラン子 1 本 (sol)、段 3 敵対 2 本 (sol / luna) を read-only で並列。実装子なし。
