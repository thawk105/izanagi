# 段 4 裁定 — [T-1310] 正式 workload profile (rr80 / rr20)

裁定者 = 親。2026-08-17 23:40 JST、worktree `t1310-formal-workload-profile`、起点 main `2a3b5055`。
入力 = 段 2 プラン (`s2-plan.md`)、段 3 レンズ A (`s3-lensA.md`)、レンズ B (`s3-lensB.md`)、
親の実測 (`parent-measurements.md` M1〜M10)。

## 結論

**本 wave では正式 profile を実装しない。** 実装差分ゼロで段 5・6 を飛ばし `4→7→8→9` とする。
理由は下記 R1〜R3 であり、いずれも一次資料で親が再確認した。scope 外の real 所見は
裁定パッケージとしてユーザーへ返す。

## R1 — Layer-3 突き合わせ検査が「producer は単一 scale」を機械的に固定している (決定的)

`orchestrator/campaign/autonomous_trial_completeness.py:2272-2297` (親が直読):

```
workload = cell.get("workload")
if not isinstance(workload, str) or workload not in producer.WORKLOADS:
    _fail("campaign-chain", f"cells[{index}].workload is not producer-supported")
...
workload_flags = producer.WORKLOADS[workload]
expected_descriptor, expected_binding = producer._descriptor_for(workload_flags)
if cell.get("workload_flags") != workload_flags: _fail(...)
if cell.get("descriptor") != expected_descriptor: _fail(...)
if cell.get("descriptor_binding") != expected_binding: _fail(...)
```

検査は (a) workload が探索表 `producer.WORKLOADS` に在ることを要求し、(b) descriptor を
**profile を渡さない `_descriptor_for(flags)`** で再導出して完全一致を要求する。
プランの「3 sink へ optional な formal 引数を足す」形では、正式 run の cell は必ず (a) で落ちる。
`WORKLOADS` へ rr80 / rr20 を足しても、(b) の profile-less 再導出は探索 scale を返すため一致しない。

通せる形は原理的に 2 つだけで、**どちらも台帳項の scope を超える。**

- **形 1**: scale を workload 表の entry に持たせ、producer と検査が同じ entry から
  descriptor を導出する。→ cell に載る `workload_flags` の形が変わり、**探索側の成果物 schema と
  campaign identity も変わる。**
- **形 2**: 検査を profile-aware にする。→ これは [T-822] (i) が必須化しようとしている
  **Layer-3 検査層そのもの**の改訂であり、本項が「前提」として先に来る想定と順序が逆になる。

レンズ B 所見 1 を real と裁定し、親が独立に再現した。

## R2 — 正式受理の材料 (床値・予算) が未充填で、実測と人間承認を要する

`output/s8b-freeze/holdout_freeze.json` は `floor = null`、`budget = null`、
`refreeze_note = "floor/budget は対象別 floor 再実測後に再凍結 + 承認で充填する (設計 §5.2)"` (親が直読)。
`layer3_report.py:360-381` は floor 照合で `records` / `threads` / `workload` の完全一致を要求する
(レンズ B 所見 3)。

→ producer を配線しても正式 floor 受理と予算結果は存在しない。**配線だけを「正式 profile 実装済み」と
記録すると、床値なき成果物を正式扱いすることになる。**
レンズ B 所見 5 を real と裁定。

## R3 — DW-G04 (条件付き機能の発火 gate) が実装を禁じる

正式 profile の発火条件は「承認済み active v2 世代 + 登録済み manifest + 床値/予算」である。
親は発火条件を満たす**既存 artifact path も計測 ID も brief に書けない** (M3 `no-active`、R2、
レンズ A 所見 1 の unregistered admission 拒否 `trial_registry.py:1268`)。
`DW-G04` は「書けなければ設計メモに留める」と定める。よって実装せず設計メモへ送る。

**なお「発火しない配線を置いて C01 の静的条件だけ通す」形は、規律 2/3 が禁じる
恒真な保証そのものである** (親の暫定裁定 (P1a) はこの点でレンズ A 所見 1 に refute された)。

## 親の provisional 裁定への処理

| # | 裁定 | 処理 |
|---|---|---|
| (P1) 正式値は literal でなく実行時読取 | **維持** (repo scan の根拠は M8b で実証済み) | ただし実装は本 wave で行わない |
| (P1a) 値も identity も ratified のみ | **refuted** — 発火不能な配線 = 恒真 (レンズ A 所見 1) | 裁定パッケージ (α) へ |
| (P1b) 値 v1 + identity ratified | **refuted** — ratified identity は `no-active` で止まるので定義矛盾 (レンズ A 所見 4) | 破棄 |
| (P1c) ratified 既定 + v1 opt-in | **条件付き real** — ただし `load_verified_freeze(expected_hash=None)` は任意の working-tree bytes を受けるため不適。正しい経路は `s8b_ratified_freeze.py:1376` の `load_legacy_freeze` で、source kind を `legacy-v1` と記録し non-certifying 固定 (レンズ A 所見 4) | 裁定パッケージ (β) へ |
| (P2) 3 sink に正式 scale literal + 照合 | **維持するが根拠を訂正** — `_integers` は `ast.walk(FunctionDef)` 全体を見るため default 引数・annotation・decorator・nested・`if False` 内でも通る。C01 は実射影の証拠にならない (レンズ A 所見 5) | 実装時の要件として保存 |
| (P3) 探索既定は不変・明示 selector | **維持** | 実装時の要件として保存 |
| (P4) C01 snapshot は実測後に更新 | **維持し、対象を 1 箇所へ限定** — `:151` のみ。`:1869` は負の変異 oracle であり更新禁止 (段 2 プランの指摘、親が `:1849-1877` で確認) | brief の誤りを訂正 |

## 親の実測に対する refute の受理

レンズ A 所見 8・レンズ B 所見 11 の指摘を受理する。親の M1・M3・M4・M6・M9 は
それぞれ「現 snapshot」「現 HEAD の pointer 不在」「v1 の値の実在」「登録経路の実在」
「descriptor 単体の値域」だけを支え、**正式 scale の runtime 射影・v2 承認・正式受理を支えない。**
記録ではこの限定を明記する。

レンズ A 所見 7 も受理する。凍結 artifact 内の generator SHA は現 generator source SHA と既に相違し、
`freeze_verification_hold.py` の `HELD=True` で検査が保留中である。よって
**「pin テストが事故を止める」とは主張できない。**brief の不変条件の書き方を訂正する。

## 実装しないと決めた結果、成果物はどう変わるか (DW-G05)

本 wave 単独では **正式受理集合は空のまま**である。変わるのは台帳の記述だけであり、
certified 選択結果・レポート・proof 参照の値は 1 つも変わらない。
逆に「実装した」と記録した場合は、床値なし・世代未承認・Layer-3 検査を通れない配線を
正式 profile として参照させることになり、そちらが成果物を汚す。

## ユーザーへ返す裁定パッケージ (択)

- **(α) 順序を入れ替える**: [T-1310] を「正式 profile 実装」から「正式 profile の**前提の充填**」へ
  組み替える。すなわち (1) 床値/予算の対象別再実測、(2) v2 世代の発行と承認、
  (3) Layer-3 検査の profile 対応 (= [T-822] (i) の層) を先に置き、producer 配線を最後にする。
  親の推奨はこれ。理由 = R1 の形 1 / 形 2 のどちらを採るにせよ、検査層と成果物 schema の
  裁定が producer 配線より先に必要である。
- **(β) 自作の証拠水準を明示的に下げる**: `load_legacy_freeze` による `legacy-v1` 源を
  正式 profile の暫定源として認め、non-certifying と明記したうえで rr80 / rr20 を
  1,000,000 / 48 で**実測できるようにする**。物理的な測定自体は今日でも可能であり、
  塞いでいるのは v2 承認と床値という自作の手続きである。採る場合は R1 の形 1 / 形 2 の
  どちらかも同時に裁定が必要。
- **(γ) 現状維持**: [T-822] (i) を「前提未充填のため見送り」のまま置き、本項も凍結する。
  親は推奨しない (8c 正式受入が無期限に空のままになる)。

## 本 wave の成果物

docs のみ。実装面の差分は 0 件。

- worklog fragment: 本裁定と R1〜R3、実測 M1〜M10、[T-1310] / [T-822] (i) の書き換え、
  新規台帳項 (探索経路の byte 単位非回帰固定 = レンズ B 所見 7、profile selector の
  fail-closed = 同所見 8 は、実装を行う wave の要件として登録する)
- decisions fragment: R1 (単一 scale 前提の機械的固定) を設計判断として記録するか段 7 で判定
- insights package: 子 3 本の逐語 + 親の実測

## 変異 matrix

`DW-S04` により、「実装しない」と裁定済みで実装差分ゼロの wave は変異 matrix を免除する。
受入全走は免除しない。
