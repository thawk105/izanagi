## 総括

**v4 への修正完了。** [probe/verify_phase_runner.py](/work/1/SFC/tanab/izanagi/.codex/worktrees/t2807-author/probe/verify_phase_runner.py) だけを編集し、未コミットの差分を残しました。禁止された Git 操作は実行していません。

| 所見 | 状態 | 対応・改版後の行番号 |
|---|---|---|
| 1 | closed | attempt-1 のみ実行、既存 rep は再走しない。複数 attempt は構造誤り。L348、L356、L923、L1089 |
| 2 | closed | cohort の bench 失敗件数を開示して pass を阻止。校正失敗は指定理由付きで本走禁止。L342、L1016、L1177、L1293 |
| 3 | closed | 対象の完走 anomaly を先に評価。混入・SHA 不一致・規約不適合があっても失格を維持。L1016 |
| 4 | closed | calib／verify の job 段失敗 record を収集し、規約不適合として開示・pass 阻止。L968、L1145 |
| 5 | closed | hard timeout を校正3600／本走1800／再検証3600秒に変更。L38、L725、L895 |
| 6 | closed | 校正分岐を純関数化し、停止3例・継続例を検査。校正 anomaly fixture も修正。L333、L905、L1382 |
| 7 | closed | literal 6 define との完全一致、保全欠落のみ・期待 identity 不一致のみの負例へ強化。L1417、L1743、L1760 |
| 8 | closed | resume 照合で `in_judgment_set is True` を要求。L749、L1864 |
| 9 | closed | 指定 (a)〜(i) と補助ケースを追加。L1487〜1564、L1802〜1890 |

改版後は **1968行**。SHA-256:

```text
f98360ad0c8256a80c198df84de3ec46219d53e5f9dcfe2f741e76bc84455856
```

検証結果:

- `python3.10 -B probe/verify_phase_runner.py selftest`: **rc=0、`selftest: PASS 160/160 cases`**。既存120件を維持・指定箇所を強化し、40件追加。
- AST 構文確認: **PASS、rc=0**。
- `prerun / calibrate / verify / reverify / summarize / selftest --help`: **6件すべて rc=0**。

**未実走:** build、bench、verifier、実 trace の保全・復元、計算ノード経路。selftest の実行制御検査は合成 record と callback によるものです。

事前登録 v1・段6裁定からの新たな逸脱はありません。§5 が列挙する trace 欠落・witness 不一致も bench 失敗として扱います。B6 の setup＋hydrate＋build 2400秒が事後検査である制約は、段6裁定の「記録のみ、fix なし」に従い維持しました。