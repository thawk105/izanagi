# 段 6 所見の裁定 (レビュー A・B、統合 commit 4449cd02a)

| ID | 所見 | 判定 | 処置 |
|---|---|---|---|
| S6-1 | A1・B1: driver の measure raw は最上位 `schema_version` = 1 (driver:932)、作図器は 3 以外を拒否 (作図器:166) | real・must-fix | 作図器を直す: raw の最上位 schema は driver の実出力 (1) を受理し、W 条件の各 run の `parsed.schema_version` = 3 を要求する。driver が `measure` で書く形そのもの (最上位 `runs`・`conditions`・`records` 等) の fixture を作り、作図器の入口から出力まで通す結合 test を足す (fixture の run の中身は driver の test の schema 3 fixture 生成と同じ形を使う)。driver は変えない |
| S6-2 | A2・B2: driver の smoke が W 条件の所要を測らない | refuted (実装不要) | 裁定 R11 は親の運用で満たす (smoke 1 job で inert witness と既存 build、続く所要 probe 1 job で W の極端条件と build キーの所要・maxrss を測り、親が見積もる)。driver の smoke 内の旧式見積りは判断に使わない。一次資料に実行した手順として書く |
| S6-3 | A3: abort 理由の名前が driver (`latest`・`scan_node_set` 等) と作図器 (`rmw_delete_latest`・`node_insert` 等) で食い違う | real | 作図器は driver の `ABORT_REASONS` を import して使い、別の名前表を持たない |
| S6-4 | A4: H4 の領域順位が常に `live_ratio` の中央値 | real | 一次資料 §1.5 に明記した順で並べる: H4 は通過率 → 境界年齢 p50 の bucket 上界の中央値 (公開 0 回 = 停止は無限大) → 論理生存版数 / record 数の中央値。H1 = h1、H2 = h2 の中央値 |
| S6-5 | B3: 領域に同じ機構・用途の定型文を付ける | real | 作図器は機構・用途の文を生成しない (列ごと外す)。領域ごとの解釈は親が一次資料に書く |
| S6-6 | B5: MB2 test が `state()` を直接呼ぶだけで `evaluate()` を通らない。`_install_parser()` が無処理 | real | MB2 test を 2 反復の run から `evaluate()` (状態表の生成) まで通す形に強める。無処理 helper を削除 |
| S6-7 | B4: 全点表が依頼の測る値より狭い。B「削れるもの」(未使用 `by_point`、H2 の直後に上書きされる代入、写すだけの SCHEMA3 辞書) | real (should) | 全点表 (CSV) に次の列を足す: site 別 (read_update・read_ronly・blind_write・rmw_latest・precheck・install・readcheck・writecheck) の位置 ≥1 / ≥4 / ≥8 の割合、read site の K = 1, 2, 4, 8 の「K より奥」の割合、楽観的候補率 K = 1, 2, 4, 8 (分母件数も)、abort 率、論理生存版数、生存 bytes の見積り (= 論理生存版数 × (sizeof_version + sizeof_ycsb)、列名に estimate を含める)、maxrss_kb、hot key の鎖長の最大・中央値。反復ごとと平均の両方。削れるもの 3 点は削除 |

S6-2 以外はすべて作図器とその test だけの変更で閉じる。driver・計器 patch は変えない。
変異の追加登録: MB5 = 作図器が raw 最上位 schema 1 を拒否する (旧実装) → S6-1 の結合 test が赤。MB6 = 作図器の abort 理由名を driver と別の表にする → abort 理由表の test が赤。
