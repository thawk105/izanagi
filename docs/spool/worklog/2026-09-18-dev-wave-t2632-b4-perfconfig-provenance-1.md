---
schema: izanagi-spool-v1
ledger: worklog
authored: 2026-09-18
wave: dev-wave-t2632-b4-perfconfig-provenance
seq: 1
title: [T-2632] B-4 本走用 PerfConfig の 3 種の出所 (較正の出力値・取得構成からの復元値・選択値) と環境契約 artifact 3 種を第 22 回裁定の委任で確定した — site = Pegasus 計算ノード、reps は候補 5 のまま、§5 は記入せず実走認可を含めない (docs のみ、branch worktree-dev-wave-t2632-b4-perfconfig-provenance、変異 matrix 免除 = 実装面差分ゼロ)
---

## 本文

- ユーザー依頼は「[T-2632] (第 22 回 /rulings 項 2、ユーザー『推奨通りで』2026-09-18) B-4 本走用 PerfConfig の 3 種の出所を AI 委任
  (D1641 決定 3 と同型、thawk105 名義) で確定し決定台帳へ残す docs wave — 較正 3 件の出力値 (records 1M / 1M / 2M、threads 48、
  workload 3 key 逐語)・取得構成からの復元値 (extime=3、ycsb_max_ope=10、D2088 の復元限界を引き継ぐ)・選択値 (reps は候補 5 の
  まま、承認値にしない) を出所で区別し、環境契約 artifact 3 種 (env_contract.py の path + bytes sha256、activation の path + bytes
  sha256、generation + contract_sha256) を併記する。site = Pegasus 計算ノード (gen_S、tag pegasus)、導出記録に対象 checkout と
  base の実 resolver 経路を残す。結果を見る前に固定する。§5 の記入は D1483 / D1510 の順序 (床値の後) を守って行わず、実走認可を
  含めず、B-4 は適格な赤 precursor 0 件で実施不可のまま (D1986 項 4)。着手直前の local main から fresh worktree を作る。規律 2 を
  緩めない。本題の D 起草だけ。仮想リスク向けの gate・検査・台帳・一般化の追加は scope 外」。
- **閉じた (D 1 本 = {{D:b4-perfconfig-provenance}})。** §5 の値セルは 1 byte も変えていない。実装面ゼロ、insight は作らず実測値は
  D 本文に逐語で残した。第 22 回裁定の fragment (branch `worktree-rulings-all-20260918`) は本 wave の起草時点で未 land のため、
  D は裁定を名前 (第 22 回 /rulings 項 2、2026-09-18) で引く (他 wave の placeholder は参照不可)。
- 実測は login node (pegasus02) からの静的導出のみ (計算ノード dispatch 0)。対象 checkout = local main `24ede1d11`。較正 3 件の
  sha256・`saturation.records` (1M / 1M / 2M)・threads 48・workload 3 key・取得 argv 3 件 (`--extime` 無し、3 key、`ycsb_max_ope`
  無し)・calibrator CLI 既定 `--extime 3`・CCBench 既定 `ycsb_max_ope 10`・`env_contract.py` bytes `292bbed3…`・activation
  `00000001.json` bytes `6a44b5b1…` (pegasus g1 `e576e9cd…` active)・g2 `1346c20b…` (登録済み・`resolve_by_contract_sha256` が
  ever-active でないと拒否)・resolver 経路 (`p3_b4_launcher.py` base 枝 → `p3_s4_loop._current_site` → `_admit_env_contract` →
  literal `_SITE_ENV_TAGS` → `env_contract.lookup`) は、precheck (entry 1620、`output/insights/2026-09-17/t2632-b4-s5-precheck/`)
  の値と全項目一致した。差分ゼロ。
- 出所の 3 種の扱い: (a) 較正の出力値と (b) 復元値は本 D で採る。(c) 選択値 `reps` は候補 5 のまま承認しない — 確定は §5 記入の
  時点で同じ委任の下で別に行う。環境契約は 3 種併記 + 記入前 / 発効前の再導出条件を D に書き、g2 の登録を発効と扱わない
  (D1484)。attestation 用較正 (契約の `calibration_ref`、g1 では D1537 の 753f535a) と動作点用較正 (3 件) は別の量と明記。
- 軽量版 (docs-only)。段 2・3 は省略 (択は裁定で尽き、残るのは現物の再実測と転記)。実装子なし。段 6 相当として read-only codex
  レビュー 1 本 (`gpt-6-astra` / medium、値・sha256・世代・順序不変条件の独立検算) を回した — **NO-GO → fix 後 GO 相当**:
  must-fix 2 (較正 JSON の `reps` 文字列の出現 key を `notes` と誤記 → 現物は `acquisition_receipt.walltime.formula`、rr5 は説明文
  にも / Pegasus wrapper の command を `python3 -m …` と非逐語で引用 → 現物は `"$PY" -B -m orchestrator.campaign.p3_s4_loop`)、
  should 1 (却下案の根拠に D1936 項 8 を引くのは射程の拡大 — 同項が却下するのは母集合を作るための追加基盤 → 裁定の逐語と依頼の
  scope へ差し替え)、nit 0。検算表 52 行は 3 箇所の指摘以外すべて一致 (契約 hash 2 本は canonical JSON から独立再計算、worklog の
  `base:` も lookup で一致)。3 件とも親が現物で裏取りして反映した。dev-wave 改善候補 0 (段 8 は無言通過)。
- 検査: `tools/check_docs.py`、`spool_fold.py --dry-run`、三軸語走査 (`s8b_holdout_freeze search`、holdout の conjunction hit 0。
  本 fragment は rr50 の positive control にだけ hit — D2089 と同じ 3 key 逐語の転記であり holdout ではない)、`git diff --check`、
  provenance 監査。受入全走は land 前に 1 回 (結果は land の受領証)。

## 次の一手差分

### 更新

- [T-2632] **P2・裁定済み (D2120 項 5、第 22 回 /rulings 項 2) → 条件待ち + 出所調査 (AI)**: 前 wave の 3 件 (bootstrap 集合は非空
  入力が出るまで定義しない、対応証拠の出所は AI が現存資料で先に確かめる、耐久 carrier や D39 決定 3 の変更が要ると分かった時点で
  別裁定) は D2120 項 5 のまま。§5 の 2 欄の前提 4 項のうち、本走の site (Pegasus 計算ノード、tag `pegasus`、対象 checkout
  `24ede1d11` と base の resolver 経路)・`PerfConfig` の 3 種の出所 (較正の出力値と復元値は採用、`reps` は候補 5 のまま未承認)・
  環境契約 artifact 3 種 (g1 `e576e9cd…` active、g2 `1346c20b…` 未発効、記入前 / 発効前の再導出条件) は
  {{D:b4-perfconfig-provenance}} で確定 (2026-09-18)。2 欄の確認・記入は thawk105 名義の AI 委任。**記入は D1483 / D1510 の順序
  (床値の 12 行裁定・測定・採用裁定の後) を守り、前倒ししない。** 残るのは、§5 記入時の `reps` の確定 (同じ委任)、承認済み
  `PerfConfig` を base CLI が読む経路 (`p3_s4_loop.py` の `default_perf()` 無条件使用の差し替え、別の実装候補、委任だけでは実走
  可能にならない)、literal 写像と registry 属性の二重定義の解消 (恒久一致を求めるなら)。裁定パッケージの正本は
  `output/insights/2026-09-17/t2632-b4-s5-precheck/README.md`。通常 base campaign からの自然発生赤の回収は変わらない。
  base: c1c43d80a4767d45d700240def68a8838291ffcee401cce26df904065133f9bd
