# 敵対レビュー（レンズ A: 正しさ境界）

**判定: NO-GO。** `contract_sha256` の g1 golden 自体を変える直接経路は見つからないが、計画中の型は権限として偽造可能で、history resolver は実 consumer に一度も結線されず、transition gate も本番世代列では発火不能である。静的読解のみで、pytest は実走していない。

## 所見

[severity: must-fix] [攻撃シナリオ] `CurrentContract` は公開 dataclass なので、`HistoricalContract` の中身を `CurrentContract(generation=h.generation, contract=h.contract)` で再包装できる。`dataclasses.replace(require_current(...), contract=h.contract)` でも同じであり、`type(value) is CurrentContract` は生成権限を証明しない。さらに内包 raw contract の nested 型は現行 `isinstance` 検査なので、追加 field を持つ `CalibrationRef` subclass を exact `ExecutionEnvironmentContract` に入れ、`asdict()` の canonical object 自体を拡張できる。[根拠 `/work/1/SFC/tanab/dev-wave-jobs/t419-u2-contract-generation/s2-plan.md:26-57`; `orchestrator/campaign/env_contract.py:130-160`; `orchestrator/campaign/pipeline.py:745-752`; `orchestrator/campaign/buildcache.py:635-650`] [提案] 全 issuer で canonical singleton との同一性または `require_current(env_tag, contract_sha256=...)` による再検証を行い、公開 constructor・`replace()`・nested subclass で作った forged Current を副作用前に拒否するテストを置く。型だけでなく A′-5 相当の capability/receipt を要求する。

成果物影響: g2 導入後も g1 を Current として build・receipt・certified pipeline に流せ、build cache namespace と execution receipt が旧 SHA のまま「current」として受理される。

[severity: must-fix] [攻撃シナリオ] production の contract gate は全入口を覆わない。`run_campaign()` は `env_contract=None` を既定とし、`_authorize_measurement()` は型検査前に `None` を返す。plan もこの legacy 分岐を維持する一方、実際の P3 loop は contract を渡さず、結果を `certified` として返せる。[根拠 `orchestrator/campaign/loop.py:62-70,101-116,139-145`; `orchestrator/campaign/p3_s4_loop.py:730-745`; `/work/1/SFC/tanab/dev-wave-jobs/t419-u2-contract-generation/s2-plan.md:192-195`; `output/insights/2026-08-05_t478-calibration-contract-generation/README.md:76-80`] [提案] certified を発行できる全 caller で `CurrentContract` を必須化し、最初の layout/WAL 書込み前に検証する。今回は scope 外にするなら、A′-3 を「production 全入口の権限 gate」と数えず、該当経路を明示的に未防護とする。

成果物影響: `execution_receipt=None` のまま WAL に commit が入り、contract SHA を含まない同一 campaign ID/layout に g1・g2 の certified 値が混在する。

[severity: must-fix] [攻撃シナリオ] history resolver の production 利用が 0 件なので、元の破断は解消しない。g2 が current になると、旧 floor protocol の g1 hash は `require_current(env_tag)` の g2 hash と比較されて拒否され、旧 oracle manifest も report loader で同様に拒否される。[根拠 `/work/1/SFC/tanab/dev-wave-jobs/t419-u2-contract-generation/s2-plan.md:156-182`; `orchestrator/campaign/s8b_floor_contract.py:138-151`; `orchestrator/campaign/s8b_floor_campaign.py:308-324`; `orchestrator/campaign/s8b_oracle_report.py:1189-1208`] [提案] artifact の構造・履歴検証は、artifact 自身の hash を `resolve_by_contract_sha256(..., expected_env_tag=...)` へ渡して `HistoricalContract` で行う。その後、live launch/current eligibility だけを別の `require_current()` gate で判定する。

成果物影響: g2 登録直後、旧 floor protocol と oracle manifest が report/ratified 検証から脱落し、proof chain と材料レポートが `unresolved` のままになる。

[severity: must-fix] [攻撃シナリオ] transition の条件が「差分非空かつ許可 pointer 集合の部分集合」なので、同じ calibration path のまま SHA だけを替える successor が通る。その path の bytes を g2 用に上書きすれば、current だけを走査する calibration test は g2 を検証して通る一方、g1 の bytes は失われる。[根拠 `/work/1/SFC/tanab/dev-wave-jobs/t419-u2-contract-generation/s2-plan.md:59-68`; `orchestrator/tests/test_env_contract.py:434-436`; `orchestrator/campaign/env_attestation.py:811-828`; `output/insights/2026-08-05_t478-calibration-contract-generation/README.md:166-172`] [提案] 少なくとも「同一 path なら SHA も同一」を必須にし、U-2 の新較正では path/SHA の対を原子的に変更する。独立テストは `REGISTRY` でなく全 `GENERATIONS` の path 実在・bytes SHA・path 再利用禁止を検査する。

成果物影響: resolver は g1 contract を返せても calibration bytes の SHA が一致せず、旧 certified 選択・report・台帳参照が履歴検証不能になる。

[severity: must-fix] [攻撃シナリオ] transition predicate の単体正例は書けるが、実際の全世代列は g1 一件なので production の隣接世代検査は本 wave では一度も発火しない。plan の synthetic test は predicate 本体だけを検査するため、初期化から predicate 呼出しを削除しても全テストが通り得る。[根拠 `/work/1/SFC/tanab/dev-wave-jobs/t419-u2-contract-generation/s2-plan.md:7-14,112-120,257-260`; `/work/1/SFC/tanab/dev-wave-jobs/t419-u2-contract-generation/brief.md:21-24`] [提案] 実際の初期化が使う validator に synthetic 2 世代 mapping を通す正例・負例を置き、初期化との結線削除も kill する。そこまで入れないなら「本 wave では production 発火不能」と明記し、A′-2 を実装済み gate と数えない。

成果物影響: 結線が欠落したまま将来 g2 の `attestation_mode` 等が変わると、その g2 が current 化され、attestation を外した run が certified 集合へ入る。

[severity: should-fix] [攻撃シナリオ] 「g1 hash が同じだから受理集合も同じ」は一般には成り立たない。現行 `build_v2()` は任意の `ExecutionEnvironmentContract` を受け、テストも二つの synthetic contract で completion manifest と namespace を生成する。planned exact Current 化はこの低水準 API の受理集合を縮める。[根拠 `orchestrator/campaign/buildcache.py:600-601`; `orchestrator/tests/test_buildcache_v2.py:129-140,330-340`; `/work/1/SFC/tanab/dev-wave-jobs/t419-u2-contract-generation/s2-plan.md:186-191`] [提案] 不変と主張する集合を「登録済み g1 を使う既存 certified flow」に限定し、build/receipt API の意図的な受理縮小を別途列挙する。g1 canonical bytes は現行 golden `orchestrator/tests/test_env_contract.py:691-743` を一切変更しない。

[severity: should-fix] [攻撃シナリオ] `ec.lookup()` を機械的に `require_current()` へ置換すると、`test_contract_is_frozen` は hash 対象の raw `ExecutionEnvironmentContract` ではなく wrapper の frozen 性だけを検査するようになる。raw dataclass から `frozen=True` が失われても wrapper への代入は失敗し、テストが緑になり得る。また buildcache の synthetic raw contract を public `CurrentContract` で包む追随は、forged Current を正例化する。[根拠 `orchestrator/tests/test_env_contract.py:272-275`; `/work/1/SFC/tanab/dev-wave-jobs/t419-u2-contract-generation/s2-plan.md:227-235`; `orchestrator/tests/test_buildcache_v2.py:129-140,838-855`] [提案] raw contract と wrapper の frozen test を分離する。cache namespace test は正規 `require_current()` 由来の二契約を使い、synthetic/History/`replace()` Current は production API の負例にする。

[severity: should-fix] [攻撃シナリオ] env-literal 免除は名前が同じでも実質範囲が広がる。検査機構は `_build_registry` の FunctionDef 部分木を丸ごと免除し、plan はその本体へ世代 tuple と wrapper 構築を追加する。また禁止集合に generation 固有の calibration path/SHA/contract SHA が無いため、それらを consumer に直書きしても検出しない。[根拠 `orchestrator/campaign/env_contract.py:220-244`; `orchestrator/tests/test_env_contract.py:48-51,67-86,797-805`; `/work/1/SFC/tanab/dev-wave-jobs/t419-u2-contract-generation/s2-plan.md:209-223`] [提案] 免除関数の許可 AST shape を固定し、独立 generation golden が列挙する calibration path/SHA/contract SHA も production module の禁止 literal に加える。免除名が一つというだけで「穴を広げていない」と数えない。

[severity: nit] [攻撃シナリオ] 親の狭い実測、すなわち production `env_attestation.probe()` が `/proc/cpuinfo` を一度だけ読むことは正しい。しかし「方式 α は未実装」という一般化は広すぎる。T-419 probe には K=5、CPU pin rotation、論理 CPU ごとの累積最小が既に実装されている。[根拠 `orchestrator/campaign/env_attestation.py:404-451`; `tools/pegasus/probes/t419_probe_causality.py:301-350,4012-4053`; 同ファイル `:189-218`] [提案] 「production attestation への方式 α 結線が未実装」と書き直し、後続 wave は既存 pure function/rotation logic を再利用する。ただし同 probe は明示的に non-certifying/counterfactual-only なので、U-2 entry condition は依然未成立である。[根拠 `tools/pegasus/probes/t419_probe_causality.py:3800-3804`]

## scope 外に置かれた層

以下は実装済みと数えず、段 4 の裁定パッケージへ返す必要がある。

- A′-4 activation authority — `REGISTRY = 各列の末尾` だけでは pending・rejected・直接追加 g2 と active g2 を区別できない。
- A′-5 全入口 activation receipt — 同一 migration epoch/bundle の証明、forged Current、`env_contract=None`、副作用前拒否を防げない。
- A′-6 campaign identity — 現行 preimage は env/contract を含まないため、g1/g2 の WAL・layout 混在を防げない。[根拠 `orchestrator/campaign/ident.py:125-144`]
- A′-7 versioned predicate dispatch — hash から値を得ても、旧 predicate で proof chain を再計算できず `historically_verified` を保証できない。
- A′-8 shell 結線 — wrapper は旧 protocol path を固定しており、検証済み generation bundle の選択を強制できない。[根拠 `tools/pegasus/floor_campaign.sh:880-895`]
- A′-9 の残り — generation key/hash の独立 golden だけでは、bundle role、record 非空性、closure completeness の自己申告を防げない。
- 方式 α・accepted publish receipt・self-comparison・pin closure — 有効な g2 を生成できず、実世代遷移を一度も exercise できない。[根拠 `output/insights/2026-08-05_t478-calibration-contract-generation/README.md:205-216`]
- historical retention — 旧 calibration、source commit、git object、legacy evidence bytes の削除・貼り替えを型では防げない。[根拠 同 README `:166-172`]
- T-126 closure — control は contract SHA を持たず、attestation payload も profile SHA だけなので、series/result/receipt を世代へ束縛できない。[根拠 `orchestrator/qualification/t126_control_v1.json:7-14`; `orchestrator/qualification/t126_driver.py:439-456`]
- 8c/P3 prereg・trial registry — 凍結 evidence contract は削除予定の `lookup(env_tag)` を参照したままで、将来の trial acceptance を generation へ束縛できない。[根拠 `orchestrator/campaign/s8c_preregistration_evidence_contract.v1.json:430-486`]

## (P1) の裁定

[severity: must-fix] [攻撃シナリオ] A′-4/A′-5 を外しながら `CurrentContract` を権限型と呼び、各列末尾を自動 current 化する判断は、この形のままでは誤りである。独立 golden は source と test の同時更新を止めず、accepted publish receipt のない g2 でも末尾へ追加すれば current になる。これは「直接追加した calibration は activation 不能」という設計正本と矛盾する。[根拠 `/work/1/SFC/tanab/dev-wave-jobs/t419-u2-contract-generation/s2-plan.md:11-14,112-120,269-271`; `output/insights/2026-08-05_t478-calibration-contract-generation/README.md:146-151,214-216`] [提案] 次のいずれかを裁定する。

- A′-4/A′-5 を両方入れる。
- 両方外すなら `len(generations) == 1` の bootstrap fuse を置き、wrapper を権限 gate と数えない。
- 片方だけなら、静的 g1 registry から bootstrap receipt を発行して全入口で要求する **A′-5 単独**だけが防御的である。A′-4 単独は trust root を外部 record へ移すだけなので採用不可。

成果物影響: publish/closure を通っていない g2 が Current となり、その SHA が build cache、execution receipt、certified 台帳へ正規値として記録される。

## 総括

- 最重症は、公開 dataclass の再包装で Historical を Current に偽造でき、A′-3 が権限分離になっていないこと。
- history resolver の利用が 0 件なので、g2 後も旧 floor/oracle proof chain は解決されず、親 brief の成果物効果は成立しない。
- transition は実世代列で発火不能なうえ、同一 path・新 SHA を許して g1 calibration bytes を失わせる。
- P1 は A′-4 単独を避ける点だけ正しい。両方外すなら g2 fail-closed fuse と「gate 未実装」の明記が land 条件である。