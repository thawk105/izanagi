# CCBench の修正 5 本と正しさ関門の記録を F の上に束ねた tip `izanagi-fix-bundle` = `90355098` を作った ([T-2917]・[T-2919]・[T-2945]、D2322 項 4・6) — 上流 CI 相当 2 本は緑、D297 の合成比較 A→B′ は GCC 11・12 とも pass、Silo・MOCC・Cicada の正しさを各 1 走で取り直し、D297 検査器に Cicada の値 macro 4 個の組合せ文脈を足した。push はしていない (人間の手番)

authority: none
default_effect: no-state-change

- 日付: 2026-09-30 着手 (計算と記録は 2026-10-01。00:4x〜09:44 JST は利用上限による一旦停止)
- wave: `dev-wave-ccbench-fix-bundle` (branch `worktree-dev-wave-ccbench-fix-bundle`)。着手時 local main `908741c6fe1db954c824857ccc2086fe16856d45` (開始 gate rc=0、`verbatim/startup-gate.log`)
- 依頼: `/work/1/SFC/tanab/tmp/gen-opt-2026-09-29/md_16.txt` と同 dir の `common-5.txt` (repo の外)。裁定: D2322 項 4 (D297 は例外を足さず 3 条件で認める)・項 6 (束ねた tip は改めて push を依頼)、D2305 項 6、D297、D2293、D2304、D2308、D1464
- job dir (使い捨て script・生 log・Codex receipt・bundle・計算の全出力): `/work/SFC/tanab/tmp/ccbench-fix-bundle-2026-09-30/` (= `/work/1/SFC/tanab/tmp/...`)。以下 `$J`
- 段の記録: `verbatim/` (brief・plan・相談 2 本・段 4 裁定と erratum E1〜E5・レビュー 2 本・段 6 裁定・焦点再レビュー)

## 0. 結論

1. **束ねた branch:** CCBench の新しい local branch `izanagi-fix-bundle` = **`9035509829f005aaaddf44fa5ca431851c2ecdac`** (tree `27ef1f5bec07e87e5f4207bf237c65eb21728aeb`)。F `25898d00` から次の順に `--no-ff` merge した 4 commit (§1)。文面の衝突は 0 件、merge は自前のコードを足していない。bundle = `$J/fix-bundle.bundle` (sha256 `49d2e5bd31d1cc5d5e93553c2726d504961aa0599d43bc09ac0f29f6a1ca9295`)。gitlink・`CCBENCH_FULL_SHA`・`CURRENT_PIN` は動かしていない (md_15 と後続 wave の範囲)。
2. **上流 CI 相当 (§2):** format は login の clang-format 14.0.0 と CI image `:latest` の 14.0.6 で 213 file・rc=0。CI image `:ci` の全 protocol build は configure・build rc=0、実行 file 34、CCBench 本体の warning・error 0、TRACE=0 の `ycsb_*.exe` 7 本で trace 記号なし (request 40084.nqsv、Elapse 35 秒)。GitHub Actions の結果ではない。
3. **D2322 項 4 の条件 (2)、D297 (§3):** 合成 A (親 F、tree = F に Silo・MOCC・Cicada の各修正 tip の F からの diff を `git apply` で独立に当てたもの) → B′ (親 A、tree = 束ねた tip の tree) を、GCC 11.4 と GCC 12.3 の別 job で検査器に掛け、**両方 `result: pass`**。差分 path は期待の 3 本 (`cc/silo/transaction.cc`・`include/trace.hh`・`include/ycsb.hh`) と完全一致。header 分岐は選定 configure 65、consumer entry の予定 1,820 = 実行 1,820、重複を除いた比較 278 件がすべて一致。**読み:** 束ねた tip の TRACE=0 正規化前処理出力と include 活性は、選定した macro 文脈で「F + 各修正の diff」と一致する。merge の解決と正しさ関門の記録 (U1) は TRACE=0 に何も足していない。**主張しないこと:** この比較の両側には同じ修正の差分が入っているので、修正の hunk そのもの (特に Cicada の 3 本) を D297 が認証したのではない。修正の hunk は §3.2 の manifest で F と各修正 tip から独立に固定した。
4. **条件 (3)、修正後の build での正しさの取り直し (§4):** Silo = 起動器 v3 型 (TRACE=1、W-rmw・W-blind、`--require-gate-witness`、判定器の意味の版 2) で両 workload とも serializable・certified、関門の違反 0 (request 40086.nqsv)。MOCC = TRACE=1 の 1 走で巡回 0・integrity 数値項目 0・C 行数 = commit 数 (40085.nqsv)。Cicada = **promotion 無効の INLINE_VERSION_OPT=1 genome** の YCSB R 1 走で巡回 0・integrity 数値項目 0・C 行数 = commit 数・READ_WTS_MISMATCH 0、判定は上限の indeterminate (40137.nqsv)。各 1 走であり、Cicada の job 全体の rc は 1 (同居させた登録確認側の script 不具合、§4.3)。
5. **promotion 有効の Cicada の正しさは、現行の計装では判定できない (§5)。** repo の計装 patch は D1464 (promotion の内部 write を workload の write と区別して verifier に見せる) を満たせないので promotion × TRACE を `#error` で禁じている。前例 2 wave が使った repo 外の診断 patch は、この `#error` 1 行を消しただけで D1464 を満たさない。本 wave はこの patch の上の判定を合格に数えず、genome を選び直した。前例 2 wave の記録は書き換えず、本資料と台帳への追記で扱う。
6. **D297 検査器の拡張 (§6):** `tools/check_trace0_preprocess_identity.py` は Cicada の `.cc` を、old/new 各 commit の Cicada の CMake 供給値を確かめたうえで、値 macro 4 個 (INLINE_VERSION_OPT・INLINE_VERSION_PROMOTION・SINGLE_EXEC・WORKER1_INSERT_DELAY_RPHASE) の 16 組合せ × 既存 overlay 2 = 32 文脈で比べる。従来の「未知マクロ」停止は解消した。名前を既知集合に足すだけの形はとらない (緩和ではなく拡張)。`source_digest.py` の CONTEXT_MACROS と digest の bytes は変えていない。テスト 337 件緑、変異 7 件すべて期待どおり (正例 1 生存・負例 6 KILLED)、実データの登録確認も合格 (40590.nqsv)。
7. **計算:** 12 request、Elapse 合計 7,271 秒 ≈ 2.02 node 時間。2 node 時間を跨ぐ見積り (1.99〜2.21) は land 調整役の GO (ユーザー委任、common-5 §4) で投入した。D297 は検査器に分割機能が無く、1 本 約 55 分で 5 分程度への分割 (common-5 §4) はできなかった (限界)。
8. **push の依頼 (§7):** 人間の手番。依頼文と完全 SHA は §7。

## 1. 束ね方

| 順 | merge commit | 第 2 親 | 中身 |
|---|---|---|---|
| 1 | `6ea3cafca45f74a69ef048a75ddde4f7705a2837` | Silo `dbac49b6dc2d2ab9211b1ec0a41e44fa21245f43` | 取引内の値の修正 + `#line` +3 (`izanagi-silo-intra-txn-fix`) |
| 2 | `22935fc0f2cbc7ca789f8f1a2650c1e6e9db40d8` | MOCC X `f4a5169ede52630d9357444e3412ffe9aed7c78f` | validation の版の読み直し (`izanagi-mocc-validation-fix`) |
| 3 | `13708dd193570ee9f73da85b5983e374a7f14907` | Cicada `16ad3eb8ca5f7bb3aea789bff99958e2192f6714` | `izanagi-cicada-promotion-uaf-fix`。履歴に build 修正 G `eb93423b` と gc_records 修正 `81fc4a84` (の merge `aa8e36f1`) を含むので、Cicada の 3 branch を元の commit のまま取り込む |
| 4 | `9035509829f005aaaddf44fa5ca431851c2ecdac` | U1 `dcb9a41f3e538744298b0e5c42dc37349bac114e` | 正しさ関門の記録 (`izanagi-gate-witness-trace`、YCSB の手順列 Q 行と刻印 V 行) |

- 各 tip は、wave 木の submodule で主 checkout の submodule git dir から取り直し、GitHub へ HTTPS の `ls-remote` で照合した (U1 は local のみ)。push 済み 5 本の GitHub check-runs は build・format-check とも success (promotion-uaf は 2026-09-30T13:00Z)。[T-2959] の branch は push・CI 緑で確定していたので含めた。
- merge は job dir の使い捨て clone (`$J/cc-bundle`) で行い、wave 木の submodule は動かしていない (`evidence/mk-bundle.log`)。作者は先行 commit と同じ `thawk105`、message は英語で trailer = Claude manager (コードを足さない merge なので Codex author は無い)。
- 検査 (同 log): F と 7 本 (5 tip + G・gc) がすべて祖先、F→tip の差分 path は 8 本 (`cc/cicada/include/{cicada_op_element,transaction,tuple}.hh`・`cc/cicada/transaction.cc`・`cc/mocc/transaction.cc`・`cc/silo/transaction.cc`・`include/{trace,ycsb}.hh`)、Silo 以外の 7 path の blob は対応する修正 tip と同一。
- **`#line` の整合:** Silo の `#line` 6 本 (365・381・638・661・682・703) は Silo 修正 tip と同一。U1 が `cc/silo/transaction.cc` に足した行は writePhase の `#if TRACE` 枝の内側だけで、直後の絶対値 `#line` が打ち消す構造なので、TRACE=0 の論理行番号は Silo 修正のまま。§3 の D297 (`.cc` の Silo 16 文脈と header 分岐の完全展開) でも確かめた。

## 2. 上流 CI 相当

- **format** (login、`$J/format-ci.sh`、`evidence/format-ci.log`): 束ねた tip の checkout で `git ls-files -- cc include common | grep -E '\.(cc|hh|cpp)$'` の 213 file に `clang-format --dry-run --Werror`。login の 14.0.0 と CI image `:latest` (sha256 `64132a2f…`) の 14.0.6 の両方で rc=0。
- **build** (request 40084.nqsv、bnode013、Elapse 35 秒、`evidence/jobs/ci.report.json`): CI image `:ci` (sif sha256 `cb8cd1c36d57f7c32e6d8a87c733fd55dd7f63d53fb1931505391828b606adc8`、GCC 13.3.0) で CI と同じ `-DCMAKE_BUILD_TYPE=Release -DENABLE_SANITIZER=OFF` の全 protocol build。configure rc=0、build rc=0、実行 file 34、CCBench 本体の warning 0・error 0 (第三者の warning 0、それ以外の warning 12 は configure 等)、TRACE=0 の `ycsb_*.exe` 7 本 (cicada・ermia・mocc・oze・si・silo・tictoc) の trace 記号検査がすべて合格。`acceptance.passed = true`。

## 3. D2322 項 4 の条件 (1)・(2)

### 3.1 条件 (1)
C → F は D2293 で GCC 11.4・12.3 とも pass 済み。本 wave では取り直していない。

### 3.2 修正 hunk の manifest (merge と独立)
`evidence/fix-hunk-manifest.json` は F と各修正 tip の差分から作った (`$J/scripts-v6/mk_synth.sh`)。Silo 1 path・6 hunk (read の順序入替、update の値の置換、`#line` +3 の 4 本)、MOCC 1 path・1 hunk (validation)、Cicada 4 path・9 hunk (うち header 3 path)。MOCC の F→X の D297 不合格 (意図した修理差分) は D2304、Silo の「pin + 修正 → 新 tip」の D297 (b) pass は `output/insights/2026-09-30/silo-intra-txn-fix-line/README.md` §2 に記録済み。

### 3.3 合成 A→B′ の D297
- 構成 (`$J/synth/`、`evidence/synth.oids`): A = `ced2ce41f83bd72083483d6499be9dd8e19f7682` (親 F、tree = F + Silo F→`dbac49b6` + MOCC F→`f4a5169e` + Cicada F→`16ad3eb8` の diff を `git apply --check` → `git apply`、作者・日時固定)、B′ = `439b02f9283478d262a704df9296d0ec279d1fa0` (親 A、tree = 束ねた tip の tree `27ef1f5b`)。Cicada の 3 branch は祖先が重なるので、F→promotion-uaf tip の集約差分を 1 回当てた。
- 照合 (login の親実走と job 内の両方、`$J/scripts-v6/verify_synth.sh`): A の修正対象 path の blob = 修正 bundle 側の対応 tip の blob、それ以外 = F、両 bundle の F が同一、B′^=A・A^=F・B′ の tree = 束ねた tip の tree、A→B′ の差分 path = 期待の 3 本。負例 (synth.oids の A を F に差し替え) は `synth parent mismatch` で rc=2 (親実走)。
- 検査器: wave の commit `d9897f32c` の `tools/check_trace0_preprocess_identity.py` (§6 の変更を含む。この比較に Cicada の path は入らない)、header 4 引数、`--expect-paths cc/silo/transaction.cc include/trace.hh include/ycsb.hh`。

| compiler | request | Elapse | 結果 |
|---|---|---:|---|
| GCC 11.4.0 | 40083.nqsv | 3,284 s | rc=0・`result: pass`。`.cc` Silo 16/16 文脈一致。header: configure 65、consumer 予定 1,820 = 実行 1,820、比較 278 件一致。gitlink `third_party/shirakami` (`fb14e659`) 旧新一致 |
| GCC 12.3.0 | 40087.nqsv | 3,300 s | 同上 (すべて同じ件数で pass) |

- 判定は「rc=0 かつ report の `result == pass`」(`evidence/jobs/d297-gcc1{1,2}.decision.json`)。report 全文は `evidence/jobs/d297-gcc1{1,2}.report.json`。
- 保証の名前は D297 のとおり「選定した macro context における TRACE=0 正規化 preprocess 出力の同一性、および include 活性の同一性」で、翻訳単位の同一性は名乗らない。header の consumer は silo・mocc・tictoc・cicada の YCSB・TPC-C 系。si・ermia・oze の YCSB は検査器の選定外で、§2 の trace 記号検査だけが見ている。

## 4. 条件 (3)、正しさの取り直し

共通: 束ねた bundle を job 内で `verify_inputs.sh` で照合 (tip・tree・4 merge の親列・祖先) してから clone、TRACE=1・GCC 11・Release、`compile_commands.json` の `-D` を期待値と照合。判定器は wave 木 (`d9897f32c`) の `python -m orchestrator.verifier`、`--expected-commits` は走行の commit 数。事前登録は段 4 裁定 (`verbatim/s4-ruling.md`) で結果を見る前に固定し、script に埋めた。

### 4.1 Silo (request 40086.nqsv、bnode018、Elapse 58 秒、`evidence/jobs/silo.result.json`)

cell: 200 record・zipf 0.9・rratio 50・max_ope 5・thread 4・1 秒。patch なし (U1 の記録は束ねた tip に入っている)。判定器に `--require-gate-witness --protocol silo`。

| workload | commit = C 行 | 巡回 | D1a/D1b1/D1b2/D1c | D2a | D2b (i)/(ii) | 到達不能 | D5 | 判定 |
|---|---:|---:|---|---:|---|---:|---|---|
| W-rmw | 197,785 | 0 | 0/0/0/0 | 0 | 0/0 | 0 | pass | **serializable・certified** |
| W-blind | 228,282 | 0 | 0/0/0/0 | 0 | 0/0 | 0 | pass | **serializable・certified** |

発生条件 (W-blind の例): 自分の書きの後の読みを含む取引 17,582、同じ key を 2 度書く取引 17,520、書きのある取引 221,243、検査した外部読み 551,340 (いずれも ≥1)。

### 4.2 MOCC (request 40085.nqsv、bnode016、Elapse 66 秒、`evidence/jobs/mocc.result.json`)

cell: 48 thread・1,000,000 record・rratio 95・rmw 0・max_ope 10・zipf 0.9・**1 秒** (前例 3 秒を所要のため縮めた)。commit = C 行 1,557,661、巡回 0、integrity 数値項目すべて 0。判定器 `--protocol mocc`。主張はこの 1 走の観測に限り、修理 X の経路 (版の読み直しによる abort) の発火は数えていない (先例の 112 走の代わりではない)。

### 4.3 Cicada (3 回投入、3 回目で正しさ合格)

| 回 | request | Elapse | genome | 計装 | 結果 | 原因 |
|---|---|---:|---|---|---|---|
| 1 | 40088.nqsv | 32 s | OPT=1・PROMO=1 | なし | 不合格 (`trace files missing`) | Cicada の trace は izanagi の `patches/instr-cicada-trace.patch` で入るのに当てていなかった (段 4 の指定の欠落、erratum E2) |
| 2 | 40116.nqsv | 31 s | OPT=1・PROMO=1 | repo の計装 (sha256 `f4db2abd…`) | 不合格 (build: `#error "Cicada TRACE cannot observe writes from inline version promotion"`、`evidence/jobs/cicada-retry-1.build.stderr.txt`) | repo の計装は promotion × TRACE を禁じる (D1464)。前例の patch 列を読み落とした (E3) |
| 3 | 40137.nqsv | 53 s | **OPT=1・PROMO=0** (他 0) | repo の計装 | **正しさは合格**、job rc=1 | rc=1 は同居させた登録確認の合成 patch の生成不具合 (下記) |

- 3 回目の正しさ (`evidence/jobs/cicada-retry-2.result.json` の `runs.cicada`): cell YCSB R (200 record・zipf 0.9・rratio 90・max_ope 4・thread 4・1 秒)、commit = C 行 1,238,570、巡回 0、integrity 数値項目すべて 0、READ_WTS_MISMATCH 0、判定 indeterminate (Cicada の判定器の上限。certified は名乗らない)、`accepted = true`。compile の `-D` は INLINE_VERSION_OPT=1・INLINE_VERSION_PROMOTION=0・TRACE=1 で照合一致。
- **記録上の注意 (land 調整役の指示どおり 3 点を並べる):** (a) job 全体の rc は 1 で、正しさの `runs` と登録確認の `errors` は result.json に別々に残っている。(b) 走行は 1 workload・1 走だけ。(c) promotion 有効の経路は判定の対象外 (§5、D1464)。
- 通る経路: build 修正 G の非既定 build (OPT=1)、insert の初期化修正 (修理 4、OPT=1 の insert 経路)。**通らない経路:** promotion の修理 1・2、gc_records・scan・abort の修理 (TPC-C を回していない)。
- 3 回目の rc=1 の原因: 登録確認の合成 commit (i) を作るとき、job script が `git diff` の出力を末尾の空白を削る関数で読み、最後の hunk の末尾の文脈行 (空白 1 字の行) が消えて `corrupt patch at line 85` になった。script の不具合で、判定器・検査器・束ねた tip とは無関係。2 回目と 3 回目の間に land 調整役へ「FAIL-2」で報告し、4 回目は投げずに相談した (調整役の判断: 正しさはこの結果で充足と記録してよい、登録確認は単独 job で 1 回だけ)。

## 5. promotion 有効の Cicada と D1464

- repo の `patches/instr-cicada-trace.patch` (md_3、commit `2eb59bec`) は INLINE_VERSION_OPT ∧ INLINE_VERSION_PROMOTION ∧ TRACE を `#error` で止める。根拠は D1464「Cicada の内部の版昇格が作る同値 body への write は、workload の write でなく内部 maintenance として区別して verifier に見せる」。計装の記録は commit 時の `write_set_` 全体を W 行に出すので、promotion が `write_set_` に積む要素も workload の W 行として区別なく出てしまう。
- 前例の診断 patch `/work/SFC/tanab/tmp/ccbench-cicada-bugfix-20260929/scripts/instr-cicada-trace-promotion-diag.patch` (sha256 `feaab9b6a98baf4be13cdb93e4cc7478ae5eeaf41aa3830a247dd5bfd8c1b3a3`、repo 外) は、repo の計装からこの `#error` 1 行を消しただけで、記録の仕組みは同じ。promotion の write は「見えないまま」ではないが、D1464 の区別を満たさない。本 wave は land 調整役の確認を受け、この patch の上の判定を条件 (3) の合格に数えないことにし、genome を promotion 無効へ替えた (erratum E4・E5)。
- **前例 2 wave での使われ方 (記録は書き換えず、ここに追記として残す):**
  - `output/insights/2026-09-29/ccbench-cicada-bugfix/README.md` §4.3: promotion 有効 genome の 1 設定 (BACK_OFF=0・REUSE_VERSION=1・WRITE_LATEST_ONLY=0) の YCSB K・W・R・P を各 1 走。K 巡回 4・R 巡回 327 を根拠に promotion 8 genome を**失格**にした (W・P の巡回 0 は合格に数えていない。同資料も「標準の計器で保証された結果ではない」と明記)。失格は安全側の判断で、巡回の原因は後続 wave が読み取り専用 tx の promotion の欠陥と実証しているので結論は変わらないが、根拠の計装は D1464 非準拠である。
  - `output/insights/2026-09-30/ccbench-cicada-promotion-uaf-fix/README.md` §0 項 6・§6・§7: 修理後 tip の promotion 有効 8 genome × YCSB K・W・R・P (32 走行) と TPC-C M・R2 (16 走行) の「巡回 0 (上限 indeterminate)」を修理の確認として数え、正例 (修理 1 を外す壊し patch で R 巡回 308) も示した。いずれも D1464 非準拠の計装の上の判定で、**promotion 有効 genome の正しさは、現行の計装では確認されていない**と読むべきである。
- 恒久対応は台帳の新規項目 (D1464 に沿って promotion の write を内部処理として印を付ける計装と、それを読む verifier の拡張、上の 2 wave の promotion genome の判定の再確認) と failures の新規エントリで扱う (spool fragment)。

## 6. D297 検査器の Cicada 登録

- 変更 (wave commit `d9897f32c9aacc57959d24d8909a59777b6f49c4`、Codex author、`tools/check_trace0_preprocess_identity.py`・`orchestrator/tests/test_check_trace0_preprocess_identity.py`): `cc/cicada/` 配下の `.cc` だけ、`Genome("cicada", {})` と `_head_defines` で old/new 各 commit の Cicada の CMake 供給値を得て、両側の供給集合の一致と 4 macro の値が 0/1 であることを確かめ、4 値の直積 16 組合せ × `_context_overlays()` 2 = 32 文脈で正規化前処理出力と include 活性を比べる。既定値 (OPT=0・PROMO=1・SINGLE_EXEC=0・DELAY=0) を含む。期待件数は path ごとに列挙元から導出し、実比較数と食い違えば拒否。report に path 別の期待件数 `expected_context_count_by_path` と file 別の期待数・実数を足し、Cicada の文脈タグと不一致の例外文に値の組合せを入れた。他の path の文脈 (SILO_SPACE 8 genome × overlay 2 = 16)・文言・既存 key は不変。未登録の macro は従来どおり「未知マクロ」で止まる。
- **D2322 項 4 の文言との差:** 裁定は「cicada の文脈 macro を検査器の既知一覧 (CONTEXT_MACROS) へ登録する」と書く。`orchestrator/campaign/source_digest.py` の CONTEXT_MACROS は TU 内 `#define` で注入される macro の素/define 2 文脈用で、2 個以上は停止する設計であり、ここへ足すと digest の bytes (src token と凍結の閉包) が変わる。Cicada の 4 macro は CMake が `-D` で値を与える macro なので、登録は検査器の中で値の組合せを列挙する形にした (段 2 plan・段 3 相談・段 4 裁定 (P2))。目的 (未知マクロ停止を解消し、Cicada の `.cc` の TRACE=0 差分を機械判定できるようにする、緩和しない) は同じ。決定は decisions fragment に記録した。
- テスト (追加): Cicada の `#if TRACE` 内だけの変更は pass で 32 文脈・define 集合が 16 × 2 と厳密一致・既定値の組合せを含む、4 macro それぞれ「既定値と反対の値でだけ生きる枝」の TRACE=0 変更は拒否、`NEW_CICADA_MACRO` は未知マクロで拒否、include 活性の不一致の例外文に値の組合せが出る、overlay を 1 つ落とす注入で件数不一致の拒否。焦点テスト 4 file (同 file・`test_check_trace0_header_rule.py`・`test_mocc_trace_job_contract.py`・`test_mocc_trace_pair.py`) が 337 passed。
- **変異** (`tools/mutation_harness.py`、独立 clone `main = d9897f32c`、`evidence/mutation-*.json`): probe (40048.nqsv、192 s、baseline 緑) で赤 node を観測し、その完全集合を期待にした本走 (40063.nqsv、191 s、spec sha256 `d7cdb1d8…`) で 7/7 が期待どおり。

| 変異 | 内容 | 結果 | 主な kill (受理集合の変化) |
|---|---|---|---|
| M0 | コメントだけ | SURVIVED (期待どおり) | — |
| M1 | 列挙を既定値 1 組合せに縮める | KILLED | 反既定値の負例 4 本が通ってしまう |
| M2 | 値を上書きせず名前だけ既知 | KILLED | 同上 + define 集合の厳密一致 |
| M3 | WORKER1_INSERT_DELAY_RPHASE を既定値に固定 | KILLED | その macro の負例と define 集合 |
| M4 | Cicada 判定を外し Silo 文脈で比べる | KILLED | Cicada 正例が未知マクロで止まる |
| M5 | 未登録 macro を既知扱い | KILLED | `NEW_CICADA_MACRO` 負例が通る |
| M6 | 期待件数を実数から導出 (恒真化) | KILLED | 件数不足の注入と既存の件数テスト |

- **実データの登録確認** (単独 job、request 40590.nqsv、bnode026、Elapse 16 秒、`evidence/jobs/registration.result.json`、GCC 11): F → (i) (F + 16ad3eb8 の `cc/cicada/transaction.cc` の F からの差分だけ、header なし) は rc=1、理由「TRACE=0 正規化 preprocess 出力が不一致」(文脈 `INLINE_VERSION_OPT=0,…;base`、「未知マクロ」ではない)。F → (ii) (F の同 file の末尾に新しい `#if TRACE` 枝を足したもの。F の同 file には `#if TRACE` 枝が無いので erratum E1 で形を変えた) は rc=0・pass・Cicada 文脈 32 件。投入前に login で生成 patch 2 本 ((i) 85 行 `9f76b022…`・(ii) 11 行 `ea3c4242…`) が F の上で `git apply --check` rc=0 であることを親が実走で確かめた (`evidence/registration-prepare-parent.result.json`。1 回目は親が渡した scratch の親 dir が無く rc=1、作って再実行)。

## 7. push の依頼 (人間の手番)

依頼文:

> CCBench の local branch `izanagi-fix-bundle` (tip `9035509829f005aaaddf44fa5ca431851c2ecdac`) を push し、GitHub Actions の build と format-check が緑であることを確かめてください。主 checkout の `external/ccbench` で `git push origin izanagi-fix-bundle` (別名の新 branch なので force 不要)。
> - 中身: F `25898d00` の上に 4 本の `--no-ff` merge。含めた修正 = Silo の取引内の値の修正 (`izanagi-silo-intra-txn-fix` = `dbac49b6`)、MOCC の validation の修理 X (`izanagi-mocc-validation-fix` = `f4a5169e`)、Cicada の build 修正 G (`eb93423b`)・gc_records と scan の修理 (`81fc4a84`)・promotion と abort の修理 4 本 (`izanagi-cicada-promotion-uaf-fix` = `16ad3eb8`)、正しさ関門の記録 U1 (`izanagi-gate-witness-trace` = `dcb9a41f`、これまで local のみ。この push で祖先として一緒に上がる)。
> - 手元の確認: CI image `:ci` の全 protocol build は configure・build rc=0、実行 file 34、CCBench 本体の warning・error 0。format は clang-format 14.0.0・14.0.6 とも 213 file rc=0。GitHub Actions の結果ではない。
> - 上流への PR は D2305 項 10 のとおり pin に入り CI 緑になってから人間の判断。

- branch の所在: job dir の bundle `$J/fix-bundle.bundle` と、land 後に主 checkout の submodule git dir へ非 force で取り込む (段 9 の後、`$J/fetch-bundle-to-main.sh`)。取り込んだかどうかは worklog に書く。

## 8. 段の経過と所見

- 軽量版でなく段 2・3 を行った (正しさ防壁 = D297 検査器に触るため、DW-C00)。段 3 の主な採用: 条件 (2) の証拠を 3 層 (manifest・A の blob 照合・A→B′) に分け、D297 が修正 hunk を認証したと書かない (A1)、Cicada の 1 走で修正の経路を通す (A2)、計算の止め方 (B-1、調整役への相談で解決)。
- 段 6: レビュー 2 本で must-fix 3 (D297 job の rc 消失、E1 の未反映、`.done` の書き漏れ) と should 多数。fix 後の焦点再レビューは NO-GO 1 件 (job 内の A 照合が合成 bundle に無い修正 tip を参照) → fix 2 巡目 (照合を独立 script に切り出し) → 親の実走で正例 rc=0・負例 rc=2 を確かめて closed。
- 計算の実走で見つかった欠陥 4 件 (Cicada の計装欠落、promotion × 計装の #error、D1464 非準拠の診断 patch、登録確認の patch 生成の空白削り) は、いずれも段 4 の指定の不足か script の不具合で、親の誤りを含む。いずれも 1 件ずつ原因を読んで変更点を決めてから再投入し、同じ job の 3 回目の失敗の後は land 調整役へ FAIL-2 で報告して止めた。
- 段 9 の前に land 調整役経由で届いたユーザー指示 (2026-10-01): やり直し前に原因と変更点を 1 行で書く、同じ原因 2 回で止めて FAIL-2、自己改善 (SELF-REVIEW 送付済み)、worktree 撤去の手動並列方式。
- 段の子: plan 1・相談 2・実装 2・レビュー 2・fix 7 (a 1・b 6、うち b4 は親が途中で停止し不使用)・焦点 1。全子 Codex `gpt-6-sol`・medium (receipt で確認)。

## 9. 確かめたこと・確かめていないこと

確かめたこと:
- 束ねた tip の祖先関係・差分 path・blob・`#line` (§1)、format 2 版と CI image build (§2)、A→B′ の D297 を GCC 11・12 で pass (§3)、Silo・MOCC・Cicada (promotion 無効) の各 1 走 (§4)、検査器の変更のテスト・変異・実データ確認 (§6)。

確かめていないこと:
- GitHub Actions の結果 (push していない)。
- promotion 有効の Cicada の正しさ (現行の計装では判定できない、§5)。gc_records・scan・abort の修理の経路の正しさ (TPC-C を回していない)。
- MOCC の修理経路の発火、各 protocol の複数走・複数 cell。
- 束ねた tip での patches/ の当たり方 (Silo 系 V26・V27 の作り直しを含む、[T-2917] の gitlink 前進 wave の範囲)。
- D297 の C → 束ねた tip の直接比較 (修正を含むので構造上不合格になる。D2322 項 4 の 3 条件で扱う)。
- 登録の実データ確認は GCC 11 だけ。

## 10. 再現資料

- 束ね: `$J/mk-bundle.sh`・`mk-bundle.log`、merge message `$J/msg/`、format `$J/format-ci.sh`。
- job script: `$J/scripts-v6/` (最終版。v1〜v5 は段 6 の各巡の退避) — Codex author の使い捨て script で repo には入れない。投入は `$J/submit-6.sh` (checkout を分けた同時投入、計算用 checkout `.codex/worktrees/cfb-j1〜j5`) と `scripts-v*/submit_one.sh` (再投入)。job の出力は `$J/jobs/<tag>/`。
- 合成物: `$J/synth/` (`synth.bundle`・`synth.oids`・`manifest.json`)。
- 変異: `$J/wave/run-mutation.sh`・`make-mutation-source.sh`・`mutation-spec-*.json`。
- **写しの可逆な最小正規化:** `verbatim/review-b.md` (30 行) と `evidence/mk-bundle.log` (2 行) は `git diff --check` に掛かる行末空白だけを除いた。原文の sha256 (`4c1ede1c…`・`9a12e610…`)・byte 数・行ごとの除去した空白は `evidence/trailing-whitespace-normalization.json` にあり、各行末へ付け直すと原文に戻る (可視文字は不変)。原文は `$J/wave/review-b.md` と `$J/mk-bundle.log`。
