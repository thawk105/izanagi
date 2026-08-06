## 総括

- **NO-GO**。段 7 の記録前に裁定文と裁定パッケージを直す必要がある。
- 親裁定は**全体として過小実行**。提案された S1/S2 を実装しない判断自体は正しいが、それを理由に既割当 scope まで test 1 本へ畳んだ。
- must-fix は **7 件**（D-01〜D-04、D-06、D-08、D-09）、nit は **2 件**。
- `DW-O01` −159、`DW-M05` −48、合計 −207 は検算一致。現行は 25,187 / 25,200 bytes、`check_docs.py` は違反なし。

### 所見 D-01 — S1/S2 の不実装は正しいが、wave 全体は過小実行

**主張**

S1/S2 を段 2 案のまま実装しない裁定は正しい。しかし、それで T-454 全体を「strict-superset test 1 本」へ縮めることは正当化されない。

S1 を実装しても旧 raw 経路が正規手順として残るため、受理集合は `旧経路 ∪ 新経路` のままになる。stale `.done`、重複 waiter、checker 未接続を迂回でき、既存 launcher とも二重投資になる。[lensA.md:11](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t454-testification/s3/lensA.md:11) [lensB.md:107](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t454-testification/s3/lensB.md:107)

S2 も target job ではなく「その瞬間に同 repo の誰かが lock を持つ」ことしか示さず、ABA、cross-node false-death、starvation、完了・clean の誤認を残す。[lensA.md:149](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t454-testification/s3/lensA.md:149) [s4-adjudication.md:44](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t454-testification/s4-adjudication.md:44)

一方、最新の既割当 scope は待ち手規約、(217) の 3 候補、F112/F124 追記を明記し、さらに以前の裁定で T-505 起草等も割り当てている。[worklog-phase3-0806-242-244.md:1010](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t454-testification/docs/archive/worklog-phase3-0806-242-244.md:1010) [worklog-phase3-0805-224-225.md:247](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t454-testification/docs/archive/worklog-phase3-0805-224-225.md:247)

**成果物への影響**

T-454 をこの wave で完了扱いすると、旧子出力の誤採用、途中変異台帳の確定、未採録規律が残ったまま active scope だけが消える。

**判定**

**must-fix**。

**推奨**

S1/S2 の欠陥案を復活させず、この wave を「exact-set 判定の一方向だけを補った部分実施」とする。T-454 は active のまま残し、既割当の起草物・byte 会計・見送りを段 7 で実体化する。

### 所見 D-02 — 「exact node set」のテスト化も片側だけ

**主張**

新 test が固定するのは `expected ⊂ failed` だけであり、完全一致性そのものをテスト化したとは言えない。

production は集合 equality で判定する。[mutation_harness.py:1191](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t454-testification/tools/mutation_harness.py:1191) 新 node は actual が真上位集合の場合だけを固定する。[test_mutation_harness.py:352](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t454-testification/orchestrator/tests/test_mutation_harness.py:352)

実装報告自身が `failed ⊂ expected` は専用 node なし・非 scope と認めている。[impl.md:15](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t454-testification/s5/impl.md:15) したがって、対称な弱化 `failed_keys == expected_keys` → `failed_keys <= expected_keys` を殺す vector がない。lens A も関係分割を一般推奨していた。[lensA.md:268](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t454-testification/s3/lensA.md:268)

**成果物への影響**

期待 node の一部しか赤くない変異を KILLED と誤認し、変異台帳の `status` と worklog の kill 件数が実走と食い違いうる。

**判定**

**must-fix**。

**推奨**

`expected={one,two}`, `failed={one}` を MISMATCH に固定し、`failed_keys <= expected_keys` を変異登録する。追加しないなら、「exact equality をテスト化した」とは書かず、残 vector を見送りへ明記する。

### 所見 D-03 — R1〜R7 は段 3 の全所見を収容していない

**主張**

段 4 は「20 件すべて real」としただけで、各所見の採否・scope 内外を裁定していない。[s4-adjudication.md:3](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t454-testification/s4-adjudication.md:3) これは `DW-S04` の real/refuted、採否、scope の三軸要求を満たさない。[core.md:69](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t454-testification/docs/dev-wave/core.md:69)

R1〜R7 に収容されたのは概ね A-01/B-02/B-04、A-05/A-06、A-09、B-01、B-05 である。次は入っていない。

- A-02、A-03 の S1 側：startup 前死亡、job-dir 所有・mode・ACL、shared FS の権威性。
- A-04/B-09：output checker と採用の E2E 結線、log・通知禁止、現行 wrapper との非互換。
- A-07/B-06：論理 condition key と generation nonce の分離、`launch.json`/`.done` schema の namespace 衝突。
- A-08 の残部：`failed ⊂ expected` と正規化衝突 vector。
- B-03：機械化時点では削減を計上せず、pointer 適用・caller 強制後だけ計上する原則。
- B-07：事実記録と長期 interface 発効の境界。
- B-08：将来 S1 を復活させる場合の G01 先行実験と、dogfood を通常成功走だけで代用しない条件。

[s4-adjudication.md:114](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t454-testification/s4-adjudication.md:114) [lensA.md:47](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t454-testification/s3/lensA.md:47) [lensA.md:216](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t454-testification/s3/lensA.md:216) [lensB.md:215](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t454-testification/s3/lensB.md:215)

A-10/B-10 は総括なので独立 R は不要だが、上記の実体所見は別である。

**成果物への影響**

現行 R1/R3 だけで将来案を承認すると、false completion、論理重複 waiter、無効 output 採用、誤った mutation verdict を再導入できる。

**判定**

**must-fix**。

**推奨**

R1 と R3 に設計前提を追記するか、R8「S1 の安全・identity・採用 E2E 条件」、R9「削減計上条件と G01」を追加する。採らない所見は `real / 不採用 / scope外` と明記する。

### 所見 D-04 — R6 は既割当 scope を正しく畳めていない

**主張**

R6 は T-505、F112/F124、142 bytes を列挙したが、T-287 §5 の 274-byte 追記／270-byte 歴史持越しを含めていない。[s4-adjudication.md:122](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t454-testification/s4-adjudication.md:122)

確認結果は次のとおり。

- T-505 の削除リスト、恒久 3 機構の規範文、新 D 起草は T-454 に明示割当済み。[worklog-phase3-0805-224-225.md:293](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t454-testification/docs/archive/worklog-phase3-0805-224-225.md:293)
- F112/F124 の `DW-S06-B` 追記も割当済み。[worklog-phase3-0805-235-236.md:307](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t454-testification/docs/archive/worklog-phase3-0805-235-236.md:307)
- 142 bytes は削減候補ではなく、予算不足で撤回した `DW-S01`/`DW-S02` への **+142-byte 追記**である。[s4-adjudication.md:130](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t454-testification/output/insights/2026-08-05_t244-p2-noninterference/s4-adjudication.md:130)
- archive (244) が直接持ち越したのは「必要枠 270 bytes」。[worklog-phase3-0806-242-244.md:969](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t454-testification/docs/archive/worklog-phase3-0806-242-244.md:969)
- 元の追記本文は raw 274 bytesで、当時の余白 4 bytes を引いた不足が 270 だった。[README.md:175](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t454-testification/output/insights/2026-08-04_t412-l2-pruning/README.md:175)

したがって R5 が 274 を需要量として扱う算術自体は正しいが、「(242-244) が 274 を記録した」という出典は不正確で、R6 の scope 復旧からは脱落している。

現行値では −207 適用後の余白は 220 bytes。そこへ既知の +274 と +142 だけで 196 bytes 超過し、F112/F124 と T-505 の byte はまだ未算出である。

**成果物への影響**

274-byte の `DW-G05` 防壁を scope 外へ落とし、未起草の F112/F124・T-505 を「入らない」と判定する根拠も作れない。

**判定**

**must-fix**。

**推奨**

R6 に 274-byte 本文を追加し、「原文 274／歴史不足 270／現行需要 274」を分離する。T-505 は「扱いを決める」ではなく、非発効の逐語 draft と byte 数を成果物にする。F112/F124、T-505 も文案を作って初めて「入らない分」を判定する。

### 所見 D-05 — −207 bytes と現行予算値は一致

**主張**

lens B の byte 数に誤りはない。

**根拠 (file:line)**

raw UTF-8、末尾 LF 込みの独立検算結果:

| 対象 | 現行 | 提案 | 差 |
|---|---:|---:|---:|
| `operations.md:8–12` | 644 | 485 | −159 |
| `mutation.md:35–37` | 263 | 215 | −48 |
| 合計 | 907 | 700 | **−207** |

現行本文は [operations.md:8](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t454-testification/docs/dev-wave/operations.md:8)、[mutation.md:35](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t454-testification/docs/dev-wave/mutation.md:35)、提案本文は [lensB.md:21](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t454-testification/s3/lensB.md:21) と [lensB.md:28](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t454-testification/s3/lensB.md:28)。

現行実サイズも一致した。

- core 8,534 / 9,600
- workers 4,668 / 5,000
- mutation 3,674 / 3,750
- operations 8,311 / 8,400
- 合計 25,187 / 25,200、余白 13

cap は [check_docs.py:176](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t454-testification/tools/check_docs.py:176)、hard ceiling は [check_docs.py:254](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t454-testification/tools/check_docs.py:254)、raw UTF-8 集計は [check_docs.py:3493](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t454-testification/tools/check_docs.py:3493) で実装されている。`python3 tools/check_docs.py` の実行結果は `check_docs: 違反なし`。

**成果物への影響**

数値訂正は不要だが、−207 は未適用の見込みであり、worklog の実績へ計上してはならない。

**判定**

**nit（確認済み、修正不要）**。

**推奨**

実績 0 と裁定後見込み −207 を同じ欄へ混ぜない。

### 所見 D-06 — P1/N1 は古典的矛盾ではないが、裁定表として論理型が壊れている

**主張**

P1 の「refuted（ただし採用）」は、「ユーザー発話から導出できるか」と「親が wave-local scope として選ぶか」を別軸と読めば矛盾ではない。しかし表の P1 は行為命題そのものを表題にしており、二軸を明示していない。[s4-adjudication.md:10](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t454-testification/s4-adjudication.md:10)

N1 も同様で、「同じ全件棚卸しの再実行は冗長」は real、「delta 監査まで無用」は refuted という量化範囲の分解なら通る。しかし元の N1 は無限定に「3 回目は無駄」と書く。[brief-addendum.md:5](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t454-testification/brief-addendum.md:5) 現行セルの `real (一般化は refuted)` だけでは、何が採用済みか確定しない。[s4-adjudication.md:20](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t454-testification/s4-adjudication.md:20)

**成果物への影響**

worklog が docs 凍結をユーザー命令と誤帰属したり、R7 の delta 監査を未裁定のまま発効済み手順として記録しうる。

**判定**

**must-fix**。

**推奨**

次のように命題を分ける。

- P1a「ユーザー発話が全 Markdown 凍結を含意する」＝ refuted。
- P1b「本 wave は `docs/dev-wave/**` を変更しない」＝親の wave-local 選択として adopted。
- N1a「同一外延の全件再走」＝ redundant。
- N1b「前回 anchor 以後の delta 監査も不要」＝ refuted。
- R7 の手順変更＝未発効・ユーザー裁定待ち。

### 所見 D-07 — worklog/insights は新 D 発効ではない。decisions fragment を書かない判断は正しい

**主張**

事実だけの worklog fragment、非規範の insights、未発効提案の byte 会計は新 D 発効に当たらない。spool は canonical 台帳への安全な搬送路であり、decision 権限を与えるものではない。[spool/README.md:3](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t454-testification/docs/spool/README.md:3)

長期の設計・権限・interface を変える採用済み判断だけが decisions 行きであり、未裁定の大変更は裁定パッケージへ返す。[skill-self-improvement.md:22](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t454-testification/docs/skill-self-improvement.md:22)

境界は場所でなく意味である。

- 事実記録: test 1 本、production 不変、回収 0、未実走、S1/S2 不実装。
- 未発効提案: R1 の必須 route、R2/R3 の pointer 置換、T-505 恒久 3 機構、R7 delta 監査。
- 新 D 発効: これらを「今後必須」「採用済み標準」と規範化すること。

**成果物への影響**

境界を守れば decision 台帳を汚さず事実を記録できるが、未発効提案を断定形で書けば worklog が別 decision 台帳になる。

**判定**

**nit（親方針は正しい）**。

**推奨**

`docs/decisions.md` fragment は書かない。insights には「非規範 draft／未発効」、worklog には「ユーザー裁定待ち」を逐語で付ける。

### 所見 D-08 — worklog に必要な最低文言

**主張**

次の事実を欠いた worklog は成果申告として不誠実になる。

**根拠 (file:line)**

実装報告は「1 node・13 行・production/docs 不変・未実走」と明記する。[impl.md:1](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t454-testification/s5/impl.md:1) 段 4 も回収 0 としている。[s4-adjudication.md:25](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t454-testification/s4-adjudication.md:25)

**成果物への影響**

過大な完了表現は T-454 を carry から落とし、未機械化経路や未採録規律を後続 wave から不可視にする。

**判定**

**must-fix**。

**推奨**

worklog に最低限、次を逐語相当で入れる。

- 「実装は `test_mutation_harness.py` の 1 node・13 行だけ。production の受理集合は不変」
- 「固定したのは `expected ⊂ failed` の MISMATCH だけ。`failed ⊂ expected` 等は未固定」
- 「S1/S2、待ち手 3 条、stale `.done`、pgrep 代替は未実装。旧経路は残る」
- 「`docs/dev-wave/**` は不変。回収実績 0 bytes、25,187 / 25,200、予算問題は未解決」
- 「−207 bytes は裁定後に実装・結線・本文置換した場合だけの見込み」
- 「削除実施なし、新 D 発効なし、decisions fragment なし」
- 「T-454 は部分実施で、R1〜R7と既割当 scopeはユーザー裁定／後続実施待ち」
- テスト・変異・受入は段 7 時点の実測だけを書く。現レビュー時点では pytest・変異は未実走であり、緑を先書きしない。[impl.md:59](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t454-testification/s5/impl.md:59)

禁止すべき誇大表現は「テスト化した」「exact equality を機械化した」「待機を機械化した」「予算を空けた」「T-454 を完了した」「段 3 全所見を解消した」である。

### 所見 D-09 — wave 終了時に明記すべき見送り一覧

**主張**

次をすべて列挙しなければ「入らない分だけ見送り」ではなく scope loss になる。

**根拠 (file:line)**

上位裁定は上限を上げず、削除・テスト化で空けて、入らない分だけ見送る方針である。[brief.md:15](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t454-testification/brief.md:15) 最新 scope も不変と明記されている。[worklog-phase3-0806-242-244.md:1010](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t454-testification/docs/archive/worklog-phase3-0806-242-244.md:1010)

**成果物への影響**

一項でも黙って落とすと、T-454 の完了集合と active task 集合が実際の未実装状態を表さなくなる。

**判定**

**must-fix**。

**推奨**

段 7 で次を明示する。

1. S1 の権威 route 選択、D100/T-184 調停、startup-death・identity・schema・FS 所有・checker E2E の設計と実装。
2. 待ち手規約 3 条と stale `.done` 拒否。docs に置くか tool に置くかも未裁定。
3. S2 probe と、その ABA・cross-node・starvation・generation/terminal/clean 問題の解決。
4. `DW-O01` −159、`DW-M05` −48 の本文置換・削除実施。現時点では両方未適用。
5. `DW-G05` の 2 行・274 bytes 追記。
6. `DW-S01`/`DW-S02` の撤回済み改善案 +142 bytes。
7. F112/F124 の `DW-S06-B` 追記。
8. T-505 の削除リスト。
9. T-505 恒久 3 機構の規範文と新 D draft。発効は明示どおり保留。
10. exact-set の残 vector `failed ⊂ expected`、および採らないなら正規化衝突 vector。
11. R7 の delta 監査への手順変更。
12. F112/F124・T-505 文案の実 byte 計測と、どれを入れどれを見送るかの優先順位裁定。

反対に、O04/O10 と既存 L2 全節は削除 gate を満たす候補がゼロであり、「見送り」ではなく「削除不適格」と記録する。実施済みと言えるのは `(d)` のうち strict-superset vector 1 本だけである。