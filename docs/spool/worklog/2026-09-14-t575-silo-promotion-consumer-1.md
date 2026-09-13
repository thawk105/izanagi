---
schema: izanagi-spool-v1
ledger: worklog
authored: 2026-09-14
wave: t575-silo-promotion-consumer
seq: 1
title: [T-575] silo ladder 証拠の適格性昇格 consumer は確認した閉包で不在と確定し、ability-probe writer を昇格入口に数えないことにした (docs のみ、branch worktree-dev-wave-t575-silo-promotion-consumer)
---

## 本文

- 2026-08-06 の起票以来の持ち越しを閉じた。判定は {{D:silo-promotion-consumer-absent}}。
  **適格性への昇格を行う consumer は、確認した静的参照閉包に存在しない。**
  証拠を検査・発行する consumer と、Python 以前に書く shell/PBS writer は実在する。別物である。
- **決め手は producer 側にあった。** 発行 document の `classification` が
  `ability_probe` / 研究非適格 / 回復非適格のリテラルで固定されており、**適格な成果物を出す枝が無い。**
  再読側の validator も同じ値を要求する。ladder driver が condition gate へ渡す用途は
  `raw-measurement` (昇格用途は `certified-selection` / `floor` / `oracle` / `paper`) だが、
  **これは用途の宣言であって機械的な昇格禁止ではない** — 同 gate の受理判定は raw と promotion で
  分岐しない。**親は当初これを「決め手」と書き、さらに「昇格用途の call site は oracle の 1 本だけ」
  という誤った実測を添えていた。** 段 6 のレビューが現物で反例 (`p3_s4_loop.py:441` の
  `certified-selection`、`paper_story_a2_certification.py:784` の `paper`) を出し、親が検算して訂正した。
  原因は親の検索出力が `head` で切れ、テスト除外の指定も効いていなかったこと。
- **段 3 の 2 レンズが、親と段 2 の探索範囲を独立に 2 箇所で訂正した。** (a) 段 2 が `output/**` を
  丸ごと探索から落としたのは根拠不足で、両レンズが output 配下の現用 README を読み直した
  (昇格誤記は 0 件)。(b) 段 2 の参照鎖表は Python 関数に偏り、shell/PBS の実在 writer を
  挙げていなかった。**昇格の反例にはならないが、入口被覆率の根拠としては不足していた。**
- **「訂正対象 0 件」という親の暫定判定は過小だった。** レンズ B が `patches/README.md` の
  「新 rung は登録必須」に、現行契約が ledger の entry 数を 1 に固定しているという限定が
  欠けていることを見つけた。親が `silo_ladder_rung1_contract.py` の現物で検算して採用し、
  2 箇所へ限定句を足した。登録は必要条件であって、新 rung を入れる入口が在るという意味ではない。
- 「silo 昇格入口」という語そのものの現行 (非凍結) 側の出現は 0 件。`docs/archive/**` と
  `output/insights/**` には出現するが、そこでの用法は「未実装と名乗る」という裁定そのものであり、
  凍結記録でもあるため訂正しない。
- **D162 決定 (7) では本件は閉じない**と判定した。同決定の対象は `patches/ledger.json` の 3 適格性
  field を昇格権威として読む consumer であり、T-529 の 6 入口列挙では「適格性」と「silo 昇格」が
  別項目である。本 wave は ledger を経由しない経路 (成果物 classification、condition gate の
  use class、materializer 登録、共有依存 helper、shell/PBS writer) まで広げて確認した。
- 親が段 2 の prompt で候補を列挙した際、`ability_probe` を「false から true へ変える」対象に
  混ぜたのは誤り。同 field は既に `true` である。レンズ A が指摘し、記録では独立した確認事項へ直した。
- 実装面 (D95 決定 2 = 非 Markdown) の差分はゼロ。変異 matrix は免除。受入全走は免除していない。
- Codex 子 4 本 (plan 1 / consult 2 / review 1)。いずれも read-only。子は file を 1 byte も変更していない。
- 成果物と生証拠 = `output/insights/2026-09-14_t575-silo-promotion-consumer/`。

## 次の一手差分

### 完了

- [T-575] silo 昇格を実行する consumer を探し、**適格性への昇格を行う consumer は確認した静的参照
  閉包で不在**と確定した。ability-probe writer を活性化権限の「silo 昇格入口」に数えないことにし、
  `patches/README.md` の登録手順へ exact-one の限定を足した。silo の書込み入口そのものは実在するので
  入口調査からは外さない。無限定の不存在保証はしていない。
  remaining: none
  base: 211541bcf4aabaa49490f092f4351a88c3dc8614a01005f76d664270580bbd9d
