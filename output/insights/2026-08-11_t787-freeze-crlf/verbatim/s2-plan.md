結論は「修正付き GO」です。最大の修正点は、P1 の「各 node で NUL → CR/LF の順に見る」だけでは不変条件 2 を守れないことです。文書順で先に CR/LF path、後に NUL path がある場合、CR/LF を即 raise すると従来の NUL reason/pointer を横取りします。CR/LF の最初の pointer を保留し、走査全体で NUL がなかった場合だけ raise する必要があります。

## 1. choke point の具体的 diff

対象は [s8c_preregistration.py:344](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t787-freeze-crlf/orchestrator/campaign/s8c_preregistration.py:344) と、その呼出し [同:363](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t787-freeze-crlf/orchestrator/campaign/s8c_preregistration.py:363) だけです。

推奨 diff は次の形です。

```diff
-def _assert_no_nul_in_contract_paths(value: Any) -> None:
-    """契約の ``path`` field に NUL があれば fail-closed で拒否する。
+def _assert_no_forbidden_control_chars_in_contract_paths(value: Any) -> None:
+    """契約の ``path`` field に NUL / CR / LF があれば拒否する。
 
-    走査対象は key が exact ``path`` かつ値が ``str`` のものだけである。NUL 以外の文字も、
-    ``path`` 以外の field の NUL も拒否しない。文書順で最初に見つけた 1 件で停止する。
+    走査対象は key が exact ``path`` かつ値が ``str`` のものだけである。
+    NUL は CR/LF より全域で優先し、既存の reason と最初の NUL pointer を維持する。
+    NUL / CR / LF 以外の文字と、``path`` 以外の field は拒否しない。
     """
+    first_crlf_pointer: Optional[str] = None
     pending: list[tuple[str, bool, Any]] = [("", False, value)]
     while pending:
         pointer, is_path, node = pending.pop()
-        if is_path and isinstance(node, str) and "\x00" in node:
-            raise PreregistrationError("evidence-contract-path-nul", repr(pointer))
+        if is_path and isinstance(node, str):
+            if "\x00" in node:
+                raise PreregistrationError(
+                    "evidence-contract-path-nul", repr(pointer)
+                )
+            if (
+                first_crlf_pointer is None
+                and ("\r" in node or "\n" in node)
+            ):
+                first_crlf_pointer = pointer
         if isinstance(node, dict):
             for key, child in reversed(list(node.items())):
                 pending.append((f"{pointer}/{key}", key == "path", child))
         elif isinstance(node, list):
             for index, child in reversed(list(enumerate(node))):
                 pending.append((f"{pointer}/{index}", False, child))
+    if first_crlf_pointer is not None:
+        raise PreregistrationError(
+            "evidence-contract-path-crlf", repr(first_crlf_pointer)
+        )
...
-    _assert_no_nul_in_contract_paths(value)
+    _assert_no_forbidden_control_chars_in_contract_paths(value)
```

検査順は厳密に次です。

1. `_strict_json`。
2. `_canonical_bytes`。失敗は従来どおり `evidence-contract-json`。
3. 明示 stack による単一走査。
4. exact `path` の `str` で NUL を見つけたら直ちに既存 reason/pointer で拒否。
5. CR/LF は文書順で最初の pointer だけ保存し、走査を続行。
6. NUL が全域になければ保存した pointer で `evidence-contract-path-crlf`。
7. 何もなければ既存 canonical bytes を hash。

これにより次が成立します。

| 入力 | 結果 |
|---|---|
| NUL path あり、CR/LF の有無を問わない | 従来と同じ最初の NUL pointer、`evidence-contract-path-nul` |
| NUL path なし、CR/LF path あり | 最初の CR/LF pointer、`evidence-contract-path-crlf` |
| どちらもなし | 従来と同じ hash |
| 非 `path`、非 `str`、その他の制御文字 | 従来どおり受理 |

`repr(pointer)` 以外を detail に渡さず、CR/LF 入り path 自体は保持も報告もしません。[発効層 `_safe_path`:180](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t787-freeze-crlf/orchestrator/campaign/s8c_preregistration_evidence.py:180) と `load_contract_bytes` は no-touch です。

## 2. helper の再利用・変更

対象は [core test helper:121](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t787-freeze-crlf/orchestrator/tests/test_s8c_preregistration_core.py:121) 以降です。

- `_contract_path_cases` と `EVIDENCE_CONTRACT_PATH_CASES`（121–142）  
  変更せず再利用可能です。実契約の 26 required + 12 consumer = 38 位置を production から独立して列挙します。

- `_contract_with_selector_suffix`（145–153）  
  38 位置テストにはそのまま使えます。ただし別 node の CR/LF と NUL を同時注入する優先順位テストには不足します。`_contract_with_selector_suffixes(*changes)` に一般化し、1 件・複数件を同じ fixture へ適用する形を推奨します。現行利用は 563 行の 1 箇所だけです。

- `_contract_with_path_suffix`（156–173）  
  変更せず再利用します。反転する 4 param、同一 node の NUL 併存、既存 E2E 利用を担えます。

- `_contract_with_interior_path_nul`（176–199）  
  hard-code されているため CR/LF へはそのまま再利用不可です。`_contract_with_interior_path_control(*, owner, control)` へ一般化し、既存 NUL test も `control="\x00"` で呼び直します。

## 3. テスト変更の全列挙

主対象は [core test:548](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t787-freeze-crlf/orchestrator/tests/test_s8c_preregistration_core.py:548)–[698](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t787-freeze-crlf/orchestrator/tests/test_s8c_preregistration_core.py:698) です。

1. 38 位置 inventory

   `test_contract_path_inventory_has_expected_count` は `38` のまま維持します。

2. 既存 NUL 38 位置

   `test_evidence_contract_hash_rejects_nul_at_every_consumed_path` は意味を変えません。複数 suffix helper へ一般化した場合だけ呼出し構文を更新します。

3. 新設 CR/LF 38 位置 × 2

   `test_evidence_contract_hash_rejects_crlf_at_every_consumed_path` を追加します。38 pointer × `cr`/`lf` = 76 node とし、ID は例として `/conditions/0/required_evidence/0/path-cr` の形に固定します。

   各 fixture は `control + "alias"` を付け、末尾一致だけを見る変異も殺します。assert は新 reason、exact pointer、detail への CR/LF 非混入です。

4. 既存 4 param 受理固定の反転

   [現行 test:594](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t787-freeze-crlf/orchestrator/tests/test_s8c_preregistration_core.py:594) の `required-cr`、`required-lf`、`consumer-cr`、`consumer-lf` を維持して、関数名を `test_evidence_contract_hash_rejects_crlf_path_controls` へ変更します。

   `expected_sha256` 4 literal は削除し、`_contract_with_path_suffix` が返す pointer に対する `evidence-contract-path-crlf` を検査します。76 node と一部重複しますが、「wave 前に受理していた 4 ケースの反転」を直接固定するため残します。

5. 中間位置

   既存 NUL test は一般化 helper で維持します。新しく `test_evidence_contract_hash_rejects_crlf_at_interior_position` を `required/consumer × cr/lf` の 4 node で追加します。control の前後がともに非空であることも fixture 側で assert します。

6. NUL 併存の優先順位

   `test_evidence_contract_hash_preserves_nul_precedence_over_crlf` を最低 4 node で追加します。

   - `same-node-cr/lf`: 同じ path に `CR/LF`、その後に NUL を置く。
   - `earlier-path-cr/lf`: `EVIDENCE_CONTRACT_PATH_CASES[0]` に CR/LF、`[-1]` に NUL を置く。

   後者は、旧実装が返した後側の NUL pointer と `evidence-contract-path-nul` を exact に要求します。P1 の node-local 実装不備を殺す中心テストです。

7. 非 path field の NUL/CR/LF 受理

   [現行 non-path NUL test:633](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t787-freeze-crlf/orchestrator/tests/test_s8c_preregistration_core.py:633) を `nul/cr/lf` の 3 param に拡張します。`static_only_note` への escape 注入と exact hash は次です。

   | ID | exact hash |
   |---|---|
   | `nul` | `77cd405fcc67ebd51416d4329edee3a2ecd9ed8ef0be71855d94c32486915735` |
   | `cr` | `43776aacfa0793d7d8e20fdfa45d7d97e8ef49a9d26de0179e7d7b4b2c7a8e50` |
   | `lf` | `8218499e58e1643e3c0488c49c7f81e718a37fc7165b2280543ae0585089da8e` |

8. malformed shape の CR/LF

   [既存 NUL malformed cases:643](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t787-freeze-crlf/orchestrator/tests/test_s8c_preregistration_core.py:643) の 3 shape を CR/LF にも適用し、6 node を追加します。これがないと「CR/LF だけ既知 v1 schema 位置に限定する」変異が 38 位置 test を通過します。

9. canonicalization 優先

   [既存 NUL test:674](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t787-freeze-crlf/orchestrator/tests/test_s8c_preregistration_core.py:674) と同型で、CR/LF + unpaired surrogate の 2 node を追加します。期待 reason は `evidence-contract-json` です。

10. 現行契約 hash と既発行 pin

    [current hash test:684](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t787-freeze-crlf/orchestrator/tests/test_s8c_preregistration_core.py:684) と [g1 pin test:690](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t787-freeze-crlf/orchestrator/tests/test_s8c_preregistration_core.py:690) は既に必要な exact 値を固定しています。重複 test は新設せず、両 node を変更せず受入対象に残します。

11. 過剰拒否の正例

    `test_evidence_contract_hash_accepts_values_outside_exact_string_path_boundary` を追加し、次を exact hash で受理固定します。

    | ID / raw | exact hash |
    |---|---|
    | `non-exact-key`: `{"not_path":"x\r"}` | `bbde929109e679341d3e8c019b4a524ea76e2863a06c45f396e78261b633f8fa` |
    | `non-string-path-list`: `{"path":["x\r"]}` | `9ebf2983b21173bed63774bbde43fc6e35c4dfabee8bbc422edcbc18718130db` |
    | `non-string-path-number`: `{"path":1}` | `c972129fb103a6986ba9634df52125dcd99d707d4615dabd36ad11c568988556` |
    | `other-path-control`: `{"path":"x\u000balias"}` | `e27ced393e0b9ef4d95104c99d57afa293467c99e8b5cf825cc2e19080a7609b` |

    これで exact key、`str` 型、CR/LF 限定、schema 非検証をそれぞれ正例から固定できます。

## 4. P1〜P3 への裁定案

- P1: 一部反対。理由語の分離と NUL 語維持には賛成です。ただし node 内の NUL → CR/LF だけでは、先行 CR/LF node が後続 NUL node を横取りします。代案は「NUL は即 raise、最初の CR/LF pointer は走査終了まで保留」です。統一 `…-control-char` は既存診断契約を壊すため不採用でよいです。

- P2: 実装構造には賛成、名前だけ修正推奨です。単一 choke point・単一走査を維持し、二重走査は不要です。ただし `_assert_no_control_chars_in_contract_paths` は「他の制御文字を受理する」という不変条件と名前が衝突します。`_assert_no_forbidden_control_chars_in_contract_paths` を推奨します。

- P3: 条件付き賛成です。指定された 38 位置、4 param 反転、中間位置、非 path、hash pin は妥当です。加えて、別 node の NUL 優先、malformed shape の CR/LF、CR/LF と canonicalization failure の優先を追加しないと、D281 の全域走査・検査位置を CR/LF 分岐だけが破る変異を殺せません。

## 5. 変異事前登録候補

| 変異 | KILL を期待する node |
|---|---|
| 必須: 最終 helper 全体を wave 前の NUL-only 実装へ revert | CR/LF 38×2、反転 4、interior 4、malformed 6 の計 90 node |
| CR 条件だけ削除 | 上記の `*-cr` 45 node |
| LF 条件だけ削除 | 上記の `*-lf` 45 node |
| CR/LF を見つけた場で即 raise | `preserves_nul_precedence_over_crlf[earlier-path-cr/lf]` |
| CR/LF reason を NUL 語または統一語へ変更 | CR/LF 拒否 90 nodeの reason assertion |
| `in` を `endswith` へ狭める | 38×2、interior 4、malformed 6 |
| outer `is_path` 条件を削除 | non-path `nul/cr/lf` と positive の `non-exact-key`、`non-string-path-list` |
| CR/LF 判定を全 C0 文字へ拡大 | positive `other-path-control` |
| CR/LF だけ既知 schema 位置へ限定 | malformed CR/LF 6 node |
| helper 呼出しを canonicalization 前へ移動 | 既存 `...reason_before_nul` と新 CR/LF 2 node |
| exact `path` の全 string を無条件拒否 | `test_current_evidence_contract_hash_is_frozen` と positive path cases |
| detail を `repr(node)` に変更 | 任意の CR/LF 拒否 nodeの exact pointer・制御文字非漏洩 assertion |

最初の revert は、単に関数呼出しを削る変異ではなく、現行 344–360 行と 370 行を wave 前の NUL-only helper/call へ戻す exact 変異として登録します。

## 6. 実装子の所有分割

実装子は 1 本だけにし、次を単独所有させます。

- [production choke point:344–370](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t787-freeze-crlf/orchestrator/campaign/s8c_preregistration.py:344)
- [test helpers:121–199](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t787-freeze-crlf/orchestrator/tests/test_s8c_preregistration_core.py:121)
- [core tests:548–698](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t787-freeze-crlf/orchestrator/tests/test_s8c_preregistration_core.py:548)

別実装子との file 分割はしません。実装子は module と tests だけを編集し、発効層、契約 JSON、docs、mutation ledger、commit には触れません。mutation 登録、テスト実走、受入全走、記録は親所有です。本起草では pytest は実走していません。

## 総括

- 修正付き GO。P1 の node-local 優先だけでは別 node の NUL reason/pointer を保てない。
- CR/LF は最初の pointer を保留し、全域で NUL がなかった場合だけ新語で拒否する。
- choke point、明示 stack、canonicalization 後、pointer-only detail は D281 のまま維持する。
- 既存 4 param は拒否へ反転し、38×2、interior、併存、非 path、正例を追加する。
- malformed shape と canonicalization 優先も追加し、CR/LF 分岐だけの抜け道を塞ぐ。
- 現行契約 hash と g1 protected hash は既存 exact test をそのまま使う。
- 実装子 1 本が module と core tests を単独所有し、実走・変異・記録は親が担う。