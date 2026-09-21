# 段 4 裁定 (2026-09-21 22:1x JST、親)

入力: brief `brief.md`、段 2 `stage2/plan.md` (受理 rc=0)、段 3 `stage3/consult-a.md` (レンズ A 正しさ境界、受理 rc=0)、`stage3/consult-b.md` (レンズ B 実効性と過剰、受理 rc=0)。裁定 inbox を再走査: wave 開始後の更新は `2026-09-21-rulings-full30-verdicts.md` (21:47) の 1 件で、TPC-C に触れない (非関連)。

## 0. 形の裁定

- **コード・テスト・CCBench・patches は実装しない** (依頼「実装差分ゼロ」)。実装面の差分ゼロなので変異 matrix は免除 (DW-S04)。
- 成果物は docs のみ: insight `output/insights/2026-09-21/tpcc-trace-certification-design/README.md` (設計 v2 + 工数 + 容量 + 正例・負例 + 実装前の裁定事項) と、段 2・3 の全文の写し (`verbatim/`)、worklog fragment。decisions は作らない (未採用の設計提案)。
- 一次資料から事実を再抽出する docs wave なので、段 6 の read-only review を 1 本残す (DW-C00)。**本裁定で親が新たに採った「不在の観測を直接の証拠で決める」規則 (§2 の R4) は段 3 で攻撃されていないので、段 6 のレンズに明示的に入れる。**
- 受入全走は免除しない (DW-S04)。TPC-C の実験ではなく repo のテスト走で、2 node 時間の確認ラインを大きく下回る (見積りは段 6 投入前に記録)。

## 1. 所見の real / refuted

| 所見 | 判定 | 採否 |
|---|---|---|
| A1 到達可能性で不在を決める規則は偽認定を作る (反例: S が k を挿入前として空読み → I が k 挿入と y 更新 → D が k 削除 → S が I の y を読む。実 DSG は S→I→S の G2 だが、規則は D→S を選び非巡回にする) | **real、must-fix** | 採用。草案 §2.4 (i) と親 P4 暫定案を撤回。不在の観測版は直接の証拠で決め、無ければ indeterminate |
| A2 初期キー集合は必要。G 一覧だけでは同時欠落を捕えない | real (必要性) / 一覧の形式は refuted | 採用: 取得法 (ロード後の実木の走査) と、ロード側の件数との照合を分けて定義し、同時欠落 (common-mode) は非検出限界として明記 |
| A3 / B(P4) 物理 LIMIT の prefix は観測範囲であって可視行 LIMIT の完全性ではない | real | 採用: 認定契約 = 「物理候補が上限を埋め、返却件数 < 上限」の scan は indeterminate。上限到達時の実効範囲は [下限, 最後の物理候補] |
| A4 / B3 / B4 abort した INSERT の寿命 | 2 経路とも静的に real | 公開後・write set 登録前の return (3 CC) は **TPC-C では到達しない** (scan する取引は insert せず、insert する取引は scan しない: B3) → 必須工事から外し、CCBench の一般 API 欠陥として insight に構造化。abort 即時解放は全 5 取引で静的に到達しうる (NewOrder の品目 rollback 中に隣 order の line 0 を scan が拾う経路) → **段 2 の前提**。本体修正 (perf build の挙動も変わる) なので実装前の裁定事項へ |
| A5 / B(P1,P7) si は update / delete で読み集合の要素を消す (si:239-247, :352-362)。deleted 版も read set に入る (si:153-164) | real | 採用: si の読みは live / deleted / 不可視 / 自己版を区別して trace 専用履歴へ保存。ただし A6 により si は認定対象外なので優先度は低 |
| A6 si には X/P 証拠面が無く (`model.py:77-82`, `:450-465`; emitter は silo だけ = 親 grep)、形式だけの emitter は証拠の偽装になる | real、must-fix | 採用: **si は TPC-C の認定対象にしない (検出専用)**。非直列化判定は有効、「serializable」は X/P 不足で indeterminate のまま。si の証拠契約の設計は実装前の裁定事項 |
| A7 witness の TRACE 限定 quit 修正は妥当。試験は終了境界に加え、末尾 C frame・最大 txid・thread file 丸ごとの欠落を別々に | real、should | 採用 |
| A8 正例・負例の帰属不成立 (表欠落の見逃し例・二表 W 上書き例・手書き G2 を表識別の control に使う・到達可能性の例) | real、must-fix | 採用: 表識別は cycle でなく「表ありの参照グラフとの辺集合比較」で確かめる。到達可能性の例は削除。レンズ A の実取引 schedule (NewOrder→Delivery→StockLevel) を実 CC の焦点例に採る (静的案、未再現) |
| A10 / B 末尾 brief の「段 1 / 段 2 は確定裁定」は強すぎる (控えは「改訂推奨、明示確認は未取得」) | real、should | 採用: 「TPC-C 必須 (ユーザー意向) に対する親の分割案」と書く。再承認は求めない |
| B1 scan の述語を commit まで運ぶ容器は新設が要る。値で保存し `#if TRACE` 内に閉じる。物理末尾は scan buffer の順序から採る (`result.back()` ではない) | real、must-fix | 採用 |
| B2 草案の「YCSB v1/v2 入力を維持」は現行の v1 拒否 (`parse.py:323-326`) を緩める | real、must-fix | 採用: v1 拒否を維持。**si の現行 trace (v1) は YCSB でも parser が拒否する** = si は現状どの workload でも検証できない (新事実として insight へ) |
| B5 pin 前進は 1 回必要。旧 8b/8c の再凍結・旧 lock 移行は裁定控え項 5 により見積りから外す | real、should | 採用。稼働中の T-2844 (mocc X/P の候補 commit C) の上に積み、pin 前進を分けない |
| B6 17 単位・5 wave は暫定工程表でしかない | real、should | 採用: 必須でない単位を外し、review/fix・人間の push 待ち・計算投入を別欄にする |
| B7 段 1 を既存 flag で走らせると NewOrder 57% : Payment 43% (45:43 の正規化は表せない)。容量は約 1.37 GB / 百万 commit | real、should | 採用 |
| B8 OrderLine の番号差 (初期 1..O_OL_CNT+1、実行時 0..n−1、`[(o,1),(o+1,1))` は隣の line 0 を含む) | real (親も tpcc_initializer.hh:279 / neworder:314 で確認) | 採用: 実コードの範囲のまま扱う。workload の修正は trace 計装と分ける |
| B9 TPC-C の throughput 実測は repo に無い。2 node 時間未満とはまだ判定できない | real | 採用: 最初に小さい 1 走で throughput と trace 量を測る手順を工数に入れる |
| 親 P2 (quit 順序を counter 側で閉じる) / P3 (姓検索の索引は実行中不変。OrderStatus も同じ) / P6 (mocc watermark 不使用) / P8 (編集面と pin) | real | 維持 |
| 親 P1 / P4 / P5 / P7 | refuted (上記) | 訂正 |

## 2. 設計 v2 の要点 (insight 本文の骨格)

- **R1 (段 1 の形式):** TPC-C 専用 v3 frame。`C <txid> <thid> <epoch> <tid> <nR> <nW> <nS> <nQ> <tx_type>`、`R <txid> <table> <key> <ver_epoch> <ver_tid>`、`W <txid> <table> <key> <op> <epoch> <tid>`、`E <txid>`。v2 (YCSB) の判定・出力 bytes は不変、v1 拒否も不変、run 単位で schema を固定し混在は拒否。verifier の key は `(table, key_hex)`、object 経路と compact 経路の両方。
- **R2 (commit 計数):** `tpcc.hh` の commit 後 `quit_` 判定を `#if !TRACE` で囲み、trace build だけ成功 commit を必ず数える。witness は完全一致のまま。pipeline の allowlist は v3 と表識別が揃った tpcc binary に限って広げる。
- **R3 (段 2 の観測):** scan ごとに S 行 (表・両端と排他・上限・物理件数・返却件数・最後の物理候補・停止理由) と Q 行 (物理候補ごとの状態: live 返却 / tombstone 観測 (版つき) / 不可視 / 自己版 / 既読再利用) を値で buffer し、成功 commit の frame にだけ出す。
- **R4 (不在の観測版 — 親の新規採用、段 6 で攻撃させる):** 範囲内で返らなかった key の観測版は、(a) 挿入のみの key は「挿入前」で一意 (読み手 → 挿入者の predicate rw)、(b) 挿入 + 削除の key (TPC-C では NewOrder 表だけ) は **直接の証拠** で決める: Q の tombstone 観測 (版つき)、si は CC 自身の snapshot 時刻 (`txid_`) と挿入・削除版の `cstamp` の比較、silo / mocc は trace build だけの全体通し番号 (木への挿入の直前・木からの除去の直後・scan の開始・node 検証の終了) による前後関係。区間が重なるなど決まらなければ indeterminate。DSG の cycle 有無で観測版を選ばない。
- **R5 (初期キー):** trace build だけ、ロード後に scan 対象 3 表 (NewOrder・OrderSecondary・OrderLine) の実木を走査して初期キー一覧を出し、ロード側の件数と照合する。同一 process 由来の同時欠落は非検出限界として明記。
- **R6 (LIMIT の認定契約):** A3 のとおり。
- **R7 (CC ごと):** silo = 認定対象 (X/P 既存)。mocc = T-2844 の X/P 計装 + pin 前進の後に認定対象。si = 検出専用 (v3 frame と読み履歴を足せば非直列化の検出はできるが、certified にはしない)。
- **R8 (寿命):** abort 即時解放の本体修正は段 2 の前提。公開後・登録前の return は TPC-C では非到達なので必須工事から外す。

## 3. 実装前の裁定事項 (insight に推奨付きで載せる。本 wave は返答を待たずに終える)

1. si の扱い: 検出専用で進める (推奨) か、si 固有の証拠契約を設計するか。
2. abort 即時解放の本体修正 (perf build の挙動と baseline が変わる) を段 2 の前提として採るか。
3. pin 前進を T-2844 の候補 C の上に 1 回で行う順序。
4. 段 1 → 段 2 の分割 (親案) をそのまま使うか。
5. 最初の計算投入 (小さい 1 走で throughput と trace 量を測る) の node 時間見積りの確認。

## 4. 変異事前登録

なし (実装面の差分ゼロ、DW-S04 により免除)。
