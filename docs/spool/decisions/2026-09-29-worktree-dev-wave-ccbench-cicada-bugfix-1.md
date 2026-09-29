---
schema: izanagi-spool-v1
ledger: decisions
authored: 2026-09-29
wave: worktree-dev-wave-ccbench-cicada-bugfix
seq: 1
---

## {{D:ccbench-cicada-build-fix}}. CCBench の Cicada の不具合は直す (ユーザー判断)。build 不能 2 件と計器 build 1 件を、非既定の #if の内側の行の置換だけで F の子 commit G に直す。promotion 有効の 8 genome は build できるようになったが判定器が直列化違反を検出したので失格とし、D297 検査器が cicada の変更を判定できないことは検査器を変えずに記録する

**決定 (ユーザー判断):** 還元判断がユーザー確認待ちだった Cicada の build 不具合 (INLINE_VERSION_OPT=1 ∧ INLINE_VERSION_PROMOTION=1 の 8 genome と WORKER1_INSERT_DELAY_RPHASE が compile できない) について、ユーザーは 2026-09-29 (21 時台 JST) に「CCBench の不具合は直したい」と判断した。本決定はこれを「直す」で確定し、次の方針で直したことを記録する。
TPC-C 全 mix × 4 thread の `gc_records()` の ERR は、後から作られた専用の依頼 (md_23) が扱う (同じ判断の対象だが本決定の修理の範囲外)。

1. **置き場:** CCBench の新しい local branch `izanagi-cicada-build-fix` に、F `25898d00` (D2293) の子 commit G `eb93423bbb27a2694d3d75861696c365f0fb8f7c` として置く (Codex author、D95)。izanagi の gitlink・`CCBENCH_FULL_SHA`・`CURRENT_PIN`・`patches/` は変えない。push・PR は人間 (D16・D18・D20)。pin の前進は push と GitHub の CI が緑になった後の別の作業とする (D2277 項 1 の順序)。
2. **直し方:** 変更は非既定の `#if` 区間の内側の行の置換だけにし、物理行数を変えない。既定の build の preprocess 出力と `ERR` の `__LINE__` を F と同じに保ち、既存の patch (計装 patch の `#line` の値を含む) がそのまま当たるようにするため。promotion は改名後の `update()` を呼ぶ形にし、`read_internal()` が既に積んだ読み取りを promotion が重ねて積む行を除く。待機の分岐は README と flag 定義どおり runtime flag `-worker1_insert_delay_rphase_us` を読み、既に取り込み済みの `sleepTics()` で待つ。ADD_ANALYSIS=1 で compile できない計上の行 (存在しない計時開始値を使う) も同じ族として直す。
3. **検証:** G で正準 24 genome・ADD_ANALYSIS=1 の promotion 2 genome・W5 の build が全部通り、上流 CI の 2 本 (clang-format 14 の 213 file と CI image の全 protocol build、本体の warning・error 0) を手元で通した。W5 の待機は trace の thread 別 commit 数で直接確かめた (待機 1 ms で worker 1 の commit が 2 件、待機なしの対照で 47,551 件)。既定 genome の YCSB・TPC-C (Delivery なし) の小走行は判定器で巡回 0。
4. **promotion の 8 genome は失格 (規律 2):** 計装の `#error` を外した診断用の変種で promotion genome の 1 設定 (BACK_OFF=0・REUSE_VERSION=1・WRITE_LATEST_ONLY=0) を走らせると、判定器は YCSB K で巡回 4 件、R で 327 件を検出し、TPC-C は `std::bad_alloc` で異常終了した。promotion の経路はこれまで compile できず一度も走っていなかった。異常は 1 設定で観測したものだが、安全側の判断として 8 設定すべてを VHash の比較・探索から除外する。G で除いた重複登録を戻しても YCSB K・R の巡回は残り、計装なし (TRACE=0) でも TPC-C の異常終了は再現した。重複登録の除去は観測した YCSB の巡回に必須ではなく、計装は TPC-C の異常終了に必須ではない (それ以上の原因の除外はしていない)。G の promotion の修正は取り消さない (compile できないままでは欠陥を観測できない。既定の build の preprocess 出力を変えない見込みで、既存 patch の当たり方も F と同じ)。原因の特定と修理は別の項目とする。build できることと正しく動くことを分けて記録する。
5. **D297:** D297 検査器は C→G を判定できない (cicada の transaction.cc の条件指令が参照する cicada 固有の macro が検査器の既知の文脈に無く、判定の前に fails-closed で止まる、T-148)。検査器は変えない (規律 2)。選定文脈 (stock・mocc・silo) についての結論は C→F の判定 (D2293、pass) と同じと推論し、cicada の 2 file は意図した変更として差分の範囲を一次資料に書く。この推論を検査器の pass とは呼ばない。pin を G へ進める作業は、cicada の文脈 macro の扱いを決める必要がある。
6. **直さないもの:** YCSB の再試行で読み取り専用の指定が戻らないこと (workload 共通 header の設計)、`update()` の early abort が `Status` に出ないこと (既存の挙動)、待ち時間の積の桁あふれ (現実の指定では起きない)。一次資料に記録するだけにする。

一次資料: `output/insights/2026-09-29/ccbench-cicada-bugfix/README.md`。

**理由:** ユーザー判断と D2277 項 2 (基盤の欠陥は使いながら直す)。VHash の較正 (build できない 8 genome) と評価の前提 (読み取り後に待つ長い tx の型 W5) を埋める。上流の CCBench の CI を通す品質で作る (D2277 項 1)。行数を変えない形は D2293 と同じく、既定の build と既存の patch を変えないため。promotion の失格は、build できたことを正しさの根拠にしないため (規律 2・3)。

**却下した選択肢:**
- compile 時定数 `WORKER1_INSERT_DELAY_RPHASE_US` を定義する — README・flag 定義と食い違い、待ち時間を変えるたびに build し直す。
- `include/delay.hh` を include して `clock_delay()` を使う — 物理行数が変わり、既定 build の `ERR` の行番号と既存 patch の `#line` がずれる。
- promotion の引数を無名にして未使用の警告を避ける — 計装 patch の hunk がその行を文脈に含み、G に当たらなくなる (段 6 レビューが検出)。
- promotion の修正を取り消して compile できない状態に戻す — 欠陥の観測ができなくなり、ユーザーの「直したい」にも反する。
- D297 検査器に cicada の macro を登録して C→G を判定させる — gate の変更で本件の範囲を超える。pin 前進の作業で扱う。
