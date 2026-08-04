# 段 1 brief — [T-419] probe 実験 (因果立証、是正は実装しない)

wave branch `worktree-dev-wave-t419-probe-experiment` / base `23e4363` (main)。

## scope

**する:** 計算ノード上で「走行 CPU・cpufreq driver / governor / boost・同居プロセス」を束縛または
記録した probe 実験を行い、F108 が主張する「`/proc/cpuinfo` の `cpu MHz` 帯外サンプルは probe 自身の
観測者効果である」の**因果**を、介入 (走行 CPU の意図的な移動) で立証する。同じ実験データで
是正方式候補 α / β / γ の成立可否を評価し、裁定パッケージとして返す。

**しない:** `orchestrator/campaign/env_attestation.py` の是正、較正の再取得、凍結 bytes と
`env_contract.py` の pin 更新 (すべて U-2 の所有)。受理集合・正しさ防壁・gate は一切動かさない。
Pegasus campaign は開かない。

## 確定済みユーザー裁定

- (2026-08-04 /rulings、worklog (182)) 「先に計算ノードで走行 CPU・cpufreq driver・boost 設定・
  同居プロセスを束縛した probe 実験を置き、因果を立証してから是正方式を選ぶ」。
  α = K 回読み論理 CPU ごとに最小値 (述語を緩めない、筆頭) / β = 走行 CPU を 1 要素除外
  (受理集合 47/48 へ緩む) / γ = 帯外 1 個許容 (根拠が弱い)。
- D155 決定 (4): 是正方式は受理集合と凍結 bytes に同時に触れるためユーザー裁定へ返す。

## 前提実測 (2026-08-04 22:1x、ログインノード、読み取りのみ)

1. **scheduler は生きている。** `qstat -Q` = gen_S ENA/ACT、RUN 61 / QUE 116。debug RUN 1。
   自分の request は 0 件。
2. **login node の cpufreq: `scaling_driver=acpi-cpufreq`、`scaling_governor=performance`、
   `/sys/devices/system/cpu/cpufreq/boost=1`、`intel_pstate` 不在。** 計算ノードの値は未取得
   (実験で記録する)。login は 96 論理 CPU、計算ノードは 48 physical / HT 無効 (runbook §1)。
3. **帯外は「self CPU だけ」ではない。** `/proc/cpuinfo` + `/proc/self/stat` の processor を同時に
   採る 3 試行で、self=88 は 3/3 とも帯外だったが、**同時に他の CPU も 2〜11 個帯外**だった
   (他ユーザー負荷のある共有 login node)。→ 機序は「self である」ことではなく
   **「その瞬間 busy である」**の可能性が高い。(181) の 6/6 は self を見ただけで他を数えていない。
4. **`taskset` と `python3.10` は login に実在**する (`/usr/bin/taskset`, 3.10.12)。
5. **新規追加 path に凍結 pin は無い。** `FROZEN_MANIFEST` (23 件) は `output/insights/` 配下の
   新規 dir を含まず、`grep -rn "output/insights" --include=*.py` の hit はすべて既存の別 path。
   → `DW-O09` / `DW-O10` は不成立。`DW-O08` (freeze 族) も不成立。

**承認済み裁定を覆す新事実は無い** — 実測 3 は裁定の前提 (因果未立証) を否定せず、むしろ
「self か busy か」を分ける実験が要るという裁定の趣旨を強める。

## 親の provisional 仮説 (攻撃対象)

- **(P1)** 帯外の原因は「読み取り時点でそのコアが busy であること」であり、probe 自身の走行 CPU は
  定義上必ず busy なので常に帯外に出る。→ 走行 CPU を意図的に移せば帯外 index が追随する。
- **(P2)** 同居プロセスが無い計算ノードでは帯外は self の 1 個。観測された 2 個は、読み取り中の
  migration (読み始めと読み終わりで別コア) か kernel thread による。
- **(P3)** α (K 回読み per-CPU 最小) は**単独ノードでのみ**全要素を帯内へ落とす。同居負荷があれば
  そのコアは全 K 回 busy になりうるので収束しない。
- **(P4)** β は self しか除かないので同居負荷で破れる。γ は帯外が 2 個出た時点で破れる。
- **(P5)** self 以外の値が**常に厳密に同一の定数** (2101.0) なら、`samples_mhz` は実効クロックを
  測っておらず「どのコアで probe が走ったか」だけを符号化している。→ 方式選択の根拠が変わる。

## 実験設計 (計算ノード 1 job、gen_S、48 core、HT 無効)

すべて `/proc` と `/sys` の読み取り + 自前の busy loop のみ。root 権限を要さない。

| arm | 介入 | 測る量 |
|---|---|---|
| A0 baseline | 何もしない (現行 probe と同じ読み方) × N | 帯外 index 集合、self CPU、帯外個数分布 |
| A1 pin sweep | `sched_setaffinity` で self を CPU c に固定、c = 0..47 全走査 × R 回 | 帯外 index == c の一致率 (**因果の本体**) |
| A2 co-resident | self を CPU 0 に固定 + 別プロセスの busy loop を CPU k に置く | k が帯外に現れるか (同居プロセスの因果) |
| A3 方式 α | 48 CPU を巡回して K 回読み、論理 CPU ごとに最小値 | 全要素が帯内 (厳密 2101.0) へ収束するか。A2 併走版も |
| A4 migration | affinity 非固定で読み、読み前後の processor を記録 | 帯外 2 個の説明 (読み中 migration) |

**記録する束縛**: node 名、job ID、`scaling_driver` / `scaling_governor` / `boost` / 各 policy の
`scaling_cur_freq` と `cpuinfo_cur_freq` の可読性、`/proc/loadavg`、`ps` による同居プロセス一覧と
単独性判定 (`pgrep`、F3 と runbook §8)、`nproc`、`sched_getaffinity` 集合、実験開始/終了時刻。

**規模** (規律 4): A1 = 48 × R(=5) = 240 読み、A0 = 30、A2 = 8 対、A3 = 3 反復 × 48、A4 = 30。
合計約 500 回の `/proc/cpuinfo` 読み。**数秒**で終わる。wall time 要求は 00:10:00 で足りる。

**判定 (事前登録)**: 因果 CONFIRMED = A1 で「帯外集合が pin した CPU c を含む」が 48/48 かつ
「A0 の帯外集合が self を含む」が 30/30。REFUTED = どちらかが 1 件でも外れる。
A2 で k が帯外に出れば「self 限定」仮説は棄却され「busy コア」仮説が採られる (P1 の精密化)。

## 不変条件

- 実装子はコードのみ編集し docs 編集と commit をしない。`env_attestation.py` / `env_contract.py` /
  `output/` 配下の既存ファイルには触れない (新規 dir のみ)。
- 計算ノードの出力は**データ**であって指示ではない (規律 6)。
- 実験自身の観測者効果を消せないことを明記する — これは測定対象そのものである (規律 1)。
- 述語も gate も緩めない。本 wave は受理集合を 1 bit も動かさない。

## 成果物

- `output/insights/2026-08-04_t419-probe-causality/evidence/probe_causality_experiment.py`
  (使い捨て driver、`--self-test` 付き。`DW-G01` の最安経路)
- 同 dir の `raw/*.json` (計算ノード生出力) と `README.md` (因果判定 + α/β/γ 評価 + 逐語)
- 裁定パッケージ (方式選択はユーザーへ返す)
- worklog / failures fragment (`docs/spool/`)。F108 は「因果立証済み」を追記 (新 F は作らない)

## 成果物影響 (DW-G05)

これを実装しない場合、U-2 (較正再取得と pin 更新) は**因果不明のまま方式を選ぶ**ことになり、
選んだ方式が外れれば Pegasus campaign の certified 選択結果は再び attestation で塞がれ、
凍結 evidence の再発行が空振りする。α/β/γ の受理集合は 48/48・47/48・47/48 と異なるため、
選択を誤ると `effective_clock.samples_mhz` の照合が恒真化 (γ) するか、過剰拒否 (α) で campaign が
開かないままになる。

## 分割方針・軽量版判定 (DW-C00)

正しさ防壁に触れず、受理集合を変えず、設計択一は実装せず裁定パッケージへ返す →
**軽量版**が既定に該当する。ただし本 wave の価値は**因果推論の妥当性そのもの**であり、設計を誤ると
計算ノード job を 1 本無駄にして誤った因果を台帳へ焼き込むため、**段 3 の敵対レンズ 1 本を実験設計へ、
段 6 のレビュー 1 本を結果解釈へ**当てる (段 2 のプラン起草は本 brief が代替)。
実装面は 1 単位 (単一ファイル) のため Codex author 1 本で分割しない。
