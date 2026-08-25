---
schema: izanagi-spool-v1
ledger: worklog
authored: 2026-08-26
wave: dev-wave-t360-mutation-transport-task
seq: 1
title: [T-360] 変異本走 transport と汎用コマンド送出を投入表の task として実装した。束ねは動くが attempt 証拠を持たない (コード + テスト + docs、branch worktree-dev-wave-t360-mutation-transport-task、変異 matrix = baseline PASSED・7/7 KILLED・SURVIVED 0・MISMATCH 0)
---

## 本文

- **親の段 1 前提が 2 つ覆った。** (1) 親も段 2 プランも、汎用 task の追加を明示的に決めた
  後発のユーザー裁定を見落としていた。段 3 レンズ B が発見した。「汎用 task を作らない」は
  親が選べる択ではなく、裁定済み方針を親が不採用にしない規律に従って実装側へ倒した。
  (2) 束ね単位を shard とする暫定は誤りで、正しくは wrapper 呼び出し 1 本である。
  稼働中 process の argv を実測したところ fan-out を走らせている process は 1 本も無く、
  実在するのは wrapper 経由 1 本と harness 直接起動 2 本だった。
- **親の裁定に内部矛盾があり、段 6 のレビューが検出した。** 裁定は「束ね文脈では attempt 対応の
  sidecar を許す」と書きながら、実装子への指示では「その制約を緩めるな」と明示していた。
  実装子は指示に忠実で、誤っていたのは裁定文である。結果として束ね経路は
  「attempt 証拠を残すと wrapper が停止し、落とすと証拠を失う」二択になり、
  **恒久 transport が要求する証拠契約を満たさない**。射程を {{D:mutation-bundled-path-scope}} で
  限定し、閉じる設計はユーザー裁定へ返した。
- **hook の変更は構造的に実装できなかった。** hooks subtree への書き込みは guard 自身が拒否し、
  例外は README だけである。codex 子も親も編集できない。正本が定める正規手順は
  「防護有効化前の commit から作り直す」で、本 wave の変更単位を超える。迂回せず裁定へ返した。
- **見送りの判断材料が実測でひっくり返った。** 実装子が書いた hook の**否定**テストまで赤に
  なったことで、現行 hook が `--task <任意> -- <重量コマンド>` を既に許していると判明した。
  この穴は本 wave 以前から在り、汎用 task が作ったものではない。未知 task を実際に止めているのは
  dispatcher の閉集合である。親が裁定文へ書いた「hook を広げる変更」は、実際には
  「既に広い hook をむしろ狭める」変更だった。認識が逆だったことを記録する。
- **敵対レビュー 2 本が正しさ防壁の所見を 2 件出し、いずれも実在した。** 1 件目は argv policy の
  迂回で、`-rf -qkselected` のような短 option cluster を検査が素通りし pytest が
  `-q -k selected` と解釈する経路である。変異走行が裁定した test 集合の部分集合で走ると
  KILLED / SURVIVED と台帳の集計値が変わる。2 件目は公開 CLI が呼び出し側申告の hash を受理し、
  受領証の束縛の意味が偽になる経路である。両方とも fix で閉じた。
- **live dogfood を必須にした判断が効いた。** 汎用 task は 3 回目で通った (1 回目は親の
  walltime 書式誤り、2 回目は runner の interpreter を相対名で渡したための構造検査拒否)。
  いずれも道具が正しく fail-closed しており実装欠陥ではない。**runner の interpreter は
  絶対パスで渡す必要がある** — 既存 harness と同じ要求だが、束ね経路では見落としやすい。
- **変異 matrix は 3 走目で確定した。** 1 走目は期待 node に parametrize 引数を書いておらず
  harness が起動前に停止し、変異は 1 件も走っていない。2 走目は期待 node を部分集合で登録した
  ため 3 件が MISMATCH になったが、いずれも「期待した node が落ちなかった」のではなく
  「期待より多く落ちた」ものだった (25 / 16 / 2 node)。観測した完全集合で再登録して 3 走目を
  走らせ、7/7 KILLED を得た。**検出力は登録より強かった。**
- 実測: 焦点走 8 file = 1686 passed / 5 skipped / rc 0。変異 matrix = baseline PASSED・
  7/7 KILLED・SURVIVED 0・MISMATCH 0。汎用 task の dogfood = bnode011 で実行・子 rc 7 が
  transport の infra rc に潰れず伝播・stdin 非 TTY・cwd が repo root。変異 task の dogfood =
  投入 1 回で baseline PASSED と変異 1 件 KILLED を完走 (従来経路なら 3 回)。
- main が競合 wave の land で進んだため前方取り込みを行った。auto-merge は競合ゼロだったが、
  検査器とその test は merge 結果が両親のどちらとも異なったため、契約に従い Codex author が
  合成を監査した。両側の意図が生きていることを file:line で確認し intact と判定した。

## 次の一手差分

### 完了

- [T-360] 投入表へ変異 task と汎用 task を足し、閉集合を 4 値へ広げた。束ねは 1 投入で
  完走するが attempt 対応証拠を持たない。射程と未充足は {{D:mutation-bundled-path-scope}}。
  remaining: none
  base: ab3c8ffa098d5311237b9bf7bb16fea8bf54582c65c1a3e9f3018227271d4003

### 新規

- {{T:bundled-attempt-evidence-marker}} **P1・ユーザー裁定待ち**: 束ね経路で attempt 対応の
  永続証拠を成立させるか。task 内部からだけ立つ marker を設け、compute site と marker の双方が
  真のときだけ local の attempt recorder を許す設計が候補だが、変異 harness の受理集合を変える。
  現状は「束ねて走るが証拠を持たない」状態で、恒久 transport の要件は未充足である。
- {{T:hook-gateway-spelling-dependence}} **P2・実装不能につき手順裁定待ち**: hook が
  dispatch gateway の内側 argv を綴りによって拒否したりしなかったりする。hooks subtree は
  guard 自身が編集を拒否するため、通常の wave では直せない。正本が定める
  「防護有効化前の commit から作り直す」手順を実行する専用の段取りが要る。
- {{T:mutation-lock-repo-wide}} **P2・新規**: 変異の共有 lock 移行は task 経路についてだけ
  閉じている。harness 直接起動は共有 lock を通らないため、repo 全体では未了である。
