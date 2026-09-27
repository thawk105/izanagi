# 第 2 プロトコル MOCC での 5 手法の疎通 (20 候補 × 3 workload) ([T-2849] 残り (3)、2026-09-26〜27)

- 依頼 (逐語): `verbatim/request.md`。段 1 brief: `verbatim/brief.md`。開始 gate: `verbatim/startup-gate.log` (rc=0、起点 local main `6c3913bc5`)。
- 設計は D2220 項 6、差し込みは D2248 と `output/insights/2026-09-26/t2849-mocc-insertion/README.md`、write-heavy の同時検査は D2251。
- **コード変更なし。** 既存の harness (`t2849_comparison_harness run-series / run-block-controls --protocol mocc`) を job body (`tools/pegasus/p3_s4_loop_pegasus.sh`) の harness mode で直接 qsub した。
  全 job の submit-tree は `6c3913bc5` (ccbench = pin C `68106660686232781bca3be792a750d3e19d7a8a`)。
- 台帳・証跡・集計は repo 外の job dir `/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2849-mocc-conn/` (cohort は `main/cohort`、集計は `main/aggregate.json`、費用は `main/job-costs.json`)。
  trace の保全先は `/work/1/SFC/tanab/izanagi-repro-archive/t2849-mocc-conn-20260926/` (単価実測は `probe/`、本投入は `main/`)。

## 0. 要約

1. **5 手法 × 3 workload の 15 系列がすべて同じ口で終端まで走った。** 15 系列とも `b-complete` (B = 2 を消化)、block 対照 3 本も `b-complete`。
   候補評価は workload ごとに 20 (初期点 2 + 探索 2 の 4 × 5 系列)、終点の再計測を含む候補 slot は 25。集計 (`aggregate`) の不一致は 0。
2. **stock 比 (終点の score ÷ 同 workload の block 対照の stock、§3):** write-heavy 0.66〜1.06、balanced 0.97〜1.20、read-heavy 0.99〜1.76。
   **既知最良の参照は無い** (MOCC には `p2_2_flag_opt` に当たる実測が無く、参照比は全系列で null、D2220 項 6)。1 系列ずつ・反復なし・同時刻の対照なしの疎通の観測であり、手法間の優劣や性能の主張ではない。
3. **read-heavy の候補 slot 25 件中 6 件で正しさ検査が non-serializable を検出し、候補を reject した (§4)。** 6 件とも 1 反復に巡回 1 件の write skew (G2)。
   同じ workload の stock slot 7 件と、write-heavy・balanced の候補 slot 50 件は anomaly 0。値 5・10・20・135・651 µs で出ており、特定の値に限らない。原因 (MOCC 本体か、差し込みか、verifier か) は未確定。
4. **llm 系列の提案 13 機会のうち 7 件が planner の axis 名の揺れで拒否された (§5)。** planner は axis に `silo-backoff-magnitude` 以外の名前 (`swept-parameter-magnitude` 等) を返し、巡 tool の検査で落ちる。
   設計どおり救済せず機会 A を消費し、3 系列とも A の上限 (6) の内で B = 2 に達した。silo の [T-2850] smoke にも 1 件あり、MOCC 固有ではない。
5. **計算:** 本投入 18 job の Elapse 計 49,135 s = 13.65 node 時間 (ユーザー承認時の見積り 10〜14)、単価実測 1,416 s、止まった 1 job 31 s。trace の保全は 552 反復すべて complete、115 GB。

## 1. 構成

| 項目 | 値 |
|---|---|
| cohort | `t2849-mocc-conn-v1` (silo と別名・別 root、D2248 項 1)。単価実測は `t2849-mocc-conn-probe-v1` |
| 系列 | 各 workload で random・sweep・bo・evolution・llm を 1 系列ずつ (series = 1、block = 1)、A = 6・B = 2・N_eval = 1 |
| 1 系列の slot | 開始 stock 1 → 初期点 2 (5・10 µs) → 探索 B 件 → 終点の再計測 N_eval 件 = 6 slot |
| block 対照 | workload ごとに block-stock 1 session (MOCC は参照 slot を作らない) |
| genome | stock = `mocc|BACK_OFF=1,KEY_SORT=0,TEMPERATURE_RESET_OPT=1` + `BACKOFF_FIXED=-1`、候補 = 同 flags + `BACKOFF_FIXED=<v>` (literal の材料化) |
| 検査 | write-heavy は同時検査 (D2251、harness が slot argv に常に付ける)、balanced・read-heavy は直列検査 (着地済みの挙動のまま、下記) |
| trace 保全 | qsub の env に `IZANAGI_TRACE_ARCHIVE_ROOT` を渡した (job body は env を消さず、harness の子 `b5_generator_contrast.default_runner` は `os.environ` を継承) |
| submit-tree | job ごとに 1 本、job dir 下 (`trees/m-<wl>-<arm>`)、third-party は tree 内 staging へ hydrate、`git worktree lock` 済み。LLM 親は専用の `trees/llm-parent` |
| LLM 親 | T-2850 glue v3 の `parent_driver.py` (未改変の写し、sha256 `b1eba1bf…`) を login で起動。親 template は T-2850 版の写しで、固定 commit・description・materials root・事前登録の参照だけ差し替えた (job dir `parents/`)。model `claude-opus-5` (B-5 の settings) |

- **balanced・read-heavy に同時検査を使わなかった理由:** 依頼は「使うなら記憶量と静定待ちの上限を先に測る」。着地済みの比較 harness は同時検査を write-heavy の slot にだけ付け、広げるにはコード変更と実測が要る。
  単価実測で直列検査の費用 (balanced 346 s、read-heavy 760 s / slot) を示してユーザー確認を取ったので、本 wave では広げていない。

## 2. 単価実測 (本投入の前、DW-G01 の生死確認を兼ねる)

block 対照 (stock 1 session、保全有効) を workload ごとに 1 job。

| workload | request | 判定 | tps | slot wall | job Elapse | 保全量 |
|---|---|---|---:|---:|---:|---:|
| write-heavy (同時検査) | 30084 | certified・normal | 1,230,349 | 212 s | 244 s | 522 MB |
| balanced (直列) | 30086 | certified・normal | 822,729 | 346 s | 380 s | 714 MB |
| read-heavy (直列) | 30087 | certified・normal | 2,399,092 | 760 s | 792 s | 2.4 GB |

この単価で 20 候補 × 3 workload (93 slot) を約 10〜14 node 時間 (中心 12.5) と見積もり、ユーザーの回答は「20 候補 × 3 workload (推奨)」(`verbatim/estimate.md`・`verbatim/user-compute-confirmation.md`)。

## 3. 結果

stock = 同 workload の block 対照の stock (write-heavy 1,238,350・balanced 819,720・read-heavy 2,405,757 tps)。slot は「値 µs: tps」、A = anomaly、Q = 品質欠測 (§6)、R = 提案の拒否。

| workload | 手法 | 初期点 5 / 10 | 探索 (順) | 終点 | score | stock 比 | 状態 |
|---|---|---|---|---:|---:|---:|---|
| write-heavy | random | 798,159 / 801,770 | 31: 810,058、253: 1,314,217 | 253 | 1,313,931 | 1.061 | scored |
| write-heavy | sweep | 785,548 / 811,302 | 150: 1,173,505、12: 812,848 | 150 | 1,180,408 | 0.953 | scored |
| write-heavy | bo | 785,466 / 805,638 | 1000: 1,172,904、214: 1,269,918 | 214 | 1,261,336 | 1.019 | scored |
| write-heavy | evolution | 775,283 / 809,353 | 13: 816,686、7: 791,247 | 13 | 816,632 | 0.659 | scored |
| write-heavy | llm | 761,555 / 804,123 | R、R、25: 813,436、100: 1,057,597 | 100 | 1,037,252 | 0.838 | scored |
| balanced | random | 800,367 / 803,573 | 24: 855,142 (Q)、7: 834,224 | 7 | 807,621 | 0.985 | scored |
| balanced | sweep | 810,606 / 788,863 | 15: 813,732、1: 792,195 (Q) | 15 | 821,593 | 1.002 | scored |
| balanced | bo | 811,212 / 774,866 | 1000: 658,258、1: 800,897 | 5 (初期点) | 800,599 | 0.977 | scored |
| balanced | evolution | 806,451 / 814,626 (Q) | 7: 799,818、2: 802,338 (Q) | 5 (初期点) | 794,878 | 0.970 | scored |
| balanced | llm | 785,765 / 813,484 | R×4、25: 859,111、50: 978,986 | 50 | 980,030 | 1.196 | scored |
| read-heavy | random | 3,893,781 / A | 651: A、503: 2,399,333 | 503 | 2,383,141 | 0.991 | scored |
| read-heavy | sweep | A / 3,952,706 | 800: 1,863,528、20: 4,002,575 | 20 | 再計測 A | 1.000 | fallback-score-anomaly |
| read-heavy | bo | A / 3,934,611 | 135: 4,067,907、1000: 1,671,113 | 135 | 再計測 A | 1.000 | fallback-score-anomaly |
| read-heavy | evolution | 3,917,503 / 3,931,631 | 3: 3,873,568、13: 3,996,519 | 13 | 3,977,847 | 1.653 | scored |
| read-heavy | llm | 3,911,119 / 3,946,817 | R、20: 3,994,794、80: 4,219,540 | 80 | 4,229,195 | 1.758 | scored |

- `fallback-score-anomaly` は終点の再計測が anomaly だった系列で、集計は score を block の stock で代替する (stock 比 1.000 は定義上の値)。
- 終点の選択は harness の規則どおり、同 workload のどこかの系列で anomaly を出した値を除外する (`_disqualified`)。read-heavy の random は 5・10 µs が他系列の anomaly で除外され、503 µs を終点にした。
- 観測の形 (疎通の 1 回の観測で、主張ではない): write-heavy は小さい固定値 (5〜31 µs) が stock より約 35% 低く、150〜253 µs で stock 前後。read-heavy は 3〜135 µs で stock の約 1.6〜1.75 倍、500 µs 以上で stock 以下。balanced は 50 µs の 1 点を除き stock の ±5% 内。
- **read-heavy の 1.65・1.76 は certified の終点だが、同じ値域の他の値で anomaly が出ている (§4)。** 1 slot の certified (5 反復 + 再計測 5 反復) はこの値域で候補が安全であることの強い証拠ではない。

## 4. read-heavy の anomaly (正しさゲートによる reject)

| 系列 | slot | 値 µs | 検出 | 巡回 | key | 検査走行の abort 率 |
|---|---|---:|---|---|---|---:|
| bo | 初期点 1 | 5 | 性能 pass rep 5 (rep 1〜4 は合格) | G2 1 件 (rw・rw の 2 取引) | 0・2 | 19.70% |
| bo | 終点の再計測 | 135 | 性能 pass | G2 1 件 | 0・3 | 5.91% |
| random | 初期点 2 | 10 | 性能 pass | G2 1 件 | 0・1 | 17.28% |
| random | 探索 1 | 651 | 性能 pass | G2 1 件 | 0・0x61 | 1.68% |
| sweep | 初期点 1 | 5 | 性能 pass | G2 1 件 | 1・2 | 19.67% |
| sweep | 終点の再計測 | 20 | 性能 pass | G2 1 件 | 0・1 | 14.49% |

- 6 件とも `abort_reason = non-serializable`・`failure_class = candidate` で、pipeline がその slot を reject し、harness は値を endpoint から除外した。規律 2 のとおりで、正しさ判定の条件は変えていない。
- 巡回の witness は 2 取引がそれぞれ相手の読んだ版を上書きして両方 commit した write skew で、関わる key は zipf の上位。digest は各 slot の campaign root の `s4_loop_digest.txt`
  (例: bo の初期点 = `trees/m-rh-bo/output/exploration/campaigns/p3-s4-loop-s4-autonomous-c90fb5b6/`)。anomaly の反復を含む trace は保全先にある。
- 比較: 同じ read-heavy の stock slot 7 件 (単価実測 1・block 対照 1・各系列の開始 stock 5) は anomaly 0。write-heavy・balanced の候補 slot 50 件も 0。
  MOCC の既存の検出実走 (`output/insights/2026-09-26/t2847-mocc-run/README.md`) の stock 28 run は小規模 cell (commit 18〜20 万 / 105〜355 万) ですべて serializable だった。
- 検査走行の abort 率 (digest の abort 統計、その campaign で検査した trace の値) は anomaly の 6 件で 1.68〜19.70%、同じ digest 群の stock で 2.82〜3.20%。abort の多い条件だけで出ているとは言えない。
- **未確定:** MOCC 本体の欠陥が固定 backoff の条件 (多くは高 throughput) で表に出たのか、literal の差し込みが MOCC の意味を変えたのか、verifier の誤検出かは切り分けていない。
  stock (適応 backoff) を同じ throughput 域で走らせる手段は今回の構成に無い。

## 5. llm 系列 (K0)

| workload | 機会 A | 拒否 (role-output) | 評価 B | 提案待ちの計 | role 呼出し |
|---|---:|---:|---:|---:|---:|
| write-heavy | 4 | 2 (`swept-parameter-magnitude`・`backoff-magnitude`) | 2 | 1,742 s | 6 |
| balanced | 6 | 4 (`initial-points-parameter-magnitude`・`tuned-parameter-magnitude` ×2・`single-parameter-magnitude`) | 2 | 1,577 s | 8 |
| read-heavy | 3 | 1 (`primary-tuning-parameter-magnitude`) | 2 | 2,087 s | 5 |

- 拒否はすべて planner の axis 名が `silo-backoff-magnitude` でないことによる巡 tool (`tools/t2849_llm_round.py` の planner 検査) の不通過。planner の入力 prompt には axis 名が無く、役割定義 (`.claude/agents/planner-v4.md` の出力例) の axis を他の欄と同じ占位と読んだ出力と見える。
  silo の [T-2850] smoke v1 の planner 出力にも `single-parameter-magnitude` が 1 件ある。MOCC の protocol は planner に渡らないので、MOCC 固有の原因ではない。
- template どおり親は候補を直さず、A を消費した。balanced は A = 6 のうち 6 を使い切る直前で B = 2 に達した。model 不一致 (`model-mismatch.md`) は 0。
- LLM の週枠 429 は起きなかった。

## 6. 品質欠測

balanced の 4 slot (evolution の初期点 10 と探索 2、random の探索 24、sweep の探索 1) が certified だが `settled=false` で品質欠測になり、終点の候補から外れた。
計測前の静定待ち (1 分平均 load ≤ 4.0 を最大 20 秒) の既存条件で、silo の [T-2850] 試走にも同じ型がある。系列はいずれも `b-complete`。write-heavy (同時検査は静定待ちの上限 120 s、D2251 項 4) と read-heavy は 0。

## 7. 計算の費用 (D2212 項 4)

| 区分 | job | Elapse |
|---|---|---:|
| 単価実測 | 30084・30086・30087 | 1,416 s |
| 本投入 write-heavy | 30998・30999・31000・31001・31003・31004 | 8,219 s |
| 本投入 balanced | 31005〜31010 | 12,236 s |
| 本投入 read-heavy | 31011〜31016 | 28,680 s |
| 本投入 計 | 18 job | 49,135 s = 13.65 node 時間 |
| 止まった試行 | 31002 | 31 s |
| 計 | | 50,582 s ≈ 14.05 node 時間 |

- 見積り (10〜14、中心 12.5) の上側寄りになった主因は read-heavy の候補 slot が stock より長かったこと (約 960 s vs 760 s)。候補の throughput が stock の約 1.6 倍で、検査する取引が多い。
  見積りは「候補 slot は stock 以下」(前回 wave の write-heavy の実測) を仮定していた。
- llm 系列の job は提案待ちの間も node を握った (3 系列の待ちの計 5,406 s ≈ 1.5 node 時間)。
- 受入全走は記録 commit の後に走らせる (本 insight には書かない)。

## 8. 止まった試行

| job | 停止 | 対応 |
|---|---|---|
| 31002 (write-heavy の block 対照、walltime 30 分) | harness は各 slot の開始前に残り 1,800 s 以上を要求する (`b5_generator_contrast.SESSION_BUDGET_S`)。30 分の walltime では 1 slot も始まらず `allocation-exhausted` | 台帳と証跡を job dir の `main/failed-31002/` へ退避し、walltime 45 分で投げ直した (31004)。計測値は 0 件 |

## 9. 残りと申し送り

- [T-2849] の完了条件 (5 手法が同じ口で走る基盤 S1 と第 2 プロトコルでの疎通) はこれで満たした。
- read-heavy の anomaly の原因の切り分け (§4) は新しい課題として起票する。論文の「正しさゲートが探索の候補を実際に reject する」例になりうるが、MOCC 本体の欠陥か差し込みの影響かが決まるまで主張に使わない。
- K0 の planner の axis 名の揺れ (§5) は、silo・MOCC 共通で提案機会の約半分を失わせる実測欠陥として起票する。候補の直し方 (planner の入力に axis 名を載せる等) は択一がある。
- harness mode の直接 qsub の walltime は「最後の slot の開始までの時間 + 1,800 s」以上にする (§8)。

## 10. 追記 (2026-09-27、[T-2868]) — §4 の切り分けの結果と記述の訂正

本節は追記であり、§0〜§9 の記述と判定は変えない (規律 7)。詳細は `output/insights/2026-09-27/t2868-mocc-g2-cause/README.md`。

- §4 の 6 件は、保全 trace で同じ版の verifier を再実行して同じ witness が出た。verifier を使わない生の行の照合でも 2 辺が成立した。保全 patch は template + `now_backoff` の 1 行だけだった。
- 同じ構成の stock (literal なし) を 16 slot 追加で走らせると、性能構成 74 反復中 3 件に同じ形の G2 が出た。候補 6/119 対 stock 3/109 (本節の 0/35 を含む) で率の差は検出されない (両側 Fisher p = 0.50)。原因は MOCC 側 (本体の実装か trace の記録、両者は未分離) に絞られ、literal の差し込みは必要条件ではない (候補での寄与の有無と率の同等性は示していない)。
- 訂正 1: §4 の「検査走行の abort 率」列は digest の legacy workload (4 thread・200 record・1 秒) の値だった。性能構成の anomaly 反復では bo 初期点で 6.8%。
- 訂正 2: 1 slot は legacy 1 回 + 性能構成最大 5 反復 (anomaly で打ち切り) で、「stock slot 7 件は 0」は性能構成の反復で 0/35。
- read-heavy の block 対照の stock も同じ性質の実装なので、§3 の read-heavy の stock 比と certified の終点は「基準の stock が性能構成の検査に落ちる反復がある cell」(観測 3/109、95% 区間 0.6〜7.8%) での値である。扱いは新しい課題で決める。
