## 受理集合

- 所見 1 (深刻度: nit):
  プランどおりなら受理集合は広がらない。現行は evaluator または normalize の `Exception` を捕捉すると、12 件すべてを `ERROR / evaluator-exception / evidence=()` に置換する (`orchestrator/campaign/s8c_preregistration.py:1853-1859`)。test registry も同様に `ERROR / registry-exception` へ置換する (`orchestrator/campaign/s8c_preregistration.py:1891-1896`)。`effective` は全 predicate が `SATISFIED` の場合だけ真なので (`orchestrator/campaign/s8c_preregistration.py:1930-1959`)、この fallback から発効する経路はない。プランも同じ fallback 値を明記している (`/home/SFC/tanab/.claude/jobs/78b62369/tmp/t2401/s2-plan.md:161-174`)。診断 dataclass は `ActivationReport` の field ではなく、`_jsonable` は渡された dataclass の field だけを走査するため (`orchestrator/campaign/s8c_preregistration.py:2121-2137`)、同一 report の digest preimage に診断は入らない。
  成果物への影響: 捕捉済み例外について status、reason_code、effective、certified 選択、同一 report の台帳 digest は不変で、追加されるのは側 channel の診断だけである。

## 捕捉集合の変化

- 所見 2 (深刻度: nit):
  try の分割自体は、raw iterable を evaluator 側 try で受け取り、`_normalize_predicate_results(raw)` の呼出し全体を第2 try に置く限り、捕捉集合を変えない。現在の遅延評価点は normalize 内の `tuple(results)` である (`orchestrator/campaign/s8c_preregistration.py:1742-1745`)。したがって generator 本体、`__iter__`、`__next__` が送出する `Exception` は第2 try で従来どおり捕捉される。`KeyboardInterrupt`、`SystemExit`、`GeneratorExit` などの `BaseException` 直系は現行でも捕捉されず、新設する両方の `except Exception` でも捕捉されない (`orchestrator/campaign/s8c_preregistration.py:1853-1859`; `/home/SFC/tanab/.claude/jobs/78b62369/tmp/t2401/s2-plan.md:161-167`)。ただし `tuple(raw)` などの materialize を両 try の間へ出す実装は、現行で捕捉される遅延例外を外へ漏らすので、プランの「normalize 呼出し」をその内部処理まで含む境界として固定する必要がある。
  成果物への影響: 正しく分割すれば report と受理集合は不変だが、materialize が try 外へ出ると従来の `ERROR` report が返らず、CLI と台帳再導出の参照が失われる。

- 所見 3 (深刻度: nit):
  generator の遅延例外は evaluator が生成した処理から出ても、観測点が `tuple(results)` なので診断上は `"_normalize_predicate_results"` になる (`orchestrator/campaign/s8c_preregistration.py:1742-1745`; `/home/SFC/tanab/.claude/jobs/78b62369/tmp/t2401/s2-plan.md:115-120`)。これは捕捉集合や report を変えないが、callsite は例外の意味上の発生源ではなく評価タイミングを示す値になる。計画した 11 件の concrete result テスト (`/home/SFC/tanab/.claude/jobs/78b62369/tmp/t2401/s2-plan.md:201-223`) ではこの差は観測できない。
  成果物への影響: certified 選択と台帳は変わらないが、遅延 evaluator の診断レポートでは原因箇所の参照が normalize 側に寄り、人間の切り分けを誤らせうる。

## 診断 channel と正しさ防壁

- 所見 4 (深刻度: nit):
  sibling API 自体は capability 検証の迂回路にならない。既存 `activation_report_at` はすでに生の `ActivationReport` を公開しており (`orchestrator/campaign/s8c_preregistration.py:1978-1983`)、新 API の第1要素も同じ値にすぎない。capability は `effective_at` が `report.effective` を確認して生成し (`orchestrator/campaign/s8c_preregistration.py:2001-2006`)、consumer は型、commit、再計算した effective、digest を再検証する (`orchestrator/campaign/s8c_preregistration.py:2140-2169`)。`trial_registry` も型と commit を検査した後にこの再検証を必ず呼ぶ (`orchestrator/campaign/trial_registry.py:4126-4144`, `orchestrator/campaign/trial_registry.py:5860-5878`)。プランも production sibling に registry 注入を公開せず、これら consumer を変更しない (`/home/SFC/tanab/.claude/jobs/78b62369/tmp/t2401/s2-plan.md:176-195`)。
  成果物への影響: 診断付き API の report だけから新たな certified 選択や登録済み launch を発行する経路は増えず、台帳受理も従来の sealed capability 再検証に束縛されたままである。

- 所見 5 (深刻度: nit):
  `s8c_gate_report` は引き続き旧 API を呼び、report の `effective` を投影するだけで、そもそも認可しないことを明記している (`orchestrator/campaign/s8c_gate_report.py:2-6`, `orchestrator/campaign/s8c_gate_report.py:45-73`, `orchestrator/campaign/s8c_gate_report.py:116-122`)。診断を同レポートへ混ぜない判断は防壁を弱めない。
  成果物への影響: gate report の JSON、status、authorization 表示は不変で、診断付き report が認可成果物へ昇格することはない。

## digest / pin 束縛の検算

- 所見 6 (深刻度: must-fix):
  親 brief の因果関係は正しいが、「台帳が全件不一致」は過大である。`ActivationReport` に field を追加すれば、`dataclasses.fields` が新 field も列挙するため (`orchestrator/campaign/s8c_preregistration.py:2121-2126`)、report JSON preimage と `_activation_report_digest` は変わる (`orchestrator/campaign/s8c_preregistration.py:2133-2137`)。その古い digest を持つ `registered-effective` admission は再導出値と不一致になる (`orchestrator/campaign/trial_registry.py:4138-4161`, `orchestrator/campaign/trial_registry.py:4358-4405`)。一方、明示的 exploratory は digest が `None` (`orchestrator/campaign/trial_registry.py:4101-4109`)、formal non-certifying も `None` (`orchestrator/campaign/trial_registry.py:4166-4211`) であり、その不在が検査される (`orchestrator/campaign/trial_registry.py:4286-4296`)。従って正確には「旧 digest を持つ registered-effective 成果物が不一致」であって、全 mode、全 trial、全台帳行ではない。
  成果物への影響: field 追加時に不一致になるのは非 null の旧 activation digest を束縛した launch、lifecycle、report、receipt であり、digest を持たない exploratory と formal non-certifying の値はこの理由では変わらない。

- 所見 7 (深刻度: must-fix):
  親が十分に分離していない別の digest 経路がある。診断を report 外へ置いても、実装差分そのものが `s8c_preregistration.py` の blob bytes を変える。この blob hash は `ActivationReport.core_module_blob_sha256` に入り (`orchestrator/campaign/s8c_preregistration.py:1871-1876`, `orchestrator/campaign/s8c_preregistration.py:1960-1974`)、commit ID も report field なので、差分前後の別 commit 間では report digest が当然変わる。同一 commit、同一 report に対する旧 API と sibling API の digest が同じ、という主張だけが正しい。また同 file は現在と pre-T733 の enforcement source closure に含まれる (`orchestrator/campaign/campaign_lock.py:47-67`, `orchestrator/campaign/campaign_lock.py:115-136`)。authority は exact path map を検査し (`orchestrator/campaign/campaign_lock.py:328-363`)、実際の binding は各 commit blob の SHA-256 を取得して live bytes と照合する (`orchestrator/campaign/contract_loader_binding.py:518-555`)。既存 path の編集なので path 集合 pin は増減しないが、blob pin は更新対象になる。
  成果物への影響: 同一 report の診断有無では digest は変わらない一方、新実装 commit の report digest と source-closure blob digest は旧 commit と異なり、旧 binding を新 live bytes に対して使えば参照不一致になる。

- 所見 8 (深刻度: nit):
  `_canonical_bytes` を通る他の preimage は、evidence contract (`orchestrator/campaign/s8c_preregistration.py:404-412`)、§5 field 名、§6 条件、個別条件、normative body (`orchestrator/campaign/s8c_preregistration.py:1031-1044`)、protected contract (`orchestrator/campaign/s8c_preregistration.py:206-214`)、freeze record の canonical bytes (`orchestrator/campaign/s8c_preregistration.py:1176-1194`, `orchestrator/campaign/s8c_preregistration.py:2100`) である。いずれも診断 object や `ActivationReport` 全体を入力にしないため、独立 dataclass の追加だけでは変わらない。`ReasonCode` と `REASON_CODES` は閉じた enum から導出される (`orchestrator/campaign/s8c_preregistration_evidence.py:48-92`)。既存テストは direct registry の12結果がその集合内かだけを検査する (`orchestrator/tests/test_s8c_preregistration_predicates.py:212-218`)。core 外側の `"evaluator-exception"`、`"registry-exception"`、新しい `preregistration_reason` はこの検査対象ではない。
  成果物への影響: 診断 dataclass は freeze や protected digest を変えず、既存 predicate reason_code 語彙も不変だが、側 channel の reason 安全性は既存の閉集合テストでは保証されない。

## fail-closed 終端

- 所見 9 (深刻度: blocker):
  診断抽出 helper は現案のままでは total ではない。`isinstance(exc, PreregistrationError)` の後に `exc.reason` を直接読む案 (`/home/SFC/tanab/.claude/jobs/78b62369/tmp/t2401/s2-plan.md:115-120`) は、`PreregistrationError` subclass が基底 `__init__` を呼ばず `reason` を持たない場合に `AttributeError` を出す。property や `__getattribute__` が例外を出す subclass でも同じである。`type(exc).__name__` も異常な metaclass の属性取得で送出しうる。これらは元の evaluator 用 try の `except` handler 内で発生するため、その try では再捕捉されない。library API は report を返さず、CLI の外側は `PreregistrationError` しか捕捉しないので (`orchestrator/campaign/s8c_preregistration.py:2187-2213`)、`AttributeError` や `RuntimeError` は traceback とともに漏れる。
  成果物への影響: 現行なら12件の `ERROR` report になった入力が report 不在と未処理例外へ変わり、CLI stdout、終了値、台帳再導出の参照が失われるため、受理は広がらないが fail-closed の返却契約が壊れる。

- 所見 10 (深刻度: blocker):
  `PreregistrationError.reason` は型も語彙も検査されていない。基底 constructor は渡された値をそのまま保存する (`orchestrator/campaign/s8c_preregistration.py:133-138`)。従って evaluator は path や環境値を reason に入れられ、非文字列や JSON 化不能 object も保持できる。前者は brief の環境依存値禁止 (`/home/SFC/tanab/.claude/jobs/78b62369/tmp/t2401/brief.md:26-27`) に反し、後者は stderr の `json.dumps` を `TypeError` にできる。異常な型名についても同じ問題がある。計画した通常の `PreregistrationError("predicate-result-type")` だけのテスト (`/home/SFC/tanab/.claude/jobs/78b62369/tmp/t2401/s2-plan.md:216-230`) ではこの終端を証明できない。
  成果物への影響: certified 選択と activation digest は直接変わらないが、診断レポートが環境依存または生成不能となり、stderr bytes、CLI 終了、再現可能な参照が変わる。

## 規律 2 / 3

- 所見 11 (深刻度: nit):
  規律 2 を緩める差分ではない。fallback status と reason_code、`effective` の conjunction、sealed capability の生成と再検証を変えないためである (`orchestrator/campaign/s8c_preregistration.py:1853-1859`, `orchestrator/campaign/s8c_preregistration.py:1930-1959`, `orchestrator/campaign/s8c_preregistration.py:2001-2006`, `orchestrator/campaign/s8c_preregistration.py:2140-2169`)。
  成果物への影響: evaluator 失敗を SATISFIED や effective に倒す経路は増えず、certified 選択と台帳受理集合は現行のままである。

- 所見 12 (深刻度: must-fix):
  通常の F631 については規律 3 を満たす。11件の結果は `_normalize_predicate_results` で `PreregistrationError("predicate-result-type")` になる (`orchestrator/campaign/s8c_preregistration.py:1742-1745`)。標準の例外 object なら計画した3 field に `"_normalize_predicate_results"`, `"PreregistrationError"`, `"predicate-result-type"` が入り、`check` CLI が stderr に出す (`/home/SFC/tanab/.claude/jobs/78b62369/tmp/t2401/s2-plan.md:182-189`, `/home/SFC/tanab/.claude/jobs/78b62369/tmp/t2401/s2-plan.md:216-230`)。ただし所見9、10の totality と payload 境界を解決しない限り、「なぜ壊れたかを必ず構造化して返す」という一般の規律 3 までは成立しない。
  成果物への影響: F631 の標準ケースでは診断値が人間へ届き、report と台帳は不変だが、異常例外では診断 report 自体が失われる。

## scope 外の所見

- 所見 13 (深刻度: nit):
  新 channel が扱うのは外側の evaluator 呼出しと normalize だけである。`get_registry()`、`getattr(registry, "evaluate_all")` は現行 try 外にあり (`orchestrator/campaign/s8c_preregistration.py:1845-1852`)、プランも移動しない (`/home/SFC/tanab/.claude/jobs/78b62369/tmp/t2401/s2-plan.md:161-167`)。また evidence evaluator 内部では `PreregistrationError` が `commit-blob-read-error` に縮約され、その他の例外は `evaluator-internal-error` に縮約される (`orchestrator/campaign/s8c_preregistration_evidence.py:3424-3471`)。これらへの変更は提案しないが、「評価器例外理由」全般ではなく外側2地点だけの改善である。
  成果物への影響: 該当する内部例外では certified 選択は引き続き fail-closed だが、診断 report は空または汎用 reason のままで、真因参照は増えない。

## 総括

- 所見 14 (深刻度: blocker):
  受理集合、report field、reason_code、effective、capability 防壁を不変にする骨格は成立している。しかし、診断抽出と JSON 化が例外を出さない保証、および `.reason` と型名の再現性境界がプランにないため、現行の `ERROR` 返却を未処理例外へ変える経路が残る (`/home/SFC/tanab/.claude/jobs/78b62369/tmp/t2401/s2-plan.md:115-121`; `orchestrator/campaign/s8c_preregistration.py:2187-2213`)。また「全台帳不一致」は non-null digest を持つ registered-effective 成果物に限定して訂正すべきである。検査は静的のみで、pytest は実走していない。
  成果物への影響: このまま author 段へ進むと certified 受理集合は広がらない一方、例外時の report、CLI、台帳再導出が欠落しうるため、fail-closed の成果物契約を満たさない。