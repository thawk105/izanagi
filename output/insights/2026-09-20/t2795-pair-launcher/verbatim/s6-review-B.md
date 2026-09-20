## 判定と範囲

**must-fix 0 件、should 2 件。レンズ B は GO。** 既定経路を変える production 上の不具合は見つかりませんでした。ただし、新テストの一部は名前・報告より被覆が狭く、補正を勧めます。

指定資料と累積差分を静的に読み、base `371674ea6` との関数比較・AST によるテスト件数集計を行いました。pytest、変異実行、ファイル書込みは行っていません。

以下、L＝`p3_s4_loop.py`、J＝`p3_s4_loop_pegasus.sh`、TL／TJ／TV＝指定された各テストファイル。行番号は現 worktree のものです。

## must-fix

なし。

## should

**S1 — 「既定 CLI の bytes 不変」テストが既定の候補 CLI を通っていない。**

- **根拠:** TL:9923–9927 は `main(["--stock-control", "--isolate-worktree"])` と `default_cfg()` の preimage を比較しています。新 option を一つも使わない候補 main の cfg は捕捉していません。
- **成果物への影響:** 候補分岐だけで identity key を追加する回帰は、この名前のテストでは拒否できません。現在の実装にその回帰があるという指摘ではありません。
- **是正:** 既存テスト内で新 option なしの候補 main も通し、campaign 境界で捕捉した cfg を同じ固定 bytes と比較する。新しい検査基盤は不要です。

**S2 — 同 manifest の identity テストが layout root の一致を独立に検査していない。**

- **根拠:** TL:9657–9679 の helper は `exploration_campaign_layout` を、受け取った ID に無関係な同一 layout に置換します。TL:10101–10127 は canonical preimage と receipt bytes を比較しますが、layout に渡された ID を比較しません。
- **成果物への影響:** stock または候補だけが誤った campaign ID で layout を選ぶ実装でも、このテストの layout／receipt 部分は緑になり得ます。
- **是正:** TL:9894 のテストと同様に layout factory の入力 ID を記録し、両経路とも `str(ident.campaign_id(cfg))` であることを既存テスト内で確認する。

## nit・削除と未了

**N1 — lock 復元テストは同じ検査の重複実行です。**

- **根拠:** TL:10013–10014 は `test_verify_opt_in_reaches_real_loop_evaluate_options(..., True)` を呼ぶだけです。復元比較は既に TL:10006–10010 にあります。
- **影響:** 削除しても受理集合は変わらず、実行件数だけが 1 減ります。
- **是正:** 専用 node を残すなら復元比較をそちらへ移し、重複をなくす。裁定上の名前を維持するためだけなら、重複であることを報告する。

**N2 — README は親の更新待ちであり、完成済みではありません。**

- **根拠:** README:365–371 は今も manifest・宣言値を「proposal 分岐だけへ渡す」と説明しています。author 報告「波及」には変更項目がありますが、適用可能な差分案そのものはありません。
- **影響:** production／test の受理集合は変わりませんが、pair 時の identity 転送の説明が実装と食い違います。
- **是正:** 親の予定どおり既存文を置換し、stock env、候補優先 rc、fresh layout、skip 非成功、別 worktree、digest 更新を記載する。第二の qsub fence は追加しない。

削除裁定の対象だった terminal 復元の二層化、較正・verify の job env、token/projection 専用テストは残っていません。resolver は追補で認可された実 admission 用であり、削除対象ではありません。

## 各 hunk と既定挙動

| 累積差分の hunk／現物 | 分類・判定 |
|---|---|
| L imports（73、93 付近） | 新機能用 import。既定 cfg／argv／WAL の変更なし |
| L:417–461 | stock gate 追加。候補側の capture・request・bits 宣言は従来形を維持 |
| L:1661–1670 | 較正 helper の新設。既定値の再定義なし |
| L:1899–2019 | digest 抽出、stock resolver・評価関数の新設 |
| L:2948–2955 | 新 CLI option。受容済みの `--v` 曖昧化あり |
| L:3038–3055 | 新 option の組合せ検査。既存 ingestion 排他の後 |
| L:3147 | stock のみ coder authority 必須条件から除外 |
| L:3163–3173、旧 `perf` 代入削除 | perf 確定の前倒し。新 option なしでは cfg に key を追加しない |
| L:3209–3217 | stock 専用 context。既定側の引数は維持 |
| L:3244–3258 | proposal／LoopState より前の stock 分岐 |
| L:3366 | `_refresh_critic_digest` への抽出。同じ出力先・引数・write 処理 |
| J:99–114 | stock env と identity argv。未指定では off |
| J:596–621 | rc 捕捉と pair 分岐。既定 driver argv は不変 |
| TL の 2 hunk | import と末尾への新テスト追加のみ |
| TV の 1 hunk | 末尾への helper／テスト追加のみ |
| TJ の各 hunk | 新 pin／テスト、許可された呼出し数・順序・helper 履歴化。詳細は後述 |

`default_cfg()`、`default_perf()`、`_assert_coder_value_domain()`、`_resolve_duplicate()` は base と関数本文が一致しました。固定 preimage は TL:9654 の文字列定数で、テスト対象から実行時に再生成した期待値ではありません。ただし「変更前に採取した」という来歴自体は報告・コメントによるもので、採取ログは提示資料にありません。

stock 側には指定の 5 outcome があり、成功は `certified-stock` のみです。variant と BUILD_START の `src_token` を両方確認し、skip の結果復元はありません。stdout も指定形式です。

digest は L:2015 の「skip でない、かつ WAL record が存在」で更新に入り、helper 内で admitted view を取得します。生 WAL の存在確認そのものが admission 判定なのではありません。更新時の admission は省略されていません。

## テストごとの実効

TL の autouse fixture（85–88）は condition gate 全体を stub にします。したがって、**すべての新テストが外部境界だけを stub にしている、とは言えません。** 一方、stock 評価関数そのものを stub にして内部変異を隠す構造はありません。

下表のテスト名は `test_` を省略しています。

| TL テスト・行 | 実際に通る層／限界 |
|---|---|
| `stock_control_reaches_campaign_under_applied_template` :9681 | 実 main＋実 stock 関数。applied・gate・campaign は spy／stub。genome、順序、転送を検査 |
| `stock_control_does_not_touch_loop_state` :9744 | 実 main＋実 stock 関数。禁止 spy は L の実呼出し先に設置。checkpoint 不在／bytes 保持も検査 |
| `stock_control_cli_rejects_conflicting_modes` :9772 | 実 argparse。所定のエラー文と rc、後段未到達を検査 |
| `fixture_value_minus_one_remains_rejected` :9787 | 実 main に加え、構築後に値を変えた coder を実 iteration に渡す。M5 を constructor 拒否だけで済ませない |
| `stock_control_rejects_non_stock_certified_source` :9809 | 実 stock 判定。campaign 結果と WAL 読取を模擬。variant と source の独立負例 |
| `stock_control_reports_skipped_without_restore` :9825 | 実 stock 分岐。campaign は stub。復元禁止、ID 非捏造、checkpoint 保持 |
| `stock_condition_gate_declares_adaptive_branch` :9843 | `_REAL_CONDITION_GATE` を使用。request／MeaningCase を実構築し、supply／meaning 実行を模擬 |
| `calibrated_perf_uses_p2_constants_and_exact_workload` :9885 | 実 helper。期待値は P2／S2 定数から独立に構成 |
| `calibrated_cli_binds_effective_perf_before_layout` :9894 | 実 emit／stock main。cfg、perf、layout 入力 ID、実 lock を比較 |
| `default_cli_preserves_preimage_bytes` :9923 | 実 stock main＋固定定数。候補 main の欠落は S1 |
| `calibrated_candidate_cli_reaches_effective_perf` :9931 | fixture／proposal の実 main・iteration。campaign 境界で停止して観測 |
| `perf_cli_rejects_partial_and_invalid_options` :9974 | 実 argparse |
| `verify_opt_in_reaches_real_loop_evaluate_options` :9982 | 実 main＋stock 関数＋`loop.run_campaign`。evaluate は観測 stub。実 lock からも復元 |
| `campaign_lock_preimage_reconstructs_performance_correctness` :10013 | 上記 verify=True の再実行。N1 |
| `stock_digest_refresh_keeps_checkpoint` :10017 | 実 main、stock、loop、pipeline 呼出し。実 WAL／digest を検査。gate・source 等は模擬 |
| `stock_resolver_refuses_non_stock_evidence` :10066 | 実 stock 関数＋loop＋pipeline 呼出し。source evidence を差し替え、ABORT reason と build 未到達を確認 |
| `stock_and_candidate_share_manifest_campaign_identity` :10101 | 実 manifest／identity／receipt と両 main。layout 観測の欠落は S2 |
| `candidate_cli_rc_zero_on_rejected_outcome_is_not_pair_success` :10130 | 実 proposal／iteration の grammar 拒否と既存 rc=0 を検査 |
| `stock_perf_cli_ingestion_exclusion` :10153 | 実 main の既存 ingestion 排他を検査 |

digest／resolver／TV が使う既存 `_mock_pipeline` の定義は投影外です。提示された呼出し側では admission／verifier を新たに stub 化していませんが、その helper 内部まで独立に監査済みとはしません。

| TJ／TV 新テスト | 判定 |
|---|---|
| TJ `stock_fragment_mutants_have_one_static_failure` :1844 | 実 contract 関数へ変更した文字列を入力。shell 実行ではない |
| TJ `default_job_invokes_driver_once` :1868 | 実 shell。未設定／0、fixture／proposal／K2 の argv exact と履歴 1 件 |
| TJ `pair_job_runs_candidate_then_stock` :1889 | 実 shell。順序、stock argv exact、同 receipt、K2 宣言転送 |
| TJ `pair_job_runs_stock_after_candidate_failure` :1909 | 実 shell＋EXIT trap。履歴 2 件、process rc と JSON `driver_rc` |
| TJ `invalid_stock_environment_refuses_before_prebuild` :1919 | 実 shell preflight。空値等の rc=2、後段・compute-result 不在 |
| TV `performance_verify_keeps_legacy_and_all_repetitions` :293 | 実 evaluate 呼出し。legacy→全 performance rep、flags、COMMIT を検査 |
| TV 初回 anomaly :320 | `do_bench=True`。trace を負例へ替え、bench 禁止・即停止・ABORT を検査 |
| TV 最終 anomaly :324 | 同上。最後の rep までの実行を必要とする |
| TV legacy anomaly :329 | performance に進まないことを検査 |
| TV exact numactl :333 | 不一致時は build／trace 禁止、空 prefix は成功正例 |

TJ の driver stub は外部プロセス境界として妥当です。`compute-result.json` は stub が成功値を作るのではなく、実 shell の EXIT trap が生成します。TV は `do_bench=False` による偽の未到達検査にはなっていません。

## M0〜M17 の静的予測

**author／fix1 の「プロセス内 KILLED」は、ファイルを書き換えて再起動する harness の結果とは別物です。** 以下は後者でも同じ担当 node が検出するかの予測であり、実測結果ではありません。

| 変異 | 担当 node・主な検出理由 | 予測 |
|---|---|---|
| M0 | docstring のみ | SURVIVED |
| M1 | TL:9681 `stock_control_reaches_campaign_under_applied_template`：genome の `BACKOFF_FIXED` 不一致 | KILLED |
| M2 | 同 node：`BACK_OFF` 不一致 | KILLED |
| M3 | TL:9744 `stock_control_does_not_touch_loop_state`：禁止 spy／checkpoint 変更 | KILLED |
| M4 | TL:9772 `stock_control_cli_rejects_conflicting_modes`：所定の早期 argparse 拒否を失う | KILLED |
| M5 | TL:9787 `fixture_value_minus_one_remains_rejected`：構築後変異が quarantine に到達 | KILLED |
| M6 | TJ:1889 `pair_job_runs_candidate_then_stock[k2]`：stock argv の manifest 欠落 | KILLED |
| M7 | TL:9809 `stock_control_rejects_non_stock_certified_source`：非 STOCK を成功扱い | KILLED |
| M8 | TL:9894 `calibrated_cli_binds_effective_perf_before_layout`：cfg の records／threads 不一致 | KILLED |
| M9 | TL:9923 `default_cli_preserves_preimage_bytes`：固定 preimage 不一致 | KILLED |
| M10 | TL:9843 `stock_condition_gate_declares_adaptive_branch[-1]`：stock request／適応枝宣言不一致 | KILLED |
| M11 | TJ:1868 `default_job_invokes_driver_once` の未設定ケース：履歴が 2 件になる | KILLED |
| M12 | TJ:1909 の proposal・candidate=7：stock 未起動 | KILLED |
| M13 | TJ:1909 の (7,0)／(7,9)：候補優先 rc 不一致 | KILLED |
| M14 | TL:9982 `verify_opt_in_reaches_real_loop_evaluate_options[True]`：追加 correctness が消える | KILLED |
| M15 | TV:324 `performance_anomaly_at_last_repetition_aborts_before_bench`：最終負例に達せず bench 側へ進む | KILLED |
| M16 | TL:10066 `stock_resolver_refuses_non_stock_evidence`：期待した admission-error を失う | KILLED |
| M17 | TL:10017 `stock_digest_refresh_keeps_checkpoint`：実 admission で失敗。TL:9681 も resolver 引数欠落を検出 | KILLED |

補足：

- M6 は K2 ケースが担当です。manifest のない fixture／proposal ケースや TL identity テストへ帰属させてはいけません。
- M10 は import 時に保存した `_REAL_CONDITION_GATE` を呼ぶので、ファイル変異後の新プロセスなら変異対象を通ります。
- M16 の mutant は後続の build mock 引数不足などで別の abort に至る可能性があります。それでも `reason == "admission-error"` が検出します。「mutant が測定成功した」という証拠ではありません。
- M17 は報告どおり複数 node が失敗し得ます。「単一理由」は全 suite の失敗件数 1 を意味しません。
- TJ の新 7 pin は fragment がそれぞれ一意です。各置換は既存 proposal／fixture pin を残し、missing label が 1 個になる構造です。stock-mode の変更は別の stage-order 検査にも影響しますが、単一 missing label の契約とは矛盾しません。

## 既存テストの変更・shell・plain harness

既存期待値の変更は許可された範囲です。

- TJ:522 の呼出し箇所数は 2→3。
- TJ:577 に stock の stage-order marker を追加。
- TJ:1180–1357 の helper を履歴・rc・JSON 返却へ変更し、各 consumer で従来の rc=0 を再確認。
- helper から消した `assert completed.returncode == 0` は、既存 consumer の `rc == result["driver_rc"] == 0` に移っています。成功条件の緩和ではありません。
- TJ:1081、1319 の stock env 除去は裁定で要求された環境隔離です。
- TL／TV の既存 assert、fixture、skip の変更はありません。fixture 移動 fragment と既存 K2 pin も維持されています。

J の `${IZANAGI_S4_STOCK_CONTROL-0}` は未設定だけを 0 にし、空値を拒否します。stock argv の `-v` 判定より前に既存 K2 preflight が空値を拒否するため、空文字の宣言値を新たに通すことはありません。

既定 off 時、候補失敗の rc は OR-list 右辺で保存され、直後の off 分岐で同じ rc を `exit` します。成功時は初期値 0。EXIT trap に渡る rc、driver argv、stdout の追加有無は従来と整合します。失敗後に少数の shell 文を通る制御差はありますが、追加 driver や WAL 操作はありません。

pair の stdout 行は on 時だけです。compute-result は stdout を解析せず `$?` から生成するため干渉しません。提示資料にない外部 log consumer まで互換と認定はできません。

README の対象 qsub fence は 1 個で、TJ:1781–1806 の契約を維持しています。

TL:10160–10173 の plain harness は fixture を注入せず `fn()` を直接呼びます。新テストも既存 fixture 使用テストと同じく plain 実行には対応しません。`test_plain_runner_coverage.py:35–41` は harness の文字列 signal を確認するだけなので、その機械的契約には触れません。**meta-test の成功は TL の plain 実行成功を証明しません。** 今回は裁定どおり既存問題として扱えます。

## 報告件数の照合

AST で decorator のケース数を数えた結果です。pytest の実走確認とは区別します。

| 対象 | base | 新規関数／ケース | 統合後 |
|---|---:|---:|---:|
| TL | 509 | 19／41 | 550 |
| TJ | 82 | 5／25 | 107 |
| TV | 6 | 5／5 | 11 |

author 段階は resolver 負例の 1 件がまだないため TL は 549 件です。報告の **548 passed＋1 failed** と一致します。「TL 548 passed」を全緑として引用するのは誤りです。

fix1 はその失敗を解消し、負例を 1 件追加した **550 passed** と件数上整合します。新 test 名も author の 28 関数＋fix1 の 1 関数と一致します。

焦点走の 43 件、47 件については、報告本文に exact な `-k` 式／選択 node 一覧がないため、選択内容までは再構成できません。fix1 の `47＋503＝550` は整合します。実走成功や M15 の新旧差については報告上の主張であり、本レビューで再実証してはいません。

## 総括

**must-fix：0 件。GO。**

should は、既定候補 CLI の bytes 比較と、同 manifest テストの layout ID 観測の 2 件です。削る候補は lock 復元テストの重複実行だけで、裁定が削除指定した過剰要素は残っていません。

README は親の予定作業として未了です。file 変異 harness の実測、実 compiler での STOCK 成立、pair 測定成功は、この静的 GO の認定範囲に含みません。