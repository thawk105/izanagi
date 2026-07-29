# 計測反復・検証 seed の逐次停止 (sequential stopping) の設計 v2 (2026-07-15)

**契機:** related-work §7.2 Best-of-∞ (`2509.21091`) の部品予約「固定反復を逐次停止に置換し、
反復予算を際どい点に寄せる」の具体化。phase3.md 段 8 で bench-first screening と同一の実装承認
案件に束ねてある (2026-07-15 追記)。bench-first 設計 v2
(`output/insights/2026-07-14_bench-first-screening-design.md`) の姉妹設計であり、様式・規律
整合の作法を同文書から継承する。

**分類: 探索効率の機構設計。設計フェーズは計測ゼロ。実装フェーズの検証はモック列挙と既存 WAL
の照合を主とし、実走は最小限 (計測窓を使う)。事前登録の凍結内容に触れない。実装着手はユーザー
gate (bench-first と同一案件)。**

**版歴: v1 (2026-07-15) → 3 レンズ敵対レビュー (§12、原文 =
`2026-07-15_sequential-stopping-review.md`) → v2 (must-fix 6 系統・should-fix 7 系統を全反映。
最大の変更 = **(b) bench rep 前倒しを「採らない」へ降格** — 3 レンズが独立に「採否不変」の
主張を反証したため)。**

---

## 1. 目的と非目的

- **目的:** near_floor 帯の差の cross-run 裏取り (D19 が要求、未実装) を、固定 rounds でなく
  逐次停止で**最小コスト導入**する。将来の検証相 (複数 seed trace) の seed 数設計を較正前提で
  予約する。v1 が掲げた「bench 反復の削減」はレビューで棄却され (§10-(vi))、本設計の主目的は
  機械時間の節約ではなく**裏取りコストの最小化**である (節約の主役は bench-first)。
- **非目的:** (i) 採否規則の変更 — between-run floor 丸め + Mann-Whitney (stability.compare)
  へ渡す測定の反復構成 (reps=5) も含めて不変。**「採否に使う測定」の反復数は一切触らない**
  (v1 の (b) はここを破っていた — §10-(vi))。(ii) S-1 事前登録済みサンプル設計への適用。
  (iii) D36 で凍結した verify 構成 (legacy+S2) の縮小。(iv) 正しさゲートの緩和 — anomaly
  検出時の即 reject は完全に不変。

## 2. 現行構造とコスト (実コード・実測 — レビュー 3 レンズの照合で生存)

- 1 測定 = reps 反復を内包した 1 点 (`pipeline.PerfConfig.reps`、**既定** 5 — 不変条件ではなく
  呼び手により 2/3/10 も存在する [レビュー L3-S1]。本設計の対象は既定 5 の探索的 bench のみ)。
  bench ≈ 18 秒/variant (bench-first v2 の WAL 実測)。
- remeasure (`stability.remeasure_until_stable`) は既に逐次: CV 収束で 1 ラウンド打ち切り、
  最大 3 ラウンドで unstable。
- verify は構成ごとに 1 trace run (`pipeline._run_one_pass`、legacy + S2)。seed 反復は現行に
  存在しない — 「検証 seed の逐次停止」は既存機構の適応化ではなく検証相設計そのもの (§4(c) 予約)。
- cross-run 再現は rounds=1 固定 (`backoff_repro`: 別 campaign・逆順・別時間窓で 1 回再測、
  **round ループは存在しない**)。`stability.compare` の docstring が「near_floor 帯の headline
  化前に cross-run 再現で裏取り要。別 boot / rounds≥3 への拡張が将来必要」と明記済み。
- between-run floor 較正 = 8 独立セッション固定 (保守側規約)。
- コスト非対称: verify ≈ 120〜250 秒/variant ≫ bench ≈ 18 秒/variant。

## 3. 適用先の裁定 (v2 — レビュー反映で (b) を降格)

| 適用先 | 裁定 | 理由 |
|---|---|---|
| (a) near_floor cross-run 再現の rounds 適応化 | **採る (唯一の実装対象)** | D19 裏取り要件 (rounds≥3) の未実装を逐次で最小コスト導入。8b の workload 特化主張の headline gate に直結 |
| (b) bench rep の逐次打ち切り | **採らない (v2 で降格)** | 3 レンズが独立に「採否不変」を反証 — §10-(vi) に理由を固定 |
| (c) 検証相 seed の逐次停止 | **予約 (条件を v2 で厳密化)** | 検証相自体が未実装。較正・独立性検査の前提 (§4(c)) が通るまで数値上界の報告を禁止 |
| (d) floor 較正セッションの削減 | **採らない** | floor は保守側 (最大) 規約 — 早期打ち切りは floor 過小推定 = 偽 faster の温床 |

## 4. 停止則の規定

### (a) cross-run 再現の逐次化 — SPRT (逐次確率比検定)

対象: `compare` が `near_floor` (floor〜1.5×floor) の faster/slower を返した差の headline 昇格前
裏取り。1 round = variant/baseline の独立セッション対を新しい時間窓で 1 回ずつ再測し、二値
`x_i = 1` (元と同方向 かつ |rel| > floor) / `x_i = 0` (それ以外) を得る。

- **検定:** SPRT。H0: p = 0.5 (偶然の一致) vs H1: p = p1 (真の再現)。既定 p1 = 0.9、
  α = β = 0.1。対数尤度比 (一致 +ln1.8 = +0.5878、不一致 ln0.2 = −1.6094) を round ごとに
  加算し、+ln9 (=2.1972) 超で「再現確定」、−ln9 未満で「非再現確定」、いずれも跨がず
  R_max = 8 に達したら **indeterminate (headline 不可)** に倒す (fails-safe)。
- **停止挙動の正確な記述 (v1 の「不一致 2 で非再現」は誤り — レビュー L2-M1 で訂正):**
  再現確定の最短は 4 round 連続一致。非再現確定は「不一致 2・一致 ≤1」の系列 (先頭 00 は
  2 round、010/100 系は 3 round)。一致 2 以上を挟むと不一致 2 では確定しない (例 1100 は
  LLR −2.04 で境界内)。R_max = 8 では 1 不一致を挟む系列も確定に到達できる (例 11011111 =
  1 不一致 + 7 一致で LLR 2.51 > 2.20。7 round 時点の 1101111 は 1.92 で未確定 — v1 の
  R_max=6 では先頭 4 連続一致のみが確定可能で不確定率が過大だった)。
- **operating characteristic (OC) の明示 (レビュー L2-M1 の要求):** p=0.9 の下で R_max=6 の
  場合、再現確定 65.6% / 非再現確定 3.6% / indeterminate 30.8% (レビュー検算値)。R_max=8 の
  OC と期待 round 数は**実装時にユニットテストの全系列列挙で厳密に固定**し、その表を本 insight
  に追記してから初回運用する (概算を運用判断に使わない)。indeterminate は「headline 不可」で
  あって「非再現」ではない — 保守側に倒れる設計であり、不確定率の高さは fails-safe の対価
  として明示的に受け入れる。
- **1 round の実装は 2 形態:** (i) **保守形 (v2 の既定・唯一の初期実装)** = pipeline.evaluate
  のフル評価 (verify 込み、現行 backoff_repro と同じ。round あたり ~140〜270 秒 × 2)。
  (ii) 軽量形 = bench-only 再測。**軽量形の有効化条件 (レビュー L3-M4 で強化):** variant_id
  (genome + src_token) だけでは certified の同一性を主張できない — ccbench pin・verify_configs・
  workload・PerfConfig を WAL 照合する共通 certification consumer と、bench-first の
  uncertified 数値隔離 (screening 配線) の**両方**が実装された後にのみ有効化し、repro 系列は
  fitness でなく専用ステージに記録して COMMIT を書かない (§7)。
- **i.i.d. への対策 (レビュー L2-M2):** SPRT の α/β は round 間独立を仮定する。対策 3 点:
  (1) round 内の variant/baseline の測定順序を round ごとに無作為化 (系統的順序効果の除去)、
  (2) round 間に時間窓の分離を義務化 (back-to-back の連続実行を禁止。最小間隔は基準点再測の
  30 分規約 [bench-first §3.2] と同じ帯で実装時に規定)、(3) 系列 ledger に各 round の符号付き
  rel・時刻・boot-id を残し、**同一 boot 内で完結した系列は「same-boot」フラグ付きで報告し
  α/β を名目値として主張しない** (現行 repro の「別 boot ではない」限界の正直な継承)。
  単調ドリフト検知 (v1 §5-2) は停止規則から**外し**、事後診断 (ledger の rel 系列への自己相関・
  トレンド記録) に降格する — 二値 x_i に単調性は定義できず [L3-S2]、rep3 の全増全減の偶然率は
  33% [L2-S1] で規則としては誤発火が支配するため。
- **identity と再開 (レビュー L3-M2 / L1-M4):** 系列は `series_id` (元差の campaign-id +
  variant 対 + 検定パラメータの正準化 hash) で識別し、各 round は search_config に
  `{"seqstop": {"series": series_id, "round": i}}` を焼き込んで**別 campaign-id** にする
  (同一 config の再実行が terminal skip で空振りする現行 backoff_repro の構造 [ident.py/loop.py]
  への対策)。p1/α/β/R_max/順序無作為化 seed も series_id の正準化対象に含め、パラメータ変更が
  旧 round を再利用しないことを回帰テストで固定する。
- **耐久記録と再開 (レビュー L3-M3 / L1-M5):** LLR 軌跡・round ごとの campaign-id 参照・
  停止判定は、driver 管轄の**append-only 系列 ledger** (JSONL、campaign dir 配下。reports/ の
  ような proof-chain 保護外に置かない) に記録する。クラッシュ再開は ledger から LLR を再構成
  する (round の実測値自体は各 round の campaign WAL が正本 — ledger は集計の重複であり、
  食い違えば WAL 側を採る)。**再計算可能性の主張は「観測済み round 列から停止判定を決定論的に
  再計算できる」に限定**する — v1 の「固定反復ならどうだったかを replay 可能」は未実行 round
  が存在しない以上、原理的に恒真 (F9 型) であり撤回する。
- **headline gate の配線 (レビュー L1-M6):** 系列の終端状態 (再現確定 / 非再現 / indeterminate /
  same-boot) を層3 headline consumer が読む形式で ledger に置き、**「再現確定」以外は headline
  昇格を fail-closed で拒否**する否定テストを固定する。indeterminate を faster/成功と誤読する
  経路の非交差テスト (bench-first §3.3 と同作法) を含める。
- p1 = 0.9 は**事前固定の設計値**であり、初回 ablation で較正できる類のものではない
  (レビュー L1-S2/L2-S2 — 1 点の ablation は配線 smoke と結論比較に限定)。較正するなら
  workload・差の向き・abort class を跨ぐ複数系列の holdout で下側信頼限界を求める別タスク。
  high-abort genome (D19: between-run ドリフト大) は SPRT 対象外 (固定 rounds) に倒す。

### (b) bench rep の逐次打ち切り — v2 で「採らない」(§10-(vi) に理由)

v1 の規定は削除。§10-(vi) 参照。

### (c) 検証相 seed の逐次停止 — 較正前提の予約 (v2 で条件厳密化)

対象: 将来の検証相 (最終候補への複数 seed trace 検証、roadmap §3.2)。

- **前提タスク (これらが全て通るまで実装しない・数値上界を報告しない) [レビュー L1-M1 /
  L2-M6 で強化]:**
  1. per-seed anomaly 検出率の較正: positive control 群 (verify-red 実証済みの壊れ variant) を
     seed を変えて N 回検証し、**点推定でなく片側下側信頼限界 p_det,L** を求める。
  2. seed 間独立性の検査: 同一 control の seed 系列で全 green の頻度を二項期待と比べ、
     過分散 (相関) を検査する。相関が棄却できなければ有効 seed 数へ割り引くか固定 seed 数に
     倒す (完全相関なら見逃しは (1−p_det) のまま n で減らない)。
  3. 較正の選別バイアスの明示: 較正に使う control は「既に検出できた壊れ方」であり、報告は
     常に**較正済み故障クラスへの条件付き** (「較正外の壊れ方への検出率は宣言範囲外」を
     roadmap §3.2 の宣言範囲の作法で書く)。calibration 集合と holdout control を分離する。
- **停止則:** anomaly 検出 → 即 reject (現行どおり、逐次以前)。green が連続する場合、
  (1−p_det,L)^n_eff (n_eff = 独立性検査を通った有効 seed 数) が目標 ε (既定 0.05) を下回ったら
  停止。前提 1〜3 のいずれかが不成立の間は固定 seed 数 + 「較正未了」の明示に倒す (fails-safe)。
- Best-of-∞ の Bayes factor 型は「anomaly が seed 依存で flaky に出る」事態が観測されたときの
  拡張として予約。

## 5. 非定常・バイアスへの防御 (v2 で再構成)

1. **admission 静定の事実の訂正 (レビュー L1-S1):** 現行の admission は campaign 冒頭 +
   remeasure の再測前であり、rep/round ごとではない。(a) では **round ごとの admission 静定を
   新規要件**として課す (各 round は独立セッション対 = campaign 評価なので、既存の campaign
   冒頭 admission がそのまま round ごとに効く — 新実装は不要、要件の明文化のみ)。
2. **順序無作為化 + 時間窓分離 + same-boot フラグ** (§4(a) i.i.d. 対策に統合)。
3. **採否規則の構造隔離:** 停止則が触るのは round 数のみ。各 round の測定は本構成 (reps=5)
   のまま、採否・headline 判定は常に between-run floor 丸め + SPRT 終端状態のみを通る。
4. **proof chain:** LLR 軌跡・round 参照・終端状態を append-only ledger に残す (§4(a))。
   主張は「観測済み round 列からの停止判定の再計算可能性」に限定する。

## 6. 規律・既存決定との整合

- **規律 2:** anomaly 即 reject 不変。(c) の green 打ち切りは前提 1〜3 (較正・独立性・条件付き
  報告) が通るまで数値化を禁止し、暗黙の見逃しを宣言値に変える (緩和でなく明示化)。
- **規律 3:** 系列の終端状態と各 round の構造化記録を ledger + WAL に残し、層3 headline gate
  と人間 gate が読む (§4(a) 配線)。「WAL に書くだけで consumer 未配線」を作らない
  (レビュー L1-M6 対応 — loader/render の実装は着手時計画 §8 に含める)。
- **規律 4:** 反復数を無造作に増やさない (R_max=8 上限)・減らさない ((b)(d) 却下、round 測定は
  本構成のまま)。
- **規律 5:** 実装対象を (a) 保守形 1 本に絞った (v1 から縮小)。SPRT 1 本 + ledger + gate 配線
  のみ。軽量形・(c) は前提が揃うまで予約。
- **D19:** (a) は near_floor 裏取り要件の実装。floor 丸め・near_floor 意味論は不変。round 測定
  が本構成 (reps=5) のままなので「reps を減らした測定に floor を流用できない」問題 (bench-first
  §6(iii)) は発生しない。
- **D25 (再評価冪等):** series_id + round index + 検定パラメータを campaign-id に焼き込み、
  同一系列の再実行は ledger から再開、パラメータ変更は別系列 (§4(a) identity)。
- **bench-first との関係:** 同一承認案件。実装順は bench-first 本体 → (a) 保守形 →
  ((a) 軽量形は screening 配線 + certification consumer の後) → (c) は検証相設計時。
  機械時間の節約は bench-first の領分であり、本設計は裏取りの導入コスト最小化 — v1 の
  「削減」枠からの後退を正直に記録する。

## 7. WAL スキーマと consumer 波及

- (a) 保守形: 各 round は通常の campaign 評価 (既存スキーマのまま)。系列状態は driver の
  append-only ledger (§4(a))。新 WAL ステージは導入しない。
- (a) 軽量形 (将来・予約): `STAGE_REPRO_DONE` (fitness と COMMIT を持たない再測記録) を導入
  する場合、**変更対象の具体列挙** (レビュー L3-S3): `model.STAGES`、`wal.replay` /
  `records_by_stage`、stage 分岐の全 consumer (digest / replay / report 群)、および「repro-only
  variant が terminal/committed/certified に化けない」負例テスト。導入時に STAGE 読み手の
  全数 grep 監査を gate 条件にする (bench-first §3.5 と同じ F2/D25 型対策)。
- ledger は WAL の代替ではない: round の実測の正本は各 round の campaign WAL。ledger は系列
  集計で、食い違いは WAL 優先 (§4(a))。

## 8. 検証計画 (実装時)

1. **SPRT のモック全系列列挙 (計測ゼロ・主検証):** R_max=8 の全 2^8 系列で停止点・判定を列挙し
   OC 表 (p∈{0.5, 0.7, 0.9} の確定/非再現/不確定率・期待 round 数) をテストで固定、本 insight に
   追記。境界系列 (1100 非確定、010 非再現確定、先頭 4 連続一致の確定) を個別に固定。
2. **identity 回帰:** series_id が round・パラメータで一意に割れること、パラメータ変更で旧
   round が再利用されないこと、ledger からの再開が WAL と整合すること。
3. **headline gate の否定テスト:** indeterminate / 非再現 / same-boot / ledger 欠損の各終端で
   headline 昇格が fail-closed に拒否されること。
4. **決定論的 positive control (レビュー L1-S3):** 人工負荷でなく**注入系列** (モックの rel 列)
   でドリフト診断・same-boot フラグ・非再現早期確定の発火を固定。実走の positive control は
   「既知の非再現ペア (floor 内の 2 genome)」1 件で非再現確定の早期停止を確認 (計測窓 1 点)。
5. **shadow ablation (初回採用系列で 1 回):** SPRT 系列と並行して固定 rounds=5 の judgment
   (多数決) を同じ round 列に適用し、結論一致を確認 (これは反実仮想でなく同一データの別集計 —
   L2-M5 対応で「shadow 固定反復」の実走は行わず、観測済み round 列上の比較に限定)。

## 9. 効果の見積もり (帯 — v2 で「節約」から「導入コストの最小化」へ再定義)

- (a): 未実装の rounds≥3 裏取り要件を、固定 5 round (保守形 ~25〜45 分/件) に対し適応
  2〜8 round で導入する。非再現の早期確定 (2〜3 round = ~10〜27 分/件) と明確な再現の
  4 round 確定 (~20〜36 分/件) が主帯。R_max=8 の際どい系列は最大 ~37〜72 分/件 —
  **固定 5 round より高くつく尾がある**ことを明示する (fails-safe の対価。headline 昇格候補
  にのみ回すので件数は少ない)。厳密な期待値は §8-1 の OC 表で置換する。
- (c): 検証相の仮設計 (seed N 固定) に対する削減は前提 1〜3 の較正結果に依存し、事前に
  数値を約束しない (v1 の「p_det=0.6 なら半減」は較正前の数字遊びなので撤回)。
- v1 (b) の「~7 秒/点 × 点数」は (b) 降格により消滅。機械時間の節約は bench-first
  (点あたり 120〜250 秒) の領分。

## 10. 却下した代替案

- **(i) DISC の z-score 受理規準:** 採否判定への逐次統計の導入は between-run floor 丸め
  (主防壁) と競合し、location-scale 仮定が throughput の非定常ノイズで壊れる。
- **(ii) Dirichlet/Bayes factor の連続量直用:** 型不一致 (Best-of-∞ ノートの指摘どおり)。
- **(iii) 逐次 t 検定 (連続量の本格逐次検定):** 採否には触らない構造 (§1) を守る限り利得なく、
  α 消費・停止規則の複雑化のみ。
- **(iv) floor 較正セッションの適応削減:** §3(d)。保守側規約と正面衝突。
- **(v) remeasure ラウンドの拡張・改変:** 既に逐次であり、変更は挙動互換性を失うだけ。
- **(vi) bench rep の逐次打ち切り (v1 の (b) — v2 で棄却):** 3 レンズが独立に「採否不変」を
  反証した。(α) rep3 の CV は自由度 2 で、真の CV が閾値ちょうどでも 38.7% が γ=0.7 閾値以下に
  落ち誤停止する [L2-M3]。(β) 停止に使った同じ 3 rep の median を fitness に使う選択バイアス +
  MWU の標本数変更 (完全分離でも 3対3 は p≈0.081 で faster 判定不能、3対5 は p≈0.037) で
  compare の挙動が変わる [L3-M1/L2-S3]。(γ) bench-first §6(iii) 自身が「reps を減らした測定に
  本構成較正の floor を流用できない」と明記しており自己矛盾 [L2-M3]。(δ) rep 失敗時の有効
  標本数の未規定 [L3-M5/L1-M3]、v1 の「乖離時に γ を上げる」は緩める方向の逆向き修正 [L1-M2]。
  修正には floor 再較正・compare 投入条件の新設が要り、利得 (~7 秒/点、verify 支配下では
  総時間の数%) に対して機構増が規律 5 に反する。**将来、bench が支配項になる構成 (bench-first
  全面採用後の大規模 grid) が現実化したら、「screening 専用の低忠実 bench + 専用較正 floor」
  (bench-first §6(iii) の将来拡張) として別設計で再起票する** — 既存 floor の流用を前提と
  しない形でのみ。

## 11. 既知限界 (主張時に限定表現)

- (a) の p1 = 0.9 は事前固定の設計値で較正されていない — OC は p1 仮定への条件付き。
  same-boot 系列は α/β を名目値として主張できない (§4(a))。
- indeterminate 率は p が 0.5〜0.9 の中間帯で高い (R_max=8 でも残る) — headline 不可に倒れる
  fails-safe の対価であり、「逐次化すれば常に速い」ではない (§9 の尾)。
- 時間窓分離・順序無作為化は系列相関を減らすが消せない (同一機械・同一 binary)。残存相関は
  ledger の事後診断で可視化するのみで、補正はしない。
- (c) の較正は較正済み故障クラスへの条件付き — 未知の壊れ方への検出率は宣言範囲外。

## 12. レビュー (3 レンズ敵対レビュー、2026-07-15 — v1 に対して実施)

独立コンテキスト read-only (codex gpt-5.6-sol、reasoning high、worktree 内) で実施。原文 =
`output/insights/2026-07-15_sequential-stopping-review.md`。

- **正しさゲート・規律整合レンズ: adopt-with-conditions** (must 6 / should 3 / nit 1 /
  refuted 5)。最重要 = (c) の見逃し「上界」が上界でない (点推定・独立性・選択バイアス)、
  γ 逆向き修正、identity/durability/headline 配線の欠落。refuted に「verify 迂回経路」
  「D19 意味論の改変」「直接の時間報酬 reward hack」— 設計の核は実コード裏取りで生存。
- **統計・測定整合レンズ: reject** (must 6 / should 3 / nit 1 / refuted 5)。最重要 = SPRT 停止
  挙動の誤記述 (「不一致 2 で非再現」は一般に不成立) と OC の欠落、(b) の γ=0.7 が χ²(2) の
  裾を塞げない (38.7% 誤停止)、offline replay による γ 較正の不成立 (WAL は採用 round しか
  保存しない + 適応的過学習)、反実仮想 replay の恒真性 (F9 型)。**reject の主因は (b) と
  検証計画** — v2 は (b) を降格し検証計画を全面差し替えで応答。
- **実効性・実装整合レンズ: adopt-with-conditions** (must 5 / should 4 / nit 1 / refuted 5)。
  最重要 = (b) が MWU 標本数を変え採否不変が不成立、(a) の campaign-id/再開規約の欠落
  (terminal skip で 2 round 目が空振り)、軽量形の certified 同一性が variant_id では不成立。
  refuted に「seqstop ネストの後方互換破壊」「omit-when-off の実装不能」「§9 算術」— 生存。

**v2 の主応答:** (b) 降格 (§10-(vi))、SPRT の OC 明示 + R_max=8 (§4(a))、i.i.d. 対策と
ドリフト検知の降格 (§4(a)/§5)、identity・ledger・headline gate の規定 (§4(a)/§7)、(c) 前提の
厳密化 (§4(c))、検証計画の全面差し替え (§8)、効果見積もりの再定義 (§9)。

## 裁定欄 (ユーザー)

- 設計 v2 の採用 / 実装着手: **2026-07-27 に採用済み** (裁定記録 =
  `docs/archive/worklog-phase3-0726-12-0727-19.md`、[T-126])。
- 2026-07-29 の実装 preflight で、formal source eligibility、qualification hold、
  promotion authority の未見 blocker が判明した。採用を取り消さず、本 wave は実装せず
  **追加情報付き再裁定待ち**とする。正本 =
  `output/insights/2026-07-29_t126-implementation-preflight.md`。
