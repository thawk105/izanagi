# 段 1 brief — F976 writer 飢餓 + F977 巻き戻し通知 (親、2026-09-17、main abc7085ae)

- 研究前進: 土台。受入全走の非帰属赤 (F976、44 走中 7 走 = 16%、2026-09-16 再発) と land 後の main 巻き戻しの無通知 (F977、2〜3 日に 1 回) が
  各 wave の受入やり直し (1 走 18〜21 分) と取り込み直し (約 20 分) を強いている。完了判定 = (1) 負例 test で「reader 流れの中で writer が
  取れる」を実測、(2) `message --kind rolled-back` が fold-failed JSON から固定文を返す test + runbook/入口の送信義務。
- scope: (1) `orchestrator/tests/conftest.py` の `_real_repo_lock_path_context` / `_real_repo_flock_until` (1250〜1410 行) に process 間で見える
  writer 優先 gate (同 directory の第 2 flock file、`_open_real_repo_lock` と同じ owner/mode 検査) を足す。deadline 245.0 / retry 0.05 不変、
  同時実行数制限なし。`tools/acceptance_shards.py` にロック実装は無い (shard affinity のみ) → 触らない。
  (2) `tools/wave_land_window.py` の `message` に `--kind rolled-back` を足す。`_rollback_fold` / `rollback_ref=locked_main` の契約は不変。
  送信義務は `docs/pegasus-runbook.md` (land 節) と `.claude/commands/dev-wave.md` 項 9 (+ `tools/check_docs.py` の exact pin 467 行と
  `orchestrator/tests/test_check_docs.py` 55 行の fixture)。DW-O23 は L2 単節予算 1000 に対し満杯なので追記しない。
- 確定済み裁定: 第 20 回 /rulings 項 33 / 34 (fragment 未 land、D 番号は placeholder)。D1594 / D1618 の read/write lock 設計の内側。
  Codex author (D95) + 変異事前登録。仮想リスク向け gate・検査・台帳・一般化は scope 外。規律 2 を緩めない。
- 不変条件: reader 同士の並行 (SH overlap) は保つ。writer 待機なしなら reader は待たない。既存 fd 上の昇格 (SH→EX) / 降格 (EX→SH) は
  gate を通さない (通すと gate 保持 writer と相互待ちで deadline まで停止)。legacy→common の取得順は不変。fails-closed の deadline 文言不変。
  `landed` kind の固定文・rc は不変。`fold-rollback-failed` (rc=28) は通知しない (rc=3 拒否)。
- 成果物: (1) conftest 差分 + `test_real_repo_serialization.py` の正例 (reader 並行・writer 無しで reader 即時) / 負例 (reader 流れ →
  gate 無しで writer が短縮 deadline 内に取れない、変更後は取れる) + 既存 `test_real_repo_priority_order_is_literal_and_writers_follow_barrier`
  の fd 数・flock 列の期待更新 + README「real-repo 排他と loadgroup」1〜2 文。(2) `wave_land_window.py` 差分 + `test_wave_land_window.py`
  の正例 (fold-failed JSON → 固定文) / 負例 (landed JSON・rollback-failed JSON・main_after==wave_tip → rc=3) + runbook/入口/check_docs/fixture。
- 並列分割: (1) と (2) は編集面が重ならない → 段 5 で author 2 本並列、(1) を先に閉じる。
- (P1) process 内層 (`_real_repo_same_process_request_is_compatible`) に writer 優先は不要 — 取得中は `_REAL_REPO_PROCESS_LOCK_CONDITION` の
  RLock を握るため同 process の新規 reader は writer の flock 待ち中に入れない。xdist worker は test 本体が単 thread。
- (P2) 入口 項 9「land 成功時だけ `message` を…」は「land 成功時と巻戻し時に」へ是正する (+12 bytes、9507→9519 / 9520)。
  check_docs の pin literal と test fixture を同 commit で更新 (実装面 → author)。
- (P3) `rolled-back` の受理述語: `status == "fold-failed"` ∧ `main_after` が sha ∧ `main_before == main_after` ∧ `wave_tip` が sha ≠ `main_after`。
  merge 前の fold-failed (candidate planning / declared no-fold / fold preflight 失敗、main 不動) も同形で通る — 文面を両方で真にする
  (「main は merge 前 <sha> にあり、この wave の tip は main に無い」+ `git merge-base --is-ancestor <取り込んだ SHA> refs/heads/main` 助言)。
  `reason` 文字列 prefix (`fold failed: `) への結合は採らない (別 tool の自由文への結合)。
- 模擬/実の差: 既存 test の flock 模擬 (fd 91/92 固定) は実 kernel flock でない。負例は実 flock (tmp_path の lock file、別 fd/別 process) で取る。
- 受入・実測環境: 焦点走 = 計算ノード generic dispatch (worklog 1595 と同じ)、受入 = `tools/dev_wave_wait.py acceptance`。
