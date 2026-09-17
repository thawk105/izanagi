## 所見

- **A1｜正しさ・timeout 競合｜tools/cleanup_remove_dirs.py:104,216｜推奨: must-fix**
  `expired` に入った子が、`cancel()` 冒頭の `_live()` による再 poll までに rc 0 で終了すると、`child.cancelled=True` を通らない。path が消えていれば `removed`、全件同様なら **timeout 検出済みにもかかわらず rc 0** になる。timeout 検出時点で対象の取消を記録し、送信対象だけを生存確認で絞る必要がある。現行 timeout test は STOP 状態を維持するため、この競合を検出しない。
  **放置時の成果物影響:** timeout を完了扱いし、prune へ進めてしまう。

- **A2｜signal 応答性｜tools/cleanup_remove_dirs.py:114,218｜推奨: must-fix**
  `cancel(expired, SIGTERM)` の猶予待ち中は、handler が立てた `cancelled` を読まない。期限超過した子 A が TERM で終了しない間に launcher が INT/HUP/TERM を受けても、期限未超過の生存子 B への転送は最大約 6 秒遅れる。50 ms sleep はあるが、そこで全体取消へ移行できない。取消待機中も flag を確認し、全生存子への取消へ拡張する必要がある。
  **放置時の成果物影響:** launcher 中断後も、別の撤去子が猶予期間中に削除を続ける。

- **A3｜出力整合性｜tools/cleanup_remove_dirs.py:241,258｜推奨: nit**
  summary 作成後、flush 完了前に signal が入ると、JSON は `rc:0, cancel_signal:null`、実際の終了コードは 2 になり得る。最後の再集約があるので **CLI の rc 0 漏れではない**。ただし `_finish()` の「summary rc＝終了コード」という前提には例外がある。出力中断時も含め、終了コードを最終判定とする契約を明記したい。
  **放置時の成果物影響:** JSON だけを読む consumer が成功と誤認する余地が残る。

- **A4｜テストの実行環境・期限｜orchestrator/tests/test_cleanup_remove_dirs.py:54,134,160｜推奨: nit**
  children 数一致＋全員 T、pending bit 観測後の CONT は通常の起動競合を避けている。ただし `/proc/.../children` が提供されない環境では同期失敗し、高負荷では総期限 6 秒・pending 期限 2 秒で偽陰性になり得る。必要な procfs 機能を明示し、同期失敗時に状態を診断出力するとよい。`_cleanup()` の CONT→KILL には wrapper が一瞬進む余地があるが、対象はテスト用 directory に限られる。
  **放置時の成果物影響:** 環境不足や負荷による赤を、機構の退行と取り違えやすい。

その他の確認結果：

- `fault`、unknown、interrupted、件数不一致は集約で rc 2。分類途中の例外で `results=[]` でも成功しない。
- spawn/PGID/poll/出力例外は取消経路を通る。`process=None` は送信できないが、spawn 例外時は `current.error` により unknown。継続的な poll 例外は生存候補に残り、最終的に unknown になる。
- KILL 前に再 poll するため、通常は TERM で回収済みの子へ再送しない。poll 自体が壊れている場合は死亡確認ができず、再送候補に残る。
- handler は flag のみで最初の signal を保持する。Popen 中の受信でも、戻った process を登録してから取消へ進める。
- PGID 比較は恒真ではない。`error` 優先、取消済み rc 0 の interrupted 判定も裁定どおり。
- nohup 由来の HUP 無視は launcher の明示 handler 登録で上書きされる。捕捉 disposition は子の exec で default に戻るため、HUP test の推論は成立する。ただし nohup 配下の実測証拠は提示ログにはない。
- docs §3:58–62 は確定文案と一致。前景起動・rc 0 以外停止・prune 条件は妥当。同一 process group の実装は launcher が担う。

## 変異の帰属表

変異実走ログは提示されていないため、以下は**静的な期待判定**。node 名の接頭辞は `orchestrator/tests/test_cleanup_remove_dirs.py::`。

| 変異 | 期待 killer node／結果 | single-reason 評価 |
|---|---|---|
| M0 | docstring のみなら SURVIVED | 等価対照として妥当 |
| M1 | `test_children_share_parent_pgid_then_remove` は赤 | PGID 検査が第 1 子で止めるため、独立 PGID assertion より先に「2 子 T」の同期失敗になり得る。assertion 単独への帰属は不可 |
| M2 | `test_launcher_signal_is_forwarded_before_removal[TERM/INT/HUP]` は pending 未観測で赤 | 転送削除に帰属可能。ただし実装では handler 内でなく `cancel()` の送信を変異する |
| M3 | signal 3 node、`test_timeout_is_interrupted` | interrupted→removed を実際に到達する分岐で変更すれば赤。rc も変更するため複合変異 |
| M4 | `test_zero_returncode_with_existing_path_is_failed` | 残存を removed にする分類変異なら赤。CLI の最終再確認だけを迂回する変異への証明ではない |
| M5 | `test_nonzero_returncode_with_absent_path_is_failed` | rc>0→removed の直接検出。chmod node は残存判定もあるため、変異位置次第では生存し、root では skip |
| M6 | `test_usage_rejects_paths_without_removal[nested]` は赤 | 包含拒否の欠落に帰属可能 |
| M7 | `test_usage_rejects_cwd_inside_target[exact/descendant]` は赤 | cwd 拒否の欠落に帰属可能 |
| M8 | `test_timeout_is_interrupted` は pending 未観測で赤 | 「TERM を送らず待ち続ける」という登録どおりなら帰属可能。変異後の実走・回収確認は別途必要 |
| M9 | `test_children_share_parent_pgid_then_remove` の独立 PGID assertion が赤 | 意図どおり両層変異。single-reason／単層検査とは呼べない |
| M10 | `test_launcher_signal_is_forwarded_before_removal[HUP]` は赤 | 通常環境では launcher 終了、nohup 由来の無視継承時は転送なし。いずれも pending 未観測だが、故障形態は異なる |

## 総括

**NO-GO：must-fix 2 件（A1、A2）。**
timeout 記録の競合で rc 0 が漏れ、timeout 取消中の全体 signal 転送も遅れる。
親ログの新規 36 passed、consumer/meta 1169 passed・3 skipped、TERM dogfood 成功は確認した。
これらは上記競合・複数子の取消割込みをカバーしていない。静的レビューのみ実施し、変更・実走はしていない。
