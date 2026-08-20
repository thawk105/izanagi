段1の実装プランです。対象ファイルは変更しておらず、pytestも実行していません。

### 1. `_accounting_present` の diff 案

正規表現は既存の NQSV regex と同じく、行頭・行末と inline `(?m)` を使います。`_NQSV_REQUEST_ID_RE` の後、`_NQSV_STARTED_RE` の前に追加します。

```diff
 tools/pegasus/dispatch_compute.py:141
 _NQSV_REQUEST_ID_RE = re.compile(
     r"(?m)^[ \t]*Request ID:[ \t]*(\S+)[ \t]*$"
 )
+_NQSV_GROUP_NAME_RE = re.compile(
+    r"(?m)^[ \t]*Group Name:[ \t]*(\S+)[ \t]*$"
+)
 _NQSV_STARTED_RE = re.compile(
     r"(?m)^[ \t]*Started Request Time:[ \t]*\S.*$"
 )
```

`_accounting_present` は次のように変更します。

```diff
 tools/pegasus/dispatch_compute.py:928
-    """NQSV 会計サマリを submit ID と必須 field の連言で束縛する。"""
+    """NQSV 会計サマリを submit ID・policy account・必須 field の連言で束縛する。"""

     tail = stderr_record.get("tail")
     if type(tail) is not str:
         return False
     request_ids = _NQSV_REQUEST_ID_RE.findall(tail)
     if len(request_ids) != 1:
         return False
+    group_names = _NQSV_GROUP_NAME_RE.findall(tail)
+    if group_names != [DEFAULT_PROJECT]:
+        return False
     try:
         observed = _normalize_request_id(request_ids[0])
```

`findall` の結果を `[DEFAULT_PROJECT]` と比較するため、欠落・不一致・複数出現のいずれも fail closed になります。既存4フィールドの検査条件は変更しません。

期待値は P1 の provisional 裁定どおり、関数内で module 定数 `DEFAULT_PROJECT` を直接参照することを推奨します。qsub の `-A`、生成スクリプトの `#PBS -A`、receipt の project 欄と同じ単一の policy source を使え、呼び出し側が期待値を渡し忘れる余地もありません。

### 2. 呼び出し側

変更不要です。次の2箇所はそのまま維持します。

```python
# dispatch_compute.py:1935
_accounting_present(stderr_record, request_id)

# dispatch_compute.py:1944-1946
_accounting_present(stderr_record, request_id)
```

関数の戻り値は従来どおり bool なので、caller 側の引数・制御構造に差分はありません。

### 3. `_Scheduler._finish` の fixture diff 案

`orchestrator/tests/test_pegasus_dispatch_compute.py:96-103` の Request ID の直後に追加します。

```diff
             b"\n".join((
                 b"Request ID:             424242.nqsv",
+                b"Group Name:             SFC",
                 b"Started Request Time:   Thu Jul 30 10:03:23 2026",
                 b"Ended Request Time:     Thu Jul 30 10:10:20 2026",
                 b"  Elapse:               421S",
```

`SFC` は現行の `DC.DEFAULT_PROJECT` / `DEFAULT_PROJECT` と一致します。

### 4. 新規テストの assert 案

既存の `test_accounting_requires_matching_request_id_and_all_nqsv_fields` の parametrize に、次の2ケースを追加するのが最小です。

```python
        (
            "Request ID:             424242.nqsv\n"
            "Group Name:             OTHER\n"
            "Started Request Time:   now\n"
            "Ended Request Time:     later\n"
            "Elapse:                 1S\n"
        ),
        (
            "Request ID:             424242.nqsv\n"
            "Started Request Time:   now\n"
            "Ended Request Time:     later\n"
            "Elapse:                 1S\n"
        ),
```

assert は既存形式を維持しつつ、bool 契約を明示して次のようにします。

```python
def test_accounting_requires_matching_request_id_all_nqsv_fields_and_group_name(
    tail,
):
    assert DC._accounting_present({"tail": tail}, _JOB_ID) is False
```

既存の Request ID 不一致・Started/Ended/Elapse 欠落ケースには、独立した理由を保つため正しい行を追加します。

```python
"Group Name:             SFC\n"
```

また、`test_accounting_accepts_measured_nqsv_shape_only_when_id_matches` の正例にも追加します。

```diff
         "Request ID:             424242.nqsv\n"
+        "Group Name:             SFC\n"
         "Started Request Time:   Thu Jul 30 10:03:23 2026\n"
```

既存の assert は次の契約になります。

```python
assert DC._accounting_present({"tail": tail}, _JOB_ID) is True
assert DC._accounting_present({"tail": tail}, "424243.nqsv") is False
```

### 5. (P1)(P2) の推奨

- **P1: module 定数を直接参照する。**  
  現行 dispatcher は policy account を `DEFAULT_PROJECT` に固定しており、`dispatch()` や `_dispatch_impl()` に account 引数がありません。引数化すると2箇所の caller とテストの変更が増え、submit 時の account と検証時の account が分岐する余地が生じます。

- **P2: mismatch は `False` のみ返す。**  
  `_accounting_present` は bool 述語として既存 caller に組み込まれています。`False` なら accounting grace 中は待機し、期限到達時に既存の `result/log/accounting-grace-expired` 経路へ進みます。専用例外を追加すると receipt・marker 判定・infra reason の制御変更が必要になり、スコープを広げます。

### 6. brief と実コードの差分・見落とし

- brief は policy account の利用箇所として `qsub -A` の line 1714 を挙げていますが、実コードには生成 job script の `#PBS -A {DEFAULT_PROJECT}`（line 548）と receipt の `"project": DEFAULT_PROJECT`（line 1572）もあります。直接参照はこれら全てと整合します。
- brief は `_Scheduler._finish` の更新を明記していますが、直接呼び出す正例テスト（line 2242-2250）の tail にも `Group Name` 行が必要です。ここを更新しないと fixture 以外にこの単体テストも失敗します。
- `_bounded_log`（line 763-783）は末尾 `limit` bytes のみを `tail` として検査します。新たに Group Name が tail の外へ切れた場合も `False` になりますが、これは証跡が不完全なら受理しない既存設計と整合します。
- 既存コードは Request ID の重複を拒否する一方、Started/Ended/Elapse は非空行の存在だけを確認しています。今回の差分では既存挙動を変えず、Group Name だけは曖昧性を避けるため1件かつ exact 値を要求します。

## 総括

`Group Name` 用 regex を追加し、`_accounting_present` 内で抽出結果を `[DEFAULT_PROJECT]` と exact 比較する。期待値は module 定数を直接参照し、呼び出し側は変更しない。fake footer と既存正例へ `Group Name: SFC` を追加し、既存 parametrize に不一致・欠落ケースを加える。mismatch は bool `False` として既存の accounting-grace-expired 経路に委ねる。