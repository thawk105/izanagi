## 配置の択一

**結論は択 A を維持。ただし scope の記述と検査面を補正する必要がある。** Plan は `_validate_attempt` だけを変更し、codec を変更しないと明記しているため、説明と実装方針は一致している。[s2-plan.md:75-89](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2102-b4-reference-tps-domain/artifacts/t2102-b4-reference-tps-domain/s2-plan.md:75)

択 A の実際の波及は「seal だけ」ではない。

- in-memory 入力は `_normalize_attempts` から `_validate_attempt` へ到達するため、`scheduled_attempts_sha256`、seal、receipt 検査、registry 再構成がすべて狭まる。[p3_b4_analysis_ledgers.py:439-504](/work/1/SFC/tanab/izanagi/.codex/worktrees/dev-wave-t2102-b4-reference-tps-domain/orchestrator/campaign/p3_b4_analysis_ledgers.py:439) [同:634-675](/work/1/SFC/tanab/izanagi/.codex/worktrees/dev-wave-t2102-b4-reference-tps-domain/orchestrator/campaign/p3_b4_analysis_ledgers.py:634)
- 外部 registry JSONL は `_ratio_from_payload` 後に `_validate_attempt` を必ず通る。したがって `[1,3]` は択 A でも registry loader を通過できなくなる。[p3_b4_analysis_ledgers.py:387-436](/work/1/SFC/tanab/izanagi/.codex/worktrees/dev-wave-t2102-b4-reference-tps-domain/orchestrator/campaign/p3_b4_analysis_ledgers.py:387) [同:702-761](/work/1/SFC/tanab/izanagi/.codex/worktrees/dev-wave-t2102-b4-reference-tps-domain/orchestrator/campaign/p3_b4_analysis_ledgers.py:702)
- `generate_analysis_manifest` は先頭で registry を再構成するため、非有限十進を含む forged in-memory registry も選抜前に拒否する。[p3_b4_analysis_ledgers.py:1042-1067](/work/1/SFC/tanab/izanagi/.codex/worktrees/dev-wave-t2102-b4-reference-tps-domain/orchestrator/campaign/p3_b4_analysis_ledgers.py:1042)

一方、manifest-only の穴は実在する。

- `load_analysis_manifest` は `[1,3]` を `_ratio_from_payload` で復元し、正値であることしか見ない `_manifest_row_payload` で再 canonical 化する。[p3_b4_analysis_ledgers.py:931-989](/work/1/SFC/tanab/izanagi/.codex/worktrees/dev-wave-t2102-b4-reference-tps-domain/orchestrator/campaign/p3_b4_analysis_ledgers.py:931) [同:1100-1129](/work/1/SFC/tanab/izanagi/.codex/worktrees/dev-wave-t2102-b4-reference-tps-domain/orchestrator/campaign/p3_b4_analysis_ledgers.py:1100)
- Plan が落としている production surface として、公開関数 `assert_manifest_unchanged_before_run` も manifest を単独で 2 回 load する。等しい `[1,3]` manifest 同士なら択 A 後も通る。[p3_b4_analysis_ledgers.py:1262-1283](/work/1/SFC/tanab/izanagi/.codex/worktrees/dev-wave-t2102-b4-reference-tps-domain/orchestrator/campaign/p3_b4_analysis_ledgers.py:1262)
- ただし完全 publication は registry を先に load し、後段でも manifest を registry から再生成するため成立しない。[p3_b4_prerun_issuer.py:1046-1055](/work/1/SFC/tanab/izanagi/.codex/worktrees/dev-wave-t2102-b4-reference-tps-domain/orchestrator/campaign/p3_b4_prerun_issuer.py:1046) [同:1138-1150](/work/1/SFC/tanab/izanagi/.codex/worktrees/dev-wave-t2102-b4-reference-tps-domain/orchestrator/campaign/p3_b4_prerun_issuer.py:1138)
- 分析入口も registry を manifest より先に読み、完全性検査を行う。[p3_b4_analysis_path.py:199-240](/work/1/SFC/tanab/izanagi/.codex/worktrees/dev-wave-t2102-b4-reference-tps-domain/orchestrator/campaign/p3_b4_analysis_path.py:199)

択 B にすると `_ratio_payload` と `_ratio_from_payload` が registry と manifest の共用であるため、manifest-only reader/writer の受理集合まで縮む。[p3_b4_analysis_ledgers.py:279-302](/work/1/SFC/tanab/izanagi/.codex/worktrees/dev-wave-t2102-b4-reference-tps-domain/orchestrator/campaign/p3_b4_analysis_ledgers.py:279) [同:379,952,979](/work/1/SFC/tanab/izanagi/.codex/worktrees/dev-wave-t2102-b4-reference-tps-domain/orchestrator/campaign/p3_b4_analysis_ledgers.py:379)

裁定パッケージ候補は次の二択として明文化すべきである。

- **A 維持:** `_validate_attempt` を通る hash・seal・registry load・completeness・manifest generation を registry lifecycle として scope に含め、manifest-only loader と `assert_manifest_unchanged_before_run` は意図的に従来値域のまま残す。
- **B へ変更:** 上記 manifest-only surface も狭める。その場合は「registry only」と説明せず、codec 受理集合変更として再裁定する。

## 事前登録との関係

択 A は §5.1.1 の判定順序を変えない。純関数は引き続き `as_b4_exact_fraction(value) is not None and value > 0` だけを `reference_tps` の値域条件としている。[p3_b4_analysis_contract.py:233-253](/work/1/SFC/tanab/izanagi/.codex/worktrees/dev-wave-t2102-b4-reference-tps-domain/orchestrator/campaign/p3_b4_analysis_contract.py:233) [同:371-395](/work/1/SFC/tanab/izanagi/.codex/worktrees/dev-wave-t2102-b4-reference-tps-domain/orchestrator/campaign/p3_b4_analysis_contract.py:371)

したがって次が成立する。

- `Fraction(1,3)` は現在も純関数の正の exact rational であり、`reference_value_domain_error` ではない。
- 択 A 後の完全 artifact では registry load が先に失敗し、分析入口では `field_missing_or_ill_typed` に写る。これは registry admission の別層であり、純関数の `reference_value_domain_error` の集合変更ではない。[p3_b4_analysis_path.py:124-155](/work/1/SFC/tanab/izanagi/.codex/worktrees/dev-wave-t2102-b4-reference-tps-domain/orchestrator/campaign/p3_b4_analysis_path.py:124)
- 択 B でも純関数自体は変わらないが、manifest-only transport が `1/3` を純関数まで運べなくなるため、§5.1.1 が述べる入力値域と transport の能力がずれる。[preregistration.md:404-427](/work/1/SFC/tanab/izanagi/.codex/worktrees/dev-wave-t2102-b4-reference-tps-domain/docs/phase3-b4-reflux-ablation-preregistration.md:404)

`p3_b4_analysis_prereg_consumer.py` が抽出する literal・構造的事実に変化はない。ledgers について調べるのは manifest の first-n slice、violation 判定順、closure path tuple であり、`_validate_attempt` の値域は抽出対象ではない。[p3_b4_analysis_prereg_consumer.py:703-754](/work/1/SFC/tanab/izanagi/.codex/worktrees/dev-wave-t2102-b4-reference-tps-domain/orchestrator/campaign/p3_b4_analysis_prereg_consumer.py:703)

文書 bytes を変更しない限り、次の値も動かない。

- `preregistration_section_sha256`
- `semantic_section_sha256`
- consumer result の contract fields

両 section digest は §5.1.1 の文書 bytes だけから算出される。[p3_b4_analysis_prereg_consumer.py:394-407](/work/1/SFC/tanab/izanagi/.codex/worktrees/dev-wave-t2102-b4-reference-tps-domain/orchestrator/campaign/p3_b4_analysis_prereg_consumer.py:394) 説明は §5.1.1 を改稿せず、親 brief・insight・spool の registry admission 節へ置けばよい。

## source closure と凍結境界

独立検算した現行値は次のとおり。

- ledgers member SHA-256: `7476c81290a36346517968b375cad68cedf3620c8adc42807970c0115a23c152`
- closure receipt SHA-256: `57e84eeb4f8207ba9f4b6df704b2108c20592b2b129736d8462ec477bf4a384c`

両 literal を repository 全域で検索した結果は 0 件だった。親と plan の「literal pin なし」は正しい。member hash と receipt hash は live bytes から都度導出される。[p3_b4_analysis_path.py:503-536](/work/1/SFC/tanab/izanagi/.codex/worktrees/dev-wave-t2102-b4-reference-tps-domain/orchestrator/campaign/p3_b4_analysis_path.py:503)

path 以外も検査した。

- schema `"p3-b4-analysis-source-closure/v1"` の live 定義は analysis path のみ。[p3_b4_analysis_path.py:62](/work/1/SFC/tanab/izanagi/.codex/worktrees/dev-wave-t2102-b4-reference-tps-domain/orchestrator/campaign/p3_b4_analysis_path.py:62)
- dataclass `B4AnalysisSourceClosureReceipt` の field 全体から canonical bytes と hash を生成するが、その receipt を decode・admit・固定値比較する別 consumer はない。[p3_b4_analysis_path.py:81-99](/work/1/SFC/tanab/izanagi/.codex/worktrees/dev-wave-t2102-b4-reference-tps-domain/orchestrator/campaign/p3_b4_analysis_path.py:81)
- live な key→canonical path 束縛は production の 2 tuple と test の 2 tupleだけで、path/order pin であり hash pin ではない。[p3_b4_analysis_path.py:67-73](/work/1/SFC/tanab/izanagi/.codex/worktrees/dev-wave-t2102-b4-reference-tps-domain/orchestrator/campaign/p3_b4_analysis_path.py:67) [p3_b4_analysis_prereg_consumer.py:98-104](/work/1/SFC/tanab/izanagi/.codex/worktrees/dev-wave-t2102-b4-reference-tps-domain/orchestrator/campaign/p3_b4_analysis_prereg_consumer.py:98) [test_p3_b4_analysis_path.py:52-58](/work/1/SFC/tanab/izanagi/.codex/worktrees/dev-wave-t2102-b4-reference-tps-domain/orchestrator/tests/test_p3_b4_analysis_path.py:52) [test_p3_b4_analysis_prereg_consumer.py:27-33](/work/1/SFC/tanab/izanagi/.codex/worktrees/dev-wave-t2102-b4-reference-tps-domain/orchestrator/tests/test_p3_b4_analysis_prereg_consumer.py:27)
- archived mutation specs は path を key にするが、別箇所の old/new source snippet を固定する履歴成果物であり、closure digest consumer ではない。[mutation-spec-final.json:117-175](/work/1/SFC/tanab/izanagi/.codex/worktrees/dev-wave-t2102-b4-reference-tps-domain/output/insights/2026-08-27_t2001-b4-analysis-path/mutation-spec-final.json:117)

波及は限定される。

- ledgers の member SHA、closure canonical bytes、closure receipt SHA は必ず変わる。
- `preregistration_section_sha256`、consumer result、path tuple は変わらない。
- finite な既存 registry/manifest の canonical bytes、batch hash、選抜順、report 値はコード変更だけでは変わらない。
- 非有限十進を含む旧 registry が存在すれば、新 loader の受理集合から外れる。これは本 wave が意図する値域縮小である。
- repository 内に persisted closure receipt、golden、role binding は無いため repin 対象はない。repository 外の独自保存物だけは静的検索では否定できない。

## 呼び出し元の全数

direct call site の全数は次のとおり。definition、`__all__`、AST 上の関数名 lookup、monkeypatch 用文字列は数えていない。

| 関数 | direct call 数 | production / internal | test |
|---|---:|---|---|
| `_validate_attempt` | 3 | ledgers `:363,436,446` | 0 |
| `scheduled_attempts_sha256` | 5 | ledgers `:504`、prereg consumer `:797`、issuer `:725` | ledgers test `:64`、path test `:222` |
| `seal_scheduled_attempt_registry` | 9 | prereg consumer `:800`、issuer `:777` | ledgers test `:73,137,179,186`、path test `:225`、issuer test `:118,885` |
| `generate_analysis_manifest` | 15 | ledgers `:1143`、prereg consumer `:826`、issuer `:794` | ledgers test `:103,193,217,362,382,454,505,604,717`、path test `:246`、issuer test `:130,897` |

根拠は ledgers 内の 3 direct call である。[p3_b4_analysis_ledgers.py:362-446](/work/1/SFC/tanab/izanagi/.codex/worktrees/dev-wave-t2102-b4-reference-tps-domain/orchestrator/campaign/p3_b4_analysis_ledgers.py:362)

loader の direct caller も全数では次のとおり。

- `load_scheduled_attempt_registry`: production は analysis path `:130` と issuer `:1048`。test は ledgers `:153,346,645` と issuer `:231`。
- `load_analysis_manifest`: production は analysis path `:147`、issuer `:1049`、`assert_manifest_unchanged_before_run` `:1274,1275`。test は issuer `:234`。

非有限十進を渡した場合に変わる production 挙動は次のとおり。

- issuer の新規 issuance は最初の `scheduled_attempts_sha256` で落ち、`SCHEDULED_INPUTS_INVALID` へ写る。publication root 作成より前である。[p3_b4_prerun_issuer.py:724-741](/work/1/SFC/tanab/izanagi/.codex/worktrees/dev-wave-t2102-b4-reference-tps-domain/orchestrator/campaign/p3_b4_prerun_issuer.py:724)
- publication reload は registry loader で落ち、`ARTIFACT_MISMATCH` へ写る。[p3_b4_prerun_issuer.py:1046-1055](/work/1/SFC/tanab/izanagi/.codex/worktrees/dev-wave-t2102-b4-reference-tps-domain/orchestrator/campaign/p3_b4_prerun_issuer.py:1046)
- analysis path は registry load 失敗を `field_missing_or_ill_typed` へ写し、manifest を読まない。[p3_b4_analysis_path.py:124-150](/work/1/SFC/tanab/izanagi/.codex/worktrees/dev-wave-t2102-b4-reference-tps-domain/orchestrator/campaign/p3_b4_analysis_path.py:124)
- forged in-memory registry を `generate_analysis_manifest` へ直接渡しても、選抜前の completeness 検査で落ちる。
- prereg consumer の自己検査値は整数 `1000 + index` なので挙動は変わらないが、生成される closure receipt hash は変わる。[p3_b4_analysis_prereg_consumer.py:757-826](/work/1/SFC/tanab/izanagi/.codex/worktrees/dev-wave-t2102-b4-reference-tps-domain/orchestrator/campaign/p3_b4_analysis_prereg_consumer.py:757)

## 親 brief の欠陥

- **P1 の配置判断は妥当だが、「封印時のみ」は不正確。** `_validate_attempt` への追加は hash、外部 registry load、完全性検査、manifest generation にも効く。親の scope 外宣言は「関数本体を編集しない」という意味なら正しいが、「挙動も変わらない」という意味では誤り。[parent-brief.md:14-25](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2102-b4-reference-tps-domain/verbatim/parent-brief.md:14) [同:101-107](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2102-b4-reference-tps-domain/verbatim/parent-brief.md:101)

- **共有 helper が必ず `as_b4_exact_fraction` と結合するという懸念は refuted。** helper を contract に置けば D1424 違反になるが、共有すること自体が contract への配置を意味しない。独立実装を選ぶ実際の根拠は、producer 側防壁との故障独立性、producer を closure 外のまま保つこと、変更 scope を増やさないことにある。[parent-brief.md:56-58](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2102-b4-reference-tps-domain/verbatim/parent-brief.md:56) [p3_b4_raw_record_producer.py:31-65](/work/1/SFC/tanab/izanagi/.codex/worktrees/dev-wave-t2102-b4-reference-tps-domain/orchestrator/campaign/p3_b4_raw_record_producer.py:31)

- **有効な `None` 値域を plan が固定していない。** `reference_tps` は schema 上 optional で、非 `SCHEDULED` row では `None` が現行の正当な値である。新述語は `reference is not None` の場合だけ評価しなければならない。[p3_b4_analysis_ledgers.py:124-143](/work/1/SFC/tanab/izanagi/.codex/worktrees/dev-wave-t2102-b4-reference-tps-domain/orchestrator/campaign/p3_b4_analysis_ledgers.py:124) [同:341-358](/work/1/SFC/tanab/izanagi/.codex/worktrees/dev-wave-t2102-b4-reference-tps-domain/orchestrator/campaign/p3_b4_analysis_ledgers.py:341) Plan の `(1,10)` 正例だけでは、`None` を誤拒否する実装を殺せない。[s2-plan.md:75-81](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2102-b4-reference-tps-domain/artifacts/t2102-b4-reference-tps-domain/s2-plan.md:75)

- **「201 試行後に `EVIDENCE_SCHEMA`」は実コードと一致しない。** 非有限十進は `_fraction_token` の `ArithmeticError` から専用 code `DECIMAL_NOT_TERMINATING` へ写る。`EVIDENCE_SCHEMA` は `ValueError` 側である。[parent-brief.md:88-92](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2102-b4-reference-tps-domain/verbatim/parent-brief.md:88) [p3_b4_raw_record_producer.py:1541-1551](/work/1/SFC/tanab/izanagi/.codex/worktrees/dev-wave-t2102-b4-reference-tps-domain/orchestrator/campaign/p3_b4_raw_record_producer.py:1541) また repo には sanctioned runner が無く、publisher は attempt 単位の API なので「必ず 201 件を実走した後」という時点・件数も推論である。[p3_b4_analysis_path.py:11-16](/work/1/SFC/tanab/izanagi/.codex/worktrees/dev-wave-t2102-b4-reference-tps-domain/orchestrator/campaign/p3_b4_analysis_path.py:11)

- **443,911 と 2,010 は親自身の再測値ではない。** 親は明示的に「ユーザー提示の実測」と書いており、この点に虚偽はない。[parent-brief.md:76-77](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2102-b4-reference-tps-domain/verbatim/parent-brief.md:76) ただし 443,911 は recorded throughput の上位集合であり、実際の production scheduled batch は producer 不在で空集合である。[s4-ruling.md:28-37](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2102-b4-reference-tps-domain/verbatim/s4-ruling.md:28) したがって「既存 production artifact では発火しない」は真だが、target registry 上の非自明な発火実測ではない。

- M12 の must-fix 判断は正しい。raw producer は publication を disk から再 load するため、新 registry 検査後は非有限十進 publication が `_fraction_token` まで届かない。[p3_b4_raw_record_producer.py:561-585](/work/1/SFC/tanab/izanagi/.codex/worktrees/dev-wave-t2102-b4-reference-tps-domain/orchestrator/campaign/p3_b4_raw_record_producer.py:561) Plan の直接分岐検査と rejection mapping 検査への二分は妥当である。

## 所見一覧

- **real 候補 R1 — optional `None` の保存が plan に欠落。** 非 `SCHEDULED` row の `reference_tps=None` は現行 accepted domain であり、数値述語から除外する必要がある。根拠: `p3_b4_analysis_ledgers.py:139,279-281,341-358`、`s2-plan.md:75-81`。
- **real 候補 R2 — 択 A の全波及層が scope 表に入っていない。** hash、registry load、completeness、generate に効き、manifest-only の `assert_manifest_unchanged_before_run` には効かない。根拠: `p3_b4_analysis_ledgers.py:439-504,678-761,1042-1067,1262-1283`。
- **real 候補 R3 — 親の成果物影響説明の code と件数が誤り。** 実 code は `DECIMAL_NOT_TERMINATING` であり、201 試行後という保証も無い。根拠: `parent-brief.md:90-92`、`p3_b4_raw_record_producer.py:1541-1551`、`p3_b4_analysis_path.py:11-16`。
- **real 候補 R4 — closure identity は確実に動く。** member hash と receipt hash は変わるが、既存 literal consumer は 0 件。根拠: `p3_b4_analysis_path.py:503-536`、`test_p3_b4_analysis_path.py:596-634`。
- **refuted 候補 F1 — 択 A では完全 artifact が manifest codec を迂回して受理される。** registry-first load と exact regeneration により refuted。根拠: `p3_b4_analysis_path.py:217-240`、`p3_b4_prerun_issuer.py:1046-1055,1138-1150`。
- **refuted 候補 F2 — 本 wave で §5.1.1 の判定順序・literal・section digest が動く。** 文書、contract、consumer 抽出対象を変更しないため refuted。根拠: `p3_b4_analysis_prereg_consumer.py:394-520,703-754`。
- **refuted 候補 F3 — closure の member/receipt digest を literal pin する live ledger、test、golden がある。** 現行 2 hash の全域検索はともに 0 件。根拠となる生成面: `p3_b4_analysis_path.py:503-536`。
- **refuted 候補 F4 — helper 共有は必ず `as_b4_exact_fraction` と結合する。** 配置次第であり必然ではない。根拠: `p3_b4_analysis_contract.py:233-253`、`p3_b4_analysis_ledgers.py:26-35`。
- **疑い — repository 外に保存済み closure receipt がある可能性。** repository 内には loader・admission consumer がなく判定不能。根拠: public producer `p3_b4_analysis_prereg_consumer.py:1092-1101` と receipt assembler `p3_b4_analysis_path.py:481-536`。

## 総括

択 A 自体は妥当で、plan の説明と予定差分は codec を狭めない点で一致している。
ただし author 前に、optional `reference_tps=None` を保存する条件と正例を must-fix とすべきである。
また A の実効範囲を hash・registry load・completeness・generate まで明記し、manifest-only surface は意図的な scope 外として裁定する必要がある。
closure の新しい identity は動くが、repository 内に repin 対象や既存 closure receipt は無い。
親の `EVIDENCE_SCHEMA` と「201 試行後」という成果物影響説明は訂正が必要である。pytest は実行しておらず、緑は主張しない。