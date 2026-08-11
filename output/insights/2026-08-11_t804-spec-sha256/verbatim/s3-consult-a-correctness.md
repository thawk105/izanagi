## 総括

**NO-GO。**

official manifest branchの `schedule` / `campaign_ids` / `run_contract` / `binding_identity` / `allowed_excluded_reasons` の再導出照合は、受理集合を実際に狭める。しかし wave 全体では次が残る。

- judge の `spec_sha256 == module pin` は、正しい公開 pin を書くだけで満たせる。
- report の legacy branch は現在も `verify_manifest` を通らず official observations を生成する。
- 提案された AST pin は loader-only consumer を検出しない。
- P5 は明示裁定に反して generic builder を過剰拒否する。
- `generator_versions` 変異は既存 validator に先に拒否され、DW-M01 の単一帰属を満たさない。

書き込み・pytest・build は実施していない。以下は静的検査結果のみ。

## 所見

- **所見 1**: judge の pin 一致検査は迂回者にとって恒真であり、certified 選択まで provenance が繋がらない

  - 分類: BLOCKER
  - 根拠: [worklog.md:2957](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t804-spec-sha256/docs/worklog.md:2957) は「`driver / report / judge の全層で再検証する`」と裁定している。一方、[plan.md:180](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t804-spec-sha256/s2/plan.md:180) は「`judge にできるのは pin 連続性の検査だけで、manifest 内容の再導出や observations の真正性証明はできない`」と明記する。[s8b_oracle_artifacts.py:45](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t804-spec-sha256/orchestrator/campaign/s8b_oracle_artifacts.py:45) も OfficialObservations/OfficialVerdict を「`provenance 検証済みであることは意味しない`」marker と定義する。judge CLI は [s8b_oracle_judge.py:290](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t804-spec-sha256/orchestrator/campaign/s8b_oracle_judge.py:290) の `load_official_observations` の直後に `judge_oracle` を呼ぶだけである。さらに combined は [s8b_verdict.py:827](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t804-spec-sha256/orchestrator/campaign/s8b_verdict.py:827) の `load_official_verdict` から直接判定へ進む。現在のテスト自身も [test_s8b_oracle_judge.py:53](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t804-spec-sha256/orchestrator/tests/test_s8b_oracle_judge.py:53) で marker を手書きし、[同:71](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t804-spec-sha256/orchestrator/tests/test_s8b_oracle_judge.py:71) で determinate な winner を得ている。計画後も、この入力へ公開された正しい `spec_sha256` を一項足せば新検査を満たす。また judge は I/O をしないため、pin が非 `None` なら spec file が欠落・改竄していても検出しない。
  - 成果物影響: 迂回者は正しい pin と自己整合した任意の rows/medians を持つ observations を与え、既知構成の `winner_configuration_id` を操作できる。さらに任意の official-verdict JSON を combined へ直接渡せるため、`oracle_floor_exceeded`、combined `status`、`oracle_manifest_sha256` 参照まで変更できる。budget ledger はこの経路では変更されない。
  - 対処案: judge に manifest・freeze・approved spec を渡し、`load_approved_spec` と `verify_manifest` を実際に呼ばせ、observations の `manifest_sha256` / `spec_sha256` をその VerifiedManifest に束縛する。verdict→combined にも verified upstream identity を再束縛する。正しい公開 pin を持つ手書き observations/verdict が拒否される負例を必須にする。

- **所見 2**: P4 の AST pin は choke point を逆向きに数えており、既存 legacy bypass すら検出しない

  - 分類: BLOCKER
  - 根拠: [plan.md:189](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t804-spec-sha256/s2/plan.md:189) は「`verify_manifest call の module 集合`」だけを `{driver, report}` に固定する。しかし loader は [s8b_oracle_artifacts.py:131](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t804-spec-sha256/orchestrator/campaign/s8b_oracle_artifacts.py:131) で「`schema classifier`」「`full verification は行わない`」と明記され、schema 欠落または run_contract 欠落を LegacyManifest として返す。report は [s8b_oracle_report.py:1750](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t804-spec-sha256/orchestrator/campaign/s8b_oracle_report.py:1750) で loader を呼び、OfficialManifest の場合だけ `verify_manifest`、その後は branch 外で `build_observations` と出力を行う。実在テスト [test_s8b_oracle_report.py:1293](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t804-spec-sha256/orchestrator/tests/test_s8b_oracle_report.py:1293) は `test_cli_legacy_skips_freeze_resolution`、[同:1314](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t804-spec-sha256/orchestrator/tests/test_s8b_oracle_report.py:1314) は `rc == 0` と output 実在を要求する。新しい loader-only consumer を足しても verify caller 集合は不変なので、P4 の検査は緑のままである。
  - 成果物影響: schema-less/run_contract-less manifest が spec/freeze reverify なしで report の受理集合に残り、`manifest_kind="legacy"` の OfficialObservations、rows、n、manifest hash が生成される。計画の `spec_sha256=None` は judge での偶発的 fail-close に依存し、report 層自身の再検証保証にはならない。
  - 対処案: 検査を反転し、`load_official_manifest` の全 production consumer が canonical verifier に支配されることを固定する。より堅い形は、report official API を VerifiedManifest 専用にし、legacy 出力を別 schema/type に分離すること。AST では verify caller ではなく loader/raw marker constructor/official sink を列挙する。

- **所見 3**: standalone gate の既存 `verified_manifest` 注入口が、required spec 引数を迂回する

  - 分類: MAJOR
  - 根拠: [s8b_oracle_driver.py:314](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t804-spec-sha256/orchestrator/campaign/s8b_oracle_driver.py:314) は `verified_manifest: Optional[...] = None` を持つ。[同:333](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t804-spec-sha256/orchestrator/campaign/s8b_oracle_driver.py:333) は「`与えた場合は manifest を再検証・再読込せず`」とし、[同:445](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t804-spec-sha256/orchestrator/campaign/s8b_oracle_driver.py:445) は `verified_manifest is None` の場合にしか verifier を呼ばない。この注入口は [同:460](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t804-spec-sha256/orchestrator/campaign/s8b_oracle_driver.py:460) の公開 `gate_check` にも露出しており、exact type・manifest path/hash の束縛が無い。
  - 成果物影響: 任意の非 `None` object を渡した standalone gate の受理集合が狭まらず、spec 不一致 manifest に対して `allowed=True` を返し得る。実走 `run_block` は [同:1124](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t804-spec-sha256/orchestrator/campaign/s8b_oracle_driver.py:1124) で先に verify し、ledger は [同:1249](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t804-spec-sha256/orchestrator/campaign/s8b_oracle_driver.py:1249) なので、production ledger の直接迂回は確認しなかった。
  - 対処案: 公開 `gate_check` から `verified_manifest` を除去し、run flow 専用 private 関数だけに閉じる。少なくとも exact VerifiedManifest type、指定 path の canonical hash、approved spec identity を再束縛する。

- **所見 4**: spec は一回 read だが、freeze と同等の immutable snapshot ではない

  - 分類: MAJOR
  - 根拠: [plan.md:108](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t804-spec-sha256/s2/plan.md:108) は「`事後変更した object も verifier の権威にはならない`」と主張する。しかし [s8b_oracle_spec.py:51](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t804-spec-sha256/orchestrator/campaign/s8b_oracle_spec.py:51) の `@dataclass(frozen=True)` が固定するのは属性再代入だけで、`document` と `schedule` は Mapping のままである。[同:153](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t804-spec-sha256/orchestrator/campaign/s8b_oracle_spec.py:153) は mutable な `copy.deepcopy` を返し、[同:189](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t804-spec-sha256/orchestrator/campaign/s8b_oracle_spec.py:189) がそのまま保持する。対して freeze は [s8b_ratified_freeze.py:717](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t804-spec-sha256/orchestrator/campaign/s8b_ratified_freeze.py:717) で dict→MappingProxyType、list→tuple の「`再帰 immutable 化`」を行う。
  - 成果物影響: helper 検証後から各 projection 比較までに同一 object の nested dict/list が変更されると、schedule、campaign ID、run contract 等が単一の検証済み snapshot ではなくなる。manifest の受理・拒否と、その後の ledger/report 参照が異なる authority 状態を観測し得る。
  - 対処案: ReviewedSpec も再帰 immutable 化するか、helper が raw bytes から作った immutable normalized snapshot を返し、以後の全比較をその戻り値だけで行う。元の `approved_spec.document/schedule` を検証後に再参照しないことを契約化する。

- **所見 5**: `generator_versions` の新 deep-equality と変異は既存 validator に包含される

  - 分類: MAJOR
  - 根拠: plan は [plan.md:105](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t804-spec-sha256/s2/plan.md:105) で spec helper が `validate_reviewed_spec` を再利用し、[同:121](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t804-spec-sha256/s2/plan.md:121) で generator mapping をさらに比較する。spec validator は既に [s8b_oracle_spec.py:137](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t804-spec-sha256/orchestrator/campaign/s8b_oracle_spec.py:137) で `_validate_generators` を呼び、manifest verifier も projection 比較より前の [s8b_oracle_manifest.py:1070](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t804-spec-sha256/orchestrator/campaign/s8b_oracle_manifest.py:1070) で同じ関数を呼ぶ。その関数は [同:448](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t804-spec-sha256/orchestrator/campaign/s8b_oracle_manifest.py:448) で role ごとの canonical path、[同:465](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t804-spec-sha256/orchestrator/campaign/s8b_oracle_manifest.py:465) で実 byte hash を強制する。安定した同一 root では、両側に異なるが個別には有効な mapping は存在しない。
  - 成果物影響: この projection について受理集合は狭まらない。plan の `generator-versions` 変異は既存 `_validate_generators` が先に拒否し、新 spec-binding gate の赤理由にならない。
  - 対処案: `generator_versions` を新規 shrink の証拠から外して defense-in-depth と明記する。変異を残すなら source 差替え TOCTOU 専用に再定義する。それ以外の各変異も「旧 verifier では受理、新 gate 有効時だけ拒否」の正例対を固定する。

- **所見 6**: P5 は generic builder を過剰拒否し、同時に extra-key 変異を二重決定する

  - 分類: BLOCKER
  - 根拠: [plan.md:132](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t804-spec-sha256/s2/plan.md:132) は共有 `_validate_run_contract` を exact-key 判定へ変更する。しかし generic builder は [s8b_oracle_manifest.py:753](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t804-spec-sha256/orchestrator/campaign/s8b_oracle_manifest.py:753) で同じ helper を呼ぶ。既存裁定 [decisions.md:13181](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t804-spec-sha256/docs/decisions.md:13181) は「`生成側の generic builder の受理集合は変えない`」、[同:13193](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t804-spec-sha256/docs/decisions.md:13193) は generic builder への gate を「`既存 programmatic caller の受理集合を狭め、互換を壊す`」として明示的に却下している。また plan は run_contract deep equality も [plan.md:118](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t804-spec-sha256/s2/plan.md:118) に持つため、extra key は P5 を無効化しても後段比較で拒否される。[mutation.md:7](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t804-spec-sha256/docs/dev-wave/mutation.md:7) の「`同じ入力を拒否する層が前後に無いこと`」に反する。
  - 成果物影響: 現在受理される余剰 metadata key 付き programmatic builder 入力が manifest 生成前に拒否され、既存 producer/API の受理集合を T-804 の verifier 境界外で狭める。serialized extra-key 変異は新 spec 比較との二重拒否になり、kill 帰属も成立しない。
  - 対処案: shared helper は現状の必須-key判定のまま残し、approved-spec との exact equality を `verify_manifest` 内だけで行う。generic builder の余剰 key 正例を DW-M01 の過剰拒否検査として追加する。shared helper を変えるなら D288 を supersede する明示裁定と schema/API versioning が必要。

- **所見 7**: 「凍結 bytes の pin 閉包は影響ゼロ」は範囲を広げると誤り

  - 分類: MINOR
  - 根拠: brief は [brief.md:39](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t804-spec-sha256/output/insights/2026-08-11_t804-spec-sha256/brief.md:39) で「`凍結 bytes の pin 閉包 = 影響ゼロ`」とする。確かに [test_frozen_artifacts.py:38](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t804-spec-sha256/orchestrator/tests/test_frozen_artifacts.py:38) の FROZEN_MANIFEST に対象 source path は無い。しかし [test_s8b_oracle_manifest.py:79](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t804-spec-sha256/orchestrator/tests/test_s8b_oracle_manifest.py:79) の独立 `PIN_GATE_SPEC_RAW` は path ではなく `artifacts` / `judge` / `report` role の下に source SHA-256 を埋め込む。plan 自身も [plan.md:257](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t804-spec-sha256/s2/plan.md:257) でその更新を必要としている。`review_ledger.py` の role-name keyed mapも確認したが、そこには oracle role の pin は無かった。
  - 成果物影響: 凍結 output bytes と live artifacts は変わらないが、独立 reviewed-spec golden と `PIN_GATE_SPEC_SHA256` は変わる。「pin 閉包ゼロ」のままでは更新理由・レビュー参照を取りこぼす。
  - 対処案: 「frozen artifact bytes への影響ゼロ」と「test/review pin closure は非ゼロ」を分けて記録する。

## choke point 実査

| 到達先 | 実経路 | `verify_manifest` |
|---|---|---|
| budget ledger | driver `run_block` → verify → gate → `create_ledger` | 通る |
| official report | report loader → OfficialManifest branch | 通る |
| legacy report | report loader → LegacyManifest branch → OfficialObservations | **通らない** |
| oracle 選択 | observations loader → judge | **通らない** |
| combined verdict | verdict loader → `judge_combined` | **通らない** |

`load_official_manifest` の production 呼出しは [s8b_oracle_report.py:1750](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t804-spec-sha256/orchestrator/campaign/s8b_oracle_report.py:1750) の1箇所だけだった。test-only 参照は以下の全件で、production sink ではない。

- `test_s8b_oracle_artifacts.py`: 95, 106, 120, 131, 175, 179, 180, 194
- `test_s8b_oracle_report.py`: 256, 914, 945, 958, 1064, 1182, 2888

したがって `verify_manifest` は ledger 経路の choke point ではあるが、report全体・judge・combined を含む成果物チェーンの choke point ではない。

## 親の実測値の独立裏取り

| 親の主張 | 判定 | 裏取り |
|---|---|---|
| `n` / `master_seed` / `block_sizes` / `campaign_ids` は freeze 束縛から完全に自由 | **real（freeze 束縛について）** | [s8b_oracle_manifest.py:276](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t804-spec-sha256/orchestrator/campaign/s8b_oracle_manifest.py:276) は自己整合のみ、freeze との比較は [同:1036](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t804-spec-sha256/orchestrator/campaign/s8b_oracle_manifest.py:1036) の cell 集合だけ。campaign ID も [同:1052](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t804-spec-sha256/orchestrator/campaign/s8b_oracle_manifest.py:1052) の1対1・非空・一意のみ。ただし「無制約」ではなく、n正整数、単一block、行完全性等は既存検査される。 |
| run contract で自由なのは4項目だけ | **refuted（逐語）** | 定義済み9 keyの中では real だが、[同:395](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t804-spec-sha256/orchestrator/campaign/s8b_oracle_manifest.py:395) の部分集合判定と [同:425](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t804-spec-sha256/orchestrator/campaign/s8b_oracle_manifest.py:425) の全 dict 保存により、任意の余剰 key も自由。さらに実走では [s8b_oracle_driver.py:766](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t804-spec-sha256/orchestrator/campaign/s8b_oracle_driver.py:766) が env_tag、contract hash、clocks を外部 authority に束縛する。 |
| manifest run_contract は部分集合、spec は完全一致 | **real** | manifest は [s8b_oracle_manifest.py:395](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t804-spec-sha256/orchestrator/campaign/s8b_oracle_manifest.py:395) の `<=`、spec は [s8b_oracle_spec.py:113](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t804-spec-sha256/orchestrator/campaign/s8b_oracle_spec.py:113) の `set(...) != _RUN_CONTRACT_KEYS`。 |
| judge は `verify_manifest` を呼ばない | **real** | [s8b_oracle_judge.py:287](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t804-spec-sha256/orchestrator/campaign/s8b_oracle_judge.py:287) の main は observations loader と judge のみ。 |
| 両 output dir 不在、pin None、live artifact 移行なし | **real（tracked repo 範囲）** | working tree と `git ls-tree -r HEAD` の双方で2 directory は0件。[s8b_oracle_spec.py:18](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t804-spec-sha256/orchestrator/campaign/s8b_oracle_spec.py:18) が fixed path、[同:22](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t804-spec-sha256/orchestrator/campaign/s8b_oracle_spec.py:22) は `APPROVED_SPEC_SHA256 = None`。 |
| 凍結 bytes の pin 閉包に影響ゼロ | **refuted（無限定の主張）** | frozen output bytes だけなら real。しかし role-keyed `PIN_GATE_SPEC_RAW` が artifacts/judge/report の source hash を固定しており、plan自身が更新を認める。 |

結論として、P1/P2 と official manifest の主要 projection 比較は維持可能だが、P3・P4・P5を現案のまま段4へ渡してはならない。