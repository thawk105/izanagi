# land の attempt 数と往復原因の集計 (直近 landed wave 20 本、診断のみ) — land 局面 201 分のうち往復由来が 101 分 (50%)、その 65.6 分 (65%) は「受入取り直し」2 本、残りは rc=10 ×3 回 (17.9 分、うち固有の直列化待ち 14.7 分)・rc=31 EINTR ×2 回 (10.2 分、F672 同型)・wrapper の「別 land 走行中」停止 ×3 回・理由不明の rc=23 ×1 回。rc=25 / rc=26 は 0 (2026-09-21)

- 依頼: land の attempt 数と往復の原因を直近 landed wave 20 本の job dir (`/work/1/SFC/tanab/dev-wave-jobs/<wave>/`) の `land*` / `acceptance-receipt*` から集計し、rc=10 / rc=25 / rc=26 / rc=31 / terminal-merge 起因の受入取り直しの件数・追加 wall・受入再走の有無を出す。1 attempt で終えた wave との差を出し、往復を減らす局所修正を効果見積り付きの裁定パッケージにする。診断だけ、実装 0 行。land の受理集合・provenance 監査・fold の契約は変えない。規律 2 に触れない。
- 測定: 2026-09-21 07:37〜08:00 JST に login node で読み取りのみ (段 6 レビュー後の再集計は 08:2x JST)。基準 commit = local main `5efd69367` (wave 木は同 SHA から fresh)。
- 隣接 wave: `dev-wave-acceptance-resubmit-causes` (同時刻開始) が受入側の原因 6 分類を担う。本資料は land 側だけを分類し、受入の赤 (rc=70 / 91 / 94) は回数を数えるだけで中身を分類しない。

## 結論 (最初に読む)

1. **20 wave のうち 12 本は land tool 起動 1 回・wrapper 停止なしで landed (land 局面 2:54〜10:16、median 3:32)。8 本が往復した (land 局面 6:39〜43:26、median 13:38)。** land tool の起動は計 27 回、拒否 7 回 (rc=10 ×3、rc=23 ×2、rc=31 ×2)、tool を起動せず wrapper が止めた回が 4 回 (rc=97 ×3、rc=92 ×1)。rc=25 (postcondition) と rc=26 (fold-owned) は 0、rc=11 (lock-busy) も 0 (順番票 D2119 と wrapper の事前確認で吸収)。
2. **往復による追加 wall は合計 6,060 秒 (101.0 分) で、land 局面合計 12,047 秒 (200.8 分) の 50%。** 内訳は表 2 のとおりで、上位 2 件が「受入全走の取り直し」— t2797 (rc=23、26.8 分) と t2803 (wrapper rc=92、38.8 分) — で 3,935 秒 = 65.6 分 (追加 wall の 64.9%)。
3. **rc=10 (stale-main) は 3 回 / 2 wave (17.9 分) だが、うち 14.7 分は「別 wave の land が順番票で先に走っている間の待ち」で、回避可能なのは再 merge + dry-run + 失敗 preflight の 3.2 分。** 3 回とも「別 wave の land が走行中 (順番票待ち) のときに、自分の landing tip (tested tip そのもの、または merge 済みの tip) を固定して投入した」形で起きた。順番票が order を後ろへ回す (D2119 項 3) ので、待っている間に main が進めば必ず rc=10 になる。
4. **rc=31 (fold gate) は 2 回 / 2 wave (10.2 分) で、2 回とも F672 同型 (`registered worktree path cannot be resolved: [Errno 4] Interrupted system call`、path は他 wave の submit-tree)。source で確認できたのは次の 4 点:** `_registered_worktree_paths` は `_FoldGateOuterWatchdog` の armed 区間 (SIGALRM を 100 ms 周期で自分に送る) の中で呼ばれる、`Path.resolve(strict=True)` → `os.path.realpath` → `posixpath._joinrealpath` は `os.lstat` / `os.readlink` を使う、CPython 3.10.12 のその C 実装に EINTR の自動再試行 loop は無い (PEP 475 の対象外)。**「その SIGALRM が今回の EINTR を起こした」「Lustre の混雑が必要条件」は、source と観測 (混雑窓・他 wave の Lustre 上の path・直後の再投入は成功) に整合する未検証の仮説である** (静穏時 probe 460 回 × 2 では再現せず)。**同一 request の再投入は現行 source で新規登録として受理され、検査を再実行する** (k2-loop は同じ landing tip を拒否の 31 秒後に再投入して landed、受入不要) — F672 の復旧文「受入を取り直すしかない」は現行 source と合わない。
5. **terminal-merge 起因の受入取り直しは 1 本 (t2797)。** 受入 final2 (tested tip `088bbdec7`) の後に 1 親の docs commit `cf1c90e1f` を積んだため、land が「forward main merge first-parent commit must have exactly two parents」(rc=23) で拒否し、受入 final3 (22:57) を取り直した。これは契約どおり (前方 merge 列は 2 親の自動 merge だけ)。隣接 wave の分類 5「記録 commit 後の tip 変更 rc=23」に該当する。
6. **契約が要求しない受入取り直しが 1 本 (t2803、38.8 分)。** wrapper `land-go.sh` が「main 側の差分が `tools/run_tests.py` / `tools/dev_wave_wait.py` / `tools/check_acceptance_reds.py` / `tools/dev_wave_land.py` のいずれかを変えたら停止 (rc=92)」と検査し、実際の差分は `tools/dev_wave_land.py` 9 行だけ (`run_tests.py` は不変) だった。land tool の契約 (D987 / D1234) は「最終 incorporated main と tested main の runner blob (`tools/run_tests.py`) の net 差だけが受領証の再利用を拒否する」で、waiter / checker の束縛先は tested tip (checker は verdict `non-attributable-only` のとき tested main も) の tree (`tools/dev_wave_land.py` 1119〜1175 行)。この差分は D987 の再受入条件に該当しない。**旧 receipt のまま前方 merge → land する経路は t2803 では実測されていない** (実際の成功は新 receipt、tested tip `65966f4d8`、`incorporated_main_shas=[]`)。
7. **裁定パッケージ (§5): 局所修正 3 件 (A: F672 経路で `InterruptedError` を armed 区間内で有界に再試行、B: 呼び手 loop を「走行中 land 0 を確認 → 固定 SHA merge → 即投入」に、C: 呼び手の land 前 guard を D987 の比較基点に一致) で、本母集合の追加 wall 101 分のうち 47〜51 分 (A 6.4〜10.2 分、B 4.1 分、C 36.4 分) が削減候補区間。実測削減量ではなく区間の割当てである。** 受理集合・監査・fold 契約を変えないことを採用条件とし、A は watchdog の期限監督を保つ形に限る。t2797 型 (26.8 分) は契約どおりで、受入後に docs commit を積まない手順 (隣接 wave の裁定) でしか消えない。提案しないもの (§5.4): 順番票の order 保持 (D2119 が意図的に回転)、監査の順番票外への移動 (D2119 の却下択「lock 区間の移動」に隣接、本 wave の scope 外)、land tool 自身の merge (親が merge する契約)。

## 1. 何を測ったか

- **母集合:** `/work/1/SFC/tanab/dev-wave-jobs/` 配下で、`land*` の名前の file (`land*.json` / `land*.log` / `land*.stdout`、wave ごとに違う) に `"status":"landed"` の land 結果を持つ dir を、その file の mtime 降順で 20 本。t2797 (09-21 05:26) 〜 cleanup-backup-loss-record (09-20 21:49)。21〜23 番目 (t2153、paper-intro-ja、t2766) は annex として表に載せるが集計に入れない。20 本の候補列挙は段 6 レビュー (codex) が 1,394 dir の `land*` 走査と更新 dir の任意 file 名走査で再確認した (dir mtime 制限なしの全走査は未完了)。
- **母集合外:** 20 本の窓 (main `eb6aa98de`..`5efd69367`、cleanup-backup の main_before → t2797 の main_after) の fold commit は 21 件で、job dir に land 記録の無い着地は 1 件 (`1ee9ef2cb` 21:55:44、[T-2501] の対話 session、その merge message に rc=10 の再試行あり)。窓より前 (09-20 19:18〜21:49) にも job dir 記録のある着地 (rulings-all-20260920c、T-2792、t2795 など) と rc=10 の merge message 2 件 (19:44、20:44) があるが、本母集合には入れない。
- **定義:**
  - land 局面 = 最初の land 試行の開始 (wrapper が受領証を読んで走り始めた時刻、無ければ tool 起動時刻) → landed の壁時計。
  - 成功試行 = 最後 (成功) の試行で wrapper が main を固定して merge を始めた時刻 (merge が無ければ tool 起動時刻) → landed。wrapper 内の「走行中 land 0 を待つ」時間は成功試行に含めず追加 wall 側 (t2813 land-3 の 210 秒)。
  - 追加 wall = land 局面 − 成功試行。
  - 固有の直列化待ち = 追加 wall のうち、別 wave の land が走っていた区間 (相手の開始・終了時刻は相手の job dir から。段 6 レビューが 8 区間全部の重なりを再確認)。重なりは「修正後もその全時間が不可避」の証明ではない。
  - 回避可能 = 追加 wall − 固有の直列化待ち。t2797 は契約どおりの取り直しなので「回避可能」欄は「手順を変えれば」の意味。
  - attempt = land tool (`tools/dev_wave_land.py`) の起動回数。wrapper 停止 = tool を起動せずに親の script が止めた回 (rc=97 「別 land 走行中」、rc=92 「incoming が実行体を変えた」)。「1 attempt」= tool 起動 1 回かつ wrapper 停止なし (tool 起動 1 回だけで数えると 14 本)。
- **時刻の出所:** wrapper log の時刻 (`land-loop.log` / `land-N.log` / `land-go.log`)、`*.started.txt` / `*.finished.txt`、file の mtime。JSON の `window_elapsed_s` は lock 取得後の窓だけで順番票待ちを含まない (`waited_s` は全件 0.0) ので所要には使わない。
- **rc の出所:** land JSON に rc は無い (status / reason だけ)。wrapper log の `rc=` 行、無ければ reason 文字列を `tools/dev_wave_land.py` の `_Reject(RC_..., "...")` / `LandResult(RC_..., ...)` に対応させた (`main moved outside the tested audited closure while locking` = 3424 行 rc=10、`landing tip does not contain locked main` = 2390 行 rc=10、`forward main merge first-parent commit must have exactly two parents` = rc=23、`fold gate failed: registered worktree path cannot be resolved` = 4102 行 rc=31)。
- 一次資料の dump は `land-attempts-timeline.txt` (23 wave 分、file ごとの mtime・status・reason・受入 receipt の verdict / tested main / tip)。rulings-all-20260921 の成功 JSON は `land-1.log` の中にあり dump には出ない (`window_elapsed_s` 203.46)。

## 2. 数表

### 表 1. wave ごと (JST、`waves-table.md` と同じ)

| wave | 最初の試行 | landed | land 局面 | 成功試行 | 追加 | 固有待ち | 回避可能 | tool rc 列 | wrapper 停止 | 受入投入 | land 起因の再受入 |
|---|---|---|---|---|---|---|---|---|---|---|---|
| t2797-b5-contrast | 04:54:42 | 05:26:06 | 31:24 | 4:36 | 26:48 | 0:00 | 26:48 | [23, 0] | - | 3 | あり |
| branch-residue-cleanup | 04:29:15 | 04:32:25 | 3:10 | 3:10 | 0:00 | 0:00 | 0:00 | [0] | - | 1 | - |
| t2817-acceptance-bottleneck-3 | 04:00:40 | 04:07:19 | 6:39 | 5:39 | 1:00 | 0:00 | 1:00 | [23, 0] | - | 3 | - |
| t2810-g1-launch-validation | 03:41:32 | 03:44:27 | 2:55 | 2:55 | 0:00 | 0:00 | 0:00 | [0] | - | 2 | - |
| t2814-cleanup-command | 03:16:02 | 03:19:32 | 3:30 | 3:30 | 0:00 | 0:00 | 0:00 | [0] | - | 2 | - |
| wall-decomp | 02:51:57 | 02:55:30 | 3:33 | 3:33 | 0:00 | 0:00 | 0:00 | [0] | - | 1 | - |
| paper-story-20260921 | 02:44:18 | 02:47:36 | 3:18 | 3:18 | 0:00 | 0:00 | 0:00 | [0] | - | 1 | - |
| paper-abstract-conclusion-ja | 01:59:34 | 02:02:28 | 2:54 | 2:54 | 0:00 | 0:00 | 0:00 | [0] | - | 1 | - |
| rulings-all-20260921 | 01:17:22 | 01:20:46 | 3:24 | 3:24 | 0:00 | 0:00 | 0:00 | [0] | - | 1 | - |
| t2344-closure-stage | 00:15:42 | 00:21:24 | 5:42 | 5:42 | 0:00 | 0:00 | 0:00 | [0] | - | 2 | - |
| t2803-provenance-receipt | 23:28:34 | 00:12:00 | 43:26 | 4:39 | 38:47 | 2:23 | 36:24 | [0] | [97, 92] | 3 | あり |
| t2804-provenance-timeout-contract | 23:26:46 | 23:30:57 | 4:11 | 4:11 | 0:00 | 0:00 | 0:00 | [0] | - | 2 | - |
| t2243-collection-diag | 23:08:17 | 23:13:14 | 4:57 | 4:57 | 0:00 | 0:00 | 0:00 | [0] | - | 2 | - |
| t2807-b8-prerun | 22:41:41 | 22:54:55 | 13:14 | 5:02 | 8:12 | 6:30 | 1:42 | [10, 10, 0] | - | 1 | - |
| t2813-o26-inventory | 22:35:06 | 22:49:08 | 14:02 | 5:36 | 8:26 | 5:14 | 3:12 | [31, 0] | [97] | 1 | - |
| k2-loop-originals-lost-downstream | 22:33:35 | 22:42:57 | 9:22 | 5:52 | 3:30 | 0:00 | 3:30 | [31, 0] | - | 1 | - |
| fig13-b10-waiting-grid | 22:13:05 | 22:18:53 | 5:48 | 5:48 | 0:00 | 0:00 | 0:00 | [0] | - | 1 | - |
| paper-related-work-ja | 22:02:52 | 22:12:48 | 9:56 | 5:19 | 4:37 | 4:03 | 0:34 | [0] | [97] | 1 | - |
| paper-story-20260920b | 21:56:39 | 22:06:55 | 10:16 | 10:16 | 0:00 | 0:00 | 0:00 | [0] | - | 2 | - |
| cleanup-backup-loss-record | 21:30:27 | 21:49:33 | 19:06 | 9:26 | 9:40 | 8:10 | 1:30 | [10, 0] | - | 3 | - |
| (annex) t2153-witness-requested-us | 21:30:25 | 21:38:37 | 8:12 | 8:12 | 0:00 | 0:00 | 0:00 | [0] | - | 2 | - |
| (annex) paper-intro-ja | 21:08:38 | 21:18:25 | 9:47 | 5:33 | 4:14 | 3:50 | 0:24 | [0] | [97] | 3 | - |
| (annex) t2766-pairing-adopt | 21:03:48 | 21:12:28 | 8:40 | 8:40 | 0:00 | 0:00 | 0:00 | [0] | - | 不明 | - |

「受入投入」は job dir の `acceptance-*.started.txt` (無ければ `.done`) の本数で、赤 (rc=70 など) も数える。受入側の原因は隣接 wave が分類する。t2813 の成功試行は wrapper 開始 22:40:02 → 走行中 land 0 を 210 秒待つ → 22:43:32 merge 開始 → 22:49:08 landed で、待ち 210 秒は追加 wall 側。

### 表 2. 往復の原因別 (20 本、秒 → 分)

| 原因 | 回数 (wave 数) | 追加 wall | うち固有の直列化待ち | 回避可能 | 受入の再走 |
|---|---|---|---|---|---|
| rc=23 → 受入取り直し (受入後の docs commit、t2797) | 1 (1) | 1,608 s = 26.8 分 | 0 | 26.8 分 (手順を変えれば) | あり (final3、22:57) |
| wrapper rc=92 → 受入取り直し (t2803、rc=97 停止 157 s と固有待ち 143 s を含む) | 1 (1) | 2,327 s = 38.8 分 | 143 s | 2,184 s = 36.4 分 | あり (final2 赤 → final3、21:47) |
| rc=10 stale-main (t2807 ×2、cleanup-backup ×1) | 3 (2) | 1,072 s = 17.9 分 | 880 s = 14.7 分 | 192 s = 3.2 分 | なし (前方 merge で追随) |
| rc=31 fold gate EINTR (k2-loop、t2813 の 22:36:53→22:43:32) | 2 (2) | 609 s = 10.2 分 | 226 s (t2813 が待った k2-loop の it=2 は k2-loop 自身の EINTR 再投入) | 383 s = 6.4 分 (k2-loop の it=2 も数えれば 10.2 分) | なし |
| wrapper rc=97 別 land 走行中 (paper-related、t2813 の 22:35:06→22:36:53) | 3 (3、t2803 分は上の行) | 384 s = 6.4 分 | 331 s | 53 s | なし |
| rc=23 理由不明 (t2817、reason は stdout 上書きで消失) | 1 (1) | 60 s | 0 | 60 s | なし |
| rc=25 postcondition / rc=26 fold-owned / rc=11 lock-busy | 0 | 0 | 0 | 0 | - |
| **合計** | **拒否 7 + wrapper 停止 4** | **6,060 s = 101.0 分** | **1,580 s = 26.3 分** | **4,480 s = 74.7 分** | **2 本** |

検算: 原因別の追加 wall の和 6,060 s = wave ごとの追加 wall の和 6,060 s (`waves.json` の `extra_by_cause_check_sum_s`)。受入取り直し 2 本の関連追加 wall 3,935 s は受入 final3 自体の所要 (22:57 + 21:47 = 44:44) とは別の量。

### 表 3. 1 attempt と往復の差

| | 1 attempt (12 本) | 往復 (8 本) |
|---|---|---|
| land 局面 (min / median / max) | 2:54 / 3:32 / 10:16 | 6:39 / 13:38 / 43:26 |
| land 局面の合計 | 3,218 s = 53.6 分 | 8,829 s = 147.2 分 |
| 成功試行の合計 | 3,218 s | 2,769 s = 46.2 分 |
| 前方 main merge (`incorporated_main_shas` 非空) を伴う wave | 5 (t2814、wall-decomp、t2344、fig13、paper-story-20260920b) | 6 (t2807、t2813、k2-loop、paper-related、cleanup-backup、t2817) |

**前方 main merge を伴う 11 本は全部、受入を取り直さずに landed** (D987 の経路が機能している)。1 attempt 側の 10:16 (paper-story-20260920b) と annex の 8 分台 (t2153 / t2766) は `window_elapsed_s` 482〜570 秒で、21:00〜22:10 の混雑窓 (70 分に 6 本の land) の監査・fold gate の遅さによる。成功 land の `window_elapsed_s` は 20 本で min 168.0 / median 273.4 / 18 番目 (nearest-rank の p90) 326.4 / 19 番目 533.0 / max 569.9 秒 (四捨五入の昇順: 168, 174, 188, 189, 190, 195, 203, 225, 250, 272, 275, 275, 278, 296, 299, 307, 317, 326, 533, 570)。median は D2119 が記録した n=34 の 272 秒と近い。

## 3. 分類ごとの機序 (source の位置)

### 3.1 rc=10 stale-main (3 回)

- 判定箇所: `tools/dev_wave_land.py` `_locked_preflight` — landing tip が tested tip と同じなら `_main_is_allowed` (2601 行) で locked main が tested main か監査列の中にあることを要求し、外れると 3424 行の `main moved outside the tested audited closure while locking` (t2807 の 1 回目、cleanup-backup — どちらも landing tip = tested tip、merge なし)。前方 merge 済みの landing tip なら `_verify_locked_forward_main` (2375 行) で「landing tip が locked main を含む」ことを要求し、外れると `landing tip does not contain locked main` (t2807 の 2 回目)。
- 3 回とも同じ形: 投入時に別 wave の land が順番票を持って走っており (t2807-1: k2-loop の it=2、t2807-2: t2813 の land-3、cleanup-backup: t2153)、自分は landing tip を固定したまま順番待ちに入り、相手が landed して main が進んだ直後に grant を受けて locked main と照合され拒否された。順番票は stale-main で seq を保持しつつ order を末尾へ回す (D2119 項 3、`_finish_land_turn` 3006〜3017 行) ので、待ち行列に 3 本目がいれば同じことが繰り返される (t2807 が 2 回連続)。
- 回避可能分は「再 merge (6〜12 秒) + spool dry-run (5〜6 秒) + 失敗した試行の preflight (15〜90 秒) + 親の再投入までの間 (30 秒前後)」で 1 回 1〜1.5 分。残り (14.7 分) は相手の land が終わるまでの待ちで、投入順序を変えても消えない。

### 3.2 rc=31 fold gate EINTR (2 回)

- 判定箇所: `_registered_worktree_paths` (4083〜4107 行) が `git worktree list --porcelain` の全登録 path (probe 時点で 23 本、うち 6 本が `dev-wave-jobs` 配下の submit-tree) を `Path.resolve(strict=True)` し、`FileNotFoundError` 以外の `OSError` を `_FoldGateFailure` (既定 `retryable_same_request=False`) に変換する。
- 呼び出し位置: `_run_fold_gate` (4557 行) が `with _FoldGateOuterWatchdog(budgets.outer_seconds):` の中で `_execute_fold_gate` (4441 行) を呼び、その先頭 (4446 行) で `_registered_worktree_paths` が走る。`_FoldGateOuterWatchdog.__enter__` (4418〜4432 行) は `signal.setitimer(ITIMER_REAL, 0.1, 0.1)` で SIGALRM を 100 ms 周期にし、Python の handler `_alarm` を登録する。登録 path の解決も outer watchdog の期限 (145 秒) の監督下にある。
- Python 側: CPython 3.10.12 の `os.path.realpath` → `posixpath._joinrealpath` は `os.lstat` と `os.readlink` を使う (login で `inspect.getsource(posixpath._joinrealpath)` に両語が含まれることを確認。job dir の `realpath_impl.py` は `realpath` 本体だけを見るので `_joinrealpath` は別の 1 行で確認した)。両者の C 実装 (`Modules/posixmodule.c`) に EINTR の自動再試行 loop は無く、PEP 475 の対象 (`os.open` / `read` / `write` / `fstat` / `waitpid` など) にも入っていない。
- **仮説 (未検証):** handler 付きの SIGALRM が、Lustre 上の遅い metadata 呼び出し (interruptible になる wait) を中断し、`InterruptedError` がそのまま上がった。整合する観測: 2 回とも 09-20 22:36〜22:39 の混雑窓 (同時刻に land が 3 本)、path は他 wave の submit-tree (`dev-wave-t1505-a1-sized-submit` / `dev-wave-t2792-a1-sized-attempt2`、どちらも Lustre 上で今も登録・実在)、`main_before == main_after`、直後の再投入は通った。F672 の既存 EINTR 5 例 (08-27、09-10、09-17、09-19 ×2) と同型で、本 2 例を足して EINTR 型 7 例 (別型の ENOENT 1 例は含めない)。**「その SIGALRM が今回の EINTR を起こした」「混雑が必要条件」は静穏時の非再現からは導けない。**
- 静穏時 probe (job dir の `eintr_probe.py`、sha256 先頭 `634fe7a8ce7944e1`): 登録 23 path × 20 周 = 460 回の resolve を timer 無し / 100 ms 周期 / 1 ms 周期で回して EINTR 0 回、resolve 0.04 ms/回。
- 同一 request の再試行可否: 現行は `retryable_same_request=false` → `_finish_land_turn` で phase `rejected` → 順番票の entry を削除 (D2119 項 3「fold gate 赤は seq 削除」)。receipt は消費されず (`release_safe=true`)、main も不変なので、**同じ tested tip / landing tip / receipt で再投入すると `_register_land_turn` (2881 行〜) が新しい seq で新規登録し、検査を再実行する** (成功は保証しない — main の前進などで再拒否されうる)。k2-loop ではその再投入 (it=2、22:37:05) が 22:42:57 に landed した。失うのは待ち行列の順番。F672 の復旧文「受入を取り直して新しい request を作るしかない」は現行 source と合わず、従うと受入 1 走 (10〜25 分) を無駄にする。D1321 は stale/busy の裁定であり fold gate 赤には及ばないので、本項は「source 上そう動く」以上の裁定を主張しない。

### 3.3 terminal-merge 起因の受入取り直し (t2797、rc=23)

- 受入 final2 (04:40:32〜04:52:36、tested tip `088bbdec7`) の後、親が段 7 の insight 追記 `cf1c90e1f` (1 親の docs commit、04:54:09) を積み、land try1 (04:54:42) が `_forward_main_merge_topology` の「tested tip → landing tip の first-parent 列は 2 親の merge だけ」で rc=23。親は受入 final3 (04:57:50〜05:20:47、22:57) を取り直し、land-1 (05:21:30〜05:26:06) で landed。
- 契約どおり (land は受入後の編集を受け付けない)。追加 wall 26.8 分のうち 23 分が受入。消すには「受入結果の追記を land 前の commit にしない」手順が要り、隣接 wave の裁定 (分類 5) に委ねる。

### 3.4 wrapper rc=92 (t2803) — 契約が要求しない受入取り直し

- t2803 の `land-go.sh` (job dir) 32〜36 行: `MB=$(git merge-base "$LANDING" "$MAIN_NOW")` から `git diff --quiet "$MB" "$MAIN_NOW" -- tools/run_tests.py tools/dev_wave_wait.py tools/check_acceptance_reds.py tools/dev_wave_land.py` が非 0 なら「incoming changes runner/waiter/reds checker/land -> stop」で rc=92。
- 実際の差分 (`git diff --stat 1cc303534 6305f2d05 -- <4 file>`): `tools/dev_wave_land.py` 9 行 (t2804 の provenance timeout 契約) だけ。`tools/run_tests.py` は不変。
- land tool の契約: D987 (2026-08-26) と D1234 (2026-08-28) — 「最終 incorporated main と tested main の runner blob の net 差で判定し、変わった場合だけ旧 receipt の再利用を拒否する」。実装は `_verify_forward_main_runner_blob` (887 行、receipt の tested main と最終 incorporated main の `tools/run_tests.py` tree entry を比較)。waiter (`tools/dev_wave_wait.py`) と checker (`tools/check_acceptance_reds.py`) の受領証束縛は tested tip の tree (checker は verdict `non-attributable-only` のとき tested main の tree も) に対して照合する (1119〜1175 行) ので、main 側で変わっても拒否しない。land 自身の bytes は束縛しない (`executed_bytes_sha` は provenance checker のもの)。指定資料 (D987 / D1234 / DW-O23 / DW-O25 / F524) に、land 時の 4 file 検査を要求する文は無い (段 6 レビューも同じ結論)。
- したがって、この差分は D987 の再受入条件に該当しない。**旧 receipt のまま前方 merge → land する経路は t2803 では実測されていない** (実際の成功は final3 の新 receipt、tested tip `65966f4d8`、`incorporated_main_shas=[]`)。同じ形 (main 側の変更を前方 merge して旧 receipt で land) は本母集合の他 11 本で通っている。wrapper の 4 file 検査は、F524 が受入**投入前**に課す「待ち手・launcher・runner の bytes を変える前進は先に取り込む」を、land 時にも・`dev_wave_land.py` にも広げたもの。追加 wall 38.8 分 (受入 final2 の wrapper 赤 rc=94 と final3 21:47 を含む) のうち固有待ち 143 秒を除く 36.4 分が回避可能。

### 3.5 wrapper rc=97 (3 回 + annex 1 回)

- 親の script が `pgrep -fc dev_wave_land.py` で別 land を見つけて停止し、次回は main を固定し直してやり直す。paper-related と paper-intro と t2813 は merge と spool dry-run を済ませた後に停止し (merge commit 自体は次回に引き継がれ、次回は新しい main をさらに merge する — paper-related の成功 JSON は `incorporated_main_shas=[1ee9ef2cb, 7f4d6debe]`)、t2803 は main が HEAD に含まれていたので merge も dry-run もせずに停止した。捨てるのは dry-run と確認の時間 (1 回 20〜60 秒) で、待ち自体 (相手の land 終了まで) は固有。
- rc=10 と同じ「投入時に別 land が走っている」条件を、tool 起動前に気づいた版。t2813 の land-3 の wrapper (`land-go2.sh`) は逆に「走行中 land 0 になるまで 30 秒周期で待ってから main を固定 → merge → 投入」の形 (§5.2 の B と同じ) で、210 秒待って 1 回で landed。

### 3.6 rc=23 理由不明 (t2817)

- 04:00:40 前方 merge → 04:00:58 rc=23 (`not retryable -> stop`)、拒否の 42 秒後 (04:01:40) に同じ landing tip `4cb00a851` で再投入 → 04:07:19 landed。reason と失敗時の receipt digest は `land-1.stdout` を 2 回目が上書きして消えた。確認できるのは rc=23 と、同じ landing tip の再投入が通ったことだけで、原因は不明。出力 file を attempt ごとに分けないと失敗本文が残らない (再試行の前に失敗の本文を読む、の前提が壊れる)。

## 4. 1 attempt で終えた wave との差

- 1 attempt の 12 本は、投入時に別 land が走っていない (job dir の相互参照で確認: 各 wave の land 開始時刻に他 wave の land 区間が重ならない) か、走っていても順番票の grant 前に相手が landed して main が監査列の中に留まった (t2344 は `5733c0f08` を前方 merge 済みで投入し、その間に main は動かず)。
- 往復した 8 本のうち 5 本 (t2807、t2813、paper-related、cleanup-backup、t2803) は投入時に別 land が走っていた。k2-loop (22:33:35 投入) は最初の投入時に別 land は走っておらず、EINTR だけが原因。残る 2 本 (t2797、t2817) は自分の tip / 監査の問題。
- 受入投入回数との相関は無い (1 attempt 側も 2〜3 回投入した wave が 6 本ある)。受入の再走を land 側が強いたのは 2 本 (t2797、t2803) だけ。

## 5. 裁定パッケージ (実装しない、効果見積り付き)

受理集合・provenance 監査・fold 契約を変えないことを採用条件とする。規律 2 に触れない (受入は取り直さず、赤を弱めない)。効果見積りは表 2 の「回避可能」区間を各修正に割り当てた値で、実測削減量ではない。

### 5.1 A: F672 経路の局所修正 — `InterruptedError` を armed 区間内で有界に再試行する

- 変更: `_registered_worktree_paths` (4083〜4107 行) の `path.resolve(strict=True)` を、`InterruptedError` だけ有界 (例: 5 回、sleep なし) に再試行する。**watchdog の armed 区間内に留める** (outer 145 秒の期限監督は保つ — 期限超過は現行どおり handler が `_FoldGateInfrastructureFailure` を投げ、`except (OSError, UnicodeError)` には捕まらない)。再試行を使い切ったら現行どおり `_FoldGateFailure`。D2119 項 3 の rc 分類 (fold gate 赤 = seq 削除) と `_FoldGateInfrastructureFailure` の使い分けには触れない (F672 が裁定へ送った「retryable へ再分類」とは別の、原因側の修正)。登録一覧の snapshot と使用の間の race は現行と同じ。
- 却下した変形: resolve を `with _FoldGateOuterWatchdog` の前へ出す (hoist) — 解決が期限外になり、遅い syscall の停止時間を何も制限しなくなる (段 6 レビュー所見 3)。
- 効果見積り: 本母集合の rc=31 2 回 (追加 wall 10.2 分) のうち 383〜609 秒 = 6.4〜10.2 分 (上限は t2813 の待ち 226 秒を含み、その分は表 2 の固有待ち 26.3 分から差し引く)。F672 の EINTR 型 7 例が同経路。混雑窓では t2813 の EINTR が t2807 の 2 回目 rc=10 を誘発した (t2813 の再 merge が t2807 の前に並んだ) ので、連鎖分も減りうる。仮説 (§3.2) が正しくない場合 (EINTR の発生源が別) でも、再試行は同じ syscall をやり直すだけで害は無い。
- 検査: 変異 = 再試行を外す (現行の形へ戻す) と、SIGALRM handler 下で `InterruptedError` を 1 回注入する test が赤になる正例・負例 (Codex author、実装 wave で登録)。
- 費用: 数行。実装 wave 1 本 (軽量版)。

### 5.2 B: 呼び手 loop の順序 — 「走行中 land 0 を確認 → 固定 SHA merge → 即投入」

- 変更: `DW-O23` の loop 形 (memory「land-race-close-with-fixed-sha-merge-loop」に同じ) を「merge の**前**に `pgrep -fc '^python3( -u)? [^ ]*dev_wave_land[.]py'` (または順番票 registry) で走行中 land を確認し、0 になるまで有界に待ってから main を固定して merge → dry-run → 即投入」にする。t2813 の `land-go2.sh` (30 秒周期、上限 1,800 秒) が先例。現行の rc=97 wrapper は merge の**後**に確認して止まる。docs-only (`docs/dev-wave/operations.md` `DW-O23` の 1 文と land memory)。
- 効果見積り: rc=10 3 回の回避可能分 192 秒と rc=97 3 回の 53 秒、合計 245 秒 ≈ 4.1 分 / 20 wave。固有の直列化待ち (14.7 分) は消えない。事前待機で競合窓 (merge 6〜12 秒 + dry-run 5〜6 秒 + tool 起動〜preflight 15〜90 秒 = 26〜108 秒) の短縮を狙うが、`pgrep = 0` は予約ではなく複数の wrapper が同時に通過できるので、競合回避は保証しない。
- 検査: docs の文だけ。実測は次の混雑窓の land で rc=10 の回数を数える。本 wave の land もこの形で投入し、結果を §7 末尾に書く。
- 費用: 文 1〜2。

### 5.3 C: 呼び手の land 前 guard を D987 / D1234 の比較基点に一致させる

- 変更: 前方 merge の前に「incoming が実行体を変えたか」を見る呼び手の guard は、**receipt の tested main と、今回取り込む固定 main SHA の `tools/run_tests.py` blob** (`git rev-parse <tested_main>:tools/run_tests.py` と `git rev-parse <main_sha>:tools/run_tests.py`) を比較し、違うときだけ受入取り直しにする (source の `_verify_forward_main_runner_blob` と同じ基点)。`merge-base HEAD main` と可変 ref `main` の diff ではない (tested main の runner が A → main で B → 再び A に戻った場合、D1234 は再利用を許すが diff 基点の guard は止める)。`tools/dev_wave_wait.py` / `tools/check_acceptance_reds.py` / `tools/dev_wave_land.py` の差分は前方 merge で取り込んで land する (受領証の束縛先は tested tip / tested main の tree)。F524 の「待ち手・launcher・runner」検査は受入投入前にだけ当てる。docs-only (memory「land は incoming が実行器を変えたか検査しない — 呼び手の責任」の是正と `DW-O23` の 1 文)。
- 効果見積り: t2803 の 2,184 秒 = 36.4 分 (本母集合の追加 wall の 36%)。同型は main が land / waiter / checker を変えた直後の窓で毎回起きうる (09-20 23:30 の t2804 着地の直後がそれ)。
- 検査: docs の文だけ。land tool 側は D987 を既に強制しており (`_verify_forward_main_runner_blob`)、guard を狭めても受理集合は変わらない。
- 費用: 文 1〜2。

### 5.4 提案しないもの (理由)

- 順番票の order を stale-main で保持する — D2119 が「stale-main request 2 本が保持 seq のまま先頭を交互に占め、後続 10 本が期限切れ」の実測から意図的に回転させている。本母集合でも回転が飢餓を作った例は無い。
- provenance 監査を順番票の外 (登録前) へ出して直列区間を縮める — 直列区間は median 273 秒で、その大半が監査 (≤480 秒) と fold gate (130 秒予算) だが、D2119 の却下択「監査を lock 内に置く、plan 作成を lock 外へ出す — lock 区間の移動では直らない」に隣接し (D2119 がこの案そのものを却下したわけではない)、監査の TOCTOU 束縛 (DW-O25 の receipt 再照合) の設計変更になる。本 wave の scope (局所修正) 外。
- land tool 自身に前方 merge をさせる — 「merge / add / commit は親、子は競合解決だけ」(DW-C01) と、親の merge を replay で検証する契約 (`_replay_forward_main_merges`) の反転。
- 受入後の docs commit を land が受け付ける (t2797 型) — 受理集合の変更。scope 外。隣接 wave の裁定に委ねる。
- 出力 file 名の attempt ごとの分離 (t2817 の reason 消失) — wrapper は wave ごとの使い捨てなので gate にしない。memory の loop 形に「attempt ごとに別 file」を 1 句足すだけ (段 8 候補)。

### 5.5 効果の合計 (削減候補区間の割当て、実測削減量ではない)

| 修正 | 割り当てた区間 (本母集合 20 本) | 種別 |
|---|---|---|
| A (EINTR の有界再試行) | 383〜609 s = 6.4〜10.2 分 | code 数行 (Codex author) |
| B (loop 順序) | 245 s = 4.1 分 | docs 1〜2 文 |
| C (guard の比較基点) | 2,184 s = 36.4 分 | docs 1〜2 文 |
| 合計 | 2,812〜3,038 s = 46.9〜50.6 分 / 101.0 分 (46〜50%) | |
| 残り | t2797 型 26.8 分 (隣接 wave)、固有の直列化待ち 26.3 分 (A の上限を採るなら 226 秒を引いて 22.6 分)、理由不明の rc=23 1 分 | |

## 6. 既存被覆との関係 (二重に数えない)

- F672 (EINTR の非再試行分類): 事象・根本原因は既知。本資料の純増は (1) source での呼び出し位置 (watchdog の armed 区間内) と CPython 3.10.12 の `_joinrealpath` / PEP 475 範囲の確認、(2) 同一 request の再投入が新規登録として通る実測 (k2-loop)、(3) EINTR 型 6 / 7 例目。failures fragment で再発 2 件を追記する。
- D987 / D1234 (runner blob の net 差だけが再受入): 契約は既知。純増は「呼び手の guard が契約より広く、38.8 分の取り直しを 1 回誘発した」実測と、guard の正しい比較基点。
- D1321 (stale/busy で止めずその場で再試行)、D2119 (順番票、order 回転、seq 削除の rc 分類): 契約は既知。純増は「rc=10 の 3 回が全て投入時の別 land 走行中に起きた」形と、回避可能分 (3.2 分) と固有待ち (14.7 分) の分離。
- memory `land-discipline` (2026-09-20 追記「land-go.sh は別 wave の land 走行中で rc=97 の後に再実行不可、fold gate の EINTR は一過性」): 本資料はその定量化。
- 隣接 wave `dev-wave-acceptance-resubmit-causes`: 受入投入回数 (表 1 の列) は数えるだけで原因は分類しない。t2797 の rc=23 型はそちらの分類 5。

## 7. 限界・言わないこと

- 母集合は job dir に land 記録がある wave 20 本。同じ窓の着地 21 件のうち job dir 外は 1 件 ([T-2501]、rc=10 の merge message あり) で、その追加 wall は測っていない。窓より前の着地は母集合外。
- 「固有の直列化待ち」は相手 wave の land 区間の重なりで測った。親が land 投入前に自主的に待った時間 (例: paper-story-20260920b の受入緑 21:44 → land 開始 21:56) は「land 局面」に入らないので、1 attempt 側の待ちは過小に見える可能性がある。
- rc=31 の機序のうち source の位置と CPython の実装は確認したが、「SIGALRM が今回の EINTR を起こした」「Lustre の混雑が必要条件」は未検証の仮説 (静穏時 probe は 0 回、混雑時の再現は試していない)。修正 A の効果見積りは「同経路の 7 例が消える」前提で、EINTR の発生源が別なら再試行の効き方は変わりうる (害は無い)。
- t2817 の rc=23 の reason は失われており、言えるのは「同じ landing tip の再投入が通った」ことだけ。
- t2803 について「旧 receipt で前方 merge → land が通った」とは言わない (未実測)。言えるのは「差分は D987 の再受入条件に該当しない」まで。
- 効果見積りは本母集合 (09-20 21:30〜09-21 05:26、混雑窓を含む 8 時間) の回避可能区間の割当てで、実測削減量ではない。混雑度が違う窓では比率が変わる。
- 受入側の赤 (rc=70 / 91 / 94) の原因は分類していない (隣接 wave)。
- 本資料は実装 0 行。A / B / C は裁定パッケージで、採用は人間の裁定。
- 段 6 レビュー (codex read-only、1 本、08:07〜08:19 JST): 所見 17 件 = real 14 (must-fix 6: t2813 の成功試行開始、65.6 分の集計、A の期限監督、C の比較基点、EINTR の断定範囲、母集合外の説明 / should 7 / nit 1)、refuted 2 (表の引き算・分類・rc 対応、固有待ち区間の重なり)、判定不能 1 (任意 file 名の母集合の完全性)。全件を本版に反映した。逐語は job dir `codex/s6-review-A.md`。
- 本 wave の land (§5.2 の B の形で投入) の結果は fold 後に確定するため、本 README には書かない (worklog の次 entry か job dir の `land-loop.log`)。

## 8. この dir の中身

- `README.md` — 本文。
- `waves.json` — 表 1 の元 (20 本 + annex 3 本、各行に出所 file 名)、集計 (`summary`)、原因別 (`extra_by_cause_s`)。
- `waves-table.md` — 表 1 (同じ値)。
- `land-attempts-timeline.txt` — 23 wave の job dir から起こした file ごとの時系列 (mtime / status / reason / receipt の verdict と tested main / tip / wrapper log の `rc=` 行)。rulings-all-20260921 の成功 JSON (`land-1.log` 内) は含まない。
- 抽出 script は repo に入れない (job dir `/work/1/SFC/tanab/dev-wave-jobs/dev-wave-land-roundtrip-diagnosis/`、sha256 先頭 16 桁: `list_landed.py` 22445db0894486f5、`chain_landed.py` ea7103154df7801c、`dump_land_attempts.py` 38fd53975615f326、`build_table.py` 75e8b2806f0a1ce1、`find_landed_any.py` 30706e7cebb84685、`eintr_probe.py` 634fe7a8ce7944e1、`realpath_impl.py` f4ee50de55281c66)。`find_landed_any.py` は file 本文の文字列一致なので、他 wave の集計 file (例: 隣接 wave の `timeline*.txt`) を偽陽性で拾う — 20 本の同定は各 dir の `land*` file を手で確認した。

## 9. 再現手順

1. `/work/1/SFC/tanab/dev-wave-jobs/` の各 dir で `land*` の名前の file に `"status":"landed"` を含むものを探し、その file の mtime 降順で 20 本を取る (file 名は wave ごとに `land-N.json` / `land-attempt-N.json` / `land-N.log` / `land-N.stdout` と違う。本文に同じ文字列を含む集計 file を除く)。
2. 各 dir の `land*.json` / `land*.stdout` (status / reason / `incorporated_main_shas` / `window_elapsed_s`)、`acceptance-receipt*.json` (verdict / tested_main / tested_tip)、`acceptance-*.started.txt` / `.finished.txt` / `.done`、`land*.log` の `rc=` 行を mtime 順に並べる (`land-attempts-timeline.txt` の形)。
3. wrapper log から「最初の land 試行の開始」「成功試行で merge を始めた時刻」「landed」の時刻を取り、land 局面・成功試行・追加 wall を引く。別 wave の land 区間は相手の job dir の同じ file から取る。
4. rc は wrapper log の `rc=` 行、無ければ reason 文字列を `tools/dev_wave_land.py` の `_Reject(RC_..., "...")` / `LandResult(RC_..., ...)` に対応させる。
5. source の位置は `grep -n "_registered_worktree_paths\|_FoldGateOuterWatchdog\|setitimer" tools/dev_wave_land.py`、Python 側は `inspect.getsource(posixpath._joinrealpath)` に `lstat` / `readlink` が含まれることで確認する。
