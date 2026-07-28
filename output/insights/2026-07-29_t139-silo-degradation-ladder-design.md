# [T-139] 劣化版 Silo の梯子 — 設計台帳と生死確認 (dev-wave 2026-07-28〜29)

`authority: none` / `default_effect: no-state-change` — 本書は凍結スナップショット + ユーザー
裁定パッケージであり、可変状態の正本 (worklog 末尾・現行 phase doc) ではない。§7 の選択肢は
**未承認**である。

**位置づけ (必須の但し書き):** 既知の最適解への復帰は **recovery であって新規 CC の発明ではない**。
`docs/roadmap.md` §1 の研究目標に数えず、**能力測定 (ability probe) としてのみ**扱う。
この但し書きの出自は外部相談 (`output/insights/2026-07-27_external-consultation-scope-and-axes.md` §3)。
ここを曖昧にすると絶対規律 6 が警告する「謳うだけで発火しない保証」と同型の自己欺瞞になる。

**本書の範囲:** T-139 初回 wave の (1) 生死確認 (DW-G01) の設計と実測、(2) rung 候補の裁定台帳、
(3) 恒久実装 (後続 wave) の要件束、(4) ユーザー裁定パッケージ。**本 wave は恒久 patch・恒久
driver・pytest・decisions 新設を実装していない** (段 4 裁定で scope 縮小 — 段 3 レンズ B の
DW-G01/G04 指摘を採用)。逐語は `2026-07-29_t139-ladder-verbatim/` に凍結。

## 1. 梯子とは何か / 本 wave が確定させたこと

梯子 = 最適化済み Silo から段階的な「**構造的に遅いが serializable 不変**」の劣化版 (rung) を
用意し、AI がどこまで登り戻せるか (recovery) を連続量で測る能力の物差し。天井問題 (最適化済み
Silo は改善余地が薄く能力測定の解像度が足りない) への回答。既存 positive control
(`patches/` の broken-silo = 正しさを壊す赤 fixture) と異なり、rung は**正しさを保ったまま
性能だけを損なう緑の fixture** である。

本 wave が実測で確定させたのは、rung 候補 2 種について (a) trace build・t4 で certified
serializable かつ全 worker 生存、(b) trace-disabled・t48 の **2 workload × 5 reps の局所観測で
全標本が stock 未満** (方向シグナル)、という**生死確認そのもの**。(a) と (b) は build 構成・
thread 数が異なる別実測であり一体の確定事項ではない (t48 での per-worker liveness は未確認 —
恒久実装の obligation、§6)。梯子の本体 (恒久 rung patch 台帳・回復ループ接続・RF 実測) は
未実装であり、本書は「梯子が立つ」と主張しない。

## 2. rung と既存 patch 分類の関係

| 型 | 正しさ | 性能 | 用途 | 例 |
|---|---|---|---|---|
| broken-silo | **壊す** (意図的バグ) | — | verifier/assert の赤検出証明 | `broken-silo-norw-validation` |
| 合成 variant (D18 第4類) | 保つ | 改善を狙う | 評価中の正当な候補 | `silo-backoff-fixed` |
| 診断計器 (D20 第5類) | 保つ | 不変 (inert) | perf 帰属 | `BACKOFF_NOINLINE` |
| **劣化版 rung (新)** | **保つ** | **意図的に損なう** | ability probe (recovery の出発点) | 本書の候補 A/B |

置き場と型 (D16 第 6 類新設 vs D18 第 4 類の subtype `evaluation_role=ability_probe`) は
**未裁定** — §7 裁定パッケージ (a)。段 3 レンズ B は「改変の性質は D18 と同一 (正しい inert
patch)、rung は利用目的の違い」として subtype を推奨し、1 例からの恒久カテゴリ一般化は
DW-G03 と緊張すると指摘した。親も subtype 推奨に同意する。

## 3. 生死確認 (DW-G01) — 設計と結果

### 3.1 probe patch (使い捨て)

`t139-probe-degradation.patch` (67 行、`2026-07-29_t139-ladder-verbatim/` に凍結)。
`cc/silo/transaction.cc` のみ、裸マクロ 2 個 (CCBENCH_ 接頭辞なし = pipeline の genome flags
から定義不能)。追加行は全て `#if` ブロック内、`#else` に stock 逐語温存:

- **候補 A `IZANAGI_T139_PROBE_CAS_GATE`** — lockWriteSet の write-lock CAS 1 回を単一 global
  mutex (`std::lock_guard` スコープ) 経由に直列化。CAS は同一 lvalue・同一 1 回呼び出しで
  wrapper 関数化しない (段 3 レンズ A-3: 参照渡し `expected` の failure 更新を値渡し wrapper が
  壊す事故を構造回避)。
- **候補 B `IZANAGI_T139_PROBE_COMMIT_GATE`** — `commit()` の `writePhase()` 全体を単一 global
  mutex で直列化 (record lock を保持したまま待つ convoy を意図的に作る)。

**serializable 不変の論拠:** global mutex は scheduling 制約のみで、stock の全操作を無変更で
実行する — mutex 下の任意の実行は stock Silo の合法な実行である。deadlock は構成されない
(mutex 所有者は record lock を待たない。A は段 3 レンズ A-1 で「exact hunk なら永久 deadlock は
直ちに構成できない」と独立確認)。ただし hold-and-wait による**飢餓 (実質 livelock)** は
排除できない (レンズ A-2 = real) ため、per-worker liveness を probe の受理基準に入れた。

### 3.2 correctness leg (login node、動作確認扱い — 性能主張なし)

`t139_probe_correctness.py` (verbatim に凍結) を `patchharness.applied()` 下で実行。
trace build (`CCBENCH_TRACE=1`) → 高競合 t4 run (rmw/skew0.9/tuple50/maxope5/1s) →
`python3 -m orchestrator.verifier` → revert 後 pinned-clean 再 assert。結果
(`t139-probe-correctness.json`、2026-07-29):

- **A: all_pass** — certified SERIALIZABLE (rc=0)、per-worker commits = 63,533 / 67,307 /
  69,026 / 71,552 (全 worker > 0)、nm に probe シンボル出現 (活性証明)
- **B: all_pass** — certified SERIALIZABLE (rc=0)、per-worker commits = 60,209 / 67,403 /
  66,017 / 66,882 (全 worker > 0)、nm 活性証明
- 規律 1: 正しさ = trace build。gap leg (下記) は trace-disabled の別 build・別 run。
  nm で `izanagi_trace` シンボル 0 個を gap leg 側で確認 (観測者効果分離の witness)
- **証拠の適用範囲 (段 6 R1-4/R2-4):** この liveness は t4・extime 1s・trace build (かつ
  `CCBENCH_BACK_OFF` 未指定 = cmake 既定) での観測であり、gap leg の構成 (t48・trace-disabled・
  BACK_OFF=0) へは転移しない。provenance の post-hoc 束縛は
  `t139-probe-correctness.provenance.json` (JSON 本体に provenance field が無いのは恒久 driver
  要件へ — §6)

### 3.3 gap leg (Pegasus 計算ノード、job 873583)

`t139_probe_gap.sh` (verbatim に凍結)。同一計算ノードで stock / A / B を trace-disabled build
(certify と同じ configure flags: BACK_OFF=0, NO_WAIT=1, WAL=0) し、nm witness (probe シンボル =
stock 0 / A・B ≥1、izanagi_trace = 全 binary 0) を通過後、2 workload × interleaved 5 reps:

- W1 (高競合 write): rmw / skew 0.9 / tuple 10,000 / max_ope 10 / t48 / extime 3
- W2 (中競合 mixed): rratio 50 / skew 0.5 / tuple 100,000 / max_ope 10 / t48 / extime 3

**局所観測 (median tps、未較正 probe 値 — 受理不能 (non-acceptance)。性能比較・headline・
calibration・floor のいずれの入力にもしない):**

| workload | stock | 候補 A (CAS gate) | 候補 B (commit gate) |
|---|---|---|---|
| W1 高競合 write | 790,027 | 96,787 (stock 比 12.3%) | 657,927 (stock 比 83.3%) |
| W2 中競合 mixed | 10,581,616 | 1,038,968 (stock 比 9.8%) | 1,503,646 (stock 比 14.2%) |

一次資料 = `output/env/pegasus/t139-probe/0_873583.nqsv/` (summary.tsv、全 30 run の生ログ、
nm-witness、PBS 会計、**manifest.json = post-hoc provenance 束縛と回収不能項目の列挙**。
node = bnode011、compiler = system g++ 11.4、投入時 load average 0.75・外部 ycsb プロセスなし、
rep 内ばらつきは全系列 CV 2% 未満)。

**証拠の限界 (段 6 R1-1/R1-2/R1-3/R2-1/R2-2/R2-3/R2-9 を裁定して明記):**
- レコード数 (10k/100k) は**未較正** — 登録済み Pegasus calibration は近接 t48 YCSB で 1m を
  最小と裁定しており、本観測は cache-resident な負荷点の局所観測に留まる (規律 4 の較正は
  恒久 characterization の義務)
- rep 順序は固定 (stock→A→B) で order bias を排除していない。専有保証なし (Exclusive
  submit=OFF)、単独性検査は投入時 1 回のみ
- source identity は **post-hoc 束縛** (manifest.json の attestation window assumption を参照)。
  binary sha・compile argv・A/B の macro 別シンボル識別は回収不能 — 第三者再現可能な forensic
  証拠ではない
- 環境 CXXFLAGS の scrub は script が実装していない (段 4 裁定の宣言と実装が食い違った —
  DW-O12 に従い実態を正とする。恒久要件 §6)

**判定 (生死確認の結論 — 上記の限界の内側で):**
- **この 2 workload × 5 reps では、候補側の全 20 標本 (A 10 + B 10) がいずれも同 workload の
  stock 最小標本を下回る** (W1: max(B)=671,794 < min(stock)=771,337 / W2: max(B)=1,519,914 <
  min(stock)=10,446,945) — 方向シグナルとして生死は緑
- 段 3 レンズ B-4「候補 A は競合抑制でむしろ速くなる可能性が未排除」は、**この 2 セルでは
  観測されなかった** (存在主張なので一般反証はしない — 未測の workload では引き続き未排除)
- 候補 B の W1 比 83.3% は order bias・未較正の影響を受けやすい帯にあり provisional。W1 で
  劣化が小さいのは、abort/retry が支配的な高競合では直列化対象 (成功 commit の writePhase) の
  実行頻度自体が低いためという**仮説**を記す (機序帰属は恒久 characterization で)
- rung 1 の最終選定と恒久実装は §7 裁定パッケージ (b) に従う — 本観測はその設計入力であり
  受理証拠ではない

### 3.4 生死確認から得た一次知見

1. **probe patch は「マクロ OFF でも binary レベルで inert ではない」— そして binary 同一性
   witness はそれを正しく検出した (段 6 R1-7 で因果を訂正)。** 同一 build dir での逐次実測:
   未改変 build = `f9991d40…`、patch 適用 + マクロ OFF 再 build = `74c7879c…` (不一致)、
   revert 再 build = `f9991d40…` (完全復帰 = build は決定的)。**機序の具体的な候補がある**:
   probe patch の hunk 1 は行を追加し、下流の `ERR` マクロ (include/debug.hh — `NNN` 経由で
   `__FILE__`/`__LINE__` を fprintf の引数に埋め込む。transaction.cc:106 等で使用) の
   `__LINE__` 展開定数をシフトさせる。ソース上 `__LINE__` 展開値が変わることは確実だが、
   binary 差のどの section に現れるか・単独原因かは object/section diff 未取得のため確定して
   いない (仮説として記録)。いずれにせよ「witness が使えない」のではなく、**行追加型 patch の
   OFF 状態は真に stock と非同一** (異常時の診断出力の行番号が変わる)。帰結: (a) 恒久 rung patch を
   適用したまま stock を名乗る運用は binary 的に alias であり不可 — **stock は常に patch
   非適用 tree から build する** (probe もそうした)。(b) D93 の実 TU witness も full-TU
   preprocess を却下した設計であり `__LINE__` 型の同一性は保証しない — OFF-inert 主張の
   witness 設計は恒久 wave の未解決要件として残る。なお link 順序等の対立仮説は object/section
   diff までは取っていない (行番号仮説は ERR の実在で支持されるが、単独原因の証明ではない)。
2. **恒久 rung は通常 recovery pipeline に直結できない** (`recovery_measurement_eligibility=false`、
   dedicated-driver-only)。裸マクロは `source_digest.resolve()` の未知文脈 fails-closed に
   かかり (望ましい隔離)、さらに候補 A/B の `#include <mutex>` 追加は include 行 HEAD 固定の
   第 2 の fails-closed に当たる (段 3 レンズ A-13)。
3. **login node (pegasus02) は生死確認の全経路 (build→run→verifier) を回せる**。system
   g++ 11.4 + pinned gflags/glog の static build (certify §iv の作法)。compiler の記録は
   gap leg = job 内 `compiler.txt`、correctness leg = **post-hoc sidecar**
   (`t139-probe-correctness.provenance.json` — JSON 本体に field が無かったのは実装漏れ)。
   g++-13 (linux-baremetal 既定) との差は probe の結論 (方向) に影響しない**前提を置く**が、
   恒久 characterization は環境契約に従うこと。

## 4. rung 候補台帳 (段 2 起草 + 段 3 攻撃 + 段 4 裁定)

| 候補 | 内容 | 裁定 |
|---|---|---|
| A: CAS 中央 gate | write-lock CAS を global mutex 経由化 | **probe 採用**。レンズ B-4「競合抑制で速くなる可能性未排除 (backoff と同型の効果)」= real → gap leg で方向を実測してから rung 適格を判定 |
| B: writePhase 直列化 | commit の書き込み相を global mutex で直列化 | **probe 採用**。record lock 保持のまま待つ convoy で劣化の確度が高い。trace build では mutex 内に trace I/O が入るため trace/perf の転移に注意 (レンズ A-10) |
| C: 冗長 sort (同一 comparator 8 回) | — | **却下**: 小 write-set では gap が識別不能になりやすく (レンズ A-4)、「何が直列化されたか」の機序説明力も弱い |
| D: CAS 前固定 pause | — | **却下**: 人工遅延であり構造的資源競合ではない。ability probe として単純すぎる (段 2 自己申告 + レンズ A-4) |

## 5. recovery fraction (RF) — **provisional 定義** (規範化しない)

RF(X) = (S_X − S_degraded) / (S_stock − S_degraded)。S は「大きいほど良い」に正規化した
同一 metric・同一 env・同一 workload・trace-disabled 条件の統計量。分母が noise floor に対して
正に識別可能になるまで RF は未定義。clamp しない (RF<0 = さらに悪化、1 = stock 水準、>1 =
stock 超過 — ただし >1 を「recovery」と「新規改善」のどちらに帰属するかは未設計)。
trace-enabled 値から RF を計算してはならない。**paired 順序・反復数・欠測処理・識別可能性の
判定手続きが未定義のため規範化は後続 wave** (段 3 レンズ B-9 = real 採用)。

## 6. 恒久実装 (後続 wave) の要件束 — 段 3 で real 裁定した攻撃の反映

1. **activation witness は実 binary に束縛する** (nm シンボル + 実 compile argv の macro
   exactly-one 検査)。preprocess 射影だけの witness は空 stdout 偽緑・別 configure 乖離の
   穴がある (レンズ A-5/B-5)
2. **committed 実証 JSON は pytest で現物へ再束縛する** (patch SHA256・full pin・macro・
   compiler realpath/version・workload の再照合。stale evidence の偽緑を塞ぐ — レンズ A-9/B-7)
3. **変異事前登録は単一理由性を再設計する** (段 2 の M1–M5 は M3 二重理由・M4 到達不能・
   M5 誤帰属 — レンズ A-12 の表を出発点に)
4. **意味的空 patch (劣化が実質何もしない) の静的契約**: 単一 namespace-scope 非 thread_local
   mutex、lock_guard lifetime が対象操作を包含、bypass 経路なし (レンズ A-8)。経験的には
   gap leg の実測が最終防壁
5. **答えの露出対策** (レンズ B-6): rung の隣に stock 逐語 (#else) が置かれる構造は「コピーで
   RF=1」を許す。恒久設計では (a) 中立命名 (probe は `IZANAGI_T139_PROBE_*` を使用)、
   (b) 台帳 schema に `ability_probe: true` / `research_goal_eligible: false` を機械可読で
   持たせる、(c) coder/planner への射影規則で rung ソース・台帳を入力に含めない、を要件とする
6. **命名 stem の統一** (driver と JSON で同一限定 stem — レンズ B-11)、compiler の記録、
   環境契約 (`env_contract`) への整合
7. **provenance は in-job capture にする** (source HEAD + clean witness、依存 repo HEAD、
   binary sha256、実 compile argv、CMakeCache、実行 timestamp を成果物 JSON の field として
   取得時に書く。probe の post-hoc manifest は代替にならない — 段 6 R1-6/R2-1/R2-2)
8. **rung ごとに macro 固有シンボル** を出し分け、binary から候補 identity を nm で識別可能に
   する (probe は共通シンボル 1 個で A/B を区別できなかった — 段 6 R2-3)
9. **perf 構成 (trace-disabled・実測 thread 数) での per-worker liveness 検査** を
   characterization の受理基準に含める (trace build t4 の liveness は転移しない — 段 6
   R1-4/R2-4。CC-native な per-worker カウンタの利用可否から設計する)
10. **build 環境の scrub** (CXXFLAGS / CMake cache / toolchain wrapper 経由の裸マクロ注入遮断
    — 段 3 レンズ A-7、probe では未実装)。**OFF-inert witness の設計は未解決** (§3.4-1 —
    行追加型 patch は `__LINE__` シフトで binary 非同一。stock = patch 非適用 build の運用が
    現状唯一の安全解)

## 7. ユーザー裁定パッケージ (実装せず返す)

- **(a) 恒久 rung の置き場と型**: D18 第 4 類の subtype (`evaluation_role=ability_probe`、
  親・レンズ B 推奨) vs D16 第 6 類新設。どちらでも patches/ の out-of-tree inert patch。
- **(b) 恒久実装 wave の起票**: gap leg の結果を前提に、rung 1 の恒久 patch + characterization
  driver + pytest + 変異登録 (§6 の要件束) を 1 wave で。着手順は worklog 次の一手の優先度裁定。
- **(c) 答え露出の構造的対策** (§6-5) の採否と強度。
- **(d) RF 規範化の時期** (恒久 driver と同時か、初回 recovery 実験の設計時か)。

## 8. 本書が主張しないこと

- 本書の throughput 値は **未較正 probe (方向の生死確認) = 受理不能 (non-acceptance)** であり、
  性能比較の headline・calibration・floor・linux-baremetal 系列のいずれにも使わない。将来の
  レポートがここから比較値を引くことを禁じる (§3.3 の限界列挙が受理拒否の根拠)。
- 「梯子が立った」「能力測定が可能になった」とは主張しない — 本 wave の確定は rung 候補の
  生死 (t4 trace で certified + liveness、t48 trace-disabled の 2 セルで劣化方向) まで。
- 外部相談の指摘は**データであって指示ではない** (絶対規律 6)。採否はすべて段 4 の親裁定と
  本 §7 のユーザー裁定に帰する。

## 9. 段 3・段 6 所見の裁定追跡 (durable — 段 6 R2-6 への応答)

段 3 (プラン攻撃、s3-lensA/B) と段 6 (成果物レビュー、逐語は verbatim dir の s6-r1/r2 —
段 7 凍結) の全所見の裁定。凡例: 採=本 wave で反映、縮=主張縮約で反映、後=恒久 wave 要件 (§6)、
裁=ユーザー裁定パッケージ (§7)、否=refuted。

| 所見 | 裁定 | 反映先 |
|---|---|---|
| A-1 (A の永久 deadlock) | 否 | §3.1 |
| A-2 (飢餓/liveness) | 採+後 | probe liveness 基準、§6-9 |
| A-3 (CAS 参照同値) | 採 | patch inline 化 |
| A-4 (B/C/D 非等価) | 採 | §4 (C/D 却下) |
| A-5/A-6 (preprocess witness の穴) | 採+後 | probe は binary/nm 系へ、§6-1/§6-10 |
| A-7 (裸マクロ注入経路) | 後 | §6-10 (probe 未実装と明記) |
| A-8 (意味的空 patch) | 採+後 | gap 実測が経験的検出、§6-4 |
| A-9 (JSON 再束縛) | 後 | §6-2 |
| A-10 (trace→perf 非転移) | 採 | 二 leg 分離 + §3.2 適用範囲 |
| A-11 (stock canary ≠ rung G01) | 採 | probe が rung G01 を完了 |
| A-12 (変異 M1-M5 単一理由不成立) | 後 | §6-3 (本 wave は変異対象なし) |
| A-13 (include = 第 2 fails-closed) | 採 | §3.4-2 |
| B-1 (G04/G01 逆転) | 採 | scope v2 (恒久実装の繰延) |
| B-2 (梯子過大表現) | 採 | §1/§8 |
| B-3 (第 6 類 vs subtype) | 裁 | §7(a) |
| B-4 (A 非劣化の可能性) | 縮 | §3.3 (2 セルで不観測、一般反証せず) |
| B-5 (witness-binary 未結線) | 採+後 | nm witness、§6-1 |
| B-6 (答えの露出) | 採+後 | 中立命名、§6-5 |
| B-7 (JSON pytest 再束縛) | 後 | §6-2 |
| B-8 (変異の自己言及) | 後 | §6-3 |
| B-9 (RF 規範化不足) | 採 | §5 provisional |
| B-10 (D94 衝突) | 採 | 本 wave D 新設なし・次空きは D95 |
| B-11 (命名 stem) | 後 | §6-6 |
| B-12 (README 第 5 類欠落) | 採 | patches/README 行追記 |
| B-13 (予算非衝突) | 否(攻撃不成立) | — |
| R1-1/R2-1 (stock pinned-clean 未証明) | 縮+後 | §3.3 限界 + manifest、§6-7 |
| R1-2/R2-9 (順序 bias・B-4 反証過大) | 縮 | §3.3 |
| R1-3 (規律 4 未較正) | 縮+後 | §3.3 限界 |
| R1-4/R2-4 (liveness 適用範囲) | 縮+後 | §1/§3.2、§6-9 |
| R1-5 (headline 経路) | 縮 | §3.3 見出し・§8 禁止文 |
| R1-6/R2-2 (JSON/job 束縛) | 採+後 | sidecar + manifest、§6-7 |
| R1-7 (inert 因果誤り) | 採 | §3.4-1 書換 |
| R1-8 (README 行の既成事実化) | 採 | 行を witness 条件付きに修正 |
| R1-9/R1-10/R1-11/R1-12 | 否 (攻撃不成立。R1-11 の B 表記 nit は採) | §3.2 |
| R2-3 (A/B 識別・scrub 未実装) | 採+後 | manifest 明記、§6-8/§6-10 |
| R2-5 (authority header・sha 表) | 採 | 本書冒頭・verbatim README |
| R2-6 (裁定追跡) | 採 | 本節 |
| R2-7 (射影 gate) | 後 | §6-5 |
| R2-8 (namespace 曖昧) | 採 | t139-probe/README.md 新設 |
| R2-10 (日付束縛) | 採 | sidecar/manifest の timestamp |
| R2-11 | 否 (攻撃不成立) | — |

焦点再レビュー (round 1、逐語 = verbatim `s6-focus.md`) は 20/23 closed・R2-7 partial (後続
要件として受理)・regressed 3。round 2 fix: (1) 標本数「全 30」→「候補 20 標本が同 workload の
stock 最小を下回る」(summary.tsv の min/max で親が再計算検証)、(2) `.rodata` 断定 → `__LINE__`
シフト確実 + section/単独原因は未確定の仮説に緩和 (debug.hh 実読で検証)、(3) verbatim README を
64 桁 hash + `handoff-final.md` 実体化で是正 (sha256sum 再計算で検証)。3 件とも機械検証可能な
是正のため、親の再計算検証をもって closed と裁定 (DW-O16 の 3 巡上限内、round 2 で終了)。
