## 所見

**B-1 — must-fix：science-slice の削除は、項 5 優先と断定できない。**  
対象：`s1-brief.md:51`、`s2-plan.md:172–180`、`docs/decisions.md:68594–68616`。  
項 5 は候補 15 対の条件付き削除であり、項 6 の維持指定を上書きしていない。`test_t1434_t1222_science_slice.py:409–442` は実際に `inventory/list-D.txt:283` に載る。plan の留保は妥当。段 4 では、重複指定を解消できなければ module/test の 1 対を残すべきである。  
**DW-G05：放置すると、維持指定された外部 jobs 集合の exact pin が受入から消える。**

**B-2 — should：保持の結論と「現行機構である」という証明を分ける。**  
対象：`s1-brief.md:27–37`、`s2-plan.md:155–166`。  
「事前登録に義務が書かれている」「現行 producer を読む」「見送り台帳にある」だけでは、その tool が現在必要とは証明できない。ただし、それを反証しても削除の 3 条件が揃うわけではない。特に fanout は「将来直すから保持」ではなく、**完了した一回限り処理・凍結済み結果という分類が成立しないため保持**と書くべき。  
**DW-G05：放置すると、保持根拠が広すぎる前例となり、次回棚卸しでも歴史的参照だけで保守対象が残る。**

**B-3 — should：「残る test の受理集合は不変」は撤回する。**  
対象：`s1-brief.md:47,58`、`s2-plan.md:194`、`test_ccbench_spawn_sites.py:2840–2847`。  
残る exact inventory test 自体の期待集合が変わる。焦点走の緑も、変更前後の受理集合の同一性を証明しない。plan の「残存 site に課す述語を維持する」という訂正を brief に反映する。  
**DW-G05：放置すると、共有 gate の受理集合変更を成果物記録が過小申告する。**

**B-4 — nit：削除量の単位を統一する。**  
対象：`s1-brief.md:57,65`、`s2-plan.md:59–106`。  
正しくは共有表 **6 エントリ行＋付属コメント 2 行**。spawn 側の launch 数が 7 なのであって、pin 行が 7 ではない。README は別に 1 行。plan が既に訂正している。  
**DW-G05：実際の受理集合への追加影響はないが、author の所有範囲と差分検収の基準が食い違う。**

## 残す 9 対の反証表

以下の「残す」は、将来の永久保持を意味しない。今回の条件付き削除に必要な確認が成立するかで判定した。

| module | 判定・反証結果 |
|---|---|
| `backoff_counterfactual_analysis.py` | **残す。親の理由は限定が必要。** `:3` は固定 cohort 専用であり、事前登録 `:345–352` の義務だけなら「解析終了後も保存必須」とは読めない。しかし現物 `:582–598` は文書・seed の契約を実装し、T-2586 README `:212–216` でも producer／文書／consumer の整合対象である。「現行機構でない」の確認が足りず、追加削除には進めない。 |
| `backoff_counterfactual_cohort2_analysis.py` | **残す。** 固定 cohort 用という反論は成立するが、`test_t2187_adaptive_const_probe.py:24–26,1974–1980` が現在の probe の seed 集合をこの module と照合する。削除には専用 test 以外の契約検査も失う判断が必要。単なる解析結果の保存とは異なる。 |
| `backoff_nonmonotonicity_analysis.py` | **残す。ただし「現在の常用 library」とまでは言えない。** T-2583 README `:380–386` は 6 関数の再利用と、probe が使い捨てだったことの両方を明記する。T-2635 でも別解析に再利用されており、一回だけの処理だったという分類は成立しない。履歴上の再利用だけで永久保持する一般則にはしない。 |
| `backoff_sweep_report.py` | **残す。** `:53–66` は特定の凍結 JSON ではなく、campaign を探索し certified view と digest を読む射影器。T-2702 README `:50–53,93` と整合する。過去に図を一度出したことだけをもって、完了した一回限り tool に再分類できない。 |
| `floor_liveness.py` | **残す。** `:20` の import は reader → checkpoint producer であり、floor driver がこの reader を呼ぶ証拠ではない。この点は plan の訂正が正しい。一方 `:477–655,682–811` は投入ごとの receipt／checkpoint／journal を扱う診断器で、固定した一回の結果を生成して完了した tool ではない。 |
| `mocc_trace_pair_anchor.py` | **残す。** D1110 に似た実装があることだけで利用実績は証明できない。しかし `:342–403,513–574,577–670` は任意の対象 receipt に対する外部 pin 検証を実装する。成果物が見つからないなら、それは「結果凍結済み」の証拠にもならない。今回の削除条件は満たせない。 |
| `t1994_readonly_snapshot_qualification.py` | **残す。ただし production 機構そのものとの表現は強すぎる。** `:1,10–11` は一回限り qualification／既存機構の観測器と明記するため、親の説明への反証は成立する。それでも `:716–722` の連言を `test_buildcache_v2.py:5787–5823` が直接検査し、`:5627–5657` は実 session の保護検査に helper を再利用する。削除は専用 probe/test の撤去だけでは収まらない。 |
| `tools/mutation_fanout.py` | **残す。保持理由を修正。** T-1177 は `docs/phase3.md:1997–1998` で active から除外されており、再実装予定を保持理由にするのは不適切。ただし現物 `:401–418` は D433 の実行不能条件を保持し、完了した一回限り作業の tool とは確認できない。契約 module への依存方向も driver → contract である。 |
| `tools/verify_paper_story_a1_balanced_sizing.py` | **残す。hash 束縛だけを理由にしない。** 事前登録 `:286–291` の source hash は、それ単独なら削除対象の図 provenance と同種の歴史記録にもなる。一方 `:711–772` は証明書・再現受領証の検証機構で、`test_paper_story_a1_balanced_sizing.py:21–22` は残す generator と verifier の共有 test。完了した使い捨て検証器としての対削除は確認できない。 |

**追加削除を支持できる対は 0。** 保持理由に弱い部分はあるが、それを削除許可へ読み替えることもできない。

## 過剰・副作用・変異案への所見

**削除の追随**

- `test_ccbench_spawn_sites.py:73–74`：削除 site 専用の説明。残すと次の pipeline 行へ誤接続するため、コメント 2 行の削除は必要な追随。一般的なコメント整理へ広げない。
- `orchestrator/tests/README.md:138`：削除必須。`test_plain_runner_coverage.py:81–83` が不存在の allowlist entry を拒否する。親の統合時に必ず揃える。
- 新 gate、互換層、台帳形式、helper 統合の追加は plan にない。既存検査の実行や今回の結果記録は、新しい検査機構の導入とは異なる。

**副作用**

| 対象 | 判断 |
|---|---|
| `patches/silo-backoff-requested-us.patch` | **保持が正しい。** `condition_meaning_gate.py:143–146` と `test_ccbench_spawn_sites.py:2885–2898` が現在も扱う。driver 不在を理由に patch／registry まで削るのは scope 拡張。 |
| 受入所要台帳の stale 162 entry | **保持が正しい。** `conftest.py:1739–1758`、`acceptance_shards.py:392–404` は収集対象から lookup する。余剰 entry を消す必要はない。ただし coverage は別途確認する。 |
| 図 provenance の生成器 SHA | **保持が正しい。** 生成時の source identity を現在の checkout に合わせて変更してはならない。生成器撤去による現 checkout での再生成不可は結果記録に明記すれば足りる。 |
| T-1941 `job-body.sh:383` | **保持が正しい。** 実呼出しが残るため「参照ゼロ」は誤りだが、凍結された歴史 script の書換えや互換 stub は不要。関連専用 test の撤去により、この script の継続検査も消える点は記録する。 |

**変異の単一理由性**

| 案 | 静的判定 |
|---|---|
| M1 | 妥当。`:2847` の exact Counter 比較で消滅 site が余る。`:4101–4106` の measurement 検査は Counter 減算で非正値を落とすため、この余剰期待 entry だけでは赤にならない。 |
| M2 | 妥当。export_stock の 1 entry／値 3 に限定すれば exact inventory の同じ理由で赤。M1 と異なる gate の証拠ではなく、別の追随表区分の確認である。 |
| M3 | 妥当。`MACHINE_CALLERS` の巡回 `:1211–1212` で当該 file の読取りが失敗する。他の削除を stage 済みにして、tracked-source 検査の失敗を混ぜないこと。 |
| M4 | 妥当。`:83` の stale entry 検査が先に拒否する。後続の self-runnable 検査へ到達しないが、それは狙った理由そのもの。 |
| M5 | **別観測として妥当。単一の受入実行で二つを証明することはできない。** targeted run では `run_tests.py:787–788` が削除 preflight を適用せず、AST scan `:667` に到達する。受入実行では preflight の rc=13 が先に返り、pytest node は実行されない。 |

M5 は targeted node の実行と受入入口の実行を別々に記録し、rc=13 を pytest の KILLED に数えない。削除後 commit を変異 baseline にするなら、作業木で file を消すだけでは未 stage 削除にならないため、**index に削除前 blob が残る状態**を実際に作ったことも確認する。新しい gate は不要。

段構成は author 1 本＋敵対 review 2 本＋局所変異＋受入全走で足りる。fix 子は所見発生時だけでよく、追加 consult は不要。plan が加えた閉包／import invariant の既存検査は妥当。

## 親 brief / plan の実測値への所見

本段は静的確認のみで、pytest 緑や変異 KILLED は報告しない。

- **「R6 相乗りの発火なし」：支持。** 棚卸し README `:315` の対象 5 組と削除・追随 file は交差しない。`plot_t2266_tail_mechanism.py` の重複 helper は C87 にあるが、指定された R6 の 3 作図組には含まれない。
- **「p3_b4 閉包 47 に触れない」：静的再計算で支持。** 現物の root 定義・catalog・依存抽出関数を使って読取り専用で閉包を再計算し、**47 module、削除 campaign module との交差 0** を得た。manual probe／tools はこの catalog 外。
- **「残る test の受理集合は不変」：不支持。** B-3 のとおり。残存 site に対する述語を維持する、という限定なら妥当。
- **「R2／R4／R5／R7 に触れない」：実装変更の意味では支持。** 指定された保持 module や helper の統合はない。ただし「触れない」を、重複表との path 交差までゼロという意味に広げてはいけない。削除対象には C87、C91、C117 の member がある。片側の module 削除と、見送りになった helper 統合は別の操作である。
- **台帳値：再計算で一致。** 総数 24,379。削除候補 5 test は順に **36／62／12／22／30 entry、合計 162、11.580 worker 秒**。science-slice を保持すると **132 entry、10.341 秒**。これは現 HEAD の collection 数や wall 短縮の実測ではない。
- **coverage：plan の留保が正しい。** `test_acceptance_schedule_order.py:704–715` の分母は収集 rows。stale entry の存在だけでは赤にならないが、削除後の 90% 合格を台帳件数だけで断定できない。

## 総括

must-fix は **1 件**：science-slice の項 5／項 6 の重複指定を解消せず削除しないこと。  
残す 9 対から削除集合を広げる根拠は **0 対**。未解決なら既存削除候補を **1 対狭める**。  
コメント 2 行・README 1 行は必要な追随。patch・台帳・凍結参照の保持は妥当。  
段 4 への判定は **条件付き GO**。P1 の留保を維持し、保持理由と受理集合の記述を訂正して渡す。