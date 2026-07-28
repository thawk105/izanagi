推奨構成は `silo-degraded-rung1-lock-manager.patch`、裸マクロ `IZANAGI_DEGRADE_SILO_LOCK_MANAGER`、専用 driver `silo_ladder_characterization.py` である。以下は静的読解だけに基づく実装プランであり、性能差・build・verifier の実測結果は主張しない。

## 1. rung 1 の劣化設計候補

### 候補 A — CAS 前段の中央 lock manager（推奨）

- 変更箇所:
  - [transaction.cc:1](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t139-ladder/external/ccbench/cc/silo/transaction.cc:1) の include 群に、ON 枝だけの `<mutex>`。
  - `transaction.cc:11-15` 直後に anonymous namespace の共有 `std::mutex` とラッパー関数。
  - [transaction.cc:172](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t139-ladder/external/ccbench/cc/silo/transaction.cc:172) の `compareExchange()` 呼出しだけを ON 枝でラッパー経由にする。
- マクロ: `IZANAGI_DEGRADE_SILO_LOCK_MANAGER`
- ON 枝の形:
  - ラッパーが `std::lock_guard<std::mutex>` を獲得。
  - 同じ `tidword_.obj_`、`expected.obj_`、`desired.obj_` で元の `compareExchange()` を一度だけ呼ぶ。
  - manager mutex は CAS 直後に解放し、record lock の保持期間には重ねない。
- inert 保証:
  - `CCBENCH_` 接頭辞のない裸マクロ。`Genome.cmake_defines()` は `CCBENCH_` 付きしか生成しない（[model.py:57](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t139-ladder/orchestrator/campaign/model.py:57)）。
  - `cmake/Options.cmake` と protocol CMakeLists は変更しない。
  - OFF 枝には元の CAS 文を逐語で残し、driver が実 TU compile command による preprocess 結果を pinned stock と比較する。
- serializable 不変:
  - 元の CAS は acquire-release のまま（[atomic_wrapper.hh:63](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t139-ladder/external/ccbench/include/atomic_wrapper.hh:63)）。
  - CAS 待ち中に `expected` が古くなっても、元と同じ CAS failure 更新・retry が働く。
  - write-set sort `transaction.cc:408`、read/node validation `transaction.cc:449-485`、commit TID `transaction.cc:563-582`、write/install/unlock `transaction.cc:630-682` は無変更。
  - record lock を manager mutex の外まで持ち越さないため、新しい lock-order cycle を作らない。
- 遅さの期待機序:
  - 異なる record への CAS も一つの共有 mutex を通り、write-lock 獲得判定が全 worker 間で直列化される。
  - manager mutex の cache line handoff と lock/unlock 経路が直接 CAS に上乗せされる。
  - 差の大きさは本 wave では主張しない。
- 重ね先:
  - `izanagi-trace` の現行 pin `d706650`（[pin.py:26](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t139-ladder/orchestrator/campaign/pin.py:26)）へ直接適用する設計。
  - `broken-silo-lockskip-validation.patch` は同じ CAS 近傍を触るため、相互 stacking は保証対象外。

### 候補 B — writePhase の全プロセス直列化

- 変更箇所: [transaction.cc:693](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t139-ladder/external/ccbench/cc/silo/transaction.cc:693) の `commit()` で、`validationPhase()` 成功後から `writePhase()` 終了まで共有 mutex を保持。
- マクロ: `IZANAGI_DEGRADE_SILO_SERIAL_WRITE_PHASE`
- inert 保証: 裸マクロ + 元の `writePhase();` を OFF 枝に逐語温存。preprocess stock 一致を確認する。
- serializable 不変:
  - 施錠と validation は元のまま完了してから mutex に入る。
  - writePhase は既に獲得済みの record lock の下で動き、mutex は正しい commit 同士に追加順序を与えるだけ。
  - TID 計算、data install、release-store は変更しない。
- 遅さの期待機序:
  - disjoint write-set の transaction も、TID 決定、trace emit、WAL、data install、GC を含む `writePhase()` 全体が一列になる。
  - 待機 transaction は record lock を保持したままになるため convoy が強く、候補 A より侵襲的。
- 重ね先: `izanagi-trace` へ適用可能な独立 hunk。commit 近傍は現行 trace hook と非衝突だが、親の `git apply --check` を必須にする。

### 候補 C — write-set の冗長反復 sort

- 変更箇所: [transaction.cc:408](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t139-ladder/external/ccbench/cc/silo/transaction.cc:408) の stock `sort()` を、ON 時だけ同じ comparator による固定 8 回の反復へ置換。
- マクロ: `IZANAGI_DEGRADE_SILO_REDUNDANT_SORT`
- inert 保証: 裸マクロ。OFF 枝は既存 `sort(write_set_.begin(), write_set_.end());` の逐語温存。
- serializable 不変:
  - 各 pass が同じ `WriteElement::operator<`（[silo_op_element.hh:67](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t139-ladder/external/ccbench/cc/silo/include/silo_op_element.hh:67)）を使う。
  - 最終順序と permutation は stock と同じ。既存の trace permutation 検査 `transaction.cc:390-435` も残る。
  - lockWriteSet、validation、writePhase は無変更。
- 遅さの期待機序: lock 取得前の比較・swap・cache access を固定倍に希釈する。ただし小さい write-set では gap が弱い可能性がある。
- 重ね先: `izanagi-trace` には適用可能。`silo-sort-variant.patch` と同じ行を触るため、その上への stacking は不可。

### 候補 D — CAS 各試行前の固定 pause

- 変更箇所: `transaction.cc:169-173`、`desired.lock = 1` から CAS までに、ON 時のみ固定回数の `_mm_pause()`。
- マクロ: `IZANAGI_DEGRADE_SILO_LOCK_ACQUIRE_PAUSE`
- inert 保証: 裸マクロ。OFF 時は追加命令ゼロで preprocess stock 一致。
- serializable 不変:
  - CAS、expected 更新、retry、validation、release は完全に元のまま。
  - delay 中に状態が変われば、元の CAS failure が検出する。
- 遅さの期待機序: 各 lock 試行の前に CPU 時間を消費し、成功 CAS の密度を薄める。
- 重ね先: `izanagi-trace` に直接適用可能。ただし lockskip patch と近接する。
- 弱点: 構造的な集中資源ではなく人工 delay であり、ability probe として単純すぎる。

推奨は候補 A。外部相談の lock-manager 例を最小の一共有資源で具体化でき、任意の sleep 定数に依存せず、stock CAS の意味と memory order をそのまま保存できる。候補 B より lock 保持時間への副作用が小さく、候補 C/D より「何が直列化されたか」が明確である。

## 2. characterization driver の設計

新規ファイルは `orchestrator/campaign/silo_ladder_characterization.py` とする。予定構成は以下。

- `:1-55`: 契約、`PIN = pin.CURRENT_PIN`、patch 名、裸マクロ名、workload、timeout。
- `:57-90`: `_validate_env_tag()`、`_repo_root()`、patch SHA/target 検査。
- `:92-145`: clean tree から CMake `compile_commands.json` を生成し、`transaction.cc` の実 TU command を preprocess command に射影する `_load_compile_command()` / `_preprocess_transaction()`。
- `:147-180`: `_build_trace()`。fresh `TMPDIR`、`TRACE=1`、`-DCMAKE_CXX_FLAGS=-DIZANAGI_DEGRADE_SILO_LOCK_MANAGER=1`、buildcache 非経由。
- `:182-225`: `_run_trace()`、`_verify()`。trace directory は一時領域で、stdout の throughput は保存しない。
- `:227-260`: `_make_checks()`。副作用なしの純粋関数。
- `:262-350`: `main()`、JSON 出力、exit status。

実行順は厳密に次とする。

1. `_assert_single_tenant()` と `assert_pinned_clean()`。
2. clean pinned tree の stock preprocess SHA を取得。
3. `patchharness.applied()` に入る。
4. touch 集合が `cc/silo/transaction.cc` だけであることを確認。
5. マクロ OFF の preprocess SHA が stock と一致することを確認。
6. マクロ ON の preprocess SHA が OFF と異なること、および manager callsite が ON 枝にあることを確認。
7. fresh trace build、write を含む t4 YCSB run、verifier。
8. verifier 完了後に `applied()` を抜けて revert。
9. 再度 `assert_pinned_clean()`。
10. checks と JSON を書き、`all_pass` に応じて 0/1 を返す。

機械判定項目:

- `patch_targets_exact`
- `naked_macro_not_cmake_exposed`
- `apply_entered`
- `default_off_preprocess_matches_stock`
- `rung_on_preprocess_differs`
- `trace_build_succeeded`
- `run_succeeded`
- `writes_present`
- `verifier_exit_zero`
- `verifier_serializable`
- `verifier_certified`
- `revert_clean`
- `apply_roundtrip`
- `all_pass = all(checks.values())`

既存慣行への追従点:

- `applied()` が enter で apply、finally で revert する契約（[patchharness.py:234](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t139-ladder/orchestrator/campaign/patchharness.py:234)）。
- s3 の fresh build と verifier 構造（[s3_lock_coverage.py:123](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t139-ladder/orchestrator/campaign/s3_lock_coverage.py:123)）。
- s8a 同様、run と verifier まで `applied()` の body 内で行ってから revert（[s8a_trigger_coverage.py:191](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t139-ladder/orchestrator/campaign/s8a_trigger_coverage.py:191)）。
- `checks`、`all_pass`、0/1 exit、env calibration JSON（`s3:190-230`、`s8a:221-265`）。

相違点:

- broken-silo の「赤の歯」ではなく、正しい rung が certified 緑であることを確認する。
- 性能値・fitness・stock 比較は一切行わない。
- 裸マクロなので buildcache/source_digest へ通さない。`EVOLVE_BLOCK_SOURCES`、`ALLOWLIST`、freeze は変更しない。
- OFF preprocess identity と ON 枝の非空性を追加する。
- `--env-tag` を必須、`--cc` / `--cxx` を記録付きで上書き可能にし、Pegasus では `--env-tag pegasus --cc gcc --cxx g++` を許す。

実証 JSON は次に置く。

`output/env/<env-tag>/calibration/t139_silo_ladder_rung1_characterization.json`

JSON には env tag、full CCBench HEAD、patch SHA256、macro、compiler 実体、preprocess SHA、workload、verifier の verdict/certified/cycle/txns/writes、checks を入れる。throughput、latency、recovery fraction は入れない。

## 3. 文書の骨子

### `patches/README.md`

- `patches/README.md:6-12` の現行分類表に、未反映の第5類「診断計器」と第6類「劣化版 rung」を追加する。
- `patches/README.md:13-19` の説明直後に次を明記:
  - broken-silo = 正しさを意図的に壊す赤検出 fixture。
  - rung = serializable を保ったまま既知の非効率を入れる緑の ability-probe fixture。
  - 合成 variant = 改善候補、rung = recovery の出発点であり別物。
- `patches/README.md:42` の前に新節:
  - `## silo-degraded-rung1-lock-manager.patch — Silo degradation ladder rung 1`
  - macro、base pin、apply/revert、inert witness、正しさ不変、driver、JSON、非 stacking 対象。
  - 「性能差は未測定。本 wave は certified liveness のみ」を明記。

### `docs/decisions.md`

第6類追加を含める。現状の次番号は D94 なので、実装時の次の空き番号で新設する。

- `docs/decisions.md:258` の D16 後続拡張注記を「D18 第4類、D20 第5類、D94 第6類」に更新する。元の歴史的3分類本文は書き換えない。
- `docs/decisions.md:4200` 予定の新 D:
  1. rung を D16 第6類として out-of-tree patch に永久隔離。
  2. broken、variant、diagnostic との型の違い。
  3. rung 1 に中央 lock-manager 案を採用する理由。
  4. 裸マクロ/default OFF/preprocess witness/専用 driver。
  5. recovery loop、gap 測定、複数 rung は後続 wave。
  6. freeze、oracle、proof chain、gitlink は不変。
  7. 既知解への復帰は recovery であり、新規 CC の発明ではなく、roadmap §1 の研究目標には数えない。

### 設計台帳 insight

新規ファイル:

`output/insights/2026-07-28_t139-silo-degradation-ladder-design.md`

予定構成:

1. authority・scope・non-goals
2. rung / broken / variant / diagnostic の分類表
3. rung 台帳の必須 field
   - rung id、base pin、patch SHA、macro、target hunk
   - inert witness
   - correctness proof obligation
   - slowdown mechanism
   - composition contract
   - characterization JSON
   - recovery measurement eligibility
4. 候補4案と選定理由
5. rung 1 の file:line correctness proof
6. recovery fraction の規範定義
7. driver/evidence schema
8. mutation preregistration
9. future work と停止境界

位置づけ文は insight の冒頭と「§9 研究上の位置づけ」、D94 の「位置づけ」、patches/README の rung 節の3箇所に置く。

> 既知解への復帰は recovery であって新規 CC の発明ではない。`docs/roadmap.md` §1 の研究目標に数えず、ability probe としてのみ扱う。

これは外部相談 insight の必須但し書き（[該当 insight:137](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t139-ladder/output/insights/2026-07-27_external-consultation-scope-and-axes.md:137)）をそのまま制度化するもの。roadmap 自体は変更しない。

recovery fraction の規範定義は設計台帳 §6 に一箇所だけ置く。

\[
RF(X)=\frac{S_X-S_{\mathrm{degraded}}}
           {S_{\mathrm{stock}}-S_{\mathrm{degraded}}}
\]

- `S` は方向を「大きいほど良い」に正規化した、事前指定の同一 metric/statistic。
- 3点は同一 env、workload、compiler、trace-disabled 条件で取得する。
- 分母が正かつ識別可能になるまで RF は未定義。
- clamp しない。`RF < 0` はさらに悪化、`RF = 0` は回復なし、`RF = 1` は stock 水準、`RF > 1` は stock 超過。
- trace-enabled characterization 値から RF を計算してはならない。
- 本 wave は定義だけで、値を出さない。

## 4. テスト計画と変異事前登録

新規 `orchestrator/tests/test_silo_ladder.py` を作る。pytest は CCBench を build/run せず、次を持つ。

- patch の touch 集合、裸マクロ名、`CCBENCH_`/Options 露出なし。
- OFF 枝に stock CAS が逐語温存され、ON callsite が manager wrapper を呼ぶ構造。
- compile command から `-E -P` command を作る純粋変換。
- preprocess hash と verifier result から checks を作る純粋関数。
- non-certified、writes 0、OFF hash 不一致、ON hash 同一の各赤 fixture。
- fake `applied()` と fake clean checker により、post-context clean gate が実際に駆動されること。
- committed JSON の schema、期待 check-key 集合、`all_pass=true`。txns/writes の具体値は pin しない。

実証 JSON が持つもの:

- 実 patch apply/revert。
- 実 compiler/build/run。
- OFF preprocess stock 一致、ON 枝差。
- write を含む trace。
- verifier certified 緑。
- revert 後 clean。
- compiler/env/pin/patch SHA provenance。

変異事前登録:

| 変異 | 壊す hunk | 赤になる検査 | 理由 |
|---|---|---|---|
| M1 | patch の OFF guard を `#if 1` にする | `default_off_preprocess_matches_stock` | default build に mutex/helper/callsite が残る |
| M2 | ON callsite を元の直接 CAS に戻し、manager helper を dead code 化 | pytest `manager_callsite_live` | ON preprocess 差だけでは空の劣化を見逃すため、call graph の静的契約が殺す |
| M3 | manager wrapper の CAS 第3引数を `desired.obj_` から `expected.obj_` にする | pytest `stock_cas_exact`、実走 `verifier_certified` | lock bit を立てず成功扱いになり、trace lock-coverage integrity が赤になる |
| M4 | driver の certified 条件を `exit==0 OR certified` に緩める | `test_noncertified_never_all_pass` | verdict/certified/exit の AND 契約が崩れる |
| M5 | `applied()` exit 後の `assert_pinned_clean()` を削除する | `test_revert_clean_gate_is_driven` | apply 前だけの clean 検査では revert 漏れを検出できない |

## 5. 実装手順、所有関係、依存順、概算工数

1. **Patch + driver 契約凍結 — 同一 owner**
   - patch 名、macro、base pin、touch 集合、JSON check keys を決める。
   - patch と driver は別 owner に分けない。driver が patch の inert/ON/certified 契約の実行主体だからである。
   - 0.5人日。

2. **Patch 実装 — patch/driver owner**
   - pinned `izanagi-trace` から out-of-tree patch を生成。
   - `git apply --check`、OFF preprocess、ON preprocess、revert clean を確認。
   - submodule commit・gitlink 前進なし。
   - 0.5人日。

3. **Driver + pytest — 同 owner**
   - fresh build、run、verifier、JSON。
   - 純粋 helper と5変異の kill テスト。
   - 1.0〜1.5人日。

4. **文書 — docs owner**
   - patch/macro/check-key が凍結した後、README、D94、設計台帳を作成。
   - 実測前は JSON を「予定」と書き、`all_pass` 確認後にだけ実証済みへ更新。
   - 0.5〜0.75人日。

5. **親による実証・統合**
   - static pytest、`git apply --check`。
   - Pegasus login node で build/run。不可能なら短時間 qlogin。
   - JSON `all_pass`、revert clean、submodule clean。
   - 関連テスト、`tools/run_tests.py`、`tools/check_codex_agents.py`、`tools/check_docs.py`。
   - commit 後 `tools/check_ai_provenance.py`。
   - 0.5〜1.0人日、scheduler 待ち時間を除く。

6. **独立レビュー2本**
   - correctness lens: CAS 同値性、lock-order、validation/writePhase 非改変。
   - isolation/evidence lens: naked macro、pipeline 非露出、apply/revert、JSON、位置づけ、性能主張なし。
   - 修正込み 0.5〜1.0人日。

総計は約3〜4.25人日、scheduler 待ち時間を除く。

## 6. 未解決の設計問題と親 brief への疑義

1. **「劣化」の実測はまだ無い。** 本 wave で証明できるのは「構造的ボトルネックが生きている」「serializable/certified」「default inert」までである。stock より実際に遅いことは後続の trace-disabled gap calibration まで未確定。文書では「rung candidate / structurally degraded」とし、performance-calibrated rung への昇格条件を別に置くべきである。

2. **compiler 既定の不一致。** 既存 driver は `g++-13` を既定とするが（[buildcache.py:118](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t139-ladder/orchestrator/campaign/buildcache.py:118)）、親 brief の Pegasus login node は system g++ 11.4 を最初に試す。driver に `--cc/--cxx` を設け、JSON に実体・version を記録する裁定が必要。

3. **recovery fraction の `X` と方向が brief では未規定。** 上記の「higher-is-better score」「分母正」「clamp なし」を採用するのが妥当。これを採らない場合、lower-is-better metric や stock==degraded で式が逆転・未定義になる。

4. **source_digest との将来接続。** `transaction.cc` は `EVOLVE_BLOCK_SOURCES`（[source_digest.py:72](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t139-ladder/orchestrator/campaign/source_digest.py:72)）であり、裸マクロは通常の `resolve()` では未知文脈として fails-closed になる（`source_digest.py:451-458,702-713`）。本 wave は専用 fresh-build driver なので、これは望ましい隔離であり、`EVOLVE_BLOCK_SOURCES`、ALLOWLIST、freeze を変更しない。後続 wave で通常 recovery loop に rung を直接投入するなら、専用 identity/activation 経路について DW-O09 の再評価が必要になる。