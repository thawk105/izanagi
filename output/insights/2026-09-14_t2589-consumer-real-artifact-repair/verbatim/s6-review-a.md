## 所見

- **real／文書 nit** — 「全文は成果物に無い」の適用範囲が広すぎます。[buildcache.py:2903](orchestrator/campaign/buildcache.py:2903) は completion manifest に full version manifest と digest を保存します。[consumer:9](orchestrator/campaign/t1998_stock_inline_pair.py:9) と親記録の説明は「この consumer が読む回収済み WAL／result」に限定すべきです。これは旧等式が正しかった反例ではなく、追加 gate の提案でもありません。
- **real／証拠の過大評価** — [親 README:139](output/insights/2026-09-13_t2557-balanced-stock-inline/README.md:139) の「残る検査に追加の欠陥は無い」は、1 成果物の受理からは導けません。「この成果物では追加の拒否に遭遇しなかった」が確認できる範囲です。

## 撤去の妥当性

**refuted — 有効だった digest 対応検査を撤去したという疑い。** [buildcache.py:2518](orchestrator/campaign/buildcache.py:2518) は full version を含む対象を hash し、[pipeline.py:2063](orchestrator/campaign/pipeline.py:2063) は identity 射影とその digest を別々に記録します。導入 commit `297008465` も同じ構造でした。期待 manifest を渡さない経路では digest が欠落し、撤去後も必須形式検査で拒否されます。

実 WAL でも、8 build の射影と記録 digest が共通することを確認しました。探索した producer 経路に、旧等式が正しい対応検査になる反例は見つかりませんでした。撤去は妥当です。

## 波及

- **refuted — JSON 検査の道連れ。** 削除 helper に状態変更はなく、WAL の再帰的な有限 JSON 検査は [wal.py:400](orchestrator/campaign/wal.py:400) に残ります。射影の腕間一致、digest の腕間一致、result との一致も [consumer:1254](orchestrator/campaign/t1998_stock_inline_pair.py:1254) に残っています。
- **refuted — 空 prefix による wrapper 通過。** [consumer:641](orchestrator/campaign/t1998_stock_inline_pair.py:641) は空 prefix なら `argv[0]`、非空なら完全一致した prefix の直後だけを取り出します。[consumer:810](orchestrator/campaign/t1998_stock_inline_pair.py:810) の実行対象照合により、先頭に `env`／shell／別 wrapper を挟む形は拒否されます。
- **refuted — 非保証記述の中核が不正確。** 同じ有効形式の digest へ両腕を置換しても、この対応検査では検出できないという説明は正確です。ただし WAL を変えれば、別途 result の WAL hash 束縛が発火します。「この層で」の限定は必要です。

## 親裁定の評価

**refuted — 差し替え後の理由が技術的に成立しないという疑い。** 撤去対象は異なる preimage を同一視した等式です。認証 admission、source 束縛、anomaly／非直列化の拒否は維持されています（[consumer:978](orchestrator/campaign/t1998_stock_inline_pair.py:978)、[consumer:1181](orchestrator/campaign/t1998_stock_inline_pair.py:1181)）。

ただし「受理条件は動かない」は不正確です。受理集合は変わります。**誤った証拠解釈を修正し、正しさ検証の拒否条件を維持する変更**という説明なら支持できます。§6 に列挙されないことや D1876 の類例だけでは、撤去の根拠として不足します。

## 総括

**実装を止める正しさ回帰は見つかりませんでした。撤去と prefix 修正を支持します。** 文書上の一般化には上記 2 件の nit があります。

静的レビューと既存成果物の読取りのみ実施しました。テスト未実行であり、親の再走結果を緑とは認定していません。