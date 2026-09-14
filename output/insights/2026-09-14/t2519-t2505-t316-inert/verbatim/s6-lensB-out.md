## bytes 変更の波及

**実装子の5項目は正しいが、網羅ではありません。** 汎用 AST 検査、実行時間台帳、収集・並列実行の間接 consumer が抜けています。

- **commit 前の投入:** `.pbs:61–64` の BOUND_PATHS dirty 検査で `exit 3`。通常は SHA 比較より先に止まり、Python probe・新 receipt の生成まで進みません。dirty 検査を通る状態でも、`:69–75` の live／commit blob 不一致で拒否します。
- **commit 後の再投入:** 新 HEAD を `IZANAGI_T316_EXPECTED_COMMIT` に渡す必要があります。旧 commit 指定のままなら `.pbs:49` で拒否します。新 HEAD・clean・各 SHA 一致で初めて先へ進みます。新 receipt の commit と probe の `runtime_sha256` は新 identity になります。
- **Python 側:** `probe.py:2307` の `_execution_binding` も HEAD・dirty・runtime PBS を検査し、live bytes の digest を記録します。commit blob との全件比較を担うのは PBS 側です。
- **既存 receipt:** 実在する `900383`、`900427`、`996644` の3件は、それぞれ過去の commit／SHA を保持しています。今回の変更で過去観測として無効にはなりません。ただし、新実装の実測証拠には転用できません。
- **非 path キーによる参照:** `driver_id`、`SCHEMA_VERSION`、受理理由コード、`dispatch-required`、`primary_gate`、build sink の関数・行番号、`xdist_group`／`real-repo`／loadgroup を確認しました。登録簿・分類 golden・動的 AST inventory は存在しますが、今回ずれる t316 の絶対行番号を固定した現行 golden は見つかりませんでした。
- **履歴文書:** archive の行番号参照は当時の状態を記したものです。現在の行番号へ置換する必要はありません。

## 焦点走に含めるべき file

以下の test file はすべて `orchestrator/tests/` 配下です。親が実走済みの t316 file に加え、少なくとも次を焦点走へ含めるべきです。

| file | 到達経路・確認対象 |
|---|---|
| `test_ccbench_spawn_sites.py` | `_production_build_sources()` → `_define_sink_cross_product_failures()`。`tools/pegasus` を再帰走査し、helper 経由の condition gate と build sink を検査。**報告の重要な漏れ** |
| `test_hooks.py` | admission registry → 分類・primary gate の独立 golden／実行体 inventory |
| `test_official_perf_closure.py` | production 再帰走査 → `_scan_source()` → perf caller・guard inventory |
| `test_pytest_collection_config.py` | runner の収集・除外契約 |
| `test_acceptance_schedule_order.py` | conftest の duration lookup → loadgroup 順序・収集 identity・実台帳 coverage |
| `test_real_repo_serialization.py` | 実 collection → xdist group 契約・shard の group 保存 |
| `test_plain_runner_coverage.py` | test source → 自走 harness／README allowlist。実装子の3 node 成功報告あり |

docs 整合の実体検査は **`tools/check_docs.py`**、間接 consumer は `test_check_docs.py` です。`_check_pegasus_admission_docs_impl()` が登録簿と runbook の表を照合します。checker 自体を変更していないため、その合成負例全体の再走は優先度を下げられます。

`test_condition_meaning_gate.py` は呼出先 evaluator の契約確認として補助候補です。ただし gate 本体・共有 fixture は変更されず、他 driver の同名 `_require_condition_gate` は t316 helper の caller ではありません。同名だけを理由に全 driver test を焦点走へ追加する根拠はありません。

追加 node は duration 台帳に未登録です。`conftest.py:1722` で unknown となり、`:1738` 以降の既知コスト第96位相当を使う順序へ入ります。新しい xdist group や worker 数変更はありませんが、worker の占有時間と他 file の開始時刻には影響します。**5分以内かは file 単独走から判定できません。** 台帳へ数値を足す場合も、4.44秒という invocation 全体の時間を node duration として転記してはいけません。

## 追加 test の所要時間の説明

**この追加 test は CMake configure を2回実行しません。**

1. `test_t316_sandbox_probe.py:54` が requested source に `FATAL_ERROR` を追加。
2. `condition_meaning_gate.py:1889` の requested configure が実行される。
3. `_run_process()` の `:1611` 以降で非ゼロ終了を例外化し、`:1927` の捕捉へ移る。`:1894` の stock configure は未到達。
4. meaning は `:3339` の `declaration is None` で即時に record を返す。

したがって測っているのは、**実 configure 失敗 → supply 赤 → family 拒否 → detail の stderr 出力**です。test は witness 文字列、rc、argv、従来の例外文言を検査しており、目的の拒否経路を通らない偽緑を示す証拠はありません。

4.44秒と4.61秒は別 invocation の総時間なので、差の0.17秒を「残り144件の所要時間」とは読めません。収集・初期化・環境差を含みます。また既存 test の実 gate helper には `lru_cache` があります（`:186`、`:282`）。正確な内訳は未提示ですが、**2回 configure という前提による時間上の矛盾は解消します**。

## docs 整合

今回の診断出力追加によって更新が必要な repo docs は見つかりませんでした。

`docs/pegasus-runbook.md:541–542` の分類は引き続き `dispatch-required`。登録簿の static classification と一致します。receipt schema・比較 field・受理契約を変えていないため、D1849 等の改訂も不要です。

実装子報告の `s5-author-out.md:38–41` は現物と一致します。`:42` の検査経路列挙には上記メタ検査・台帳経路が不足していますが、虚偽の成功報告ではありません。「CMake 2回」は実装子報告には書かれておらず、依頼側の前提の訂正です。

## must-fix

**成果物の値・受理集合・参照を壊す実装欠陥は、本レンズでは確認できませんでした。**

nit：`s5-author-out.md:42` の波及列挙を補完し、親の焦点走へ特に `test_ccbench_spawn_sites.py` と収集・スケジュール検査を追加してください。未実走という事実だけを、成果物破損の must-fix には格上げしません。

## 成立しなかった攻撃

- 短時間だから実 CMake を通っていない、という攻撃。requested configure の故意の失敗で説明できます。
- probe の bytes 更新で既存 receipt が一律失効する、という攻撃。過去 identity の観測として残ります。
- 行番号移動が t316 の現行 golden を壊す、という攻撃。汎用検査には行番号照合がありますが、t316 の該当 pin は確認できません。
- fixture 汚染・新 group による他 file の直列化。コピー先だけを変更し、group 追加もありません。
- 分類表・schema・受理理由コードの更新漏れ。対応する契約は変更されていません。

## 総括

実装の must-fix はなし。波及列挙には汎用メタ検査と duration／collection 経路の漏れがあります。  
追加 test は requested configure 1回の拒否経路を検査し、所要時間から偽緑とは判断できません。  
本レビューは静的検査のみです。焦点走の補完と新 commit 束縛による別観測は親に残ります。