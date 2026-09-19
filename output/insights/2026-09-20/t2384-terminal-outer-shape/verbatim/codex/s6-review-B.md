## 所見一覧

| id | 判定 | 対象 | 所見 | 放置時の成果物影響 1 行 |
|---|---|---|---|---|
| B01 | nit | `focus/focus1.log`、最終 README | ログは 1016 passed を示すが、実行 argv・file 名・nodeid がなく、個別の pin 検査を含むことまでは確認できない。既存の実行記録への参照を添える。 | FC07・reason・receipt・変異台帳への直接影響はないが、pin 閉包の実走証拠をログ単体で追跡できない。 |

## 各所見の根拠

**1. 過剰・削除：scope 超過なし。削除差分は不要。**

`2579b4638` の変更は consumer 23 行、test 96 行の追加だけ。現物は当該 commit と一致し、既存 test の AST はすべて不変だった。

`orchestrator/campaign/reflux_formal_consumer.py:1133` の helper と同 `:1165` の呼出しは裁定どおり。helper の一般化、定数共有、非 terminal の外枠検査、payload key 集合の閉包、docs 変更はない。全 records の走査は terminal 件数を数えるためであり、非 terminal への外枠検査ではない。

D1730 の四項も満たす。

- key 集合・root shadow：exact 5 key により余分な root field を拒否。
- 値の型：variant／env_tag／ts／payload を検査。stage は既存 outcome 別比較（`:1169`、`:1175`）で確定する。
- 重複：root commit／abort の合計を 1 件に限定。既存 stage 比較との積で末尾性も成立する。
- JSON の重複 key は `reflux_origin_artifacts.py:74` の上流検査で拒否される。

payload 型・ts 有限性の述語は、現行経路では拒否能力が重複する。それでも D1665 と同型に保つという `s4-ruling.md` §1・§2 の判断は妥当。削除による受理集合の改善はなく、指定された形だけを崩すため、削除を求めない。

**2. 負例の過剰決定：裁定表との矛盾なし。**

`test_reflux_formal_consumer.py:468` の `_rewrite_wal` は source bytes・projection・参照 hash を整合させる。root attempt がある場合は payload attempt を書き換えないため、`:1682` の shadow 負例も意図どおり残る。

| 負例 | 新 gate を外した場合 | 変異への帰属 |
|---|---|---|
| root shadow、extra key | 既存判定を通り得る | M03、M06 |
| missing key ×3 | 既存判定を通り得る | M06 |
| invalid type ×4 | 既存判定を通り得る | M06、および対応する M04／M07／M08 |
| duplicate abort、commit-before-abort | 末尾 abort の既存判定を通り得る | M05、M06 |
| payload-only stage | 既存の `terminal.get("stage")` 比較でも拒否 | M06 の証拠にはならず、M02 の証拠 |

最後の負例（`:1721`）は過剰決定だが、`s4-ruling.md` §3 は M06 の予測から明示的に除外している。M06 の新規検出予測は 11 node、M02 はそれに payload-only stage を加えた集合となり、整合する。

`_assert_reason`（`:688`）は FC07 に加え receipt／evidence-root 参照がともに `None` であることも検査するため、診断文字列だけの kill にはならない。

**3. 変異の帰属：anchor・累積置換とも問題なし。**

現物を読み、ファイルへ書き込まず文字列の累積置換を確認した。

| 変異 | 各置換直前の `old` 出現数 |
|---|---|
| M01 | 1 |
| M02 | 1、1 |
| M03〜M09 | 各 1 |

M02 の gate 無効化は stage 比較の anchor を消さない。これは `tools/mutation_harness.py:1076` の累積 `count == 1` 契約に一致する。probe spec の root／mutation／replacement の key 集合も同 `:544`、`:567`、`:623` の exact 契約に適合する。

M01 は、**この wave では明示された s4 裁定を採る**。exact keys 通過後は root stage が存在し、`_wal_field`（consumer `:1095`）も root を返すため静的には等価である。DW-M01 の実効 gate への再照準は M02 が担い、M01 は名指しされた旧変異と harness の SURVIVED 観測を確認する限定的な対照となる。`positive` は harness が許す分類だが、受理集合の検出力や過剰拒否検出の実績として数えてはいけない。実走での等価確認には、予定どおり注入 diff と SURVIVED の両方が必要。

登録しない二変異の論証も成立する。

- **payload 型**：root attempt がなければ resolver の `_projection_attempt_id`／attempt 比較（`reflux_result_evidence.py:1573`、`:1636`）で拒否。あれば terminal の exact keys で拒否される。
- **ts 有限性**：projection 自体を読む `strict_json_loads` が再帰的に非有限数を拒否する（`reflux_origin_artifacts.py:33`、`:87`）。指数表記の overflow もこの検査対象。

M09 は許容される有限 float を int 限定へ狭めるため、承認外の過剰拒否を検出する正例として妥当。対応 test は `test_reflux_formal_consumer.py:1755`。

全件 SURVIVED・空 node の登録は DW-M07 の **probe 用**契約に合う。final の KILLED 判定には DW-M08 の失敗 node 完全集合が必要であり、今回その実測結果までは確認していない。

**4. pin 閉包：静的な破損なし。実走の個別包含には B01 の限界がある。**

- `reflux_origin_fixture_baseline.json` は builder 出力の byte length／hash を固定する。builder `:395` の trigger＋abort は不変で、新 gate を満たす。
- `test_reflux_result_evidence.py:40` の golden と `:512` 以降の長さ・hash 検査は builder 出力を対象とする。consumer／test のソース変更は入力 bytes を変えない。
- `test_reflux_formal_consumer.py:2382` の構造検査は production file 15 件と禁止構築・定義を検査する。追加 helper は禁止構築を含まず、目録も不変。
- 変更前後の 2 file の SHA-256／Git blob ID を tracked files で検索し、pin は見つからなかった。行数は consumer 1544→1567、test 2390→2486。指定された検査にこれらの行数固定はない。
- duration ledger に新 node は未登録だが、`tools/acceptance_shards.py:404` が未登録 node に重み 1 秒を与える。登録必須の node 閉包ではない。

B01 の根拠は [focus1.log:18](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2384-terminal-outer-shape/focus/focus1.log:18) と同 `:35`。1016 items／1016 passed は確認できるが、指定 12 file や個別検査名は出力されていない。受入全走ではない旨も明記されている。

**5. 全層 scope：両入力経路に同じ gate が適用される。**

判定順は次のとおり。

`_canonical_wal_interval`（`reflux_result_evidence.py:1580`）
→ canonical-list、または `parse_line` による frame 射影
→ projection records との canonical bytes 一致（`:1640`）
→ `ResolvedOrderedWal.records`
→ evidence／binding／bijection／topology 検査
→ `_validate_wal_outcomes`（consumer `:1471`）
→ 新 gate（`:1165`）。

frame の外枠は `wal.py:364` の `parse_line` が検査するが、projection 全体の terminal 件数はそこで検査しない。新 gate の件数検査は frame 経路にも効く。

新 test は `_rewrite_wal` が canonical-list bytes を生成するため、frame 経路の実走証拠ではない。**最終 README にはこの限界を書くべき**であり、`s4-ruling.md:12` とも一致する。今回の実装へ frame test を追加する要求までは不要。

**6. 記録の正確さ：実装との矛盾は認めない。**

`s5-author.md` の受理・拒否の説明、fixture 形状、構造検査、duration ledger の説明は整合する。p3 の source bytes 保持（`test_p3_autonomous_workload_trial.py:10722`）と、issuer の二重 abort が `result_evidence_context=None` の経路であること（`test_reflux_campaign_issuer.py:1250`）も確認した。

author の「未実走」は author 時点の報告であり、後続の親による焦点走と矛盾しない。commit 本文も追加 gate、負例 12／正例 2 node、既存判定不変という実装内容に一致する。「12 file」の実走裏取りだけは B01 の留保が残る。

## 総括

must-fix 0 件、should 0 件、nit 1 件。
最重要の留保は、焦点走ログ単体では個別 pin 検査の包含を確認できないこと。
実装レビューは **GO**。scope 超過・四項の取りこぼし・anchor 衝突は認めない。
pytest は未実行。変異 final と受入全走の完了は、このレビューでは認定しない。
