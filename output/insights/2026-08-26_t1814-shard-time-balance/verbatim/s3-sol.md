[severity: must-fix]  
[攻撃シナリオ] 現物台帳は 15,909 nodeid、現行受入集合は 17,160 node。少なくとも 1,251 node が欠けるため、plan の「1 件でも未知なら全体を count fallback」は毎回発火し、duration allocator は実環境で一度も有効にならない。新規 node の追加でも同じ状態が再発する。  
[根拠 anchors.md:17; anchors.md:64; artifacts/s2-plan.md:24-30; artifacts/s2-plan.md:48-52; orchestrator/tests/test_acceptance_schedule_order.py:703-713]  
[提案] 「台帳を再生成しない」を維持するなら実装しない。再検討時は台帳更新・退役/new-node lifecycle と、現物 collection で duration mode が実際に発火する positive control を scope に入れる。

[severity: must-fix]  
[攻撃シナリオ] K=3、単一 node の成分 A/B/C に対し、3 controller が file 置換窓で降順 A,C,B／C,B,A／B,A,C の異なる完全台帳を読む。各 controller の shard 0/1/2 は A/B/C を選び、混成結果の union・重複なし・file/group closure・全 report evidence がすべて通るが、共通の割付は存在しない。K=2 の差異は通常 `selected-partition` が落とす一方、この K=3 例では exact 述語は一つも破れない。  
[根拠 artifacts/s2-plan.md:10-14; orchestrator/tests/conftest.py:885-907; tools/acceptance_shards.py:61-66; tools/acceptance_shards.py:455-537; tools/acceptance_shards.py:592-607]  
[提案] report schema に全 Assignment または ledger snapshot の digest を追加し、merge で全 shard の exact 一致を要求する。異なる snapshot を与える K=3 killer も追加する。

[severity: must-fix]  
[攻撃シナリオ] 完全で有効な台帳値 → `allocate()` の結果 → shard-local `selected` → `pytest_deselected` へ直接流れる。global union は保存できても、process 隔離、実行順、共有 fixture・資源競合が変わり、pytest verdict と `finished`・terminal evidence に影響しうるため、「台帳を selection・skip・受理判定の入力にしない」という plan の記述は実装と両立しない。  
[根拠 artifacts/s2-plan.md:40-44; artifacts/s2-plan.md:54-67; tools/acceptance_shards.py:763-789; tools/acceptance_shards.py:936-959]  
[提案] 「selection」が global universe だけを意味するのか shard-local deselection も含むのか裁定する。後者を含むなら本実装は不可能であり、前者なら不変条件を明文化し直す。

[severity: must-fix]  
[攻撃シナリオ] 100 個の単一-node成分をすべて有限値 `1e308` とした完全台帳 → 各 component 和は有限なので duration mode に入るが、K=2 の bin 加算は両 load が `inf` になり、残りが index 0 に集中する。偏った割付は全 node を実行するため closure/report gate を通り、壊れた台帳から count fallback しない。  
[根拠 artifacts/s2-plan.md:24-35; artifacts/s2-plan.md:40-46; tools/acceptance_shards.py:337-364]  
[提案] component 単位だけでなく全 node cost の `math.fsum` と各 bin 更新の有限性を検査する。component overflow と独立な「bin/global sum overflow」killer を追加する。

[severity: must-fix]  
[攻撃シナリオ] 台帳を schema-valid・全被覆・有限非負だが意味的に誤った値へ置換 → 全 controller が同じ誤 bytes を読めば、静かな fallback も snapshot 不一致も発火せず、任意の割付が受理される。静的な path・識別子・別名検索では現物 SHA-256 の pin はなく、既存 test は schema/有限性、8 suite の部分 node-set、90% coverage だけを固定する。なお anchors が schema 名とする `izanagi_acceptance_duration_ledger_v1` は document schema ではなく workerinput key である。  
[根拠 anchors.md:17; orchestrator/tests/conftest.py:752-765; orchestrator/tests/conftest.py:783-844; orchestrator/tests/test_update_acceptance_duration_ledger.py:307-325; orchestrator/tests/test_update_acceptance_duration_ledger.py:329-404]  
[提案] ledger bytes/HEAD blob を独立 trust root に pin し、duplicate-key を含む曖昧 JSON を拒否する。これは `conftest.py`、generator、pin test、report/merge 層まで及ぶため、現 scope 外の裁定パッケージにする。

[severity: should-fix]  
[攻撃シナリオ] synthetic な完全台帳テストだけを追加 → production が常時 fallback でも計画した検査は通る。これは failures の [恒真ゲート]・[テスト代表性]、pin 閉包漏れは [手順漏れ]・[誤前提]・[防壁の射程誤認]、selection の説明矛盾は [受理集合]・[説明と実装の食い違い]、snapshot 置換窓は [恒真ゲート] の再発型に当たるが、plan に型タグ別の再発検査がない。  
[根拠 docs/failures.md:683; docs/failures.md:951; docs/failures.md:1457; docs/failures.md:3326; docs/failures.md:3607; docs/failures.md:4848; artifacts/s2-plan.md:94-129]  
[提案] 型タグ→killer の対応表を plan に追加する。最低限、現物 ledger activation、K=3 snapshot 差異、bytes pin の3検査を入れる。

[severity: should-fix]  
[攻撃シナリオ] a1k2 と a2k1 の差から「worker 準備費を倍払った」と帰属する → K=1 の約9,000秒は worker occupancy の実測でなく wall からの逆算であり、K=2 occupancy 自体も worker startup・collection・idle を含まない。競合による testcase duration 膨張と準備費を識別できず、duration balance の利得判断を誤る。  
[根拠 anchors.md:64-67; anchors.md:84-92; tools/acceptance_shards.py:799-809; tools/acceptance_shards.py:920-958]  
[提案] 同じ観測定義で K=1/K=2 の worker busy・startup・collection を取得するまでは、準備費倍増を因果ではなく仮説として扱う。

[severity: should-fix]  
[攻撃シナリオ] P2 の式へ参照走 `W=7472.5, K=2` を代入 → 正値は `W/(48K)=77.84秒` だが brief は `155.7秒` として chain 律速を判定する。さらに chain が平均 capacity より長くても、開始遅延や別 component の tail が短縮不能とは導けない。  
[根拠 brief.md:40-46; artifacts/s2-plan.md:145-175]  
[提案] plan の指摘どおり分母を訂正し、この不等式を no-gain 保証ではなく再検討 trigger に限定する。

## 未確認事項

- pytest、import probe、受入実走は行っておらず、緑とは判定していない。
- 17,160 node は anchors の同一-tip 実測に依拠し、現セッションで再 collection していない。
- repo 外の report、JUnit、親 probe は読んでいない。
- Web 検索は使用していない。

## 総括

must-fix は 5 件。現 scope・不変条件のまま実装すべきではない。  
最大の理由は、現物台帳では必ず count fallback して実装が no-op になることと、K=3 の snapshot 不一致を exact gate が見逃すことである。  
`assignment_closure_gate` は allocator/ledger から独立しているが、保証するのは集合・file/group closure までで、共通割付や台帳 provenance ではない。  
再検討には `conftest`、report schema、merge gate、generator/pin、台帳更新 lifecycle までの scope 拡張が必要である。