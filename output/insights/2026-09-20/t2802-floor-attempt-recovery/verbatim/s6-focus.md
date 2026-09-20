## 所見表

**NO-GO：A-M1 の系列順序検査が partial です。** pytest・測定は実行せず、静的検査、提供された実測資料の検算、集計ロジックの書込みなし合成検算を行いました。新たな regression は確認していません。

以下、`J`＝[job dir](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2802-floor-attempt-recovery)、`P`＝その `probe/`、`T`＝[admission test](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2802-floor-attempt-recovery/orchestrator/tests/test_s8b_holdout_admission.py)、`H`＝[production module](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2802-floor-attempt-recovery/orchestrator/campaign/s8b_holdout_admission.py) とします。

| 所見 | 判定 | 根拠 | 残作業 |
|---|---|---|---|
| A-M1 | **partial** | `P/t2802_ab_analyze.py:250–287` は隣接対を作るが、slot/order 違反を対の `reason` に記すだけ。`:296–301` は残った有効対で肯定判定できる。下記反例を確認。既存 selftest PASS は `J/probe/selftest-analyze-3.log:8` | 順序違反を系列違反として拒否する負例を追加。正規の取り直し・投入途中の片走は維持 |
| A-M2 | **closed** | 分類検査は集計器`:186–196,288–295`、再開は `run-series.sh:31–54`、上限・固定終了は `run-measure.sh:40–69`。selftest log`:8–9`。正常系列の1〜6走時点も合成検算で停止条件に誤分類されなかった | A-M1 の順序違反は別途修正 |
| A-M3 | **closed** | `run-warm.sh:39–64` の前後状態・dispatch 証跡と、集計器`:199–220` の検査。selftest`:460–474`、log`:8`。抽出文字列は焦点走2 log`:4` の実形式と一致 | warm 本走の成功は未証明。測定前に実施 |
| A-M4/B-MF1 | **closed** | fix patch 第1 hunk、patch`:173–209`、T`:3000–3055`。明示的13 field 辞書に変更。焦点走2 log`:20` の293 passed | 下記の独立性の射程を維持 |
| A-S1 | **closed** | patch 第2 hunk`:217–223`、T`:3116–3120`。9→7 case。焦点走2 log`:20` | なし |
| A-S2 | **closed** | patch 第1 hunk`:9–170`、T`:2842–2997`。6＋3＋2＋2 case追加。焦点走2 log`:20` | 裁定が採用した代表例の範囲ではなし |
| B-MF2 | **closed** | 正例 log`:3–8` は M1 実変異と rc=1。正例 JSON`:1781–1788` は24状態中2不一致。production は正例実施HEADと現HEADで同一 SHA-256 | 9変異全体の実測とは分ける |
| B-S1 | **closed** | 差分 probe`:261–372`。run2 JSON`:1755–3069` に2×2、非target coverage、再呼出し、legacy v1/v2 の追加16状態。原データから40/40一致を確認 | なし |
| B-S2 | **partial** | author報告`:185` と T`:3213–3226` は「2回目の読取回数」が改竄より先。root-key 化は spec`:105–122` | 変異実測後、最初の失敗位置と帰属を台帳へ記録 |
| B-N1 | **partial** | H`:5339` は呼出しローカル。裁定`:16` は文言修正を採用。ただし修正済み insight は提示資料にない | insight への反映を確認 |
| A nit | **partial** | 集計器`:304–326` で Markdown を縮約、selftest`:476–479` と log`:8–9` が裏付け。consumer log`:23` は全体集計のみ | file/node 別 summary は A/B 成果物待ち |

**A-M1 の残反例：** 全走を正常・非重複時刻・同一環境とし、`A1,B2,A1,B1,B2,A2,A3,B3` を渡すと、先頭の slot 違反対だけが除外され、`valid_pairs=3`、`series_invalid=[]`、`direction-consistent-above-threshold` になりました。これは infra 分類済みの同slot・同順序の取り直しではありません。[該当処理](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2802-floor-attempt-recovery/probe/t2802_ab_analyze.py:269)

一方、正常系列の途中状態、分類済みの赤を含む対の取り直し、先頭走が赤だった場合の取り直しは通ります。指定された三つの regression 候補――正常系列の停止、正規再試行の誤拒否、dispatch 行の抽出失敗――は確認されませんでした。

## N1 の独立性

[期待辞書](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2802-floor-attempt-recovery/orchestrator/tests/test_s8b_holdout_admission.py:3020) は13 keyを明示し、`_floor_expected_marker`、`_floor_attempt_document_for_state`、文書 constructor を期待値生成に使っていません。fix報告`:24–36` の出所表とも全項目が一致します。

| field | 現物の出所 |
|---|---|
| `schema_version` | 固定 literal |
| `event` | `"consume"` |
| `observation_role` | `"floor_campaign"` |
| `cell_effect_digest` | 発行済み claim の JSON 読取 |
| `measurement_generation_digest` | reservation の公開 field |
| `measurement_generation_claim_digest` | token の公開 field |
| `attempt_id` | fixture の cell ID＋schedule の seq |
| `campaign_run_id` | reservation に渡した `"run-a"` |
| `manifest_sha256` | fixture が書いた manifest bytes の SHA-256 |
| `run_relpath` | protocol の env_tag＋同じ run ID |
| `cell_id` | protocol/freeze から列挙した cell |
| `freeze_holdout_key` | 同 cell |
| `configuration_id` | 同 cell |

ただし、**digest 算法まで独立した oracle ではありません。** 発行側の H`:1691–1696` と constructor の H`:4576–4579` は `_measurement_generation_claim_digest` を共有します。`cell_effect_digest` の生成・projection検証も `_claim_digest` を共有します。期待辞書自体はこれらを呼ばず発行済み値を読むため、裁定の constructor 非依存要件は満たしますが、共通digest helperの誤りまで検出できるとは主張できません。

## 派生値の検算

| 親の数値 | 独立検算 |
|---|---|
| 焦点走2：293 passed | **一致**。[log:20](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2802-floor-attempt-recovery/focus/focus2-admission-fix1.log:20)。child rc=0 は`:10` |
| 新規99→97→110 case | **一致**。元10群＝`1+4+3+9+9+2+3+8+24+36=99`。N4を−2、新規4群を`6+3+2+2=13`追加 |
| 差分 probe：40状態全一致 | **一致**。40状態それぞれの両順序について戻り値／例外・message・root不変を再比較。40一致、0不一致。JSON`:3071–3073`とも一致 |
| 正例：2状態不一致 | **一致**。24状態中22一致。`e-later-nontarget-marker-campaign_run_id` は変異側の誤受理、`f-later-A-campaign_run_id` は拒否messageの変化 |
| 集計器 selftest PASS | **一致**。[log:8–9](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2802-floor-attempt-recovery/probe/selftest-analyze-3.log:8)。ただし A-M1 の上記反例は未検査 |
| consumer：2522 passed / 16 skipped | **一致**。focus1 log`:23`。fix前の全体集計であり、file/node 別性能値ではない |

指定された数値の食い違いはありません。別件として、`SHA256SUMS.txt:1` の自己ハッシュは空ファイルの値で不一致です。**対象5 script のハッシュはすべて一致**しました。

## 変異 spec

9変異・計10置換の `old` は現productionで各1回だけ一致し、独立適用後の構文解析も通りました。author anchor表`:164–172`、裁定§5、レビューBの案と狙いは整合します。

| 変異 | 判定 |
|---|---|
| M1 | 登録前の `memo_key in context.projections` で判定するため **hit限定**。missを弱めない。先行shape検査により、B案の添字アクセスとspecの `.get()` の差もここでは問題なし |
| M3 | generation のhit membershipだけを無効化 |
| M4 | canonical filename比較だけを無効化 |
| M5 | A identity重複拒否だけを無効化 |
| M6g / M6v | 対応するmain equalityだけを無効化 |
| M7 | completed拒否だけを無効化。既存検出力 |
| M8 | module dictをrootで分離。同一root内の呼出し間保持を起こし、異なるfixture rootのtest順序による混入を避ける。`setdefault` の引数生成は既存contextを置換しない |
| P0 | canonical成功後のidentityは文字列なので、`str()`除去は対象契約内で等価 |

**DW-M08 適合は条件付きです。** 全件 `SURVIVED`期待・node空という形式は初回probe用として一致します。しかし、[裁定:72](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2802-floor-attempt-recovery/s4-ruling.md:72) が要求する「消費testのparametrize完全集合を静的に確定できない」理由は、提示spec・報告には明示されていません。110 caseを数えられることと、各変異で失敗するnodeの完全集合を確定できることは別です。初回probe前に未確定対象と理由を記録し、probe後は実測に基づくfinal specへ移す必要があります。

## 総括

**NO-GO。**
残must-fix：A-M1――slot/order違反を除外して後続3対から肯定判定できる処理を修正する。
初回変異probeの前提：DW-M08の「静的確定不能」の対象・理由を記録する。
productionの新たな受理集合差、指定の三つのregression候補、親の数値の誤算は確認されませんでした。