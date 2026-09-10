# 受入全走フレーク (F57 族) の機序帰属 — 予算の縁に張り付いた設計だった (2026-08-13)

wave = `dev-wave-t1005-acceptance-flake-attribution` /
branch `worktree-dev-wave-t1005-acceptance-flake-attribution`。
[T-1005] の執行。**診断 wave であり実装差分はゼロ。** 恒久対応の採否は裁定へ返す
(`package.md` の R1〜R4)。

## 1. 何を見に来たか

`docs/failures.md` F57 は 2026-07-30 から 20 回以上の再発を記録し、一貫して
「原因未確定」「恒久対応は [T-190] の失敗 artifact 保存」としてきた。
2026-08-13 の受入 8 走で**同一 file の失敗が 21 / 8 / 3 / 0 件と振れた** — 既載の再発が
すべて 1〜2 件だったのに対し 1 桁大きい — ことを受け、機序と併発条件を特定しに来た。

## 2. 決定的な実測 — 予算の余裕がほぼゼロだった

走 A (`acceptance.log`、bnode130、request 908484) の失敗 21 件すべてに、
receipt の job 側 wall clock が記録されていた。

| 量 | 値 |
|---|---|
| テストが渡す予算 `--max-wall-clock-s` | **3.0 秒** |
| 実測 `receipt_actuals.wall_clock_s` (21 件) | **3.0099 / 3.0460 / 3.1160 / 3.1369 / 3.2324 / 3.2650 …** |
| 超過幅 | **0.010〜0.265 秒 (0.3%〜9%)** |
| 同じ record の `attempt.wall_clock_s` | 0.716〜0.988 秒 |

**「多秒の停止が起きた」のではない。48 並列下では job 全体の所要が予算の縁に常時張り付いており、
わずかな揺らぎで境界付近にいたテスト群が一斉に越える。**

この 1 点で、F57 が説明できずにいた性質が揃って説明できる。

- 失敗 node が毎回移動する → 境界付近にいるテストは走ごとに違う
- 単独再走で再現しない → 単独なら所要が予算を大きく下回る
- loadavg と相関しない (既載に 0.80 での発火と 17.42 での発火が併存) → 必要な摂動が極小
- 件数が 1〜21 と振れる → 摂動の大きさで境界を越える集合の大きさが変わる

## 3. 一見矛盾した診断行の正体

失敗診断は「予算 3 秒に対し `wall_clock_s=0.716` で wall 超過」という不可能に見える組を出す。
これは**異なる 2 つの時計を同じ名前で読んでいる**ためである。

- wall gate が判定に使うのは **job clock** (`codex_worker_launch.py:1244`)。起点は `:35` の
  module import 時刻。
- 失敗診断が印字するのは **attempt clock** (`:1540`)。起点は `:1347` の `AttemptState` 生成。

段 3 レンズ A は attempt clock で wall 判定する経路を探索し、**存在しないことを確認**した。

## 4. 判定不能として残したもの (規律 3)

走 B / C の述語 (evidence grace 満了、`residual=None`) はコード経路としては実在するが、
**どの入口を通ったかを receipt が保存しないため確定できない。**

- `codex_exit_code=-9` は外部 SIGKILL (OOM・scheduler) でも同値。識別する情報が無い。
- 必須同伴と見えた `metering_status='missing'` には一次資料内に反例がある
  (`auto-acceptance-3.log`: -9 かつ metering complete)。
- `evidence_forced_stop` は代入されるだけで receipt にも受理判定にも出ない (`:349` / `:1497`)。
- `residual=None` の出所は 4 つ以上あり (identity 自体が `None`、`/proc` の `scandir` 失敗、
  個別 `stat` 読取失敗、parse 失敗)、区別されない。

**バーストの述語が均一なのは「1 原因」の証拠ではない。** 実装が `if/elif` で複数原因を
単一 field へ縮約し (`:1461-1475`)、`limit_trigger` が立つと evidence deadline を見ずに
break する (`:1487-1499`)。走ごとに失敗集合が違うのは、たまたまその phase にいたテストだけが
終端述語を出す selection effect で説明できる。

## 5. 併発条件

- **計算ノードの co-tenancy ではない。** gen_S は 1 job = affinity 全数 48 で実質専有。
  3 バーストは別ノード (bnode130 / bnode019 / bnode010)。
- **並行 codex 子は判別子でない。** 2026-08-13 の窓では codex 子は**緑の走とも重なっている**。
  → [T-139] land2 の K5 (lease を他 wave の codex 子まで広げるか) は
  **親推奨「現状維持」を支持する**実測になった。
- **48 並列という条件は支持される** (F57 既載の `-n 8` 緑との対照、および §2 の縁張り付き)。
- **「共有 Lustre が原因」までは分離できていない。** phase 別時刻も I/O latency も記録が無く、
  M1 の git I/O・M2 の rollout 発見・M3 の `/proc` 走査のどれとも決められない。未分離として返す。

## 6. 段 3 の成果

敵対 2 レンズの 16 所見はすべて **real**、refuted ゼロ。**うち 8 件が親の brief を直接壊した**。
親は全件を実装・一次資料に当たって確認し、撤回した主張を `verbatim/s4-ruling.md` の表に残した。
撤回の代わりに得たのが §2 の実測である (レンズ A が一次資料から job clock を掘り出した)。

## 7. 成果物

- `package.md` — 裁定パッケージ (選択肢 O1〜O6 の親推奨、O2 で壊れる 12 nodeid の列挙、R1〜R4)
- `verbatim/s3-consult-sol.md` / `s3-consult-luna.md` — 敵対 2 レンズの逐語
- `verbatim/s4-ruling.md` — 段 4 裁定の全文
