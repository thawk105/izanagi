# [T-2293] 8c 結線の実装 wave — R1・R3・R4 の契約側

2026-09-07。branch `worktree-dev-wave-t2293-8c-wiring-r1r4`。base main `cf4273f56`。

- 依頼: D1667 (R1)・D1668 (R2)・D1669 (R3)・D1670 (R4) を、
  `docs/phase3-8c-wiring-design.md` §J の受入要件 9〜18 として結線する。
- 逐語: `s1-brief.md`、`s4-adjudication.md` (末尾に段 6 の追記 2 節)、`verbatim/` 配下 15 本。
- 変異: `mutation-spec.json` / `mutation-ledger-round1.json` (probe)、
  `mutation-spec-round2.json` / `mutation-ledger.json` (本走)。

## 1. 名乗らないこと

本 wave が閉じたのは **「8c の物理束縛契約」**だけである。次は名乗らない。

- 「8c 結線完了」「発行 3 条件を満たした」「P6 が発火する」「本番で物理実行を保証する」。
- **発行 3 条件は 0/3、本番 authority は 0 件のまま変わらない。**
  本 wave は結線を実装するだけで、本番で発火する経路は 1 本も生まれない。
- 「trusted harness を認証する」「execution receipt の実在を確認する」。
  実行後に計算どおりの canonical root へ整合した錠前と WAL を後置した入力は拒否できない。
  D1674 が明記した trusted-writer 運用前提の外側であり、この限界は狭めていない。
- 「lifecycle loader が起点束縛の必要十分条件を強制する」。loader は自分が見えるものだけを
  検査する。手で書いた start 行の起点主張が本物かは判定できない。
  最終 acceptance が拒否するので certified 選択の値には到達しない。

## 2. 実装した範囲と、しなかった範囲

| 受入要件 | 本 wave | 根拠 |
|---|---|---|
| 9 (33 identity の決定的導出と相異検査) | 実装 | 依存する未存在層が無い |
| 10 (registry / capability は論理 identity だけを受ける) | 実装 | 同上 |
| 11 (envelope を予約後・observation 前に create-only) | 実装 | §C の順序欠陥を直す |
| 13 (provenance の `campaign_run_identity` 必須 key) | 実装 | R3 そのもの |
| 14 (錠前から物理 identity を再導出) | 実装 | §4 の解法で carrier 問題を解消 |
| 15 (envelope を disk から再読) | 実装 | R1 の束縛先が本 wave で生まれる |
| 16 (FC05a の attempt id 相異) | **実装済みだった** | `reflux_formal_consumer.py:768-780`。差分 0 |
| 17 (native WAL shape) | 一部実装 | decoder は既に実在。足したのは混在拒否だけ |
| 12 (sealed executor) | **実装しない** | 物理 evidence producer が無く、実行結果が届かない |
| 18 (origin report の campaign_runs) | **実装しない** | producer 側 finalizer が単一 root を要求する |
| R2 (起点専用 completion) | **実装しない** | 要件 18 に依存する |

## 3. 段 3 の敵対レンズが独立に一致した点

両レンズとも判定は「作り直し」。根本原因も一致した。

- R2 と受入要件 12・18 は、親 brief 自身が scope 外と宣言した層
  (ledger producer FSM、物理 evidence writer、witness normalizer、材料レポート renderer =
  設計文書 §9 の未存在層) を必要とする。
- 発火する producer を持たない gate を足すのは、ユーザーが明示した
  「仮想リスク向けの gate・検査の追加は scope 外」に反する。

段 6 のレビュー 2 本も、**独立に同じ must-fix を 1 件挙げた** — lifecycle loader が
`origin_terminal_projection` の有無を `origin_binding` の代理にしており、受理集合が広い。

## 4. 親が refuted と裁定した点 — 錠前の場所は計算で導く

段 2 プランと段 3 の両レンズは「受入要件 14 は `result-evidence` に 3 本目の
content-addressed ref が要り、R1〜R4 の裁定範囲外だから実装不能」と結論した。

実測: `exploration_campaign_layout(campaign_id, output_root)` は
`<root>/exploration/campaigns/<cid>` を決定的に返す (`orchestrator/campaign/layout.py:589-597`)。
formal consumer は `run_plan.members[q].planned_campaign_run_identity` を既に受け取っている。

したがって受け手は canonical root を**計算**して錠前を読める。**呼び手に場所を申告させないので、
content-addressed ref 案より受理集合が狭い** — 「plan identity と整合する錠前と WAL を、
計算どおりでない directory に後置した入力」も拒否できる。schema の bytes も受理集合も変えない。

## 5. 親が自分の裁定を訂正した点

段 4 で「lifecycle loader でも必要十分条件を強制せよ」と裁定したが、段 6 で**実装不能**と判明した。
loader は台帳の bytes だけを受け取り、start 行が持つのは `launch_admission_sha256` (digest) で
あって record 本体ではない。digest からは `origin_binding` の有無を判定できない。

実装子はこれを、start 行へ launch admission の record 全体を埋め込むことで解こうとした。
**D1667 が認めたのは optional key 1 本であって record 全体ではない**ので却下・revert した。
必要十分条件は情報が実在する層 (書き手・終端・受入) で強制する。

## 6. 本 wave が入れた退行 (同じ wave 内で修正)

受入要件 11 の順序是正で lifecycle start が observation 開始より前へ移った結果、
observation 開始後の失敗が terminal を書けなくなった。台帳に「開始だけあって終端がない」行が残り、
再試行を阻止しながら acceptance も成立しない。

失敗 status (`indeterminate` / `partial`) かつ非空の `failure_reason` を持つときに限り
projection 無しの終端を許す形で直した。**`complete` は従来どおり projection を必須とし、
成功側の関門は 1 つも外していない。**

## 7. 受理集合の変化 (D1721 に従い「拡張」と記録)

「緩めていない」とは書かない。

1. lifecycle `start` 行: base 15 key の 1 択から、base と base + `origin_run_plan_sha256` の
   2 択への**制御された拡張**。`origin_binding` の有無との対応で拡張分を限定する。
2. `execution-provenance`: v2 世代の**追加**。起点 consumer の受理は v2 だけへ**縮小**する。
3. lifecycle `terminal`: 起点試行が projection 無しで終端できる場合の**追加**。
   失敗 status かつ非空 `failure_reason` のときに限る。成功終端の受理集合は不変。

受入要件 14・15・17 の変更は受理集合を**縮小**する側であり、拡張しない。
originless 経路の bytes と受理集合は不変。

## 8. 検査

- 焦点走 (計算ノード実走): **637 passed / 0 failed** (158 秒、request 981659.nqsv)。
  段 5 統合直後は 625 passed / 4 failed で、4 件はすべて呼び手の未結線という単一原因だった。
  1 回目の投入は `queue-wait-timeout` で rc=16 (子は 1 度も起動せず、変更に帰属しない)。
  D612 の上書き (queue 3600 / grace 600) で再投入した。
- 変異 probe 第 1 巡 (repo_head `0977e8432`): baseline PASSED、KILLED 4 / MISMATCH 5 / SURVIVED 1。
  MISMATCH は赤にはなったが観測 node 集合が登録より広い型。DW-M08 は完全一致だけを KILLED とする。
- 変異本走 第 2 巡 (repo_head `baaabd026`): **baseline PASSED、9/9 KILLED、
  SURVIVED 0 / MISMATCH 0。**
- probe で SURVIVED した 1 件は**等価変異**と確定した。producer が `campaign_output_root` へ
  `run_root` そのものを 1 箇所で代入している (`p3_autonomous_workload_trial.py:4837`) ため
  2 式は同値で、どのテストも区別できない。段 6 の fix が root の分裂を構造的に閉じた結果である。
  **ただしこの性質はテストではなく単一代入によって保たれている。**
- mu3 は観測 node が 52 件に及び、単一理由性の証拠としては弱い (DW-M03 に従い明記)。

## 9. 変異の除外 (D1723)

段 2 プランの 18 候補から、他層が先に同じ入力を拒否する 4 件を外した。

- 受入要件 9 の query ordinal 固定 0 — `reflux_origin_topology.py:368-370` の既存相異検査が先に拒否する。
- 受入要件 10 の issuer へ物理 cfg を渡す変異 — `reflux_origin_binding.py:559-562` が
  registry campaign ID 不一致で先に拒否する。
- 受入要件 12・18 に属する 2 件 — 本 wave で実装しないため対象外。

## 10. 段 6 レビューの偽装入力判定 (レンズ B、実測)

consumer を直接通した場合の判定。結線経路では呼び手の未結線を直すまで到達しなかった。

| 入力 | 判定 |
|---|---|
| q10/q11 の root・config 交換 | 拒否 |
| 別 path・別 object の envelope | 拒否 |
| 別 trial の 33 WAL 流用 | foreign root は拒否。canonical root への整合コピーは拒否できない |
| 過去 attempt の WAL 流用 | 拒否 |
| **実行後に canonical root へ整合した錠前と WAL を後置** | **拒否できない (期待どおり)** |
| `build_attempt_id` の 1 件重複 | 拒否 |
| originless start に digest を追加 | 書き手と最終 acceptance は拒否。loader 単体は拒否できない |
| origin start から digest を削除 | 同上 |
| `execution-provenance/v1` を起点 consumer へ | 拒否 |
| native/legacy shape の混在 | 拒否 |

## 11. 裁定パッケージ (ユーザーへ返す)

**Q. 8c の物理実行の producer 層 (ledger producer FSM、物理 evidence writer、
witness normalizer、材料レポート renderer) を作るか。**

- 作らない限り、受入要件 12・18 と R2 は実装しても発火する producer を持たない。
- 作る場合、設計文書 §9 が「未存在」と書いた 4 層の設計 wave が先に要る。
- 現状は発行 3 条件 0/3、本番 authority 0 件なので、作らなくても certified 選択・
  材料レポート・試行台帳の現在値は 1 つも変わらない。

親の推奨: **本 wave の契約を land してから、producer 層の設計 wave を 1 本立てる。**
R2 と受入要件 12・18 はその後の実装 wave で閉じる。
