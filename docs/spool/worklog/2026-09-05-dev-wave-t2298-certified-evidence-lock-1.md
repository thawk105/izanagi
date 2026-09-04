---
schema: izanagi-spool-v1
ledger: worklog
authored: 2026-09-05
wave: dev-wave-t2298-certified-evidence-lock
seq: 1
title: [T-2298] certified_evidence の lock を seed 排他・読み手共有・書き手排他へ分けた — 受入の律速を測り、D1593 の鎖 1 が現行 run に無いことと t080 の時間が git と複製であることを実測した (コード + insight、branch worktree-dev-wave-t2298-certified-evidence-lock、変異 13/13 KILLED + 等価 1 SURVIVED)
---

## 本文

- **ユーザー依頼:** 受入全走の最遅 shard (388.3 秒) を 5 分以内へ。(1) `certified_evidence` を seed 排他 →
  読み手共有 / 書き手排他へ (T-2298)、(2) shard-0 の 58% を占める t080 系の 145〜153 秒の内訳を先に測る (T-2273)、
  (3) T-2297 が fold 済みなら含める。段 1 で T-2297 は未 fold と確認し (1)(2) だけで進めた。
- **(1) は実装した。** 書き手は M17 / M18 の 2 本で別 fixture `certified_evidence_writer` を取る。17 consumer の assertion と
  node id は不変 (実装子と段 6 レビュー D が AST / hunk 単位で確認)。lock 意味論の正負例・実 fixture の mode 別保持・
  yield 位置と mode 転送の AST・atomic metadata の call edge と順序・writer 直接 path mutation の閉包 AST を足した
  (検査 10 本)。設計判断は {{D:certified-evidence-rw-lock}}。焦点走 (3 file) は計算ノードで 142 passed。
- **brief 前の実測で依頼の前提が 3 つ覆った。段 4 で再裁定した。** (a) 引数の `real_repo_fixture_lock` は git 資源用の
  別 lock で、流用は資源の取り違え (段 2 と段 3 レンズ A が独立に同結論)。(b) 「258.1 秒の直列」は台帳合計で、当日 junit の
  17 consumer 合計は 84.9 秒、M-A の setup 合計 ≈ 90 秒。待ちは重なるので合計は wall ではない。**T-2298 単独で 5 分に入れる
  量ではない** (21:16 走 411.9 秒から全部引いても 327 秒)。(c) D1593 の「鎖 1 = real-repo group 303.7 秒の 1 worker 直列」は
  現行 run に無い。`_strip_real_repo_loadgroup_suffix` (commit 5ac638955、08-26) が yield 後に suffix を剥がし、21:16 走の
  report.json で real-repo は 38 worker に散る。この commit は D1593 起草 wave の tested_tip の祖先。F832 の再発として記録。
- **(2) は 3 つの測定で答えた** (`output/insights/2026-09-04_t2298-t2273-shard0-critical-path/`)。M-B (t080 の phase 内訳、
  `-n 0`、2 回): build も直列性検査も走らない。base 構築 60〜77 秒 = 受領証発行の子 python 30 秒 + `git add -A` 7 秒 +
  git 可視 output の複製 ≈ 10 秒 + verify、`verify_receipt` 1 回 2.3〜11.7 秒。base は process 内 memo なので worker ごとに
  繰り返され、48 worker 同時では 2 倍超 (132〜155 秒) になる。M-A (全 suite 非 shard、bnode095): wall 487 = collection 119 +
  test 361 + 7、48 worker 完全均衡、report に無い待ちは 0。M-C (shard-0 の 111 file、bnode080): wall 250 = 56 + 190 + 5、
  隠れ待ち 0。同じ file 集合の受入 shard-0 は 251〜412 秒で、差は受入 plugin 側 (全 node collection と deselect、LPT 並べ替え、
  report 生成) と host の混合。**shard-0 の超過 95〜207 秒の内訳は、report.json に session timeline が無い限り確定できない。**
- **T-2297 (D1618) の状態は「runtime 効果は既に在る、明示契約は未了」。** ItemRecord の affinity 属性、payload / parser、
  component と closure gate、`test_g6_*` の期待値が未実装。「実装済み」とは書かない。D1618 の前提 (鎖 1) が現物と食い違う
  ため、scope の再裁定をユーザーへ返す ({{T:t2297-rescope-after-chain1-refutation}})。
- **段 3 (2 レンズ) と段 6 (2 レンズ + 焦点再レビュー 1) の must-fix は 6 件、すべて検査側。** lens A: 実 fixture の lock
  保持配線が未検査、seed 完了印が非 transactional。lens C / D (独立に同一): 実 scope 検査が両 mode に `LOCK_EX|LOCK_NB` を当て
  mode 定数化が緑で通る。lens C: atomic 検査が production seed の call edge を固定していない。lens E: 直接公開の検出が path
  構文依存、fsync の順序未検査。fix 2 巡で閉じ、以後は変異 (h, i, j) で裏取りした。lens B は親の一般化を 5 点訂正した
  (鎖 1 反証の射程、wall 表現、効果の限定、T-2297 の状態、shard-0 因果の格下げ)。
- **変異:** probe (全件 SURVIVED 期待、対象 file 全体) で負例 13 件すべてに赤 node を観測、等価 1 件 SURVIVED。b / e / f では
  並走する reader consumer も赤 (lock が競合を防いでいる実例、競走依存)。本走 (KILLED 期待、`-k certified_evidence`、
  HEAD b47cf3975) は **13/13 KILLED、等価 1 SURVIVED、14/14 期待一致、baseline PASSED**。
- **受入 (段 6、実装 tip + main の merge 7b585a1f1、canonical、K=3):** child-green、20488 passed / 68 skipped。最遅 shard
  303.4 秒 (bnode035)、p3_b4 を載せた shard-2 は 204.5 秒。同時刻の別 wave (旧 lock) は 331.9 / 223.4 秒、17 consumer の
  junit 合計は 346 → 290 秒。host が違い統制比較ではない。**5 分以内は未達。** land 用の最終受入は記録 commit 後に再走する。
- **計測汚染 1 件 + near miss 1 件 (親の手順):** 実装子が編集中の worktree から M-C を dispatch し、m18 の赤 1 件と同 file の
  所要が HEAD のものでなくなった。焦点走の local 試行中に `git add` して digest を変え rc=16。
  {{F:measure-dispatch-during-author-edit}}。
- 実装子・レビュー子はいずれも sandbox で pytest を起動できず「実装済み・未実走」と申告した。実走はすべて親。
  Codex: plan 1 (9 calls)、consult 2 (12 calls / accepted)、author 1 (22 calls)、review 3、fix 2。

## 次の一手差分

### 完了

- [T-2298] `certified_evidence` の lock を seed 排他・読み手共有・書き手排他へ分け、正負例と閉包を検査した。
  remaining: none
  base: 6ea27bbb1d1cfa6aed72252ac1d99681b90eb281bf30a685186a7bce25490baf

### 更新

- [T-2273] **P1・測定済み → 次の手番は測定面の拡張と t080 base の共有可否**: t080 stub-free e2e (132〜155 秒/node) の時間は
  build でも直列性検査でもなく、受領証発行の子 python 30 秒 + `git add -A` 7 秒 + output 複製 ≈ 10 秒 + verify 2〜12 秒の
  base 構築 (60〜77 秒) が xdist worker ごとに繰り返されるもの。shard-0 の wall − 最大占有 95〜207 秒は非受入形の再現走
  (M-A / M-C) では出ず、受入形固有 (collection / deselect / LPT / report) と host の混合。report.json に session timeline が
  無いと内訳を確定できない ({{T:acceptance-session-timeline}})。[T-1933] が cache 共有と grouping で 2 度失敗した base の
  共有は、M-B の内訳を持って再検討する余地がある (子 python 30 秒は同一 base で毎回同じ受領証を発行する)。
  base: 52022c1f1fec594c7c2eebc57e0ee2bd6f77399137deeeca15d21a89258c4e01
- [T-2297] **P1・裁定済み (D1618) → 前提の再裁定待ち**: 承認の前提「read-only 92 node が group marker で互いを待つ」は現行
  run に無い (suffix strip、08-26)。runtime 効果 (shard affinity 保持 + worker 分散 + RW lock) は既に在り、未了は D1618 の
  明示契約 (ItemRecord affinity、payload / parser、component / closure gate、g6 期待値)。scope の再裁定は
  {{T:t2297-rescope-after-chain1-refutation}}。
  base: 2bd9c88f6ccbafee204e1ccc8195042d20b14482fdcae01196823472f575ba8a

### 新規

- {{T:t2297-rescope-after-chain1-refutation}} **P1・ユーザー裁定待ち**: D1618 (T-2297) の前提 D1593 鎖 1 は現行 run に無い
  (本エントリ)。選択肢: (a) D1618 の明示契約 (affinity 属性・gate・g6) だけを実装する、(b) runtime 効果で足りるとして
  T-2297 を「現物で充足」と閉じ D1593 / D1618 へ追記で訂正する、(c) 現状維持。推奨 (b): 効果は在り、契約の明示化は
  受入 wall を動かさない。
- {{T:acceptance-session-timeline}} **P2・ユーザー裁定待ち**: 受入 shard の report.json に session timeline (collection 終了、
  各 worker の最初/最後の test 時刻、`pytest_runtest_protocol` wrapper の lock 取得/解放時刻) を足すか。D1620 の面 (最遅 shard
  wall) を内訳へ分解する唯一の手段で、本 wave の M-A / M-C は非受入形の代用にすぎない。新規 field なので裁定が要る。
- {{T:m18-shared-mutation-outside-try}} **P3・新規**: M18 (`test_m18_symlinked_evidence_is_rejected_with_regular_control`) の
  最初の共有変異 (`role_file.rename` 後の `symlink_to`) が `try` の外にあり、失敗すると復元されない。assertion は変えずに
  `try` へ入れる小修正 (段 6 レンズ C の nit)。
