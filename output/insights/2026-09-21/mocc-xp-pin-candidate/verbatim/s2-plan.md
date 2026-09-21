# 判定と設計の前提

**(P1) 条件付き支持、(P2) 条件付き支持、(P3) 支持、(P4) 条件付き支持、(P5) 条件付き支持、(P6) 支持。** 最小修正版を C に載せ、既存 driver の候補 mode で実走する案を採る。ただし、旧成果物との分離、`.text` bytes の追加観測、可搬 test と実 C の束縛を具体化する。

本回答は **未実走・静的読解**である。pytest・build・前処理・patch 適用・commit は実行していない。親の保存済み log と report の読解、Git オブジェクトの読取、コード検索を行った。

以下、`BASE` は `e9e477ca1b55348ab4530de0b1cf663ce4555290`、`J` は `/work/1/SFC/tanab/dev-wave-jobs/dev-wave-mocc-xp-pin-candidate` を表す。repo 内の `file:line` は提示された worktree の現物、`J/…` は repo 外の資料を指す。

親 brief は次の点を限定して読む必要がある。

- **certification gate は pin 照合ではない。** 渡された compiled-source snapshot の literal `#if TRACE` 内に X/P emitter があるかを調べる。Git OID、前処理後の到達可能性、実発火は同 gate の保証外である。「素の BASE の mocc は gate 偽」は支持するが、「現行 pin を使う mocc の結果が常に indeterminate」は広すぎる。BASE＋旧 patch の診断実走には既に certified 正例がある。C との束縛は今回の driver が担う。根拠: `orchestrator/verifier/model.py:77,192,258`、T-2294 insight `README.md:15`。
- **p4 は TRACE=1 build の証拠ではない。** GCC 11.4 / 12.3 の保存 report は各 16 context、include 11 行、`basis=exact_identity`、`result=pass`。負例 4 本は `git apply --check` の成功である。コンパイルと実行の成功へ一般化しない。根拠: `J/probe/p4-keep-line17.sh:33,38`、`p4-keep-line17.log:6`。
- p4 script 冒頭の「`#line 17` を除く」というコメントは実装と不一致。実際の置換は `<set>` だけを除き、`#line 17` の存在を assert して残している。結果の解釈は処理本文に従う。根拠: 同 `.sh:2,18,21`。
- witlight の保存計画は **land 後・撤去前の fetch**。今回の land 前 fetch は先例からの前倒しであり、同じ順序ではない。根拠: witlight insight `README.md:193`。

# 1. (P1) 候補の内容 — 条件付き支持

**確定案:** 新規 `patches/instr-mocc-lock-coverage-pin-candidate.patch` を BASE 基準で作る。適用後 source は「BASE＋旧計装 patch」に対して、次の 3 箇所だけを変える。

| 旧 patch 上の位置 | 変更 |
|---|---|
| `patches/instr-mocc-lock-coverage.patch:8` | `#include <set>` の行だけを削除 |
| 同 `:22` | `std::multiset<const void*>` → `std::unordered_multiset<const void*>` |
| 同 `:32` | 同じ型置換 |

`#line 17` と残る計装本文・context は保存する。**byte 不変の対象は適用後 source の他の部分**である。新 patch の hunk 件数・新側開始行は 1 行削除に合わせて再生成しなければならず、patch のメタデータまで旧 bytes 不変とはできない。期待差分は BASE に対して transaction.cc の **64 行追加のみ**。根拠: 旧 patch `:4,16,48`、`J/probe/p4-keep-line17.log:2`。

**(a) P の意味論。** 各 `rcdptr_` を `const void*` に変換して挿入し、同じ pointer 値の出現回数を保存する。`unordered_multiset` は重複を消さない。hash 衝突は等値比較で区別され、bucket 順・挿入順は等価性の条件にならない。したがって「size が等しい、かつ各 pointer の多重度が等しい」は D1686 の主張と一致する。op、key、payload、CLL 順序、所有者の一致まで証明するものではない。根拠: `J/verbatim/D1686.md:3`、旧 patch `:21,29,34`。

計算量について「hash なので常に線形」とは書かない。unordered の等価性比較には最悪二次の上界があり、一般の equivalent-key group の比較では重複群の大きさにも依存する。今回の pointer 等値群では群内の値そのものが同じで、手元の libstdc++ 11 は群を数え、対応 bucket と `is_permutation` を使う。旧 `multiset` の順序列比較とは処理・確保・cache 挙動が異なる。**P の述語は同値でも TRACE=1 の観測負荷は同一でない**ため、旧実測を流用せず C 上で再走する。根拠: `/usr/include/c++/11/bits/functional_hash.h:107`、`bits/hashtable_policy.h:1743`、`bits/unordered_set.h:1818`。

**(b) header 依存と対案。**

| 案 | 評価 |
|---|---|
| `unordered_multiset` | `<unordered_set>` が `trace.hh:33` から供給される。呼出元の include と供給先の内容はいずれも `#if TRACE` 内。C の親・touch set を固定する今回には明示可能な依存であり採用する |
| `vector`＋sort＋比較 | `<vector>` は `cc/mocc/include/transaction.hh:3`、`<algorithm>` は `transaction.cc:2` に存在する。ただし無関係な object pointer を並べる comparator は `std::less<const void*>` 等の全順序を明示すべきで、裸の pointer `<` に頼る案にはしない。比較前後の sort と宣言が増え、今回の最小変更条件から遠ざかる |

`<unordered_set>` が偶然どこかの STL 内部 include から入る、という依存ではない。**BASE が固定する trace.hh の明示 include に依存する**。test でその供給元も確認する。ただし将来 header を整理した際の独立性は直接 include より弱い。この限界を README に記す。D297 checker を緩める理由にはしない。根拠: `external/ccbench/cc/mocc/transaction.cc:13`、`external/ccbench/include/trace.hh:25,33`。

**(c) build flags。** `-O3 -Wall -Wextra -Werror -std=c++20` に対して、変更した型・insert・比較の静的な不成立は見当たらない。変数は同じ TRACE 条件内で使われ、`std::size_t` 同士を比較し、pointer の数値変換も追加しない。`validation()` の途中に今回の宣言を飛び越す goto はない。RWLOCK 無しでは従来どおり CLL/rwlock 参照が成立しない。**C の build は未実走であり、警告ゼロは未確認**。根拠: `transaction.cc:986`、旧 patch `:20`、`patches/README.md:561`。

**(d) `#line 17`。** BASE では trace include の `#endif` が物理行 16、次の空行が 17、`using namespace std;` が 18。候補では `#line 17` 自体が追加の物理行になり、その次の空行を論理行 17 に戻す。残すことは D1687 と整合する。また early/hot 負例の先頭 hunk がこの行を context に含む。p3 で削除するとこの 2 本が拒否され、p4 で保存すると 4 本とも適用可能だった。根拠: `transaction.cc:16`、`broken-mocc-early-unlock.patch:8`、`broken-mocc-hot-update-unlock.patch:7`、`J/probe/p3-minimal-variant.log:8`。

**(e) D297 の判定との対応。**

| checker の判定 | 候補が通る理由・必要な実測 |
|---|---|
| `check_trace0_preprocess_identity.py:528` BOM | 旧 source を保持し、BOM を追加・除去しない |
| `:539` literal include | include operand は旧 source と同じ |
| `:541` include 行列 | `<set>` を候補へ入れないため 11 行の順序・文字列が完全一致 |
| `:547` 追加 include 特例 | 分岐へ入らない。trace.hh 特例を利用して `<unordered_set>` を許す設計ではない |
| `:552` marker 列 | include 行の順序・個数が不変なので同じ marker 列になる |
| `:560` head defines | CMake 不変。追加の条件指令は既存の `TRACE` だけで、新しい裸 macro はない |
| `:567,580` TRACE=0 | 追加の変数、container 操作、X/P 検査は消える |
| `:583` 正規化出力 | 元の非 TRACE 本文を保持する。`#line` は所定の論理位置へ戻す。p4 の各 context で一致を観測済み |
| `:592` include 活性 | 既存 include の条件所属を変えない。`_compare_include_activity:484` の完全一致経路 |
| `:636` context 件数 | 追加によって列挙を変えない。p4 は各 16 件。正式 C でも実件数を report で確認する |
| `:670` 祖先・差分 | C を BASE の単一親とし、通常 file の transaction.cc だけ変更。`--expect-paths` と一致させる |

保証は D297 の名称どおりに限定する。p4 の合格から、全 macro 空間、header 展開済み TU、全 compiler、TRACE=1 build、binary identity、admission toolchain 全体の一致を導かない。16 件も 16 種の独立した mocc 構成とは限らない。根拠: T-2756 insight `README.md:83,92,114`。

# 2. (P2) 実走 driver — 条件付き支持、既存 file の候補 mode を採用

**既存 `s3_mocc_lock_coverage.py` に候補 mode を追加する。** `PIN`、`INSTRUMENTATION_PATCH`、`CHECK_KEYS`、既存 helper の既定動作・signature は保持する。旧 mode は旧 schema・旧 path・旧 14 check のまま動かす。

新 CLI は次とする。

```text
--candidate-oid <C の full 40-hex OID>
--third-party-cache <absolute path>
--policy <既存 mocc_trace_v1_policy.json>
--out <候補専用 JSON>
```

`--candidate-oid` 無しは legacy mode。候補 mode の既定出力は
`output/env/pegasus/calibration/s3_mocc_xp_pin_candidate.json`、
schema は `s3-mocc-xp-pin-candidate/v1` とする。候補 mode から旧 3 本の proof JSON を上書きする出力指定は拒否する。根拠となる分岐箇所: driver `:594,609,707`、旧 consumer `test_mocc_proof_surface.py:957`。

**登録簿の比較。**

| 面 | 既存 mode 拡張 | 新規 driver |
|---|---|---|
| materializer | `_build_variant` / `_install_dependency` をそのまま呼ぶので `materializer_admission.py:78,93` 不変 | helper を委譲するだけなら追加登録不要。新 build 関数へコピーすれば新登録が必要 |
| condition gate | `driver_id` は実際の file と一致し `:283` 不変 | 旧 helper を呼ぶと旧 ID が記録される。新 ID を正確に記録するには helper の引数化か wrapper が必要 |
| DefineSpec/witness | 同じ負例 macro・patch を使うため `condition_meaning_gate.py:204,276` 不変 | 新 file だけを理由に DefineSpec が必要になるわけではない |
| subprocess inventory | 既存 `_run_checked` / `_run_trace` 経由。`test_ccbench_spawn_sites.py:63,217` 不変 | subprocess を新設すれば inventory 追加。完全委譲なら不要 |
| build authority | 既存 materializer のまま。`test_p3_build_authority_cli.py:164,183,186` 不変 | 新たな manual build 実装なら追随が必要 |
| 後続 import | 旧定数・helper を保持すれば不変 | 新 file でも旧側を触らなければ不変 |

**「新 driver は必ず登録簿変更が必要」は反証する。** 完全委譲なら不要な面もある。ただし今回、同じ build・workload・負例経路を継承するには候補 mode が最小である。なお condition gate は driver ID の登録集合を照合しておらず、非空文字列を要求する。ID の固定は provenance 上の整合として扱う。根拠: `condition_meaning_gate.py:1002`、`s3_mocc_mutation_proof.py:22,62`、`s3_mocc_template_proof.py:20`。

**候補 source の作り方。**

1. CLI の full OID を解決し、C の親が **ちょうど `[BASE]`** であることを確認する。
2. BASE→C の raw tree 差分が transaction.cc の通常 file・mode 不変の変更 1 件だけであることを確認する。
3. 一時 `checkout(BASE)` に新候補 patch を厳密適用し、その source bytes・Git blob が `C:cc/mocc/transaction.cc` と一致することを確認する。この checkout は候補の束縛確認用である。
4. 実走 source は必ず `checkout(C)`。clean を確認してから、正例は無 patch、負例は対応する broken patch だけを直接適用する。
5. verifier には各 build に使った source root を渡す。根拠: driver `:387,430,648`、`patchharness.py:174,204,346`。

**実走行列。** 旧 6 走を C 上で再実行し、4 本目の負例にも最小の正例対を置く。

| run | source / workload | 期待 |
|---|---|---|
| stock_single / stock_high | C、既存 SINGLE/HIGH_FLAGS | 旧 check の意味を保持 |
| lockskip_single / lockskip_high | C＋lockskip、macro=1 | X 発火、single は cycle=0・indeterminate |
| perm_erase_single | C＋permutation、macro=1 | `size-changed` の P |
| early_unlock_single | C＋early、macro=1 | 入口 X=0、保持 2 reason が正 |
| hot_stock_single | C、rr0・通常 UPDATE、max_ope=1、thread=1、temp_threshold=0 | certified、X/P=0、非 INSERT write 正 |
| hot_update_unlock_single | C＋hot-update、同じ workload、macro=1 | 完走、cycle=0、P=0、入口・保持の X が正、indeterminate |

hot 対の `ycsb_rmw=false` / `ycsb_max_ope=1` は既存 mutation proof の U workload に合わせる。C の stock TRACE=1 binary は再利用できるため、build は TRACE=1 が stock＋負例 4 本、TRACE=0 が 2 本の計 7 本。**旧 6 走の緑だけで hot 経路まで再立証したとはしない。** 根拠: `s3_mocc_mutation_proof.py:33,42,44`、hot patch `:23,42,56`。

**check 集合は旧 14＋候補固有 7＝21 key。** 旧 `CHECK_KEYS` 自体は変更せず、新 `CANDIDATE_CHECK_KEYS` を作る。

| 旧 key | 候補 mode での意味 |
|---|---|
| `stock_single_certified_and_silent` | C の single 正例 |
| `stock_single_non_insert_writes_positive` | 同上の実 write 到達 |
| `stock_high_xp_silent` | C の high 正例。certified を要求する key ではない |
| `stock_high_non_insert_writes_positive` | 同上の実 write 到達 |
| `lockskip_single_cycles_zero_x_positive` | C＋lockskip |
| `lockskip_single_both_entry_and_retention_reasons` | 既存の 3 reason |
| `lockskip_high_x_positive` | C＋lockskip、high |
| `perm_single_only_size_changed` | C＋perm |
| `early_unlock_single_retention_reasons_without_entry` | C＋early |
| `trace0_nm_izanagi_zero` | BASE/C の TRACE=0 |
| `trace0_strings_izanagi_trace_zero` | 同上 |
| `trace0_text_identical` | 既存の正規化 objdump 比較 |
| `all_patch_touch_sets_are_transaction_only` | 新候補 patch＋broken 4 本の実測 touch set |
| `toolchain_matches_policy` | 既存 policy の compiler digest 比較 |

追加 key:

```text
candidate_parent_is_base
candidate_tree_changes_transaction_only
candidate_blob_matches_patch
candidate_proof_surface_present_base_absent
trace0_text_bytes_identical
hot_stock_single_certified_and_silent
hot_update_unlock_single_x_reasons_without_cycles
```

旧 14 key は `compute_checks()` をそのまま使用し、新 helper が候補固有の観測から追加 7 key を導出する。各 key に成立入力と、それだけを壊す対照を置く。旧 `compute_checks()` の変更は不要。根拠: driver `:493,589`。

**TRACE=0 は BASE と C の比較。** source と build の絶対 path 長を揃える。既存の `trace0-base` / `trace0-inst` に加え、`checkout()` の生成 source path 長も記録・照合する。`_trace0_record()` は既存の逆アセンブル比較であり、`.text` bytes 比較ではないので変更せず、候補専用 helper が `objcopy --dump-section .text=…` 等で section を抽出し、非空 bytes・size・sha256・直接比較結果を記録する。根拠: driver `:444,451,481,687`、`patchharness.py:362`。

**JSON の束縛。** 少なくとも次を実観測から保存する。

- `ccbench_commit=C`、`base_commit=BASE`、C の全 parent OID、tree OID。
- transaction.cc の base/candidate blob OID、candidate source SHA-256。
- 候補 patch の path/hash、BASE に適用した結果の blob/hash、raw tree 差分。
- broken 4 本の path/hash/touch set、condition gate 4 本、run 行列と実 flags。
- BASE/C の proof-surface assessment、TRACE=0 の section 証拠、21 check。
- 既存 NON_ADMISSIBLE materializer、toolchain の観測値と比較元 policy の path/hash。

既存 policy の `new_oid=BASE` は旧比較契約として保持する。候補 mode は `_load_policy()` を「BASE と toolchain の固定条件」として使用し、**policy が C を承認しているとは記録しない**。根拠: driver `:140`、policy `:20`。

compute の 1 job 内で実行する argv:

```bash
python3 -m orchestrator.campaign.s3_mocc_lock_coverage \
  --candidate-oid "$C" \
  --third-party-cache "$IZANAGI_PEGASUS_THIRDPARTY_CACHE" \
  --policy tools/pegasus/mocc_trace_v1_policy.json \
  --out output/env/pegasus/calibration/s3_mocc_xp_pin_candidate.json
```

これは gen_S の実行 body であり、login で直接実行しない。投入先の submodule object store に C が存在することを、投入前に確認する。

# 3. (P3)/(P4) C の作成と保存

**(P3) 支持。** branch は `izanagi-mocc-xp-instrumentation`、単一親は BASE とする。readfrom-witness と witlight の branch は動かさない。`izanagi-mocc-pin-e9e477ca` は承認済み pin の公開名であり、未承認候補に同名を流用しない。根拠: T-2304 insight `README.md:11`、`J/verbatim/D16.md:8,38`。

**(P4) 条件付き支持。** A が作った patch を親が一時 worktree で適用し、`commit -F` する。親が C++ 本文を別実装しない。順序は次のとおり。

1. wave submodule の HEAD=BASE、clean と branch 名の非衝突を確認する。
2. 同 object store から一時 worktree を BASE で作り、新 branch を作成する。
3. 新候補 patch を `git apply --check` 後に適用する。
4. index に transaction.cc だけを載せ、差分が 64 行追加・他 path/mode 不変であることを確認する。
5. message file を確認し `git commit -F <message-file>`。
6. 最終 C、親、tree、blob、source hash、message を保存する。**message の amend でも C は変わる**ので、確定後の OID を B と D297 実走へ渡す。
7. branch を含む自己完結 bundle を `J/C.bundle` に保存し、`git bundle verify` と hash を記録する。
8. land 前に、主 checkout の **submodule git dir** へ bundle から branch を fetch し、OID/tree/blob 一致を確認する。既存同名 ref が別 OID なら force 更新しない。
9. wave と主 checkout の submodule HEAD・index gitlink が BASE のまま、working tree が clean であることを確認する。

fetch は refs/objects の保存であり、checkout や gitlink 更新ではない。これを land 前に済ませる案は支持するが、witlight 先例の land 後 fetch からの変更として記録する。根拠: witlight insight `README.md:180,193`、`J/verbatim/D16.md:31`。

commit message の本文案:

```text
feat(mocc): add TRACE-only lock coverage and permutation checks

Add RWLOCK/CLL entry, pre-write and pre-publish lock checks and
write-set size/record-pointer multiset preservation checks.

Use unordered_multiset supplied by the existing TRACE trace.hh include.
Preserve the base source's logical line positions with seven #line
restorations. Change only cc/mocc/transaction.cc relative to e9e477ca.

This commit is an Izanagi trace-hook candidate. It does not advance
the superproject pin or add write-intent coverage.
```

最後の trailer block には、実際に寄与した Codex author、採用された review、親の実質的 manager/integrator を `docs/ai-provenance.md:18` の形式で記録する。値は実際の表示値から採り、witlight の値をコピーしない。同じ role を複数行にする場合は scope を付ける。機械的 commit 代行だけなら integrator として水増ししない。根拠: 同 `:25,46,67`、witlight `verbatim/W-commit-message.txt:18`。

submodule には provenance 導入履歴が無い可能性があり、superproject と同じ full-history 監査が成立したと推定しない。message の形式確認、実 commit message の確認、superproject 側の通常監査を区別して記録する。根拠: T-2756 insight `README.md:57`。

# 4. (P5) test の可搬性 — 条件付き支持

**「他 worktree が C を持つ保証はない」は支持する。「gitlink でないので絶対に取得されない」は反証する。** 通常の submodule update は記録された BASE を checkout する操作であり、C を必須取得しない。一方、remote ref の fetch や object store の共有によって C が既に存在する場合はある。test の前提にしてはいけないのは、C の存在が保証されない点である。根拠: T-2756 insight `README.md:38`、T-2304 insight `README.md:31,87`。

**確定案:** 新 patch を「branch 上の候補 C を再現する test/証拠用差分」として保存する。trace-hook の成果物本体は C であり、新 patch を通常 producer に追加適用する運用にはしない。C 上の実走では計装 patch を当てない。

D16 の trace-hook→branch 原則と、同じ差分を patches/ に保存することには緊張がある。ただし今回のユーザー依頼は C の作成を明示し、既存 README も T-2294 の計装 patch を認めている。**branch 移送を済ませたうえで、可搬な再現資料を保持する**ものと位置付ける。D16 の一回限り試作例外を再利用する説明は採らない。根拠: `J/verbatim/D16.md:13,19`、`patches/README.md:14,533`。

新 test は **`orchestrator/tests/test_mocc_xp_pin_candidate.py` 1 本**に置き、旧 test file の bytes は変えない。既存 helper は module alias 経由で import できる。`_source_root(*patches)` は patch を引数で受け、X/P 構造 helper は container 型を固定していない。旧 test 関数自体を import して新 file の test として収集させない。根拠: `test_mocc_proof_surface.py:98,256,370,1009`。

| 新 test node 案 | 内容 |
|---|---|
| `test_candidate_source_is_minimal_transform` | BASE＋旧 patch から指定 3 箇所だけ変えた bytes と、BASE＋新 patch の bytes が完全一致 |
| `test_candidate_header_dependency` | BASE の trace.hh に `<unordered_set>` が TRACE 内に存在し、新 source の include 行列が BASE と同じ |
| `test_candidate_proof_surfaces` | C 相当=X/P present・I absent・gate 真、BASE=X/P absent・gate 偽 |
| `test_candidate_xp_structure` | `_assert_instr_x_p_structure`、`_assert_instr_source_contract` を再利用。unordered container 2 箇所と挿入対象も検査 |
| `test_candidate_trace0_logical_rows` | 既存 preprocess / logical-row helper で BASE と C 相当を比較 |
| `test_candidate_broken_patch_contracts` | C 相当への broken 4 本の厳密適用、作用位置、balanced relock、directive 一意性 |
| `test_candidate_fixture_routing` | g7 正例は certified、BASE は indeterminate、m3/m4 は各 X/P 違反で indeterminate |
| `test_candidate_identity_controls` | 単一親・1 path・mode・blob 照合の正例と独立した破壊対照 |
| `test_candidate_mode_source_routing` | C checkout に計装 patch を適用しないこと、負例 patch を省略しないこと、TRACE=0 の BASE/C 対を検査 |
| `test_candidate_checks_are_input_derived` | 21 key の完全一致と各観測を壊した際の対応 key の偽化 |
| `test_candidate_json_is_bound` | 新 schema、C/親/tree/blob、patch hash、行列、21 check、`.text` 証拠の照合 |

JSON consumer は C を `git show` しない。親が C 確定時に渡した **C・tree・blob の固定期待値**を新 test に持ち、BASE＋新 patch の source bytes から blob OID と SHA-256 を再計算する。JSON の OID 1 文字改変もこれで検出する。固定期待値を JSON から逆算して定義しない。

ただし、可搬 test 単体は「その commit object が現存し、この tree を持つ」ことまで独立再検査するものではない。**実 C→親/tree/blob の関係は、compute driver の Git 実測と親の保存記録が担う。** この役割分担を README に明示する。根拠: 既存 consumer `test_mocc_proof_surface.py:968`、`J/s1-brief.md` の P5。

# 5. D297 の正式実走計画

親が login で、最終 C を持つ submodule に対して次の 3 本を実行する。CLI は full OID を要求するため、**`--old e9e477ca` の短縮形は実 argv に使わない**。根拠: `tools/check_trace0_preprocess_identity.py:731`。

```bash
python3 tools/check_trace0_preprocess_identity.py \
  --repo "$C_REPO" \
  --old e9e477ca1b55348ab4530de0b1cf663ce4555290 \
  --new "$C" --cxx /usr/bin/g++ \
  --expect-paths cc/mocc/transaction.cc

python3 tools/check_trace0_preprocess_identity.py \
  --repo "$C_REPO" \
  --old e9e477ca1b55348ab4530de0b1cf663ce4555290 \
  --new "$C" --cxx /usr/bin/g++-12 \
  --expect-paths cc/mocc/transaction.cc

python3 tools/check_trace0_preprocess_identity.py \
  --repo "$C_REPO" \
  --old e9e477ca1b55348ab4530de0b1cf663ce4555290 \
  --new "$C" --cxx /usr/bin/clang++ \
  --expect-paths cc/mocc/transaction.cc
```

保存先は `J/evidence/d297-{gcc11,gcc12,clang14}.{stdout.json,stderr.txt}`。argv、rc、compiler の解決 path/version、checker hash、C/BASE OID、report hash を索引に保存し、insight へ収載する。stdout が空の失敗を合格 report に整形しない。

**負例 C′:** 別 scratch の BASE に旧 T-2294 patch をそのまま適用し、一時 commit を作る。候補 branch には入れない。同じ checker を BASE→C′、GCC 11 で走らせ、rc=1 と「include 行文字列（順序込み）が不一致」を期待する。これが p2 と同型の拒否理由である。C′ は broken protocol の commit ではなく、include 契約を満たさない計装候補の対照である。根拠: `J/probe/p2-d297-asis.log:2`、checker `:547`。

clang 14 が再び空入力の環境 prefix 不一致で止まれば、**比較未完了**と記録する。候補不一致や clang 合格に読み替えない。D2150 の GCC 2 版受容は旧候補への裁定なので、今回の材料でもその既知限界を明示する。checker 修理は本 wave に含めない。根拠: T-2756 insight `README.md:114`、`J/verbatim/D2150.md:14`。

# 6. 波及表 — D1603 材料 (3)

以下は **将来 pin を C へ進める場合**の分類であり、本 wave の変更一覧ではない。母集合は指定逐語の **43 file**。主分類は **追随 15、据置 27、衝突 1**。複数性質を持つ file は備考で区別する。

| # | file:line | 分類 | pin 前進時の扱い |
|---:|---|---|---|
| 1 | `.claude/agents/auditor.md:53,59` | 据置 | BASE の行位置を明示した proof 契約。C 向け改訂時は関連 hash 束縛を伴う別作業 |
| 2 | `.codex/role-adapters/auditor.json:19` | 据置 | 上記本文の休眠 adapter。pin だけで再生成・起動しない |
| 3 | `docs/paper-story/2026-09-19.md:130` | 据置 | 日付版の歴史 |
| 4 | `docs/paper-story/2026-09-20.md:172` | 据置 | 日付版の歴史 |
| 5 | `docs/paper-story/2026-09-20b.md:388` | 据置 | 日付版の歴史 |
| 6 | `docs/paper-story/2026-09-21.md:14` | 据置 | BASE 前進の取得事実 |
| 7 | `docs/paper-story/2026-09-21b.md:121` | 据置 | 日付版の主張・証拠 |
| 8 | `docs/paper-story/README.md:218,225` | 据置 | 既存結果の索引説明は保存。新成果は新項目 |
| 9 | `docs/paper-story/claim-evidence/2026-09-20.md:168` | 据置 | 日付版の証拠対応 |
| 10 | `docs/paper-story/claim-evidence/2026-09-21.md:185,352` | 据置 | BASE 時点の主張境界 |
| 11 | `docs/paper-story/results/2026-09-20-mocc-g2-observation-conditions.md:81` | 据置 | producer OID/hash の実測記録 |
| 12 | `docs/paper-story/results/2026-09-20-mocc-witlight-four-arm.md:120` | 据置 | W と合成 source の取得事実 |
| 13 | `docs/paper-story/results/2026-09-21-b8-final-candidate-longrun-verify.md:58,65` | 据置 | BASE に束縛された正式結果 |
| 14 | `docs/phase3-8b-restart-runbook.md:161` | 追随 | 現行 gitlink の期待値。旧 floor の説明は保存 |
| 15 | `docs/related-work/cc-candidates-2026-09-17.md:87` | 据置 | 調査時点の差分量 |
| 16 | `docs/related-work/claim-survey/2026-09-18b-axis1-search-execution.md:38` | 据置 | 凍結済み裁定の引用 |
| 17 | `orchestrator/campaign/axis_mocc_temperature.py:21,22,42` | **衝突** | `PIN` は自動追随するが PROOF_PIN/template/proof は BASE 固定。C 系列へそのまま接続できない |
| 18 | `orchestrator/campaign/buildcache.py:1059` | 据置 | BASE の形を再実測した履歴は保存。C について生成物形の新確認が必要 |
| 19 | `orchestrator/campaign/pin.py:31` | 追随 | CURRENT_PIN。歴史定数と取得履歴は保持 |
| 20 | `orchestrator/campaign/s3_mocc_lock_coverage.py:42` | 据置 | legacy PIN は BASE 固定。候補 mode と分離 |
| 21 | `orchestrator/campaign/s3_mocc_template_proof.py:244` | 据置 | BASE 固定の template proof/control |
| 22 | `orchestrator/campaign/s8b_approved.py:67` | 追随 | 承認後に gitlink/CURRENT_PIN と同一 commit |
| 23 | `orchestrator/tests/acceptance_duration_ledger.json:10640` | 据置 | 旧 node 名と実測所要時間 |
| 24 | `orchestrator/tests/test_between_run_floor.py:255,445` | 据置 | BASE で R/W hook が入った履歴。C でもその事実は成立 |
| 25 | `orchestrator/tests/test_dynamic_backoff_transitions.py:17` | 追随 | 実 checkout の HEAD に対応する PIN_FULL |
| 26 | `orchestrator/tests/test_mocc_mutation_proof.py:24` | 据置 | BASE＋旧計装の proof |
| 27 | `orchestrator/tests/test_mocc_proof_surface.py:28,397` | 据置 | BASE/511c と旧 patch の対照 |
| 28 | `orchestrator/tests/test_mocc_trace_job_contract.py:31` | 据置 | 旧 pilot policy/receipt の契約 |
| 29 | `orchestrator/tests/test_p3_build_authority_cli.py:196` | 追随 | 現行 repo_stock_pin の独立期待値 |
| 30 | `orchestrator/tests/test_p3_s4_loop.py:9666` | 追随 | policy preimage の現行 epoch。driver の独立 source pin は別 |
| 31 | `orchestrator/tests/test_p3_s4_loop_sort.py:781` | 追随 | CURRENT_PIN alias の期待値・policy golden |
| 32 | `orchestrator/tests/test_p3_s4_loop_trigger_gating.py:2178` | 追随 | 同上 |
| 33 | `orchestrator/tests/test_s6_sort_sweep.py:390` | 追随 | 現行 pin の独立期待値 |
| 34 | `orchestrator/tests/test_s8a_trigger_sweep.py:159,544` | 追随 | 現行 characterization/policy。歴史 epoch は保持 |
| 35 | `orchestrator/tests/test_s8b_protocol_builder.py:74` | 追随 | 現行承認定数に束縛された builder golden |
| 36 | `orchestrator/tests/test_t126_qualification_driver.py:785` | 追随 | 現行 stock source の期待値 |
| 37 | `orchestrator/tests/test_t2187_adaptive_const_probe.py:47` | 追随 | 実 checkout と現行 probe に対応する PIN_FULL |
| 38 | `output/env/pegasus/calibration/s3_mocc_lock_coverage.json:5` | 据置 | 旧実測 bytes |
| 39 | `output/env/pegasus/calibration/s3_mocc_mutation_proof.json:5` | 据置 | 旧実測 bytes |
| 40 | `output/env/pegasus/calibration/s3_mocc_template_proof.json:3` | 据置 | 旧実測 bytes と hash 鎖 |
| 41 | `patches/README.md:14,538,630` | 追随 | C の採用状態・適用条件を追記。旧 preimage 記録は書換えない |
| 42 | `tools/pegasus/mocc_trace_v1_policy.json:20,21` | 据置 | 511c→BASE の比較契約。C 向けは別契約 |
| 43 | `tools/pegasus/probes/t2187_adaptive_const_probe.py:72` | 追随 | CURRENT_PIN との一致を要求する probe |

**文字列集合外の依存。** `CURRENT_PIN`、`CCBENCH_FULL_SHA`、`PROOF_PIN`、`s3_mocc_lock_coverage`、`instr-mocc-lock-coverage.patch`、`repo_stock_pin`、`resolve_current_floor_protocol` の key 側も検索した。43 file は更新閉包ではない。

| 依存 | 帰結 |
|---|---|
| gitlink `external/ccbench` | 将来は承認定数 2 本と同時更新。本 wave は不変 |
| `patches/instr-mocc-lock-coverage.patch:4` | C には既に X/P があり、そのまま重ねない。旧 patch は BASE 用に保存 |
| `patches/mocc-temperature-predicate-variant.patch:23` | BASE preimage。C への機械適用が仮に通っても、旧 `#line` と新 helper 挿入の相互作用を別確認する必要がある |
| `patches/instr-mocc-lock-coverage-temperature.patch:4,16` | BASE＋template 用。C へ二重適用する設計は不可 |
| `axis_mocc_temperature.py:66` | proof OID、template/hash を束縛。探索用 PIN の移動だけでは proof の移行にならない |
| `s3_mocc_mutation_proof.py:28,35,49` | legacy PIN・旧 patch・旧 JSON を import。旧 driver の定数変更は波及する |
| `s3_mocc_template_proof.py:20,31,34` | wave1/legacy の helper と proof hash 鎖。今回保持 |
| `tools/pegasus/mocc_trace_pilot.sh:1748,3240,3524` | T1943 receipt v2 は旧 X/P patch path/hash、適用後 source hash、TRACE=0 build 配線を束縛。new_oid だけ C に置換すると二重適用・命題不一致になる |
| `build_admission.py:502` | policy preimage に CURRENT_PIN。C への前進で policy epoch が変わり、SHA 文字列を含まない golden と live consumer に波及 |
| `s8b_floor_campaign.py:1032,1296` | 現行 gitlink と承認定数、head に対応する floor protocol を要求。旧 floor の自動流用はできない |
| `ident.py` と旧 campaign.lock | source pin と admission policy に束縛。固定 source OID だけでは新 main の policy 変更を免れない |
| fixture / 事前登録 / 較正 / 凍結 | 旧取得事実は保持。C の取得値と主張する新系列だけ再取得・新登録・successor を用意 |
| auditor 本文の hash consumer | 将来本文を C 用に変更する場合、adapter・review ledger・関連 test の hash 同期も必要 |
| `docs/phase3.md:2744` | T-167 の再承認経路。今回、再承認提示や「pin 前進済み」の記録はしない |

policy epoch の波及は仮想問題ではなく、前回 104 failed / 75 errors と後続取り残しを生んだ実例がある。将来の pin 更新では literal 置換だけを作業範囲と見積もらない。根拠: T-2304 insight `README.md:46,61,65`。

# 7. (P6) I 面 — 支持、未実装として残す

BASE の `cc/` と `include/trace.hh` を、verifier が認識する `emit_write_intent_violation` と `"I "` について Git tree 上で検索し、該当なしだった。親の「現行 pin に認識対象 I emitter がない」は支持する。ただし文字列検索からあらゆる別表記・生成コードの不在まで証明しない。verifier が評価対象とする protocol 自体も silo/si/mocc に限られる。根拠: `orchestrator/verifier/model.py:37,51`。

`W … I` の INSERT op は I 違反レコードではない。X/P gate は I を要求しないため、C で gate 真・I absent は矛盾しない。根拠: `transaction.cc:1150`、`model.py:77`。

mocc の I を閉じるには少なくとも次の設計が必要であり、X/P の型置換では済まない。

- write_set から逆生成しない独立 shadow を、成功した write intent の登録点に置く。
- storage/key、operation、record pointer、多重度、重複 UPDATE や INSERT/DELETE の意味を決める。
- hot での早期 lock、RLL 経由の再 lock、失敗 return と intent 登録の順序を定める。
- validation/writePhase 前の照合、abort/retry/commit 後の clear、Tuple lifetime を定める。
- erase/forge/op-swap/pointer-swap の対照、TRACE=0 の完全除去、I の実発火と verifier 集計の対応を証明する。

具体的な接続点は `transaction.cc:430,459,477,1059,1134,1210`。Silo の write-intent branch `izanagi-trace-t152` は `c9c1a9c2…` に存在するが、BASE との merge-base は `d706650c…` であり BASE の祖先ではない。mocc 向け実装として取り込めるものでもない。根拠: Git ref/merge-base の読取、`orchestrator/campaign/t152_write_intent_coverage.py:3,53,66`、`docs/phase3.md:2744`。

# 8. 段 4 の変異事前登録案

以下の KILLED node は **見込み**であり、未実走。初回 probe で実際の失敗 node 集合を取り、final spec と区別する。patch hash の consumer だけが赤になる場合を意味検査の成功に数えない。根拠となる先例: T-2294 insight `README.md:84,107`、T-2773 insight `README.md:50`。

| 変異 | 期待 | 主 killer 見込み |
|---|---|---|
| P の pointer 比較を恒真化して違反を抑止 | KILLED | `test_candidate_xp_structure`、`test_candidate_source_is_minimal_transform` |
| X 入口検査を削除／恒偽化 | KILLED | `test_candidate_xp_structure` |
| unordered_multiset を unordered_set に変更 | KILLED | `test_candidate_source_is_minimal_transform`、container 契約 |
| `#line 1169` を ±1 | KILLED | `test_candidate_trace0_logical_rows` |
| `#line 17` を削除 | KILLED | `test_candidate_broken_patch_contracts` |
| `<set>` を候補へ戻す | KILLED | `test_candidate_header_dependency`、正式 D297 対照 |
| JSON の C OID を 1 文字変更 | KILLED | `test_candidate_json_is_bound` |
| JSON の tree/blob/patch hash を変更 | KILLED | `test_candidate_json_is_bound` |
| 候補 mode で broken patch 適用を省く | KILLED | `test_candidate_mode_source_routing` |
| 候補 mode で旧計装 patch を再適用 | KILLED | `test_candidate_mode_source_routing` |
| tree 差分検査を「transaction.cc を含む」に緩和 | KILLED | `test_candidate_identity_controls` の第二 path 対照 |
| 親検査を単なる祖先検査に緩和 | KILLED | 同 node の孫 commit／複数親対照 |
| `.text` bytes 一致を定数 True | KILLED | `test_candidate_checks_are_input_derived` |
| hot 対の X reason 検査を緩和 | KILLED | 同 node |
| 正しい C 相当を拒否するよう条件を反転 | KILLED | identity／source routing の正例 |
| driver docstring の意味不変な言換え | SURVIVED | 等価変更を過剰拒否しない対照 |

P の size 変更だけでなく、**同サイズの pointer 置換と重複数変更**を構造・意味対照に含める。既存 runtime の perm-erase は size 違反しか立証しないため、これを pointer 保存全体の動的実証と呼ばない。根拠: driver `:558`、旧 patch `:29,34`。

# 9. author 分割と完了までの順序

A→親の C 作成→B の順序を採る。旧 test・旧 patch・旧 JSON の bytes を守るため、B は新 test file を使う。登録簿への変更は現設計では **ゼロ**であり、所有を曖昧にした「必要なら何でも更新」枠を設けない。

| 所有者 | 所有 file／操作 |
|---|---|
| Codex author A | 新規 `patches/instr-mocc-lock-coverage-pin-candidate.patch` のみ |
| 親 | submodule の一時 worktree、C の commit/message、branch、bundle、主 module store への fetch |
| Codex author B | `orchestrator/campaign/s3_mocc_lock_coverage.py` |
| Codex author B | 新規 `orchestrator/tests/test_mocc_xp_pin_candidate.py` |
| Codex author B | `patches/README.md` の候補再現用差分の説明 |
| 親の実走成果物 | 新規 `output/env/pegasus/calibration/s3_mocc_xp_pin_candidate.json`、D297 report と log |
| 親の記録 | 新 insight、波及表、worklog/decisions fragment |

B へ渡す入力は最終 C・親・tree・blob・候補 source hash・候補 patch hash、bundle の位置、段 4 の確定 check 集合である。実装後は関連焦点 test、compute 1 job、D297 3 compiler と負例、変異、review の順で材料を揃える。テスト/build は親の通常経路で `tools/run_tests.py` を通し、`check_codex_agents.py`、`check_docs.py`、commit 後の provenance 監査も親工程で実施する。**本 plan ではいずれも未実走。**

## 総括

| provisional | 判定 |
|---|---|
| P1 | **条件付き支持** — 最小 3 箇所変更を採用。TRACE=1 build と C 上の再実走が必要 |
| P2 | **条件付き支持** — 既存 driver の候補 mode。旧 14 key を保持し候補固有 7 key を追加 |
| P3 | **支持** — BASE の単一子、新規 local hook branch |
| P4 | **条件付き支持** — 親の一時 worktree commit、bundle 保全、land 前 fetch。先例との差を明記 |
| P5 | **条件付き支持** — patch は再現資料。可搬 test は BASE から再構成し、C との関係は固定期待値・実測で束縛 |
| P6 | **支持** — I absent を明記し、本 wave では実装しない |

確定設計の要約:

1. C は BASE＋64 行、transaction.cc 1 path、X/P のみ。
2. 新 patch と新 test を作り、旧 patch/test/JSON は保持する。
3. 実走は C checkout、broken 4 本を直接適用する。
4. compute は 8 走・7 build・21 check を候補専用 JSON に保存する。
5. TRACE=0 は BASE/C の論理行列、D297、逆アセンブル、`.text` bytes を区別する。
6. D297 は正式 C で GCC 2 版と clang を試行し、clang 未完了を隠さない。
7. 43 file の分類に加え、template・receipt・policy epoch の依存を材料化する。
8. gitlink、承認定数、push、再承認提示、探索開始は行わない。

author に渡す所有表:

| A | B | 親 |
|---|---|---|
| 候補 patch 1 本 | 既存 driver、新 test、patches README | C/branch/bundle/fetch、実走 JSON/report、insight・fragment |

親の段 4 裁定が要る点は、**hot 正負例 2 走を加えた 21 check 案の採用、patch を branch 候補の再現資料として保持する位置付け、land 前 fetch への前倒し**の 3 点。C の実 OID と各 hash は commit 後に確定する。pytest・build・compute の成否は未確定であり、本回答に緑の主張はない。