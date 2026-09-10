# T-1851 D2 — v5 prefix proof の consumer 結線

## 実装と範囲

holdout と ratified の consumer が result v5 の exact key 集合を選び、既存の shared live verifier と
対象世代の registry replay を通して prefix proof 7 key を検証する。既存 v4 の受理、正当な後続 append、
凍結23件の bytes、FORMULA_ID=s8b-floor-stats/v2 を維持した。

本体は consumer 2 file の入口と契約コメントだけ。検証器・registry・producer の新設や改訂はしていない。
fixtures は正規 reservation、issued marker、production plan/capture を使い、公開入口で正負例を検査する。
fixture の値は非性能テスト用であり、official 床値の実測でも、本走同等のE2E証拠でもない。
C3b の registry 側実値域は未取得のまま残し、新規 official campaign は起動していない。

## 検証した境界

- schema / registry_schema、7 keyの欠損・余剰: 既存proof shape validator。
- freeze / protocol: artifactの束縛と、実protocol/freezeから導く期待値。
- schedule: 実scheduleから独立に導く期待値。
- row_count / chain_head: 実registryの先頭N行のproof。
- registryの欠損・改竄・有効prefixへの短縮: 対象世代の実replay。
- 正当append後のv5、registryを持たない既存v4: 両公開consumerで受理。

## 実装前後の実測

継承元は d995828089efca39073548223ed4951c9bdf5402。
親は local main を統合し、7d79909507bb72700dc85933ad37e94608dfbbde 上へD2差分を適用して実走した。

| 検査 | 結果 |
|---|---|
| merge の docs/caller テスト | 616 passed / 3 skipped |
| 既存 prefix / v5 検証器 | 34 passed |
| 既存 consumer baseline | 197 passed / 2 skipped |
| 保全 producer の通常v5・prefix全消費対応・再開再検証 | 3 passed |
| 初稿の公開v5正例 | holdout成功、ratifiedはfixtureのsession射影不具合で停止 |
| 修正後の公開v5正例とunhashable schema回帰 | 6 passed |
| holdout単独全走 | 157 passed / 2 skipped |
| ratified単独全走 (990010.nqsv) | 82 passed、22.04s |
| 関連35file (990012.nqsv) | 3810 passed / 24 skipped、1 collection error |
| 上記で収集できなかったapproved単独 | 探索pathを明示し10 passed |

35fileの唯一のerrorは、選択走で tests.skiputil の探索pathが無いことだった。
ソースや期待値は変えず、同fileを正しいpythonpathで実走した。したがって関連集合の実走は
3820 passed / 24 skipped。初稿のratified不具合は検査入力だけをsession/session-startへ射影して修正した。
frozenset membershipによるunhashable schemaのTypeError回帰も、非hash比較で旧来の管理された拒否へ戻した。

独立レビュー2本と焦点再レビューは完了し、既知2件はclosed、追加real所見は無かった。
変異本走は2回とも baseline成功、6/6 KILLED・期待失敗node完全一致となった。
M1/M2はv5 keyのv4固定、M3は独立proofの自己照合、M4は現在末尾との比較、M5はv4の過剰拒否、
M6は余剰proof keyの見逃し。M3/M6は公開consumerで不正成果物が誤受理されることを実測した。
隔離テストのchild rcは0、復元・後片付けも成功したが、外側wrapperは並行mainの状態変化を
検出し2回ともrc=125だった。1回目はmethods文書land、2回目は同sessionのhandoff削除。
sourceのHEADとbytesは不変であり、変異結果と共有状態検査の不成立を区別して記録する。
初回probeのMISMATCH6は失敗node集合の採取を目的とした仮登録との差であり、本走結果ではない。
同じanchor/specを独立local cloneに置き、同じ既存wrapperで再実行した最終走は
6/6 KILLED・期待node完全一致、child/wrapperともrc=0、shared snapshot一致・teardown成功となった。
この最終結果は mutation/mutation-isolated.json.gz と対応wrapper receiptに収録した。

最新mainを含むmerge f5652cbe9e8084cba55805e3fbdf08e4a1d0ba08で、checker合成の関連テストは
636 passed / 3 skipped。D2本体・fixtures・所要台帳は実装anchor ce2769c329123837f9fda92cac8c90837edabe17 と同じ。
受入1はmergeされたchecker2fileの著者確認でテスト開始前に停止し、D95 author合成後に再投入した。
受入2は3 shardで開始したが、既存t1259のgit status30s timeoutが21件出た。
同コードの単独走は51 passedだった。最後のshardは99%でログ無成長・補助process不在・長時間無応答となり、
D676に従い受入親へTERM、残computeをqdelして終了した。成功受入とは扱わない。
再走は同じテスト集合で既存設定を2 shard/8 workerへ抑える。受入3は並行mainのcaller一覧合成の
著者確認でテスト開始前停止したため、D95 authorで合成して再投入する。
所要台帳更新とmain landは、この記録時点では未完了である。

## 全走で判明した既存fixtureの履歴依存

2 shard/8 workerの受入5では片側が11524 passed/6 skippedとなったが、残る片側が99%で長時間化した。
Python stackを取得すると test_t1998_stock_inline_pair の事前登録blob欠損負例が、HEAD全史の各commitに
対してloader63blobを読み、「現在と同じloaderで事前登録文書が無い祖先」を探していた。
40分を超えても終端せず、D676の復旧として受入を終了した。成功受入とは数えない。

Codex authorが同fileの既存一時Git fixtureにcommitted_missing分岐を加え、loader bytesは同じ、
測定commitにだけpreregistration blob無し、current worktree文書は正規bytesという負例へ置換した。
公開consumerと拒否code/field/armは不変、production・gate・期待値・テスト集合・timeoutは変更していない。
独立焦点レビューで追加must-fixなし、親の同file全走は991557.nqsvで39 passed、7.37秒。
追加差分は受入を現に塞いだこのfixture1fileだけである。

## 統合時の文書整理

C3bの保全fragmentと後続rulingsが同じT-1851の次手を更新する衝突を解消した。
古い更新案はC3b fragment本文へ全文保存し、deltaをcarryにした。canonical台帳は直接編集していない。
spool foldのdry-runはplannedとなった。

起動時のmain未包含で作業全体を終了した判断は誤りだった。ユーザー指示を受け、認可範囲内の
復旧可能な赤は修復して再検査し、継続した。自己改善用プロンプトは self-improvement-prompt.md に収録した。

## 収録物

- verbatim/: brief、plan、敵対相談、裁定、author、review、fix、focusの逐語をgzipで無損失保存。
- mutation/: probe、本走spec、2回の本走とwrapper結果をgzipで無損失保存。
- ruling-package.md: 旧10件を現行裁定と今回の直接指示へ照合した持ち越し整理。
- self-improvement-prompt.md: 誤停止を防ぐ自己改善用プロンプト。改善実装や次waveは起動していない。
