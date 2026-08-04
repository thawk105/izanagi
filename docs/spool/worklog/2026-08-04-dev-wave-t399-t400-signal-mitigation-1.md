---
schema: izanagi-spool-v1
ledger: worklog
authored: 2026-08-04
wave: dev-wave-t399-t400-signal-mitigation
seq: 1
title: [T-399][T-400] mitigation 構成は捕捉可能と実測決着 — controller 証拠を 3 分離し危険側観測を authoritative 化 (コード + docs、branch worktree-dev-wave-t399-t400-signal-mitigation)
---

## 本文

- **依頼は「dev-wave のツールでコア数を使い切る並列化が無く、入れたら速くなるものの実装」。**
  survey 実測: run_tests.py (xdist + login 自動 dispatch)、check_ai_provenance.py
  (ThreadPool)、build `-j` (site 由来) は並列化済み。check_docs.py 1.0 秒 /
  check_codex_agents 0.16 秒 / check_codex_output 0.03 秒は対象外。land / fold の直列は
  D102 の設計。**測った範囲の最大候補は変異本走の「1 変異 = 1 qsub」の順番待ち** (T-357 の
  生死確認実測: 外側 579.3 秒 → 束ね 2.5 秒。内側 pytest 約 990 秒は束ねでも不変)。その恒久
  実装 [T-360] (裁定済み・択 (a)) の未充足前提 = D130 条件 3 の mitigation 実測 [T-399] と
  その前提 [T-400] を本 wave の対象に確定した
- **[T-399] は肯定側で決着した。** authoritative attempt (t362-mitigation a1、request
  887918) で、警告 SIGTERM の Python parent 捕捉 (+118.93 s) → cleanup 完走 (5.01 s) →
  observer 独立 readback で canary ORIGINAL → **期限 46 秒前の自発終了** (scheduler `.e` が
  `signal SIGTERM` と `Remaining Elapse: 46S` を明示) を凍結判定式で確認。
  **「捕捉可能な signal と grace を与える構成は存在する」**。十分性は
  `R_restore_bound` (mutation_harness `_restore_targets` の上限) が未実測のため凍結式どおり
  UNKNOWN。split-warning は非 authoritative (SIGUSR1 は Bash trap 止まり、canary MUTATED、
  cause 不整合) で verdict UNKNOWN。正本 =
  `output/insights/2026-08-04_t399-t400-signal-mitigation/RESULT.md`
- **[T-400] は split-v2 証拠 3 分離 ({{D:probe-evidence-three-way-split}}) として実装した。**
  段 3 敵対 2 レンズが blocker 9 / must-fix 10 (安全側 mitigation が qwait rc=9 要求で構造的に
  棄却、現 state で resolve が ledger 不在停止、複合 predicate 丸ごと移動の観測 gate 弱化等) を
  検出し全件 real 裁定。段 6 はレビュー 2 本 + 焦点再レビュー 3 巡 (DW-O16 上限) + fix 8 回で、
  後半 5 回は**実測が導いた** — (i) 通し検査 3 本の赤 = T-361 専用 bnode hostname 正規化の
  T-362 への誤適用、(ii) racct が `sudo: パスワードが必要です` で恒久欠測し旧 evaluator が
  観測無効へ誤変換 ([T-401] の真因は反映遅延でなく permission gate)、(iii) 「安全終端 =
  qwait rc=0」の操作化が誤り (NQSV は警告 signal 配送でも rc=9 を返す)。(ii)(iii) は事前登録の
  erratum-1/-2 として初回凍結文を消さず追記した
- **保存 raw からの決定的再評価経路を resolve へ追加した。** 旧 evaluator の凍結契約違反の
  評価を、staged evidence (hash 束縛) から新規 qsub なしで再走し、旧評価を
  `superseded_evaluation` に保存する。置換 retry 禁止 (raw に安全性内容がある attempt) と
  両立する唯一の訂正経路。8/3 から詰まっていた t362-default の terminal migration も
  resolve 初回で 1 件成功し、leg 進行が回復した
- **検査:** driver 評価器テスト 63/63 緑 (計算ノード dispatch)。変異 matrix は G1〜G8 の
  8/8 KILLED・期待 node 一致 (`mutation-ledger-final.json`。期待集合の実測併合 2 回は
  v2/v4 erratum として凍結、dispatch infra 起因 rc=16 の再走 1 回)。§7.0 実測 =
  controller certified peak 181 MiB < 512 MiB (local-ok、`MemoryMax=512M` の fail-closed cap
  付き)。**受入全走は対象外** — production コード差分ゼロ (変更は probe driver +
  insights + spool fragment のみ)、(128)/(149) と同じ射程。B-057 は本 wave の変異 matrix で
  充足。check_docs / provenance preflight は全 commit で緑、full 監査は land 前に再走
- **キュー異常:** gen_S が 15:20〜21:15 頃 INA (他ユーザー滞留 223 本、gpu が 136 node 占有)。
  ユーザーの停止指示と回復報で再開した。probe 資源は request 2 本 / walltime 各 180 s
- エージェント工数: codex 13 本 (段 2 プラン 1、段 3 レンズ 2、段 5 author 1、段 6 レビュー 2 +
  焦点 2 + fix 8 のうち fix4 は空振り)、claude 子 1 本 (anchor 採取)。dispatch 多数 (テスト・変異)

## 次の一手差分

### 完了

- [T-399] mitigation leg の実測を完了した。捕捉可能構成の実在は肯定で決着、十分性は
  {{T:restore-bound-measurement}} へ分離した。
  remaining: none
  base: 9e0e4e3890f2c7c68dae5d7e76a463241898e3ef684e6876ffd0de61fd53c7b3
- [T-400] controller admissibility の 2 field 分離 (実装は 3 分離) を完了した。
  remaining: none
  base: 3f778476089d7f8c6457c7402da5ef2185b0d1ed6dc33f42329a3f7eed958f3c

### 更新

- [T-360] **P1・裁定済み → 前提は残り 2 件**: 択 (a) は不変。D130 条件 3 は
  「捕捉可能構成の実在 = 実証済み ([T-399])、十分性 = {{T:restore-bound-measurement}} 待ち」
  へ前進した。条件 2 (flock 確定) は [T-402] のまま。warn margin は `elapstim_req` の warn 値で
  拡大可能であり設計上の障害は残っていない。着手は D131 前提 6 点 + D105 supersede の
  次 wave で、ユーザー裁定に従う
  base: f6a9395589926dcf2f4883978503cb82268765578573f376c4a2acb02852b8cc
- [T-401] **P2・真因判明**: racct 系の欠測は反映遅延でなくログインノードの
  `sudo` permission gate である疑いが強い (実測: racctjob/racctreq が
  `sudo: パスワードが必要です` で失敗)。会計は必須連言から外して欠測 3 分類
  (permission / empty / error) の evidence field になった (事前登録 erratum-1)。
  残件は「racct を捨てて `.e` 会計 block を正式な会計証拠にするか」の設計判断のみ
  base: f646aa1f9a26a96b98ed7b0e73bab2b8a3897e390640eaf0e2760a136e6f95a1

### 新規

- {{T:restore-bound-measurement}} **P1・新規**: mutation_harness `_restore_targets`
  (書戻し + pycache purge + byte 検証) の実測上限 `R_restore_bound` を計測し、[T-399] の
  凍結式 `G_usable_lower ≥ 10 s + R` で T-360 の grace 十分性を決着する。warn margin の
  拡大 (`elapstim_req` warn 値) と併せて設計する
