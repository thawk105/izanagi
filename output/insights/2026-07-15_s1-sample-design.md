# S-1 サンプル設計 4 点の確定 — 3 レンズ敵対レビューと裁定 (2026-07-15)

- 種別: 事前登録追記の裁定台帳 (phase3.md 段 6 S-1 closure checklist「サンプル設計 4 点の
  数値を事前登録へ追記し、独立レビューする」の履行記録)
- 状態: **確定案 v2 はユーザー承認待ち** (検定単位の実質改訂 1 点を含むため D44 作法の
  AI 単独改訂範囲外)。承認後に `docs/phase3-main-experiment.md` 末尾へ追記する
  - **2026-07-15 訂正:** ユーザー承認済み・発効。§4 全文を同日
    `docs/phase3-main-experiment.md` 末尾へ逐語追記し、承認記録を付した (履歴として
    上記の承認待ち表記は保持)
- レビュー体制: codex `gpt-5.6-sol` (reasoning high)・独立コンテキスト 3 本 (統計 /
  事前登録作法 / fails-closed 実効性)。verdict = reject / adopt-with-conditions /
  adopt-with-conditions。v1 の must-fix 20 件はすべて real と裁定し v2 へ反映 (refuted 0)
- 委譲情報: 親 (Fable5) が v1 設計とレンズ設計、codex がレビュー、親が裁定と v2 起草

## 1. v1 からの主要な変更 (レビューが正した誤り)

1. **主統計量の変更 (統計 must-fix 2、v1 の数理的誤り):** v1 は「median 差の exact
   permutation で完全分離時 min-p = 1/C(16,8) = 1/12,870」としたが、median は中央 2 値に
   しか依存せず端の値の入れ替えで同値になるため、完全分離でも極端分割は一意でない (min-p は
   1/12,870 より大きく、N=5 では Holm 初段 α=0.0125 を通らない)。v2 は主統計量を**層別
   rank-sum** (確率優越 A と単調同値、完全分離の極端分割が一意) に変更し、median 差は効果量
   表示へ降格した。
2. **層別化 (統計 must-fix 1):** 2 campaign ブロック分割と無層化 permutation は交換可能性と
   矛盾する。v2 は campaign 内割付を保存する層別 exact permutation (C(8,4)² = 4,900 分割、
   完全分離時 p ≈ 2.0×10⁻⁴) + 事前固定 seed の均衡ランダム化 schedule に変更した。
3. **選択推論の遮断 (統計 must-fix 4 / prereg must-fix 3):** スクリーニング通過後に同一
   データを pool して検定する v1 設計は選択推論を許す。v2 は全比較・全 N の無条件完走 +
   「gate 不通過なら p\* = 1」の連言規則に変更し、Holm への投入物を機械定義した。「独立な
   検証相」の呼称も撤回 (ブロック化した単一登録追試 + gate 連言と記す)。
4. **検定単位の扱い (prereg must-fix 1):** 「系列 → 独立セッション」は明確化でなく検定を
   可能にする方向の実質改訂であり、v2 はユーザー承認を発効条件化し承認まで実走禁止とした。
5. **検証相の繰延べ撤回 (prereg must-fix 4 / fails-closed must-fix 1):** N_verify =
   8/workload・extime 校正規則 (1 verify ≤ 10 分に収まる最大値、下限 3s)・総 ≤ 4h・
   「extime は下げてよいが N_verify は削らない」を拘束値として確定した。
6. **1-εⁿ 主張の撤回 (fails-closed must-fix 7):** ε 未定義・seed identity 非記録・trace は
   verify 後に削除される (pipeline.evaluate の finally) ため、形式的信頼度は主張せず
   「独立反復 24 verify 全て anomaly ゼロ」の操作的事実として報告する。
7. **fails-closed の consumer 実在化 (fails-closed must-fix 全般):** freeze 先行 commit +
   起動時 hash 照合 + positive control、certified 照合 hard gate + 負例テスト、schedule
   凍結 + ledger 完全一致、時間計上規則 + 起動前残予算 gate、機械故障 retry の閉じた列挙、
   判定不能発火条件の機械化 — を「S-1 計測開始 gate」5 条件として登録した。
8. **HARKing 台帳 (prereg must-fix 2):** 2026-07-15 時点の既知結果 (D50 +61〜99%、fresh
   CV、wired 3.0%、既知軸過去実測) を閲覧済みで数値確定した旨を冒頭に開示した。

## 2. 不採用にした proposed_fix (代替対応)

- prereg must-fix 3 の「既存 D50 偵察をスクリーニングとして固定」案: D50 には既知軸 vs
  系側の比較が存在しない (gate on/off のみ) ため適用不能。統計レンズの p\*=1 連言案で対応。
- 統計レンズの具体数値「median 差の完全分離 tail = 20/12,870」は独立検算していない
  (統計量変更により moot)。問題の構造 (中央 2 値非依存による同値 tail) は正しいと裁定。

## 3. 残る限定・次段への引き渡し

- v2 の「S-1 計測開始 gate」5 条件: (1) ユーザー承認 (検定単位)、(2) freeze 生成 + commit、
  (3) driver + positive control、(4) 統計実装 + テストベクトル commit、(5) 検証相校正。
  (2)〜(4) は S-1 直接比較 driver タスク (checklist 次項) の完了条件に組み込む。
- 検証相の extime 確定値は校正後に事前登録本節へ日付付き追記する (校正は trace-enabled
  build の verify 所要実測のみで、性能計測窓を使わない)。

## 4. 確定案 v2 全文 (承認後に docs/phase3-main-experiment.md 末尾へ追記する文面)

---
### 2026-07-15 着手時確定 — S-1 サンプル設計 4 点 (性能分布比較の n・検定単位・検定力・総予算)

統計計画「サンプル設計 (実行前に数値を確定して本節に追記)」4 点の履行。2026-07-13 節と同じ
二層書き分け (層 1 = 認可ブランクの充足、層 2 = 実走に必要な付帯規則の確定)。3 レンズ敵対
レビュー (統計 / 事前登録作法 / fails-closed 実効性、独立コンテキスト = codex gpt-5.6-sol
reasoning high) の must-fix 反映済み。裁定台帳 =
`output/insights/2026-07-15_s1-sample-design.md` (レビュー全文 JSON 同梱、同一 commit)。

**改訂の類型 (正直な開示):** 本追記の大半は認可ブランク (「実行前に数値を確定」) の充足と
fails-closed 方向の付帯規則だが、**1 点だけ実質改訂を含む** — 統計計画本文の「検定単位 =
系列」の S-1 への適用を「独立セッション」に確定する箇所 (層 1 (ii))。これは検定を可能にする
方向 (n 増) の変更であり D44 作法 (制約方向のみ AI 改訂可) の範囲外のため、**ユーザー承認を
発効条件とする。承認までは S-1 実走禁止** (未承認のまま計測に入ったら protocol 違反として
当該計測を無効とする)。

**2026-07-15 改訂時点の既知結果台帳 (HARKing 境界):** 本節の数値は次を閲覧済みの状態で確定
した — D50 偵察 (gate on/off +61〜99%、3 workload cross-run 再現)、fresh between-run CV
実測 (silo stock baseline: write-heavy 0.67% / balanced 1.07% / read-heavy 0.11%)、wired
保守 floor 3.0% (D19)、P2-2 / BACKOFF_FIXED / sort 各既知軸の過去実測、s8a F 段 iteration
1〜2。したがって S-1 は結果既知の登録追試 (confirmatory と呼ばない)・対象軸 n=1 という
限定は不変であり、以下の N・検定方向・統計量・gate 規則はこれらを見た後の固定である。

**層 1 — 認可ブランクの充足 (4 点):**

- **(i) アームあたり系列数と 1 系列の試行予算:** アーム = 比較セル (構成 × workload)。
  セル構成 = 3 workload (rr50/rr5/rr95) × 6 構成 {系側 best gate (balanced/read-heavy =
  g_rl、write-heavy = g_rt に事前固定), ident_all (S-1b 対照), P2-2 フラグ最適,
  BACKOFF_FIXED grid 最良, sort 全列挙最良 (read-heavy は sk_ad 事前固定 — §2.1 既定),
  共通 stock} = **18 セル**。検定標本 = **N = 8 独立セッション/セル** (時間分離した 2
  campaign ブロック × 4、計 144 セッション)。これと**別に** floor 推定標本 = N_floor = 8
  独立セッション/セル (先行 floor campaign、計 144 セッション。検定標本と floor gate 入力の
  分離 — 同一標本から gate と検定を両方導出しない)。1 セッション = 確定動作点 (RECORDS=1M /
  THREADS=48 / EXTIME=3s / REPS=5) の measure_point 1 回、観測値 = セッション reps median。
  sort read-heavy の欠測補充 (sk_ad + stock) と対象別 between-run floor 再実測は上記に
  **包含** (別枠計上しない — checklist 該当 2 項はこの campaign 群で閉じる)。
- **(ii) 検定単位 = 独立セッション (S-1 限定・ユーザー承認待ち):** 統計計画本文の「検定単位
  = 系列 (P2-5 と同じ。試行は path-dependent で独立でない)」は LLM 探索実験の規定であり、
  探索実験を復活させる場合はそのまま生きる。D52 で登録追試に再構成された S-1 は固定構成の
  再計測であり path-dependence が存在しないため、S-1 に限り検定単位を独立セッションとする。
  セッション間の独立は**操作的仮定** (プロセス分離 + RNG の run ごと自己シード —
  `external/ccbench/include/random.hh` Xoroshiro128Plus は std::random_device で初期化され
  ycsb に CLI seed はない) であり、時間ドリフト等の系列相関は除去されない — その対処は
  層別化・ランダム化 schedule (層 2) が担い、独立性の証明とは主張しない。within-run reps は
  セッション内相関のため観測単位にしない (median に縮約)。
- **(iii) 検定と検定力:** 検定 = **層別 exact permutation** (campaign ブロック内の割付数を
  保存する全列挙 = C(8,4)² = 4,900 分割、片側)、**主統計量 = 層別 rank-sum** (層内 rank-sum
  の和、van Elteren 型。確率優越 A と単調同値)。tie は tail 包含の保守則 (P(T ≥ T_obs))。
  中央値差・確率優越 A・セル CV は効果量として併記 (判定には使わない)。完全分離時の達成 p =
  1/4,900 ≈ 2.0×10⁻⁴ < Holm 初段 α = 0.0125 (族 4 = S-1a/S-1b/S-2/S-3、2026-07-12 追記)。
  N=8 の根拠 = **p 値解像度の確保** (完全分離時に Holm 全段を通る + 少数の順位交差への耐性)
  と between_run_floor.py の独立 8 セッション前例。**prospective power は未保証と明記する**
  (対象セル、特に high-abort 構成の分散は floor campaign まで未実測のため)。参考の感度計算
  (既知結果条件付き・N 選定の根拠にしない): 中央値差 > 3.0% かつ CV ≈ 1.1% (stock fresh 実測)
  なら標準化差 d ≥ 2.7 で事実上完全分離、S-1b は D50 実測 +61〜99% が floor の 20 倍超。
  事後の「判別力再評価」は行わない — N=8 完走時は常に p*・効果量・CV を報告し、判定不能の
  発火は層 2 の機械条件のみ。
- **(iv) 実計測の総予算上限 = 合計 12 時間 (宣言値、拘束):** 時間計上 = S-1 の全 campaign
  プロセスの monotonic wall time を**成功・失敗・timeout・機械故障 retry・build・verify・
  bench・floor campaign・検証相校正・検証相のすべて込み**で台帳に累積する。driver は各
  セッション起動前に残予算を検査し、不足なら起動せず、その時点で未完走の**全比較を対称に**
  判定不能へ倒す (観測値を見た選択的な打ち切りをしない)。内訳概算 (拘束は総額のみ): floor
  campaign ≈ 1.5h、検定 campaign ≈ 1.5h、variant build + 開発相 verify (18 構成) ≈ 1h、
  検証相校正 ≈ 0.5h、検証相 ≤ 4h、機械故障 retry 予備 ≈ 2h。予備枠の使途は機械故障 retry
  のみ (層 2 の閉じた列挙)、枠の目的間移転は禁止。
- **(iv 付属) 検証相の拘束数値 (繰延べの撤回):** 対象 = headline 最終候補 = 系側 gate 構成
  のみ (g_rl / g_rt、§7 既定)。**N_verify = 8 独立反復/workload** (計 24 verify)。long
  extime = 校正で確定: trace-enabled build で extime {3, 6, 10}s 各 1 回の verify 所要を
  実測し、**1 verify ≤ 10 分に収まる最大値**を採る (下限 3s = S2 前例)。確定値は本節へ
  日付付き追記。総検証相予算 ≤ 4h、超過見込み時は extime を下げ **N_verify は削らない**
  (信頼度の指数を観測後に弱める自由度を残さない)。判定 = 24 verify 全て anomaly ゼロで
  pass、1 件でも anomaly → 当該 variant は失格 (規律 2)。**形式的信頼度 1-εⁿ は主張しない**
  (ε の定義・seed identity の記録・trace の永続保全 (現行 pipeline は verify 後に trace を
  削除する) のいずれも無いため) — 「独立反復 n=8 × 3 workload で anomaly ゼロ」という操作的
  事実として報告する。roadmap §3.2 の 1-εⁿ 表現は本 S-1 報告では限定表現に置換する。

**層 2 — 付帯規則の確定 (いずれも fails-closed / 機械判定可能な形で):**

- **スクリーニングの gate 連言化 (選択推論の遮断):** 全 18 セル・全 N=8 を**無条件に完走**
  する (途中結果による比較の除外・差し替え・停止をしない)。比較ごとに
  p\* = p_perm (下記 gate を全通過した場合) / p\* = 1 (いずれかの gate 不通過)。
  gate = {(1) 中央値差の点推定 > floor_cmp、(2) 2 campaign ブロック間で差の方向が一致
  (cross-run 再現)}。**S-1a = max over 9 比較 (3 workload × 3 既知軸基準点) の p\*、
  S-1b = max over 3 比較 (workload 別 gate on/off) の p\*** を各 1 本 Holm 族 4 へ投入
  (intersection-union、α inflation なし)。gate 不通過はそのまま (c) 系レベル失敗条件の
  評価に入る。本設計は「独立な検証相」を持たない — ブロック化した単一登録追試 + gate 連言
  であり、その旨を報告に明記する (§2.1 の「スクリーニング → 検証相」の二段階は本 gate 連言
  として実装される、の読み替えを含む)。
- **floor_cmp の定義 (純関数):** floor_cmp = max(floor campaign での当該比較両側セルの
  between-session CV, 3.0%)。floor campaign 標本のみから計算し、検定標本を使わない。
  near_floor 帯 (floor_cmp〜1.5×floor_cmp) の cross-run 裏取りは gate (2) が担う。欠測・
  非有限値・入力 hash 不一致は判定不能へ倒す。
- **比較点の事前固定と freeze (改竄検出込み):** 系側 = D50 の workload 別勝ち gate に事前
  固定 (再計測での構成再選択をしない)。既知軸側 = 過去実測 argmax 構成に事前固定。
  **machine-readable freeze (workload × 構成ごとの canonical genome/構成・選定元 artifact
  のパスと hash・argmax/tie-break 規則・CCBENCH_COMMIT pin・生成時 HEAD) を S-1/floor 計測
  開始前に生成・commit し、driver は毎起動時に freeze の存在と hash を照合、不在・不一致は
  起動拒否** (positive control: 改変 freeze で起動拒否することをテストで確認)。freeze には
  workload ごとの {gate_on, ident_all} 対応表と「gate 述語以外の構成が同一」の機械 diff
  検査を含める (S-1b が別構成差に化ける経路の遮断)。再計測での順位入れ替わりは観測として
  報告するが基準点は動かさない (§2.1 既定)。
- **certified gate の consumer 登録:** 性能標本はすべて pipeline.evaluate 経由 (COMMIT を
  書く唯一の経路) で取得し、S-1 report は各標本について certified evidence (variant_id・
  src_token・verify 構成) との照合を hard gate とする。measure_point 直接呼び出しによる
  標本投入は driver が拒否し、負例テスト (certified を欠く標本が report 生成を fail させる)
  を実装完了条件に含める (規律 2 の consumer 実在化)。
- **schedule の凍結と実行照合:** campaign × 周回 × セルの実行順は事前固定 seed の均衡
  ランダム化で生成し、schedule 本体の hash を freeze と同時に commit。実行時は event
  ledger (WAL) と schedule の完全一致 (重複・欠落・順序逸脱なし) を report 生成の hard gate
  とする。逸脱 = 当該 campaign を判定不能 (schedule mutation の positive control を実装
  完了条件に含める)。時間分離の最小条件: campaign ブロック間は別プロセス起動 + 開始時刻を
  ledger に記録 (定量閾値は置かない — ブロック間差は層別化が吸収し、ブロック efect の観測
  値は報告に併記)。
- **機械故障 retry の閉じた列挙:** retry を許すのは (a) プロセス異常終了 (非ゼロ exit /
  signal)、(b) build 失敗、(c) measure_point の例外、のみ。retry ≤ 2/セッション、判定根拠を
  provenance 記録。観測値の内容 (差が小さい等) を理由とする再測は禁止。retry 上限超過で
  当該セル n 未達 → 当該セルを含む全比較を判定不能。
- **「seed×N」の操作的定義:** ycsb は CLI seed を持たず RNG は run ごとに自己シードする —
  検証相・性能計測とも「seed×N」は**独立 N 反復**を意味し、決定論的 seed 固定は導入しない
  (CCBench 改変 (D16) を要するため)。独立性は操作的仮定 (層 1 (ii) と同じ限定)。
- **統計実装の凍結 (S-1 計測開始の前提条件):** 層別 exact permutation・層別 rank-sum・tie
  規則・p\* 純関数の実装は、数式・テストベクトル (完全分離 → 1/4,900、既知の順位交差
  パターン数例、tie ケース) とともに S-1 計測開始前に commit し、実装ファイルの hash を
  freeze に含める。
- **判定不能の発火条件 (機械化・三値判定):** (1) retry 上限超過による n 未達、(2) 総予算
  12h 超過 (起動前検査で発火)、(3) freeze / schedule ledger / certified 照合の失敗、
  (4) floor_cmp 入力の欠測。いずれも成立/不成立に倒さずそのまま報告する。

**S-1 計測開始 gate (すべて成立するまで実走禁止):** (1) 本節のユーザー承認 (検定単位)、
(2) freeze 生成 + commit、(3) driver の schedule/ledger/certified/時間台帳/判定純関数と
positive control テストの完備、(4) 統計実装 + テストベクトルの commit、(5) 検証相校正の
完了と extime 確定値の本節追記。

---

## 5. レビュー全文 (JSON、逐語)

### 5.1 統計レンズ (verdict: reject)

```json
{"lens":"統計","must_fix":[{"claim":"2 campaign・interleave を採用しながら全 8/8 を無層化 permutation する設計は、必要な交換可能性を満たしていない。","evidence":"`search_baselines.py` の exact 検定は pooled 標本の全分割が等確率という交換可能性を明示的に仮定する。一方ドラフトは時間分離した campaign を設け、`between_run_floor.py` も温度・周波数・時間窓ドリフトを認めている。OS entropy による RNG 初期化はワークロード乱数を変えるだけで、同一機の熱・周波数・背景負荷による系列相関や campaign 効果を除去しない。さらに interleave 順がランダム化されておらず、固定順なら構成と時刻が交絡する。","proposed_fix":"各周回のセル順を事前固定 seed でランダム化または counterbalance し、検定は campaign 内の割付数を保存する層別 permutation（各 campaign 4/4 なら C(8,4)^2）に変更する。より細かく周回をブロックとするなら、各周回内のラベル交換に限定する。OS entropy を独立性の証明とは書かない。"},{"claim":"median 差を統計量とする場合の最小可能 p と N 下限の計算が誤っている。","evidence":"C(16,8)=12,870 自体は正しいが、median 差は完全分離でも極端分割が一意でない。値を連続な順位 1〜16 として全列挙すると、上位 8 対下位 8 の片側 tail は20分割あり p=20/12,870≈0.001554で、1/12,870ではない。同様に N=4 は2/70≈0.02857、N=5 は6/252≈0.02381であり、N=5はHolm初段0.0125を充足しない。N=6で6/924≈0.00649となる。throughput の tie はtailをさらに増やし得る。","proposed_fix":"median 差を維持するなら、選定した層別設計の下で達成可能 p を全列挙し、同値を `>= observed` に含める保守的 tie 規則と N 根拠を再登録する。代案は確率優越 A／順位和を検定統計量にしてmedian差を効果量表示へ降格することだが、その場合も層別 permutation と tie 規則を固定する。"},{"claim":"d≥2.7・検定力≈1.0という概算は、登録した endpoint・分散・IUT のいずれにも対応していない。","evidence":"3.0%/1.07%は約2.80だが、1.07%は stock silo のfresh CVであり、両セル、とくにhigh-abort variantの共通SDではない。ドラフト自身が実測CV>3%を許しており、その場合floor直上の標準化差は概ね1程度まで下がる。さらにdによる正規近似は平均差系の近似で、登録統計量であるmedian差 exact permutationのpowerではない。S-1aの成功確率は9比較すべてが通るIUTの同時powerであり、単一比較のpowerではない。スクリーニング通過後の観測差に条件付けたpowerはNを事前正当化するprospective powerにならない。","proposed_fix":"対象セルの分散・分布・効果差を明示した生成モデルまたは保守的シナリオを固定し、実際に採用する層別 exact 検定、floor gate、tie、S-1aの9比較IUTまで含めてMonte Carloまたは全列挙でpowerを再計算する。根拠が置けないなら「N=8はp値解像度の確保であり、検定力は未保証」と明記し、検定力≈1.0を削除する。S-1bは結果既知pilotに基づく別感度解析として分離する。"},{"claim":"screening後に同じcampaign-1を含む全8件で検定する規則が、第一種過誤制御上の合成判定として定義されていない。","evidence":"`§2.1` は「スクリーニング→検証相」を定めるが、ドラフトではcampaign-1でscreenし、campaign-1/2の方向一致を確認したうえで両方をpoolするため、独立な検証標本ではない。再利用自体は、固定された検定の棄却事象に追加gateを連言するだけなら第一種過誤を増やさないが、通過比較だけ検定・報告する、失敗比較をIUTから落とす、構成やNを差し替える余地が残ると選択推論になる。現文はHolmへ何を投入するかまで閉じていない。","proposed_fix":"全比較・全Nを無条件に完走し、各componentについて `p*=p_perm` はfloor・方向一致の全gate通過時のみ、それ以外は `p*=1` と機械定義する。S-1aは9本のp*のmax、S-1bは3本のp*のmaxをHolm族へ投入し、screen失敗を比較の除外や差し替えに使わない。campaign-1を再利用する以上「独立検証相」とは称さず、ブロック化した単一登録追試の追加gateと記す。"},{"claim":"floorがどの標本からどう算出されるか未確定で、データ依存gateと検定の関係が再現不能である。","evidence":"原統計計画は比較対象のプロトコル／contention域ごとのfloor再実測を要求するが、ドラフトは「両側セルの実測between-CV」と「対象別floor再実測」を併記し、campaign-1の4件、全8件、別calibrationのどれを使うか不明である。N=4または8のCVは不安定で、同じ性能標本から算出するならscreen閾値も確率変数になる。これはp値を直接無効化しない追加連言にできるが、power計算と判定規則へ組み込まれていない。","proposed_fix":"floor用データを性能検定標本から分離してセル／workload別に事前計測し、推定式・必要n・欠測時の判定不能を固定する。性能標本のCVも保守gateへ使うなら、使用範囲をcampaign-1か全8件か一意に定め、`max(独立calibration floor, 3.0%, 規定したセルCV)` を追加連言として扱い、上記p*=1規則とpower評価へ組み込む。"}],"should_fix":[{"claim":"S-1bのident_all対照が「同一backoff条件」を統計的に保証する対応関係まで固定されていない。","evidence":"D52と一次資料§1はS-1bを同一backoff条件のgate on/off差分と定義するが、ドラフトの18セル列挙はident_allを独立した構成名として置くだけで、g_rl/g_rtとのbuild、backoff定数、実行ブロック、比較方向の一致をmachine-readableに拘束していない。D50の+61〜99%は既知pilotであり、この対応が崩れると軸寄与ではなく別構成差になる。","proposed_fix":"workloadごとに `{gate_on, ident_all}` の対応表と、gate述語以外が同一であるhash／設定差分検査をfreeze成果物へ追加し、同一campaign・同一ブロック内の事前指定比較として扱う。"},{"claim":"IUTの検定力を単一componentの検定力と混同しない旨を明記すべきである。","evidence":"max-pによるIUT自体は、各component pが妥当なら依存性にかかわらず正当で、Holmへ1本として投入できる。しかしS-1aは9本すべて、S-1bは3本すべての通過が必要であり、共通の系側セルを共有するためcomponentは強く依存する。","proposed_fix":"報告するpowerを「各component」「S-1a IUT全体」「S-1b IUT全体」に分け、共通セルを共有する相関構造をsimulationに含める。"},{"claim":"「少数観測の交差でもpが10^-3台」というN=8の保守化根拠は、交差数と値配置を定義しないため検証不能である。","evidence":"median差のpermutation tailは順位だけでなく中央付近の値間隔にも依存し、完全分離時点でもp≈1.55×10^-3である。したがって「少数交差」という自然言語だけでは頑健性を数量化できない。","proposed_fix":"0、1、2件の順位交差、tie、campaign効果を含む事前固定シナリオ表を示し、各シナリオの棄却確率または達成pを実装で列挙する。"}],"notes":["S-1aを9比較、S-1bを3比較のmax-pとするIUTは、それぞれ「全workload・全対照で優越」という連言主張に対応する限り正当である。Holmは4本のp値の独立性を要求しない。","N=8/8の組合せ数C(16,8)=12,870という算術は正しい。誤りは、その逆数をmedian差統計量の達成可能最小pと同一視した点にある。","歴史データで選んだg_rl/g_rtと既知軸argmaxをfresh標本の前に固定することは、登録追試と明記する限りfresh検定の第一種過誤を直ちに壊さない。ただしpilot選択を含む一般化可能性の限定は維持すべきである。","fails-closedの語だけでは統計ゲートにならない。F9/F14型の恒真ゲート再発を防ぐには、screen失敗時p=1、層別分割のみ列挙、tieをtailへ含める、といった機械判定可能な規則が必要である。"],"verdict":"reject"}```

### 5.2 事前登録作法レンズ (verdict: adopt-with-conditions)

```json
{"lens":"事前登録作法","must_fix":[{"claim":"検定単位を「系列」から「独立セッション」へ変える改訂を、fails-closed な「明確化」と分類することはできない。","evidence":"docs/phase3-main-experiment.md の統計計画は検定単位を明示的に「系列」と固定し、D52/§2.1 も「現行統計計画をそのまま適用」としている。N=8 個のセッションを独立標本化する変更は検定力を上げ、LLM 側の有意化を容易にする。OS entropy は独立性仮定の根拠にはなっても、事前登録改訂の類型を制約方向へ変換しない。","proposed_fix":"「旧規定との明確化」「制約方向」という記述を撤回し、D44 の範囲外となる実質的プロトコル改訂として、既知結果を明示した上で人間の明示承認を得る。承認しないなら検定単位は系列のまま維持し、固定構成追試用の系列定義を別途事前固定する。"},{"claim":"2026-07-15 改訂時点の HARKing 境界が登録されていない。","evidence":"親節は2026-07-12時点のD50等を開示しているが、本ドラフトはその後、D50の+61〜99%、fresh CV 0.11〜1.07%、wired 3.0%を見た上でN=8、片側検定、IUT、floor下限を選んでいる。本文中で数値を根拠に使うだけでは、「これらを見た後の設計確定」であることや、S-1が結果既知の登録追試・対象軸n=1である限定を更新できない。","proposed_fix":"冒頭に「2026-07-15改訂時点の既知結果台帳」を追加し、閲覧済みのD50、既知軸実測、fresh CV、既存floor、その他S-1関連結果を列挙する。N・検定方向・IUT・floor規則はそれらを見た後の固定であり、S-1はconfirmatoryではない結果既知の登録追試、対象軸n=1という限定が不変だと明記する。"},{"claim":"campaign-1をスクリーニングに使いながら、同じ4セッションを全8セッションの最終検定へ再利用する二段階判定は既存§2.1と矛盾する。","evidence":"§2.1は「一次スクリーニング＝偵察の型」「headline＝検証相(seed×N)上の分布比較」と段階を分離している。本ドラフトはcampaign-1の観測でfloor超過を選別した後、campaign-1/2をpoolしてexact permutationを行うため、選別に使ったデータが検証標本へ混入する。時間ブロック化はこの二重使用を正当化しない。","proposed_fix":"既存D50偵察をスクリーニングとして固定し、fresh N=8は全て検証相の標本として扱う。4+4 campaignは検証相内の時間ブロックに限定し、campaign-1結果による選別・停止・検定変更を禁止する。"},{"claim":"検証相のN_verifyを「後で確定」に残したまま、S-1サンプル設計の認可ブランクを充足したとは称せない。","evidence":"2026-07-13節はC4抽出粒度の実走前繰延べを撤回し、同節末尾もS-1a/S-1bの検証相nは別途固定するとしている。本ドラフトはN=8性能セッションと、未確定の「想定N_verify=10/workload」の関係を定義せず、正しさ検証反復数・長extime・certified成立条件を実装タスクへ繰り延べている。これは観測後に検証強度を選べる空白を残す。","proposed_fix":"追記前にN_verify、対象構成、workload別反復数、長extime、性能N=8との関係、未達時の扱いを拘束値として確定する。確定できない場合は「4点充足」を撤回し、S-1実走禁止の未充足ブランクとして残す。"},{"claim":"既知軸比較点のmachine-readable freezeが実体化されておらず、基準点選択の自由度が残る。","evidence":"ドラフトは「checklist次項の成果物」と参照するが該当する次項がなく、P2-2、BACKOFF_FIXED、sortのworkload別variant ID・flags・source/hashを本文でも成果物でも特定していない。§2.1は過去実測argmaxを再計測前に固定することを要求しており、名称だけのfreezeはF9型の恒真ゲートになり得る。","proposed_fix":"実走前にworkload×既知軸ごとの一意なvariant ID、全flags、source/pin、選定元観測、hashを持つfreeze台帳を生成し、その実在パスとdigestを本節へ記載する。freeze不在・不一致ならdriverが開始を拒否する規則も固定する。"},{"claim":"12時間の総量上限だけでは、再測・予備2時間の結果依存配賦を防げず、LLM有利の自由度を残す。","evidence":"「再測・予備≈2h」の使用条件、セル別上限、実行順、未使用枠の移転可否が未定義で、「超過が必要になった時点で当該比較」の当該比較も特定できない。観測した僅差や失敗に応じて系側だけを再測したり、後順位の対照を予算切れにしたりできる。F8の定量裏付け不足型にも近い。","proposed_fix":"セル・workload・検証相ごとの最大反復数、再測を許す観測値非依存の閉じた故障条件、固定実行順、予備枠の対称配賦、枠移転禁止、予算切れ時に同時に判定不能へ倒す比較集合を事前固定する。"},{"claim":"裁定台帳が未実在の段階で「must-fix全反映」と断定しており、そのまま追記すると虚偽の監査保証になる。","evidence":"指定パス output/insights/2026-07-15_s1-sample-design.md は現時点で存在しない。2026-07-13節の形式は、実在する裁定台帳とレビュー全文を根拠に確定済み状態を記録するものだった。不存在参照はF9の恒真ゲート、未反映レビューの全反映宣言はF8型の裏付けなし記述を再発させる。","proposed_fix":"全レビュー裁定を反映し、台帳を実際に生成・監査した後でのみこの文言を確定形にする。追記前チェックで台帳の実在、レビューJSON、全must-fix対応表を検査する。"}],"should_fix":[{"claim":"continuous値向けexact permutation拡張の分析仕様が実装タスクへ残り、tiesや片側p値計算の解釈余地がある。","evidence":"既存search_baselines.pyは離散小値域用であり、ドラフト自身が連続値2標本への拡張を後続タスクとしている。統計量はmedian差とあるが、同値、欠測、非有限値、全分割に観測割当を含める規約、確率優越Aのtie処理が固定されていない。","proposed_fix":"計測前に数式、tie規約、欠測・非有限値の扱い、片側方向、テストベクトルと実装hashを凍結する。"},{"claim":"「検定力≈1.0」は事前の設計検定力ではなく、既知のスクリーニング通過効果へ条件付けた事後的な感度説明である。","evidence":"効果量d≥2.7は「中央値差>floor」とfresh CVから構成され、さらにS-1bの巨大な既知効果を引用しているため、未知効果に対するN選定根拠ではない。","proposed_fix":"「検定力概算」から分離して既知結果条件付きの感度分析と明記し、N=8の根拠は最小p、事前固定した効果量レンジ、または保守的シミュレーションで示す。"},{"claim":"OS entropy自己シードをもってセッションの独立性が「成立」と断定する表現は強すぎる。","evidence":"乱数初期値の相違は同一ホストの時間ドリフト、熱、負荷、campaign内相関を除去しない。ドラフト自身が時間ブロックとinterleaveを必要としており、完全な独立性保証とは整合しない。","proposed_fix":"「独立性の操作的仮定」と弱め、campaign/block別結果、ドリフト診断、違反時の判定不能規則を報告義務にする。"}],"notes":["S-1a/S-1bをmax-pのIUTとしてHolm族へ各1本だけ投入する規則、workload別勝ちgateの固定、共通stock併記、3.0%を下限にするfloor規則は、単独ではLLM有利の自由度を増やさない制約方向である。","追記位置、###見出し、日付付き「着手時確定」、二層書き分け、裁定台帳参照という外形は2026-07-13節と整合する。ただし裁定台帳の実在と内容確認が確定形掲載の前提である。"],"verdict":"adopt-with-conditions"}```

### 5.3 fails-closed 実効性レンズ (verdict: adopt-with-conditions)

```json
{"lens":"fails-closed 実効性","must_fix":[{"claim":"12 時間上限は検証相の N・長 extime が未確定で、かつ時間計上規則もないため拘束として発火しない。","evidence":"phase3-main-experiment.md の統計計画は実行前に総予算上限を確定するよう要求し、同時に seed×N・長 extime の検証相を headline 必須としているが、ドラフトは N_verify=10/workload を非拘束の想定として後続タスクへ残す。さらに成功・失敗・timeout・自動再測・floor・build・verify のどの経過時間を 12h に算入するか、累積値を誰が判定するかが未定義で、「超過が必要になった時点」を再現不能にする。","proposed_fix":"初回計測前に検証相の N・extime・対象セルと全計測種別を固定し、campaign 所有プロセスの monotonic wall time を成功・失敗・timeout・再測込みで台帳へ累積する規則を明記する。各起動前に残予算を検査して不足なら起動せず判定不能へ閉じる driver gate と positive control を必須化する。"},{"claim":"「certified 要件は全構成に適用」は性能標本を拒否する consumer と証明書の同一性条件がなく、宣言だけで迂回できる。","evidence":"既存 pipeline.evaluate は trace/perf 別ビルド後、全 verify pass が certified の場合だけ bench と COMMIT へ進むが、ドラフトの 144 セッションは measure_point 直接実行として定義され、S-1 driver がこの経路を必ず使うとも、certification artifact と性能 binary・source・config・workload を digest で結ぶとも書かれていない。phase3-main-experiment.md の失敗条件 (a) は certified 破れを即失格とするため、report 側の取り残しは規律違反になる。","proposed_fix":"S-1 driver/report の前提として、各採用標本に対応する trace_bin・perf_bin・source/config/workload digest、必須 verify_configs、certified COMMIT を照合し、欠落・不一致・indeterminate・unstable を検定入力へ入れない hard gate を登録する。measure_point 単独経路からの標本投入を拒否する負例も要求する。"},{"claim":"既知軸 argmax freeze は固定時点・入力集合・tie 規則・改竄検出がなく、再計測後の差し替えを防げない。","evidence":"§2.1 の正本は過去実測 argmax を事前固定し再計測順位で動かさないとするが、ドラフトは成果物を「checklist 次項」に委ねるだけで、どの既存 campaign/WAL、pin、環境、候補集合から選ぶかを固定していない。現時点で machine-readable freeze も裁定台帳も存在せず、D52 が入力凍結に要求した hash provenance と非対称である。","proposed_fix":"最初の S-1/floor 計測より前に、全18セルの canonical config、候補母集団、選択元 artifact hash、argmax/tie-break 規則、pin・binary/source digest を含む freeze を commit し、その commit と時刻先行性を登録する。driver は毎起動時、report は集計時に同じ hash を再検証し、不在・drift を判定不能として停止する。"},{"claim":"2 campaign・interleave・ドリフト検出は実行予定の文章に留まり、順序違反や block drift があっても pooled 検定がそのまま走る。","evidence":"各 campaign のセル順、順序の乱数 seed、時間分離の最小条件、中断・失敗・再開時の位置処理、期待72セッションとの照合が未定義である。さらに campaign を時間 block と称しながら全8点を無層化 permutation するため、block shift がある場合の全標本交換可能性を仮定してしまい、「ドリフトの検出面」に閾値も停止動作もない。これは docs/failures.md F9/F14 の恒真ゲート型である。","proposed_fix":"観測前に campaign×round×cell の均衡ランダム化 schedule と hash を凍結し、実行 event ledger との完全一致、重複・欠落・順序逸脱を driver が拒否するよう登録する。検定は campaign 内割付を保つ stratified exact permutation にするか、事前固定した drift 判定閾値と逸脱時の判定不能規則を置き、schedule mutation の positive control を必須化する。"},{"claim":"「セル実測 CV で判別力を再評価し、確保できなければ判定不能」は判別力不足の数値基準がなく、結果を見た後に任意発火できる。","evidence":"ドラフトは正常近似 d≥2.7 の参考計算を示す一方、high-abort セルについては使用する分布モデル、対象効果、α、検定統計量、power 閾値、CV の推定時点を一切定義していない。CV だけでは median 差の exact permutation power は決まらず、全8点観測後の裁量判断は negative/positive の選択的な判定不能化を許す。","proposed_fix":"実走前に、対象効果を floor 超の固定値、Holm 初段 α=0.0125、power 下限を例えば0.80とし、median-difference permutation と整合する固定 simulation/厳密計算、入力データ、評価時点、三値出力をコード化する。事後 power を採否に使わない方針なら当該条項を削除し、N=8 完走時は常に p・効果量・不確実性を報告する。"},{"claim":"floor スクリーニングは入力値と計算順が矛盾し、同じデータから異なる判定を生成できる。","evidence":"正本は対象プロトコル/contention 域ごとの floor 再実測と near_floor の cross-run 裏取りを要求するが、ドラフトは別枠の対象別 floor 再実測を予算計上しつつ、判定には「両側セルの実測 between-CV」と3%の最大を使うとしている。そのCVを campaign-1だけ、全8点、別floor計測のどれから得るか不明で、中央値差の分母、丸め境界、方向一致、near_floor、同値時の扱いも未定義である。","proposed_fix":"比較ごとの floor 入力源・標本・式・評価順を一意に固定し、例えば max(事前の対象別floor、両セルの事前指定CV推定、3%)、相対差の分母、境界の包含、campaign別方向一致、near_floor の三値規則を純関数として登録する。欠損・非有限値・入力hash不一致は判定不能へ倒す。"},{"claim":"OS entropy 自己シードを独立性および信頼度 1-εⁿ の根拠にする条項は監査不能で、現在の実装事実にも反する。","evidence":"external/ccbench/include/random.hh は std::random_device の1出力を s[0] に入れ、s[1]を決定論的生成するだけで、seed値・entropy源・重複を記録しない。プロセス分離は性能ドリフトの独立性を保証せず、std::random_device もコード上はOS entropyを保証しない。また既存 pipeline.evaluate は finally で trace directory を削除するため、「traceファイル自体の保全で事後再現」という consumer は現状存在しない。εの定義もないため 1-εⁿ は計算不能である。","proposed_fix":"決定論的seed導入と記録を行わない限り、seed×Nを「独立seed」と呼ばず反復セッションと限定し、1-εⁿ の形式的信頼度主張を停止する。形式信頼度を維持するなら D16 手続きを経て seed/stream identity・εの根拠・重複検査を実装し、検証traceを永続保存してhashとretentionを検査するまで headline を blocked にする。"},{"claim":"裁定台帳と「must-fix 全反映」の記述は対象ファイル不在でも通るため、採用時点では F9 の恒真保証を再発させる。","evidence":"ドラフトが正本として指す output/insights/2026-07-15_s1-sample-design.md は現時点で存在しない。docs/failures.md F9 は検査対象不在を黙ってskipしたことを恒真ゲートとして記録し、対象存在のhard failとpositive controlを恒久対応にしている。","proposed_fix":"3レンズ裁定台帳の作成、各must-fixの disposition と反映箇所、未解決ゼロの機械検査を phase追記と同一commitに含める。check_docs.py またはS-1専用preflightで台帳不在・未解決must・本文hash不一致をfailさせ、わざと台帳を欠損/改変するpositive controlを追加する。"}],"should_fix":[{"claim":"144セッション内に含まれる read-heavy の sk_ad と stock を予算内訳で「欠測補充」として再度計上しており、実験範囲が二重に読める。","evidence":"セル定義は3 workload×6構成にsortと共通stockを含む一方、総予算内訳はsort read-heavy欠測補充（sk_ad+stock）を別項目に置くため、同一campaign再計測とfreeze用の事前測定のどちらか判別できない。","proposed_fix":"144セッションに包含されるものと別枠測定を表で排他的に列挙し、重複計上なら削除、別測定なら目的・N・予算計上規則を固定する。"},{"claim":"「ほぼ完全分離」「少数観測の交差でも10^-3台」は具体的な交差パターンを固定しておらず、N=8の頑健性根拠として再計算できない。","evidence":"完全分離時の最小pは示されるが、何件の交差までを想定し、median差統計量でどのpになるかが記録されていない。","proposed_fix":"代表的な1交差・2交差パターンの列挙結果を固定スクリプトで示すか、根拠を「最小pの可達性と8セッション前例」に限定して曖昧な10^-3主張を削除する。"}],"notes":["N=8/8の完全分離時に最小片側pがHolm初段0.0125を下回る点、IUTのmax-pをHolm族へ1本ずつ投入する方針、within-run repsを観測単位にしない方針自体は保守的である。","主な欠陥は方針の方向ではなく、停止・拒否・判定不能を発火させるdriver/report consumer、凍結hash、台帳、positive controlが未登録な点に集中している。"],"verdict":"adopt-with-conditions"}```

## 6. v1 全文 (レビュー対象になった版、逐語)

### 2026-07-15 着手時確定 — S-1 サンプル設計 4 点 (性能分布比較の n・検定単位・検定力・総予算)

統計計画「サンプル設計 (実行前に数値を確定して本節に追記)」4 点の履行。2026-07-13 節と同じ
二層書き分け (層 1 = 認可ブランクの充足、層 2 = 実走に必要な付帯規則の確定 — 「数値確定のみ」
とは称さない)。3 レンズ敵対レビュー (統計 / 事前登録作法 / fails-closed 実効性、独立コンテキスト)
の must-fix 全反映。裁定台帳 = `output/insights/2026-07-15_s1-sample-design.md`。

**層 1 — 認可ブランクの充足 (4 点):**

- **(i) アームあたり系列数と 1 系列の試行予算:** アーム = 比較セル (構成 × workload、下記
  18 セル)。**N = 8 独立セッション/セル**。1 セッション = 確定動作点 (RECORDS=1M / THREADS=48 /
  EXTIME=3s / REPS=5) の measure_point 1 回、観測値 = セッション reps median。セル構成 =
  3 workload (rr50/rr5/rr95) × 6 構成 {系側 best gate, ident_all (S-1b 対照), P2-2 フラグ最適,
  BACKOFF_FIXED grid 最良, sort 全列挙最良 (read-heavy は sk_ad 事前固定 — §2.1 既定), 共通
  stock} = 18 セル、計 144 セッション。
- **(ii) 検定単位 = 独立セッション:** 統計計画本文の「検定単位 = 系列 (P2-5 と同じ。試行は
  path-dependent で独立でない)」は旧 headline (LLM 探索実験) の規定であり、D52 で登録追試に
  再構成された S-1 は**固定構成の再計測**のため path-dependence が存在しない。セッションは
  プロセス分離 + RNG の run ごと OS entropy 自己シード (ycsb は CLI seed を持たない —
  `external/ccbench/include/random.hh` Xoroshiro128Plus::init) により独立。within-run reps は
  セッション内相関のため観測単位にしない (median に縮約)。本明確化は検定単位の粒度を細かく
  する方向 (n 増) だが、独立性が成立しない単位を観測に数える経路を塞ぐ fails-closed 側の
  確定であり、S-1 固有 (旧規定は探索実験復活時に復活)。
- **(iii) 検定力概算:** 検定 = 2 標本 exact permutation (片側、N=8/8 の全 C(16,8) = 12,870
  分割列挙、統計量 = median 差) + 確率優越 A 併記 (`search_baselines.py` の枠組みを連続値
  2 標本に拡張、実装は S-1 driver タスク)。完全分離時の最小 p = 1/12,870 ≈ 7.8×10⁻⁵ <
  Holm 初段 α = 0.0125 (族 4 = S-1a/S-1b/S-2/S-3、2026-07-12 追記)。N の下限根拠: N=4 は
  最小 p = 1/C(8,4) = 1/70 ≈ 0.0143 > 0.0125 で構造的に不可、N=5 (1/252 ≈ 0.0040) が最小
  充足。8 への保守化根拠 = ほぼ完全分離 (少数観測の交差) でも p が 10⁻³ 台に留まる頑健性 +
  between_run_floor.py の独立 8 セッション前例との整合。正規近似の検定力: スクリーニング
  通過条件 (中央値差 > floor、wired 保守値 3.0%) と fresh between-run CV 実測 (0.11〜1.07%、
  silo baseline) の下で効果量 d ≥ 2.7、n=8/8・α=0.0125 片側で検定力 ≈ 1.0。**正直な限定:**
  この検定力はスクリーニング通過 (= 点推定で floor 超差が観測された比較) に条件付き。
  high-abort 構成で between-CV が膨らむ場合はセル実測 CV で再評価し、判別力が確保できない
  比較は判定不能としてそのまま報告 (2026-07-10 追記 2 の型)。S-1b は D50 実測 +61〜99% が
  floor の 20 倍超で、事実上完全分離を予期。
- **(iv) 実計測の総予算上限 = 合計 12 時間 (宣言値、拘束):** 内訳概算 — 性能 144 セッション
  (verify 込み、certified 要件は全構成に適用 — 規律 2) ≈ 2.5〜3 h、対象別 floor 再実測 +
  sort read-heavy 欠測補充 (sk_ad + stock) ≈ 0.5〜1 h、検証相 (想定 N_verify = 10/workload —
  予算計画上の想定であり、拘束数値は検証相実装タスクで確定して本節に追記) ≈ 3〜5 h、再測・
  予備 ≈ 2 h。**超過が必要になった時点で当該比較は判定不能として報告する** (S-2/S-3 採点
  工数上限と同型の fails-closed。予算を後から増やして完走を装わない)。

**層 2 — 付帯規則の確定 (いずれも fails-closed / 制約方向):**

- **S-1a の検定の形 (intersection-union):** p_S-1a = max over {3 workload × 3 既知軸基準点}
  の片側 permutation p — 全 9 比較で有意のときのみ S-1a 有意 (IUT、α inflation なし・保守)。
  S-1b も同型 (gate on/off、3 workload の max-p)。Holm 族への投入はこの max-p 各 1 本
  (族 4 は不変)。
- **比較点の事前固定 (best-of-n 選択効果の遮断):** 系側 = D50 の workload 別勝ち gate
  (balanced/read-heavy = g_rl、write-heavy = g_rt) に事前固定 — 再計測での構成再選択をしない。
  既知軸側 = 過去実測 argmax 構成を machine-readable freeze (checklist 次項の成果物) で事前
  固定し、その構成のみ再計測 (grid/列挙の全点は回さない。再計測での順位入れ替わりは観測と
  して報告するが基準点は動かさない — §2.1 既定の適用)。
- **二段階判定の計測配置:** 性能計測は時間分離した 2 campaign (各セル 4 セッション × 2、
  interleaved) に分ける。スクリーニング = campaign-1 の floor 丸め + campaign-1/2 間の方向
  一致 (cross-run 再現)。検証相の検定 = 全 8 セッションを pool した exact permutation
  (時間ブロック分割はドリフトの検出面も兼ねる)。計測総量は増やさない。
- **実行順 interleave:** 各 campaign 内でセル間 1 セッションずつ交互に周回 (系統時間ドリフト
  がアーム差に化ける経路の遮断)。
- **floor の判定適用:** スクリーニングの floor 丸めには、当該比較両側セルの実測 between-CV の
  max と wired 保守値 3.0% の大きい方を使う (対象別再実測の保守化。fresh 値 0.67〜1.07% を
  そのまま使って丸め幅を狭めない)。
- **「seed×N」の操作的定義:** ycsb は CLI seed を持たず、RNG は run ごとに OS entropy で自己
  シードする — 検証相・性能計測とも「seed×N」は**独立 N 反復**を意味する。決定論的 seed 固定
  は導入しない (CCBench 改変 (D16) を要し、独立性はエントロピーシードで既に満たされる。trace
  の事後再現は trace ファイル自体の保全で担保)。信頼度 1-εⁿ の n は独立反復数と読み替える。
- **判定不能の扱い:** n 未達・予算超過・判別力不足は判定不能としてそのまま報告 (どちらにも
  倒さない — 2026-07-13 節と同一原則)。

---

