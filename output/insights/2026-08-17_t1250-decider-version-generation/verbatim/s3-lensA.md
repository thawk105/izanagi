必読物はすべて読めた。read-only のため pytest は未実走であり、合格とは報告しない。`HEAD=5a19b8ab...` に対する production 判定器の無書込 probe と、Markdown parser のメモリ内検査だけを実施した。

### A1 — wave 固有テストは、整合的に再生成された条件弱化と §5 記入を検出できない

- **主張:** must-fix 候補。提案テストは版一致と `effective is False` しか固定せず、既存 candidate test は新 doc と新 g4 を相互比較している。このため、例えば C02 の規範を弱めて g4 も整合的に再生成する変異、または §5 の placeholder を canonical JSON へ変更する変異が生き残る。
- **根拠:** 新テストの assert は schema・版・reason・最終 `effective` だけである [s2-plan.md:87](/work/1/SFC/tanab/dev-wave-jobs/t1250-decider-version-generation/s2-plan.md:87)。candidate test は tip record と同じ candidate から parse した contract を比較する [test_s8c_preregistration_invariant.py:144](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1250-decider-version-generation/orchestrator/tests/test_s8c_preregistration_invariant.py:144) ため、doc と record を一緒に変えれば通る。もう一方の candidate test は predicate の `SATISFIED` が 0 件であることしか固定しない [test_s8c_preregistration_invariant.py:199](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1250-decider-version-generation/orchestrator/tests/test_s8c_preregistration_invariant.py:199)。§5 の値は意図的に protected hash 外である [phase3-8c-preregistration.md:240](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1250-decider-version-generation/docs/phase3-8c-preregistration.md:240)。現行 real-doc test も欄名集合・条件番号・C01 の一部文言しか固定しない [test_s8c_preregistration_core.py:434](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1250-decider-version-generation/orchestrator/tests/test_s8c_preregistration_core.py:434)。
- **成果物への影響:** 現時点の `effective` は false のままでも、`section5_findings` の blocker 除去や §6 の受理条件弱化が g4 に入り、将来の certified 選択が意図より広い集合を受理しうる。
- **推奨対応:** g4 の `section5_field_names_sha256`、`section6_conditions_sha256`、全 12 個の condition hash が immutable な g3 と同一であることを追加検査する。さらに §5 は「8 UNFILLED、検定欄だけ FILLED」の exact map を固定する。変異表へ「§5 を 1 欄埋める」と「C02 を弱め、g4 も再生成する」を追加する。現行 fixture から literal hash をコピーせず、直前世代 record との意図的な連続性として比較すべきである。

### A2 — brief の発効 baseline と「変わるのは reason code だけ」は実コードと不一致

- **主張:** must-fix 候補。C01〜C12 は `evaluator-exception` ではない。また g3 から g4 では reason code 以外に `commit`、`freeze_generation`、`protected_sha256`、`decider_version`、`decider_version_matches` が変わり、report digest も変わる。
- **根拠:** brief は全条件を `evaluator-exception` とし、変更点を reason code 1 点に限定する [s1-brief.md:21](/work/1/SFC/tanab/dev-wave-jobs/t1250-decider-version-generation/s1-brief.md:21)。しかし `evaluator-exception` は `evaluate_all()` 自体が外へ例外を投げた場合だけである [s8c_preregistration.py:1644](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1250-decider-version-generation/orchestrator/campaign/s8c_preregistration.py:1644)。実 registry は各条件の例外を内部で ERROR に閉じる [s8c_preregistration_evidence.py:687](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1250-decider-version-generation/orchestrator/campaign/s8c_preregistration_evidence.py:687)。

  現行 HEAD の実際の vector は次で、SATISFIED も `evaluator-exception` も 0 件だった。

  | 条件 | status | reason |
  |---|---|---|
  | C01 | UNSATISFIED | workload-projection-mismatch |
  | C02 | EVIDENCE_UNDEFINED | arm-binding-declared-only |
  | C03 | EVIDENCE_UNDEFINED | manifest-registry-proof-undefined |
  | C04 | UNSATISFIED | crash-policy-cell-partial |
  | C05 | EVIDENCE_UNDEFINED | schedule-schema-absent |
  | C06 | EVIDENCE_UNDEFINED | budget-consumer-contract-undefined |
  | C07 | EVIDENCE_UNDEFINED | floor-judge-contract-undefined |
  | C08 | EVIDENCE_UNDEFINED | prereg-binding-proof-undefined |
  | C09 | UNSATISFIED | formal-acceptance-layer3-consumer-absent |
  | C10 | UNSATISFIED | cross-binding-verifier-incomplete |
  | C11 | EVIDENCE_UNDEFINED | completion-proof-not-machine-checkable |
  | C12 | UNSATISFIED | environment-contract-consumer-absent |

  C01/C04/C09 の分岐は [s8c_preregistration_evidence.py:412](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1250-decider-version-generation/orchestrator/campaign/s8c_preregistration_evidence.py:412)、未定義 6 条件は [s8c_preregistration_evidence.py:613](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1250-decider-version-generation/orchestrator/campaign/s8c_preregistration_evidence.py:613)、C10〜C12 は [s8c_preregistration_evidence.py:496](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1250-decider-version-generation/orchestrator/campaign/s8c_preregistration_evidence.py:496) に対応する。§5 は実物どおり 8 欄未記入、検定欄 1 欄だけ記入済みである [phase3-8c-preregistration.md:164](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1250-decider-version-generation/docs/phase3-8c-preregistration.md:164)。

  発効は freeze valid、版一致、全欄記入、12 条件全充足の連言である [s8c_preregistration.py:1727](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1250-decider-version-generation/orchestrator/campaign/s8c_preregistration.py:1727)、[s8c_preregistration.py:1753](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1250-decider-version-generation/orchestrator/campaign/s8c_preregistration.py:1753)。返却 report には世代・hash・版が個別 field として入る [s8c_preregistration.py:1759](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1250-decider-version-generation/orchestrator/campaign/s8c_preregistration.py:1759)。digest は dataclass 全体から作られる [s8c_preregistration.py:1932](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1250-decider-version-generation/orchestrator/campaign/s8c_preregistration.py:1932)。段 2 も複数 field の変化には気付いているが、`commit` の変化を列挙から落としている [s2-plan.md:122](/work/1/SFC/tanab/dev-wave-jobs/t1250-decider-version-generation/s2-plan.md:122)。
- **成果物への影響:** 誤った oracle を字義どおり使うと正しい g4 report を拒否するか、逆に本来不変である §5・predicate vector の変化を「reason 以外」として整理できなくなる。台帳へ運ぶ report digest は必ず変わる。
- **推奨対応:** 期待差分を明文化する。変更可は `commit`、世代 3→4、protected hash、版 `None`→`s8c-decider/v1`、match false→true、reason unbound→match。freeze valid/reason、§5 vector、predicate status/reason vector、3 module hash、`effective=false` は不変とする。

### A3 — 新しい版束縛テスト自体は「自分と自分」の恒真検査ではない

- **主張:** この点は欠陥なし。初回生成時には producer が定数を record へ写すが、着地後は immutable な record blob と実行中 module 定数という別の source を比較する。定数だけを後日 bump すれば失敗する。
- **根拠:** テストは `report.commit` の tip bytes を直接読み [s2-plan.md:93](/work/1/SFC/tanab/dev-wave-jobs/t1250-decider-version-generation/s2-plan.md:93)、record field と `DECIDER_VERSION` を比較する [s2-plan.md:101](/work/1/SFC/tanab/dev-wave-jobs/t1250-decider-version-generation/s2-plan.md:101)。定数は core module の独立 blob にある [s8c_preregistration.py:49](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1250-decider-version-generation/orchestrator/campaign/s8c_preregistration.py:49)。protected preimage は evidence・normative・field names・conditions だけで版を含まない [s8c_preregistration.py:191](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1250-decider-version-generation/orchestrator/campaign/s8c_preregistration.py:191)。これは D458 の恒真化回避理由と一致する [decisions.md:19123](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1250-decider-version-generation/docs/decisions.md:19123)。既発行 record の編集は `generation-mutated` が拒否する [s8c_preregistration.py:1425](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1250-decider-version-generation/orchestrator/campaign/s8c_preregistration.py:1425)。
- **成果物への影響:** g4 着地後の版 drift を実 repo で検出できる。受理集合を単独で広げる欠陥はない。
- **推奨対応:** 提案テストは維持する。版を protected preimage へ追加したり、現行 g4 bytes hash の literal 比較へ置換したりしない。A1 の契約連続性検査を別に足す。

### A4 — 提案位置の追記は protected hash を確実に変え、`spurious-revision` にはならない

- **主張:** 欠陥なし。追記は §6 の plain paragraph であり、正規化後も内容が残る。
- **根拠:** 挿入位置と文面は [s2-plan.md:52](/work/1/SFC/tanab/dev-wave-jobs/t1250-decider-version-generation/s2-plan.md:52)、現行の改訂手続きは [phase3-8c-preregistration.md:244](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1250-decider-version-generation/docs/phase3-8c-preregistration.md:244)。H2 §6 から次の H2 までを section とする [s8c_preregistration.py:681](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1250-decider-version-generation/orchestrator/campaign/s8c_preregistration.py:681) ため、H3 配下も含まれる。§1・2・3・4・6・7 が normative body に入る [s8c_preregistration.py:896](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1250-decider-version-generation/orchestrator/campaign/s8c_preregistration.py:896)。paragraph と code span の中身も保持される [s8c_preregistration.py:538](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1250-decider-version-generation/orchestrator/campaign/s8c_preregistration.py:538)、[s8c_preregistration.py:594](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1250-decider-version-generation/orchestrator/campaign/s8c_preregistration.py:594)。

  独立 parser 検査では次の差になった。

  - normative: `1d143e24...1746` → `19ab798d...276e9`
  - protected: `5c7e32c9...ae14` → `fea3a889...fcc3`
  - §5 欄名 hash、§6 aggregate hash、12 個の condition hash はすべて不変

  `prepare_revision` はこの protected 差を見て進み、同値の場合だけ `spurious-revision` にする [s8c_preregistration.py:1882](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1250-decider-version-generation/orchestrator/campaign/s8c_preregistration.py:1882)。D458 も例外新設を明示却下している [decisions.md:19129](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1250-decider-version-generation/docs/decisions.md:19129)。
- **成果物への影響:** g4 は `protected_sha256=fea3a889...fcc3` となり、空改訂扱いされない。受理条件の field/condition 部分は変わらない。
- **推奨対応:** 文面と位置を段 2 の案どおり固定し、例外を作らない。

### A5 — g4 の世代連鎖は整合するが、git timeout 再較正債務は既に発火済み

- **主張:** g4 追加そのものは `generation-gap`、`generation-mutated`、`generation-limit`、supersedes の各検査と整合する。一方、timeout コメントの再較正条件は g4 ではなく g2 時点から成立している。
- **根拠:** g3 の実 bytes SHA-256 は `2b28cde32feaa4509ff6c8cfe382240d7b4d2d8f919608a6199f2b282c2f23e1` で、plan の期待値と一致する [condition-freeze.v1.g3.json:1](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1250-decider-version-generation/output/s8c-preregistration/condition-freeze/condition-freeze.v1.g3.json:1)。producer は HEAD tip の生 bytes を hash して supersedes を作る [s8c_preregistration.py:1873](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1250-decider-version-generation/orchestrator/campaign/s8c_preregistration.py:1873)。gap は [s8c_preregistration.py:1447](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1250-decider-version-generation/orchestrator/campaign/s8c_preregistration.py:1447)、supersedes は [s8c_preregistration.py:1465](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1250-decider-version-generation/orchestrator/campaign/s8c_preregistration.py:1465)、上限は 1024 [s8c_preregistration.py:100](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1250-decider-version-generation/orchestrator/campaign/s8c_preregistration.py:100)。

  timeout コメントは「generation が g2 以上」で再較正すると書く [s8c_preregistration.py:112](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1250-decider-version-generation/orchestrator/campaign/s8c_preregistration.py:112)。timeout は `git-timeout` として fail-closed になる [s8c_preregistration.py:951](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1250-decider-version-generation/orchestrator/campaign/s8c_preregistration.py:951)。
- **成果物への影響:** 連鎖面では g4 を正しく受理する。未較正 cap が不足すると freeze reason が `git-timeout` となり、certified 選択を誤って拒否する可能性はあるが、誤受理には倒れない。
- **推奨対応:** 本 wave では定数・コメントを変更しない。計算ノードで別タスクとして再較正し、結果が出るまで「再較正済み」と記録しない。候補検査で timeout が出た場合も cap 緩和で隠さない。

### A6 — 版束縛は registered 経路には効くが、certified 層や全経路を強制しない

- **主張:** この wave の成果物が効く層と効かない層は明確に分かれる。特に phase doc の「起動と受入へまだ結線されていない」という一括表現は、現コードの partial wiring に対して広すぎる。
- **根拠:**

  効く層:

  - g4 schema/version/history の妥当性と activation report。
  - `effective_at()` は false report なら capability を発行しない [s8c_preregistration.py:1800](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1250-decider-version-generation/orchestrator/campaign/s8c_preregistration.py:1800)。
  - registered launch は capability を再導出する [trial_registry.py:1318](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1250-decider-version-generation/orchestrator/campaign/trial_registry.py:1318)、正式 acceptance も同じ検査を再実行する [trial_registry.py:2408](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1250-decider-version-generation/orchestrator/campaign/trial_registry.py:2408)。
  - CLI は manifest の prereg commit に対して `effective_at()` を呼ぶ [p3_autonomous_workload_trial.py:3375](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1250-decider-version-generation/orchestrator/campaign/p3_autonomous_workload_trial.py:3375)。

  効かない層:

  - exploratory 経路は明示 opt-in で gate を通らず、ただし `certifying=False` である [trial_registry.py:1252](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1250-decider-version-generation/orchestrator/campaign/trial_registry.py:1252)。
  - registered admission と acceptance receipt も現状は `certifying=False` に固定される [trial_registry.py:1357](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1250-decider-version-generation/orchestrator/campaign/trial_registry.py:1357)、[trial_registry.py:2683](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1250-decider-version-generation/orchestrator/campaign/trial_registry.py:2683)。
  - bump 忘れと import 済み code bytes は D458 が明示した非保証である [decisions.md:19138](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1250-decider-version-generation/docs/decisions.md:19138)。
  - 外部 immutable anchor、実行 bytes、全経路配線は scope 外と文書自身も認める [phase3-8c-preregistration.md:299](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1250-decider-version-generation/docs/phase3-8c-preregistration.md:299)。

  指定された consumer test はすべて real HEAD ではなく、`effective=True` の synthetic report を作って `activation_report_at` を monkeypatch している [test_p3_autonomous_workload_trial.py:5248](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1250-decider-version-generation/orchestrator/tests/test_p3_autonomous_workload_trial.py:5248)、[test_reflux_origin_binding.py:101](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1250-decider-version-generation/orchestrator/tests/test_reflux_origin_binding.py:101)、[test_trial_registry.py:1203](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1250-decider-version-generation/orchestrator/tests/test_trial_registry.py:1203)。
- **成果物への影響:** g4 後も実 HEAD から capability は出ず、registered launch・acceptance は拒否を続ける。既存 synthetic consumer test の `decider-version-match` 期待値、certified 選択、receipt の `certifying` 値は変わらない。report digest 自体は変わるが、実発行 capability や台帳 row は生じない。
- **推奨対応:** wave 記録では「registered gate に partial wiring 済み、certified issuance は未実装」と層を分ける。phase doc の blanket 記述を直すなら protected doc の別改訂になるため、本 g4 へ無裁定で混ぜず裁定パッケージ化する。

### A7 — brief の「pin 閉包」検索は indirection を落としている

- **主張:** brief の検索結果は不完全。`output/README.md` と `legacy_prefix` はそもそも bytes pin ではなく、逆に core test に検索から漏れた実 literal pin がある。ただし「外部 raw-bytes manifest/trust root は無い」という最終結論は正しい。
- **根拠:** brief の主張は [s1-brief.md:74](/work/1/SFC/tanab/dev-wave-jobs/t1250-decider-version-generation/s1-brief.md:74)。`legacy_prefix` は旧誤配置 namespace が存在しないことを確かめる負の検査である [test_s8c_preregistration_invariant.py:134](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1250-decider-version-generation/orchestrator/tests/test_s8c_preregistration_invariant.py:134)。README は namespace の説明だけである [output/README.md:24](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1250-decider-version-generation/output/README.md:24)。一方 core test は `generation_path(1)` という indirection 経由で g1 の evidence/protected hash を literal pin している [test_s8c_preregistration_core.py:1159](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1250-decider-version-generation/orchestrator/tests/test_s8c_preregistration_core.py:1159)。`FROZEN_MANIFEST` には s8c record が含まれない [test_frozen_artifacts.py:41](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1250-decider-version-generation/orchestrator/tests/test_frozen_artifacts.py:41)。

  版束縛テストについては、tracked test 全件を `activation_report_at`、`DECIDER_VERSION`、version fields で検索した。real-repo invariant は legacy v1 可読性 [test_s8c_preregistration_invariant.py:164](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1250-decider-version-generation/orchestrator/tests/test_s8c_preregistration_invariant.py:164) と candidate report [test_s8c_preregistration_invariant.py:204](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1250-decider-version-generation/orchestrator/tests/test_s8c_preregistration_invariant.py:204) だけで、版一致 tests は `tmp_path` 合成 repo である [test_s8c_preregistration_core.py:1998](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1250-decider-version-generation/orchestrator/tests/test_s8c_preregistration_core.py:1998)。したがって「実 repo 版束縛 test は 0 本」は全件検索でも正しい。
- **成果物への影響:** g4、certified 選択、report、ledger の値への直接影響はない。pin 閉包の説明だけが不正確な nit だが、将来の変更影響検索を過小評価する。
- **推奨対応:** brief を「namespace reference」「semantic field pin」「raw record bytes pin」「外部 trust root」に分けて訂正する。検索には literal `condition-freeze` だけでなく `generation_path`、`FREEZE_DIR`、既知 hash literal を含める。

### A8 — [T-324] stale 判定は正しいが、`git cherry` 単独は証明にならず worklog も未整理

- **主張:** brief の結論「束ねる対象は無い」は正しい。しかし patch-id 等価性だけでは task 内容の着地証明にならない。また現在の worklog は [T-324] を「次の一手」に持ち越しており、台帳側は stale のままである。
- **根拠:** 現 HEAD の g2 record は revision reason に T-324 の G=2・還流・標本設計・正式起動形を明記する [condition-freeze.v1.g2.json:1](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1250-decider-version-generation/output/s8c-preregistration/condition-freeze/condition-freeze.v1.g2.json:1)。g3 record は T-1132/T-1133/T-1134 を明記し、g2 bytes hash を supersedes する [condition-freeze.v1.g3.json:1](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1250-decider-version-generation/output/s8c-preregistration/condition-freeze/condition-freeze.v1.g3.json:1)。さらに両 task commit について `git merge-base --is-ancestor <commit> HEAD` が 0 であり、branch 名だけでなく現 tree の record 内容も照合した。一方、worklog は現在も [T-324] を次タスクとして列挙する [worklog.md:2418](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1250-decider-version-generation/docs/worklog.md:2418)、[worklog.md:2431](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1250-decider-version-generation/docs/worklog.md:2431)。
- **成果物への影響:** 現 g4、certified 選択、report、ledger の値は変わらない。運用上は重複 wave や不要な衝突を招く scope 外 real 所見である。
- **推奨対応:** stale 判定の根拠を ancestry、現在の g2/g3 record、対象 doc 内容の三点に更新する。worklog carry から [T-324] を除く maintenance を別途行う。

## 総括

must-fix 候補:

- **A1:** g4 と g3 の field/condition contract 連続性、§5 exact status を検査し、整合的再生成による条件弱化を殺す。
- **A2:** brief の誤った evaluator baseline と report 差分を訂正する。`commit` と digest の変化も忘れない。
- **A7:** 実装阻害ではないが、段 3 記録へ残す「pin 閉包」の実測説明は修正が必要。

scope 外だが real な所見:

- **A5:** g2 以上で発火済みの git timeout 再較正債務。
- **A6:** registered gate は partial wiring 済みだが certified issuance、全経路強制、外部 anchor、bump 忘れ検出、import 済み bytes 束縛は未実装。phase doc の一括「未結線」表現も再裁定候補。
- **A8:** [T-324] は内容上 land 済みだが worklog carry が stale。

名目どおりの doc 追記、protected hash 変化、g4 supersedes、版束縛テスト自体には欠陥を認めなかった。現状の `effective` は、版 gate が match へ移っても §5 と全 12 predicate の双方で false を維持する。