---
schema: izanagi-spool-v1
ledger: worklog
authored: 2026-09-10
wave: dev-wave-t2448-b5-executor
seq: 1
title: [T-2448] 軸 B5 の leaf 実行器と 2 つの preflight を作り、registration preflight を親が実データで通した — 実行器は軸全体の完走を返さず、未登録の運用値では本走 request を 1 本も出せない (コード + テスト + 台帳 + insight、branch worktree-dev-wave-t2448-b5-executor、変異 12/12 KILLED・期待 node 完全一致、受入 child-green 22413 passed)
---

## 本文

- **成果物の名乗りを段 4 で狭めた。** 段 3 の敵対検証 2 本が独立に「この範囲を『軸 B5 の実行器』と
  名乗るのは不可」と指摘した。scope は広げず、代わりに実装の公開面で担保した — 実行器は
  `完走` / `RW3` / 軸の成熟度を返す API を持たず、control の「発火」も返さない。
  registration seal は `seal_scope` に暫定であることと除外層を機械可読に書く。判断は {{D:b5-executor-scope-is-leaf-only}}。
- **凍結文が沈黙している運用値を、沈黙のまま可視化する形にした** ({{D:b5-unregistered-run-policy-fails-closed}})。
  期待 content type・timeout・User-Agent・request 間隔・retry 対象・redirect は事前登録が定めていない。
  実装子の便宜値で埋めると凍結後に実装者が選んだ実行契約になるので、本走 request の発行を
  fail-closed にして未登録 6 項目を列挙して返す。**走行の認可の前に、この 6 値をユーザーが決める必要がある。**
- 索引の 3 値に入らない応答を丸めない ({{D:b5-lookup-unclassified-not-rounded}})、
  登録に無い阻止条件を実行器へ足さない ({{D:b5-no-unregistered-blocking-gate}}) も同じ段で裁定した。
  後者は段 2 プランの推奨 (work ID の drift で走行を阻止する) を退けたものである。
- **親が registration preflight を実 repo で 1 回通したことが、本物の欠陥を 1 件出した。**
  directory の exact set 検査が `.gitignore` の `__pycache__/*.pyc` を余分な path と数え、
  一度でも import した環境では gate が構造的に通らなかった。実装子の test は合成 tree だったので緑だった。
- **変異走行を 2 回まわしたことが、もう 1 件出した。** 本走 1 回目の MISMATCH の原因は、
  上の欠陥の正例 test が実 repo の共有 tree へ `.pyc` を書いて消す作りで、xdist の別 worker が
  同じ実 repo を読む test を巻き込んでいたこと。赤 node 集合が走行ごとに変わり、受入でも
  ランダムに赤を出す形だった。どちらも合成 fixture が実際の形を通していない同型で、F899 の再発として記録した。
- **段 6 の指摘の修正方向を、親が正本で確かめてから決めた。** レビューは「正常な OpenAlex 応答が
  条件 1 で落ちる」と指摘したが、条件 1 の OpenAlex 節の登録構造を確認すると**実装の builder が正しく、
  誤っていたのは合成 fixture の側**だった。指示を誤れば正しいコードを壊すところだった。
- **段 1 brief の誤りを段 4 で訂正した。** 「DBLP 13 member は不達」と実測のように書いたが、
  閉包記録は anchor 固有 request を 1 本も送っておらず、不達は共有 endpoint の probe からの外挿である。
  13 member の個別値は未観測なので、live preflight で実際に出すことには情報価値がある。
- 受入の post-claim merge が受入所要台帳の競合で止まった。merge 内で両親と異なる台帳を書かないよう
  競合解決では main 側を採り、落ちた 54 行は merge 後に Codex 子が正本 producer で入れ直した。
- 焦点走で 1 件赤が出たが、**焦点走の選択範囲による偽赤**だった。main tip に本 wave の変更を
  一切含まない木で同じ test を単独で走らせても落ち、受入全走では緑。本 wave に帰属しない。
- 段 8 の自己改善候補は 1 件。`DW-C01` の「隔離 worktree の detach は launcher の `.sh` へ外出し」は、
  launcher を作っても親が `nohup setsid bash <launcher>` を直に叩くと guard に拒否されるため、
  実際には detach 用の 2 枚目の `.sh` が要る。

## 次の一手差分

### 更新

- [T-2448] **P2・ユーザー認可待ち**: 軸 B5 の leaf 実行器 (parser・fixture・schema・runner) と
  registration preflight・live preflight は実装を終え、registration preflight は親が実データで
  通した (38 file を seal)。**残るのは live preflight の実施だけで、これは人間の実行認可を要する。**
  実施すると 3 索引 30 member の ID lookup の 3 値がその時点の実行記録に入る。
  DBLP 13 member の個別値は今も未観測である (閉包記録の `不達` は共有 endpoint の probe からの外挿)。
  本走の 6 運用値は {{T:b5-run-policy-ruling}} が先に要る。
  base: 2637ed8028965f4ee3b2e69246e210ce09a6a001f0c190a65300a5d68513e07f

### 新規

- {{T:b5-run-policy-ruling}} **P1・ユーザー裁定待ち**: 軸 B5 の本走に必要な未登録 6 運用値
  (期待 content type の exact 集合・timeout・User-Agent・request 間隔・retry 対象の失敗集合・
  redirect の扱い) を決める。実行器はそれまで本走 request を 1 本も発行できない。
  決めた値は後継凍結物へ登録し、実行器の定数として seal し直す。
- {{T:b5-axis-aggregator}} **P2・新規**: 軸 B5 の完走述語 (部分登録 §5.2 の論理積) を評価する軸集約器と、
  登録全体を索引順・query ID 辞書順で走らせる production 入口を作る。現行の実行器は leaf に閉じている。
- {{T:b5-checkpoint-resume}} **P2・新規**: 軸 B5 の checkpoint / resume と、複数窓にまたがる枝の
  独立 2 走 digest 一致を実装する。**入れると runner の bytes が変わるので registration seal を取り直す。**
- {{T:b5-control-and-aux-streams}} **P3・新規**: 演算子 control (§4.1) の集合関係と anchor 包含 control (§4.3) の
  評価、および anchor に依存する補助 61 stream を後継凍結物へ登録して実行できるようにする。
