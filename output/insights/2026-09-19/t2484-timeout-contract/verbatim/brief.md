# T-2484 段1 brief

- 研究土台の実在欠陥: t2484-watchdog-segments §5 の5441/5442/5452.nqsvで短い外側監視がPre-runningを切り、変異source残置・orphan holdを発生させた。研究実装の変異検査をdispatcherのin-band終端まで回収する最小修正。
- 目的: D2148項8の(a-1)+(a-3)だけを実装。
- 外側timeoutは前段P、queue Q、walltime W、grace G、回収A、cleanup Cの全区間を覆う。
- dispatchのhang_riskは短いhang_timeout_secondsを外側へ渡さず、内側walltimeに委ねる。
- 内側期限・回収・qdel gate・orphan hold・復元・失敗node完全一致・resume束縛・local hang挙動を維持。
- D2044項29(b)のcollection gate式変更不採用、(c)非拒否の早期診断採用を維持。
- 新gate、区間認識watchdog、一般化、schema/台帳追加、内側dispatcher変更はscope外。
- (P1) spec値を拒否で取り締まらず、dispatch実効timeoutをmax(spec値,全区間予算)にする局所helperが裁定に適合する。既存collection Q+G gateはspec値で現状通り判定する。独立相談の攻撃対象。
- (P2) Pは資料の実測max15.9秒から有限の余裕を選ぶ必要がある。2秒は平均相当で保証ではない。数値と根拠をplanで吟味し、絶対保証と称さない。
- 実アンカー: tools/mutation_harness.py::_collection_command / _collect_expected_nodes / _baseline / _run_one_mutation相当のtimeout選択 / _run_tests。
- 読取アンカー: tools/pegasus/dispatch_compute.pyのDEFAULT_*、tools/run_tests.py::_default_dispatch、orchestrator/tests/test_mutation_harness.py、test_t2337_dispatch_timeout_overrides.py。
- docs変更: docs/dev-wave/mutation.md DW-M06/M07、phase完了、成果insightとspool worklog。旧insight実測は書換えない。
- 完了判定: 各呼出しが全区間予算を使用し、local短いhangと既存拒否・回収を維持。D95 author、独立レビュー、焦点test、変異、受入、docs/provenance検査、共通land。
- 分割: 実装面は依存が一枚岩なのでauthor1単位。親はdocsと統合のみ。read-only plan、相談2レンズ、レビュー2レンズ。
- 実測環境: Pegasus02、pytest/buildはrun_tests.py、変異本走は独立clone/dispatch、性能測定はない。
- 成果物影響: 現行の外側先行発火は変異検出結果を回収不能にする。修正は異常variantの受理や正しさgateの弱化を許さない。
