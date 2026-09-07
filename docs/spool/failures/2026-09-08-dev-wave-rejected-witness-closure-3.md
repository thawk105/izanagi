---
schema: izanagi-spool-v1
ledger: failures
authored: 2026-09-08
wave: dev-wave-rejected-witness-closure
seq: 3
---

## 新規

### {{F:unmeasured-runtime-premise-as-ruling-ground}}. 言語と自 repo の実行時挙動を実測せずに断定し、裁定の根拠に据えた [捏造/幻覚] [手順漏れ]

- 事象: 段 4 裁定で親が 3 つの前提を実測せずに書き、いずれも子の実測で否定された。
  (1)「`canonical_json_bytes()` が float を拒否するので witness に float は入らない」— 実際は
  有限 float を許し、Python の `2.0 == 2` により型検査を素通りしていた。
  (2)「verifier の出力は決定的なので正規化は不要」— 実際は
  `orchestrator/verifier/dsg.py` の `_reasons()` が `u_writes.keys() & v_writes.keys()` を
  未整列で走査するため、理由順が process 間で変わる。
  (3)「producer が書く boolean は必ず恒真になる」— producer は untyped JSON へ潰れる前の
  `VerifyResult` を持つので偽になりうる値を書ける。
  (1) は受理集合を実際に広げており、段 6 の敵対レビュー 2 本が具体的に通る入力を示した。
- 根本原因: いずれも**関数を 1 本呼べば 10 秒で確かめられる事実**を、名前と docstring からの
  推測で断定した。`canonical_json_bytes` は「canonical JSON」という名前から float 拒否を
  推測し、`_validate_json_value` の本体を読んでいない。決定性は「SCC を size 昇順に整列」
  という別の決定性の記述から集合反復の決定性まで拡張した。
- 恒久対応: `DW-S01` の既存義務「brief 前に承認済み裁定と引数の前提を実測し、覆す新事実は
  brief に出して段 4 で再裁定する」と `DW-O13`「field の実在では足りない。その field が実環境で
  取りうる値を実測し、要求する値が到達可能か確かめてから述語を採用する」の適用範囲に、
  **判定式が依拠する言語・標準ライブラリ・自 repo helper の挙動**を含める。
  memory `read-own-memory-before-deriving-from-source` と同じ向きで、
  「source 導出より先に実行して確かめる」を優先する。
- 再発検知: 裁定文へ「X は Y を拒否する / X は決定的である」の形の前提を書いたら、
  その 1 文ごとに実行して確かめた出力を裁定パッケージへ貼る。貼れない前提は裁定の根拠にしない。
  本件は段 3 と段 6 の敵対レビューが 3 件すべてを捕まえており、
  独立の敵対検証子を省かない規律 (`DW-C00`) が実際に働いた例でもある。

## 再発

### F245

- **再発: 2026-09-08** — 変異 `b060.m23-length-exact-int` / `b060.m24-endpoint-exact-int`
  (`type(x) is not int` を `not isinstance(x, int)` へ緩める) が probe 走で SURVIVED した。
  `isinstance(2.0, int)` は False なので、float を使う既存の負例に対してこの緩和は
  **何も変えていない**。開くのは bool の穴だけで、それを突く負例が集合に無かった。
  F245 と同じく「緩和した方向を 1 件も持たない負例集合に対しては、その緩和が観測不能」である。
  `DW-M02` に従い型検査そのものを取り除く形へ再照準して KILLED を実測し、
  isinstance 版は「型の厳密さが負例で pin されていない」ことの実測として登録 SURVIVED で残した。
