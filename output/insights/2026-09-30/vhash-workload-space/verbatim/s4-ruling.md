# 段 4 裁定 — dev-wave vhash-workload-space (md_29、md_28 を統合)

入力: brief.md、stage2/plan.md (条件付き GO)、stage3/parent-notes.md、stage3/consult.md (条件付き GO)。裁定時点の local main = 4f412c67b (開始から不変)。T-2933 は未裁定のまま。

## 所見の裁定

| 所見 | 判定 | 採否・処置 |
|---|---|---|
| plan P0 (全 worker 1000 操作と batch 1 本の区別) | real | 操作数軸 (全 worker の ycsb_max_ope) と長い tx 軸 (batch worker 1 本) を別軸にする (R1) |
| plan P1 (wait10msR は W5 と衝突) | real (理由は一部誤り: wait10msU も待つ型) | 待つ型を全廃し、長い tx = {none, batchU, batchR} (batch_th_num=1、izanagi_long_kind=1/2、batch_max_ope=1000) |
| plan P2 (BEST100 の 1000 操作は外挿) | real | 採用。一次資料に外挿と明記 |
| plan P3 (時刻分割は介入後の値ではない) | real | R7 |
| plan P4 (分母・別状態) | real | R3 |
| plan P5・consult 3 (候補の安定性) | real | R4 |
| plan P6・consult 6 (L3 収容の断定) | real | record 軸は熱さの軸とし、cache 収容は maxrss 実測なしに主張しない |
| plan P7・consult 5 (bytes の内訳) | real | R5 (sizeof(Version)・sizeof(YCSB)・VAL_SIZE を echo、run ごとの maxrss を driver が記録) |
| plan P8・consult 6 (5 s/走は根拠にならない) | real | R11 (極端条件 smoke の実測で投入判定、縮小順を事前登録) |
| consult 1 (S 層に batchR が無い) | real | S 層の長い tx を 3 水準にする (R1) |
| consult 2 (H4 が公開停止を見落とす) | real | 公開 0 回を「停止」(右打ち切り) として別状態・通過扱いにし、境界遅延と版の蓄積を別判定 (R3) |
| consult 4 (H2 が失敗負荷を優先) | real | abort 率を H2 の条件から外し、commit 数・候補件数の下限を置く (R3) |
| consult 7 (md_28 の図と現実性の節) | real | R9、R10 |
| consult 8 (鎖走査時間が wall に入る) | real (nit) | 走査時間を別 field に記録 (R5) |
| consult「abort 理由の細分類は重い」 | refuted | 分類箇所は plan の表で 8 種・数か所の代入に留まり、md_28 が理由を要求する。そのまま採る |
| consult「L27 の 2 本目は削れる」 | 保留 | 縮小順の 1 番目に置く (R11)。削るかは smoke の所要だけで決める |

## plan v2 (事前登録、結果を見る前に固定)

- **R1 点の選び方。** 層 S = skew {0.5, 0.6, 0.7, 0.8, 0.9, 0.95, 0.97, 0.99} × rr {5, 50, 95} × 長い tx {none, batchU, batchR} = 72 点。他軸は中心値 (record 1,000,000・操作 10・ro 0%・値 4 B・thread 48・gc_inter_us 100)。層 O = `design/make_design.py` の L27 2 本 (O1・O2、各 27 点、重複 0、任意の 2 列で 9 組が各 3 回) = 54 点、因子と水準は skew {0.6, 0.9, 0.99}・rr {5, 50, 95}・record {1万, 10万, 100万}・操作 {10, 100, 1000}・長い tx {none, batchU, batchR}・ro {0, 50, 95}%・値 {4, 100, 1000} B・thread {12, 24, 48}・gc {10, 1000, 100000}。長い tx ありの点は通常 worker = thread − 1、batch 1。skew 0.995・0.999 は足さない (YCSB の既定の zipf 定数が 0.99 であることは原典確認後に書く。0.99 超は予算と現実性で外す)。計 126 点。
- **R2 genome と反復。** 全点を既定 (default) と負荷の最良 (操作 10 → tuned = BEST、操作 100・1000 → best100 = {BACK_OFF 0, INLINE_VERSION_OPT 0, PROMOTION 0, REUSE 0, WLO 0}) の 2 通り、各 2 反復。1000 操作への best100 は md_11 の範囲外の外挿。gc_inter_us は軸で、最良の gc に固定しない。126 × 2 × 2 = 504 走。
- **R3 述語 (点 × genome ごと)。** 状態は 通過 / 境界 (2 反復の片方だけ通過) / 不通過 / 判定不能 (rc≠0・timeout・parse 失敗・分母の下限未満)。
  - H1: h1 = (read_update と read_ronly のうち位置 ≥ 1 の件数) / (read_update と read_ronly の全件数)。u1 = read_update の位置 ≥ 1 の割合。通過 = h1 ≥ 0.10 または u1 ≥ 0.05。分母下限: read 全件 ≥ 10,000 (u1 は read_update ≥ 10,000 のときだけ使う)。
  - H2: h2 = 楽観的候補数 (K=1) / read_update 全件数。通過 = h2 ≥ 0.01 かつ候補件数 ≥ 100 かつ update commit ≥ 1,000 / 走。abort 率と理由は併記し、条件にしない。
  - H4: 2 つの副述語を別々に判定し、どちらかで通過。H4-lag = 境界年齢 p50 の bucket 上界 ≥ 1,024 µs、または MinRts 公開 0 回 (「停止」= 右打ち切り、通過として別表示)。H4-live = 論理生存版数 ≥ 1.1 × record 数。
  - 「上限」は観測時点の頻度・機会量であり、実装したときの性能向上率ではないと一次資料に明記する。
- **R4 候補領域の選び方。** 全点 × 2 genome の状態表を全件公開する。領域 = O 層では 1 因子の 1 水準 または 2 因子の水準の組、S 層では (rr, 長い tx) を固定した skew の連続区間。採用条件: (a) O 層の組は O1・O2 の両方で支持 3 点中 2 点以上が通過 (1 水準の領域は両方で 9 点中 6 点以上)、S 層の区間は区間内の全 skew 水準で通過し長さ ≥ 2 水準、(b) default と最良の両 genome で (a) が成り立つ。H ごとに (a)(b) を満たす領域を通過率・指標の中央値の順に並べ、H1・H2・H4 から最大 2 個ずつ、計 3〜5 個を採る。満たす領域が 3 未満なら不足と書き、最も近い領域を「未達」と明記して並べる。領域ごとに確かめるべき機構 (前進 C・GC 接続 E・hot 配置 B・区間 GC・read-only commit の公開) と、現実の用途との対応を書く。
- **R5 計器・driver の拡張 (単位 A)。** 新条件族 W (既存 A/B/R/S/T の dict・argv・build・parse は 1 bit も変えない、固定 fixture の回帰 test)。build キー (genome, val_size) を重複なく build し、`-DCCBENCH_VAL_SIZE` と compile command の `VAL_SIZE` を照合。schema 3: build に val_size・sizeof_version・sizeof_ycsb(値の確保単位)、worker に abort 理由 (1 試行 1 件、最初に失敗を確定した箇所、plan の 8 分類 + other、合計 = aborts を parser で検査)、走行末に key 0〜7 の鎖長 (worker join 後、run() 直後の明示呼出し、二重出力なし、未発見・異常は別表現、走査時間を別 field)。driver は run ごとに子の maxrss を記録。既存 2 macro の中に閉じ、新 macro を足さない。既定 build の inert witness (正規化 objdump・rodata・nm・strings) は smoke で再確認。
- **R6 作図・集計 (単位 B)。** `tools/plotting/plot_vhash_workload_space.py` を新設。入力は measure raw 複数 + 条件表。raw の stdout 再 parse と parsed の一致、ID 重複・欠測・build キー不一致・反復不足を拒否。R3 の状態判定、R4 の領域選択を実装し、全点表 (CSV/Markdown)・候補表・図を出す。FIGURE_CONVENTIONS.md に従う。
- **R7 T-2933 の 2 場合。** H4 の表に stock 観測と、時刻分割による ro flag 機会 (local_flag_opportunity、md_15 と同じ定義) を並べ、介入後の値と呼ばない。
- **R8 観測者効果。** 計器入り build の throughput・wall_s は性能値に使わない。
- **R9 図。** (i) md_28 の skew 図 3 枚 (位置 ≥1・≥8 の割合、候補率、abort 率 vs skew; rr・長い tx・genome 別、反復点を描く)、(ii) 軸ごとの伸びしろ (O 層の主効果、H1・H2・H4-lag・H4-live、各点を描く)、(iii) 熱いキー鎖長と熱いキー数 (zipf の式からの解析値、実現値ではないと明記) の表、(iv) 候補領域の表。
- **R10 現実性の節。** 親が docs として書く。原典で確かめた範囲だけ (YCSB の zipf 定数、長い read-only の用途は md_1・motivation-evidence の既読原典)。
- **R11 予算と縮小順。** 先に smoke 1 job: 既定 build の inert witness、全 build キーの build 所要、極端条件 (操作 1000・record 100 万・値 1000 B・skew 0.99・batchU / batchR、各 genome) の 1 走所要と maxrss。smoke の**所要時間と maxrss だけ**から本計測の見積りを出し (伸びしろの値は見ない)、焦点走・変異・受入の見込み (≈ 0.5 node 時間) と合わせて 2 node 時間以上なら、縮小順 (1) O2 を落とす → (2) S 層の skew 0.5・0.7 を落とす、の順に適用する。なお超えるなら投入せず見積りを書いて止める。
- **R12 分割。** 単位 A (patch・driver・test・condition gate の件数 pin・patches/README.md の追記) と単位 B (作図器・その test) は所有素集合で並列。B は A の schema 3 を本裁定の field 名で先取りし、合成 fixture で test する。

## 変異の事前登録 (DW-M01)

実装後に位置・単一理由性を確かめて最終登録する。kill 期待 node は実装後に login 自走 probe で集める。
- MA1: W 条件の `_flags` が条件の records を使わず smoke の records を使う → W 条件の argv test が赤。
- MA2: 旧条件の `_flags` が条件 dict の操作数を読む形に変わる (旧条件の argv が変わる) → 旧条件 fixture の回帰 test が赤。
- MA3: parser の「abort 理由の合計 = aborts」検査を外す → 合計不一致の負例 test が赤。
- MA4: VAL_SIZE 照合を外す → 値サイズ不一致の負例 test が赤。
- MA5: best100 の genome 引数を tuned と同じにする → genome 引数 test が赤。
- MB1: 作図器が raw 再 parse と parsed の不一致を拒否しない → 不一致の負例 test が赤。
- MB2: 通過判定を 2 反復の片方だけで行う → 境界状態の test が赤。
- MB3: 公開 0 回を H4 不通過にする → 停止状態の test が赤。
- MB4: 領域選択が genome 条件 (b) を無視する → 片方 genome だけ通過の負例 test が赤。
