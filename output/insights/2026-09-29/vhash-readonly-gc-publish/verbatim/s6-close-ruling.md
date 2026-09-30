# 段 6 レビューを閉じる裁定 — md_22 [T-2911] (2026-09-30 01:2x JST)

入力: 焦点再レビュー (`codex/stage6focus/out.md`、fix 統合は GO)、焦点走 3 (5c781ae7c、44 file、**5148 passed, 8 skipped, 0 failed**、01:12〜01:15 JST)、smoke3 (5c781ae7c、rc=0、`raw/smoke3.json`)。
fix の巡: fix1 (レビュー 2 本の所見 + 焦点走 1 の赤 10)、fix2 (焦点走 2 の赤 1)、fix3 (smoke1 の gate 停止)、fix4 (smoke2 の vlife flag)。DW-O16 の 3 巡上限はレビュー所見に対しては fix1 の 1 巡で、残りは親の実機 blocker (焦点走・smoke) の別枠。

| 所見 | 焦点再レビューの判定 | 親の裁定 |
|---|---|---|
| A1 探索範囲 | partial (3 worker・2 key・2 read は未探索) | 閉じる。一次資料では探索した 5 構成 (w2-k1-r1・w2-k1-r2・w2-k2-r1・w2-k2-r2・w3-k1-r1) を列挙し、上限全体の安全は主張しない。段 4 の A-1 は「2〜3 worker、1〜2 key、1〜2 read」の範囲指定で、全組合せの網羅は求めていない (w3 の 2 key・2 read は状態数の見積りで上限 200 万を超える見込み) |
| A2・B8 bad-raise-slot | partial (ro 途中の flag が要る条件付き正例) | 閉じる。正例は「陰性対照 neg-early-flag (ro 途中の flag、単独で違反 0) + ro 途中の slot 引上げ」の組として採用する。variant (commit 時だけ flag) では slot 引上げ単独で回収に届かないことをモデルの結論として書く (md_14 の不具合 = tx 途中の安全点で flag と slot を動かした、と同じ構造)。bad-clear-slot は safe-flag に slot の ∞ 化を 1 つ足した正例 |
| A6 rc=3 の受理 | partial (名称は変更、受理は維持) | 閉じる。Cicada の trace は証拠面が無く上限が indeterminate (md_3・md_14 の先例)。`verdict_label` で certified と区別済み |
| B6 非同居 | partial (照合結果が未提示) | 計測後に親が行う (本計測の job の hostname・時刻と、並走 wave の dispatch receipt の hostname・時刻を照合し、一次資料に結果を置く) |
| B7 非 ro の write の実行時確認 | partial | 閉じる (限界として記録)。workload の計数は試行・ro 試行・commit・長い ro だけで、非 ro の write 件数は数えていない。構造 test と実現 ro 率で担保し、一次資料の限界に書く |
| 新 should-fix「全構成 complete」の一般化 | real | 一次資料で「登録した 5 構成で complete」と書く (A1 と同じ) |
| 新 nit (vlife macro の test が AST の字面を見る) | nit | 実装しない。smoke3 の 4 run の argv に `izanagi_long_kind` が無いことを親が実測で確認済み |

変異の本走と受入は段 6 の続きとして親が行う (DW-S06-C)。
