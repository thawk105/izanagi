# 段 1 brief — [T-2737] SS2PL runner の condition gate 問題に対する対照材料 (2026-09-18 06:27 JST)

wave: `worktree-dev-wave-t2737-ss2pl-gate-controls` (main `d2ebef7a4`、clean)。job dir: `/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2737-ss2pl-gate-controls/`。

## 研究前進 (1 行)
SS2PL ロック規律スタディ (D790/D791、`docs/cc-diagnostics.md`) の `controls` / `sweep` mode は T-2018 の condition gate に全 arm を拒否されて 1 走も取れない。本 wave は gate を緩めずに runner を動かせる 2 案 (ii)(iii) の**採否材料**を計算ノードの実測で揃える。完了判定 = 下の cell matrix が 1 job で取れ、各 cell の gate `reason_code` と「何を変えれば通るか (patch / 登録簿 / runner の層別)」が insight に構造化されていること。

## 確定済みユーザー裁定 (D2120 項 12、2026-09-17)
- (i) gate の適用範囲を軸ごとに絞る案は**採らない (確定)**。gate 本体 (`orchestrator/campaign/condition_meaning_gate.py` の判定 logic) と runner の `controls` mode は現行のまま動かさない。
- (ii) patch の軸を define だけの差へ再設計する案、(iii) runner が warm-up (`config.h` 生成) を持つ案の採否は、代表的な inert / 非 inert arm で「gate 不変のまま必要な比較 (stock 側 `ycsb_ss2pl.exe` target / owner TU の成立を含む) が成立する」ことを示してから再提示する。**本 wave は再提示材料を作るだけで採否を決めない。**
- probe と再設計 patch の試作は job dir に置き repo へ入れない (`compute-probe-stays-out-of-repo`、T-317 未裁定につき実装面は Codex `role=author` が書く)。仮想リスク向けの gate・検査・台帳・一般化の追加は scope 外。規律 2 を緩めない。

## 一次資料 (読了済み) と現行事実 (実測または現物)
- `output/insights/2026-09-17/t2644-ss2pl-wfg-connect/README.md` §5 の 1〜3、`receipts/probe-result-{1,2}.json`、`receipts/gate-login-phase1-wfg.json`。
- gate の構造 (`condition_meaning_gate.py`): 要求ごとに **inert** (`requested == default` または `inert_values`) なら「patched 木 (要求値 + companion) vs **stock 木** (値なし + companion)」で前処理 bytes の**完全一致** (root path 置換のみ許容、`_classify_stock_inert_root_location_difference` は 1 行でも残渣があれば `stock-inert-mismatch`)。**非 inert** なら「要求値 vs 既定値 (同じ patched 木)」で comparable argv 一致 (`_preprocess_argv`: 試験 macro と companion だけ除外、inert 時は同 patch の全登録 macro を除外) + 依存閉包 (identity, sha256) 一致 + bytes 相違。owner TU は `_select_owner_entry` が `CMakeFiles/<target>.dir/` 配下の compile entry 1 件を要求。`_run_process` は **stderr 非空も失敗** (CMake の未使用変数警告で `configure-failed`)。
- runner (`tools/pegasus/run_ss2pl_lock_study.py:42-57, 1959-2045`): arm ごとに 4 軸を **全部** 要求、`default_value=AXIS_DEFAULTS` (0,1,1,0)、`stock_comparison = requested == default`。S = 全軸 inert、phase1 = 全軸非 inert、C = IMPL 非 inert + 他 3 軸 inert。
- 登録簿 (`condition_meaning_gate.py:184-199`): 4 macro とも `target="ycsb_ss2pl.exe"`、owner `cc/ss2pl/transaction.cc`、`SS2PL_LOCK_KIND` だけ companion `SS2PL_LOCK_IMPL=1`。**stock の `cc/ss2pl/CMakeLists.txt` は `WORKLOADS bomb tpcc`** で `ycsb_ss2pl.exe` を持たない (現物)。`ccbench_add_protocol` は workload ごとに `transaction.cc` を別 target で compile する (`external/ccbench/cmake/ProtocolHelpers.cmake:32-34`) ので、stock にも `CMakeFiles/tpcc_ss2pl.exe.dir/…transaction.cc.o` の entry は存在する。
- 現行 patch (`patches/ss2pl-lock-protocol-study.patch`): `IMPL=1` で `ss2pl_study_lock.hh`、`WFG=1` で `ss2pl_wfg.hh` を include し `wfg.cc` を source list に足す (閉包差)、`DLR` は CMake が `DLR0/1/2` marker を切り替える (argv 差)。新規 header 3 本は `#pragma once`。`INERT_DECLARED_DIFFERENCES` (runner:71-84) は S arm が stock と **意図的に違う** 3 箇所 (transaction.cc の abort 二重計数の除去、util.cc の出力、bomb) を宣言している。
- **親の前提実測 (login、g++ 11.4.0、`-E -P`):** 中身が全部 `#if` で消える header は include guard 形式なら出力 bytes に **0 byte** しか寄与しない (2 回 include・空行込みでも同一)。`#pragma once` は **7 空白 + 改行の残渣**を残す。→ (ii) で S arm を stock と byte 一致させるには新規 header を include guard にし、全差分を軸 macro で囲む必要がある。stock 側の header (`rwlock.hh` 等) の `#pragma once` は両側に等しく出るので問題ない。
- 既知の所要 (bnode、-j48、T-2644 実測): clone 0.5 s、warm-up 13 s、S build 12 s、phase1 build 5 s。gate 1 要求 = configure 2 回 + 前処理 2 回。
- 計算ノードは外部 net 不在。依存は hydrate 済み staging (`fetch_third_party.py hydrate --cache-root /work/1/SFC/tanab/izanagi-thirdparty-cache --staging-root <job dir>/thirdparty-src`、pristine = masstree `config.h` 無し) と `/work/1/SFC/tanab/ss2pl-study-deps/{gflags,glog}-install`。path に `wfg` を含めない (T-2644 §5.4)。generic dispatch は clean env・cwd = 投入 worktree。

## 割れうる前提 (親の provisional 裁定・攻撃対象)
- **(P1) inert arm の stock 比較は、登録簿の `target` を stock に実在する `tpcc_ss2pl.exe` (または `bomb_ss2pl.exe`) へ変えない限り構造的に成立しない** (`owner-tu-unresolved`)。patch 側だけでは閉じない。これは gate logic の変更ではなく「patch 由来の interface 宣言」(DefineSpec の docstring) の変更である、と親は位置づける。測定は job dir の **shadow 登録簿** (gate module の写しで登録簿の行だけ差し替え、logic bytes は diff で同一を示す) で行い、repo の gate は触らない。
- **(P2) KIND / DLR は IMPL に従属する軸なので、companion 付きでは inert (S arm の KIND=1 vs stock) が構造的に不成立、companion 無しでは非 inert (phase1 の KIND=0 vs 1) が `preprocess-bytes-identical` で不成立**。gate は「各軸が他軸の既定値のもとで効く (直交)」ことを要求する。(ii) の再設計はこの緊張を解く形 (a: KIND/DLR に IMPL=0 でも効く意味を与える、b: KIND を IMPL に畳む = runner の軸表も変わる) を選ばないと全 arm は通らない。**本 wave の試作は a/b を選ばず、緊張を cell で可視化する** (DLR は stock の `#ifdef DLR0/DLR1` 分岐を `SS2PL_DLR` へ付け替えれば IMPL=0 でも効く見込み。KIND は試作では IMPL 従属のままにし、shadow 登録簿で companion を外した cell と外さない cell の両方を取る)。
- **(P3) S arm の byte 一致は `INERT_DECLARED_DIFFERENCES` の 3 箇所と衝突する。** transaction.cc の abort 二重計数除去は `SS2PL_WORKLOAD_YCSB` (ycsb target だけの define) で囲めば tpcc target の gate 比較では stock と一致するが、実測する `ycsb_ss2pl.exe` の TU とは別 TU を認証することになる (TU / arm 束縛の隙間、D2120 項 8 の (3) と同じ型)。親はこれを (ii) の**費用**として insight に明記し、隠さない。
- **(P4) (iii) の必要な比較** = 同じ pristine staging で「warm-up 前: gate 前処理が `config.h` で `preprocess-failed`」「`masstree_build` 1 回の warm-up 後: stock / patched 両木の前処理が通り、失敗理由が (ii) の drift または green へ移る」を 1 job 内の対で取る。warm-up は共有 `thirdparty-src/masstree` の source dir に書くので 1 回で両木に効く見込み。
- **(P5) 試作 patch は gate を通すための最小改変**: 新規 header の include 無条件化 + 中身の `#if` 囲い + include guard 化、`wfg.cc` の無条件 compile、CMake の `DLR1` marker 固定と `SS2PL_DLR` 純 define 化、`ss2pl_lock.hh` の `#error "SS2PL_DLR=n requires DLRn"` 撤去、abort 二重計数除去の `SS2PL_WORKLOAD_YCSB` 囲い。**新しい lock 意味論は足さない**。試作が両 arm で `-Wall -Wextra -Werror` で build できること (plain build、trial は走らせない) と、runner の静的契約 (`validate_abort_counter_ownership`、`_study_lock_header_declarations` / `validate_default_stock_lock_absence` の入力) をどう満たす/破るかも材料に含める。
- **(P6) 変異 matrix は免除** (repo の実装面差分 0、`DW-S04`)。受入全走は免除しない。probe の fail-closed は `--selftest` に置いて親が login で実走する。

## scope 外 (書くだけ)
runner の `controls` / `sweep` の実走、性能値、D790 の inert 性の証明、B/D arm (DLR=2) の直交化、登録簿・patch・runner の本改修、gate の変更、T-2738〜T-2741。

## 成果物の形
- `output/insights/2026-09-18/t2737-ss2pl-gate-controls/README.md`: cell matrix (arm × 軸 × {現行 patch, 試作 patch} × {現行登録簿, shadow 登録簿} × {pristine, warm-up 後}) の `reason_code` 表、(ii)(iii) それぞれの「成立した比較 / 成立しない比較 / 成立に要る変更の層 (patch / 登録簿 / runner)」、費用と隙間 (P3)、再提示用の裁定パッケージ案 (採否は書かない)。
- `receipts/`: 計算ノード job の probe 結果 JSON、shadow 登録簿の diff (`.diff.txt`)、試作 patch の sha256 と byte 数。`verbatim/`: brief、plan、レンズ 2 本、裁定、レビュー 2 本、probe と試作 patch の逐語 (`.md`)。
- `docs/spool/` の worklog / decisions fragment。repo の実装面差分は 0 byte。

## 分割方針
段 2 plan 1 本 (read-only) → 段 3 レンズ 2 本 (A: 正しさ境界 = gate の意味を試作が骨抜きにしていないか・規律 2、B: 整合と実効性 = cell matrix が裁定に足りるか・runner 契約・計算ノード運用の穴) → 段 4 裁定 → 段 5 author 1 単位 (probe worktree `.codex/worktrees/t2737-probe`、成果物 = 試作 patch + probe + shadow 登録簿生成、親が job dir へ退避) → 親が login で selftest と S arm 前検査 (configure + `-E -P` は login で可) → 段 6 計算ノード 1 job (generic dispatch、walltime 00:30:00) + レビュー 2 本 → 段 7〜9。

## 変更面アンカー表 (repo 内は docs / insight のみ)
| 面 | path | 種別 |
|---|---|---|
| insight | `output/insights/2026-09-18/t2737-ss2pl-gate-controls/**` | 新規 (docs) |
| spool | `docs/spool/<wave>-worklog.md`, `docs/spool/<wave>-decisions.md` | 新規 (docs) |
| job dir | `/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2737-ss2pl-gate-controls/{probe/, shadow/, patch/, thirdparty-src/, scratch/}` | repo 外 |
| 読む only | `orchestrator/campaign/condition_meaning_gate.py`, `tools/pegasus/run_ss2pl_lock_study.py`, `patches/ss2pl-lock-protocol-study.patch`, `external/ccbench/cc/ss2pl/**`, `external/ccbench/cmake/ProtocolHelpers.cmake` | 不変 |

[T-2772] 系稼働 wave (mocc auditor-live) の編集面 (DefineSpec 登録簿・materializer_admission・裸 define 登録簿・`patches/broken-mocc-hot-update-unlock.patch`) と本 wave の編集面は素集合 (06:20 JST に相互通知済み)。
