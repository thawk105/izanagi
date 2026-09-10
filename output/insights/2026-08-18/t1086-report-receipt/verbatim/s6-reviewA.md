## must-fix

[RA-1] real — `O_NOFOLLOW` の実効性を検査するテストがない。  
根拠: `orchestrator/campaign/s8b_oracle_report.py:1852-1858` で `O_NOFOLLOW` を付けているが、`orchestrator/tests/test_s8b_oracle_report.py:4586-4612` の symlink 負例は、その前の resolve containment または `lstat` 相当の検査 (`s8b_oracle_report.py:1835-1837,1869-1878,1900-1906`) で拒否される。したがって両方の `O_NOFOLLOW` を削除しても当該 2 テストは緑のままである。`stat` 後、`open` 前に symlink へ交換する対照が必要。  
成果物影響: `O_NOFOLLOW` が後退すると競合窓で root 外の bytes を hash でき、SHA が一致すれば observations の `store_reverification.state="verified"`、oracle は `determinate`、combined verdict も従来の確定値を維持しうる。

## nit

[RA-2] real — 段 4 の M10 killer は依然として変異行を検査しない。  
根拠: M10 は `s8b_oracle_report.py:1837` の containment 削除だが、指定された symlink tests (`test_s8b_oracle_report.py:4586-4612`) は削除後も `s8b_oracle_report.py:1876-1879,1905-1906` で拒否される。source hash pin だけは赤になるため、機能検査による kill と誤認しやすい。段 4 の指定は `s4-ruling.md:23,58-59`。  
成果物影響: M10 単独では observations、oracle、combined verdict の値も受理集合も変わらず、現登録は equivalent mutant である。従って must-fix ではなく、M10 の再登録または独立 helper 契約テストが必要な nit とする。

[RA-3] real — production caller pin の探索範囲が契約より狭い。  
根拠: `test_s8b_oracle_report.py:4716-4735` は `campaign/*.py` の top-level `FunctionDef` 内だけを走査する。module-level call、`AsyncFunctionDef`、別 production package、別名 import 経由は検出しない。現時点の実 caller が `s8b_oracle_report.py:2239` の `main()` だけであること自体は静的検索で確認できた。  
成果物影響: 未検出 caller が追加されると receipt のない observations report を発行できるが、現 judge は欠落を拒否するため oracle・combined verdict は indeterminate 側へ倒れ、現時点の偽 determinate は生じない。

## 総括

既知の `output_root` 不在による 2 件の赤は再掲していない。  
outer state は cells から再導出され、空・部分集合・重複に対する負例も determinate baseline から分岐している。  
expected SHA の report-side 出所は `ReverifiedFreeze.binaries_by_cell` に限定され、WAL や row からの混入は見つからなかった。  
legacy と token 省略経路も judge で fail-closed になる。  
source hash golden は現在の report/judge bytes と一致し、raw spec SHA も自己整合している。  
主な blocker は、`O_NOFOLLOW` の競合防御がテストされていない点である。  
M10 は現実装では冗長層の単独削除になり、現在の登録のままでは機能的 kill を主張できない。  
pytest は read-only レビュー契約に従い実走せず、差分と周辺コードの静的監査のみを行った。