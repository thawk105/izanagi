# 2026-08-13 [T-139] land 2 / Q4 組み替え scope — 先行 2 閂は解消したが承認済み契約が塞いだ、実装ゼロで land

wave `dev-wave-t139-land2-q4` / branch `worktree-dev-wave-t139-land2-q4`。base = local main `adf7997f`。
**実装面差分ゼロ。ただし land した。**

## この wave が何をしたか

指示は「[T-139] land 2 を Q4 の組み替え scope で完了 land させる」だった。
Q4 = 「投入の実務経路 (`submit_pilot`・PBS driver・collector) + D292 を上書きする解除 decision +
束縛検査だけを 1 session・同一 land で組む」。

段 2 のプラン起草と段 3 の敵対 2 レンズが**独立に NO-GO** を返し、親は段 4 で
**Q4 scope を実装しない**と裁定した。根拠は裁定時点で未見だった事実 4 件である。

| file | 内容 |
|---|---|
| `verbatim/s1-brief.md` | 段 1 brief — 実測 M1〜M9、前提 9 件の表、provisional 裁定 (P1)〜(P6)。**(P1) と (P1b) は後に撤回** |
| `verbatim/s2-plan.md` | 段 2 プラン起草 (codex, reasoning=max) — file:line プランを書いたうえで **NO-GO** |
| `verbatim/s3-lensA.md` | 段 3 レンズ A「正しさ境界」— **NO-GO**、所見 A-01〜A-12 |
| `verbatim/s3-lensB.md` | 段 3 レンズ B「整合・実効性・発火点」— **NO-GO**、所見 B-01〜B-15 |
| `verbatim/s4-adjudication.md` | 段 4 裁定 — real/refuted 22 件、親 brief の訂正 5 件、変異免除の根拠 |
| `package.md` | 裁定パッケージ **K1〜K5** (ユーザー手番) |

## 先行 wave の閂 2 件は解消していた (これは前進である)

worklog archive エントリ 470 が同じ Q4 scope で NO-GO を返したときの閂は、本 wave の実測では
**どちらも解けていた**。

| エントリ 470 の閂 | 本 wave の実測 |
|---|---|
| (i) `a12` が実装・実走 0 件 | **解消。** R1 (a) の裁定に従い独立 wave が完走 (2026-08-12、job `907407.nqsv`、計算ノード bnode013)。pass artifact は tracked |
| (ii) `a09` serialization が `record-items-v2.md` §10 の未承認閉包 4 | **解消。** R2 (a) が「canonical `schedule_sha256` を名乗らず `operational-only` とする」で回避経路を確定。段 3 レンズ B も「計画文面上の R2 (a) 違反は確認していない」と追認 |

**本 wave の NO-GO はこれらとは別の根による。**

## 中核の発見 — 承認済み契約の必須引数が、先送りされた層そのものだった

**D234** が固定する契約は次である。

```text
submit_pilot(*, binding: PreregBinding) -> submission_id
```

同 decision は「`binding` が `resolve_effective_preregistration` から返っていない限り
**実行してはならない**」と書き、(i)〜(vii) の 7 条件を課す。

**`PreregBinding` と `resolve_effective_preregistration` は pilot 投入前提 #6 そのもの**であり、
Q1 / Q2 の下流として本 wave の scope 外である。恒真かどうか以前に、
**承認済み API 契約の必須引数が存在しない。**

段 2 が提案した `submit_pilot(*, submission_id: str)` は D234 と別物であり、
段 3 レンズ B が [B-01] で blocker と判定した。

## R1 (a) の裁定理由が実測で反証された

R1 (a) の理由欄は「完走すれば正例が構成可能になり、R3 の恒真問題が自然に解消する」と書いた。
**`a12` の成果物自身がこれを否定する。**

```text
verdict                             = pass
run_status                          = completed
claim_scope.pilot_ready             = false
remaining_unmet_pilot_prerequisites = [1, 4, 5, 6, 7, 8, 9]
```

(`output/env/pegasus/t139-a12-stress-check/full-v1/stress-check-simulation.json`)

`a12` の完走が満たすのは前提 **#3 だけ**である。#4〜#6 (受領証 schema の digest 束縛 /
approval manifest / resolver + `PreregBinding` + receipt writer) は未実装のまま残るため、
`submit_pilot` の最終受理集合は依然として空であり、**正しい staged gate と
「診断だけ計算して最後に定数 deny する実装」が観測上区別できない**。
レンズ A は「現 scope 内でこの区別不能性を消す設計は無い」と断言した。

なお `claim_scope` は producer 申告値であり、`record-items-v2.md` §8 の否定検査が
「受理条件の入力に使ってはならない」と列挙する型と同種である。gate は再導出しなければならない
(レンズ B [B-04])。**本 README も認可根拠には使わず、状態の記述としてのみ引用している。**

## 裁定の内部矛盾 (ユーザー手番。K1)

同じ T-139 Q1 / Q2 に、選択肢集合が同一で結論が正反対の裁定が 2 つある。

| 束 | 日時 (JST) | Q1 | Q2 |
|---|---|---|---|
| 第 2 束 | 2026-08-12 12:38 | 機構を新設しない | 機構を新設しない |
| 第 7 束 | 2026-08-13 00:41 | (a) canonical decision 1 本 | (a) 固定 envelope + namespaced projection |

第 7 束は第 2 束が却下した当の機構を選ぶ。**本 wave への指示自身も両方を書いている**
(Q1/Q2 を (a) としつつ「D320 により承認機構は新設しない」)。
レンズ A [A-11] は「第 7 束が後発として上書きした」と判定した。

**走行中に canonical 側で決着した。** 受入 1 回目の後に取り込んだ main のエントリ 516 が、
第 7 束の読みで [T-139] 項を確定させていた —
「Q4 = (a) 裁定確定後に 1 session で manifest + resolver + writer + validator + vectors を組む。
… **次は Q1 の canonical decision 起草 → 投入経路 session**」。

**canonical 台帳が示すこの順序は、本 wave が実装可能性の側から独立に到達した順序と一致する。**
別々の根拠 (台帳側 = 裁定の後発性、本 wave = D234 の契約と受理集合の空性) から
同じ順序に到達したことになる。K1 は「どちらが有効か」ではなく
「D320 の但し書きが第 7 束 Q1/Q2 (a) にかかるか」の確認へ縮小した。

## 親 brief の訂正 5 件 (本 README と `verbatim/s4-adjudication.md` が正本)

1. **(P1) を撤回。** 「層を分ける / 所有 6 前提で正例を構成 / `authorized` を名乗らない」の 3 点セットは
   R3 (a) に適合しない。R3 が縛るのは最終 admission の受理集合であり、
   所有層の観測を非空にしても受理集合は空のままである。
2. **(P1b) を撤回。** テスト fixture の解除 decision は parser の正例であって、
   D292 が要求する「canonical 台帳へ fold された decision」の正例ではない。
3. **D308 の引用を撤回。** D308 の決定本文は床値 build の compiler site 依存化と
   toolchain 束縛検査に限定されており、pilot 解除の同一 land 義務の直接根拠ではない。
   根拠は Q4 裁定の逐語である (レンズ A [A-06])。
4. **§3.1 の「scope 外」分類に注記。** 第 7 束を後発有効と読むなら、#4〜#6 は
   「実装禁止」ではなく「Q1 decision 後に実装」である。
5. **pilot precheck handoff の #3 行は superseded。** 同 handoff は `a12` を
   「実装も実行結果も 0 件」と記録するが、これは a12 wave 完走前の実測である
   (レンズ B [B-05])。現況の正本は tracked artifact である。

## 副次的発見 — R5 の起票前提が現物と食い違う

R5 は `orchestrator/qualification/submission.py:150` の `_durable_json` を
「単発 `os.write` で short-write 検査も read-back も持たない」とした。
**親の実測 (`:143-164`) では short-write ループ + `os.fsync(fd)` + 親 directory の `os.fsync` を
既に持つ。** 欠けるのは read-back 検証だけである。K4 で是正を問う。

## land したもの / しなかったもの

**land した:** 本記録と裁定パッケージ、段 1〜4 の逐語、worklog / failures fragment。
**実装面差分はゼロ。**

**land しなかった:** 解除 decision、`submit_pilot`、PBS driver、collector、束縛検査、
D264 のテスト期待値変更。

**pilot / 本走は依然として投入不可。** 認可は裁定で解かれたが、D292 が要求する
canonical decision が台帳に無く、投入機構も存在しない。

## 変異 matrix と受入

- **変異 matrix は D301 の連言で免除** (「実装しない」裁定 + 実装面差分ゼロ)。
  なおレンズ B [B-03] が「#4〜#6 の前段拒否が後段変異を先取りする」と実測しており、
  **仮に実装していても変異の単一理由帰属は成立しなかった** (`DW-M01` の登録要件を満たさない)。
- **受入全走は免除していない** (D301 が明示)。[T-836] (c) の実手順に従い、
  **記録 commit を含む最終 tip で走らせ、結果数値は worklog でなく land 報告が持つ**。
- **main 由来の既知赤 1 件を親が独立に実測済み** — `adf7997f` の時点で
  `orchestrator/campaign/s8c_preregistration.py` の `_assert_history_transition` が
  octopus merge `d1de13ad` (親 4 つ) を `PreregistrationError("octopus-merge")` で拒否する。
  本 wave の差分とは無関係で、ユーザー裁定 (2026-08-13 01:05 JST) により既知赤として land 可。
