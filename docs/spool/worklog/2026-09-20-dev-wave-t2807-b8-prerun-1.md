---
schema: izanagi-spool-v1
ledger: worklog
authored: 2026-09-20
wave: dev-wave-t2807-b8-prerun
seq: 1
title: [T-2807] B-8 事前登録 v1 の発効前試走 — D2160 runner を B-8 の規則へ改版 (v5、Codex author + fix 2 巡、repo 外)、案 A (g_rl / g_rt) を現行 pin e9e477ca へ厳密適用して trace-enabled build と identity を計算ノードで導出 (g_rl b0f95b21… / g_rt a0219ce0…、build 前後一致)、発効束を揃えて発効 commit + 本走認可を 1 行で再提示 (docs のみ、branch worktree-dev-wave-t2807-b8-prerun)
---

## 本文

- 依頼 = D2186 項 1 (第 26 回裁定、段階認可) の試走手番。発効・校正・本走は行っていない。成果物 = insight
  `output/insights/2026-09-20/t2807-b8-prerun/README.md` (段 1 実測・runner 改版の対応表・試走 record・発効束 §7.1・1 行再提示 §7.2)、
  runner v5 (job dir `dev-wave-t2807-b8-prerun/probe/verify_phase_runner.py`、2103 行、sha256 `4ff6652a365b952cba4deb23e2ae910ba863dabba4a107503c641c7a36863430`、
  repo へは入れない)、発効束 draft (`verbatim/b8-effective-bundle.draft.json`)。設計判断は {{D:t2807-b8-prerun-runner-and-bundle}}。
- 試走 (計算ノード gen_S、job 6 本 (runner v3 / v4 / v5 で各 2)、各 Elapse ≈ 36 秒、bench・verifier なし): template patch は現行 pin へ `git apply` で厳密に当たり、
  identity は **g_rl `b0f95b213e6d419cf31473a37c6be3246f9b0fefbd42ead2273d5ab7408a670d`、g_rt `a0219ce0b258e339ac6489cb5b17b3acb4158ce0d6087ca6098d1e408862f833`**
  (`src_token` = `source_bytes_sha256`、build 前後・login 事前照合・runner v3 / v4 / v5 の 6 record すべて一致)。07-16 校正の g_rl `4608a96e…` は旧 pin の値で期待値にしない。
- 軽量版 (段 2・3 省略、実装面ありで author + レビュー 2 本並列 + fix 2 巡 + 焦点 2 本)。Codex 全段 `gpt-6-astra` / medium。author 1 本 (v3、selftest 120/120)、
  レビュー A / B とも NO-GO (must 3 + 2、should 2 + 4)、fix 1 は親 prompt の矛盾 (終端 commit 後は runner が tracked) で編集前に停止、fix 1b で v4 (所見 9 件 closed、selftest 160/160)、焦点再レビュー 1 が保全済み trace の初回 verifier 再開経路の回帰を must-fix (fix 1 の副作用)、fix 2 で v5 (resume の 4 分類、selftest 166/166)、焦点再レビュー 2 (insight §10)。
- **親の誤り 3 点 (レビューと author が捕まえた):** (1) author prompt に D2160 の bench attempt-2 を写し事前登録 §5「bench を再生成しない」と矛盾させた (author が開示、両レビューが must-fix)。
  (2) (P2) の本走 hard timeout 3600 s は親の追加解釈 → 事前登録自身の数 (校正 3600 = §11、上限 1800 = §12 / D2186 (5)) に揃えた。(3) D2186 項 1 の逐語 file を sed の行範囲で切って見出しだけにした。
- 規則の解釈で親が決めた点 (レビューで攻撃済み、insight §5): rc=3 `indeterminate` verdict は失格 (P3)、§5 の bench 失敗は校正・本走とも pass 阻止 (P10)、失格は混入・sha 不一致に関わらず先に評価 (P11)、期待 identity は発効束 JSON から読む (P1)。
- 変異 matrix は repo 内実装面差分ゼロで免除 (`DW-S04`)。受入全走は免除しない。local main は着手 `f94b61fc8` から記録前に `eb6aa98de` (T-2766 / T-2153) へ ff-only で取り込んだ。
- 改善候補 3 件 (段 8): docs 変更なし、memory へ (先例 runner の規則 → 本 wave の規則の対応表を brief に置く / fix prompt は「対象 file は commit 済み (tracked) で唯一の編集対象」と書く / 逐語射影は見出しで切る)。

## 次の一手差分

### 更新

- [T-2807] **P2・ユーザー裁定待ち (発効 commit + 本走認可の 1 行再提示)**: 試走完了・発効束が揃った。insight
  `output/insights/2026-09-20/t2807-b8-prerun/README.md` §7.2 の 1 行 (事前登録 v1 raw sha256 `6ccb18c7…` を対象 = 案 A、identity g_rl `b0f95b21…` / g_rt `a0219ce0…`、
  pin `e9e477ca`、patch `31316713…`、verifier 9 file sha256、runner v5 `4ff6652a…` の発効束で発効し、校正 3 job (workload 別 {6, 10} s、walltime 03:30:00) →
  規則が決める extime での本走 6 job (24 verify、≤ 4 h / 対象、本走 verifier hard timeout 1800 s) の投入を認可する) をユーザーが承認するか。承認後 = 発効 commit (発効束 JSON を
  `effective` に、D 番号・日付) → 固定 checkout で校正 3 job → `summarize` → `stage_B_allowed` なら本走 6 job → 3 値判定 → §8 / §6.3 の書き方で results 稿へ。
  不承認の選択肢 = (b) timeout 3 値・校正 walltime だけ変えて再提示、(c) 据え置き。
  base: 03f262289aa8bb28636486e211ce55a7ce381b6d7826577a800f5eccc8cd6184
