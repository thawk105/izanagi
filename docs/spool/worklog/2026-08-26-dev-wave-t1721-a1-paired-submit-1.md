---
schema: izanagi-spool-v1
ledger: worklog
authored: 2026-08-26
wave: dev-wave-t1721-a1-paired-submit
seq: 1
title: [T-1721] A-1 対測定の投入は 2 つの独立した理由で成立しなかった — 実装差分ゼロで再裁定へ返す (docs、branch worktree-dev-wave-t1721-a1-paired-submit)
---

## 本文

- 依頼は「A-1 対測定を `formal=false` の探索値として投入する。裁定は確定済みで装置と事前登録は
  凍結済み、投入だけが残る。ただし着手時に『正式 certification ではないので批准 (D905) の gate は
  適用されない』という前提を probe で確認し、通らないなら理由を構造化して報告する」。
  **probe の結果、前提は 2 つの独立した理由で偽だった。qsub は 1 度も投げていない。**
- **理由 1 — 批准 gate は A-1 に適用される。** 論文上の `formal=false` とは無関係である。
  A-1 は各 arm の受理に verifier の `certified=True` を要求し、pipeline は certification 成功時だけ
  COMMIT して環境契約 hash を記録する。D259 は certification を lane 名でなく
  「成果物が certified 実行を主張するか」で決めるため、**論文上は探索値でも campaign としては
  certified 成果物**であり、gate の定義域に入る。`declared_use_class="exploration"` は
  layout selector を選ぶだけで gate を外さない (`loop.py` の該当分岐)。
  探索用に gate を外している production の呼出しは `guided.py` の 2 箇所だけで、そこは新しい build も
  bench も行わない replay harness である。段 3 の sol レンズがこの帰属を確定させた。
- **理由 2 — 装置には投入器が無い。** 「投入だけが残る」は D905 と独立にも偽である。
  A-1 の job body は自分が submitter でないと明記し、親が直接 qsub して acquisition receipt を
  create-only で書くことを前提にしているが、**その親側手順は実装されていない**。
  tracked file の全数検索で `paper-story-a1-paired-submission/v1` を書く実装は 1 つも無く、
  driver と job body はどちらも検証側だけである。receipt を組み立てるのは契約テストの fixture だけで
  ある。他の dispatch 必須 job body には `tools/pegasus/submit_*.sh` が 6 本あるが、
  A-1 に対応するものは無い。{{F:frozen-apparatus-without-submitter}}
- **実測した gate の壊れ方は、記録済みの理由とは別の場所だった。** 従来 F498 が記録してきたのは
  「closure digest が批准台帳に無い」である。今回実走すると、その比較へ到達する前に
  `ratification history is not a strict prefix extension` で落ちる。台帳の path 履歴は 17 commit で、
  台帳を開設した 1 件以外の 16 件はすべて merge commit であり blob が 112 bytes のまま動かない。
  検査は commit ごとに真の byte 増加を要求するため 2 件目で必ず失敗する。
  **どの digest を入力しても値を返さない状態**であり、wave 971 当時の main でも同型だった
  (新規回帰ではない)。これは F600 として台帳に既にあり、
  **修理は並行 wave (branch `worktree-dev-wave-t1759-t1742-ratification-history`) が所有している。**
  本 wave は同じ面を触っていない。
- **その修理が着地しても A-1 は開かない。** 検査 module 自身が閉包 25 path の 1 つなので、
  直せば closure digest が動き、台帳の唯一の行とは一致しない。正しい終端は履歴検査を通ったうえで
  `enforcement-source-closure-unratified` で落ちることであり、台帳へ行を足す行為が批准そのもので、
  D905 が「設計が着地するまで批准は進めない」と裁定済みである。
- **旧批准 commit へ戻る逃げ道も無い。** 唯一の批准行に対応する commit には A-1 driver が在るが、
  study ID が旧版で policy v2 が存在せず、wave 971 が凍結した反復数 72/205/28 の事前登録も無い。
  そこで走らせても事前登録した study にならない。
- **検出力の穴を実測した。** 批准検査の単体テストは計算ノードで 12 passed の緑である
  (request `948874.nqsv`)。production では動かないのにテストが全部通るのは、テストの履歴が
  すべて直列で merge を含む DAG を 1 度も通していないためである。並行 wave が同じ commit で
  504 行のテストを足している。
- **親の成果物影響の書き方が誤っていた。** 段 1 brief は「投入しないと論文 §8 の A-1 が 0 件のまま」
  と書いたが、`formal=false` の走行は成功しても §8 を正式には動かさない。凍結文書自身がそう明記して
  いる。実際に失うのは 610 rep の探索データ、3 workload の記述的分類、実分散、`rep_notes`、
  内部再測定の発生率、正式系列の設計を更新する経験的材料である。段 3 の sol レンズの指摘で直した。
- **親の数え間違いを段 2 が 1 件直した。** 台帳の履歴 commit 数を 18 と書いたが 17 である
  (wave 971 当時の main では 16)。数え直して brief を訂正した。構造的結論は変わらない。
  段 3 の luna レンズはさらに精度を上げた — 16 件は「両親に対して差が無い」のではなく、
  台帳を持つ親には差が無く、持たない古い親には差があるため列挙される。
- **段 3 が「成立するが採ってはならない」経路を 8 件確定させた。** v2 lock の偽造、
  `require_environment_contract=False` 化と collector の v1 対応、driver 内での複製や monkeypatch、
  `pipeline.evaluate` の直呼び、旧 closure への rollback、履歴の squash、AI による台帳追記、
  人間への転記依頼、平文承認。いずれも凍結境界、D905、D758、絶対規律 2 の少なくとも 1 つに反する。
  親はすべて不採用にした。
- **段 3 の sol が親と段 2 の双方が列挙し損ねた経路を 1 件見つけた。** 環境契約と live source 束縛は
  保ったまま、批准 authority を持たない**明示的な非 certification 成果物型**を作る経路である。
  sol は成立条件を 5 つ示した — caller のラベルでなく lock と WAL と consumer が主張する authority を
  見る、certified consumer の受理集合が 1 件も広がらない、非 certification が成果物の exact schema に
  刻まれ汎用 certified consumer が必ず拒否する、field の除去や付替えで昇格できず D510 決定 7 の
  昇格禁止を機械的に保つ、批准と独立な防壁は維持する。これを満たすなら gate を緩めるのではなく
  非 certification 型を certified gate の定義域外へ分離する変更になる。装置変更なので実装せず
  裁定パッケージへ回した。
- **段 3 の luna が A-1 投入と独立の real 所見を 3 件返した。** どれも実装せず裁定パッケージへ回した。
  (a) 既存 v2 lock の resume は批准を再検査しない。正規に作った lock の再開としては意図された設計だが、
  lock は署名物ではなく公開 encoder と現在の blob map から構成できるため、出力 root を書ける主体には
  批准済みと形式だけ正しいものを区別できない。F498 の本文はこの経路の存在を記していたが、
  偽造可能性までは書いていない。
  (b) 6 時間の walltime は end-to-end の完了を機械的に束縛していない。build は timeout 無しで呼ばれ、
  1 rep の timeout は 120 秒、reservation の入口検査は 1 秒しか要求しない。正常時の見積 (610 rep、
  約 34.2 分、内部再測定が最大まで起きても約 102.6 分) には余裕があるが、多数の rep が timeout する
  故障条件では balanced の 1 arm だけで 6 時間を越えうる。
  (c) 単独性と外乱の防護が runbook の要求を完全には満たさない。probe が見るのは ycsb の実行ファイルだけで
  compiler や他種の負荷を見ない。最初の bench の settle は 20 秒で未整定のまま進み、collector は
  `settled` を検査しない。bench 後の競合 post-probe が無い。
- **luna は「投入不能」という表現が強すぎると指摘した。** 機構上は qsub でき、3 workload とも
  `campaign-error` を持つ invalid な raw bundle を作って driver は 0 を返す。正確には
  「qsub はでき、finished な invalid bundle も作れるが、受理可能な探索値は得られない」である。
  親はその diagnostic 投入も**行わなかった**。投入器が無いので新規実装が要り、確実に無効な bundle を
  得るためだけに実装と計算資源を使うのは依頼の意図から外れると裁定した。
- **段 8 の改善候補 1 件は D782 の委任手順で実施しないに落とした。** 候補は「DW-G05 の成果物影響の
  1 行を、対象成果物の凍結文書が主張する射程と突き合わせて書く」。本 wave が親の誇張を実際に生んだ
  ので発火実績はある。`docs/dev-wave/**` の L1 層予算は満杯で、約 90 bytes の追記で
  10,625 bytes を 91 bytes 超過した。義務を担う既存文面を意味等価に削れず、発火実績は 1 例だけで
  D730 の例外収容が要求する独立 3 例に満たない。上限は引き上げていないので D782 に従い報告事項は無い。
- **段 4 の裁定は「実装しない」。** 実装差分ゼロで 4→7→8→9 とした。DW-S04 に従い、
  承認済み裁定を親が不採用にするのではなく、新事実を添えて再裁定へ戻す。

## 次の一手差分

### 更新

- [T-1721] **P1・ユーザー再裁定待ち**: A-1 対測定は `formal=false` でも campaign としては
  certified 成果物を作るため批准 gate の定義域に入り、現行 main では投入できない。
  加えて親側の投入器が実装されていない。択は (a) D905 の執行主体設計が着地するのを待つ、
  (b) certified consumer へ絶対に昇格できない非 certification 成果物型を別 wave で設計する、
  (c) 投入器の実装だけを先に別 wave で行う。
  base: 759ed7b272db7b80b0ef093a85613730e8bab64b79f6d49f04e227fe7f96ba4e

### 新規

- {{T:a1-noncertification-artifact-type}} **P2・ユーザー裁定待ち**: 環境契約と live source 束縛を
  保ったまま批准 authority を持たない明示的な非 certification 成果物型を設計するか決める。
  成立条件は段 3 sol が示した 5 つ。
- {{T:a1-parent-submitter}} **P2・新規**: A-1 の親側直接 qsub と acquisition receipt の
  create-only 書き出しを実装する。他 job body の `tools/pegasus/submit_*.sh` に対応する部品が無い。
- {{T:v2-lock-forgery-resume}} **P2・ユーザー裁定待ち**: 既存 v2 lock の resume が批准を再検査しない
  件を、意図された resume 設計のままにするか防壁の穴として塞ぐか決める。
- {{T:a1-walltime-hard-bound}} **P3・新規**: A-1 の end-to-end 完了を要求 walltime へ機械的に束縛する。
- {{T:bench-settle-and-post-probe}} **P3・新規**: 最初の bench の未整定通過、collector が `settled` を
  見ないこと、bench 後の競合 post-probe 不在を塞ぐ。
