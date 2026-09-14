## 検査 1 — 既存 assert の保存

変更前 `7dc4ecc39` と変更後を AST で比較した。既存230 test 関数すべてで assert の列が一致し、対象 test 内の20 assert も保存されている。

`test_p3_autonomous_workload_trial.py:1850` は `report["cells"][0]` をコピーせず返す。producer の `:3799` 以降も通常の dict と cells を組み立てて返している。helper 呼出しから既存の2利用箇所（`:1929`、`:1939`）までに先頭 cell を差し替える処理はない。**両箇所が参照するオブジェクトは変更前と同一。**

partial 時は追加 assert で早期停止するため後続 assert の実行回数は減るが、その走は既に赤であり、既存防壁の弱化ではない。

## 検査 2 — test 関数名集合の差

静的比較結果：

- 変更前：230関数
- 変更後：231関数
- 削除・改名：0件
- 追加：`test_role_sink_report_complete_rejects_partial_reports` の1件のみ

## 検査 3 — 受理集合

既存の赤を緑にする経路は発見しなかった。対象 node の受理条件は、既存条件に各 report の `status == "complete"` を加えたものになる。

ただし、実 producer における旧版との受理集合差は未実証。指定された二つの負例は旧 node の他の条件も満たさないため、それだけでは縮小の証拠にならない。M5／M5′ の親の実測が必要。

## 検査 4 — D1847 との整合

差分は対象 test file のみ。32反復、固定並行度4、順序保存の `executor.map`、main thread での集約、件数・横断 assert は維持されている。

skip／xfail、動的並行度、production、`contract_loader_binding` の cache、既存 admission 経路への変更はない。

## 検査 5 — 波及と meta-test

実体を読んだ結果、新規 node が既存 golden の更新を必要とする条件は見つからなかった。

- `conftest.py:2123`：real-repo 分類は node 名の登録集合で決まる。新規 node は未登録で、module／関数の group marker もない。
- `test_real_repo_serialization.py:1259,1320,1427,1581`：pin 対象は group 名・分類集合・共有 fixture の consumer 閉包。新規 node は `tmp_path` のみを要求し、対象 module に共有 fixture の追加もない。組込み fixture は収集 plugin の `:958` 付近で閉包対象から除外される。
- `test_acceptance_schedule_order.py:698`：全収集数の固定値ではなく、収集結果同士の整合と台帳被覆率90%以上を検査する。新規未登録 node により分母が1増える。閾値直前なら赤になるため、最新被覆率は親の焦点走で確認が必要。
- `conftest.py:1661,1741`：未登録 node は unknown cost で並べ替えられる。台帳未登録による除外はない。
- `test_pytest_collection_config.py:423`：動的列挙は file 名と除外表を検査する。既存 file 内の node 追加では集合が変わらない。

親の4対象以外では、`test_p3_build_authority_cli.py:643::test_tracked_python_coder_authority_ast_closure_is_exact` が対象 file を動的に読む。ただし pin は authority 発行 call の集合であり、今回の追加はその集合を変えない。`test_update_acceptance_duration_ledger.py:306,329` も確認したが、台帳の内部整合・別 wave の指定 entry が対象で、今回の収集増分は pin していない。

## 検査 6 — 費用

**要検証・費用所見** — `test_p3_autonomous_workload_trial.py:2016,2046`。

既存同型 node の台帳値は critic 欠落が0.099秒、invalid planner が0.11秒。二走を足す今回の暫定見積りは **約0.2秒／node**。fixture 費用の重複などが違うため単純加算は実測値ではない。

具体シナリオは、受入全走で新規 node が二つの trial を逐次生成する場合。**影響は直列実行時間の増加と未登録 node 1件の増加**であり、無料ではない。real-repo 共有直列 group の増加は見つからない。

二走には fatal あり／なしの判別という別の役割がある。一方、段4 `:36` の「1 node に収める＝直列 work を増やさない」という説明は成立しない。node 数を抑えても trial 二走の費用は残る。

## 検査 7 — scope 境界と言語規律

プランv2の実装範囲からの逸脱は見つからなかった。partial 成立条件は `pytest.raises` の外で、捕捉対象は helper 呼出しだけになっている。

**real・nit** — [test_p3_autonomous_workload_trial.py:2007](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2497-role-sink-status/orchestrator/tests/test_p3_autonomous_workload_trial.py:2007)。

新規 docstring が英語。隣接する対象 test の日本語説明と、依頼で指定された言語規律に揃っていない。日本語で保守説明を読む場面で不統一になる。**成果物の値・受理集合・参照への影響はない。**

## 検査 8 — 段 4 裁定への攻撃

**real・nit（保証の過大表現）** — [stage4-ruling.md:44](/home/SFC/tanab/.claude/jobs/a196dbeb/tmp/t2497/stage4-ruling.md:44)。

「2形あれば原因によらず complete 以外を拒否する性質が機械で守られる」は反証できる。例えば `supervisor-wall-budget` の partial だけを受理する弱化なら、現在の二形は両方拒否でき、負例は通る。**現在の実装の受理集合は変わらないが、検証報告が保証する範囲を過大にする。**新しい検査の追加ではなく、説明を二形と登録変異の範囲に限定すべき。

**real・nit（是正効果の限界）** — 同 `:24`。

helper 呼出し削除を `NameError` にする是正は、意味のある status 検査への接続というより、戻り値への構文的依存を作るもの。call と参照2箇所を一緒に戻せば回避できる。helper 名から cell を返す契約も読み取りにくくなる。**単独削除への耐性は増えるが、協調した弱化への受理集合は守らない。**2参照の変更だけなので重大な構造破壊とは言えず、must-fix にはしない。

裁定表の「接続削除を負例が検出できない」「fatal 部分集合への弱化が生存する」という所見自体は refuted ではない。反証できたのは是正後の保証範囲と費用説明である。

なお同 `:84` の `.get()` に関する理由も不正確。`report.get("status") == "complete"` なら欠落は依然拒否する。現行コードを変更する必要はないが、拒否集合が広がることを不採用理由にはできない。

## 総括

**must-fix：静的検査では発見なし。** 既存 assert・test 名・cell 参照の保存を確認した。

nit は英語 docstring、裁定の保証範囲・費用説明。新規 node の所要と最新台帳被覆率、旧版との差分変異は親の実測待ち。**本レビューでテストは実行しておらず、緑とは報告しない。**