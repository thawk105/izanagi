## 総括

- **closed 0 / partial 5 / regressed 0**。F1〜F4 は実装済み、統合動作は未実走です。
- 変更は指定の production・test の2 file のみ。docs・commit・branch 操作なし。
- TERM 初期化相当の単体確認は成功。
- M1〜M7 の変更前文字列は各1箇所。`git diff --check` 成功。
- 最終 AST 検査は審査拒否、pytest・変異実走は未実施です。

## 対応表

以下、DC＝[dispatch_compute.py](/work/1/SFC/tanab/izanagi/.codex/worktrees/t2676-impl/tools/pegasus/dispatch_compute.py)、TEST＝[test_pegasus_dispatch_compute.py](/work/1/SFC/tanab/izanagi/.codex/worktrees/t2676-impl/orchestrator/tests/test_pegasus_dispatch_compute.py)。

| 所見 | 状態 | 根拠 |
|---|---|---|
| RA-1 | partial | TEST:7747・7754：C/G の SIG_DFL＋unblock。TEST:7834：診断追加。fixture 全体未実走 |
| RA-2 | partial | DC:891〜902：`session_unknown` と残存集計を分離。対応テスト未実走 |
| RA-3 | partial | DC:928／TEST:7930付近：M2 のコード維持。diagnostic sensitivity pin として親の台帳処置待ち |
| RB-1 | partial | TEST:7774・7834：15/20/10秒の期限、production 引数を無変更で委譲。負荷下未実走 |
| RB-2 | partial | TEST:7834・7992：PID通知、pidfd追跡、共通回収期限でpoll、後始末エラー集約。未実走 |

## 変更点

- TERM の期待値を維持し、失敗時に records・mode・準備/sweep/回収の実所要を出力します。
- scanner の猶予上書きを削除。production の 5.0/1.0/2 と定数 assert を維持しました。
- 専用 pipe で N/C/G 等を通知し、sweep 中にも pidfd を取得。後始末は各段の失敗後も続行します。
- 最終 status は残存優先の `remaining`、所属不明のみなら `unknown`、双方なければ `clean`。新規テストに unknown 単独ケースも追加しました。

## 変異対応表

変更前行・行番号とも維持。`rg -n -F` で各1箇所を確認しました。

| 変異 | DC行 | fix後の変更前1行 | 一意性 |
|---|---:|---|---|
| M1 | 1906 | `_maybe_sweep_job_session(request_sha256)` | 1 |
| M2 | 928 | `excluded = {ancestor["pid"] for ancestor in ancestors}` | 1 |
| M3 | 908 | `if request_sha256 is None or os.environ.get(_JOB_SESSION_SWEEP_ENV) != request_sha256:` | 1 |
| M4 | 877 | `_signal_session_process(fd, record, signal.SIGKILL)` | 1 |
| M5 | 809 | `events = poller.poll(math.ceil(remaining * 1000))` | 1 |
| M6 | 829 | `for round_index in range(rounds):` | 1 |
| M7 | 775 | `attributed = user_ns is not None and user_ns != own_user_ns` | 1 |

M2 は **diagnostic sensitivity pin（別枠）**です。祖先誤殺の挙動検出とは申告しません。

## 未実走・限界

単体確認では、SIG_IGN と block mask を継承した process が、fixture 相当の初期化後に SIGTERM で終了しました。fork・namespace・sweep を含む fixture 全体の検証ではありません。pytest、変異較正、計算ノード再走、受入全走は未実施で、KILLED・closed は申告しません。

自動実行審査 `guard_bash` が、最終2 file と埋め込み source の AST 検査を「Pegasus ログインノード上の未登録実行体」として拒否しました。最終 AST 検査は未完了です。