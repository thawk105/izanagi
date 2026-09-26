# 段 1 brief — [T-2847] 残り (4) si の trace v2 化 + V28・V29・V36 の実走 (2026-09-26)

wave: dev-wave-t2847-si-v2 / worktree `/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2847-si-v2` (branch `worktree-dev-wave-t2847-si-v2`) / 起点 local main `6d198ca8afddf9a1ecbc4ac421f163e080838751` (開始 gate fresh rc=0、18:5x JST) / CCBench gitlink = pin C `68106660686232781bca3be792a750d3e19d7a8a` (動かさない)。依頼逐語 = 同 dir `request.md`。

**研究前進:** VLDB 差分分析 P0「検証の意味」の検出表 (設計書 `output/insights/2026-09-22/t2847-verifier-detection-design/README.md` §4.5) の si 3 行 (V36 無改変 si の write skew、V29 first-updater-wins を外す、V28 可視性の除外を外す) は現状 E (parse error) で、現行の検出力に数えられない。完了判定 = si の trace が現行 verifier に受理され、3 行それぞれに実測の分類 (D2239 五分類 + D2246 の状態) を書いた insight。論文の「無改変 si で巡回を検出」(2026-06-18、v1) を現行 verifier で取り直す根拠にもなる。

**親の実測 (brief 前):**
- si の emitter = `external/ccbench/cc/si/transaction.cc:526-555` (`#if TRACE`、`izanagi_trace::emit_commit` の v1 5 field C 行、E 行なし)。parser は 5 field C を `trace v1 C record is not supported` で拒否 (`orchestrator/verifier/parse.py:359-361`)、v2 は C 7 field + E 必須・件数照合 (`parse.py:356-410`・`:289-311`)。silo の v2 は transaction.cc 内で `stream()` を直接呼んで C 行を書き `emit_commit` を残した (`cc/silo/transaction.cc:594-616`・`:698`)。
- pin `e9e477ca` と pin C で `cc/si/` と `include/trace.hh` は同一 (`git diff --stat` 空)。設計書の SI 行番号はそのまま有効: 版選択 `read_internal` 153-158、first-updater-wins `install_version` 172-211 (inflight 176-186・committed 後 198-206)、update の read set 消去 239-247。
- 既存 driver は protocol を固定 (`s3_mocc_mutation_proof.py:185-190,225-226`、`s2_verify_calibration.py:202,325,328`)。si の driver・policy・patch は repo に無い。`patchharness.py` の `checkout`/`assert_pinned_clean`/`apply_patch`/`patch_files` は protocol 非依存。si の CMake target は `ycsb_si.exe` (`cc/si/CMakeLists.txt:1-8`)。YCSB flag は mocc と同名 (`ycsb_si.cc:23-51`)。
- verifier の `--protocol si` は受理済み、X/P/I は evidence-absent (`model.py:36`、`test_verifier.py:138-141`)。巡回が無ければ I、あれば N (`model.py:505-567`)。certified には届かない (設計書 §5.3)。
- 無条件 patch (裸マクロなし) は条件 gate・裸マクロ登録 test の対象外 (`s3_mocc_mutation_proof.py:106-107`、`test_p3_s4_loop.py:8489-8493`)。変異 patch の裸マクロは mocc と同じ 3 表 + test の allowlist へ登録が要る (`condition_meaning_gate.py:79,347,473`、`test_p3_s4_loop.py:8362`)。
- 既存被覆: decisions/failures に si v2 の実装記録なし。D297 近傍 (silo v2 化) は「SI の v2 化は当時の編集面外として見送り」。D16 の本来の置き場は `izanagi-trace` 枝だが、依頼が patch/local branch を明示し、D16 の T-109 例外と同じく `#if TRACE` 下の out-of-tree patch として置く。枝への移送と pin 前進は人間の判断。

**進め方 (DW-G01 生死確認を先頭に):**
- L0 (Codex author): `patches/instr-si-trace-v2.patch` (cc/si/transaction.cc の `#if TRACE` 内だけ、C 7 field + E 行、`trace.hh`・`tpcc.hh` 不変) と、repo 外起動器 (job dir、mocc の `launch_mocc_run.py` と同型、patch の積み重ね・build 一覧・cell 一覧を引数で受ける)。
- 生死確認 1 job (stock si + v2 patch、1/4 thread の write skew 条件): trace が framing violation 0 で verifier に受理され verdict が出るか。**不成立なら実装差分ゼロで事実を返して止める** (patch は commit しない)。
- 成立後: 段 2 plan (V28・V29 patch、V36 = 無改変、cell・期待の事前登録) → 段 3 相談 2 本 → 段 4 裁定 → 段 5 (V28・V29 patch + 条件 gate 登録) → 段 6 (review 2 本・実走・変異 matrix・受入) → 記録。

**(P1) 親の provisional 裁定・攻撃対象:** v2 化 patch は無条件 (裸マクロなし、`#if TRACE` の内側だけ)。V28・V29 は v2 patch の上に重ねる第 2 patch (mocc 旧経路の「計装 + 壊し」と同じ 2 段適用、両方 touch set = `cc/si/transaction.cc`)。
**(P2)** V36 の N は schedule 依存。巡回 0 なら I で「未発生」でなく「巡回の未観測」とし、証拠面が無いので S にはならないことを分類規則に書く。si の行は certified と呼ばない。
**(P3)** V28・V29 には D2239 と同じ発火診断 (reached/changed/committed を stderr へ 1 行) を付ける。

**不変条件:** 規律 2 (verifier・parser・driver・条件 gate の判定を変えない、壊し patch を baseline に混ぜない)。規律 1 (変更は `#if TRACE` の内側だけ、性能値を取らない)。pin を動かさない、共有 header を変えない。仮想リスク向けの gate・検査・台帳・一般化を足さない。

**成果物:** `patches/instr-si-trace-v2.patch`・V28/V29 patch + README 節、条件 gate 登録 (V28・V29 の macro)、repo 外起動器、insight `output/insights/2026-09-26/t2847-si-run/README.md`、worklog / decisions の fragment。

**計算 (D2212 項 4):** 生死確認 1 job ≈ 150〜200 秒。本走は build 3 本 (v2 / v2+V28 / v2+V29) × cell で 2〜3 job ≈ 400〜900 秒、焦点走 ≈ 150 秒 × 2、変異 matrix ≈ 1,400 秒、受入 ≈ 900 秒 × 2。合計 ≈ 1.2〜1.5 node 時間 < 2 の見込み。段 4 で再見積り、2 以上なら投入前にユーザー確認。

**実測環境:** 計算は Pegasus 計算ノード、`tools/pegasus/dispatch_compute.py --task generic` を計測用 detached worktree から (先例 mocc-run)。受入は `tools/dev_wave_wait.py acceptance --lease-optional`。
