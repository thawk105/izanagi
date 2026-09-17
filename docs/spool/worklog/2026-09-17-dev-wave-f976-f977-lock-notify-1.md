---
schema: izanagi-spool-v1
ledger: worklog
authored: 2026-09-17
wave: dev-wave-f976-f977-lock-notify
seq: 1
title: D2104 項 33 / 34 — 実 repo ロックに writer 優先 gate を足し、land の巻き戻し通知 kind を足した (コード + テスト + docs、branch worktree-dev-wave-f976-f977-lock-notify、変異 matrix = baseline PASSED・11/11 KILLED・等価 1 SURVIVED・MISMATCH 0・期待 node 完全一致)
---

## 本文

- ユーザー依頼は「F976 の writer 飢餓と F977 の巻き戻し通知を 1 wave で直す (第 20 回 /rulings 項 33 / 34)。(1) 実 repo ロック
  (D1594 / D1618 の read/write lock の内側) に『待機 writer がいる間は新規 reader を待たせる』writer 優先を局所修正で入れ、
  正例・負例を同じ変更単位で置く。deadline は伸ばさず同時実行数制限も入れない。(2) fold 失敗で main を merge 前まで巻き戻す
  契約は維持し、通知を `wave_land_window.py message` の既存経路へ 1 kind 足す。Codex author (D95) + 変異事前登録。本題 2 件の
  局所修正だけ。規律 2 を緩めない」。着手時に main の裁定は D2104 (項 33 / 34) として採番済みだった。
- **閉じた。** 一次資料は `output/insights/2026-09-17/f976-f977-lock-notify/README.md`。設計判断は
  {{D:real-repo-writer-gate-and-rolled-back-notice}}。docs commit `b869861a5` (親)、実装 commit `df2da88ee` (Codex author ×2)。
- **plan v1 の「昇格は gate を通さない」は F976 の一方の経路を直さないと親が検算した。** F976 の当該 node の writer は
  `repository_candidate_commit` fixture の parent EX で、同 module の module 寿命 SH fixture が生きた worker では既存 fd 上の
  昇格になる。裁定で昇格も gate を通す (gate を開いてから自分の SH を明示解放する) 形に変えた。
- **段 3 レンズ A が plan v1 の三者循環 (reader が legacy main を握ったまま common gate で待つ + 入れ子昇格 + 別 worktree の
  writer) を real と示した。** 裁定で reader は「process が実 repo lock を 1 つも持たないときだけ、全 key の gate を SH で試して
  即解放する」形に変え、gate 辺を通る循環を現行の main 間 hold-and-wait と同じ族に閉じた。段 6 レビュー A が v2 で同反例が消えた
  ことを wait-for graph で確認した。
- **brief の P3 (`main_before == main_after`) は recovery 経路の本物の巻き戻しを拒否する** (レンズ A の経路表)。条件を落とし、
  述語は fold-failed ∧ after / tip が SHA ∧ after ≠ tip とした。merge 前の失敗 (main 不動) も通るが文面は両方で真。
- **レンズ B が `test_check_docs.py` の byte 数 pin (`9_507`) の見落としと、author に docs を持たせる所有割当の契約違反を出した。**
  親が docs (入口 項 9 +12 bytes = 9,519 / 9,520、runbook、tests README) を先に commit し、author worktree を ff してから投入。
  「DW-O23 は L2 1,000 bytes で満杯」という brief の理由も誤り (段 9 の無条件参照で L1) と訂正された。
- **段 6 レビュー 2 本の must-fix 2 件** (昇格時に `LOCK_UN` が gate open より先で open 拒否時に外側 reader の SH を失う /
  P2 の実時間 2 秒未満 assert が高負荷で偽赤) を fix 子で閉じ、負例 `test_real_repo_gate_open_rejection_preserves_outer_reader`
  を追加 (旧順序で赤を確認)。再レビュー 1 本 = GO。
- 実走 (計算ノード): 焦点走 f1 (統合前 10 file) 1945 passed / 16 skipped、f2 (fix 後 7 file) 1544 passed / 10 skipped。
  受入全走 attempt 2: **24541 passed / 67 skipped / child-green** (tested main `48e3ff9e5`、tip `be21eb0b5`)。attempt 1 は
  post-claim merge 直後に main が進み postcheck rc=70 (無走行)。provenance full 監査 rc=0。
- **変異 matrix (container worktree、`run_tests.py` 3 file、probe と本走で各 13 request)。** 初回 probe (2 file 選択) は F982 を踏み
  baseline 赤 → `test_p3_s4_loop.py` を足して再投入。本走は baseline PASSED、負例 11 件 (M1〜M11) すべて KILLED で期待 node と
  観測 node が完全一致、等価 M0 SURVIVED、MISMATCH 0。専属 killer: M6 (保持中も gate 検査) → P2 の入れ子 reader 1 node、
  M7 / M8 / M11 → 各 1 node。
- 残存 (scope 外、記録のみ): gate は NB polling で待機順を持たず、保証は「writer が gate を保持する間、その gate の事前検査を行う
  fresh reader を待たせる」に限る。既に lock を持つ process の fresh reader は gate を見ない。昇格の変換失敗後に外側 reader が
  SH を失ったまま `mode=read` を信じる既存の穴 (gate 導入前から) は裁定パッケージ。
- 工数: codex 子 8 本 (plan 1、consult 2、author 2、review 2、fix 1、再レビュー 1、全段 `gpt-6-astra` / `medium`)。親の実測は
  焦点走 2 本、変異 3 走 (probe 失敗 1 + probe 13 request + 本走 13 request)、受入 2 attempt (走行 1)、provenance full 1 本。

- D2104 項 33 / 34 を実装した: 実 repo ロックの writer 優先 gate (fresh 取得と昇格、reader は保持ゼロ時だけ検査) と
  `wave_land_window.py message --kind rolled-back`。正例・負例を同じ変更単位に置いた。

## 次の一手差分

### 新規

- {{T:real-repo-upgrade-failure-state-and-gate-fairness}} **P3・裁定パッケージ**: 実 repo ロックの (a) 昇格の変換失敗 (deadline)
  後に外側 reader が SH を失ったまま `mode=read` を信じる既存の穴の fail-closed 化 (state の毒化等) と、(b) gate 取得前からの
  厳密な writer 優先 (待機登録 / FIFO)、(c) 既に lock を持つ process の fresh reader が gate を見ない流れだけで writer が
  飢餓する実例、の 3 件は {{D:real-repo-writer-gate-and-rolled-back-notice}} の scope 外。実害の観測を待って別裁定。
