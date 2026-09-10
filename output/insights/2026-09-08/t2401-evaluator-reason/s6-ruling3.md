# 段 6 裁定 (3 巡目) — 変異走行が掘り当てた実欠陥

## 実測 (親)

変異 probe (26 変異、全件 SURVIVED 登録) が **最初の変異 `m1-evaluator-fallback-satisfied` で停止**した。
harness の停止理由は `rc=3 だが canonical stdout から failed node を確実に抽出できないため停止`。
baseline は `rc=0 / PASSED / failed_nodes 0` で正常。

job stdout を読むと真因は明確である。

```
INTERNALERROR> E   File ".../orchestrator/tests/test_s8c_preregistration_core.py", line 529, in __getattribute__
INTERNALERROR> E     raise SystemExit("secret-detail")
INTERNALERROR> E   SystemExit: secret-detail
INTERNALERROR> AssertionError: ('orchestrator/tests/test_s8c_preregistration_core.py::test_invalid_exception_type_uses_bounded_sentinel_without_leaking[hostile-type-name]', <WorkerController gw47>)
=================== 3 failed, 44 passed, 1 warning in 5.68s ====================
```

pytest が失敗を報告する経路 (`_pytest/_io/saferepr.py` → `reprlib.repr1` → `typename = type(x).__name__`)
が、本 wave が足した敵対 fixture の metaclass `__getattribute__` を踏み、`SystemExit` を送出する。
xdist の worker がその場で落ち、pytest は `INTERNALERROR` と **rc=3** を返す。
3 件の失敗自体は digest に出ているが、`FAILED` の要約行が出ないため harness は node を抽出できない。

## 裁定

- **判定: real、blocker。** これは本 wave が足したテストの欠陥である。
  **「失敗すると走行そのものを壊すテスト」は信用できない。**
  正常時に緑であることは、失敗時に正しく報告できることを含意しない。
- 影響は変異走行に留まらない。受入全走でも、これらの node が何かの理由で落ちれば
  worker が落ち、全体が rc=3 になって赤の帰属が不能になる。
- **固定している命題は変えない。** 敵対的な `__name__` / `reason` が sentinel へ倒れ、
  detail が漏れないことは引き続き固定する。変えるのは**敵対的な挙動が有効な区間**だけである。

## fix の scope (これ以外を実装しない)

1. **敵対 fixture の危険な挙動を、検査対象の呼び出しの前後だけで有効にする。**
   `__getattribute__` / property / metaclass が例外や非文字列を返すのは、
   `_evaluator_exception_reason` (またはそれを呼ぶ production 経路) を呼ぶ**その瞬間だけ**とし、
   それ以外の時点では通常の class として振る舞わせる。
   これにより、テストが失敗しても pytest は traceback を安全に整形できる。
2. **対象は本 wave が足した敵対 fixture すべて。** `SystemExit` を送出する型、
   非文字列の `__name__` を返す型、`reason` 属性が無い / 非文字列 / 例外を出す型を含む。
   `reprlib` は `type(x).__name__` を直接読むため、**非文字列 `__name__` も pytest の
   報告経路を壊しうる**。同じ扱いにする。
3. **同じ危険が無いことを機械で確かめる。** 敵対 fixture の instance を、
   armed でない状態で `repr()` しても例外が出ないことを固定する assertion を足す。

**scope 外:** production コードの変更 (この fix でも `s8c_preregistration.py` は 1 byte も変えない)、
固定している命題の変更、テストの削除・skip・緩和。

## 追加する変異事前登録

| ID | 位置 | 変異 | 期待 |
|---|---|---|---|
| D17 | 敵対 fixture の arm 機構 | arm 区間を常時 on にする | 「armed でない状態で `repr()` しても例外が出ない」assertion が落ちる (診断感度 pin) |

## 記録する失敗型

`{{F:hostile-fixture-breaks-failure-reporting}}` として台帳へ残す。
**恒久対応は arm/disarm と、armed でない状態の `repr()` 安全性を固定する assertion** を指す。
