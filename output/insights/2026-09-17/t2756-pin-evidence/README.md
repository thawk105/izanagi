# [T-2756] ccbench pin 更新項 ([T-167]) の再承認材料 3 点 — 候補 commit・直接区間の TRACE=0 同一性検査・pin 束縛の波及

- authority: none
- default_effect: no-state-change
- 日付: 2026-09-17
- wave: dev-wave-t2756-pin-evidence (branch `worktree-dev-wave-t2756-pin-evidence`)
- 起点の裁定: D2114 項 3 (pin 前進は未承認、D1603 の材料 3 点が揃った時点で見送り台帳の pin 更新項の再承認として別途提示、初回候補は mocc 単独)、D2104 項 13 (非 silo between-run 実測は保留)、D1603 (材料 3 点 = 候補 commit、D297 検査の結果、承認済み定数への波及範囲)
- 基準: local main `38353207f719acb0871cfe3d9bbe3a02490282bb`、superproject の gitlink `external/ccbench` = `511c9538e4e8efa54b45cda62e72389ed3b706ec` (本 wave では動かしていない)
- 骨格の出典: `output/insights/2026-09-17/cross-protocol-scope-release/README.md` §4 (候補観測)・§5 (波及表の骨格)

## 0. 提示目的と現在の結論

本資料は、見送り台帳 (`docs/phase3.md` の [T-167] 行) の ccbench pin 更新項を**再承認として諮るための判断材料**であり、pin 前進の承認・実行を意味しない。superproject の gitlink、`orchestrator/campaign/pin.py`、`orchestrator/campaign/s8b_approved.py`、凍結物、事前登録、checker は 1 byte も変えていない。

3 材料の現在の状態:

| 材料 | 状態 |
|---|---|
| (1) 候補 commit | mocc 単独 = `e9e477ca1b55348ab4530de0b1cf663ce4555290` を提示候補として確定 (§2)。現 pin の直系子孫 4 commit 先、追加差分は `cc/mocc/transaction.cc` 1 file。GitHub には未 push (push は人間、D16) |
| (2) D297 検査 | 直接区間 (現 pin → 候補) を現行 checker で実走。**GCC 11.4 / 12.3 は各 16 context で pass。clang 14 は環境 prefix 不一致で比較未完了 (検査不能)**。事前計画の「3 本すべて成功」は未達。保証範囲は §3.2 の逐語に限る |
| (3) 波及範囲 | pin の値を含む tracked file 134 件を層別に分類し (§4)、文字列集合の外にある依存 13 件以上を別表にした。結論: pin 前進は旧 pin・旧 identity で得た測定事実と当時の判定を無効化しない。新 pin で継続する系列は登録・identity・凍結・consumer・テスト契約の整合と明示された再実測を要する |

## 1. この wave が判定しないこと

- pin 前進の可否・実行。`CCBENCH_FULL_SHA` / `CURRENT_PIN` / gitlink の更新。
- 非 silo (mocc / tictoc) の between-run 実測の再開 (D2104 項 13)。
- mocc の正しさ、certified な合成経路の成立、変異探索面への解禁 (D579)、TicToc の候補化、上流 CCBench への還元。
- 性能上の結論。検査結果に合わせて条件を選び直した結論も出していない。
- D986 と現行実装の残余 (§3.2) の修理や受容。既存較正 record を新 pin 系列へ流用してよいか (§4.3)。

checker の合格は規律 1 の**必要条件の一つ**に過ぎず (D780)、これを理由に「前進可能」とは書かない。

## 2. 材料 (1) — 候補 commit の確定 (mocc 単独)

| 項目 | 値 (2026-09-17 の親の実測、worktree の submodule で) |
|---|---|
| 候補 full OID | `e9e477ca1b55348ab4530de0b1cf663ce4555290` |
| 所在 | submodule `external/ccbench` の local branch `izanagi-t1943-mocc-g2-readfrom-witness` の先端 (primary checkout の module store では `refs/heads/…`、wave の worktree では `refs/remotes/origin/…`。worktree の `origin` は GitHub ではなく primary の module store) |
| 現 pin | `511c9538e4e8efa54b45cda62e72389ed3b706ec` |
| 祖先関係 | `git merge-base --is-ancestor 511c9538… e9e477ca…` rc=0、merge-base = 現 pin。候補は現 pin の**直系子孫で 4 commit 先** (前 wave insight の「非祖先」は「候補は現 pin の祖先ではない」の意味)。checker の祖先性 gate (old ⊑ new) を通る |
| 追加差分 | `git diff-tree --raw -r --no-renames` = `M cc/mocc/transaction.cc` の 1 path (+141 行、削除 0)。4 commit すべてが同 path だけを変更。共有 `include/trace.hh` は両端で同一 blob `570e35e308e1104d53d43ea5556f54b3fb86922a` |
| 「mocc 単独」の意味 | 現 pin から候補までの**追加変更範囲**が mocc の 1 file だけ、という意味。候補 tree は Silo / SI の既存計装を含む |
| GitHub 到達性 | `git ls-remote https://github.com/thawk105/ccbench` (2026-09-17、`verbatim/github-ls-remote.txt`) の広告 ref 一覧に候補 OID を先端とする ref も候補 branch も**無い**。現 pin は `izanagi-trace-pin-t816` / `izanagi-trace-t816-fn2` として存在。GitHub だけを取得元とする fresh clone で候補を取得できることは未確認であり、移行前に人間による公開 (push、D16) と取得確認を要する。wave の worktree の `origin` は候補を保持する local store (primary の module store) |
| 旧候補 | `c9c1a9c` (2026-07 承認、GitHub `izanagi-trace-t152`) は採用候補としない (D2114 項 3)。TicToc は別候補 (同項) |

4 commit (旧 → 新。author / committer はいずれも `thawk105 <thawk105@gmail.com>`、逐語 = `verbatim/candidate-commits.txt`):

| OID | 日付 | 件名 | 変更 | 来歴 (本文・trailer から) |
|---|---|---|---|---|
| `ef9328a35d49b1b9b610f244bee22ad7f10b8b66` | 2026-08-21 | feat(mocc): add correctness trace v2 hook | +31 | `AI-Agent:` trailer なし。T-1506 の記録はユーザーの commit と記す。superproject では同日 gitlink を 511c9538→ef9328a3 へ進めた commit `09ce607b7` が同日の `13101ab3e` で revert された |
| `058d0c4e5f237d88ec1c2ebe0739113d82906e47` | 2026-08-23 | fix(mocc/trace): move the trace include comment to its own line (izanagi [T-1506]) | +2 −1 | Codex author / Claude manager の trailer。D673 に基づき AI が commit |
| `ae6880f747834805ebea1ed4f0e1b15f3e960b23` | 2026-08-28 | feat(mocc): add T-1943 payload lineage witness | +111 | Codex author / reviewer、manager は model・reasoning が unknown。TRACE-only の payload watermark と per-thread witness stream (G2 discriminator 用) |
| `e9e477ca1b55348ab4530de0b1cf663ce4555290` | 2026-08-28 | fix(mocc): preserve TRACE=0 include identity | +7 −9 | Codex author、manager unknown。witness 専用の標準 library include を除き既存 trace include 面を使う |

来歴について言えること・言えないこと:

- T-1943 の記録 (`docs/archive/worklog-phase3-0828-1079.md`) は、submodule に provenance 導入 commit が無く post-history 監査は不能で、commit 前の message 検査だけ通過したと記す。上表を「provenance 監査済み」とは読まない。trailer の unknown は補完しない。
- witness は TRACE=1 でだけ有効な計装であり、D18 の性能 variant 昇格の候補ではない。§3 の TRACE=0 一致から TRACE=1 の意味的無影響や mocc の正しさを導かない。
- 過去の checker 実走: 区間別に 現 pin → 058d0c4e (T-1506、2026-08-23、16 context 一致) と 058d0c4e → 候補 (T-1943、2026-08-28、16 context 一致) があり、さらに T-1943 の計算ノード pilot (request 956466.nqsv、2026-08-28 18:16) にも**現 pin → 候補の直接区間の pass report** (GCC 11.4、16 context、schema v2、sha256 `3bbda8db4596296ce45d0250607d15ed27837579419016aa7b74b7bf23d86079`) が job dir の raw staging (`/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t1943-mocc-g2-discriminator/attempts-final1/raw-staging-0_956466.nqsv/trace0-preprocess-identity.json`、repo 外) に残る。ただし同 pilot は completed receipt の公開前に artifact classification が rc=2 で停止し、completed pilot receipt と job-result は存在しない (RESULT.md)。本 wave は現行 checker 版 (T-1584 の修理と t1642 の文言を含む) で直接区間を login node から**再検査**した。当時の report の存在と正式な証拠化は区別する。

## 3. 材料 (2) — 直接区間の TRACE=0 前処理同一性検査 (D297)

### 3.1 実走の結果

実走 (親、login node `pegasus02`、2026-09-17 21:39〜21:42 JST、cwd = wave worktree、worktree clean、checker blob `79dc9bbd229d23bf6a78f78b18d744eb417160d7`、`source_digest.py` blob `0f062df910201f74c99ec526027b2db77e6f0c92`、submodule checkout HEAD = 現 pin。索引 = `verbatim/runs.json`):

```
python3 tools/check_trace0_preprocess_identity.py --repo <worktree>/external/ccbench \
  --old 511c9538e4e8efa54b45cda62e72389ed3b706ec --new e9e477ca1b55348ab4530de0b1cf663ce4555290 \
  --cxx <CXX> --expect-paths cc/mocc/transaction.cc
```

| CXX (requested → resolved) | rc | 結果 | report |
|---|---|---|---|
| `/usr/bin/g++` → `x86_64-linux-gnu-g++-11 (Ubuntu 11.4.0-1ubuntu1~22.04.3) 11.4.0` | 0 | `result: pass`、`cc/mocc/transaction.cc` = `match`、16 context すべてで正規化 preprocess 出力と include 活性が old / new 一致 | `verbatim/trace0-gcc11.report.json` (sha256 `a15ca6e4…`、33,036 bytes) |
| `/usr/bin/g++-12` → `x86_64-linux-gnu-g++-12 (Ubuntu 12.3.0-1ubuntu1~22.04.3) 12.3.0` | 0 | 同上 | `verbatim/trace0-gcc12.report.json` (sha256 `aa675a46…`、33,036 bytes) |
| `/usr/bin/clang++` → `Ubuntu clang version 14.0.0-1ubuntu1.1` | 1 | **比較未完了 (検査不能)**。stderr: `source_digest: preprocess 出力が空入力の環境 prefix と不一致 — identity を確定できないため fails-closed`。report JSON は出ない | `verbatim/trace0-clang14.stderr.txt`、stdout は 0 bytes |

**読み方:** GCC 2 版 (11.4 / 12.3) の各実行は pass。clang 14 の実行は old / new の比較に到達する前に fail-closed し、候補差分の不一致を検出した結果ではないが、**clang での同一性は未確認**である。親 brief が事前に置いた「3 本すべて成功」は未達であり、総合合格へ置き換えない。D297 の「複数の compiler で走らせ」は異なる実行体 2 本 (GCC 11.4 / 12.3) で満たすが、2 つの compiler family で合格したわけではない。

GCC 2 本の report の中身 (`verbatim/runs.json` と report 本体から):

- schema `izanagi-trace0-preprocess-identity/v2`、`old_is_ancestor_of_new = true`、diff = `[(cc/mocc/transaction.cc, M)]` のみ、`--expect-paths` と厳密一致。
- context 行列 = `SILO_SPACE.enumerate()` 8 genome × `_context_overlays()` 2 (素文脈 / `GLOBAL_VALUE_DEFINE=1`) = 16 件 / file。
- 全 16 件で `normalized_preprocess.identical = true`、`include_activity.identical = true`。old / new とも TRACE=0 で活性な include marker は 10 個で一致。
- mocc の trace.hh 特例: `policy_comparison = {accepted: true, basis: permitted_mocc_trace_include_addition, permitted_addition: {active_at_trace0: false, new_include_index: 10}}` (全 context)。policy 受理と生 marker 列の一致は別の証拠で、今回は両方が成立している。
- 実効 define map は 4 種 (`BACK_OFF ∈ {0,1}` × `GLOBAL_VALUE_DEFINE` の有無。他は `ADD_ANALYSIS=0, KEY_SIZE=8, KEY_SORT=0, Linux=1, MASSTREE_USE=1, RWLOCK=1, TEMPERATURE_RESET_OPT=1, TRACE=0, VAL_SIZE=4` で固定)。正規化出力の digest は 2 種で `BACK_OFF` でだけ分かれる。GCC 11.4 と 12.3 で正規化 digest の集合は同一 (`148e44ea…`, `4db297ef…`)、活性 digest も同一 (`c0fdab05…`)。report file の sha256 が異なるのは compiler field の差であり、比較対象の差ではない。
- login の `/usr/bin/g++` (と `/usr/bin/gcc`) の `--version` 全文に `toolchain_binding.tool_version_body()` を当てた sha256 は `b713e6ab62b67126b772f6b0a8d9751070f0d0315c7017291cb5dde67747b9c0` で、`tools/pegasus/mocc_trace_v1_policy.json` の `expected_compiler_version_body_sha256` (D1487: pilot receipt 37 件と計算ノード calibration receipt が同じ値) と一致する。g++-12 (`75f4ea26…`)、clang++ (`4b53fd45…`) は一致しない。これは compiler binary・依存 library・build flag・実行環境を含む admission toolchain 全体の同一性の証明ではない。

### 3.2 保証範囲 (この検査が言えること・言えないこと)

- 保証名は D297 の「**選定した macro context における TRACE=0 正規化 preprocess 出力の同一性、および include 活性の同一性**」であり、対象は現 pin から候補への端点間差分である。祖先関係と差分 path 集合の厳密一致を検査し、中間 commit ごとの無害性は保証しない。翻訳単位の同一性を名乗らない。
- 16 件は SILO_SPACE の 8 genome × 2 overlay の列挙であり、mocc TU に対する実効構成は 4 種・出力 digest は 2 種だった。mocc 固有の macro 空間を列挙した結果ではない (下表)。「16 個の異なる macro 構成を検証した」とは書かない。
- 正規化は include 行を除去し、compiler builtin を保持したまま `-E -P -dD -nostdinc -Werror=undef` + 所定の build flag + context の `-D` 群で preprocess する。`-dD` は有効枝の `#define` / `#undef` を残し skipped 枝は出さない。同じ argv の空入力出力を環境 prefix として剥がす (clang 14 はこの境界で停止した。原因は §3.3)。
- include 活性は各 include 行を一意な marker に置換して順序込みで別途検査する。唯一の特例は `cc/mocc/transaction.cc` の単純な `#if TRACE` 初期枝内の exact `#include "../../include/trace.hh"` 1 行の追加で、追加 marker が全 context の TRACE=0 で非活性、残る marker の対応・順序が一致することを要求する。任意の include 追加は受理しない。
- header 差分、未対応の差分形 (追加・削除・mode 変更・非 source 拡張子)・非 literal な include 構文、比較 0 件・件数不一致は拒否する。header を展開した翻訳単位、指令と include の相対位置、`#pragma push_macro` / `pop_macro` の復元値、binary 同一性、trace の完全除去は証明しない。両 commit に `#undef TRACE` / `#define TRACE 1` を置いても pass する (T-1584 の段 3 が実証) — 完全除去は実 compile command・全 TU・link object・build receipt など別防壁の領分で、この検査はその**必要条件の一つ** (D780)。
- 不在 macro registry (`MQLOCK`) は old / new 別々の commit tree と検査時 checkout の認識対象 text で再検証する。submodule 内部は不在証明の対象外 (D723)。**解決不能な CMake 間接値は現行実装では拒否しない** (D774、T-1584 §6 R5、[T-1644] で据え置き)。D986 (3 穴を塞ぐ) のうち単純形は T-1584 が修理したが、本資料は D986 の全面閉塞を主張しない。この残余の修理も受容も本 wave では行わない。
- 本 wave の単独実行 report は `verbatim/runs.json` に索引した判断材料であり、計測 pilot の receipt / job-result へ組み込んだ証拠ではない。T-1584 当時の R1 (report が proof chain に入らない) に対して、現行の `tools/pegasus/mocc_trace_pilot.sh` には report の path・sha256・schema・guarantee を receipt / job-result へ束縛する実装がある (D779 / D813)。今回の保存物だけでその経路の実行は主張しない。`__has_include` と `-nostdinc` の include path 差 (T-1584 R3) も残る。
- 結果は使用 compiler と選定 context に依存し、admission toolchain と同一であるとは主張しない (D297)。

候補 `cc/mocc/transaction.cc` の条件付き指令と、16 context がどちらの枝を検査したか (親が候補 blob で検算。`#else` / `#elif` / `#ifndef` は無く、行 616 の `// #else` はコメント):

| 指令 | 出現 | 選定 context での値 | 両枝を検査したか |
|---|---|---|---|
| `#if TRACE` | 8 | 常に 0 | 否 (真側 = trace 計装の枝は検査対象外。これが検査の定義) |
| `#if ADD_ANALYSIS` | 17 | 常に 0 | 否 |
| `#ifdef RWLOCK` | 15 | 常に定義済み (mocc CMake の実供給、D722) | 否 |
| `#ifdef MQLOCK` | 11 | 常に未定義 (registry の不在証明) | 否 |
| `#if TEMPERATURE_RESET_OPT` | 1 | 常に 1 (Options.cmake の既定) | 否 |
| `#if BACK_OFF` | 2 | 0 / 1 | **是** |

SILO_SPACE の残る genome 軸 3 種 (`NO_WAIT_LOCKING_IN_VALIDATION` / `NO_WAIT_OF_TICTOC` / `WAL`) は mocc の実効 define map に残らず、この source に条件指令も無いため、検査件数を増やすが異なる構成を増やさない。一方 `GLOBAL_VALUE_DEFINE` は overlay として define map に追加され (map を 2 種から 4 種に増やす) が、この source には対応する条件指令が無く、include を展開しない今回の正規化出力では digest を増やさない。

### 3.3 clang 14 が検査不能になった原因 (親の probe、要約と sha256 = `verbatim/compiler-probe-summary.txt`。生出力は末尾空白が内容 (空定義) なので repo に置かない)

同じ flag (`-E -P -dD -nostdinc -Werror=undef -x c++ -`) で空入力と 1 行入力 (`int x;`) を前処理すると、clang は空入力の出力 (405 行) の末尾に空行を 1 行出し、非空入力ではその位置が本文に置き換わる (diff: `405c405`)。したがって実出力が空入力出力を prefix として持たず、`source_digest._cpp_normalize` の環境 prefix 剥がし (「対象 GCC の実測」に基づく設計、docstring) が fail-closed になる。gcc では空入力出力 (423 行) が実出力の厳密な prefix になる (diff: `423a424`)。これは候補の拒否ではなく、今回の checker 版・clang 14・この入力条件では正規化を確定できないという限界である。prefix 問題を解消すれば clang でも old / new が一致するかは未検証。本 wave は checker を改変しない。

## 4. 材料 (3) — pin の値を束縛する物と、pin 前進時の波及

### 4.1 新 pin で系列を始めるときに要る作業 (短い一覧)

1. 承認: `orchestrator/campaign/s8b_approved.py` の `CCBENCH_FULL_SHA` と `orchestrator/campaign/pin.py` の `CURRENT_PIN` の更新は再承認 (本項) の後。gitlink と同じ commit で更新し、`orchestrator/tests/test_s8b_approved.py` が gitlink と定数の一致を検査する。
2. 新系列の登録・identity: A-1 事前登録 (`paper_story_a1_paired.v3-*.json` の `canonical_pin`) と source 契約 (`paper_story_a1_source.v2.json` の `canonical_head`) は旧登録を旧 pin のまま保持し、新条件は新登録または追補。campaign identity (`ident.py` の `ccbench_commit`) は新 campaign が新 ID になる (content-addressed)。旧 lock の resume 拒否は過去判定の取消しではない。
3. 独立 full OID を持つ driver (`p3_s4_loop.py:PIN` は D1936 で完全 40 桁固定、`silo_ladder_rung1*.py`、probe 群) は `CURRENT_PIN` に自動追随しない。新系列へ移す driver だけ明示更新し、専用の旧系列 (ability-probe、歴史的 driver) は据え置く (`pin.py` 冒頭の注記のとおり歴史的 driver は自分の pin を保持)。
4. 生成物形の再実測: `orchestrator/campaign/buildcache.py` の docstring が「CCBench pin 更新時は CMakeCache / DependInfo の生成物の形を再実測すること」と要求する。
5. 凍結 floor protocol (`output/s8b-freeze/floor-protocols/*--511c9538….json`) は旧凍結を保持し、新 pin 系列は新しい版の凍結 (protocol 生成と床値の実測は別)。
6. 較正 record (`output/env/pegasus/calibration/registered/*.json`) は取得事実として保持。新 pin で取得した較正値と主張するなら再取得 + 新登録 (§4.3)。
7. テスト・fixture: 現行 pin を期待する test (`test_s8b_approved.py` 等) は定数更新に伴って更新するが、旧 pin を control として使う test (`test_mocc_proof_surface.py` の「候補に当たり旧 pin を拒否する」、`fixtures/README.md` の producer clone HEAD、`b10_backoff_shape_locks/*.campaign.lock`) は一律更新しない。
8. 性能事前登録 3 本 + balanced 別事前登録 + 軸 B5 検索事前登録は旧登録を保持し、新 pin の計測を登録するなら erratum または新登録 (`docs/backoff-*-preregistration.md`、`docs/dynamic-backoff-preregistration.md`、`docs/t1998-balanced-stock-inline-preregistration.md`)。
9. mocc 比較 policy (`tools/pegasus/mocc_trace_v1_policy.json` の `base_oid` = 現 pin、`new_oid` = 候補) は旧 → 候補の比較契約として保持する。base を新 pin へ機械置換すると自己比較になる。新しい命題には別 policy。
10. 前回の pin 前進 (`fb5e74a17`、2026-08-12、d706650 → 511c9538) は「現用 pin 23 箇所を追随、歴史 preimage・固定 fixture・凍結 golden・PREVIOUS_PIN / KICKOFF_PIN は据置、校正 pin 4 件だけ機械再 pin、測定値は 1 つも変えず再測定はしない — 16 context で機械確認」だった。以後 A-1 / A-2 事前登録、s8b 凍結 floor、較正 record の head_sha、mocc policy が増えており、同じ手順の再演では足りない。

### 4.2 層別表 (pin の値を含む tracked file 134 件の分類)

取得条件: 2026-09-17、superproject HEAD `38353207f719acb0871cfe3d9bbe3a02490282bb` の worktree (clean、未 commit 差分なし) で `git grep -l 511c953 -- .` を母集合とし、`docs/worklog.md`・`docs/decisions.md`・`docs/failures.md`・`docs/archive/`・`docs/spool/`・`output/insights/` を除いた 134 file。形別 (40 桁 / describe `g511c9538` / 8 桁 / 7 桁) の出現数は regex (`verbatim/pin_closure_scan.py.txt`) で数え、40 桁を含むのは 79 file、describe 形は 0 file。**これは文字列検索の集合であり、依存閉包でも更新対象の件数でもない** (集合外の依存は §4.4)。134 行の全数分類 (path:line → 分類 → 帰結 / 役割) は `verbatim/pin-impact.tsv` (段 2 plan 子の起草、段 3 レンズ B が全数検算し主分類の訂正 0 件、親が優先 2 群を現物で確認)。

| 分類 | 件数 | 代表例 (path) | pin 前進時の帰結 |
|---|---|---|---|
| A 現行・専用 driver の定数 | 12 | `pin.py` (`CURRENT_PIN`、7 桁)、`s8b_approved.py` (`CCBENCH_FULL_SHA`)、`p3_s4_loop.py` (D1936 の独立 40 桁)、`axis_trigger_gating.py` / `backoff_sweep.py` / `s5_permutation_coverage.py` / `s6_sort_sweep.py` (`CURRENT_PIN` alias)、`silo_ladder_rung1.py` (ability-probe 専用)、probe 2 本 | 新 pin へ移す系列だけ更新。専用の旧系列は維持。`s8b_approved` は再承認なしに変更不可 |
| B 事前登録・source / patch / pilot の登録契約 | 12 | 性能事前登録 3 本、balanced 別事前登録、B5 検索事前登録、A-1 `v3-pilot` / `v3-sized` の `canonical_pin`、A-1 source 契約 v1 / v2、`patches/README.md` / `patches/ledger.json` (rung1 patch の `base_commit`)、`mocc_trace_v1_policy.json` (`base_oid`) | 旧登録を保持、新条件は新登録または追補。patch は候補差分が mocc のみなので Silo patch の機械適用が維持される可能性はあるが未実測で、適用成功と `base_commit` 契約の充足は別 |
| C identity・lock・取得証拠 | 31 | 較正 record (registered 6、attempts 7、job-staging の candidate / receipt 14)、a2 perf verify cost 2、profile json、t316 sandbox receipt | 旧 bytes を保持 (hash 束縛、`env_contract.py` が path を較正 hash の content-address に束縛)。新系列では新しい証拠と束縛。pin 差だけで既存較正が無効になるとは結論しない (§4.3) |
| D 凍結物 | 1 | `output/s8b-freeze/floor-protocols/e576e9cd…--511c9538….json` (内容と filename に pin) | 旧凍結を保持。新 pin 系列の要否を裁定 (再凍結ではなく新しい版) |
| E 歴史記録・説明・provenance | 35 | paper-story 本文 / results / claim-evidence / figures README、figure provenance json 5 本、`buildcache.py` docstring、known_violations 4 本、`acceptance_duration_ledger.json`、profile md、worktree-add ログ 7 本、B10 provenance | 保持。書き換えない。ただし `buildcache.py` の「pin 更新時は再実測」は独立の移行作業として残す |
| F テスト・fixture | 31 | `test_s8b_approved.py` は集合外 (§4.4)。集合内は `test_mocc_proof_surface.py` (候補に当たり旧 pin を拒否する対)、`fixtures/README.md` (producer clone HEAD)、`b10_backoff_shape_locks/*.campaign.lock`、A-1 / A-2 / plot / backoff 解析 / s8b / sort / trigger-gating の各 test | **現行 pin 追随と旧 pin 回帰証拠を分ける**。一律更新しない。旧 producer の trace・lock・拒否 control を新 pin と偽装しない |
| G 一致検査 consumer | 12 | `paper_story_a1_paired.py` (`CANONICAL_CCBENCH_OID`) と `tools/pegasus/paper_story_a1_paired.sh` (literal と HEAD の二段照合)、backoff 解析 3 本、`silo_ladder_rung1_contract.py` (ledger の `base_commit` を exact 照合)、plot 3 本、`t2216_backoff_walk_model.py`、`phase3-8b-restart-runbook.md` の人間 preflight、t2228 liveness probe の pbs | 旧契約を保持。新系列を通すなら policy / 登録と consumer を同時に対応させる。新 pin checkout では旧登録の実行・再解析が拒否される (過去判定の取消しではない) |

§5 骨格 13 行との対応: 行 1 (gitlink / 現行定数) = A、行 2 = `s8b_approved.py`、行 3 = A-1 `v3-*.json`、行 4 = A-1 source v2 (+ v1)、行 5 = `paper_story_a1_paired.py` (+ `.sh`)、行 6 (A-2) と行 7 (`ident.py`) と行 9 (`source_digest.py`) は pin literal を持たず集合外 (§4.4)、行 8 (campaign.lock) = test fixture の実在 lock 3 本 (生成済み campaign の lock 全体の列挙ではない)、行 10 = D、行 11 (凍結 evidence manifest) は `output/insights/` 除外で集合外かつ **`current_pin` は 7 桁 `511c953`** (骨格の「full SHA」は誤りで「短縮 pin + manifest 内 file hash による束縛」が正しい)、行 12 = B の性能事前登録 3 本、行 13 = B の balanced 別事前登録。骨格に無い層 = 生成物互換性の再実測義務 (E)、D1936 の独立 full pin (A)、ability-probe patch 契約 (B)、mocc 比較端点 policy (B)、content-addressed 較正 (C)、テストの旧 pin control (F)、解析・plot consumer (G)、provenance 既知違反 (E)、検索事前登録 (B)。

### 4.3 較正・floor・凍結の境界 (規律 7 の適用)

規律 7: 現行コードとの差だけを理由に記録された測定を無効化しない。新しい測定の開始条件に過去の承認済み状態とのコード同一性を置かないが、**事前登録の充足・凍結・環境契約・較正・correctness gate といった同一性と無関係な前提条件はそのまま残る**。

| 層 | 判定 | 根拠・限界 |
|---|---|---|
| 既存較正 record (registered 全 8 件 = 現 pin の silo・mocc・tictoc 各 2 件 (検索集合内の 6 件) + 旧々 pin d706650 の silo 2 件 (集合外)) | 保持 | acquisition の `head_sha` を含む bytes を保持。pin 前進だけでは取得事実を取り消さない。d706650 (旧々 pin) の silo 2 件が既に保持されている先例 |
| 環境契約の較正参照 (`env_contract.py`) | 保持 / 変更時は新登録 | path / hash・schema・env_tag・clock を束縛。確認した環境契約の検証経路では acquisition の `head_sha` は schema 検証の対象 (`orchestrator/calibrator/schema_v2.py` が 40 桁 hex を検証) だが、現行 CCBench pin (`CURRENT_PIN` / gitlink) との等値照合には使われない |
| 新 pin で取得した較正値という主張 | 再取得 + 新登録 | 旧 record の `head_sha` を張り替えて作れない |
| 新 pin 系列で旧較正を利用できるか | **再承認パッケージの一項** (親の推奨 = 既定は再取得。D297 合格は TU の binary 同一性を証明せず、規律 7 は較正を同一性と無関係な前提条件として残す。流用を認めるなら対象 protocol・workload・用途を名指しして裁定) | hash 検査通過だけでは適用範囲の拡張を証明しない。一方、pin 差だけで一律再取得も導けない |
| 既存凍結 floor protocol | 保持 | 旧 pin を含む凍結 bytes・path を変更しない |
| 新 pin 系列の floor protocol | 新登録 / 新しい版の凍結 | 解決キーに pin を含む (`s8b_floor_campaign.py`)。旧 protocol を新 pin の契約として流用しない |
| D2083 の within-run floor 登録 (非 silo 4 対) | 保持 | 用途限定の登録。`registered/` を report が自動走査しないことも D2083 が明記 — 6 件の record 列挙を「環境契約へ登録済み」と読まない |
| 新 pin での within-run floor 観測 | 再取得 + 新登録 | 旧 4 対の値を新 pin の観測に読み替えない |
| 過去記録の誤りが判明した場合 | erratum (追記) | pin 差だけでは erratum 不要 |

結論: pin 前進だけを理由に旧 pin・旧 identity で得た測定事実と当時の判定を無効化しない。新 pin で継続する系列は、登録・identity・凍結・consumer・対応するテストの契約を整合させ、明示された再実測を行う。旧証拠の保持は新 pin への保証の移転を意味しない。D297 の合格はこの表の SHA 束縛を内容ハッシュへ置換する承認にならない (D2114)。

### 4.4 文字列集合の外にある依存 (再承認の判断に要るもの、今回確認した最低数)

| 対象 | 役割 |
|---|---|
| gitlink `external/ccbench` (tree entry、通常 file ではない) | pin の実体 |
| `orchestrator/tests/test_s8b_approved.py` | `git ls-tree HEAD external/ccbench` で実 gitlink を読み、`CCBENCH_FULL_SHA` との一致を検査 |
| `orchestrator/campaign/ident.py` | `identity_preimage` の `ccbench_commit` 不一致を拒否 |
| `orchestrator/campaign/source_digest.py` | source evidence の commit 束縛 |
| `orchestrator/campaign/paper_story_a2_certification.py` | evidence・campaign identity・`pin.CURRENT_PIN` の照合 |
| `orchestrator/campaign/env_contract.py`、`calibration_verify.py` | 較正の path / hash と契約世代の束縛、較正 bytes の検査 |
| `orchestrator/campaign/s8b_floor_campaign.py` | pin を含む凍結 protocol の解決・生成 |
| `output/insights/2026-09-07_t2364-paper-story-a2-certification/raw-manifest.json` (+ 同 dir の `artifact-manifest.json`、`completion-receipt.json`)、`2026-08-24_paper-story-a2-certification/raw-manifest.json`、`2026-09-08_t2411-paper-story-a6-certification/raw-manifest.json` | 凍結 evidence の `current_pin` (7 桁) と file hash による束縛 |
| `docs/decisions.md` (D1936 項 1、D2083、D2114) | pin 固定・用途限定登録・再承認範囲の正本 |

## 5. 裁定に残す論点 (再承認パッケージの構成要素。本 wave は決めない)

1. 候補 `e9e477ca` を新 pin として承認するか (材料 1〜3 を根拠に)。承認するなら gitlink・`CCBENCH_FULL_SHA`・`CURRENT_PIN` を同じ commit で更新し、§4.1 の作業を新系列の開始条件にする。
2. GitHub への公開 (push、人間、D16) と取得確認。GitHub だけを取得元とする clone で候補を取得できることは未確認。
3. clang 14 の比較未完了を、GCC 2 版の pass で足りるとするか (D297 は複数 compiler を求め、family は指定しない)。
4. 旧較正 record の新 pin 系列への流用 (§4.3、親の推奨 = 既定は再取得)。
5. D986 と現行実装の残余 (解決不能な CMake 間接値を拒否しない) は [T-1644] が見送り台帳で据え置き中。pin 前進の条件にするかは同項の再訪条件の問題であり、本 wave は新しい裁定項目を起こさない。

## 6. 段 2 / 段 3 の所見と裁定 (要約。全文 = `verbatim/`)

- 段 2 plan (`verbatim/plan.md`): 親 brief の訂正 6 点 (D986 全件閉塞の断定、preprocess 引数、拒否時に report が出ない、134 は文字列集合、F は機械更新でない、追記は spool の見送り追記)、134 / 134 分類、保証範囲 9 点、decisions fragment 不要。すべて採用。
- 段 3 レンズ A 正しさ境界 (`verbatim/consult-A.md`): must-fix 8 / nit 2。clang の分類と「3 本すべて成功」未達 (採用)、login g++ の version body digest が policy と一致 (親が実測して確認、採用)、16 context の分岐被覆表 (親が候補 blob で検算、採用)、D986 全面閉塞は断定不可 (採用、修理・受容は scope 外)、保証範囲 8 点 (採用)、候補来歴 (採用)、「mocc 単独」「未 push」の限定 (採用、GitHub は親が `ls-remote` で実測)、結果と裁定の分離 (採用)、検査器の版の束縛 (採用)、wall / bytes の用途 (採用)。
- 段 3 レンズ B 波及表 (`verbatim/consult-B.md`): must-fix 6 / nit 2。134 は文字列集合で集合外依存 ≥ 13 (採用、§4.4)、凍結 raw-manifest の pin は 7 桁 (親が検算、採用)、patch 適格性と mocc policy の文言 (採用)、P4 の結論置換 (採用)、較正・floor の境界表 (採用、流用可否は再承認パッケージへ)、追記文 (採用)、134 / 79 の再現条件 (採用)。主分類の訂正 0 件。
- 段 6 レビュー A 正しさ境界 (`verbatim/review-A.md`): must-fix 3 / nit 3、事実誤り 4。採用: 「直接区間は本 wave が初めて」は誤り (T-1943 の pilot raw staging に直接区間の pass report が残る、親が現物と sha256 で確認)、GitHub からの取得不能を断定しない、report が proof chain 外という T-1584 当時の留保を現行へ一般化しない、`GLOBAL_VALUE_DEFINE` は define map を 4 種にするが digest は増やさない、registered 較正 record は全 8 件 (集合内 6 件)、`head_sha` は schema 検証対象だが pin との等値照合には使われない。すべて README に反映済み。
- 段 6 レビュー B 波及表 (`verbatim/review-B.md`): must-fix 1 / nit 2。件数 A12 / B12 / C31 / D1 / E35 / F31 / G12 を再集計して一致、分類の訂正 0、閉包 script の再実行で TSV と完全一致、集合外依存 13 file の実在と役割を確認。採用: registered 8 件 / 集合内 6 件の区別、見送り追記文から可変状態 (「裁定待ち」) を外す、worklog fragment 本文の圧縮。
- 親の裁定は `verbatim/s4-adjudication.md`。decisions fragment は作らない (新しい設計判断なし)。

## 7. 再現情報と証拠索引

- 実装面差分ゼロ (docs のみ)。変異 matrix は免除、受入全走は実施 (結果は worklog)。
- checker は親が実走 (§3.1)。段 2 / 3 / 6 の子は read-only の静的検査で、pytest・checker は実走していない。
- `verbatim/` の一覧と sha256 は `verbatim/MANIFEST.json` (自己 hash は含めない)。JSON report は正規化せず原 bytes を保持。子の逐語・log などの text は行末空白と EOF の連続空行だけを可逆最小正規化し (可視文字不変)、正規化前後の sha256 と件数を MANIFEST.json に記録した。
- 閉包の再取得は `verbatim/pin_closure_scan.py.txt` を任意の HEAD に当てる (main の進行で件数は変わる。旧 TSV は上書きしない)。
