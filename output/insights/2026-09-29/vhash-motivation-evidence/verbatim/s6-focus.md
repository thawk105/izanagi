## 所見ごとの判定

| 所見 | 判定 | README の逐語（根拠） | 残る問題 |
|---|---|---|---|
| A1 | closed | §5.1 M1「実行中の tx から見えうる版を回収できない」「途中版の剪定 (M5) はその一部を回収できる」 | なし |
| A2 | closed | §5.2「prepared tx は commit / rollback の決定を待つだけで新しいアクセスが無く」 | なし |
| A3 | closed | §5.2「前進を許す操作だけからなるもの」「scan・insert・delete を含む tx \| 試作では扱わない」 | なし |
| A4 | closed | §3「`statement_timeout` (上限を超えた文を中止する。tx の長さそのものは縛らない)」 | なし |
| A5 | closed | §4.2「どちらも、待つ前に読み取りをしたかは指定しない」「読み取りの後に待つ具体的な型は md_2 の条件」 | なし |
| A6 | closed | §2.1「ただし時間型にも回収を止める例外があり、Spanner は partition token … CockroachDB は … protected timestamp」 | なし。別の時間型の一般化は N3。 |
| A7 | closed | §3「TiDB は既定で 24 時間まで回収を止めて待ち、その後は safe point を強制前進する」 | なし |
| B1 | closed | §4.1 の数値表は Steam・vDriver・SAP HANA・LeanStore の4件。「表に入れなかった研究」に Wu・HyPer・Sirin を記載 | なし |
| B2 | closed | §8「書き方の制限は §5.1 の M2」 | 指定された §8 の重複は参照に置き換わった。 |
| B3 | closed | 冒頭「台帳: worklog fragment `docs/spool/worklog/2026-09-29-dev-wave-vhash-motivation-evidence-1.md`」 | 所在の記載は確認した。fragment 自体の存在は射影外のため未点検。 |

## 量化の検算

- **§3「どの製品の対処も…両立させていない」— 成立。** 読んだ製品文書では、見えうる版を保持する、読み手を終了・失効させる、または書き手を抑える対処が記されている。Spanner の partition token と CockroachDB の protected timestamp も、読み手を生かす間は回収を止める例である（R2-4・R2-6）。
- **§0 項4「R3 の10本では、長い側が read-write の tx である実験は1本も無かった」— 成立。** R3-1〜4 の長い側は分析 query、固定 snapshot、点 query、cursor／読み取りだけの Trans-SI tx。R3-6 は read-only scan。R3-5 の「Long Transactions」実験は read-only の100操作 tx で、別の混合実験には100操作の read-write tx もあるが、「長い側」を read-write にした実験ではない。R3-7〜10 は該当する版保持実験を示さない。
- **§3「PostgreSQL・MySQL InnoDB・SQL Server・Aurora MySQL は…期限なし」— 成立。** ここでの「期限なし」は既定の*時間上限がない*という意味。PostgreSQL と Aurora MySQL の timeout は既定0、SQL Server の読んだ節にも時間による自動終了はない。README は SQL Server の強制 shrink 時の victim 化を明記している（R1-PG-CLIENT・R1-AWS-PARAM・R2-2）。
- **§2.1「C1 と C2 を分けて書いているのは SQL Server と Aurora PostgreSQL の blocker 一覧だけ」— 範囲の書き足しが要る。** SQL Server は snapshot scan と版生成 tx を別項にする。一方、Aurora PostgreSQL の一覧は reader instance と active statement を分けるが、後者を普通の read-write tx と特定していない。また、PostgreSQL は standby query と open tx を別の節で、MySQL は read-only の consistent read を明示している。「同じ blocker 一覧で両者を別項に列挙」のように判定基準を限定する必要がある（R1-PG-HS・R1-MY-MVCC・R1-AWS-PGBLK・R2-2）。

§1.1 の vDriver の上付き判定、§2.1 の Spanner 例外、§3 の timeout 行、§4.1 の表下の注、§4.2 の C3、§5.1 M1、§5.2 の表は、照合した保存原文・§6／§6.1 と整合した。

## 新しい所見

| ID | 重大度 | 節 | 何が誤りか・根拠 | 直し方 |
|---|---|---|---|---|
| N1 | should-fix | §0 項4 | 「研究側の数値はすべて C1」は無限定だと不成立。R3-8 の Sirin は OLTP throughput 0.58 等、R3-10 は latency の標準偏差を報告するが、どちらも版・GC の C1 症状値ではない。§4.1 は両者を正しく除外している。 | 「§4.1 の版・GC に関する症状の数値は」と限定する。 |
| N2 | should-fix | §2.1 末尾 | Aurora PostgreSQL の「active statement」は C2 と特定できず、「だけ」は PostgreSQL・MySQL の区別にも読める。上記の量化検算を参照。 | 文書内の別項列挙という基準と、active statement の tx 種別は未特定である点を明記する。 |
| N3 | should-fix | §3 末尾 | 「時間型の製品 (Oracle・…) は…長い読み取りを失敗させる側を選んでいる」は Oracle を一律に扱いすぎる。保存原文 `R2/oracle-undo19.txt` §16.2.2.3 は、既定では無効の `RETENTION GUARANTEE` を有効にすると長い query を守るため undo を上書きせず、領域不足では DML が失敗しうると記す。README の同節の表もこの設定を載せている。 | Oracle の既定動作と保持保証を分け、保持保証では書き手が失敗しうると併記する。 |

## 総括

閉じていない前回所見: **0件**。新しい must-fix: **0件**。
新しい事実記述上の修正が3件あるため、判定: **NO-GO**。