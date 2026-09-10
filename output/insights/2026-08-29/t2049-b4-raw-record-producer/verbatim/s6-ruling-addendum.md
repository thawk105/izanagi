# [T-2049] 段 6 レビュー裁定 (段 4 裁定への追補)

段 6 の敵対レビュー 2 本 (sol = 正しさ境界、luna = 変異帰属と実効性) の所見を裁定する。
**両レーンが独立に同じ最重要欠陥へ到達した** (assembly が転記して再導出しない)。real 認定する。

## must-fix (成果物影響を書けるもの)

### A. assembly は転記でなく**再導出**する (sol#1、luna#1。両レーン一致)

- **欠陥:** 最終組立てが、事前確定 path に置かれた source artifact の判断値
  (`treatment_fired` / `contaminated` / `protocol_ok` / `execution_disposition` /
  `throughput` / `assignment_observation`) を**無検証で転記**する。
  publish 経路を通さず canonical な file を planned path へ先置きすれば、
  `evidence` も receipt も欠いたまま任意の判断値を注入できる。
  production と consumer を両方 stub にしても certified 正例が緑になる。
- **成果物影響:** 証拠未検証の arm を B-4 の受理集合へ入れ、verdict を任意方向へ動かせる。
- **裁定:** **assembly は source artifact に記録された証拠 pointer から判断値を自ら再導出し、
  記録値と一致することを要求する。** 一致しなければ拒否する。
  証拠が読めない・欠けている場合も拒否する (§D の例外を除く)。
  これは新しい署名や nonce を作らず、**既に記録済みの証拠 bytes を読み直すだけ**である。
  D162 決定 4「consumer は decision を入力として受け取らず、trusted validator を
  同一呼出し内で再実行する」の要求そのものである。段 4 裁定 §2.85 を assembly へも及ぼす。
- assembly は非保証 tuple の実在も要求する (sol#7)。

### B. 終端性の判定を締める (sol#2、sol#3、luna#7)

- **欠陥 (B-1):** flock は `run_campaign()` の内側しか覆わない。authorization・preflight・
  quarantine・checkpoint は外側なので、実行中でも lock を取得でき、
  実行中の arm を不可逆な欠測として封印できる。
- **欠陥 (B-2):** 終端 WAL の durable 化から `save_loop_state()` までの**正規の window** で
  producer を呼ぶと、古い checkpoint から `checkpoint_ok=false` / `whiteboard_result=null` を
  publish し、正常な COMMIT を protocol failure へ封印する。後の再実行は path 衝突になる。
- **成果物影響:** 実行中の arm が missing に固定され、正常 COMMIT が protocol violation になる。
  block score・欠測数・verdict が変わる。
- **裁定:**
  - **終端 record があっても、checkpoint が終端と整合するまで publish しない。**
    loop state が終端 iteration に追いついていなければ「まだ確定していない」として
    **deferred を返す** (publish しない)。`checkpoint_ok=false` を publish して封印しない。
  - 終端 record 不在で lock 取得可の経路では、**lock 取得後に WAL を読み直し、
    取得前と同一であることを確認する。** 変わっていれば deferred。
  - **B-1 の残余は閉じない。** `p3_s4_loop.py` の lock 範囲変更は本 wave の scope 外
    (編集禁止 file)。**非保証へ逐語で書く** — 「flock は campaign 実行の内側区間しか覆わず、
    その外側で実行中の campaign を終了と誤判定しうる」。裁定パッケージへ追加する。

### C. `treatment_fired` の恒真を潰す (sol#5)

- **欠陥:** 判定が「赤節 header の有無」だけを見ている。structured rejection が 0 件でも
  on digest は `# rejections` と「rejection なし」を含むため、**両 arm が常に true** になる。
- **成果物影響:** treatment 未発火の block が n 件に数えられ、判定不能になるべき publication が
  検定へ進む。
- **裁定:** header ではなく**赤詳細の実体 (4 クラスのいずれかの entry) の実在**で判定する。
  on は実体があること、off はその実体が無いことを要求する。
  実体が 0 件の block は事前登録の適格性述語 (§5.1.1) を満たさないので、
  true にせず構造化拒否とする。

### D. 証拠欠落で行を落とさない (sol#4)

- **欠陥:** 終端 WAL と receipt がある campaign で launch sidecar 等が欠けると、
  `protocol_ok=false` を記録する前に `EVIDENCE_UNAVAILABLE` が返り、planned path が空のまま
  assembly が `INCOMPLETE_SET` で止まる。
- **成果物影響:** protocol violation の campaign が全件報告から消える (file-drawer)。
- **裁定:** **終端 record が実在する試行は必ず artifact を残す。**
  補助証拠の欠落・schema 破損は `protocol_ok=false` として記録し、
  欠けた証拠の種類を構造化して artifact に書く。行を落とすことを禁じる。
  §B の deferred (まだ確定していない) と、本項の「確定したが証拠が欠けた」を混同しない。

### E. driver を束縛する (luna#2)

- **欠陥:** manifest の `driver` が source binding へ転記されるだけで、campaign / receipt の
  `driver_kind` と一度も照合されない。別 driver の有効な pair を任意の manifest row へ供給できる。
- **成果物影響:** 事前固定した母集合とは別 driver の試行が受理集合へ混入し、verdict と
  driver 別報告の帰属が変わる。
- **裁定:** manifest row の `driver` と、launch sidecar / receipt の `driver_kind` の
  対応を検査する。不一致は拒否する。

### F. symlink 拒否を全証拠へ及ぼす (sol#6)

- **欠陥:** receipt bundle 外の `evidence_executable_path` と role file が
  symlink 追従 reader で読まれる。
- **成果物影響:** 再現不能な executable provenance が `protocol_ok=true` の artifact へ流れる。
- **裁定:** 段 4 裁定 §2.85(b) の symlink 拒否を**推移的に**適用する。

### G. 変異の帰属を実効 gate へ再照準する (luna 変異表、DW-M01)

luna の検証で、実効的に一意なのは **M04・M16・M18・(publish 層限定の) M12 の 4 点だけ**。

- **到達不能 (前段が同じ入力を先に拒否):** M02、M08。
- **検出不能 (登録 node が機構を pin していない):** M01、M03、M05、M13、M17。
- **複数 node が落ちる:** M06、M07、M09、M10、M11、M14、M15。

**裁定:** DW-M01 に従い、到達不能・検出不能の 7 点は**そのまま登録しない**。
実効 gate へ再照準し、その変異が到達する位置で**ちょうど 1 node が落ちる**ように test を置き直す。
複数 node が落ちる 7 点は、赤理由が単一である限り登録を維持してよい (DW-M03)。
ただし **M10 の逆向き変異 (両 arm を一律 true) が全新規 test を通過する**ことは
§C の恒真と同じ穴なので、これを kill する node を必ず置く。

### H. テスト時間 (親の実測。レビュー所見ではない)

- **実測:** 新規 test file 単独で **897 秒 (14分57秒)**。内訳は
  `test_positive_201_block_certified_preserves_decimal_and_all_pair_protocol_bindings` が **619.80s**、
  `test_positive_201_block_all_terminal_records_absent` が **614.80s**。
  残り 20 node は call が約 7s 以下で、うち 18 node が共有 setup に約 6.7s ずつ払っている。
  **2 node が全体の 99% を占める。**
- **規律:** ユーザー裁定の絶対上限は**テストスイート全体で 5 分** (pegasus 計算ノード占有時)。
  単独 file で 15 分は明確な違反であり、このままでは land できない。
- **コスト class:** `EXPECTED_BLOCK_COUNT = 201` は凍結定数なので **O(1) (repo 成長に非比例)**。
  「履歴に比例」型ではない。したがって恒久保留の対象ではなく、**直して通す**案件である。
- **裁定:** 保留・除外・skip を既定の答えにしない (それは検査を消して緑を買う形)。
  **繰り返し払っている不変コストを 402 回のループから外す。**
  1 arm あたり約 1.5 秒は、hash・filesystem 操作にしては大きい。
  projection closure manifest の再計算、role file の再 hash、
  module 一覧の再走査など、**402 回とも同じ結果になる計算**を特定して 1 回に畳む。
  共有 setup も 18 回払わずに済む scope へ移す。
  **実 evidence を減らす方向 (201 block のうち一部を軽い偽物にする) は採らない。**
  所見 A が assembly の再導出を要求するため、証拠は 402 件とも本物でなければならない。
- **目標:** 新規 test file 単独で **120 秒以下**。60 秒以下が望ましい。
  所見 A の再導出を入れると重くなる方向なので、両方を入れたうえで測ること。
  120 秒に届かない場合は、**残ったコストの内訳を測って報告せよ。**
  黙って受け入れるな。除外や skip で数字を作るな。

## nit として扱う (must-fix にしない)

- production の 2 個の `assert` が直前条件から含意されて恒真 (sol nit2)。
  → 除去するか、含意されない位置へ移す。成果物影響は書けないので nit。
- D1240 の固定 absence digest を producer が使わず、lock 不在を先に拒否する (sol nit3)。
  → **欠陥ではない。** 正式 B-4 campaign は marker を持つ lock が必須であり、
  lockless な campaign は B-4 標本になりえない。拒否は D1240 の受理集合より狭いが、
  狭い方向であり規律 2 と両立する。**ただしその旨を docstring に明記する**こと。
- luna nit の十進 token・揮発値・M14 の同期点は問題なし。指摘なし。

## 裁定パッケージへの追加 (scope 外)

4. **campaign lock の保持範囲。** advisory flock が campaign 実行の内側区間しか覆わないため、
   producer は「実行中か終了済みか」を確実には判定できない。閉じるには
   `orchestrator/campaign/p3_s4_loop.py` の lock 範囲を変える必要があり、本 wave の編集禁止面である。

## 親が実走する既存 test (luna の名指し)

- `test_plain_runner_coverage.py::test_every_test_file_is_self_runnable_or_allowlisted`
- `test_campaign_import_invariant.py` の 3 node
- `test_campaign.py::test_certified_writer_authorization_caller_inventory_is_closed`
- `test_t1286_commit_receipt.py::test_production_commit_producer_census_is_exactly_five`
- `test_ccbench_spawn_sites.py::test_reviewed_process_launch_inventory_is_recursive_and_exact`
- `test_s8b_floor_campaign.py::test_materializer_registry_covers_all_python_build_launches`
- `test_p3_s4_loop.py::test_backoff_coder_text_materialization_ingress_is_closed_and_nonempty`
- `test_p3_b4_analysis_path.py::test_public_evaluate_analysis_production_caller_inventory_is_pinned_not_closed`
- `test_pytest_collection_config.py::test_permanent_exclusion_table_has_no_other_verifier_or_oracle_tests`
