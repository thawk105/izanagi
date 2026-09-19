# auditor 監査報告 — mocc 温度述語 template 候補 3 本 (T-2773 n=1)

(fresh Claude `auditor` subagent の実応答の逐語。2026-09-19 23:41〜23:46 JST、Read/Grep/Glob のみ、81,862 token、tool 18 呼。親は期待 verdict・fitness・推論を渡していない。)

監査対象: `/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2773-mocc-template-wave2/wave-artifacts/n1/` の candidate-A1 / A2 / B (diff と適用後 .cc)、base `transaction-template-instr-seed.cc`、骨格 patch 2 本、軸定数 module `orchestrator/campaign/axis_mocc_temperature.py`、CCBench `external/ccbench/cc/mocc/include/common.hh`。`output/` 配下は一切開いていない (manifest の `verify_projection.source` が指す `output/env/pegasus/calibration/s3_mocc_template_proof.json` も未読、射影値のみ使用)。

共通の事実確認 (行単位):
- base の EVOLVE-BLOCK は seed 物理行 20〜27、hole は 23 行目 `return temp >= threshold;`。4 callsite は seed 318 / 485 / 596 / 1004 で全候補とも無改変 (grep で 4 候補分の行が一致)。
- 3 候補の .diff と .cc の内容整合は grep で確認 (A1 は hole 無改変 + validation 1 行削除、A2 / B は hole 1 行のみ差分)。SHA-256 は計算手段が無いため manifest の値をそのまま返す。

---

## 候補 A1

- **verdict: reject**
- **diff_digest:** `f8ec4b522d5acceac7fa743b92f1a6a5821bd9ddccde18a327200d41fbde5048`
- **violations:**
  1. **型 13 (marker 領域外への侵食) + 型 8 (write_set 被覆を狭める)**
     - 場所: `candidate-A1.diff` hunk `@@ -1051,7 +1051,6 @@`。seed 物理行 1054 (`#line 1026` 後の論理行 1028)、`TxExecutor::validation()` phase 1 の `lock((*itr).rcdptr_, true);` を削除。hole (seed 23 行目) は無改変で、差分は EVOLVE-BLOCK の外だけにある。
     - なぜ正しさを破るか: mocc は cold (temp < threshold) の record を read/update 時には施錠せず、validation phase 1 で write_set_ の非 INSERT 要素を全件 w_trylock する (no-wait)。この 1 行を消すと cold record への UPDATE / DELETE は一度も W_LOCKED にならずに writePhase で body を memcpy し tidword を publish する。結果: (a) 同一 cold record への並行 2 writer が両方 validation を通過して write-write 競合を無序で publish (lost update)、(b) cold reader の read validation `ldAcqCounter() == W_LOCKED && searchWriteSet == nullptr` (seed 1085〜1086) は writer を検出できず、writer の memcpy と reader の body 読みが tidword 変化前に交錯すれば torn read を受理する、(c) ループ内の `status_ == aborted` 判定は lock 失敗経路を失い実質不活性化。hot regime では update() (seed 485) の早期 `lock(tuple,true)` (upgrade 込み) が write lock を用意してしまうため、この欠落は hot arm では現象化しない (auditor.md 型 8 の「早期 hot lock が validation-time lockskip を隠す」の実例)。
     - verifier が見逃す理由: DSG は committed txn の C/R/W 行しか見ず、lock 獲得は trace されない。torn read は値が trace に載らず版 ID が整合すれば緑。競合が実際に cycle を成すまで二次的にしか現れず、hot regime / 1 thread では踏まない。一次防壁は `#if TRACE` の X 計装 (`not-locked-at-entry`、writePhase 入口の CLL_ writer 走査 + `W_LOCKED` 判定) だが、これは trace build のみで perf build では無音。A1 の `verify_projection` は `not_run` なので、この X が実際に赤になった記録は無い。
- **nits:** なし (正しさ違反で reject のため性能軸の評価はしない)。
- **proposed_tests:**
  1. **cold arm での X 赤化 (A1 そのものを mutation として使う):** base に A1 diff を当て、cold regime (全 record が temp < threshold になる threshold / per_xx_temp 設定) × thread ≥ 4 × 書込みを含む workload (U または W) で verify。期待: `x_reasons["not-locked-at-entry"] > 0`、`lock_coverage_violations > 0`、verdict `indeterminate`、certified false。driver は mutation_red_gate で「赤にならなければ計装が恒真」と機械判定する。
  2. **hot arm の偽緑を certify に使わない負例:** 同じ A1 を hot regime で走らせると X = 0 で緑になり得る (早期 lock による遮蔽)。driver は hot-only の緑を A1 系 (validation-lock 削除) の certified に昇格させない規則を持ち、cold arm 必須をテストに固定する。これは「型 4 空振り認証」の防止。
  3. **DiffQuarantine の positive control:** A1 diff はマーカー外 1 行削除なので DQ の行単位機械拒否で落ちるはず。A1 を DQ に投入して reject が出ることを記録する (DQ 自体が恒真化していないことの機械実証)。もし A1 が DQ を通過して私に届いたのなら、それは DQ の穴であり別途報告対象。
- **uncertainty:**
  - A1 が DQ を通過したのか、DQ 前の意図的な負例なのかは入力から分からない。
  - 上記 (b) torn read の機序は seed の read 経路 (needVerification 分岐、seed 341〜) の tidword 再検査タイミングから読んだ推論で、実走で再現した記録は持たない。X 計装は cold arm で確実に赤になるはずだが、それも未実走 (`not_run`)。

---

## 候補 A2

- **verdict: reject**
- **diff_digest:** `178c0092664c8b4bb87ed9b5cae68c3676b22584eea72b1c42259caf77328fe0`
- **violations:**
  1. **型 16 (読取契約違反) — 内容は型 3 (環境判別述語) + 型 2 (識別 alias / 素通り certified)**
     - 場所: `candidate-A2.diff` hunk `@@ -20,7 +20,7 @@`、seed 23 行目 hole を `return (FLAGS_clocks_per_us == 2100) && (temp >= threshold);` に置換。差分は hole 1 行に収まっている (型 13 ではない) が、`FLAGS_clocks_per_us` は軸定数 module の `SYNTAX_CONTRACT_FORBIDDEN` 第 1 項 `"FLAGS_"` に該当し、許可集合 (値渡しの temp / threshold + bool/整数定数) の外の global を読む。
     - なぜ正しさ (契約) を破るか: `FLAGS_clocks_per_us` は起動引数で与えるマシン依存の gflag (`external/ccbench/cc/mocc/include/common.hh:34` で既定 2100、README の実行例も `-clocks_per_us=2100`)。既定値のときは述語が stock と完全一致し (identity alias)、verify 環境が既定値で走れば stock の certified をそのまま継承する。一方 clocks_per_us ≠ 2100 で走る環境では述語が恒偽になり、read_internal / update / delete_record / construct_RLL の全 4 site で早期施錠が消え、mocc が「常に cold」の純 OCC に縮退する。つまり同じ diff が verify 環境と perf 環境で別プロトコルとして振る舞い得る、まさに verify 判別述語。construct_RLL でも `failed_verification_` 以外の RLL 登録が消え、abort 後の再試行の保護が別挙動になる (liveness 差)。
     - verifier が見逃す理由: 恒偽側でも validation phase 1 の write lock は残るため serializability は破れず G2 cycle は出ない。「hot/cold の判定がどちらの環境でどうなったか」は trace に一切載らない。差は abort 率・再試行挙動・throughput にしか出ず、それらは verifier の対象外で fitness 側に流れる。契約側 (D48 型の構文契約) が唯一の防壁。
- **nits:** なし。
- **proposed_tests:**
  1. **構文契約 gate の positive control:** hole 行の自由識別子集合が `{temp, threshold}` ⊆ に収まることを機械検査する gate に対し、A2 diff を負例として投入し必ず reject されることを記録する。追加 mutation: `return temp >= threshold && thid_ == 0;` (型 15 相当)、`return temp >= threshold || result_->local_commit_counts_ > 0;` (型 12 相当) も赤になることを対で登録し、B (`!(temp < threshold)`) が緑になることを正例とする。
  2. **flag 感度テスト (挙動側):** 同一 build の A2 を hot regime で `-clocks_per_us=2100` と `-clocks_per_us=2101` の 2 arm で走らせ、abort 要因分布 (ADD_ANALYSIS の `local_validation_failure_by_writelock_` 等、あるいは trace 上の abort 数の射影) が別物になることを示す。ただしこれは契約 gate の代替ではなく、gate が見逃した場合の第 2 層。性能値を判定に使わない形 (要因分布・abort 有無だけ) で設計する。
- **uncertainty:**
  - verify harness / perf harness が `clocks_per_us` をどう与えているか (既定 2100 か環境ごとに較正値か) は入力に無いため、実際に verify と perf で分岐したかは断定しない。分岐し得る構造であることが reject 理由。
  - A2 も DQ を通過したのか意図的負例なのか不明。行単位封じ込めだけなら DQ は通る (module docstring の通り DQ は物理行の封じ込めしか見ない)。

---

## 候補 B

- **verdict: pass**
- **diff_digest:** `9b042413a0299f31f0e48a229d0839bb2eec5cf813111079dc724fc76a61d459`
- **violations:** なし。
  - 差分は hole 1 行のみ (`return !(temp < threshold);`)。マーカー外・Options.cmake・4 callsite・CLL_/RLL_・validation・X/P 計装に差分なし。
  - 読取契約: 自由識別子は `temp` / `threshold` のみ、呼出し・副作用・global・FLAGS_・thid_・result_・コンテナ・乱数・時刻・TRACE 参照なし。
  - 論理等価: 両引数は `std::uint64_t` (全順序、NaN 無し) なので `!(temp < threshold)` ≡ `temp >= threshold`。stock 述語と全入力で一致し、hot/cold 分類・施錠被覆・RLL 登録は骨格と同一。fairness (型 15): key / thread / storage への依存なし。
  - 射影された 12 走 (hot / cold / default × t1 / t4 × W / U) はいずれも total_cycles 0、X・P 0、integrity clean。
- **nits:**
  1. B は stock と意味的に同一 (identity) なので、比較計測で差が出ても noise でしかない (型 6 の注意を消費側へ)。「速い variant」として採用する根拠にはならず、正直な帰結は tie。
  2. 骨格側 nit (候補の責任ではない): helper 全体が `#if MOCC_TEMP_PREDICATE` の中にあるため、hole の `#else` 枝 (seed 25 行目) は到達不能で、frozen block の一部としては冗長。
- **proposed_tests:**
  1. **hole 等価性の境界 unit test:** hole 行を抽出して harness に埋め込み、`temp ∈ {0, threshold-1, threshold, threshold+1, UINT64_MAX}` × `threshold ∈ {0, 1, 10, UINT64_MAX}` で stock `temp >= threshold` と一致することを検査。mutation 対照: hole を `temp > threshold` に変えると `temp == threshold` で赤になることを登録 (恒真でないことの実証)。driver は両方の結果 (正例 緑 / 変異 赤) を対で記録する。
  2. **abort > 0 の実行証拠 (型 4):** hot × t4 × W/U の arm で abort が 0 でないこと (= 述語が hot 側へ分岐し施錠競合を踏んだ証拠) を射影に含める。現在の射影は作業量を除外しているので、abort の有無だけを bool で載せる形が入力隔離と両立する。
- **uncertainty:**
  - 射影 12 走の run 名が `template_stock_*` で、B の `source_sha256` (`d0c8d6e5…`) と結び付いた走であるかは projection からは確認できない (`proof_template_sha256` は与えられているが source との束縛は私の入力外)。B と stock が同値なので結論は変わらないが、帰属は driver 側の束縛に依る。
  - 述語が実際に hot 側へ分岐した実行証拠 (abort > 0) は射影に含まれないため未確認。

---

## 全体の uncertainty / 注記

- SHA-256 は算出手段 (Bash) を持たないため、`diff_digest` は manifest.json の値を転記した。diff ↔ .cc の整合は内容 (grep) で確認したのみ。
- base (`transaction-template-instr-seed.cc` 53〜66 行) の `#if TRACE` 内 G2 witness コードは `std::getenv` を使う。これは候補 diff ではなく凍結された計装骨格の一部で、`#if TRACE` に閉じているため 3 候補の判定には影響させていないが、環境依存分岐が trace build に常駐している事実として記録する (規律 1 上の扱いは本監査の射程外)。
- `output/` 配下 (計測結果・WAL・fitness・proof JSON 原本) は一切開いていない。性能値・作業量は入力に含まれておらず、判定に使っていない。
- A1 / A2 が DQ を通過して届いたのか、意図的な負例 (positive control 用) なのかは入力から判別できない。前者なら DQ (A1) / 構文契約 gate (A2) の穴として別途報告が要る。
