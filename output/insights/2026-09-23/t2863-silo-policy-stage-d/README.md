# silo-function-policy 軸の段階 D — 型付き有限 IR の機械偵察 (2026-09-23、[T-2863])

- 位置づけ: 軸オンボーディング (`docs/axis-onboarding.md` §3-D) の段階 D の記録。**報告カテゴリは「偵察 (preliminary)」** で、事前登録 (`docs/phase3-main-experiment.md` ほか) のどの構成でもない (D46 決定 1)。設計の正本は `output/insights/2026-09-21/silo-function-synthesis-space/README.md` (以下「設計」) §5、前段は `output/insights/2026-09-22/t2857-silo-policy-stage-c/README.md` と D2226・D2214、本段の設計判断は同じ wave の decisions fragment。可変状態の正本 (worklog 末尾・`docs/phase3.md`) にはしない。
- wave: branch `dev-wave/t2863-silo-policy-stage-d`、起点 local main `cadaf3805` (開始 gate rc=0)。wave 中に local main を 2 回取り込んだ (`fb12a492b` を早送りで、`b14d8b01c` を merge `4eab7c65c` で)。submodule pin `e9e477ca` (不変)。
- 逐語 (`verbatim/`): 依頼 `request.md`、段 1 brief `brief.md`、段 2 plan `s2-plan.md`、段 3 相談 `s3-consult-{A,B}.md`、段 4 裁定 `s4-ruling.md` (§6 がユーザー指示による 8 job 分割の追補)、実装子の報告 `s5-author-{a,b}.md`、段 6 のレビュー `s6-review-{A,B}.md`・裁定 `s6-ruling-{1,2}.md`・fix 子の報告 `s6-fix-{1,2}.md`・焦点再レビュー `s6-focus-1.md`・前方 merge の合成子 `s6-merge.md`、login 正式検査の結果 `ir-check-1.json`、変異 matrix `mutation/`。行末空白の可逆正規化は `verbatim/NORMALIZATION.md`。prompt と codex の受領証は wave の job dir (repo 外)。

## 0. 要約

1. **二値 = true (床超の地形あり)。** 後段 (段階 E の coder / planner の入力) へ渡してよいのはこの二値と射程文だけで、正本は `output/env/pegasus/calibration/silo_function_policy_recon/projection.json`。
2. **二値の射程 (段 4 裁定 A5 の固定文言):** 「固定 16 点のテンプレート部分空間で、両 verify certified・非 high-abort の点が、同 job の abort0 に対して 5 rep 中央値で 3% 超を示し、それが別 job の再測でも再現したか」。
   - 「あり」は、既知最良 (`B0-L-W0`) 超え・統計的な優位・LLM の必要性を意味しない。
   - 比較の基準 abort0 (待機 0・lock 競合で即 abort) は write-heavy で abort 率 0.78 の thrashing 点であり、**待機を入れる方策ならほぼ何でも 3% 線を越える**。結果を見る前に固定した問いへの答えとして正しいが、問い自体が易しかったことを限定として残す (§4)。
3. 16 点すべてが legacy と write-heavy 性能構成の両 verify で certified (anomaly 0)、high-abort 除外 0 件。同 job の abort0 に対する 5 rep 中央値の比は 1.34〜1.78。ID 順の先頭 4 点を別 job で再測し、4 点とも 1.53〜1.62 で再現した。
4. 計算は合計 約 1.6 node 時間 (初走 8 job + 重複 1 job + 再測 4 job + 焦点走、§3.4)。ユーザー承認の上限 4.0 node 時間の内側。ユーザー指示「計算ジョブを分割して投げる」に従い初走を 8 job に割り、各 job 7〜9 分で終えた。

## 1. 依頼と裁定

- 依頼 (ユーザー直接起動の `/dev-wave`、逐語 = `verbatim/request.md`): 設計 §5 の型付き有限 IR の生成器・列挙・偵察 driver を Codex author で書き、段階 C の診断経路を再利用する。計算は投入前に job Elapse の実測単価で見積もってユーザー確認。偵察結果は二値だけを後段へ渡し、継続 / 見直しは人間判断。正しさゲートは不変。本題の実装だけ。
- 計算の確認: 段 4 で用途別の見積り (シナリオ 約 1.7〜3.1、walltime 上限で 4.0 node 時間) を示し、「上限 4.0 h で承認」を得た。
- 作業中のユーザー指示「一瞬で終わらせてね。計算ジョブを分割して投げることで」→ 段 4 裁定 §6 で初走を 2 job から 8 job に、再測を候補ごとの別 job に変えた。
- 段 3 相談は 2 本とも NO-GO (must-fix: job 割付が因子 M と完全交絡 A1/B5、集計の入力照合の欠如 A2、二値の射程を固定 16 点へ限定 B1、見積りを用途別総額に B6)。全件を段 4 で採用した (`verbatim/s4-ruling.md`)。

## 2. 実装 (単位と commit)

| 単位 | commit | 内容 |
|---|---|---|
| A | `b25530b85` | `orchestrator/campaign/silo_policy_ir.py` (型付き式木・`validate_ir`・決定的描画・16 点の列挙・login 正式検査 CLI) と test |
| B | `ce4985ab2` | `orchestrator/campaign/silo_policy_recon.py` (`run` = 初走 / 再測の 1 job、`aggregate` = 集計と二値の投影)、`silo_policy_coverage.py` の `_source(body=...)`・`_build_variant(stock_backoff=...)`、`job_of` の 8 組割付、行番号 pin の追随 |
| 段 6 fix 1 | `e867a3669` | 集計で固定 workload と対照 (abort0 本文・軸 OFF の genome) を照合、不採用の投入 script の test を削除 |
| 段 6 fix 2 | `c90f05b4b` | 集計の job 識別を (hostname, started_at) に (§3.5) |
| main 取り込み | `4eab7c65c` | 両親と異なる 1 file は 3 版を Codex に合成させ、自動 merge の blob と sha256 一致を確認 |

- 実装面の全ハンクは Codex author (単位 A = gpt-6-astra、単位 B 以降 = gpt-6-sol。wave 中に local main で DW-O01 の model が変わった。reasoning はいずれも medium) が子 worktree で書き、親は所有 path の差分だけを統合した。
- 単位 B の子が書いた job body・投入 script (`tools/pegasus/` の 2 本) は、Pegasus の投入許可台帳 (`tools/pegasus/admission_registry.json`) に未登録で hook が実行を拒否するため取り込まず、既存の許可済み経路 `tools/pegasus/dispatch_compute.py --task generic` で driver を投げた。dispatch は checkout ごとに同時 1 本なので、計測用の worktree を 8 本 (`.claude/worktrees/t2863-recon-0..7`、detached) 作った。

### 2.1 IR と列挙 (設計 §5 の具体化)

- IR = frozen dataclass の型付き式木 (定数・abort 要因・lock 試行番号・状態参照・比較・条件式・min / max・飽和加減算・有界 shift) と hook ごとの同時代入。深さ (葉 = 1) ≤ 4、全 hook の node 出現数の合計 ≤ 64、状態 ≤ 4 field、数値二項演算は同型同士、`rand` なし。`validate_ir` を描画の先頭で必ず呼ぶ。
- 描画は hook の入口で参照する状態を局所へ写してから計算し、最後に代入する (段 3 相談 A3、入替え `f0'=f1, f1'=f0` を実 compile・実行で試験)。飽和加算は `a > MAX - b ? MAX : a + b`、飽和減算は `a < b ? 0 : a - b` (子式は先に局所へ下ろす)。出力は policy-C++ v1 の部分集合で、既存の 4 段検査 (`prepare_policy`) をそのまま通す。
- 列挙 = 4 因子 × 2 水準の完全要因 16 点 (ID は bit 列 LSRM)。L = lock 競合で即 abort / attempt < 4 の間 retry (lock 待機 0)、S = 静的待機 / 連続 abort で待機を飽和加算 (上限 1000 µs) し commit で 0 に戻す、R = 全要因で待機 / lock_conflict だけ待機、M = 待機の単位 5 / 10 µs。定数は段階 C の手書き方策の値から結果を見る前に固定した。
- **この 16 点は「全 IR の列挙」ではなく、固定テンプレートの部分空間の全列挙である。** U64・減算・shift・lock 待機・状態を lock hook で更新する方策などは含まない。
- login 正式検査 (`python3 -m orchestrator.campaign.silo_policy_ir check`、単位 A の子が 1 回実走、`verbatim/ir-check-1.json`): 16 点 + abort0 の 17 方策すべてが構文検査・単独 TU compile を通り、UBSan harness は 20/20 通過 (17 方策 + UB 負対照 3 種、各方策 1,904 呼出し、GCC 12.3.0)。

## 3. 実測

### 3.1 動作点と正しさゲート

- Pegasus (env_tag `pegasus`)、1 job = 1 ノード、CCBench PIN `e9e477ca`。
- 各点: 4 段検査 → TRACE=1 build → legacy verify (200 records / 4 threads / RMW / 1 秒) と性能構成 verify (1M records / 48 threads / skew 0.9 / rratio 5 / rmw false / max_ope 10 / 3 秒、numactl interleave) → **両方が certified の点だけ** TRACE=0 build → owner TU の trace0 確認 (compile command に `IZANAGI_` の define なし、前処理に probe・break の断片なし) → bench 5 回 (性能構成と同じ flags、numactl interleave)。結果 JSON の `workload.numa` は性能構成 verify と bench の条件で、legacy verify は numactl を使わない (焦点再レビュー F1、各走の実 command は `command` に残る)。
- trace0 の確認は owner TU の範囲で、trace 全体の除去の証明ではない。
- 診断 build は NON_ADMISSIBLE で、certified 候補とは称さない (D2226 項 5)。verify の certified は各有限履歴についての判定である。

### 3.2 初走 (8 job 同時投入)

commit `ce4985ab2` の `run`。結果 = `output/env/pegasus/calibration/silo_function_policy_recon/initial-{0..6,7b}.json`。表の値は 5 rep の中央値 (throughput は千 txn/s)。比は同じ job の abort0 に対する中央値の比。

| job | 点 (LSRM) | throughput | abort 率 | 比 | 同 job の abort0 |
|---|---|---:|---:|---:|---:|
| 0 | 0000 / 1111 | 3,932 / 4,238 | 0.500 / 0.290 | 1.584 / 1.708 | 2,482 (0.778) |
| 1 | 0001 / 1110 | 3,917 / 4,257 | 0.386 / 0.341 | 1.627 / 1.768 | 2,407 (0.779) |
| 2 | 0010 / 1101 | 3,843 / 3,657 | 0.552 / 0.196 | 1.536 / 1.462 | 2,501 (0.780) |
| 3 | 0011 / 1100 | 3,964 / 3,953 | 0.443 / 0.239 | 1.610 / 1.606 | 2,462 (0.782) |
| 4 | 0100 / 1011 | 3,634 / 4,063 | 0.287 / 0.426 | 1.467 / 1.640 | 2,478 (0.775) |
| 5 | 0101 / 1010 | 3,346 / 3,402 | 0.239 / 0.543 | 1.340 / 1.362 | 2,497 (0.780) |
| 6 | 0110 / 1001 | 3,839 / 4,218 | 0.375 / 0.348 | 1.616 / 1.775 | 2,376 (0.783) |
| 7 | 0111 / 1000 | 3,756 / 3,905 | 0.315 / 0.467 | 1.544 / 1.605 | 2,433 (0.785) |

- 軸 OFF の参考値 (二値には使わない): stock (`BACK_OFF=1`、Cicada 適応 backoff、job 0) 1,355 (abort 率 0.122)、`B0-L-W0` (`BACK_OFF=0`、job 1) 2,423 (0.790)。abort0 (軸 ON、待機 0・即 abort) は `B0-L-W0` とほぼ同じで (同 job 2,407)、骨格の常駐コストは 1 走の範囲で見えない。
- abort0 の abort 率は全 job で 0.775〜0.785 なので、high-abort 除外 (候補が基準の 2 倍超) は構造的に働かない (段 3 相談 A4 の予告どおり)。除外 0 件はこのためで、絶対的な高 abort や公平性を除いたわけではない。
- 8 job の abort0 の中央値は 2,376〜2,501 (幅 5.1%)。job 間の差は同 job の基準で割ることで吸収する設計である。

### 3.3 再測 (候補ごとに別 job)

初走の再測候補は 16 点すべて (比 > 1.03)。規則どおり ID 順の先頭 4 点を 4 job で同時に投げた (abort0 を先頭、候補を後。初走とは順序を反転)。

| 点 | 初走の比 | 再測の比 | 再測 job の結果 file |
|---|---:|---:|---|
| 0000 | 1.584 | 1.619 | `remeasure-0000.json` |
| 0001 | 1.627 | 1.586 | `remeasure-0001.json` |
| 0010 | 1.536 | 1.532 | `remeasure-0010.json` |
| 0011 | 1.610 | 1.610 | `remeasure-0011.json` |

- 最初に完了した再測 (0001、別ノード bnode060) で「あり」が確定したので、次の組 (0100 以降) は投げていない。先に投げた 3 本は走り切らせて記録した。
- 集計 = `aggregate.json` (詳細、login で実行)、投影 = `projection.json` (二値・射程文・除外件数だけ)。集計は初走 8 job の IR 点の和集合 = 16 点、本文 sha256 = 現在の描画、固定 workload、abort0 本文と軸 OFF の genome、job 識別 (hostname, started_at) の別を照合し、中央値と比を生の rep から再計算する。

### 3.4 計算ノードの使用 (job Elapse)

| 用途 | request | Elapse |
|---|---|---|
| 初走 job 0〜6 | 20189・20187・20182・20184・20186・20183・20188.nqsv | 506・564・430・434・435・428・436 秒 |
| 初走 job 7 (投げ直し、採用) | 20366.nqsv | 428 秒 |
| 初走 job 7 (元 request、不採用・記録のみ、§3.5) | 20185.nqsv | 430 秒 |
| 再測 4 本 (0001・0000・0010・0011) | 20367・20369・20368・20370.nqsv | 304・305・305・306 秒 |
| 焦点走 4 回 | 20172・20181・20218・20365.nqsv | 10・139・93・11 秒 |

- 計測 13 job の合計 5,311 秒 + 焦点走 253 秒 + 変異 matrix の runner 時間 2,029 秒 (probe 2 本と final 6 本、待ち行列込みの上限値) = 7,593 秒 ≈ 2.11 node 時間 (上限値)。受入全走は本記録の commit の後に行い、結果は land の受領証に残る。
- gen_S の同時実行は 3〜4 本で頭打ちになり、8 本の初走は 2 波で走った (投入 14:08 JST、最後の完了 14:5x JST)。

### 3.5 実行上の erratum

- 初走 job 7 の元 request (20185.nqsv) が 14:08 から 20 分以上 Pre-running のまま起動しなかった。qdel はせず (F47 の投入停止ラッチ)、同じ job 7 を別の計測木から投げ直し (20366.nqsv)、**先に完了した方を採用**した (選択は完了順で値に依存しない)。元 request も後で完了し、値 (0111 3,815 / 1000 3,944 / abort0 2,439) は記録として `initial-7.json` に残した。
- `dispatch_compute --task generic` は子の環境変数を消す (env_mode=clean) ため、結果 JSON の `pbs_jobid` は null。集計の job 識別は (hostname, started_at) にした (段 6 fix 2)。request ID は本節の表に親が dispatch log から写した。
- 段 4 裁定の変異 M-BODY-GATE は登録から外した (本文引数は同じ `prepare_policy` 呼出しへ渡るだけで、段階 C の M-SMOKE-SKIP が同じ 4 段検査の経路を押さえている)。

## 4. 限定と残存リスク

- **問いの易しさ。** 基準 abort0 は thrashing 点なので、3% 線は「待機を入れる方策が即 abort を上回るか」をほぼ自明に問うた。「IR 空間に、既知最良 (静的・適応 backoff の調整済み値) を超える地形があるか」は本偵察の問いではなく、答えていない。軸 OFF の `B0-L-W0` と stock は同 job の参考値で、正式比較ではない。
- 部分空間の結果と全空間の生死を区別する (手順書 §4 第 3 列)。「なし」でなかったことは全 IR の地形の豊かさを示さない。
- 床 3% は `orchestrator/campaign/p2_2.py` の過去の between-run 指標 (旧 linux-baremetal・旧 PIN・既存方策) の暫定流用で、Pegasus・新骨格で較正していない。16 点から選んだ最大値の有意水準でもない (多重選択は補正していない)。
- verify と perf で同じ分岐を踏んだとは言えない (設計 §3.1)。公平性 (worker 間の偏り) は観測していない (D41 型 15)。偵察の候補は機械生成で auditor 段を省いた (D46 決定 3)。
- **firewall (手順書 §3-D):** 本 insight と `aggregate.json` には点 ID・因子・比・順位が載る。段階 E / F の coder・planner の入力 (leakproof_context・planner direction・whiteboard) へ流してよいのは `projection.json` の二値と射程文だけ。本 insight を読んだ事実は、段階 E / F の campaign provenance に情報源として記録する義務を残す (D46 残存リスク (a) のループ版)。機械的な firewall は実装していない (段階 E の scope)。

## 5. 段 6 の経緯

| 巡 | 入力 | 直したもの | 裁定 |
|---|---|---|---|
| 1 | レビュー A (NO-GO、must-fix 3)・B (NO-GO、must-fix 1)、焦点走の赤 1 件 | 集計の固定 workload と対照の照合 (RA1・RA2)、不採用の投入 script の test の削除 (RA3/RB1)。RB2・RB3 (build / verify の省略) と RB4 は計測済みの run を変えるので不採用 | `verbatim/s6-ruling-1.md` |
| 2 | 親の実測 (初走結果の `pbs_jobid` が null) | 集計の job 識別 (G1) | `verbatim/s6-ruling-2.md` |
| 焦点再レビュー | fix 1 後 (NO-GO) | F1 (numa の記録) は nit で本 insight に明記、F2 (protocol 照合) は仮想リスクで不採用、RB2・RB3 の「時間切れで欠測」は実測 (1 job 428〜564 秒、walltime 1,800 秒) で refuted | `verbatim/s6-ruling-2.md` |

## 6. 変異 matrix と記録前の検査

- 変異 (段 4・段 6 で事前登録、`verbatim/mutation/`): 計測を終えた計測木 (detached、clean) に `tools/mutation_harness.py --runner-mode dispatch --detached` を直接当てた。runner = `run_tests.py --force-dispatch orchestrator/tests/test_silo_policy_ir.py orchestrator/tests/test_silo_policy_recon.py -q -rf`。
  - probe (commit `c90f05b4b`、IR 系 8 件と集計系 10 件の 2 本、全件 SURVIVED 期待): 基準走は PASSED、18 件すべてで赤 node を観測した。期待 node はこの観測の完全集合 (`observed-nodes.json`)。spec 生成の道具は wave の job dir の `make_mutation_specs.py` (repo 外、各 anchor が対象 file に 1 回だけ現れることを検査)。
  - **final (commit `4eab7c65c`、6 本に分けて並列): 18 / 18 KILLED、期待 node と完全一致 (MISMATCH 0・SURVIVED 0)、基準走は 6 本とも PASSED。**

| ID | 壊したもの | 落ちた node (final、完全一致) |
|---|---|---|
| m-snapshot | 描画の入口状態の写し | 入替え・出力と reset の実行 test 2 |
| m-satadd / m-satsub | 飽和加算 / 減算の guard | 飽和境界の実行 test (u32・u64) 2 |
| m-depth / m-nodes / m-fields | 深さ 4・node 64・field 4 の上限 | 各境界 test 1 |
| m-shift | shift 量の幅未満 | shift 境界 test 4 |
| m-partition | 8 組の job 割付 | 因子均衡 test 1 |
| m-cert | bench 前の certified 分岐 | driver の verify・trace0・5 rep の test 1 |
| m-reps | bench 5 回 | 同上 1 |
| m-floor | 比 > 1.03 | 集計境界 test 4 |
| m-highabort | high-abort 除外 | 除外 test 1 |
| m-null | 未完了 → null | null 規則の test 2 |
| m-agg-sha / m-agg-workload / m-agg-control / m-agg-jobid | 集計の本文 sha256・固定 workload・対照・job 識別の照合 | 各照合 test 1〜2 |
| m-projection | 投影に点 ID を含める | 投影の内容 test 1 |

- 事前登録からの変更 (erratum): M-BODY-GATE を外した (§3.5)。M-AGG-WORKLOAD・M-AGG-CONTROL (段 6 裁定 1 巡目) と M-AGG-JOBID (2 巡目) は fix 前に追加登録した。
- 焦点走: 単位 A 後 71 passed (20172.nqsv)、単位 B 後 1 failed / 937 passed / 5 skipped (20181.nqsv、赤 = 不採用 script の test、fix 1 で削除)、fix 1 後 193 passed / 2 skipped (20218.nqsv)、fix 2 後 19 passed (20365.nqsv)。
- provenance の全史監査 (merge `4eab7c65c` の後): 12,716 件、新規違反なし。
- 三軸語の走査器 (`python3 -m orchestrator.campaign.s8b_holdout_freeze search`) は記録 commit の前に rc=1。hit はすべて main に既存の file で、本 wave の追加 file の hit は 0 件 (走査 log は wave の job dir の `three-axis-search.log`)。記録 commit の後の再走は worklog に書く。
