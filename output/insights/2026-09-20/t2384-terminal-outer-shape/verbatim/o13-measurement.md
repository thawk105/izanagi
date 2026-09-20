# DW-O13 実測 — terminal record の外枠が実環境で取りうる値 (2026-09-20 07:52 JST、親の実測)

script: `/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2384-terminal-outer-shape/o13_scan_real_terminals.py` (読み取り専用)。
出力原本: 同 dir の `o13-scan-output-campaigns.txt` (repo 内 `output/campaigns/*/runs/wal.jsonl`)、`o13-scan-a5-second-boot.txt` (repo 外 `/work/1/SFC/tanab/a5-second-boot-runs/*/campaigns/*/runs/wal.jsonl`、2026-09-06 実走)。

## 母集合 1: repo 内 output/campaigns (30 file、attempt 世代より前)

- terminal record (stage ∈ {commit, abort}) = 474 件、不正行 0。
- outer key 集合: `['env_tag', 'payload', 'stage', 'ts', 'variant']` が 474/474 (EXACT)。
- 型: ts = float 474/474 (非有限 0)、variant = str 474/474、env_tag = str 474/474、payload = dict 474/474。
- payload に `build_attempt_id` を持つ record は 0 件 (attempt 世代前の campaign) → attempt ごとの件数は測れない。

## 母集合 2: a5 second boot 実走 (2 file、2026-09-06、attempt 世代)

- terminal record = 16 件 (commit 16、abort 0)、不正行 0。
- outer key 集合: EXACT 16/16。型: ts = float 16/16、variant = str、env_tag = str、payload = dict。
- `build_attempt_id` を持つ attempt = 16、**attempt ごとの terminal 件数 = 1 が 16/16** (2 件以上は 0)。

## 判定

- gate が要求する値 (exact key 集合、str / str / 有限数 / dict) は実環境の全 490 件で到達している。過剰拒否の実例は 0。
- 「terminal はちょうど 1 件」は attempt 世代の実走 16/16 で成立。abort の実例は attempt 世代の母集合に無い (abort 側は producer の code 経路と fixture で確認、consult A §1 の表)。
- 観測 regime: campaign 実走 (backoff sweep / repro / s1 direct / p2 / p3 sort / a5 second boot)。8c formal consumer が読む ordered WAL projection の実成果物は 8c 正式系列が未開通 (D1829) のため存在しない — projection は同じ WAL record を射影するので、外枠は同一である (`reflux_result_evidence.py` `_canonical_wal_interval` の射影 5 key)。
- 時間予算は本 gate に関係しない (純関数の形状検査)。
