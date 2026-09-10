静的検査のみであり、pytest は実走していない。実装 gate の順序自体は成立しているが、変異検査に must-fix が 2 件ある。

## 所見 1

所見: M2 の指定テストは equality の欠落を殺さない。`test_land_rejects_child_green_runner_blob_divergence` は tip digest を受領証へ入れているため、child-green の equality を非帰属枝へ戻しても、その直後の main digest 検査が拒否を先取りする。

根拠: fixture は tip digest を選ぶ (`orchestrator/tests/test_dev_wave_land.py:1537`, `:1540`)。実装は equality の後で受領証 digest を main blob と比較する (`tools/dev_wave_land.py:1084`, `:1085`)。したがって equality を `verdict == "non-attributable-only"` で条件付ける M2 でも、child-green は main digest 不一致で同じ `acceptance-receipt-rejected` になる。テストは内部拒否理由を区別しない (`orchestrator/tests/test_dev_wave_land.py:1558`)。これは裁定の「tip digest なら digest 検査で拒否されない」という説明 (`s4-adjudication.md:129`, `:152`) と、main digest 照合契約 (`s4-adjudication.md:97`) の矛盾でもある。

影響: equality gate が消えても M2 検査が緑になり、land の独立 equality 保証を証明できない。

判定: must-fix。

成果物影響: 未検出の M2 回帰では、main digest を自称する divergent child-green receipt が受理集合へ入り、certified な選択結果・材料レポート・試行台帳の着地根拠参照が、実際に走った tip runner と一致しない receipt SHA へ変わる。

推奨対応: このテストだけは `runner_digest_revision=repo.base` とし、main digest を自認した divergent receipt を作る。これにより equality を外した変異だけが land まで通る。裁定の tip digest 指示も同時に訂正する。

## 所見 2

所見: M5 の指定正例は `locked_main` と `tested_main` が同じなので、`tested_main` を `locked_main` へ置換する変異を殺さない。

根拠: テストは runner に触れない tip を作るだけで main を進めておらず (`orchestrator/tests/test_dev_wave_land.py:1566`)、tested main は既定の `repo.base`、着地前の locked main も同じ `repo.base` である。期待 lookup も `[tip, repo.base]` (`orchestrator/tests/test_dev_wave_land.py:1586`) なので、`tools/dev_wave_land.py:1066` の引数を `locked_main` に変えても値も結果も変わらない。land が verifier へ渡す値は `preflight.locked_main` である (`tools/dev_wave_land.py:5041`)。なお `test_land_runner_gate_uses_tested_main_after_main_reaches_tip` (`orchestrator/tests/test_dev_wave_land.py:1749`) は別途 M5 を殺しうるが、事前登録された指定テストではない。

影響: M5 の事前登録表が主張する過剰拒否検出を、指定正例は提供しない。

判定: must-fix。

成果物影響: 未検出の M5 回帰では、tested pair の runner が一致していても locked main だけ更新された receipt が受理集合から脱落し、certified 結果は未着地となり、レポート・台帳の land status と着地参照が欠落する。

推奨対応: `locked_main != tested_main` かつ locked main の runner だけが異なる正例を、可能なら `_verify_acceptance_receipt` の直接テストとして作り、tested main/tip の receipt が受理されることと exact lookup を確認する。

## 所見 3

所見: 追加・改名された 8 テストは、実装全体を旧状態へ戻した場合にはすべて赤になる。完全 rollback に対する偽の緑はない。

根拠:

| テスト | 旧実装で赤になる理由 |
|---|---|
| `test_matching_main_and_tip_runner_blobs_execute_tested_main_source` | 旧 launcher は tip, tip の 2 回読取で、期待する main, tip, main と一致しない (`test_acceptance_launcher.py:125`) |
| `test_main_tip_runner_blob_mismatch_is_rejected_before_execution` | 旧 launcher は比較せず `_unreachable` runner を呼ぶ (`test_acceptance_launcher.py:149`) |
| `test_missing_tested_main_runner_is_rejected_before_execution` | 旧 launcher は main を読まず runner へ到達する (`test_acceptance_launcher.py:169`, `:180`) |
| `test_missing_tested_tip_runner_is_rejected_before_execution` | 旧 launcher は最初に tip だけを読み、期待順 `[main, tip]` に反する (`test_acceptance_launcher.py:220`) |
| `test_land_rejects_child_green_runner_blob_divergence` | 旧 child-green は tip digest だけで着地する (`test_dev_wave_land.py:1558`) |
| `test_land_accepts_child_green_matching_main_and_tip_runner_blobs` | 旧 land は main lookup をせず、spy の期待に反する (`test_dev_wave_land.py:1586`) |
| `test_land_child_green_runner_path_absence_is_permanent_rejection` | 旧 child-green は欠落した main runner を読まず着地する (`test_dev_wave_land.py:1668`) |
| `test_land_child_green_runner_lookup_process_failure_is_retryable` | 旧 child-green は tested-main lookup 自体を行わない (`test_dev_wave_land.py:1739`) |

影響: 完全 rollback の検出力はある。ただし M2 のような部分変異には所見 1 の穴が残る。

判定: nit。

推奨対応: rollback 表と変異表を別物として扱い、「旧実装で赤」を M2 の証明に数えない。

## 所見 4

所見: `runner_digest_revision` の各指定を 1 件ずつ追うと、中心負例以外にも旧実装で通る互換テストがある。これらを新 gate の検出テストへ数えてはならない。

根拠:

- child-green divergence (`test_dev_wave_land.py:1537`): 完全 rollback は殺すが、M2 は main digest 検査に先取りされる。
- matching child-green (`:1574`): main/tip が同じ blob なので digest revision は結果へ影響しない。main lookup の存在だけを検出する。
- non-attributable divergence (`:1602`): 旧実装にも非帰属 equality があり、旧実装のまま通る負例。
- non-attributable main absence (`:1631`): 旧実装にも非帰属 main lookup があり、旧実装のまま通る負例。
- child-green main absence (`:1663`): 旧実装は着地するため、新しい共通 main lookup を正しく検出する。
- main reaches tip (`:1762`): 旧実装も tested main を非帰属枝で引くため、旧実装のまま通る。ただし M5 の別検出にはなる。
- E2E の runner を main commit へ移した変更 (`:1951`): 新旧双方で通る互換正例であり、裁定どおり実装差は検出しない。

影響: テスト数をそのまま検出 gate 数として数えると、検出力を過大評価する。

判定: nit。

推奨対応: 検証一覧で「新 gate 検出」「既存保証維持」「互換正例」を明示的に分ける。

## 所見 5

所見: 実環境で恒真となる追加条件が 1 個ある。main runner object ID の SHA 形式再検査は発火不能である。

根拠: `_runner_tree_entry` は object ID が 40 桁または 64 桁の小文字 hex に一致した場合だけ tuple を返す (`tools/dev_wave_land.py:838`, `:843`)。したがって返却後の `_SHA_RE.fullmatch(main_runner_entry[1]) is None` (`tools/dev_wave_land.py:1082`) は、実 helper 経由では決して真にならない。

影響: 実際の受理集合は変えないが、独立した拒否 gate が 1 個あるように見える。

判定: nit。

推奨対応: 冗長条件を削るか、helper が既に object ID 形式を保証している旨を明記し、独立 gate や被覆対象として数えない。

## 所見 6

所見: launcher に suite 起動の順序穴は見つからない。main、tip の読取と bytes equality が完了するまで `blob_runner` は呼ばれない。

根拠: main 読取、tip 読取、比較は `tools/acceptance_launcher.py:436`, `:437`, `:438`、runner 呼出しはその後の `:441`。実行 buffer の identity も `test_acceptance_launcher.py:127` で main 由来に固定される。実行後の 3 回目は main の再取得 (`acceptance_launcher.py:446`) で、M3 テストは main, tip, main を確認する (`test_acceptance_launcher.py:259`)。

影響: main/tip 不一致または両 revision の読取例外から suite が起動する経路は静的にはない。

判定: nit。

推奨対応: 順序変更は不要。負例へ `not config.log_file.exists()` を足すと、suite 前に log を作らない境界も明示できる。

## 所見 7

所見: 新変更に起因する資源リークは見つからないが、実 production reader と一部 fail-closed 分岐は直接テストされていない。

根拠: runner log は context manager で閉じられ、signal handler も finally で復元される (`tools/acceptance_launcher.py:213`, `:230`)。receipt fd も finally で閉じる (`:421`)。outcome/completion fd は launcher が開いたものではなく、CLI 終了時に process が閉じる。suite 後の M3 失敗では log は残るが receipt は空のままである (`test_acceptance_launcher.py:260`)。一方、missing main/tip テストは fake reader 自身が例外を投げており (`:169`, `:200`)、実 `_read_runner_blob` の Git 非ゼロ分岐 (`acceptance_launcher.py:194`) は通らない。land の tested-main `ls-tree` malformed-output 分岐 (`tools/dev_wave_land.py:843`) も未検査である。

影響: 中心 gate は被覆されるが、Git subprocess 接続と malformed 出力時の permanent/retryable 分類には実行証拠がない。

判定: nit。

推奨対応: actual `_read_runner_blob` を使う main 欠落・tip 欠落テストと、main lookup に malformed `ls-tree -z` を返す permanent-rejection テストを追加する。

## 所見 8

所見: M1、M3、M4 は指定テストが殺す。裁定で禁じた変更も見つからない。

根拠: M1 は equality を runner 後へ移すと `_unreachable` が発火する (`test_acceptance_launcher.py:149`)。M3 は期待 revision 順と main buffer identity の双方で tip 読取への退行を殺す (`:125`, `:127`)。M4 は tip 例外を main bytes で代用すると `_unreachable` runner が発火する (`:202`, `:211`)。差分は指定 4 ファイルだけで、schema は v5 のまま (`tools/acceptance_launcher.py:22`, `tools/dev_wave_land.py:94`)、`_run_blob` の interpreter は `python3` のまま (`acceptance_launcher.py:216`)。waiter、xfail、root field、retryable の新 rc・理由変更はない。fixture の既定も tip のままである (`test_dev_wave_land.py:356`)。

影響: M2、M5 以外の事前登録変異と禁止変更について、静的な契約違反は見つからない。

判定: nit。

推奨対応: M1、M3、M4 は現状維持。M2 と M5 の修正後に親が実走する。

## 総括

- must-fix は 2 件: M2 が main digest 不一致に先取りされること、M5 正例で locked main と tested main が同値なこと。
- 実装本体の launcher equality は suite 前に発火し、main 由来 buffer だけを実行する。
- land 本体も全 verdict で main/tip を取得し、child-green divergence を拒否する。
- 追加・改名 8 テストは完全 rollback をすべて検出するが、部分変異 M2 の証明にはならない。
- main object ID の SHA 再検査は helper の事後では恒真である。
- production Git reader と malformed main lookup は未実走・未検査である。
- schema、interpreter、waiter、xfail、fixture 既定、retryable 契約への禁止変更は見つからない。
- pytest は実走しておらず、以上はすべて静的判定である。