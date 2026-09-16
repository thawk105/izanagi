# [T-2644] SS2PL の待ちグラフ計器と検証器を接続し、計算ノード 1 走の実データで D791 の 4 条件を独立判定した

- 日付: 2026-09-17。branch `worktree-dev-wave-t2644-ss2pl-wfg-connect`、基底 main `20a92f6a6`。
- 統合 commit: `3204f48b2` (patch / runner / test、Codex `role=author`)。
- 一次資料 (この dir): `receipts/` (計算ノード 3 走の結果 JSON、login の gate CLI 出力、実走の stdout と durable file)、
  `verbatim/` (段 1 brief、段 2 plan、段 3 レンズ 2 本、段 4 裁定、段 6 レビュー 2 本、実機事実 2 本、probe 本体の逐語)。
- 起票: worklog entry 1507 の T-2644。受理条件の正本は D791。scope は「本題の接続だけ」。

## 1. 何を接続したか (6 件)

起票は 3 件 (伝達・field 名 4 箇所・出力先 flag) だったが、段 1 の前提実測と段 2 の plan で 3 件増えた。

| # | 断絶 | 修正 (どこに) |
|---|---|---|
| 1 | 伝達: 計器は指定 file へ最終 JSON 1 枚、検証器は標準出力の event を読む | 計器 (`wfg.cc`) が閉路の立った watchdog tick ごとに 1 行 JSON event を標準出力へ出す (`cout_mutex` + `flockfile` の中で `fwrite` 1 回 + `fflush`)。durable file には最後に emit した同じ文字列を書く |
| 2 | node の field 名 (`waiting_lock_id` / `requested_mode` ↔ `wait_lock_id` / `request_mode`) | 計器を検証器の名前に揃え、`held_locks[{lock_id, mode}]` (同 snapshot の保持一覧) を足した。schema は `ss2pl-wfg/v2` |
| 3 | 辺の field 名 (`waiter` / `holder` ↔ `waiter_thread_id` / `holder_thread_id`) | 同上。`compatible:false` を付け、holder の保持一覧に無い辺は出さない (架空の write holder を出す fallback を廃止) |
| 4 | runner が出力先 flag を渡さない (計器は `chkArg` で必須) | `_run_phase_trial` が trial ごとの directory を `mkdtemp` で作り `-ss2pl_wfg_output=<dir>/final.json` を渡す |
| 5 | **build 軸の表示行 `ShowOptParameters()` は全 worker join 後にしか出ない** (`external/ccbench/common/runner.hh:316`) ので、hang して kill された走行では `_admit_output` が `parse_runtime_axes` で必ず落ちる (段 1 で発見) | `ycsb_ss2pl.cc` の `chkArg()` 直後に `#if SS2PL_WFG_DIAG` の中で `ShowOptParameters()` を呼ぶ |
| 6 | **排他 lock (`KIND=0`) で計器は read 操作を `read` と出す**が、検証器の `_edge_is_incompatible` は read/read を両立と判定するので、read holder を含む実閉路が拒否されうる (段 2 で発見) | `mode_name` を `IMPL=1 && KIND=0` では全箇所 `"write"` (study lock は `writer_` に格納する排他 1 種) にした。検証器は変えない |

検証器 (`validate_deadlock_evidence`、`_extract_snapshots`、`_holder_evidence`、`_edge_is_incompatible`、`_admit_output`) は
**変更していない** (規律 2)。計器の追加はすべて `wfg.cc` (CMake で `WFG_DIAG=1` のときだけ sources に入る) か
`#if SS2PL_WFG_DIAG` の内側 (規律 1)。patch は現行 pin `511c9538` へ `git apply --check` rc=0。

runner はさらに、trial directory に生の `stdout.txt` / `stderr.txt` を保全し、受領証に `wfg_output`
(`path` / `status` / `sha256` / `json` / `error`) と `stdout_path` / `stderr_path` を残す。file は受理条件にも
代用証拠にもしない (段 3 レンズ B の所見 B-10、段 4 裁定)。

## 2. 実データ — 計算ノード 1 走 (probe 3 走目)

request `0:2339.nqsv`、bnode007、2026-09-17 01:48 JST。計装 build (`IMPL=1 KIND=0 DLR=0 WFG=1`)、動作点は高競合
(`ycsb_tuple_num=100`、zipf 0、48 threads、extime 10 s、hard timeout 60 s)。結果は `receipts/probe-result-3.json`
(`trial` 節が runner の `_run_phase_trial` の受領証そのもの)、実 stdout は `receipts/probe-3-trial-stdout.txt`
(12 行、3,198 bytes、sha256 `c98ea15b033a54c55dca34b77bd0d4a236f51609aac7dbf0ce4bd3c418784bf4`)。

| D791 の条件 | 検証器が使った判定材料 (受領証の field) | 実値 |
|---|---|---|
| 1. 各辺が「待ち手 → その lock の実 holder」で mode が非両立 | edge の `lock_id` == waiter の `wait_lock_id`、holder の `held_locks` に同じ `lock_id` と `mode`、`_edge_is_incompatible(request_mode, holder_mode)` の再導出 | 辺 16→21 (lock `0x14d33800a740`) と 21→16 (lock `0x14d33800b1c0`)。holder の `held_locks` に一致。write/write |
| 2. 連続 3 snapshot で node 属性と辺 topology が同一 | `_node_signature` と `_edge_signature` を 3 枚で比較 | tick 5 / 6 / 7 の 3 枚、`snapshot_indexes=[0,1,2]`。node は thread 16・21、attempt 1 |
| 3. commit / abort counter が不変 | `_node_signature` に含む `commit_count` / `abort_count` | 両 thread とも commit 0 / abort 0 (最初の transaction で詰まった。原 study の報告と同じ) |
| 4. hard timeout で終了 | `_run_process` の `timed_out` / `termination` / `returncode` | `timed_out=True`、`termination="kill"` (SIGTERM に応答せず SIGKILL)、`returncode=-9`、所要 62.1 s |

`accepted_cycle` は非 None、`cycle_observed=True`、`conflict_count=41`。durable file (`receipts/probe-3-trial-final.json`、
sha256 `fecb3b1e…`) は標準出力の最後の event 行と byte 一致した。閉路は走行開始から約 50 ms (tick 5) で立った。

**独立性の射程 (段 3 レンズ A の限定):**
- `held_locks` は計器の registry の写しであり、検証器はそれと辺との**照合**と非両立性の**再導出**を行う。registry
  自体の正しさ (取得成功後に登録、登録削除後に実 unlock、という順序) は信頼境界である。
- 条件 3 の counter は `TxExecutor::begin()` で写された attempt 開始時の値で、`attempt` が変わらない限り構造上不変。
  独立な進行監視ではなく、attempt 不変と冗長である。値そのものは閉路中の thread が更新箇所へ進めないので正しい。
- 計器は閉路の立った tick だけ event を出し、tick 番号は data として載せる (5, 6, 7 と連続していた)。検証器は emit 列の
  上で連続 3 枚を見る。phase1 (排他 + wait) では閉路が消えて同じ signature で再出現する経路は構成できない
  (取得は実 lock 成功後に registry へ、解放は registry 削除後に実 unlock、DLR0 は blocker が居る間 loop する) が、
  検証器単体が任意の欠番入力を拒否するとは主張しない。
- 条件 4 は「同一走行が hard timeout で終わった」ことであり、「kill まで閉路が持続していた」ことは観測していない
  (watchdog は連続 3 回一致で file を書いて止まる)。D791 の逐語はそこまで要求しない。

## 3. 規律 1 の実測 — 性能 build に計器が無いこと

同じ走 (probe 3) で、性能 arm `S` (`IMPL=0 KIND=1 DLR=1 WFG=0`、stock 逐語) も同じ patched clone から build し、
production の `_wfg_absence_evidence` を新 patch で取り直した (`receipts/probe-result-3.json` の `absence_S.wfg_absence`)。
前処理した 3 TU に計器の識別子なし、symbol なし、binary の軸 label は `ShowOptParameters` の 1 箇所のみ、
population 検査 OK。binary sha256 `dd910551…`。

probe 2 走目では同じ検査が赤になったが、hit はすべて **path 文字列に含まれる `wfg`** (job dir 名
`dev-wave-t2644-ss2pl-wfg-connect`) で、計器の痕跡は無かった (`receipts/probe-result-2.json`、`verbatim/s6-fix-b2-facts.md`)。
`_wfg_text_hits` は前処理出力の行マーカと binary の `__FILE__` 文字列を path ごと総当たりする。3 走目は scratch と
thirdparty を `wfg` を含まない path へ移して取った。

## 4. probe と production の差 (F29)

1 走は `tools/t2644_wfg_probe.py` (Codex author、repo へは commit しない。逐語は `verbatim/probe.md`、
sha256 `8ed60cba…`、16,218 bytes) が runner の production 関数を呼ぶ形で行った。

| 項目 | probe の扱い | `accepted_cycle` への影響 |
|---|---|---|
| required commands・thirdparty pin・canonical submodule の検査 | production 関数を呼び結果を保存 | なし |
| stock / patched の clone、patch 適用、abort 所有権検査 | production 関数 (`clone_network_free`、`_apply_patch`、`validate_abort_counter_ownership`) | なし |
| **build の admission (condition gate)** | **通していない** (§5)。configure / `cmake --build` / `_find_binary` / `_target_compile_entries` / `_validate_compile_definitions` / cache 照合 / sha256 は production 関数 | gate は build の define 効果を検査するもので、閉路の判定材料には入らない |
| masstree の warm-up | probe が `masstree_build` target を先に 1 回 build (§5) | なし |
| trial・admission・timeout・閉路判定 | **production の `_run_phase_trial` をそのまま** | これが対象 |
| PBS job id | env には届かないので dispatcher の `compute-visible.json` から best-effort で採取 | なし (記録のみ) |
| inert witness、性能 arm 全体、sweep / controls matrix、plot、`validate_phase_matrix` | 省略 | なし。**D790 の inert 性や `controls` mode 全体の成立は示していない** |
| 単一 trial (高競合点 1 回) | 12 trial の観測機会・分布とは異なる | 述語は同じ |

## 5. 発見した既存の不整合 (本 wave では直さない、別起票)

probe 1・2 走目 (`receipts/probe-result-1.json`、`probe-result-2.json`) と login の gate CLI (`receipts/gate-login-*.json`) で確定した。
いずれも T-2018 (2026-08-27) の condition gate 導入以来、SS2PL runner の `build_target` が一度も実走していなかったことによる。

1. **inert な arm (S) は gate が stock 木を対照にする**が、stock の ss2pl には `ycsb_ss2pl.exe` target が無く (patch が足す)
   owner TU が解決できない (`owner-tu-unresolved`)。companion define `CCBENCH_SS2PL_LOCK_IMPL` を stock に渡すと CMake の
   未使用警告が stderr に出て `configure-failed`。
2. **非 inert な arm (phase1) は依存閉包と argv の drift で拒否される** (`dependency-closure-drift` / `compile-command-drift`)。
   この patch は `IMPL=1` で `ss2pl_study_lock.hh`、`WFG=1` で `ss2pl_wfg.hh` を include し、`DLR` は CMake が `DLR0/1/2`
   marker を切り替える設計なので、「define 1 個だけの差」を要求する gate とは構造的に合わない。
3. **pristine な thirdparty staging では masstree の `config.h` が無い**ため、gate の前処理が `fatal error: config.h` で落ちる。
   `config.h` は `masstree_build` custom target (bootstrap + configure + make、in-source) が生成する。production の `run()`
   (inert witness も前処理する) も同じ理由で pristine staging では落ちる。永続 cache に `config.h` が残っているため
   T-2213 の gate 実測は通っていた。
4. `_wfg_text_hits` は path 文字列の `wfg` で偽陽性になる (§3)。
5. 検証器は node と edge の**両側**で `request_mode` が欠けると `None == None` で通す (段 3 レンズ B の所見)。計器は
   field を出すので実データでは起きないが、既存の受理限界として記す。
6. phase2 (No-Wait) の `_phase2_counters` が要求する `acquisition_paths` は計器がまだ出さない。`controls` mode は接続後も
   phase2 で `ContractError` になる。
7. `tools/pegasus/ss2pl_lock_study.sh:207` は policy の `gflags_source_path` を読むが、T-548 で同 key は `gflags_source_url` に
   変わっており launcher は `dependency_policy` 段で落ちる。

## 6. test と変異 matrix

追加 test (`orchestrator/tests/test_ss2pl_lock_study.py:1480-`): (a) 実 stdout を逐語で写した fixture
(sha256 一致を assert) が `_json_events` → `_extract_snapshots` → `validate_deadlock_evidence(timed_out=True)` で受理され
`timed_out=False` で None、(b) 旧 field 名 3 種は各単独で None、(c) `held_locks` 欠落・lock id 不一致・mode 不一致で None、
(d) 起動時軸行 + workload 行だけの stdout で `_admit_output(require_metrics=False)` が通る、(e) 実 `_run_phase_trial` を
`_run_process` だけ差し替えて呼び、flag 1 個・絶対 path・trial ごとに異なる path・受領証の `wfg_output` /
`stdout_path` の内容一致・file 不在 / 不正 JSON / 不正 UTF-8 / 読取失敗の各 status・性能経路に flag が無いこと、
(f) 全 mode write は受理、read/read は None。焦点走 (login、bounded local): 103 passed (2 回)、`test_hooks.py -k ss2pl`
1 passed。既存 3 test の期待値は変えていない。

変異 matrix: 段 4 で 11 件 (等価 1 + 負例 10) を登録し (`mutation-spec-final.json`、sha256 `c17dde25…`)、統合 commit
`3204f48b2` の detached worktree (job dir 内) で `tools/mutation_harness.py --runner-mode dispatch` により
`run_tests.py orchestrator/tests/test_ss2pl_lock_study.py --force-dispatch` を走らせた。C++ (patch) 側の変異は login で compile
できず Python test では検出できないので登録せず、実 stdout を逐語で写した fixture との一致 (§2) を契約感度の根拠にした。

先に probe 走 (`mutation-spec-probe.json`、全件 SURVIVED 登録) で観測 node を集め (`mutation-ledger-probe.json`)、
段 6 レビュー B の静的予測と完全一致したのを確かめてから本走した。

**本走 (`mutation-ledger-final.json`): baseline PASSED、負例 10 件すべて KILLED、期待 node と観測 node は 11/11 一致、
等価変異 m0 は SURVIVED、MISMATCH 0、TIMEOUT 0。**

| id | 変異 | KILLED した node |
|---|---|---|
| m0 | (等価) `_wfg_fixture_workload` の dict 構築法 | SURVIVED (対照) |
| m1 | runner: `-ss2pl_wfg_output=` の付与を削除 | (e) |
| m2 | runner: trial dir を固定 path に | (e) |
| m3 | runner: `wfg_output.sha256` を None 固定 | (e) |
| m4 | runner: `stdout.txt` を空で書く | (e) |
| m5 | runner: `_extract_snapshots` の top-level 枝を削除 | (a)(b)×3(c)×3(e)(f) の 9 node |
| m6 | fixture: tick 6 の commit_count を +1 | 同 9 node |
| m7 | fixture: tick 7 の `held_locks` を削除 | 同 9 node |
| m8 | fixture: tick 7 の `compatible` を削除 | 同 9 node |
| m9 | test (d): 起動時軸行を除外 | (d) |
| m10 | runner: 性能 argv に `-ss2pl_wfg_output=x` を追加 | (e) |

## 7. 主張しないこと

- 計器の registry が実 lock 状態と常に一致すること (§2 の信頼境界)。
- `controls` mode の 12 trial や study 全体が現行 runner で動くこと (§5 の 1〜3、6、7 が塞ぐ)。
- D790 の inert 性 (inert witness は取っていない)。性能への影響 (計測していない)。
- 他 protocol への配線。tick の欠番を検証器が拒否すること。

## 8. 工数

codex 子 10 本 (plan 1、consult 2、author 2、review 2、fix 3。全段 `gpt-6-astra` / `medium`)。計算ノード job 4
(probe 1〜3、provenance 監査 1)。login の gate CLI 2 回。所要は段 1 開始 00:24 から統合 commit 02:00 まで約 1 時間 36 分。
