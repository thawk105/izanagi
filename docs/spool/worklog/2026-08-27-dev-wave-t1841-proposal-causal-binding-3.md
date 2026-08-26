---
schema: izanagi-spool-v1
ledger: worklog
authored: 2026-08-27
wave: dev-wave-t1841-proposal-causal-binding
seq: 3
title: [T-1841] 決定と proposal の因果束縛は hash 鎖では閉じないと確定し、代わりに鎖の根で受領証要求が丸ごと飛ぶ穴を塞いだ (コード + docs、branch worktree-dev-wave-t1841-proposal-causal-binding、変異 matrix = baseline PASSED・6/6 KILLED・SURVIVED 0・MISMATCH 0)
---

## 本文

- **依頼された機構は非恒真な形で実装できないと確定した。** 段 2 の設計案 (決定原像を正規生成器へ
  渡し、生成後の proposal bytes を独立 handoff receipt へ内包する) について、段 3 の 2 レンズと
  親の裏取りが同じ結論に達した。terminal receipt を持つ者は隣接する envelope を読め、
  handoff の全欄を自分で計算できる。秘密・署名・外部権威が 1 つも関与しないため、
  決定を無視した proposal に整合する受領証を作れる。自己申告の所在が file 1 枚ぶん移るだけで
  D1061 が却下した形と同型になる。裁定は {{D:causal-proposal-binding-needs-unforgeable-receipt}}。
- **代わりに、同じ鎖の根に空いた穴を塞いだ。** `loop_state.json` を 1 つ消すか zero state へ
  置換するだけで、継続が bootstrap と誤認され受領証の要求が丸ごと飛んでいた。受領証の偽造すら
  不要で、critic の決定を 1 度も経ていない iteration を certified B-4 標本へ足せた。
  裁定は {{D:b4-bootstrap-bound-to-authoritative-history}}。
- **変異走行だけが検査漏れを暴いた。** 第 1 回 probe で「gate を全状態へ適用する」変異が生存した。
  段 3 と段 6 の敵対レビュー 4 本はいずれもこの穴を指摘していない。正例が gate の発火する側しか
  覆っておらず、早期 return の枝が無検査だった。F161 へ再発として記録した。
- **親が段 1 で書いた前提のうち 2 件を段 3 が訂正し、受け入れた。** (a)「D1061 が本 wave を後続として
  指名した」は裁定本文に無い。発注はユーザー指示である。(b) 実測の一般化が過大だった。
  正しくは「同じ受領証に対し任意の 1 本を流せる」で、実 driver は受領証 hash を鍵に消費記録を
  排他公開するため 2 本目は止まる。
- **B-4 実走の追加前提が 1 つ増えた。** `p3_s4_loop.py` は 3 driver すべての projection 閉包 entry
  なので、本 wave の bytes 変更で base / sort / trigger の `projection_sha256` がすべて変わる。
  既存 receipt と登録済み期待 hash は失効する。**これは閉包の正しい挙動であり、旧 hash を受理する
  緩和はしてはならない。** 実際には B-4 未実走で事前登録 §5 の当該欄も未記入のため、
  壊れる登録値は無い。実走前に新 hash を登録する必要がある。
- 工数: codex 子 9 本 (plan 1、consult 2、author 1、review 2、fix 3、focus 1)。
  全数 `gpt-5.6-sol` / `xhigh` / accepted。実装子と fix 子はいずれも dispatch 基盤の rc=16 で
  テストを実走できず、緑の一次資料はすべて親の実走である。
- 裁定 inbox の `2026-08-27-b4-run-owner-assigned.md` は、当該 doc を触る wave が実行責任者欄を
  埋めるよう求めている。本 wave は同 doc を触らない裁定にしたため手を出していない。控えは残る。

## 次の一手差分

### 更新

- [T-1841] **P1・ユーザー裁定待ち**: 決定と proposal 本文の因果束縛。
  hash 鎖では閉じないことが確定した ({{D:causal-proposal-binding-needs-unforgeable-receipt}})。
  択一は (a) 生成前の依頼を封じ応答を provider 受領証で束縛する形 — D39 決定 7 の supersede と
  実験対象の変更を伴う、(b) D1099 の方針どおり偽造不能受領証の機構へ相乗りする形。
  裁定パッケージは wave 成果物 dir の `s4-ruling.md`。
  base: 85b99e42a52a6f922118ccaee41dc8a45d9e3c75f518d83a915b6d7d11890891
- [T-1911] **P1・ユーザー裁定待ち**: [T-1841] と同一主題である。裁定は [T-1841] へ集約する。
  base: 623ecb8c8a93f4c1fcf1f8890cc426a2db1510347775d49a6bb4fc451d458b87

### 新規

- {{T:b4-consumption-before-entry-stop}} **P2・新規**: 消費記録が入口停止判定より先に公開され、
  実行されなかった proposal を消費済みとして記録する。3 driver とも同じ順序である
  (base は消費 → 停止判定、sort と trigger も同型)。**修正方向が設計択一**である —
  消費を後ろへ動かすと、停止した iteration の受領証が後で再利用できるようになる。
- {{T:b4-projection-hash-registration-before-run}} **P2・新規**: B-4 実走前に、3 driver それぞれの
  新しい projection closure hash を事前登録と admission record へ登録する。
  本 wave の `p3_s4_loop.py` 変更で全 driver の値が変わった。旧 hash を受理する緩和はしない。
