# 段 4 裁定 — [T-2098]

## 総括

段 3 の 2 レンズは BLOCKER 4 件 (A-F1、A-F2、B1、B2) を含む 21 所見を返した。**全 21 件を real と裁定し、
20 件を採用、1 件 (A-F9) を部分採用する。** plan v1 はそのまま段 5 へ渡さない。plan v2 を以下に確定する。

## 裁定の中核 — 時計を跨がない分解に組み替える

レンズ B の B2 が plan の因果 anchor を反転させた。実装 (`tools/pegasus/dispatch_compute.py:3751`
と `:3775`) では `intent → qsub → qsub 復帰 → confirm` の順であり、**`confirm` は NQSV の
`Created` より後**である。plan は `confirm` を Created の前側 anchor に置いていた。逆である。

これを直すと同時に、B1 (login / compute / scheduler の mtime を単一時計と扱えない) も解ける。
**時計を跨ぐ引き算を主推定量から全部追い出す。**

session `s`、shard `j`。`F` `H` は login node が書く mtime、`C` `E` は NQSV 会計時刻。

| 記号 | 定義 | 時計 |
|---|---|---|
| `S_s` | `max_j H_j − min_j F_j` (session envelope) | login 内で閉じる |
| `Jmax_s` | `max_j (E_j − C_j)` (最長単体 job) | scheduler 内で閉じる |
| `Env_s` | `max_j E_j − min_j C_j` (scheduler envelope) | scheduler 内で閉じる |
| `Skew_s` | `Env_s − Jmax_s` | scheduler 内で閉じる |
| `Rout_s` | `S_s − Env_s` | 2 つの duration の差。静的 offset は相殺する |
| `Rpair_s` | `S_s − Jmax_s` | 同上 |

恒等式 `Rpair_s = Rout_s + Skew_s` が成立する。**3 量とも静的な時計 offset に依存しない**
(duration どうしの差だから)。残るのは session 内の drift だけであり、これは別項で上下に挟む。

`Rout_s = (max_j H_j − max_j E_j) + (min_j C_j − min_j F_j)` の 2 項分割は**時計を跨ぐ**ので、
raw 値として別枠に出し、offset を含むと明記する。主推定量の分解には使わない。

## 各所見の裁定

| ID | 判定 | 採否 | 対応 |
|---|---|---|---|
| A-F1 | real | 採用 | **成果物を「75 秒の分解」と呼ばない。**「75 秒は非対差であって量として成立しない」を第一の結論とし、`Rpair` `Rout` `Skew` を別名の新推定量として定義する |
| A-F2 | real | 採用 | `Env_s` を導入。`Rpair = Rout + Skew` で dispatch skew を分離する |
| A-F3 | real | 採用 | **cohort 規則は復元できる。** `output/insights/2026-08-29_acceptance-speedup-tmpdir/README.md:44-48` に「母集合 568 / dispatch-intents なし 1 / confirm・handled 欠落 18 / 集計対象 549」がある。日付 cutoff を掃引して 568・549・中央値 338 を再現できるかを**反証可能な検査**として置く。再現しなければ「再現せず」と書き、合わせ込まない |
| A-F4 | real | 採用 | `receipt.result.runner_binding.tested_main` で checkout 別、月別に層別する。混合集団であることを成果物本文に明記する |
| A-F5 | real | 採用 | 各検査を `恒等式` / `自己整合` / `診断 (合否なし)` / `反証可能` の 4 種に分類して出す。A-F3 の再現検査が唯一の外部反証可能検査である |
| A-F6 | real | 採用 | oracle を 3 shard 全部の会計値で作る。親が射影する |
| A-F7 / B1 | real | 採用 | marker を writer host (login / compute / scheduler) で分類する。**cross-host の mtime 比較を主結論に使わない** |
| A-F8 | real | 採用 | `Ended→handled` を poll / 収集 / merge へ分けて呼ばない。保存測点が無い |
| A-F9 | real | **部分採用** | `--expected-sessions` gate、固定行帯、構造化 stdout protocol、未使用 counter を削る。除外 counter は正直さに要るので残す |
| A-F10 | real | 採用 | `--output-dir` は入力 root の外であることを script が起動時に検査する |
| A-F11 | real | 採用 | quantile は nearest-rank に固定し方式を出力へ書く。同率 shard は全候補件数だけ出す |
| B2 | real | 採用 | anchor を `intent < Created < confirm` に直す。上記の中核裁定で吸収 |
| B3 | real | 採用 | `queue_wait_s` は「qsub 復帰→qstat RUN 初観測」であり会計 queue 待ちの代用にしない。診断として別枠 |
| B4 | real | 採用 | 会計 file の glob に `dispatch.sh.e*` を含める。`Created` / `Request Name` は dispatcher の gate が要求していないので、欠落を除外 counter にする |
| B5 | real | 採用 | K=2 を正規として受理する (`tools/acceptance_shards.py:1033`)。K 別に層別する |
| B6 | real | 採用 | complete-case であり長い側が落ちうると本文に明記し、除外 session の outcome 内訳 (queue-wait-timeout 等) を出す |
| B7 | real | 採用 | P2 は「worker の `start()` との並行」までしか静的に示せない。off-path 判定は **login 側 marker だけ**で行う (`login-collection.log` の mtime と `max_j H_j` の比較。両方 login clock)。判定不能件数を別に出す |
| B8 | real | 採用 | 区間名を marker の実意味 (最後の書込み) で書き、事象名に昇格させない |
| B9 | real | 採用 | root `junit.xml` は handled より後なので主推定量の外。付録として「handled 後の親費用」に回す |
| B10 | real | 採用 | 走査は snapshot ではない。**実行前に他の受入 session が走っていないことを親が確認する。** inventory 時刻を記録する |

## 段 5 で実装するもの (plan v2)

Codex `role=author` が解析 script 1 本を書く。**repo へ commit しない。** 親が実行し、
出力を insight へ収め、script 本体は repo 外へ退避して逐語 sha256 を記録する。

主出力は `sessions.csv` / `shards.csv` / `summary.json` の 3 本。stdout は人が読む短い要約だけ。

## 変異事前登録 (DW-M01)

**実装面 (D95 決定 2) の repo 差分は 0 byte になる** — 解析 script は commit しないため。
`DW-S04` により変異 matrix を免除する。受入全走は免除せず、記録 commit 後に land 対象 tip へ投入する。

## scope 外として実装しないもの

- 短縮策の実装・提案 (D1384 が採らないと決めた 3 項を含む)
- 新規 gate・検査・台帳・framework・互換層・一般化 (ユーザーが scope 外と明示)
- 新規の受入走行 (本 wave の受入全走を除く)
- 時計 offset の実測 calibration (新規観測点の提案として別項へ回す)
