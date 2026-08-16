---
schema: izanagi-spool-v1
ledger: failures
authored: 2026-08-16
wave: dev-wave-t1222-growth-hold-sweep
seq: 3
---

## 新規

### {{F:primitive-sweep-misses-in-process-calls}}. 探索 primitive の文字列検索が in-process 呼び出しを落とす [テスト代表性] [手順漏れ]

- 事象: 成長比例テストの全件走査で、子は 209 file / 8,018 top-level test を AST で閉包化し
  候補 230 件を出したが、少なくとも 11 top-level node を落としていた。落ちた node は
  `check_docs.main()` や `provenance.main()` を**同一プロセス内で**呼ぶ形と、
  production の enumerator (`load_role_specs(ROOT)` 等) を経由する形である。
- 根本原因: 探索 primitive を `(?:check_docs|check_ai_provenance)\.py` のような
  **実行形の文字列**で定義したため、module 属性経由の呼び出しに構造的に当たらない。
  subprocess 起動と in-process 呼び出しは同じ費用を払うが、検索面が異なる。
- 恒久対応: 走査の primitive に「実 ROOT を引数に取る production 関数の呼び出し閉包」を
  独立の軸として含める。文字列検索の hit 数と候補集合の件数を別々に記録し、
  ゼロは「宣言した primitive と AST 規則の範囲で未検出」と書く。
  母集合が閉じたとは書かない ({{D:growth-hold-input-set-criterion}} と同 wave の記録)。
- 再発検知: 棚卸し結果に対する敵対レビューで、同型の取りこぼしを 1 件でも file:line で
  示せるかを検査面に含める。本 wave では親と敵対レンズ 2 本がそれぞれ独立に検出した。

### {{F:partial-call-closure-declared-non-proportional}}. 呼び出し閉包の一部だけを見て「非比例」と断定した [捏造/幻覚]

- 事象: 親が段 4 の裁定で、`test_check_ai_provenance.py` の実 repo 2 node を
  「固定された歴史 commit を渡すので成長比例でない」と断定した。実際は
  `_audit_history` が毎回 `_scope_policy_commit()` / `_implementation_policy_commit()` を呼び、
  現在の HEAD に対して `git log -S … -- docs/ai-provenance.md` を走らせる。
  同じ裁定で「copytree 対象 4 部分木は 1 file も増えていない」とも書いたが、
  自分が同じ文書に載せた表が `tools/task_runs` の 0 → 7 file を示していた。
- 根本原因: 入力範囲を決める関数 (`_commit_range`) と祖先展開 (`_build_ancestry`) だけを読み、
  その手前で毎回走る epoch 探索を読まなかった。表と結論文を別々に書き、突き合わせなかった。
- 恒久対応: 「非比例」と書く前に**呼び出し閉包を終端まで追い**、自分が同じ文書へ載せた
  実測表と結論文を突き合わせる。断定を弱める材料が自分の表にあるなら結論を書き換える。
- 再発検知: 敵対レビューのレンズに「親の実測とその一般化」を明示的に含める
  (`DW-S03` は既に要求している)。本 wave では段 6 のレビュー 2 本が独立に検出した。

## 再発

### F268

- **再発: 2026-08-16** — 段 6 の敵対レビュー A の待ち手が、`.done` も成果物も無く
  producer が生存 (経過 3 分 15 秒) の状態で **rc=0・出力空**のまま返った。
  投入から待ち手を張るまでは 2 秒で、実際の完了はその約 30 分後だった。
  3 点照合が偽完了を捕まえ、`Monitor` で張り直した待ち手が正しい完了時刻を拾った。
  同 wave の他 5 本 (plan、consult 2 本、author、fix) の待ち手は正常に返っており、
  偽完了は 6 本中 1 本である。
