---
schema: izanagi-spool-v1
ledger: worklog
authored: 2026-09-03
wave: dev-wave-t2141-rejection-durability
seq: 1
title: [T-2141] raw 試行記録 producer の rejection を耐久化した — 相乗り 5 経路は全て不可で、非保証は落とさず 2 つに割って狭めた (コード + テスト + insight、branch worktree-dev-wave-t2141-rejection-durability、変異 10/10 KILLED)
---

## 本文

- **ユーザー指示の「既存の記録経路に相乗りできるかをまず測る」を段 2 で実行し、5 経路すべて
  不可と判定した。** 判定は性質でなく file:line で行った。とくに成功 attempt leaf への union は
  `PLANNED_PATH_CONFLICT` と leaf 自身の IO error という**最も重要な棄却理由ほど記録できない**。
  足したのは publication root 直下の固定名 leaf 1 種だけで、母数と attempt mapping は既存の
  issuer receipt を再利用した。
- **起動時の重複検査で、ユーザーが指定した待機条件は不成立と判定した。** T-2103 は
  「裁定済み (D1345) → 比較実験待ち」で wave の worktree も branch も存在しない。T-2102 は
  worklog 1219 で着地済み。全 59 worktree を branch 差分 + 未 commit まで走査し、`p3_b4_*` を
  触る稼働 wave は 0 件だった。
- **段 4 直前の裁定再走査で、wave 開始後に入った D1533 と D1529 を取り込んだ。この 2 件が
  hash chain の是非を決めた。** 段 2 プランは chain を置いていたが、段 3 の両レンズが独立に
  「chain head を pin しないので末尾の完全切断と file 削除を検出できない」と指摘した。
  D1533 は「防いでいない範囲を成果物へ明記する」「実経路が示されていない段階では bytes 級
  provenance は見送り側」と定めており、**機構の追加ではなく範囲の明記で閉じよ**という裁定である。
  詳細は {{D:rejection-ledger-scope}}。
- **「全 rejection の耐久化」は達成不能だった。** publication の検証そのものが失敗したときは
  書き込む信頼できる root が確定しない。保証を「検証に成功した後の producer rejection」へ
  明示的に狭めた。
- **段 6 の敵対レビューが「抜いても全テストが緑」の実装を複数暴いた。** `flock`、台帳の
  `O_NOFOLLOW`、`fsync`、batch の記録行 2 本、event の schema 値がそれである。
- **機構の正例が実体を名指していなかった。** 「台帳が invalid でも正常な assembly は成功し
  続ける」の正例が、両側とも `INCOMPLETE_SET` で落ちる入力を使っており一度も機構を通って
  いなかった。fix で既存の certified 201-block 正例を再利用して作り直し、本走で N08 が
  この node を落としたことで機構を通ったと確認できた。
- **N01〜N09 は probe の観測 node をそのまま本登録し、N10 だけ probe を取れなかったため親の
  予測 node で登録した。本走で一致した。** 外れた場合は erratum + 再登録の経路を使う予定で、
  予測を後から書き換えて辻褄を合わせてはいない。
- **変異 probe の 2 回目は session 終了に巻き込まれて途中で死に、作業ツリーに N10 の変異が
  残った。** 待ち手の通知ではなく `git status` と `pgrep` で生死を判定したため検出でき、
  `git checkout --` で復元した。
- **計算ノードの混雑が変異走の律速だった。** queue 待ちは 66 分〜4 時間半。変異 harness は
  login node での local モードを禁止しているため dispatch しか選べない。D612 の queue-wait
  上書きは単独で `run_tests.py` を叩けば効く (60 秒設定で 63 秒に切れる正例対照を取った) が、
  harness 経由では 3600 秒設定でも 904 秒で切れた。**食い違いの原因は特定していない。**
  5400 秒設定の本走は完走した。
- 実装子と fix 子はいずれも codex sandbox の制約で pytest を開始できず、正しく
  「実装済み・未実走」と申告した。実測はすべて親が行った。
- **親 prompt の誤りを 1 件記録する。** 段 5 実装子の prompt に書いた作業ツリー path が親側で、
  投入先の author worktree と違っていた。子が自分で検出して正しい側へ書いたため実害は無いが、
  `DW-O02` の現行版は「prompt の repo path は投入先 worktree のもの」と明記している。
  F819 の同型再発として追記した。F810 (submodule 初期化の 1 回目失敗) も 2 回踏んだ。
  回数は固定ではなく、fix2 の worktree では 2 回連続で落ちて 3 回目で成功した。
- **段 8 で 1 件が byte 予算に阻まれた。** 変異走の中断後に作業木を検査する義務を
  `docs/dev-wave/mutation.md` の DW-M05 へ収容しようとしたが、`docs/dev-wave/**` の L1.5 予算
  9696 bytes に対して 228 bytes 足りなかった。D730/D782 の手順で既存記述の削減を 2 箇所試し、
  それでも足りず、独立 3 例に達しないため例外収容もせず、**上限は引き上げなかった。**
  恒久対応は memory へ置き、その経緯を failures へ書いた。

## 次の一手差分

### 完了

- [T-2141] raw 試行記録 producer の rejection を耐久化した。publication root 直下の
  `raw-record-rejections.jsonl` 1 種を足し、材料レポートが棄却 event・母数 3 種・
  未解決 absent・但し書き付きの件数と率を出すようにした。閉じていない範囲は成果物へ明記した。
  remaining: none
  base: 23f25bc4f45d24944cd0606333c27494019b5c6581a10badd900381bf39f29a6

### 新規

- {{T:rejection-ledger-concurrent-append}} **P3・新規**: rejection 台帳の並行追記を検査する。
  現状 `flock` は単一 process のテストでは殺せず、diagnostic 扱いで kill に数えていない。
  producer を並行に走らせる実経路が生じたときに起票を昇格させる。
- {{T:mutation-harness-dispatch-override}} **P2・新規**: 変異 harness 経由の走行で D612 の
  queue-wait 上書きが効かない食い違いを特定する。単独で `run_tests.py` を叩けば効く
  (60 秒設定で 63 秒、正例対照を実測) が、harness 経由では 3600 秒設定でも 904 秒で切れた。
  harness は `IZANAGI_DISPATCH_*` を設定も除去もしていない。
