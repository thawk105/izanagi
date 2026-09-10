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
受入全走、所要台帳更新、変異の実測結果、main landはこの記録時点では未完了である。

## 統合時の文書整理

C3bの保全fragmentと後続rulingsが同じT-1851の次手を更新する衝突を解消した。
古い更新案はC3b fragment本文へ全文保存し、deltaをcarryにした。canonical台帳は直接編集していない。
spool foldのdry-runはplannedとなった。

起動時のmain未包含で作業全体を終了した判断は誤りだった。ユーザー指示を受け、認可範囲内の
復旧可能な赤は修復して再検査し、継続した。自己改善用プロンプトは記録段で収録する。
