## 実装した内容

所有 path 内に **14 ファイル**を追加しました。既存 tracked file・docs・submodule は変更していません。index／履歴を書き込む操作、commit は行っていません。

適用順は次のとおりです。

| patch | 適用する直前の状態 | 変更 |
|---|---|---|
| `instr-silo-function-policy-probe.patch` | 骨格 | worker 別独立計数、戻り値照合、要因照合、終了時の mutex 付き出力 |
| `broken-silo-policy-norw-validation.patch` | 骨格 | 要因記録を含む abort 部を無効化 |
| `broken-silo-policy-lockskip-validation.patch` | 骨格 | 共通ループ前で max_wset 更新後に continue |
| 既存 early-unlock | 骨格 | 既存 patch をそのまま使用 |
| 機構変異 8 枚 | 骨格 → probe | clamp／reload／limit／両 prefix unlock／3 hook／要因記録の変異 |

probe は `IZANAGI_SILO_POLICY_PROBE`、機構変異は各一か所の `#if IZANAGI_BREAK_SILO_POLICY` を使用します。probe 不使用の機構変異走も、適用基底として probe patch は重ねますが、macro を供給せず計装を除去します。

`focus.cpp` は指定された状態・符号化・attempt 判定を実装しました。

`orchestrator/campaign/silo_policy_coverage.py` の coverage は **30 case・53 check** です。

- 負例 6 走：norw は `non-serializable && cycles>=1 && exit_code==1`。lockskip は cycles=0・violations>0・indeterminate・両 X reason。early-unlock は保持欠落 reason のみ。各走に owner TU の macro 0/1 差分と case／patch／source digest を保存。
- 焦点 3 走：符号化照合、正の到達数、retry 成功、上限 abort、clamp、要因保存則を検査。未到達要因は `unmeasured`。
- 機構変異 8 走＋対照 8 走：指定表の層で判定。no-limit は `NON_DETECTION_CONTROL`。
- flag 境界 4 件：owner TU の preprocess が指定 `#error` で失敗することを要求。
- TRACE=0 1 件：実 compile command と preprocess の診断混入を検査。

case／check の完全一致、厳密な bool、到達数、観測から再計算した判定との一致を確認して `all_pass` を出します。

smoke は stock＋4 方策、**5 case・30 check**。DiffQuarantine → effect gate → B の grammar → 単独 TU compile を通過した本文だけを materialize し、digest・書込み後の一致を確認します。その後、legacy／性能構成 verify、bench 1 回、source identity を検査します。全 build は `NON_ADMISSIBLE` です。

## 確認の実測

すべて rc=0 でした。

- driver・test の `python3 -m py_compile`
- 一時 git repo で、骨格 → 負例 3 種の `git apply --check`／適用
- 骨格 → probe → 各機構変異 8 種の同検査
- `focus.cpp` の単独 TU：`g++ -std=c++17 -Wall -Wextra -Werror -fsyntax-only`
- probe／wrapper 抽出部の単独 TU：同構文検査

`.scratch-t2857-c1/` は削除済みです。

以下は **実装済み・未実走**です。

- `orchestrator/tests/test_silo_policy_coverage.py`：9 test、自走 harness 付き
- driver の `coverage`／`smoke`
- B の実体による受理試験、CCBench build、動的到達・変異検出

## 要る登録 (C2 へ渡す)

| file | 追加・追随事項 |
|---|---|
| `orchestrator/campaign/condition_meaning_gate.py` | `DefineSpec(ROUTE_CMAKE_CXX_FLAGS, _SILO_OWNER, "ycsb_silo.exe", patch)` の形で PROBE／BREAK を追加。companion は軸 ON。既存 norw／lockskip macro を新 patch でも再利用 |
| 同上 | 通常骨格の `#if SILO_POLICY_VARIANT` は15か所、通常 probe の `#if IZANAGI_SILO_POLICY_PROBE` は21か所。BREAK は各1か所 |
| `orchestrator/campaign/materializer_admission.py` | `orchestrator.campaign.silo_policy_coverage._build_variant` を `MaterializerRegistration(NON_ADMISSIBLE, …)` で登録 |
| `orchestrator/tests/test_ccbench_spawn_sites.py` | 新 build sink `_build_variant`、直接 subprocess site `_run:451`、既存 helper 経由の configure／`_preprocess`／`_verify` 呼出しを inventory に反映 |
| `orchestrator/tests/test_condition_meaning_gate.py` | define／meaning 閉集合、site 数、specimen と新 patch の追随 |
| `orchestrator/tests/test_p3_s4_loop.py` | 新11 patchの path 別 `IZANAGI_` 許容集合。機構変異は BREAK と、patch 内に現れる PROBE を含む |
| `orchestrator/tests/test_campaign.py` | 単位 A の軸 module／SOURCE_REL 登録確認 |
| smoke 接続試験 | `prepare_policy` の拒否・例外・timeout・unavailable が build に到達しないことを統合検証 |

機構変異では、その実 source 上の BREAK 分岐を証明します。軸／probe の site-count 証明は正常対照で取得します。囲い込み型変異が inactive branch に複製した site を、正常 probe の証明と混同しません。

事前登録 node は指定どおり追加済みです。

- `test_judge_rejects_missing_or_empty_checks` — M-CHK-EMPTY
- `test_norw_judgement_requires_exit_code_one` — M-CHK-NORW

## 計算ノードでの実行

B／C2 統合後、親が実行する command です。今回は投入していません。

```bash
python3 tools/pegasus/dispatch_compute.py --task generic --walltime 01:00:00 -- /usr/bin/python3 orchestrator/campaign/silo_policy_coverage.py coverage --third-party-cache /work/1/SFC/tanab/izanagi-thirdparty-cache
```

```bash
python3 tools/pegasus/dispatch_compute.py --task generic --walltime 01:00:00 -- /usr/bin/python3 orchestrator/campaign/silo_policy_coverage.py smoke --third-party-cache /work/1/SFC/tanab/izanagi-thirdparty-cache
```

- coverage：30 case、CCBench build 26 回、trace 25 走。timeout 期待2走は各120秒。
- smoke：5 case、CCBench build 10 回、trace 10走＋bench 5走。
- 依存ライブラリ build と condition-gate configure は別途発生します。各1時間は未実測の余裕を含む walltime 目安です。

出力先は `output/env/pegasus/calibration/silo_function_policy_{coverage,smoke}.json` です。

## 未了と疑問

**「対応する照合だけが不一致になる」という条件は、指定の符号化と固定応答変異では成立しません。**

abort hook を `0u` にすると、戻り値に含まれる lock／commit の符号も失われます。lock hook の固定 `(abort, 0)` も、abort 回数の符号を失います。指定本文と変異を維持し、driver は表で指定された対応不一致の発生を判定しますが、**単一理由性の証明は未了**です。

また、B／C2 統合、全体 build、テスト、動的到達、certified、timeout、throughput は未確認です。

## 総括

C1 の patch・焦点方策・driver・test を追加し、許可された構文検査と厳密適用検査は通りました。**実走合格および C 段合格は主張しません。** 親への残件は B／C2 統合・計算ノード実走と、hook 変異の単一理由性に関する仕様の整理です。