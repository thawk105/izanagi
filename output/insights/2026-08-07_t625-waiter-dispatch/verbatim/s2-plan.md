## 採用プラン

基準は clean な `bb824d8b`。3 ファイルを同一変更単位で編集し、`DW-C00` 本文、既存行、段 dispatch、予算値は変更しない。

### 条件 key

現行の条件 key は次の22本（番号上限は23だが、07が欠番）である。

- operations 由来: `01, 02, 03, 04, 05, 06, 08, 09, 10, 11, 12, 13, 14, 16, 17, 18, 19, 20, 23`
- 特殊条件: `15` → `DW-M07`、`21, 22` → `DW-CTX`
- 削除済み: `DW-O07` は T-154(1)、`DW-O15` は T-450 の裁定で削除済み。`15` は条件 key として既使用。

したがって採用 key は、最大使用番号23の次である新規単調増加の `24`。`07` や `DW-O15` を復活させる案には新たなユーザー裁定が必要であり、採らない。`24` は core 条件なので `_OPERATION_NUMBERS` には追加しない。

## ファイル別編集

行番号は編集前の `bb824d8b` を基準とする。

### 1. 入口

[dev-wave.md:105](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t625-waiter-dispatch/.claude/commands/dev-wave.md:105) の `| 23 |` 行直後、現行106行の空行前へ挿入する。結果は新106行。

```text
| 24 | 背景 producer・待ち手の生成 / 再利用 / 停止、通知処理の直前 | `docs/dev-wave/core.md`: `DW-C00` |
```

`wave 開始` の `DW-C00` dispatch は残す。これは開始時と事故直前の二重 dispatch を意図した追加であり、段 dispatch 表は変更しない。

### 2. ハードコード契約

[check_docs.py:502](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t625-waiter-dispatch/tools/check_docs.py:502) の `CONDITION_DISPATCH_CONTRACT.update({...})` 内で、現行504行の `"22"` の直後へ挿入する。結果は新505行。

```python
    "24": _pairs(_CORE, "DW-C00"),
```

これは既存の core 条件 `21` / `22` と同じ様式である。以下は変更しない。

- `_OPERATION_NUMBERS`
- `REQUIRED_REFERENCE_SECTIONS`（`DW-C00` は既に登録済み）
- `STAGE_DISPATCH_CONTRACT`
- `_ALL_OPERATIONS`

### 3. guard mutation テスト

採用 case 名は `condition_waiter_deleted` とする。

[test_check_docs.py:4321](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t625-waiter-dispatch/orchestrator/tests/test_check_docs.py:4321) の `condition_land_operation_deleted` 分岐直後、現行4328行の前へ挿入する。結果は新4328〜4334行。

```python
    elif case == "condition_waiter_deleted":
        _rewrite_matching_lines(
            root,
            ".claude/commands/dev-wave.md",
            lambda line: line.startswith("| 24 |"),
            lambda line: "",
        )
```

[test_check_docs.py:4588](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t625-waiter-dispatch/orchestrator/tests/test_check_docs.py:4588) の `_COMMAND_GUARD_CASES` で、`condition_land_operation_deleted` の直後へ挿入する。先の7行追加後の結果位置は4596行。

```python
    "condition_waiter_deleted",
```

[test_check_docs.py:4658](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t625-waiter-dispatch/orchestrator/tests/test_check_docs.py:4658) の `_COMMAND_GUARD_NEEDLES` で、`condition_land_operation_deleted` の直後へ挿入する。先行する8行追加後の結果位置は4667行。

```python
    "condition_waiter_deleted": "条件 dispatch '24' が契約と不一致",
```

既存 `condition_supervisor_deleted` / `condition_land_operation_deleted` との差分は、case 名、削除対象の行頭 `| 24 |`、期待 needle の key `24` だけである。`_COMMAND_GUARD_EXPECTED_COUNTS` は case list から既定値1を作るため編集しない。

[test_check_docs.py:476](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t625-waiter-dispatch/orchestrator/tests/test_check_docs.py:476) の synthetic fixture は `CONDITION_DISPATCH_CONTRACT.items()` から行を自動生成する。契約追加により次の行が自動生成されるため、fixture 本体は編集しない。

```text
| 24 | synthetic | `docs/dev-wave/core.md`: `DW-C00` |
```

`_OPERATION_CONDITION_KEYS` は operations path だけを抽出するため、core を指す `24` は含まれず、19件のままである。

## byte・最長行予算

追加行の逐語計算は次のとおり。

- 行本文: 82文字、UTF-8で126 B
- 改行 LF: 1 B
- ファイルへの純増: `126 + 1 = 127 B`
- 追加後: `8908 + 127 = 9035 B`
- 上限9500 Bに対する余裕: 465 B
- 追加行は82文字。現行最長137文字より短いため、追加後も最長137文字
- 最長行上限140文字に対する余裕: 3文字

したがって予算引き上げなしで収まる。

## 静的な検査影響

| 経路 | 静的判定 |
|---|---|
| 入口の byte／行長 | `check_docs.py:3517-3555`。9035 B／137文字なので上限内 |
| 条件 key・参照・行数 | `_dispatch_tables` と `check_docs.py:3894-3907`。`24` が契約・入口の双方にあり、行数1なら整合 |
| core 参照 | `DW-C00` は既に必須節かつ一意。`core.md` の追加編集不要 |
| synthetic baseline | 契約から24行を自動生成するため追従する |
| guard positive control | case、mutation 分岐、needle のいずれかが欠けると失敗する。期待違反数は1 |
| operation pin | 正しい案では不変。誤って `_OPERATION_NUMBERS` に24を加えると `test_operation_contract_pins_exact_section_set`、段5/6契約、存在しない `DW-O24` 検査が赤くなる |
| `condition_all_operations_deleted` | `24` は core 条件なので対象外。期待件数19は変更しない |
| 段 dispatch | 無変更。`wave 開始` の `DW-C00` を削れば既存段契約検査が赤くなる |

入口の検査には次の実装上の差がある。

- 行数は key ごとに厳密に1件を要求する。
- key 集合は契約側と抽出側の和集合を走査するため、欠落・余分な抽出済み key を拒否する。
- 列数は「3列以上」しか要求せず、厳密な3列検査ではない。提案行自体は3列である。
- 発火条件の逐語は契約に保持されず、文言変更を直接比較しない。本変更で literal pin まで追加するのは scope 外。

厳密な3列検査と `leaked_tokens` 診断を持つ `_condition_dispatch_table` は、`docs/ai-provenance.md` の条件表にだけ使われ、dev-wave 入口には使われない。

### `DW-` token の leak 判定

発火条件セルへ Markdown code span の `DW-C00` を書くと赤くなる。ただし専用の `leaked_tokens` 診断ではない。入口は `_dispatch_pairs_from_line(line)` に行全体を渡すため、参照 path より前の `DW-C00` が `("<unbound>", "DW-C00")` という余分な参照として入り、「条件 dispatch '24' が契約と不一致」になる。裸の `DW-C00` は正規表現が backtick を要求するため検出されない。

採用する発火条件セルには `DW-` token を置かないので、この問題は生じない。

## Skill への波及

[SKILL.md:14](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t625-waiter-dispatch/.agents/skills/dev-wave/SKILL.md:14) は入口を共通 dispatcher として参照し、[SKILL.md:21](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t625-waiter-dispatch/.agents/skills/dev-wave/SKILL.md:21) で条件直前の再読を委譲している。条件表や key を複製していないため編集不要で、Skill の literal・byte・interface 検査にも波及しない。

`DW-C00` 本文、既存条件行、列数/leak 検査機構の強化、予算変更はすべて scope 外。read-only sandbox のためテストおよび `check_docs` は実走しておらず、緑は主張しない。

## 総括

採用 key は新規単調増加の `24` とし、削除済み07／O15は復活させない。  
入口へ裁定逐語の3列行、契約へ `"24": _pairs(_CORE, "DW-C00")` を同一変更単位で追加する。  
`condition_waiter_deleted` を mutation・case list・needle map の3箇所へ登録し、fixture は自動生成を使う。  
入口は9035 B／最長137文字に収まり、core・既存行・予算・Skill は変更しない。  
テストは未実走であり、関連テストと検査の実走は親が行う。