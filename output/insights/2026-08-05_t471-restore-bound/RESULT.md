# [T-471] 実測結果 — 復元は 10 s 予算の 3 桁下、しかし T-360 条件 3 は R では閉じない (2026-08-05)

- `authority: none`
- `default_effect: no-state-change`
- 判定は `preregistration.md` (実測前に凍結) の規則への機械的当てはめ。可変状態の正本は worklog。

## 1. 実測 (attempt `rbound-a1`)

計算ノード `bnode064`、PBS `0:889476.nqsv`、Lustre `/work`、kernel 5.15.0-173-generic、
Python 3.10.12、commit `24f3f12`、経過 76 s。**500 trial すべて成功、`valid=true`。**
生証拠は `evidence/rbound-a1/restore-bound.json` (全 trial の生値を含む)。

| arm | 構成 | min | p50 | p90 | p99 | max |
|---|---|---|---|---|---|---|
| `A-e0` | C2, E=0 | 2.86 | 2.99 | 3.09 | 3.58 | 37.72 |
| `A-e143-fresh` | C2, E=143 (hot) | 33.91 | 34.53 | 35.07 | 35.74 | 38.80 |
| `A-e143-aged` | C2, E=143 (attempt 冒頭に作成) | 34.50 | 54.10 | 54.77 | 61.78 | 71.79 |
| `A-b240-n1` | C1, n=1, B=240,600, E=143 | 33.08 | 33.61 | 34.15 | 42.86 | 45.65 |
| `A-p2-synth` | C2 bytes を 2 親へ, E=[143,97] | 55.14 | 56.17 | 56.80 | 57.41 | 58.11 |

単位はミリ秒。**全 500 trial の実測 max = 71.79 ms。**

これは `R_restore_observed` であり、凍結記号 `R_restore_bound` (= 上限) では**ない**
(`preregistration.md` §0)。妥当性は上の 5 arm・この 1 allocation・この時刻に限定する。

## 2. 何が支配項か

- **`__pycache__` の purge が支配項で、bytes はほぼ効かない。** `E=0` の 2.99 ms に対し
  `E=143` は 34.53 ms。一方、対象を 69,659 bytes (2 file) から 240,600 bytes (1 file) へ
  3.5 倍にしても 34.53 → 33.61 ms とほぼ動かない。
- **entry あたりの限界コストは arm を跨いで一致する。** `(p50 − p50(E=0)) / E` は
  `A-e143-fresh` 0.2205、`A-b240-n1` 0.2141、`A-p2-synth` 0.2216 ms/entry。
  E と bytes が別々に異なる 3 arm で同じ傾きが出ることは、arm の setup が実在したことの
  内的整合証拠でもある (下記 §5)。
- **冷却は効く。** `A-e143-aged` の p50 は fresh の 1.57 倍 (54.10 / 34.53)、
  限界コストは 0.3574 ms/entry。dentry cache が冷えた状態の unlink は明確に重い。
- **`[T-360]` の実運用経路では `E > 0` が主ケースである** (`preregistration.md` §4)。
  `runner_mode=dispatch` では `PYTHONDONTWRITEBYTECODE=1` が計算ノードへ伝播しないため、
  pytest が .pyc を書く。したがって参照すべきは `A-e0` ではなく `A-e143-*` である。

## 3. [T-399] 凍結式への当てはめ

`preregistration.md` §7 の規則どおり、次の 2 つを分けて記録する。

1. **凍結分岐による machine verdict**: 本 wave は `R_restore_bound` (上限) を確定しなかった。
   非定常な Lustre の wall-clock に対し、有限標本の max は上限ではないためである
   (段 3 レンズ A #1/#10、レンズ B #2 を親が real と裁定)。よって `R_restore_bound = null`、
   凍結分岐により **十分性 = `UNKNOWN`**。
2. **R 非依存の算術事実**: T-399 authoritative attempt の左辺は凍結代入規則により
   `cleanup_elapsed = 5.013 s` に固定される。`R ≥ 0` である以上 `5.013 ≥ 10 + R` は
   **R の値によらず偽**である。

**どちらの読みでも運用結論は同一** — T-399 の attempt では [T-360] 条件 3 の十分性を
certify できない。そして (2) が示すのは、より強い事実である:

> **`R` を測れば条件 3 が閉じる、という従来の見通しは成り立たない。**
> 条件 3 は R の精度の問題ではなく、「production の cleanup 列が grace 内で実際に完走した
> attempt が 1 つも無い」という証拠の問題である。

これは「実 grace が物理的に不足した」ことの証明ではない (左辺は「実際に使えた時間の下限」であり、
この不等式は片側の certify 器である)。射程の詳細は
`../2026-08-04_t399-t400-signal-mitigation/verdict-preregistration-erratum-3.md`。

**本 wave は [T-360] 条件 3 を閉じない。変異本走を計算ノードへ束ねる安全根拠は成立していない。**

## 4. 設計への含意 (実測が実際に答えたこと)

復元は **数十ミリ秒**であり、`_stop_process` の 10 s 予算に対して 3 桁小さい。したがって:

- cleanup 予算 `C_repo_known_safe = H_stop_actual + R + H_head` の支配項は
  **R ではなく `H_stop_actual` (最大 10 s の 2 段 wait)** である。R の寄与は 0.1 s 未満。
- 未計測項のうち `H_head` (`_assert_head` の git subprocess) は、Lustre 上の git 呼出しである以上
  **R より大きくなりうる**。R を精密化するより `H_head` を測るほうが予算への寄与が大きい。
- 条件 3 を閉じる新 attempt を設計するなら、その probe の cleanup は
  「10 s + 0.1 s 程度」の仕事をして完走する必要がある。現行 nominal grace 60 s に対して
  十分な余裕がある — **足りないのは時間ではなく証拠**である。

warn margin の設計は `warn-margin.md`。

## 5. 実測 attempt の忠実性 (親の独立検算)

段 6 の焦点再レビューは、計測器が「偽の setup / 偽の harness / 非交互化を検出しきれない」と
指摘した (7 件 partial + 新規 6 件)。親はこれらを real と認めたうえで、
**検出器を足すのではなく、実際に走った attempt の忠実性を生証拠から直接検算した。**

| 疑い | 検算結果 |
|---|---|
| 交互化されていない可能性 | 生 trial 500 件の arm 列が凍結順の exact round-robin と完全一致 |
| 偽 harness を測った可能性 | 記録 `harness_sha256_before` = `after` = 実ファイルの sha256 = `HEAD:tools/mutation_harness.py` の内容 sha256 |
| 偽 case を測った可能性 | 記録された spec sha256 が親の独立 inventory 走査の値と一致 (C2 = `1ecd2111…`) |
| E を偽って軽く作った可能性 | E と bytes が別々に異なる 3 arm で entry あたり限界コストが 0.2141〜0.2216 ms/entry に一致。偽 setup ではこの E 依存性は出ない |
| 失敗を隠した可能性 | 失敗 trial 0、`restore_call_count != 1` が 0、sequence が 0..499 で連続 |

**残る限界 (未閉塞、意図的に閉じていない):** 計測器は、将来 driver が改変された場合に
偽の setup・偽の source bytes・非交互化を静的検査だけで殺しきれない。本 wave の公表値は
診断値であって上限ではない (§3) ため、この限界は結論を変えない。閉じるコストのほうが
得られる保証より大きいと親が裁定した。詳細は `erratum-1.md`。

## 6. 妥当性の限定 (凍結どおり)

- 測った 5 arm・1 allocation・1 node・1 時刻に限定する。単調性は主張しない。
- 適用条件: 復元中に追加の SIGINT / SIGTERM が到着しないこと。
- fault model: `_restore_targets` は fsync しない。支えるのは
  「live node・Lustre client 生存・return 後に process だけが kill される」契約までであり、
  書込み途中の SIGKILL・node 障害・power loss に対する durability は支えない。
  これは R の秒数ではなく復元定義の問題である。
- `A-p2-synth` は実在する変異ではない合成 profile である。
