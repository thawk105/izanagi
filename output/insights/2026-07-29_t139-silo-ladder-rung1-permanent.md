# [T-139] rung 1 恒久実装 wave — 実装・実測・受理の台帳 (dev-wave 2026-07-29)

`authority: none` / `default_effect: no-state-change` — 本書は凍結記録であり、可変状態の正本
(worklog 末尾) ではない。設計仕様の正本 = `2026-07-29_t139-silo-degradation-ladder-design.md`
(以下「設計 insight」) §6 要件束 + ユーザー裁定 (worklog 2026-07-29 (45) と (54))。

**位置づけ (設計 insight の但し書きを継承):** rung 1 は ability probe であり、研究目標
(roadmap §1) に数えない。本書の throughput は characterization の受理証拠であり、
性能比較 headline・calibration・floor・RF のいずれにも使わない。

## 1. 成果物 (wave branch `worktree-dev-wave-t139-permanent` の commit 集合)

| 成果物 | 所在 |
|---|---|
| rung 1 恒久 patch (D18 第 4 類 subtype `evaluation_role=ability_probe`) | `patches/silo_ladder_rung1.patch` (sha256 = ledger の `patch_sha256`) |
| 機械可読台帳 (closed schema、projection_policy 付き) | `patches/ledger.json` |
| 静的契約 checker (reason code 別) | `orchestrator/campaign/silo_ladder_rung1_contract.py` |
| 専用 characterization driver (correctness / gap-job / collect / verify-result) | `orchestrator/campaign/silo_ladder_rung1.py` |
| 射影 tripwire (§6-5(c)) + 3 loop loader 配線 | `orchestrator/campaign/projection_guard.py`、`p3_s4_loop{,_sort,_trigger_gating}.py` |
| PBS 資材 (offline staging・F49 receipt・walltime 式) | `tools/pegasus/silo_ladder_rung1.sh`、`submit_silo_ladder_rung1.sh`、`policy.json` |
| committed 実証 JSON (all_pass=true) | `output/env/pegasus/silo_ladder_rung1/silo_ladder_rung1.json` |
| raw evidence bundle (sha256 相互参照鎖、124MB) | `output/env/pegasus/silo_ladder_rung1/job-staging/0_873917.nqsv/raw-bundle-attempt-1/` |
| 再束縛 pytest (content 束縛・HEAD 非束縛) | `orchestrator/tests/test_silo_ladder_rung1_evidence.py` ほか test 3 本 + fixtures |

## 2. 実測 (campaign 4 = request 873917.nqsv、2026-07-29)

- **correctness leg** (login pegasus02、trace build t4、attempt a8): verifier certified_serializable、
  anomaly 0、integrity clean — rung 1 は serializable 不変 (規律 2 gate 通過)
- **gap leg** (計算ノード、trace-disabled t48、N=1,000,000、interleave 6 rep、事前凍結 schedule):

| workload | stock (min–max tps) | rung 1 (min–max tps) | rung/stock |
|---|---|---|---|
| W-cal (登録 calibration workload 逐語: rmw=0/rr=50/skew=0.9) | 3,440,398–3,670,262 | 155,225–163,263 | ≈4.4% |
| W-hw (高競合 write: rmw/skew=0.9。N/t48/build 契約の転写のみ = `contract-transfer-only`) | 1,520,374–1,562,354 | 161,864–168,770 | ≈10.7% |

- 方向 gate `max(rung) < min(stock)` は両 workload で成立 (差 ≈9〜22 倍で決定的)
- per-worker witness: rung-liveness build (REPORT マクロ) の 4 run 全てで 48 worker
  全 ordinal・全 commits>0・合計 conservation・batch=0。starvation-freedom は主張しない
  (`per_worker_ever_committed` + `bounded_completion` の限定命名)
- attestation: CPU/クロック/cpuset/HT/NUMA を登録契約と実測照合、28 sample 前単独性検査
- 受理: driver 検証 + collect の raw 再計算 + verify-result rc=0 + evidence pytest。
  受入全走 3258 passed / 18 skipped (login node、g++-13 系 18 skip はこの環境で検出力なし)

## 3. 実測が検出し fix した実装欠陥 (計 6 件 — 静的検査層では原理的に捕捉不能だったもの)

1. identity 定義が `extern "C"` 単一宣言 + 初期化子で -Werror 赤 → brace 形へ (commit d8b017e)
2. compile_commands.json は多ターゲットで TU 重複 → ycsb_silo.exe target 限定 (D75 型)
3. **計算ノードは外部 network 不可** — FetchContent (masstree/mimalloc/googletest) の clone が
   不能 (873903/873904 で 2 回再現、DNS 解決不能)。→ pinned 事前 staging 化 (submitter が
   login で clone・照合、job へ FETCHCONTENT_SOURCE_DIR_* を渡す)。環境事実は
   `docs/pegasus-runbook.md` §7.1 に追記
4. NQSV の会計エピローグに OpenPBS 形式 `exit_status` 行は存在しない → 実在 field
   (Request ID/Started/Ended/Elapse) へ是正。scheduler 側 exit status は取得不能
   (JSON `limitations` に明記。in-job 成功は success sentinel + failure receipt 不在が担う)
5. nm/readelf の link 検査が basename 文字を期待 vs realpath 起動 → argv[0] フルパス完全一致へ強化
6. compiler `--version` 第 1 token は起動名依存 → 第 1 token 除外の正規化比較 (realpath 一致は維持)

裁定メモ: 3 の後の再測定は「両 attempt とも configure 段で死亡 = 観測 sample ゼロ」のため
optional stopping に当たらないと親裁定し、新 campaign として実施 (B-14 の retry 上限は
同一 campaign 内の選別対策)。5/6 の後も R2-4 束縛 (submit receipt との bytes 一致) が
働き、campaign 3 の測定は破棄して campaign 4 で submit→測定→collect を同一 bytes で貫通した。

## 4. 変異検査 (事前登録 = 段 4、本走 = commit I 後、DW-O19)

| mutant | 内容 | killer nodeid (期待どおり各 1 件) |
|---|---|---|
| PM1 | liveness all→any | test_n5_one_zero_worker_kills_only_ever_committed_gate |
| PM2 | macro exactly-one→at-least-one | test_compile_argv_gate_requires_exactly_one_macro_and_clean_stock |
| PM3 | certified→serializable 単独受理 | test_n4_certified_false_kills_only_correctness_gate |
| PM4 | 射影 tripwire を token 素通しへ | test_projection_tripwire_rejects_excluded_token_in_all_three_loaders |

4/4 KILLED、他 133 test 不変、復元は内容比較で確認。負例 fixture N1/N2a/N2b/N3〜N6 +
正例 P+1/P+2 (過剰拒否検出) は suite 常設。

## 5. evidence pytest の実測後逸脱 (B-11 の規定による記録)

実測前凍結 sha256 = `9603008c…`。実測後、現物に対して 2 件の表現是正を行った
(最終 sha256 = `fe21b67a…`):
1. binding 複合検査の `third_party_heads` 期待位置 (driver は `provenance.third_party_sources`
   に記録 — pin 照合は同 test の provenance 側検査が担う。値の要求は不変)
2. CMakeCache の型 token 期待 `:FILEPATH=` → 実挙動の `:STRING=` (コマンドライン -D 指定時の
   CMake 実挙動。compiler パス完全一致の要求は不変)

いずれも「値・受理集合を弱めない表現是正」であり、性能値や gate 判定への影響はない。

## 6. レビュー閉鎖の要約 (段 3 × 2 + 段 6 × 2 + 焦点 3 巡 + targeted fix)

段 3 (32 所見) と段 6 (21 所見 + 親検出 2) は全件 real/refuted 裁定済み (裁定正本 =
wave handoff の s4-ruling / s6-focus3)。DW-O16 の 3 巡上限到達後の残余 3 blocker は
親裁定 + targeted fix + テスト・変異による直接閉鎖検証で閉じた (レビュー round は増やさず)。

## 7. ユーザー裁定パッケージ (実装せず返す)

1. **prompt 因果束縛** (A-10/B-2): 射影 tripwire は「harness が受理する proposal 経路」までを
   閉じる字面回帰検知であり、planner/coder への実 prompt bytes の因果証明は未実装。
   mediated launcher / provider receipt の導入は独立 wave の設計裁定として返す
2. **origin-allowlist 再設計** (A-9/B-1 残余): encoding・言い換え・semantic copy への保証は
   token/path 検査では原理的に閉じない。入力組み立てを trusted registry の artifact ID 起点に
   再設計するかの裁定
3. **raw bundle の保存形** (nit/backlog): trace 4 本で bundle 124MB。圧縮保存 + manifest の
   hash 対象定義の変更は driver 変更 = 再測定を要するため、次に characterization を
   取り直す機会に合流させる案を推奨
4. identity symbol の layout ablation 省略の追認 (段 4 A-12 裁定の記録)

## 8. 本書が主張しないこと

- 「梯子が立った」「recovery 測定が可能になった」— recovery pipeline への接続
  (`recovery_measurement_eligibility=false`) と RF 規範化 ((d) 裁定) は将来の実験設計時
- rung 1 の劣化の機序帰属 (CAS 中央 gate という構造は既知だが、cell 間差 4.4% vs 10.7% の
  機序説明は未検証の観察)
- W-hw の N=1m が較正済みであること (契約転写のみ — `calibration_status` field が機械可読に区別)
