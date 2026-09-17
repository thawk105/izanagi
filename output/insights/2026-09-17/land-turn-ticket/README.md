# main land の進行保証を道具に入れた — 受入 lease と別の順番票、証拠保持の二層予算、control-plane 観測の非接触、cleanup の対象限定撤去

authority: none / default_effect: no-state-change (プロセス監査・逐語凍結。可変状態の正本は worklog 末尾と現行 phase doc)

- wave branch: `worktree-dev-wave-land-turn-ticket`
- 基準 commit: `abc7085ae6e1a69dc294c4f827ed7949e6df5305` (local main、wave 開始時、fresh worktree)
- 実装 commit: `ec6af3d0f1da3c6af7fdd403f228ff2bc1f06175` (Codex `role=author` 2 単位 (U1 land / U2 cleanup) + fix 10 巡、4 file、+2,720/−214)
- 起票: ユーザー依頼 (2026-09-17)。新規 T は本 wave の worklog fragment の slug `land-turn-ticket` で land の fold が採番する。背景の相談原文は
  `/work/1/SFC/tanab/dev-wave-jobs/land-progress-consult-20260917/out-{correctness,liveness}.md`
- 設計判断: 本 wave の decisions fragment (slug `land-turn-ticket`、D432 / D1996 を supersede、D109 / D702 を部分改訂)、失敗の型は failures fragment (slug `land-storm-lock-busy`)
- job dir (prompt・log・patch・probe script の原本): `/work/1/SFC/tanab/dev-wave-jobs/worktree-dev-wave-land-turn-ticket/`

## 何をしたか

2026-09-16 21:09〜22:25 に 8〜13 本の land が共通 flock を 3 回 (initial / post-provenance / post-fold-gate) 取り直す
競走で全員 `lock-busy` (rc=11) になり 76 分着地ゼロだった。manager session が手で 1 本ずつ GO を渡すと 2 波 30 本が
失敗 0・5〜6 分/本で流れた。この人手の直列化を land driver 自身に入れた。

`tools/dev_wave_land.py`: (1) `<common>/dev-wave-land-turn/` の順番票 (registry.lock / registry.json / `<seq>-<holder>.jsonl`)。
登録は受入 receipt の lock 非依存検証を通した request だけ、key = (acceptance_wave, tested_tip, receipt sha256)。生存は
ticket FD の `LOCK_EX`。grant は非横取り、terminal で同じ registry 更新で次へ引き渡す。seq (identity) と order (選出順) を
分け、grant を消費して終端した request (stale-main 等) は order を待ち手の後ろへ回す。`mutating` record (ff 前 / apply 前 /
shape B の mark・finalize 前) と死亡票の完了照合 (state 実在 / rollback 済 / ff 済 / finalize 済 / fail-closed)。
(2) 二層予算: `_LAND_TURN_WAIT_SECONDS = 3600` の絶対期限 + 180 秒の累積競合枠 (据え置き)。`_run_outside_land_lock` は
runner を 1 回だけ呼び、成功 payload を期限まで保持して再取得し、取得後に既存の全再検査を通す。非ゼロ provenance は既存
分類で即終端。(3) `_worktree_snapshot` は protected child だけ open し、無関係 child の `.git` 消失 race を消す。
registry は内容が変わったときだけ保存する。

`tools/dev_wave_cleanup.py`: 全体 prune を自 wave の admin gitdir だけの対象限定撤去へ。基準 snapshot との等価要求、journal の
原子的公開 (`os.link` no-replace、Lustre は `renameat2(RENAME_NOREPLACE)` が EINVAL)、link 後停止からの再入。

## 受理集合の変化 (段 4 裁定 §1 #21・§3.2)

- land: 無関係 child の同名差替え・alias・`.git` 欠損・不正名は拒否から受理へ (D109 の方向、incoming と非衝突)。自 wave の
  差替え・incoming と衝突する child・handoff 名前集合の拒否は不変。受入 receipt の不正 (runner digest 等) は登録前に rc=23 で
  拒否される (従来は lock 内の完全検証で拒否、rc は同じ)。ancestor-symlink case (tools 全体が symlink、受入 receipt が成立
  しない) は rc=29 → rc=23 (登録前提)。
- cleanup: 非 canonical な gitdir binding (`/work/SFC/...` 経由) は拒否へ (172 登録中 0 件、実害なし)。他 wave の live / stale
  admin と branch は保持。
- 順番待ちの終端: 180 秒枠を使い切っても順番期限 3600 秒まで待つ (180 秒は総待ち上限でなくなる)。

## 親の probe

- **旧 tree 負例 (base abc7085ae の container に新 harness だけを重ねる、pytest 不使用で scheduler を直接駆動):** policy `storm-e`
  (13 本、20 秒間隔到着、in-lock 240 秒、監査 430 秒、gate 130 秒、rc=11 は 120 秒後に同 key 再投入、fake 4,560 秒 = 76 分) で
  **着地 0・main 不変・監査 18 回・終端 151 回 (全 rc=11、最終 initial 12 / post-provenance 1)**。in-lock 30 / 200 秒の policy
  (`storm-a` / `storm-d`) では旧 tree でも 1 本着地する — 嵐の本体は「lock 内作業 > 180 秒の累積予算 + 到着率 > 処理率」で、
  D1996 が直した混同とは別の穴。`verbatim/probe-old-tree-storm.json`。
- **新 tree 対照 (fix-4 時点、同 policy):** 着地 1・監査 1。ただし独立 branch の stale-main request 2 本が保持 seq のまま先頭を
  交互に占め、seq 4〜13 の 10 本が順番期限で `lock-busy` → order 回転則 (fix-5) の根拠。`verbatim/probe-new-tree-storm-fix4.json`。
- **実機依存:** Lustre (`/work`, `/home`) は `renameat2(RENAME_NOREPLACE)` が EINVAL、`/tmp` (xfs) は成功。`os.link` は実 `.git`
  dir で EEXIST / nlink 2→1 を確認。`/tmp` の registry 保存 (write + fsync + rename + dir fsync) は 1 回 37 ms (load 55) で、
  poll ごと保存では 8 本の正例 node が runner 外で 270 秒 (runner 内は数秒)。
- **DW-O13 の分布:** dev-wave-jobs 配下の land 結果 468 件 (窓付き 113 件) で、成功 land の窓 n=34: median 272 / p90 543 /
  max 1,180 秒。3600 ≈ 13 × median。`verbatim/land-window-distribution.txt`。

## 段 3・段 6 の所見と裁定 (逐語は `verbatim/`)

- 段 3 レンズ A (正しさ) / B (進行保証) の所見 39 件を段 4 で裁定 (`verbatim/s4-adjudication.md` §1)。主要補正: 原子的引渡し、
  rc 別 seq 処理表、死亡票の完了照合 (state 有無だけに頼らない)、seam は scheduler main thread で実物委譲 (signal 制約)、完了判定は
  依頼どおり「有限 step に 1 本完了」。`wave_land_window.py` は編集面から除外 (第 20 回裁定 項 34 の別 wave)。
- 段 6 レビュー 4 本 (U1 A/B、U2 A/B) + 焦点再レビュー 1 本の must-fix: U1 R1 (親の裁定誤り: 非ゼロ provenance の分類)、R2
  二重回収、R3 初回 registry 公開前の死亡、R4 gate 後受入再検証の retryable、N1 自己再入、B1〜B5 (観測強化・M7 再照準・
  subprocess 死亡 test)、h′ の runner digest 静的化; U2 A1 基準 snapshot、B1 journal 原子公開、link 後停止の再入。すべて閉じた
  (fix 10 巡: U1 7 (うち fix-2 は親の停止文の不備で未編集)、U2 3)。
- 親の裁定誤り 2 件: (a) 非ゼロ provenance を「非 retryable」と書いた (既存 verifier は violation rc だけ非 retryable)、(b) fix
  prompt の「報告して止める」が全体停止と読まれた。

## 親の実走

- land 単独 (login): fix-1 後 1 failed / 345 passed、fix-3 後 4 failed (D16 退行)、fix-4 後 357 passed、fix-6 後 2 failed
  (lookup 列)、**fix-7 後 360 passed / 1 skipped / 19.3 秒**。
- cleanup 単独 (login): author 131 passed、fix-2 後 141 passed、**fix-3 後 143 passed / 8.0 秒**。
- consumer 18 file (計算ノード、fix-4 時点): **2130 passed / 4 skipped / 123 秒**。
- 受入全走: docs commit 後の最終 tip に対して land 前に 1 回投入する (受領証は job dir の `acceptance-receipt-*.json`、結果は land の受領証と worklog に束縛)。本 README は実測前に値を書かない。

## 変異 matrix

container worktree `.codex/worktrees/land-turn-ticket-mutcontainer` (実装 commit `ec6af3d0f` の使い捨て worktree) で
`tools/mutation_harness.py --runner-mode dispatch --detached`、runner は `python3 tools/run_tests.py` に
`test_dev_wave_land.py` + `test_dev_wave_cleanup.py` + `-q -rf --force-dispatch`。D612 の queue-wait / grace 上書き 1800 / 600。
spec は fix-6 報告の exact 表 (old / new を JSON 文字列で逐語指定、fix-7 で不変) + U2 の M10 を `make_mutation_spec.py` (job dir)
が生成した。本 dir の `mutation-spec-probe.json` (sha256 `d07f2ae4…`) / `mutation-ledger-probe.json`、`mutation-spec-final.json`
(sha256 `8dcc34de…`) / `mutation-ledger-final.json`。

- probe 走 (全件 SURVIVED 登録、観測 node を集める、22 run / 4,088 秒): baseline PASSED (407 秒)、M0 と M7b は SURVIVED、他 19 件は
  MISMATCH (= 赤 node を観測)。**M7a (provenance 後の fingerprint 比較) は SURVIVED 対照の予測に反して既存 test 5 本が殺した**
  (`test_provenance_audit_detects_removed_ignored_collision` / `..._still_rejects_moved_land_heads[wave]` /
  `test_provenance_receipt_rejects_tip_that_moves_during_audit` / `test_post_provenance_head_change_preserves_provenance_rejection_order`
  ほか) → 冗長 gate ではなく生きた gate として KILLED 期待へ再登録した。M7b (fold gate 後の同比較) は SURVIVED のまま (指定入力に
  対する冗長対照、全入力の等価証明ではない)。
- 本走 (22 run / 1,711 秒): **baseline PASSED (698 秒)、負例 19 件すべて KILLED で期待 node と観測 node が完全一致 (matching
  21/21)、等価変異 M0 (comment のみ) と対照 M7b は SURVIVED、MISMATCH 0、TIMEOUT 0**。全変異の anchor は 1 箇所。

| ID | 変異 (exact 1 箇所) | KILLED node 数 | 狙いの node (新設) と主な killer |
|---|---|---|---|
| M0 | `_land_lock_now` に comment 1 行 (等価) | — (SURVIVED) | — |
| M1 | `_wait_land_turn` を迂回 (誰でも initial へ) | 4 | `eight_requests_complete_in_sequence`、`independent_waves_one_lands_rest_stale`、`stale_head_rotates_behind_waiters`、完了観測 [finalized] |
| M2 | 同 key 再入で seq を再発行 | 12 | `retry_preserves_sequence`、gitlink recovery 4 本、subprocess 死亡 ほか |
| M3 | 生存を FD lock でなく mtime / TTL で判定 | 1 | `live_owner_is_not_expired` (専属) |
| M4a | ff 前の `_land_turn_mutating` を省略 | 7 | `mutation_rechecks_owner[ff]`、[ff-wave]、[fold]、観測解消 [rolled-back] / [ff-done] ほか |
| M4b | `apply_fold` 前の marking を省略 | 1 | `mutation_rechecks_owner[fold]` (専属) |
| M4c1 | shape B の mark 前確認を省略 | 2 | `mutation_rechecks_owner[shape-b-mark-ticket]` / `[shape-b-mark-fd]` (専属) |
| M4c2 | shape B の finalize 前確認を省略 | 1 | `mutation_rechecks_owner[shape-b]` (専属) |
| M5a | 選出時に `mutating` 票を削除 | 5 | `recovery_precedes_successor`、二重回収、観測解消 [rolled-back]、完了観測 2 本 |
| M5b | 完了観測で state 判定前に票を削除 | 12 | `recovery_precedes_successor`、二重回収、gitlink recovery 4 本 ほか |
| M6a | provenance payload の再取得を旧 180 秒残枠へ戻す | 9 | `preserves_evidence_after_lock_budget[provenance]`、`invalidates_changed_inputs[collision/fold-state/tip]`、累積予算 test ほか |
| M6b | fold gate payload の再取得を旧 180 秒残枠へ戻す | 2 | `preserves_evidence_after_lock_budget[fold]`、`cumulative_wait_budget_fold_does_not_refill` |
| M7a | provenance 後の fingerprint 比較を無効化 | 5 | 既存 5 本 (上記) — 生きた gate |
| M7b | fold gate 後の fingerprint 比較を無効化 | — (SURVIVED) | 冗長 gate の対照 (指定入力では後段が同じ拒否) |
| M8 | 無関係 child も open して binding を読む (旧挙動) | 30 | `land_ignores_unrelated_child_cleanup_race`、非接触で受理へ反転した既存 5 本 ほか |
| M9 | mutation 直前の自 wave inode 比較を外す | 1 | `mutation_rechecks_owner[ff-wave]` (専属) |
| M10 | cleanup の対象限定撤去を直接 `subprocess.run` の全体 prune へ | 18 | `cleanup_preserves_foreign_stale_admin[stale]`、部分削除再入 5 本、journal 再入 ほか |
| M11 | static 受入検証の拒否を握りつぶして登録へ進む | 6 | `rejects_invalid_acceptance_before_registration[child_rc/runner_executed_sha256]`、runner gate 系 4 本 |
| M12 | 引渡し前に registry を先に公開 (原子性を壊す) | 2 | `red_head_hands_over_atomically[timeout/red]` (専属) |
| M13 | 非ゼロ provenance の早期終端を無効化 | 1 | `red_provenance_fails_fast` (専属) |
| M14 | grant 消費後の終端で order を回さない (旧挙動) | 1 | `stale_head_rotates_behind_waiters` (専属) |

M4 系は呼出し省略で wrapper 内の故障注入も消えるため、「故障した所有権を無視した」と「故障注入なしで mutation が成功した」の
両方が赤の理由になる (焦点再レビューの帰属注記)。M8 / M2 / M5b / M10 は既存 test も killer になり専属性は主張しない。

## 残存限界・scope 外 (記録のみ、裁定パッケージ候補)

- 元 request 不在の fold 途中 state (state file 実在) を他 wave が自動復旧する主体 (cwd・binding・receipt・起動主体・結果帰属)。
- 生存したまま hang した先頭を止める・停止確認する・引き継ぐ監督主体 (TTL 追越しは不採用)。
- fold 子 process (`git add` / `git commit`) が lock fd を継承しない既存境界。
- lease 保持を land 待機全体へ広げる契約 (TTL 2400 < 順番期限 3600)。
- 新 receipt でも wave の順位を引き継ぐ契約 (現 key では別 request)。
- 共有 admin 一覧 (`_administrative_gitdirs_for_wave` / porcelain) の完全非接触化。
- 進行保証の前提: 新 driver 同士、旧 driver の妨害終息、先頭が有限時間で進む、registry lock の公平性は OS 依存。
- 順番期限直前に監査緑になっても期限で証拠を破棄する (有界の availability cap、seq / order 保持で再投入)。

## 逐語の行末空白の可逆正規化 (DW-S07)

`verbatim/` の `.md` / `.txt` / `.json` は `git diff --check` に触れる行末空白を除いてある (可視文字不変)。原文 bytes は
`verbatim/originals.json` (sha256 `1899dc8256e9cad9fd6206b41a0a2c3880e43936e613d4375b45f9b53e606236`) に UTF-8 text として収め、各 text をそのまま書き出せば原文 bytes を
復元できる。
