## 計算ノードで落ちる箇所

静的検査では、計算ノードで必ず落ちる新規欠陥は確認できませんでした。計算ノードでの新構成の成功は未確認です。以下、行番号は統合後の現物を指します。

- **Python／PATH:** probe は repo root、hydrate の `_driver_module` は repo root と `orchestrator` を `sys.path` に追加するため、`-I` と `unset PYTHONPATH` に対応しています。`buildcache`／hydrate driver の import 時依存を静的に追い、必須の site-packages 依存は検出しませんでした。`sort_swo_oracle` の非修飾 `evolve_block` import は直接実行用の分岐です。旧 receipt は `/usr/bin/python3.10`、`/usr/bin/cmake`、GCC/G++ 11 の inside/outside 成功を記録しています。
- **site／並列度:** `bnode031` は `PEGASUS_COMPUTE` となり、`require_heavy_work_site` を通ります。旧 receipt の affinity は48 CPUなので、同条件の prepare は外側 `-j 48`。ただし本物の custom command 内部は数値なしの `make -j` です。
- **固定 configure:** outside の依存 install 後に prefix を渡す順序は正しいです。patch の追加 option は既定値を持ち、prepare が専用 define を渡さないこと自体は configure の障害になりません。
- **inside の配置:** SOURCE_DIR override と binary directory は別です。BASE_DIR 未指定の関門／両 build はそれぞれの `<build>/_deps` を使い、masstree の生成先だけが S 内です。prepare が両 OUTPUT を生成すれば、inside で custom command を再実行する必要はありません。

**[RB-1] nit — autotools と ccache の実効性は、新構成の計算ノード実走で確認が必要。**
影響：autoreconf 等が解決しなければ prepare-build 失敗となり、S6 は `S6_CONDITION_GATE_UNPROVEN` になります。

旧 receipt は生成物付き cache を使っており、bootstrap の成功証拠にはなりません。facts の pristine staging に対する SS2PL warm-up 13秒は肯定材料ですが、今回の制限 PATH での `autoconf`／`autoreconf` の所在までは証明しません。**実走で確認**してください。

prepare は ccache を抑制せず、host 環境も継承します。ただし `masstree_build` の本体は直接の autotools／make であり、CMake launcher がそのまま適用されるとは限りません。ccache が見つかっただけで HOME 書込みや偽の S6 緑が発生するとまでは断定できません。host prepare の副作用を sandbox 内の書込み観測と混同しないことが必要です。

**[RB-2] should-fix — prepare 失敗時、実行した argv が構造化記録から失われる。**
影響：S6 の拒否は維持されますが、計算ノードで失敗した configure 条件を receipt の `masstree_prepare` から復元できません。

`probe.py:1887` で argv を null に初期化し、`:1923` の成功 return 後だけ埋めています。configure 成功後の target 失敗でも両 argv は null のままで、`test.py:2282` はこれを期待しています。共有 helper を変更しない裁定は尊重しつつ、失敗時に保持できる呼出し入力と、実行済み argv の記録範囲を明確にする改善が必要です。

## 時間と予算

旧 receipt の実測は次のとおりです。

| 項目 | outside | inside |
|---|---:|---:|
| CCBench configure | 0.701秒 | 0.660秒 |
| CCBench build | 4.094秒 | 3.987秒 |
| probe 全体 | 93.276秒 | — |

hydrate の15.75秒は **login→Lustre**、prepare の13秒は **別 runner の計算ノード実測**です。単純加算は約122秒、作業見積りとして追加30〜60秒、全体約123〜153秒は妥当ですが、今回の `/scr` 実測ではありません。manifest の6回の version subprocess も追加されます。

通常所要は `s6_minimum_remaining_s=3600`、deadline 5100秒、walltime 5400秒に十分収まる見込みです。hydrate 最大1200秒、prepare configure 最大300秒／target 最大1200秒の分割も、既存実測との比較では保守的です。残時間が短い場合も、prepare の二つの timeout の合計は割当 budget 以下になります。

**[RB-3] nit — timeout 値の合計2700秒は S6 全体の終了上限ではない。**
影響：hang や終了処理の停滞では、完全な receipt が出ず、最後の partial 記録に留まる可能性があります。

manifest は無 timeout、prepare は直接の subprocess の timeout のみ、hydrate の kill 後の `communicate()` と staging 撤去も無制限です。最低3600秒の入場条件は、後続 build／関門／S7 の時間確保を保証しません。これは段4で受容された限界であり、新たな must-fix とはしません。

## テストコスト

親の実走結果は次のとおりです。

- F1：**180 passed、271.18秒**。単独ファイルだけで5分の90.4%を使用。
- F2：**897 passed / 2 skipped、710.98秒**。ログは `effective_scheduler=serial`。

F2 の主要な遅い node は以下です。名前は共通 prefix を省略しています。

| node | call |
|---|---:|
| `test_define_sink_cross_product_t2520_certify_entry_removal` | 79.09秒 |
| `test_g5_real_ledger_covers_at_least_90_percent_of_real_collection` | 57.80秒 |
| `test_g6_all_real_repo_items_stay_one_unit_and_keep_relative_order` | 54.31秒 |
| `test_t080_import_temp_environment_fails_closed_for_foreign_module` | 53.89秒 |
| `test_s6_live_offline_source_paths_and_prepare_order` | 25.30秒 |
| `test_s6_live_patch_cleanup…[gate]` | 20.37秒 |
| `test_s6_live_requested_gate_and_both_build_roots_match` | 19.10秒 |
| `test_s6_live_staging_is_readonly_outside_scratch` | 17.04秒 |
| `test_s6_live_patch_cleanup…[outside]` | 16.13秒 |
| `test_s6_prepare_failure…[target/configure]` | 9.03／6.56秒 |

offline 配線 node には teardown 6.83秒もあります。

**[RB-4] should-fix — fixture の反復構築コストと3 shard 実時間を測り、実 hydrate／prepare を維持して削減する。**
影響：S6 の受理集合は変わりませんが、受入テストの5分以内という検証記録を現ログでは成立させられません。

変更前の同一 node 計時と処理別計時がないため、**1本あたり何秒「増えたか」は算出不能**です。現在の call 全体を追加時間と扱ってはいけません。また parameter 展開や早期終了があるので、「8本×同じ追加時間」でもありません。観測済みの関連9 nodeだけで call 合計128.54秒です。

710.98秒を完全均等に3分割した算術値は237秒ですが、直列グループ、競合、collection の費用を含む実測上限ではありません。

意味を弱めない削減候補は、immutable な Git seed を一度構築し、各 test には独立した cache／dependency clone を渡すことです。origin 変更や ignored 生成物の隔離、各 test の実 hydrate／prepare は維持します。fixture の mimalloc／googletest は既に `LANGUAGES NONE` であり、MakeAvailable を消す案は不適切です。prepare の外側 `-j 16` も、copy/touch だけの target では主要費用と断定できません。

## fixture の忠実度

**[RB-5] nit — masstree fixture は生成物の存在と配置を検証するが、autotools／archive の実体を検証しない。**
影響：配線テストが緑でも、本番 prepare のツール不足や archive のリンク不良によって S6 が拒否され得ます。

検出できない差は次です。

- `bootstrap.sh`、autoreconf、configure の依存と環境。
- make の内部並列度、実 compiler／flags、生成 header の内容。
- 実 archive の object／ABI／リンク妥当性。fixture は空ファイルを touch するだけです。

一方、両 OUTPUT の生成前不在／生成後実在と、readonly な S を使う inside build は検査しており、段3 B-10 の主要な穴は塞いでいます。

**[RB-6] nit — package fixture は prefix の配線検査であり、本物の imported target の再現ではない。**
影響：本物の `gflags::gflags`／`glog::glog` の依存・リンク不良は、この fixture の緑では排除できません。

fixture config は marker 変数だけを設定します。ただし `find_package(... REQUIRED)` に加えて marker を要求するため、通常のシステム package が見つかっただけで prefix 欠落を緑にする経路は防いでいます。

**[RB-7] should-fix — 関門例外時にも、それまでの hydrate／prepare 観測を保持する。**
影響：実際には供給と準備を実行済みでも、receipt は `S6_BUILD_NOT_ATTEMPTED` となり、新観測2項目が失われます。

`_require_condition_gate` の例外は `observe_s6` を抜け、`run_probe:2756` が `attempted=False` の汎用観測に置き換えます。既存の例外処理ですが、新しい供給記録にも波及しています。cleanup test の成功は、この記録欠落を防いだ証拠にはなりません。

## 束縛と投入

`.pbs` と Python の束縛一覧は同じ9 pathです。追加2 path の fixture bytes、shell の22 parameter node、Python dirty 拒否の4 node、独立 literal 同期検査が反映されています。F1 の全件成功がこれらを含みます。

投入時に冒頭検査を通す条件は次です。

1. wave worktree から投入し、正準化した `PBS_O_WORKDIR` が expected worktree root と一致する。
2. expected commit が40桁の実 HEAD commit と一致し、job 開始まで HEAD を変更しない。
3. 9 path の staged／unstaged 差分がなく、各実ファイルの SHA-256 がその HEAD blob と一致する。
4. PBS spool の実行 bytes も、その HEAD の `.pbs` blob と一致する。
5. `refs/replace/` が存在しない。
6. cache／dependency root／nodefile が有効な絶対パスで、nodefile に実 hostname が含まれる。login hostname は拒否される。
7. Python 3.10 と起動検査用 command が解決し、scratch root に shim を作成できる。

9 path 外の dirty があるだけでは、この shell gate は拒否しません。推移的 import 全体の束縛でもありません。旧 receipt の7 path 記録は変更せず、新 receipt で9 path を確認する扱いが正しいです。

## 段 3 real 所見の反映

| 所見 | 反映状況 |
|---|---|
| B-4 | helper は変更せず、固定 configure の抑制差を author 報告に明記。新構成の計算ノード成功は未確認。 |
| B-10 | package config＋marker 必須化、masstree OUTPUT 2本、生成前後 assertion に反映済み。 |
| B-13 | 両束縛一覧、fixture bytes、dirty 検査に反映済み。投入時の確定 HEAD 照合は今後の実行条件。 |
| B-14 | staging context と通常失敗時の撤去検査あり。強制終了時の撤去保証なしを明記済み。 |
| B-15 | manifest 無 timeout／prepare 子孫停止の限界を明記済み。実 timeout・残存子孫を検証したテストではない。 |

指定資料内では、限界の記載は段4裁定と author 報告で確認できました。予定された insight への反映完了までは確認していません。

## 総括

**must-fix なし。** 新構成の計算ノード成功と、3 shard・5分以内の達成は未証明です。

should-fix：

- **RB-2:** prepare 失敗時の argv 記録を改善する。放置すると失敗条件の追跡情報が欠ける。
- **RB-7:** 関門例外時の供給観測を保持する。放置すると実行済み S6 が未実行扱いになり、新観測が消える。
- **RB-4:** fixture の反復費用を削減し3 shard 実時間を確認する。放置すると受入時間の達成記録が得られない。

nit：

- **RB-1／RB-3:** autotools・ccache の実環境と厳密 deadline は未保証。
- **RB-5／RB-6:** fixture の緑は本物の autotools、archive、package target の成功証拠ではない。