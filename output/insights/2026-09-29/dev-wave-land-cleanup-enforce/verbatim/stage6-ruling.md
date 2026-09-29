# 段 6 裁定 (review A2 = 正しさ・損失、review B2 = 過剰・削除、2026-09-29)

| 所見 | 判定 | 採否 |
|---|---|---|
| A2-1 退避経路の wave 条件 (a) を削除直前の再検査で見ない (`wave=None`) | real。条件が途中で失効しても撤去が進む (撤去の受理集合が裁定より広い) | 採用 (fix F1) |
| A2-2 Stop hook の stdin に時間・サイズ上限がない | 一部 real。実入力は Claude Code の有限 JSON で実害は小さいが、対策が安い | 採用 (fix F2: 1 MiB 上限 + settings の hook timeout 10 秒) |
| A2-3 退避条件の競合 test がない | real | 採用 (F1 の負例 test) |
| B2 DW-O28 の「子 branch は `-D`」が実装 (`update-ref -d` + 期待 OID) と食い違う | refuted。`update-ref -d` も非統合 branch の強制削除で意味は同じ。期待 OID 照合は安全側の上乗せ。DW-O28 は 996/997 bytes で追記不能 | 不採用 (decisions に実装形を記す) |
| B2 Stop test が毎回 git repo を作る | nit。所要への影響は未実測で小さい | 不採用 |
| B2 退避経路で未使用の `ancestry` 計算 | nit | 不採用 |
| B2 hooks/README の「何も拒否しない」が block と紛らわしい・冒頭と重複 | real (docs) | 採用 (親が docs で直す) |

B2 の「止まらない経路」(wave 本体の reflog rc=20、manifest 外の補助木、symlink path の rc=2、合図待ち、main に戻ってからの終了、main 前進以外の rc=30) は裁定範囲外として後送し、insight に記す。

## 変異の追加登録 (fix 前)
| ID | 変異 | 殺すべき test |
|---|---|---|
| M13 | 削除直前の再検査で wave 条件を見ない (fix F1 を外す) | F1 の新しい負例 (退避開始後に wave が非祖先へ動く) |
| M14 | stdin の 1 MiB 上限を外す | F2 の新しい subprocess test (上限超過で通す) — 上限を外すと巨大 JSON を読んで判定へ進むので、payload を「読めれば block される形」にして単一理由にする |
