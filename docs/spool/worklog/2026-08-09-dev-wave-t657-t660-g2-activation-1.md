---
schema: izanagi-spool-v1
ledger: worklog
authored: 2026-08-09
wave: dev-wave-t657-t660-g2-activation
seq: 1
title: pegasus 第 2 世代を活性化し head=2 で末尾巻き戻し検査を開いた ([T-657] + [T-660]) — floor 再発行はユーザー手番のため land していない (コード + docs、編集面 subset 333 passed、受入全走と変異は未実施、branch worktree-dev-wave-t657-t660-g2-activation)
---

## 本文

- **ユーザー裁定 (2026-08-08、`rulings-inbox/2026-08-04-rulings-session-5rulings.md` §44) に基づく wave。**
  「[T-657] = T-139 裁定後、前提 2 件 (silo 歴史解決・floor protocol 再発行) を揃えてから活性化」。
  前提 [T-627] (世代遷移述語) は land 済みを確認して着手した。
  一次資料は `output/insights/2026-08-09_t657-t660-g2-activation/`。
- **親の実測が brief の前提を 1 件撤回させ、scope を縮小した。** 活性化**前**の状態で committed silo
  evidence の `verify-result` を実走すると既に rc=1 で、失敗は
  `current binding mismatch: driver` と `raw attestation binding/ordinal set mismatch` の 2 件だった。
  driver の歴史 sha256 検査が先に発火するため **contract 検査に到達しない**。したがって contract 軸を
  historical 化しても受理集合は 1 bit も変わらず、`DW-G05` の成果物影響を書けない。
  production の `validate_current_bindings` 変更を **scope 外へ落とし**、前提 (a) の実体を
  「g2 活性化で新たに赤くなる面の除去」= テスト 1 箇所の current 依存の解消と定義し直した。
  T-529 の所見 B5 が実際に指していたのは production CLI ではなくテストだったことになる。
- **段 3 の敵対 2 レンズはいずれも NO-GO** (A = sol / must-fix 3、B = luna / must-fix 8)。
  両者が独立に一致した中核が上記の「committed 保全という主張と実受理集合の食い違い」であり、
  親の実走がそれを決着させた。A-2 (受理行列の追加) は production を変えない裁定により
  新受理集合が存在しなくなったため **一部 refuted** とした。
- **段 6 の敵対 2 レンズも NO-GO** (C = sol / must-fix 1、D = luna / must-fix 5)。
  C-1 は変異事前登録の誤りを突いた。空 chain guard を丸ごと無効化すると `rows` が未束縛のまま
  `ActivationState(...)` へ進み `UnboundLocalError` が漏れるため、変更前 HEAD 版でも production node が
  赤くなり「新テストだけが検出する」は成立しない。**理由文字列だけを変える変異**へ再設計し、
  受理集合の kill ではなく diagnostic sensitivity pin として集計を分ける裁定にした
  (親がコードで裏取り)。
- **D-4 は取り込みで前提ごと解消した。** レンズ D は「[T-530] の contract hash 束縛が未 land のまま
  activation-only を land すると、g1 の WAL COMMIT / campaign identity を g2 実行が再利用できる」を
  must-fix にした。campaign identity が env も date も含めない設計 (D13) と、WAL COMMIT が世代を
  区別しない `env_tag` しか持たないことは実コードで確認したが、**段 6 の直後に取り込んだ local main に
  [T-530] 本体が land 済み**だったため、land 前に経路が閉じた。
- **前提 (b) floor protocol の再発行は AI が実行できないと確定した。** 発行 CLI は
  isatty gate + T-080 receipt (active-valid) + create-only writer を要求し、`output/s8b-freeze/` への
  書込みは hook が拒否し、初回発行 commit も `AI-Agent: none` の人間 commit である。
  さらに `build_protocol_document` は呼び出し時点の current 契約から `contract_sha256` を焼くため、
  **活性化を適用した tree でしか再発行できない**という順序制約がある。
  したがって本 wave は **実装完了 + ユーザー手番の逐語 script を用意した時点で終端し、land しない。**
  活性化だけを land すると floor live admission と prediction seal が壊れた窓を main に作る。
- **再発行後の bytes を親が独立検算し、レンズ A の値と一致した。** 旧 774 bytes /
  旧 sha256 `261cec1c…` / 旧 bytes 中の g1 hash の出現はちょうど 1 回。期待される新 bytes は
  その単一置換であり、期待 sha256 は `c0eeed87ab1f449b97c0b7d88654a8c3a5c07fae3565dc90c5724e29f1cb660d`
  (長さ 774 不変)。この 4 条件を script の停止条件に事前登録した。
- **ユーザー手番の script は 3 度の must-fix を経て安全化した。** 原案は `mv` で tracked file を
  外へ出したまま復旧経路が無く、検査が表示のみで停止条件になっておらず、provenance preflight も
  欠けていた。最終形は `set -Eeuo pipefail` + trap で、失敗・中断のどの経路でも HEAD へ復元して
  HEAD/index/worktree の blob 一致まで確認し、冪等分岐と exact staged path 検査を持つ。
  実行ファイルであるため Codex `role=author` が書き、親は仕様と裁定だけを与えた。
- **受入全走と変異本走は実施していない。** floor 未再発行の tree では
  certified writer admission 系・floor 系・prediction seal 系が構造的に赤くなるためで、これらは
  `blocked/pre-floor` の期待赤であって回帰ではない。実施したのは編集面 4 file の実測
  (計算ノード、request 896505、22.21 秒、**333 passed**、非受入形) だけである。
  変異 spec の実 JSON も、`DW-M07` の anchor が再開時の tree と一致する保証がないため
  本走直前に作る裁定とし、設計 (5 件、うち 2 件は SURVIVED 期待) だけを凍結した。
- **worktree と branch を残した。** ユーザーが再発行 script をこの worktree で実行する必要があったため、
  背景 job の常例に反して畳まなかった。
- **ユーザーが floor protocol を再発行し (`8780332c`、`AI-Agent: none`)、wave はその後を続行した。**
  script は事前登録した全停止条件を通過し、bytes は親が独立検算した期待値と一致した。
- **再発行が既存の盲検封印との紐付けを壊すことが判明した (裁定時点で未見の新事実)。**
  `s8b_floor_campaign.py:1497` は「selector prediction を封印した時点の floor blob」と
  「現在の floor」の一致を campaign launch の条件にする。再発行で両者が食い違い、
  production が正しく launch を拒否した。**この E2E は再発行の前後どちらでも赤**であり
  (前は現行契約 g2 と protocol 契約 g1 の不一致、後は封印時 floor と現行 floor の不一致)、
  g2 世界と既存の固定封印は構造的に両立しない。段 3 レンズ A の A-6 が
  「新規 seal は g2 floor commit を基点にする」と予告していたが、親は帰結の重さを詰め切れていなかった。
- **ユーザー再裁定 (発話「推奨で」) で E2E を 2 lane へ分けた。** 歴史 lane は clone を封印 commit へ
  detach し、activation authority を genesis record だけの合成 head=1 へ差し替えて第 1 世代を現行にする
  (契約照合と launch gate が当時の状態で揃う)。現行 lane は launch が拒否されることを固定する。
  **検査を 1 つも失わずに**歴史の再現性と g2 の防壁を両立させた。
- **親が provenance trailer を 8 commit にわたり誤記した ({{F:provenance-model-after-model-switch}})。**
  セッション途中の `/model` 切替後も開始時 system prompt の slug を書き続けた。ユーザーの指摘で判明。
  裁定 (発話「推奨通りで」) は **B + C** — 既存 commit は rewrite せず訂正 commit と台帳で残し、
  以降は `model=unknown` を使う。forward correction 枠は消費済みで使えない。
  **形式として妥当な誤りのため checker では検出されない**点が同日の [T-139] (22 commit が
  `claude-opus-5[1m]` で形式違反 → 機械検出) と対照的である。
- **取り込んだ local main に既存の provenance 違反 22 件があった。** [T-139] R4 probe wave の commit 群で、
  既知違反リストにも未登録。本 wave の commit に違反はゼロで、履歴書き換えは禁止のため修正できない。
  事実として記録する。

## 次の一手差分

### 更新

- [T-657] **P1・実装完了**: pegasus 第 2 世代を活性化した。**ユーザーが floor protocol を対話 shell で
  再発行し (`8780332c`、`AI-Agent: none`)**、wave はその後を続行して pin 3 件を更新し、
  裁定 (1) の検証 CLI 明示も同段へ同梱した。裁定 (2) は見送りどおり実装しない。
  前提 (a) は実測により「テストの current 依存解消」へ縮小して完了 (production の silo は
  受理集合を変えないため scope 外に落とした)。再発行が既存の盲検封印との紐付けを壊す新事実が
  判明し、ユーザー再裁定で E2E を歴史 lane と現行 lane へ分けて解決した。
  base: 8c4fcd02e2dde1ac1d65fad0dd2edc2a469b073d68c919e110714b787c5b548e
- [T-660] **P3・実装済み・実測待ち**: production 層の末尾巻き戻し検査の検出力。head=2 になったため
  空 chain 拒否の mask が外れ、期待例外を head serial / state hash 不一致へ絞り、空 chain 拒否の
  理由を独立 node で固定した。**変異による検出力の実測は floor 再発行後の本走で行う**
  (設計は 5 件を凍結済み。うち serial 単独・state hash 単独は SURVIVED が正解で、
  対変異のみが実効 head pin の kill 証拠)。
  base: 6cde23c9936be6325596675ddadb7959e49c5e3002e69d5afb8f0c8dae0ec70b

### 新規

- {{T:provenance-model-switch-rule}} **P2・新規**: `AI-Agent:` trailer の `model` について、
  現行の共通則が覆えていない 2 つの契機を規約本体へ定める。(i) **セッション途中の `/model` 切替** —
  共通則は「確定できないなら `unknown`」と述べるだけで切替を名指ししないため親が 8 commit 踏み抜いた
  ({{F:provenance-model-after-model-switch}})。(ii) **実行面が許可文字集合外の slug を表示する場合** —
  `claude-opus-5[1m]` は `[a-z0-9][a-z0-9._-]*` に反するが、値は表示されており「確定できない」わけでは
  ないため `unknown` / `not-exposed` のどちらにも当てはまらない。main には変換した
  `claude-opus-5-1m` が 4 commit land 済みで checker を通る一方、変換しなかった 22 commit は
  形式違反になった。「表示名だけなら小文字化し空白を `-` に置換する」は**表示名**の規則であって
  model ID が文字集合外のときの規則ではない。値の真偽を機械照合する層は存在せず、形式が妥当な誤りは
  checker を素通りする。memory への記録は済んでいる。**本 wave では既成事実にしない。**
  なお [T-139] の 22 commit の処置自体は 2026-08-09 に別途裁定済み (known-violation 登録、
  逐語 `rulings-inbox/2026-08-09-t139-r4-probe-provenance-format-violation.md`) であり本項の対象外。
  親は当初これを未裁定として起票したが、当事者 wave からの指摘で訂正した。
