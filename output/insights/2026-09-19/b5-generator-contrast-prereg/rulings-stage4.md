# 段 4 裁定 — B-5 生成器対照の事前登録 (2026-09-19 22:30 JST)

親 = Claude (本 wave manager)。対象 = 段 2 plan (`codex/plan.md`)、段 3 相談 A (`codex/consult-a.md`、正しさレンズ)、
相談 B (`codex/consult-b.md`、事前登録・統計レンズ)。裁定 inbox の再走査: `docs/handoff/` は T-1998 (中断、無関係) のみ、
worklog 末尾は (1685) のまま。wave 開始後の新裁定なし。

## 1. 親 brief の訂正 (段 1 実測の一般化の誤り)

| # | brief の記述 | 訂正 | 根拠 |
|---|---|---|---|
| C1 | 「停止判定は harness が書くが、手動 loop では次巡を投げるかは親が決める」 | **単一 campaign layout で回すなら誤り。** `drive_iteration` は入口で `check_stop` を実行し、停止済みなら `ran=False` で評価しない (`p3_s4_loop.py` `drive_iteration` 冒頭、親が実コードで裏取り)。T-2746 の実運用は評価ごとに fresh tree・fresh layout で iteration=1 から始めるため入口停止は発火しないが、その代わり whiteboard の系列内継承は harness でなく親の射影が担う。**事前登録は「評価ごとに fresh layout、系列状態は親の射影で継承」を LLM arm の運用契約として明示し、系列状態の継承を機械で検査する部品が無いことを「実装が要る」に載せる** | plan「停止」、A5、B「停止」 |
| C2 | 「3 arm の支持集合は構造的に同一」 | **「受理可能な候補集合 S = {1..1000} が 3 arm 共通」へ訂正。** random は S 全点に正の確率、sweep は 28 点、LLM が S 全点へ到達する証拠は無い | plan §2、A5、B7 |
| C3 | 「三すくみは本 hole では発生しない」 | **「必要性を要求しない条件付き比較に限れば三すくみは前提にならない」へ訂正。** 完全列挙可能性は D1409 の解消ではない | B7 |
| C4 | 「1 評価 = 1 job」 | **「単回評価の呼出し単位 = 1 job」へ限定。** job が必ず新規評価を生むとは限らない (T-2746 は投入 2 本・評価 1 本) | A「1 評価 = 1 job」 |
| C5 | 「重複も B を消費」 (暗黙に fresh 計測) | 単一 layout では同一 genome の terminal 結果を WAL から復元する (`_resolve_duplicate`)。fresh layout 運用では発火しない。**事前登録は「重複も fresh に 1 評価、B を消費」を契約とし、単一 layout で回す実装が生じたら復元を無効化する部品が要ると書く** | plan「重複」 |

## 2. 所見の裁定

| 所見 | real/refuted | 採否 | 裁定内容 (事前登録へ反映) |
|---|---|---|---|
| A1 session 成立条件 (must) | real (`pipeline.py` `_run_bench` の `remeasure_until_stable(max_rounds=3)`、`require_all_reps` を親が確認) | 採用 | **session の定義を既存経路に束縛する:** 1 session = 既存 bench 経路 1 回 (5 rep、CV 閾値超なら静定して再測、最大 3 round)。5 rep 完走を要求 (`require_all_reps` 相当)、settle 成立を要求。3 round で不安定なら**品質欠測** (機械故障でも候補起因でもない第 3 の分類、B も A も返さない、fallback に置き換えない)。物理測定回数は論理 session 数の最大 3 倍まで、台帳に別記。現行 loop がこれらの flag を渡すかは束縛されていない → 実装が要る |
| A2 同値 anomaly の波及 (must) | real | 採用 | **値 v について workload w で anomaly が 1 件でも観測されたら (探索・再検証・floor のいずれでも、順序を問わず)、v は w の全 arm・全系列で endpoint 資格を失う。** 先行する certified 記録は歴史事実として残す (規律 7) が資格に使わない。既に score 確定済みの系列に後から発見が及んだ場合は、その系列を stock fallback + (a) 記録へ改め、改訂を Erratum ではなく「結果の訂正」として日付付きで報告する |
| A3 scheduler 中断の分類 (should) | real | 採用 | 機械故障 = 候補の処理開始前の中断、scheduler 記録で裏付く node 喪失・preemption、候補と独立な依存物供給・入出力障害。**候補の実行中に job walltime を超えた打切りは候補起因** (B 消費、score なし)。walltime は本走前の試走で測った最大所要への倍率で決め、全 arm 同一 |
| A4 初回 stock の受渡し (should) | real | 採用 (設計変更) | 探索 job ごとの stock 対測定 (1080 session) は採らない。**系列開始時に stock 1 session** (同機体・同 job) を取り、LLM arm の初期 `current_perf` に渡す (random / sweep には渡すが分岐しない)。job body にこの順序は無い → 実装が要る |
| A5 brief 訂正 (must) | real | 採用 | §1 C1〜C5 |
| B1 共有 stock と符号反転 exact 検定 (must) | real | 採用 | **主解析** = 系列番号で対にした d_r の符号反転 exact 検定 (仮定: block 内で 3 arm を均衡順に走らせた対の帰無下対称性)。**共有 stock による依存は fallback 対にだけ入る**ので、**副解析 = fallback (どちらか一方でも) を含む対を除いた同検定**を事前登録する。同一比較で fallback 対が 2 以上あるときは主解析の exact 性を主張せず、副解析の結果を報告値とし、主副で結論の向きが違えば判定不能 |
| B2 不安定性と判定順 (must) | real | 採用 | 不安定性の操作的定義 = (i) session 水準: 3 round 不安定 → 品質欠測、(ii) endpoint 水準: 5 session の CV が `2 × max(0.03, CV_stock(w))` を超える → その比較は**精度不足で判定不能**。判定順 = 規約不適合 → 欠測・精度不足 (判定不能) → 優越 → 同等 → 残りは判定不能 |
| B3 endpoint CV を等価域へ (should) | real | 採用 (親案へ戻す) | 等価域 δ = ln(1 + max(0.03, CV_stock(w)))。endpoint CV は等価域に入れず B2 の精度 gate に使う。(c) は「精度の保証を伴わない観測差の分類」と明記。baseline が floor 超で上回る場合は「逆向きの記述的差」とし、有意な逆向き優越とは書かない |
| B4 fallback を含む score の意味 (should) | real | 採用 | 各 arm の certified endpoint 数 (12 中) を必ず併記。**両 arm とも certified 系列が 6 未満なら (c) 成立でなく「生成不成立」** (第 4 の結末) として報告 |
| B5 台帳と設計選択の対応 (should) | real | 採用 | 「設計選択 ↔ 見ていた既知結果」の表を §8 冒頭に置く。knowledge は値だけでなく性能・正しさ・LI・旧実行条件を含む WAL 射影と書く。「open-loop」は実行中の性質であり設計者は既知結果を見ている、と分ける |
| B6 Erratum と事後再解析 (should) | real | 採用 | 結果閲覧後の判定規則変更は方向を問わず事後改訂。当初規則の結果を事前登録の結果として報告し、事後改訂の結果は別欄。Erratum 追記前の測定版 SHA を保存し、cohort との対応を記録 |
| B7 brief 訂正 (must) | real | 採用 | §1 C2・C3 |
| 費用 (A/B 共通) | — | 採用 (親の設計変更で縮小) | A4・B3 の裁定により session 数を **1080 (探索) + 108 (系列開始 stock) + 540 (endpoint score、CV も同標本) + 45 (block stock 5 × 9)= 1773 論理 session** に縮める。endpoint 専用 floor 540 は採らない (score 5 session の CV で代替、B3)。「総実行 wall」= job Elapse の総和 (Tier0・stock・verify・bench・retry・再測込み)、queue 待ちと LLM 時間は別欄。管理上限は本走認可時の確認事項 (数値は実測所要の試走後に決め、本書では固定しない) |

## 3. scope 外・裁定パッケージ候補

- 実装 (較正動作点の CLI、B/A 台帳、停止・重複の契約、random 生成器、sweep の hash 順 B 点、系列状態の継承検査、
  exact correctness 経路、解析 consumer) — すべて「実装が要る」として事前登録 §10 に列挙。本 wave では実装しない。
- 本走認可時の確認事項 (plan「ユーザー裁定へ返すべき事項」1〜7 + B の追加) は事前登録 §12 に列挙。**本 wave の文書作成を止める事項ではない。**
- 統計の妥当性・欠測条件は親が閉じた (B の指摘どおりユーザー承認で代替しない)。

## 4. 変異事前登録

実装面差分ゼロ (docs 2 file + insight + spool fragment) → DW-S04 により変異 matrix を免除。受入全走は免除しない。

## 5. plan v2 (親が書く)

`docs/b5-generator-contrast-preregistration.md` を plan の草案を骨子に、§1・§2 の裁定を反映して親が書く。
`docs/README.md` へ 1 bullet。段 6 = 独立 read-only レビュー 1 本 (一次資料との食い違い、D2148 項 11)。
