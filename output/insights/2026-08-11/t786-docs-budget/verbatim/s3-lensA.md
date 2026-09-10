## 総括

**判定: NO-GO。現プランのまま land すべきではない。**

最も高い確率で起きる事故は、段 6 で `tools/dev_wave_wait.py acceptance` を使っているというだけで機械検査を通し、`run_tests.py -rf` 等の非 canonical な受入を投入して、F153 が追加した未追跡削除・RuleOps の事前検査を静かに迂回したまま「受入緑」と記録することだ。

brief の P1 は「script が義務を代替する」という範囲を過大評価している。実際の script が保証するのは一部の実行時挙動だけで、正しい argv、正しい PID の作り方、親が script を必ず使うこと、`.done` 内の exit code、停止時の waiter 廃棄は保証しない。

## 実在する所見

### A-1 — 段 6 から runbook への唯一の住所が消え、F153 の迂回経路が再び開く

- **file:line:** [plan2.md:84](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t786-docs-budget/plan2.md:84)、[dev-wave.md:51](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t786-docs-budget/.claude/commands/dev-wave.md:51)、[pegasus-runbook.md:781](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t786-docs-budget/docs/pegasus-runbook.md:781)、[dev_wave_wait.py:274](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t786-docs-budget/tools/dev_wave_wait.py:274)、[failures.md:3931](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t786-docs-budget/docs/failures.md:3931)
- **何が壊れるか:** 現行 command は runbook を参照し、そこには裸の `python3 tools/run_tests.py` を渡し、`-rf` や `-q` を付けてはならないという F153 の恒久対応がある。置換後は bare script 名しか残らない。一方、script は `--` 以降の任意コマンドを受け付け、canonical な受入形状かを検査しない。
- **再現シナリオ:** 親が  
  `python3 tools/dev_wave_wait.py acceptance … -- python3 tools/run_tests.py -rf`  
  を実行する。script は正当に lease を取得して rc=0 を返し得るが、`run_tests.py` 側では canonical acceptance と認識されず、F153 の事前検査が発火しない。計画中の literal checker も通る。
- **自己判定:** **real / blocker**
- **修正案:** 段 6 に runbook の住所と「裸の `python3 tools/run_tests.py`」を残す。機械化するなら script が argv を exact match し、非 canonical な引数を fail closed するまで prose を削らない。

### A-2 — 新 checker は安全義務ではなく文字列の所在しか検査しない

- **file:line:** [plan2.md:309](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t786-docs-budget/plan2.md:309)、[plan2.md:359](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t786-docs-budget/plan2.md:359)、[skill-self-improvement.md:83](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t786-docs-budget/docs/skill-self-improvement.md:83)、[failures.md:4387](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t786-docs-budget/docs/failures.md:4387)
- **何が壊れるか:** `tools/dev_wave_wait.py acceptance` などの literal が「見える top-level」に一度あることは、その invocation が義務であることを保証しない。これは F170 が記録した「decoy literal でも通る」失敗と同型である。正本自身も `check_docs.py` は意味ではなく構造を守るものだと明記している。
- **再現シナリオ:** 段 6 を  
  「`tools/dev_wave_wait.py acceptance` は参考例であり、急ぐ場合は手動投入してよい」  
  と変える。要求 literal は一度だけ存在し、節も正しいため、計画された検査契約では通る。
- **自己判定:** **real / blocker**
- **修正案:** 文字列の存在ではなく、全文一致する normative line を pin する。否定、参考例化、blockquote 化、任意 argv、`--owned-path` 欠落を落とす negative test を追加する。runtime invocation の代替だと主張するなら、実際の argv/receipt lineage も検査対象にする。

### A-3 — P1 は producer PID 義務を script 実装済みと誤認している

- **file:line:** [brief.md:59](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t786-docs-budget/brief.md:59)、[plan2.md:47](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t786-docs-budget/plan2.md:47)、[dev_wave_wait.py:244](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t786-docs-budget/tools/dev_wave_wait.py:244)、[dev_wave_wait.py:353](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t786-docs-budget/tools/dev_wave_wait.py:353)、[pegasus-runbook.md:842](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t786-docs-budget/docs/pegasus-runbook.md:842)、[failures.md:4087](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t786-docs-budget/docs/failures.md:4087)
- **何が壊れるか:** script は `--pid` を今も受理し、pid-file を producer 自身に書かせない。また `/proc/<pid>/stat` を読めない場合は starttime 照合なしの PID-only に降格する。producer 自身の `echo $$` は runbook/prose にしか存在しない。したがって T757 を「構造的に不要化」、T738 を「starttime 三点照合へ移行済み」とする一般化は成立しない。
- **再現シナリオ:** 親が `nohup setsid … &` の `$!` を pid-file に書く。script はその数値が producer 自身によるものか検証できず、wrapper PID の死を producer 死と誤認し得る。`--pid "$!"` を直接渡しても parser は受理する。
- **自己判定:** **real。既知の starttime fallback 自体を新規 bug とするのではなく、P1 の「全面的に機械代替済み」という根拠が false**
- **修正案:** T757 の prose と runbook 住所を残す。producer 起動 wrapper が自分で pid-file を生成するところまで単一 tool に封じるか、script 側で自己発行された identity を検証できるようにしてから不要化する。

### A-4 — `DW-C00` の「停止時に待ち手も落とす」は script に実装されていない

- **file:line:** [core.md:17](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t786-docs-budget/docs/dev-wave/core.md:17)、[plan2.md:41](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t786-docs-budget/plan2.md:41)、[dev_wave_wait.py:386](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t786-docs-budget/tools/dev_wave_wait.py:386)
- **何が壊れるか:** 現行は manager に「生産者を止めるときは待ち手も落とす」という能動義務を課す。script は PID が生存している限り待ち続け、default では timeout もない。計画文の「生産者の停止・死で待ち手も終える」は、自動保証であるかのように読めるが実装と一致しない。
- **再現シナリオ:** producer が hang/SIGSTOP し、親がその仕事を中止扱いにするが process を殺し切らない。新文を script 任せと解釈した親は waiter を落とさず、wave が永久待ちになる。
- **自己判定:** **real**
- **修正案:** 現行の能動形「生産者を止めるときは待ち手も落とす」を保持する。script に cancellation/mandatory timeout を実装するなら、その後に置換する。

### A-5 — `DW-O01` の prompt 検査順序が弱化する

- **file:line:** [operations.md:8](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t786-docs-budget/docs/dev-wave/operations.md:8)、[plan2.md:55](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t786-docs-budget/plan2.md:55)、[plan2.md:64](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t786-docs-budget/plan2.md:64)、[failures.md:335](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t786-docs-budget/docs/failures.md:335)
- **何が壊れるか:** F23 の恒久対応は「投入前」の非空検査である。現行の「先に」が消えると、「detach 後に検査した」実装も文面上は反論可能になる。
- **再現シナリオ:** 空 prompt を渡して worker を起動し、直後に親が非空検査して失敗を検知する。既に worker は空入力で走っており、検査は安全 gate になっていない。
- **自己判定:** **real。文の並びから順序を推測できても、安全 gate の縮約としては曖昧化自体が弱化**
- **修正案:** 「prompt 非空を**投入前に**検査し」を保持する。

### A-6 — `DW-S04` は意味等価ではなく、mutation 免除を明確に拡大している

- **file:line:** [core.md:79](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t786-docs-budget/docs/dev-wave/core.md:79)、[plan2.md:176](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t786-docs-budget/plan2.md:176)、[plan2.md:188](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t786-docs-budget/plan2.md:188)、[skill-self-improvement.md:58](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t786-docs-budget/docs/skill-self-improvement.md:58)
- **何が壊れるか:** 現行の免除は、人間が「実装しない」と裁定した wave に限定される。置換案は「実装差分ゼロ」の全 wave に広げる。plan 自身も非等価と認めている。
- **再現シナリオ:** 将来の docs-only budget wave が command の安全 gate を縮約する。実装差分ゼロを理由に、否定 mutation や static consumer 検査なしで完了できる。
- **自己判定:** **real / blocker**
- **修正案:** T765 をこの wave から外して現行文を維持する。正しさ防壁の変更なので、段 4 worker の内部判断ではなく明示的なユーザー裁定を得て別変更として扱う。

### A-7 — `DW-M08` の追加文は expectation laundering を許す

- **file:line:** [plan2.md:269](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t786-docs-budget/plan2.md:269)、[failures.md:3625](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t786-docs-budget/docs/failures.md:3625)、[failures.md:4344](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t786-docs-budget/docs/failures.md:4344)
- **何が壊れるか:** 「予測を実測へ揃える走行を見込む」は無条件に読める。F138 が許したのは静的に完全集合を確定できない場合の明示的 probe、erratum 保持、再登録・再走である。F168 は review で分かった blast radius を本走前に更新する義務を置く。
- **再現シナリオ:** review が expected node 3 件を示しているのに親が 1 件だけ登録して走らせ、結果を見て期待値を更新し「実測へ揃えた」と処理する。
- **自己判定:** **real**
- **修正案:** 「静的に完全集合を確定できない場合に限り、初回を probe と明記し、erratum を残して再登録・再走する」と F138 の条件をそのまま残す。

### A-8 — 「現状余白では 1 件も入らない」は実測から導けない

- **file:line:** [brief.md:25](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t786-docs-budget/brief.md:25)、[brief.md:33](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t786-docs-budget/brief.md:33)、[plan2.md:299](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t786-docs-budget/plan2.md:299)
- **何が壊れるか:** 全体や別 layer の余白ゼロは、各候補が入らないことを意味しない。現在の `DW-O09` は 935/1000、plan が算出した T784 の追加義務は 63 bytes なので、単純計算では 998/1000 に収まる。T765 も置換自体は負 delta である。
- **再現シナリオ:** 「何も入らない」を根拠に unrelated な安全文を複数削り、その後に実は候補単体が既存 slack 内へ入ったと判明する。
- **自己判定:** **real。ただし headline の層別実測値そのものは正しい**
- **修正案:** 「当初案の文面では超過」と「意味を保った最小 net delta」を分け、候補ごとに差分後 byte を計測する。T784 は既存 O09 を削らず、追加だけで検証すべきである。

## 親が挙げた疑いのうち refuted だったもの

### rulings の ID 差分

- **file:line:** [plan2.md:125](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t786-docs-budget/plan2.md:125)、[rulings.md:14](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t786-docs-budget/.claude/commands/rulings.md:14)、[failures.md:5241](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t786-docs-budget/docs/failures.md:5241)
- **自己判定:** **refuted**
- 新案は全 `-[T-` 実体を走査し、現 entry の実体 ID と索引 ID の差を索引確定前に検査する。新規追加 ID を索引から落とすとこの差に現れる。前 entry への遡及を消滅・降格に限定しても、新規追加の検出経路は失われない。
- ただし曖昧さを消すため「差集合」を `実体ID − 索引ID` または `対称差` と明記するのがよい。

### `.done` の実在照合

- **file:line:** [plan2.md:67](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t786-docs-budget/plan2.md:67)、[dev_wave_wait.py:408](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t786-docs-budget/tools/dev_wave_wait.py:408)
- **自己判定:** **実在義務の消滅という疑いは refuted**
- 「`.done` の exit code」は `.done` の存在を前提とし、script も regular file の実在を照合する。
- ただし script は `.done` の内容を読まない。空、非数値、非ゼロでも waiter 自体は成功するため、named tests は「exit code を読んで成否判定する」という O01 prose の代替にはならない。この prose は削除不可である。

## 破れなかった面

- `L1=10,625/10,625`、`L1.5=9,554/9,566`、`DW-O09=935/1000`、rulings 4,991、dev-wave command 9,497 は、`check_docs.py` の分類処理と `wc -c` を静的に再現した範囲で一致した。測定値の捏造・分類不一致は見つからなかった。
- `DW-M01`、`DW-S05-C`、`DW-S06-A`、`DW-O09` の提案文には、今回構成できる新しい許容挙動は見つからなかった。
- 段 9 の release 縮約は、成功した acceptance lease を land terminal まで保持する runbook と整合していた。
- L2 節の削除候補は plan 自身が提出していないため、「発火実績なし」を反証すべき候補はなかった。この wave で L2 削除を追加する根拠もない。
- pytest は要求どおり実行していない。確認は source、履歴、failure ledger、checker と waiter の静的読解のみである。