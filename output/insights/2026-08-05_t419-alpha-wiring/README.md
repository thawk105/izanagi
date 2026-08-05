# [T-419] 方式 α の本番結線 — 逐語と変異台帳

dev-wave (2026-08-05)。branch `worktree-dev-wave-t419-alpha-wiring`。
本 wave の所有 = [T-419] U-2 entry condition (i) = 方式 α を本番 attestation の取得経路へ結線する
(= [T-528])。較正の再取得・登録・pin closure は下流。

## 収録物

| ファイル | 内容 |
|---|---|
| `brief.md` | 段 1 brief (前提実測を含む) |
| `plan-out.md` | 段 2 codex プラン (read-only, reasoning=max) |
| `lensA-out.md` / `lensB-out.md` | 段 3 敵対相談 2 レンズ (両者 NO-GO) |
| `s4-adjudication.md` | 段 4 親裁定 (所見 15 件、変異事前登録) |
| `impl-out.md` | 段 5 実装子 (codex role=author) の報告 |
| `revA-out.md` / `revB-out.md` | 段 6 敵対レビュー 2 本 (両者 NO-GO) |
| `fix-out.md` | 段 6 fix 子の報告 (所見別 closed/partial 表つき) |
| `mutation-spec.json` / `mutation-ledger.json` | 変異事前登録と実走台帳 |

## 実装したもの

`orchestrator/campaign/env_attestation.py` の `probe()` を方式 α にした。

- 走行 CPU を sysfs CPU 集合 ∩ 元 affinity から決定的に等間隔 K=5 点選び、pin しながら
  `/proc/cpuinfo` を K 回読み、**論理 CPU ごとの最小値**を `effective_clock.samples_mhz` にする。
- 方式 identity (`effective_clock.method`) は K・最小 interval・target 選択規則 ID から組み立てる。
  値は `proc-cpuinfo-rotating-min/k5/interval-ns50000000/sysfs-affinity-intersection-evenly-spaced-v1`。
- 読み開始は deadline 方式で 50 ms 以上あけ、最小 horizon `(K-1) × interval` を構造で保証する。
  遅延そのものは拒否理由にしない (過剰拒否を新設しない)。
- 走行 CPU の検査は `/proc/thread-self/stat`。pin mask の exact 検査は interval 待機の**直後**。
  pre / post の走行 CPU 検査と合わせて独立な 3 検査にする。
- affinity は `try/finally` で復元し、復元後に再取得して exact 一致を確認する。復元失敗は
  profile を返さず拒否する。復元失敗が本来の失敗理由を上書きしないよう primary と合成して報告する。
- TSC 測定は affinity 復元完了後に固定する。
- 単読みへの fallback を持たない。巡回不能・pin 不発・K 未達・読み間の CPU 集合/identity drift は
  すべて fail-closed。
- schema key 集合は変えない (`samples_mhz` / `method` / `governor`)。

## 実装していないもの (射程)

較正の再取得・登録、凍結 bytes と `env_contract.py` pin の更新、帯述語・`tolerance_pct` の変更、
`KNOWN_SELF_INCONSISTENT_CALIBRATIONS` の縮小、[T-529] 活性化権限、[T-443]/[T-444]、
α の should-reject 実測 (裁定で「測らずに採る」と確定済み)。

## 段 1 の前提実測

1. 変更前の `probe()` は `/proc/cpuinfo` を 1 回読み `method="proc-cpuinfo"` を出していた。
2. **method 文字列だけを変える 1 行変異では、clock/freeze 系 6 test file 330 件が 1 件も落ちなかった**
   (計算ノード request 891526)。既存被覆はこの取得方式変更を検出しない。検出力は純増分に帰属する。
   変異は即時復元した。
3. login node (96 CPU) での α 実演: 単読みでは 4 CPU が帯外 (23/29/83/85)、走行 CPU を 5 点へ移した
   CPU ごと最小では 1 CPU (29)。機構は効き、恒真にもならない。`sched_setaffinity` は使え、
   affinity は復元できた。1 読み約 20 ms。
   **この実演は機構の存在を示すだけで、本番手続きの妥当性根拠ではない** (§「限定」参照)。

## 段 3 / 段 6 の敵対検証が変えたもの

- **(P4) の撤回。** 親は走行 CPU の検査に `/proc/self/stat` を使うと書いたが、
  `sched_setaffinity(0, ...)` は呼び出し **thread** に効くのに `/proc/self/stat` は
  thread-group leader の stat である。worker thread から probe すると別 task を検査して
  誤拒否・誤裏付けになる。`/proc/thread-self/stat` へ是正した。
- **待機中の pin 外れ。** mask の exact 検査が interval 待機の**前**にあったため、待機中に affinity が
  広げられても pre/post の瞬間だけ target 上にいれば通った。検査を待機の直後へ移した。
- **復元例外による primary failure の消失。** `finally` 内の raise が pin/read の本来の失敗理由を
  置き換えていた。primary と restore を合成して報告する形にした。
- **偽 kill 3 件を走らせる前に潰した。** (a) CPU 集合 drift の負例が CPU を欠落させており、
  集合検査を消しても直後の `mhz_by_cpu[cpu_id]` が `KeyError` になって赤いままだった
  → 余分な CPU を追加する形へ変更。(b) reader 外れ値 fixture が事前計算した target 列に従って
  高値を移しており、巡回を壊しても意味検査が落ちなかった → fake の**実際の走行 CPU**から
  高値ベクトルを生成する形へ変更。(c) 静穏 fixture の K ベクトルが完全一致していたため、
  「全 read の完全一致を要求する」過剰拒否変異を検出できなかった → 帯内のまま read ごとに
  値が異なる系列へ変更。

## 変異 matrix

事前登録 14 件 (負例 13・過剰拒否を検出する正例 1)。**初回走行で 14/14 KILLED、期待 node 完全一致、
SURVIVED 0 / MISMATCH 0** (`mutation-ledger.json`)。単一理由性のために次を分けた。

- M06a (pre 検査) / M06b (post 検査)、M08a (CPU 集合) / M08b (identity) を別変異にした。
- M02 は「K 回のうち最初の snapshot を再利用する」退化へ、M10 は selector の不足拒否・distinct 検査・
  reducer の exact K を同時に緩める三層変異へ再照準した (段 3・6 の指摘どおり、単層では別層に mask される)。
- M11 (γ 相当の外れ値マスク) は受理述語が no-touch の comparator 側にあるため、
  reducer 内で「中央値の 1.2 倍を超える最大 1 CPU を中央値へ潰す」変異として新規領域に anchor を置いた。

## 成果物影響と限定

- certified 受理集合は**閉鎖のまま変わらない**。live probe と登録済み g1 較正の突合せは、
  取得が成功すれば `effective_clock.method` を必ず含む comparison failure、取得が失敗すれば
  `strict attestation probe failed` になる。どちらか一方に確定はしない。
- **実験で 9/9 を得た α と本番手続きは時間窓が違う。** 実験の α 群は randomized pin sweep の
  各 target の先頭読みを束ねたもので群の幅が広く、本番は宣言した 50 ms 間隔の 5 読みである。
  機序 (reader が居る CPU は必ず busy) の除去は時間窓に依存しないが、一過性の吸収 (should-pass 率) は
  依存する。**9/9 を本番手続きの妥当性根拠に使わない。** 本番手続きの計算ノード検証は裁定へ返す。
- **K 回取得したことの事後証拠は成果物に残らない。** outward schema は最小値と method だけであり、
  method は手続きの証明ではない。schema を広げる案は、旧 probe corpus・較正 loader・profile hash・
  登録 artifact・contract pin を同時に動かすため本 wave では採らない (裁定 §2.2、レンズ B が
  file:line で裏取り)。取得 transcript の凍結は別 wave (probe-output v3) として裁定へ返す。
- **α の受理集合は単読みのそれと同じではない。** `min` は上向きの一過性を K−1 回まで消し、
  下向きは 1 回で残す非対称性を持つ。性質として characterization test で固定した。
- affinity を復元しても走行 CPU・cache・P-state は戻らない。暖機の持ち越しは既知限界として残す
  (helper process への隔離と ablation は裁定へ返す)。

## 受入

- 実装後の consumer 13 file: 974 passed / 3 skipped (計算ノード request 891667)。
- fix 後の 7 file: 448 passed (計算ノード)。
- 変異 matrix: 14/14 KILLED。
- 受入全走の値は worklog エントリに記録する。
