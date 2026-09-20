---
schema: izanagi-spool-v1
ledger: failures
authored: 2026-09-20
wave: dev-wave-t2792-a1-sized-attempt2
seq: 1
---

## 再発

### F1013

- **再発: 2026-09-20** ([T-2792] A-1 sized attempt-0002 の記録 wave) — DW-S07 の三軸語走査器 (`s8b_holdout_freeze search`) を段 7 で走らせ「本 wave の file に hit なし」を確認したうえで、**その走査器の生出力 (走査の対象・正規表現名・既知 hit の一覧を含む JSON) を insight の `verbatim/three-axis-scan.txt` として repo に写した。** 出力自身が三軸語 conjunction に当たり、受入全走 (attempt 1、25 分) が `test_s8b_oracle_driver` の t080 系 `IZANAGI_FREEZE_HOLD` と `test_s8b_floor_campaign` の `clean scan 拒否` で赤 25 件 (全件がこの file を名指し)。走査は写す前の tree に対して行ったので緑だった。是正: file を削除し (走査結果は insight の要約 1 行で足りる)、走査を再走して hit が既知 4 file に戻ることを確認してから受入を取り直した。**走査器の出力は走査器の候補集合に入る**ので、走査後に足す file にも同じ検査を掛ける。
