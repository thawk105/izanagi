# 段 4 裁定 — [T-2401] 評価器例外の理由を fail-closed のまま構造化して残す

親が段 2 プランと段 3 レンズ A / B の所見を real / refuted、採用 / 不採用、scope 内 / 外で裁定する。

## 所見の裁定

### レンズ A

| 所見 | 判定 | 採否 | 裁定 |
|---|---|---|---|
| A1 受理集合は広がらない | real | 追認 | 骨格は成立。不変条件として維持する。 |
| A2 materialize を try 外へ出すと遅延例外が漏れる | real | 採用 (実装制約) | `_normalize_predicate_results(raw)` の**呼び出し全体**を第 2 try の内側に置く。`tuple(raw)` 等の materialize を 2 つの try の間へ出してはならない。 |
| A3 遅延 generator の callsite は normalize 側に寄る | real | 採用 (docstring) | `callsite` は「例外の意味上の発生源」ではなく**捕捉した評価地点**であると docstring に明記する。コードは変えない。 |
| A4 sibling API は capability 迂回路にならない | real | 追認 | production sibling へ registry を露出しない。 |
| A5 gate report の防壁は弱まらない | real | 追認 | `s8c_gate_report.py` は変更しない。 |
| A6 「台帳が全件不一致」は過大 | **real・親 brief の誤り** | 採用 (訂正) | 正しくは「**非 null の activation digest を束縛した registered-effective の成果物**が不一致になる」。exploratory と formal non-certifying は digest が `None` なのでこの理由では変わらない。段 7 の記録でこの訂正を書く。**不変条件 2 (field を増やさない) 自体は変わらない。** |
| A7 module blob 変更と source closure | real・ただし新規作業なし | 採用 (確認のみ) | `s8c_preregistration.py` は `CONTRACT_LOADER_RELATIVE_PATHS` (exact 63 path の enforcement source closure) に含まれる。path 集合は増減しないので pin 更新は不要。blob 束縛は commit blob と live bytes の**照合**であり literal pin ではない (親の実測でも literal hash pin は hit 0 件)。**帰結として、実装は段 6 の子を起動する前に親が commit する必要がある** (未 commit だと `contract-loader-drift` で偽赤・子が rc=2)。 |
| A8 他の `_canonical_bytes` preimage は不変 | real | 追認 | 独立 dataclass の追加は freeze / protected digest を変えない。 |
| **A9 診断抽出が total でない (blocker)** | **real** | **採用** | 下記「設計 v2」の 1 と 2。 |
| **A10 `PreregistrationError.reason` は型も語彙も無検査 (blocker)** | **real** | **採用** | 下記「設計 v2」の 2 と 3。 |
| A11 規律 2 は緩まない | real | 追認 | |
| A12 異常例外まで含めた規律 3 は A9/A10 解決が前提 | real | 採用 | A9/A10 を解けば閉じる。 |
| A13 内側 evaluator の catch-all は対象外 | real | 追認 (scope 外) | |

### レンズ B

| 所見 | 判定 | 採否 | 裁定 |
|---|---|---|---|
| **B1 プランの fixture は到達しない (blocker)** | **real (親も独立に実測)** | **採用** | `_default_registry_module` は evaluator を module 名で live import し、その実 file の bytes が commit blob と一致することを要求する。tiny repo 側だけ 11 件版へ差し替えると `evaluator-blob-mismatch` に倒れ、目的の経路へ到達しない。 |
| B2 到達可能な構成 2 案 | real | **採用 (実 process 方式を主、直接呼び出しを従)** | 下記「設計 v2」の 5。**monkeypatch は使わない** (`DW-O14`: 正規注入 seam が実在する)。 |
| B3 二層 stub を避けよ | real | 採用 | 実体を通す。 |
| B4 正常系の「診断は空」assertion が無い | real | 採用 | 下記「設計 v2」の 6。 |
| B5 `str(exc)` 代入の変異が殺せない | real | 採用 | detail 付き `PreregistrationError("fixture-reason", "secret-detail")` を evaluator から送出する負例を足し、**detail が診断に現れないこと**を固定する。 |
| B6 診断を無効化・虚偽化できる変異 3 件 | real | 採用 | 下記「変異事前登録」の D1〜D6。 |
| B7 `test_non_json_cli_reports_decider_reason` の seam 追随 | real | 採用 | monkeypatch 対象を新関数へ合わせ、返り値を `(report, ())` にする。**exit code と stdout の期待値は 1 文字も変えない。** これは期待値の変更・反転・緩和ではなく collaborator seam の追随である。 |
| B8 他の既存 test は壊れない | real | 追認 | |
| B9 `s8c_gate_report` CLI では閉じない | real | **scope 外** | F631 の事故コマンドは判定器 CLI (`s8c_preregistration.py`) であり、そこは閉じる。gate report への診断露出は同型の catch の修正ではなく**機能追加**なので、本 wave の「本題の実装だけ」に入れない。段 7 で次の一手へ登録する。`--json` の stdout だけを保存する利用者に届かない点も同じ扱いとし、stdout の形は変えない (不変条件 3)。 |
| B10 test-registry 経路は過大 | **real だが不採用** | **不採用 (含める)** | 除くと、その分岐は例外を握り潰したまま診断を空で返す。**「診断が空 ⟺ 例外を握り潰していない」という不変条件が壊れ、channel 自体が黙って不完全になる。**これは成果物影響を書ける: 診断が空であることを根拠に「評価器例外は起きていない」と読んだ人間が、実際には握り潰された例外を見落とす。よって含める。代わりに B6 が要求する assertion を必ず足す。 |
| B11 不足している assertion 群 | real | 採用 | 下記「設計 v2」の 6。 |
| B12 内側 catch-all は scope 外 | real | 追認 | |

## 設計 v2 (確定)

段 2 プランの骨格 (report 不変 + sibling API + stderr) を採用し、次を上書きする。

1. **診断抽出 helper は total にする。** 例外 object から値を取り出す全処理を自身の `try` で囲み、
   何が起きても `EvaluatorExceptionReason` を必ず返す。**診断生成が原因で例外が外へ漏れてはならない。**
   取得不能なら固定の sentinel を使う。fail-closed の返却契約 (12 件の `ERROR` report を返す) を、
   診断の追加で 1 経路たりとも未処理例外に変えない。
2. **診断の 3 field はすべて「安全な文字列」に正規化する。**
   - `callsite`: 実装が与える固定 literal のみ (`"default-registry.evaluate_all"` /
     `"_normalize_predicate_results"` / `"test-registry.evaluate_all"` /
     `"test-registry._normalize_predicate_results"`)。外部由来の値を入れない。
   - `exception_type`: `type(exc).__name__` が `str` で、保守的な charset (ASCII 英数と `_`) と
     長さ上限に収まるときだけ採用。それ以外は固定 sentinel。
   - `preregistration_reason`: `isinstance(exc, PreregistrationError)` かつ `exc.reason` が `str` で
     保守的な charset (ASCII 小文字・数字・ハイフン) と長さ上限に収まるときだけ採用。
     それ以外 (非 str、path や環境値を含む、長すぎる) は固定 sentinel。`PreregistrationError` でなければ `None`。
   - **`str(exc)`、detail、message、traceback、repo path、環境値は 1 つも入れない。**
3. **sentinel は reason_code 語彙ではない。** `ReasonCode` enum と `REASON_CODES` を拡張しない。
   sentinel は診断専用の固定文字列とし、`reason_code` として使わない。
4. **`ActivationReport` / `PredicateResult` / `EvidenceRef` の field は増減しない** (不変条件 2)。
   診断は独立 frozen dataclass の immutable tuple として、report と並ぶ第 2 返り値に置く。
   module 大域の可変状態・`contextvars`・logging は使わない。
5. **到達方法。**
   - **実 process (CLI e2e、主):** temporary repo に**変更後の** core・projection・**11 件しか返さない
     evaluator** を同じ bytes で配置して commit し、`cwd=<temporary repo>` で
     `-m orchestrator.campaign.s8c_preregistration` を、および temporary repo 側の core file path 直接起動で
     CLI を走らせる。core・evaluator・projection の live bytes と commit blob が全部一致するので
     `_default_registry_results` と実体の `_normalize_predicate_results` に到達する。
   - **直接呼び出し (単体、従):** `_default_registry_results(root, commit, module)` の `module` 引数は
     設計上の正規注入 seam である。ここへ module 様 object を渡す形は monkeypatch ではない。
     実体の `_normalize_predicate_results` と診断 helper を通す。
   - **monkeypatch は使わない** (`DW-O14`)。
6. **必須 assertion (すべて純増。既存の期待値は変えない)。**
   - 負例: 12 件すべて `status is ERROR`、`reason_code == "evaluator-exception"`、`evidence == ()`、
     `effective is False`。同じ commit の plain `activation_report_at` の report と
     `_jsonable` / `_activation_report_digest` が診断の有無で完全一致。
   - 正例 (normalize 側): `callsite == "_normalize_predicate_results"`、
     `exception_type == "PreregistrationError"`、`preregistration_reason == "predicate-result-type"`。
   - 正例 (evaluator 側): evaluator が `RuntimeError` を直接送出する場合に
     `callsite == "default-registry.evaluate_all"`、`exception_type == "RuntimeError"`、
     `preregistration_reason is None`。
   - detail 非漏出: evaluator が `PreregistrationError("fixture-reason", "secret-detail")` を送出する場合に
     `preregistration_reason == "fixture-reason"` であり、診断のどの field にも
     `"secret-detail"` が現れない。
   - 異常例外の total 性: `reason` 属性が無い / 非 str の `PreregistrationError` subclass、および
     `reason` に path 様の値を入れた場合に、**例外が漏れず** 12 件の `ERROR` report が返り、
     診断が sentinel になる。
   - 正常系: 例外の無い commit で診断 tuple が `()` であり、CLI の stderr が完全に空である。
   - CLI: `--json` / 非 `--json`、path 形式 / module 形式で stdout bytes が現行と完全一致、
     終了値は現行どおり、stderr は診断 1 行の JSON object だけ、
     `"Traceback"` と temporary repo path が stderr に無い。
   - test-registry 経路: 例外を握り潰したときに診断が空でないこと。
   - field 集合 pin: `ActivationReport` / `PredicateResult` / `EvidenceRef` の field 名集合を現行どおり pin。
   - 新 sibling API に `registry` 引数が無いこと。
7. **新規 test file を作らない。** 追記先は
   `orchestrator/tests/test_s8c_cli_entrypoints.py` と
   `orchestrator/tests/test_s8c_preregistration_core.py`。

## 変異事前登録 (`DW-M01`、実装前登録)

`DW-M08` により、本 wave は**受理集合を変えず構造化シグナルを足す**型なので、
変異を 2 枠に分けて登録する。単一理由性は実装後に確認する。

### 枠 1: 受理集合の変異 (期待 KILLED)

| ID | 位置 | 変異 | 期待 |
|---|---|---|---|
| M1 | `_default_registry_results` の fallback | `PredicateStatus.ERROR` → `PredicateStatus.SATISFIED` | KILLED (負例の status assertion) |
| M2 | 同上 | `"evaluator-exception"` → `"evaluator-internal-error"` | KILLED (負例の exact reason_code) |
| M3 | 同上 | `_normalize_predicate_results` 呼び出しを外し raw を返す | KILLED (12 件・型 assertion) |

### 枠 2: 診断感度 pin (`DW-M08` の別枠。kill と数えない)

| ID | 位置 | 変異 | 検出する assertion |
|---|---|---|---|
| D1 | 診断 helper | 常に空 tuple を返す | 正例 2 種 |
| D2 | 診断 helper | 全例外に F631 の固定 3 値を返す | evaluator 側 `RuntimeError` の正例 |
| D3 | 診断 helper | `exc.reason` の代わりに `str(exc)` を入れる | detail 非漏出 |
| D4 | `_default_registry_results` | 両 callsite を同じ literal にする | callsite 2 種の正例 |
| D5 | `_activation_report_at` | 例外が無くても診断を 1 件返す | 正常系の空診断・空 stderr |
| D6 | test-registry 分岐 | 診断を常に空にする | test-registry の assertion |
| D7 | CLI `check` | 診断を stdout へ出す / JSON separator・改行を変える | stdout bytes 完全一致 |
| D8 | 診断 helper | total 化の `try` を外す (異常例外で送出させる) | 異常例外の total 性 |

## 実装単位と順序

- 実装単位は 1 つ (P4 のとおり素集合に割れない)。並列分割しない。
- **順序制約 (A7 由来、`DW-STOP` 級):** `s8c_preregistration.py` は HEAD blob 束縛の
  enforcement source closure に含まれるため、**段 5 の実装後、段 6 の子を起動する前に親が統合 commit する。**
  未 commit のまま段 6 を起動すると `contract-loader-drift` で偽赤になり、codex 子は rc=2 で死ぬ。

## 不変条件 (再掲・段 5 の停止条件)

1. 受理集合を 1 bit も広げない。
2. `ActivationReport` / `PredicateResult` / `EvidenceRef` の field を増減しない。
3. CLI `check` の stdout の形と bytes を変えない。
4. stderr に traceback・message・detail・repo path・環境値を出さない。
5. 新規 file を足さない。
6. 自由文を `reason_code` へ入れない。`ReasonCode` / `REASON_CODES` を拡張しない。
7. 診断の追加によって、現行 `ERROR` を返す経路が未処理例外に変わらない。
