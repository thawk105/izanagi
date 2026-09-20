## 所見

**must-fix は0件です。** HEAD は `455b03f36`、作業木は clean。削除13 fileと共有 test 4行・README 1行の変更は、s4 plan v2 と完全一致しました。レビューでは pytest を実行していません。

- **RB-1 — should**  
  **対象:** 点検項目3／`orchestrator/tests/test_acceptance_schedule_order.py:704–712`  
  「台帳 coverage が削除後に下がる方向でない」は成立しません。被覆済み96 nodeを除くため、削除前が100%未満なら比率は低下します。ただし、低下と90%閾値割れは別であり、提示された焦点走は合格しています。段7では「stale entry は無害、coverage は低下方向だが実走で閾値を維持」と記録してください。  
  **DW-G05:** 放置すると実装・台帳は変わりませんが、受入 coverage の説明が逆になります。

- **RB-2 — nit**  
  **対象:** s4「不変条件／DW-O11」、author報告「変更」、統合手順の記録  
  s4 は author の `git rm` を指定していますが、author報告は未stage削除です。最終状態は削除がcommit済みで、`git ls-files --deleted` も空でした。依頼に記載された親の `git apply --index` による統合は、受入前にstageする目的を満たします。段7には実際の分担を書けば十分です。  
  **DW-G05:** 放置しても受入集合は変わりませんが、削除を誰がいつstageしたかの手順記録が不正確になります。

## gate 追随の全列挙表

以下の行番号は削除後の tree に基づきます。「焦点内」は指定7 fileに含まれる検査です。

| gate／対象 | 現物確認・削除後の状態 | 焦点走 |
|---|---|---|
| spawn-site exact 表：`test_ccbench_spawn_sites.py:89,2836` | canary 4キーだけ削除済み。削除13 fileへの残存登録なし | 内 |
| measurement 分類：同 `:4096,4144` | 同じ表をCounter減算に使用。追随済み | 内 |
| `MACHINE_CALLERS`：`test_p3_build_authority_cli.py:1210` | 削除対象なし。保持する requested-us の登録は維持 | 内 |
| tracked Python AST閉包：同 `:649–667` | index由来の走査。削除13 fileはcommit済みで読取対象から除外 | 内 |
| materializer registry：`materializer_admission.py:52`、上記test `:1224,1244` | 削除対象の登録なし。manual-build集合・registry射影の変更不要 | 内 |
| materializer全走査：`test_s8b_floor_campaign.py:8014` | campaign再帰走査とregistryのexact照合。削除対象の固定登録なし | **外** |
| 静的import閉包47：`test_p3_b4_wiring_probe.py:324`、`p3_b4_wiring_probe.py:1083` | 指定rootからの依存閉包。削除対象への参照なし。47 pin変更不要 | 内 |
| import例外台帳：`test_campaign_import_invariant.py:1222–1286` | 削除対象の例外entryなし | 内 |
| README allowlist：`test_plain_runner_coverage.py:49–93` | insights testの1行削除済み。他の削除testへの参照なし | 内 |
| READMEの他一覧・skip分類 | README全体に削除対象なし。`test_skip_classification.py` の参照先にも削除対象なし | **外** |
| 台帳lookup：`conftest.py:1584,1739` | schema内部整合を検査し、収集itemからlookup。余剰96キーは使用しない | 内 |
| 台帳coverage：`test_acceptance_schedule_order.py:660` | 実collectionとの被覆率を検査。stale禁止ではない | 内 |
| 台帳schema／固定差分：`test_update_acceptance_duration_ledger.py:306,329` | schema・有限値と別suiteの固定集合を検査。今回の96キー削除は要求しない | **外** |
| shard割当：`tools/acceptance_shards.py:392–404` | 収集record起点のlookup。削除済みnodeを台帳から復活させない | **外** |
| 未stage削除：`tools/run_tests.py:784–819` | 全受入時だけ発火。現在の未stage削除は0件 | **外：焦点走は対象外** |
| hooks／`.claude`／`.codex` の設定・allowlist | path・stem検索で削除対象の登録なし | **外** |
| `tools/pegasus/admission_registry.json` | 削除対象の登録なし。関連検査は `test_check_docs.py`、`test_hooks.py` 等 | **外** |
| living docs実在検査：`tools/check_docs.py:129,6767` | livingな参照に削除対象なし。残存hitは歴史記録・保持指定台帳 | **外：親が別途確認済み** |
| provenance：`docs/ai-provenance.md` | trailer形式とCodex author契約に適合 | **外：親の全史監査済み** |

削除集合は次の13 fileで過不足ありません。

- `orchestrator/campaign/`：`p2_5.py`、`s6_amendment_20260713_fence.py`、`s6_canary_rename.py`
- `orchestrator/manual_probes/`：`t1994_capdrop_probe.py`、`t1994_readonly_snapshot_liveness.py`、`t1994_rootview_probe.py`、`t1994_seccomp_probe.py`
- `tools/insights_date_layout.py`、`tools/migrate_output_gzip.py`、`tools/plotting/plot_t2266_tail_mechanism.py`
- `orchestrator/tests/`：上記toolsに対応する3 test file

## 受入の赤の予想

**削除に起因する具体的な赤は見つかりませんでした。** 残存test・fixture・設定・dataをpath／stemで検索し、実在を要求する参照の取り残しは検出していません。台帳の96件と歴史記録は保持指定どおりです。

焦点外で注意した箇所は、materializer全走査 `test_s8b_floor_campaign.py:8014`、台帳検査 `test_update_acceptance_duration_ledger.py:306,329`、受入入口 `tools/run_tests.py:784` です。いずれも今回の削除による不整合は認めません。

台帳coverageは、削除前の収集数を \(N\)、被覆数を \(C\)、削除する被覆済みnodeを96とすると、

\[
\frac{C-96}{N-96}-\frac{C}{N}
=\frac{96(C-N)}{N(N-96)}\leq0
\]

です。90%維持条件は \(C-0.9N\geq9.6\)。提示された焦点走は **557 passed / 8 skipped** ですが、要約にはcoverageの分子・分母がないため、正確な余裕幅は報告できません。全受入の合格はまだ未確認です。

## 変異事前登録への所見

| 変異 | anchor／置換内容 | 期待する失敗集合の静的確認 |
|---|---|---|
| m0 | `old` は1箇所。コメント追加前後のASTは同一 | `SURVIVED`、空集合で整合 |
| m2 | `old` は1箇所。消滅した `export_stock` のCounter値3だけ復元 | `test_reviewed_process_launch_inventory_is_recursive_and_exact` の1 node |
| m4 | `old` は1箇所。allowlist内に不在testを1件復元 | `test_allowlist_has_no_stale_or_self_runnable_entries` の1 node |

m2の表の参照先はexact比較とCounter減算2箇所です。`:4099` と `:4144` の減算では消滅siteの非正値が落ちるため、追加の赤を生みません。m4では`:83`のstale検査だけが拒否し、他の2 testには失敗条件を追加しません。**指定runner内のF33期待集合は静的に整合しています。**

期待nodeはいずれも指定2 file内のトップレベル `test_*` 関数で、parametrize・skip decoratorはありません。収集対象として整合していますが、実collection・変異結果は本レビューでは確認していません。

数値と来歴も整合しています。

- briefの17 file／8,623行／162 nodeから、保持した2対を除き、s4の**13 file／4,337行／96 node**になります。
- 台帳秒は実物から **2.070＋0.894＋3.385＝6.349 worker秒**。wall短縮量ではありません。
- authorの **4,341 deletions＝4,337＋pin 4**、統合commitの **4,342＝4,341＋README 1** と記録できます。
- 保持理由はs4・commitに反映済み。briefのprovisional判断はs4で更新されたものとして扱えます。
- unit commit `8f6aee197` と統合tipの実装面差分は空。親の追加変更はREADMEのみで、実装面を直接修正した形跡はありません。
- trailerは最終連続blockにあり、Codex author行は実装寄与と対応します。`git apply --index` の実行そのものは提示情報に依拠し、最終stage状態は独立確認しました。

## 総括

must-fix **0件**。削除集合・追随・変異期待集合・provenanceに実装上の不整合は見つかりません。  
判定は **条件付き GO**：この差分のまま段7へ進めてよいです。  
段7ではcoverageの低下方向と実際のstage分担を正確に記録してください。  
変異本走の期待集合一致と受入全走の合格を確認してからlandしてください。