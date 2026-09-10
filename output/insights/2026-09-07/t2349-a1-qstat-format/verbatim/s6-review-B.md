## 所見 1: production caller の波及は閉じている

(a) 主張: 変更された observer と validator の production 呼出し元に、未追跡の回帰経路は見つからない。

(b) 根拠:

- `_observe_qstat_visibility` の全 production caller:
  - V3 fan-out submit: `paper_story_a1_paired.py:3165`
  - direct submit: `paper_story_a1_paired.py:3312`
- submission receipt の再検査:
  - V3 submit 直後: `paper_story_a1_paired.py:3229`
  - V3 acquisition: `paper_story_a1_paired.py:3424`
  - V3 completion: `paper_story_a1_paired.py:4066`
  - final consumer: `paper_story_a1_paired.py:6526,6559`
  - measurement acquisition: `paper_story_a1_paired.py:6733,6997`
  - V3 materializer: `paper_story_a1_paired.py:8417`
  - direct materializer: `paper_story_a1_paired.py:8516`
- `_observe_scheduler_terminal` の全 production caller:
  - V3 group completion: `paper_story_a1_paired.py:4113`
  - direct completion: `paper_story_a1_paired.py:4308`
- `validate_completion_receipt` の全 production caller:
  - final consumer: `paper_story_a1_paired.py:6593`
  - V3 completion projection: `paper_story_a1_paired.py:8363-8384`
  - direct materializer: `paper_story_a1_paired.py:8550`
  - V3 final consumer と materializer は `_validate_v3_group_completion` 経由で到達する: `paper_story_a1_paired.py:6535,8424`
- producer が新しく書く `QUE` / `RUN` は、V3 group validator、legacy acquisition validator、prior-visibility validator の既存 12 語集合に含まれる: `paper_story_a1_paired.py:3010,3565-3568,3615-3618`。

(c) 成果物への影響: V3 fan-out、direct submit、acquisition、completion、consumer、materializerはいずれも canonical `QUE` / `RUN` を受理する。別 ID または非 signature の disappearance receipt だけが新たに拒否される。

(d) 判定: **refuted**。未追跡 caller による回帰は確認できない。

(e) 分類: **nit**。

## 所見 2: `state` の記録値変更は既存 reader を壊さない

(a) 主張: producer が raw state ではなく canonical `QUE` / `RUN` を保存する変更によって、既存 receipt reader や fixture は壊れない。

(b) 根拠: producer は共有 parser の結果を `{QUE,RUN}` に制限してその値を保存する: `paper_story_a1_paired.py:2904-2924`。一方、reader は意図どおり 12 語集合を維持している: `paper_story_a1_paired.py:322-335,3010,3565-3568,3615-3618`。既存 fixture も既に `"state": "QUE"` を使用する: `test_paper_story_a1_paired.py:719-725`。12 語を全て受理する既存テストも変更されていない: `test_paper_story_a1_job_contract.py:217-245`。

(c) 成果物への影響: 新規 receipt は `QUE` / `RUN` に正規化されるが、保存済みの `PRR`、`STG`、`HLD` などを読む互換経路は維持される。job body の既存 state membership 契約も canonical 値を受理できる: `test_paper_story_a1_job_contract.py:2047-2084`。

(d) 判定: **refuted**。

(e) 分類: **nit**。

## 所見 3: disappearance reader の受理縮小は実在するが、確定仕様どおりである

(a) 主張: 旧 validator が受理していた「非空かつ Request ID 行が無い任意 stdout」は、保存済み receipt であっても今後は拒否される。これは実在する互換性変更だが、意図しない回帰ではない。

(b) 根拠: consumer は対象 ID に束縛された NQSV 不存在行の fullmatch を要求する: `paper_story_a1_paired.py:557-569,3755-3767`。producer も同じ述語と空 stderr を要求する: `paper_story_a1_paired.py:3783-3808`。親裁定が producer と completion validator の両方をこの意味論に変更すると明記している: `s4-ruling.md:129-136`。既存 disappearance fixture は既にこの書式である: `test_paper_story_a1_job_contract.py:1147-1196`。

(c) 成果物への影響: 過去に任意の診断文を disappearance として保存した receipt は final consumer、V3 projection、materializerで拒否される。一方、正規の NQSV 不存在 receipt は引き続き通る。この縮小は誤った complete/materialization を止めるための本題である。

(d) 判定: **real**。ただし親が明示的に採用した受理集合縮小である。

(e) 分類: **nit**。must-fix ではない。

## 所見 4: import、request-ID regex、死んだコードに回帰はない

(a) 主張: 共有 leaf の import、request-ID regex の alias 化、初期化順に破壊的な問題は見つからない。NameError や未使用の旧定義も残っていない。

(b) 根拠:

- direct CLI 用の `sys.path` と `__package__` 補正が共有 import より先にある: `paper_story_a1_paired.py:36-43`。
- 段3 B は共有 module が標準ライブラリ、regex、dataclass 定義だけで、逆 import が無いことを確認済み: `s3br/out.md:161-175`。
- alias の全参照は次の3箇所:
  - `_qstat_mentions_request`: `paper_story_a1_paired.py:545-554`
  - `_parse_qstat_terminal`: `paper_story_a1_paired.py:572-589`
  - visibility の唯一 ID 検査: `paper_story_a1_paired.py:2904-2914`
- `_parse_qstat_terminal` の caller は validator と producer の2箇所だけ: `paper_story_a1_paired.py:3732-3754,3809-3815`。
- 旧ローカル request-ID regex 定義は削除済み。旧 state/exit regex は terminal parser が引き続き使用する: `paper_story_a1_paired.py:306-310,577-588`。
- 新しい queue regex、disappearance regex、visible-state 集合もそれぞれ production 経路から参照される: `paper_story_a1_paired.py:313-321,561,2906,2911`。

(c) 成果物への影響: module import、direct CLI、visible-terminal receipt の再検査で NameError や循環 import は生じない。新設された到達不能受理枝もない。

(d) 判定: **refuted**。

(e) 分類: **nit**。

## 所見 5: source closure の非推移性だけは残る

(a) 主張: 新たな runtime dependency である `scheduler_nqsv.py` は A-1 source binding に含まれない。この観察自体は real だが、親が明示的に変更しないと裁定している。

(b) 根拠: exact source closure meta-test は従来の 9 / 10 path を維持する: `test_paper_story_a1_job_contract.py:393-425`。親は closure が既に curated subset であり、共有 leaf を追加しないことを確定した: `s4-ruling.md:73-82,115-117`。

(c) 成果物への影響: materialized `source_binding.files` に共有 parser 自体は列挙されない。ただし HEAD と clean-tree binding は維持され、本 wave で新しい種類の closure 欠落を作ったものではない。closure を追加すれば、逆に既存 exact-set test と所有外 shell 一覧を同時変更する必要がある。

(d) 判定: **real**。親が採用しなかった既知の provenance 残余である。

(e) 分類: **nit**。この段の must-fix ではない。

## 所見 6: 新規 fixture は既存 meta-test 制約に抵触しない

(a) 主張: 新しい test module はなく、追加された5 fixtureによる登録簿、命名、収集、source closure の破壊は見つからない。

(b) 根拠: 差分は既存 `test_paper_story_a1_job_contract.py` への追加と、非 Python fixture 5本である: `impl.patch` の fixture hunksおよび test hunk。既存 test file は plain-runner entrypoint を維持する: `test_paper_story_a1_job_contract.py:3162-3168`。影響候補となる検査は次のとおり。

- pytest の `test_*.py` 収集: `.txt`、`.stdout`、`.stderr` は収集対象外。
- `test_non_certifying_source_closure_matches_shell_and_preserves_legacy_set`: `test_paper_story_a1_job_contract.py:393-425`。fixture は runtime source closure ではない。
- `test_job_body_is_executable_and_registry_is_exact_dispatch_required`: `test_paper_story_a1_job_contract.py:2097-2105`。data fixture は admission registry 対象ではない。
- plain-runner 契約: 既存 test file 内への追加なので新規登録不要。
- `git diff --check`: 実装報告では通過済み: `s5b/out.md:37-44`。
- `tools/check_docs.py` と `tools/check_ai_provenance.py`: commit 後の全体 gate 候補だが、この差分に新規 docs や test module 登録面はない。

(c) 成果物への影響: fixture の存在によって test collection、source closure、job registry が赤になる経路はない。

(d) 判定: **refuted**。

(e) 分類: **nit**。

## 所見 7: 既存テストの赤は静的には予測されない

(a) 主張: 射影された既存2 test fileについて、この差分だけで赤になる既存 nodeid は予測されない。許可外の assertion 変更もない。

(b) 根拠:

- 差分で変更された既存テストは
  `orchestrator/tests/test_paper_story_a1_job_contract.py::test_submit_runs_real_qsub_call_from_repository_root`
  だけである。
- 変更されたのは qsub request ID と qstat stdout の入力 fixture: `test_paper_story_a1_job_contract.py:2688-2698`。
- assertion は従来どおり cwd、receipt key、長さを検査するだけで変更されていない: `test_paper_story_a1_job_contract.py:2701-2712`。
- visible-terminal 述語は維持され、既存正例も同じ alias regex で通る:
  - `::test_scheduler_completion_receipt_cross_binds_terminal_and_logs`
  - `::test_scheduler_terminal_ext_flows_from_producer_to_validator`
  - `test_paper_story_a1_paired.py::test_run_complete_uses_raw_sidecar_gate_then_enables_final_view`
- 既存 disappearance 正例は新 fullmatch に合致する:
  - `::test_scheduler_completion_accepts_disappearance_after_submission_visibility`
- exact 12-state testsは定数不変のため影響を受けない:
  - `::test_acquisition_receipt_accepts_exact_nqsv_qstat_state_vocabulary`
  - `::test_nqsv_qstat_state_allowlist_is_exact`
- patch 全文に既存 assertion の変更はない。

(c) 成果物への影響: 既存挙動を期待値変更で隠した形跡はない。旧 synthetic qstat 入力のままなら repository-root test が赤になるが、親が唯一許可した入力 fixture 置換で閉じている。

(d) 判定: **refuted**。

(e) 分類: **nit**。pytest は未実走なので、これは静的予測に限る。

## 所見 8: 段3で採用された所見は実装で閉じている

(a) 主張: 段3 A/B の real 所見のうち、親が採用した項目に未実装は見つからない。

(b) 根拠:

- A1 `QUE` 正例: Queued fixture と `QUE` assertionを追加: `test_paper_story_a1_job_contract.py:248-301`。
- A4 canonical producer制限: `paper_story_a1_paired.py:321,2904-2924`。保存 completion receipt の再解析変異: `test_paper_story_a1_job_contract.py:1286-1340`。
- A5 production wiring: observerを直接通す: `test_paper_story_a1_job_contract.py:264-273,379-390,1208-1220,1273-1283`。
- A6 queue 全体一意性と位置: `paper_story_a1_paired.py:2905-2915`、負例: `test_paper_story_a1_job_contract.py:305-368`。
- A7/B5 producer-only stderr: `paper_story_a1_paired.py:2910,3784-3788`。schema に stderr を足していないため親の弱い裁定どおり。
- A8 disappearance fullmatch: `paper_story_a1_paired.py:317-320,557-569`。
- B1 報告制約: 実装報告は bench 到達を保証していない: `s5b/out.md:50-60`。
- B2 実機 RUN を terminal と誤認しない負例: `test_paper_story_a1_job_contract.py:1233-1283`。
- B3 alias import による NameError 回避: `paper_story_a1_paired.py:41-43,576`。
- B6 caller closure: 所見1の全経路に実装上到達している。
- 親が不採用とした A2、A3、A9 は、それぞれ共有 raw surface、12語 reader、curated source closureとして意図的に残っている: `s4-ruling.md:25-40,42-82`。

(c) 成果物への影響: 親の確定仕様に対する実装漏れはなく、F852 の既知 visibility blocker と disappearance の過剰受理が対象どおり閉じる。bench 到達性、reader縮小、schema migration、source closure一般化は未解決のままだが、本差分の完了主張には含まれていない。

(d) 判定: **refuted**。採用所見の未閉鎖は確認できない。

(e) 分類: **nit**。

## 総括

**must-fix 所見はない。** 静的レビュー上、変更面と caller propagation は親の確定仕様どおり閉じている。既存 receipt への実在する影響は、任意の診断文を disappearance としていた保存 receipt を今後拒否する点だけで、これは意図された受理集合縮小である。

既知の残余は、12語 reader、producer-only stderr、共有 parser の source closure 外、実機 bench 到達未証明である。いずれも段4で明示的に別 waveまたは報告制約へ送られており、この差分の must-fix には当たらない。pytest は実行していない。