# 段 1 brief — [T-2227] `BACKOFF_NOINLINE` の runtime-meaning を枝選択 witness で確立し、未確立のまま `paper` へ受理される形を狭める

## scope (これだけ)

D1569 を実装する。`BACKOFF_NOINLINE` の意味の節 (runtime-meaning arm) に D1490 の compile-time
枝選択 witness を registry の factory (`declare_define_runtime_meaning`) から発行させ、宣言を作らない
driver で常に `unestablished` のまま promotion class (`paper`) の admission を通っている形を、
「witness が green なら受理・red なら拒否」へ狭める。旧 `MeaningWitnessDeclaration` と CLI の
宣言経路は `BACKOFF_FIXED` に固定したまま据え置く。配線先は D1492 に従い、未確立一覧が実際に
縮む driver に限り、配線しない driver は名前と理由を記録する。

## 確定済みユーザー裁定 (覆さない)

- D1569: 厳格化する。`MEANING_SUPPORTED_MACROS` へ足すだけの形は採らない (D1491 却下形)。
  枝選択 witness を registry factory から発行。旧宣言経路は BACKOFF_FIXED 固定。配線先は D1492。
- D1490: witness は macro ごとに (所有 file の相対 path, 開始指令の逐語) だけを宣言し、所有 TU 全体を
  実 compile command で前処理して観測する。要求値で (1,1)・既定値で (0,1) のときだけ green、同じなら
  非識別で red。主張範囲は「所有 TU でその define の値が宣言した枝の選択を決めている」に限る。
- D1491: 新 witness は registry factory 以外から発行できない。旧宣言型の受理面を広げない。
- D1492: 配線は「対象 macro を実際に要求し、その admission が成果物へ載る driver」に限る。
  配線しない理由は driver 名とともに記録する。
- D1198: 供給の節と意味の節は独立した必須節。片方の緑をもう片方の緑と読める形にしない。
- D1523 (別 wave の scope、触らない): A-2 の inert 供給比較 (`preprocess-root-dependent-builtin`) は
  差を取ってから置き場所由来かを判定する形で直す。本 wave は供給の節に触れない。
- D95: 実装面は Codex `role=author`。親は実装面を直接編集しない。
- command 引数: 本題の厳格化だけ。仮想リスク向けの gate・検査・台帳・一般化は scope 外。規律 2 を緩めない。
  既受理成果物への影響を先に列挙してから入れる。

## 実測 (brief 前、基準 commit 764fdf202、この worktree)

- **既受理成果物への影響 = 空集合。** `output/` 全体 (untracked 含む) を走査し、`BACKOFF_NOINLINE` を
  runtime-meaning `unestablished` で含む実 admission record は 0 件。`unestablished_meaning_macros`
  field を持つ JSON も 0 件 (hit は変異 report 内の pytest 出力と設計 prose のみ)。A-2 の実走は
  `a2gate-20260902a` / `b` の 2 回のみで driver_rc=2、4 cell 緑未達 (entry 1208、
  `output/insights/2026-09-02_a2-condition-gate-patched-root/`)。**したがって受理集合を狭めても
  過去の判定は 1 件も変わらない。** 影響一覧は空であることを記録として残す。
- **指令の所在:** `#if BACKOFF_NOINLINE` は patch `patches/silo-backoff-fixed.patch` の
  `include/backoff.hh` hunk に 1 回だけ (`__attribute__((noinline))` を挟む 3 行)。所有 TU
  `cc/silo/transaction.cc` (DefineSpec owner_tus) には無い。include 連鎖は
  `cc/silo/transaction.cc` → `cc/silo/include/transaction.hh:9` `#include "../../../include/backoff.hh"`
  (quote include、相対 path)。
- **現行 shadow tree では header 計装が所有 TU から見えない (toy tree、g++ 11.4.0 実測):**
  `_write_shadow_owner_source` は祖先 dir を symlink で鏡像化し `_replace_owner_compile_input` が
  compile operand を計装 file へ差し替える。header を計装して owner を shadow 経由で compile すると、
  `cc` が symlink dir のため `..` が実体側へ解決され marker 0 個。**全 dir を実体・file を symlink にした
  深い鏡像**なら 値 1 → (選択 1, 完了 1)、値 0 → (0, 1) と D1490 の期待形どおり。CCBench 木は
  404 file / 49 dir (`.git` 除く) で深い鏡像のコストは小さい。
  模擬/実の差: toy は 3 file の最小 include 連鎖。実 TU の compile argv (`-I`、`-ffile-prefix-map`、
  masstree `config.h`) での再現は段 6 の親 dogfood (実 fixture / 実 patch 木) で確かめる。
- **A-2 の要求値は既定値と同じ 0 (inert 要求):** `paper_story_a2_certification.v2.json:49`
  `"CCBENCH_BACKOFF_NOINLINE": "0"` が全 cell の `controlled_define_base`。driver は
  `defaults = {"BACKOFF_FIXED": -1, "BACKOFF_NOINLINE": 0}` (:583) で `sorted(set(genome.flags) & set(defaults))`
  を要求し、`BACKOFF_NOINLINE` には `declaration = None` (:630-660)。現行 factory は
  `requested == "1" and default == "0"` のときだけ宣言を返す (:873-888) ので、**登録するだけでは
  A-2 の未確立一覧は縮まない。**
- **factory 呼び手:** `s3_lock_coverage.py:101`、`s5_permutation_coverage.py:98`、
  `t152_write_intent_coverage.py:198` (T-2153 で配線した 3 面)。他は未配線。
- **`BACKOFF_NOINLINE` を関門へ要求する driver と use class:**
  A-2 `paper` (:670); `s1_direct_comparison.py` (`_CONDITION_DEFAULTS` :178、宣言 :229-246 は
  BACKOFF_FIXED のみ、use class は `floor` 既定 / `certified-selection` (role≠develop) / `raw`);
  `backoff_sweep.py` :82/:125-150 (`raw-measurement`); `screening_driver.py` :53/:101 (`raw`);
  `silo_ladder_rung1.py` :2213 (`raw-measurement`); `tools/pegasus/probes/t1683_rr5_cost_probe.py`
  :152-209 (`raw-measurement`)。`paper_story_a1_paired.py` は BACKOFF_FIXED のみ要求 (該当せず)。
  `backoff_profile.py` (NOINLINE=1 の診断 build) は関門を呼ばない (`admission=None`)。
- **既存 test の pin:** `test_condition_meaning_gate.py:1953` `MEANING_SUPPORTED_MACROS == {"BACKOFF_FIXED", *_COMPILE_TIME_BRANCH_MACROS}`、
  `:1960-1962` SUPPLY_DOMAIN − {BACKOFF_FIXED} 全 macro で `MeaningWitnessDeclaration` が
  `no runtime witness support` を出す (据え置き対象)、`:30` `_COMPILE_TIME_BRANCH_MACROS` 8 件、
  `:707-724` registry と patch 逐語の束縛 (`_patch_added_branch_declaration` は patch の `+++ b/` から
  所有 file を導くので `include/backoff.hh` を返す。fixture 側 assert は transaction.cc 固定)。
  `test_paper_story_a2_certification.py:528-560` は gate を stub して `BACKOFF_NOINLINE` 未確立の
  拒否 message 書式を pin。`:70` は helper source に `"BACKOFF_NOINLINE"` 文字列を要求。
- **test fixture:** `orchestrator/tests/fixtures/condition_meaning_gate/supplied/include/backoff.hh` に
  `#if BACKOFF_NOINLINE` は無い (Options.cmake には cache 変数あり)。fixture の transaction.cc は
  `#include "../../include/backoff.hh"` を直接 include (実木の transaction.hh 中継とは異なる)。
- **凍結 bytes の pin 閉包 (DW-O09):** `condition_meaning_gate.py` / `paper_story_a2_certification.py` /
  fixture 木を bytes・sha256 で pin する台帳・manifest は 0 件 (`acceptance_duration_ledger.json` は
  所要 hint、`test_t316_sandbox_probe.py:144` は fixture path 参照のみ)。producer の出力 bytes
  (admission JSON) は新 field を足さない限り schema 不変。DW-O10 は不成立 (凍結成果物なし)。
- **編集面重複 (DW-O20 起動時要求):** t2266 (`backoff_extended_sweep.py`、同 test、
  `tools/pegasus/b10_backoff_grid.sh`、`submit_b10_backoff_grid.sh`)、t2189 (`t2187_adaptive_const_probe.*`、
  `test_hooks.py`、`admission_registry.json`、dirty `test_ccbench_spawn_sites.py`)。本 wave の
  編集面と交わらない。
- 受入環境: `tools/run_tests.py` (Pegasus 計算ノードへ自動 dispatch)。baseline
  `test_condition_meaning_gate.py` 88 passed / 5.07s (request 975694.nqsv、Elapse 10S)。

## 変更面 (実アンカー)

| file | anchor | 変更の性質 |
|---|---|---|
| `orchestrator/campaign/condition_meaning_gate.py` | `_CONDITIONAL_BRANCH_WITNESSES` :182-206 | `BACKOFF_NOINLINE: ("include/backoff.hh", "#if BACKOFF_NOINLINE")` を登録 (MEANING_SUPPORTED_MACROS は構成上ここから導かれる) |
| 同 | `declare_define_runtime_meaning` :873-888 | (P1) 所有 file が owner TU でなく依存 header である場合の宣言、(P2) inert 要求 (要求 0 = 既定 0) の宣言 |
| 同 | `_write_shadow_owner_source` :2716-2749、`_replace_owner_compile_input` :2752-2782、`_compile_time_observation` :2785-2855、`_assert_compile_time_branch_selection` :2857-3030 | (P1) 深い鏡像 + compile operand を shadow 側 owner TU へ差し替え、計装 header が依存閉包に入ることの fail-closed |
| 同 | `ConditionalBranchMeaningDeclaration` :553-571 | registry 束縛の維持 (D1491) |
| `orchestrator/campaign/paper_story_a2_certification.py` | `_condition_gate_family_context` :630-660 | `declaration = None` の枝を factory 呼び出しへ (配線) |
| `orchestrator/campaign/s1_direct_comparison.py` | `_condition_meaning_declaration` :229-246 | (P3) promotion class (`floor` / `certified-selection`) なので配線候補 |
| `orchestrator/tests/test_condition_meaning_gate.py` | :30、:707-724、:1953-1962、`_compile_time_source_root` :196-220、fixture `supplied/include/backoff.hh` | 登録 pin の更新、header 所有 witness の正例・負例、inert 要求の正例・負例、fixture への directive 追加 |
| `orchestrator/tests/test_paper_story_a2_certification.py` | :70、:528-560 | 配線後の期待値 (stub の宣言経路) |
| `orchestrator/tests/test_s1_direct_comparison.py` | :479 付近 | (P3 採用時) |

## 割れうる前提 (親の provisional 裁定・攻撃対象)

- (P1) **header 所有の witness を許す形。** registry の source_rel が owner TU でなく、所有 TU の
  依存閉包にある header を指すことを許す。observation は「全 dir 実体・file symlink の深い鏡像」に
  計装 header を書き、compile operand を **shadow 側の owner TU path** (`instrumented_root/<owner_tu>`)
  に差し替えて前処理する。計装 header (`instrumented_root/<source_rel>`) が前処理の依存 file
  (`-MD -MF`) に現れなければ red (fail-closed、「計装したが読まれていない」を緑にしない)。
  既存 8 macro (source_rel == owner TU) の挙動・evidence bytes は変えない。
  代替 (却下予定): 所有 TU 側に `#if BACKOFF_NOINLINE` を持たせる CCBench 改変 (D16/D18/D20 の対象、
  測定対象を触る); header 断片の単体前処理 (D1490 が却下した文脈欠落)。
- (P2) **inert 要求 (要求値 == 既定値 == 0) の宣言。** factory は登録 macro について
  `{requested, default}` が `{"0"}` または `{"0","1"}` のとき宣言を返し、観測は値 0 と値 1 の両方で行う
  (要求が 0 なら 1 が対照値)。green は 値 1 → (1,1) かつ 値 0 → (0,1)。evidence には要求値側と
  対照値側を区別して記録する。主張は D1490 と同じ「所有 TU でその define の値が枝の選択を決めている」
  であり、要求 0 側の意味は「noinline 枝が選ばれていない (stock と同じ枝)」。これは D1490 の
  「要求値と既定値の両方で観測」を、要求値が既定値と一致する場合に対照値で補う拡張であり、
  段 7 で decision (D1490 の補遺) を記録する。要求値 1 (診断 build) の宣言も同じ factory で出る。
  代替 (却下予定): inert 要求は宣言せず unestablished のまま (= 本題が直らない); 値 0 だけを観測して
  (0,1) で green (非識別・恒真、規律 2 違反)。
- (P3) **配線先。** A-2 (`paper`) は必須。`s1_direct_comparison` は promotion class (`floor` /
  `certified-selection`) で `BACKOFF_NOINLINE=0` を要求しており D1492 の条件を満たすので配線する。
  raw 系 (`backoff_sweep`、`backoff_repro`、`screening_driver`、`silo_ladder_rung1`、t1683 probe) は
  promotion でない raw class に閉じており、本 wave では配線せず driver 名と理由 (raw class、
  未確立一覧は残るが certified / 論文成果物へ昇格しない) を記録する。
  攻撃点: raw 系を残すと同じ macro が driver ごとに green / unestablished へ分裂する (D1492 の懸念)。
  s1 の編集面拡大が「本題だけ」を超えるか。
- (P4) **既存受理済み成果物への影響は空集合** (実測)。したがって migration・追記訂正は不要。
  攻撃点: repo 外 (Pegasus attempt root、`/work` 配下の durable base) に A-2 / s1 の admission が
  残っていないか。親は `output/` 全体だけを走査した。
- (P5) **fixture への directive 追加**は `supplied/include/backoff.hh` に patch と同じ 3 行
  (`#if BACKOFF_NOINLINE` / `__attribute__((noinline))` / `#endif`) を入れる。`_patch_target_source`
  と materialized EVOLVE block の束縛 (:1925) は backoff.hh 全体でなく block だけを比べるので壊れない
  (要確認)。
- (P6) 供給の節 (`evaluate_define_supply_effectuation`)、D1523 の inert 比較、CLI、旧
  `MeaningWitnessDeclaration` は触らない。`RELATED_DEFINE_DECODE_MACROS` も触らない。

## 不変条件

- 受理集合は狭まるだけ: 既存 green は green のまま、既存 unestablished は green か red になる。
  supply arm の判定は不変。
- 既存 8 macro の witness evidence (canonical JSON) は bytes 不変。
- 旧宣言型は BACKOFF_FIXED 固定 (:533-548 の `macro != MACRO` 拒否を維持)。
- 新 witness の宣言は registry factory 以外から作れない (`ConditionalBranchMeaningDeclaration.__post_init__`)。
- 検査した木と build する木は一致 (A-2 の patch 済み木、entry 1208 の教訓)。
- テスト全体 5 分上限。新規 test は fixture 木で数秒以内。

## 成果物の形

- コード + テスト (Codex author) + 段 7 記録 (worklog fragment、decisions fragment: D1490 補遺、insight README
  に「既受理成果物への影響 = 空集合」の走査記録と配線しない driver の一覧)。

## 並列分割方針

- 実装子は 1 本 (gate 本体・fixture・test は producer/consumer 契約が 1 単位を跨ぐため分けない)。
  A-2 / s1 の配線は同じ子が最後に行う。
