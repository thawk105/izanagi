## 前提の検算

**P1-a は枝選択機構について成立する。実 compiler による green は本段では未検証。** 指定の射影資料はすべて読めた。ファイル変更・pytest・build・patch 適用は行っていない。

以下の行番号は変更前の現物を指す。略号は次のとおり。

| 略号 | ファイル |
|---|---|
| G | `orchestrator/campaign/condition_meaning_gate.py` |
| S2 | `orchestrator/campaign/s2_verify_calibration.py` |
| TG | `orchestrator/tests/test_condition_meaning_gate.py` |
| T5 | `orchestrator/tests/test_s5_permutation_coverage.py` |
| Support | `orchestrator/tests/condition_gate_test_support.py` |

G:2929–2938 は改行だけを除いた開始指令の逐語一致を数え、**ちょうど 1 行**を要求する。G:2949–2955 の置換を対象 macro `M` に展開すると、次の形になる。

```cpp
#if M
IZANAGI_COMPILE_TIME_BRANCH_SELECTED()
#endif
IZANAGI_COMPILE_TIME_BRANCH_COMPLETED()
#if M
// 元の本文
#else
#if ADD_ANALYSIS
// 元の計測本文
#endif
// 元の本文
#endif
```

最初の `#if M` は挿入した `#endif` で閉じる。完了 marker の後に元の開始指令を再開するため、**元の `#else` と、その内側の `#if ADD_ANALYSIS` は marker の選択条件に入らない**。HIGHKEY の要求側本文にある `#if ADD_ANALYSIS` も同様である。

ただし、元の本文も所有 TU 全体の前処理対象ではある。「評価に入らない」は marker の条件についての説明であり、本文中の前処理エラーまで無視されるという意味ではない。

G:3158 の対照値は `comparison = "1" if requested == "0" else default`。今回の要求 1・既定 0 では対照は 0 になる。G:3220–3230 は同じ route で両値の compile command を導出し、G:3086–3092 が command 上の値を照合する。G:3282–3296 の期待値は次のとおり。

| 入力 | 選択 marker | 完了 marker |
|---|---:|---:|
| 要求 1 | 1 | 1 |
| 対照＝既定 0 | 0 | 1 |

`ADD_ANALYSIS=0/1` のどちらでも、この組は変わらない。対象 patch の入れ子は釣り合っており、この形に由来する反証は見つからなかった。D1490 の主張は枝選択に限り、異常の発火や動的到達性には広げない。

brief のアンカーは概ね一致するが、次を補正する。

- TG:1488 に、NOREAD を「未登録 macro」として使う既存テストがある。brief の変更表から漏れており、変更が必要。
- TG の parametrize は 1195 行、関数は 1196 行。
- **registry 追加は供給側の既存分岐にも影響する。** G:1879–1888 は登録済みの非 inert な CXX_FLAGS 要求で requested/control の build root を共有する。今回の 2 macro もこの分岐へ入る。G:2499–2504 の共有 root 許容も連動する。したがって「S2 の supply 呼出し・configure 引数は変更しない」は成立するが、「供給内部の実行形も完全不変」は成立しない。

## 届かない 4 件の検算

現状では 4 件とも未登録なので factory は `None` を返す。以下は、対応する実指令を登録するだけで既存機構に届くかの検算である。

| macro | 現物 | 届かない理由 |
|---|---|---|
| `IZANAGI_BREAK_TRIGGER_MISATTR` | `patches/broken-silo-trigger-misattr.patch:6–21` | `#if NO_WAIT_LOCKING_IN_VALIDATION`、`#if BACKOFF_TRIGGER_GATING` の内側に `#ifdef` がある |
| `IZANAGI_SILO_LADDER_RUNG1` | `patches/silo_ladder_rung1.patch:9,31` | 所有 TU に同じ `#if IZANAGI_SILO_LADDER_RUNG1` が 2 行 |
| `BACKOFF_REQUESTED_US` | `patches/silo-backoff-requested-us.patch:60,178` | 所有 TU に同じ指令が 2 行。header にも :29、:41 の 2 行がある |
| `BACKOFF_TRIGGER_GATING` | `patches/silo-backoff-trigger-gating-variant.patch:41–193` | 所有 TU に同じ `#if BACKOFF_TRIGGER_GATING` が 12 行 |

MISATTR は、外側条件が有効なら要求 `-D…=1` と対照 `-D…=0` の両方で `#ifdef` が真となり、両観測が `(1,1)` になる。外側条件が無効なら挿入した完了 marker も消えて、両観測が `(0,0)` になる。いずれも G:3288 の非識別判定で red。`#if BACKOFF_TRIGGER_GATING` の既定 0 だけでなく、もう一段外側の条件にも依存する点を brief に補足する。

残る 3 件は G:2934 の一意性検査で拒否される。RUNG1 の patch:56 の複合条件は別 TU `cc/silo/ycsb_silo.cc` にあり、RUNG1 の `owner_tus` に含まれない。REQUESTED_US の header を選ぶことも、G:967–969 の所有 TU 条件を満たさない。

既存機構で実 patch のこれら 4 件を green にする例は見つからなかった。旧 insight の「3〜12 箇所」は所有 TU 内の完全一致件数としては粗く、今回確認した件数は **2・2・12**。機構変更は計画しない。

## registry entry の具体差分

G:281 の既存最終 entry の後、:282 の閉じ括弧の前へ追加する。

```python
    "IZANAGI_BREAK_NOREAD_VALIDATION": (
        "cc/silo/transaction.cc", "#if IZANAGI_BREAK_NOREAD_VALIDATION",
    ),
    "IZANAGI_BREAK_HIGHKEY_VALIDATION": (
        "cc/silo/transaction.cc", "#if IZANAGI_BREAK_HIGHKEY_VALIDATION",
    ),
```

TG:44 の後にも同じ順序で 2 macro を追加する。TG:975 は集合ではなく **iteration order を含む tuple 等値**なので順序を揃える。

patch からの独立導出は次のとおり。

| patch | target の宣言 | 完全一致する追加指令 |
|---|---|---|
| `broken-silo-norw-validation.patch` | :4 `+++ b/cc/silo/transaction.cc` | :9 `+#if IZANAGI_BREAK_NOREAD_VALIDATION`、1 件 |
| `broken-silo-highkey-validation.patch` | :3 `+++ b/cc/silo/transaction.cc` | :8 `+#if IZANAGI_BREAK_HIGHKEY_VALIDATION`、1 件 |

TG:253–266 の `_patch_added_branch_declaration` はこの 1 件を導出するため、上記 entry は TG:988 の `(target, directive)` 等値条件を満たす。

G:286–288 の導出により、枝選択 registry は **12→14**、意味対応集合は BACKOFF_FIXED を含め **13→15**、未対応は **25→23** になる。`DEFINE_SPECS` は変更しない。

## S2 配線の具体差分

S2:108–110 を次の形にする。

```python
    meaning = condition_meaning_gate.evaluate_define_runtime_meaning(
        captured,
        request=request,
        declaration=condition_meaning_gate.declare_define_runtime_meaning(request),
        cxx=buildcache.DEFAULT_CXX,
    )
```

既存 import で足りる。S2:95–107 の capture/supply、:111–113 の `use_class="raw-measurement"` は据え置く。`configured_commands` は渡さず、meaning 側は G:3220 の 2 configure を使う。

G:3326 の引数型は指定どおり、

```python
MeaningWitnessDeclaration | ConditionalBranchMeaningDeclaration | None
```

である。今回の entry は G:967–969 の要求 `"1"`・既定 `"0"`・所有 TU 条件を満たす。適正な request でこの値条件を満たさなければ factory は `None`、G:3335–3341 は `unestablished / meaning-witness-undeclared` を返す。これは meaning の red にはならない。ただし request 自体の検証失敗や supply の拒否まで免除するものではない。

P1-b は検索結果と整合する。両 macro を要求する production 経路は S2。`screening_driver.py:81–82` は既定値表、`t2187_adaptive_const_probe.py:3849` は fixture 記述であり、追加配線しない。

## テスト案

**変更は指定の 4 file に収める。**

1. **既存 registry 被覆の拡張**

   TG:32–45 に 2 macro を追記すると、:1195 の parametrize に実 compiler を使うケースが 2 件増える。:972 の patch 束縛テストも両 macro を検査する。

   TG:2585 の domain テストは式の変更不要。意味集合は tuple から追随し、供給 route 件数 **22/16 は不変**。旧宣言型を BACKOFF_FIXED に限定する :2617–2619 も維持する。

2. **未登録 macro テストの修正**

   TG:1488 の NOREAD を `IZANAGI_BREAK_TRIGGER_MISATTR` に替える。:1489 と :1500–1502 の期待値は維持する。テスト削除や green への期待値変更はしない。

3. **(a) 型の実 TU 構造を写した正例を 1 関数追加**

   TG:1337 の後に、例えば `test_compile_time_branch_selection_accepts_else_with_nested_analysis` を置く。NOREAD を使い、`owner_text` を次の形にする。

   ```cpp
   void validation_fixture() {
   #if IZANAGI_BREAK_NOREAD_VALIDATION
     int selected_body = 1;
   #else
   #if ADD_ANALYSIS
     int analysis_body = 1;
   #endif
     int default_body = 1;
   #endif
   }
   ```

   `_compile_time_source_root(tmp_path, macro, owner_text=…)`、実 factory、`capture_define_inputs`、実 meaning evaluator を使う。既存正例と同様に status/reason、要求 `(1,1)`、既定 `(0,1)`、観測値 `"1"`/`"0"` を確認する。

   Support:17–38 の `_OPTIONS`、:166–180 の設置処理、コピー元 `supplied/CMakeLists.txt:1–8` は **ADD_ANALYSIS を define しない**。通常のこの fixture では未定義識別子が `#if` 内で 0 と扱われ、analysis 本文が消える。これは未定義時の正例であり、`ADD_ANALYSIS=1` の実測とは記録しない。0/1 に依存しない構造上の理由は前節のとおり。

   新規 compiler テスト関数はこの 1 本。既存 parametrize の追加 2 ケースと合わせ、compiler を使う実行ケースの純増は 3 件になる。0/1 や 2 macro の追加直積は作らない。

4. **既存 source 検査の拡張**

   T5:89 を `if module in {s2, s3, coverage}:` にする。既存 :85 の module parametrize は既に s2 を含む。

5. **S2 consumer テストを追加する**

   source 内に factory 呼出し文字列があるだけでは、その戻り値が meaning evaluator に渡ることは証明できない。T5:130 の前に、S5 の :94–128 と同形の monkeypatch テストを追加する。

   両 macro を parameter にし、実 `make_define_request` と factory の結果を使いつつ、capture・supply・meaning・family の外部処理を stub 化する。次を確認する。

   - factory が受け取る request と evaluator の request が同一。
   - declaration が `ConditionalBranchMeaningDeclaration` で、macro・所有 TU・逐語が期待どおり。
   - family に supply/meaning の両 record と `raw-measurement` が渡る。
   - admit 時には返却辞書へ各 canonical JSON が載る。
   - reject 時には `RuntimeError` になる。

   admit/reject の分岐は parameter 化しても compiler 呼出しは 0。新 gate や新台帳は不要。

## 変異 matrix の事前登録候補

以下は **期待 KILLED 候補であり、実測結果ではない**。TG/T5 の略号は前掲のパスを表す。新設行は author 後の行番号に確定させる。

| 変異対象 | production 側の変異 | 期待 KILLED node | 被覆の由来 |
|---|---|---|---|
| G:282 前の NOREAD entry | 指令末尾の 1 文字を変更 | `TG::test_compile_time_branch_registry_and_fixtures_are_bound_to_real_patches`、`TG::test_compile_time_branch_selection_accepts_each_registry_macro[IZANAGI_BREAK_NOREAD_VALIDATION]` | 既存テストの対象拡張 |
| 同 HIGHKEY entry | 同上 | 同 registry node、`…accepts_each_registry_macro[IZANAGI_BREAK_HIGHKEY_VALIDATION]` | 既存テストの対象拡張 |
| 各新 entry の `source_rel` | `include/backoff.hh` に変更。macro ごとに別変異 | 同 registry node、対応する accepts node | 既存テストの対象拡張。factory の所有 TU 条件でも宣言が出ない |
| S2:109 の配線 | `declaration=None` に戻す | `T5::test_condition_preflight_dominates_first_benchmark_build[orchestrator.campaign.s2_verify_calibration]`、新 S2 consumer node | 本 wave の拡張・新規テストが初めて検出 |
| G:2934 | `!= 1` → `< 1` | `TG::test_compile_time_branch_selection_rejects_duplicate_start_directive` | 変更前から存在 |
| G:3288–3294 | 非識別検査を除去 | `TG::test_compile_time_branch_selection_rejects_non_discriminating_observation` | 変更前から存在。reason code の不一致を検出 |
| G:967 | `requested != "1"` → `requested not in {"0", "1"}` | `TG::test_compile_time_factory_rejects_nonpaired_values[0-0]` | 変更前から存在 |

非識別検査の単独除去でも G:3295 の期待値照合が red を返す。したがって、この変異の KILLED は **非識別 reason の契約を守る証拠**であり、誤受理を防ぐ独立層の生死証明ではない。前 wave insight:60–64 の指摘を継承する。

T5:89 の条件を元へ戻す変異は test 側なので登録しない。新 S2 consumer は、source 検査が外れても配線の実引数を検査する。

各候補は焦点 baseline を先に通し、観測された failing node を確認してから登録上の exact node 集合を確定する。追加正例だけが殺す変異を作るための機構変更は行わない。

## 焦点テスト集合と影響範囲

`rg -n` と `grep -rnE` で test consumer を検索した。直接 import と集合参照は次のとおり。

| 対象 | test file とアンカー |
|---|---|
| condition gate の直接 import | `test_condition_meaning_gate.py:18`、`test_mocc_proof_surface.py:17`、`test_s1_direct_comparison.py:32`、`test_t2228_driver_gate_liveness_probe.py:9`、`test_screening_driver.py:19`、`test_ccbench_spawn_sites.py:23`、`test_s8b_floor_campaign.py:3841,3899`、`test_paper_story_a2_certification.py:629` |
| S2 の直接 import | `test_s5_permutation_coverage.py:10`、`test_ccbench_spawn_sites.py:25`、`test_build_site_gate.py:23` |
| registry／意味集合参照 | `test_condition_meaning_gate.py:229,975,988,1293,1296,2606,2609`、`test_mocc_proof_surface.py:569` |
| 共有 fixture support | `condition_gate_test_support.py:7`。変更不要 |

間接参照も含む検索では、次も該当した。

`test_backoff_sweep.py`、`test_backoff_extended_sweep.py`、`test_backoff_profile_pegasus.py`、`test_p3_s4_loop.py`、`test_paper_story_a1_paired.py`、`test_pegasus_calibration_workload.py`、`test_t316_sandbox_probe.py`、`test_s8b_oracle_n_pilot.py`、`test_p3_build_authority_cli.py`。通常 test 外には `orchestrator/manual_probes/test_t2397_a1_source.py` がある。

再走を次の順にする。

1. **変更直結の焦点集合**  
   TG の registry 束縛、各 registry macro 正例、新 (a) 型正例、未登録・非対値 factory、旧宣言型/CLI 境界、domain 境界、重複・非識別・完了 marker 負例。T5 は全体。
2. **直接 consumer 回帰**  
   `test_mocc_proof_surface.py`、`test_build_site_gate.py`、`test_ccbench_spawn_sites.py`。供給の共有 root 分岐もあるため、TG の供給・共有 command 関連を含め、最終的には TG 全体を対象にする。
3. **統合受入**  
   親の既存 acceptance 全走で上記の間接 consumer を覆う。新たな全走系統や manual probe 実行は追加しない。

後段のテストは `python3 tools/run_tests.py …` を通し、完了時の既定 checker と親の `tools/dev_wave_wait.py acceptance` に接続する。本段ではいずれも未実行。受入 5 分以内は実測で判定し、静的検査から保証しない。

## リスクと未確定点

- **stock と patch 後の一意性**  
  現在の `external/ccbench` HEAD は `511c9538…`、S2:63 の PIN は `dff0f1e` で一致しない。両者の stock `transaction.cc` に対象 2 macro の同名出現がないことを検索で確認した。S2 PIN の該当本文も patch context と整合する。各 patch が開始指令を 1 行だけ追加するため、正しく 1 回適用された TU では完全一致指令も 1 行になる。実適用後の compiler 実走とは区別する。

- **供給側の暗黙の実行形変更**  
  registry 会員追加で G:1879 の共有 build root 分岐に入る点は brief の補足事項。I4 を「S2 の supply 呼出しと configure 引数を変えない」と読む限り維持できる。「内部 root 配置も不変」という意味なら P1 の前提を親が確認する必要がある。ここを避ける機構変更は提案しない。

- **masstree `config.h`**  
  現 checkout の `include/masstree_wrapper.hh:20` は `<config.h>` を要求し、`cmake/ThirdParty.cmake:66–78` は生成を build custom command として持つ。gate の `_configure_compile_commands`（G:1703–1720）は configure と compile database 取得であり、その build を実行しない。

  supply と meaning は同じ `_preprocess_argv` を使うが、supply は元 TU、meaning は shadow TU を別 temporary build から前処理する。**supply green だけで meaning の header 可用性まで保証はできない。** 同じ供給済み依存先を使うなら header 欠落は共通に解消するが、別 build の依存展開先なら改めて欠落しうる。正確な reason は supply が `preprocess-failed`、meaning が `compile-time-branch-preprocess-failed`。本 wave の toy fixture はこの実機依存を検証しない。

- **未登録 duration node**  
  `orchestrator/tests/conftest.py:1675–1695` は未登録を `None` として扱い、:1739–1763 は unknown の割当コストを使う。`tools/acceptance_shards.py:397–404` は未登録を 1 秒の重みとする。新 node の未登録だけで失敗する契約ではなく、実測時間を 0 と見なすものでもない。台帳更新は本変更に加えない。

- **観測上の限界**  
  今回は静的な導出であり、baseline green、変異 KILLED、S2 成果物の未確立一覧減少は後段の確認事項。checker や実機 S2 の成功を先取りして報告しない。

読み取り用の Python heredoc は `guard_bash` に「保護対象パスと不透明構文の同居」として拒否されたため実行していない。その後、許可された単純な `git show`・`grep` による読み取りで確認を継続した。

## 総括

既存機構を変更せず、2 entry と S2 の factory 配線を追加する計画で進められる。(b)(c) の 4 件を含める根拠はない。

変更は指定の 4 file。brief に対する必要な補正は、**NOREAD を未登録扱いする TG:1488 の差替え**と、**registry 追加による供給側の共有 build root 分岐への移行の明記**である。新規 compiler 正例は 1 関数、S2 配線は compiler 不要の consumer テストでも確認する。実装・baseline・変異・受入の実測は後段へ引き継ぐ。