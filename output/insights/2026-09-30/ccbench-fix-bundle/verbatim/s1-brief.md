# 段 1 brief — md_16 CCBench 修正束ね tip ([T-2917]・[T-2919]・[T-2945]、D2322 項 4・6)

wave: dev-wave-ccbench-fix-bundle / worktree: /work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-ccbench-fix-bundle (HEAD = local main 908741c6f、開始 gate rc=0)
依頼の正本: /work/1/SFC/tanab/tmp/gen-opt-2026-09-29/md_16.txt と common-5.txt (読めなければ即停止)

## 研究前進
gen-opt の候補評価・段 A の試しは「Silo の取引内の値の修正 + 正しさ関門の記録 (Q/V 行)」入りの CCBench を要し、MOCC を 2 つ目のベースにするには MOCC 修理 X が要る。
本 wave の完了 = F の上にそれらを束ねた CCBench commit (branch、push はしない) と、D2322 項 4 の 3 条件の証拠、push 依頼文。gitlink 前進は md_15 → 後続 wave。

## 実測済みの事実 (親、2026-09-30 22 時台)
- 束ねる tip (worktree の submodule で主 checkout から取り直し、GitHub へ HTTPS ls-remote で照合、一致):
  Silo `dbac49b6dc2d2ab9211b1ec0a41e44fa21245f43` / MOCC X `f4a5169ede52630d9357444e3412ffe9aed7c78f` / Cicada build G `eb93423bbb27a2694d3d75861696c365f0fb8f7c` /
  Cicada gc `81fc4a84cc855a3f98374e40e2ba7e3330c2614d` / Cicada promotion-uaf `16ad3eb8ca5f7bb3aea789bff99958e2192f6714` (G と gc の merge aa8e36f1 + 4 commit) /
  関門記録 U1 `dcb9a41f3e538744298b0e5c42dc37349bac114e` (local のみ)。F = `25898d00b9a6bbf09329ff8e8318c77d4f08b46e`。全部 F の子孫。
- GitHub check-runs (公開 API): 上の push 済み 5 本とも build・format-check success (promotion-uaf は 2026-09-30T13:00Z)。→ promotion-uaf を含める ([T-2959] の branch は push・CI 緑で確定)。
- 変更 path (F から): Silo = cc/silo/transaction.cc / MOCC = cc/mocc/transaction.cc / Cicada 3 本合計 = cc/cicada/transaction.cc と cc/cicada/include/{cicada_op_element,transaction,tuple}.hh / U1 = cc/silo/transaction.cc, include/trace.hh, include/ycsb.hh。
- 使い捨て clone (job tmp) で F → silo → mocc → cicada-promotion-uaf → U1 の順に --no-ff merge: 4 本とも文面衝突 0。統合後の silo の `#line` 6 本 (365 381 638 661 682 703) は Silo 修正 tip と一致。U1 の追加行はすべて `#if TRACE` の内側で、直後の絶対値 `#line` が打ち消す構造。
- D297 検査器 (tools/check_trace0_preprocess_identity.py、sha256 bcd46b29…) は old が new の祖先であることを要求。`.cc` 差分は SILO_SPACE の genome × overlay 文脈で比較し、cicada の `.cc` は `#if SINGLE_EXEC` 等の未知 macro で fails-closed (前 wave §6)。header 差分は規則 v2 (実 configure 65 = stock1・mocc8・silo8・tictoc24・cicada24)。
- Cicada の 4 macro は cc/cicada/CMakeLists.txt が `-D` で与える値 macro (既定 OPT=0・PROMOTION=1・SINGLE_EXEC=0・DELAY=0)。source_digest.py の CONTEXT_MACROS は「TU 内 #define で注入される macro の素/define 2 文脈」用で、2 個以上は停止する設計 (同 file 351 行の注記)。
- 計算単価 (実測): D297 で ycsb.hh を含む F→U1 は GCC 11 で約 3,300 s (bnode053)。trace.hh のみの C→F は 1 job 内 GCC 11・12 並行で 988 s。Silo の生死確認は 1 条件 (1 build・2 workload) 117〜130 s。CI image build 33〜51 s。

## 確定済みの裁定
D2322 項 4 (例外を足さず 3 条件: (1) C→F 合格 = D2293、(2) F→tip の TRACE=0 差分が修正の hunk だけ、(3) 修正後 build での正しさの取り直し。Cicada は CONTEXT_MACROS 登録で機械判定可能にする。人の目だけで受け入れない)、D2322 項 6 / D2305 項 6 (束ねた tip は改めて push 依頼、push は人間)、D297 (header 差分・比較 0 件は拒否、複数 compiler)、D2293、D2304、D2308、D16/D18/D20。

## provisional 裁定 (攻撃対象)
- (P1) 条件 (2) の機械判定は Silo の先例 (D2322 が (2) として認めた「pin + 修正 → 新 tip」の D297 (b)) と同形にする: 使い捨て clone に A = (親 F、tree = F に 5 本の修正 tip の F からの diff を `git apply` で独立に当てたもの)、B′ = (親 A、tree = 束ねた tip の tree) を作り、D297 A→B′ を GCC 11・12 で pass させる (`--expect-paths cc/silo/transaction.cc include/trace.hh include/ycsb.hh`)。読み: 束ねた tip の TRACE=0 は「F + 各修正の diff」と一致 = F からの差は修正の hunk だけ。merge の解決と U1 は TRACE=0 に何も足さない。
- (P2) Cicada の登録は D297 検査器の中に閉じ、source_digest.py の CONTEXT_MACROS・digest の bytes は変えない (凍結・src token の閉包へ波及させない)。登録した macro は値の組合せ文脈を実際に列挙して比べる (既知集合へ名前を足すだけの形は緩和なので不可)。未登録の新 macro は従来どおり停止。(P1) の A→B′ には cicada の `.cc` が入らないので、登録の効きは単体テスト + 小さな実走 (F → F+cicada の .cc 修正だけの合成 commit で「未知 macro 停止」でなく「TRACE=0 不一致」で rc=1、trace だけの合成差分で pass) で示す。
- (P3) 束ね方は --no-ff merge 4 本 (Silo・MOCC・Cicada promotion-uaf・U1)、merge は親、衝突解決が要れば Codex author。branch 名は `izanagi-fix-bundle` (一次資料に記録)。cherry-pick は push 済み SHA を変えるので採らない。
- (P4) 条件 (3) は束ねた tip の trace build で各 1 回: Silo = gen-opt 起動器 v3 型 (W-rmw・W-blind、`--require-gate-witness`、事前登録 = serializable・certified)、MOCC・Cicada = 既存判定器 (`--protocol mocc|cicada`)。
- (P5) 計算見積り: D297 GCC 11・12 別 job 各 ≈3,300〜3,600 s (walltime 1:30) + CI build ≈60 s + 正しさ 3 本 ≈10 分 + 登録の実走 ≈5 分 ≈ 2.1〜2.2 node 時間 → 2 以上。common-5 §4 (ユーザー委任) に従い land 調整役へ 5 点で相談し GO を得てから投入 (md_16 項 4 の「止める」との食い違いは相談文に明記し、調整役が止めれば止める)。D297 は検査器に分割機能がなく 1 本 5 分へは割れない (限界として記録)。

## scope / 成果物
- CCBench: branch `izanagi-fix-bundle` (commit のみ、gitlink は動かさない)。bundle を /work/SFC/tanab/tmp/ccbench-fix-bundle-2026-09-30/ に保存し、主 checkout の submodule git dir へ非 force で取り込む。
- izanagi: tools/check_trace0_preprocess_identity.py の cicada 登録 + テスト (Codex author、受入)。一次資料 output/insights/2026-09-30/ccbench-fix-bundle/README.md。spool fragment ([T-2917]・[T-2919]・[T-2945]・[T-2921]・[T-2924]・[T-2959] の更新)。
- scope 外: gitlink・CCBENCH_FULL_SHA・CURRENT_PIN、上流 PR、新しい修正、patches/ の作り直し ([T-2917] の V26・V27 は gitlink wave)。

## 不変条件
規律 1 (TRACE=0 同一性の検査を緩めない、D297 に意図差分の例外を足さない)、規律 2・3 (照合を緩めない、stock が赤でも緩めない)、push しない、force しない、他 session の branch を書き換えない、source_digest の digest bytes 不変。

## 分割
段 2 plan 1 本 (検査器の登録設計 + 合成 A/B′ の作り方 + job script 群の設計)。段 3 相談 2 本 (正しさ境界 / 実効性・過剰)。段 5 実装子: (a) 検査器 + テスト、(b) 計算 job script 群 (job dir に置く使い捨て、Codex author)。
