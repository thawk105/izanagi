GO / NO-GO: **NO-GO**。実装着手・「実装済み」台帳記録・land は止めるべきです。指定資料はすべて読了し、pytest は実行していません。

## 規模検算

既存 `preregistration/` は実測 **881 行**（28 + 186 + 266 + 401）、指定テストは **527 行**です。実装は固定 blob 読取、erratum 合成、envelope parser、非 gate facade に限定されています。

| 単位 | 申告 production / test | 判定 |
|---|---:|---|
| U1 | 600–855 / 320–430 | 過大ではない。ただし manifest 自己参照、祖先検査、trust root の負例が見積りに不足 |
| U2 | 230–290 / 130–180 | production の実体は文書再発行のみで、分類は過大。実行時 validator まで含めるなら逆に過小 |
| U3 | 1,800–2,530 / 1,000–1,400 | 過大ではない。完全 schema と nested closure を含めるなら下限寄り |
| U4 | 270–375 / 220–300 | 文書 100–140 行を production に含めている。実効 gate の公開経路まで試すなら不足 |
| U5 | 700–965 / 890–1,230 | 既存の land 2,460 行、spool fold 2,161 行、git-state 1,060 行を跨ぐため下限寄り |
| U6 | 1,480–1,980 / 870–1,180 | receipt の cross-field 検査までなら妥当。ただし writer/consumer/correctness は未算入 |

したがって合計値 **5,080–6,995 / 3,430–4,720** は算術的には正しいものの、「文書を production に含める単位」と「実効 gate の欠落層」が混在しており、全体としては過小かつ比較不能です。

### U3 の実数根拠

`record-items.md` は top-level **18 key** を固定しています。[record-items.md:40](/work/1/SFC/tanab/izanagi/output/insights/2026-08-08_t139-addendum-a/record-items.md:40)

保守的に数えると、明示済みだけで次の規模です。

- `planned_execution.runs[]` は 1 cluster **36 object**。[record-items.md:80](/work/1/SFC/tanab/izanagi/output/insights/2026-08-08_t139-addendum-a/record-items.md:80)
- 各 run は 10 key、`preceding_wait` は 2 key。[record-items.md:92](/work/1/SFC/tanab/izanagi/output/insights/2026-08-08_t139-addendum-a/record-items.md:92)
- `stock/mode1/modeX` の 3 arm を展開すると、compile/source/cache/compile_commands/binary/toolchain 等だけで少なくとも **105 path-qualified key slot**。[record-items.md:169](/work/1/SFC/tanab/izanagi/output/insights/2026-08-08_t139-manifest-w1/record-items.md:169)
- observation は 11 direct key、raw pointer 2 個、performance marker、failure evidence を持つ。[record-items.md:167](/work/1/SFC/tanab/izanagi/output/insights/2026-08-08_t139-manifest-w1/record-items.md:167)

この数え方では、既知部分だけで **generic arm 定義 174 slot 以上、3 arm 展開で 244 slot 以上、object path は 52/66 程度**です。さらに `allocations[]`、`liveness[]`、`attempts[]`、`phase_caps[]`、`translation_units{}`、`cluster_slots[]` などは exact key・型・必須性が未定義です。[record-items.md:180](/work/1/SFC/tanab/izanagi/output/insights/2026-08-08_t139-manifest-w1/record-items.md:180)

つまり、完全な総数は現時点では導出不能です。

## 依存グラフと候補 scope

(i)〜(v) は brief の U1〜U5 に対応すると解釈します。U6 はそれらを実効化する必須層です。

```text
U2 record-items ──> U3 schema ──┐
U5 alpha ledger ────────────────┼──> U1 manifest ──> U6 resolver/binding/verify
U4 erratum gate ────────────────┘                         │
                                                          ├─> receipt writer
intent ─> PBS/driver/collector ──────────────────────────┤
correctness verifier ────────────────────────────────────┤
                                                          └─> certified selection/report/ledger
```

| 候補 | 1 wave 完結性 | F13 判定 |
|---|---|---|
| U1 だけ | 参照する schema/ledger が無く、現計画のままでは閉じない。activation 文書だけに縮めれば意味はある | no-land・未承認と明記する限り非該当。実装済み gate と記録すれば F13 |
| U1+U2+U4 | schema、alpha、resolver が無く、gate が到達不能 | land/実装済み主張なら F13 |
| U2+U3 | 契約 artifact slice としては完結可能。ただし Q-A 後、未承認・未landに限る | 明示的に gate でないなら非該当 |
| U1+U2+U3+U4+U6 | alpha ledger が無く、receipt は受理できない | 半実装。F13 相当 |
| U1〜U6 | admission infrastructure の最小閉包だが、1 wave には収まらず、producer の正例も無い | land して producer 完了と記録すれば F13 |

「実効 gate」の最小集合は U1〜U6 であり、そこから削れる U はありません。

## blocker

### B1 — P3 が canonical decision と衝突している

brief は第 2 erratum を未承認としますが、D263 の理由欄には「第 2 erratum が既に承認済み」とあります。[D263:12173](/work/1/SFC/tanab/izanagi/docs/decisions.md:12173) 計画はこれを散文として無視しています。[s2-plan.md:9](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t139-manifest-w1/s2/s2-plan.md:9)

ユーザー裁定による supersede を canonical decision に明記してからでなければ、U1/U4 の approved errata 集合を確定できません。

未是正時の成果物影響: `approved_errata` が `{erratum-1}` と `{erratum-1, erratum-2}` に分岐し、pilot 受理集合・certified 判定・台帳参照が一致しません。

### B2 — U3 は入力仕様が閉じておらず、完全 schema を実装できない

`record-items.md` 自身が完全 schema ではないと明記しています。[record-items.md:3](/work/1/SFC/tanab/izanagi/output/insights/2026-08-08_t139-manifest-w1/record-items.md:3) 計画は 1,500〜2,100 行の JSON Schema を見積もりますが、exact key、null、配列長、cross-field 制約の未定義部分を列挙していません。

未是正時の成果物影響: validator A と B が同じ receipt を異なる適格 cluster 集合として扱い、certified 選択が実装依存になります。

### B3 — gate の全層が scope 外

U6 は receipt 自体と binding を検査するだけで、correctness verifier、submission intent、PBS preflight、driver、collector、receipt writer、certified consumer は実装しません。[s2-plan.md:500](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t139-manifest-w1/s2/s2-plan.md:500) 前 wave もこれらを未実装として記録しています。[README.md:19](/work/1/SFC/tanab/izanagi/output/insights/2026-08-10_t139-producer-slice/README.md:19)

裁定パッケージ候補として、少なくとも次を名指しで残す必要があります。

- `submit_pilot` と durable submission intent
- PBS preflight、実 driver、collector
- `PreregBinding` 必須の receipt writer
- iteration 毎の correctness verifier
- certified eligibility/selection、材料 report、trial ledger consumer

未是正時の成果物影響: `verify_receipt()` が `accepted` を返しても producer/consumer が存在せず、certified 選択・report・trial ledger の値は変わらないため、「gate が効いた」と記録できません。

### B4 — DW-M01 の新規変異 matrix が存在しない

前 wave の M1〜M9 は既存 erratum/envelope 用であり、今回の U1/U3/U4/U5/U6 の mutation 登録ではありません。DW-M01 は各変異について前後層の mask が無いことを要求します。[mutation.md:5](/work/1/SFC/tanab/izanagi/docs/dev-wave/mutation.md:5)

特に U2 は文書のみで、a03 の reject は U3 schema と U6 semantic check が重複します。U3 の closure loader は JSON Schema runtime に、U5 は parser・resolver・land/git-state に、U6 は schema stage に mask されます。

未是正時の成果物影響: mutation ledger の `KILLED/SURVIVED` が実効 gate の検出力を証明せず、受理集合の変化を台帳へ正当に記録できません。

### B5 — 未land wave の積み上げ手順が無い

Q-D に従って本 wave を land しない判断自体は正しいです。[s1-brief.md:18](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t139-manifest-w1/s1-brief.md:18) ただし標準契約は `dev_wave_land.py` による FF、同一 lock 内の spool fold、canonical 台帳更新を前提にしています。[DW-O23:126](/work/1/SFC/tanab/izanagi/docs/dev-wave/operations.md:126)

`dev_wave_land.py` に deferred-land 状態はなく、通常経路は lock、FF、fold を行います。[dev_wave_land.py:2090](/work/1/SFC/tanab/izanagi/tools/dev_wave_land.py:2090)

必要なのは、各未land waveについての base main SHA、wave tip SHA、監査 commit 閉包、受入結果、mutation 結果を固定し、次 wave が前 wave tip から開始し、最終 wave tip で全走・全変異・provenance を再実施してから一度だけ land する手順です。

未是正時の成果物影響: 次 wave が main から再開して前 wave のコード/fragment/検査結果を落とすか、古い受入・変異結果を新しい tip に誤って再利用します。

## must-fix

### M1 — 単位別見積りを「コード・schema・docs・test」に分離する

特に U2 の 230〜290 行は production code ではなく record-items 文書です。[s2-plan.md:113](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t139-manifest-w1/s2/s2-plan.md:113) 一方、U3/U6 は未定義の semantic validator を含めていません。

未是正時の成果物影響: 台帳の実装量・残作業量が過少または過大に記録され、次 wave の scope 判定を誤ります。

### M2 — U1 の artifact commit が他単位の所有権を奪っている

U1 の artifact commit は record-items、schema、erratum draft、alpha request、ledger を同時に作る計画です。[s2-plan.md:16](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t139-manifest-w1/s2/s2-plan.md:16) これは brief の A/B/C 所有分離と衝突します。[s1-brief.md:81](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t139-manifest-w1/s1-brief.md:81)

さらに U1 の `AlphaReservationContract` と U5 の `AlphaReservationPlan/Evidence` の型境界が定義されていません。[s2-plan.md:64](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t139-manifest-w1/s2/s2-plan.md:64)

未是正時の成果物影響: manifest が pin する blob commit/digest が worker の実装順序に依存し、receipt の受理集合と台帳参照が再現不能になります。

### M3 — manifest 自身の `manifest_ref` を自己参照しない構造を明記する

D262 は manifest と payload を同一 commit に置く自己参照を却下しています。[decisions.md:12158](/work/1/SFC/tanab/izanagi/docs/decisions.md:12158) しかし U1 の `ApprovalManifest` は `manifest_ref` を持ち、`parse_approval_manifest()` に trusted ref の引数がありません。[s2-plan.md:64](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t139-manifest-w1/s2/s2-plan.md:64)

`manifest_ref` を trusted code pin から導出するのか、blob 内 key にしないのかを固定すべきです。

未是正時の成果物影響: manifest を構成できず全 resolver が fail-closed になるか、caller supplied ref が trust root に昇格します。

### M4 — U4 の synthetic v2 は非恒真性の証拠に留まり、実効 gate の正例ではない

計画は第 2 erratum を承認した synthetic v2 なら通るとしています。[s2-plan.md:267](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t139-manifest-w1/s2/s2-plan.md:267) しかし実際の approved v2 manifest、producer、binding、writer、consumer はありません。前 wave の裁定も stub e2e を偽陽性としています。[s4-adjudication.md:21](/work/1/SFC/tanab/izanagi/output/insights/2026-08-10_t139-producer-slice/verbatim/s4-adjudication.md:21)

未是正時の成果物影響: gate helper の単体受理だけを pilot 投入可能・producer 完了と誤記します。

### M5 — alpha ledger の canonical main 境界を成果物に明記する

計画自身が common-dir lock では独立 clone の二重予約を防げないと認めています。[s2-plan.md:384](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t139-manifest-w1/s2/s2-plan.md:384) 現在の lock も common Git directory 内だけです。[dev_wave_land.py:1272](/work/1/SFC/tanab/izanagi/tools/dev_wave_land.py:1272)

「一つの canonical main と trusted consumer だけが権威」という運用境界を manifest、report、receipt resolver の全てで同じ wording に固定してください。

未是正時の成果物影響: clone 間で同じ `(family_root, ordinal)` が予約され、alpha 台帳と全体誤り率の証拠が偽になります。

### M6 — D264 を緩める前提で計画しない

既存の `test_module_exports_no_admission_api` は、package facade の 4 名前非 export を検査しています。[test_t139_preregistration_binding.py:512](/work/1/SFC/tanab/izanagi/orchestrator/tests/test_t139_preregistration_binding.py:512)

計画どおり専用 `gate.py` だけへ 3 名前を置くなら、この既存テストは赤くなりません。逆に package root へ再 export すれば同テストの 519〜520 行相当が赤くなり、それは「契約の前進」ではなく D264 違反です。

正当な前進として記録するには、ユーザー裁定または superseding decision、package root の 4 名前非 export、`gate.py` の明示 export 集合、`submit_pilot` の不在、実 consumer の import 経路を別々に機械検査する必要があります。

未是正時の成果物影響: root export を許すと admission API の到達可能性と受理集合が拡大し、D264 の参照が無効になります。

## nit

### N1 — U6 の「関数 2 つ + 型 1 つ」は実装面を過少に表す

U6 は resolver、private factory、receipt verifier、13 reason code、例外群、専用 facade、既存 blob helper、D264 境界テストを含みます。[s2-plan.md:411](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t139-manifest-w1/s2/s2-plan.md:411)

未是正時の成果物影響: acceptance の値は直ちには変わりませんが、実装量と所有単位が台帳上で過少表示されます。

## P1〜P5 の判定

- P1 の reissue 方針は正しい。ただし U2 は文書だけで、validator の所有者を追加で固定する必要があります。
- P2 の第 2 erratum を専用 validator にする方針は正しい。
- P3 は D263 との衝突を解消するまで不成立です。
- P4 は canonical main 限定なら成立します。任意 clone まで含む保証ではありません。
- P5 の 1 blob + digest 固定は方向として正しいが、U3 の未閉包仕様と manifest 自己参照問題が残っています。

## 総括

1 wave 収容判定は **不可**です。U1〜U6 の全てが gate の最小閉包であり、さらに receipt writer、intent、driver、collector、correctness verifier、certified consumer が必要です。

本 wave で完結させる最小 scope としては、Q-A 裁定後の **U2+U3 の contract/artifact-only slice** を推奨します。manifest への digest binding、gate export、alpha ledger、certified claim、land は含めず、成果物には明確に「未承認・未land・admission 非実装」と記録します。

実効 gate を要求するなら最小集合は U1〜U6 であり、Q-D を再裁定して複数 wave の最終同一 land 手順を先に確定すべきです。