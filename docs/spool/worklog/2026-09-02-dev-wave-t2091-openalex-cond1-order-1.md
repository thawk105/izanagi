---
schema: izanagi-spool-v1
ledger: worklog
authored: 2026-09-02
wave: dev-wave-t2091-openalex-cond1-order
seq: 1
title: [T-2091] OpenAlex の完走条件 1 を順序非依存の比較へ改め、新 epoch AX1-20260902-E1 を発行する (コード + 凍結契約、branch worktree-dev-wave-t2091-openalex-cond1-order)
---

## 本文

- **裁定の実装である。** D1432 が「OpenAlex の条件 1 を `oqo` の順序非依存な比較へ改める。
  新しい amendment・新しい epoch・新しい query ID を発行する」と裁定していた。
- **全枝の再実行は本 wave の選択ではなく、改訂される契約自身が要求している。**
  旧 amendment §8 は「非意味的修繕 = 正規化 request が同一である変更だけ」と定義し、その構成要素に
  完走述語を含めない。完走述語の変更は意味的 amendment であり、§8 が新 epoch・新 query ID・
  **全枝の再実行**・独立レビューを要求する。親は当初これを旧 §3.1 の先例から導いていたが、
  段 3 の指摘で根拠を §8 と D1207 へ訂正した。
- **段 3 が実測付きで規律 2 の穴を 1 件出した。** 素朴な JSON 読み取りは同一 object 内の重複 key を
  後勝ちで潰すため、`{"join":"xor","join":"or",...}` が `{"join":"or",...}` として読まれる。
  これを放置すると、契約に書いた「未知 join は両側同形でも不一致」という fail-closed 条項が
  生応答経由で迂回され、**謳うだけで発火しない保証**になる。live と offline の両抽出経路で
  重複メンバを拒否して閉じた。
- **段 3 の 2 提案を費用で不採用にした。** 旧凍結物を登録 preflight の凍結集合へ加える案は、
  追加分 2,130 file / 99,925,266 bytes に対し現実装が 1 file ごとに別 process で blob を読むため、
  既存 18 秒の検査が数百秒規模になり実行器の起動ごとにも同じ費用がかかる。しかも同じレンズが
  「preflight 後に旧 bundle へ書ける」経路は塞がらないと指摘した。epoch 欠落 catalog を拒否する
  新 gate も、production 経路が既に生成 document の完全一致で拒否済みなので追加硬化と判定した。
  両方とも裁定へ返す (U15、および U14)。
- **段 6 の整合レビューが親の docs の誤りを 3 件出し、差し戻した。** (1) 旧実行記録に実在する
  未裁定 U11 (同じ work ID が頁境界で重複する場合の条件 5) を落とし、同じ番号を anti-replay へ
  再利用していた。**裁定台帳の番号を再利用すると未決事項が記録から消える。** (2) U7 を
  「閉じた」と書いたが、旧実行記録は「どちらを正とするかは人間の裁定に委ねる」と明記しており
  併記は解決ではない。(3) file 数で追加分と拡張後総量を取り違えた。3 件とも一次資料で
  裏を取って訂正し、焦点再レビューが `closed` を返した。
- **整列キーの非単射は fixture では縛れない。** 親が実測したところ、引用符・カンマ・括弧・
  空文字列を含む敵対的な値で 29 通りの異なる canonical node を作っても整列キーは 29 通り
  すべて相異だった。キーはタグ付き tuple の JSON 表現で単射なので衝突対が存在しない。
  代わりに変異 M9 (キーを定数化) で性質を縛った。
- **計算ノードのキュー混雑で焦点走が 2 回 `queue-wait-timeout` になった** (`child_started: false`)。
  2 回目は codex 子を走らせずに投入して同じ結果なので外部要因である。3 回目で通った。
- **変異は 10/10 が期待 node 完全一致で KILLED、baseline は PASSED。** 固定 commit
  `e143c67a8` に対する走行で、MISMATCH・SURVIVED・TIMEOUT はゼロ。単一理由性は probe 段で
  実測した (各変異がちょうど 1 node を殺す。M8 のみ 2 node)。
- **変異 wrapper は 2 回とも rc=125 (`共有木の事後検査に失敗`) で終わったが、
  いずれも `child_rc = 0` で harness 自体は完走している。** 1 回目は親が走行中に
  `git checkout main -- docs/` で base digest を取ったためで、**親のミスである**。
  2 回目は作業ツリーに触れておらず、**共有 main checkout が並行 wave の land で変化したため**。
  この wrapper は走行中ずっと共有 main の観測 bytes が不変であることを要求するので、
  land が頻繁に走る環境では成功しにくい。成果物への帰属は無い。
- **教訓: base digest の lookup は作業ツリーを一時的に汚すので、変異走行と排他にする。**
- エージェント工数: codex 子 8 本 (plan 1、consult 2、author 1、review 2、fix 1、focus 1)。
  受領証は `dev-wave-jobs/dev-wave-t2091-openalex-cond1-order/artifacts/` 配下。
- **軸 1 の継続取得そのものは本 wave では行っていない。HTTP を 1 本も発行していない。**
  軸 1 の成熟度は `RW1` のままである。

## 次の一手差分

### 完了

- [T-2091] 条件 1 を順序非依存の比較へ改め、新 amendment `2026-09-02-axis1-search-amendment.md`・
  新 epoch `AX1-20260902-E1`・新 catalog を発行した。軸 1 の継続取得は解禁された。
  remaining: none
  base: a856f8d513d5cf26c8f442142331a9d6fd9b2c5a08e004c63ed95ffd6837f4eb
