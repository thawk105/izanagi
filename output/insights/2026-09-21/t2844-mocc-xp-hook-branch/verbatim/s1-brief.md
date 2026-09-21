# 段 1 brief — dev-wave-t2844-mocc-xp-hook-branch (2026-09-21 20:5x JST 起草、初版保存 20:52 頃・条件表追記 20:54:19 = file mtime、base main 36fb14a3d131d516dc57b02ec69f56c711927c2e)

**研究前進:** mocc 第 2 例 (D2114 項 2) の certified 系列は、pinned producer e9e477ca (以下 BASE) の mocc source に X/P emitter が無く、verifier の certification gate (`orchestrator/verifier/model.py` の `ProofSurfaceAssessment.certification_gate_satisfied`) が偽のため 0 件で止まっている。本 wave は X/P 計装を BASE の単一の子 commit C として hook 系統 branch に載せ、D1603 の材料 3 点を揃え、D2114 項 3 の再承認 (人間手番) へ出せる状態にする。完了判定 = (i) C を commit し bundle 保全 + 主 checkout の submodule git dir へ fetch、(ii) C に対し D297 検査 GCC 11.4 / 12.3 pass、clang は実走して結果を正直に記録、(iii) C 上の正例・負例 compute 1 走 all_pass、(iv) 波及表の点検。

**DW-G05:** 放置すると mocc は pinned producer 上で certified 結果を出せず、第 2 例の certified 比較の受理集合は空のまま。D1603 の材料が欠け、pin 再承認は提示できない。

**確定済み裁定 (逐語 = job dir `verbatim/`):** D2207 (D297 検査器の include 規則は緩めず計装側を include 行不変に直す、容器の最終選択と実走経路は本 wave の段 3・4 で確定)、D2150 項 1、D2114 項 3、D1686 (X/P の真実源 = RWLOCK counter + CLL)、D1687、D579 (`cc/mocc/transaction.cc` の限定 authoring)、D297、D780、D1603、D16 / D18 / D20 (trace-hook は submodule branch、push は人間)、D95 (実装面は Codex author、Codex 不可用なら親は代筆しない)、D2153。

**段 1 の実測 (本 wave、20:45〜20:54 JST):**
- Codex 利用枠: 他 wave (t2632) の codex 子が 20:27:47〜20:31:34 (consult、rc=0、11,993 byte) と 20:37:31〜20:43:15 (author、rc=0、8,452 byte) に完了。前 wave の枠切れ (表示 Sep 26th) は解消している。本 wave の段 3 の投入が直接の確認になる。
- wave 木の submodule: HEAD = BASE、`git submodule status --recursive` 3 行とも空白始まり。`refs/heads/izanagi-t1943-mocc-g2-readfrom-witness` = e9e477ca (hook 系統の先端 = BASE)。`izanagi-mocc-xp-instrumentation` は wave 木の submodule の refs (origin/* = 主 module store の heads を含む) に無い。
- 前 wave の起点 d99c556df から現 main までに、計装 patch (sha256 e9e65b78…)、負例 patch 4 本、driver `s3_mocc_lock_coverage.py` (sha256 3d3d013b…)、D297 検査器 (9cf5b84c…)、verifier/model.py、materializer_admission.py、condition_meaning_gate.py、test_mocc_proof_surface.py、patches/ の変更は 0 commit。段 2 plan の file:line はそのまま現物に当たる。
- 波及表の母集合 (`e9e477c` を含む tracked file、docs の 3 台帳・archive・spool と output/insights を除く) は 45 件 (前回 43 件 + `docs/paper-story/2026-09-21c.md` と `docs/paper-story/claim-evidence/2026-09-21b.md`)。一覧 = job dir `e9e477c-tracked-files.txt`。

**Provisional 裁定 (親、攻撃対象):**
- (P1) 候補の中身 = 前 wave §3 の p4 版 (BASE に対し transaction.cc だけ +64 行、blob `e393efbfd5fad7bbe05117b43669ccc0f44abb6a`)。`#include <set>` を足さず、`std::unordered_multiset<const void*>` を 2 箇所、`#line 17` を含む `#line` 7 箇所は T-2294 と同じ。Codex author A が BASE 基準の patch を作り、親が BASE への適用結果の blob を実測して目標と照合する。一致しなくても C に対して D297 を実走する (前 wave の結果は内容同一のときだけ参考として引き継ぐ)。
- (P2) 実走 = 既存 driver `orchestrator/campaign/s3_mocc_lock_coverage.py` に候補 mode (`--candidate-oid <40hex>`) を足す。旧 mode・`PIN`・`CHECK_KEYS`・既存 helper と旧 JSON の bytes/挙動は不変。候補 mode は C を checkout し計装 patch を当てない。正例は無 patch、負例は既存 3 本 (lockskip / permutation-erase / early-unlock) を C に直接当てる。行列は旧 6 走と同じ。TRACE=0 は BASE と C を等長 dir で比較 (既存 `_trace0_record`)。check は旧 14 key の意味をそのまま再利用し、候補固有の追加は C の束縛に要る最小 (親が BASE ちょうど 1 本、BASE→C の差分が transaction.cc 1 path) に留める。**段 2 plan が足した hot 正負例 2 走 (hot-update-unlock)・`objcopy` による `.text` bytes 比較・proof-surface key・21 key 化は provisional に不採用** (依頼は T-2294 の正例・負例を C で再走すること。hot-update-unlock は mutation proof (T-2757) の命題、`.text` は既存の正規化 objdump 比較 + D297 が担う)。出力は新 path `output/env/pegasus/calibration/s3_mocc_xp_pin_candidate.json`、旧 3 本の JSON を上書きしない。
- (P3) branch = `izanagi-mocc-xp-instrumentation` (新規、local)、C の親は BASE ちょうど 1 本。readfrom-witness / witlight は動かさない。
- (P4) C の commit は witlight 先例 (job dir `mk-W-commit.sh` 型) どおり、親が wave 木 submodule の一時 worktree (job dir 配下、BASE で detach) に author の patch を `git apply --check` → 適用 → `commit -F`。trailer は `docs/ai-provenance.md` の形式で実寄与どおり。wave 木と主 checkout の submodule HEAD・gitlink は BASE のまま。bundle (自己完結) を job dir に置き `git bundle verify` + sha256 を記録。主 checkout の submodule git dir への branch の fetch は **C の message が確定した後 (段 6 の C に関する所見が閉じた後)、worktree 撤去より前**に行い、同名 ref が別 OID なら force しない。
- (P5) 他 wave の木は C の object を持つ保証が無い。repo の test は C の object に依存させない。候補 patch を `patches/instr-mocc-lock-coverage-pin-candidate.patch` として置き (branch C の可搬な再現資料、production に重ねない)、test は BASE (全 wave で初期化される pin) + この patch で候補 source を再構成して検査する。C との束縛 (OID/tree/blob) は driver の git 実測と親の記録、JSON consumer test の固定期待値が持つ。
- (P6) I 面 ([T-2295]) は本 wave で実装しない。不足として記録する。
- (P7) D297: 親が login で C に対し `--cxx` = g++-11 / g++-12 / clang++ の 3 本を実走 (full OID、`--expect-paths cc/mocc/transaction.cc`)。負例対照 = scratch の BASE + 旧 T-2294 patch そのままの一時 commit (repo・branch に入れない) に GCC 11 で rc=1 (include 行文字列の不一致) を期待。clang が既知限界で止まれば「比較未完了」と書く。検査器は直さない。
- (P8) 波及表: 段 2 plan §6 の分類を現 main の 45 件に更新し、段 3 レンズ B と段 6 で点検する。表中の file は編集しない。
- (P9) 生死確認 (DW-G01): driver 実装の前に、親が login で C の TRACE=1 / TRACE=0 build を CCBench の実 CMake flags (`-Werror`) で通す (benchmark の実行はしない)。

**不変条件:** gitlink・`CCBENCH_FULL_SHA`・`CURRENT_PIN`・verifier・D297 検査器・既存 patch (計装・負例 4 本・template 系) / 旧 JSON 3 本 / 旧 test の bytes は不変。push・remote 操作・pin 再承認の提示・見送り台帳への「提示」記録・探索開始・mocc の変異軸化はしない。C の touch set は `cc/mocc/transaction.cc` 1 file。規律 2 (anomaly を出す variant の即 reject、検証の甘化の不採用) は不変。仮想リスク向けの gate・検査・台帳・一般化は足さない。

**成果物:** (1) submodule commit C + branch + bundle + 主 module store への fetch、(2) `patches/` の候補 patch、(3) driver 候補 mode + compute JSON + consumer / routing test、(4) D297 report 3 本 + 負例対照、(5) 波及表 (45 件 + 文字列外依存)、(6) insight・worklog / decisions fragment。

**分割:** 段 2 = 前 wave の plan を流用 (job dir `prev/s2-plan.md`)。段 3 相談 2 本 (A: 正しさ境界・観測者効果 / B: 過剰・削除と pin 材料・可搬性・波及表) → 段 4 → 段 5 author A (候補 patch のみ) → 親が C を commit・login build → author B (driver 候補 mode + test + patches/README、C の OID/tree/blob を渡す) → compute 1 走 → 段 6 レビュー 2 本 (1 本は過剰・削除レンズ) → 変異 → 受入。全 9 段 (DW-C00: 正しさ防壁の計装に触る。段 2 は流用)。

**環境:** login pegasus02 (D297、patch 適用、build の生死確認)、Pegasus gen_S (driver 実走、焦点走、受入)。所在 = worklog、機体固有情報 = `docs/pegasus-runbook.md`。

## 条件表の再評価 (brief 直後、20:54 JST = file mtime)

- 08 (proof chain に触る): 成立。driver の候補 JSON は proof 成果物。submodule は初期化済みで木の中身を実測済み (HEAD e9e477ca、status 3 行とも空白始まり、`external/ccbench/cc/mocc/transaction.cc` 実在)。
- 09 (凍結 bytes): 変更候補 (`orchestrator/campaign/s3_mocc_lock_coverage.py` 3d3d013b…、`patches/README.md` 68a2bb53…、参照のみの `orchestrator/tests/test_mocc_proof_surface.py` f9dc5cee…、`materializer_admission.py` f1f1f75a…、`condition_meaning_gate.py` 3e05d8f5…) の変更前 sha256 先頭 16 桁で tracked 全体を `git grep` → 0 件。path / module 名の consumer (docs と output/insights を除く) = materializer_admission.py、s3_mocc_mutation_proof.py、s3_mocc_template_proof.py、test_ccbench_spawn_sites.py、test_mocc_mutation_proof.py、test_mocc_proof_surface.py、test_p3_build_authority_cli.py、旧 JSON 3 本、patches/README.md (段 2 plan §2 の表と同じ)。verifier/model.py と D297 検査器は触らない。凍結成果物 (s8b freeze、floor protocol、事前登録) は変えない。driver に `"--build"` を含む関数を新設すると materializer 登録簿 (exact 一致 test) の追随が要るので、候補 mode は既存 `_build_variant` / `_install_dependency` を呼ぶだけにする。
- 10 (producer write-path): 非成立。driver は凍結 producer ではなく (sha pin 0 件)、候補 mode は新 path の JSON を書き、旧 JSON 3 本の bytes は変えない。
- 13 (検証の新設): 成立 (候補 mode の束縛 check)。入力の実在と値域: `certified` は `Integrity.clean()` 経由で proof-surface gate を含む (`orchestrator/verifier/model.py` の `certified` / `clean`)。旧 14 key の入力 field は T-2294 JSON (job 979791) に実在し正例・負例とも到達済み。束縛 check の入力 (C の parent 列、BASE→C の raw diff の path 集合) は `git rev-list --parents -n1` と `git diff-tree` で取れる (C を作った後に親が実測する)。
