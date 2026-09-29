# 比較 harness への MOCC の差し込みと、pin C での MOCC 動作点の較正 ([T-2849] 残り (2) = 単位 8、2026-09-26)

- 依頼 (逐語): `verbatim/request.md`。設計は D2220 項 6 と `output/insights/2026-09-22/t2849-comparison-harness-design/README.md` §9、既存実装は D2233 と `output/insights/2026-09-23/t2849-comparison-harness-impl/README.md`。
- 起点: local main `42d148868` (fresh worktree、開始 gate rc=0 = `verbatim/startup-gate.log`)。ccbench gitlink = C `68106660686232781bca3be792a750d3e19d7a8a`。
- commit: 較正記録 `f72ad2c52`、実装の統合 `955bfed71`、fix 1 `3aa390388`、fix 2 `18f379f0d`。
- 残り (3) 第 2 プロトコルでの疎通は scope 外 (依頼どおり)。

## 0. 要約

1. **MOCC の動作点を pin C で較正した。** 既存の認定較正 launcher で rr5・rr50・rr95 を 3 job 同時に取り、3 件とも accepted・records = 1,000,000 (D15 の下限基準)。S1 の silo の動作点 (`p2_2`: 1,000,000 records・48 threads・3 秒・5 rep) と同値になった。
2. **比較 harness の 1 slot 経路に protocol `mocc` を通した。** 単回評価 (`p3_s4_loop`)・系列制御 (`t2849_comparison_harness`)・K0 LLM 巡 tool (`tools/t2849_llm_round.py`)・job body (`p3_s4_loop_pegasus.sh`) に `--protocol` / `IZANAGI_S4_T2849_PROTOCOL` を足した。silo は既定のままで、既定時の argv・search_config・genome・header は変えていない。
3. **計算ノードで MOCC の stock と literal 候補が通った。** 系列 1 本 (開始 stock・初期点 5/10 µs・random の探索 1 点・endpoint 再計測) の 5 slot がすべて certified・品質 normal・anomaly 0 で完了し、block 対照 1 slot も certified・normal で参照 slot を作らずに完了した。K0 LLM の MOCC 経路は試験で通したが、計算ノードでは走らせていない。
4. **新事実: 比較 harness の campaign pin は pin 前進の範囲外だった。** 評価入口の campaign pin (`p3_s4_loop.PIN`) は D1936 項 1 で 511c9538 に固定され、pin C への前進 (D2227 項 1・D2236) は D2150 項 1 の ①④⑦ に限られていた。511c9538 の mocc には X/P 計装が無い。D2150 項 1 の「③ 移行する driver は各新系列の着手時」と D2227 項 1 の承認理由 (S2 の X/P 前提は C で足りる) に従い、MOCC の slot だけ campaign pin を C にした。silo は 511c9538 のまま (D1936 項 1、[T-2850] 試走の D2245 と整合)。
5. 規律 1・2 は変えていない。verifier・anomaly 即 reject・Tier0・diff 検疫・意味検査の条件は不変で、意味検査は build する protocol の翻訳単位に合わせただけである。

## 1. 較正 (wave 先頭、コード変更なし)

`tools/pegasus/submit_certify.sh --protocol mocc --rratio {5,50,95}` を pin C の checkout (作業木 HEAD `42d148868`) から投入した。third-party の staging は作業木に無いので、T-2224 §6 と同じく `fetch_third_party.py hydrate` を先に走らせた。

| workload | request | node | 判定 | record | records | 採用点の LLC miss | within-run CV | 雑音床 median (tps) | 所要 |
|---|---|---|---|---|---:|---:|---:|---:|---:|
| write-heavy (rr5) | 29393.nqsv | bnode095 | accepted | `calibration-4b8329b42bb47c65.json` | 1,000,000 | 13.98% | 1.22% | 1,232,915.5 | 186 秒 |
| balanced (rr50) | 29394.nqsv | bnode096 | accepted | `calibration-ae83d7382329999b.json` | 1,000,000 | 14.35% | 0.99% | 817,245.5 | 181 秒 |
| read-heavy (rr95) | 29395.nqsv | bnode098 | accepted | `calibration-7f00a49f493e1015.json` | 1,000,000 | 17.00% | 1.22% | 2,411,110.5 | 216 秒 |

- genome は 3 件とも `mocc|BACK_OFF=1,KEY_SORT=0,TEMPERATURE_RESET_OPT=1`。build argv の `-DCCBENCH_*` は TRACE=0 を含むちょうど 4 件。`pinned_clean=true`、ccbench `head_sha` = C。3 件とも `saturated=false`・`lower_bound_selected=true`・`l3_multiple=4.0`。
- 所要は `job-staging/0:<id>/reservation.json` の `scheduler_started_epoch` から `job-result.json` の `completed_epoch` まで。計 583 秒。
- 旧 pin 511c9538 の mocc rr50 / rr95 record (`calibration-449d0ad22f13e366.json`・`calibration-b3329d93417c76ad.json`) は旧 pin の取得事実として残した (D2150 項 1 (iv))。
- records が S1 と同値なので、`calibrated_perf` の値は変えず、出典の 3 record を同関数の comment に記した (段 4 裁定で `MOCC_RECORDS` 表は作らないとした)。

## 2. 変更の一覧

| file | 内容 |
|---|---|
| `orchestrator/campaign/p3_s4_loop.py` | `backoff_genome(protocol, value)` (silo = 従来の `_BASE` + BACK_OFF=1、mocc = BACK_OFF=1・KEY_SORT=0・TEMPERATURE_RESET_OPT=1、どちらも `BACKOFF_FIXED`) で stock・候補・B-5 sidecar の genome を作る。`campaign_pin_for_protocol` (silo = `PIN` 511c9538、mocc = C の 40 桁 literal、gitlink から導出しない) を campaign 設定・template patch の適用・checkout・清浄性検査に使う。CLI `--protocol {silo,mocc}`、mocc と `--reference-genome` の併用は拒否。`default_cfg` は mocc のときだけ `scale`・`protocol` を search_config に載せる。silo では従来の呼出しの形のまま (`protocol=` を渡さない) |
| `orchestrator/campaign/condition_meaning_gate.py` | `BACKOFF_FIXED` の意味検査を、mocc の評価では owner `cc/mocc/transaction.cc`・target `ycsb_mocc.exe` で行う spec を足した (従来は silo の翻訳単位で代用され、MOCC の実効の証拠にならなかった)。mocc で他の macro を要求したら拒否 |
| `orchestrator/campaign/t2849_comparison_harness.py` | `run-series`・`run-block-controls` に `--protocol`。mocc の header に `protocol`、子 argv に `--protocol mocc`。分類の期待 genome と stock 成立の照合を protocol 対応にした (B-5 module は編集していない)。mocc の block 対照は block-stock だけで reference file・slot を作らず、aggregate の参照 median・参照比は null、stock 比は通常どおり |
| `tools/t2849_llm_round.py` | mocc では coder 文脈の固定 flags・動作点・背景節を MOCC のものにし、hole の axis 名 `silo-backoff-magnitude` が共有 header の marker 名であることを 1 文断る。silo の文脈は不変 |
| `tools/pegasus/p3_s4_loop_pegasus.sh` | harness mode の任意 env `IZANAGI_S4_T2849_PROTOCOL` (silo / mocc)。mocc のときだけ driver argv に `--protocol mocc` を足し、照合する campaign pin を C にする |
| 試験 | `test_t2849_loop_entry.py`・`test_t2849_comparison_harness.py`・`test_t2849_comparison_aggregate.py`・`test_t2849_job_contract.py`・`test_t2849_llm_round.py`・`test_condition_meaning_gate.py` に追加。`test_p3_s4_loop_job_contract.py` は補助関数に ccbench の HEAD を渡す引数を足しただけで既存呼出しの期待は不変 |

規模 (`f72ad2c52` からの追加 / 削除、orchestrator と tools): production と test を合わせて約 380 行追加・60 行削除 (統合 290 / 39、fix 1 35 / 13、fix 2 55 / 10)。

## 3. 段の経過

- **段 2 plan (read-only):** brief の P1〜P6 に賛成。brief の変更面から、harness が B-5 から借りる `_genome`・`_stock_established`・`_header` の silo 固定が漏れていた (放置すると MOCC の slot が stock 不成立で欠測になる)。
- **段 3 相談 2 本:** A (正しさ境界) は、意味検査の `BACKOFF_FIXED` spec が silo の翻訳単位に固定されていて MOCC の候補でも silo の証拠で通る点を must-fix とした。B (実効性・過剰) は、K0 巡 tool の coder 文脈に silo の固定 flags と動作点が残る点と、plan の生死確認手順 (単回 CLI ×2) が既存の job body から起動できない点を must-fix とし、`MOCC_RECORDS` 表・harness 外の mocc 拒否・orphan env 拒否・aggregate の protocol キー化を削るよう求めた。裁定は `verbatim/s4-ruling.md`。cohort の混在は「MOCC は silo と別の cohort 名・root で走らせる」運用とし、拒否検査は足さなかった。
- **ユーザーの計算確認 (D2212 項 4):** 生死確認 2 job を含めて実測単価で約 1.3〜1.7 node 時間 (walltime 上限込みで最大約 2.8) と示し、回答は「生死確認込みで進める (推奨)」(`verbatim/user-compute-confirmation.md`)。
- **段 5 author (Codex):** 1 本、所要約 11 分。
- **段 6 レビュー 2 本:** A は GO (must-fix 0)。should の「T7 が `_require_condition_gate` から protocol が渡ることを検査しない」を採用。B は NO-GO だったが、must-fix 2 件はいずれも変異の帰属の問題で、M4 の変異位置の移動と、期待 node を観測した完全集合で登録する形で解いた。裁定は `verbatim/s6-ruling.md`。
- **焦点走 1 回目の赤 7 件 (自分起因):** `test_p3_s4_loop.py` の既存試験が `default_cfg` を `protocol` を知らない代用関数に差し替え、`_require_condition_gate` に `protocol` 属性の無い genome を渡していた。統合差分が silo 既定の呼出しにも `protocol=` を足していたのが原因で、fix 1 で silo の呼出しを変更前の形に戻した。
- **生死確認で判明した新事実 → 追補裁定 1 と fix 2:** §0 項 4。裁定は `verbatim/s4-ruling-addendum-1.md`。
- **焦点再レビュー 1 本:** GO (must-fix 0)。所見の対応表で closed 6・not-applicable 3・partial 3 (partial はいずれも焦点走・変異の実走待ちで、その後の実走で閉じた)。

## 4. 検査

- 焦点走 (変更 test 6 file・変更 production を参照する consumer test・inventory 4 群、計 58 file): 1 回目 (`955bfed71`、29449.nqsv、Elapse 368 秒) 7 failed / 7,054 passed / 21 skipped → 2 回目 (`3aa390388`、29461.nqsv、191 秒) 7,062 passed / 21 skipped → 3 回目 (`18f379f0d`、29520.nqsv、239 秒) 7,064 passed / 21 skipped / 0 failed。
- 受入全走は記録 commit の後に走らせる (本 insight には書かない)。

## 5. 変異 matrix (DW-M01〜M08)

`tools/mutation_harness.py` (dispatch) で wave 作業木 `18f379f0d` に 12 変異を注入した。対象試験は t2849 系 5 file・`test_condition_meaning_gate.py`・`test_p3_s4_loop_job_contract.py`。基準走は緑 (32 秒)。

| 変異 | 意味 | final の失敗 node 数 | drift 層を引いた残差 |
|---|---|---:|---|
| M1 | mocc の genome に silo の `_BASE` を混ぜる | 8 | T2 (`test_mocc_exact_genomes_and_default_silo_identity`) 1 件 |
| M2 | B-5 sidecar の候補 genome を silo に戻す | 7 | 0 件 (下の補足) |
| M3 | harness の mocc 子 argv から `--protocol mocc` を落とす | 3 | — (p3_s4_loop.py 外) |
| M4 | harness の stock 成立照合で protocol を捨てる (関数本体) | 4 | — |
| M5 | mocc の block 対照で block-reference を測る | 1 | — |
| M6 | 意味検査の mocc spec の owner / target を silo に戻す | 2 | — |
| M7 | 巡 tool の mocc 文脈に silo の固定 flags を書く | 2 | — |
| M8 | job body で `--protocol mocc` を driver に渡さない | 1 | — |
| M9 | job body で protocol 未設定でも mocc 扱いにする | 5 | — |
| M10 | `_require_condition_gate` が意味検査へ protocol を渡さない | 8 | fix 1 の新試験 1 件 |
| M11 | mocc の campaign pin を silo の `PIN` に戻す | 8 | fix 2 の新試験 1 件 |
| M12 | job body が mocc でも silo の `PIN` を照合する | 2 | — |

- probe 1 (`3aa390388`、10 変異、全件 SURVIVED 期待で観測 node を収集) → probe 2 (`18f379f0d`、12 変異) → final (probe 2 の観測 node の完全集合を期待値に登録) で **12 / 12 KILLED・期待 node と完全一致**。
- **drift 層:** `p3_s4_loop.py` は contract-loader の閉包に入っており、未 commit の変異を入れると campaign を組む試験 7 件 (`test_read_heavy_reference_exact_flags` 3 件・`test_harness_machine_slot_accepted` 2 件・`test_reference_identity_and_absent_defaults`・`test_mocc_slot_start_sidecar_genome`) が「disk bytes が HEAD blob と不一致」で意味と無関係に落ちる。M1・M2・M10・M11 の帰属はこの 7 件を引いた残差で判定した。
- **M2 の補足:** 残差が 0 件で drift 層に隠れるため、変異を commit した使い捨ての detached worktree (撤去済み) で T3 と drift 7 件だけを dispatch で走らせた。T3 (`test_mocc_slot_start_sidecar_genome`) の 1 件だけが赤、drift 7 件は緑 (Elapse 13 秒)。この確認は `mutation_harness.py` の外で行ったので、変異台帳の KILLED とは別の証拠として扱う。
- runner の所要 (待ち行列込み): probe 1 411 秒、probe 2 475 秒、final 929 秒 (M3 の 1 件が待ち行列で 467 秒)。

## 6. 計算ノードでの生死確認

submit-tree (job dir 下の detached worktree、`18f379f0d`、ccbench = C) から job body を harness mode で直接 qsub した。cohort 名 `t2849-mocc-liveness-v1`、workload write-heavy、block 1、N_eval 1。台帳・証跡は repo 外の job dir (`dev-wave-jobs/dev-wave-t2849-mocc/liveness/`) に置いた (campaign 成果物は repo へ複製できない)。

**系列 2 (random arm、A = 1・B = 1、29621.nqsv、driver rc 0、Elapse 1,575 秒):**

| slot | BACKOFF_FIXED | 判定 | 品質 | throughput (tps) | anomaly | slot の子の wall |
|---|---:|---|---|---:|---:|---:|
| 開始 stock | −1 (適応) | certified | normal | 1,243,757 | 0 | 332 秒 |
| 初期点 1 | 5 | certified | normal | 794,788 | 0 | 288 秒 |
| 初期点 2 | 10 | certified | normal | 799,041 | 0 | 291 秒 |
| 探索 1 (random) | 169 | certified | normal | 1,206,159 | 0 | 312 秒 |
| endpoint 再計測 | 169 | certified | normal | 1,205,433 | 0 | 320 秒 |

- 系列は `b-complete`、score 1,205,433。genome はすべて `mocc|BACKOFF_FIXED=<v>,BACK_OFF=1,KEY_SORT=0,TEMPERATURE_RESET_OPT=1`、run_cmd は `cc/mocc/ycsb_mocc.exe -thread_num=48 -ycsb_tuple_num=1000000 -extime=3 -clocks_per_us=2100 -ycsb_zipf_skew=0.9 -ycsb_rratio=5 -ycsb_rmw=0 -ycsb_max_ope=10`。campaign の WAL の build 定義は `CCBENCH_BACKOFF_FIXED` が −1・5・10・169 で genome と対応する。
- 値によって throughput が変わる (5・10 µs は stock より約 36% 低く、169 µs は stock に近い) ので、literal の材料化が MOCC の実行に届いていると読める。これは生死確認の 1 回の観測であり、性能の主張ではない (反復なし、同時刻の対照なし)。
- 意味検査は緑の経路で記録を残さない設計なので、owner の選択は計算ノードでは観測していない。試験 (T7・fix 1 の新試験) と変異 (M6・M10) で確かめた。

**block 対照 (29589.nqsv、driver rc 0、Elapse 368 秒):** block-stock 1 session が certified・normal・1,250,439 tps・anomaly 0。reference-genome.json・block-reference slot は作られず、系列は `b-complete`。

**止まった試行 (いずれも driver 未起動か stock slot 1 件で停止、計算の合計は下記に含む):**

| 回 | job | 停止理由 | 対応 |
|---|---|---|---|
| 1 | 29463 / 29473 (各 4 秒) | job body が「repository root must not be inside an AI worktree container」 | submit-tree を `.codex/worktrees` 下から job dir 下へ移した ([T-2850] と同じ置き場) |
| 2 | 29487 / 29488 (7・9 秒) | 「CCBench P3 S4 campaign pin mismatch」 | §0 項 4 の新事実。追補裁定 1 と fix 2 |
| 3 | 29514 / 29516 (21・24 秒) | 「scratch masstree source is not fresh」 | third-party の供給元を `izanagi-thirdparty-cache` の直接指定から submit-tree 内 staging への hydrate に替えた ([T-2850] と同じ) |
| 4 | 29530 (34 秒) | block 対照の stock slot が意味検査の「stock root identity changed after capture」で停止 | 同じ submit-tree の `external/ccbench` を系列 job と同時に stock root にしたため。block 対照を別の submit-tree から再投入 (29589) |
| 4 | 29529 (381 秒) | 開始 stock が certified だが bench の静定判定 (`settled`: 1 分平均 load ≤ 4.0 を最大 20 秒待つ) が未成立で品質 quality-missing → stock 不成立で系列終了 | silo と共通の既存 admission で、MOCC 固有の欠陥ではない ([T-2850] の silo 試走でも探索 slot 1 件が同じ理由で quality-missing)。系列番号 2 で 1 回だけ再投入し通った |

## 7. 計算の費用 (D2212 項 4)

| 区分 | 内訳 | 秒 |
|---|---|---:|
| 較正 | 3 job (reservation 開始〜完了) | 583 |
| 焦点走 | 3 回 (job Elapse) | 798 |
| 変異 | probe 1・probe 2・final の runner 所要 (待ち行列込みの上限) + M2 の補足 13 秒 | 1,828 |
| 生死確認 | 29463・29473・29487・29488・29514・29516・29529・29530・29589・29621 の job Elapse | 2,427 |
| 計 | (受入は記録 commit の後) | 5,636 ≈ 1.57 node 時間 |

ユーザー確認時の見積り (実測単価で約 1.3〜1.7、walltime 上限込みで最大約 2.8) の範囲内。生死確認の止まった試行は計 484 秒 (29529 の 381 秒を含む)。

## 8. 残りと申し送り

- [T-2849] (3) 第 2 プロトコルでの疎通 (20〜40 候補 × 3 workload、検証だけで約 8〜16 node 時間) は未着手。MOCC の slot 1 本は、今回の実測で子の wall が 288〜332 秒 (write-heavy、verify 5 回で約 290 秒) だった。
- MOCC は silo と別の cohort 名・cohort root で走らせる (aggregate は protocol をキーにしていない)。
- MOCC の比較は stock 比で報告し、既知最良の参照が無いことを明記する (D2220 項 6)。
- harness mode を直接 qsub するときの作法 (submit-tree は AI の worktree 置き場の外に job ごとに 1 本、third-party は submit-tree 内 staging へ hydrate) は、段 8 で記載先を決める。

## 所在の移動・撤去 (2026-09-30 追記)

本 insight が投入元として名指す submit-tree `/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2849-mocc/submit-tree` と `submit-tree-b` (detached `18f379f0d`、main の祖先) は、2026-09-30 の掃除 wave で回収せずに撤去する。生死確認の値は本文 §6 にあり、job dir の `liveness/` は撤去しない。
判定の根拠・木ごとの退避の所在・残る写しの一覧は `output/insights/2026-09-30/cleanup-originals-migration/README.md` を正本とする。上の本文は当時の事実として書き換えない (記録された測定・判定は撤去を理由に無効にならない、規律 7)。撤去は同 wave の land の後に行う。
