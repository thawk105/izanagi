## 節構成

成果物は `output/insights/2026-09-01_paper-story-a1-balanced5-pilot-preregistration/README.md` の 1 ファイルだけとする。予定行は親が本文を起草するときの配置目安であり、内容の出典は次のとおり固定する。

| 予定行 | 節 | 書く内容 | 根拠 |
|---|---|---|---|
| `README.md:1-9` | 表題・メタデータ | `study_id`、人間可読の対であること、計測前凍結、pilot-only、本文へ hash を書かないこと | [`study_id` / `authority`](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1777-pilot-prereg/orchestrator/campaign/paper_story_a1_paired.v3-pilot.json:2)、`final_estimate_eligible` 同:37、先例:1-8、D1296 |
| `README.md:11-30` | `## 1. 何を測るか` | 3 workload、各 variant と `no-backoff` baseline、role による contrast、規模、探索目的 | `workloads[*]` 同:188-305、`scale` 同:109-119、`pairing.contrast` 同:58、`execution.mode` 同:32 |
| `README.md:32-59` | `## 2. pilot の配置と記録` | 60 対/workload、5 対×12 block、AB/BA 均衡、凍結 seed、記録する observation fields | `pairing` 同:56-85、`sizing.pilot_*` 同:170-176、`workloads[*].schedule_root_seed`、D1296、receipt keys [`paper_story_a1_paired.py:1568-1584`](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1777-pilot-prereg/orchestrator/campaign/paper_story_a1_paired.py:1568) |
| `README.md:61-69` | `## 3. 推定対象の限定` | 英文 estimand の逐語と D1295 項目 5 の日本語限定 | `pairing.estimand` 同:60、D1295:41639-41640 |
| `README.md:71-88` | `## 4. pilot から計画 sigma を作る` | `sigma_pair`、`sigma_block`、上側係数、最終的な `max` | `sizing` 同:121-185、D1296、[`size_paper_story_a1_balanced.py:386-523`](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1777-pilot-prereg/tools/size_paper_story_a1_balanced.py:386) |
| `README.md:90-125` | `## 5. 反復数の探索と判定` | candidate grid、区間、floor、3 条件、成功定義、80% 条件、certification、seed 分離 | `sizing.n_grid/conditions/*probability`、D1296、同 tool:534-728, 773-828 |
| `README.md:127-172` | `## 6. 走行・品質・invalid・再走` | execution、CV、16 個の invalid、閉じた再走理由、CCBench pin/boundaries | `execution`、`quality`、`invalid_rules`、`rerun`、`ccbench_acceptance` |
| `README.md:174-182` | `## 7. pilot と最終推定の分離` | pilot は sizing 入力だけで、本走の推定へ混ぜない | `authority.result_authority`、`final_estimate_eligible`、D1296:41680 |
| `README.md:184-210` | `## 8. この設計で言えないこと` | 残る限界と、配置変更により旧先例から変わった限界 | D1295 理由、policy、driver の v3 limitations [`paper_story_a1_paired.py:4334-4348`](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1777-pilot-prereg/orchestrator/campaign/paper_story_a1_paired.py:4334) |

先例の「還元判断」は pilot policy に対応する field も D1295/D1296 の要求もないため落とす。独立した「推定対象の限定」「pilot と最終推定の分離」を pilot 固有節として足す。

## 逐語対応表

分数 object は常に「既約分数を先、割り切れる場合だけ正確な百分率を併記」とする。近似小数は作らない。

| policy path | 本文へ出す表現 |
|---|---|
| `study_id` | `paper-story-a1-20260901-balanced5-pilot-v1` |
| `authority.formal` | `formal=false` |
| `authority.promotion_prohibited` | `promotion_prohibited=true` |
| `authority.result_authority` | `pilot-sizing-input-only` |
| `final_estimate_eligible` | `final_estimate_eligible=false` |
| `execution.mode` / `.site` | `exploration` / `pegasus-compute-only` |
| `pairing.contrast` | `variant-minus-baseline` |
| `pairing.estimand` | `arithmetic mean of paired differences under the balanced five-rep schedule` |
| `scale.records` / `.threads` / `.extime_s` | `records=1,000,000` / `threads=48` / `extime=3 秒` |
| `scale.ycsb_zipf_skew` / `.ycsb_rmw` / `.ycsb_max_ope` | `zipf skew=0.9` / `rmw=0` / `max_ope=10` |
| `scale.expected_verify_configs` | `legacy` |

Workload と arm は次の組だけを書く。

| `workloads[*]` | 本文表現 |
|---|---|
| `write-heavy` | `ycsb_rratio=5`; variant=`fixed10`, `BACKOFF_FIXED=10`; baseline=`no-backoff` |
| `balanced` | `ycsb_rratio=50`; variant=`fixed5`, `BACKOFF_FIXED=5`; baseline=`no-backoff` |
| `read-heavy` | `ycsb_rratio=95`; variant=`fixed2`, `BACKOFF_FIXED=2`; baseline=`no-backoff` |
| 各 variant | `role=variant`, `contrast=minuend`, `protocol=silo`, `BACK_OFF=1`, `NO_WAIT_LOCKING_IN_VALIDATION=1`, `NO_WAIT_OF_TICTOC=0`, `WAL=0` |
| 各 baseline | `role=baseline`, `contrast=subtrahend`, `protocol=silo`, `BACKOFF_FIXED=-1`, `BACK_OFF=0`, `NO_WAIT_LOCKING_IN_VALIDATION=1`, `NO_WAIT_OF_TICTOC=0`, `WAL=0` |
| 各 workload | `reps=60`, `df=59`, `pair_index=0..59` |

配置と seed は次を逐語対応させる。

| policy path | 本文表現 |
|---|---|
| `pairing.design` | `balanced-a5b5-b5a5-v1` |
| `pairing.arm_block_reps` | `5 rep/arm block` |
| `pairing.group_pairs` | `10 対/組` |
| `pairing.physical_orders.bit_0` | `A^5 B^5 B^5 A^5` |
| `pairing.physical_orders.bit_1` | `B^5 A^5 A^5 B^5` |
| `sizing.pilot_pairs_per_workload` | `60 対/workload` |
| `sizing.pilot_pair_blocks` | `5 対/ブロック × 12、variant 先行 6、baseline 先行 6` |
| `pairing.seed.digest` | `SHA-256` |
| `pairing.seed.order_bit` | `least-significant bit of the SHA-256 digest` |
| `pairing.seed.group_preimage` | `a1-balanced5/v1\|workload=<name>\|group=<zero-based decimal>` |
| `pairing.seed.group_preimage_prohibits` | preimage に `study ID` と `date` を含めない |
| `pairing.seed.all_identical_redraw.*` | counter は `0` から `16` 未満。全 bit が同一なら全列を再描画し、16 到達時は fail-closed |
| `workloads[write-heavy].schedule_root_seed` | `1698e2cba5aa7853040e2fed47e88e1f682a019878348bfc392b8f8f60eb5447` |
| `workloads[balanced].schedule_root_seed` | `b2ada8029ec867d5188c87076f3d7cc4c1314ca642bb0b3c0cd1e4dd811d1a24` |
| `workloads[read-heavy].schedule_root_seed` | `fb3ffea0fc8bace8166b39558b8ac10f426fb92ac5efa8dbe90acb33d6d33fd1` |

Sizing の数値・式は次から一字一句引く。

| policy path | 本文表現 |
|---|---|
| `sizing.alpha_c` | `1/20（5%）` |
| `sizing.family_alpha` | `1/20（5%）` |
| `sizing.arm_failure_probability` | `1/120` |
| `sizing.floor_fraction` | `3/100（3%）` |
| `sizing.required_success_probability` | `4/5（80%）` |
| `sizing.conditions[zero]` | `0/1（0%）` |
| `sizing.conditions[positive-six-percent]` | `+3/50（+6%）` |
| `sizing.conditions[negative-six-percent]` | `-3/50（-6%）` |
| `sizing.upper_factor` | `c(one-sided, alpha_c, df) = sqrt(df / chi-square-quantile(alpha_c, df))` |
| `sizing.sigma_pair` | `c(one-sided, alpha_c, df = 59) * sd(60 paired differences)` |
| `sizing.sigma_block` | `sqrt(5) * c(one-sided, alpha_c, df = 11) * sd(12 five-pair block means)` |
| `sizing.planned_sigma` | `max(sigma_pair, sigma_block)` |
| `sizing.n_grid` | nominal minimum `28`、effective minimum `30`、step `10`、maximum `4096`、maximum candidate `4090`; `evaluate operating characteristics only at the actual candidate n` |

品質規則は翻訳で意味を丸めず、field の英文を併記する。

| policy path | 逐語 |
|---|---|
| `quality.aggregate_cv` | `sample standard deviation of all arm rep TPS divided by arithmetic mean of all arm rep TPS` |
| `quality.block_cv` | `diagnostic-only and never substituted or averaged for aggregate CV` |
| `quality.unstable` | `aggregate_cv > 0.05` |
| `execution.bench_max_rounds` | `1` |
| `execution.automatic_retry` | `false` |
| `execution.bench_lock_acquisitions_per_workload` | `1` |
| `execution.settle` | `once-at-workload-schedule-start` |
| `execution.competing_tenant_probe` | `before-each-five-rep-arm-block-fail-closed-workload-abort` |

`invalid_rules[0..15]` は日本語要約へ置換せず、JSON の 16 文字列を同じ順番で引用する。特に exactly-one build、両 arm の事前 verify、毎 block 前の競合検査、aggregate CV、`rounds == 1`、5 positive finite TPS、schedule receipt、片側 commit、中断、trace0、CCBench pin/cleanliness を落とさない。

`rerun.allowed_reasons` も次の token だけを閉じた列挙として写す。

- `build-failure-before-bench`
- `verify-failure-before-bench`
- `competing-tenant-detected-before-bench`
- `scheduler-or-infrastructure-failure-before-bench`

併せて `closed_enumeration=true`、`performance_output_may_not_authorize_rerun=true` を逐語で置く。

## D1296 の本文化

| D1296 の要求 | policy 対応 | policy にない部分の出典・本文化 |
|---|---|---|
| 60 対/workload | `sizing.pilot_pairs_per_workload`、`workloads[*].reps`、`pair_indices` | なし |
| 5 対/ブロック×12 | `sizing.pilot_pair_blocks.pairs_per_block/total`、`block_mean_count` | なし |
| A 先行 6 / B 先行 6 | `variant_first=6` / `baseline_first=6` | driver では A=`variant`、B=`baseline` と解決する [`paper_story_a1_paired.py:1531-1557`](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1777-pilot-prereg/orchestrator/campaign/paper_story_a1_paired.py:1531) |
| 組内順は凍結 seed | `pairing.physical_orders`、`pairing.seed`、各 `schedule_root_seed` | all-identical redraw も省略しない |
| TPS | `quality.aggregate_cv`、throughput 関連 invalid rules | observation field 名 `tps` は D1296 と receipt schema 実装。同 tool:434-456 |
| 物理順 | `pairing.physical_orders`、`pairing.schedule_receipt_schema` | observation の `arm` と時刻順で保存。D1296 |
| ブロック番号 | `sizing.pilot_pair_blocks` | observation field `block`。D1296、sizing tool:441-446 |
| ブロック内位置 | `pairs_per_block=5` | observation field `block_position`。D1296 |
| 時刻 | 対応 field なし | `started_at_ns` / `ended_at_ns`。D1296、receipt keys |
| 対 SD からの sigma | `sizing.sigma_pair` | 60 個の `variant TPS - baseline TPS` の標本 SD に `df=59` の片側上側係数を掛ける |
| block 平均からの実効 sigma | `sizing.sigma_block` | 連続 5 対の差の平均を 12 個作り、その標本 SD に `sqrt(5)` と `df=11` の上側係数を掛ける |
| 大きい方 | `sizing.planned_sigma` | `planned_sigma = max(sigma_pair, sigma_block)` |
| floor | `sizing.floor_fraction` | pilot baseline 60 点の平均を `m0` とし、`B=(3/100)*m0`。sizing tool:499-518, 611-616 |
| 判定式 | policy に分類 operator field はない | D1296 の「既存 sizing」と tool:560-590, 793-803 を引用して固定する |
| 3 条件と成功率 | `sizing.conditions`、`required_success_probability` | 下記の exact success 定義は tool から書く |
| pilot を最終推定へ混ぜない | `final_estimate_eligible=false`、`authority.result_authority` | D1296:41680 を日本語で明記 |

判定式は `df=n-1`、`k=t(1-(1/120)/2, n-1)`、`h=k*s/sqrt(n)`、`L=mean-h`、`U=mean+h`、`B=(3/100)*m0` とする。

- `zero`: `L >= -B` かつ `U <= B` の `bounded-within-floor` が成功。
- `positive-six-percent`（tool 名 `positive-two-floor`）: `L > B` の `resolved-beyond-floor/improvement` が成功。
- `negative-six-percent`（tool 名 `negative-two-floor`）: `U < -B` の `resolved-beyond-floor/regression` が成功。
- それ以外は `unresolved`。
- 各条件の成功率が `4/5` 以上であることを要求する。search 通過後は Clopper–Pearson 片側下限も `4/5` 以上でなければならず、失敗時は次の search-passing candidate へ進む。最初に 3 条件すべてを認証した `n` を採る。

親 brief P1-3 の `resolved-above-floor` / `bounded-below-floor` は数式上それぞれ対応するが、現在の sizing certificate の機械 label ではない。本文では tool の `resolved-beyond-floor` / `bounded-within-floor` を主表記にする。

simulation は bootstrap と書かない。実体は正規標本平均とカイ二乗標本分散の sufficient-statistics Monte Carlo である。root seed は次を逐語で置く。

- preimage: `paper-story-a1-balanced-sizing-root-seed/v1|20260901|paired-mean-block-sigma`
- SHA-256: `e72bc005d156caea2c89085c563c72fa04bbeb4afd98160fca968da9a7f6b3b3`
- child seed preimage: `paper-story-a1-balanced-sizing-seed/v1|root=<root>|phase=<phase>|workload=<workload>|condition=<condition>|n=<n>|trials=<trials>`。certification だけ `|attempt=<attempt>` を追加する。
- generator と verifier は source-separated replay だが、独立統計 oracle とは主張しない。

## D1295 項目 5

置き場は `README.md:61-69` の独立節とし、次の順で隣接させる。

> policy `pairing.estimand`: `arithmetic mean of paired differences under the balanced five-rep schedule`

続けて日本語の規範文を次のまま置く。

> 推定対象は「5-rep 均衡スケジュール下での差」であり、残留効果の無い定常状態の直接効果と同一視しない。

その直後に `pairing.contrast = variant-minus-baseline` を記し、「物理的に先に走った arm から後の arm を引く」のではないことを明確にする。英文は翻訳で置き換えず、日本語限定と併記する。

## 書いてはならないもの

- 本文自身の SHA-256、現行または発効後の policy SHA-256、空の hash 欄。policy から本文への一方向束縛だけにする。
- pilot 未走のため存在しない workload 別 `pair_sd_tps`、`sigma_pair_tps`、`sigma_block_tps`、`planned_sigma_tps`、採用 `n`、`k`、実現成功率。
- 空表、`TBD`、`TODO`、`<反映>`、`<受入結果を反映>`、`<受入全走結果を反映>`。値の欄を作らず、「観測値と採用 n は pilot 後の sizing certificate にだけ記録する」と書く。
- 「必要なら」「状況に応じて」「外れ値なら」「不安定なら再走」など、再走理由や invalid 判定へ裁量を足す文言。
- `invalid_rules` の “exactly”、全 workload abort、fail-closed、物理順一致、片側 commit、CCBench clean 条件を弱める翻訳。
- performance output、CV、pilot の符号・効果量を再走判断へ使えると読める文言。
- pilot 自身に `resolved-*` 等の結果分類を与える文言。分類式は sizing の動作特性評価専用である。
- 旧 v2 の採用値 `72 / 205 / 28`、旧計画 sigma、旧 Monte Carlo seed/trial 数、`static10 - adaptive` という全 workload 共通 contrast。
- 先例 §1 の「2026-08-24 探索走から規模以外を流用」、§2 の計画 sigma・採用 n 表と「到達する動作特性」表、§3 の `variance_plan_breach`、§4 の旧 publish 条件、§6 の還元判断。
- 先例 §5 のうち、arm-grouped の約615秒/40倍、5点 sigma、`rep_notes` 感度分析、最大3回の内部再測定。いずれも pilot policy の配置・invalid rules・`bench_max_rounds=1` と一致しない。

## 限界の節

残す限界は次に限定する。

- 配置は識別可能性を上げるためのもので、時間隔交絡や残留効果が存在しない／消えた証拠ではない。したがって estimand は 5-rep 均衡スケジュール固有である。根拠は D1295:41647-41656 と `pairing.estimand`。
- pilot の観測値は反復数設計の入力に限られ、最終推定、正式結果、promotion に使えない。根拠は `authority`、`final_estimate_eligible`、D1296。
- 動作特性は normal paired-difference sufficient-statistics model と凍結 sigma の下の評価であり、source-separated verifier も独立統計 oracle ではない。根拠は sizing tools。
- source-routed trace0 は単体 artifact だけの証明ではなく、不完全・不整合なら invalid。根拠は `invalid_rules[14]`、`ccbench_acceptance.boundaries`、driver の v3 limitation。
- workload ごとに扱い、横断結論を作らない。根拠は D1296 の「各 workload」、policy の独立した workload plans、driver の v3 limitation。

配置変更で変わった点も同じ節で短く明示する。

- arm 全反復を別時間帯で測る旧 limitation はそのまま移植しない。5-rep block により同番号間隔は D1295 の見積りで約16.8秒、旧配置の約1/41になった。ただしゼロにはならない。
- 旧「便宜的な位置対応 SD」は、role 固定の paired difference 60 個と 5-pair block mean 12 個へ変わり、両 sigma の大きい方を使う。
- 5 点だけの sigma limitation は 60 対/12 block の設計へ変わった。
- CV による内部再測定問題は `bench_max_rounds=1` により消えた。
- `rep_notes` は v3 の `invalid_rules` にないため、旧感度分析を持ち込まない。

## 検査計画

静的に読んだ結果は次のとおり。テストは実行していないため、緑とは報告しない。

| 検査 | README 追加だけで発火するか | 根拠 |
|---|---|---|
| `tools/check_docs.py` placeholder guard | 発火しない | 対象は `output/insights/*.md` の直下だけで、directory 配下の `README.md` は列挙されない [`check_docs.py:2611-2688`](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1777-pilot-prereg/tools/check_docs.py:2611)。新文書は living docs にも入らない。同時に、本文自体は 3 literal を使わない。 |
| 三軸語走査 | 条件付きで発火しうるが、本設計では発火させない | 三軸走査は `check_docs.py` 内ではなく [`test_s8b_repo_scan_invariant.py:27-35`](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1777-pilot-prereg/orchestrator/tests/test_s8b_repo_scan_invariant.py:27) が行う。untracked file も列挙対象。本文の rratio は 5/50/95 だけなので holdout の 80/20 conjunction にはならない。 |
| `test_frozen_artifacts.py` | 発火しない | exact 23-path manifest のみを hash 検査し、新 directory の census はしない [`test_frozen_artifacts.py:41-179`](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1777-pilot-prereg/orchestrator/tests/test_frozen_artifacts.py:41)。 |
| `test_paper_story_a1_paired.py` | README 追加だけなら発火しない | legacy goldens は固定 path のみで、`rglob` も headline preregistration directory だけ [`test_paper_story_a1_paired.py:903-938`](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1777-pilot-prereg/orchestrator/tests/test_paper_story_a1_paired.py:903)。ただし発効時には未凍結正例:1351-1390が必ず赤になるので更新が必要。 |
| `test_paper_story_a1_headline.py` | README 追加だけなら発火しない | non-touch manifest に新 path はない [`test_paper_story_a1_headline.py:1232-1251`](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1777-pilot-prereg/orchestrator/tests/test_paper_story_a1_headline.py:1232)。発効編集を未 commit のまま走らせると paired module/test の dirty status により:1303-1312が赤になるため、全受入は人間の発効 commit 後に行う。 |
| `test_artifact_admission.py` | 発火しない | real tree の diff 検査は `output/campaigns` に限定され、lock census も `campaign.lock` だけ [`test_artifact_admission.py:830-887`](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1777-pilot-prereg/orchestrator/tests/test_artifact_admission.py:830)。 |
| `test_paper_story_a1_balanced_sizing.py` | README 追加では発火しないが、本文照合用に重要 | sigma、grid、seed、分類、replay の実体を固定する。親は受入全走に含め、本文と式を静的照合する。 |

親は docs wave では `check_docs.py` と指定テスト群を既存の runner 経由で実測する。発効 wave では focused paired/sizing testsを先に行い、commit 後に headline を含む受入全走を行う。

## 発効手順

親 brief §6 の 4 箇所は、採用 README bytes を変更しない前提なら実行到達性を閉じるのに十分である。追加の runtime pin や job-script 編集は不要。人間は次の順で 1 commit にまとめる。

1. 採用する README bytes を最終確認する。人間が 1 byte でも直す場合、その変更も発効 commit に含める。
2. repo root で README の hash を再計算する。

   ```bash
   sha256sum -- output/insights/2026-09-01_paper-story-a1-balanced5-pilot-preregistration/README.md
   ```

3. [`paper_story_a1_paired.py:175-176`](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1777-pilot-prereg/orchestrator/campaign/paper_story_a1_paired.py:175) の `V3_PILOT_PREREGISTRATION_RELATIVE_PATH` と `_SHA256` に exact path と手順 2 の hash を入れる。
4. [`paper_story_a1_paired.v3-pilot.json:87-90`](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1777-pilot-prereg/orchestrator/campaign/paper_story_a1_paired.v3-pilot.json:87) の `preregistration.path/sha256` に同じ値を入れる。
5. 変更後の policy JSON bytes を `sha256sum -- orchestrator/campaign/paper_story_a1_paired.v3-pilot.json` で計算し、[`paper_story_a1_paired.py:168-170`](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1777-pilot-prereg/orchestrator/campaign/paper_story_a1_paired.py:168) の `V3_PILOT_POLICY_SHA256` を更新する。
6. [`test_paper_story_a1_paired.py:1351-1390`](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1777-pilot-prereg/orchestrator/tests/test_paper_story_a1_paired.py:1351) を、exact path/hash、非 `None` の module pins、`_require_policy_ready_for_execution(policy)` が成功する正例へ更新する。
7. focused tests を確認後、この 4 編集箇所（README を直した場合は README も）を 1 commit にする。commit 後に full acceptance、`check_codex_agents.py`、`check_docs.py`、provenance 監査を実測する。push は人間が行う。

## 未解決の論点

重大な未凍結値が 1 件ある。

`--search-trials` と `--certification-trials` は policy に field がなく、D1296 にも数値がなく、両 sizing CLI に default もない。一方、選ばれる `n` と Clopper–Pearson 認証はこの 2 値に依存する。テストの `32 / 128` は小型 fixture、先例の `20,000` は旧 v2 であり、どちらも本 study へ流用できない。

したがって親は本文完成前に、この 2 整数を人間裁定で凍結し、policy と人間可読本文のどちらを正本にするかも決める必要がある。未裁定のまま空欄・仮値・「後で決める」を置いて発効してはならない。

## 総括

- 親は上記 8 節で README を起草し、policy literals と D1295/D1296 以外の値を足さない。
- 先に search/certification trial 数を人間裁定へ返し、確定前は本文を発効可能扱いしない。
- 起草後は placeholder、三軸 conjunction、指定テスト群を実測する。
- 発効は人間が README hash → policy binding → policy hash →正例更新の順に 1 commit で行う。