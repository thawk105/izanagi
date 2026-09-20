## 所見

**RA-1 — should：削除の実行手順を、段4の予定と区別して記録する。**

- **対象**：`s4-adjudication.md`「不変条件」、`codex/s5-author-2.md`「変更」、unit commit `8f6aee197`。
- 段4は「`git rm` でstage」とするが、authorは未stage削除を報告している。その後、launcherが残差をcommitしたことをunit commitから確認した。段7には、この実際の経路を記録し、「authorがgit rmでstageした」とは書かないこと。
- 現在のHEADは`455b03f36`、作業木はclean。DW-O11の本体である「未stage削除を受入へ持ち込まない」は解消済みであり、削除をやり直す必要はない。
- **DW-G05：放置すると、成果物の値・受理集合は変わらないが、実施記録が実際のstage／commit経路と食い違う。**

実装のmust-fixは検出しなかった。以下は静的検査の結果であり、変異本走・受入全走の合格を主張するものではない。

## 消しすぎ / 残しすぎの判定表

削除済みファイルの行番号は、削除前の`947fd160a`を指す。

| 対象 | 判定 | 根拠 |
|---|---|---|
| R1の6ファイル | 削除妥当 | D2172項5の明示対象。残存code・設定の名前検索でconsumerを検出せず。歴史記録・到達性台帳は裁定が保持を指示しており、未見の保持理由ではない。 |
| `s6_canary_rename.py` | 削除妥当 | 完了済みcanary。共有表から消したのは対応する4エントリのみ。 |
| `insights_date_layout.py`＋test | 対削除妥当 | testのconsumer／pin検査も、一時Git tree上で削除toolを検査するもの。残存readerの検査は検出しなかった。 |
| `migrate_output_gzip.py`＋test | 対削除妥当 | round-trip、stage、rollbackは削除migratorの検査。`gzip.decompress`による検算を、live readerのfallback被覆と取り違えていない。 |
| `plot_t2266_tail_mechanism.py`＋test | 対削除妥当 | `:281`は削除生成器の外挿関数とliteralを比較。`:390`は同生成器が新しく作るprovenanceの入力digestを検査する。実reportは読むが、残存live codeの独立検査ではない。継続再計算・図生成の被覆は失われる。 |
| `backoff_requested_us`対 | 保持妥当 | test `:1092`がliveな`dispatch_compute._child_environment`を直接呼び、PBS変数除去を検査する。残存patch・registryの検査もあり、「専用testごと削除」の前提が成立しない。 |
| `t1434_t1222_science_slice`対 | 保持妥当 | test `:409`の外部jobs集合pinは`list-D.txt:283`に実在。D2172項6は候補も「削らず」とする。項5優先を新設せず保持した裁定は妥当。 |
| `backoff_counterfactual_analysis`対 | 保持妥当 | 凍結仕様のSHA・seed集合との契約を実装。「現行機構でない」の確認が足りず、追加削除を支持できない。 |
| `backoff_counterfactual_cohort2_analysis`対 | 保持妥当 | 残存`test_t2187_adaptive_const_probe.py:24`・`:1976`がseed定数をimportし照合する。 |
| `backoff_nonmonotonicity_analysis`対 | 保持妥当 | T-2583／T-2635の別解析で関数再利用が記録され、一回限りという分類が成立しない。 |
| `backoff_sweep_report`対 | 保持妥当 | 固定図専用ではなく、campaignを探索してcertified viewを読む射影器。 |
| `floor_liveness`対 | 保持妥当 | 投入ごとのreceipt／checkpointを扱う診断器。producerへの依存を、producerからの呼出し証拠とは扱わない。 |
| `mocc_trace_pair_anchor`対 | 保持妥当 | 外部pin・署名等の検証を実装。完了した一回限り処理と結果凍結を確認できない。 |
| `t1994_readonly_snapshot_qualification`対 | 保持妥当 | 残存`test_buildcache_v2.py`がhelperとerrno連言を直接検査する。 |
| `mutation_fanout`対 | 保持妥当 | 「将来直すから」ではなく、一回限り・結果凍結済みという削除条件が未成立。 |
| `verify_paper_story_a1_balanced_sizing`対 | 保持妥当 | 証明書／受領証の検証器であり、testも残存generatorとの共有。source hashの存在だけを保持理由にする必要はない。 |

**消しすぎの反証は未検出。保持11対から追加削除を支持できる対も0。**

## 記録の検算

| 主張 | 検算結果 |
|---|---|
| scope | `947fd160a → 455b03f36`は削除13ファイル＋共有testの4行＋READMEの1行だけ。追加行・scope外変更なし。 |
| 4,337行 | 削除13ファイルのblobから再計算して一致。追随5行を含む総差分は**4,342行削除／15ファイル**。 |
| 96 node | 台帳登録数として**62＋12＋22＝96**。現時点のcollection実測数とは区別する。 |
| 6.349秒 | 台帳値は**2.070＋0.894＋3.385＝6.349 worker秒**。今回の実測時間やwall短縮量ではない。 |
| 0.06% | 旧17ファイル案の11.580秒÷17,958.848秒＝**0.06448075%**として正しい。確定案は**0.03535305%（約0.04%）**。段7へ旧案の割合を転記しないこと。 |
| 残存siteに課す述語を維持 | 支持。検査ロジックは無変更で、exact表のcanary4エントリだけを削除。表の値の合計は6 launchであり、「4行」と区別する。受理集合全体の不変は意味しない。 |
| 台帳はlookup専用 | 収集対象の所要時間参照について支持。`conftest.py:1739`と`acceptance_shards.py:392`は収集済みitemからlookupする。余剰96 entryがtestを復活させることはない。coverage等の別検査まで不存在とは言わない。 |
| 図provenanceのSHAは歴史記録 | 削除前生成器のSHA-256がprovenanceの`034a3721…6139aaa`と一致。生成時のidentityを保持する処置は妥当。現checkoutでの再生成・継続検査が失われる点は記録する。 |
| commit message | 本文の削除数・行数・保持理由は実体と一致。「13 file」はtest3本を含む総数。 |
| 親の実装直接編集 | author unit `8f6aee197`と統合tipの差分はREADMEの1行だけ。提示された履歴・author報告と整合し、親による実装面の追加編集は検出しなかった。 |
| Codex trailer | unit／統合commitとも`product=codex; model=gpt-6-astra; reasoning=medium; role=author`を確認。 |
| 親の実測 | 提示要約は557 passed／8 skipped、provenance 11,883件・新規違反なし。本レビューでは再実行していない。 |

## 変異事前登録への所見

| 変異 | anchor／期待理由の静的判定 |
|---|---|
| m0 | `old`はtipで1箇所。コメント追加のみで、空の期待失敗node集合・SURVIVEDは妥当。実際の注入diff確認は本走で必要。 |
| m2 | `old`は1箇所。存在しないcanaryの期待entryを戻すため、exact inventory比較が拒否する。measurement側はCounter減算で余剰期待値を落とすため、別の赤理由にならない。 |
| m4 | `old`は1箇所。allowlistの不存在検査が先に拒否し、後続のself-runnable検査には到達しない。期待nodeは妥当。 |

F820の単一理由性に静的な反証はない。失敗nodeの完全集合との一致は、未提示の本走結果で確定すること。

「削除moduleを戻す正例」の追加は必須ではない。canaryだけを戻すと、削除済みの期待表との不一致で拒否されるため、SURVIVEDを期待する正例にならない。moduleと対応表を同時に戻すケースは追加の往復確認にはなるが、今回変更した二つの追随箇所について、必須変異の欠落を示すものではない。

変異中の親編集・書込み可能な子の禁止は、cleanなsnapshotやcommit差分だけでは全期間を証明できない。DW-M05の親の自己申告事項として、本走記録で確認する必要がある。本レビューは読取りのみで実施した。

## 総括

must-fix **0件**。scope超過、消しすぎ、追加削除すべき保持対は検出しなかった。  
判定は **条件付きGO**。実装差分は維持してよい。  
変異本走の期待結果・復元・書込み禁止遵守を確認後、段7へ進める。  
段7では実際のstage経路と確定案の数値を記録し、受入全走child-greenを確認してからlandする。