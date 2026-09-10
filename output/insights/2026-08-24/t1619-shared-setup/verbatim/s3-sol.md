## 総括

land を止めるべき must-fix は 1 件ある。負の対照が共有化後だけの確認になっており、共有化前後の検出力同値を証明していない。
exact-match は左右を別評価するため、plan どおりなら恒真化しない。現行 5 件には共有値を書き換える処理もない。
ただし要素の immutable 性は射影内で未証明であり、gap tripwire の実行順と効果見積もりにも修正が要る。
pytest は実走しておらず、以下は指定 6 ファイルだけによる静的レビューである。

[severity: must-fix] [攻撃シナリオ] 共有化で特定の検査経路を失っても、共有化後の clean、mutation の 2 走だけが赤になれば負の対照を通過できる。plan の「baseline、変異後」は同一版での非変異版と変異版を指すだけで、共有化前にも同じ変異が同じ assert を kill したことを記録していない。5 変異は test 別に分離され、C12 も `check_reservation` と `read_binding` の別変異になっている点は妥当だが、比較軸が欠けている。[根拠 `s2-plan.md:73-87`; `test_s8c_preregistration_predicates.py:187-260,279-286`] [提案] 各行について「共有化前 clean 成功、共有化前 mutation が指定 assert で失敗、共有化後 clean 成功、共有化後の同一 mutation が同じ assert で失敗」の 4 状態を記録する。各 mutation は対象 node だけで別 run にし、C12 の 2 変異も混ぜない。anchor の一意性検査も `s2-plan.md:85` の条件どおり必須にする。

[severity: should-fix] [攻撃シナリオ] 外側を tuple にしても、共有された `PredicateResult` が mutable なら、先行 test の属性代入や内部 evidence 更新が後続 test、特に gap ledger の観測値を汚染できる。実装上 `evaluate_all` は内部 list を最後に tuple 化し、evidence も tuple だが、要素は射影外で定義された `core.PredicateResult` と `core.EvidenceRef` であり、frozen 性は確認できない。plan 自身も深い immutable 性を断言していない。現行 5 件は反復、辞書内包、属性読出し、等値比較だけで、現在のコードには実際の書換え元はなく、新しい順序依存は確認されなかった。[根拠 `s8c_preregistration_evidence.py:804-806,1472-1482,3111-3210,3213-3223`; `s2-plan.md:59-61`; `test_s8c_preregistration_predicates.py:190-260,283-286`] [提案] land 前の記録へ `PredicateResult` と `EvidenceRef` の定義位置と frozen、nested field の型を追加する。frozen でなければ raw instance を共有せず、test ごとに独立コピーを返す。

[severity: should-fix] [攻撃シナリオ] 5 件を同じ xdist group に直列化すると、source 順では一般的な zero-satisfied と exact-match が gap ledger より先に走る。他 wave の変更で先行 test が赤になり、`-x` または `--maxfail=1` が使われると、意図再審査用の詳細な C01-C12 reason map が実行されず、診断が一般的な失敗へ埋もれる。親の実測コマンドは fail-fast ではないため通常走で検出自体は残るが、tripwire の優先度は下がる。[根拠 `test_s8c_preregistration_predicates.py:187-249`; `s2-plan.md:4,107-115,123-125`; `measurements.md:8-10`] [提案] group 内の最初になるよう gap-reason test を `test_current_repository_*` 族の先頭へ移す。関数名、assert、group membership は変えない。

[severity: should-fix] [攻撃シナリオ] stale node の 32 秒まで共有化で削減できるものとして数えると、実在する 5 test の効果を 160 秒、wall 3.3 秒と過大評価できる。親の値では 207 秒は exact 47 秒と 32 秒が 5 件であり、そのうち 1 件は source に存在しない。したがって live 5 件は 175 秒で、共有後 45 秒という親の仮定なら削減は約 130 秒、48 worker 単純換算で約 2.7 秒である。[根拠 `brief.md:24-26`; `measurements.md:53-61`; `chain-measurement.md:22-25`] [提案] stale 32 秒を総 work と本族 work の両方から除外し、live-only の before/after 実測で効果、下界、削減比を再計算する。

恒真化については、共有 snapshot が左辺、`evaluate_all("HEAD", repo_root=_ROOT)` の新規呼出しが右辺として残るため安全である。`actual = snapshot` 等も明示的に禁止されている。[根拠 `s2-plan.md:63-71`; `test_s8c_preregistration_predicates.py:198-204`]

絶対規律 2 についても、実装手順は fixture 拡張、5 decorator、独立 oracle 追加、計測だけであり、test 削除、skip、xfail、assert 弱化、現行 hash の期待値化、揮発 payload の焼込みは見当たらない。JSON whitespace 変異は exact-match 用の一時的な負の対照であり、land する期待値ではない。[根拠 `brief.md:28-34`; `s2-plan.md:51-57,77-87,119-127`]