# 段 1 brief — [md_17] Cicada の正しさ検査を insert / delete と TPC-C へ広げる (T-2874 の (4) の一部、2026-09-29)

wave: dev-wave-vhash-cicada-verifier-ext / worktree `/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-vhash-cicada-verifier-ext` (branch 同名) / 起点 local main `035fc11fa` / CCBench gitlink は動かさない (pin C `68106660`)。依頼逐語 = job dir `request-md_17.txt` + `request-common.txt` (md_17 が優先)。前段の一次資料 = `output/insights/2026-09-29/vhash-cicada-verifier/README.md` (md_3、D2279)。

**研究前進:** VHash 評価計画草稿 (`docs/vhash-evaluation-preregistration-draft.md` の限界節「TPC-C は本計画の主要な判定に入れていない … 門の対象の拡張 (scan・insert・delete) が先に要る」) の前提を埋め、TPC-C と insert のある負荷に絶対規律 2 の門 (巡回検出) を掛けられるようにする。完了判定 = (i) stock Cicada の TPC-C 小走行の trace が巡回 0・存在履歴違反 0・integrity 数値項目 0・C 行 = commit 数 (上限は indeterminate)、(ii) insert か delete の経路を壊した patch 1 本以上を判定器が巡回として検出し、事前登録の帰属規則を満たす witness が 1 件以上、(iii) TRACE=0 で tpcc (と未比較の bomb / sbomb) target の TU の命令列が pin C と一致、を実測した insight。

**親の実測 (brief 前、path は main checkout と同内容):**
- YCSB (`external/ccbench/include/ycsb.hh:67-73`) の操作は READ / WRITE / READ_MODIFY_WRITE だけで insert / delete は無い。insert / delete は TPC-C だけ (NewOrder の insert、Delivery の delete)。→ 依頼の (a) と (b) は「Cicada の TPC-C を trace する」に一体化する。
- TPC-C の trace は既存契約で **v3** (D2224 / D2225: `C` 10 token に nS nQ tx_type、R / W / X は表番号 = `Storage` 整数付き)。v2 は表を持たず、TPC-C では表だけ違う同じ key bytes が 1 本の版列に混ざる (D2224 理由)。存在履歴検査 (D2232) は v3 だけで走る。v3 は既存書式であり、YCSB の v2 は変えない。
- v3 の部品 (`include/trace.hh` の v3 emitter と取引種別の thread-local 文脈、`include/tpcc.hh` の begin 直後の set と trace build の全 commit 計数) は **pin C に無い**。CCBench の local branch `izanagi-tpcc-v3-silo-mocc` の C1' `6aa7a58f` (pin C の子、header 2 file だけ) にある。pin の C2' 系への前進は D2277 項 1 で承認済み、並走 wave (T-2854、session c32da1) が整形と D297 判定を実施中。本 wave は gitlink を動かさない。
- `patches/instr-cicada-trace.patch` は `cc/cicada/` だけを触る (C1' と touch set が素)。md_14 (稼働中) はこの patch の上に forwarding patch を重ねて YCSB を検査している。
- 判定器: v3 と `--protocol cicada` の組合せに制限なし。cicada は証拠面 unavailable (`orchestrator/verifier/model.py:37`) で上限 indeterminate。
- TPC-C の初期ロードも `TupleInitParam::initial_wts` (`cc/cicada/include/tuple.hh:16-20,77-89`) で版を付ける → genesis `(1,0)` 写像はそのまま。実行時 insert は `Tuple::init(thid, ver, wts)` (`tuple.hh:95-107`) で版 = tx の wts、既存 key への insert は `get_value` 非 null で失敗 (`cc/cicada/transaction.cc` の `insert`)。D2232 項 4 が別 CC に求める 2 点が Cicada でも成り立つ見込み (段 2 で file:line、生死確認で実測)。
- delete は `new Version(wts)` を積む。`read_internal` は deleted 版を nullptr にし read set に入れないので stock では D 版の R は出ない。存在しない key の読みも read set に入らない (R なし) — v3 段 1 の扱い (不在の読みは表さない、nS = nQ = 0) と同じ。
- `INLINE_VERSION_OPT=1` では insert の `Tuple::init(thid, ver, wts)` が ver を `latest_` に繋がない (`tuple.hh:100-102`)。既定は 0。未対応構成として記録する。
- scan は `read_internal` を通るので R に出る。phantom 防止 (`node_map_` の検証) は trace に表れない。
- `patches/ledger.json` は entries 1 件固定 (`orchestrator/campaign/silo_ladder_rung1_contract.py:517-518`)。登録は `patches/README.md` だけ (md_3 R0 と同じ)。新 patch の `#if` 条件語は `TRACE` だけ、`IZANAGI_` の語は含めない (md_3 R0)。
- 条件 08 / 09 / 10: 凍結 bytes・oracle gate に触る見込みなし (patch の bytes pin は md_3 で検索 0 件、段 2 で新 patch 名について再検索)。条件 13 (検証の新設) は成立扱い: 正例・負例の判定規則を新設するので、段 2 で入力 field の実在と実値域を確かめる。

**(P1) 親の provisional 裁定・攻撃対象 — 置き場:** `patches/instr-cicada-trace.patch` の bytes は変えない (md_14 の重ね適用と YCSB の v2 出力を 1 byte も揺らさない)。TPC-C の v3 出力は新 patch `patches/instr-cicada-trace-tpcc.patch` として instr patch の上に重ね、base に C1' `6aa7a58f` 以降を要求する。依頼の「instr-cicada-trace.patch の更新」を「instr-cicada-trace 系の更新 = 重ね patch の新設」と読み替える (1 本に統合すると pin C で TRACE=1 の compile が壊れる)。
**(P2)** v3 の切替: `traceCommit` で `izanagi_trace::tpcc_tx_type()` が非 0 なら v3 (C 10 token・R / W に `storage_` の整数・nS = nQ = 0・tx_type)、0 なら既存 v2 の式のまま。E の直後に文脈を 0 へ戻す (silo C2' と同じ、D2225 項 2)。`tpcc_cicada.cc` の main で `initial_wts` を渡す (ycsb と同形)。
**(P3)** 判定器 production は変えない。Cicada 形の fixture テストも足さない (実走が一次証拠。md_3 R6 erratum で Cicada 形 fixture は新しい検出力を示さなかった)。受理失敗が実測で出たらその一点だけ最小修正し、既存 protocol の判定不変をテストで示す。
**(P4)** 壊し patch: insert か delete の経路を単一 site で壊す 1〜2 本 (`patches/broken-cicada-*.patch`、無マクロ・既存 3 本と同じ診断形式・事前登録の帰属規則)。候補と TPC-C で巡回になる機序は段 2 に起草させる。存在履歴違反 (D2232) だけで出る壊しは完了判定 (ii) に数えない (追加の検出として記録はする)。
**(P5)** TRACE=0: 同じ compile command で (i) pin C 対 pin C + instr (tpcc・bomb・sbomb target の全 TU)、(ii) pin C 対 C1' + instr + tpcc 重ね patch (tpcc target の全 TU)。判定の根拠は objdump の命令列 (md_3 と同じ正規化)、前処理は調査用、nm / strings の trace 語残存 0。
**(P6)** 範囲読み取りの phantom は判定器側の対応が要る (S / Q 行、D2224 の段 2) ので設計メモだけ書いて未対応に残す。
**(P7)** TPC-C の cell は段 2 に提案させ段 4 で事前登録する (段 1 mix 57:43 と Delivery を含む mix、warehouse 1、thread 1 / 4 程度)。

**不変条件:** 規律 2 (判定器・既存 protocol の判定を変えない、壊し patch を baseline に混ぜない、巡回 = 失格)。規律 1 (追加は `#if TRACE` 内だけ、`#line` で TRACE=0 の行番号を保つ、性能値を取らない)。gitlink を動かさない。md_14 / md_15 / md_16 の所有物 (`patches/cicada-forwarding-*`、`orchestrator/campaign/vhash_forwarding_prototype.py`、`patches/instr-cicada-version-lifetime.patch`、`tools/vhash_forwarding_model/`) を編集しない。仮想リスク向けの gate・台帳・一般化を足さない。テスト全体 5 分上限。計算 < 2 node 時間。

**成果物:** `patches/instr-cicada-trace-tpcc.patch` (新)、`patches/broken-cicada-*.patch` (新 1〜2 本)、`patches/README.md` の該当節、repo 外起動器 (job dir、md_3 の `launch_cicada_run.py` を雛形に TPC-C・v3・identity 拡張)、insight `output/insights/2026-09-29/vhash-cicada-verifier-ext/README.md`、worklog / decisions fragment。

**分割 (段 5):** 単位 T = trace 重ね patch + 起動器の TPC-C / identity 拡張 (Codex author、先行)。生死確認 (親) 成立後に単位 B = 壊し patch + 帰属解析 (Codex author)。所有は素集合。

**計算:** build (TRACE=1 × 2〜3、TRACE=0 identity × 3〜4) と TPC-C 小走行 (数十秒) で、生死確認 1 job + 本走 1〜2 job、合計 ≈ 1 node 時間の見込み (< 2)。受入・変異 matrix は別枠で見積もり段 4 で更新。

**実測環境:** Pegasus 計算ノード、`tools/pegasus/dispatch_compute.py --task generic` を計測用 detached worktree から (md_3 と同じ)。受入は `tools/dev_wave_wait.py acceptance --lease-optional`。
