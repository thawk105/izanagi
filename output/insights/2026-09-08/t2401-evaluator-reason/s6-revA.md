## 不変条件 1〜7 の逐条検査

1. 受理集合は維持されています。変更前の直接構築と現在の `_uniform_predicates(PredicateStatus.ERROR, "evaluator-exception")` は、`PREDICATE_IDS` 順に同じ `PredicateResult(id, ERROR, "evaluator-exception", ())` を生成します。test-registry 側も引き続き `"registry-exception"` です。12 件の `ERROR` により `effective=False` も不変です。

2. `EvidenceRef`、`PredicateResult`、`ActivationReport` の field は増減していません。新しい `EvaluatorExceptionReason` は report と並ぶ tuple にだけ存在し、`activation_report_at` は `[0]` だけを返します。したがって、同一 report に対する `_jsonable(report)` と `_activation_report_digest(report)` の入力は不変です。

3. 通常の出力成功時、`--json` と非 JSON の stdout の式、順序、空白、改行は変更前と同一です。診断出力は stdout 完了後に stderr へ送られます。通常時の終了値も同じですが、所見 3 の失敗経路では終端契約を維持できません。

4. `callsite` は全 4 呼出箇所で固定 literal です。一方、残る 2 field と既存の fatal-error 経路に問題があります。

- 所見 1 (深刻度: must-fix): [`_evaluator_exception_reason`](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2401-evaluator-reason/orchestrator/campaign/s8c_preregistration.py:1786) は、許可文字と 128 文字以下という条件を満たした `type(exc).__name__` と `exc.reason` をそのまま採用しています。hostile metaclass は `__name__` に環境値由来の英数字を返せます。また `PreregistrationError` は `reason` の語彙を検証しないため、秘密値が小文字・数字・ハイフンだけならそのまま通ります。charset・長さ検査は改行注入を防ぎますが、値の由来や機密性は保証しません。両 sentinel 自身も許可正規表現に一致するため、外部値による sentinel 偽装も可能です。
  成果物影響: certified 選択、ActivationReport、台帳値、受理集合は変わりませんが、保存される診断参照が外部選択値になり、機密値または偽の原因を成果物へ焼き込みます。

- 所見 2 (深刻度: must-fix): CLI の outer catch は現在も [`print(str(exc), file=sys.stderr)`](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2401-evaluator-reason/orchestrator/campaign/s8c_preregistration.py:2356) を実行します。たとえば `_git` は git stderr または `str(OSError)` を `PreregistrationError.detail` に格納するため、外部指定の `--repo-root`、repo path、環境依存の git エラー文が生のまま stderr に出ます。これは新しい 3-field 診断とは別経路ですが、裁定の「stderr に message・detail・repo path・環境値を出さない」を CLI 全体について満たしません。
  成果物影響: この経路では certified 選択や台帳は生成されませんが、CLI の失敗記録・参照に揮発的な repo path や環境依存値が混入します。

5. commit `134e5926d` の変更集合は、既存の `s8c_preregistration.py` と既存テスト 2 ファイルの計 3 件で、すべて `M` です。新規ファイルはありません。

6. `s8c_preregistration_evidence.py` は commit で変更されておらず、`ReasonCode` と `REASON_CODES` の拡張はありません。診断 sentinel の参照は helper 内だけで、`PredicateResult.reason_code` へ入る経路はありません。

7. helper 内の `type(exc).__name__`、`isinstance`、`exc.reason`、`len`、正規表現処理はそれぞれ `except BaseException` の内側です。非 str、巨大文字列、再帰的 object は exact `str` 検査または長さ検査で sentinel になります。固定 dataclass の構築と 1 要素 tuple 化には外部 object の callback はなく、通常の入力から例外を起こす経路は見つかりませんでした。ただし CLI 出力段には fail-closed の穴があります。

- 所見 3 (深刻度: blocker): 診断の `_jsonable`、`json.dumps`、stderr への `print` は [`main` の診断 loop](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2401-evaluator-reason/orchestrator/campaign/s8c_preregistration.py:2337) で実行され、外側が捕捉するのは `PreregistrationError` だけです。現在の安全な field からデータ依存の JSON 失敗は起きませんが、stderr の閉鎖、broken pipe、容量不足などによる `OSError` は未捕捉です。変更前なら `ERROR` report を出して定義済みの値を返した同じ評価が、診断追加によって未処理例外になります。診断処理中の `BaseException` もこの段では捕捉されません。
  成果物影響: 受理集合は広がりませんが、CLI report が出力済みのまま異常終了したり診断が欠落し、終了値とレポート参照の対応が変更前から変わります。自動処理がその結果を正規の fail-closed 終端として扱えなくなります。

## try 分割の副作用

通常の iterable について捕捉集合の変化はありません。

- evaluator 本体の例外は第 1 try、`tuple(results)` が呼ぶ `__iter__`、`__next__`、length hint または `__len__` の例外は第 2 try で捕捉されます。
- これらは変更前には単一 try の内側にあり、現在もすべて `Exception` は捕捉、`BaseException` 直系は非捕捉です。
- materialize は try の外へ出ていません。遅延 generator の例外は normalize callsite に帰属するだけで、fallback 値は同一です。
- 厳密な評価順では、変更前は `_normalize_predicate_results` の関数 object を evaluator 呼出し前に解決し、変更後は evaluator 後に解決します。evaluator が core module の同名 global を再束縛する hostile な場合は差が出ますが、commit に束縛された現行 evaluator にその処理はなく、repo 入力から到達する経路は見つかりませんでした。
- production 経路の `raw` は `_default_registry_results` の return 時に解放されてから report の `effective` を計算します。現行 evaluator は tuple を返すため、保持期間の差による副作用もありません。

## 診断の完全性

対象となる外側 4 catch、すなわち default evaluator、default normalizer、test evaluator、test normalizerでは、「捕捉した例外なら診断 1 件、正常 return なら空 tuple」が成立します。例外なしで診断を追加する代入経路もありません。

ただし、リポジトリ全体の全例外について文字どおり「診断が空 iff 例外を握り潰していない」と読むと成立しません。具体例は scope 外の所見 4 です。

## 既存 consumer への波及

`activation_report_at`、`_activation_report_at`、`_activation_report_at_for_test`、`effective_at`、`require_effective_preregistration` の signature と返り値は維持されています。production sibling に `registry` 引数もありません。

`s8c_gate_report.py` と `trial_registry.py` は commit で変更されず、いずれも従来の `activation_report_at`、`effective_at`、`require_effective_preregistration` を使用します。診断 dataclass は report に含まれないため、同一 report の digest、registered-effective admission、`activation_report_digest_sha256` の台帳照合には混入しません。

なお、commit 自体が変わることで `core_module_blob_sha256` と、それを含む report digest が変わるのは既存契約どおりです。診断追加による同一 report 内の変化ではありません。

## scope 外の所見

- 所見 4 (深刻度: nit): [`s8c_preregistration_evidence.PredicateRegistry.evaluate_all`](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2401-evaluator-reason/orchestrator/campaign/s8c_preregistration_evidence.py:3464) の per-predicate catch-all は例外を `ERROR / evaluator-internal-error` に変換して正常 return するため、外側の診断は空です。裁定 A13/B12 が明示的に scope 外としています。
  成果物影響: predicate report は `ERROR` のままで受理集合や台帳値は広がりませんが、外側の診断参照だけでは内部例外の発生を復元できません。

- 所見 5 (深刻度: nit): `s8c_gate_report.py` の `_error_json` は `str(exc)` を stdout の `message` に含めます。裁定 B9 により本 wave の対象外です。
  成果物影響: gate report の成功値や certified 選択は変わりませんが、エラー JSON の参照には例外 message や path が残り得ます。

## 総括

blocker 1 件、must-fix 2 件です。不変条件 1、2、5、6、および通常 iterable に対する try 境界は維持されていますが、stderr 出力失敗で既存 fail-closed 終端が未処理例外へ変わるため、このままでは裁定の不変条件 7を満たしません。また、不変条件 4を CLI 全体へ適用すると、許可文字内の外部 payload と既存 `str(exc)` 経路が残っています。

pytest は実行しておらず、本結果は指定資料と commit 差分による静的検査です。