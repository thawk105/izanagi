---
schema: izanagi-spool-v1
ledger: worklog
authored: 2026-09-23
wave: dev-wave-t2854-mocc-v3-emitter
seq: 1
title: [T-2854] TPC-C 段 1 の単位 3 — mocc の trace v3 emitter を、候補 C 68106660 の上に C1 の helper を載せ直した CCBench の local branch izanagi-tpcc-v3-mocc (C1' 6aa7a58f → C3 53f6b097) に置き、計算ノード 1 走で v3 の構造・witness・内容、YCSB v2 の certified、TRACE=0 の前処理と逆アセンブルの一致、変異 6 件を確かめた (insight + docs、push と pin 前進なし、branch worktree-dev-wave-t2854-mocc-v3-emitter)
---

## 本文

- **依頼:** `/dev-wave [T-2854] の残り・単位 3 (P1)` (逐語 = `output/insights/2026-09-23/t2854-mocc-v3-emitter/verbatim/request.md`)。着手時 local main `cadaf3805`、開始 gate rc=0。
- **段構成:** 軽量版。段 2・3 は省いた (silo の C2 と同じ形の移植で設計択一が割れない)。正しさ信号の producer に触るので段 6 の敵対レビュー 2 本 (正しさ境界と規律 1 / 過剰・削除) は残し、どちらも GO・must-fix 0。should 2 件は段 4 裁定文の訂正 (C0 で取り出す checkout は C と C3 の 2 本) と計算見積りの注記で、fix 子は起動していない。
- **設計判断:** {{D:tpcc-v3-producer-mocc}} (置き場・切替・規律 1 の比較基点 C)。
- **計算:** 計算ノード 1 本 (request 19053.nqsv、Elapse 206 秒、待ち行列 18 分)。1 タスク合計 2 node 時間の確認線に届かない (受入を含めても約 0.3 node 時間の見込み)。
- **並走:** 同じ T-2854 の残り (1) (存在履歴の verifier 実装) を別 wave が同時に進めている (担当分割済みで譲り合いの対象ではない)。相手からの連絡で、worklog の [T-2854] 項目は「後に land する側が受入投入の直前に local main で相手の着地を確かめ、着地済みなら両成果を統合した `更新` を 1 つ置く」取り決めにした。相手の依頼に応じ、存在履歴の契約 (初期ロードの版が (1,0)、insert は既存 key で失敗) が mocc でも静的に成り立つことを C3 の source で確かめた (insight §6、実 trace での確認はしていない)。
- **観測 (未調査):** TPC-C の stdout に `insert order failed` が 311 行 (commit 35,572、abort 2,844)。同条件の silo (前 wave) でも 434 行で、mocc 固有ではない。
- **Codex 子:** 4 本 (author 2・review 2)、model call 計 53、wall 合計 1,154 秒、全子 gpt-6-astra / medium。

## 次の一手差分

### 更新

- [T-2854] **P1・段 1 の一部完了 (D2212 項 2、D2219 項 2) → 残り = 設計 §3.3 の存在履歴、単位 5・11**: TPC-C 段 1 (NewOrder / Payment、CCBench 既定比 45% + 43%、
  点読み・点書き・insert のみで `tx.scan` を使わない) の合成候補を直列化可能性で認定できるようにする。設計 = `output/insights/2026-09-21/tpcc-trace-certification-design/README.md`
  (§7.1 の実装単位、§8 の親決定)。実装は Codex author、正しさゲートは不変、trace は compile 時に除去する (規律 1)。
  **済:** 単位 1・2 (CCBench 側、D2225、`output/insights/2026-09-22/t2854-tpcc-ccbench-v3/README.md`) = CCBench の local branch
  `izanagi-tpcc-v3-trace` に pin e9e477ca の子として C1 `56b5cb709628c9cac98e4e18ff676defc77a9117` (trace.hh の v3 helper・tpcc.hh の取引種別 context と
  trace build 限定の計数) と C2 `a6f2c7410d58ad140a62b11cc1beab29bfcd191b` (silo の v3 emitter)。計算ノード 1 走で v3 の構造・witness・内容、YCSB v2 の certified、
  TRACE=0 の前処理と逆アセンブルの一致、変異 6 件を確認。この branch は今は push しない (D2227 項 7、C1 / C2 は job dir の自己完結 bundle で保全済み)。
  単位 11 で C の上へ乗せ直し、header 差分の受理方法と結合確認を揃えた候補を人間の push 判断へ渡す (D16)。単位 4 (verifier 側、D2224、entry 1828、
  `output/insights/2026-09-22/t2854-tpcc-verifier-v3/README.md`) = v3 を (表, key) で読み cycle に表と取引種別を載せる。v3 の run は存在履歴を検査するまで
  認定しない印 `Integrity.v3_existence_unverified` を立てる。単位 3 (mocc 側、{{D:tpcc-v3-producer-mocc}}、`output/insights/2026-09-23/t2854-mocc-v3-emitter/README.md`) =
  CCBench の local branch `izanagi-tpcc-v3-mocc` に [T-2844] の候補 C `68106660686232781bca3be792a750d3e19d7a8a` の子として C1' `6aa7a58fccff9efa218067d1b7ce83026a75357d`
  (C1 の cherry-pick、header の blob は C1 と同一) と C3 `53f6b09757331ac7200f3f6bb5d526a676480fe3` (mocc の v3 emitter)。計算ノード 1 走で C を基点に同じ形の確認
  (v3 の構造・witness・内容、YCSB v2 の certified、TRACE=0 の前処理と逆アセンブルの一致、変異 6 件) を満たした。この branch も今は push しない
  (bundle で保全、単位 11 の候補の材料)。
  **残り:** (1) 設計 §3.3 の存在履歴 (初期キー集合・insert 前の不存在・delete 版の読みの不整合) の verifier 実装と上の印の撤去。v3 を認定に使う前提で、
  §7.1 の単位表に担当が無い (単位 4 の insight §6)。mocc でも存在の契約 (初期ロードの版が (1,0)、insert は既存 key で失敗) が静的に成り立つことは単位 3 の insight §6。
  (2) 単位 5: 旧 result_to_dict・CLI・pipeline・受領証 digest への v3 の表・取引種別の配線
  (`core.result_to_dict_v3`)、`orchestrator/campaign/pipeline.py` の allowlist の拡張 (tpcc + v3 + 57:43 の flag)、witness 試験と段 1 の正例・負例。
  単位 1・2 の実 trace は `/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2854-tpcc-ccbench-v3/evidence/traces-2/`、単位 3 の実 trace は
  `/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2854-mocc-v3-emitter/evidence/traces-1/` に zstd で保持。(3) 単位 11: pin 前進。C 単独の pin 前進は [T-2858] で承認済み (D2227 項 1) なので、
  C1' / C2 / C3 は C の上へ 1 系列に並べた別候補として、結合後の証拠を揃えて改めて承認を求める。D297 の検査器は header の差分を拒否するので、header を含む候補の受理方法を先に決める
  (単位 1・2 の insight §8)。受理方法の方式案は AI 手番だが、検査器の拡張・代替証拠での受理は委任されていない — D297 / D2207 / D2225 決定 6 の変更を要する案になれば、
  不足する保証と必要性を示して改めて諮る。
  本項で TPC-C の corpus が入るとき (pipeline の allowlist が tpcc を受理した時点) に見送り台帳 [T-156] (selector-8b descriptor への set-size 条件) の発火条件
  「TPC-C 級 workload corpus を採るとき」が成立するので、同項を再評価し、既裁定の「着手前に workload 別の set-size 分布を測る」順序を確認する。
  設計 insight §9 の CCBench 所見 (D2219 項 7): 段 1 で観測できたのは実行時の OrderLine 番号が 0 始まりであることだけ。寿命と範囲読みの所見は [T-2855]、
  si の所見は si を走らせる wave の担当。計算: 検証走・計測・開発の検査を含め 1 タスクの job 合計が 2 node 時間以上になる投入は、見積りを示してユーザー確認後に
  投入する (D2212 項 4、D2219 項 1)。一次資料 `output/insights/2026-09-21/vldb-direction/gap-analysis.md` §10、roadmap §3.1。
  base: a8db5033e85c6f88a769008ac79d514c8a19e670aecfe8a2e5cb1f32d8306c5d
