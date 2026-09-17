---
schema: izanagi-spool-v1
ledger: worklog
authored: 2026-09-17
wave: dev-wave-t2632-b4-s5-precheck
seq: 1
title: [T-2632] 順序 (2) の precheck — B-4 事前登録 §5 の 2 欄 (校正済み PerfConfig / env_tag) は今日記入できない: 第一の理由は D1483 の順序、次に reps の出所・消費経路・契約世代・確認者の担当範囲 (docs のみ、実装差分ゼロ、branch worktree-dev-wave-t2632-b4-s5-precheck、変異 matrix = 実装面差分ゼロにつき免除)
---

## 本文

- ユーザー依頼は「[T-2632] 順序 (2) の precheck (P2、実装差分ゼロ)。B-4 事前登録 §5 の 2 欄 (校正済み `PerfConfig` の artifact
  パスと hash / env_tag) を今日記入できるかを確かめ、記入はせず条件と不足を報告する。確かめる点 = (1) accepted 較正 3 件が
  records / threads を供給できるか、reps / extime が較正に無いことをどう扱うか、(2) env_tag を site resolver から機械導出できるか、
  (3) 確認者と発効版への併記の要件。floor 欄 (A-5 裁定待ち) と順序 (3) の campaign 起動には触れない。成果物は insight +
  裁定パッケージ。規律 2 を緩めない」。
- **答え: 2 欄とも今日は記入できない。** 一次資料は `output/insights/2026-09-17/t2632-b4-s5-precheck/README.md`。§5 の値セルは
  1 byte も変えていない。
- **第一の理由は順序。** D1483 (2026-09-02 ユーザー裁定、D1510 で再確認) は §5 全欄の記入を「床値の 12 行裁定・測定・成果物の
  採用裁定の後に順序どおり個別に」とし、3 者の指名が「実行 site・較正済み PerfConfig」を解禁しないと名指す。この 2 欄の記入順序を
  解除する後続裁定は無い (段 3 レンズ A が独立確認)。12 行裁定は D1641 で済み、測定 (A-5 の spec 凍結を含む) と採用裁定は未了。
- **PerfConfig 欄 (順序が解けた後も残る不足):** 較正 3 件 (5c836a22 / 94a4b79f / 2b7ba072、tracked、accepted) は records
  (1M / 1M / 2M)・threads 48・workload 3 key・env_tag・clocks_per_us を供給する。extime=3 と ycsb_max_ope=10 は較正の出力値では
  なく取得構成 (tracked な取得 argv に `--extime` 無し → CLI 既定) からの復元 (D2088 と同じ導出)。**reps は較正にも取得構成にも
  無く、D2088 の reps=5 は床値 spec 用の AI 選択で B-4 転用は未認可。** さらに **§5 の pin を実走 `PerfConfig` へ束縛する既存経路が
  無い** — base CLI は `p3_s4_loop.py` の `default_perf()` (100000 / 4 / extime 1 / reps 2) を無条件に使う (段 3 レンズ B が
  親 brief の落ちとして指摘)。§5.1 の「差し替えるまで記入しない」の差し替えは実装を要する。
- **env_tag 欄:** tag `pegasus` は B-4 の sanctioned 経路 (`p3_b4_launcher.py` → `p3_s4_loop._admit_env_contract`、site→tag の
  literal 写像) から機械導出でき、registry 属性 (`lookup_required_attestation_contract`) と現 checkout で同じ契約 object を返す
  (同値は現世代限り、写像の二重定義は残る)。閉じないのは併記要件の側 — (a) B-4 本走の site の明文裁定 (D1641 決定 3 は床値の
  site)、(b) 契約の世代 (active は g1 `e576e9cd…` で calibration_ref は D1537 の自己整合しない較正、g2 `1346c20b…` は登録済み
  未発効で D1484 が発効を鎖の末尾に置く。source bytes / activation bytes / contract_sha256 の 3 種を区別して併記する候補)、
  (c) 確認者の担当範囲 (identity は thawk105、D1483 が 3 者指名の他欄への波及を否定)。書式 (複合値) は裁定不要 (D1854 / §0 /
  先例)。計算ノード dispatch は本 precheck に不要 (login からの静的導出で足りる。live admission は証明しない)。
- **裁定パッケージ (順序 D1483 が解けた後に効く。今日の記入を求めるものではない):** 1) B-4 本走の driver・site・tag の確定
  (推奨: Pegasus 計算ノード)、2) B-4 用 PerfConfig の採用範囲と承認主体 (較正出力 / 取得構成からの復元 / reps の AI 候補 5 を
  分けて、D1641 決定 3 と同型の委任を明示的に拡張する推奨)、3) 確認者・記入者の担当範囲の追加 (thawk105 名義の AI 委任を
  2 欄へ及ぼす推奨、実走認可は含めない)、4) 環境契約の artifact の読み (3 種併記、発効時点の active 世代と照合)。
  既裁定で閉じるもの (D1483 / D1484 / D1641 / D1812 (c) / D2088〜D2090 / D1854) は返さない。
- **次の一手候補 (実装 T、本 wave では開かない):** 承認済み PerfConfig を base CLI が消費する経路 (`default_perf()` の差し替え)、
  literal 写像と registry 属性の二重定義の解消。
- 段 3 敵対相談 2 本 (read-only codex、`--lane luna` × 2、reasoning medium) の所見 20 件は real 10 / refuted 10。親の較正値・sha256・
  契約世代・key 再計数に誤りは無かった。dev-wave 改善候補は 0 件 (段 8 は無言通過)。
- 検査: `tools/check_docs.py`、`spool_fold.py --dry-run`、`git diff --check` (逐語 2 本の可逆最小正規化を README に記録)。

## 次の一手差分

### 更新

- [T-2632] **P2・裁定済み (D2120 項 5) → 条件待ち + 出所調査 (AI)**: 本 wave の成果は「不足報告 + 空 batch
  での発行器到達」までと認定。bootstrap 集合の定義と固定時点は適格な赤 precursor ≥ 1 を実際に扱う時点で裁定する
  (今は定義しない、carrier も台帳も作らない)。proposal・走行・参照点の対応証拠の出所は AI が現存資料で閉じられるかを
  先に確かめ、耐久 carrier や D39 決定 3 の変更が要ると分かった時点で別裁定。残る順序のうち **§5 の 2 欄 (校正済み
  PerfConfig / env_tag) は precheck 済み (2026-09-17、`output/insights/2026-09-17/t2632-b4-s5-precheck/`): 今日は記入
  できない。** 第一の理由は D1483 の順序 (§5 全欄は床値の 12 行裁定・測定・採用裁定の後。A-5 は D2120 項 4 で AI の
  手番になったが測定・採用裁定は未了)。順序が解けた後も、reps の出所 (D2088 の 5 は床値 spec 用の AI 選択)、承認済み
  PerfConfig を base CLI が消費する経路の不在 (`default_perf()` 無条件)、B-4 本走の site・契約世代 (g1 active / g2
  未発効)・確認者の担当範囲の裁定が要る。tag `pegasus` の機械導出はできる。裁定パッケージ 4 項は同 README。
  通常 base campaign からの自然発生赤の回収は変わらない。
  base: e304379daccccddcede4d7fb284611382f2ce8fe8f61d0855af2be4102d52948
