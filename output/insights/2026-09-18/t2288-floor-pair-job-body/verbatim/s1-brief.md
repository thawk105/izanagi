# 段 1 brief — [T-2288] (a) B-4 床値 (floor-pair) の Pegasus job body 着地 wave

wave `dev-wave-t2288-floor-pair-job-body`、branch `worktree-dev-wave-t2288-floor-pair-job-body`、起点 local main
`24ede1d11cb33af8d2278cd6d48d29863225465b` (2026-09-18 10:43 JST)。worktree
`/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2288-floor-pair-job-body`。

## 研究前進 (1 行)
論文の B-4 床値 (silo・t48・3 workload の測定床値、事前登録 §11) は凍結済み 3 spec (D2138、commit 0b4fbd7a6) の実測待ちで止まっている。
止めているのは「計算ノードで `floor_pair_driver --execute-window` / `--finalize` を起動する登録済み job body が無い」ことだけ
(申し送り 1)。本 wave の最小差分 = job body + submitter + 登録簿 + 契約 test。完了判定 = 登録簿の閉包 (check_docs / 契約 test) 緑 +
login 側の起動確認 (下記)。実測は F660 により含めない (w1 は 2026-09-19T00:00Z 以降)。

## scope (純増)
- 新規 `tools/pegasus/floor_pair_window.sh` (job body、`#PBS -q gen_S`) — 1 job = 1 spec × {1 窓 | finalize}。
- 新規 `tools/pegasus/submit_floor_pair.sh` (login 側 submitter、`--dry-run` あり)。
- `tools/pegasus/admission_registry.json` に 2 entry (job body = `dispatch-required` / `static job-body classification`、submitter =
  `local-ok` / `static login-side submitter classification`)、`docs/pegasus-runbook.md` §7.0 投影表に同 2 行 (親)。
- 新規 `orchestrator/tests/test_floor_pair_job_contract.py` (静的契約 + bash snippet 実行; `orchestrator/tests/README.md` allowlist または
  `__main__` 自走 harness)。
- `docs/pegasus-runbook.md` に投入手順の節 (§7.8、親、docs のみ)。
- scope 外: driver / issuer / verifier / spec の変更 (0 byte)、実測、仮想リスク向け gate・台帳・一般化、`tools/pegasus/README.md` の改変
  (宣言表・site tag の要件に触れるため、本文で新 path に言及しない)。

## 確定済みユーザー裁定・既裁定
D1641 (3 者 = thawk105 名義で AI 操作、測定認可済、実行機構は別 wave の Codex author)、D2120 項 4 (A-5 の AI 確定)、D2138 (A-5 の値:
3 spec の relpath・sha256・窓 w1/w2・campaign_id・summary path)、D2069 (binary は `output/env/pegasus/binaries/<sha>` へ ignored 複写、
place は checkout ごと)、D1974 (集約は期待 spec 列を呼び手から)、D95 (実装面は Codex author)、F660 (新規 Pegasus 実行体はこの wave から
起動できない)。申し送り 1〜7 (t2288-a5-freeze insight)。

## 実測した前提 (brief 前、login pegasus02)
- 3 spec の `sha256sum` = D2138 項 7 と全桁一致。本 worktree (HEAD 24ede1d11) で `--validate-only --expected-sha256` 3 本 rc=0・stderr 0 byte
  (stdout 126,415 / 126,415 / 123,935 bytes、`validate-<wl>.json` を job dir に保存)。
- `b4_binary_record place` (record `rr20--stock_common.json`、source-root `/work/1/SFC/tanab/izanagi-b4-floor-binaries`) rc=0、
  701,760 bytes、tree clean。binary の NEEDED は libstdc++/libm/libgcc_s/libc のみ (gflags/glog build は不要 — floor_campaign.sh の
  gflags/glog 段は継承しない)。
- driver 現物: `main()` は `--repo-root --spec --expected-sha256` + `{--validate-only|--execute-window <id>|--finalize}`。`run_window` は
  `_assert_live_environment` (site_policy.current_site(require_evidence=True) が `PEGASUS_COMPUTE`、env_tag `pegasus`) → runtime HEAD ==
  loaded HEAD → `_validate_output_path` → create-only (`O_EXCL`) の順で、live env 不一致は出力確保の前に落ちる。`finalize_floor` は live env を
  検査しない (login でも走る)。probe は `pgrep -af ycsb_.*\.exe`。driver は bench lock を取らない (runner.measure_point 直呼び)。
  clean tree は要求しない (tracked 入力は HEAD blob から `git show`)。
- login の site 判定 = `PEGASUS_LOGIN`、`python3` = 3.10.12、`python3.10` = /usr/bin/python3.10、qsub = /system/tool/bin/qsub。
- 現在 2026-09-18T01:47Z < w1 not_before 2026-09-19T00:00Z → 本 wave 中は窓の時刻 gate が「窓前」で拒否する (正例の dry-run は不可)。
- 所要の実測分布 (a5-freeze insight): bench 部分 1 窓 1.21〜1.55 h、probe timeout 全件計上 4.3〜4.65 h、全 rep timeout 44.4 h (母集合 = 較正時の
  rep wall 3.5〜4.5 秒 × 124 session × 10 rep、regime = 同 cell・同 binary の較正走。本走と同一 regime とは主張しない)。
- t2772 編集面 (orchestrator/campaign 4 本 + tests 5 本) と重ならない。spawn sites の `.sh` 走査は `cmake --build --target ycsb_*` sink だけで、
  本 job body は build しない。`test_codex_worker_launch` は登録簿を HEAD blob 束縛する → 段 6 の子起動前に登録簿を commit。

## 不変条件
規律 2 (driver の gate を 1 つも緩めない・job body / submitter は driver の検査を代替せず前段で fail-closed するだけ)、create-only (既存出力を
置き換えない、申し送り 5)、窓の末端・手前に投入しない (申し送り 4)、3 段同一 HEAD (申し送り 2、driver の loaded_head 検査が権威)、place は
checkout ごと (申し送り 3)、F660 (本 wave から qsub しない)、実行対象 path は `tools/pegasus/...` literal (README §0)。

## 成果物の形と (P) — 親の provisional 裁定・攻撃対象
- (P1) 分割: 1 job = 1 spec × (1 窓 | finalize)。3 spec × 2 窓 = 6 window job + 3 finalize job。並走は admission 依存。
  代案 = 1 job で 3 spec 直列 (walltime 3 倍、queue に不利)。
- (P2) walltime: window job `elapstim_req=10:00:00` (floor_campaign.sh と同値、probe 全 timeout 込み 4.65 h の ×2.15)。finalize job `00:30:00`。
  全 rep timeout の 44.4 h は覆わない (その regime は 5% 判定で不採用になるので窓を守る価値が無い)。walltime 切れは terminal 無しの
  create-only 成果物 = 窓の喪失。
- (P3) finalize も job body の mode として持つ (依頼どおり)。live env 検査が無いので login でも走るが、submitter の経路は job に統一する。
- (P4) submitter の前段 (fail-closed、qsub 前): 引数 `--workload {rr95,rr50,rr5}` + `{--window {w1,w2} | --finalize}` + `--dry-run`;
  repo root = 実行 checkout (canonical、`git rev-parse --show-toplevel` 一致); HEAD detached・40 hex; tracked clean
  (`--untracked-files=no`; 窓 1 の JSONL は untracked で残るため untracked は許す); spec relpath・sha256 は D2138 項 7 の 3 組を script 内に
  pin し、実 file の sha256 と HEAD blob の sha256 の両方が pin と一致; binary が spec の `binary_relpath` に実在し sha 一致 (place 済の確認);
  窓 job は `now_utc >= not_before` かつ `now_utc + elapstim_req <= not_after`、finalize job は summary_relpath 不在;
  同名 nonce の evidence dir 不在 (create-only)。
- (P5) job body の前段 (driver 起動前、順序固定): PBS_JOBID / PBS_O_WORKDIR / 束縛 env (nonce 32 hex・expected HEAD 40 hex・spec relpath・
  sha256・mode・window_id・evidence dir) → PATH 固定 + 汚染 env unset → python ≥ 3.10 解決 (floor_campaign.sh の型) → 必須 command
  (git pgrep sha256sum hostname date realpath mkdir) → REPO_ROOT = PBS_O_WORKDIR (realpath、canonical) → HEAD == expected → spec file sha ==
  pin → binary 実在 + sha → hostname `^bnode[0-9]+` (site gate; login の負対照はここで止まる) → 窓 job は `now_utc + elapstim_req <= not_after`
  と `now_utc >= not_before` を再検査 (queue 待ちで窓外へ出た job を driver 起動前に止め、path を残す) → TMPDIR `/scr/<jobid>` create-only →
  driver 起動 (`"$PY" -I -B -m orchestrator.campaign.floor_pair_driver --repo-root "$REPO_ROOT" --spec ... --expected-sha256 ...
  --execute-window <id> | --finalize`、stdout を evidence dir へ) → job result receipt。SIGTERM は `--accept-sigterm=yes` で受け、
  driver は殺さない (create-only の途中死は窓の喪失; 救出経路は scope 外)。
- (P6) evidence root は repo 外 `/work/1/SFC/tanab/izanagi-job-evidence/floor-pair/<nonce>/` (submit receipt・qsub stdout/stderr・
  scheduler `-o/-e`・driver stdout・job result)。attempt dir は job body が所有 (投入側は mkdir 以外置かない)。
  代案 = `output/env/pegasus/floor-pair/attempts/` (repo 内、floor の型) — 測定 checkout を untracked で汚す。
- (P7) 登録簿の evidence 文字列は既存 2 種の逐語 (`static job-body classification` / `static login-side submitter classification`)。
- (P8) `--dry-run` は qsub だけを省き gate は同一。窓前の今日は dry-run が窓 gate で拒否される。正例の dry-run は `--dry-run` 専用の
  `--assume-now <UTC>` (dry-run 以外では rc=2) で通す案 vs 契約 test の snippet 注入だけで済ます案 — 後者を既定、前者は攻撃対象。
- (P9) 契約 test: 登録簿 class、PBS header (`-q gen_S`、elapstim)、pin 表 == D2138 == 実 file sha、driver argv literal
  (`--execute-window` / `--finalize`、`--validate-only` 不在)、hostname regex、窓 gate 関数の snippet 実行 (now 注入で正例 2・負例 2:
  窓前・末端)、mode の閉集合、submitter の引数閉集合、evidence root が repo 外。実 qsub・実 driver は呼ばない。
- (P10) 変異事前登録 (段 4 で確定): M0 等価 (SURVIVED)、M1 登録簿 class 反転、M2 pin sha 1 桁、M3 窓 gate の不等号、M4 hostname regex 除去、
  M5 `--execute-window` → `--validate-only`、M6 runbook 投影行削除 (check_docs、DW-O19 直接測定)。
- 起動確認 (login、模擬/実の差): `bash -n` 2 本 (実); submitter `--dry-run` を detached clean checkout から実走 → 今日は窓 gate で拒否
  (負対照、実); job body を PBS env 模擬 (PBS_JOBID/PBS_O_WORKDIR/束縛 env) で実走 → identity 段まで実で通り hostname gate で拒否
  (負対照、実; driver は起動しない); 窓 gate の正例は契約 test の now 注入 (模擬)。計算ノードでの正例は次 wave (F660)。

## 並列分割
段 2 plan 1 本 (read-only)、段 3 consult 2 本 (レンズ A = 凍結成果物の保護・create-only・窓・同一 HEAD の正しさ境界; レンズ B = PBS/NQSV
実行面・env 伝播・interpreter・登録簿閉包・test の殺傷力)、段 5 author 1 本 (job body + submitter + registry + test)、段 6 review 2 本 +
fix。docs (runbook §7.0 投影表・§7.8) は親。
