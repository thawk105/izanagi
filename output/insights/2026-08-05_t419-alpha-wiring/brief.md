# 段 1 brief — [T-419] 方式 α の本番結線 (= T-528 / U-2 entry condition (i))

起点 main = `6d6cd095`。branch = `worktree-dev-wave-t419-alpha-wiring`。
軽量版ではない (正しさ防壁 = attestation gate に触れ、受理集合が変わる)。段 2・3・6 の子を省かない。

## 確定済みユーザー裁定 (前提)

- (208) R-1 = **方式 α 採用** (走行 CPU を移しながら K 回読み、論理 CPU ごとに最小値)。留保 2 件:
  (i) should-reject は未測定のまま採用、(ii) 本番 probe の取得手続きが変わる。R-0 追認済み。
- 較正の再取得・登録・pin closure は**下流** (T-506 chain の後段)。本 wave は取得経路の実装だけ。

## 段 1 前提実測 (実編集・即時復元、DW-O19)

1. `env_attestation.probe()` (`orchestrator/campaign/env_attestation.py:404-455`) は `/proc/cpuinfo`
   を 1 回読み `method="proc-cpuinfo"` を出す。α は未実装。
2. **method 文字列を `proc-cpuinfo-rotating-min/k5` へ 1 行変異しても、clock/freeze 系 6 test file が
   330 passed / 0 failed** (計算ノード request 891526)。既存テストはこの取得方式変更を検出しない。
   → 本 wave の検出力は**純増**であり、既存被覆に依存できない。復元済み (`git checkout --`)。
3. login node で α を実演: 単読みは 4 CPU 帯外 (23/29/83/85)、走行 CPU を 5 点へ移した CPU ごと最小は
   1 CPU 帯外 (29)。機構は効き、かつ恒真にもならない。`sched_setaffinity` は使え、affinity は復元できる。
   1 読み ≈ 20 ms (96 CPU) なので K=5 で ≈ 100 ms。
4. `effective_clock.method` は expected/observed の比較 field に入っている
   (`env_attestation.py:679`)。α 化で live probe は登録済み g1 較正 (`method="proc-cpuinfo"`) と
   **必ず不一致になる**。これは既定の運用宣言 (再較正まで certified campaign を開かない) と整合する。

## scope (実装する)

- `probe()` の**取得手続き**を α にする: 走行 CPU を決定的に K 点へ移しながら K 回読み、
  論理 CPU ごとの最小を `effective_clock.samples_mhz` にする。
- 方式 identity: `method` を新定数にする (K と選択規則を identity に含める)。
- 退化の fail-closed: 巡回不能・pin 不発・K 未達・読み間で CPU 集合/identity 不一致は拒否。
- 純増の検出力 (テスト): α でなければ通らない負例と、過剰拒否を検出する正例。

## scope 外 (実装しない。射程として明記する)

較正の再取得・登録、凍結 bytes と `env_contract.py` pin の更新、帯述語・`tolerance_pct` の変更、
`KNOWN_SELF_INCONSISTENT_CALIBRATIONS` の縮小、[T-529] 活性化権限、[T-443]/[T-444]、
α の should-reject 実測 (裁定で「測らずに採る」と確定済み)。

## 不変条件 (破ったら赤)

- 受理**述語**は不変 = 全位置が帯内 (`canonical_pass`)、`EFFECTIVE_CLOCK_TOLERANCE_PCT=2.0`。
  α は取得だけを変える。判定式に「1 個まで許す」等を混ぜない (それは γ であり不採用)。
- 凍結 bytes 不変: `output/env/pegasus/calibration/registered/calibration-753f535a8d024727.json`、
  同 attempts、`env_contract.py` の `{path, sha256}` pin、g1 の `contract_sha256`。
- **単読み fallback を持たない。** 巡回できない環境で α を名乗って 1 回読みへ退化する経路を作らない
  (規律 2: 正しさゲートを緩める変異を許さない)。
- probe の affinity 変更は `try/finally` で必ず復元し、attestation 以外の process 状態を残さない。
- `KNOWN_SELF_INCONSISTENT_CALIBRATIONS == 1` と既存 schema key 集合の exact 検査を恒真化しない。

## 成果物影響 (DW-G05)

- **実装した場合:** certified 選択・材料レポート・試行台帳の**現在値は変わらない** (campaign は
  再較正まで閉鎖中)。変わるのは拒否の理由で、「常に帯外」から「method 不一致」という明示拒否になる。
  U-2 entry condition (i) が成立し、再取得 chain が開く。
- **実装しない場合:** U-2 は永久に着手不能。再取得しても観測者効果を焼き直した較正しか作れず、
  certified campaign を再開できない。

## 親の provisional 裁定 (攻撃対象)

- **(P1)** K=5 固定 (因果実験の `ALPHA_K` と一致)。可変引数にしない。
- **(P2)** schema key 集合を変えない。K 読みの生ベクトルは保持せず、方式 identity は `method`
  文字列だけに載せる。← 裁定パッケージの α 行は「schema (K 回保持)」と書いており、ここは割れうる。
- **(P3)** 巡回対象 = attested CPU 集合 ∩ `sched_getaffinity`、そこから決定的に等間隔 K 点。
- **(P4)** pin が実際に効いたことを `/proc/self/stat` の走行 CPU で検査し、不一致は fail-closed。
- **(P5)** テスト seam は `os.sched_*` の monkeypatch でなく注入可能な sampler を置く (DW-O14)。

## 成果物の形

`orchestrator/campaign/env_attestation.py` の取得経路 + `orchestrator/tests/test_env_attestation.py`
(必要なら新 test file)。docs は段 7 で spool fragment。実測は `tools/run_tests.py` 経由 (計算ノードへ
自動 dispatch、login では走らせない)。

## 並列分割

段 3 は 2 レンズ (A: 退化・fallback・観測者効果の抜け道 / B: 受理集合と凍結 bytes への波及)。
段 5 は単一実装子 (面が 1 module に閉じるため分割しない)。段 6 は review 2 本。
