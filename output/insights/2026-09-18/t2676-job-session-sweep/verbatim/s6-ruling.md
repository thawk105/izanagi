# [T-2676] 段 6 裁定 — レビュー所見と fix 仕様 (2026-09-18 07:40 JST)

## 所見の裁定

| 所見 | 判定 | 処置 |
|---|---|---|
| RA-1 / RB-1 TERM fixture が既定動作を確立していない、正常版が赤、猶予・期限の根拠不足 (must-fix) | real | **F1 / F2**。親の login 再現 (`probe_term_repro.py term`): 同構成で after=term 0.5 ms → login では緑。計算ノード job 内の差 = 祖先の signal 状態の継承が有力 (probe `probe_sigign.py` を request 5043 で採取中。結果は insight へ)。原因の確定に依らず、C に SIG_DFL + unblock を明示するのが正しい fixture |
| RA-2 session 所属不明の stat 読取り失敗が集計を汚す | real (仕様との差) | **F4**: `unreadable` → `session_unknown`、status ∈ {clean, remaining, unknown}、error は wrapper 例外のみ。判定表 §3 の「unreadable 0」は「session_unknown 0」に読み替え (非 0 は期待外として記録、成功にしない) |
| RA-3 M2 は祖先保護の挙動を検出しない (台帳 must-fix) | real | **台帳処置**: M2 は帰属述語に守られる冗長 gate の **diagnostic sensitivity pin (別枠)** として記録し、「祖先の誤殺を検出した」とは書かない。挙動検出の別 fixture (S を入れ子 ns、L を外) は production 構造と離れるので本 wave では登録しない |
| RB-2 finally が group 全員の終了を確認しない (must-fix) | real | **F3** |
| RA-4〜RA-7、RB-3〜RB-6 | refuted | 同意。RA-6 の「job 内 SIGTERM が必ず `_SignalAbort` とは言えない」は insight の言えないことへ |
| RA-8 trace の field 配置 (`process.pid`) | nit | insight の trace 仕様表記を実装 (`process` 入れ子) に合わせる。コードは変えない |
| RB-7 3 本を 1 本へ統合しない | nit | 同意 (3 nodeid 維持) |

## 確定 fix 仕様

- **F1**: `_SESSION_ORPHAN_SOURCE` の C (と `late` の G) は mode 別設定の前に `signal.signal(SIGTERM, SIG_DFL)` + `pthread_sigmask(SIG_UNBLOCK, {SIGTERM})`。失敗時の assert message に records / mode / 実所要を出す。期待値は緩めない。
- **F2**: 期限 = 準備 15 秒 / sweep 20 秒 / 回収 10 秒 (絶対打切り、固定 sleep なし)。scanner は production wrapper を production 定数 (5.0 / 1.0 / 2) のまま走らせる (差し替えは記録して無変更で委譲するだけ)。
- **F3**: finally は L・D・N・C・G の pidfd で回収期限内の全員終了を確認。各後始末段は独立に続行。subreaper / 非子 waitpid 不使用。
- **F4**: 上記 RA-2 の処置。対応する新規テストの期待も更新 (意味を弱めない)。

## 変異登録の更新 (段 4 §2 の 2 段階目、fix 後・変異実行前に親が行を再固定)
M1〜M7 の変更前 1 行はレビュー B の一意性表 (DC 1906 / 928 / 908 / 877 / 809 / 829 / 775、fix 後に再照合)。M2 = 別枠 (diagnostic sensitivity pin)。期待 node 完全集合は較正走 (SURVIVED 期待の probe 走) で実測して固定 (DW-M08)。

## 焦点走の事実 (5015.nqsv、計算ノード)
14 passed / 1 failed (term mode)。同 job の job body sweep は本番経路で走った: ancestors = python3.10 (542579) → bash (542560) → nqs_shpd (542559 = sid) → nqs_shpd (542362) → nqs_shpd (2233) → systemd (1)。found_total 0、status clean、elapsed 33.8 ms、W→J ≈ 0.141 秒。**session leader は NQSV の `nqs_shpd`** (F-1 の未採取だった祖先鎖がこれで採れた)。
