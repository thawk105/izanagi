# 変異事前登録の単一理由性検証 (親が実装後のコードで確認)

`DW-M01` は「各変異は位置に加え、同じ入力を拒否する層が前後に無く、無効化時の赤理由が
一つに絞れることをコードで確認する。できなければ登録せず実効 gate へ再照準する」と定める。
実装が着地した現物に対して 1 件ずつ確認した結果を記す。

## 逐語 anchor の実在と一意性

| id | file | anchor | 実在 | 一意 |
|---|---|---|---|---|
| m01 | `s8b_compiler_input.py:45` | `_V3_ROOTS = _V2_ROOTS \| frozenset({"dependency-prefix"})` | あり | 一意 |
| m02 | `s8b_compiler_input.py:1118` | `if len(matches) != 1:` + 直後の `raise` 3 行 | あり | **単独行は非一意** (`:189` にも同じ行がある)。**raise 本文まで含めた 4 行で一意化する** |
| m03 | `s8b_compiler_input.py:1133` | `special_roots.extend(current_dependency_roots)` | あり | 一意 |
| m04 | `s8b_binary_admission.py:239-241` | `current_dependency_prefix_roots=(` + 続く 2 行 | あり | 一意 |
| m05 | `s8b_floor_campaign.py:4396-4398` | `current_compiler_input_dependency_prefix_roots=(` + 続く 2 行 | あり | 一意 |
| m06 | `s8b_compiler_input.py:1049` | `if is_v3 and current_dependency_prefix_roots is None:` | あり | 一意 |

`DW-M04` の「置換対象が一箇所でなければ停止」に m02 が抵触するので、anchor を 4 行へ広げた。

## 単一理由性の判定

- **m01 登録する。** `_V3_ROOTS` を縮めると、正しい v3 の `dependency-prefix` タグが
  `s8b_compiler_input.py:936` の membership 検査だけで拒否される。前段の shape / digest は
  正しく、後段へ到達しない。受理集合が縮む向きの変化。
- **m02 登録する。** `if not matches:` へ潰すと、2 つの current 根に同じ相対 file と同じ bytes を
  置いた**負例が誤受理される**。`matches[0][1] != entry["sha256"]` は通ってしまう。
  origin 側の ambiguity 検査は collector 側の別経路なので、手で組んだ manifest を
  validator へ通す負例には掛からない。**受理集合が広がる向きの変化。**
- **m03 登録する。** special root から current dependency 根を外すと、
  current dependency 根の中を `filesystem` タグで指す再封印 manifest が誤受理される。
  root-tag canonical 性がこの入力に対する唯一の拒否点。**受理集合が広がる向きの変化。**
- **m04 登録する。** issuer が caller 値の代わりに `None` を渡すと、正しい v3 receipt の
  正例が live 検証でだけ落ちる。issuer 前段の admission / binding / snapshot 検査は同じ入力で通る。
  受理集合が縮む向きの変化。
- **m05 登録する。** floor が根を渡さないと issuer 既定の `None` になり、同じく正例が落ちる。
  新規 bridge test だけがこれを殺す。bridge test の実在が登録の前提であり、実在を確認した
  (`orchestrator/tests/test_s8b_dependency_prefix_bridge.py`、159 行、自走 harness つき)。
- **m06 は kill 変異として登録しない — 冗長 gate である。**
  `if is_v3 and current_dependency_prefix_roots is None:` を無効化しても、直後の
  `_canonical_dependency_prefix_roots(None, ...)` が `s8b_compiler_input.py:681-682` の
  `if type(value) not in (list, tuple):` で `"current dependency prefix roots is not a
  root sequence"` を送出する。**両者の発火条件は `is_v3` で完全に一致しており、
  受理集合は 1 bit も変わらない。変わるのは診断文言だけである。**
  `DW-M03`「診断文字列だけの赤を kill にしない」と `DW-M08`「受理集合を変えず構造化シグナルだけを
  pin する変異は kill でなく diagnostic sensitivity pin へ別枠記録する」に従い、
  **m06 は diagnostic sensitivity pin として別枠に記録する。**

  **これは段 6 レンズ B 所見 3 (B3) の是正が、受理面では純増ゼロだったという実測でもある。**
  親は段 4 で B3 を「採用」と裁定したが、実装後に測ると受理集合を変えない改善だった。
  裁定を撤回はしない (診断の明確化として保つ) が、**受理面の強化として数えない。**

## 過剰拒否の正例 (`DW-M01`「受理集合を縮小する wave は承認外の過剰拒否の正例も登録する」)

- **p01:** dependency entry を持たない v3 manifest が、明示的な空 tuple の context で**受理される**。
  m03 / m06 が過剰拒否へ倒れていないことを示す。
- **p02:** 既存 v1 manifest と、既存 v2 の 3 根 (`snapshot` / `fetchcontent-masstree` /
  `filesystem`) の受理挙動が変わっていない。

## 走らせ方 (`DW-M07` / `DW-M08`)

1. **probe:** 全件 SURVIVED 期待で登録し、観測 node を採取する。
2. **本走:** 実測した完全 node 集合を KILLED 期待で登録して走らせる。
   `--runner-mode dispatch`、runner argv へ `--force-dispatch`、
   `--attempt-out` と `--wrapper-attempt` は同時指定。
3. 変異中は親の編集と、worktree へ書きうる子の起動を止める。
   段 6 のレビュー子は read-only だが**現物を読む**ので、変異は
   レビューと fix が終わってからにする (レビュー中に変異させると読ませる現物が壊れる)。
