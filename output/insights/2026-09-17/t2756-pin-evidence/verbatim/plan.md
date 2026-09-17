## 総括

- **plan として提示する。書込み・pytest・checker 実走は行っていない。**
- 親 brief の訂正・限定は **6 点**：D986 全件閉塞の断定、実際の preprocess オプション、report の合否表現、134 file の閉包の意味、F の機械的更新、P5 の追記方法。
- 分類済み **134 / 134 file、不明 0**。ただし文字列検索の閉包は依存関係全体の閉包ではない。
- 保証範囲の訂正・補足は **9 点**。最大の問題は、解決不能な CMake 間接値が現行実装では拒否されないこと。
- P1・P2 は補足付き同意、P3・P4・P5 は一部異議。
- decisions fragment は **現状不要**。未対応範囲を許容する新判断を本 wave で行うなら別途必要。
- checker が合格しても、pin 前進・mocc の certified 化・between-run 実測再開の判断にはしない。

## 1. 事実の裏取り

以下の repo 相対 path はすべて指定 worktree 配下。説明上、`checker` は `tools/check_trace0_preprocess_identity.py`、`digest` は `orchestrator/campaign/source_digest.py` を指す。

### (a) checker の契約

| 項目 | 確認結果・根拠 |
|---|---|
| 祖先性 | `checker:109` が `git merge-base --is-ancestor old new` を実行。rc=0/1 を区別し、それ以外も拒否。`checker:670` で old ⊑ new を要求する。 |
| 比較区間 | `checker:131` の `diff-tree --raw -r -z --no-renames old new`。**端点間の tree 差分**を検査し、中間 commit ごとの無害性は保証しない。 |
| 差分の受理 | `checker:180`。非空、status=M、mode 不変、regular file、拡張子 `.c/.cc/.cpp/.cxx` が必要。header、追加・削除、mode/type 変更などは拒否。 |
| `--expect-paths` | `checker:204`。順不同の集合として厳密一致。期待側・実際側の重複、空の期待集合、過不足を拒否。filter ではない。 |
| context 数 | `checker:678` で genome 数×overlay 数を計算し、0 件を拒否。`checker:636` で実際の比較件数と一致を要求。 |
| compiler | `checker:227` で `shutil.which`、realpath、`--version` 先頭行を取得。実行バイナリ bytes の同定ではない。 |
| schema | `checker:47`：`izanagi-trace0-preprocess-identity/v2`。 |
| 成功 report | `checker:708`：top-level `result="pass"`。file ごとは `checker:642` の `result="match"`。 |
| 拒否 | `checker:746`。検査例外では stderr と rc=1、**拒否 report JSON は生成しない**。CLI 引数誤りは argparse 側の拒否。 |

**mocc trace.hh 特例の正確な条件**

`checker:421` の `_mocc_trace_include_addition_index` は以下を要求する。

1. path が **exact `cc/mocc/transaction.cc`**。
2. 新側の include 数が旧側より **ちょうど 1 多い**。
3. 追加行は前後空白を除いて exact `#include "../../include/trace.hh"`。末尾コメント付きは受理条件を満たさない。
4. その行を除いた include 行列が旧側と**文字列・順序とも一致**し、挿入位置候補が一意。
5. `checker:389` の字句解析で、追加位置を囲む stack に単純な `#if TRACE` の初期枝がある。`#ifdef TRACE` や複合式だけでは根拠にならない。入れ子内でも、外側の該当初期枝があれば条件を満たし得る。
6. 全 context で追加 marker が TRACE=0 時に非活性であることを `checker:493` で確認。
7. 追加分を除き、旧 marker 列への対応後に活性・順序が一致することを `checker:458` で確認。
8. 通常の正規化 preprocess 同一性検査も通す。特例だけで成功にはしない。

候補 tree の `cc/mocc/transaction.cc:13` は `#if TRACE`、`:15` が該当 include、`:16` が `#endif`。これは **e9e477ca の `git show` 出力**で確認したもので、現 checkout の同番号とは区別する。

### (b) context と mocc の実供給 define

- `digest:351`：`CONTEXT_MACROS = ("GLOBAL_VALUE_DEFINE",)`。
- `digest:1712`：overlay は `[{}, {"GLOBAL_VALUE_DEFINE": "1"}]`。
- `orchestrator/campaign/genome.py:106`：SILO_SPACE は4軸の二値空間。ただし no-wait の2軸に XOR 制約があるため **8 genome**。4軸独立の16 genomeではない。
- `digest:90`：`cc/mocc/transaction.cc` の owner は `"mocc"`。
- `checker:558`：登録済み path に `source_rel` を渡し、old/new それぞれに `_head_defines` を呼ぶ。
- `digest:2116`：各 commit の `cmake/Options.cmake` と、owner が指す `cc/mocc/CMakeLists.txt` を読む。
- `digest:841`：universal と protocol の供給表を統合する。空集合・mapping 衝突は拒否。
- `digest:903`：既定値に genome.flags を重ね、供給集合で絞り、cache mapping・`Linux=1`・bare define を反映する。

mocc の現物は `external/ccbench/cc/mocc/CMakeLists.txt:5` が bare `RWLOCK`、`:6` が `TEMPERATURE_RESET_OPT=${CCBENCH_TEMPERATURE_RESET_OPT}`。前者は `digest:957` により `"1"`、後者は Options の既定値から引く。現物の既定値は `external/ccbench/cmake/Options.cmake:48` の `1`。

owner 解決失敗時に silo へ戻る処理はない。`digest:2025` が不正 owner・未知 source を拒否する。未登録 source に `None` を渡す経路とは別である。

**16 context は16種類の実効構成ではない。** mocc の供給集合で silo 固有軸が落ちるため複数 genome が同じ define map へ写る。T-1506 の「map 4種・digest 2種」は過去実測として引用し、今回の3 reportで再集計する。現行 `_cpp_normalize` は `-dD` を含むため、過去の digest の種類数を今回の期待値として固定しない。

### (c) D986 の3穴

| 穴 | 現行の対応 | 判定 |
|---|---|---|
| (1) CMake 間接供給・行継続 define | `digest:1332` が `set` binding、`:1218` が有限再帰展開、`:1273` が展開後 token を検査。認識した供給は `:1626`→`:1639` で拒否。C/C++ は `:982` の splice、`:1101` の物理行・論理行の両 view、`:1635` の define 検出で拒否。 | **単純形は対応済み。ただし全面的な fail-closed は未対応。** |
| (2) macro 経由 include 差替え | `checker:290`、特に `:354`・`:356`・`:360` が継続 include、非 literal operand、認識不一致を拒否。old/new 両方へ `:539` で適用。`#define H ...`＋`#include H` は受理しない。 | 指名された穴は対応済み。header 展開全体を検証する実装ではない。 |
| (3) hash 不一致と `identical:true` の併記 | `checker:253` が元 bytes の一致と独立 hash の一致を別計算し、不整合なら拒否。include の policy 受理は `:632` に別 field として保存。 | 対応済み。policy 受理と生 marker bytes 一致を混同しない。 |

**(1) の残余を隠さない。** `digest:1290` は未認識 command、実行分岐、function、CACHE/PARENT_SCOPE の実行時値、遅延展開と CMake eager expansion の差、32段制限を明記する。`digest:1381` は `SUPPLIES` のみ True にし、`UNPROVABLE_REPO_VALUE` を拒否へ変換しない。`digest:1570` も「解決不能な間接 CMake 値は…拒否にも使わない」と明記している。

したがって、射影された D986 の強い要件に対して「全件閉塞済み」とは報告できない。**本 wave では checker を修正せず、未対応範囲として提示する。** この残余の受容を新たに決めることも本 wave の成果物に混ぜない。

### (d) gitlink の限界

`digest:1503` は checkout の `os.walk` に commit tree 走査を加える。

- regular blob は対象拡張子なら読む：`:1534`。
- symlink entry は拒否：`:1544`。
- gitlink の object type が commit でなければ拒否：`:1549`。
- `.git` marker の実在・非 symlink、repository top-level の一致を確認してから HEAD を解決：`:1460`。
- checkout HEAD と gitlink OID が違う、未初期化、repository でない場合は **coverage を主張せず continue**：`:1555`。
- submodule 内部を不在証明の対象外とする限界：`:1508`。

old/new の不在証明は `checker:664` でそれぞれ実行する。一方の結果を他方へ流用しない。ただし各証明は commit tree だけでなく**検査時 checkout**にも依存する。

## 2. 材料 (2) の実走計画と保証範囲の逐語案

### 実走 argv・保存先

親が以下を**順次**実行する。作業場所は指定 worktree。`-B` は Python bytecode の不要な生成を避けるだけで、checker の意味を変えない。

```bash
python3 -B /work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2756-pin-evidence/tools/check_trace0_preprocess_identity.py --repo /work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2756-pin-evidence/external/ccbench --old 511c9538e4e8efa54b45cda62e72389ed3b706ec --new e9e477ca1b55348ab4530de0b1cf663ce4555290 --cxx /usr/bin/g++ --expect-paths cc/mocc/transaction.cc
```

```bash
python3 -B /work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2756-pin-evidence/tools/check_trace0_preprocess_identity.py --repo /work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2756-pin-evidence/external/ccbench --old 511c9538e4e8efa54b45cda62e72389ed3b706ec --new e9e477ca1b55348ab4530de0b1cf663ce4555290 --cxx /usr/bin/g++-12 --expect-paths cc/mocc/transaction.cc
```

```bash
python3 -B /work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2756-pin-evidence/tools/check_trace0_preprocess_identity.py --repo /work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2756-pin-evidence/external/ccbench --old 511c9538e4e8efa54b45cda62e72389ed3b706ec --new e9e477ca1b55348ab4530de0b1cf663ce4555290 --cxx /usr/bin/clang++ --expect-paths cc/mocc/transaction.cc
```

保存先の基点：

`output/insights/2026-09-17/t2756-pin-evidence/verbatim/`

| compiler | 成功時の stdout 保存名 | 別途保存 |
|---|---|---|
| `/usr/bin/g++` | `trace0-gcc11.report.json` | `trace0-gcc11.stderr.txt`、rc |
| `/usr/bin/g++-12` | `trace0-gcc12.report.json` | `trace0-gcc12.stderr.txt`、rc |
| `/usr/bin/clang++` | `trace0-clang14.report.json` | `trace0-clang14.stderr.txt`、rc |

実走前に出力ディレクトリを用意し、各実行の stdout/stderr/rc を個別に保存する。**拒否した実行の空 stdout を有効な report JSON と扱わない。** 拒否時は `.stdout.txt` として保存し、親作成の `runs.json` に `report_emitted: false`、rc、stderr path を記録する。checker schema v2 の拒否 report を捏造しない。

`runs.json` には argv、cwd、host、実行時刻、superproject HEAD、checker/digest の hash、requested compiler と report の解決済み compiler path/version、rc、stdout/stderr の bytes/hash を保存する。新しい gate は作らず、既存結果を構造化する。

GCC 12 は今回の read-only 照会で **12.3.0**。GCC 11.4 と Clang 14 は親実測を起点に、実走 report の version で確定する。

### 合格・拒否の記載形

**3本とも成功した場合**

> 材料 (2)：現行 checker による直接区間の検査は、記録した3 compiler のすべてで rc=0、schema `izanagi-trace0-preprocess-identity/v2`、`result=pass` だった。対象差分は `cc/mocc/transaction.cc` の1 file、各 compiler の比較件数は16 context だった。保証は下記の範囲に限る。D986 の間接 CMake 値に関する未対応範囲は残り、本結果をその全面閉塞の証拠とはしない。pin 前進の裁定は本 wave では行わない。

**いずれかが拒否した場合**

> 材料 (2)：3 compiler を対象に実行し、少なくとも1本が拒否したため、総合結果は拒否とする。compiler 別に rc・stderr・report の有無を保存した。拒否理由を観測者効果の実在と同一視せず、未対応構文・環境／起動失敗・比較不一致を実際の診断に従って区別する。pin 前進可能とは判定しない。

「比較不一致」と「検査不能」は説明上区別するが、総合合格の条件を緩めない。

### P3 の訂正・補足9点

1. **言い過ぎ**：「D986 で塞いだ3穴」→ (1) の未解決間接値は未対応と書く。
2. **言い過ぎ**：「16構成」→ 16件の列挙・比較。実効構成の重複を除いた数ではない。
3. **言い過ぎ**：「map 4種・digest 2種」→ T-1506 の過去実測。今回値は3 reportから別に出す。
4. **言い足りなさ**：compiler 依存に加え、**admission toolchain と同一とは主張しない**。
5. **言い足りなさ**：include は展開しない。header 内容・完全な翻訳単位・binary 同一性を保証しない。
6. **言い足りなさ**：現行処理は `-E -P -dD -nostdinc -Werror=undef`＋`BUILD_FLAGS`。空入力の環境 prefix を除去する。単に「git と `-E -P` だけ」では不正確。
7. **言い足りなさ**：`digest:1672` の、指令と include の相対位置、および `push_macro/pop_macro` の復元値に関する限界。
8. **言い足りなさ**：不在証明は認識対象の repo text・検査時 checkout・各 commit tree の範囲。任意の build define の不在証明ではない。D723 の gitlink 内部も対象外。
9. **言い足りなさ**：mocc 特例の追加行非活性と既存列対応、比較0件拒否、端点差分の受理条件を明記する。policy 受理を生 marker hash 一致と書かない。

### 保証範囲の訂正版逐語

> 本検査の保証名は「選定した macro context における TRACE=0 正規化 preprocess 出力の同一性、および include 活性の同一性」である。対象は旧 commit `511c9538e4e8efa54b45cda62e72389ed3b706ec` と候補 `e9e477ca1b55348ab4530de0b1cf663ce4555290` の端点間差分であり、旧 commit が新 commit の祖先であること、差分 path が `cc/mocc/transaction.cc` だけであることを検査する。
>
> context は SILO_SPACE の no-wait XOR 制約を満たす8 genome と、GLOBAL_VALUE_DEFINE の非供給／1供給の2 overlayとの積、計16件である。mocc source には各 commit の mocc CMake 供給表を用いるため、silo genome の違いが同一の実効 define map に写る場合がある。16件は16種類の異なる macro 構成を意味せず、mocc 固有空間の全列挙でもない。T-1506 の実効 define map 4種・正規化 digest 2種は過去の区間・checker による観測であり、今回の値は compiler ごとの report によって別に記録する。
>
> 正規化では include 行を除去し、compiler builtin を保持した preprocess 出力を比較する。現行実装は `-dD` により有効枝の source の define/undef を残し、同じ引数の空入力出力を環境 prefix として除去する。include 活性は別に marker 化して順序込みで検査する。唯一の追加特例は、mocc transaction source の単純な `#if TRACE` の初期枝内にある exact trace.hh include 1行であり、その marker が全選定 context の TRACE=0 で非活性で、残る include の対応・活性・順序が一致することを要求する。
>
> header 差分、非対応の差分形・include 構文、比較0件または期待件数との不一致は拒否する。本検査は header を展開した翻訳単位、指令と include の相対位置、pragma push_macro/pop_macro の復元値、任意のビルド条件、binary 同一性、trace の完全除去を証明しない。結果は記録した compiler と選定 context に依存し、admission toolchain と同一であるとは主張しない。
>
> 不在 macro registry は old/new 別々の commit tree と検査時 checkout の認識対象 text で再検証する。単純な CMake 間接供給と行継続 define は検出するが、解決不能な間接 CMake 値は現行実装では拒否理由にならず、その背後の供給は証明範囲外に残る。submodule 内部も不在証明の保証対象外である。従って D986 の3穴が全面的に閉塞済みとは主張しない。report は生 bytes/hash の同一性と mocc 特例の policy 受理を区別する。
>
> 本検査の合格は限定された観測者効果検査の結果であり、pin 前進、旧登録の張替え、mocc の正しさ・性能・certified な合成経路の成立、非 silo between-run 実測再開を決定しない。

## 3. 材料 (3) 波及表の分類案

### 分類の使い方

A〜G は主たる役割を1つ付す。**分類は編集許可を意味しない。全134 fileとも本 waveでは不変。**

- A：現行・専用 driver の定数。新 pin へ移す系列だけ更新対象。専用の旧系列は維持。
- B：事前登録・source/patch/pilot の登録契約。旧版維持、新条件には新登録・追補。
- C：identity・lock・取得証拠。旧 bytes 維持、新系列では新しい証拠と束縛。
- D：凍結物。旧物維持、新系列で再凍結の要否を裁定。
- E：歴史記録・説明・provenance。旧記録維持。ただし再実測義務等を備考に残す。
- F：テスト・fixture。**現行 pin 追随と旧 pin 回帰証拠を分ける**。一律更新しない。
- G：照合 consumer。旧契約を保持し、新系列を通すなら契約と一緒に対応させる。

表の番号は `pin-closure.tsv` の data row 順。帰結欄に当該行の役割も併記する。

### 1〜26：docs

| # | path:line | 分類 | pin 前進時の帰結／該当行の役割 |
|---:|---|:---:|---|
| 1 | `docs/backoff-counterfactual-preregistration.md:140` | B | 旧登録維持、新条件を追補／pin＋順序付き patch stack |
| 2 | `docs/backoff-policy-performance-preregistration.md:129` | B | 旧登録維持、新条件を追補／性能条件の pin |
| 3 | `docs/dynamic-backoff-preregistration.md:82` | B | 旧登録維持、新条件を追補／動的 backoff の基底 |
| 4 | `docs/paper-story-backoff/2026-09-05.md:87` | E | 保持／実験の主張範囲と版の相違 |
| 5 | `docs/paper-story-backoff/2026-09-10.md:42` | E | 保持／主要実験の版 |
| 6 | `docs/paper-story/2026-09-02.md:63` | E | 保持／当時の A-2 条件・結果 |
| 7 | `docs/paper-story/2026-09-05.md:640` | E | 保持／source・pin の実行同一性 |
| 8 | `docs/paper-story/2026-09-14.md:36` | E | 保持／機構訂正と旧条件 |
| 9 | `docs/paper-story/2026-09-17.md:356` | E | 保持／hook と現 pin の関係、結果条件 |
| 10 | `docs/paper-story/claim-evidence/2026-08-26.md:132` | E | 保持／限定付き観測の導出索引 |
| 11 | `docs/paper-story/figures/README.md:51` | E | 保持／図の条件・caption・版差 |
| 12 | `docs/paper-story/figures/fig2c_b10_extended_backoff.provenance.json:182` | E | 保持／図入力の source identity |
| 13 | `docs/paper-story/figures/fig5_a2_certification_reject.provenance.json:86` | E | 保持／旧 attempt の pin |
| 14 | `docs/paper-story/figures/fig6_a2_certification_observed_positive.provenance.json:122` | E | 保持／旧 positive の pin |
| 15 | `docs/paper-story/figures/fig7_a2_builtin_backoff_onoff_reject.provenance.json:92` | E | 保持／旧 reject の pin |
| 16 | `docs/paper-story/figures/fig8_b10_static_tail_not_observed.provenance.json:71` | E | 保持／図の build admission と caption |
| 17 | `docs/paper-story/results/2026-09-04-a2-certification-reject.md:37` | E | 保持／正式走行の条件 |
| 18 | `docs/paper-story/results/2026-09-07-a2-certification-observed-positive.md:88` | E | 保持／positive の適用範囲 |
| 19 | `docs/paper-story/results/2026-09-07-a2-certification-reject.md:51` | E | 保持／admission・機構訂正の根拠 |
| 20 | `docs/paper-story/results/2026-09-09-a2-certification-observed-positive-en.md:96` | E | 保持／結果の英語記述 |
| 21 | `docs/paper-story/results/2026-09-14-b7-all-workload-regression.md:86` | E | 保持／B7 の実行条件 |
| 22 | `docs/paper-story/results/2026-09-16-b10-static-tail-not-observed.md:115` | E | 保持／短縮 pin と gitlink の束縛 |
| 23 | `docs/paper-story/results/2026-09-16-b7-three-run-materials.md:103` | E | 保持／短縮 pin から full OID を推定しない根拠 |
| 24 | `docs/phase3-8b-restart-runbook.md:154` | G | 新系列の期待値は別確認／人間が行う gitlink preflight |
| 25 | `docs/related-work/claim-survey/2026-09-07-backoff-axis-b5-search-preregistration.md:13` | B | 旧検索範囲維持／調査対象版の固定。pin 前進だけで再検索しない |
| 26 | `docs/t1998-balanced-stock-inline-preregistration.md:83` | B | 旧登録維持、新条件を登録／gitlink・patch適用・evidence 基底 |

### 27〜46：campaign コード・登録

| # | path:line | 分類 | pin 前進時の帰結／該当行の役割 |
|---:|---|:---:|---|
| 27 | `orchestrator/campaign/axis_trigger_gating.py:59` | A | 正本定数に追随／実値は `pin.CURRENT_PIN`、literal はコメント |
| 28 | `orchestrator/campaign/backoff_counterfactual_analysis.py:26` | G | 旧解析維持、新系列は対応追加／`:121` で build binding を照合 |
| 29 | `orchestrator/campaign/backoff_counterfactual_cohort2_analysis.py:26` | G | 旧解析維持／`:124` の pin＋stack 照合 |
| 30 | `orchestrator/campaign/backoff_policy_performance_analysis.py:30` | G | 旧解析維持／`:292` が短縮・full pin を照合 |
| 31 | `orchestrator/campaign/backoff_sweep.py:55` | A | 正本定数に追随／CURRENT_PIN alias |
| 32 | `orchestrator/campaign/buildcache.py:1059` | E | **新 pin で生成物形を再実測**／CMakeCache・DependInfo の観測条件。`:1062` が再実測を要求 |
| 33 | `orchestrator/campaign/p3_s4_loop.py:112` | A | 新系列移行時に明示更新／D1936 による独立 full OID。CURRENT_PIN 変更だけでは動かない |
| 34 | `orchestrator/campaign/p3_s4_loop_sort.py:103` | A | 正本定数に追随／CURRENT_PIN alias。`:28` は説明 |
| 35 | `orchestrator/campaign/p3_s4_loop_trigger_gating.py:35` | A | axis 定数に追随／literal は説明、実値は `:72` の import |
| 36 | `orchestrator/campaign/paper_story_a1_paired.py:205` | G | 旧 v3 契約維持／`:2400` 等の canonical OID 照合 |
| 37 | `orchestrator/campaign/paper_story_a1_paired.v3-pilot.json:17` | B | 新系列は新登録／pilot の canonical_pin |
| 38 | `orchestrator/campaign/paper_story_a1_paired.v3-sized.json:17` | B | 新系列は新登録／sized の canonical_pin |
| 39 | `orchestrator/campaign/paper_story_a1_source.v1.json:5` | B | 旧版保持／source 契約 canonical_head |
| 40 | `orchestrator/campaign/paper_story_a1_source.v2.json:4` | B | 新系列は新契約／source canonical_head |
| 41 | `orchestrator/campaign/pin.py:28` | A | 再承認後の定数更新対象／現行短縮 pin の正本 |
| 42 | `orchestrator/campaign/s5_permutation_coverage.py:50` | A | 正本定数に追随／CURRENT_PIN alias |
| 43 | `orchestrator/campaign/s6_sort_sweep.py:87` | A | 正本定数に追随／CURRENT_PIN alias |
| 44 | `orchestrator/campaign/s8b_approved.py:67` | A | 再承認なしに変更不可／承認済み full SHA |
| 45 | `orchestrator/campaign/silo_ladder_rung1.py:61` | A | 専用旧系列は維持／通常 campaign 外の ability-probe 固定 pin |
| 46 | `orchestrator/campaign/silo_ladder_rung1_contract.py:543` | G | 旧契約維持、新系列は ledger と同時対応／expected_scalars の base_commit exact 照合 |

### 47〜78：テスト・fixture

F の「追随」は、新系列を検証する期待値に限る。旧 producer の trace・lock・拒否 control を新 pin と偽装しない。

| # | path:line | 分類 | pin 前進時の帰結／該当行の役割 |
|---:|---|:---:|---|
| 47 | `orchestrator/tests/acceptance_duration_ledger.json:10208` | E | 保持／pin を含む test nodeid の時間記録 |
| 48 | `orchestrator/tests/fixtures/README.md:108` | F | **旧値保持**／実 trace fixture の producer clone HEAD。`:200` も同様 |
| 49 | `orchestrator/tests/fixtures/b10_backoff_shape_locks/balanced.campaign.lock:1` | F | 旧 fixture 保持／取得済み campaign identity・admission |
| 50 | `orchestrator/tests/fixtures/b10_backoff_shape_locks/read-heavy.campaign.lock:1` | F | 旧 fixture 保持／取得済み campaign lock |
| 51 | `orchestrator/tests/fixtures/b10_backoff_shape_locks/write-heavy.campaign.lock:1` | F | 旧 fixture 保持／取得済み campaign lock |
| 52 | `orchestrator/tests/test_b10_extended_figure_provenance.py:200` | F | 旧図 fixture 保持、新図には追加／短縮・full OID の対応 |
| 53 | `orchestrator/tests/test_backoff_counterfactual_analysis.py:27` | F | 旧解析 fixture 保持／登録済み解析 pin |
| 54 | `orchestrator/tests/test_backoff_policy_performance_analysis.py:36` | F | 旧解析 fixture 保持／prefix 異常系も含む |
| 55 | `orchestrator/tests/test_backoff_profile_pegasus.py:47` | F | 旧 profile fixture 保持／入力 source identity |
| 56 | `orchestrator/tests/test_backoff_requested_us.py:589` | F | 使用契約に応じ追加／requested-us の evidence 入力 |
| 57 | `orchestrator/tests/test_dynamic_backoff_transitions.py:17` | F | 旧基底保持／動的 backoff の固定 source |
| 58 | `orchestrator/tests/test_mocc_proof_surface.py:29` | F | **旧 pin の拒否 control を保持**／`:397` は候補適用・旧 pin 拒否の対 |
| 59 | `orchestrator/tests/test_mocc_trace_job_contract.py:32` | F | 旧端点保持／mocc policy の BASE_OID |
| 60 | `orchestrator/tests/test_mocc_trace_pair.py:20` | F | 旧端点保持／pair 証拠の BASE_OID |
| 61 | `orchestrator/tests/test_p3_build_authority_cli.py:192` | F | 新現行契約へ移す際に追随／独立 EXPECTED_REPO_STOCK_PIN |
| 62 | `orchestrator/tests/test_p3_s4_loop_job_contract.py:1184` | F | driver 更新と整合／fake git HEAD と job 入力 |
| 63 | `orchestrator/tests/test_p3_s4_loop_sort.py:781` | F | 現行系列移行時に追随／cfg・S.PIN・literal の一致 |
| 64 | `orchestrator/tests/test_p3_s4_loop_trigger_gating.py:2170` | F | 現行系列移行時に追随／cfg・T.PIN・literal の一致 |
| 65 | `orchestrator/tests/test_paper_story_a1_job_contract.py:463` | F | 旧 v3 control 保持、新版に追加／canonical checkout |
| 66 | `orchestrator/tests/test_paper_story_a1_paired.py:1632` | F | 旧 policy fixture 保持／canonical_pin |
| 67 | `orchestrator/tests/test_paper_story_a2_certification.py:1023` | F | 旧 cohort control 保持、新系列を追加／current_pin と正規化 control |
| 68 | `orchestrator/tests/test_plot_a2_certification.py:123` | F | 旧図 fixture 保持／manifest・caption の旧 pin |
| 69 | `orchestrator/tests/test_plot_b10_static_tail_formal.py:68` | F | 旧図 fixture 保持／repo_stock_pin |
| 70 | `orchestrator/tests/test_plot_dynamic_backoff.py:38` | F | 旧図 fixture 保持／short/full pin |
| 71 | `orchestrator/tests/test_plot_t2187_adaptive_consts.py:120` | F | 旧 probe fixture 保持／source identity |
| 72 | `orchestrator/tests/test_s6_sort_sweep.py:390` | F | 現行系列移行時に追随／policy から逆算しない独立期待値 |
| 73 | `orchestrator/tests/test_s8a_trigger_sweep.py:108` | F | characterization と現行期待値を分離／`:485` は独立 pin |
| 74 | `orchestrator/tests/test_s8b_floor_campaign.py:2276` | F | 新系列例を追加、旧凍結例保持／`:12148` は旧 floor path |
| 75 | `orchestrator/tests/test_s8b_protocol_builder.py:55` | F | 旧 byte control 保持、新世代を追加／凍結 protocol の exact bytes |
| 76 | `orchestrator/tests/test_t126_qualification_driver.py:785` | F | fixture 契約に応じ追加／clean stock source evidence |
| 77 | `orchestrator/tests/test_t1998_stock_inline_pair.py:54` | F | 旧登録例保持、新登録に追加／short/full gitlink |
| 78 | `orchestrator/tests/test_t2187_adaptive_const_probe.py:47` | F | 旧 probe control 保持／PIN_FULL |

### 79〜119：環境証拠・凍結

| # | path:line | 分類 | pin 前進時の帰結／該当行の役割 |
|---:|---|:---:|---|
| 79 | `output/env/pegasus/b10-backoff-shape/24d80d9a35122de1/reports/final/b10_backoff_shape_provenance.json:5` | E | 保持／完了済み B10 report の pin |
| 80 | `output/env/pegasus/calibration/a2_perf_verify_cost_t48_skew0p9_rr50_rmw0.json:6` | C | 旧証拠保持／較正の short/full source identity |
| 81 | `output/env/pegasus/calibration/a2_perf_verify_cost_t48_skew0p9_rr5_rmw0.json:4` | C | 旧証拠保持／較正の short/full source identity |
| 82 | `output/env/pegasus/calibration/attempts/0_478.nqsv/calibration.json:44` | C | 旧証拠保持／acquisition の head_sha |
| 83 | `output/env/pegasus/calibration/attempts/0_989271.nqsv/calibration.json:43` | C | 旧証拠保持／acquisition の head_sha |
| 84 | `output/env/pegasus/calibration/attempts/0_995805.nqsv/calibration.json:44` | C | 旧証拠保持／acquisition の head_sha |
| 85 | `output/env/pegasus/calibration/attempts/0_995806.nqsv/calibration.json:44` | C | 旧証拠保持／acquisition の head_sha |
| 86 | `output/env/pegasus/calibration/attempts/0_998860.nqsv/calibration.json:45` | C | 旧証拠保持／acquisition の head_sha |
| 87 | `output/env/pegasus/calibration/attempts/0_998863.nqsv/calibration.json:45` | C | 旧証拠保持／acquisition の head_sha |
| 88 | `output/env/pegasus/calibration/attempts/0_998864.nqsv/calibration.json:43` | C | 旧証拠保持／acquisition の head_sha |
| 89 | `output/env/pegasus/calibration/job-staging/0:478.nqsv/acquisition-candidate.json:43` | C | 保持／取得候補の source binding |
| 90 | `output/env/pegasus/calibration/job-staging/0:478.nqsv/acquisition-receipt.json:43` | C | 保持／取得 receipt の source binding |
| 91 | `output/env/pegasus/calibration/job-staging/0:478.nqsv/worktree-add.stdout:1` | E | 保持／旧 checkout 作成ログ |
| 92 | `output/env/pegasus/calibration/job-staging/0:989271.nqsv/acquisition-candidate.json:42` | C | 保持／取得候補の source binding |
| 93 | `output/env/pegasus/calibration/job-staging/0:989271.nqsv/acquisition-receipt.json:42` | C | 保持／取得 receipt の source binding |
| 94 | `output/env/pegasus/calibration/job-staging/0:989271.nqsv/worktree-add.stdout:1` | E | 保持／旧 checkout 作成ログ |
| 95 | `output/env/pegasus/calibration/job-staging/0:995805.nqsv/acquisition-candidate.json:43` | C | 保持／取得候補の source binding |
| 96 | `output/env/pegasus/calibration/job-staging/0:995805.nqsv/acquisition-receipt.json:43` | C | 保持／取得 receipt の source binding |
| 97 | `output/env/pegasus/calibration/job-staging/0:995805.nqsv/worktree-add.stdout:1` | E | 保持／旧 checkout 作成ログ |
| 98 | `output/env/pegasus/calibration/job-staging/0:995806.nqsv/acquisition-candidate.json:43` | C | 保持／取得候補の source binding |
| 99 | `output/env/pegasus/calibration/job-staging/0:995806.nqsv/acquisition-receipt.json:43` | C | 保持／取得 receipt の source binding |
| 100 | `output/env/pegasus/calibration/job-staging/0:995806.nqsv/worktree-add.stdout:1` | E | 保持／旧 checkout 作成ログ |
| 101 | `output/env/pegasus/calibration/job-staging/0:998860.nqsv/acquisition-candidate.json:44` | C | 保持／取得候補の source binding |
| 102 | `output/env/pegasus/calibration/job-staging/0:998860.nqsv/acquisition-receipt.json:44` | C | 保持／取得 receipt の source binding |
| 103 | `output/env/pegasus/calibration/job-staging/0:998860.nqsv/worktree-add.stdout:1` | E | 保持／旧 checkout 作成ログ |
| 104 | `output/env/pegasus/calibration/job-staging/0:998863.nqsv/acquisition-candidate.json:44` | C | 保持／取得候補の source binding |
| 105 | `output/env/pegasus/calibration/job-staging/0:998863.nqsv/acquisition-receipt.json:44` | C | 保持／取得 receipt の source binding |
| 106 | `output/env/pegasus/calibration/job-staging/0:998863.nqsv/worktree-add.stdout:1` | E | 保持／旧 checkout 作成ログ |
| 107 | `output/env/pegasus/calibration/job-staging/0:998864.nqsv/acquisition-candidate.json:42` | C | 保持／取得候補の source binding |
| 108 | `output/env/pegasus/calibration/job-staging/0:998864.nqsv/acquisition-receipt.json:42` | C | 保持／取得 receipt の source binding |
| 109 | `output/env/pegasus/calibration/job-staging/0:998864.nqsv/worktree-add.stdout:1` | E | 保持／旧 checkout 作成ログ |
| 110 | `output/env/pegasus/calibration/registered/calibration-2b7ba072b88023ae.json:44` | C | hash 束縛を保持／登録済み較正内の acquisition head |
| 111 | `output/env/pegasus/calibration/registered/calibration-449d0ad22f13e366.json:43` | C | hash 束縛を保持／同上 |
| 112 | `output/env/pegasus/calibration/registered/calibration-5c836a22eff9ab40.json:44` | C | hash 束縛を保持／同上 |
| 113 | `output/env/pegasus/calibration/registered/calibration-9b49335d02ad4d2e.json:45` | C | hash 束縛を保持／同上 |
| 114 | `output/env/pegasus/calibration/registered/calibration-b3329d93417c76ad.json:43` | C | hash 束縛を保持／同上 |
| 115 | `output/env/pegasus/calibration/registered/calibration-cb98513996e5ae35.json:45` | C | hash 束縛を保持／同上 |
| 116 | `output/env/pegasus/profile/backoff_profile_t48_skew0p9_rr50.json:16` | C | 旧証拠保持／profile の取得 source |
| 117 | `output/env/pegasus/profile/backoff_profile_t48_skew0p9_rr50.md:13` | E | 保持／profile の説明記録 |
| 118 | `output/env/pegasus/t316-sandbox-backend/0:999027.nqsv/receipt.json:5568` | C | 保持／expected/observed HEAD の実行 receipt |
| 119 | `output/s8b-freeze/floor-protocols/e576e9cd1369bba3ae8faca084d1b7256bf919a7dd2e5d6facb093cd9e242c01--511c9538e4e8efa54b45cda62e72389ed3b706ec.json:1` | D | 旧凍結保持、新系列の要否を裁定／内容と filename の pin |

**registered は「事前登録」という語だけで B にしない。** 実測 acquisition receipt を含む較正証拠であり、`orchestrator/campaign/env_contract.py:454` が filename を calibration hash prefix に束縛し、`:466` が path/hash を渡して検証する。source pin の文字列だけ張り替える操作はできない。一方、pin が変わっただけで既存較正がすべて無効になるとも、この表からは結論できない。

### 120〜134：patch・policy・provenance・consumer

| # | path:line | 分類 | pin 前進時の帰結／該当行の役割 |
|---:|---|:---:|---|
| 120 | `patches/README.md:289` | B | 旧 preimage 契約保持、新基底の適用性確認／`:318` の stack、`:539` の旧 pin 拒否も含む |
| 121 | `patches/ledger.json:10` | B | 専用登録保持／rung1 patch の base_commit。`:12`〜`:18` は ability-probe 専用・pipeline 不適格 |
| 122 | `tools/known_violations/09ce607b779272fda5629a350676471a16bea9bb--missing-ai-agent--12f11b35eeeb53694d73497912e4738bd6fba2f9be51bd88a32d807dca863150.json:6` | E | 保持／過去の人間作成 gitlink commit の説明 |
| 123 | `tools/known_violations/13101ab3ec09a54e1f30462d1c2b4621b121ba65--missing-ai-agent--9dd642477798a8a78ce2ea913a27d56832ca1911ecb08b7276f593e04af26dea.json:6` | E | 保持／過去 revert の説明 |
| 124 | `tools/known_violations/8ceebcdbe40fac27cb2a1fbd7a1b1e016894bd0e--missing-codex-author--fed5101b3814fd999b21cd5f47adf339f4e6684eb36352279f30e0c7612f6ee5.json:6` | E | 保持／過去 pointer 是正の説明 |
| 125 | `tools/known_violations/d87fd42c0335c1396c1f79557e45357e9bfc163f--missing-ai-agent--82baac7ef1376e9f13c240a9381c8eb3726ecd683ce0c1e8a37c566bcf2fdbfe.json:6` | E | 保持／過去 merge の説明 |
| 126 | `tools/pegasus/mocc_trace_v1_policy.json:20` | B | **base_oid を機械追随させない**／旧→候補の比較契約。`:21` は既に e9e477ca |
| 127 | `tools/pegasus/paper_story_a1_paired.sh:366` | G | 新 policy と consumer を同時対応／canonical_pin literal と HEAD を二段照合 |
| 128 | `tools/pegasus/probes/t2187_adaptive_const_probe.py:72` | A | 旧 probe 維持、新版のみ対応／PIN_FULL |
| 129 | `tools/pegasus/probes/t2228_driver_gate_liveness_probe.pbs:224` | G | 旧 liveness 対照維持／現行・repro の OID 解決と prefix 検査 |
| 130 | `tools/pegasus/probes/t2228_driver_gate_liveness_probe.py:47` | A | 旧 characterization 維持／CURRENT_CCBENCH_PIN |
| 131 | `tools/plotting/plot_b10_extended_backoff.py:43` | G | 旧図の再現経路維持、新系列は追加／`:432` の source binding 照合 |
| 132 | `tools/plotting/plot_b10_static_tail_formal.py:206` | G | 旧図の再現経路維持／repo_stock_pin 拒否と`:281` caption |
| 133 | `tools/plotting/plot_dynamic_backoff.py:67` | G | 旧図の再現経路維持／`:297`・`:299` の short/full 照合 |
| 134 | `tools/t2216_backoff_walk_model.py:36` | G | 旧モデル入力契約維持／`:401` の source pin 照合 |

### §5 骨格13行との対応

| 骨格 | 閉包への対応・閉包外 |
|---|---|
| 1 gitlink／現行定数 | #41。gitlink 自体は通常 file の文字列検索外。alias は #27、31、34、35、42、43。独立定数 #33 等を追加。 |
| 2 承認済み定数 | #44 |
| 3 A-1 事前登録 | #37、38 |
| 4 A-1 source 契約 | #40。旧 v1 の #39 を追加。 |
| 5 A-1 実行 consumer | #36。shell preflight #127 を追加。 |
| 6 A-2 | `orchestrator/campaign/paper_story_a2_certification.py:1352` 等は literal 閉包外。関連 fixture #67、68、歴史記録を収録。 |
| 7 campaign identity | `orchestrator/campaign/ident.py` は literal 閉包外。機構として別行で維持。 |
| 8 campaign.lock | #49〜51 は**テスト用の実在 lock**。一般の生成済み campaign lock 全体の列挙ではない。 |
| 9 source evidence | `digest:192`・`:249` は literal 閉包外。取得証拠 #80〜118 を追加。 |
| 10 凍結 floor | #119 |
| 11 凍結 evidence manifest | 元 insight の raw-manifest は **insights 除外により閉包外**。骨格行を削除しない。 |
| 12 性能事前登録 | #1〜3 |
| 13 balanced 別事前登録 | #26 |

**骨格にない層**は、生成物互換性の再実測義務、D1936 独立 full pin、ability-probe patch 契約、mocc 比較端点 policy、content-addressed calibration、テストの旧 pin control、解析・plot consumer、provenance 既知違反、検索事前登録。

親の読取優先順位は次のとおり。

1. **最優先**：`digest:1290`・`:1381`・`:1570` の D986 残余。
2. **次点**：#32、33、45、46、121、126、127、110〜115。単純な定数置換が誤りになる箇所。
3. **その次**：#48〜60、74、75。旧証拠・拒否 control を失う変更を防ぐ。
4. E の歴史資料は保持方針を確認すればよく、全本文の再査読を必須にしない。

## 4. 成果物の骨格

### insight README

配置：

`output/insights/2026-09-17/t2756-pin-evidence/README.md`

`output/README.md:83` の日付/topic 配置に従い、`:90` に従って冒頭に次を置く。

```text
authority: none
default_effect: no-state-change
```

節順は以下とする。

1. **提示目的と現在の結論**
   [T-167] の再裁定材料。材料整備と pin 前進を分離。checker の観測結果を短く記す。
2. **この wave が判定しないこと**
   pin 前進、between-run 再開、mocc certified 化、変異探索解禁、正しさ・性能、TicToc 採用、上流還元。**材料1の前**に置く。
3. **材料1：候補 commit と来歴**
   full OID、branch、4 commit、author/body/trailer、祖先関係、端点差分、過去区間との違い。
4. **材料2：直接区間 checker の結果**
   compiler 別の rc・schema・件数・report link。続けて保証範囲逐語、D986 残余。
5. **材料3：pin 束縛と波及**
   閉包の取得条件、134行、分類、骨格13行の対応、literal 閉包外の依存。
6. **裁定に残す論点**
   本資料を pin 前進可能判定にしない。新系列の登録・consumer・再実測・凍結の扱いを列挙。
7. **再現情報と証拠索引**
   MANIFEST、親実走、子の静的所見、実施していない検査を区別。

### verbatim 一覧

すべて上記 topic の `verbatim/` 配下。

- `trace0-gcc11.report.json`
- `trace0-gcc12.report.json`
- `trace0-clang14.report.json`
- compiler ごとの `*.stderr.txt`。拒否時は report の代わりに `*.stdout.txt`。
- `runs.json`：親作成の実行索引。checker 生 report と区別。
- `pin-closure.tsv`：親が採取した元の134行を保持。
- `pin-impact.tsv`：134行の分類・帰結・根拠。生閉包とは別 file。
- `candidate-commits.txt`：4 commit の fuller log/body/trailer。
- `candidate-diff.txt`：祖先性・raw diff・diffstat の親実測。
- `plan.md`：本回答の逐語。
- `consult-a.md`、`consult-b.md`、`review-a.md`、`review-b.md`：各子の逐語。実際に存在するものだけ載せる。
- `MANIFEST.sha256`：証拠 file の保存 bytes を hash 化。自己 hash は含めない。

子の逐語は事実の保証元ではなく、所見の来歴として保存する。

### [T-167] への追記逐語

対象は `docs/phase3.md:2632` の**先頭物理行末尾**。

> 【2026-09-17 追記: [T-2756] の候補 commit・直接区間の検査結果と保証限界・pin 束縛134 fileの波及表を `output/insights/2026-09-17/t2756-pin-evidence/README.md` に記録。pin 更新の裁定待ち】

承認語も旧 pin literal も含めない。「材料3点がすべて合格」とは書かない。

**追記手段は spool の `### 見送り追記` を推奨する。** `docs/spool/worklog/README.md:71`〜`:80` がこの操作を既に提供している。P5 の文面上の目的を満たし、台帳本体を wave で直接編集する必要がない。親が直接編集を明示的に選ぶ場合でも、spool との二重追記はしない。

### worklog fragment

file 案：

`docs/spool/worklog/2026-09-17-dev-wave-t2756-pin-evidence-1.md`

title 案：

> [T-2756] ccbench pin 更新項の裁定材料3点を整備 (docs-only、branch worktree-dev-wave-t2756-pin-evidence)

本文 H2 は `docs/spool/worklog/README.md:5` に従って `## 本文` と `## 次の一手差分` の2つ。

記録項目：

- 親が採った／棄却した consult・review finding と理由。
- D986 残余の発見と、checker 改変・新たな許容判断をしなかったこと。
- 実走した compiler と結果の所在。子は静的検査のみであること。
- pin・gitlink・事前登録・凍結物・実装差分が不動であること。
- checker 結果、docs 検査、受入について実際の実行結果のみ。
- [T-2756] の完了は材料が揃った時点。pin 更新の未決を [T-2756] 自身の未完了と混同しない。

`### 完了` には実際の完了後に [T-2756]、`remaining: none`、main の現物から取得した `base:` を記す。`### 見送り追記` には上記 [T-167] の1物理行を置く。形式根拠は同 README `:64`・`:75`・`:81`。

**decisions fragment：不要。** 候補の事実確定、既存保証の正確な記述、波及の分類は既裁定の具体化である。ただし「D986 の未解決形を今後も受理してよい」「較正を新 pin に流用してよい」と新たに判断するなら、その判断は今回の資料整備を超える。黙って decisions 不要扱いにしない。

## 5. P1〜P5 への異議

### P1：補足付き同意

e9e477ca 単独を**提示候補として**固定してよい。`tools/pegasus/mocc_trace_v1_policy.json:21` も同 OID を指す。

今回 `git show -s --format=fuller` と4 commit の fuller logを確認した。

- author/committer：`thawk105 <thawk105@gmail.com>`。
- e9e477ca の日時：2026-08-28 17:45:02 +0900。
- 本文：witness 専用標準 library include を除き、既存 trace include 面の宣言を使って TRACE=0 include 対応を保つ修正。
- trailer：
  - `product=codex; model=gpt-5.6-sol; reasoning=xhigh; role=author`
  - `product=codex; model=unknown; reasoning=unknown; role=manager`

**author 名から「人間が全コードを書いた」と推定しない。** trailer の unknown も補完しない。T-1943 archive は submodule の post-history provenance 監査不能を記録しているので、今回 log を読んだことを履歴監査合格に格上げしない。

追加すべき根拠は、可変 branch 名だけでなく full OIDへの固定、commit body/trailer、4 commitの対象 path、端点差分、現行 checker の直接区間結果である。今回の merge-base も旧 full OID、端点 diffstat も1 file・141追加だった。

### P2：補足付き同意

- `--expect-paths` は付ける。`checker:204` が「mocc単独候補」という今回の命題を厳密に固定する。
- GCC 11、GCC 12、Clang 14 の3本は、2 compiler family と GCC 世代差を含む利用可能な選択として妥当。admission toolchain の代替という説明はしない。
- `--cxx` は絶対 path。`checker:227` が realpath/version を記録するため、requested pathと解決後を両方残す。
- login nodeでの軽い preprocess 検査という整理に同意。ただし処理説明は `-dD`・`-dM`・checkout/commit supply走査を含める。性能測定ではない。
- 3本成功を材料(2)の checker 合格条件にする。拒否時の生 JSON が存在する前提は訂正する。

### P3：異議

主な根拠は `digest:1290`・`:1381`・`:1570`・`:1672`、`checker:253`・`:632`。D986全面閉塞、過去の map/digest 数の現在への流用、特例の policy受理と生hash一致の混同を避ける。§2の逐語に差し替える。

### P4：分類軸には同意、更新帰結には異議

A〜Gで134 fileの主分類は可能。ただし次を追加する。

- **生成物再実測義務**：`buildcache.py:1062`。
- **旧 pin 固定の専用契約**：`silo_ladder_rung1_contract.py:543`、`patches/ledger.json:10`。
- **比較旧端点**：`mocc_trace_v1_policy.json:20`。
- **旧 producer の fixture**：`orchestrator/tests/fixtures/README.md:108`。
- **hash束縛較正**：`env_contract.py:454`。

「新系列だけが A〜C・F の更新を要する」では D・G と再実測を落とす。また、Fは機械的更新ではない。

規律7の適用は正しい。ただし「過去判定は保持」と「現行 checkout で旧consumerが再解析を受理する」は別。旧環境・旧契約による再現が必要になり得る。`pin.py:11`〜`:17` が歴史driverの pin保持と不一致拒否を説明する。

### P5：目的に同意、方法と文言に異議

- `docs/phase3.md:2632` の既存内容を保存する。
- `docs/spool/worklog/README.md:75`〜`:78` の既存機構で先頭行末尾へ追記する。
- 「再承認は未提示」は、今回の提示目的と時点依存が紛らわしい。「pin 更新の裁定待ち」とする。
- 追記に候補採用・前進可能・承認済みという判断を含めない。

## 6. リスク

### check_docs の pin・byte・台帳構造

- `docs/phase3.md` は living docs：`tools/check_docs.py:142`。
- **現行 pin literal の部分文字列がある行は拒否**：`:6782`。full OIDを書いても短縮 pinを内包するため該当する。提案追記は旧 pinを書かず、insightへ参照する。
- docs の行番号参照も living docsで拒否：`:171`・`:6765`。本planの file:line根拠を phase追記へ丸ごと移さない。
- [T-167] の重複や見送り台帳構造は `:2922` 以降の対象。独立した `- [T-167]` を phase本体へ増設しない。
- 確認した byte予算は command、skill、provenance、worklog等。`phase3.md` 全体や新 insight report に一律の同じ予算を適用する根拠は見つからない。`tools/check_docs.py:283`、`:5977`、`:6014`。
- exact skill digest／節契約を避けるため、今回 command・skill・dev-wave規範は編集しない。

### 三軸語と placeholder

`s8b_holdout_freeze search` は **file全体で3軸が揃う**と hitする。根拠は `orchestrator/campaign/s8b_holdout_freeze.py:68`・`:120`・`:575`。

対象の形は `ycsb_rratio`、`ycsb_zipf_skew`、`ycsb_rmw` の値付き表記であり、本文の別々の行でも合流する。閉包TSVの path 一覧だけと、較正JSONの本文転載は違う。**本資料に不要な workload JSON をコピーしない。** checker reportのdefinesには通常この workload三軸は入らないが、保存後の実物で親が既存searchを行う。結果を通すための生証拠の書換えや除外追加はしない。

placeholderは `tools/check_docs.py:206` の3つの exact文字列が対象で、引用でも検出される。完成資料に埋め戻し指示を残さない。なお現行列挙は `:2652`・`:2690` で insights直下と日付直下のMarkdownを扱い、**今回の topic/verbatim まで一般再帰しているとは読めない**。check_docs合格だけで深い位置の逐語にplaceholderがないとは主張しない。親が新規成果物を目視・静的検索する。

### 並行 wave

確実な共通面は、完了時の canonical worklog／phase／archive と、任意に編集した場合の `output/insights/README.md`。

- t2757：mocc変異実証設計。`docs/phase3.md`、既存cross-protocol insight、source/proof面の参照が重なる可能性。
- t2760：TicToc floor baseline。`between_run_floor.py`、関連test、phase/worklogが想定面。本waveは実装を編集しない。
- 新 insight は topic固有、spoolはwave固有filenameにする。共有の既存 insight、checker、digest、pin定数を今回の訂正名目で編集しない。
- 他waveの実際のdirty差分は本planでは調査していない。推定を「競合確認済み」と記録しない。

### 生 report の size・NFC

`checker:753` は `ensure_ascii=False` の compact JSON＋末尾LFを出すが、NFC正規化や上限byte検査は行わない。

- 保存後に実byte数・UTF-8 decode・NFC状態を確認し、MANIFESTへhashを記録する。
- 実走していないため、reportの具体的sizeを見積り値で断定しない。
- `tools/ruleops.py:32`・`:229`・`:238` のsize/NFC制約はそのschema入力用であり、任意のinsight JSONすべてに同じ上限があるとは扱わない。
- 非NFCがあっても **verbatimを正規化して置換しない**。原bytesを保持し、必要なら別の表示用派生物を明記する。
- report全量をREADMEやworklogへ重複貼付せず、結果要約とfile参照にする。

親の完了確認では、3 compilerの実走証拠、134行の過不足・重複、gitlink等の不動、check_docs・check_codex_agents・所定受入、spool dry-runを実際に確認する。本planはそのいずれも実走合格と報告していない。
