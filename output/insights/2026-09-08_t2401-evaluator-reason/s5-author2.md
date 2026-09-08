## 現行の受理・拒否挙動

変更前は evaluator 呼出しと normalize が単一の `except Exception` に縮約され、例外時は 12 件すべて `ERROR / evaluator-exception / evidence=()`、`effective=False` でした。test-registry も `ERROR / registry-exception` へ縮約され、例外型・`PreregistrationError.reason`・捕捉地点は失われていました。CLI stdout と終了値には反映されず、診断用 stderr もありませんでした。

## 実装した差分

- [s8c_preregistration.py:67](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2401-evaluator-reason/orchestrator/campaign/s8c_preregistration.py:67)
  - ASCII charset、128 文字上限、診断専用 sentinel を追加。
- [s8c_preregistration.py:179](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2401-evaluator-reason/orchestrator/campaign/s8c_preregistration.py:179)
  - 独立した frozen dataclass `EvaluatorExceptionReason` を追加。
- [s8c_preregistration.py:1786](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2401-evaluator-reason/orchestrator/campaign/s8c_preregistration.py:1786)
  - 例外属性取得を `BaseException` まで自己捕捉する total helper を実装。callsite は意味上の発生源ではなく捕捉評価地点であることを docstring に明記。
- [s8c_preregistration.py:1910](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2401-evaluator-reason/orchestrator/campaign/s8c_preregistration.py:1910)
  - `_default_registry_results` を evaluator と normalize の 2 try に分離。遅延 iterable の materialize は normalize try 内に維持。
- [s8c_preregistration.py:1951](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2401-evaluator-reason/orchestrator/campaign/s8c_preregistration.py:1951)
  - report と immutable な診断 tuple を返す内部関数を追加。test-registry の evaluator と normalize も別 callsite で診断。
- [s8c_preregistration.py:2088](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2401-evaluator-reason/orchestrator/campaign/s8c_preregistration.py:2088)
  - 既存 API の signature と返り値を維持。
- [s8c_preregistration.py:2111](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2401-evaluator-reason/orchestrator/campaign/s8c_preregistration.py:2111)
  - production sibling `activation_report_with_diagnostics_at` を追加。`registry` 引数は非公開。
- [s8c_preregistration.py:2320](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2401-evaluator-reason/orchestrator/campaign/s8c_preregistration.py:2320)
  - CLI `check` のみ sibling API を使用。診断を compact JSON 1 件 1 行で stderr へ出力。

## 追加したテスト

| テスト | 固定する命題 | 必須 assertion |
|---|---|---|
| `test_evaluator_exception_remains_fail_closed` | 11 件 evaluator が 12 件の exact ERROR fallback になる。plain/sibling report、JSON、digest が一致 | 負例、不変 digest |
| `test_evaluator_exception_reason_names_real_normalizer_failure` | 実 normalizer の型・reason・callsite | normalize 正例 |
| `test_evaluator_exception_cli_preserves_stdout_and_emits_one_diagnostic` | path/module と JSON/text の 4 組で stdout bytes、rc、stderr exact | CLI 全項目 |
| normal `oracle` の純増 assertion | 正常 sibling は `()`、正常 CLI stderr は空 | 正常系 |
| `test_default_registry_evaluator_runtime_error_is_structured` | evaluator 側 `RuntimeError` の 3 field | evaluator 正例 |
| `test_preregistration_exception_detail_is_not_copied_to_diagnostics` | reason は残り detail は漏れない | detail 非漏出 |
| invalid reason/type の parameterized tests | 欠落、非文字列、path、長過ぎる値、hostile property/metaclass を sentinel 化 | total 性、型・charset・長さ |
| `test_lazy_evaluator_exception_is_caught_at_normalization_callsite` | 遅延 generator 例外も normalize try で捕捉 | materialize 境界 |
| test-registry の evaluator/normalize tests | 例外を握り潰した場合は診断が非空、正常時は空 | test-registry 経路 |
| field 集合 pin | 既存 3 dataclass の field 不変、新 dataclass の frozen 性 | field 集合 |
| production signature test | sibling に `registry` が無い | API 境界 |
| non-JSON CLI 既存 test | monkeypatch 対象だけ sibling へ追随し `(report, ())` を返す | 許可された既存 test 追随 |

CLI fixture は [test_s8c_cli_entrypoints.py:155](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2401-evaluator-reason/orchestrator/tests/test_s8c_cli_entrypoints.py:155)、単体 assertion 群は [test_s8c_preregistration_core.py:2595](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2401-evaluator-reason/orchestrator/tests/test_s8c_preregistration_core.py:2595) からです。

## 実走した nodeid と結果

- `orchestrator/tests/test_s8c_cli_entrypoints.py` の収集全 nodeid
  - 10 passed
  - 新規 6 nodeid: fail-closed、normalizer reason、CLI 4 組
- `orchestrator/tests/test_s8c_preregistration_core.py` の収集全 nodeid
  - 406 passed
  - 新規 nodeid 群には normalizer、遅延 generator、RuntimeError、detail、異常 reason 5 例、異常 type 4 例、正常空診断、test-registry 3 例、field pin を含む

実行形式はいずれも指定どおり `PYTHONPATH=. python3 orchestrator/tests/<file>.py` の自走 harness です。`git diff --check` も通過しました。

## 波及の静的列挙

- `_default_registry_results` の所有内 caller は新しい pair を受け取るよう追随済み。
- `activation_report_at`、`effective_at`、`_activation_report_at_for_test` の caller 契約は不変。
- `s8c_gate_report.py`、`trial_registry.py`、predicate/invariant consumer は未変更。
- `ReasonCode` / `REASON_CODES` は未変更。両 sentinel がその集合外であることを静的確認済み。
- 共有 CLI fixture は正常系の空診断 assertion を追加。predicate/invariant fixture には変更なし。
- 同一 report の digest は診断の有無で不変。ただし新 commit では core blob と commit ID が変わるため、commit 間の report digest は通常どおり変わります。

## 不変条件の自己検査

1. 受理集合: 例外 fallback は exact `ERROR`、既存 reason code、空 evidence、`effective=False` を維持。
2. field: `ActivationReport`、`PredicateResult`、`EvidenceRef` の field 集合を exact pin。
3. stdout: JSON/text、path/module の 4 組で bytes 完全一致。
4. stderr: safe な 3 field だけ。traceback、message、detail、temporary path は非包含。
5. file: 変更は許可された既存 3 file のみ。新規 file なし。
6. reason 語彙: sentinel は診断専用で `ReasonCode` を拡張していない。
7. fail-closed: hostile な属性取得や遅延 generator でも未処理例外へ変わらず、12 件の ERROR を返す。

## 未了・懸念

- `test_s8c_preregistration_predicates.py`、`test_s8c_preregistration_invariant.py`、`test_s8c_gate_report.py` は未実走です。緑とは扱っていません。
- core test file には自走入口が無かったため、末尾へ test-only の自走入口を純増しました。
- source-closure の blob 束縛があるため、段 6 の前に親側で本差分を commit する必要があります。未 commit のまま production repository を評価すると `contract-loader-drift` の偽赤要因になります。
- `git add`、commit、push は行っていません。

## 総括

段 4 の設計 v2 を許可された 3 file 内で実装しました。受理・拒否、report、digest、stdout、終了値を維持したまま、評価器例外の安全な構造化診断を stderr と sibling API から取得できます。