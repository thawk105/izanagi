# 段 6 裁定 — read-only レビュー 1 本 (`s6-review.md`、NO-GO、must-fix 1 / should 1 / nit 0) (2026-09-22)

レビューは codex (`tools/dev_wave_codex.py --stage review --sandbox read-only`、rc=0、`check_codex_output.py` rc=0)。prompt 全文は `s6-review-prompt.md`。
数値・識別子・sha・比と率・停止規則の判定・択 A の入力の由来 (pair 結果の混入なし)・epoch 差・正規化・fragment 形式は、原本から独立に再抽出して一致と判定された。

| 所見 | 判定 | 処置 |
|---|---|---|
| M1 見積りの説明が D2211 項 1 と食い違う (候補のみ job の Elapse から pair の所要を外挿し、brief が「D2211 の注意どおり」と書いた) | **real・採用** | brief は当時のまま保存し、README §6 を「投入前の見積りは裁定に反していた、外挿なしの上限は 6 node 時間で確認ラインを越える、本来は 1 本目の前に確認を取るべきだった」と書き直した。4 巡目前の取り直し (pair 実測 100 秒) は別と明記。worklog fragment の同じ段落も直し、failures fragment (新規 F、[権限逸脱] [手順漏れ]) と memory `experiment-compute-needs-user-confirmation` の追記を足した |
| S1 候補間差の不確かさを「stock の揺れと同じ桁」と定量的に言い過ぎた | **real・採用** | README §3 を「job・node の差と分離できず設定の効果へ帰属できない、不確かさの大きさは推定していない」に直した |

測定値・certified 判定・停止規則の判定・再投入の要否は、どの所見でも変わらない (レビュー自身の総括)。
