## 所見

- **B1 — must-fix — [test_s8b_oracle_driver.py:1183](/work/1/SFC/tanab/izanagi/.claude/worktrees/t2273-shard0-precopy/orchestrator/tests/test_s8b_oracle_driver.py:1183)**
  T1 は同じ `node` で hook を 2 回呼んでいる。裁定 v2 が求める「2 node 分」の 1 回性は検証できず、node ごとに起動する退行でも受入の緑が誤って残りうる。2 個の `SimpleNamespace` に同じ `config` と `testrunuid` を渡し、それぞれで hook を呼ぶ。

## 削れるもの

- [conftest.py:2519](/work/1/SFC/tanab/izanagi/.claude/worktrees/t2273-shard0-precopy/orchestrator/tests/conftest.py:2519) の `module.ROOT` 一致検査は通常の同一 repo import では重複確認。ただし裁定 v2 に明記されており、今回の削除対象にはしない。
- `result.json` の失敗記録、config 属性の 1 回性 guard、helper の待機 loop は、非同期の生成結果を worker に渡す経路に必要。短縮しても分岐は実質減らない。
- identity 式の重複は、共通化すると conftest と test module の import 関係が増えるため現状が短い。T1 の conftest 複写と `importlib.util` 読込みも、`__file__` から小 repo の root を導くために使われている。既存 `_load_suite_conftest` は実 repo のファイルを読むので、そのままでは代替にならない。
- T1 の集合・bytes・mtime と除外対象の assert は、それぞれ fixture 内容の退行を検出する。削除候補はない。

## GO 判定

**修正後 GO** — T1 を別々の 2 node に直せば、静的確認では裁定 v2 の起動・複製・削除経路に取りこぼしはない。

## 総括

shard spec 付きで本物の hook を呼ぶ既存 test は `_early_memo_cache_probe` 経由の群で、追加された no-op が覆っている。他の直接呼出しには該当する shard spec がない。テスト実走は行っていない。