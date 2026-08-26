---
schema: izanagi-spool-v1
ledger: failures
authored: 2026-08-27
wave: dev-wave-ccbench-pin-precheck-20260827
seq: 2
---

## 新規

### {{F:pin-closure-wrong-key-shape}}. pin 閉包を「値の長い表現」と「成果物 path」だけで引き、短縮表現と操作起動の gate を落とした [手順漏れ] [テスト代表性]

- 事象: CCBench pin 前進の影響範囲を測る precheck wave の段 1 で、親が
  `DW-O09` に従って閉包を列挙したが、2 種類の束縛を丸ごと落とした。
  段 3 の敵対検証が両方を露出させ、親の再実測で確定した。
  (1) 正本の定数 `orchestrator/campaign/pin.py` の `CURRENT_PIN` は **7 桁** (`511c953`) だが、
  親は 40 桁 (`511c9538…`) だけを `git grep` した。40 桁で 119 file、7 桁で 142 file。
  差集合 23 file を落とし、その中に「repo policy から逆算しない独立 pin」と明記された
  test golden が 6 file・7 箇所あった。
  (2) `docs/decisions.md` D297 は「pin を前進させるとき」に発火する専用 checker
  `tools/check_trace0_preprocess_identity.py` を定めるが、この gate は成果物 path でも
  pin 値でもなく **操作 (pin 前進) を key に**張られており、親の検索語のどれにも掛からなかった。
  実走すると rc=1 で赤だった。
- 根本原因: `DW-O09` は「path を key にする pin」と「role 名など key 側の pin」の 2 形しか
  警告しておらず、親はその 2 形だけを検索軸にした。同じ値が**長短 2 通りの表現**を持つこと、
  および gate が**これから行う操作**を key に張られうることを、検索軸として持っていなかった。
  結果として「119 file を全数検索した」という手続きの見た目が、閉包の完全性の根拠に化けた。
- 恒久対応: memory `pin-closure-search-two-missing-axes` — 閉包の件数を報告する前に
  (a) 正本定数の定義を開いてそこに書かれている表現で再検索し件数差を見る、
  (b) 行う操作の名前で `docs/decisions.md` を検索する、の 2 つを必須にする。
  本来の置き場は `docs/dev-wave/operations.md` の `DW-O09` だが、同節は
  997/1000 byte で追記余地が 3 byte しかなく、既存の安全義務を削らずには入らない。
  予算引き上げは自己改善契約に従い裁定パッケージへ回した
  (`output/insights/2026-08-27_ccbench-pin-precheck/README.md`)。
- 再発検知: 閉包を数える前に「正本の定数がどの表現で書かれているか」を定数定義から読み、
  その表現で再検索して件数差がゼロであることを確認する。件数差が出たら差集合を必ず列挙する。
  gate 側は、行う操作の名前 (「pin 前進」「凍結」「発行」など) で `docs/decisions.md` を
  検索してから閉包を確定する。
