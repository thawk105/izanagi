# [T-2854] 単位 4 — 段 4 裁定 (親、2026-09-22 20:1x JST、main = wave HEAD = eef04f5a7)

入力: s1-brief.md、codex/s2-plan.md (plan)、codex/s3-consult-A.md (A、正しさ境界)、codex/s3-consult-B.md (B、実効性・過剰)。
裁定 inbox 再走査: 2026-09-22-rulings-full31-verdicts.md (19:52 更新) は第 31 回の記録・着地の追記のみ、T-2854 の実体は entry 1819
「段 1 の実装 (Codex author)」で本 wave と一致。新しい食い違いなし。

## 所見の裁定

| 所見 | 判定 | 採否・扱い |
|---|---|---|
| A-F1/F2, B-B1 (P7: 存在履歴を検査しない v3 が certified になる。pipeline の拒否は公開 API / CLI を守らない) | **real** | 採用 → R1。§3.3 の実装はしない (scope 外) が、v3 の certified は本 wave で出さない |
| A-F3 (別表同 hex の衝突), A-F5 (v2 の順序), A-F7 (厳格検査の抜け), B-B2 (emitter と不一致), B-B4 (過剰実装), B-B6 (合成 token 化) | refuted | plan §1・§3 の identity と派生型を維持 |
| A-F4 (table の表記揺れの直接試験なし) | 攻撃は refuted・検査不足は real | 採用 → R3 (厳格 10 進) と試験 |
| A-F6 / B-B5 / A-F11 / B-B8 (schema の二重検査、変異 #5 の帰属不能、優先順位の過大な機構) | real (過剰と帰属) | 採用 → R2 (単純規則 1 箇所) |
| A-F8 (last-wins の tx_type), A-F10 (v3 の pool 障害 fallback), B-B7 (実並列の証明) | real (検査不足) | 採用 → R8 の追加試験 (代表 fixture 1 つずつ) |
| A-F9 / B-B3 (旧 result_to_dict・CLI・receipt digest は v3 情報を落とす) | real・scope 制限 | 不採用 (単位 5)。result_to_dict_v3 は本単位の出力点で、既存 serializer の v3 対応完了とは扱わない |
| A-F12 / B-B11 (閉包の一般化: sha pin 0 件 ≠ 結果 golden 不在) | real | 採用 → R10 (brief の記述を限定、挙動 golden は不変条件 1 で守る) |
| A-F13 / B-B16 (表番号の未確認・op 名) | real (nit) | NewOrder=5・Order=6 (brief 記載済み)。op は wire の U/I/D |
| B-B9 (変異 #3・#10 の fixture) | real | 採用 → 変異登録 M3・M12・M13 |
| B-B10 / B-B15 (試験の重複・直積、規模の楽観) | real | 採用 → R8 (直積削減)、R9 (規模上限) |
| B-B12 / B-B13 (不変条件 8・9 の過大な一般化) | real | 採用 → R10 (設計選択として書き直す。Integrity に 1 field を足す R1 を許す) |
| B-B14 (P3 支持) | — | P3 維持 |

## 裁定 (plan v2 = plan に以下を上書き)

- **R1 (P7 の改訂、規律 2):** v3 の run は本 wave の verifier で certified にしない。`model.Integrity` に既定値 False の field を 1 つ
  (名前は `v3_existence_unverified: bool = False`) 足し、`Integrity.clean()` はこれが False のときだけ真。`core.verify_trace_dir` は
  run の schema が v3 で n_txns>0 のとき True にし、notes に 1 行 (設計 §3.3 の insert / delete の存在履歴を未検査なので認定しない、
  単位 5 以降で撤去) を足す。cycle があれば従来どおり non-serializable、anomaly は構造化して返す (規律 3)。v2 は field が False のままで
  verdict・result_to_dict・notes が不変。§3.3 の存在履歴の実装そのものは本 wave でしない。この印の撤去は §3.3 を実装する単位の完了条件。
  capability 経路 (`_verify_trace_dir_with_capability`) も同じ判定を通ることを確かめる (A-F2)。
- **R2 (P1 の改訂、schema 混在):** 同一 file 内の v2 / v3 混在は `_parse_file` がその C 行で ParseError (per-file の状態)。file 跨ぎは、
  既存の「全 outcome の failure を sorted path 順に raise」をそのまま先に行い、その後に 1 つの helper が全 file の schema
  (C の無い file は中立) を sorted path 順に照合し、最初に run schema と食い違った file を ParseError にする (run schema を決めた file の
  path と食い違った file の path を message に含める)。compact (columns と NeedsLegacy の両 outcome が per-file schema を持つ) と
  legacy (`_finish_legacy_parse` が全 file を読んだ後) は同じ helper を呼ぶ。merge での再検査、failure outcome への最初の C の保存、
  `_raise_parent_file_error` の変更はしない (plan §2 の手順 2・4・5・6 は不採用)。契約: file 自身の ParseError は file 跨ぎ混在より優先する。
- **R3 (P2 の字句):** v3 で新しく足す整数 field (table、tx_type、nS、nQ) は ASCII の `0|[1-9][0-9]*` に全体一致したときだけ整数化する
  (符号・先頭 0・underscore・空白混入は ParseError)。v2 と共有の field (txid・thid・epoch・tid・nR・nW・版) の変換は現行のまま。
  根拠: emitter は符号なし整数を ostream で出すので正規形しか出さない。受理集合を最小にして、将来 raw 行を束縛する consumer に
  表記の多義を残さない。
- **R4 (値域):** table 0..10、tx_type 1..5、nS = nQ = 0 (非 0 は ParseError「段 2 未対応」)、v3 の W op は U / I / D。S/Q tag は未知 tag のまま。
  v3 frame 内の R=6・W=7・X=5・I=5 token、v2 形の行は ParseError。v2 の op は従来どおり検査しない。
- **R5 (identity・型):** plan §1・§3 を採用 (v2 = key 文字列、v3 = (table, hex)。compact は (table, key) 単位の interning と token ごとの
  table 列。ReadV3 / WriteV3 / TxnV3 / EdgeReasonV3 / AnomalyV3 の派生型。基底の Read / Write / Txn / EdgeReason / CycleEdge / Anomaly /
  VerifyResult は変更しない)。生の key field は hex のまま。
- **R6 (出力点):** `core.result_to_dict_v3(res)` (plan §4 の形)。package 再 export・CLI・pipeline・receipt digest への配線はしない。
- **R7 (X/I と notes):** plan §5 を採用 (v3 の tuple 第 2 要素は (table, hex)、core の sample と version-dup notes は v3 のときだけ
  `table=<n> key=<hex>`)。v2 の文言は 1 byte も変えない。
- **R8 (試験):** plan §7 を基に次で上書き。(a) identity・cycle の metadata・fallback は全経路 (legacy、compact packed、compact tuple、
  workers=1 と 2) で比較し、字句・値域の拒否は 1 経路で足りる (直積にしない)。(b) 既存 v2 試験と重複する C 5/7/8 token の再試験は足さない。
  (c) 追加: 同一 txid の別 file 版で勝者の tx_type が cycle に載る試験 (A-F8)、v3 の parse / edge pool 障害から逐次への fallback 1 例
  (A-F10)、代表 fixture 1 つで子 PID による実並列の確認 (B-B7、既存方式)、table の表記 `01`・`+1`・`-0` の拒否 (R3)、同一 txn が別表の
  同じ hex を読み書きする `_reasons` 試験 (A #9)、R1 の非認定 (X/P 条件を満たす source context と一致する expected_commits を与えても
  v3 の非巡回 run は indeterminate・certified False、notes に印の 1 行。A の反例 2 つ = unborn の genesis 読みと DELETE 版の読みも
  indeterminate)、R1 の対照として v2 の同形 fixture は certified のまま。(d) op は wire の U / I / D。NewOrder=5・Order=6。
  (e) 既存テストの期待値は変えない (反転・緩和・skip・削除禁止)。新しい test file・fixture dir は作らず test_verifier.py へ足す。
- **R9 (規模上限):** production 4 file (model / parse / dsg / core) の差分は追加 + 削除で 550 行以内、test_verifier.py は 800 行以内。
  超えたら理由を報告に書く (超過は段 6 で差し戻し対象)。
- **R10 (brief の訂正):** 不変条件 6 は「v2 の認証集合を広げず、v3 は本 wave では認証しない (R1)」。不変条件 8・9 は実測から必然ではなく
  変更面を小さくする設計選択 (新 test file は自走 harness 付きなら inventory 上ただちに禁止ではない、B-B12。基底 dataclass への field
  追加も repr=False などで回避しうる、B-B13)。例外として Integrity に R1 の 1 field を足す。閉包の記述は「verifier 4 file の source
  sha256 を固定比較する test は 0 件」に限り、挙動 golden (test_verifier.py:1404 の JSON bytes、:2576-2663 の witness と repr、
  :2893-2956 の全 fixture 結果 hash と fixture inventory) は不変条件 1 の制約として残る。
- **R11 (後続への引継ぎ、記録のみ):** v3 を認定に使う前提 (単位 5 の allowlist 拡張・§6.1 の正例) は、§3.3 の存在履歴の実装と R1 の印の
  撤去。worklog の次の一手に書く (新しい台帳は作らない)。

## 変異の事前登録 (DW-M01、全件 category=negative・期待 KILLED)

位置は実装後に確定し、各変異で「同じ入力を前後・内側で拒否する別層が無く赤の理由が 1 つ」を確かめてから本登録する。確かめられない変異は
登録せず実効 gate へ再照準する。

| # | 変異 | 殺す試験 (予定) |
|---|---|---|
| M1 | object 経路の identity から table を落とす (v3 も hex だけ) | 表識別の辺集合試験 (legacy 経路の assertion) |
| M2 | compact の interning key から table を落とす | 表識別の辺集合試験 (compact 経路)・異表 token が別 id の assertion |
| M3 | packed の read-only token 解決で table を無視 (別 file に同表 writer と別表同 hex writer を置く fixture) | packed の read 解決試験 |
| M4 | tuple builder / worker の identity から table を落とす (実装が共通 helper なら 1 変異、別なら 2 つに分ける) | tuple 経路の表識別試験 |
| M5 | file 跨ぎ schema 照合 helper を無効化 (常に通す) | file 跨ぎ混在の拒否試験 (compact と legacy) |
| M6 | 同一 file 内の schema 状態検査を無効化 | 同一 file 内混在の拒否試験 |
| M7 | tx_type の値域検査を外す (字句は正しい 0 / 6) | tx_type 値域試験 |
| M8 | table の値域検査を外す (字句は正しい 11) | table 値域試験 |
| M9 | nS / nQ の非 0 を受理 (S/Q 行なし・nS だけ 1) | nS/nQ 試験 |
| M10 | R3 の正規形検査を外す (`01` を受理) | table 表記試験 |
| M11 | `_reasons` の照合を hex だけに戻す | 同一 txn 異表同 hex の理由試験 |
| M12 | compact の tx_type 復元を固定値にする | cycle の tx_type 試験 (異なる tx_type の節点) |
| M13 | result_to_dict_v3 が理由の table を出さない | 出力試験 |
| M14 | R1 の印を立てない | v3 非認定試験 |
| M15 | v3 の X/I 違反を収集しない | X/I の v3 試験 (循環・他違反なし frame で indeterminate) |

変異は `tools/mutation_harness.py` の dispatch (DW-M05・M07・M08)。期待 node は login の自走 probe か初回 dispatch probe で集める。
計算量の見込み: 変異 15 × test_verifier.py 1 file の走行 + 受入 1〜2 回 (≈ 0.25 node 時間/回) で 2 node 時間未満 (D2212 項 4 / D2219 項 1 の確認不要域)。
