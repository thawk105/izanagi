---
schema: izanagi-spool-v1
ledger: failures
authored: 2026-09-03
wave: dev-wave-loop-liveness-repo-external
seq: 1
---

## 新規

### {{F:lexical-prefilter-breaks-on-nfkc}}. 字句 prefilter が AST 発見の必要条件だという論証が Unicode 正規化で破れた [誤前提] [恒真ゲート]

- 事象: 親は段 1 brief で「AST の `Call` がその識別子を名乗る以上、source text に必ず現れるので、
  字句 prefilter は必要条件による上位集合であって除外述語ではない」と論証し、これを
  D872 決定 1 (族から外す条件を足さない) に抵触しない根拠とした。段 3 の敵対レンズがこれを否定し、
  親が現物で検算して確定した。`layout.ｅxploration_campaign_layout(x)` (先頭が全角 e、U+FF45) は
  生 source に ASCII の marker を含まないが、Python が識別子を NFKC 正規化する (PEP 3131) ため
  `ast.parse` 後の `Attribute.attr` は ASCII の marker になる。
  **生 source prefilter はこの file を捨て、AST 経路は driver として発見する。**
- 根本原因: 「AST が見る名前」と「source text にある字面」を同一視した。両者の間に
  言語仕様の正規化が挟まっている。親は Python の意味論を確かめずに論証を書いた。
- 恒久対応: {{D:lexical-prefilter-must-normalise-nfkc}}。判定を
  `unicodedata.normalize("NFKC", source_text)` に対して行う。費用は 187 file で 0.038 秒しか増えない。
- 再発検知: bounded fixture に全角 `ｅ` の正例を入れ、
  `_CAMPAIGN_DRIVER_MARKER not in nfkc_source` と
  `_CAMPAIGN_DRIVER_MARKER in unicodedata.normalize("NFKC", nfkc_source)` を両方 assert したうえで、
  production の発見関数を prefilter 有無の両設定で呼んで発見集合の一致を要求する。
  変異 `MUT-A2-NFKC-DROPPED` が正規化を外す形を直接殺す。

### {{F:external-binding-census-missed-work-prefix}}. repo 外束縛の全数調査が検索語の偏りで 2 系統を取り逃した [手順漏れ] [テスト代表性]

- 事象: 親は段 1 brief で「repo 外束縛は 3 件が全数」と書いた。実際は 5 file・3 root あった。
  取り逃したのは `/work/1/SFC/tanab/b10-backoff-grid-runs5` へ束縛する
  `test_b10_extended_figure_provenance.py` と `test_plot_b10_extended_backoff.py` の 2 本で、
  どちらも guard が無く、論文図 `fig2c_b10_extended_backoff.{png,pdf}` の provenance を
  22 file の sha256 で検証している。**剪定されれば全 wave の受入が同時に落ちる。**
- 根本原因: `git grep` の検索語を `/home/` と `expanduser` に絞った。事故の記憶
  (`~/.codex/sessions` の消失) に引きずられ、同じ prefix だけを探した。
  **既知の事故形から検索語を作ると、同型で prefix だけが違うものを構造的に見落とす。**
- 恒久対応: 全数を主張する前に、字句ではなく**実在判定**で絞る。AST で全 string literal を集め、
  「実在する repo 外 path で system prefix でないもの」へ絞る。親の実測では
  字句だけなら 1796 件、実在判定を掛けると意味のある束縛先は 3 root になった。
  ただし {{D:external-binding-census-stays-manual}} により、この走査を常設 gate にはしない。
- 再発検知: 段 3 の敵対レンズへ「親の全数主張を検査せよ」を明示的に課す。
  本 wave では段 2 のプラン子と段 3 のレンズ B が独立に同じ 2 件を発見した。

### {{F:concurrent-dispatch-starves-implementer}}. 焦点走と実装子を同時に投入し、実装子が 1 件も実走できなかった [手順漏れ]

- 事象: 親が段 5 の実装子を起動した直後に、別単位の焦点走を同じ worktree から dispatch した。
  実装子は自分のテストを走らせようとして `rc=16`、`child_started=false`、理由 `orphan-hold` で
  全件失敗し、**緑の裏づけを 1 つも持たずに完了報告を書くことになった。**
- 根本原因: `DW-O26` は「同一 worktree からの dispatch は全種を直列にする。並行投入は
  orphan hold で rc=16 になる」と定めているが、親はこれを段 5 の実装子起動時に適用しなかった。
  条件 dispatch の読み込みを段 6 直前だと思い込んでいた。
- 恒久対応: 手順の追加はしない。`DW-O26` は既に明示している。親が読む時点を誤っただけである。
- 再発検知: 実装子の完了報告に「実走した nodeid と結果」を必須欄として置いてあり、
  本件はそこが空になったことで即座に露見した。この欄が機能した。

### {{F:naive-parametrise-would-delete-the-check}}. 最長テストの分割案が、相互比較検査を消す形だった [恒真ゲート] [誤前提]

- 事象: 親は受入 wall の律速である最長単体 node
  (`test_role_sink_bytes_vary_only_at_declared_declassifications`、140 秒) の本体が
  `for value in range(32):` であることを見て、「32 個へ parametrize すれば最長単体は
  約 4.4 秒になり、仕事は 48 worker へ分散する」と報告した。**誤りだった。**
  node 末尾 (`:1941-1952`) にループを跨ぐ assertion があり、32 本の role sink 出力を
  相互比較して非干渉性を確かめるのがこのテストの目的である。32 node へ素朴に割ると
  相互比較がどの node からも消える。
- 根本原因: ループの本体だけを読み、末尾の集約 assertion を読まずに分割可能と判断した。
  **「1 node が N 回まわしている」形は、N 個の独立ケースとは限らない。**
  相互比較・不変量検査・非干渉性検査は、まわした結果を突き合わせるためにまわしている。
- 恒久対応: 費用削減の対象として node を挙げるときは、本体だけでなく**末尾の集約部**まで読む。
  読まずに分割案を書かない。絶対規律 2 の観点では、これは「検査を消して速くする」形であり
  reward hack に接近する。
- 再発検知: 親が自己訂正した (`measurements-3-acceptance-floor.md` の訂正節)。
  次の一手には「32 個へ parametrize する」という具体案を書かず、
  「相互比較を保ったまま 32 本の生成を並列化できるか」の生死確認 (`DW-G01`) として起票した。

### {{F:stale-done-marker-fakes-completion}}. 中断走が残した `.done` を消さずに再投入し、待ち手が偽の完了を報告した [手順漏れ]

- 事象: 変異 harness が orphan-hold で中断し `mutation.done` へ rc=2 を書いた。親は hold と sidecar を
  手順どおり解消して**同じ path へ**再投入した。新しい走行は正常に preflight を通過して稼働していたが、
  待ち手は 13:15:44 に書かれた**古い** `.done` を見て「MUTATION DONE rc=2」と報告した。
  親が file の timestamp と producer の pid 生存を突き合わせて誤りに気づいた。
- 根本原因: `DW-O01` は「既存 `.done` を消去・再利用せず再投入を止める」と定めている。
  親はこれを「消去してはいけない」とだけ読み、**同じ path へ再投入してはいけない**という含意を落とした。
  中断走が書いた完了マーカーは、次の走行にとって常に偽陽性になる。
- 恒久対応: 手順の追加はしない。`DW-O01` は既に明示している。
  中断からの再投入では `.done` を新しい path にするか、退避してから投入する。
- 再発検知: 待ち手が「完了」を報告したら、**`.done` の mtime と producer pid の生存を必ず突き合わせる。**
  本件では pid が 9 分 39 秒生存しており、`.done` は 10 分前のものだった。
  関連: 完了は `.done` と exit code だけで判定するが、**その `.done` が今回の走行のものか**は別に確かめる。

### {{F:parent-edited-repo-during-mutation-run}}. 変異走行中に親が repo を編集し、固定 HEAD 束縛で harness が全損した [手順漏れ]

- 事象: 変異 harness が baseline を終えて変異へ進んでいる最中に、親が
  `docs/spool/failures/...` へ 1 件追記した。harness は次の変異の直前に
  `runner/test bytes に固定 HEAD 外の変更を検出` で停止し、rc=2 で全損した。
  それまでの baseline の走行結果も破棄された。
- 根本原因: `DW-M05` は「変異中は親の編集と worktree へ書きうる子の起動を止める」と定めており、
  これは **tool が検証不能な親の自己申告義務**と明記されている。
  親は「docs は実装面ではないから触ってよい」と誤って区別した。
  **harness の固定 HEAD 束縛は path を区別しない。** worktree のどこであれ変更は検出される。
- 恒久対応: 手順の追加はしない。`DW-M05` は既に明示している。
  変異走行中は worktree のいかなる file も編集しない。記録は走行の前か後にまとめる。
- 再発検知: harness 自身が固定 HEAD 束縛で停止させた。**この機構は正しく働いた。**
  検出が遅れて誤った緑を出す形ではなく、fail-closed で全損させる形なので、
  損失は時間だけである。
