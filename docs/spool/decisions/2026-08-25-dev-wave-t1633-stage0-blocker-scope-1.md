---
schema: izanagi-spool-v1
ledger: decisions
authored: 2026-08-25
wave: dev-wave-t1633-stage0-blocker-scope
seq: 1
---

## {{D:stage0-deferral-three-way-match}}. 段 0 blocker からの除外は三者一致でだけ成立させる

**決定:** D778 が段 0 blocker から外した「段 1 以降 owner の fixture assignment」は、次の三者が
exact に一致し、かつ対象 case が `pending` であるときだけ除外として成立する。1 つでも欠ければ
fail-closed で拒否する。

1. fixture manifest の fixture assignment gate (owner = `stage1-and-later`) が宣言する
   `owned_fixture_ids`。
2. contract module の独立 literal (manifest から生成せず literal として書く)。
3. 上位権限束設計 §10.2 が逐語で宣言する fixture ID 列。

除外の判定は純関数へ切り出し、parsed した gate / case 集合を直接渡す unit test で負例を殺す。
manifest hash pin より手前に負例が届かない構成にはしない。

**理由:**
- 上位権限束設計は「gate ID が名乗ることは除外の証拠ではない」と既に書いている。owner literal も
  同じ manifest による自己申告であり、単独では証拠にならない。三者一致にすると、除外を広げるには
  独立した 3 つの正本を同時に書き換える必要がある。
- 設計正本側に canonical な `design row → 段 → owner` の表を作って導出する案は採らない。同設計は
  その導出こそ fixture assignment gate の仕事だと定めており、いま要求すると「段 0 が段 1 以降を待ち、
  段 1 以降が段 0 を待つ」循環を作り直す。
- 除外の判定を純関数にしないと、負例が schema 検査や hash pin に先回りされて殺され、
  帰属が成立しないまま「検出力がある」と誤判定する。実測でこの型を回避した。

**却下した選択肢:**
- manifest の owner literal だけを根拠にする — 自己申告 1 つで受理集合が広がる。
- fixture case 側へ owner field を足す — case bytes と独立 pin 2 系統が動き、除外の根拠は
  やはり自己申告 1 つのままである。

## {{D:stage0-deferral-is-carry-not-waiver}}. 段 0 からの除外は免除でなく繰越とし、別述語で要求し続ける

**決定:** 段 0 blocker から外した fixture assignment は、免除ではなく後続段への繰越として扱う。

- `require_stage0_complete()` とは別に、繰越義務の解消を要求する述語を置く。同述語は raw pending が
  0 かつ fixture assignment gate が非 blocking になるまで、未解消の fixture ID を名指して拒否する。
- 段 0 完了述語はこの義務述語を呼ばない。段 0 の `complete` は繰越義務の解消を意味しない。
- 未解消集合は gate の blocking 状態から**独立に**算出する。gate を `resolved` にしただけで
  診断から fixture ID が消える形にしてはならない。
- 上位権限束設計は、将来の段 6 実装が X 候補提出前にこの義務述語を呼ばなければならないと定める。
  現時点でこの述語を呼ぶ production caller は存在せず、設計正本にそう明記する。

**理由:**
- 除外だけを実装すると、他の blocker が解消した将来に、実行可能な陽性・陰性 fixture を 1 件も
  持たない不変条件 5 行を残したまま段 0 を `complete` にできる。敵対レビューがその入力を構成した。
- 5 行の fixture をいま固定せよという対策は採れない。5 行が `pending` である実測の理由は
  「上位 resolver / admission entrypoint が未実装」であり、存在しない関数に対して実行可能な
  陽性 control を書くことはできない。それは D778 が段 1 以降へ移した作業そのものである。
- 義務の置き場所を機械述語にしておかないと、繰越は文書上の宣言だけになり、誰の完了条件でも
  なくなる。述語があれば、後続段の入口が実装された時点でそこへ束縛できる。
- 未解消集合を gate 依存にすると、gate を閉じにいく当の局面で診断が空になる。義務の唯一の
  機械可読なポインタが、最も必要な瞬間に消える。

**却下した選択肢:**
- 除外した fixture を段 0 の記録から落とす — 義務が誰の手番でもなくなる。
- 段 0 完了述語自身に繰越義務を含める — D778 が外した条件を名前を変えて戻すことになる。
