# 段 1 brief — [T-2849] 5 手法比較基盤の計算なし設計 (2026-09-22、wave dev-wave-t2849-comparison-harness-design)

- 起点: local main `8fd2a2f5c775954d6a32cee019ac7ce276298e4d` (worktree HEAD と一致、開始 gate rc=0)。
- 依頼の逐語: 本 dir `request.md`。一次資料: `output/insights/2026-09-21/vldb-direction/gap-analysis.md` §4 P2。

## 研究前進 (1 行)

VLDB EA&B の中心命題 (探索空間の構造・検証費用が LLM / 非 LLM 探索の有効性をどう決めるか) の主実験 P3 ([T-2850] の費用・成果曲線) を、5 手法が同じ口・同じ初期条件・同じ費用単位で走る基盤の上で取れるようにする。完了判定 = 実装 wave が本設計だけから実装単位を切り出せる (口の型・揃える項目・費用単位・B-5 再利用範囲・BO / 進化の出所・MOCC の差し込み口が一意に決まっている)。

## scope

- 成果物: insight `output/insights/2026-09-22/t2849-comparison-harness-design/README.md` (+ `verbatim/`)、worklog fragment ([T-2849] を `更新`)、decisions fragment 1 件。
- 実装・投入・計算はしない。gate・検査・台帳・一般化の追加は scope 外 (依頼逐語)。B-5 事前登録 doc と `b5_generator_contrast.py` は編集しない (並走 [T-2797] wave が所有)。sort (79 値)・trigger (32 点)・flag genome (8 点) の空間への展開は scope 外。
- 確定済みユーザー裁定: D2212 (VLDB 方針、項 4 = 2 node 時間以上は事前確認)、第 31 回 (2026-09-22) 項 1 (開発検査も同じ線)・項 6 (H100 の open-weight LLM は今は採らない)・項 8 (T-2858 push は人間手番)。D2200 項 1 (B-5 段階認可)、D2214 (silo-function-policy と比較 A / B の分離、BO は差分分析 P2 へ送る)、D2215〜D2217 (Tier0・LLM arm 親運用・共通 walltime)。
- 不変条件: 規律 2・3 (anomaly 即 reject、毎回検証、構造化フィードバック)、規律 1 (性能は trace-disabled の別 build・別 run)、D39 決定 7 (harness は LLM を spawn しない)、D1067 (主張は条件付き優越に留める)、D2214 の firewall (偵察の順位・勝ちコードを LLM に渡さない)。
- 条件 08/09/10 (freeze・凍結 bytes) は非成立: 凍結成果物 (B-5 prereg、`known_axes_freeze.json`) は参照だけで bytes を変えない。条件 13 (gate 新設) も非成立。
- 受入・実測環境: 受入全走は Pegasus (`tools/dev_wave_wait.py acceptance`)、1 回 ≈ 0.25 node 時間 (2 node 時間の線の下)。

## 軽量版の段構成

設計択一が割れるので独立の敵対検証子を残す: 段 2 は省き (docs-only、本 brief の骨子 `skeleton.md` が plan)、段 3 相談 2 本 (A = 比較の公平性・情報の漏れ・統計単位 / B = 実効性と過剰・削除・再利用の実在)、段 6 read-only review 1 本 (事実の再抽出 + 設計択一) と焦点再レビュー。実装面の差分ゼロなので変異 matrix は免除 (DW-S04)、受入全走は行う。

## 親の暫定裁定 (攻撃対象)

- (P1) 口 = 生成器 (ask / tell。空間定義・seed・自系列の観測履歴だけの関数) → 既存の閉じた proposal 文書 (B-5 の `machine_proposal_document` 型) → `p3_s4_loop --run-iteration` (Tier0 → `run_campaign` / `pipeline.evaluate`) → 観測記録 (WAL / sidecar から 1 つの producer で作る) → tell。LLM は親運用 (D2216) で proposal file を作る側に立つ。
- (P2) 空間は 3 つに限る: S1 = silo の backoff 値 1..1000 (実在)、S2 = MOCC の backoff 値 (T-2858 の pin 前進後)、S3 = D2214 の policy IR (T-2857 の C 段以後)。
- (P3) S3 で sweep と BO は IR の固定 template の座標 (部分集合) だけを動く。支持集合の違いは B-5 §2 と同じく明示して許す。random・進化・LLM×IR は IR 全体。
- (P4) BO = GP-EI (Jones ら 1998 の EGO) の標準ライブラリだけでの再実装、進化 = 型を保つ subtree 変異・交叉の GP (Koza 1992 / Montana 1995 の型付き GP) の再実装。numpy (login で 2.2.6 のみ実在) にも依存しない。既存 library の移植・呼び出しはしない。
- (P5) 観測: 全 arm へ同じ観測記録を渡す。非 LLM 手法は fitness と有効性の分類だけを使うと定義で宣言し、LLM 射影 (whiteboard 5 field・critic 診断) は同じ記録から作る。K2 の知識入力は主比較に入れない。
- (P6) stock = B-5 §5.4 の系列開始 stock + block stock。`p2_2_flag_opt` (`BACK_OFF=0`、空間の外) と調整済み静的 backoff は exact reference として block ごとに測り、全 arm へ参照水準として渡す (「既知結果を条件とする探索」と明記)。空間内の初期候補は空間ごとに固定列を決め、全系列の最初の k 評価として共通に測り、探索予算 B の外に置く (D2214 §6 の「初期 3 + 探索 8」に合わせる)。
- (P7) 費用単位: A = 生成器が候補 1 件を返した回数、B = pipeline 投入数、重複 (同一 identity の再提案) は A・B を消費して fresh に測る、Tier0 不通過は A だけ、pipeline 内の build 失敗・anomaly は B。物理費用は slot ごとの job Elapse と LLM wall を別欄で全件記録し、評価数で揃える比較と費用で揃える比較の両方を [T-2850] が切れるようにする。
- (P8) B-5 の再利用は台帳 schema・slot 分類・A/B と retry 規則・Tier0・endpoint と block stock・S1 の random / sweep 生成器まで。B-5 cohort と事前登録・判定規則は変えず、新しい比較と標本を混ぜない。
- (P9) MOCC の差し込み口は前提 (pin 前進・X/P の certified・動作点の較正・MOCC の既知最良を 8 genome の全列挙で定める) と、S2 の空間定義だけを書く。温度述語 hole は proof-only (D2134 項 9) なので使わない。
- (P10) 実装単位は後続 wave 用に列挙するだけ。新しい gate・検査・台帳は足さない。
