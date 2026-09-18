単独段 dispatch: stage=review; sandbox=read-only; parent=/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2737-ss2pl-gate-controls

## レンズ A — 正しさ境界: 試作 patch と shadow 登録簿が gate の意味を骨抜きにしていないか、計算ノード receipt の主張は原データと一致するか

## 必読事項の射影 (読めなければ即停止)

- `/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2737-ss2pl-gate-controls/s4-ruling.md` — 段 4 裁定 (plan v2 = 実装の正本)
- `/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2737-ss2pl-gate-controls/codex-artifacts/dev-wave-t2737-ss2pl-gate-controls/s3-a.md` — 段 3 レンズ A (自分の前身。所見 A1〜A4 が裁定で採用済み)
- `/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2737-ss2pl-gate-controls/codex-artifacts/dev-wave-t2737-ss2pl-gate-controls/s5-author.md` と `s6-fix1.md`、`s6-fix2.md` — author / fix の最終報告
- `/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2737-ss2pl-gate-controls/probe/README-probe.md` — author の README (login 実走結果)
- `/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2737-ss2pl-gate-controls/probe/t2737_gate_probe.py` — probe 本体
- `/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2737-ss2pl-gate-controls/probe/patches/ss2pl-lock-protocol-study-define-only.patch` — revS (現行 patch との差は `diff` で取る)
- `/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2737-ss2pl-gate-controls/probe/patches/ss2pl-lock-protocol-study-define-only-abort-unconditional.patch`
- `/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2737-ss2pl-gate-controls/receipts/probe-result-2.json` — 計算ノード job 2 の受領証 (fix2 版 probe、45 cell、helper warm-up、plain build、shadow、static contracts。**主資料**) と `probe-result-1.json` (job 1、fix2 前。warm-up が内部例外で warm 系 cell は config.h 不在。ただし plain build 後の 16 cell は有効)
- `/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2737-ss2pl-gate-controls/compute-2.log` と `compute-1.log` — dispatch の stdout (request ID、node、rc)
- `/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2737-ss2pl-gate-controls/orchestrator/campaign/condition_meaning_gate.py` — gate (59-199、813-1000、1851-1950、2033-2118、2143-2330、2372-2471、2544-2712)
- `/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2737-ss2pl-gate-controls/patches/ss2pl-lock-protocol-study.patch` — 現行 patch
- `/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2737-ss2pl-gate-controls/external/ccbench/cc/ss2pl/transaction.cc` と `include/rwlock.hh` — stock

repo root は `/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2737-ss2pl-gate-controls`。**大きい file を全文 `cat` しない** (`grep -n` → `sed -n`、JSON は `python3 -c` で key を絞って読む)。

## 攻撃点

1. **試作 patch の骨抜き検査**: (a) S 経路 (IMPL=0/WFG=0/非 YCSB) の復元が stock 本文の復元であって再実装でないこと — `diff` で現行 patch と revS の差分を読み、stock の文と一致する行だけが戻されているか。DLR の `#ifdef DLR0/#elif defined(DLR1)` → `#if SS2PL_DLR == 0/== 1` 置換 5 組で分岐の意味が保たれるか (stock は `#if DLR0` の形も混在。数値 0/1 との対応)。(b) phase1 経路 (IMPL=1/KIND=0/DLR=0/WFG=1) の study lock・WFG 計器の呼び出しが現行 patch と同じか (author は local 前処理一致を主張。その検査 `work/check_phase1_projection.py` の射程)。(c) `include/rwlock.hh` の `class ReaderWriteLock` を `#if !defined(SS2PL_LOCK_IMPL) || SS2PL_LOCK_IMPL == 0` で囲む hunk が、SS2PL 以外の protocol (`cc/d2pl/include/transaction.hh` も rwlock.hh を include) の build を壊さないか (SS2PL_LOCK_IMPL は ss2pl target にしか define されないので `!defined` で stock 挙動、を検算)。(d) abort 増分の `#if defined(SS2PL_WORKLOAD_YCSB) && SS2PL_WORKLOAD_YCSB / #else` の形で、YCSB target の挙動が現行 patch と同じか。
2. **shadow 登録簿**: `registry_block()` / `shadow_bytes()` / `accept_shadow()` が裁定 A3 の受理条件 (repo bytes に許可置換だけを施した期待 bytes との全体一致) を満たすか。selftest の拒否例 (`inert_values` / `owner_tus` / 式 / 非 SS2PL / logic) が実際にその関数で拒否されるか (机上で追う)。`load_module` が正準 module を置き換えないこと (`sys.modules` の固有名、`__package__`)。receipt の `shadows[]` に identity 検算結果が残っているか。
3. **receipt の主張と原データの一致**: `receipts/probe-result-2.json` (主) と `probe-result-1.json` の各 cell の `observed_reason` と `supply_canonical_json` 内の `reason_code` が一致するか。`expected_reason` と `observed_reason` の不一致 cell を全部列挙し、裁定の予測表 (条件付き I は S 一致未達なら M) に照らして「予測どおり / 予測外」を判定。family admission の `admitted` 値。warm-up の前後 `config.h` 有無。pristine cell の `preprocess-failed` の detail に `config.h` が出ているか。plain build の rc と `_wfg_absence_evidence`。**親が書く予定の主張** (次項) をこの原データで検算。
4. **親の予定主張の検算** (insight に書く前): (i) 「非 inert 4 軸は試作 patch だけで green (登録簿変更なし)」、(ii) 「inert (S) は登録簿 target=tpcc + companion 除去でも `stock-inert-mismatch`、残差は `__LINE__` (ERR) の 1 行だけ (gate evidence の `root_diff_line_count`)」、(iii) 「warm-up 前は pristine で `preprocess-failed` (config.h)、`prepare_masstree_fetchcontent` 1 回の後は stock / patched 両木の前処理が通る」、(iv) 「abort 無条件版は S で `stock-inert-mismatch` の行数が revS より多い (負例対照)」、(v) 「D2120 が要求する stock 側 `ycsb_ss2pl.exe` / owner TU の比較は gate 不変では構造的に未成立 (owner-tu-unresolved)」。各主張を real / refuted / 原データ不足 で判定。
5. **規律 2 / 規律 1**: 試作が gate を緩める方向の何かを含んでいないか (例: 試作 patch 内の `#line`、gate が見ない場所へ差分を逃がす、shadow で `inert_values` を足す)。性能 build (WFG=0) に計器 TU が入らないこと (CMake の `wfg.cc` 条件維持) を patch で確認。

## 出力形式

所見ごとに: 番号、分類 (骨抜き / shadow / receipt 整合 / 主張検算 / 規律)、real / refuted と根拠 (file:line または receipt の key path)、放置時に insight の採否材料がどう変わるか 1 行、是正案 (fix が要るか、insight の書き方の修正か)。主張 (i)〜(v) は 1 つずつ判定を書く。`## 総括` (必須) 10 行以内: real 件数、最重要、fix 要否、insight に書いてよい主張と書いてはいけない主張。

## 禁止

file を作成・編集しない。git の状態を変えない。pytest を走らせない。走らせていない結果を緑と書かない。予算が尽きそうなら途中結論を出力形式どおり書いて終わる。
