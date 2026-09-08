## fixture の実現可能性

- 所見 1 (深刻度: blocker): プラン記載のまま既存 CLI fixture の起動方法を流用すると、11 件 evaluator には到達しない。test process は実 repository の `P` を import し、CLI も実 repository の `_PREREG_PATH` と `cwd=_ROOT` から起動する (`orchestrator/tests/test_s8c_cli_entrypoints.py:20-28,172-215`)。その状態で temporary repo の evaluator blob だけを差し替えても、固定 module 名を import した実 repository 側 module の `__file__` bytes と一致せず (`orchestrator/campaign/s8c_preregistration.py:1778-1803`)、`evaluator-blob-mismatch` になって `_default_registry_results` の caller (`orchestrator/campaign/s8c_preregistration.py:1909-1927`) へ進まない。従って `s2-plan.md:203-205` の「自身は一致する」は起動根を指定しない限り成立しない。
  - 成果物への影響: certified の受理集合は false のままだが、report と台帳 digest の reason は `evaluator-exception` でなく `evaluator-blob-mismatch` となり、F631 の診断参照は生成されない。

- 所見 2 (深刻度: must-fix): 到達可能な構成は少なくとも二つある。
  - 実 process 方式: temporary repo に変更後の core、projection、11 件 evaluator を同じ bytes で配置して commit し、path 形式は temporary repo 側の core fileを、module 形式は `cwd=temporary repo` で `-m orchestrator.campaign.s8c_preregistration` を起動する。core は direct CLI 時に自身の repository root を `sys.path` へ入れ、同一 module 名を alias 登録する (`orchestrator/campaign/s8c_preregistration.py:36-41`)。これなら core、evaluator、projection の live bytes と commit blob が全部一致し、`_default_registry_results` と実 normalizer (`orchestrator/campaign/s8c_preregistration.py:1742-1759,1845-1859`) に到達できる。library report との比較も、同じ temporary repo を import root にした別の `python -c` process で sibling API を呼べば構成でき、新規 file は不要である。
  - in-process 方式: commit には実 evaluator bytes を置き、import 済み evaluator の `get_registry` だけを monkeypatch して 11 件を返す fake registry を渡す。`get_registry` が実際の選択点である (`orchestrator/campaign/s8c_preregistration_evidence.py:3487-3498`)。file bytes は変えないので identity 検査を通り、stub されるのは入力 producer だけで、`_default_registry_results`、normalizer、診断 helper は実体を通る。ただしこれは real-process CLI の証明にはならないため、CLI 完了条件には前者が必要である。
  - 成果物への影響: この補正により受理集合と既存 report、台帳値を変えず、診断参照だけを実際の `predicate-result-type` に結び付けられる。

## 正例が機構を通るか

- 所見 3 (深刻度: must-fix): fixture を所見 2 のいずれかへ直せば、正例は実体の `_default_registry_results`、`_normalize_predicate_results`、`PreregistrationError.reason` を通せる (`orchestrator/campaign/s8c_preregistration.py:133-138,1742-1759,1845-1859`)。許容できる stub は Git fixture、import root の隔離、または evaluator の返却値を作る最上流だけである。`_default_registry_results`、normalizer、例外抽出 helper、sibling API のいずれかを stub すると、`s2-plan.md:216-223` の正例は診断機構を通らない緑になる。CLI 表示だけの単体テストで sibling API を stub することは、別の real-process 結合テストが機構全体を通る場合に限って許容できる。
  - 成果物への影響: 二層を stub したままでは受理集合と report は見掛け上維持される一方、実運用の診断参照が空でもテストが通り、台帳から真因へ辿れない。

- 所見 4 (深刻度: must-fix): 正常系の「診断は空」という assertion が不足している。既存 real-process test は正常 evaluator を確認している (`orchestrator/tests/test_s8c_cli_entrypoints.py:124-151`) が、stderr については `"Traceback"` 非包含しか要求しない (`orchestrator/tests/test_s8c_cli_entrypoints.py:238-242`)。正常 sibling API の diagnostics が `()` であり、通常 CLI の stderr が完全に空であることを純増 assertion で固定しないと、常時偽診断を出す実装が残る。
  - 成果物への影響: certified 選択、report、台帳 digest は不変でも、正常 commit に F631 の偽診断参照が付いて人間の切り分けを誤らせる。

## 変異の殺し損ね

- 所見 5 (深刻度: must-fix): `s2-plan.md:304-328` の各変異の判定は次のとおり。
  - `_normalize_predicate_results` を除去して raw 11 件を返す変異は、負例の「12 件すべて exact ERROR」で殺せる。
  - fallback status を `SATISFIED` または `EVIDENCE_UNDEFINED` にする変異は、exact status assertion で殺せる。`effective is False` 単独では freeze など別条件でも false になるため十分ではないが、計画された status assertion は十分である。
  - reason code を変更する変異は、12 件の exact `evaluator-exception` assertion で殺せる。
  - `PreregistrationError.reason` を捨てる変異は exact `"predicate-result-type"` で殺せる。しかし `str(exc)` を代入する変異は殺せない。この normalizer 例外には detail がなく、`PreregistrationError.__init__` の実装上 `str(exc) == exc.reason == "predicate-result-type"` だからである (`orchestrator/campaign/s8c_preregistration.py:133-138,1744-1745`)。殺すには detail sentinel 付き `PreregistrationError("fixture-reason", "secret-detail")` を evaluator から送出し、reason だけが残ることを要求する必要がある。
  - evaluator と normalizer の callsite を同値にする変異は確実には殺せない。両方を `default-registry.evaluate_all` にすれば現正例が失敗するが、両方を `_normalize_predicate_results` にすれば normalizer しか発火させない正例は通る。evaluator 自身が送出する別の負例と exact `default-registry.evaluate_all` assertion が必要である。
  - stdout 混入、JSON separator・改行変更、traceback・追加 message の変異は、実現可能な real-process fixtureで stdout bytes と stderr object を完全一致させれば殺せる (`orchestrator/campaign/s8c_preregistration.py:2187-2202`)。
  - 成果物への影響: 殺し損ねは受理集合と report、台帳値を変えないが、例外 detail や誤った callsite が診断参照へ入り、真因の同定を誤らせる。

- 所見 6 (深刻度: must-fix): 計画中の全テストを通したまま診断を無効化または虚偽化できる変異が少なくとも三つある。
  - sibling API が例外の有無にかかわらず、常に F631 用の固定 tuple `("_normalize_predicate_results", "PreregistrationError", "predicate-result-type")` を返す。malformed 正例と CLI 正例は通り、既存正常 CLI test は stderr 空を要求していないため通る。
  - 診断 helper が全例外に同じ F631 固定値を返す。計画は一種類の normalizer 例外しか発火させないため通る。RuntimeError を evaluator から直接送出し、`exception_type == "RuntimeError"`、`preregistration_reason is None`、callsite が evaluator 側であることを追加すれば殺せる。
  - test-registry catch の diagnostics を常に空、または callsite を誤った値にする。計画は実装対象に含める (`s2-plan.md:169-180`) 一方、test-registry 例外の診断 assertion を一件も指定していない。実コード上この経路は private test injection だけである (`orchestrator/campaign/s8c_preregistration.py:1862-1896,1986-1998`)。
  - 成果物への影響: certified の受理集合と report、台帳 digest は不変だが、診断参照が正常時に偽造されるか、例外ごとの差を失うか、特定経路で消える。

## 既存テストへの波及

- 所見 7 (深刻度: nit): sibling API 化で直接壊れる既存 test は、提示された四 test file 内では `test_non_json_cli_reports_decider_reason` の一件だけである。これは旧 `activation_report_at` を monkeypatch する (`orchestrator/tests/test_s8c_preregistration_core.py:2680-2695`) ため、main が sibling API を呼ぶと intercept できない。monkeypatch 対象を新関数へ変え、返り値だけ `(report, ())` に合わせるのは期待値の変更、反転、緩和ではなく collaborator seam の追随である。exit code と既存 stdout assertion はそのまま残すべきである。
  - 成果物への影響: 修正しなければ test suite が失敗して成果物を受理できないが、適切な追随自体は certified の受理集合、report、台帳値・参照を変えない。

- 所見 8 (深刻度: nit): 他の既存テストは次の理由で sibling API 変更だけでは壊れない。`test_s8c_cli_entrypoints.py:164-242` は正常 evaluator の real process で stdout と report を比較し、診断が空なら従来どおりである。gate report の exact-call test は旧 API を要求する (`orchestrator/tests/test_s8c_gate_report.py:194-203`) が、プラン自身が gate report を変更しない (`s2-plan.md:191-195`)。predicate tests の該当箇所は library の `activation_report_at` を直接呼ぶだけ (`orchestrator/tests/test_s8c_preregistration_predicates.py:4014-4045,4583-4603`) で、wrapper 契約維持により不変である。production entrypoint の registry 非公開 assertion (`orchestrator/tests/test_s8c_preregistration_core.py:2666-2668`) も既存二関数については不変で、新 sibling への同じ assertion は純増である。
  - 成果物への影響: これらの既存期待値を変更する必要はなく、変更すれば逆に report、台帳 digest、受理集合を守る既存参照を弱める。

## F631 は閉じるか

- 所見 9 (深刻度: must-fix): corrected fixture と計画どおりの実装なら、`s8c_preregistration check` については一コマンドで真因を読める。非 `--json` では従来 stdout の後とは別 stream に、`--json` では既存 report JSON stdout とは別に、stderr の一行 JSONから `exception_type` と `preregistration_reason` を読める (`s2-plan.md:182-189`; `orchestrator/campaign/s8c_preregistration.py:2187-2202`)。ただし `--json` の stdout payload 自体には診断が入らないため、stdout だけを保存・解析する人には読めない。
  
  さらに `s8c_gate_report` CLI では閉じない。同 CLI は診断を持たない旧 `activation_report_at` を呼び (`orchestrator/campaign/s8c_gate_report.py:116-122,159-174`)、swallow 済みの evaluator 例外は outer `_error_json` に到達しない。従って F631 で人間が打ったコマンドが gate-report CLI なら、差分後も 12 件の `evaluator-exception` までしか見えない。brief は同 CLI 終端を scope 外にしている (`brief.md:17`) ため、完了条件を preregistration CLI に限定するのか、実際の事故コマンドも対象にするのかの裁定が必要である。
  - 成果物への影響: fail-closed なので certified の受理集合、report、台帳 digest は不変だが、利用した CLI または stdout-only 消費では真因参照が欠落し、F631 と同じ誤報告が残る。

## 過大と過小

- 所見 10 (深刻度: must-fix): test-registry 経路まで診断 pair 化する部分 (`s2-plan.md:66-68,169-180`) は過大である。現行では `allow_test_registry` は private `_activation_report_at_for_test` のためだけにあり、production sibling API には registry を露出しない設計である (`orchestrator/campaign/s8c_preregistration.py:1862-1896,1986-1998`; `s2-plan.md:176-180`)。人間の F631 解決にも production report にも使われない。残すなら専用変異テストが必要になり、外すなら本題の default evaluator catch に集中できる。
  - 成果物への影響: 現時点の certified 受理集合、report、台帳値には影響しないが、private 経路の未検証診断参照を新たな契約として抱え、成果物の検証範囲だけを増やす。

- 所見 11 (深刻度: must-fix): 過小なのは、fixture の import root 指定、正常時の空 diagnostics、evaluator が直接送出する例外、detail 付き `PreregistrationError`、そして retained なら test-registry 例外の各 assertion である。逆に既存 dataclass field 集合と digest 不変の pin (`s2-plan.md:232-238`) は、brief の field 不変条件 (`brief.md:19-27`) を直接守るので過大ではない。
  - 成果物への影響: 不足を放置すると受理集合と report、台帳 digest の既存値は維持されても、診断の空非空、型、reason、callsite 参照が実例一件にだけ過適合したまま受理される。

## scope 外の所見

- 所見 12 (深刻度: nit): evaluator 内部の per-predicate catch-all は引き続き例外型と内容を捨て、当該 predicate を `evaluator-internal-error` にする (`orchestrator/campaign/s8c_preregistration_evidence.py:3424-3470`)。プランはこれを明示的に対象外としており (`s2-plan.md:86-92,330-335`)、今回混ぜない判断は scope に合っている。
  - 成果物への影響: 当該経路でも certified の受理集合は広がらず、report と台帳には既存 generic reason が残るが、元例外への診断参照は引き続き存在しない。

## 総括

静的判定は差戻しである。中心設計の「report と digest を変えず、診断を sibling API と stderr に分離する」は成立するが、現在の fixture 記述では blob identity を越えられない。temporary repo 自身を Python の実行・import root にする構成へ明記し、正常空診断、evaluator 直接例外、detail 非漏出、callsite 分離を追加で固定する必要がある。

また、F631 が閉じるのは `s8c_preregistration check` を端末で実行して stderr も読む場合に限る。`--json` の stdout-only 利用と `s8c_gate_report` CLI は未閉塞である。pytest は指示どおり実走しておらず、緑とは判定していない。