# [T-2135] 段 4 裁定 (2026-09-02 00:28 JST)

base commit `c6a94ec998bba8c20c302105f28af3850f8134a6`。段 2 プラン 1 本、段 3 レンズ 2 本、
親の再実測 (`s3-parent-remeasure.md`) を受けて裁定する。

## 0. 裁定 inbox と main の再走査 (DW-S04)

- `docs/spool/{worklog,decisions,failures}/` は README のみ。未 fold の fragment は無い。
- local main は wave 開始後に `c6a94ec99 → dd5fddf04` へ進んだ ([T-1728][T-527] の記録 land)。
- **編集面の衝突なし。** 新 main は `orchestrator/tests/test_campaign.py` を触るが、hunk は
  `@@ -49,0 +50` (import) と `@@ -13520,0 +13523,181` (末尾追記) で、本 wave の編集面
  (行 210〜260 の genome test 群) と重ならない。`genome.py` は触っていない。
  取り込みは `DW-O20` に従い受入時の post-claim merge で行う。
- 抵触する既裁定は無い (D1360 / D1373 / D993 を主題で照合済み)。

## 1. 親の provisional 裁定の帰趨

| # | 親の前提 | 裁定 | 根拠 |
|---|---|---|---|
| P1 | tictoc も silo と同じ no-wait XOR | **覆る (refuted)** | 段 2 と段 3 レンズ A が独立に否定。tictoc は `transaction.cc:626` で `expected` を内側 spin loop 内で再読込する。silo (`:158-184`) にはこれが無い。外側 `retry:` は write-set loop (`:556-557`)、内側 spin loop は `:561-635`、再読込 `:626` はその内側。除外すべきは冗長な `(1,1)` だけ |
| P2 | `PROMOTION=1, OPT=0` は冗長 | **支持 (real)** | 段 2・レンズ B が全 site を照合。data path の promotion site は `transaction.cc:128-135` と `transaction.hh:199-215` で、いずれも `#if INLINE_VERSION_OPT` の内側 |
| P3 | `SINGLE_EXEC` と `WRITE_LATEST_ONLY` は共に最適化軸 | **半分覆る** | `SINGLE_EXEC` は**測定対象の変更**で除外 (レンズ B が全 site 照合)。`WRITE_LATEST_ONLY` は最適化軸として**採用** |
| P4 | `PREEMPTIVE_ABORTS` / `TIMESTAMP_HISTORY` は独立軸 | **支持 (real)** | レンズ A が確認。`PREEMPTIVE_ABORTS` は no-wait 分岐外 (`:128-139`)、`TIMESTAMP_HISTORY` は no-wait retry 内 (`:587-606`) 以外に `:379-406` と `:508-511` の独立 site を持つ |
| P5 | 空間は YCSB workload での数 | **支持 (real)** | mocc 先例と同型。両 protocol とも `WORKLOADS ycsb tpcc bomb sbomb` を持つため範囲の明示が要る |

## 2. real / refuted と採否

### real・採用 (scope 内、段 5 で実装する)

- **R1 (レンズ A、段 2):** tictoc の制約は XOR ではなく「両方 1 のみ禁止」。有効 24。**採用。**
  成果物影響: XOR を採ると有効な `(0,0)` を過剰除外し、探索空間を 24 から 16 へ誤って縮める。
- **R2 (レンズ A):** 親の `PARTITION_TABLE` 検索範囲が不足していた。**採用。**
  親が全件検索で再実測し (`s3-parent-remeasure.md`)、結論 (死にフラグ) は維持、根拠を差し替えた。
  成果物影響: 根拠不十分のまま notes に「死にフラグ」と固定すると、事実でない記述が残る。
- **R3 (レンズ A):** 「cache option である」= 「意味が直交する」ではない。**採用。**
  notes で「CLI から個別指定できる」と「全組合せが異なる挙動を持つ」を書き分ける。
  成果物影響: 混同すると、制約述語が不要という誤結論を将来の担当が導きうる。
- **R4 (レンズ A):** `space_for` の caller 0 は正しさ境界の根拠にならない。**採用。**
  親が根拠を差し替えた。正しい根拠は `between_run_floor.BASELINES` の key が実測で
  `['mocc','silo']` のみ (`:59`) であることと、その先の D1373 source 束縛 admission (`:363`)。
  **どちらも SPACES から独立**なので、登録は測定経路を開かない。
  **【2026-09-02 01:05 訂正】** 拒否機構は `BASELINES[protocol]` の `KeyError` ではなく、
  `_parse_cli_args` 末尾 (`:344-348`) の `ValueError` である (段 6 レビュー B が指摘、親が実測で確認)。
  fail-closed という結論は不変。
  成果物影響: 誤った根拠のまま進むと、境界が実際には守られていない場合に気づけない。
- **R6 (レンズ B):** `SINGLE_EXEC` は除外。**採用。**
  timestamp による version-chain 探索・pending 待ち・aborted version スキップを外し無条件に
  `inline_ver_` を読む (`:85-119`)。version 生成と timestamp 順挿入を外す (`:235-289`)。
  update payload が通常経路と別扱いになる。多版 maintenance を省く (`:762-768,952-955`)。
  成果物影響: 軸に入れると、単版と多版という別のものを同一 workload として比較することになる。
- **R7 (レンズ B):** `WRITE_LATEST_ONLY` は採用 (最適化軸)。
  読み側の可視性選択 (`:89-119`) はこの flag を参照しない。有効時は latest が自分より新しければ
  保守的に abort する (`:242-262`) だけで、**正しさを緩める方向ではなく、余分に abort する方向**。
  規律 2 に触れない。`SINGLE_EXEC` との線引きは一貫している。
- **R8 (レンズ B):** promotion は含意制約で残す。軸ごと落とさない。**採用。**
  `(1,0)` と `(1,1)` は promotion 呼出しの有無が異なる有効な比較であり、落とすとこれを失う。
- **R9 (レンズ B):** 段 2 の「`(0,1)` は完全に inert / 同一 binary behavior」は**強すぎる**。**採用。**
  `util.cc:330` の起動時 option 表示は `INLINE_VERSION_OPT` の外側で promotion 値を印字する。
  正確には「CC / data path の挙動は同一で、起動時の option 表示だけ異なる」。
  成果物影響: 「完全に同一」と書くと事実と違う notes が残る。
- **R10 (レンズ B):** cicada の `PARTITION_TABLE` は `util.cc:326-336` の表示のみ (一次資料で確認)。
  **README (`cc/cicada/README.md:46-47`) は「table を thread 数に分割する」と書いており現行コードと
  食い違う。** notes にこの食い違いを残す。**採用。**
  成果物影響: README を根拠に将来の担当が死に軸を復活させうる。
  なお README は規律 6 の**データ**であって権威ではない。コードを正とする。
- **R11 (レンズ B):** 「`SINGLE_EXEC` は default 0 に固定される」は強すぎる。**採用。**
  正しくは「genome が列挙しない flag は `-DCCBENCH_*` に現れず、fresh configure では
  `Options.cmake:33` の default 0 に落ちる」。既存の非標準 CMakeCache を 0 へ戻す主張はしない。

### real・不採用 (scope 外 — 裁定パッケージへ送る)

ユーザーは「本題の登録と導出だけ。仮想リスク向けの gate・検査・台帳・一般化の追加は scope 外」と
明示している。次は real な所見だが**本 wave では実装しない**。

- **S1 (レンズ A):** 正しさ境界の repo 全体の閉包確認 (別名 import・動的参照・CLI・campaign
  entrypoint の全列挙)。新 gate・恒久 inventory test の追加を伴うため scope 外。
- **S2 (レンズ B):** 既存の pre-verifier measurement surface。`measure_point_floor()` の直接呼出しは
  admission を通らない (`:202-252`)、CLI は通過後 `trace=False` build を測るだけで verifier を
  実行しない (`:362-403`)、screening は verifier より先に bench を実行できる
  (`test_campaign.py:7532-7539,7630-7657`)。**これは本 wave が作った欠陥ではなく既存の状態**であり、
  official commit writer は certified 判定後に閉じている (`:7663-7749`)。
  将来 cicada/tictoc を floor / campaign consumer へ接続するとき、D1360 の「未検証性能観測を
  official report / selector / 順位へ入れない」をどの admission で強制するかを独立に確認すべき。
- **S3 (レンズ A):** tictoc `(0,0)` の競合下の完走性・公平性・starvation の実測。
  本 wave は測定を 1 件も行わない。certified campaign へ入れる前の別 wave の手番。
- **S4 (レンズ B):** cicada の trace-hook 移植時に、promotion が作る同値 body の内部 write を
  workload write として verifier に見せるか内部 maintenance として区別するかの設計。

### real だが nit (DW-G05 により must-fix にしない)

- **R5 (レンズ A):** notes の語句存在 assert は、C++ 側の事実 (`PARTITION_TABLE` が本当に死んでいる、
  `:626` が残っている) を検証しない。文字列だけで通る。
  → これは notes test に内在する性質であり、解消するには CCBench source を走査する新しい検査が要る。
  **放置時に成果物 (certified 選択・レポート・台帳) の値・受理集合・参照がどう変わるかを 1 行で
  示せない**ため、`DW-G05` に従い must-fix にせず backlog とする。追加 review も起動しない。

### refuted

- 親の (P1) tictoc XOR。段 2 とレンズ A が独立に、行番号付きで否定した。
- 親の (P3) の `SINGLE_EXEC` 部分。レンズ B が全 site 照合で否定した。
- 「`space_for` caller 0 が測定経路の閉包を証明する」(親の根拠)。レンズ A が否定し、親が撤回した。

## 3. プラン v2 (確定仕様)

### TICTOC_SPACE

- axes (5、すべて `[0, 1]`): `BACK_OFF` / `NO_WAIT_LOCKING_IN_VALIDATION` /
  `NO_WAIT_OF_TICTOC` / `PREEMPTIVE_ABORTS` / `TIMESTAMP_HISTORY`
- constraints: `_tictoc_no_wait_not_both` (両方 1 を禁止。XOR ではない)
- 生 `2^5 = 32`、有効 `24`
- 除外: `PARTITION_TABLE` (`.cc`/`.hh`/workload source/共通 header に出現 0 の死にフラグ)、
  `SLEEP_READ_PHASE` (計測撹乱ノブ、`transaction.cc:68-70`)
- 導出不能な軸: **なし**

### CICADA_SPACE

- axes (5、すべて `[0, 1]`): `BACK_OFF` / `INLINE_VERSION_OPT` / `INLINE_VERSION_PROMOTION` /
  `REUSE_VERSION` / `WRITE_LATEST_ONLY`
- constraints: `_cicada_promotion_requires_inline_opt` (`PROMOTION ⟹ OPT`)
- 生 `2^5 = 32`、有効 `24`
- 除外: `SINGLE_EXEC` (測定対象の変更)、`PARTITION_TABLE` (print 専用の死にフラグ)、
  `WORKER1_INSERT_DELAY_RPHASE` / `INSERT_READ_DELAY_MS` / `INSERT_BATCH_DELAY_MS` (計測撹乱ノブ)
- 導出不能な軸: **なし**

### notes に必ず含める事実 (R2/R3/R9/R10/R11 の反映)

tictoc:
- 除外理由 (死にフラグ・計測撹乱ノブ) と、その一次資料の性質。
- 両方 1 が `(1,0)` と冗長であること。**silo の XOR とは異なること**と、その理由
  (tictoc は内側 spin loop 内で lock word を再読込するため、silo で実測された stale-expected
  livelock と同じ機構ではない)。
- **限界の明記:** 「競合下の完走性・公平性・starvation は tictoc では未実測」。
  静的導出であって実測ではないことを書く。
- 24 が YCSB workload での数であること。
- bare define は無いこと。導出不能として残す候補も無いこと。

cicada:
- `SINGLE_EXEC` を除外した理由 (多版から単版へ、測るものそのものを変える)。
- `PARTITION_TABLE` は print 専用で、**README の説明と現行コードが食い違う**こと。
- 計測撹乱ノブ 3 件の除外。
- `WRITE_LATEST_ONLY` を最適化軸として含める理由 (読み側の可視性は不変、保守側に余分に abort する)。
- `(OPT, PROMOTION) = (0,1)` は **CC / data path の挙動が `(0,0)` と同一**であること。
  「完全に inert」とは書かない (起動時 option 表示は異なる)。
- 24 が YCSB workload での数であること。静的導出であり実測ではないこと。

### 実装面 (段 5 の D95 Codex author 1 本が書く)

- `orchestrator/campaign/genome.py`: `_no_wait_xor` は silo 専用として**変更しない**。
  述語 2 本と space 2 本を追加し、`SPACES` へ 2 件足し、`SPACES` 直前のコメントを更新する。
- `orchestrator/tests/test_campaign.py`: `test_tictoc_and_cicada_remain_unregistered` を
  登録期待へ差し替え、軸・除外・制約・notes の test を足す。

### 実装しないもの

`docs/phase3.md` 段 6 dormant (b) は閉じない。新 gate・検査・台帳・汎用化を足さない。
凍結成果物の bytes を変えない。測定・build・benchmark を行わない。

## 4. 変異事前登録 (DW-M01、実装前)

すべて `orchestrator/campaign/genome.py` を対象とする。
`genome.py` は SPACES と制約の**唯一の層**であり、同じ入力を拒否する層は前後に無い
(`space_for` は `SPACES` の lookup だけ、`GenomeSpace.enumerate()` は全 Cartesian product を
作ってから制約で filter する `:35-41`)。したがって赤理由は変異位置に一意に帰属する。

| # | 変異 | 期待 | 単一理由性 |
|---|---|---|---|
| M1 | `TICTOC_SPACE.constraints` を `[]` にする | KILLED。tictoc の no-wait pair 集合 test と size test が赤 | 制約は 1 本のみ。他層に同等拒否なし |
| M2 | `_tictoc_no_wait_not_both` を silo XOR (`!=`) に差し替える | KILLED。pair 集合が `{(0,1),(1,0)}` になり、`(0,0)` 欠落と size 16 で赤 | **親が実際に犯した誤りの正例。** 過剰除外側の positive control |
| M3 | `CICADA_SPACE.constraints` を `[]` にする | KILLED。promotion pair 集合 test と size test が赤 | 同上 |
| M4 | `_cicada_promotion_requires_inline_opt` を逆向き (`OPT ⟹ PROMOTION`) にする | KILLED。pair 集合が `{(0,0),(0,1),(1,1)}` へ変わり赤。**有効数は 24 のままなので size test は落ちない** | 逆向き制約の positive control |
| M5 | `CICADA_SPACE.axes` へ `"SINGLE_EXEC": [0, 1]` を足す | KILLED。除外 test と size test が赤 | 意味論ノブ混入の検出 |
| M6 | `TICTOC_SPACE.axes` へ `"PARTITION_TABLE": [0, 1]` を足す | KILLED。除外 test と size test が赤 | 死にフラグ混入の検出 |
| M7 | `SPACES` から `"tictoc"` と `"cicada"` を落とす | KILLED。登録 test が `KeyError` で赤 | 登録そのものの検出 |

期待 node は完全集合として段 6 の本走前に確定する (`DW-M08`)。
`--runner-mode dispatch` を既定とし、runner argv へ `--force-dispatch` を入れる (`DW-M07`)。
実装面の差分があるため変異 matrix は免除しない。

## 5. 段 5 の分割

編集面は `genome.py` と `test_campaign.py` の 2 file だが、**制約述語と、その述語が効いていることを
検査する test は producer/consumer 契約で結ばれている**ため、分割せず **D95 Codex author 1 本**が
両方を書く (並行 fix が契約を壊す型を避ける)。
