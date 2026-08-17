---
schema: izanagi-spool-v1
ledger: worklog
authored: 2026-08-17
wave: dev-wave-t782-approval-sha-binding
seq: 1
title: 承認 pin は縮小対象でなく admission gate だと確定した — 敵対検証が親の 4 命題を全件反証し、親の当初推奨 (pin ごと hold 化) は受理集合を空から任意 schema-valid spec へ広げる規律 2 違反だった (insights + docs、branch worktree-dev-wave-t782-approval-sha-binding)
---

## 本文

依頼は 3 段構えだった。(i) 起票時 3 前提の生存を実測、(ii) 生きているものについて
reviewed spec の bytes を起草して canonical path と production 生成経路を用意、
(iii) 承認値の確定時に SHA を機械的代行で記入できる形まで配線。
**(i) を実行した結果 (ii)(iii) を実行していない。** `APPROVED_SPEC_SHA256` は `None` のまま、
oracle spec の canonical directory へは 0 byte。fail-closed は 1 件も緩めていない。
設計判断は {{D:approval-pin-is-an-admission-gate}}、裁定パッケージは
`output/insights/2026-08-17_t782-approval-sha-binding/package.md`。

**起票時 3 前提はすべて生存していた。** 研究設計値 (`n` / `master_seed` / block ID /
`campaign_ids`) は未確定、canonical path の実ファイルは不在で production の producer は 0 件、
D302 の schema 据え置きを守る tripwire test は現在緑で 1 file 置けば赤になる。

**依頼が併せて求めた衝突判定の答えは「部分的に衝突している」。束縛は 1 つでなく 2 つあり、
性質が正反対だった。** 承認 pin は D320 が「対象外 (不変)」と名指す admission gate に当たり、
縮小してはならない。`generator_versions` の live bytes 照合は D302 自身が
「defense-in-depth であり新規の受理集合縮小としては主張しない」と宣言している層で、
緩めても受理集合が広がらないため縮小候補として成立する。

**段 3 の敵対検証が親の 4 命題を全件反証し、親は 8 所見すべてを一次資料で裏取りして採用した。
当初推奨は撤回した。** 最も重いのは受理集合の向きの誤りである。親は「D302 の内容再導出が
残るので pin を hold にしても門は弱まらない」と論じていたが、**内容再導出は残っても
再導出の元が未承認のファイルになる**。pin が `None` の今 official manifest を作れる spec の
集合は空であり、hold 化するとそれが「canonical path の schema を満たす任意の spec」へ広がる。
`n`・`master_seed`・`block_sizes`・run contract の `reps` / `extime` などは schema の範囲で
自由なので、**未承認の研究設計を official 経路へ入れられる**。D356 が
「欠けているのは内容束縛ではなく承認者の同一性である」と書いているとおり、
親は内容束縛と承認者同一性を混同していた。

**事実誤りも 3 件訂正された。** (1) canonical path へ書く関数は「test fixture 3 個」ではなく
test 側 5 箇所。(2) 「`load_approved_spec` を呼ぶ経路すべてで凍結読込が先に落ちる」は偽で、
floor / budget がともに `null` な今日は gate 経路が v1 verifier の枝へ入り凍結読込を経由せず
承認 pin を直接踏む。判定が動かない結論は残るが、refusal 一覧は 1 項目変わる。
(3) pin 対象 5 source の変更は「28 commit」ではなく重複を除くと 22 commit
(file 別 touch 17/6/3/0/2 の単純合計を二重計上していた)。

**承認の trust root は新しい状態変化ではなかった。** 親は「外部 trust root を作らない裁定に
より恒久的に不在化した」を本 wave の新事実として出したが、その裁定は 2026-08-13 の時点で
既に引用されており、blocker ではなく宣言済みの保証限界である。ただし [T-987] package §2 が
これを「裁定待ち」と書き「決定が付くまで承認 branch は有効化できない」と結論している点は
事実と異なり、現用文書の訂正対象として記録した。

**見落としていた blocker が 1 群ある。** judge の集約規則が未凍結、spec 層が単一 block 契約を
検査しない、env 契約の `contract_sha256` が activation 世代の進行で失効する、
`binding_identity` が active 批准凍結なしに導出不能 — の 4 件。
**active freeze が発効してもこの 4 件が残る限り approved spec を安全に確定できない。**

**実装差分ゼロの wave でも敵対検証を省いてはならない実例になった。** 親単独の結論は
規律 2 違反の方向へ倒れており、それを止めたのは段 3 の 1 本だけである。
自己改善候補として `DW-C00` の「docs-only は子ゼロでよい」が先行する該当条件に従属することの
明示を挙げたが、**敵対検証子を省ける条件は正しさ防壁と裁定境界に当たるため実装せず、
裁定パッケージ §10 へ送った。**

## 次の一手差分

### 更新

- [T-782] **P2・ユーザー裁定待ち (優先度を P1 から下げた)**: 縮小の可否を問うのは
  `generator_versions` の live bytes 照合だけで、承認 pin 自体は admission gate として
  不変扱いに確定した ({{D:approval-pin-is-an-admission-gate}})。
  選択肢と親推奨 ((b) 据え置き、durable 発行の可否と同時裁定) は
  `output/insights/2026-08-17_t782-approval-sha-binding/package.md` §5。
  **今日この項は 1 件の判定も律速していない** — 床値と予算が未実測なので gate は必ず拒否へ倒れる。
  再訪条件 = durable な reviewed spec を発行するかどうかを決める段
  (active ratified freeze の発効と package §6 の 4 blocker 解消が前提)。
  base: 52036874394031175aec7de39a7ccd3d5ff9a837a218e7806f1eddc8ad6e0f15
