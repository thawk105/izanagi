# 段 4 裁定 — [T-1250] 版を束縛した次世代の条件契約 record

裁定日時: 2026-08-17 01:2x JST / base main = 5a19b8ab

## 所見の裁定

| ID | 判定 | 採否 | scope | 根拠と対応 |
|---|---|---|---|---|
| A1 | **real** | **一部採用** | 内 (継続性検査) / 外 (§5 exact map) | 「§6 条件を弱めて g4 も整合的に作り直す」変異は現行案のテストを生き残る。**g3↔g4 の contract 継続性検査を新設して採用**。ただし世代番号 3・4 に固定し、tip 相対にしない (tip 相対だと将来の正当な条件改訂を機械的に塞ぐ)。§5 の exact status map の pin は**不採用** — §5 の値は doc が意図して保護対象外に置いており、pin すると正当な発効手続き (§5 記入) を塞ぐ。 |
| A2 | **real** | **採用** | 内 | 親 brief の不変条件 1 の記述が誤り。実測で確認した (下記「訂正した実測」)。不変条件を書き直す。 |
| A3 | 確認 | — | — | 新テストは恒真でない。record blob と module 定数は別 source。対応不要。 |
| A4 | 確認 | — | — | doc 追記は保護 hash を変える。親も独立に実測済み。対応不要。 |
| A5 | **real** | **不採用 (scope 外)** | 外 | `GIT_TIMEOUT_CAP_SECONDS` の再較正条件は g2 時点で既に成立済みの**既存債務**であり g4 が初めて発火させるものではない。判定器 module は no-touch。新規タスクとして起票する。 |
| A6 | **real** | **記録のみ** | 外 | 版束縛が効く層 (registered launch / acceptance の再導出) と効かない層 (certified issuance、全経路強制、外部 anchor、bump 忘れ、import 済み bytes) を worklog で分ける。phase doc の一括「未結線」表現の訂正は保護 doc の別改訂になるため、この g4 へ無裁定で混ぜない。 |
| A7 | **real (nit)** | **採用 (記録の訂正)** | 内 | pin 閉包の説明を「namespace 参照 / semantic field pin / raw bytes pin / 外部 trust root」に分けて記録する。`test_s8c_preregistration_core.py:1159` は `generation_path(1)` 経由で g1 の hash を literal pin しているが g4 追加では動かない。`FROZEN_MANIFEST` に s8c record は無い。最終結論 (外部 raw-bytes trust root なし) は変わらない。 |
| A8 / B7 | **real** | **採用 (T-324 は触らない)** | 外 | 未着地 patch は 0 件で land 対象は無い (ancestry + g2/g3 の revision_reason + `git cherry` の三点で確認)。しかし **[T-324] をこの wave で close しない**。台帳 carry の整理は別 transition。実測事実だけを worklog へ記録する。 |
| B1 | **real** | **採用 (手順へ固定)** | 内 | producer は**最終文言確定後に 1 度だけ**実行する。doc 編集前 = `spurious-revision`、doc 先行 commit = `record-protected-mismatch`、再実行 = `revision-exists`、g4 commit 後の doc 修正 = g5 が生える。**commit 前検証は HEAD 専用テストでなく candidate commit 検証を使う。** |
| B2 | 確認 (一部 refuted) | — | — | 静的予測では既存赤 0 件。記録には「静的予測で既存赤 0、条件付き failure は列挙のとおり、pytest は段 6 で実走」と書く。**`legacy_prefix` が実質無効という下位主張は refuted** — 当該 prefix は subdirectory を持たない旧 flat namespace を狙った負の対照であり、flat 命名が再導入されれば発火する。恒真ではない。 |
| B3 | **real** | **採用 (別手段)** | 内 | 新テストは live module bytes を読むので並行 writer と競合しうる。ただし `REAL_REPO_SERIAL_NODES` への登録は取らず、既存の同型ノード (`test_candidate_is_not_effective_and_has_zero_satisfied_predicates`) と同じ `@CANDIDATE_XDIST_GROUP` を付ける。既存先例に揃え、直列化コストを増やさない。 |
| B4 | 確認 | **記録のみ** | 内 | 現 HEAD の report digest を固定した production golden は全件検索で 0 件。歴史 golden は書き換えない。 |
| B5 | **real** | **採用** | 内 | doc へ「bump 忘れは機械検出しない。版一致検査が止めるのは明示的 bump 後に旧版 record を使い続けることだけである」を明記する。謳うだけで発火しない保証にしない。 |
| B6 | 確認 | — | — | (P4) は D95 と整合。g4 JSON は実装面でない。テストを含む commit には Codex author の trailer を付け、commit 後に全史 provenance 監査を走らせる。 |
| B8 | **real** | **採用** | 内 | worklog fragment は既存 `[T-1250]` を操作し、base は archive の実体 item から carry 解決して作る。D458 は既存参照として書き、新 decision fragment を作らない。fold は land の lock 内だけ。 |

## 訂正した実測 (親の誤りを正す)

親 brief の不変条件 1 は「C01〜C12 は `evaluator-exception`」と書いたが**誤り**である。
CLI (`python3 -m orchestrator.campaign.s8c_preregistration check`) の出力を根拠にしたためで、
CLI 経路は 12 条件すべてを `evaluator-exception` へ潰す。ライブラリ経由の
`activation_report_at(ROOT, "HEAD")` が返す実際の vector は次である (親が独立に実測)。

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

**CLI が潰す機序 (親が実コードで特定):** `-m` 実行では判定器 module が `__main__` としても
読み込まれ、評価器 (`from . import s8c_preregistration as core`) が返す `core.PredicateResult` が
`__main__` 側の `PredicateResult` と `isinstance` で一致しない
(`s8c_preregistration.py:1543` の `_normalize_predicate_results`)。
`PreregistrationError("predicate-result-type")` が上がり、`_default_registry_results` の
包括 except が全件 `evaluator-exception` へ倒す (`:1653`)。
安全側 (未発効) には倒れるが、production の入口が「なぜ充足しないか」を返せない = 規律 3 の毀損。
**scope 外 real。新規タスクと failures 台帳へ起票する。この wave では module を触らない。**

## 確定した不変条件 (brief の 1 を差し替え)

1. `effective` は **false のまま**である。
   変わってよいのは `commit`、`freeze_generation` 3→4、`protected_sha256`、
   `decider_version` `None`→`s8c-decider/v1`、`decider_version_matches` false→true、
   `decider_version_reason_code` `decider-version-unbound`→`decider-version-match`、
   および上記から導出される activation report digest。
   **不変**: `freeze_reason_code` = `valid`、§5 の記入 vector、12 条件の status/reason vector、
   3 module の blob hash。
2. g1〜g3 の bytes を 1 bit も変えない。
3. `DECIDER_VERSION` を bump しない。
4. 判定器 3 module のコードを変更しない。
5. doc 追記は §6 配下 H3 の改訂手続きブロック内に置く。
6. `spurious-revision` に例外を作らない。

## 確定した doc 追記 (プラン v2)

挿入位置: `docs/phase3-8c-preregistration.md` の「世代 record は / 直前世代の bytes hash・変更理由・
**裁定の参照** … を持つ。」の直後、「無記録の変更、記録のない差し戻し、」の直前。空行を入れない。

本文 (プラン案 + B5 の限界明記):

```
新たに発行する世代 record は schema v2 とし、判定器の版 (`DECIDER_VERSION`) を持つ。既存の
schema v1 record は版を持たない legacy として改変せずに残す。判定器・評価器・射影のいずれかで
受理集合・拒否理由・射影された判定入力の意味を変える変更は、bytes 差の有無に関わらず
`DECIDER_VERSION` を bump し、その版を持つ新世代の record を発行しなければならない。整形など
意味が変わらない変更では bump しない。版の一致検査が止めるのは、明示的に bump したあとで
古い版の record を使い続けることだけであり、bump の忘れは機械検出しない (D458)。
```

## 確定したテスト (プラン v2)

`orchestrator/tests/test_s8c_preregistration_invariant.py` に 2 関数を新設する。新 file は作らない。

1. `@CANDIDATE_XDIST_GROUP` 付き。`repository_candidate_commit` fixture を使い
   `activation_report_at(ROOT, candidate)` を評価して、freeze valid、tip が schema v2、
   `decider_version` が `DECIDER_VERSION` と一致、`decider_version_matches` true、
   reason が `decider-version-match`、そして `effective is False` を固定する。
   **HEAD 直読でなく candidate を使う理由**: candidate は HEAD tree + 作業ツリー差分なので、
   変異 harness の作業ツリー変異が観測面へ届く。HEAD 直読だと変異が 1 件も届かず、
   変異検査が無効試験になる (段 2 プラン §5 が指摘した問題の解消)。clean tree では
   candidate の tree は HEAD と同一なので、着地状態の検査として弱くならない。
2. 世代 3 と 4 の record を作業ツリーから読み、`section5_field_names_sha256`・
   `section6_conditions_sha256`・12 個の `section6_condition_hashes`・
   `evidence_contract_sha256` が**同一**であること、`normative_body_sha256` と
   `protected_sha256` が**相異**であること、`supersedes_sha256` が g3 の bytes hash であること、
   `ruling_reference` が `D458`、schema が v2、`decider_version` が `DECIDER_VERSION`
   であることを固定する。世代番号 3・4 に固定し tip 相対にしない。

`test_repository_legacy_v1_generations_remain_readable` の param は `(1, 2, 3)` のまま変えない。
既存テストの期待値は一切変更しない。

## 変異事前登録 (DW-M01)

harness = `tools/mutation_harness.py`。runner は dispatch recipe、argv に `--force-dispatch` を入れる。
新テストは candidate 経由と作業ツリー直読なので、作業ツリー変異が観測面へ届く。

| ID | 変異 | 単一理由性の確認 | 期待 KILL node (完全集合) |
|---|---|---|---|
| M01 | g4 を wave 前の形へ戻す: `schema_version` を v1 にし `decider_version` key を除去 (同一 file 2 置換の累積) | 保護 hash preimage に版は入らないので freeze は valid のまま。legacy v1 tip として読め、版判定だけが unbound へ倒れる | 新テスト 1、新テスト 2 |
| M02 | g4 の `decider_version` を `s8c-decider/v2` へ | record は構造上妥当、freeze も valid。版一致だけが mismatch | 新テスト 1、新テスト 2 |
| M03 | doc の追記を除去し g4 は据え置き | protected mismatch で freeze invalid。新テスト 2 は record 同士の比較なので不変 (survive が正) | 新テスト 1、`test_candidate_freeze_matches_contract_and_generation_chain` |
| M04 | g4 の `supersedes_sha256` を g2 の bytes hash へ | 連鎖検査だけが倒れる | 新テスト 1、新テスト 2、`test_candidate_freeze_matches_contract_and_generation_chain` |
| M05 | **§6 条件 4 を弱め、g4 の `section6_conditions_sha256` / 条件 4 の hash / `normative_body_sha256` / `protected_sha256` を整合的に再計算して差し替える** (A1 の攻撃) | 整合的なので freeze valid、版束縛も維持され、candidate 検査も通る。**継続性 assert だけが倒れる** | 新テスト 2 |

M05 の置換 literal は、置換前に親が probe で再計算して確定する。期待 node は fix 後の最終 commit で
`DW-M07` に従い再導出する。M01 は「wave 前の実コードの形」を含む要件を満たす
(tip = schema v1 / 版なし / unbound は wave 前の実状態そのもの)。

## 段 5 の分割

実装単位 1 つ (Codex `role=author`)。編集対象は
`orchestrator/tests/test_s8c_preregistration_invariant.py` のみ。並列分割しない。
doc 編集と g4 生成は親が段 5 の前に済ませ、実物を子へ渡す。

## ユーザーへ返す裁定パッケージ候補 (scope 外 real)

- A5: `GIT_TIMEOUT_CAP_SECONDS` の再較正が g2 時点から未処理。計算ノードでの再較正が要る。
- A6: 版束縛が効かない層の一覧。phase doc の一括「未結線」表現の訂正要否。
- A2 由来: CLI `-m` 経路が全 12 条件を `evaluator-exception` へ潰す既存欠陥 (規律 3 の毀損)。
- A8/B7: [T-324] の台帳 carry 整理。
