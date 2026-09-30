### A1: cold 反例は成立しない

**重大度: must-fix。** 根拠: [plan.md:13](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-vhash-hot-block-v2/plan.md:13)、[transaction.cc:102](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-vhash-hot-block-v2/external/ccbench/cc/cicada/transaction.cc:102)。**反例不成立:** plan の hot `[A(40), C(30)]`、`trts=37` は cold ではなく、`C` を選ぶ hit である。cold なら末尾を含む全 hot 記述子が `>trts`。wts 降順の物理列で、hot 末尾より前に欠けた版も `>trts` なので、末尾からの stock 走査で最初の `≤trts` を飛ばせない。**影響:** (P1) を誤った理由で撤回し、cold の性能を不必要に下げ得る。**推奨:** cold の反例主張を撤回し、列の順序と末尾 pointer の寿命を前提にした短い証明へ差し替える。保守的に latest fallback を選ぶなら、正しさ上の必須修正とは書かない。

### A2: B の COUNT と post の COUNT の schema が食い違う

**重大度: must-fix。** 根拠: [plan.md:68](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-vhash-hot-block-v2/plan.md:68)、[plan.md:70](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-vhash-hot-block-v2/plan.md:70)、[plan.md:80](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-vhash-hot-block-v2/plan.md:80)、[vhash_cicada_hot_block.py:424](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-vhash-hot-block-v2/orchestrator/campaign/vhash_cicada_hot_block.py:424)。**具体的入力:** `B-k1` の build は pin＋variant のままで `schema_version=1` を出す一方、plan は５腕すべてを COUNT v2 で集計し、旧 v1 は読めなくてよいとする。**影響:** B の COUNT 四 cell が集計で拒否され、比較表・図が完備しない。**推奨:** B の v1 と post の v2 を別々に検証して共通の集計形へ正規化する。B の binary の意味を変えずに同時刻対照を維持する。

### A3: 隣接確認後の正しさは stock の並行実行前提に留まる

**重大度: should-fix。** 根拠: [plan.md:9](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-vhash-hot-block-v2/plan.md:9)、[transaction.cc:102](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-vhash-hot-block-v2/external/ccbench/cc/cicada/transaction.cc:102)、[transaction.cc:108](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-vhash-hot-block-v2/external/ccbench/cc/cicada/transaction.cc:108)、[transaction.cc:516](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-vhash-hot-block-v2/external/ccbench/cc/cicada/transaction.cc:516)。**試した interleaving:** reader が `P->next==X` を確認し、その直後に writer が P と X の間へ `Y` を CAS 挿入する。reader は X へ進む。これは確認時点で stock が P を越えて X に着いた実行に対応するため、**反例不成立**。第２段で X が PENDING から ABORTED へ変わる場合も stock と同じ待機・飛ばし方になる。**影響:** ここを無条件の「常に現在の stock と同じ版」と書くと、保証を過大にする。**推奨:** 一致を「隣接確認の時点」に限定し、その後は stock と同じ並行実行・GC 寿命前提へ帰着すると明記する。

### A4: B2 の commit は validation が壊れた証拠だけではない

**重大度: should-fix。** 根拠: [broken-cicada-vhash-skip-pending.patch:48](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-vhash-hot-block-v2/patches/broken-cicada-vhash-skip-pending.patch:48)、[transaction.cc:553](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-vhash-hot-block-v2/external/ccbench/cc/cicada/transaction.cc:553)、[README.md:71](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-vhash-hot-block-v2/output/insights/2026-09-29/vhash-hot-block-cicada/README.md:71)。**interleaving:** update が PENDING 版 P を飛ばして古い確定版を読む。P が validation 前に ABORTED へ変われば、validation (a) は P を飛ばして同じ古い版に到達し、commit できる。この経路は T1 の committed event 67 件という計数と矛盾しない。ただし観測された巡回すべての機序を説明したものではない。**影響:** committed 件数をそのまま「commit 時点でも P を不正に飛ばした」件数と解釈すると、一次資料の診断が誤る。**推奨:** plan §4 の計器どおり、read 時と validation 時の P の状態を同一 generation で対応づける。

### A5: stale-gap 壊しの到達計数だけでは誤読を証明できない

**重大度: should-fix。** 根拠: [plan.md:54](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-vhash-hot-block-v2/plan.md:54)、[vhash_cicada_hot_block.py:624](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-vhash-hot-block-v2/orchestrator/campaign/vhash_cicada_hot_block.py:624)、[core.py:174](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-vhash-hot-block-v2/orchestrator/verifier/core.py:174)。**具体的入力:** writer が hot 追加を省いた件数だけが１以上でも、reader がその隙間を選ばなければ誤読は０。reader が誤読しても、当該 trace に巡回が生じるとは限らない。**影響:** 巡回０を「安全」と誤読したり、未到達の壊しを検出力の証拠にしたりする。**推奨:** 「省略」「隙間を hit」「返却版がその時点の stock 第１段と異なる」「その読みを含む commit」を別計数にし、巡回・witness 帰属と突き合わせる。誤読 commit があって巡回０なら「未検出」と明記する。

### A6: 計算見積りは成功 job の基本計に限られている

**重大度: should-fix。** 根拠: [plan.md:82](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-vhash-hot-block-v2/plan.md:82)、[README.md:182](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-vhash-hot-block-v2/output/insights/2026-09-29/vhash-hot-block-cicada/README.md:182)。**具体的入力:** plan の 2,483 秒は列挙した成功 job の和として正しい。一方、md_23 の一次資料は失敗走・変異 probe・test も含む実績を 4,034 node 秒と記録する。**影響:** 約 3,000 秒という wave 全体への一般化は上限２ node 時間の余裕を大きく見せる。**推奨:** 本走の事前見積りには、既に消費した smoke・失敗 job・診断・test と追加 binary の見込みを足し、投入直前に総量を再判定する。

## 総括

最大の設計上の訂正は、plan の cold 反例が hit であり、(P1) の cold 継続を否定できない点。隣接確認ありの hit について、調べた CAS・PENDING・abort の interleaving からは stock との差を示す反例は作れなかった。GC trim と遅延 writer についても、活動中の writer の時刻が切断 anchor より新しいという前提下では、古い版の書き戻し反例は成立しない。実装前に必ず直すべき整合問題は、B の COUNT v1 と post の COUNT v2 の集計契約である。静的検査のみで、patch の適用・build・判定器実走は行っていない。