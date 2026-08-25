---
schema: izanagi-spool-v1
ledger: failures
authored: 2026-08-25
wave: dev-wave-t425-d716-carry-note
seq: 2
---

## 再発

### F136

- **再発: 2026-08-25 (同日 6 例目)** — 署名は既知形と一致するが、**赤の射程が `test_s8b_floor_campaign.py` の外へ広がった**点が新しい。docs のみ (spool fragment 1 件) の wave の受入 1 回目で、操作者は受入全走を 1 本しか投入せず走行中に repo へ何も書いていないのに 12 failed / 16132 passed / 60 skipped になった。11 件は既存例と同じ `test_s8b_floor_campaign.py` の `_real_output_snapshot()` 系で、junit の差分も `first extra item: ('dir', 'task-runs/reports')` と逐語一致する。**12 件目は `test_s8b_oracle_driver.py::test_t080_stub_free_e2e_temp_roots_fail_closed_at_real_output_boundary` で、別 helper `_t080_output_snapshot()` が `output/` 自身の mtime 変化 (1787656942 → 1787657046) を検出したものである。** 既存の「再発検知の補強」は判定条件を「赤が `_real_output_snapshot` 系だけ」と helper 名で書いており、**この 12 件目を含む赤を本件型と判定できない**。判定は helper 名でなく「`output/` の before/after snapshot を assert する検査群」という性質で行う必要がある。帰属は台帳の 3 点で否定した — (1) wave の差分は `docs/spool/worklog/` 配下の新規 1 file だけで実装面 file を 1 つも触らない、(2) 落ちた 3 種の単独走は 16.49 秒で 3 passed、(3) junit 差分は実装ではなく `output/` の dir 増加と mtime を指す。恒久対応は本 wave の scope 外で、受入基盤の所有 wave の判断に委ねる点は既存の再発と同じ。

### F428

- **再発: 2026-08-25** — 既存例が「完了したのに carry が未完了と言い続けた」型だったのに対し、本件は **「許可の一部が取り消されたのに carry が許可と言い続けた」型**である点が新しい。[T-425] の carry 本文 (entry 824、2026-08-22) は rr80/rr20 calibration の取得・検証・登録の 3 脚すべてに AI/ツール経路を許していたが、翌 2026-08-23 に別 ID・別 wave ([T-1488]) で land した D716 が**登録の脚だけ**を holdout 解禁まで留保した。D716 は T-425 を引用しないため carry は追随せず、2026-08-25 に「取得・検証・登録」を求める wave が起動した。着手前実測 (`DW-S01` の裁定前提実測、F35 と同じ発火点) が段 1 前に食い違いを露見させ、実害は wave 1 本の空転で止まった。**将来この型を lint 化するとき、closing commit との対応だけを見る検査では取り逃す** — carry 本文が主張する**許可・禁止**が後続 decision で狭められていないかも検査面に要る。局所修復として、同日の worklog エントリで [T-425] の carry 本文を現況へ改めた。
