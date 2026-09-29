## 対応表

| 項目 | 判定 | 根拠 |
|---|---|---|
| H1 | closed | YCSB target の compile 行を一意に選ぶ。`orchestrator/campaign/vhash_cicada_vlife.py:367–401`。smoke3 の `delay_compile` に実機での実行結果がある（`raw/smoke3.json:10315`）。 |
| H2 | closed | 各段の失敗を記録して独立した段を続行し、全段成功を合格条件にする。`vhash_cicada_vlife.py:447–553`。 |
| H3 | closed | 実行中の例外は error 付き raw JSON になり、measure 入口は拒否する。`vhash_cicada_vlife.py:312–317, 567–625`。既存出力の上書き拒否は対象外。 |
| J1 | **partial** | 計器・長い tx は指定の 2 file に移り、batch の延長・retry・read-only 再計算、固定配列、終了時 JSON は確認できる。`patches/instr-cicada-version-lifetime.patch:35–59, 165–221, 231–264`、`external/ccbench/include/ycsb.hh:102–115`。ただし MinRts 公開計数に下記の欠落がある。 |
| J2 | closed | `SINGLE_EXEC` 対象外を明記し、内側の計器分岐を除去。`patch:8, 150, 295–299`。 |
| J3 | closed | 待機は `rdtscp()` の cycle spin。`patch:617–625`。 |
| J4 | closed | strings は stock と既定 patch の集合一致を検査。`vhash_cicada_vlife.py:356–364, 518–526`。smoke3 でも一致（`raw/smoke3.json:10354–10385`）。 |
| J5 | closed | delay compile の rc と診断を保存し、非ゼロ rc 自体では失格にしない。`vhash_cicada_vlife.py:367–401, 474–481`。smoke3 は rc=1 のまま全体 rc=0。 |
| J6 | closed | owner 33/3、companion header 8 に更新。`orchestrator/campaign/condition_meaning_gate.py:501–536`。smoke3 で両 macro の admission は `admitted=true`（`raw/smoke3.json:16` 以下の enabled gates）。 |

段4〜fix2 の hop・位置、K 深部の候補式、L/U、既読0件、pending 確定、成功 read だけの既読更新、GC 年齢、install/detach、長短別と read-only 別統計は移設後の `patch:13–24, 64–132, 273–400, 405–585, 591–655` に残る。終了時 JSON は smoke3 で **1 行、48 worker 分**を parse 済み（`raw/smoke3.json:10476, 10499`）。固定配列は 256 要素、今回の条件は総 48 worker で範囲内。

既定 patch の前処理一致テストは touched 2 file を対象とし、smoke3 の実 binary でも stock と既定 patch の `.text`・`.rodata` が一致した（`orchestrator/tests/test_vhash_cicada_vlife.py:18–21, 384–395`、`raw/smoke3.json:10355–10360`）。今回の YCSB build に関する既定同一性の根拠に穴は見つからない。

## 新たな所見

- **must-fix — MinRts の同値再公開が欠落する。** stock は GC 条件成立時に毎回 `MinRts.store(minr)` する（`external/ccbench/cc/cicada/util.cc:281–323`）。移設後は前後の値が異なる場合だけ記録する（`patch:660–676`）。同値の store が起きると、その公開の境界年齢が消え、前後の公開間隔が合算される。放置すると raw の GC 分布と図・一次資料の「公開ごと」という結論が変わる。さらに採時点は store 直後から関数復帰後へ移り、flag 更新時間を含む。公開イベントそのものを漏れなく記録する修正が必要。
- **should — 適用範囲を明記する。** 256 要素配列には総 worker 数の実行時上限検査がない（`patch:36, 187–188`）。今回の 48 worker の raw には影響しないが、この計器を 256 超へ転用した raw は不正になり得る。一次資料には今回の worker 範囲を明記すれば足りる。

## 総括

**NO-GO。残る must-fix は J1 の MinRts 公開イベントの欠落 1 件。** smoke3 の成功と既定 build の同一性は確認できたが、公開間隔と境界年齢を「公開ごと」の測定値として扱う前に修正が要る。