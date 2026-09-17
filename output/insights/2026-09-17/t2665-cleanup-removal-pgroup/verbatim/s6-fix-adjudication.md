# 段 6 レビュー裁定 (親) — [T-2665]

| id | 判定 | 採否 | 指示 |
|---|---|---|---|
| A1 timeout 競合 (expired 子が cancel() の再 poll 前に rc 0 で終了すると removed / rc 0) | real | must-fix 採用 | timeout 検出時点で `expired` の各子に `cancelled = True` を立ててから `cancel(expired, SIGTERM)` を呼ぶ (cancel() 内の `_live` 絞り込みは送信対象の限定にだけ使う)。取消前に完走した他の子の `removed` は保持する (plan どおり) |
| A2 timeout 取消の猶予待ち中に全体 signal を読まない (最大 ~6 秒遅延) | real | must-fix 採用 | `cancel()` に `interrupted: Callable[[], int \| None]` (既定 `lambda: None`) を足し、猶予 poll loop の各周で `interrupted()` が真なら即 return する。主 loop は `cancel(expired, signal.SIGTERM, interrupted=lambda: cancelled)` で呼び、戻った直後に `if cancelled:` の全体取消 (既存経路) へ進む。fault 経路の `cancel()` は既定 (中断なし) のまま |
| A3 / B-01 summary 確定後〜flush 前の signal で JSON rc 0 と process rc 2 が食い違う | real | must-fix 採用 (B の判定) | 成功境界を状態遷移として固定する: 全子 reap → 全 path lstat 再確認 → **TERM/INT/HUP の disposition を `SIG_DFL` に戻す** → `cancelled` を最終読取して summary 確定 → JSONL 出力 → flush。境界後に届いた signal は既定動作で launcher を終了させる (exit status は非 0、JSON は不完全になりうる)。docstring に「**process の exit status が正**であり、JSON summary の `rc` はそれを写す。成功境界後の signal では既定動作で終了し exit status は非 0」を明記。新 test は足さない (決定的に書けない窓。契約は docstring と `_finish` の `proc.returncode == summary["rc"]` assert で担保) |
| A4 同期失敗時の診断 | nit | 採用 | `_stopped` / `_wait_until` の失敗 AssertionError に、観測した children と各 `/proc/<pid>/stat` の状態を含める。期限値は変えない |
| B-02 chmod 復旧が `_launch` 例外時に漏れる | nit | 採用 | `parent.chmod(0o500)` 以降の `_launch` を try/finally の内側へ |
| B-03 summary 負例の網羅 | nit | 採用 | `test_summary_never_succeeds_for_incomplete_results` に (a) 件数超過 (rows 3 / total 2)、(b) 未定義 status、(c) failed + interrupted 混在 → いずれも rc 2 を足す。実装は変えない (現行判定が正しいことをレビューが確認済み) |

変異 spec への影響: M8 の anchor `                if expired:\n                    cancel(expired, signal.SIGTERM)\n` は A1/A2 の fix で変わるので、fix 後に anchor を再照準する (DW-M07)。M2 の anchor (`cancel()` の for 文) も引数追加で変わりうる — fix 後に再検算。
