# [T-1155] / [T-1178] 床値 result への SWO receipt 束縛と admission 台帳検査 — wave 記録

2026-08-16 JST / branch `worktree-dev-wave-t1155-t1178-floor-receipt` / base = main `478a4138`
/ 実装 commit `19184644`

## 何をしたか

- **[T-1155]**: sort_best cell の SWO PASS receipt を portable 形へ射影し、床値の durable record
  (`manifest.json` / `result.json` の `binaries[cell_id]`) へ束縛した。射影は
  `cell_id` / `holdout_id` / `configuration_id` / `entry_sha256` / `binary_sha256` の identity 5 項目を
  含み、receipt 移植を拒否する。ホスト絶対パスは載せず、`compiler_version` は sha256 のみ。
- **[T-1178]**: `result.json` へ `holdout_admission` 節 (claim identity・行数・
  `campaign_run_id` で絞った ledger digest) を必須化した。公開 consumer は expected を
  caller から受け取らない入口だけを使う。台帳へ到達できない場合も内容不一致と別 reason で拒否する。

## 保証境界 (実装が保証しないこと)

1. **この receipt は oracle 実行の証明ではない。** 全 field は公開かつ決定的で、oracle を
   実行せずに合成できる。保証するのは「床値 record がどの oracle 実行 receipt を主張しているか」
   という durable な辺だけである。
2. **台帳の削除→同一 bytes 再構成には耐えない。** claim digest も ledger digest も公開・決定的な
   値だけから作られ、`O_EXCL` は file が存在する間しか効かない。
3. **`measurement_head` は非権威的な同値確認用 field である。** 台帳と claim を同期して
   書き換えれば portable receipt も受理集合も変わらない (片側だけの変更は拒否される)。

1 と 2 の強化はいずれも署名機構・外部 WORM の新設に当たり、2026-08-12 のユーザー裁定
(bytes 級 provenance 機構は既定で見送り) に該当するため本 wave では実装せず、次の一手へ起票した。

## 成果物

| file | 内容 |
|---|---|
| `brief.md` | 段 1 brief。scope、不変条件、前提実測、provisional 裁定 (P1)-(P5)。**§0 の 2 件は段 3 で覆され、`s4-adjudication.md` §0 が訂正の正本**。 |
| `s4-adjudication.md` | 段 4 裁定。反証の受理、所見の real/refuted、プラン v2、変異事前登録。 |
| `verbatim/s2-plan.md` | 段 2 プラン (codex plan, reasoning=max)。 |
| `verbatim/s3-consult-a-sol.md` | 段 3 敵対レンズ A (正しさ防壁)。**NO-GO**。親 brief の実測 2 件を覆した。 |
| `verbatim/s3-consult-b-luna.md` | 段 3 敵対レンズ B (到達範囲)。must-fix 5。 |
| `verbatim/s5-u0-contract-spine.md` | 段 5 U0 (契約 spine)。 |
| `verbatim/s5-u1-producer.md` | 段 5 U1 (producer)。 |
| `verbatim/s5-u2-consumers.md` | 段 5 U2 (consumers)。 |
| `verbatim/s6-review-a.md` | 段 6 敵対レビュー A (発火実効性)。must-fix 3。 |
| `verbatim/s6-review-b.md` | 段 6 敵対レビュー B (到達範囲)。must-fix 3 / should-fix 2。 |
| `verbatim/s6-fix1-integration.md` | fix 1 巡目 (runtime/portable 分離ほか)。 |
| `verbatim/s6-fix2-attempt-coverage.md` | fix 2 巡目 (attempt 期待集合の再導出)。 |
| `verbatim/s6-fix3-portability.md` | fix 3 巡目 (`measurement_head` の root 依存排除)。 |
| `verbatim/s6-fix4-review-findings.md` | fix 4 巡目 (レビュー所見 M1-M5)。 |
| `verbatim/s6-fix5-gate-order.md` | fix 5 巡目 (新設 gate の先取り解消)。 |
| `verbatim/s6-mutspec-analysis.md` | 変異登録の単一理由性分析と除外判断 (書込前の回)。 |
| `verbatim/s6-mutspec-rereg.md` | 期待 node 訂正の再登録と、発火しなかった parametrization の原因。 |
| `mutation/mutation-spec-round1-probe.json` | 変異 spec 第 1 走 (probe)。9 件。 |
| `mutation/mutation-result-round1-probe.json` | 第 1 走の台帳。KILLED 7 / MISMATCH 2。 |
| `mutation/mutation-spec-round2.json` | 期待 node を実測どおり訂正した第 2 走 spec。2 件。 |
| `mutation/mutation-result-round2.json` | 第 2 走の台帳。KILLED 2 / MISMATCH 0。 |

## 変異 matrix

`tools/mutation_worktree.py` / 固定 commit `19184644` / `--runner-mode dispatch` /
runner argv に `--force-dispatch`。対象 = 焦点 13 test file。

| 走 | spec sha256 | 登録 | KILLED | MISMATCH | SURVIVED | TIMEOUT | baseline 失敗 |
|---|---|---:|---:|---:|---:|---:|---:|
| 第 1 走 (probe) | `d9c1b1c0a3fc110c6d795a14b09f700799766fe7c2d4ce6b41cbcb0b11f9b8c2` | 9 | 7 | 2 | 0 | 0 | 0 |
| 第 2 走 (再登録) | `5713fa96b6fa9f7c41899af7edce3eef5027d0bd72352b66aa7441e46d40b1d0` | 2 | 2 | 0 | 0 | 0 | 0 |

**合算して 9/9 KILLED、SURVIVED 0。**

### erratum E1 — 第 1 走の期待 node が完全集合でなかった

第 1 走の 2 件は MISMATCH だった。**いずれも検出漏れではなく、事前登録した `expected_nodes` が
実際の失敗集合と一致しなかった** (DW-M08 の「初回を probe として erratum を残し再登録・再走する」に
該当)。第 1 走の記録は消さず本 insight に残す。

- `swo.identity-external-binding-drop`: 期待 5 / 実際 6。
  - 発火しなかった: `test_s8b_sort_swo_receipt.py::test_validator_rejects_receipt_transplant[configuration_id-stock_common]`
  - 追加で発火した: `test_s8b_binary_admission.py::test_sort_receipt_identity_must_match_binary_record`、
    `test_s8b_floor_campaign.py::test_sort_receipt_identity_transplant_is_rejected`
- `admission.campaign-filter-drop` (positive 対照): 期待 2 / 実際 4。
  - 追加で発火した: `test_s8b_oracle_driver.py::test_transient_prepare_failure_retries_once`、
    `test_s8b_oracle_driver.py::test_v2_completed_driver_adapter_campaign_is_accepted_by_report`

### erratum E2 — configuration_id の parametrization は当該変異にとって単一理由でない

`test_validator_rejects_receipt_transplant[configuration_id-stock_common]` が
`swo.identity-external-binding-drop` で発火しなかったのは、可搬 receipt の**内部** identity 検証が
`configuration_id != "sort_best"` を先に拒否するためである
(`orchestrator/campaign/s8b_sort_swo_receipt.py` の内部検証が、変異対象の外部期待値比較より前段)。
検査が弱いのではなく二重に効いている。この parametrization は当該変異の単一理由性を満たさないので
期待集合から外した。

### 除外した変異候補 (7 件)

第 1 走の登録前に、次を「別層が同じ入力を拒否する (単一理由でない)」または
「期待 node の完全集合を静的に確定できない」として登録から外した。逐語は
`verbatim/s6-mutspec-analysis.md`。

- built record の SWO key 脱落 / raw compiler・path の portable 混入 / central key 集合の common 固定化
- pair set 比較への後退 / missing・zero-byte main ledger の空列受理
- caller supplied expected の復活 / journal・result session の片方向化

うち 4 件 (sort receipt の optional 化、空 binaries、completed-only fallback、
`expected_binaries` 不渡し) は単独では別 gate に mask されるため、実効 gate と組み合わせた
`both-layers` 変異へ再照準して登録した。

## 実測 (親が bounded local / dispatch で実行)

- 焦点 13 test file: **rc=0 / 1,192 passed / 18 skipped**。
- fix の収束: 192 → 8 → 2 → 4 → 0 (親の実測 6 回)。
- 段 5 / 段 6 の Codex 子 10 本は**全員 pytest を実走できなかった** — `hooks/guard_bash.py` が
  pytest 直呼びを機械拒否し、正規経路の `tools/run_tests.py` は codex sandbox から
  scheduler socket へ到達できず rc=16 になる。子は迂回せず「実装済み・未実走」と申告し、
  測定は毎巡 親が引き受けた。
