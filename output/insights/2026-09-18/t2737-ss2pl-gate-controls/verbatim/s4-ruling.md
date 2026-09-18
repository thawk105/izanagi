# 段 4 裁定 — [T-2737] (2026-09-18、親)

段 2 plan (`codex-artifacts/.../s2-plan.md`)、段 3 レンズ A (`s3-a.md`、正しさ境界) / B (`s3-b.md`、整合と実効性) を読み、各所見を裁定した。裁定 inbox の再走査 (D2121〜D2134、spool 3 dir、`grep` で SS2PL / condition gate / T-2737): 本件を止める裁定は無い。**新事実 1 件: D2131 (2026-09-18) が (iii) の既存実装形 (`prepare_masstree_fetchcontent`) を示す** → 下の「(iii) warm-up の形」に反映。

## 所見の裁定

| # | 所見 | 判定 | 採否 / plan v2 への反映 |
|---|---|---|---|
| A1 | tpcc target での S 一致は D2120 が要求する YCSB target の stock 比較の成立ではない | real | 採用。insight は shadow-T の結果を「機構診断」とし、「必要比較 (stock 側 `ycsb_ss2pl.exe` / owner TU) は gate 不変では構造的に未成立」と書く。P3 の「費用」表現を撤回 |
| A2 | `wfg.cc` 無条件 source は runner の `validate_wfg_absence` が source 名で拒否 (R:353) | real | 採用、ただし是正は plan の変更: **`wfg.cc` は CMake 条件付きのまま** (owner TU の閉包に無関係。WFG の閉包差は `ss2pl_wfg.hh` の include 無条件化 + 中身の `#if` 囲いで閉じる)。plan #1 の「SOURCES に wfg.cc 無条件」と #6 は撤回 |
| A3 | shadow の受理条件が「許可行以外 byte 同一」では弱い | real | 採用。probe は固定 repo bytes から O/T+/T− を**生成**し、生成物 == 期待 bytes (許可置換 = 4 行の `target` 値、T− は KIND companion の空 tuple 化のみ) を受理条件にする。selftest に `inert_values` / `owner_tus` 混入の拒否例。import 前後で正準 gate module・`source_digest`・package 属性の identity と path を記録 |
| A4 | 「`#pragma once` 残渣は両側同じ」は未証明 | real | 採用。brief の当該行は login 観測に限定。author の `-E -P` + `cmp` は前検査、最終根拠は計算ノード gate receipt |
| A5〜A8 | DLR 数値化は再実装でない / arm 全体の意味保証は主張していない / 追加負例 cell 不要 (abort 無条件版が負例対照) / 44 cell 化は逸脱でない | refuted | そのまま。abort 無条件版を負例対照と明記し、2 版差分が abort ブロックだけであることを probe が検算 |
| B1 | revS/T+/phase1/KIND (固定 target で companion だけ違う対照) が欠ける | real | 採用。**45 cell** |
| B2 | 予測表と変更層の対応表を revS に合わせる | real | 採用 (下表) |
| B3 | inert witness (`collect_inert_witness`) は宣言不一致 flag が false になりうるが拒否はしない | real | 採用。insight に「未実走。契約例外ではない」と書く |
| B4 | pristine staging の保存と attempt 複製 | real | 採用。保存用 `<job dir>/thirdparty-src` から `cp -a` で attempt 固有 staging を作り、pristine → warm-up → warm の全 cell を同じ複製で取る。realpath / config.h 有無 / 生成後 hash を保存 |
| B5 | clean env の一時領域・出力先の記録 | real | 採用。`tempfile.gettempdir()`、空き容量、realpath、`c++` / `cmake` の realpath と version を receipt 先頭に |
| B6 | 打切り優先順位を実行順へ | real | 採用。順序 = pristine 8 → warm-up → 対応 warm 8 → KIND 固定 target 対 → abort 対照 4 → plain build 2 → 残り。cell ごと try/except/finally + atomic 保存、予算未実施と内部例外を gate red から分ける |
| B7 | hostname fallback の PBS_JOBID は候補扱い | real | 採用。probe は候補として記録、親が dispatch receipt で照合 |
| B8 | configure-failed の全文診断 | real | 採用。失敗 cell では同じ引数の診断 configure を別に走らせ stdout/stderr 全文を保存 (原判定は置換しない) |
| B9〜B11 | runner 3 契約の読み / shadow / scope | refuted | そのまま |

brief の誤り訂正: 登録簿は `condition_meaning_gate.py:160-176` (brief の 184-199 は誤り)。`INERT_DECLARED_DIFFERENCES` の順は bomb / transaction / util。

## plan v2 (確定)

### 試作 patch (job dir のみ、repo へ入れない)
1. **`ss2pl-lock-protocol-study-define-only.patch` (revS)** = 現行 patch からの派生。plan #2 (`ss2pl_lock.hh` include guard 化、`#error DLRn` 撤去、`rwlock.hh` と `ss2pl_study_lock.hh` の無条件 include、alias だけ `#if IMPL==1`、`IMPL==0 && DLR==2` は `#error`)、#3 (`include/rwlock.hh` の `class ReaderWriteLock` だけ `#if !defined(SS2PL_LOCK_IMPL) || SS2PL_LOCK_IMPL == 0` で囲む hunk、`#pragma once` は保持)、#4 (study header の include guard 化、依存 include は無条件、宣言・定義は全部 `#if IMPL==1` 内)、#5 (`ss2pl_wfg.hh` の include guard 化、`<cstdint>` `<string>` 無条件、宣言は `#if WFG` 内)、#7 (transaction.cc の WFG header include 無条件化、stock の DLR 分岐 5 組を `#if SS2PL_DLR == 0 / #elif SS2PL_DLR == 1` へ)、#8 (abort 増分を `#if defined(SS2PL_WORKLOAD_YCSB) && SS2PL_WORKLOAD_YCSB` の else 側へ戻す)、**+ S 復元**: plan §2 末尾の表 (common.hh の legacy DEFINE/DECLARE 削除、transaction.hh の include 位置と constructor 出力形、`begin()` の 1 行定義、`update()` の構造、`delete_record()` の `break`、既取得ロック検査の移動、`unlockList()` の brace) を、S (IMPL=0,KIND=1,DLR=1,WFG=0) かつ非 YCSB のときに stock と同じ前処理 bytes になるよう復元する。**新しい lock 意味論は足さない。KIND を IMPL=0 で人工的に効かせない。** CMake: `_ss2pl_dlr_marker` 分岐を撤去し `OPTIONS DLR1` 固定、**`wfg.cc` は `if(CCBENCH_SS2PL_WFG_DIAG EQUAL 1)` の条件付きのまま**、4 軸 define と `SS2PL_WORKLOAD_YCSB` は維持。
2. **`…-abort-unconditional.patch`** = revS との差分が #8 のブロックだけ (abort 増分を現行どおり無条件除去)。probe が 2 版の diff を検算し「abort ブロックのみ」を受領証に残す。負例対照 (A7)。
3. author は login で、stock clone と revS clone を同じ `configure_args` で configure (login で可) し、tpcc target の `transaction.cc` compile entry を `-E -P` で前処理して `cmp` する。一致に届かなければ残差 diff の先頭 (path 差以外) を `README-probe.md` に書く。**届かないことを隠さない。** 復元は「固定した範囲」で行い、届かなければ残差が成果物。

### shadow 登録簿 (probe が生成)
- `--shadow-root` 配下に `<patch-id>/<registry-id>/orchestrator/campaign/condition_meaning_gate.py` + `patches/ss2pl-lock-protocol-study.patch` (対応する試作をこの名前でコピー)。patch-id ∈ {current, revs, abort-unconditional}、registry-id ∈ {O, T+, T−}。
- 生成は SS2PL 4 entry の完全一致 block 置換。受理条件 = 生成 bytes が「repo gate bytes に許可置換だけを施した期待 bytes」と一致。O は repo と byte 同一。
- 読込は `importlib.util.spec_from_file_location("orchestrator.campaign._t2737_gate_<id>", path)` → `sys.modules` 登録 → exec。`__package__ == "orchestrator.campaign"`、`source_digest.__file__` が repo、`_patch_changed_paths` が shadow patch を指すこと、正準 `orchestrator.campaign.condition_meaning_gate` の identity が前後で不変なことを記録。record は同じ module instance で閉じる。

### cell (45) と条件付き予測 (warm 後、軸順 IMPL/KIND/DLR/WFG)
| patch / 登録簿 | S | phase1 |
|---|---|---|
| current / O | O / C / O / O | D / E / A / D |
| current / T− | M / M / M / M | — |
| revS / O | O / C / O / O | E / E / E / E |
| revS / T+ | I / C / I / I | KIND のみ: E |
| revS / T− | I / I / I / I | E / B / E / E |
| abort-uncond / T− | M / M / M / M | — |

O=`owner-tu-unresolved`、C=`configure-failed` (stock への companion 未使用警告)、D=`dependency-closure-drift`、A=`compile-command-drift`、M=`stock-inert-mismatch`、B=`preprocess-bytes-identical`、E=`requested-default-preprocess-different`、I=`stock-inert-preprocess-identical` (または gate が認める root-location-only)。pristine = current/O/phase1 (4) と revS/T−/S (4) で全軸 `preprocess-failed` (stderr に masstree `config.h` 不在)。meaning は全 cell `unestablished / meaning-witness-undeclared`。**I は revS が S 一致に届いた場合の条件付き予測**であり、届かなければ M。

変更層の対応: inert (S) = patch の bytes 復元 + 登録簿 target 変更 (+ KIND は companion 除去)。IMPL = header の閉包固定。WFG = owner の `ss2pl_wfg.hh` include 無条件化。DLR = marker 固定 (argv) + 分岐の `SS2PL_DLR` 化 (効果)。KIND = companion ありで既に green。

### (iii) warm-up の形 — 段 4 直前の裁定 inbox 再走査で見つかった新事実 (D2131、2026-09-18)
D2131 (t316 probe) が示すとおり、condition gate の緑は永続 cache の残留 `config.h` に依存していて、**緑の既知例 (A-2、backoff_sweep 等 9 driver と t316) はすべて既存 helper `orchestrator/campaign/buildcache.prepare_masstree_fetchcontent` で masstree を準備してから関門へ供給している**。SS2PL runner だけがこれを欠く。したがって (iii) の実体は「runner に他 driver と同じ `prepare_masstree_fetchcontent` 呼び出しを関門前に 1 段足す」であり、probe の warm-up もその helper で行う (T-2644 probe の生 `cmake --build --target masstree_build` は D2131 が direct-cmake-target sink として却下した形なので使わない)。呼び方は t316 probe (`tools/pegasus/probes/t316_sandbox_backend_probe.py:1905-1930`) と同じ: `manifest = buildcache.observed_toolchain_manifest("cc", "c++")` → `prepare_masstree_fetchcontent(ccbench_dir=<revS clone>, fetchcontent_base_dir=<attempt scratch>/fetchcontent, expected_toolchain_manifest=manifest, configure_timeout_s=300, target_timeout_s=600, dependency_prefix="<gflags>;<glog>", masstree_source_dir=<attempt staging>/masstree, mimalloc_source_dir=…, googletest_source_dir=…)`。関門の configure_args には `-DFETCHCONTENT_BASE_DIR` を渡さない (D2131 項 4 と同じ。runner の `_require_condition_gates` も渡していない)。`config.h` は staging の masstree source dir に生成されるので stock clone の configure にも効く — 効いたことは stock 側 cell の前処理成功で示す。

### 実行順 (B6) と付帯
pristine 8 → warm-up (`prepare_masstree_fetchcontent` 1 回、上記) → 対応 warm 8 (current/O/phase1、revS/T−/S) → revS/T+/phase1/KIND + revS/T−/phase1 (4) → abort-uncond/T−/S (4) → plain build (revS S と phase1 の `ycsb_ss2pl.exe`、`-Werror`、`_target_compile_entries` + `_validate_compile_definitions`、S build に `_wfg_absence_evidence`) → 残り (current/O/S、current/T−/S、revS/O/S、revS/O/phase1、revS/T+/S) → runner 静的契約 (`validate_abort_counter_ownership` を 2 版で、`_study_lock_header_declarations`)。各 cell に `expected_reason` / `observed_reason` / 秒 / patch・registry・staging ID / canonical record。walltime 00:40:00。

### 成果物・免除
repo の実装面差分 0 → 変異 matrix 免除 (DW-S04)。受入全走は免除しない。probe の fail-closed は `--selftest` (親が login で実走)。insight は採否を書かず、(ii)(iii) の「成立した比較 / 成立しない比較 / 必要な変更層 / 隙間」を 1 表にし、A1 の限定 (shadow-T は機構診断、YCSB stock 比較は gate 不変で未成立) を先頭に置く。

### 段 5 の所有
Codex author 1 単位、worktree `/work/1/SFC/tanab/izanagi/.codex/worktrees/t2737-probe` (branch `probe-dev-wave-t2737-gate-controls`、base d2ebef7a4)。成果物は同 worktree の untracked dir `probe-t2737/` に置く (tracked file は編集しない、commit しない)。親が実行後に job dir へ退避し worktree から消す。
