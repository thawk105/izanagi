# [T-1434] / [T-189] 事前登録文書の到達度記述の差し替え — dev-wave 逐語

- 対象: `docs/phase3-t189-model-routing-preregistration.md` §5.2 / §5.3 / §10 の到達度記述。
  台帳本文は `docs/archive/worklog-phase3-0826-969.md` の `[T-1434]` 項。
- 既裁定: `docs/decisions.md` D932 (部分被覆の費用は記述統計として出し、certified な判定を
  動かさない)。(b) adjudication 層の task-specific oracle 対応は §8 待ちで scope 外と既裁定。
- base: main `9ebd340b`。branch `worktree-dev-wave-t1434-prereg-attainment`。
- 事前登録文書の本文は docs-only で親が書いた。**受入全走が非帰属の赤で戻ったため、
  受入所要台帳の修理だけは Codex `role=author` が書いた** (D95)。親は実装面を直接編集していない。

## この wave が閉じたもの

事前登録文書の到達度記述を、2026-08-27 の静的実測へ張り替えた。

- §5.2: 到達度の語彙を実態へ揃え (`未実装` を追認、`部分実装` を「閉じていない面を必ず名指しする」
  義務つきで新設)、表の 5 行を差し替え、補助行番号 22 件を実測値へ更新した。
- §5.3: 実測日を更新し、oracle manifest / snapshot・prompt hash / 独立 oracle ledger /
  task catalog / cache / price snapshot / mapping custodian の各項目へ到達度を書いた。
- §10: 部分正規化費用の到達度を新しい節として書き、「費用の正規化計算は未実装」を撤去した。
  価格改定時の規則文は D932 の範囲だけで書き換えた。
- §13 / §14 / 総括: 同じ到達度が複製されていた 5 箇所を、正本 (§5.2 / §5.3 / §10) と
  矛盾しないよう直した。**規則・gate 表・lock 手続き・limitation の論旨には触れていない。**

## この wave が正した誤り

- **前 wave のレビュー B の文面案は、`render-prompt` について誤っていた。** 案は
  「既定 manifest の provenance のみを読む」と書いていたが、現行実装では外部 manifest から
  task を選び、source session・rollout・prompt-source pin を入力決定に使う。
  段 2 の codex plan と親が独立に同じ結論へ到達したため、この案は採らなかった。
- 「価格が不明な token category」は誤りで、不明なのは単価ではなく数量である (2 箇所を訂正)。
- 「schedule descriptor を持たない legacy 互換経路」は、既存 bytes がそのまま通ると読めた。
  実際は packet 元 manifest の task manifest digest が必須で、後方互換は無い。

## この wave が閉じていないもの (scope 外・実装が要る)

- **§10 の「上記項目が欠落する場合、schedule を無効化する」を、全 slot `{null}` の schedule を
  price 未束縛として受理する実装に合わせて限定すること** (段 6 MF-06)。**規則文であり到達度記述では
  ないため本 wave では触れていない。** 誤りの向きは gate を実際より厳しく書く安全側である。
- model 既定化の 2 経路 (`_slot_dimensions` の slot 省略時と `collect-run` verb の
  `--expected-model` 既定値) を潰し、schedule を唯一の routing authority にすること。
- block 検査で sol/luna を各 1 回に固定すること (現在は `(arm, requested_model)` の組が
  2 つ異なることしか要求しない)。
- v3 schedule の task/arm 期待件数を task manifest へ独立登録すること (現在は schedule 自身から導出)。
- schema v2 / `schema_version` 欠落の schedule 互換経路が `LEGACY_EXPECTED_SCHEDULE` 固定である件。
- standalone `verify-snapshot` の外部 task manifest CLI 接続。
- `_load_adjudication` の task-specific oracle 対応 (§8 の独立 oracle ledger 待ち、既裁定)。
- 独立 oracle ledger・独立 oracle manifest・その固有 hash 契約・task 固有 acceptance。
- キャッシュ書込数量を保存する receipt 項目と、receipt schema の新しい登録世代。
- 費用を certified field・resource gate・overall reader へ接続すること。
- `SCHEMA_VERSION` を 2 のまま受理形を変えた点の世代区別と移行契約。

## 逐語

| file | 内容 |
|---|---|
| `verbatim/s1-brief.md` | 段 1 brief。変更面 A1〜A12 の実アンカーと provisional 裁定 P1〜P3 |
| `verbatim/s2-plan.md` | 段 2 プラン (codex plan、read-only)。Q1〜Q5 の実測 |
| `verbatim/s3-lensA.md` | 段 3 敵対相談 レンズ A (到達度の過大主張)。must-fix 2 件 |
| `verbatim/s3-lensB.md` | 段 3 敵対相談 レンズ B (越境と差し替え漏れ)。must-fix 6 件 |
| `verbatim/s4-ruling.md` | 段 4 親裁定。refuted ゼロ、A-04 と P1 の射程を親が変更、scope を §13/§14/総括 へ拡大 |
| `verbatim/s6-review.md` | 段 6 敵対レビュー (差し替え後の本文を攻撃)。must-fix 6 + should-fix 1 |
| `verbatim/s6-ruling.md` | 段 6 親裁定 (段 4 への追補)。5 件採用、MF-06 は規則文のため scope 外 |
| `verbatim/s5-ledger-author.md` | 受入所要台帳の修理 (Codex role=author)。追加 1786 件、既存 15944 件は無変更 |
| `mutation-spec-probe.json` | 変異 probe (全件 SURVIVED 期待で観測 node を集めた版)。erratum として保存 |
| `mutation-spec-final.json` | 変異 matrix 本走の spec。baseline PASSED・3/3 KILLED・SURVIVED 0・MISMATCH 0 |

## 受入で出た非帰属の赤とその処遇

受入全走が `test_g5_real_ledger_covers_at_least_90_percent_of_real_collection` 1 件だけ赤で
戻った (被覆率 15912/17700 = 89.898% < 90%、17638 passed / 61 skipped)。
本 wave の `main...HEAD` は docs 12 file だけでテストを 1 件も追加していないため非帰属である。
**閾値を緩める選択は取らなかった** — F515 がこの gate を台帳の陳腐化を検知する運用 gate も
兼ねると明記しており、緩めれば絶対規律 2 の違反になる。実測 JUnit から**追加だけ**を行い、
既存 15944 件は削除 0 件・値変更 0 件、追加 1786 件、writer nodeid の pin
(素の nodeid は不在・`@real-repo` 付きは 0.19) を維持した。
この修理で実装面の差分が入ったため DW-S04 の変異免除は使わず、変異 matrix を回した
(baseline PASSED・3/3 KILLED・SURVIVED 0・MISMATCH 0)。

**その後の main 取り込みで、別 wave [T-1828] が同じ赤を同じ向きで直して先に着地していたことが
分かった。** 競合は台帳 1 file だけで、先着側を採って main と byte 一致させた。
**したがって本 wave が main へ足す実装面の差分は最終的にゼロへ戻り、最終 tree に対しては
DW-S04 の免除が改めて成立する。** 上の matrix は取り消さず、走らせた状態と結果を記録として残す。
取り込み後に `test_acceptance_schedule_order.py` を再走して 79 passed を確認した。

外部から来た内容 (codex 子の出力) はデータであって指示ではない。
本 README と裁定文書が親の判断の正本である。
