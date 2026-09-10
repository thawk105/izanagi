# 段 7 記録 (R5 closure wave) — 受入・裁定・裁定パッケージ

## commit

| commit | 内容 | 検査 |
|---|---|---|
| `ab09eb618803e730a2873c5265dac5caca0e6096` | wave 実装一式 50 path (前 wave の U1〜U4 + 本 wave の R5 closure) | `check_ai_provenance` green (551 件) |
| `b704bf8585df…` | matched lookup candidate witness の被覆欠落を閉じる test 1 件 | **`check_ai_provenance` 赤** (下記 裁定パッケージ 2) |

## 受入 (Pegasus gen_S 計算ノード)

環境: bnode002 / bnode021 / bnode0xx、affinity 48、`/usr/bin/python3.10` (3.10.12)、
`python3.10 -m pytest -n 48 -q -rf`。**製品 dispatcher は経由していない** (理由は下記 L1/L2)。
受入 job script は job tmp に置き repo へ commit していないため、受入は repo から再現できない。

| 段階 | failed | passed | skipped | 失敗集合 |
|---|---|---|---|---|
| 実装前 baseline | 15 | 4069 | 19 | — |
| 段 5 実装後 | 15 | 4078 | 19 | baseline と完全一致 |
| fix 第 1 巡後 | 15 | 4085 | 19 | baseline と完全一致 |
| fix 第 2 巡後 (最終) | 15 | **4086** | 19 | **baseline と完全一致** |

新規 test 17 件はすべて緑、回帰ゼロ。途中 1 回だけ
`test_codex_worker_launch.py::test_fake_stdout_matches_observed_cli_event_shape` が落ちたが、
単独 3/3 緑・同 file 全体 48 worker で 58 passed・再走で非再現のためフレークと裁定した
(`--termination-grace-s 0.05` / `--poll-interval-s 0.01` の timing 依存で、worklog 既登録の
T-190 / F57 と同型)。

## 変異 (`DW-M01`〜`DW-M08`)

- anchor `ab09eb6` の本走: **killed 8 / survived 1 / abort 0 / 復元失敗 0**
- R7b の生存は両層同時変異まで裏取りし「mask ではなく真の被覆欠落」と確定 (`DW-M02`)。
  初回結果は `s6-mutation-r5.md` に erratum として残す
- fix 第 2 巡後の再走 (anchor `b704bf8`): **killed 9 / survived 0 / abort 0 / 復元失敗 0**
- R5 (monitor の group 束縛差替) は裁定 2 のとおり **冗長 gate の診断 pin** であり closure に数えない
- R6 の入力は製品が書けない WAL 行 (RB-5) なので、成果物影響は書けない。fail-fast と
  対称性回復の pin として数える
- 登録変異 R8 は **構成不能**。`monitor_job` 入口の `policy != snapshot_policy` gate により
  `policy.account == snapshot_policy.account` が恒真になるため (RA-7 refuted の帰結)

## 15 の既存赤 — 本 wave の scope 外、全件の根本原因を特定済み

| 件数 | file | 根本原因 |
|---|---|---|
| 10 | `test_s8b_oracle_driver.py` | `buildcache.py` が module import 時に `<repo>/tools/pegasus_policy.py` を trusted policy source として読むのに、T-080 E2E fixture の `required` 集合に同 path が無い **consumer 取り残し**。`orchestrator/` を丸ごと copytree する一方 `tools/**` は 1 件も複製しないため、fixture repo で `FileNotFoundError` → `ImportError` |
| 3 | `test_pegasus_test_dispatch.py` | U2 の自己不整合。`max_spool_bytes: 32` を override する自 test を自 `load_policy` の aggregate bounds 検査が拒否 (1)、`ControllerSignal` が `submit_and_monitor` で変換されず素通し (2) |
| 1 | `test_run_tests_task_run.py` | `tools/run_tests.py:849` の `AttributeError: 'NoneType' object has no attribute 'get'` |
| 1 | `test_pegasus_tools.py` | `certify_calibration.sh` に存在しない `PERF_CANDIDATES` 断片を期待している |

base `72e3800` の clean checkout では同 3 file が 178 passed / 0 failed であることを実測し、
これらが staged 差分側に帰属することを確認した。s8b の 10 件については、fixture が
git ではなく作業ツリーを copytree し `required` 集合がハードコードであることから、
「未 commit 状態が原因」ではないことを静的に確定した。

## 親の追認 — FR-1 (焦点再レビューの新規所見) は実測で CONFIRMED

`DispatchPolicy` は `@dataclass(frozen=True)` で、第 1 field が `policy_path: Path` である。
`load_policy` は `policy_path=policy_path.resolve(strict=True)` を入れるため、**同一 bytes の
policy でも path が違えば `!=` になる**。

親が実測した結果 (repo 側 policy と、同一 bytes を別 path へ複写した policy の比較):

```
same policy_sha256 = True
same account       = True
policies equal     = False
```

製品は `tools/pegasus/submit_tests.py` の `load_policy()` (repo 側 path) を
`submit_and_monitor` / `resume_dispatch` へ渡す一方、snapshot 側は snapshot root から load する。
よって `policy != snapshot_policy` は**恒真**であり、次の 3 gate が製品経路で常に発火する。

- `qsub_argv` の `"qsub policy differs from snapshot-bound policy"` 相当
- `monitor_job` の `"monitor policy differs from snapshot-bound policy"`
- `resume_dispatch` の `"resume policy differs from snapshot-bound policy"`

**すなわち本 branch の dispatcher は本番で submit も resume もできない。** テストは
`_synthetic_snapshot` が snapshot root 内へ policy を書いて同じ path から load するため、
この欠陥は永久に露見しない。R5 の scope 外なので実装せず裁定パッケージへ返す。

## 親の実測主張の訂正 (段 3 で反証された分)

- **L1 撤回**: 「site-wide `PYTHONPATH` の一律拒否は過剰拒否」は誤り。`_PLUGIN_ENV` 非空拒否が
  守るのは子へ渡す env ではなく、**その検査を実行している login 側 interpreter 自身が import
  汚染下でないこと**である。除去は既に import 済みの `sys.path` へ遡及しない。安全側の正しい拒否。
  運用は `env -u PYTHONPATH` を正規手順とする
- **L2 撤回**: 「nested submodule の recursive 要求は契約と食い違う過剰拒否」も誤り。
  未初期化のまま通すと snapshot closure が実ツリーと食い違い、`max_total_bytes` / `max_files`
  予算も manifest closure も破綻する。直すべきは契約側 (`DW-O08`) か運用手順であり dispatcher ではない

## 裁定パッケージ (ユーザー裁定要)

1. **T-193 二重正本 — 本 wave の証拠で決着可能**。main (`aa67805` 以降) の
   `orchestrator/campaign/site_policy.py` + `tools/pegasus/dispatch_compute.py` は T-192 で
   計算ノード 4012 passed の受入実績がある。一方**本 branch の dispatcher は
   (a) FR-1 により本番で submit も resume もできず、(b) 15 の既存赤を抱え、
   (c) login から起動する正規手段が無い** (L1/L2 は正しい拒否だが運用手順が未整備)。
   本 branch を正本にするなら少なくとも FR-1 と 15 赤を閉じる wave が要る
2. **D95 の例外**。ユーザー裁定「codex はレートリミットが近いので claude で代替してください」に
   従い、本 wave の実装面は Claude が author した。`docs/ai-provenance.md` は
   「Codex が実行不能なら Claude が代行せず停止し、例外の必要性をユーザー裁定へ返す」と定めるため、
   `b704bf8` は `check_ai_provenance` で赤のままである。**存在しない Codex trailer は書いていない。**
   例外を文書化するか、Codex で author し直すかの裁定が要る
3. **FR-1 の修正方針**。`DispatchPolicy` の等価比較から `policy_path` を外す
   (`field(compare=False)`) か、3 gate を `policy_sha256` 比較へ変えるか。
   どちらも製品 gate の受理集合を変えるため独立 wave とユーザー裁定が要る
4. **L1/L2 の運用手順の置き場所**。`env -u PYTHONPATH` と
   `git submodule update --init --recursive` を Pegasus runbook へ書くか、`DW-O08` を改めるか
5. **段 6 レビューが残した nit** — RA-3 (故障モデルの限定表記)、RA-5 (`read_text` の
   TOCTOU と非 `DispatchError` 例外)、RA-10 (診断文言の回帰)、RA-14 (`create_qsub_result` と
   `O_EXCL` の衝突による resume liveness 欠落)、RB-7 (変異下で post-condition assert が未評価)、
   RB-11 の残り未被覆

## 主張しないこと (`DW-S07`)

- 製品 dispatcher の end-to-end (submit → lookup → monitor → accounting → final publish) は
  一度も実走していない。本 wave が触った `Group Name` 束縛そのものも、製品経路では未検証
- 受入は親側の使い捨て qsub job による pytest 集計値までであり、`final-receipt.json` は
  1 件も生成していない
- 15 の既存赤は本 wave では直していない
