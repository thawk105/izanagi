## 総括

- **NO-GO**。
- 残 blocker は **4 件**。正規化衝突の検出穴、byte 会計の誤り、E-3/R6 の不完全な収容、worklog 未記録である。
- 最重要残余は、異なる pytest node を同じ key に潰す弱化がまだ生存し、変異台帳を偽 KILLED にできること。
- 新 3/3 KILLED・旧 3/3 SURVIVED の比較自体は限定付きで有効。MU-5 の 1-node 化も `DW-M03` と整合するが、全体被覆の証拠ではない。

## closed / partial / regressed 対応表

| 所見 ID | 状態 | 根拠 |
|---|---|---|
| C-01 | closed | MU-1 は strict-superset node だけを失敗させて KILLED。[new台帳:42](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t454-testification/mutation-ledger-new.json:42)、[test:352](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t454-testification/orchestrator/tests/test_mutation_harness.py:352) |
| C-02 | closed | MU-5 は 1 node だけを collection し、その node だけで KILLED。[control台帳:74](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t454-testification/mutation-ledger-control.json:74)、[control台帳:42](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t454-testification/mutation-ledger-control.json:42) |
| C-03 | closed | strict-subset node を追加し、MU-3 がその 1 node だけで KILLED。[test:365](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t454-testification/orchestrator/tests/test_mutation_harness.py:365)、[new台帳:86](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t454-testification/mutation-ledger-new.json:86) |
| C-04 | partial | path 全捨て変異は閉じたが、basename-only 等は生存すると fix 報告自身が認める。[test:381](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t454-testification/orchestrator/tests/test_mutation_harness.py:381)、[fix.md:61](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t454-testification/s6/fix.md:61) |
| C-05 | closed | 等集合の正例は既存 node で固定され、MU-5 が同 node で KILLED。[test:205](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t454-testification/orchestrator/tests/test_mutation_harness.py:205)、[control台帳:39](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t454-testification/mutation-ledger-control.json:39) |
| C-06 | closed | fixture・既存期待値・production は変更なし。[fix.md:67](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t454-testification/s6/fix.md:67)。差分は当該テストファイルへの 44 行追加だけ。 |
| D-01 | partial | T-454 は active のまま残ったが、F112/F124 文案は未起草。[worklog:3011](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t454-testification/docs/worklog.md:3011)、[draft:79](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t454-testification/ruling-package-drafts.md:79) |
| D-02 | closed | strict-superset / strict-subset の両方向を直接固定。[test:352](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t454-testification/orchestrator/tests/test_mutation_harness.py:352)、[test:365](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t454-testification/orchestrator/tests/test_mutation_harness.py:365) |
| D-03 | partial | 20 所見の三軸表は作られたが、A-08 全体を scope 内・実装済みと扱う一方、正規化衝突が残る。[fix裁定:57](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t454-testification/s6-fix-adjudication.md:57)、[fix裁定:65](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t454-testification/s6-fix-adjudication.md:65) |
| D-04 | partial | +274、+142 の符号、270 の歴史値は訂正済み。ただし B-2 は逐語なし、F112/F124 は未起草。[fix裁定:26](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t454-testification/s6-fix-adjudication.md:26)、[draft:37](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t454-testification/ruling-package-drafts.md:37)、[draft:81](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t454-testification/ruling-package-drafts.md:81) |
| D-05 | closed | 現行 25,187 bytes、A-1 −159、A-2 −48、合計 −207 は独立検算一致。[draft:15](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t454-testification/ruling-package-drafts.md:15)、[draft:21](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t454-testification/ruling-package-drafts.md:21) |
| D-06 | closed | P1a/P1b、N1a/N1b、R7 未発効を要求どおり分離。[fix裁定:11](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t454-testification/s6-fix-adjudication.md:11) |
| D-07 | closed | draft は非規範・未発効と明記され、repo 差分にも decisions/docs 変更なし。[draft:3](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t454-testification/ruling-package-drafts.md:3) |
| D-08 | partial | fix 裁定は「段7で入れる」と先送りしたままで、現 worklog に本 wave の実測記録はない。[fix裁定:50](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t454-testification/s6-fix-adjudication.md:50) |
| D-09 | partial | 12 項は列挙されたが、「見送り」見出し内に削除不適格を入れ、+386 / 1,150 の旧値も残る。[draft:155](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t454-testification/ruling-package-drafts.md:155)、[draft:164](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t454-testification/ruling-package-drafts.md:164) |

### 残余 R-01 — 新旧台帳と MU-5 の射程

旧側 SURVIVED は確かに collection 差で説明できる。新側は 60 node、旧側は 57 nodeである。[new台帳:170](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t454-testification/mutation-ledger-new.json:170)、[old台帳:158](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t454-testification/mutation-ledger-old.json:158)

ただし差分は追加された次の 3 node だけで、旧側だけにある node はゼロである。

- strict-superset
- strict-subset
- different-path

production tool の SHA は新旧とも `65e3390d…` で、三つの injection SHA も一致する。[new台帳:349](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t454-testification/mutation-ledger-new.json:349)、[old台帳:328](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t454-testification/mutation-ledger-old.json:328)

したがって collection 差は別要因ではなく、追加テストそのものである。「同じ collection が強くなった」ではなく、「旧 57 node では生存し、3 node だけを追加した新 60 node では各対応 node だけが殺した」と限定すれば過大ではない。一般的な検出力や残る弱化変異まで閉じた証拠にはならない。

MU-5 は `1/60 tests collected (59 deselected)` である。[control台帳:79](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t454-testification/mutation-ledger-control.json:79) これにより、既存の KILLED-dependent consumer 13 本を含む他の 59 node が、常時 MISMATCH 変異でどう壊れるかは見なくなった。

これは単一の等集合正例を証明する目的では `DW-M03` と整合する。冗長 gate を単独変異の証拠から外したためである。ただし「過剰拒否が全 consumer に無い」「全 KILLED 経路を正例が守る」という主張には使えない。

### 残余 R-02 — 正規化衝突の弱化変異が生存する

現在の vector は `tests/a.py` と `tests/b.py` なので、basename も異なる。[test:384](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t454-testification/orchestrator/tests/test_mutation_harness.py:384) 少なくとも次の弱化は静的に生存する。

```python
# directory を全部捨て、basename + test part だけ残す
path, _, test = _normalize_node(node, repo).partition("::")
return f"{path.rsplit('/', 1)[-1]}::{test}"

# 最後の二 path component だけ残す
return f"{'/'.join(path.split('/')[-2:])}::{test}"

# case-sensitive FS 上でも大小文字を同一視する
return _normalize_node(node, repo).casefold()

# class namespace を捨て、最後の test name だけ残す
return f"{path}::{test.rsplit('::', 1)[-1]}"
```

これらは現行の lower-case ASCII、二階層以下、class なしの入力では判定を変えない。一方、`tests/x/a.py` と `tests/y/a.py`、`A.py` と `a.py`、異なる class の同名 method を同一 key に潰せる。

成果物影響は小さくない。別 node の赤を期待 node の赤として偽 KILLED にし、変異台帳の `status` と worklog の kill 件数を直接変える。C-04 と同じ成果物影響なので、見送りは不整合であり **must-fix**。少なくとも basename-only 変異と、同 basename・異 directory の vector は今回固定すべきである。

### 残余 R-03 — byte 会計と削除分類

raw UTF-8、末尾 LF 込み、blockquote の `> ` だけを除いて再計数した。

| 本文 | draft 記載 | 再計数 |
|---|---:|---:|
| B-1 | 274 | 274 |
| B-2 | 142 | **逐語本文なしのため再計数不能** |
| B-3 | 263 | 263 |
| B-4 | 126 | **130** |
| B-5 | 112 | 112 |
| B-8 | 435 | 435 |

B-4 の差 4 bytes は、本文の `**拒否**` に含まれる四つの `*` である。[draft:55](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t454-testification/ruling-package-drafts.md:55) これを挿入本文から外すなら 126 だが、現 draft の raw 本文は 130 である。

B-2 の 142 を暫定的に受け入れても、

- 需要合計: `274 + 142 + 263 + 130 + 112 + 435 = 1,356`
- 回収後余白: `13 + 207 = 220`
- 不足: `1,356 − 220 = 1,136`

となる。B-7 は未起草なので、実需要はさらに大きい。したがって **1,352 / 1,132 は成立しない**。また D-b に旧見積り `+386` と `1,150` が残っている。[draft:165](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t454-testification/ruling-package-drafts.md:165)

削除候補ゼロについて、B-9 本文単体は「見送りではなく削除不適格」と正しく書いている。[draft:110](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t454-testification/ruling-package-drafts.md:110) しかし後段では「見送り（12項）」の item 8 に入れているため、文書全体では混同されている。見送り 11 件と、削除不適格 1 件を別節に分ける必要がある。

### 残余 R-04 — E-1〜E-3 と scope 収容

- **E-1 は十分。** D-06 の五分割を過不足なく再現し、worklog の禁止表現も明示した。
- **E-2 の erratum 自体は十分。** +142 の符号、+274、歴史不足 270 を正しく分離した。ただし D-04 が要求した成果物化は未完で、B-2 の逐語と F112/F124 の統合文案・実 byte がない。
- **E-3 は不十分。** 20 所見は三軸表に漏れなく現れるが、A-08 を一括して「採用・scope 内・実装」とした。[fix裁定:65](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t454-testification/s6-fix-adjudication.md:65) A-08 は正規化衝突まで関係分割に含めており、現在も残る以上、「閉じた vector」と「real・不採用・scope 外の残 vector」に分割しなければならない。[lensA:274](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t454-testification/s3/lensA.md:274)

R6 についても、列挙だけでなく F112/F124 文案と実 byte を作るまで D-04 は閉じない。

### 残余 R-05 — worklog の最終必須文言

次を逐語相当で記録する必要がある。

- 実装差分は `test_mutation_harness.py` の **3 node・44 行だけ**。commit は `a8a055a2` と `198b246d` の 2 本。production、`docs/dev-wave/**`、受理集合は不変。
- 固定したのは strict-superset、strict-subset、path 全捨ての三変異。basename-only、path suffix、case-fold、class namespace 衝突は未固定である。
- 変異は 3 走。新側 baseline 60 passed・3/3 KILLED、旧側 baseline 57 passed・3/3 SURVIVED、正例 baseline 1 passed・1/1 KILLED。
- 新旧差は collection 60 対 57 で、差分は追加 3 node だけ。「同一 collection」ではない。
- 関連受入は `test_mutation_harness.py` と `test_plain_runner_coverage.py` の **63 passed / 0 failed**、request `892462.nqsv`。[receipt:50](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t454-testification/output/pegasus-dispatch/b94e64ce5965cb35a6b6fced9c6fca6e/receipt.json:50)、[receipt:85](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t454-testification/output/pegasus-dispatch/b94e64ce5965cb35a6b6fced9c6fca6e/receipt.json:85)。repo 全受入とは書かない。
- S1/S2、権威 route、待ち手 3 条、残留 `.done` 拒否、probe、pgrep 代替は未実装。旧 raw 経路は残る。
- `docs/dev-wave/**` の回収実績は 0 bytes、現行 25,187 / 25,200。−207 は裁定・実装・caller 強制・本文置換後だけの見込み。
- 現 draft の既知需要は、B-2 の 142 を仮置きしても **1,356 bytes、不足 1,136 bytes**。B-7 は未起草で別途加算される。
- 削除実施なし、新 D 発効なし、decisions fragment なし。L2 削除候補はゼロで、これは見送りではなく削除不適格。
- T-454 は部分実施・active。R1〜R9、正規化衝突、F112/F124 文案、予算優先順位はユーザー裁定／後続実施待ち。

見送りは次の 11 件とし、削除不適格を混ぜない。

1. S1 の権威 route、D100/T-184 調停、R8 安全条件
2. 待ち手 3 条、残留 `.done`、全子 process への pgrep 照合規律
3. S2 と ABA・cross-node・starvation・generation/terminal/clean 問題
4. `DW-O01` / `DW-M05` の本文置換
5. `DW-G05` +274
6. `DW-S01` / `DW-S02` +142
7. F112/F124 の追記文案
8. T-505 恒久 3 機構と新 D の発効
9. 正規化衝突 vector
10. R7 delta 監査
11. 実 byte 確定と採録優先順位

禁止表現は、無限定の「テスト化した」「exact equality を機械化した」「待機を機械化した」「予算を空けた」「T-454 を完了した」「段3全所見を解消した」「新テストだけが検出した」「受入全走が緑」「需要1,352／不足1,132」「見送り12件」である。