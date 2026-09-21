# 段 1 brief — dev-wave-mocc-xp-pin-candidate (2026-09-21 14:18 JST、base main d99c556df)

**研究前進:** mocc 第 2 例 (D2114 項 2「指定した二つの CC 実装で合成・評価手順を実証」) の certified 系列は、pinned producer (e9e477ca) の mocc が X/P emitter を持たず verifier の certification gate (`orchestrator/verifier/model.py` `ProofSurfaceAssessment.certification_gate_satisfied` = X・P とも evidence-present) を満たせないため 0 件で止まっている。本 wave は X/P 計装を e9e477ca の子 commit C として hook 系統 branch に載せ、正例・負例と D1603 材料 3 点を揃えて D2114 項 3 の再承認へ出せる状態にする。完了判定 = C で (i) certification gate が真 (e9e477ca では偽)、(ii) D297 検査 pass (GCC 11.4 / 12.3)、(iii) compute の正例・負例 all_pass、(iv) 波及表。

**DW-G05:** 放置すると mocc の verifier 結果は常に indeterminate (X/P 不在) で、第 2 例の certified 選択・比較表の受理集合が空のまま。

**確定済み裁定:** D2150 項 1 (e9e477ca 承認、X/P 計装 T-2295 の解決は承認外)、D2114 項 3 (再承認は見送り台帳経路、D1603 材料 3 点)、D1686 (X/P の真実源 = RWLOCK counter + CLL、検査点 3、負例 3 本)、D579 (`cc/mocc/transaction.cc` の限定 authoring、変異探索面にしない)、D297 (TRACE=0 正規化前処理 + include 活性)、D16 (trace-hook は submodule branch へ、上流 push は人間)、D95 (実装面は Codex author)。

**段 1 実測 (job dir probe/、repo 外 scratch):**
- 合流: 計装 patch (`patches/instr-mocc-lock-coverage.patch`、sha e9e65b78…、+65 行、`#line` 7) は hook branch 先端 = 現行 pin e9e477ca に厳密適用で当たる。負例 4 本は e9e477ca + 計装の上でだけ当たる。兄弟 branch witlight (5b02546f) は非 certifying 観測で親にしない。
- **patch をそのまま commit すると D297 が拒否する** (probe OID 5e0fda49、rc=1「include 行文字列（順序込み）が不一致」)。原因は `#if TRACE` 内の `#include <set>` 追加で、検査器が許す include 追加は mocc の trace.hh 1 行だけ (`tools/check_trace0_preprocess_identity.py` `_mocc_trace_include_addition_index`)。
- 最小修正版 (`#include <set>` だけ除き、`std::multiset<const void*>` 2 箇所 → `std::unordered_multiset<const void*>`、`<unordered_set>` は同じ `#if TRACE` 内の trace.hh が供給、`#line 17` は残す): D297 は g++ 11.4 / 12.3 とも `result: pass`、include 列は e9e477ca と同一 11 行、負例 4 本すべて厳密適用で当たる (probe OID eb8dc6fe)。`#line 17` まで消すと early-unlock / hot-update-unlock が当たらない (文脈に `#line 17`)。
- I 面: 現行 pin はどの protocol も I emitter を持たない (grep 0 件)。certification gate は I を要求しない。mocc の I を閉じるには write-intent shadow の新設計が要る。

**Provisional 裁定 (攻撃対象):**
- (P1) 候補の中身 = 上記最小修正版。T-2294 の patch・JSON・test は不変で保持 (規律 7)。検査器の include 規則は緩めない (規律 2)。
- (P2) bytes が T-2294 と異なる (P ブロックの型と include 1 行) ため、正例・負例は内容同一性で引き継がず C 上で compute 実走する (既存 driver `orchestrator/campaign/s3_mocc_lock_coverage.py` に候補 mode を足し、`_build_variant`・condition gate・負例 patch を再利用、新 JSON に C の OID / tree / blob を束縛)。
- (P3) branch は e9e477ca の子として新規 local branch (仮名 `izanagi-mocc-xp-instrumentation`)。readfrom-witness / witlight は動かさない。
- (P4) C の commit は witlight 先例どおり親が wave 木 submodule の一時 worktree で `commit -F` (trailer は `docs/ai-provenance.md`)。submodule の checkout は gitlink のまま clean。bundle を job dir に保全し、主 checkout の submodule git dir への fetch は land 前に行う。
- (P5) 他 wave の木は C の object を持たないので、repo の test は C の object に依存させない。候補の中身を `patches/` に e9e477ca 基準の patch として置き、test は e9e477ca + その patch で検査、C との束縛 (blob / tree OID) は driver JSON と親の実測で持つ。
- (P6) I 面は本 wave で実装しない。不足として記録する。

**不変条件:** gitlink・`CCBENCH_FULL_SHA`・`CURRENT_PIN`・verifier・D297 検査器・既存 patch / JSON / test の bytes は不変。push・pin 再承認の提示・探索開始・mocc の変異軸化はしない。C の touch set は `cc/mocc/transaction.cc` 1 file。TRACE=0 は D297 pass + 等長 dir の `.text` 一致で示す。仮想リスク向けの gate・検査・台帳・一般化は足さない。

**成果物:** (1) submodule commit C + branch、(2) `patches/` の候補 patch、(3) driver 候補 mode + compute JSON + consumer test、(4) C 上の静的正例・負例 test、(5) D297 report (GCC 11.4 / 12.3、clang 14 は試行して限界記録) と負例 (patch そのまま = 5e0fda49 型の拒否)、(6) 波及表 (e9e477c を含む tracked 43 file + 文字列外依存)、(7) insight・worklog / decisions fragment。

**分割:** 段 2 plan 1 本 → 段 3 相談 2 本 (レンズ A: 正しさ・観測者効果 / レンズ B: pin 材料・波及と test 可搬性) → 段 5 author: A = 候補 patch、親が C を commit、B = driver mode + test (C の OID を渡す) → compute 1 走 → 段 6 レビュー 2 本。全 9 段 (DW-C00: 正しさ防壁の計装に触る)。

**環境:** login pegasus02 (D297 検査・build 生死確認)、Pegasus gen_S (driver 実走・焦点走・受入)。

## 条件表の再評価 (brief 直後、14:21 JST)

- 08 (proof chain に触る可能性): 成立 (driver JSON は proof 成果物)。submodule 初期化済み・木の中身を実測 (HEAD e9e477ca、status 0 行、source grep 可)。
- 09 (凍結 bytes): 変更候補 (`s3_mocc_lock_coverage.py`、`test_mocc_proof_surface.py`、`materializer_admission.py`、`condition_meaning_gate.py`、`patches/README.md`、spawn sites / build authority test) の変更前 sha256 で repo 全体を検索し pin 0 件。path / 関数名の pin = materializer 登録簿・spawn sites・build authority test・`s3_mocc_mutation_proof.py` / `s3_mocc_template_proof.py` の import。verifier/model.py と D297 検査器は campaign.lock・receipt 群に sha pin があり、触らない。凍結成果物 (s8b freeze、floor protocol、事前登録) は変えない。
- 10 (producer write-path): 非成立 (凍結 producer の出力 bytes を変えない。driver 候補 mode は新 JSON を書き、既存 JSON は不変)。
- 13 (検証の新設): 成立。入力の実在と値域: verifier の proof-surface 判定 (production `capture/assess_compiled_protocol_source_snapshot`) は e9e477ca で X/P absent・gate 偽、最小修正版で X/P present・gate 真・I absent (probe/p5-proof-surface.log)。runtime check の入力 field (certified、X/P 件数、reason、cycles、nm/strings/.text) は T-2294 JSON に実在し、正例・負例とも到達済み (job 979791 all_pass)。
