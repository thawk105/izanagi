# [T-1431] 床値 (floor value) pilot 再投入 — T-1437 解消後も新 blocker で実測未達

## 要約

D581 (decisions.md:23453) に従い、`output/insights/2026-08-20_t1431-floor-pilot-measurement/README.md`
の投入パラメータをそのまま再利用して床値 pilot を再投入した。[T-1437] (D615、entry 775) が
mocc/silo 両方の `source_digest.resolve()` fails-closed 停止を解消しており、**前回 blocker には
再遭遇せず driver がより先へ進んだことを確認した。** しかし今回は `rr20::sort_best` セルの
SWO oracle 依存 (masstree) の取得が計算ノードで失敗し、driver 全体が再び rc=1 で fail-closed 停止
した。**この新 blocker は本 wave が発見した新規欠陥ではなく、2026-08-14 の [T-971]
(worklog archive entry 549、D399) が実測・文書化した上で明示的に「scope 外」と裁定した既知
gap の再現である。** 12 セルとも実測値 (throughput 等) は 0 件のまま。admission チケットは
1 枚も消費していない。コード変更は行っていない。

## 環境・実行パラメータ (D581 が求める記録、前回 insight と同一)

- **実行環境**: Pegasus, queue=gen_S, nodes=1, elapstim_req_s=36000 (10h 割当)
- **投入元 commit**: `f72e8da8120bbfc071c68bf602c63dd7f50130ae` (main HEAD 相当、worktree
  `dev-wave-t1431-floor-resubmit` 経由)
- **submission nonce**: `fe5670379a689c3fc94d694241377830`、request ID = `928510.nqsv`
  (dry-run 先行: `dry-run-dd800f03ca7f32793caa8b12dc426fa2`)
- **投入コマンド**: `tools/pegasus/submit_floor.sh --confirm-irreversible-pilot-holdout`
  (標準投入経路、`--dry-run` で先に qsub argv を確認してから実投入。前回 insight・entry 743 と
  同一手順)
- **ccbench pin**: `511c9538e4e8efa54b45cda62e72389ed3b706ec` (`external/ccbench` gitlink、
  前回と同一)
- **floor protocol**: `output/s8b-freeze/floor-protocols/e576e9cd1369bba3ae8faca084d1b7256bf919a7dd2e5d6facb093cd9e242c01--511c9538e4e8efa54b45cda62e72389ed3b706ec.json`
  (job-result.json の `protocol_path` で確認、前回と同一世代)
- **重複稼働チェック (投入前実施)**: git worktree 一覧・ListAgents (11 peer sessions)・
  admission claims/consumed (直近ファイルは 8/16)・floor submissions dir (直近投入なし)・
  qstat (floor 関連 job 不在、`izdw-*` 系ジョブは別 wave `T-1428-worktree-submodule-tool` の
  汎用計算 dispatch と確認) のいずれにも同一 T-1431・floor pilot・admission key を扱う
  live owner を確認できなかった。受入 lease (`land-lease`) は別 wave の受入待ち行列で混雑して
  いたが、これは floor pilot の admission ticket system と別系統であり投入をブロックしない。
- **queue 状態**: `qstat -Qf gen_S` で Run State=Active, Submit State=Enable を確認 (停止していない)。

## 投入結果

- job elapsed: 142 秒 (08:44:36 実行開始 → 08:46:54 終了、JST)。前回 (45 秒) より長く走った。
- `job-result.json`: `driver_rc=1`, `mode=pilot`。
- **12 セル中**:
  - preflight 通過: 12/12 (`rr20`/`rr80` × `ident_all`/`backoff_fixed_best`/`p2_2_flag_opt`/
    `sort_best`/`system_gate`/`stock_common`)
  - build 開始: 4/12 (`rr20::ident_all`, `rr20::backoff_fixed_best`, `rr20::p2_2_flag_opt`,
    `rr20::sort_best`)
  - oracle 段階到達: 1/12 (`rr20::sort_best`) — ここで fail
  - `rr20::system_gate`, `rr20::stock_common`, `rr80` 系 6 セルは driver 全体 abort のため未到達
  - **実測値 (throughput 等) を得たセルは 0/12。**
- checkpoint.jsonl (`/work/1/SFC/tanab/izanagi-job-evidence/pegasus/928510.nqsv/fe5670379a689c3fc94d694241377830/checkpoint.jsonl`)
  の通過段: bootstrap → static-admission → attempt-setup → policy → submit-binding →
  source-identity → allocation-reservation → gflags-build → glog-build → protocol-resolution →
  floor-driver (起動、run_dir 発行) → job-result (rc=1、`pilot floor driver returned nonzero`)。
  **前回 (T-1431 entry 743) は protocol-resolution 直後の source_digest 段階で停止していたが、
  今回は floor-driver が実際に起動し複数セルの build まで進んだ。**

## [T-1256]・[T-1437] の再確認

- [T-1256] (pilot 承認フラグが標準投入経路から渡らない問題) は前回に続き問題なし。
  `--confirm-irreversible-pilot-holdout` が正しく `qsub -v` へ伝播した (dry-run receipt で確認)。
- [T-1437] の修正 (`source_digest.py` の mocc/silo protocol 分離、D615) は現 HEAD に含まれており
  (`git merge-base --is-ancestor 2a34b7b0 HEAD` = YES、実際に `PROVEN_REPO_ABSENT_MACROS` /
  `EVOLVE_BLOCK_SOURCE_PROTOCOLS` が `source_digest.py` に実在することを確認済み)、**今回の
  投入では mocc source_digest 由来の停止は一切発生しなかった。** T-1437 は意図通り機能している。

## 新 blocker: masstree FetchContent staging が floor_campaign.sh に未配線 (既知 gap の再現)

### 事象

`rr20::sort_best` セルの oracle 依存取得が失敗した
(`sort-swo-oracle-postflight-failure.json`):

```
classification: attempt-infra
reason_code: sort-swo-oracle-infrastructure-unavailable
detail_code: floor-dependency-postflight-build-failed
origin: floor-dependency-postflight:masstree
path: /scr/0_928510.nqsv/izanagi-floor-fetchcontent-i7gk7bz6/masstree-src
```

`floor-driver.stdout`: `SortSwoOracleUnavailable: sort-swo-oracle-infrastructure-unavailable`。

### 根本原因 (file:line 裏取り済み)

- 計算ノードは直結の外部 network が使えない (`docs/pegasus-runbook.md:749-762`、2026-08-01 実測)。
  CMake FetchContent で masstree を直接取得する経路は構造的に通らない。
- `orchestrator/campaign/sort_swo_oracle.py:1130-1131` に
  `IZANAGI_SORT_SWO_MASSTREE_ROOT` という代替解決経路 (env var transport、D399 が定めた設計) が
  ある。D399 (decisions.md:16805) は「masstree source root は明示引数または専用環境変数だけで
  受け取り、floor policy へ複写しない」と定めている。
- しかし `tools/pegasus/floor_campaign.sh` にはこの環境変数を設定する配線が無い
  (`grep -n "masstree\|MASSTREE\|FETCHCONTENT" tools/pegasus/floor_campaign.sh` = 0 件、実測)。
- **これは新規欠陥ではない。** 2026-08-14 の [T-971] (`docs/archive/worklog-phase3-0814-549.md`、
  D399、branch `worktree-dev-wave-t971-swo-oracle-floor`) が同じ構造を実測・特定し、
  「床値 build の FetchContent staging」を **scope 外の real 所見** として裁定パッケージへ送った
  記録が残っている: 「`docs/pegasus-runbook.md:744-756` は計算ノードの直結 network 不可と
  『proxy で FetchContent が通ると一般化するな』を明記する。→ 本 wave は『床値が取れるように
  なった』と主張しない。」T-971 は「診断が消える場所」(理由コードが記録されず fail-closed の
  原因が追えない問題) を修正したが、masstree 取得経路自体の配線は意図的に scope 外のまま
  残していた。今日までこの配線は追加されていない。

### なぜ今回初めて表面化したか

前回 [T-1431] entry 743 (2026-08-20) は mocc protocol の `source_digest.resolve()` blocker
(T-1437 で解消済み) により、floor-driver 起動より前の protocol 解決段階で停止していた。
そのため `rr20::sort_best` セルの build/oracle 段階まで到達していなかった。今回 T-1437 の
修正で driver が初めて sort_best セルの oracle 依存段階まで進み、2026-08-14 から存在する
未配線の gap に到達した。**mocc blocker と masstree gap は独立した別々の問題であり、
T-1437 は後者を修正していないし修正する設計でもない。**

### この場で修正しなかった理由

- command scope: 「コード変更は原則せず」「scope 外の…修正…は別 task として返す」の方針に従う。
- D399 が定めた設計 (env var transport、floor policy への複写禁止) を守りながら
  `floor_campaign.sh` へ実際に配線する作業は、独立した実装面変更であり Codex `role=author` を
  要する規模である (段階導入の原則、規律5)。
- T-971 (2026-08-14) が既に同じ理由でこれを scope 外に送っている先例があり、今回も同じ判断を
  踏襲するのが一貫している。

### 推奨する次の一手

新しいタスクとして起票し、次を段1 brief の出発点にする:

1. D399 の設計 (`IZANAGI_SORT_SWO_MASSTREE_ROOT` env var transport) に従い、
   `tools/pegasus/floor_campaign.sh` (または `submit_floor.sh`) に masstree source root の
   ログインノード pinned staging → 計算ノードへの受け渡し配線を追加する。
   `tools/pegasus/silo_ladder_rung1.sh` が同種の staging を自動実行している先例を参照する
   (ただし T-971 時点の `silo_ladder_rung1.py:1046` という参照は現在ファイルが `.py` から
   存在しない状態に変わっている可能性がある — 現況を再確認してから着手すること)。
2. `docs/pegasus-runbook.md:747-748` の「floor/oracle を Pegasus で走らせる際は out_root 配下
   `claims/` の事前作成と `IZANAGI_RESERVATION_*` の export が必要 (floor 実測は次段)」という
   当時の注記が、masstree staging 配線を指した「次段」なのかを確認する。
3. 配線後、本 insight と前回 insight の投入パラメータを再利用して床値 pilot を再々投入できる
   (admission・toolchain・protocol・mocc source_digest はいずれも健全と確認済み)。
4. sort_best 以外の 11 セル (rr20/rr80 × ident_all/backoff_fixed_best/p2_2_flag_opt/
   system_gate/stock_common) は masstree に依存しない可能性がある (build 開始した 3 セルは
   masstree なしで preflight を通過している) — driver の fail-fast 設計 (1 セルの失敗が
   全体を止める) を変えず sort_best だけ先送りできるかは、driver 実装
   (`orchestrator/campaign/s8b_floor_campaign.py`) の cell 処理順とエラーハンドリングを
   読んでから判断する (今回は実装していないため未確認)。

## admission ticket・retry slot の消費について

**確認済み: 本試行はチケットを 1 枚も消費していない。** admission root
(`.git/izanagi/s8b-holdout-admission-v1`、全 worktree 共有) の `claims/` `consumed/` 両
ディレクトリを実測したところ、本 job 実行時刻 (2026-08-21 08:44 JST 前後) 以降に作成された
file が 0 件だった。前回同様、`build_cells` (cell 単位の attempt ticket 消費より前の段階) で
停止したためと考えられる。次回の再投入は `retry_slots_per_cell=2` を全 12 セルぶんフルに
保持した状態から開始できる。

## 証拠の所在 (repo 外へ退避済み)

全証拠 (submission receipt・job staging・job evidence checkpoint・run directory・単一テナント
claim marker・s8b-build-cache) を repo 外の 1 bundle へ退避済み:

`/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t1431-floor-resubmit/evidence-bundle/`
(`README.md` に元 path との対応表、`MANIFEST.sha256` に全 159 file の sha256。
`sha256sum -c MANIFEST.sha256` で整合性検査済み、rc=0)。

repo 内の元 path (`output/claims/`、`output/env/pegasus/calibration/s8b-floor-pilot/`、
`output/env/pegasus/floor/attempts/submissions/…`、`output/env/pegasus/floor/job-staging/…`、
`output/s8b-build-cache/`) は holdout clean-scan 汚染 (将来の official 床値 job の起動証明を
止める) を避けるため削除済み (前回 entry 743 と同じ運用)。
