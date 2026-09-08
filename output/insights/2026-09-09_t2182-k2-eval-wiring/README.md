# [T-2182] K2 宣言アームの評価経路を Pegasus へ配線した (2026-09-09)

wave: `dev-wave-t2182-k2-eval-wiring` / branch `worktree-dev-wave-t2182-k2-eval-wiring`
実装 commit: `9a32ef5ca`。変異 matrix 5/5 KILLED、期待 node 完全一致。

## 一行で

**依頼が挙げた前提 4 件は 4 件とも着地済みで、実際に欠けていたのは 2 点だった。** job body が
driver へ K2 引数を渡す口と、condition gate へ offline の依存情報を渡す配線である。後者は
2026-09-02 に 6 回投入して到達した停止点そのもので、env の受け口だけを足しても同じ場所で止まる。

## 持ち越しの前提は stale だった

依頼と持ち越し本文 (`docs/archive/worklog-phase3-0902-1212.md`) は「残るのは前提 4 件」と述べる。
着手前に一次資料で照合したところ、**4 件とも main に着地済み**だった。

| 前提 | 現況 | 根拠 |
|---|---|---|
| 段 4 loop 用の専用 env タグ | 着地済み | `orchestrator/campaign/p3_s4_loop.py` の `_SITE_ENV_TAGS` が `PEGASUS_COMPUTE -> "pegasus"` |
| calibration の取り直し | 着地済み | `orchestrator/campaign/env_contract.py` の pegasus 世代 1/2 と `output/env/pegasus/calibration/registered/` の 2 file (実在確認) |
| binding の固定 | 着地済み | job body が expected HEAD・superproject clean・CCBench PIN・gflags/glog の HEAD と clean・toolchain manifest を照合 |
| provenance の追跡 | 着地済み | 同 job body の reservation.json / masstree-prebuild-receipt.json / compute-result.json (create-only) |

経緯は [T-2232] (job body 新設、2026-09-05) と [T-2406] (gflags/glog 供給、2026-09-08)。
持ち越し本文は 2026-09-02 時点の写しのままだった。**持ち越しの記述どおりに着手していたら、
既に存在する実装を作り直していた。**

## 実際に欠けていた 2 点

### 1. job body が K2 引数を運ばない

段 4 loop の Pegasus job body は driver へ `--run-iteration` までしか渡さず、K2 の 4 引数
(`--knowledge-manifest` / `--coder-role` / `--knowledge-classification` /
`--knowledge-de-novo-claim`) を運ぶ口を持たなかった。driver 側 CLI は 4 つとも実装済みで、
不足は job body の環境変数の受け口だけだった。

必須束は **{manifest, coder role} + proposal path** とした。分類と de novo 宣言は任意
(設定時のみ非空を要求して転送、未設定なら driver 既定に委ねる)。**4 つ全部を必須にする案は
不採用にした** — この 2 値は campaign identity に入らず受領証にしか届かないため、必須化は
同じ成果物を作れる入力を不受理にするだけで受理集合を不要に狭める。

### 2. condition gate へ offline の依存情報が渡らない

**これが評価経路の実際の停止点だった。** 段 4 loop は候補を build する前に
`_require_condition_gate` を呼ぶ。この gate は自前で cmake configure を起動するが、
同じ scope にある offline の FetchContent 情報は `run_campaign` にだけ渡されており、
gate には渡っていなかった。計算ノードには network が無いので、gate の configure は
masstree / mimalloc / googletest を clone しようとして失敗する。

2026-09-02 の実測では、環境の阻害要因を外すたびに停止点が
compiler-failed → configure-failed → preprocess-failed と前進し、6 回目
(3 依存すべて offline 供給) で `supply=preprocess-failed` に到達していた。
**同じ場所である。**

prebuild receipt がある走行でだけ configure 引数を渡し、receipt の無い既存経路
(linux-baremetal を含む) は挙動を変えない。

## 子の所見で不採用にしたもの

- **「受け口が別 wave 所有の file にあるので依存待ち」は不採用。** 段 3 の相談子は
  `condition_meaning_gate.py` を変更しないと直せないと結論したが、これは 2026-09-02 の記述
  (「condition gate の cmake argv には `-D` を足せない」) に依拠した stale な判断だった。
  現物を確認すると `capture_define_inputs` は既に `configure_args` を受け取り configure argv へ
  展開する。**受け口は main に既存で、同 file は 1 byte も変えていない。**
- **driver 入口で manifest と coder role を相互必須にする案は撤回した。** 段 3 の相談子が
  「manifest だけ渡すと K2 identity のまま K2 consumer を通らない」という fail-open を示し、
  親は一度これを採用した。しかし実装子が停止し、既存テスト
  `test_main_manifest_only_accepts_legacy_flattened_proposal` が
  **意図して登録された正例**であることを示した。その fixture は
  `retrieval_result.status = "completed_empty"` / `sources: []` の manifest で、
  「K2 と宣言したが取得結果が 0 件」という意味のある経路を守っている。ユーザーが gate の追加を
  scope 外と明示しているので撤回し、裁定パッケージとして返す (下記)。

## `buildcache.py` は編集していない

同 file は `campaign_lock.py` の enforcement source closure の member である。closure member を
変更すると campaign lock を作る全テストが contract-loader-drift で落ちる (2026-09-02 に
`wal.py` で 48 件のマスクを実測)。condition gate へ渡す define は `p3_s4_loop.py` 側で組み、
生成器の束縛は「同じ入力で campaign build が作る configure argv と同じ FetchContent token を
持つ」ことを検査するテストで保っている。

## 段 6 レビューが見つけた偽の帰属

**K2 の負例テストが、K2 の関門ではなく別の guard によって赤くなっていた。** 負例は
`IZANAGI_S4_REPO_ROOT` に `.codex/worktrees/` 配下の path を渡していたため、K2 preflight を
変異で無効化しても走行は AI worktree container の guard で拒否され、期待 stderr の不一致で
赤になっていた。専用 checkout (production の投入形) では同じ変異が K2 preflight を素通りする。

負例の repository root を `tmp_path` ベースへ変え、**sentinel 実行体 (git / cmake / python3.10 /
qstat) が呼ばれていないこと**を stderr 検査より先に確かめる形にした。これで変異は
「K2 preflight を素通りして先へ進んだ」ことによって赤くなる。

もう 1 件、**機構の正例が production の形を覆っていなかった。** 実際の job route は
`dependency_prefix` を driver へ渡さない (job body が `CMAKE_PREFIX_PATH` を環境へ export する)
ため、production の configure 引数は 4 件である。正例は 5 件の形だけを検査していたので、
4 件の production 形を足した。

## 変異 matrix

事前登録 6 件のうち 5 件を本走した (M3 は裁定 2 の撤回に伴い不登録)。**5/5 KILLED、
期待 node は完全一致。**

| # | 変異 | 結果 | 赤になった node |
|---|---|---|---|
| M1 | condition gate へ渡す source define を落とす | KILLED | `test_prebuild_offline_tokens_reach_real_condition_gate_configure_argv`、`test_prebuild_offline_tokens_without_dependency_prefix_match_production_shape` |
| M2 | prebuild 情報の有無を見ず常に渡す | KILLED | `test_without_prebuild_real_condition_gate_configure_args_remain_empty` |
| M4 | K2 の要求検出を「設定済み」から「非空」へ弱める | KILLED | `test_set_empty_manifest_alone_is_refused_by_actual_job_body` |
| M5 | proposal path 必須の拒否を無効化する | KILLED | `test_complete_k2_pair_without_proposal_is_refused_by_actual_job_body` |
| M6 | proposal 分岐から K2 argv の展開を除く | KILLED | `test_complete_k2_environment_reaches_actual_job_driver_argv` |

**job body への変異は 48 件の定数マスクを作る。** `test_registered_fragment_mutants_have_one_static_failure`
は自身が fragment 変異を注入して「静的失敗がちょうど 1 件」を検査する meta-test であり、job body を
変異させるとこの parametrized 族が一律に赤くなる。変異に依存しない一定のマスクなので、runner argv を
期待 node 6 件へ絞ってマスクを収集対象から外し、単一理由の kill を取った。

probe 走 (全件 SURVIVED 登録) の結果は `mutation-probe2-report.json` に残す。probe では m02 が
SURVIVED だった — 親が当て所を誤り、呼び出し側ではなく helper 内部の guard を変異させていた。
本走では呼び出し側へ照準し直して KILLED を取った。

## 主張しないこと

- **Pegasus で評価経路が通ったとは主張しない。** 本 wave は配線までで、実投入していない。
  投入には固定 SHA の専用 checkout が要り、本 wave の変更は land 前で main に無い。
- README §7 が明記するとおり、gflags/glog prologue 以後 (prologue の build 時間、receipt を
  通した build の成立、attestation の exact 照合、walltime 03:00:00 の充足) は未実測である。
  `_assert_single_tenant` も計算ノードで未実測である。
- 完了条件 4 件のうち達成は依然 1 件 (知識 manifest の受領証) である。残る 3 件
  (provenance 束縛・stock と異なる identity・gate の terminal verdict) は実投入で初めて測れる。

## 次の wave への出発点

配線は入った。次は固定 SHA の専用 checkout から実投入し、condition gate を越えて WAL の
BUILD_START へ到達するかを実測する。§7 の qsub 手順に K2 の 5 環境変数を足した正例がある。
2026-09-02 の run card (campaign 識別子・manifest digest・知識 source 2 件・workload) は
`output/insights/2026-09-02_t2182-k2-arm-liveness/README.md` にある。
