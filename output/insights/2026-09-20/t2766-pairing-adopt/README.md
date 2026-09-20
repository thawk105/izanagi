# [T-2766] 受入 shard 内 pairing (collection 順 49〜96 位を最小 cost の 48 unit に) を既定 on にして main へ入れる採用 wave — 待ち手経由の実受入で A (採用前 main) / B (採用後) の隣接対 3 組を再確認し、3 対とも B が短く (最遅 shard の JUnit wall の対差 145.8 / 86.3 / 57.3 秒、対率 29.1 / 19.6 / 12.6 %、対差の中央値 86.3 秒、対率の中央値 19.6 %、条件別中央値差 100.8 秒)、事前登録の判定は (i) 方向一致・閾値以上 → land。効果は前 wave (101.7〜144.3 秒) より小さく対ごとに縮み、全対で main が動いた (対 3 は docs fold だけ)。property 4 種は junit.xml を受入 1 走あたり約 +13 MB (3.4 倍) 増やす

一次資料 (wave `dev-wave-t2766-pairing-adopt`、着手時 local main `947fd160a`、実装 commit X2 `2404642c3f3d89eeb8068f0d7cdcb84016a239b7` = X1 `715bf37b7` (main + cherry-pick `0eabe67ba`) + 既定 on の差分、測定 2026-09-20 14:47〜18:11 JST)。段 1 brief / 段 4 裁定 (段 6 追補を含む) は同 dir の `s1-brief.md` / `s4-ruling.md`、author・レビュー 2 本・prompt・焦点走・門番 log の逐語は `verbatim/`、集計は `analysis/`、走ごとの記録は `runs/` (junit / report.json の写しは job dir、sha256 は各 `SHA256SUMS`)。**land 用の受入証跡ではない** (受入受領証は段 9 の land が持つ最終走のもの)。

## 1. 依頼・不変条件・結論

依頼 (D2172 項 1、択 (a)、2026-09-20 ユーザー裁定「推奨通りで」、command 引数): opt-in 実装 (branch `impl-t2766-pairing-optin`、`0eabe67ba`) を Codex author が既定 on にして main へ入れる。待ち手経由の実受入 3 対 (A = 採用前 main / B = 採用後) で効果を再確認し、効果が消えていれば land しない。tip・条件差を記録し「毎受入 100 秒」と一般化しない。A 側 witness は相乗り可で採用を遅らせない。受理集合は不変 (順序だけ)。gate・台帳・一般化の追加は scope 外。

不変条件を守った: 受理集合 (selected / hold / group / unit 境界・marker・既存 property・identity) は変えていない (レビュー B の静的結論、G12 の保全 test、変異 M3' / M5 の帰属、§4)。pairing は env を読まず既定で発火し (B 3 走 × 3 shard の witness、§6)、unit < 96 は無変更・property 無し、cardinality 不成立は `UsageError` (fail-closed) のまま。opt-out・新 gate・台帳は足していない。判定規則は結果を見る前に固定した (`s1-brief.md` §事前登録 + `s4-ruling.md` 追補)。測定中は自分の他 job (変異・焦点走) を走らせていない。

結論 (数値は §6、判定規則は事前登録どおり):

1. **有効 3 対とも B が短い。** 最遅 shard (6 走とも shard-0) の JUnit wall W_max の対差 ΔW = W_max(A) − W_max(B) は 145.8 秒 (対 1、A→B) / 86.3 秒 (対 2、B→A) / 57.3 秒 (対 3、A→B)、対率 r = 29.1 % / 19.6 % / 12.6 % (各対とも |r| ≥ 10 %)。対差の中央値 86.3 秒、対率の中央値 19.6 %、条件別中央値差 med W_max(A) 455.9 − med W_max(B) 355.1 = 100.8 秒。事前登録の判定 = **(i) 方向一致・閾値以上 → land**。3/3 一致は有意差判定ではない。
2. **効果は前 wave より小さく、対ごとに縮んだ。** 前 wave (直接投入、同一 tip) は 101.7 / 112.9 / 144.3 秒 (24.2 %)。本 wave は 145.8 → 86.3 → 57.3 秒で、対 3 は閾値 10 % に近い 12.6 %。対 3 の B (06-B) は最長 singleton unit `[ccbench-current]` e2e が 266 秒 (02-B / 03-B は 218 / 223 秒) と遅く、W_max 398.6 を押し上げている。**「毎受入 100 秒」とは一般化しない。** この夜の regime (A の W_max 440〜501) での 57〜146 秒の観測である。
3. **全対で main が動いた (待ち手の post-claim merge)。** 対 1 は main 側に `s8b_holdout_admission.py` +158 / その test +615 行、対 2 は 31 file (T-2800 の test 13 本削除、verifier、fig11 plotting 等) が入り、対 3 は docs fold だけ (実装面 0)。A / B は各走の tested_main に対する採用前 / 採用後で、B の tip はいずれも tested_main + 採用差分 2 file (+319 −7) だけ、A の tip はいずれも tested_main と tree 一致 (§6 tip 検証)。対 2 の main 側の test 削除は A (後走) を有利にする方向の条件差で、それでも B が 86 秒短い。
4. **効果は shard-0 だけに出る (前 wave と同じ)。** shard-1 の W は A 276.5 / 247.1 / 242.0 vs B 265.7 / 245.0 / 245.6、shard-2 は A 214.5 / 165.6 / 165.3 vs B 249.5 / 203.9 / 172.2 (shard-2 は B が長いが対内で 3〜35 秒、collection の差込み)。shard-0 の残差 F = W − O は 70.5〜77.3 秒 (warm 受入の固定費と一致)。差は最忙 worker の占有 O に入る: A 428.6 / 369.5 / 384.5 秒 vs B 277.8 / 283.1 / 327.3 秒。
5. **B の発火と実配布 (witness):** B 3 走 × 3 shard の全 9 shard で、junit property の被覆 100 % (shard-0 で 4061 / 4061 / 4116 testcase)、rank 48〜95 の item 集合 = partner 集合、head の (cardinality, cost) 多重集合と partner の cost 多重集合が `selected` + 台帳からの独立再計算と一致、worker 別 item 列の復元成立 (`analysis/analysis.json` の各 shard `witness.checks` 4 項目 true)。shard-0 の partner 48 unit の台帳 cost は 0.0〜0.001 (0.0 が 29 個)。最長 singleton unit `[ccbench-current]` e2e (台帳 240、実測 218 / 223 / 266 秒) は 3 走とも gw5 が走らせ、その 2 個目は `test_codex_reasoning_ab.py::test_forbidden_commits_are_unreachable_in_both_cases` (partner、cost 0.0)。台帳 cost 最大の group `real-repo` (550、実測 11〜14 秒) を持つ gw0 の 2 個目は partner でない (初期 unit が複数 item の worker は最初の `_reschedule` で飛ばされる既知の反例、前 wave §6)。A 3 走は property 0 件。
6. **property の費用 (P1):** junit.xml は A が shard-0 0.70 MB / shard-1 1.76〜1.85 MB / shard-2 1.58〜1.68 MB、B が 2.37〜2.40 / 5.82〜6.46 / 6.10〜6.65 MB。**受入 1 走あたり約 +13 MB (3.4 倍)** で、前 wave §7 の「数百 KB / shard」より大きい。時間費用は本 wave で分離していない (F は A/B で同程度)。session dir (`.izanagi-acceptance-shards/`) の増分として残る。
7. **順序依存の赤は観測しなかった。** 6 走とも child-green (failed / error 0)。競走型の再試行 2 回 (03-B の claim-self-unverified = 02-B 成功後に B wave の lease が保持されたままだった launcher 側の欠陥、04-A の postcheck = merge 後に main が動いた) は子が走る前の停止で、走表に含めない (`aborts/`)。
8. **実装は本 wave で main に入れる (land)。** 撤去は並べ替え (`_pair_initial_distribution_units` の呼び出し 1 行と property 付与) の削除だけで戻る。

## 2. 実装 (X2 `2404642c3`、Codex author gpt-6-astra / medium、X1 からの差分 4 file +44 −102、main に対する正味差分 2 file +319 −7)

| 面 | 変更 |
|---|---|
| `orchestrator/tests/conftest.py` | env / token 定数と「measurement opt-in」comment を削除 (`_ACCEPTANCE_PAIRING_PROPERTY_PREFIX` / `_ACCEPTANCE_PAIRING_HEAD_UNITS` は残す)。`_acceptance_pairing_opted_in` を削除。`_reorder_acceptance_items_by_duration(items, durations, workerid="")` は cost 順の `ordered_units` に無条件で `_pair_initial_distribution_units` を適用。hook は分岐を畳み常に `workerid=getattr(config, "workerinput", {}).get("workerid", "")` を渡す。`_pair_initial_distribution_units` 本体 (realized sort、head 48、partner `(cost, pos)` 昇順 48、rest、検算、rank / partner 付与) と property 付与は不変 |
| `tools/pegasus/dispatch_compute.py` | allowlist の `IZANAGI_ACCEPTANCE_PAIRING_V1` と comment を削除 → main と同一 |
| `orchestrator/tests/test_pegasus_dispatch_compute.py` | token 伝播 test を削除、exact pin から key を外す → main と同一 |
| `orchestrator/tests/test_acceptance_schedule_order.py` | G6 / G10 の tracer を `workerid=""` 付き署名に。G8 は `_pair_initial_distribution_units` を恒等に差し替えて cost 順の不変条件 (unknown = 96 位 known の直後、空台帳は key 計算なし・置換 0) を保つ (docstring に pairing 非検査を明記、pairing は G12)。G12: `_PAIRING_ENV` / `_PAIRING_TOKEN` と autouse fixture を削除、正例は env 無しで発火 (対照 arm だけ恒等差し替え)、off 負例 → **既定 on の負例** `test_g12_legacy_env_cannot_disable_pairing_or_change_item_state` (旧 env に `t2766-min-cost-partners` / `off` / `0` / `""` を設定しても collection 列 = literal `_PAIRING_B_UNITS`、identity・selected・marker・既存 property 不変、property 4 種付与)、invalid token 負例は削除、hold / selected / real-repo suffix 保全は既定 1 本に。cardinality 負例・短 queue・worker 数非依存・junit 到達・配布反例は不変 |

親の焦点走 (計算ノード job 12604、11 file = schedule_order / dispatch_compute / hold_inventory / run_tests_shards / real_repo_serialization / run_tests_preflight / fold_gate_nodes_contract / campaign_import_invariant / growth_test_holds_contract / flaky_test_holds_contract / pytest_collection_config): **1210 passed / 7 skipped / 0 failed** (`verbatim/focus1-summary.txt`)。author 自身は pytest を実走できなかった (login の pytest は hook が拒否、dispatch は `qstat -Q` preflight rc=1 で rc=16、`verbatim/s5-author.md`)。

## 3. 段 6 レビュー 2 本 (read-only、gpt-6-astra) と裁定

レビュー A (過剰・削除レンズ): must-fix 2 / should 4 / refuted 5。レビュー B (正しさ・整合レンズ): must-fix 1 / should 2 / refuted 7、M1〜M5 の帰属は静的に成立、M3' の kill 予測 10 node (§4 の実測と完全一致)、受理集合不変の結論。**本番 patch への must-fix は両レビューとも無し。** must-fix は集計器の入力契約 (段 4 の略記が author prompt §4 の契約と食い違っていた — 親の生成器 `write_run_json.py` とは一致しており、前 wave の A session を流用した接続確認で有効走・W_max 454.716 を再現) と、bytecode env の除外条件が事前登録に無かった件 (launcher の env 契約として結果を見る前に追加)。should は A/B の定義 (各走の tested_main に対する採用前 / 採用後、`main_moved` を記録)、門番観測の記録 (投入時・完了時の leader / load と `verbatim/series.log`)、測定量の限定 (W_max = 最遅 shard の JUnit testsuite time、受入総経過時間ではない)、P1 の費用限定 (junit byte 数を記録 → §1 結論 6)、cardinality 検算の nodeid 一意性という境界 (§7)。裁定表は `s4-ruling.md` 追補、逐語は `verbatim/s6-review{A,B}.md`。

## 4. 変異 matrix (DW-M01、独立 clone `mutation-source` (D1009)、commit X2、runner = `python3 tools/run_tests.py --force-dispatch orchestrator/tests/test_acceptance_schedule_order.py -q -rf`、計算ノード)

probe 走 (全件 SURVIVED 期待で観測 node を集める、spec sha256 `d8aee1e7…`、`mutation-spec-probe.json` / `mutation-expected-nodes.json`) → final 走 (期待 node 登録、spec sha256 `c69205b4…`、`mutation-spec-final.json` / `mutation-final-results.json` / wrapper receipt / attempts)。**baseline PASSED (92 passed)、5/5 KILLED、期待 node 完全一致 (MISMATCH 0)。**

| # | 変異 (1 理由) | 位置 | kill した node (完全集合、`test_acceptance_schedule_order.py::`) | 帰属 |
|---|---|---|---|---|
| M1 | partner 選択の sort key を昇順 → 降順 | `_pair_initial_distribution_units` の `entry[1]["cost"] … unknown_cost` | 9: G12 正例・legacy env 4 値・worker 数非依存・junit 到達・配布反例・cardinality 負例 | 固定 partner 列の不一致 (cardinality 負例は partner が 2 item 側に移り検算が通るため) |
| M2 | head 幅 48 → 47 | 同関数 `width = _ACCEPTANCE_PAIRING_HEAD_UNITS` | 8: 正例・legacy env 4 値・worker 数非依存・junit 到達・配布反例 | head の完全一致と partner 境界 |
| M3' | pairing 呼び出しを削除 (常に off) | reorder 関数の `ordered_units = _pair_initial_distribution_units(...)` | 10: 正例・legacy env 4 値・cardinality 負例・worker 数非依存・junit 到達・hold 保全・配布反例 (レビュー B の予測と完全一致) | 既定で発火しない |
| M4 | cardinality 検算を削除 | 同関数の検算 `if` | 1: cardinality 負例 | `UsageError` が出ない |
| M5 | property 付与を削除 | reorder 関数の `if "pairing_rank" in unit:` | 7: 正例・legacy env 4 値・junit 到達・hold 保全 | property 4 種の欠落 |

## 5. 測定手順 (実際に実行した手順)

- **投入形:** 待ち手 `tools/dev_wave_wait.py acceptance --wave <arm の wave 名> --lease-dir … -- python3 tools/run_tests.py` (`IZANAGI_ACCEPTANCE_SHARDS=3`、`PYTHONDONTWRITEBYTECODE` unset、`IZANAGI_ACCEPTANCE_PAIRING_V1` unset) を、A は採用前 main の木 (`.claude/worktrees/dev-wave-t2766-pairing-adopt-a`、branch `worktree-dev-wave-t2766-pairing-adopt-a`、main `947fd160a` 起点)、B は wave 木 (X2) から投入した (`run-acceptance.sh`、`probe-source.md`)。待ち手は claim 後に `HEAD..main` が非 0 なら `git merge --no-ff --no-commit main` を自動 commit するので、6 走とも tested tip は merge commit。差 = 前 wave の直接投入との違いは lease / merge / receipt / launcher の main blob 実行が入ること。**測定対象は最遅 shard の JUnit testsuite time (W_max) であり、queue 待ち・claim・merge・receipt を含む受入総経過時間ではない** (投入〜完了は 9〜26 分)。
- **門番 (`gate-series.sh`):** 他 session の受入 leader ≤ 1 (自 slug 除外) ∧ 1 分 load < 60 が 2 周連続 → 乱数 0〜45 秒 → 再カウント ≤ 1 かつ自 wave の待ち手 0 で投入。周期 100〜140 秒乱数。競走型 (claim / merge / postcheck) は走 dir を `aborts/` へ退避して同じ走を再投入 (上限 3)。赤は停止 (親が DW-O18 で判定)。門番 log は `verbatim/series.log` (87 行)。
- **順序:** 対 1 = A,B / 対 2 = B,A / 対 3 = A,B (01-A 02-B 03-B 04-A 05-A 06-B)。無効対は同順序で追加 (07-A 08-B / 09-B 10-A)、上限 10 走。実行列: 01-A → 02-B → (03-B attempt 1 は claim-self-unverified で未投入) → 03-B → (04-A attempt 1 は postcheck で未投入) → 04-A → 05-A → 06-B。有効 3 対で固定終了、追加対なし。
- **lease:** 02-B 成功後に B wave の lease (land 用、TTL 40 分) が保持されたままで 03-B の claim が落ちた。親が `wave_land_window.py release` で free にし、`run-acceptance.sh` へ「`lease is held` の走だけ終端で release」を追加した (03-B attempt 2 以降に適用。`probe-source.md` の逐語は追加後の版。land は lease 保持を要求しない: renew は表示のみ)。
- **warm-up:** 本 wave は専用の warm-up 走をしていない。計算ノードの bytecode cache は前 wave の warm (2026-09-20 02:xx) と同日中の他 wave の受入で温まっており、shard-0 の F ≈ 70.5〜77.3 秒が warm 受入の固定費 (前 wave 69〜70 秒、T-2710 67 秒) と一致する。page cache・fixture の warm は保証しない。
- **記録:** 走ごとに `runs/<NN>-<A|B>/run.json` (tip_before / tip_after / tested_tip / tested_main / main_sha_at_launch / 投入・完了時刻 / 投入時・完了時の他 wave leader 数と load1 / rc / verdict / dirty / env) と receipt・待ち手 log、session の 3 shard `junit.xml` / `report.json` の写し (job dir、sha256 は `SHA256SUMS`)。
- **集計:** `t2766_adopt_analyze.py` (Codex author が前 wave の集計器から改作、job dir、repo へ入れない、`--selftest` PASS、逐語と sha256 `4fc9463e…` は `probe-source.md`) — 走表・対表・3 種の中央値・B の witness (被覆、rank 48〜95 = partner、head の (cardinality, cost) 多重集合と partner の cost 多重集合を `selected` + 台帳 (sha256 `1edbb792…`、前 wave と同一) から独立再計算、worker 別 item 列)・A の property 0 件検査・arm 別許容 tip 集合 (`--a-tips` / `--b-tips`、親が git で検証: A 3 tip は tested_main と tree 一致かつ X2 を含まず、B 3 tip は X2 を含み tested_main との差分は採用差分 2 file だけ)・`main_moved`・事前登録の判定。出力の原本 (`analysis.json` 767 KB sha256 `ba95ccac…`、`analysis.md` 697 KB sha256 `a3eba0cd…`) は job dir と本 dir (`analysis/analysis.json` は同一、`analysis/analysis-tables.md` は原本 md の表部)。

## 6. 走表 (shard-0 = 最遅 shard、W = JUnit testsuite time、O = 最忙 worker の占有、F = W − O、時刻 JST)

| 走 | 条件 | tested_main | tip | 投入 → 完了 | 投入時 leader / load1 | 完了時 leader / load1 | shard-0 tests | W_0 | O_0 (worker / items) | F_0 | W_1 | W_2 |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| 01-A | A | `4726b6493` | `a465c29c2` | 14:47:42 → 15:11:33 | 1 / 19.7 | 1 / 10.4 | 4048 | **500.96** | 428.6 (gw0 / 73) | 72.4 | 276.5 | 214.5 |
| 02-B | B | `4fe49200e` | `a4c30d6c6` | 15:14:17 → 15:23:37 | 0 / 8.2 | 1 / 11.8 | 4061 | **355.13** | 277.8 (gw32 / 142) | 77.3 | 265.7 | 249.5 |
| 03-B | B | `c6bacf505` | `8cdd7bf54` | 15:44:02 → 16:07:25 | 1 / 4.3 | 0 / 26.3 | 4061 | **353.77** | 283.1 (gw47 / 8) | 70.7 | 245.0 | 203.9 |
| 04-A | A | `182cdb8d6` | `5fb5a37f1` | 17:09:47 → 17:35:29 | 1 / 3.3 | 1 / 3.5 | 4059 | **440.04** | 369.5 (gw36 / 76) | 70.5 | 247.1 | 165.6 |
| 05-A | A | `82d7206d6` | `94368ff75` | 17:43:37 → 17:54:41 | 0 / 5.7 | 0 / 3.5 | 4103 | **455.94** | 384.5 (gw47 / 25) | 71.4 | 242.0 | 165.3 |
| 06-B | B | `fec4a8187` | `cfb217cdb` | 17:57:13 → 18:10:52 | 0 / 3.7 | 1 / 4.3 | 4116 | **398.63** | 327.3 (gw46 / 12) | 71.3 | 245.6 | 172.2 |

6 走とも rc=0 / child-green / 3 shard の report.json 実在 / tip = tip_after / dirty 0 / bytecode env "no" / B は witness 4 検査 true → 有効。

### 対表と判定

| 対 | 順序 | 走 | main_moved (main 側の実装面差分) | W_max(A) | W_max(B) | ΔW | r | D357 注記 |
|---|---|---|---|---|---|---|---|---|
| 1 | A,B | 01-A / 02-B | yes (`4726b6493` → `4fe49200e`: `orchestrator/campaign/s8b_holdout_admission.py` +158、`tests/test_s8b_holdout_admission.py` +615) | 500.96 | 355.13 | **145.83** | **29.1 %** | ≥ 10 % |
| 2 | B,A | 03-B / 04-A | yes (`c6bacf505` → `182cdb8d6`: 31 file +3196 −4437、T-2800 の test 13 本削除・verifier dsg/parse・fig11 plotting・T-2724 freeze 等。A (後走) が有利になる方向) | 440.04 | 353.77 | **86.27** | **19.6 %** | ≥ 10 % |
| 3 | A,B | 05-A / 06-B | yes (`82d7206d6` → `fec4a8187`: docs fold のみ、実装面 0) | 455.94 | 398.63 | **57.31** | **12.6 %** | ≥ 10 % |

- 対差の中央値 **86.3 秒**、対率の中央値 **19.6 %**、条件別中央値差 med W_max(A) 455.94 − med W_max(B) 355.13 = **100.8 秒**。
- 判定 (事前登録): 有効 3 対、全対 ΔW > 0、med r = 19.6 % ≥ 10 % → **(i) 方向一致・閾値以上 → land** (`analysis/analysis-tables.md` の `verdict: land`)。

### 条件差 (記述的)

- 門番 log (`verbatim/series.log`) では、投入時の他 wave leader は 0〜1、1 分 load は 3.3〜19.7。走行中の連続観測はない (未観測)。16:29 前後に login の load5 が 116 まで上がった帯があるが、04-A の投入 (17:09) より前で、走行中の走は無い (03-B は 16:07 完了)。
- main は測定中に少なくとも 10 回前進した (peer 通知だけで 10 回: T-2610、T-2796、T-2792、B-10 results、fig11、T-2800、T-2724、verifier-capacity、T-2153、T-2795)。各走の tested_main と tip は走表のとおり。A の tip 3 本は tested_main と tree 一致、B の tip 3 本は tested_main + 採用差分 2 file (+319 −7)。
- shard-0 の tests 数は 4048〜4116 (main 側の test 追加・削除で動く)。

## 7. 残存限界・未実測

- 機序未同定 (前 wave §1 結論 5 のまま)。A 側 witness は取っていない (P2: A = 採用前 main を保つため。A の item → worker 対応は `report.json` に無い)。A の律速 worker は 01-A gw0 (73 item、428.6 秒)、04-A gw36 (76 item、369.5 秒)、05-A gw47 (25 item、384.5 秒) で中身は未観測。
- 隣接対は同 allocation でなく、対内で main も動いた (§6)。同一 tip の対比較は前 wave (直接投入) が担い、本 wave は「待ち手経由 = 本番経路」での再確認である。
- 効果量は regime 依存。本夜の A (W_max 440〜501) は前 wave の A (455〜481) と同程度だが、B (354〜399) は前 wave の B (336〜362) より幅が広い。06-B は e2e 単体が 266 秒 (他 2 走は 218 / 223 秒) で、pairing と無関係な揺れが W_max に入る。「毎受入 100 秒」とは言えない。57〜146 秒の観測である。
- 3/3 は有意差判定ではない。有効 3 対で固定終了 (追加対なし)。
- 直接投入と待ち手経由の差 (lease / merge / receipt / launcher の main blob 実行) は W_max の外にある。受入総経過時間 (投入〜完了 9〜26 分、queue 待ちと門番待ちを含む) は測定対象ではない。
- property の時間費用は分離していない (F は A/B とも 70〜77 秒)。junit.xml の増分 (受入 1 走あたり約 +13 MB、3.4 倍) は session dir の増分として残る。撤去・縮約 (rank / partner だけにする等) は別裁定。
- cardinality 検算の完全性は「受入 collection の nodeid が一意」という前提付き (レビュー B、X1 からの既存境界)。異なる item が同一 nodeid を持つ fixture では helper の cardinality (item 数) と xdist の cardinality (nodeid 辞書長) が食い違い検算を通過しうる。現行の実受入にその重複は観測されていない。gate は足していない。
- 順序依存の赤は本 wave の B 3 走 (+ 前 wave の B 4 走) で観測しなかっただけ。hold / selected の保全 test は局所検査。
- launcher の lease release は 03-B attempt 2 以降の版で、01-A / 02-B / 03-B attempt 1 は release 無しの版で走った (走の中身に差は無い。02-B 成功後の lease 保持が 03-B attempt 1 を落とした)。

## 8. 再現資料・成果物対応

- **実装:** X2 `2404642c3f3d89eeb8068f0d7cdcb84016a239b7` (親 X1 `715bf37b7` ← main `947fd160a`)。X1 は `0eabe67ba` (impl branch `impl-t2766-pairing-optin`) の cherry-pick。main に対する正味差分は `orchestrator/tests/conftest.py` と `orchestrator/tests/test_acceptance_schedule_order.py` の 2 file (+319 −7)。impl branch `impl-t2766-pairing-optin` は採用で用途を終えた (撤去はユーザー指示または `/cleanup-branches` の裁定)。
- **台帳:** `orchestrator/tests/acceptance_duration_ledger.json` (sha256 `1edbb7929a7b341e050fd37ea32f19c93f4d63d8f95afd760018b7cf7ac3273a`、前 wave と同一)。
- **集計器・launcher:** `probe-source.md` (逐語 + sha256)。再集計: `python3 t2766_adopt_analyze.py --runs-root <job dir>/runs --ledger <台帳> --out <dir> --a-tips a465c29c201e4a7d008c32d1294365e4c20d9d3c,5fb5a37f13237ace6334cd47e9cb7b8111fc47b8,94368ff7539d863bdcb7b8dea540f65a18981cd3 --b-tips a4c30d6c6333ccc622b4f7c479d7bb9eb32588aa,8cdd7bf54e821cfb9cef10303215da3b790e76eb,cfb217cdb9b3eb9ddf6ce521cfac041ac5effc67`。
- **raw 成果物 (job dir `/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2766-pairing-adopt/`):** `runs/<NN>-<X>/{run.json, acceptance.log, acceptance-child.log, acceptance-receipt.json, lease-release.json, session/shard-{0,1,2}/{junit.xml, report.json}, session/SHA256SUMS}` (本 dir の `runs/` は run.json / receipt / acceptance.log / SHA256SUMS / lease-release.json の写し)、`aborts/` (未投入停止 2 件の写しは本 dir `aborts/`)、`analysis/`、`codex/` (prompt・log・artifact・patch)、`focus/`、`mutation-*`、`contract-test/` (接続確認)。元 session (`/work/1/SFC/tanab/.izanagi-acceptance-shards/<session>/`) の path は各 `run.json` の `session_dir_origin`。
- **変異:** `mutation-spec-probe.json` / `mutation-expected-nodes.json` / `mutation-probe-results.json` / `mutation-spec-final.json` / `mutation-final-results.json` (+ wrapper receipt、attempts)。
- **起動手順:** §5。順序と slot は `gate-series.sh` の `PLAN` のとおり。

## 9. レビュー・裁定の逐語

`verbatim/s5-author.md` (author 報告)、`verbatim/s6-reviewA.md` / `verbatim/s6-reviewB.md` (レビュー)、`verbatim/prompt-author.md` / `prompt-review-{A,B}.md` (投げ文)、`s1-brief.md`、`s4-ruling.md` (追補を含む)、`verbatim/focus1-summary.txt`、`verbatim/series.log` (門番 log)。
