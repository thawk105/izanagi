# 対話型 dev-wave を研究の主経路にする裁定と、高速化計画の相談 — 裁定の控えと相談記録の写し (2026-09-29)

- authority: none
- default_effect: no-state-change
- 役割: 決定台帳の 2026-09-29 の 2 つの決定 (対話型 dev-wave を主経路にする決定と、高速化計画から外した項目の決定。本 wave の decisions fragment が fold された D)、
  roadmap §1・§2 の協議改訂、repo 直下の `README.md` の改訂が参照する一次資料を、repo 内で引けるように bytes 一致で写したもの。
  判断の正本は決定台帳、後続作業の可変状態の正本は worklog 末尾の「次の一手」である。この dir は可変状態を持たない。
- 記録した wave: branch `dev-wave-interactive-ruling-record` (基準 main `8fe87f852`)。

## 1. 収録物

| file | 原本 (repo 外) | 原本の更新時刻 (JST) | byte 数 | sha256 (写し = 原本) |
|---|---|---|---|---|
| `verdicts.md` | `/work/1/SFC/tanab/dev-wave-jobs/rulings-inbox/2026-09-29-interactive-evolution-verdicts.md` | 2026-09-29 22:23:17 | 3981 | `0907bd168212ec930139094cf8772cfce98554d70e361599bafa49a0182b0b18` |
| `briefA.md` | `/work/1/SFC/tanab/dev-wave-jobs/interactive-evolution-consult-20260929/briefA.md` | 2026-09-29 21:44:09 | 5024 | `7aa6c2901cb9c420d999e4be7b6ad03c328e9a3bab68653753488edbf5dc2b5a` |
| `outA.md` | 同 dir の `outA.md` | 2026-09-29 21:44:09 | 3710 | `a7e87e069e4ee0ebb0f37709c4bd3f3dc63aa604160c9dd4cd827da5f6bf7695` |
| `briefB.md` | 同 dir の `briefB.md` | 2026-09-29 21:44:09 | 6790 | `7f47709de703e48badf6751da53756dda5f46cf27c98c492c3fa7523d838d7e4` |
| `outB.md` | 同 dir の `outB.md` | 2026-09-29 21:44:09 | 3713 | `acc5fe1233139f6905a5cca5f2d4a352acf27977fcd9d7e44fade8060715c776` |
| `plan.md` | 同 dir の `plan.md` | 2026-09-29 22:20:13 | 8371 | `e82635624d4f781eadd6c91445f02fe88a8b74d655d13a6c13a49b191e36c48f` |
| `briefC.md` | 同 dir の `briefC.md` | 2026-09-29 22:20:13 | 9495 | `1d20b935b3cac6c6617a4170d734ce665ad093bd4ea3a3f8ad40ae26f0d4ea5d` |
| `outC.md` | 同 dir の `outC.md` | 2026-09-29 22:20:13 | 5234 | `bfeb9f49cbe5888cf15feeaf2e7d2e9e9bca9827bad2d10943052835ab7d2cb7` |
| `briefD.md` | 同 dir の `briefD.md` | 2026-09-29 22:20:13 | 9445 | `6a1fac1bc8c3755bf6e2dc0487832834ec85b2329128773527236f689a11390b` |
| `outD.md` | 同 dir の `outD.md` | 2026-09-29 22:20:13 | 4077 | `83cc8f8c0cebb6a8b4db41d1193c6dd64a6efdd4301539311c06b9ca2cbdf1d0` |
| `common.txt` | `/work/1/SFC/tanab/tmp/speedup-2026-09-29/common.txt` | 2026-09-29 22:23:02 | 4892 | `ba80222af8f2a1427828998ea465f69b78a844417a83476b24cbefd3a130c899` |

- 出所: すべて、ユーザーと相談した親セッションが作成したもの。`verdicts.md` は裁定の控え、`briefX.md` は Codex 相談子への依頼文、
  `outX.md` はその回答、`plan.md` は高速化計画の親の初案 (相談 C・D の対象)、`common.txt` は相談後に親が並行 wave へ出した共通指示である。
  写しは本 wave が 2026-09-29 に `cp` で取り、上表の sha256 を写しと原本の両方で計算して一致を確かめた。
- 相談 A・B は対話型 dev-wave の枠組みについての相談 (A = 独立見解、B = 親の初案への最強の反論。親の初案は `briefB.md` の「Claude (親) の提案」節)。
  相談 C・D は高速化計画についての相談 (C = 計画検査、D = 反論)。

## 2. どこに何があるか

- ユーザーの問い (逐語): `briefA.md`「ユーザーの問い (逐語)」節。受領の逐語「よし。ここら辺は推奨通りで良い。」と裁定 4 項・却下 2 案・最強の反対論の要約: `verdicts.md`。
- 高速化の依頼 (逐語) と README 更新の追加依頼 (逐語): `verdicts.md`「続く依頼」「続く依頼の経過」節、`common.txt` 1 節。
- 高速化計画でやらないこと・削除の条件と記録方式: `common.txt` 2・3 節。その根拠: `outC.md`・`outD.md`。

## 3. 何を確かめ、何を確かめていないか

- 確かめた: 写しと原本の bytes 一致 (sha256)、原本の byte 数と更新時刻。決定台帳へ引いた既存 D (D700・D301・D2211 項 4・D2206 項 6・D335・D1989・D1990・D2179・D2212・D2297) の文言は、本 wave が `docs/decisions.md` の現物で照合した。
- 確かめていない: `plan.md` と各 brief にある実測値 (dev-wave 1 本の平均所要と内訳、受入全走の wall、test の所要、候補の件数と秒数) は親セッションと調査役の記述の写しで、本 wave は再計測していない。
  相談子の回答 (`outX.md`) の判断は Codex の意見であり、事実として採ったのは決定台帳が引いた範囲だけである。
- `verdicts.md` の原本は親セッションが同日中に追記しうる。写しは上表の時刻の版である。
