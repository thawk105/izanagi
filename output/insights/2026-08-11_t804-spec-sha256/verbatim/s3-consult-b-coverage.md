## 総括

**NO-GO。** 静的読了のみで、テストは実走していない。コード変更は 0 byte。

driver の standalone gate / `run_block`、official report、oracle judge までは計画されているが、certified 結論を作る `s8b_verdict.judge_combined` が未被覆である。さらに、P4 の検査は静的 pin と negative test だけでは実効性を証明できず、Legacy 経路と judge の純関数性にも未解消点がある。

## 層の再計数

| 層 | 実効性 |
|---|---|
| `s8b_oracle_manifest` | approved spec と manifest projection の choke point |
| `s8b_oracle_driver` | standalone gate、`run_block`、WAL、budget ledger |
| `s8b_oracle_report` | official report。Legacy は別経路で verify を迂回 |
| `s8b_oracle_judge` | observations から oracle verdict を作る |
| `s8b_verdict` | oracle verdict と prediction から certified 結論を作る。計画から欠落 |
| `s8b_budget` / WAL / ratified chain | `verified_manifest.sha256` を opaque identity として保存。新 `spec_sha256` は manifest hash に推移的に含まれる |
| `s8b_materialization` | binding identity producer。spec は読まない |
| `s8b_oracle_exploration` | exploration namespace 専用で official 経路から隔離 |
| `s8b_prediction_runner` / `s8b_launch_cert` | selector freeze / protocol / launch certificate 専用 |
| `s8b_floor_campaign` / `s8b_holdout_freeze` | oracle manifest とは別の floor・freeze schema。official floor mode は現状拒否 |
| `t126_driver` / `collector` / 8c registry | qualification / 8c namespace。certified oracle 選択には到達しない |

## 所見 1: combined verdict が spec 検証を迂回できる

- 分類: **BLOCKER**
- 根拠: `s8b_oracle_artifacts.py:49-50` は `OfficialVerdict` を「`provenance 検証済みであることは意味しない`」と定義している。さらに `load_official_verdict` は `schema_version` しか確認しない（`s8b_oracle_artifacts.py:156-160`）。`judge_combined` は `OfficialVerdict exact type` と `holdouts` の形だけを確認する（`s8b_verdict.py:551-564`）。CLI はそのままロードして渡している（`s8b_verdict.py:827-833`）。`spec_sha256` はどこでも確認されない。
- 成果物影響: schema と `holdouts` だけを満たす verdict に `unique-best` と eligible median を入れれば、wrong/missing spec の verdict でも combined verdict の `oracle_floor_exceeded`、`status`、certified 選択が変わる。出力 evidence も `oracle_manifest_sha256` と `oracle_status` のみで、spec の参照を持たない（`s8b_verdict.py:698-725`）。
- 対処案: `s8b_verdict.py` と対応テストを B の scope に追加する。`VerifiedOracleVerdict` のような sealed token を導入し、未検証 `OfficialVerdict` を `judge_combined` に渡せないようにする。少なくとも `spec_sha256`、manifest hash、verdict structure、status/reasons を再検証する。

## 所見 2: static consumer pin は「新 consumer が必ず赤」を保証しない

- 分類: **MAJOR**
- 根拠: 段 2 プランの検査対象は `verify_manifest` の直接 call 集合だけで、期待値を driver と report に固定している（`s2/plan.md:186-198`）。仕様にあるのは import alias 解決までで、`getattr`、dynamic import、re-export、higher-order wrapper、verify なしで Official artifact を受ける sink の探索規則がない。実際、所見 1 の `s8b_verdict` は `verify_manifest` を呼ばないまま certified 結論へ到達する。
- 成果物影響: 新しい consumer が direct call 以外の形で追加されても pin test は緑のままで、spec 検証なしの受理集合が拡大する。
- 対処案: direct `verify_manifest` call の列挙ではなく、official sink 全体を対象にする。`OfficialManifest` / `OfficialObservations` / `OfficialVerdict` の生成・受理境界を static/runtime の両方で監査し、dynamic access は拒否または明示的な allowlist にする。

## 所見 3: 層別 negative test に同一 fixture の positive control がない

- 分類: **MAJOR**
- 根拠: プランの manifest / driver / report の追加検査は divergence の拒否だけを列挙している（`s2/plan.md:204-215`）。positive control を同じ otherwise-valid fixture で明記しているのは judge の metamorphic test だけ（`s2/plan.md:216-219`）。一方、既存 driftguard は「一致する cell は issue なし」を明示している（`test_s8b_binding_driftguards.py:190-214`）うえ、run_block では prepare/evaluate 0 回・出力未生成まで確認している（同 `:248-287`）。
- 成果物影響: `APPROVED_SPEC_SHA256=None` による `no-approved-spec`、ratified freeze、fixture 不備など別理由の拒否でも negative test が通る。spec 比較を削除して常時拒否する変異も検出できない。
- 対処案: 各層で、同じ fixture の spec 一致版が通ることを先に固定する。driver は gate allowed と実行到達、report は rc=0 と spec hash 付き observations、judge は determinate を確認し、その一箇所だけを別 spec に変えた負例を置く。新 test では verifier mock を使わない。

## 所見 4: Legacy report は spec-less のまま observations を生成する

- 分類: **MAJOR**
- 根拠: `load_official_manifest` は official schema でも `run_contract` がなければ `LegacyManifest` に分類する（`s8b_oracle_artifacts.py:131-146`）。`build_observations` は `LegacyManifest` を明示的に受理し、`_validate_manifest` を通して report を生成する（`s8b_oracle_report.py:1607-1639`）。既存テストもこの受理を契約化している（`test_s8b_oracle_report.py:942-952`）。プランは Legacy の `spec_sha256` を `None` にするだけである（`s2/plan.md:49-62`, `:212-215`）。
- 成果物影響: schema から `run_contract` を外した manifest は report と observations を生成でき、report の数値・campaign references は spec authority なしで残る。通常の新 judge が `None` を indeterminate にするなら certified 選択は止まるが、report 層自体の受理集合は狭まらない。
- 対処案: Legacy report を維持するなら、明示的に non-certified artifact とし、Legacy observations → judge → combined の全経路で certified 結論を禁止する integration test を追加する。Legacy 受理自体を廃止するなら D65 Stage 3 として別裁定に送る。

## 所見 5: schema version の v1 据え置きは条件付きでしか安全でない

- 分類: **MAJOR**
- 根拠: manifest verifier は exact top-level key 集合を要求する（`s8b_oracle_manifest.py:1009-1013`）。そのため v1 据え置きなら旧 official manifest の spec 欠落は verify で落ちるが、Legacy classifier と observations loader はそれぞれ別に旧形を通す（`s8b_oracle_artifacts.py:138-153`）。
- 成果物影響:
  - v1 据え置き: durable official artifact がない前提では変更範囲が小さい。ただし旧 v1 Legacy report と spec-less v1 observations は loader 段階で残る。
  - v2 へ上げる: 旧 manifest v1 は classifier で拒否され、旧 observations v1 も loader で拒否される。その代わり既存の persisted v1 artifact と互換性を失う。
- 対処案: 現 wave で v1 を維持するなら、旧 official、Legacy、旧 observations の三経路を明示的に fail-closed する。strict な official 受理集合を最優先するなら manifest/observations を v2 に上げるが、これは別の schema migration として扱う。`8b-holdout-freeze/v2` の変更とは混同しない。

## 所見 6: fixture 移行を誤ると production を緩める誘因がある

- 分類: **MAJOR**
- 根拠: required 化後に更新が必要な呼び出しが実際に残っている。manifest test の `_build_manifest` は spec を渡していない（`test_s8b_oracle_manifest.py:155-176`）、同 test の `_verify` も approved spec を渡していない（同 `:283-292`）。driver の `_write_manifest`（`test_s8b_oracle_driver.py:1441-1479`）と report の `_manifest`（`test_s8b_oracle_report.py:194-229`）も同様である。さらに driver の既存 positive helper は `_gate_check_validated` と `verify_manifest` を mock している（同 driver test `:1755-1763`）。
- 成果物影響: 呼び出し側を更新せず production signature に default を足すと、未束縛 caller が残る。fixture が spec を自動生成すると、spec A / manifest B の divergence test が恒真になる。逆に report の共通 validator へ spec 必須を混ぜると、既存 Legacy 受理契約を壊す。
- 対処案: shared fixture は official positive 経路だけに適用する。generic builder の subset/missing-cell negative は明示 hash を渡して builder 受理と verify 拒否を分離し、Legacy fixture は別管理する。required `approved_spec` に default は置かない。

## 所見 7: module constant 参照は strict な意味で純関数ではない

- 分類: **MAJOR**
- 根拠: `judge_oracle` の docstring は「純関数」としている（`s8b_oracle_judge.py:124-132`）。一方、プランは module pin を参照する設計である（`s2/plan.md:172-180`）。その pin は `Optional[str]` の module global で、初期値も `None` である（`s8b_oracle_spec.py:20-22`）。
- 成果物影響: 同じ observations が、module state の変更・monkeypatch・import 状態によって determinate / indeterminate に変わる。observations の `spec_sha256` は report が出す証拠であり、authority ではないため、これを module global と組み合わせる境界を曖昧にすると report 側の自己申告を信頼する設計へ戻り得る。
- 対処案: `judge_oracle(observations, *, approved_spec_sha256)` の required 引数、または immutable な trust-root token を渡す形にする。CLI が spec を load する I/O は外側で行い、judge core は observations と明示された pin だけから決定する。observations の値は pin と一致する証拠としてのみ使う。

## 収束・所有・T-805

- A/B の production file ownership は重複していない。`_GENERATOR_SOURCES` は report / judge / artifacts など 5 leaf に固定されている（`s8b_oracle_manifest.py:53-61`）。A の manifest/spec 変更はこの source list に含まれず、B の編集後に A が golden を一度更新すれば収束する。
- `binding_identity` の key 集合には generator hash がなく（同 `:63-66`）、generator hash と binding identity の循環依存はない。
- `manifest_sha256` は自身の field だけを除外し、追加した `spec_sha256` は hash に含む（同 `:163-169`）。driver はその hash を WAL と budget ledger に渡している（`s8b_oracle_driver.py:1244-1249`）。ledger は別の spec consumer ではなく、verified manifest hash の下流保存である。
- T-805 は budget authorization proof chain を ratified freeze v2 単独で変更せず、transition table を二度変えない裁定である（`docs/worklog.md:2962-2966`）。T-804 が oracle manifest/observations の v1 だけを変更し、`s8b_ratified_freeze.py` の transition table・budget authority を触らない限り干渉はない。

## 裁定パッケージ候補

1. **`s8b_verdict` の downstream binding**
   - **A:** T-804 B の scope に追加し、combined verdict まで spec continuity を閉じる。
   - **B:** D65 Stage 2 相当の別 wave へ送る。その場合、T-804 は certified selection 全層被覆を主張しない。

2. **Legacy report と schema bump**
   - **A:** T-804 では v1/Legacy report を維持し、judge・combined で必ず non-certified に倒す。
   - **B:** D65 Stage 3 として Legacy 廃止・manifest/observations v2 化を別裁定する。