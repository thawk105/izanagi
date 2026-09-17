## 所見別対応表

以下、L = [tools/cleanup_remove_dirs.py](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2665-cleanup-removal-pgroup/tools/cleanup_remove_dirs.py)、T = [orchestrator/tests/test_cleanup_remove_dirs.py](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2665-cleanup-removal-pgroup/orchestrator/tests/test_cleanup_remove_dirs.py)。

| 所見 | 判定 | 根拠 file:line |
|---|---|---|
| A1 | closed | L:218–221。expired 全件へ取消を記録してから再 poll するため、その間に rc 0 で終了しても L:144–145 で interrupted。他の完走済み子は `_live()` の送信対象外で、removed を保持する。 |
| A2 | closed | L:103–123。TERM・KILL 共通の猶予 loop が各周で中断 flag を確認して return。L:221–224 が直後に全体取消へ進む。早期 return 時に未回収エラーが未設定でも、全体取消が再 poll・回収し、残存は L:122–123 で unknown の根拠を記録する。fault 経路 L:233、258、267 は中断 callable を渡していない。 |
| A3-B-01 | closed | L:214–238、249–255。正常経路は全子 reap → 全 path lstat → SIG_DFL 復帰 → cancelled 読取・summary → JSONL → flush。復帰は unknown 時の追加 cancel より後。L:8–12 に終了 status 優先・既定動作による非 0 終了を明記し、L:269 でも cancelled を再読する。 |
| A4 | closed | T:61–80、101–107。同期失敗時に観測 PID と各 `/proc/<pid>/stat` 状態を出す。通常期限 6 秒、pending 期限 2 秒、usage 8 秒、後始末 2＋2 秒は維持されている。 |
| B-02 | closed | T:215–226。`_launch()` は復旧用 try/finally 内。起動失敗時も chmod 700 に戻り、未生成 proc の cleanup を避ける。 |
| B-03 | closed | T:303–306。件数超過・未定義 status・failed＋interrupted の独立した 3 負例を追加し、いずれも rc 2 を要求。L:155–169 の集約ロジックは既レビュー記載と整合する。 |

## 退行・新規所見

なし。

- expired 非空時は cancel 内で有界待機する。回収済みなら次周で live から消え、未回収なら error を検出して fault 経路へ進むため、継続的な busy loop にはならない。
- spawn・PGID・poll・分類・出力・close の例外に対する取消経路を維持している。新 option・別の取消機構・既存 assertion の緩和は認めない。
- unknown 経路では、有界取消後にも未回収子が残る可能性はある。全子 reap の保証は正常成功経路について成立し、unknown は rc 2 に固定される。SIG_DFL 復帰は指定どおり追加取消の後にある。
- 修正前ファイル自体は射影にないため、`summarize()`・期限・既存期待値の byte 単位の不変性は未検証。現コードを段 4 仕様・レビュー記録と照合した範囲で相違はない。

## 変異 anchor と期待 node の再検証

fix 報告の Python 文字列を抽出し、現コードで数え直した。(i)〜(x) は**すべて出現 1 回**。以下の node は T 内で存在を確認した。KILLED / SURVIVED は静的な期待であり、変異実走結果ではない。

| 変異 | anchor・行 | 期待 node／判定 |
|---|---|---|
| M0 | docstring 冒頭 L:2、1 回 | docstring のみの等価変更なら SURVIVED。具体的な置換全文は射影にない。 |
| M1 | (i) L:208 | `test_children_share_parent_pgid_then_remove`。PGID 不一致による取消で、独立 assertion より先に停止同期が失敗し得る。 |
| M2 | (ix) L:106 | `test_launcher_signal_is_forwarded_before_removal[TERM/INT/HUP]`。送信を除去すれば pending 未観測。引数追加後も anchor は一意。 |
| M3 | (iii) L:145 | signal 3 node と `test_timeout_is_interrupted`。status／summary rc の期待で検出。rc も変える複合変異である点は維持。 |
| M4 | (iv) L:128 | `test_zero_returncode_with_existing_path_is_failed`。残存を removed にする分類変異への検出力。CLI 経路全般の証明には広げない。 |
| M5 | (v) L:146 | `test_nonzero_returncode_with_absent_path_is_failed`。chmod node は残存条件にも依存するため、確実な killer は直呼び node。 |
| M6 | (vi) L:84 | `test_usage_rejects_paths_without_removal[nested]`。 |
| M7 | (vii) L:80 | `test_usage_rejects_cwd_inside_target[exact/descendant]`。 |
| M8 | **(x) L:218–221** | `test_timeout_is_interrupted`。新 anchor 全体を「TERM を送らず待ち続ける」置換へ再照準すれば pending 未観測で検出。旧 anchor は使用不可。 |
| M9 | (i)＋(ii) L:208、210 | `test_children_share_parent_pgid_then_remove` の独立 PGID assertion。両層変異として妥当。 |
| M10 | (viii) L:185 | `test_launcher_signal_is_forwarded_before_removal[HUP]`。登録から HUP を外す変異。復帰側 L:249 は改行が異なり、この anchor には一致しない。 |

## 総括

**GO — 焦点再レビュー対象の 6 件は closed。**
静的検査で新規の阻害所見なし。変異 anchor (i)〜(x) は各 1 回。
親ログは local OOM 後の dispatch 再走で **115 passed、rc 0**。受入全走ではない。
TERM dogfood は launcher rc 2、子 rc −15、interrupted、生存子なし。
本レビューでは書込み・pytest・変異実走を行っていない。
