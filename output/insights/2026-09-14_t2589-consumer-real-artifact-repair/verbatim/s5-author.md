## 変更点

指定の2ファイルのみ修正しました。

- wrapper prefix を契約 hash から解決。
- toolchain digest の腕内再導出と未使用 helper を削除。
- digest 検証の非保証範囲を docstring に明記。

## 残した検査

実行対象と build dir の一致、toolchain の非空性、digest の形式・腕間一致、manifest の腕間一致・result 一致を維持しました。その他の判定・認証検査も変更していません。

## テストの変更

fixture を3 key 射影・全文由来 digest・契約由来 prefix に変更。linux-baremetal の受理テストを追加しました。腕間 drift テストは維持し、共有非canonical digest の拒否テストは削除しました。

## 実行できた検査

- 2ファイルの AST 構文解析：成功。
- `git diff --check`：成功。

## 未了・リスク

`python3 -m pytest -q orchestrator/tests/test_t1998_stock_inline_pair.py` は PreToolUse guard に拒否され、未実走です。親側でテスト・実成果物解析が必要です。受入台帳は未変更です。

両腕の digest を同じ別値へ置換した改竄は、この層では拒否できません。

## 総括

修正を作業ツリーに残しました。事前登録 bytes・SHA 定数・docs・producer は未変更。commit・push は行っていません。