## 総括

**登録簿 +2 と driver 3 箇所の factory 配線を、段 5 の実測を条件に進める案です。** ただし brief には次の修正が必要です。

- REPORT の fixture は複合 directive への対応だけでは不足します。所有 TU を CMake target に追加する必要があります。
- 共通 `SORT_VARIANT_SOURCE` は同一 directive を 2 本含むため、既存の consumer テストにも波及します。
- P3 の「既存機構では届かない」は強すぎます。一意な複合行の枝選択は機構上観測可能で、不採用の根拠は主張範囲・scope・consumer の supply 拒否です。
- P2 の companion 保証は gate 単体にはありません。既存 driver 全経路の契約に依存します。
- REPORT 登録は supply の build-root 選択も変えるため、family 全体の「狭まる向きのみ」は meaning の追加だけからは証明できません。

以下の行番号は現行 worktree 基準です。必読 3 資料と関連コードを静的に確認しました。pytest・compiler・probe の実走、ファイル変更はしていません。

## 現行挙動

[condition_meaning_gate.py](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2153-witness-6/orchestrator/campaign/condition_meaning_gate.py:249) を以下 `G`、`orchestrator/tests/test_condition_meaning_gate.py` を `T` と略記します。

| 箇所 | 現行契約と本 wave への含意 |
|---|---|
| `G:249–301` | 登録簿は 15 件。`MEANING_SUPPORTED_MACROS` は登録簿から導出される。 |
| `G:967–987` | 新規対象は要求 `"1"`・既定 `"0"`、登録 source が `spec.owner_tus` 内の場合だけ宣言。BACKOFF_NOINLINE の例外は独立。 |
| `G:2937–2969` | 開始 directive の完全一致が所有 file 内でちょうど 1 回必要。その位置に自己完結した選択・完了 marker 塊を挿入する。複合式も既存機構で扱える。 |
| `G:3076–3140` | 実 compile argv の対象 define と companion を検査して所有 TU 全体を前処理する。 |
| `G:3146–3284` | 要求・既定を同じ meaning build root で configure。対象 macro 以外の comparable argv 差は赤。 |
| `G:3295–3315` | 観測が同じなら `compile-time-branch-selection-not-discriminating`、異なるが期待対と違えば `compile-time-branch-selection-mismatch`。 |
| `G:3348–3363` | `declaration=None`、または factory と一致しない宣言は `unestablished`。後者を必ず赤と想定してはいけない。 |
| `G:1892–1900` | CXX_FLAGS route の登録会員は supply の要求・既定で build root を共有する。今回変わるのは REPORT。 |

実 patched tree も読み、SORT は `transaction.cc:424`、REPORT は `ycsb_silo.cc:63`、SS2PL の複合行は `transaction.cc:56`、DLR は同 `:88` に確認しました。これは前処理実測ではありません。

## 最小変更と author の所有 path

### 登録簿

`G:295` の辞書末尾へ、既存順を維持して次を追加します。

```python
"SORT_VARIANT": (
    "cc/silo/transaction.cc", "#if SORT_VARIANT",
),
"IZANAGI_SILO_LADDER_RUNG1_REPORT": (
    "cc/silo/ycsb_silo.cc",
    "#if IZANAGI_SILO_LADDER_RUNG1 && IZANAGI_SILO_LADDER_RUNG1_REPORT",
),
```

根拠は `patches/silo-sort-variant.patch:54` と `patches/silo_ladder_rung1.patch:56`。`G:13–15` の 15 件という説明も 17 件へ整合させます。`DEFINE_SPECS`、factory、計装・比較ロジックは変更しません。

### driver 配線

次の既存引数だけを置換します。module import は既にあります。

```python
declaration=condition_meaning_gate.declare_define_runtime_meaning(request)
```

| 編集位置 | 妥当性・成果物への効果 |
|---|---|
| `p3_s4_loop_sort.py:130` | `:124` の要求値が 1 のとき SORT 宣言が発行され、`:140–143` の記録へ載る。0 その他へ factory 条件を広げない。 |
| `s6_sort_sweep.py:232` | `:224–226` は固定 1/0。`:244–247` の admission から SORT が縮む。 |
| `silo_ladder_rung1.py:2232` | REPORT だけ新たに宣言される。ループ内の BACKOFF_FIXED=-1、RUNG1 は引き続き宣言なし。REPORT 以外も確立したと報告しない。 |

`s1_direct_comparison.py:314–328` は既配線なので production 編集不要です。`:184` に SORT の既定 0 があり、要求 1 の sort_best では登録追加だけで meaning が実行されます。

### テストと fixture

**author 所有の編集面**は上記 production 4 files に加え、次を含めます。

- `orchestrator/tests/test_condition_meaning_gate.py`
- `orchestrator/tests/condition_gate_test_support.py`
- `orchestrator/tests/test_p3_s4_loop_sort.py`
- `orchestrator/tests/test_s6_sort_sweep.py`
- `orchestrator/tests/test_silo_ladder_rung1_driver.py`
- `orchestrator/tests/test_s1_direct_comparison.py`

`test_silo_ladder_rung1.py` 本体より、配線検査のある `_driver.py:30–47` が適切です。patch 3 本、production の fixture 外 CMake、凍結成果物は編集しません。

## 既存 pin と fixture の具体設計

### 複合 directive の独立した pin

`T:32–48` の tuple 末尾に SORT、REPORT を登録簿と同順で追加します。

`T:256–269` の `_patch_added_branch_declaration` は `+#if {macro}` 固定です。REPORT のみ、**テスト側に独立した期待逐語**を置き、それを patch additions から検索します。期待値を production registry から取得すると、誤った登録変更まで追認します。

`T:988` は次へ変更します。

```python
assert fixture_directives == [patch_declaration[1]]
```

`T:991` の registry と実 patch の一致検査は残します。`T:2692–2694` の集合 pin は tuple 展開なので追加が自動反映され、別の集合リスト追加は不要です。

### `_compile_time_source_root` の変更

`T:232` で取得済みの `_start_directive` を、`:245` の既定 directive に使います。明示 `directive` override、duplicate、prefix、nested、close、owner_text は維持します。

REPORT の fixture は次の形です。

```cpp
#if IZANAGI_SILO_LADDER_RUNG1 && IZANAGI_SILO_LADDER_RUNG1_REPORT
int izanagi_compile_time_selected = 1;
#endif
```

**ここに companion を `#define` しません。** `G:904–929` と `:1677–1693` による既存の注入経路を通し、要求・既定両方の実 argv に `RUNG1=1` があることを検査します。

さらに、`install_condition_gate_build_fixture` は同名 target が存在すると REPORT の owner を追加しません。

- `condition_gate_test_support.py:166–177`
- `fixtures/condition_meaning_gate/supplied/CMakeLists.txt:7`

現状 target は `transaction.cc` のみです。最小案は `T:253` の fixture 設置後、REPORT の場合だけ生成 CMakeLists に以下を追加することです。

```cmake
target_sources(ycsb_silo.exe PRIVATE cc/silo/ycsb_silo.cc)
```

これで共通 build helper の一般化を避けながら、REPORT の実 owner command を得られます。

### 共通 SORT fixture の重複

`condition_gate_test_support.py:40–64` の `SORT_VARIANT_SOURCE` には、外側の供給確認用と EVOLVE-BLOCK 内に同じ `#if SORT_VARIANT` が存在します。登録後は `start-not-unique` になります。

外側の定数定義を、例えば次の無条件の値参照に置換し、EVOLVE-BLOCK の directive を唯一にします。

```cpp
static constexpr int condition_gate_sort_variant = SORT_VARIANT;
```

値による前処理 bytes 差と既存の返却式を維持できます。gate の一意性検査を緩めてはいけません。

波及先は少なくとも以下です。

- `test_p3_exploration_namespace.py:198–208, 1342`
- `test_p3_build_authority_cli.py:1001–1006`
- `test_sort_swo_oracle.py:2650–2663`

これらは共通 fixture 修正後の回帰対象です。個別ファイル編集は必要な場合だけに限ります。

## consumer と official 経路

既存の `test_p3_s4_loop_sort.py:51–67`、`test_s6_sort_sweep.py:71–81` は gate の順序を検査し、通常テストでは gate 自体を置換しています。`declaration=None` を期待する直接 pin は確認できませんでした。したがって、既存テストが通るだけでは新配線の証明になりません。

新たに、実 helper を呼ぶテストで次を検査します。

- 正常 fixture：meaning green、対象 macro が admission の未確立一覧から消える。
- 所有 TU 内で対象 macro を無効化した fixture：supply が green のまま meaning red、driver が拒否する。
- REPORT：未確立一覧全体を空とせず、**REPORT だけが除かれたこと**を検査する。
- S1：`test_s1_direct_comparison.py:651–728` の実 evaluator 経路を使い、SORT の確立を明示検査する。

REPORT の実 companion 保証は `silo_ladder_rung1.py:4347–4355` の同時要求と、`:625–638` の実 compile argv 検査に依存します。`:2178–2184` は「存在する要求の値」を検査するだけで、REPORT から RUNG1 の存在を要求してはいません。したがって P2 は「公開 driver の成果物経路で閉じる」と限定すべきです。

official の依存供給は以下まで静的に追えます。

- `s8b_floor_campaign.py:3427`：masstree prebuild helper。
- 同 `:3480–3486`：offline configure args の作成。
- 同 `:4364` → `s1_direct_comparison.py:971`：gate capture への引き渡し。
- `p3_s4_loop.py:346–376`：BASE_DIR、SOURCE_DIR 3 本、任意の PREFIX_PATH。

**引数の到達は確認できますが、独立 meaning build からの `config.h` 可用性は未確認です。** 段 5 では同形供給を使った実 SORT owner の前処理成功が必要です。toy の成功や supply green で代用しません。P3/S6 の既存 capture はこの offline 引数を渡していないため、その環境問題まで 1 行差分で解消したとは扱いません。

## 具体正負例・変異候補

以下はコードに基づく予測です。段 5 で実測し、観測した理由コードで確定します。

| 入力・変異 | 期待結果／帰属 |
|---|---|
| SORT 1/0、唯一の実 directive、正常依存 | meaning `(1,1)/(0,1)`。supply green なら family admit、SORT の未確立が消える。 |
| REPORT 1/0、両 argv に RUNG1=1 | 同じ期待対。REPORT のみ未確立から除外。 |
| 唯一 directive の直前で SORT を `#undef` | 選択が両方 0、完了は両方 1。`not-discriminating`。無条件 `int value = SORT_VARIANT;` 等で supply 差を残し、meaning 単独の拒否にする。 |
| REPORT の owner 内で companion を `#undef` | argv 検査は通るが選択は両方 0。`companion-define-mismatch` ではなく `not-discriminating`。 |
| CMake fixture で companion token を compile argv から除く | `G:3109` 付近の companion 検査で `companion-define-mismatch`。meaning 単独テストとし、supply の同時拒否と混同しない。 |
| 登録 directive **だけ**を `#if SORT_VARIANT == 0` に変更 | 実 source に一致行がないため `start-not-unique`。mismatch にはならない。 |
| 専用 fixture と shadow 宣言を同じ反転式に揃える | `(0,1)/(1,1)` となり `selection-mismatch`。registry の 1 行変異とは別の、期待極性検査の対照。 |
| driver の宣言を None に戻す | meaning は `unestablished`。上記 meaning-only red fixture で、正常版 reject → 変異版 admit を検査する。正常 fixture だけでは admission は両方 true。 |
| tuple 順序だけを変更 | `T:978` の pin は落ちるが production の受理集合は変わらない。受理変異には数えない。 |

request の `companion_defines` を空にする操作は、spec から補完されるため companion 除去になりません。`DEFINE_SPECS` の companion 削除は本 wave の不変条件違反であり、採用する実装変異から外します。

既存の非対値検査 `T:1590–1603` は新規 2 macro にも適用し、1/None、1/1、0/0、0/1 で factory が None のままであることを確認します。

## 段 5：job-dir probe の骨子

`parent/probe_meaning_candidates.py` を **100 行以下・repo 外**に置きます。probe 本体と入力 JSON を記録し、正準 module を差し替えません。

1. base gate bytes を読み、登録簿への固定 5 entry 追加だけを施した shadow bytes を作る。許可差分との全体一致、原本 hash、`DEFINE_SPECS` 不変を確認する。
2. `orchestrator.campaign._t2153_witness_probe_<識別子>` の固有名で読み込む。relative import と dataclass のため `sys.modules` に固有名を登録するが、正準名には代入しない。
3. Request・CapturedInputs・宣言・evaluator はすべて同じ shadow module から作る。exact-type 検査があるため正準 module の object と混在させない。
4. brief の実 patched tree 3 本を入力とし、5 候補を固定 1/0 で meaning 単独評価する。
5. SORT/REPORT は supply と family も別途記録する。REPORT は登録前後の supply を同じ入力条件で比較する。
6. official 同形供給で SORT を少なくとも 1 cell 評価する。shadow admission は production 認証へ流用しない。

候補 directive は SORT/REPORT に加え、LOCK_IMPL と WFG_DIAG が `#if SS2PL_LOCK_IMPL == 1 || SS2PL_WFG_DIAG`、DLR が `#if SS2PL_DLR == 1` です。

LOCK_IMPL の対照では WFG=0、WFG の対照では IMPL=0 が必要です。相手が 1 なら OR 式が恒真になります。DLR の枝は WFG の内側なので、通常条件に加え WFG=1 の診断 cell を設ける場合は別 cell として明記します。値は configure args で与え、spec の companion は変更しません。

JSON に必要な項目：

- cell ID、環境条件、base commit、probe／原本／shadow hash。
- source root、pin、patch hash、owner、directive、完全一致件数。
- 要求・既定、companion、configure args、compiler/CMake。
- supply・meaning・family の canonical record、terminal status、reason、detail。
- green 時の選択／完了数と実 argv。
- red 時は得られた evidence をそのまま保存し、公開 record にない中間観測を捏造しない。
- 診断結果と production 採用可否を別欄にする。

実測で SORT/REPORT が緑でも、環境・対象・主張範囲を確認してから登録実装へ進みます。環境赤だけで「枝選択機構では原理的に不可能」とは結論しません。

## 不変条件と段 6 レビュー

不変条件は次のとおりです。

- 旧宣言は `G:634–636`、CLI は `G:4201–4210` の BACKOFF_FIXED 固定を維持。`T:2703–2705` の拒否検査を残す。
- `DEFINE_SPECS`、owner、target、route、inert 値、companion は不変。
- factory の新規対象 1/0 条件、BACKOFF_NOINLINE 専用例外は不変。
- 一意性、marker、非識別、期待極性、argv 比較は不変。
- 凍結成果物・既存 calibration・durable manifest は不変。
- 意味 green を枝本文の正しさ、動的到達、runtime 異常の発火へ拡大解釈しない。

段 6 は二つの観点でレビューします。

**受理集合と証拠の帰属：** meaning-only red の単一理由、None 戻しによる受理拡大の検出、旧経路の不拡張、REPORT companion が driver 最終検証まで成立すること、shadow 証拠の非流用。

**閉包と回帰：** tuple・patch・集合 pin、REPORT owner の target 組込み、共通 SORT fixture の一意性、4 consumer の記録、official の依存到達、REPORT supply の共有 root 化による差。

段 5 のテストは `tools/run_tests.py` 経由で関連 gate・driver・共通 fixture 利用先を実行します。さらに所定の docs／Codex agents 検査、commit 後の provenance 検査を行います。本段では未実行です。

## 親 brief への反論

| 仮説 | 判定 |
|---|---|
| **P1** | 条件付き賛成。production 配線は各 1 行で済むが、共通 SORT fixture の二重 directive を含める必要がある。official の `config.h` 到達は実測待ち。 |
| **P2** | 条件付き賛成。既存公開 driver 経路の契約で支える説明は可能。ただし gate helper 単体で companion 欠落を閉じてはいない。登録後の supply root 変更も別途検証する。 |
| **P3** | **機構上の必然ではない。** `G:2943` は選んだ逐語の一意性を検査し、他の異なる directive の存在は禁止しない。複合行は既存機構の候補で、meaning は dependency closure を比較しない。したがって supply の closure 赤を meaning 不成立の理由に転用できない。不採用は代表選択の scope 制約、主張範囲、consumer の拒否として記録する。 |
| **P4** | 現行 patch・機構不変なら支持。patch `:19–22, :41` が DLR0/DLR1 を変え、`G:2111–2118` は対象 macro しか comparable から除かないため `G:3280` の drift が残る。ただし環境前処理失敗が先に出る可能性と、枝の WFG 入れ子を区別する。 |
| **P5** | **許可 owner 内という限定なら支持。** KIND は `cc/ss2pl/transaction.cc` に該当 directive がない。一方、patch `:2299, :2309` の `wfg.cc` には KIND directive があり、「template のみ／どこにも指令なし」は誤り。owner 拡張は spec と supply 対象を変えるため scope 外。 |
| **P6** | 同形供給の probe は妥当。ただし過去の前処理 bytes 一致は今回の依存可用性や設定差の証明ではない。今回の cell 証拠を残す。 |
| **P7** | probe → 結果確認 → 確定集合実装の順を支持。ただし「意味 arm 緑だけで +2 確定」ではなく、REPORT supply 比較、consumer 記録、fixture 閉包を完了条件に加える。 |

規律 2 について、**meaning 追加単独は admit を維持するか reject に狭めます。REPORT の family 全体には supply 実行形の変更があるため、同じ論証を無条件には適用できません。** この残差を明記し、登録前後の実測比較を段 5 の必須証拠にします。