## 所見ごとの対応表

| 対象 | 判定 | 根拠 |
|---|---|---|
| A1 | `partial` | sentinel 偽装は、両 sentinel を受理域外へ移した `s8c_preregistration.py:67-73` と直接 assertion `test_s8c_preregistration_core.py:2896-2902` で閉じた。一方、許可文字内の外部由来 reason は `s8c_preregistration.py:1812-1825` で引き続き受理され、これは裁定済み scope 外。 |
| A2 | `scope 外 (裁定済み)` | outer catch の `print(str(exc), file=sys.stderr)` は維持されている。`s8c_preregistration.py:2360-2362`。 |
| A3 | `partial` | 現実装は診断 loop 全体を `except Exception` で隔離し、stdout は範囲外。`s8c_preregistration.py:2327-2351`。OSError 負例もあるが `test_s8c_cli_entrypoints.py:634-671`、catch を `OSError` へ狭める新しい生存変異が残る。 |
| B1 | `partial` | S1/S2 の exact 変異は、ValueError 直送 `test_s8c_preregistration_core.py:2722-2737` と遅延 TypeError `:2686-2701` で閉じた。両例外は `PreregistrationError` の基底 RuntimeError `s8c_preregistration.py:140-145` とは別系統。ただし、テスト済み例外だけを列挙する catch 変異は生存する。 |
| B2 | `partial` | live evaluator の RuntimeError fixture `test_s8c_cli_entrypoints.py:70-95,228-277` と、path/module・text/json の exact stderr assertion `:588-631` により S3 は閉じた。ただし例外型による選択的な CLI 診断破棄は生存する。 |
| B3 | `partial` | 比較演算子 S4/S5 と charset S6 は `test_s8c_preregistration_core.py:2830-2893` で閉じた。しかし入力長が production 定数から自己参照生成されており、定数自体の変更は生存する。 |
| S1 | `closed` | evaluator 側を RuntimeError catch に狭めると ValueError が `s8c_preregistration.py:1925-1936` から漏れ、`:2722-2737` が失敗する。 |
| S2 | `closed` | normalize 側を RuntimeError catch に狭めると遅延 TypeError が `s8c_preregistration.py:1937-1948` から漏れ、`:2686-2701` が失敗する。 |
| S3 | `closed` | evaluator callsite の診断を捨てると CLI の exact stderr `test_s8c_cli_entrypoints.py:631` が失敗する。 |
| S4 | `closed` | reason の `<=` を `<` にすると、128 文字として生成された値の受理 assertion `test_s8c_preregistration_core.py:2833,2870` が失敗する。 |
| S5 | `closed` | exception type の `<=` を `<` にすると `test_s8c_preregistration_core.py:2835,2874` が失敗する。 |
| S6 | `closed` | reason regex に `_` を足すと `fixture_reason` の sentinel assertion `test_s8c_preregistration_core.py:2880-2893` が失敗する。 |

`regressed` と判定した既存所見はない。ただし、A3・B1・B2・B3は別形の生存変異が残るため、root cause 全体を closed とは判定しない。

## 裁定外の変更

- 所見 1 (深刻度: must-fix): fix commit は裁定が指定した3ファイル以外に `orchestrator/tests/README.md` を変更し、pytest-only allowlist から `test_s8c_preregistration_core.py` を削除している。差分位置は `orchestrator/tests/README.md@134e5926d:181`、現行側の削除位置は `:180`。段6裁定の fix scope 1〜3には、この allowlist 編集は含まれていない。
  成果物影響: 診断修正とは独立に test runner の分類対象が変わるため、commit `8789ea89a` は裁定どおりの変更集合ではない。

それ以外の production 変更と、指定2 test fileへの追加は scope 1〜3に対応している。

## 不変条件の再検査

| 不変条件 | 静的判定 | 根拠 |
|---|---|---|
| 1. 受理集合を広げない | 成立 | evaluator fallback は引き続き12件の `ERROR / evaluator-exception`。`s8c_preregistration.py:1927-1948`。fix は受理 regex や report 判定を変更していない。 |
| 2. report系 fieldを増減しない | 成立 | field集合 assertionは維持されている。`test_s8c_preregistration_core.py:2611-2645`。診断は独立 dataclass。 |
| 3. CLI stdout bytesを変えない | 成立 | stdout生成は `s8c_preregistration.py:2327-2336`、追加 try はその後の stderr loopだけ。exact stdout assertionは `test_s8c_cli_entrypoints.py:626-631,667-671`。 |
| 4. 新診断へ危険 payloadを出さない | 裁定の範囲で成立 | sentinel は受理域外 `s8c_preregistration.py:67-73`。診断 helper は正規化済み3 fieldだけを返す `:1786-1834`。outer catch は裁定済み scope 外。 |
| 5. 新規 fileを足さない | 成立 | commit は既存4ファイルの変更だけ。ただしREADME変更は別途 scope 違反。 |
| 6. reason_code語彙を広げない | 成立 | sentinel は診断 fieldだけで使われ、fallback reason_code は従来の `"evaluator-exception"`。`s8c_preregistration.py:1929,1941`。 |
| 7. 診断追加でfail-closed終端を例外化しない | 現実装は成立、テスト感度は不十分 | evaluator/normalize は `Exception` を捕捉し `:1925-1948`、診断出力も `Exception` を捕捉する `:2337-2350`。ただし下記のcatch狭窄変異が生存する。 |

sentinel 変更は `reason_code` へ流れず、既存 assertion の期待値にも影響していない。

追加負例は本当に RuntimeError 系以外である。`ValueError` は `test_s8c_preregistration_core.py:2728`、`TypeError` は遅延 materialize 内の `:471-484` で送出される。`PreregistrationError` は明示的に RuntimeError subclass `s8c_preregistration.py:140` であり、これらとは異なる。

追加した `except Exception` は `s8c_preregistration.py:2337-2350` の診断 JSON 化・stderr printだけを囲む。stdout print `:2327-2336` は巻き込まれていない。通常の診断 tupleは固定 dataclassの0件または1件なので、本来出る診断が通常経路で消える新経路は見つからない。JSON化・stderr書込みそのものが例外になった場合の消失は、裁定が要求した終端保全に該当する。

## 新しい生存変異

以下は、射影された2 test fileの assertionを静的にはすべて通しながら、要求された性質を破壊できる。

| ID | 位置と変異 | 生存理由と破壊内容 |
|---|---|---|
| S7 | `s8c_preregistration.py:69` の `128` を `127` または `129` に変更 | 境界入力がすべて同じ定数から生成される。`test_s8c_preregistration_core.py:2833-2836`。128/129という裁定値を虚偽化できる。 |
| S8 | `s8c_preregistration.py:1927` を `except (RuntimeError, ValueError)` に狭める | evaluator側の全負例を捕捉できるため生存するが、KeyError等でfail-closed reportが返らない。 |
| S9 | `s8c_preregistration.py:1939` を `except (RuntimeError, TypeError)` に狭める | 現在のnormalize負例をすべて捕捉するが、遅延 iterable のKeyError等が漏れる。 |
| S10 | test-registry evaluator catch `s8c_preregistration.py:1983` を `except RuntimeError` に狭める | test-registry負例はRuntimeErrorだけ。`test_s8c_preregistration_core.py:2916-2954`。ValueError等でtotalityを破壊できる。 |
| S11 | test-registry normalize catch `s8c_preregistration.py:1994` を `except RuntimeError` に狭める | 現行負例はPreregistrationErrorなので通る。遅延TypeError等が漏れる。 |
| S12 | exception type抽出の `except BaseException` `s8c_preregistration.py:1805` を `except SystemExit` に狭める | hostile type testが送出するのはSystemExit `test_s8c_preregistration_core.py:507-515`。KeyboardInterrupt等を送出するmetadataでhelperのtotalityを破壊できる。 |
| S13 | reason抽出の `except BaseException` `s8c_preregistration.py:1827` を `except (AttributeError, SystemExit)` に狭める | 現行の欠落属性とhostile propertyを両方捕捉するが、それ以外のBaseExceptionを漏らせる。 |
| S14 | CLI出力の `except Exception` `s8c_preregistration.py:2348` を `except OSError` に狭める | 追加負例はOSErrorだけ `test_s8c_cli_entrypoints.py:646-650`。stderr.writeがValueError等を出すと終了値が未処理例外へ変わる。 |
| S15 | `s8c_preregistration.py:2338` で `exception_type == "ValueError"` の診断だけskipする | CLI e2eはPreregistrationErrorとRuntimeErrorだけ `test_s8c_cli_entrypoints.py:86-95`。ValueErrorの単体 test `test_s8c_preregistration_core.py:2722-2737` はCLIを通らないため、CLI診断だけ無効化できる。 |

- 所見 2 (深刻度: must-fix): 128/129境界 testがproduction定数をoracleとしており、裁定された数値を固定していない。
  成果物影響: 128文字の正当な理由をsentinelへ虚偽化、または129文字の不正値を診断へ受理できる。

- 所見 3 (深刻度: must-fix): evaluator、normalizer、test-registry、診断helper、CLI出力のcatch集合は、テスト済み例外だけを列挙する狭窄変異が生存する。
  成果物影響: 未試験の例外種で12件のfail-closed reportまたは定義済みCLI終了値が返らず、成果物生成が未処理例外になる。

- 所見 4 (深刻度: must-fix): evaluator側CLI到達は固定されたが、CLI fixtureの例外型がRuntimeErrorだけなので、ValueError診断を選択的に捨てる変異が生存する。
  成果物影響: reportは拒否のままでも、ValueError時の診断成果物が黙って欠落する。

## 既存テストの弱体化

既存 assertion の変更・反転・緩和・skip・削除はない。fix commitの指定2 test fileは純増で、`test_s8c_cli_entrypoints.py` は204行追加・削除0、`test_s8c_preregistration_core.py` は127行追加・削除0である。

README allowlistの削除はassertion弱体化ではないが、裁定外変更として前記所見1に分離した。

## scope 外の所見

- 所見 5 (深刻度: must-fix): A1のうち、許可文字と長さに収まる外部由来reasonの機密性・由来保証は裁定済みscope外のまま残る。`s8c_preregistration.py:1812-1825`。
  成果物影響: 許可文字だけで構成された外部値は診断参照へ残り得るが、本fixでは変更しない裁定である。

- 所見 6 (深刻度: must-fix): A2のouter catchは引き続き `str(exc)` をstderrへ出す。`s8c_preregistration.py:2360-2362`。段6裁定でscope外。
  成果物影響: fatal error時のstderrにはdetail、repo path、環境依存messageが混入し得る。

新たなscope外所見はない。

## 総括

静的再レビュー結果は、scope内で blocker 0、must-fix 4。S1〜S6のexact変異はすべて閉じたが、A3・B1・B2・B3の根本的なテスト感度はpartialであり、新しい生存変異S7〜S15がある。加えて、commit `8789ea89a` には裁定外のREADME allowlist変更が1件含まれる。

したがって、fix後差分はまだ受理できず、「root causeが閉じた」とは判定しない。pytestは実走しておらず、本結論は指定資料とcommit差分による静的検査である。