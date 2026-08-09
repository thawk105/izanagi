# [T-553] s8c 事前登録の git wall-clock 予算化 — 材料一式

- wave: `dev-wave-t553-git-budget` (branch `worktree-dev-wave-t553-git-budget`)
- base: main `2169a06c`
- 実施: 2026-08-09
- 裁定根拠: [T-692] R1〜R3 のユーザー裁定 (worklog エントリ 347)

## この dir の中身

| file | 内容 |
|---|---|
| `MEASUREMENT.md` | **定数の導出の正本。** 実測 2 本と、そこから RATE / CAP を決めた手順 |
| `measurement-m1-synthetic-48way.json` | 同種 git コマンドを 1 / 16 / 48 本同時に走らせた合成負荷の生実測 (request `898023`、bnode023) |
| `measurement-m2-under-full-suite-load.json` | **pytest 全走 48 worker を負荷に掛けた**生実測 (request `898026`、bnode049) |
| `package.md` | 本 wave が実装せずユーザー裁定へ返すもの |
| `verbatim/` | 段 2〜6 の子出力の逐語 16 本 |

## 実装した内容 (1 行)

`orchestrator/campaign/s8c_preregistration.py` の `_git` が、固定 15 秒ではなく
**stdin の実要求行数から内部算出した上限付き予算**で git subprocess を待つようにした。
呼び出し側に timeout 引数は出さない。

## 最も重要な実測結果

**どちらの計測でも 15 秒に到達しなかった。** 実 48 worker 全走の最中でも、
問題の `cat-file --batch-check` (7,044 要求) は最大 0.588973 秒である。
production は同じ呼び出しで 6 回 15 秒を超えている。
したがって**この失敗は定常的な混雑では説明できず、稀な尾部事象である**。
定数は実測値だけでなく、15 秒で打ち切られた観測から逆算した下界も併せて決めた。
詳細と留保は `MEASUREMENT.md` の §3 と §6。
