1. 正規表現 — **real（CRLF の境界のみ）**

`Group Name:             SFC` には整合し、空白幅・大文字小文字・行末ピリオド拒否も exact binding として妥当です。  
ただし `\r\n` では `\r` を消費できず不一致になります。既存の `_NQSV_REQUEST_ID_RE`（`dispatch_compute.py:141`）も同じ弱点ですが、Started/Ended/Elapse は `.*` により CRLF を通します。

修正案：実データが CRLF なら `dispatch_compute.py:141` と追加する Group Name regex を `(?:\r)?$` 対応にし、`test_pegasus_dispatch_compute.py:2238` 付近へ CRLF ケースを追加する。`SFC.` を許す変更は不要です。

2. DEFAULT_PROJECT — **refuted**

現行実装に別 project 経路はありません。

- `dispatch_compute.py:44` 定義
- `dispatch_compute.py:548` `#PBS -A`
- `dispatch_compute.py:1572` receipt
- `dispatch_compute.py:1714` qsub `-A`

`dispatch()` に project 引数はなく、CLI・環境変数による上書きもありません。P1 の module 定数直接参照で正当な job を reject する経路は確認できません。修正不要です。

3. tail 切り詰めと出現順 — **real（fixture の順序前提が未検証）／tail-loss の説明は refuted**

`_bounded_log()`（`dispatch_compute.py:763`）は先頭を捨て、末尾 `limit` bytes を保持します。したがって Group Name が後方・末尾寄りなら失われにくく、「後方にあるほど真っ先に失われる」は逆です。

一方、射影資料中の実データ引用は値しか示さず、Request ID 直後という順序は確認できません。実データの canonical 順序に合わせて `test_pegasus_dispatch_compute.py:96` の fixture を修正し、`test_scheduler_logs_are_tail_bounded_with_explicit_omission`（同:2270）で `Group Name` も tail に残ることを検証すべきです。

4. findall — **real（正しい fail-closed 設計）**

`.search()` だけでは、child stderr の偽 `Group Name: SFC` と実 footer の `Group Name: OTHER` が混在しても通る可能性があります。`stderr_prefix` が任意テキストを前置できることは fixture（`test_pegasus_dispatch_compute.py:106`）にも表れています。

`findall() == [DEFAULT_PROJECT]` は、欠落・不一致・重複・混在をすべて拒否でき、Request ID の重複拒否（`dispatch_compute.py:933`）とも整合します。重複 SFC と `SFC + OTHER` のテストを `test_pegasus_dispatch_compute.py:2238` 付近へ追加してください。

## 総括

blocker 級はありませんが、Group Name の実データ上の行順が未確認で、Request ID 直後の fixture は未証明です。tail は末尾保持なので説明の向きを修正すべきです。CRLF 対応と重複ケースのテスト追加を推奨します。 pytest は未実行です。