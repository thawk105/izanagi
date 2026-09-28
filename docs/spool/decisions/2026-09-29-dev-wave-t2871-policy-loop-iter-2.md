---
schema: izanagi-spool-v1
ledger: decisions
authored: 2026-09-29
wave: dev-wave-t2871-policy-loop-iter
seq: 2
---

## {{D:policy-loop-per-iteration-measurement}}. 方策 loop の pair は系列の iteration ごとの計測 campaign で測り、Pegasus の one-shot claim を iteration ごとに 1 本にする

**決定:** D2274 項 4 が別 task に送った「job をまたぐ同じ loop campaign の claim」を、claim leaf と one-shot 性を変えずに driver (`orchestrator/campaign/p3_s4_loop_policy.py`) 側で次のように解いた。記録は `output/insights/2026-09-29/t2871-policy-loop-iter/README.md`。

1. **系列 dir と計測 campaign を分ける。** 系列 (loop) の campaign dir (既存の identity のまま) には `loop_state.json`・`policy_history.jsonl`・`silo_policy_loop_digest.txt` と login の record-reject の WAL だけを置く。pair 経路 (`--run-iteration --stock-control`) の候補と stock は、系列 cfg の `search_config` に `policy_iteration` (正整数) を足した計測 cfg の campaign で、同じ authorization session を使って測る。bootstrap・r2・record-reject・preview・emit-coder-input・非 pair の `--run-iteration` の identity は不変。
2. **受理単位の変更:** Pegasus の one-shot claim の単位は「loop 系列に 1 本」から「系列の iteration に 1 本」になる。claim leaf (`campaign_claim.py`) の bytes と、同じ path の既存 file を `O_EXCL` で拒否する挙動は不変で、同じ計測 identity (同じ番号・同じ cfg・同じ out_root) の再使用は従来どおり `ClaimError`。
3. **番号の出所は系列の `loop_state.json` だけ**とし、argv では受けない。`drive_iteration` は counter を進めた直後、計測より前に系列 state を保存する。claim 取得後に強制終了した番号は欠番になり (履歴行なし、計測 dir と claim は証跡として残る)、次の job は次の番号で進む。
4. 系列の履歴行と pair の stdout JSON に `measurement_campaign_id` を載せる (coder 入力の射影には入れない)。critic digest の材料は当該 iteration の計測 campaign の admitted WAL (候補の評価後・stock の前) とし、過去の iteration と record-reject は digest に入らない (系列全体は coder が `self_history` で見る)。
5. 同じ系列の pair job は直列に投入する (番号を予約しない)。2 本目以降は `qsub --after <前の request>` で先に待ち行列へ入れてよい。

**理由:**
- claim を解くだけでは足りない。同じ campaign の WAL で終端済みの variant は次の run で skip される (retryable abort を除く) ので、stock (毎回同じ variant) を同じ loop campaign で 2 度測れない。iteration ごとの計測 campaign は claim と stock skip を同時に解く。
- 段 2 の plan 2 本が独立にこの案へ収束した。系列状態の出所が 1 つの dir に定まり、同じ submit checkout・同じ out_root のまま login 側操作と整合する。
- counter の保存を `finally` だけにすると、claim 取得後の強制終了 (PBS の walltime 超過など) で系列 state が旧番号のまま残り、次の job が同じ計測 identity を選んで `ClaimError` で止まり続ける。復旧が claim の手動退避か state の手編集しかなくなるので、依頼の目的そのものを壊す (段 3 相談 A の must-fix)。
- 結合検査 (別 process で直列に 2 回、実 `_authorize_measurement`・実 `acquire_claim`・実 `check_reservation`)、変異 5 / 5 KILLED、本番入口の pair job 2 本の連続実走で確かめた。

**却下した選択肢:**
- K2 型 (job ごとに新しい out_root・submit checkout を使い、系列状態を前の tree から持ち込む) — 系列状態の出所が tree をまたぎ、login 操作のたびに転送元を選ぶ必要がある。
- B-5 型 (「1 identity = 1 測定点」を系列全体に適用し履歴だけ連結する) — pair を 1 測定点と定義すれば本案と同型で、候補と stock を別 identity にすると同じ authorization session を共有できない。
- 系列 WAL へ計測 WAL を複写して系列全体の critic digest を保つ — lock と admission の整合を新しく扱うことになり、最小変更に収まらない。
- counter の保存を `finally` のまま、強制終了した番号の再測定を許す回復契約を足す — one-shot 性と手動退避の禁止に触れる。
- 生死確認を 1 本の計算ノード job の中で driver を 2 回起動する形に変える — job をまたぐ確認にならず、2 process の claim は結合検査が計算ノードで既に通している (codex の 2 立場で相談、A 側を採用)。
