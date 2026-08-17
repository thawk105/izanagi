# 段 4 裁定 — 実装しない (4 → 7 → 8 → 9)

## 裁定の骨子

**本 wave は実装差分ゼロとする。** 理由は「直せなかった」ではない。
**既知赤の機序が本 wave で完全に確定し、その結果、残る修理経路が 1 本しかなく、
それが受理集合の意味を変えるためユーザー裁定を要する**からである。
他のあらゆる修理経路は、台帳自身と敵対レンズ 2 本が独立にリワードハックと判定した。

## real と裁定した所見

### R1. 実行ファイル再 hash は [T-1298] の容疑者から構造的に除外される (real / 採用)

台帳 [T-1298] は「`_attempt_loop` 冒頭の codex executable 再 hash と hook 再検証の I/O が疑わしい」と
2 容疑者を挙げていた。**前者は計測区間の外にある。**

- `_hash_file(codex_path)` は `tools/codex_worker_launch.py:1670`。
- 計時の起点 `attempt_started_ns = _monotonic_ns()` は `:1698`。
- sidecar の `phase_duration_s.attempt_preflight` は `attempt_state_created` から
  `attempt_preflight_completed` (`:1774-1776`) までしか測らない。

したがって実測された attempt 2 の 1.04〜1.11 秒に再 hash は含まれない。
**計測区間の中身は `_require_attempt_hook_installation(args.repo_root, args.cwd)` (`:1764`) ただ 1 つである。**
残る構造的容疑者は hook / guard 再検証だけになった。

成果物影響: 台帳の容疑者 2 個が 1 個に縮む。再 hash 削除を修理として land する誤りを防ぐ。

### R2. evidence grace の起点が launcher 自身の preflight を含む (real / 採用、ただし実装しない)

**これが F57 evidence-grace 型の完全な機序である。**

- `evidence_deadline_ns = state.started_ns + evidence_grace_s` (`tools/codex_worker_launch.py:1797-1800`)。
  起点は preflight の**前**。
- 子の spawn は preflight の**後** (`:1778`)。
- 強制停止条件は「deadline 到達 かつ rollout evidence 未着」(`:1882-1891`)。
  spawn 直後の最初の poll では `state.session_ids` が空なので必ず成立する。

したがって **preflight 所要が evidence grace を超えた瞬間、子は生まれた直後に必ず殺される。
子の挙動は一切関係しない。**

一次資料の bundle と 1 ミリ秒精度で一致する (F57 2026-08-17 エントリ):

| worker | attempt 2 preflight | SIGTERM |
|---|---|---|
| gw27 | 1.053 秒 | 1.054 秒 |
| gw33 | 1.042 秒 | 1.043 秒 |
| gw47 | 1.105 秒 | 1.106 秒 |

**さらに重要な含意:** preflight が正常な 0.29 秒でも、子が実際に得る猶予は
公称 1.0 秒ではなく 0.71 秒である。**この gate の実効閾値は最初から負荷依存であり、
本番既定 (`--evidence-grace-s 90`) でも構造は同じ**で、余裕が大きいだけである。

**実装しない理由:** 起点を spawn 後へ動かすと、現行では強制停止されていた実行が
accepted の 7 条件へ到達しうる。レンズ A はこれを「高速化ではなく受理集合の拡張」と判定した。
`--evidence-grace-s` の意味を定義した decision も help 文も repo に存在しない (実測) ため、
**意図が確定していない契約を親が一方的に決めることになる。** DW-S04 に従い裁定パッケージへ返す。

### R3. retry ごとの hook / guard / 実行ファイル再検証は correctness gate である (real / 採用)

頻度を下げる「最適化」は NO-GO。`test_hook_preflight_is_rechecked_before_each_retry`
(`orchestrator/tests/test_codex_worker_launch.py:3409-3431`) が再検証を要求し、
guard drift 時に `codex_spawns == []` を assert する node (`:3278-3310`) もある。
attempt 間 drift を拒否する門であり、受理集合の式に現れないだけで前提状態を守っている。

成果物影響: 「preflight を速くして直す」経路が塞がった。R2 が唯一の修理経路である根拠。

### R4. S2 は「dev_wave_wait 側は支持、mutation 側は未帰属」と分けて記録する (real / 採用)

- `test_dev_wave_wait.py` の 3 node: `2da49c56` が production の mask 汚染を閉じ、
  `_handled_signals_are_unblocked` (`orchestrator/tests/test_dev_wave_wait.py:75-95`) が
  test 入口で blocked を fail、出口で漏れを assert する正例対照になっている。**構造的に支持される。**
- `test_mutation_worktree.py` の node: `2da49c56` の射程外。過去の赤を「同じ xdist worker の
  先行 polluter」で説明するのは**実測でなく仮説**である。`--dist loadgroup` は同居を可能にするが
  保証せず、赤 node と polluter の `gwN` 対応が資料に無い。
- 親の provisional 裁定 (P3) は誤り。fake child は SIGINT/SIGTERM handler を設置してから
  ready を書く (`orchestrator/tests/test_mutation_worktree.py:97-104`)。ready 後の signal 送信は
  必要な happens-before を既に持つ。

成果物影響: 「解消済み」と書くと mutation 側の独立した mask 継承欠陥を未確認で閉じる。
「再発が確認されない」と「構造的に排除済み」を分けて書く。

### R5. F57 と S2 はどちらも D362 の 3 条件を同時に満たさない (real / 採用)

D362 の「既知の赤」は (i) 原因特定済み (ii) 差分から構造的に到達不能 (iii) main 単独で再現、の
同時成立を要する。両族とも (iii) が不成立 (単独再走は緑)。
**過去これらを通して land できていたのは D362 例外ではなく、全走を再投入して緑を得ていたからである。**
「既知赤」という呼称は受領証の状態を誤記している。

成果物影響: この族に D362 を援用して land する運用は成立しない。記録して誤用を防ぐ。

### R6. 「1 走 0 failed」の一般化限界 (real / 採用)

本 wave の 09:04 全走 (0 failed) から言えるのは「その tip・その収集集合・その worker 割当・
その負荷で常時必敗する赤は無い」までである。順序依存・attempt 2 依存・負荷依存の決定的な赤、
低頻度 flake、95 skip 経路は否定できない。brief の記述をこの限定付きへ改める。

## 不採用と裁定した経路 (すべてリワードハック面)

| 経路 | 不採用の理由 |
|---|---|
| evidence grace / wall の引き上げ | 台帳 [T-1298] 逐語「上げるだけだと『遅くなっても通る』方向に受理集合を広げる」。`:5926-5986` の強制停止 assert を到達しにくくする |
| hook / guard 再検証の頻度削減 | R3。attempt 間 drift の門を無力化する |
| 待ち合わせと称した sleep | 新しい happens-before を作らず、assert を scheduler 確率へ依存させる |
| fixture の real repo を tmp mirror へ退避 | guard drift 時の `codex_spawns == []` (`:3278-3310`) を mirror への assert へ置換し、実配線の破損を control が見なくなる |
| 受入での xdist 直列化 | 裁定条件「fixture 側で断てない共有 mutable state」が不成立。sessions と receipt は tmp へ分離済み、docs authority は不一致なら rc=2 |
| 計装のさらなる追加 | R2 で機序が確定したため、追加計装が解錠する道 (なぜ 3.6 倍か) は R3 により既に塞がっている。診断のための診断になる |
| 実行ファイル再 hash の削除 | R1。計測区間外なので観測値を変えない |

## 変異事前登録 (DW-M01)

実装差分ゼロにつき、DW-S04 の「『実装しない』と裁定済みで実装差分ゼロの wave だけ変異 matrix を
免除する」に該当。**受入全走は免除しない。**

## ユーザーへ返す裁定パッケージ

**問い: `--evidence-grace-s` の起点をどこにするか。**

現状 (a) は「attempt state 作成時」= launcher 自身の preflight を含む。

- **(a) 現状維持。** 受理集合は不変。ただし evidence gate の実効閾値は
  `grace - preflight` のまま負荷依存で、F57 evidence-grace 型のフレークは再発し続ける。
- **(b) 起点を spawn 完了時へ移す (親の推奨)。** 子は公称どおりの猶予を必ず得る。
  gate が「子が証拠を出すまでの時間」を測るという名前どおりの意味になり、決定的になる。
  総時間は `max_wall_clock_s` が引き続き有界化する (`:1765-1773` で spawn 前に再検査)。
  **代償: 現行で preflight 中に期限切れとなっていた attempt が子起動後まで生存する。**
  レンズ A はこれを受理集合の拡張と判定した。
- **(c) 起点は据え置き、preflight 所要を deadline から控除する。** (b) と実効は近いが、
  控除量が観測値依存になり、gate の閾値が再び可変になる。親は推奨しない。

**親の推奨は (b)。** 理由は、現行 (a) の実効閾値が既に非決定的であり、
「負荷が高い日は子の猶予が短くなる」という gate は測ろうとしている性質を測っていないためである。
(b) は緩和ではなく、gate を宣言どおりの意味へ戻す是正だと考える。
ただしレンズ A の「受理集合の拡張」という分類は正しく、**この択一は親の権限を超える。**
