---
schema: izanagi-spool-v1
ledger: decisions
authored: 2026-09-18
wave: dev-wave-t2288-floor-pair-job-body
seq: 1
---

## {{D:floor-pair-job-body-contract}}. B-4 床値 (floor-pair) の窓 job と finalize job は 1 job = 1 spec × (1 窓 | finalize) とし、submitter が窓の時刻・create-only・同一 HEAD を qsub 前に早期拒否し、walltime は window 24 h / finalize 30 分、証拠は repo 外に置く

**決定 (D1641 決定 4 の実行機構、D2138 の凍結 spec 3 本を走らせる資材の運用契約):**

1. **分割:** 1 job = 1 spec × (1 窓 | finalize)。3 spec × 2 窓 = 6 window job + 3 finalize job。並走の可否は admission に依存し、資材は保証しない。
2. **資材:** login 側 `tools/pegasus/submit_floor_pair.sh` (登録簿 `local-ok`、`static login-side submitter classification`) と計算ノードの
   `tools/pegasus/floor_pair_campaign.sh` (登録簿 `dispatch-required`、`static job-body classification`)。job body は driver
   (`orchestrator/campaign/floor_pair_driver.py`) を `-I -B -c` で sys.path を挿入して `main()` から `--execute-window <id>` / `--finalize` で
   1 回だけ起動し、driver の gate (spec sha・HEAD blob・live site・runtime HEAD・create-only) を複製も代替も緩和もしない。
3. **submitter の早期拒否 (qsub 前、driver の検査の代替ではない):** detached checkout・tracked clean・D2138 項 7 の 3 組 (relpath, sha256) の
   pin と実 file sha・HEAD blob sha の一致・binary の実在と sha・窓 job は `now >= not_before && now + elapstim_req <= not_after` (UTC 半開)
   と対象窓 JSONL の不在と同 spec の他窓 JSONL header の `loaded_head` == 現 HEAD・finalize は summary 不在と両窓 JSONL の存在・header 一致・
   末尾 record が terminal。job body は起動時に HEAD == 投入時 HEAD・spec sha・binary・hostname (第一 label を lowercase 化して `^bnode[0-9]+$` に
   完全一致)・窓の時刻を再検査し (scratch 作成後にもう 1 度)、外れれば driver を起動せず rc=4 で止める (create-only の path を残す)。
4. **walltime:** window `24:00:00` (gen_S の上限)、finalize `00:30:00`。submitter の 1 箇所で決め、`qsub -l` と env `FP_ELAPSTIM_REQ` へ同じ値を渡す。
   24 h は成功保証ではない。
5. **証拠:** `/work/1/SFC/tanab/izanagi-job-evidence/floor-pair/<nonce>/` (repo 外)。submitter が `pre-submit.json` / `qsub.*` /
   `submit-receipt.json`、scheduler が `scheduler.std{out,err}`、job body が `driver.std{out,err}` / `job-result.json` (`open(...,"x")`) を書く。
   測定 JSONL と summary は凍結 spec が指す repo 内 path (投入元 checkout) に driver が create-only で書く。
6. **signal:** job body は driver を background child で起動して `wait` で rc を回収し、TERM/HUP/INT は記録して再 `wait` する。driver rc=0 なら job rc も 0
   (signal は `reason=signal_observed` に残す)。計算ノードの job が SIGTERM を SIG_IGN で継承する場合 (F1012) この trap は発火せず、walltime 到達時は
   KILL で driver が止まる — これは保証しない挙動として runbook §7.8 に書く。

**理由:**
- driver の CLI が 1 窓 / 1 finalize 単位で、窓ごとに別 job にすれば walltime の要求が小さく queue に乗りやすい。
- 窓の JSONL と summary は create-only で 1 度しか作れない。窓外開始・二重投入・別 HEAD の窓は path を消費して回復不能になるので、
  qsub 前と driver 起動前に「無駄な割当て」と「path の消費」を止める前段を置く。前段は driver の検査を複製せず、header 1 行と末尾 1 行だけ読む。
- 3 段同一 HEAD (D2138、申し送り 2) は driver の finalize でしか機械検査されないため、w1=H1・w2=H2 の投入を finalize まで通してしまう。
  submitter の他窓 header 照合はこの欠落を投入時に塞ぐ。
- walltime 10 h の根拠 (全 rep timeout の 44.4 h は 5% 判定で不採用になる) は不成立で、欠測率は経過時間の上限ではない (段 3 レンズ A)。
  窓の喪失は回復不能で、要求超過の費用は queue 待ちだけなので上限側へ倒す (`b10_backoff_shape_campaign.sh` の 24 h の先例)。
- 証拠を repo 外に置くのは、投入元 checkout を 3 段の間 detached・tracked clean に保つため (`submit_t2417_backoff_policy_performance.sh` の型)。

**却下した選択肢:**
- 1 job で 3 spec を直列に走らせる — walltime が 3 倍になり queue に不利。
- job body を `dispatch_compute.py --task generic` で代替する — clean env に `PBS_JOBID` が無く、job の帰属と受領証が job body の型と合わない。
- `--assume-now` (dry-run 専用の時刻注入) — 実投入の gate を騙す seam になりうる。正例は契約 test の now 注入で確認する。
- 前段を一律に外す — D2069 の複製禁止は `place → store_binaries` の経路を指し、早期拒否は規律 2 の緩和ではない。ただし前段の kill を driver の
  検査強度の証明に数えない。
- `nm` / `pgrep` を finalize の必須 command から外す — loader は sha だけを見るので finalize には不要だが、mode で集合を分ける価値が小さい。

**本決定が主張しないこと:** 実 qsub の受理、8 変数の伝播、実効 walltime、signal 配送、計算ノードでの import と依存解決、床値の生成・採用。
これらは次の測定 wave の初回実行で確認する (F660)。
