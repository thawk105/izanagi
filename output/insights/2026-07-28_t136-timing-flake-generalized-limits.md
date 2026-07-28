# [T-136] dev-waves integration の時間依存フレーク除去 — 逐語と裁定 (2026-07-28)

wave: dev-wave (背景 job、worktree `dev-waves-t088-python-gate` 流用は worklog を参照)。
コード commit = `52dcf32`。作業 artifact (prompt / plan / adv / rev / patch / 変異結果 JSON /
負荷 job log) の正本は job tmp `/home/SFC/tanab/.claude/jobs/d5886cf2/tmp/wave-t136/`
(session 領域、生存保証なし。要旨は本書へ凍結)。

## 1. baseline 実測 (job 0:873281.nqsv、bnode002、gen_S 48 core、専有)

- spin=0: 緑 16s。spin=24 (load 8→25): 4/4 緑、遅延なし。
- **spin=64 (load 43→92): 4/4 で rc=1** (赤 6/5/4/5 件、wall 64s)。
- 赤 node 合併 (再現率): child_failure 4 枝 = **4/4 決定的** (tight limits 1s/2s の枝間共有)、
  malformed[delayed_partial] = 3/4、one_wave_success = 1/4 (既定 5s limits)。
- 新事実 (c'): TIMEOUT 期待の sleep_timeout 枝も `len(_invocations)==1` が 0 になり赤 —
  total 2s が子 spawn 前に尽きる系。reason assert は安全でも副次 assert は負荷脆弱。

## 2. 設計の要点 (段 2-4)

- 機序: 製品 deadline は submit 起点 (daemon.py:729) で preflight〜checks 全工程を覆う。
  request limits ≤ profile caps (`_validate_submit_policy`)、かつ
  **per_wave ≤ total ≤ max_waves × per_wave (schema.py:647-650)** — このため
  「per-wave tight + total generous」は構成不能 (親の初期案は誤り、段 3 で棄却)。
- 採用: 成功系 per-wave 60s / caps 60/240。sleep_timeout 枝のみ 20/40 + fake sleep 600s
  (TIMEOUT 検出力と invocation==1 を維持しつつ node wall を 20s に制限)。
  テスト側 wait は算術的包含が要るものだけ延長し、独立な短窓 (socket ready 5s、SIGKILL 後
  wait 5s、synthetic、fake 短窓、sigkill 0.5s 窓) は据え置き。
- cleanup は「保証」でなく best-effort: wait 失敗時のみ、lock 内 run_id 照合 → cancel →
  対象 thread の直接 join(120)。global shutdown / wait_idle は不使用 (別 run 誤停止と
  `_last_run_thread` 取り違えの除去、R2-4)。真の hang containment は in-process では
  不可能 (cancel/shutdown の WAL 経路が無界) — 残余リスクとして明記。
- 不採用: clock 注入 (sole-deadline 防壁への seam)、retry/負荷 skip、`total_timeout=0`
  正規化変更 (scope 外)、supervisor 寿命 context manager 全面化 (diff 過大)、
  sigkill 0.5s 窓の再設計 (8 走の負荷実測で未発火、G03)。
- 受理集合の変更 (一行): state/reason/side-effect の期待集合は不変。通常 run の
  submit→terminal 許容時間だけを明示値へ拡大し、テストは応答時間を検査しない。

## 3. レビュー所見の裁定要約

段 3 (敵対相談 ×2、gpt-5.6-sol max): blocker 6 = (c') 未解決 / per-wave·total 分離不成立 /
isolation contract 語彙汚染 (kill_spawned_process を共通 cleanup に入れると F9 盲点か marker
汚染) / cleanup 無界 / M8 偽 KILL (shutdown が内部で cancel を呼ぶ) / 負荷 script の契約矛盾。
must-fix 群 = caps 過大 (300/900→60/240)、wait 一律延長の選別、変異の構成 mirror 化
(M1-M4/M11 は合わせ鏡)、統計的過大主張 (0/4 で「除去」と言えない)、F36/F38 の commit 衛生。
全採用。不成立攻撃 6 件 (AST 導出 9 関数の一致、`wait_idle` の join 妥当性、`-n 32` 実効など)。

段 6 (レビュー ×2 + 焦点再レビュー ×2、gpt-5.6-sol high): R1 blocker 1 = PM4 の単一理由性
不成立 (worker 層のみの変異は checker.py:290 が mask → **residual 観測無効化 = state assert
署名で再登録**、旧登録は erratum)。R1 must-fix = output cap の無断拡大 128→256KiB、据え置き
対象 SIGKILL wait の 5→20 緩和。R2 must-fix 4 = run-id/recovery 期限の包含不足 (直列上限
最大 185s → 240s へ)、`_start_real_daemon` の primary 例外喪失、busy test の TOCTOU
(RLock 区間で除去)、cleanup の run 非束縛。fix 2 巡 (1 巡目 NO-GO → R2-4 残存を 2 巡目で
閉鎖) → 焦点再レビュー **GO**。全所見 real、棄却 0。

## 4. 変異 matrix (事前登録 = 段 4 ruling §2 v2、実行 = commit 52dcf32 後、無負荷)

preservation control 4 本 (テスト緩和で検出力が落ちていないことの実証。新規検出は主張しない)。
各変異を fix 版テストと af2f47c 版テストの両方に投じ、**同一 node・同一署名で 4/4 KILLED**:

| ID | 製品変異 | 新旧共通の赤 node | 署名 (実測) |
|---|---|---|---|
| PM1 | worker.py timed_out→TIMEOUT 変換無効化 | child_failure[sleep_timeout] | reason assert: NONZERO_EXIT vs TIMEOUT |
| PM2 | daemon.py deadline guard `<=0`→`<0` | expired_deadline (mock) | DID NOT RAISE |
| PM3 | worker.py limited→LOG_LIMIT 変換無効化 | child_failure[log_cap] | reason assert: NONZERO_EXIT vs LOG_LIMIT |
| PM4v2 | worker.py residual 観測を False 化 | child_failure[grandchild_residual] | state assert: COMPLETED vs FAILED |

harness = DW-O19/M04/M05/M07/M08 準拠 (anchor 一意性・単一 diff entry・flock・復元の内容比較、
結果 JSON は job tmp)。旧 M1-M4/M8-M12 (構成 mirror・呼出順 oracle) は段 3 裁定で全廃。

## 5. paired 負荷検証 (job 0:873448.nqsv、gen_S、spin=64、-n 32、git archive 展開)

baseline (af2f47c) と fix (52dcf32) を同一 allocation で B/F 交互 ×10 対 → fix のみ既知
6 node subset ×30 走。readiness barrier (spinner PID 生存 + load ≥ 40) と reap を備えた
script v2 (段 3 b13: 初回 job との script 差は契約として明記し、baseline も同 script で再測)。

実測 (bnode115、load 43〜74、target sha256 = 4159...3216 は job summary 正本):

- baseline (B ×10): **10/10 rc=1**、赤計 39 件は全て既知 6 node の内 (未知の赤ゼロ)。
  sleep_timeout / nonzero / grandchild = 各 10/10、log_cap = 9/10 (delayed_partial と
  one_wave_success はこの 10 走では未発火 — 低頻度機序)
- fix (F ×10、B と交互): **10/10 rc=0**
- fix subset (既知 6 node、-n 6、×30): **30/30 rc=0**

統計の限界: 低頻度機序 (one_wave_success 系は baseline 1/4) に対する 0/N は「未再発」で
あり除去の証明ではない。支配的機序 (child_failure 4 枝 = baseline 決定的) の消滅が主証拠。

## 6. 受入 (login node、pegasus02)

- 焦点 4 ファイル (integration 80 / isolation contract 3 / fake 4 / cli 13) = 100 passed、
  22.6s (F-p1 較正前は 62.6s — sleep_timeout 枝 60/120 では node wall 60.74s)。
- 受入全走 = **3140 passed / 18 skipped / 赤 0** (50.84s、worktree、変異 harness 復元後)。
  前回 (34) と勘定・wall とも一致 (20s node は並列で完全に隠れる)。

## 7. 残余リスク (worklog 次の一手へ)

- 製品内部の固定短窓 (probe 5s ×2、handshake 5s、SIGSTOP 5s、git 30s、branch-tip 5s、
  task validator 10s、server socket read) は残る。spin=64 ×8 走で個別発火は未観測。
  「時間依存の完全除去」ではなく「観測された機序の除去」が本 wave の主張。
- fixture 構築の `_run_command` は timeout=120 で有界化したが、WAL/fsync 経路の無界は製品側。
- sigkill テストの 0.5s durability 窓は据え置き (未発火。再設計は独立裁定が要る)。
