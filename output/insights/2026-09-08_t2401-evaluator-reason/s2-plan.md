## 現行挙動

対象は brief が列挙した `except` と、その直前後で結果を決める節に限定した。

- `orchestrator/campaign/s8c_preregistration.py:1779-1788`
  - `except ModuleNotFoundError as exc` が捕捉するのは、`importlib.import_module` が送出した `ModuleNotFoundError` とその subclass だけ。
  - `exc.name` が evaluator module 自身または top-level package の場合は `module is None` の分岐へ進み、12 件すべて `EVIDENCE_UNDEFINED / evaluator-module-unavailable`。
  - それ以外、つまり依存 module の欠落なら、12 件すべて `ERROR / evaluator-import-error`。
  - どちらも `SATISFIED` ではないため、`orchestrator/campaign/s8c_preregistration.py:1930-1959` の conjunction により `effective=False`。
  - 通常の `ImportError`、`RuntimeError` などは捕捉されず、`ActivationReport` 自体が返らない。

- `orchestrator/campaign/s8c_preregistration.py:1795-1803`
  - `Path.read_bytes()` の `OSError` とその subclass だけを捕捉し、`live=b""` に置換する。
  - 通常は直後の比較で12件すべて `ERROR / evaluator-blob-mismatch`、従って `effective=False`。
  - 例外型や理由は消える。commit 側 blob も空なら比較を通過する余地があるが、本件の対象外。

- `orchestrator/campaign/s8c_preregistration.py:1812-1826`
  - 最初の `except ModuleNotFoundError as exc` は `ModuleNotFoundError` とその subclass。
  - projection 自身または top-level package の欠落なら12件すべて `ERROR / projection-module-unavailable`。
  - 依存 module の欠落なら12件すべて `ERROR / projection-import-error`。
  - 続く `except Exception` は、先行節に捕捉されなかった `Exception` subclass を捕捉し、12件すべて `ERROR / projection-import-error`。
  - `BaseException` 直系の `KeyboardInterrupt`、`SystemExit`、`GeneratorExit` は対象外。
  - いずれの返却経路も `effective=False`。

- `orchestrator/campaign/s8c_preregistration.py:1832-1837`
  - `Path.read_bytes()` から出る全 `Exception` subclass を捕捉し、12件すべて `ERROR / projection-file-read-error`。
  - `BaseException` 直系は対象外。返却された場合は必ず `effective=False`。

- `orchestrator/campaign/s8c_preregistration.py:1853-1859`
  - `except Exception` は、`evaluator(commit, repo_root=root)` の呼出し、返された iterable の走査、`_normalize_predicate_results` の全処理から出る `Exception` subclass を一括捕捉する。
  - `getattr(module, "get_registry")`、`get_registry()`、`getattr(registry, "evaluate_all")` は try の外なので捕捉しない。
  - 捕捉時は12件すべて `ERROR / evaluator-exception / evidence=()`。`orchestrator/campaign/s8c_preregistration.py:1930-1959` により `effective=False`。
  - F631 の `PreregistrationError("predicate-result-type")` は `PreregistrationError` が `RuntimeError`、従って `Exception` の subclass なのでここへ入り、型名と `.reason` の両方が消える。

- `orchestrator/campaign/s8c_preregistration.py:1878-1889`
  - `orchestrator/campaign/s8c_preregistration.py:1882` は `read_blob_at` または `parse_preregistration_markdown` の `PreregistrationError` とその subclass だけを捕捉して `pass` する。
  - この catch 自体は predicate の `status` と `reason_code` を変更しない。`contract` が `None` のままなので `section5_findings=()`、`all_filled=False` となり、最終的に `effective=False`。
  - 同じ source は `validate_condition_freeze_at` 内でも再度 parse され得る。そこで送出された `PreregistrationError` は `orchestrator/campaign/s8c_preregistration.py:1888-1889` が捕捉し、`.reason` を `freeze_reason_code` へ写す。ただし freeze 不在なら parse より先に `freeze-missing` となるため、最初の parse 例外理由が必ず再現されるわけではない。
  - `orchestrator/campaign/s8c_preregistration.py:1888` の catch は `PreregistrationError` とその subclass を捕捉し、predicate は変えず、`condition_freeze_valid=False`、`freeze_reason_code=exc.reason`、`effective=False` とする。こちらでは理由は消えていない。

- `orchestrator/campaign/s8c_preregistration.py:1891-1896`
  - test registry 経路の `registry.evaluate_all` と `_normalize_predicate_results` が送出する全 `Exception` subclass を捕捉する。`BaseException` 直系は対象外。
  - 捕捉時は12件すべて `ERROR / registry-exception / evidence=()`、従って `effective=False`。
  - 例外型と `PreregistrationError.reason` は消える。

- `orchestrator/campaign/s8c_preregistration_evidence.py:3376-3395`
  - `orchestrator/campaign/s8c_preregistration_evidence.py:3381` は `core.resolve_commit` と `_read_blob_at_resolved` の `core.PreregistrationError` を捕捉し、12件すべて `ERROR / commit-blob-read-error`。
  - `orchestrator/campaign/s8c_preregistration_evidence.py:3390` は `load_contract_bytes` の `EvidenceContractError` を捕捉し、12件すべて `ERROR / evidence-contract-invalid`。
  - いずれも activation 側へ正常な12件として戻り、最終的に `effective=False`。

- `orchestrator/campaign/s8c_preregistration_evidence.py:3424-3470`
  - `orchestrator/campaign/s8c_preregistration_evidence.py:3455` は `core.PreregistrationError` と `EvidenceContractError`、および各 subclass を捕捉する。
  - `EvidenceContractError.reason_code == "evidence-python-parse-error"` は `ERROR / evidence-python-parse-error`、`reachability-limit-exceeded` は同名の `ERROR`、それ以外は `ERROR / commit-blob-read-error`。
  - `core.PreregistrationError` は `.reason_code` を持たないため `getattr(..., "")` が空文字になり、常に `ERROR / commit-blob-read-error`。`.reason` は消える。
  - `orchestrator/campaign/s8c_preregistration_evidence.py:3464` は先行節に捕捉されなかった全 `Exception` subclass を捕捉し、その predicate だけを `ERROR / evaluator-internal-error` にする。例外型と内容は消える。
  - いずれも残りの predicate 評価を継続する。1件でもこの結果が含まれれば activation の `all_satisfied` が偽になり、`effective=False`。

## 理由が消える箇所

採否は次のとおりとする。

- `orchestrator/campaign/s8c_preregistration.py:1853-1859`
  - 例外型、`PreregistrationError.reason`、`evaluate_all` と normalize のどちらで発火したかがすべて消える。
  - 本件の一次対象として採用する。

- `orchestrator/campaign/s8c_preregistration.py:1891-1896`
  - test registry でも同じ情報が消える。
  - 一次対象と同じ fail-closed 実装をテスト注入経路でも固定するため採用する。ただし既存の `registry-exception` は変えない。

- `orchestrator/campaign/s8c_preregistration.py:1779-1788`
  - 捕捉対象は `ModuleNotFoundError` と既知であり、欠落場所も `evaluator-import-error` または `evaluator-module-unavailable` へ写っている。
  - 既に reason code へ写っているため対象外。

- `orchestrator/campaign/s8c_preregistration.py:1812-1826`
  - import の失敗箇所は `projection-import-error` または `projection-module-unavailable` へ写っている。
  - 既に reason code へ写っているため対象外。

- `orchestrator/campaign/s8c_preregistration.py:1832-1837`
  - 読取失敗は `projection-file-read-error` へ写っている。
  - 既に reason code へ写っているため対象外。

- `orchestrator/campaign/s8c_preregistration.py:1878-1883`
  - 最初の parse 例外オブジェクトは完全に捨てられる。後続 validation が同じ `.reason` を `freeze_reason_code` へ再導出する場合はあるが、保証されない。
  - 実際の情報消失だが evaluator 例外ではない。今回の最小差分から外す。

- `orchestrator/campaign/s8c_preregistration_evidence.py:3455-3463`
  - `EvidenceContractError` の一部は専用 reason code へ写り、残りは `commit-blob-read-error` へ縮約される。`core.PreregistrationError.reason` は消える。
  - per-predicate の既存 reason code 変換が既にあり、一次発火点とは異なるため対象外。

- `orchestrator/campaign/s8c_preregistration_evidence.py:3464-3469`
  - 元の例外型は消えるが、結果は predicate ID と `evaluator-internal-error` に構造化済み。
  - 別 module から診断を返す新しい registry protocol が必要になるため、今回の最小差分では対象外。

## 設計 (推奨と却下)

推奨は、既存 report と独立した明示的な第2返り値である。

```python
@dataclass(frozen=True)
class EvaluatorExceptionReason:
    callsite: str
    exception_type: str
    preregistration_reason: Optional[str]
```

新しい sibling API を次の形にする。

```python
def activation_report_with_diagnostics_at(
    repo_root: Path | str,
    commit: str = "HEAD",
) -> tuple[ActivationReport, tuple[EvaluatorExceptionReason, ...]]:
```

診断値は次の3項だけに限定する。

- `callsite`: `"default-registry.evaluate_all"`、`"_normalize_predicate_results"`、`"test-registry.evaluate_all"` のいずれか。
- `exception_type`: `type(exc).__name__`。
- `preregistration_reason`: `isinstance(exc, PreregistrationError)` の場合だけ `exc.reason`、それ以外は `None`。

`str(exc)`、detail、traceback、repo path、環境値は格納しない。診断列は immutable tuple とし、module 大域の可変状態は置かない。

既存の `activation_report_at(repo_root, commit="HEAD") -> ActivationReport` は sibling API の第1要素だけを返す wrapper として維持する。このため、次の呼出し規約は変わらない。

- `orchestrator/campaign/s8c_gate_report.py:116-122`
- `orchestrator/campaign/s8c_preregistration.py:2001-2006`
- `orchestrator/campaign/s8c_preregistration.py:2140-2169`
- `orchestrator/campaign/trial_registry.py:4138-4142`
- `orchestrator/campaign/trial_registry.py:5872-5876`
- `orchestrator/campaign/trial_registry.py:6560-6562`

`ActivationReport`、`PredicateResult`、`EvidenceRef` は `orchestrator/campaign/s8c_preregistration.py:155-166,246-260` の field を一切変えない。診断 dataclass は別 object なので、`orchestrator/campaign/s8c_preregistration.py:2121-2137` の `_jsonable(report)` と digest preimage に入らない。従って `trial_registry.py:4159-4160` などへ永続化される report digest も不変である。

`ReasonCode` と `REASON_CODES` は `orchestrator/campaign/s8c_preregistration_evidence.py:48-92` のまま変更しない。fallback の `evaluator-exception` と `registry-exception` も文字列を変えない。

却下する代替は次のとおり。

- `activation_report_at` への mutable out-parameter:
  - 古い呼出しは動くが、公開 signature を広げ、途中失敗時の部分書込みと aliasing を持ち込む。`orchestrator/tests/test_s8c_preregistration_core.py:2666-2668` が守る production 注入境界も曖昧になるため却下。

- `ActivationReport` の隠し属性または field:
  - field 追加は digest を変える。非-field 属性でも frozen dataclass に暗黙 state を付けることになり、serialization と寿命が不透明になるため却下。

- logging、module 大域 list、`contextvars`:
  - 呼出しと診断の対応が暗黙になり、thread、task、再入評価で混線し得る。明示的な返り値で解決できるため却下。

- 例外 chain の保持:
  - 現行契約は例外を外へ出さず `ActivationReport` を返す。chain を CLI が読むには再送出または report への隠し添付が必要になり、fail-closed の返却契約と両立しないため却下。

## file:line プラン

- `orchestrator/campaign/s8c_preregistration.py:155-170`
  - `EvaluatorExceptionReason` を独立した frozen dataclass として追加する。
  - 既存3 dataclass の field 定義には触れない。

- `orchestrator/campaign/s8c_preregistration.py:1735-1770`
  - `Exception` から上記3項だけを抽出する private helper を追加する。
  - `PreregistrationError.reason` 以外の message は参照しない。
  - fallback predicate を作る既存 `_uniform_predicates` はそのまま使う。

- `orchestrator/campaign/s8c_preregistration.py:1845-1859`
  - `_default_registry_results` の返り値を、predicate tuple と診断 tuple の pair にする。直接 caller は `orchestrator/campaign/s8c_preregistration.py:1925-1927` の1箇所だけ。
  - 現在の単一 try を、`evaluator` 呼出しと `_normalize_predicate_results` 呼出しの2節に分ける。
  - 両 catch とも型は `except Exception as exc` のままにし、捕捉集合を変えない。
  - evaluator 側は callsite を `"default-registry.evaluate_all"`、normalize 側は `"_normalize_predicate_results"` とする。
  - どちらも predicate は従来どおり12件の `ERROR / evaluator-exception / ()`。診断だけ第2要素に置く。
  - `get_registry()` など、現在 try 外にある処理を catch 内へ移さない。

- `orchestrator/campaign/s8c_preregistration.py:1862-1975`
  - 現在の report 構築本体を、report と診断 tuple を返す内部関数へ移す。
  - production の `_default_registry_results` から返った診断をそのまま保持する。
  - test registry の `orchestrator/campaign/s8c_preregistration.py:1891-1896` も evaluator と normalize を分離し、従来の `registry-exception` を維持したまま診断を返す。
  - evaluator、projection、freeze など対象外の分岐では空 tuple とする。
  - `effective` の式 `orchestrator/campaign/s8c_preregistration.py:1954-1959` と `ActivationReport` 構築 `1960-1975` は変更しない。

- `orchestrator/campaign/s8c_preregistration.py:1978-1998`
  - `activation_report_at` は従来どおり同じ2引数で `ActivationReport` だけを返す。
  - 新しい `activation_report_with_diagnostics_at` は同じ入力から pair を返す。
  - `_activation_report_at_for_test` も従来どおり `ActivationReport` だけを返す。診断テストには内部 pair 関数を明示的に使う。
  - production sibling API に registry 引数を露出させない。

- `orchestrator/campaign/s8c_preregistration.py:2187-2202`
  - `check` 分岐だけ新 sibling API を呼び、評価を1回だけ行う。
  - stdout の既存 print 文は変更しない。
  - 診断は1件1行の compact JSON object とし、stderr へ出す。key は `callsite`、`exception_type`、`preregistration_reason` の3つだけとする。
  - `--json` 時の stdout は現在の `json.dumps(_jsonable(report), ensure_ascii=False, sort_keys=True)` と末尾改行を完全維持する。
  - 非 `--json` 時も `EFFECTIVE` または `NOT_EFFECTIVE`、decider、section5、predicate の全行を完全維持する。
  - 両形式とも診断があれば同じ stderr、診断がなければ stderr は空。
  - exit code は `effective` が偽なら1、真なら0のまま。traceback と `str(exc)` は出さない。

- `orchestrator/campaign/s8c_gate_report.py:116-122`
  - 変更しない。`gate_report_at` は従来の `activation_report_at` を exact args で1回呼び、診断を gate report JSON に混ぜない。

- `orchestrator/campaign/trial_registry.py:4138-4160,5872-5878,6560-6563`
  - 変更しない。既存 capability 再検証、digest 永続化、`effective_at` の規約を維持する。

## テスト計画

新規 test file は作らない。

- `orchestrator/tests/test_s8c_cli_entrypoints.py:29-34,58-121`
  - malformed evaluator 用の既存形式 fixture を追加する。
  - temporary repo に実際の core、projection、evidence contract と、11件の `PredicateResult` だけを返す evaluator module を配置して commit する。
  - `_normalize_predicate_results` は monkeypatch や stub にせず、`orchestrator/campaign/s8c_preregistration.py:1742-1759` の実体を通す。11件入力により実体の `orchestrator/campaign/s8c_preregistration.py:1744-1745` から `PreregistrationError("predicate-result-type")` を送出させる。
  - evaluator module 自身は commit blob と live import bytes を一致させるため、blob mismatch 経路ではなく `_default_registry_results` の実体へ到達する。

- 同 file に負例 `test_evaluator_exception_remains_fail_closed` を追加する。
  - plain `activation_report_at` と診断付き sibling API の report が完全一致すること。
  - 12件すべて `status is PredicateStatus.ERROR`。
  - 12件すべて `reason_code == "evaluator-exception"`。
  - 12件すべて `evidence == ()`。
  - `effective is False`。
  - report の `_jsonable` と `_activation_report_digest` が診断の有無で同一であること。
  - これが受理集合を広げていない証拠になる。

- 同 file に正例 `test_evaluator_exception_reason_names_real_normalizer_failure` を追加する。
  - 同じ malformed evaluator repo を使う。
  - 診断 tuple が1件であること。
  - `callsite == "_normalize_predicate_results"`。
  - `exception_type == "PreregistrationError"`。
  - `preregistration_reason == "predicate-result-type"`。
  - message、repo path、traceback の field が存在しないこと。
  - 依存先として実体を名指しする対象は `_default_registry_results`、`_normalize_predicate_results`、`PreregistrationError.reason` であり、これらを stub しない。

- `orchestrator/tests/test_s8c_cli_entrypoints.py:155-242` の形式に合わせ、path/module と `--json` 有無を parameterize した CLI test を追加する。
  - `--json` の stdout bytes を、同じ commit に対する plain `activation_report_at` の既存 JSON serialization bytes と完全一致で比較する。
  - 非 `--json` の stdout bytes を、現在の `orchestrator/campaign/s8c_preregistration.py:2195-2201` の行構成から作った期待 bytes と完全一致で比較する。
  - 両方で return code は1。
  - stderr は構造化診断1行だけで、上記3 field が完全一致する。
  - `"Traceback"`、例外 detail、temporary repo path が stderr に無いことを固定する。

- `orchestrator/tests/test_s8c_preregistration_core.py:2483-2499`
  - `ActivationReport`、`PredicateResult`、`EvidenceRef` の field 名集合を現行どおり pin する純増 assertion を置く。
  - 診断 object を変えても report digest が変化しないことを固定する。

- `orchestrator/tests/test_s8c_preregistration_core.py:2666-2668`
  - 新 sibling API にも `registry` parameter が無いことを追加確認する。
  - 既存 `activation_report_at` と `effective_at` の assertion は変更しない。

- `orchestrator/tests/test_s8c_preregistration_core.py:2680-2695`
  - `main` が新 sibling API を呼ぶため、既存 test の monkeypatch 対象だけを新関数へ合わせ、返り値を `(report, ())` とする。
  - exit code と stdout の既存期待値は変更しない。

- 回帰対象として既存の次をそのまま実走対象に含める。
  - `orchestrator/tests/test_s8c_cli_entrypoints.py`
  - `orchestrator/tests/test_s8c_preregistration_core.py`
  - `orchestrator/tests/test_s8c_preregistration_predicates.py`
  - `orchestrator/tests/test_s8c_preregistration_invariant.py`
  - `orchestrator/tests/test_s8c_gate_report.py`

この段では sandbox 指示どおり実走していない。従って緑とは判定しない。

## 波及

repository 内 grep による静的列挙は次のとおり。

- `_default_registry_results` の直接 caller:
  - `orchestrator/campaign/s8c_preregistration.py:1925-1927` の1箇所だけ。

- `activation_report_at` の production caller:
  - `orchestrator/campaign/s8c_gate_report.py:121`
  - `orchestrator/campaign/s8c_preregistration.py:2005`
  - `orchestrator/campaign/s8c_preregistration.py:2157`
  - 現在の CLI `orchestrator/campaign/s8c_preregistration.py:2191`。ここだけ新 sibling API へ切り替える。

- `effective_at` の外部 caller:
  - `orchestrator/campaign/p3_autonomous_workload_trial.py:992-995`
  - `orchestrator/campaign/p3_autonomous_workload_trial.py:5437`
  - `orchestrator/campaign/trial_registry.py:6560-6562`

- `require_effective_preregistration` の外部 caller:
  - `orchestrator/campaign/p3_autonomous_workload_trial.py:1000-1004`
  - `orchestrator/campaign/p3_autonomous_workload_trial.py:1006-1009`
  - `orchestrator/campaign/trial_registry.py:4138-4142`
  - `orchestrator/campaign/trial_registry.py:5872-5876`

- `activation_report_at` の test caller:
  - `orchestrator/tests/test_s8c_cli_entrypoints.py:141`
  - `orchestrator/tests/test_s8c_preregistration_core.py:1556,1650,2542,2563,2589,2612,2647`
  - `orchestrator/tests/test_s8c_preregistration_predicates.py:245,4020,4029,4043,4602`
  - `orchestrator/tests/test_s8c_preregistration_invariant.py:378`
  - `orchestrator/tests/test_s8c_gate_report.py:465`

- private test injection caller:
  - `_activation_report_at_for_test` は `orchestrator/tests/test_s8c_preregistration_core.py:2253,2393,2414,2428,2451,2474,2486,2514,2534,2659,2687,2701`。
  - 返り値を `ActivationReport` のまま維持するため、既存 caller は変更不要。

- 共有 fixture:
  - CLI の `tiny_repo` と `oracle`: `orchestrator/tests/test_s8c_cli_entrypoints.py:58-152`
  - core の `_Registry`: `orchestrator/tests/test_s8c_preregistration_core.py:413-429`
  - predicate の `current_commit_snapshot`: `orchestrator/tests/test_s8c_preregistration_predicates.py:198-209`
  - invariant の `repository_candidate_commit` と `candidate_activation_report`: `orchestrator/tests/test_s8c_preregistration_invariant.py:362-378`
  - real repository lock: `orchestrator/tests/conftest.py:1401-1413`

- 強く関連する consumer test:
  - CLI/library 等価性: `orchestrator/tests/test_s8c_cli_entrypoints.py:164-242`
  - gate が旧 API を exact args で1回呼ぶこと: `orchestrator/tests/test_s8c_gate_report.py:194-203`
  - report digest: `orchestrator/tests/test_s8c_preregistration_core.py:2483-2499`
  - production registry 注入禁止: `orchestrator/tests/test_s8c_preregistration_core.py:2666-2668`
  - non-JSON CLI: `orchestrator/tests/test_s8c_preregistration_core.py:2680-2695`
  - evaluator/core/projection identity: `orchestrator/tests/test_s8c_preregistration_predicates.py:4014-4045`
  - candidate report consumers: `orchestrator/tests/test_s8c_preregistration_invariant.py:448-470,602-619`

## 変異事前登録候補

- `orchestrator/campaign/s8c_preregistration.py:1854`
  - 変異: `_normalize_predicate_results` を削除し、11件の raw result をそのまま返す。
  - kill: `test_evaluator_exception_remains_fail_closed` が12件の `ERROR` と `evaluator-exception` を要求するため失敗する。

- `orchestrator/campaign/s8c_preregistration.py:1856-1858`
  - 変異: fallback status を `SATISFIED` または `EVIDENCE_UNDEFINED` に変える。
  - kill: 同負例の status assertion と `effective is False` が殺す。

- `orchestrator/campaign/s8c_preregistration.py:1857`
  - 変異: reason code を `evaluator-internal-error` などへ変更する。
  - kill: 同負例の12件 exact `reason_code == "evaluator-exception"` が殺す。

- 新しい診断生成 helper、配置予定 `orchestrator/campaign/s8c_preregistration.py:1735-1770`
  - 変異: `PreregistrationError.reason` を捨てる、または `str(exc)` を格納する。
  - kill: `test_evaluator_exception_reason_names_real_normalizer_failure` の exact `"predicate-result-type"` と field 集合、detail 非包含 assertion が殺す。

- `orchestrator/campaign/s8c_preregistration.py:1853-1859`
  - 変異: evaluator 呼出しと normalize の callsite を同じ値にする。
  - kill: 正例の `callsite == "_normalize_predicate_results"` が殺す。

- `orchestrator/campaign/s8c_preregistration.py:2187-2202`
  - 変異: 診断を stdout に混ぜる、JSON stdout の separator や改行を変える、stderr に traceback または message を出す。
  - kill: path/module、JSON/non-JSON の stdout bytes 完全一致、stderr exact object、`"Traceback"` 非包含の CLI test が殺す。

## scope 外の所見

- `orchestrator/campaign/s8c_preregistration.py:1779-1788` は一般の `ImportError` や `RuntimeError` を捕捉しないため、brief の「import 例外は evaluator-import-error」という説明は全例外には成立しない。本件では修正を提案しない。
- `orchestrator/campaign/s8c_preregistration.py:1795-1803` は evaluator file の読取失敗を `evaluator-blob-mismatch` へ倒す。さらに commit blob が空なら一致し得る。本件では修正を提案しない。
- `orchestrator/campaign/s8c_preregistration.py:1878-1883` の parse 理由消失と、`orchestrator/campaign/s8c_preregistration_evidence.py:3464-3469` の内側 catch-all は実在するが、今回の外側 evaluator normalization 診断には混ぜない。
- `s8c_gate_report.py` の CLI 終端は `orchestrator/campaign/s8c_gate_report.py:170-172` で例外を JSON 化済みであり、brief どおり変更対象外。

## 総括

推奨差分は、既存 `ActivationReport` を完全不変に保ったまま、評価結果と immutable な診断 tuple を返す sibling API を追加し、`check` だけが第2要素を stderr へ表示する構成である。一次 catch と test registry catch の捕捉集合、12件の `ERROR`、既存 reason code、`effective=False`、stdout bytes、report digest、既存 consumer の呼出し規約はすべて維持する。

検証の中核は、11件しか返さない実 evaluator fixture に実体の `_normalize_predicate_results` を通し、`PreregistrationError("predicate-result-type")` を実際に発生させることである。静的プランのみで、テスト実走、編集、commit、push は行っていない。