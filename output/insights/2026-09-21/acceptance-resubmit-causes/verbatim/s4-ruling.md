# 段 4 裁定 — 段 3 相談 (codex gpt-6-astra / medium / read-only、`codex/s3-consult-out.md`) の所見 9 件

| # | 所見 | real/refuted | 採否 | 反映 |
|---|---|---|---|---|
| 1 | 1759 final2 / T-2803 final2 は待ち手起動前 (親 chain script の固定 SHA merge) の停止で、待ち手の post-claim merge ではない | real (`run-acceptance-gated.sh` 70〜99 行で実測: merge → preflight → commit → 待ち手起動) | 採用 | D を D1 (待ち手 post-claim merge の terminal-merge、1 件) / D2 (親 script の起動前 merge の実競合、1 件) / D3 (同 preflight 赤、1 件) / D4 (待ち手 postcheck、4 件) に分け、(P1) を「試行 = chain の attempt 1 回。待ち手起動の有無・test 実行の有無を列で示す」に改める |
| 2 | postcheck は child 起動前の main 包含再検査で、「merge 中」「親が手で再投入」は言い過ぎ・誤り | real (`gate-loop-final.log` で T-2814 / T-2804 も loop が attempt 2 を自動投入) | 採用 | (P3) を「child 起動前の main 包含再検査 (`_behind_count`) で停止。前進の瞬間は未特定」とし、4 件とも自動 loop の再投入と書く。1758 は started.txt 基準 2.45 分 |
| 3 | 帰属判定と既知性を分ける。1759 は handoff のみで既知性の先行根拠が無い。ref 除外は妥当 | real | 採用 | B の名を「非帰属の赤 (hold 未登録)」にし、既知型の根拠がある 2 件 (T-2817) と先行根拠未提示の 1 件 (1759) を分けて書く。G / H は分類外のまま |
| 4 | gate-loop log の門番待ちを抽出していない。追加 wall は 333.3 → 342.3 分 | real (`gate-loop-final*.log`、chain の再門番区間を実測) | 採用 | classify.py v2 で全試行の門番区間を埋め直し、合計 342.3 = 門番 175.7 + 外側 wall 97.4 + 残差 69.2 分 |
| 5 | 「走 wall」は test 所要ではない。lease 待ち 0 と門番待ちを別掲。`lease_renew state` だけでは TTL 内を証明できない | real | 採用 | 「外側 wall」と改名し、F は「失効を理由にした再投入は観測されない」に限定 |
| 6 | 1759 は DW-O18 の worklog 記録義務を満たしていない (handoff のみ)。D の「所有確認をしなかった」は根拠不足 | real (`operations.md` DW-O18「根拠を worklog へ残す」、entry 1759 本文に判定なし) | 採用 | 再投入の原因と記録上の逸脱を別記。D2 は「競合を観測、所有確認の履行は資料から未確認」 |
| 7 | A の「手順違反なし」は包括断定が強い。F474 の 14 file 追加は T-2344 事象後。D3 の言い方 | real | 採用 | A は「指定 4 群は実施、consumer 探索では漏れた。後から足された手順の不履行とは判定しない」。D3 は「親 script の起動前 merge で著者行の preflight が赤」 |
| 8 | 固定費・防止不能・無条件の結果記録禁止は診断を越える | real | 採用 | 削る。依頼の 3 手順それぞれに「守られた / 守られなかった / 該当事象なし」を明記。「1755 は窓の 1 本外」→「対象外」 |
| 9 | 母集合 (T-2501 欠測 → 1758 繰り入れ) と「11 wave」の意味 (試行 2 回以上 11 / test 実行 2 回以上 5) を明示 | real | 採用 | 「直近群から一次資料を回収できた 20 本」と書き、T-2501 を欠測として残す |

- 実装なし (診断のみ) → 段 5 は親の docs 起草、段 6 は read-only review 1 本、変異 matrix は免除 (DW-S04: 実装面差分ゼロ)。受入全走は免除しない。
- 裁定パッケージ候補 (実装しない): (i) DW-O26 の inventory 4 群に「repo 全体の exact 目録 test」(T-2737 の define 目録、T-2797 の process 起動点目録) を含めるか — 独立 2 例 (DW-G03) だが gate・一般化の追加は依頼の scope 外なので候補として返すだけ。(ii) 受入結果の insight 追記 (E) を「land の記録が持つ」に寄せる運用は既存手順 (operations.md 94 行付近、entry 1770 / 1774 / 1775 の記述) の再確認で足りる — 新規の正本追加はしない。
- DW-O08/09/10/13 は不成立のまま (再評価: insight + fragment のみ)。
