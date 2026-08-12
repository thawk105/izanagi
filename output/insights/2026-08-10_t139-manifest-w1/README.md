# [T-139] 第 1 波 — 逐語と成果物 (2026-08-10)

branch `worktree-dev-wave-t139-manifest-w1`。可変状態の正本は `docs/worklog.md` 末尾である。
本ディレクトリは凍結記録であり、後から書き換えない。

## 結論

**依頼された §58 裁定の (i)〜(v) のうち、実装できたのは (iii) の一部だけである。**
段 3 の敵対レンズ 2 本と段 6 のレビュー 2 本がすべて NO-GO を返し、
親は独立所見 19 件を全件 real と裁定した (refuted 0 件)。

**承認 manifest・受領証 JSON Schema・`a13`/`b03` 予約台帳・producer 本体
(`resolve_effective_preregistration` / `PreregBinding` / `verify_receipt`) は実装していない。**
**pilot は依然として投入不可であり、本 wave は local main へ land しない。**

## 作ったもの / 作らなかったもの

| 区分 | 内容 |
|---|---|
| 作った (docs) | `erratum-core-s7-stresscheck.md` (core §7 の較正義務 → 事前固定 stress check、1 operation、`draft_unapproved`) / `record-items-reissue.md` (Q-A 第三分岐 + 未閉包 nested object 7 種の exact key 閉包 + 非保証の明記) / `package.md` (裁定 R1〜R5) / D263 事実文を失効させる decision fragment |
| 作った (コード) | 第 2 erratum の固有 validator を D263 registry へ登録。`APPROVED_ERRATA` / `DRAFT_ERRATA` で「登録 ≠ 承認」を型と検査で分離。s7 の行束縛を s15 と共有しない経路へ分離。承認予定 `new_text` の exact digest 固定 |
| 作らなかった | 承認 manifest / 受領証 JSON Schema と digest 固定 / `a13` primary 台帳と `b03` 公表台帳 / resolver・binding・verify_receipt / submission intent・PBS・driver・collector・receipt writer・correctness verifier・certified consumer |
| 閉じられなかった穴 | Q-A 第三分岐は「性能 run を実行しなかった」を証明できない (producer 権限内では原理的に閉じない) / 承認の機械的強制は投入 gate を実装する wave の責務のまま / 台帳の canonicality は単一 canonical main の運用境界に依存 |

## ユーザー裁定へ返した 5 問

1. **R1 (最重要)** — **Q-D の「同一 land」が manifest の構造要件と両立しない。**
   新しい承認済み blob は、それを承認する decision を fold した後でなければ manifest に pin できず、
   manifest は自分の fold SHA を literal に持てない。**fold 2 回 = land 2 回が構造的に要る。**
2. **R2** — Q-A 第三分岐の残余捏造余地。6 条件を満たしながら実際には性能 run を実行済みの
   attempt を構成できる (段 6 レビュー A が実証)。
3. **R3** — `a13` 台帳の保証境界 (land lock は Git common dir 内。独立 clone は防げない) と、
   追補 B `b03` による 2 本目の台帳。
4. **R4** — gate が効くために必要な未実装層の一覧。
5. **R5** — `verify_receipt` が `orchestrator/campaign/t080_freeze_migration.py` に
   既に別概念で実在する (D75 の同名二義化)。

## 親が実測した値 (一次資料から独立に算出)

```text
F_e (D262 の fold commit)     dce4ae4fed6f4fb33747165c5b92c16d01822850   HEAD の祖先 ✓
凍結 core (F 時点、450 行)     ac939af4de87dff0cd3964e37cef975d57919a709d57f4e9523c8b6a9fcd60e9
core §7 の較正義務行 (221)     225268a9fe702eae37ac3f4c150fcbc24e71835ce40bd3735ce0116784278e89
対象語句の出現件数             1 件 (221 行のみ)
erratum-1 単独の合成           d1782b04ceb7cd56a3d10e2e6efb4eb7f90e6a89506a74bba727d34a5f79de82
erratum-1 + erratum-2 の合成   dfb821a5ff0b085f7092bbd5536772a8c6728ec946291a6e6eb61da9fbef678c
承認予定 new_text (117 bytes)  92fd71754c81b45b6cc01fb14600bfdc140af8e464c50484b45e1bb8caaa01a4
locator                        {404, 424} と {221} は非重複
```

erratum-1 単独の合成は D262 の申告値を**再現**した。erratum-1 + 2 の合成と `new_text` の digest は
**親と実装子が独立に算出して完全一致**した。

## 段 6 が見つけた最重要の欠陥

親が起草した第 2 erratum の検査は「置換後も 1 行」しか要求しておらず、**任意の 1 行に置換できた。**
レビュー A の probe では次が validator を通過した。

```text
事前 simulation で cluster level の型 I 誤りを較正済みである。
```

これは erratum が除去しようとしていた**強い主張そのもの**である。
承認予定 `new_text` の exact digest 固定で塞ぎ、変異 M7 が実際に kill することで裏を取った。

## 変異

`mutation-ledger.json`。7 変異、baseline PASSED、**7/7 KILLED・SURVIVED 0・MISMATCH 0**。
事前登録 (`../2026-08-10_t139-manifest-w1-mutation-spec.json`) の期待 node と全件一致。

段 6 のレビュー B の指摘で M2 (s15 と共有 helper による過剰決定)、M4 (wave 前の形を再現していない)、
M6 (置換未固定で `KeyError` になり受理集合が拡大しない) を改訂し、M7 を新設した。

## 受入

`7994 passed / 20 skipped / rc=0` (516.74 秒、計算ノード)。
測った tip は `50b9c8de86685eaf7d828de1b61d87e07f8ef41e`。

## 逐語

`verbatim/` に段 1〜段 6 の全成果物を置く。
段 3 のレンズ 2 本、段 6 のレビュー 2 本はいずれも **NO-GO** を返した。
