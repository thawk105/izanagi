# handoff — [T-971] 床値 sort_best セルの SWO oracle infrastructure-unavailable

- 目的: 床値 sort_best セルの SWO oracle が infrastructure-unavailable になる理由を確定し解消する
- 状態: 作業中
- 最終更新: 2026-08-13 20:30 JST
- 基準コミット: 48b2caab (作業ツリー dirty — 段 5 実装差分あり)

- wave: dev-wave (背景 job b7ba731c), branch `worktree-dev-wave-t971-swo-oracle-floor`
- worktree: `/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t971-swo-oracle-floor`
- 開始: 2026-08-13 17:55 JST

## 起動時検査 (2026-08-13 17:55–18:00 JST)

- `ListAgents`: 稼働 8 本。編集面が `sort_swo_oracle.py` / `floor_campaign.sh` と
  重なるものは無い。
- `git worktree list`: 12 本。`t1040-t1042-t1043-t1047` だけが
  `orchestrator/tests/test_sort_swo_oracle.py` を触る (末尾へ test 1 個 append)。
  production 側 `sort_swo_oracle.py` は無改変。→ **EOF append の merge 競合だけが残存リスク**。
- `docs/handoff/`: README のみ (正常)。
- `check_wave_startup.py`: submodule 初期化後 OK。

## 段 1 前提実測 (2026-08-13 18:05–18:20 JST)

repo 外 probe = `/home/SFC/tanab/.claude/jobs/b7ba731c/tmp/probe_resolve.py`
(T-317 裁定により親が直接書いてよい)。production の `patchharness.checkout` +
`resolve_oracle_environment` を job と同じ `TMPDIR` 形で実走させた。

- 使い捨て checkout (`$TMPDIR/izanagi_wt_*/wt`) 上 → `resolve_oracle_environment` = `None`。
  masstree 候補 8 件すべて `config.h` 不在。
- 共有 checkout 上 → 解決成功 (`/work/1/SFC/tanab/izanagi-thirdparty-cache/masstree`、
  祖先 `…/izanagi` 経由)。
- compiler leg は健全 (`/usr/bin/g++`)。

## 確定した因果

1. `floor_campaign.sh:97` が `TMPDIR=/scr/${PBS_JOBID}` を export。
2. `patchharness.checkout` (`patchharness.py:362`) が `$TMPDIR` 配下へ使い捨て worktree を作る。
3. `s1_direct_comparison.py:614` が **その使い捨て path** で
   `resolve_oracle_environment(sub)` を呼ぶ。
4. 候補 3 系統が全滅 — `build/_deps` は作りたてなので不在、祖先 fallback は
   `/scr/...` を辿るので届かない、env var は未設定。→ `None`。
5. `check_materialized_sort_swo` が `environment is None` で
   `phase="environment-resolution", detail_code="oracle-environment-unresolved"` の
   UNAVAILABLE を返す (`sort_swo_oracle.py:1237`)。
6. `s1_direct_comparison.py:627` が `SortSwoOracleUnavailable(oracle)` を raise。

## 診断が消える場所 (確定)

- 床値 driver は `run_role` を使わず `prepare_cell` を直接呼ぶ
  (`s8b_floor_campaign.py:115`)。`run_role` 側にある WAL 記録
  (`s1_direct_comparison.py:928-933`) は**通らない**。
- `build_cells` (`s8b_floor_campaign.py:1334-1417`) に try/except が無い。
- `main()` (`s8b_floor_campaign.py:4020`) は `FloorCampaignError` しか捕まえない。
  `SortSwoOracleUnavailable` は `RuntimeError` なので**未捕捉で traceback 送り**。
- `SortSwoOracleUnavailable.__init__` は `super().__init__(INFRASTRUCTURE_REASON_CODE)`
  だけ (`sort_swo_oracle.py:300`)。**`str(exc)` に phase も detail_code も乗らない。**
- → journal には `reservation-preflight` しか残らない = entry 504 の実測と一致。
- 対照: `p3_s4_loop_sort.py:186-196` は raise 前に `attempt_record(oracle)` を WAL へ書く。
  **記録する先例は既にある** (族一般化ではなく局所修復)。

## 触ってはいけない不変条件 (DW-O09 の棚卸し結果)

- `ORACLE_CONTRACT_ID` は `test_sort_swo_oracle.py:870-875` で **exact literal 固定**。
  依存は `CORPUS_SHA256` / `TU_TEMPLATE_SHA256` / `COMPILE_FLAGS_SHA256` /
  `AXIOM_CHECKER_IMPLEMENTATION_SHA256` の 4 つだけ。
- `AXIOM_CHECKER_IMPLEMENTATION_SHA256` は
  `_AXIOM_CHECKER_SOURCE_FUNCTIONS = (check_relation_matrix, _evaluate_executable,
  _run_matrix, _compile_command)` の**逐語 source hash**。→ **この 4 関数は 1 byte も触れない。**
- `resolve_oracle_environment` / `check_materialized_sort_swo` は hash 外 = 改変可。
- ただし `test_sort_swo_oracle.py:1081` が `"/work/" not in resolver_source` を要求。
  → **resolver に site 絶対 path を literal で書けない。**
- `output/` 配下に `sort-swo-v` を pin する凍結成果物は 0 件 (grep 実測)。

## 段 2 プランの主張に対する親の独立検算 (2026-08-13 19:00–19:20 JST)

plan.md (rc=0, check_codex_output OK) の load-bearing な主張を親が全件検算した。

| 主張 | 判定 | 実測 |
|---|---|---|
| floor policy は `tools/pegasus/policies/floor_v1.json` で walltime しか持たない | **real** | 111 bytes、key 3 個のみ |
| gflags/glog は凍結共有 `tools/pegasus/policy.json` にあり D115 で 1 byte も変えない | **real** | `docs/decisions.md` D115 決定 (1)(2) の逐語と一致 |
| masstree HEAD = `b3c5d054b66b08374d7a6ff5a0faeaf28b041a38` | **real** | `git rev-parse HEAD` 一致 |
| masstree `config.h` は gitignore されており Git 非管理 | **real** | `.gitignore:8:/config.h`、`git ls-files` 空 |
| `config.h` sha256 = `e9a4ecd3...404694a` | **real** | `sha256sum` 一致 |
| journal へ追記すると strict L / M-prestart resume を壊す | **部分的に real (下記)** | `s8b_floor_contract.py:450-466` を実読 |
| `ATTEMPT_DIR` は `/work` 上の job-staging に residing し job 後も残る | **real** | `floor_campaign.sh:163` + entry 504 の 84 file 退避 |
| `floor-driver.stdout` は create-only で開かれる | **real** | `floor_campaign.sh:177` に `set -o noclobber` |

**親による補正 1 件。** plan は「journal 追記が strict L を壊す」を (P1) 反証の主根拠に置いたが、
**実際の pilot 経路では strict L は既に成立していない**。fresh 経路の journal 書込みは
`launch-start` (`:3390`、`certificate is not None` のときだけ) と
`reservation-preflight` (`:3402`、`reservation_check is not None` のときだけ) の 2 つで、
entry 504 が観測した journal は `reservation-preflight` 1 行のみ = `certificate is None`。
`classify_journal_resume_state` は `records[0]["event"] == "launch-start"` を要求するので
**この時点で既に L でない**。よって plan の論拠はその構成では効かない。

ただし **(P1) を棄却する結論自体は維持する**。より強い理由が別にある:
- driver stdout は `certificate` / `reservation_check` の有無に**依らず必ず存在する** (無条件)。
- `run_write_capability` に依存しない (capability 拒否時も残る)。
- 既存 resume 状態機械を 1 mm も動かさない (`certificate is not None` 構成の L を壊さない。
  ここは plan の指摘が正しく効く)。
- 成功時の stdout 解析は `driver_rc -eq 0` でしか走らない (`floor_campaign.sh:969`) ため、
  error 経路に 1 行足しても success 経路の parse を乱さない。

## 進捗

- [x] 起動 3 点検査 / worktree 隔離 / submodule init
- [x] 段 1 前提実測 (原因確定)
- [x] 段 1 brief
- [x] 段 2 プラン起草 (codex, rc=0)
- [x] 段 2 主張の親による独立検算
- [ ] 段 3 敵対相談 (codex 並列、投入済み・待機中)
- [ ] 段 4 裁定 + 変異事前登録
- [ ] 段 5 実装 (codex author)
- [ ] 段 6 敵対レビュー + fix + 変異 matrix + 受入
- [ ] 段 7 記録 / 段 8 自己改善 / 段 9 land

## dev-wave 改善候補

(段 8 で routing する。現時点で 0 件)
