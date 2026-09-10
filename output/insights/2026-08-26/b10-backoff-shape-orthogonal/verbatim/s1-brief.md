# 段 1 brief — B-10「待ち方と待ち量の直交切り分け」

基準: local main `e29084e0` / branch `worktree-dev-wave-b10-backoff-shape-orthogonal`。

## scope

`docs/paper-story/2026-08-26.md` §8 の B-10 が「未取得」と明記する 4 項目のうち、
**待ち方と待ち量の直交切り分け** 1 項目だけを取る。過抑制域の機序、ピーク位置の再現、
balanced の profile は本 wave の scope 外 (同じ grid が材料を副産するが、結論は出さない)。

現状の説明の穴: 既存の静的 backoff sweep (`orchestrator/campaign/backoff_sweep.py`) は
`BACKOFF_FIXED` = 待つマイクロ秒数を振っているだけで、待ち方は「毎回きっかり同じ長さ待つ」
1 種類に固定されている。したがって「backoff が効く」と言えても、効いているのが
**待つ総量 (throttling)** なのか **待ち方 (retry の時間的なばらけ方)** なのかを分離できない。

本 wave はこれを 2 因子の直交計画にする。**平均待ち時間を揃えたまま待ち方だけを変える。**

## 前提の実測 (brief 前に確認済み)

- 既存の backoff sweep 成果は 5 件すべて 2026-08-02 の旧物。稼働中 worktree 14 本の編集面に
  `backoff_sweep.py` / EVOLVE-BLOCK 合成枝の重複なし → 帯域外 sweep との衝突なし。実走へ進む。
- CCBench の待機実体は `include/backoff.hh` の `Backoff::backoff()`。
  `_mm_pause()` の busy spin を `clocks_per_us * now_backoff` サイクル分回すだけで、
  **`now_backoff` が待ち量、spin の回し方が待ち方**である。
- EVOLVE-BLOCK `silo-backoff-magnitude` の hole は **`now_backoff` を作る 1 行**
  (`patches/silo-backoff-fixed.patch` の `#if BACKOFF_FIXED >= 0` 枝)。
  ここが本 wave で唯一許される実装面の編集箇所。
- この hole 行の本文を pin しているテストは無い。`test_evolve_block_markers_structure_and_inert`
  はマーカー構造と「既定 -1 で stock と preprocess 後 byte 一致 (inert)」だけを見る。
  `test_diff_quarantine` / `test_s1_direct_comparison` は自前の合成テンプレを使う。
  `patches/ledger.json` は `registered-entries-only` で本 patch を登録していない。
- 動作点は D15 の t48 / 1M records / extime 3 / reps 5。

## 待ち方の作り方 (provisional、攻撃対象)

- **(P1)** 合成枝の 1 行を「平均を保ったまま形を選ぶ 1 式」に置き換える。
  行数は 1 行のまま保ち、hole の単一行前提を壊さない。
- **(P2)** 形は既存マクロ `BACKOFF_FIXED` の千の位に符号化する。
  `mean_us = BACKOFF_FIXED % 1000`、`shape = BACKOFF_FIXED / 1000`。
  0=一定、1=一様、2=二値。**0〜999 は現行と同じ意味のまま**なので既存 sweep は不変。
  新しいビルドフラグ・新しいマクロを足さない (合成枝の外を触らないため)。
- **(P3)** 乱数源は `backoff()` の入口で既に計算済みの `start` (rdtscp の値)。
  これを掛け算とシフトだけで撹拌する。新しい include・型・関数・マクロ定義・条件指令は書かない
  (D23 の閉じた領域制約)。
- **(P4)** 3 つの形は平均待ち時間が構成上ちょうど等しい。
  - 一定: 毎回 μ。ばらつき 0。
  - 一様: 0〜2μ の一様乱数。平均 μ、変動係数 0.577。
  - 二値: 確率 1/2 で 0、確率 1/2 で 2μ。平均 μ、変動係数 1.0。
  **つまり「待ち方」を「平均を固定したときのばらつき」として操作化する。**

## 事前登録する grid と判定規則 (走らせる前に commit する)

- **(P5)** cell = 形 3 × 平均 μ ∈ {2, 5, 10, 25, 50, 100} µs × workload 3
  (write-heavy rr5 / balanced rr50 / read-heavy rr95、既存 sweep と同じ座標系) = 54 cell。
  参照点として workload ごとに backoff 無し (`BACK_OFF=0`) と stock 適応 (`BACKOFF_FIXED=-1`)
  を各 1 点足す。ビルドは形 × μ の 18 種 + 参照 2 種 = 20 種で workload 間で共有される。
- **(P6)** 反復数は既存動作点どおり reps=5 / extime=3 s。実走前に固定し、後から増やさない。
- **(P7)** 判定規則 (事前登録):
  - 帰無仮説 = 「平均を揃えれば形は throughput を変えない (効いているのは待ち量だけ)」。
  - 各 workload・各 μ で、一様・二値の throughput を一定と比べる。
    差が calibrator の実測 noise floor (within-run 変動係数) を超えた cell だけを有効差とする。
  - **「待ち方が効く」と言えるのは、同一 workload で 6 個の μ のうち 2 個以上が
    同じ符号の有効差を示したときだけ**とする。1 点だけの差は報告するが結論にしない。
  - 有効差がどの workload にも出なければ、結論は「本 grid の解像度では待ち量だけで説明でき、
    待ち方は効かない」と書く。**この否定の結論も成果である** (B-10 の穴は埋まる)。
  - read-heavy は abort が少ないので形の効果も消えるはず、という**反証点**として置く。
    ここで差が出たら機構仮説そのものを疑う。
- **(P8)** レコード数は calibrator に決めさせる。既存の 1,000,000 を再検証し、
  cache miss 率が飽和する最小値を採る (規律 4 — 大きすぎる罠と、48 スレッドの競合が
  再現されない小さすぎる罠の両方を避ける)。calibrator の出力が現行値と違えば calibrator に従う。

## 不変条件 (緩めない)

- **規律 1**: 性能計測は trace 無効ビルド、正しさ検証は trace 有効ビルド。**別ビルド・別 run**。
- **規律 2**: verifier が anomaly を返した variant は即 reject。fitness 失格。
  形の変異は待ち時間しか変えず CC 論理を触らないので serializable のはずだが、**必ず検証する**。
- **規律 4**: レコード数は calibrator の飽和点。
- 実装面の編集は **hole 1 行 + 新規 driver + そのテスト** のみ。
  EVOLVE-BLOCK マーカー・stock 枝・骨格・`cmake/Options.cmake` は不可触。
- `BACKOFF_FIXED` が 0〜999 のときの意味を変えない (既存 sweep の後方互換)。
- perf に依存する診断は範囲外 (この計算ノードに perf は無い)。
- 計算ノードの占有と単独性確認は `docs/pegasus-runbook.md` に従う。

## 成果物

1. `patches/silo-backoff-fixed.patch` の合成枝 1 行の変更。
2. `orchestrator/campaign/b10_backoff_shape_sweep.py` — grid driver
   (`backoff_sweep.py` と同型の座標系、`s6_sort_sweep.py` と同型の列挙・レポート)。
3. その単体テスト (形の平均が構成上等しいことの有限モデル検査を含む)。
4. 事前登録文書 — 因子・cell・反復数・判定規則を**実走前に commit** する。
5. 実走結果 (campaign) と、B-10 に答えるレポート。

## 成果物影響 (DW-G05)

これを取らない場合、論文の「backoff の機序を説明した」は
「待つ量と待ち方のどちらが効いているか分からないまま『backoff が効く』とだけ言っている」状態に留まる。
B-10 の 4 項目のうち 1 項目が未取得のまま残り、機序主張に限定表現が必要なままになる。

## 並列分割

- 段 2: プラン起草 1 本 (read-only codex)。
- 段 3: 敵対相談 2 本 — レンズ A = 実験設計・事前登録の妥当性 (交絡・平均一致の実効性・判定規則)、
  レンズ B = 機構安全 (合成枝の閉じた領域制約・inert・後方互換・digest 影響・規律 1/2 の破れ)。
- 段 5: 実装子 1 本 (Codex author、D95)。段 6: レビュー 2 本 + fix。
