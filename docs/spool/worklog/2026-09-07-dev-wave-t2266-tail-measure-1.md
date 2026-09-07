---
schema: izanagi-spool-v1
ledger: worklog
authored: 2026-09-07
wave: dev-wave-t2266-tail-measure
seq: 1
title: [T-2313] 歩行 model へ実測 tail の入力機構を足し、旧 model の指数外挿が tail を 20〜40 倍過小評価していたことを確定した — [T-2266] の投入は関門で止まり、測定は T-2320 wave が完遂した (コード + テスト + 解析、branch worktree-dev-wave-t2266-tail-measure、変異 10/10 KILLED + 等価 1 SURVIVED)
---

## 本文

- **依頼の核心である「旧 model の指数外挿との乖離」を数値で確定した。** 事前登録した R6 は
  「旧 model (tail 無し) の外挿値を 150/200/300/500/750/999 µs で評価し、実測 5 rep 平均との比を取る」で、
  両辺とも手元にあるため歩行 model の再走を待たずに出せる。外挿/実測の比は 3 workload とも単調に減少し、
  999 µs で write-heavy 0.052、balanced 0.023、read-heavy 0.036 だった。**旧 model は tail を 20〜40 倍
  過小評価していた。** 150 µs では 1 割以内の差でしかなく、b が伸びるほど外れが開く。
- **実測の減衰は指数ではない。** 999 µs でも write-heavy は 992,863 tps で、100 µs 時点の 42% を保つ
  (balanced 39%、read-heavy 38%)。指数外挿が予測した「消える」形にはならず、緩やかに下がって床へ近づく。
  abort 率も 3 workload とも 999 µs まで単調に下がり続け、頭打ちにならない。tail の上端でも backoff の
  abort 抑制が飽和していないことを、rep 単位の値で初めて確認した。
- **model の所要時間の増加そのものが、tail 補正が効いている傍証である。** `_simulate_condition` は
  3 秒 (`DURATION_US`) を leader period 刻みで進める。旧 model は tail で throughput が指数的に消えたので
  大 backoff 域の刻みが粗く軽かった。実測 tail では刻みが細かいままで反復が桁で増え、旧走行 728 秒に対し
  40 分の walltime でも完走しない。事前登録した閾値・種・反復・評価経路 (R5) は触っていない。
- **[T-2266] の投入は本 wave で行ったが、測定条件関門で止まった。** 2026-09-05 13:18 JST、固定 checkout
  (local main 2632aed56) から 978201 / 978202 / 978203 を投入し、3 本とも経過 90 秒・rc=1・stage
  `t2266_tail_sweep` で `BACKOFF_FIXED=red/preprocess-failed` を 7 件返した。campaign 台帳 0 件、成果物 0 件。
  [T-2211] と同型の 3 例目である。**着地済み機構であっても、関門を通した実測が無ければ投入は成立しない。**
- **再投入は [T-2320] wave が担い、3 回目で完遂した。** 重複投入を避けるため本 wave では再投入せず、
  同 wave の brief を job dir で裏取りしたうえで [T-2313] に絞った。3 回の失敗型はすべて当方も現物で確認した。
  1 回目は共有 submodule gitdir を A-5 job の `git worktree prune --expire now` が削り 5 job が同時に rc=128。
  2 回目は 8 点を commit し切った後、凍結 view が list を tuple・dict を MappingProxyType にするのに
  突合が `list == tuple` で行われて必ず不一致になり report 生成が停止した。**t2266-tail mode が report 段へ
  到達した実走は 2 回目が初めてで、単体テストは view を list / dict で手組みしていたため見えていなかった。**
  3 回目 (job 979843 / 979844 / 979845、修正 `2177b85aa`) が完走し、rep 単位値の正本は
  `output/insights/2026-09-04_t2266-backoff-static-tail/README.md` §8 になった。
- **[T-2313] の補間規則は投入前 (2026-09-05 13:10 JST) に、結果を見る前に固定した。** R1 較正格子 =
  静的 7 点 (2 rep) + tail 6 点 (5 rep) の昇順結合、R2 全 rep 算術平均、R3 補間・外挿は既存規則のまま、
  R4 tail の none / adaptive は使わない、R5 閾値・種・反復・評価経路不変、R6 旧 model の指数外挿との比、
  R7 混合仮定は検証せず結論は 3 択。逐語は insight §1。
- **Codex author 1 本で model へ `--tail-json WORKLOAD=PATH` を足した。** 0 本または 3 workload 各 1 本だけ
  受理する。受理検査は構造 (schema / run_kind / status / workload / source_measurement /
  performance_certified / realized_us exact / static 6 点 / rep 5 本 / 値域) で、byte 級 pin は足していない。
  同一性は `provenance.tail_inputs` の path と sha256。tail 無しの calibrations / predictions / evaluation は
  従来と同値であることを test で直接検査した。`allow_abbrev=False` は既存 test が要求する
  「`--tail` を受理しない」を新 option の接頭辞解釈から守るため。
- **軽量版**: 段 2・3 と段 6 の review 子は省いた (設計択一は R1〜R7 で事前固定、正しさ防壁・受理集合に
  触れない)。変異 matrix は省かず、probe (全 SURVIVED 登録で node 収集) → 本走 (期待 node 完全一致) の
  2 段で **negative 10 件すべて KILLED、等価変異 1 件 (`list(x)` → `[*x]`) が期待どおり SURVIVED**。
- 成果物はすべて**非認証**である。trace-disabled の性能測定と、それを入力にする model の再計算であり、
  直列性の検査を通していない。variant 採用の根拠には使えない (規律 2)。
- **submitter の記録欠陥を 1 件見つけた (未修正、scope 外)。** receipt `.submit.jsonl` の `job_id` が
  `Request 978201.nqsv submitted to queue: gen_S.` と qsub の stdout 全文になっている (2026-08-26 の
  receipt も同じ)。ID だけを読む consumer は現在無い。

## 次の一手差分

### 更新

- [T-2266] **P1・測定完了 → 乖離は確定、model 再走のみ残る**: 8 点格子の実測は [T-2320] wave が
  2026-09-07 に完遂した (job 979843 / 979844 / 979845、値は
  `output/insights/2026-09-04_t2266-backoff-static-tail/README.md` §8)。**依頼が求めていた「旧 model の
  指数外挿との乖離」は確定した** — 外挿/実測の比は 999 µs で 0.023〜0.052、150 µs では 0.90〜0.93 で、
  b が伸びるほど外れが開く (`output/insights/2026-09-07_t2266-tail-measurement/README.md` §4.2)。
  **1000 µs は F718 により依然測定不能で、999 は代替であって 6 点目ではない。**
  残るのは 13 点較正での歩行 model 再走 (下記 [T-2313]) と、機序の直接観測 ([T-2265]) である。
  base: fdba875e8f5a6fe2bbd23a91fe9ad854bfdd7cd6f143e2eb09d1af87f5f534e3
- [T-2313] **P2・入力機構は着地、13 点較正の再走が残る**: model 側の `--tail-json` は着地した
  (構造検査、13 点較正、`provenance.tail_inputs`、変異 10/10 KILLED + 等価 1 SURVIVED)。補間規則
  R1〜R7 は結果を見る前に固定済み (同 insight §1)。**13 点較正での再走も 2026-09-07 に完了した**
  (job 980043、所要 76 分)。**R7 の判定は 3 択のうち「変わらない」** — 形状ゲート 4 本すべてが合否を保ち、
  順位統計 (kendall 距離 6 / 10) も同一で、214 件の予測のうち動いたのは 61 件、ゲートが読む
  predicted_mean_tps の変化は 2% 以内だった (同 insight §4.3)。**否定的結論は変わらないが、足場が
  外挿から実測へ移った。** 残るのは、歩行を大 backoff 域に滞在させる条件 (より大きい step、より長い
  duration) での再評価だが、これは事前登録の外なので新しい事前登録が要る。
  base: c3df5e871289c9930bf0495fa2bbcd5c3e541daa820e8a9f7aad0a2dda1e1fe0

### 新規

- {{T:b10-submit-receipt-job-id-raw-stdout}} **P3・新規**: `tools/pegasus/submit_b10_backoff_grid.sh` の
  receipt `.submit.jsonl` が `job_id` に qsub の stdout 全文 (`Request N.nqsv submitted to queue: gen_S.`) を
  書いている。ID だけを取り出す consumer を足す時に、正規表現で ID を抜くか、raw 行を別 field に分ける
  (Codex author)。2026-08-26 と 2026-09-05 の receipt で実測。
