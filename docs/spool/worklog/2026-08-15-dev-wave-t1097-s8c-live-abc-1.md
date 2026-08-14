---
schema: izanagi-spool-v1
ledger: worklog
authored: 2026-08-15
wave: dev-wave-t1097-s8c-live-abc
seq: 1
title: 段 8 主経路 (1) の 8c A/B/C live pilot を計算ノードで起動し、受理 gate 2 件で止まった — [T-1094] は当該経路で発火しないことを実測で示した (docs のみ、branch worktree-dev-wave-t1097-s8c-live-abc)
---

## 本文

- **依頼は段 8 主経路 (1) の実走** — A=rr50 / B=rr95 / C=rr100 を 1 generation、live build /
  legacy+S2 verify / bench-first screening で single-tenant 実走し terminal report を出す。
  **実走は成立しなかった。** 止めたのは環境でも [T-1094] でもなく repo 内の受理 gate 2 件である。
  材料の正本 = `output/insights/2026-08-15_t1097-s8c-live-abc/`。
- **経路は 1 本しかないことを実測で確定した。** login node の live build は
  `_assert_build_site_opted_in` が `未受理 site='PEGASUS_LOGIN'` で機械拒否し、
  `dispatch_compute.py --task` は `{tests, provenance}` だけで `campaign` task を持たない
  ([T-236] は凍結のまま)。残るのは supervisor ごと計算ノードで走らせ D122 の
  `--allow-pegasus-compute-transport` を明示する形だけで、これは archive worklog (102) の
  [T-276] 裁定の意図と一致する。live build には `--allow-coder-derived-build` も必須である。
- **[T-1094] は 8c live build 経路では発火しない (新しい実測事実)。** pegasus-runbook は
  「git clone / CMake FetchContent / pip が proxy を honor するかは未確定」と明記していた。
  計算ノード (bnode021) で production の configure argv を実行したところ **rc=0 / 8.357 秒**で、
  `_deps` に masstree / mimalloc / googletest が pin 通り生成された (masstree-src HEAD =
  `b3c5d054b66b08374d7a6ff5a0faeaf28b041a38`、実体 3.3M / 11M / 20M)。反証したのは
  「計算ノードでは FetchContent が原理的に通らない」という一般化の方であり、
  床値経路が [T-1094] で止まっているかは本 wave の scope 外である。
- **preflight の第 1 走は probe 側の不足で無効だった** — `dependency_prefix` を空で
  `_v2_commands` へ渡したため configure は 0.655 秒で `find_package(gflags)` に落ち、
  FetchContent へ到達していなかった。prefix を production seam 経由で渡して再測して初めて
  上の事実が取れた。**「configure が落ちた」を [T-1094] の発火と読み違えなかったのは
  `_deps` が 0 件だったからである。**
- **欠陥 1 (経路を塞ぐ本体、ユーザー裁定へ返す):** D122 決定 (2)(ii) の
  `PBS_JOBID` 受理文法が実機で充足不能である。`claude_transport.PBS_JOBID_PATTERN` は
  `[A-Za-z0-9][A-Za-z0-9._-]*` で colon を含まないが、NQSV が渡す実値は `0:911106.nqsv`
  (job index + request id) である。この pattern は `qsub_binding._JOB_ID_TEXT` と byte 一致で
  pin されているが、そちらは **qsub が印字する request ID** の文法であって環境変数の文法ではない。
  **repo 自身がこの差を知っている** — `test_claude_transport.py` は
  `COLLECTOR._JOB_ID.pattern == rf"(?:0:)?{PBS_JOBID_PATTERN}"` を pin しつつ、同じテストで
  `"job:id"` を invalid と主張している。D122 段 1 の前提実測 (request `877155`) は proxy key と
  `claude -p` の rc を測ったが `is_valid_pbs_jobid` を実機値へ通す end-to-end を測っておらず、
  これが裁定時の未見事実である。**受理集合の変更にあたるため親は緩めない (規律 2、`DW-S04`)。**
- **欠陥 2 (診断を隠す側):** `autonomous_trial_completeness._EVENTS` に producer
  (`p3_autonomous_workload_trial.py:2442`) が書く `transport-admission-error` が無い。
  `_check_closed_events` が `_finish_trial` の中で例外を投げるため **`report.json` が 1 byte も
  書かれない** (実在しないことを確認)。journal は `run-finish status=partial` と report path を
  既に記録済みで、台帳と実 FS が食い違う。全件記録の機構が、それが最も要る失敗経路で自分を止めている。
  型は「説明と実装の食い違い」ではなく **consumer 取り残し**である。
- **role attempt は 0 件**で、planner / coder / auditor / critic は 1 度も呼ばれていない。
  LLM 呼び出しも descriptor 射影も発生しておらず、合成に関する主張は何も生じていない。
  build leg (masstree bootstrap を含む `ycsb_silo.exe` の完成)・legacy+S2 verify・bench も未実証である。
- **計算ノードで確認した運用事実:** `resolved_site = PEGASUS_COMPUTE`、
  `_site_admits_measurement = True`、`numactl = /bin/numactl` 実在、`claude` CLI 実在、
  従量経路 env 5 key はすべて不在、proxy は lowercase 2 key のみ。
  単独性は tanab 7 process + system daemon のみで競合 `ycsb_*.exe` は無し。
  gcc/g++ 11.4.0、cmake 3.25.0、`default_build_jobs = 48`。
- **依存 staging が live 実走の前提である。** `p3_autonomous_workload_trial.py` は
  `dependency_prefix` を 1 度も渡さない (grep 0 件) ため、ambient `CMAKE_PREFIX_PATH` だけが
  依存の seam になる。gflags/glog は install 済み prefix を持たず pinned source から job 内で
  build するのが既存の作法 (`floor_campaign.sh:810-925` を逐語再利用した)。
  本 wave の job script は repo 外の
  `/work/1/SFC/tanab/dev-wave-jobs/2026-08-15_t1097-s8c-live-abc/live/` に保全した。
- **`docs/phase3-s8c-autonomous-trial-runbook.md` §3.3 が stale である。**
  「[T-276] / [T-277] の裁定済み項目待ち」は 2026-08-02 の D122 / D125 で解消済みで、
  pegasus-runbook §8 には 2026-08-11 に訂正が入っているのに 8c runbook 側は未更新である。
  起動例も `--allow-coder-derived-build` と `--allow-pegasus-compute-transport` を欠く。
  本 wave は受理 gate の裁定が出るまで本文を書き換えず、事実だけをここへ残す。

## 次の一手差分

### 新規

- {{T:pbs-jobid-witness-grammar}} **P1・新規・ユーザー裁定待ち**:
  D122 決定 (2)(ii) の `PBS_JOBID` 受理文法が実機で充足不能である。
  択 (a) transport 側を `(?:0:)?<request-id>` へ拡げる (collector と同形。負例集合の更新を伴う)、
  択 (b) job script が request ID を切り出して渡す (**gate が検査する env の書き換えであり親は迂回と判定**)、
  択 (c) witness を `PBS_JOBID` 以外の実在証拠へ替える。
  **親の推奨は択 (a)** — repo 内に既に `(?:0:)?` を許す consumer があり、D122 決定 (7) は
  witness を attestation でないと明言済みなので防護の主張は減らない。受理集合の変更なので D96 手続。
- {{T:autonomous-trial-admission-error-event}} **P1・新規・ユーザー裁定待ち**:
  `autonomous_trial_completeness._EVENTS` に `transport-admission-error` を足すか。
  択 (a) 足す (partial report が失敗経路でも書かれる)、
  択 (b) producer 側を `provider-init-error` へ丸める。
  **親の推奨は択 (a)** — 丸めると規律 3 の還流が狭くなる。受理集合の変更なので D96 手続。
- {{T:s8c-live-abc-rerun}} **P1・新規**: 上 2 件が閉じた後に 8c A/B/C live pilot を再投入する。
  job script と依存 staging は保全済みで、単独性検査と gflags/glog build はそのまま再利用できる。
- {{T:s8c-runbook-stale-33}} **P2・新規**: `docs/phase3-s8c-autonomous-trial-runbook.md` §3.3 の
  stale な前提 ([T-276]/[T-277] 待ち) と起動例の欠落 flag 2 件を訂正する。
  受理 gate の裁定が出てから、確定した起動形と併せて 1 回で直す。
