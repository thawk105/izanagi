---
schema: izanagi-spool-v1
ledger: worklog
authored: 2026-08-18
wave: dev-wave-t848-mutation-timeout
seq: 1
title: 変異 TIMEOUT の生きている穴は local 申告 × 実 dispatch だった — 台帳 status を増やさず D454 の停止形へ寄せた (コード + テスト + 記録、branch worktree-dev-wave-t848-mutation-timeout、変異 matrix = baseline PASSED・5/5 KILLED・MISMATCH 0)
---

## 本文

- **台帳項の前提が実測で覆った。** [T-848] は「dispatch subprocess 全体に timeout が掛かるため
  一度も走っていない変異が terminal を満たす」と書いていたが、dispatch 経路は D454 が
  orphan-hold 停止を契約しており既存テストも固定していて、HEAD で再現しない。
  親は当初この閉鎖を「偶然で未固定」と誤認した。status 集合の識別子だけを検索し、
  挙動側の pin を見落としていた。段 2 プランが D454 を指摘して是正された。
- **生きていたのは local 経路。** `--runner-mode local` は実際に dispatch しないことを
  何も保証せず、harness は申告と runner argv の実体を突き合わせていなかった。
  この経路では orphan 防壁も receipt 束縛も働かない。
- **status を増やさないと裁定した。** 決め手は「新 status を足しても producer が 1 本も残らない」
  こと。schema v5 は既存 v4 台帳の resume と v4 shard の再併合を全滅させる。詳細は {{D:mutation-timeout-local-stop}}。
- **台帳項が指示した「別 status」は実装せず、ユーザー裁定へ返す。** 親の推奨は「足さない」。
  新事実は (1) dispatch 経路は D454 で決着済み、(2) local では receipt での RUN 確認が原理的に
  不成立、(3) v5 の互換性代償、(4) 実装後は新 status の producer がゼロ。
- **不在の実測を 1 度誤った。** 親は最初「全史 TIMEOUT 0 件」と報告したが、probe が
  object 形式の `*.json` だけを見ており list 形式と JSONL を落としていた。
  敵対レビューが指摘し、走査を JSON 2026 件 + JSONL 122 件へ広げて測り直した。
  正しくは「harness 台帳形式では 0 件、schema 以前の手書き台帳 2 件が hang timeout を記録」。
- **fix は 3 巡を要し 2 巡目で回帰した。** 2 巡目はテストだけを触ったのに 26 件が赤になった。
  根本原因は共有生成 fixture の二重 escape 不足で、全 test repo が SyntaxError になっていた。
  3 巡上限に達した後、親が裁定して 1 点だけ変更させた ({{D:mutation-timeout-local-stop}} の nonce 単独判定)。
- **焦点再レビューは NO-GO を出したが、主根拠は親の実測で refuted。**
  「nonce が request に載らない」という主張に対し、親は
  harness → `run_tests.py` (同変数に触れない) → `_dispatch_environment()` (素通し) →
  dispatch の env allowlist → `request.json` の各段を実コードで確認した。
  ただし副次的な指摘は正当で、テストは carrier 連鎖の 1 段を pin していない。後続タスクへ。
- 工数: codex 子 10 本 (plan 1 / consult 2 / author 1 / review 2 / fix 3 / focus 1)。
  親の実測は焦点走 4 回、変異走行 2 回 (probe + 本走)、全史 provenance 監査 1 回。

## 次の一手差分

### 更新

- [T-848] **P1・ユーザー裁定待ち**: 実装面は決着した。dispatch 経路は D454 で既に閉じており、
  生きていた local 申告 × 実 dispatch の経路を停止 sidecar で閉じた
  ({{D:mutation-timeout-local-stop}})。変異 matrix = baseline PASSED・5/5 KILLED・MISMATCH 0、
  焦点走 196 passed。**残るのは「台帳へ queue 側 status を新設するか」の裁定だけ**である。
  親の推奨は「足さない」。新事実は (1) 台帳項が名指しした dispatch 経路は D454 で決着済み、
  (2) local では receipt での RUN 確認が原理的に不成立、(3) schema v5 は既存 v4 台帳の resume と
  v4 shard の再併合を全滅させる、(4) 本 wave の実装後は新 status の producer がゼロになる。
  base: b02f50f1c6bd37fa935c63bf032a5c2bbee001f0d1aed230f59057c9489fcea4

### 新規

- {{T:mutation-nonce-carrier-pin}} **P2・新規**: 変異 harness の走行束縛 nonce が
  `run_tests.py` から dispatch の `request.json` まで実際に運ばれることを、
  fixture の自己複製ではなく連鎖として固定するテストを足す。
  現在テストは `request.json` を fixture 自身が書くため、carrier が壊れても緑のままになる。
- {{T:mutation-worktree-stop-reason}} **P3・新規**: `tools/mutation_worktree.py` の receipt が
  local 停止の理由を分類できるようにする。現在は wrapper の rc は child の 2 を返すので
  偽の緑にはならないが、`failure` 欄が null のままで停止理由を機械検証できない。
