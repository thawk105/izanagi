# [T-851] fan-out exact-N 本走 — 実行不能の実測と逐語

wave branch `worktree-dev-wave-t851-fanout-exact-n`。実装差分ゼロ (docs のみ)。
裁定の全文は `verbatim/s4-adjudication.md`。

## 結論

**fan-out の exact-N 本走は、この機体では実行できない。** 本走は 1 度も投入していない。

admission の `_attest_measurement_cgroup` は測定 cgroup の `memory.peak` を必須にするが、
この kernel (5.15.0-186-generic) の cgroup に `memory.peak` は存在しない。
`run_fanout` は既定引数で attestation を固定し CLI に override が無いため、
どの admission receipt も必ず拒否され、shard は 1 本も起動しない。

## 実測 (2026-08-16 09:05-09:10 JST、Pegasus login node)

| # | 測ったこと | 結果 |
|---|---|---|
| 1 | `uname -r` | `5.15.0-186-generic` |
| 2 | `user-31609.slice` と配下 session scope の `memory.peak` 実在 | **不在** (`memory.current` / `memory.max` / `memory.oom.group` / `memory.stat` は実在) |
| 3 | 生きた `populated 1` の cgroup へ `_attest_measurement_cgroup` を直接呼ぶ | **`False`** |
| 4 | 不正 receipt で `mutation_fanout.py run` を起動 (生死確認) | bounded scope の再 exec は成功し、**scope 内の process** が rc=2。scope 機構自体は生きている |
| 5 | login headroom (08:05 JST) | user slice `memory.max` 16 GiB、`admission_bytes` 6.15 GiB、実効天井 14 GiB、固定予約 2 GiB → 見積もり可能残 5.85 GiB |
| 6 | 変異 harness の flock 鍵 | repo 絶対 path の sha256 先頭 20 桁 (`mutation_harness.py:2090-2111`)。並行 wave とは別鍵 |

## 採れなかった計測

[T-851] が指定した 6 項目のうち、**shard が起動しないため 5 項目は採取不能**である。

| 項目 | 採否 |
|---|---|
| cgroup `memory.current` の 3 反復 | **不可** — 反復は exact-N の実行を伴い、admission を通らない |
| Git admin burst | **不可** — N shard が worktree を作らない |
| `df -Pi` | 採取自体は可能だが、比較対象となる本走が無いため意味を持たない |
| 全 request 対応 | **不可** — qsub request が 1 件も出ない |
| fair-share | **不可** — 同上 |
| 最終 `git worktree list` | 残渣ゼロ (本走を投入していないため自明) |

## 段 3 の敵対 2 本が構成した経路 (本 wave では実装しない)

`verbatim/s3-lensA.md` (gate の自己申告化) と `verbatim/s3-lensB.md` (資源・他 wave への被害)。
両者は独立に `memory.peak` 不在へ到達し、レンズ B は
`docs/pegasus-runbook.md` が同じ事実を 2026-08-01 に実測記録済みであることを指摘した。

- receipt 作成前の certification 3 走そのものが admission を通らない bootstrap になる。
- attestation は測定 cgroup と wrapper 実行を束縛しない。無関係な sleeper 1 本と、
  `..` を挟んだ同一 scope の別表記 3 通りで 3 反復を偽装できる (重複検査が raw string 比較)。
- identity は HEAD ではなく caller 指定 commit の 2 blob にしか束縛されない。
  `mutation_fanout_contract.py` は identity 外なのに split と merge 判定を実行する。
- registry 差分は path 集合の Counter 比較だけで、同一 path の再束縛を検出しない。

receipt 偽造の族は [T-849] と同じ (同一 Unix user が攻撃者) であり、
プロトタイプ基準で見送り済みの族に属する。本 wave はこの族を再裁定していない。

## 却下した実装案 (gate が通っても採らない)

- kernel `memory.peak` を `memory_current_bytes` sample として書き足す案 — その時刻に
  存在しない観測を記録へ足す捏造であり、schema を変えずに別統計量を同名 field へ詰める意味拡張。
- group root の再帰削除 — 他 wave がその下を scratch に使っていれば相手の evidence を消す。
