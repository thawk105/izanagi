---
schema: izanagi-spool-v1
ledger: failures
authored: 2026-08-26
wave: dev-wave-t1721-a1-paired-submit
seq: 2
---

## 新規

### {{F:frozen-apparatus-without-submitter}}. 凍結完了と宣言した装置に投入器が無く、次 wave が「投入だけが残る」と信じて着手した [誤前提] [手順漏れ]

- 事象: [T-1721] の裁定要約と作業依頼が「装置と事前登録は凍結済みで投入だけが残る」と述べ、
  次 wave はそれを前提に着手した。実際には親側の投入器が存在しなかった。A-1 の job body は
  自分が submitter でないと明記し、親が直接 qsub して acquisition receipt を create-only で
  書くことを前提にするが、その親側手順はどこにも実装されていない。tracked file の全数検索で
  `paper-story-a1-paired-submission/v1` を書く実装は 0 件で、driver も job body も検証側だけである。
  receipt を組み立てるのは契約テストの fixture だけである。他の dispatch 必須 job body には
  `tools/pegasus/submit_*.sh` が 6 本あるのに、A-1 に対応するものだけが無い。
- 根本原因: 前 wave は測定が別の理由 (批准 gate) で塞がれていたため投入器を作らずに凍結した。
  それ自体は妥当だが、凍結の宣言が「事前登録と検証側の装置が凍結済み」であることを
  「実行に必要な部品が揃っている」と読める形で要約され、欠けている部品が名指しされなかった。
  worklog 本文も「装置と事前登録までを作り、計測そのものは投入していない」とだけ書いており、
  投入器の不在は読み取れない。
- 恒久対応: `docs/dev-wave/core.md` の `DW-S01` が既に「別 program を起動する成果物では
  build・環境変数・外部 command と注入 seam の実在を棚卸しする」と定めている。本件はこの棚卸しを
  段 1 で実行して検出した実例であり、義務は既に存在する。欠けていたのは前 wave 側の
  「凍結時に未実装の実行部品を名指しする」側で、これは同節の「実測は省かず」と
  `DW-O12` の「裁定予定でなく実際に実行した手順を書く」で覆われる。新しい義務は足さない。
- 再発検知: 段 1 の前提実測で、投入・実行を伴う依頼は実行器の tracked file を全数検索で確かめる。
  検索が 0 件なら「投入だけが残る」という要約を根拠にしない。

## 再発

### F498

- **再発: 2026-08-26** — [T-1721] の A-1 sized-v1 を `formal=false` の探索値として投入しようとして
  同じ壁に当たった。今回は 2 点が従来と異なる。(1) 観測される例外が
  `enforcement-source-closure-unratified` ではなく、その手前の履歴検査
  (`ratification history is not a strict prefix extension`、F600) である。digest の比較まで
  到達しない。(2) 論文上 `formal=false` であることは免除にならない。A-1 は verifier の
  `certified=True` を各 arm の受理条件とし、pipeline は certification 成功時だけ COMMIT して
  環境契約 hash を記録するため、D259 の基準では certified 成果物であり gate の定義域に入る。
  `declared_use_class="exploration"` は layout selector を選ぶだけである。
  また本エントリが記していた「既存 lock の resume 経路は批准検査を通らない」について、
  その lock が署名物ではなく公開 encoder と現在の blob map から構成できることを実測で確認した。
  出力 root を書ける主体には、批准済み lock と形式だけ正しい lock を区別する手段が無い。
  批准検査の単体テストは計算ノードで 12 passed の緑である (request `948874.nqsv`)。
