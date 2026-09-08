# 段 1 brief — dev-wave-acceptance-gitbatch-20260908 (受入全走の高速化: contract-loader binding の git 呼び出し batch 化)

## 実測した現状 (一次資料: /work/1/SFC/tanab/.izanagi-acceptance-shards/*/*/junit.xml、直近 10 日)

- 最遅 shard wall: 中央値 286 秒 / p25 238 / p75 350 (K=3、worker 48)。09-07〜09-08 は 300 秒超が過半。
- 直列総仕事量 W (testcase duration 総和): 09-05 昼 ≈ 15,000 秒 → 09-08 ≈ 25,000〜29,000 秒。
  同じ node 20,873 本の和が 17,091 → 24,247 秒 (+42%)、新規 node の寄与は 1,093 秒だけ。
  「test が増えた」のではなく既存 test が重くなった。増分の主は
  test_autonomous_trial_completeness (+1,269) / test_p3_b4_raw_record_producer (+974) /
  test_p3_b4_closed_critic (+769) / test_trial_registry (+703) / test_layer3_report (+472) / test_campaign / test_p3_s4_loop。
  典型は「11 秒 → 60 秒」「8 秒 → 40 秒」の加法的 +30〜50 秒で、fixture は tmp_path だけ。
- login 単体 profile (`orchestrator/tests/test_p3_b4_raw_record_producer.py::test_m10_empty_red_section_is_rejected_instead_of_marking_both_arms_true`、47.5 秒):
  36.4 秒が `orchestrator/campaign/contract_loader_binding.py:_run_git` (git subprocess 704 回)。
  `_blob` (343 行) が 62 path × 1 process (`git cat-file blob <commit>:<path>`) を、
  `capture_contract_loader_binding` (348 行、5 回) / `verify_committed_contract_loader_binding` (386 行、4 回) /
  `verify_live_contract_loader_binding` (364 行、1 回) のたびに繰り返す。呼び出し元は
  `orchestrator/campaign/artifact_admission.py:999-1022` (`_verify_committed_loader_binding`)、同 `:1103-1118`
  (`_require_verifier_epoch_for_purpose`)、`orchestrator/campaign/ident.py:283-284, 392`、
  `orchestrator/campaign/p3_b4_closed_critic.py:762` (`_load_stable_snapshot` → require_admitted_campaign)。
  計算ノードでは 48 worker が同時に数百の git を fork するので、login より膨らむ。
- 先行 2 wave (09-05 / 09-07) の結論は生きている: collection 固定費 ≈ 59 秒/shard は D1728 (ユーザー裁定) で
  絞り込み不採用、t080 base 70 秒の共有 cache は負結果、不要 test 削除は wall に効かない。今回は触らない。

## scope

- `contract_loader_binding.py` の 62 path 逐次 `git cat-file blob` を、1 process の `git cat-file --batch`
  (stdin に `<commit>:<path>` を 62 行) へ置き換える。`_head_commit` / `_require_commit` は現状維持でよい。
- 返り値 (`ContractLoaderBinding` の commit と digest 辞書) と例外の種類・fail-closed の向きは 1 bit も変えない。
  path ごとの object 不在・型不一致 (`missing` / 非 blob) は従来と同じ `ContractLoaderBindingError` にする。
- `_read_regular_file_no_follow` (158 行、disk bytes) の drift 検査は維持する。
- 呼び出し元 3 module (ident / artifact_admission / p3_b4_wiring_probe) は変更しない。
- 変更面 (実アンカー): `orchestrator/campaign/contract_loader_binding.py:251-421`;
  test 側: `orchestrator/tests/test_artifact_admission.py:2329-2338` (`_run_git` の fake は `(root, *args)` 形。
  kwarg を足すなら `**kwargs` 透過へ)、`orchestrator/tests/test_ccbench_spawn_sites.py:111`
  (spawn site 台帳 `("campaign/contract_loader_binding.py", "<module>._run_git"): 1` — spawn site は `_run_git` 1 か所のまま)、
  `orchestrator/tests/campaign_lock_test_support.py:16` (`_blob(root, commit, relative)` を直接呼ぶ — API 維持)、
  `orchestrator/tests/test_t671_source_binding.py` (所有 test、blob 照合の正負例)。

## 確定済みユーザー裁定 (不変)

- 受入全走 5 分が絶対上限、測定面は D1620 (canonical 起動 receipt の最遅 shard wall)。
- 「開発するほどテストが遅くなる構造を作らない」「リワードハック禁止」「過剰実装・過剰ガードレール無し」。
- D711 / D1728: collection の自 shard 絞り込みは採らない。D1712: 束縛 file の変異は所有 test へ絞る。
- D1139 以降の enforcement source closure 62 path の意味 (exact path 集合と HEAD blob 束縛) は変えない。

## 不変条件

- 受理集合不変: 同一 (commit, path) の blob bytes と記録 digest の exact 照合、disk==blob の drift 検査、
  ambient GIT_* env 拒否、`/usr/bin/git` 絶対 path、`--no-replace-objects` 等の harden 引数、timeout は維持。
- `contract_loader_binding.py` 自身が closure 62 path の一員 (`orchestrator/campaign/campaign_lock.py:68`)。
  未 commit の編集は drift で全 consumer test が赤になる (D1712)。焦点走・受入は commit 後に行い、変異 runner は所有 test へ絞る。
- 凍結成果物の bytes は変わらない (digest は同じ入力の sha256)。DW-O09 の pin 閉包: 本 file の bytes を pin する
  台帳・test は `git grep` で 0 件 (参照は import と spawn site 台帳のみ)。

## 割れうる前提 (親の provisional 裁定・攻撃対象)

- (P1) `git cat-file --batch` の出力 (`<oid> <type> <size>\n<bytes>\n` / `<obj> missing\n`) を path ごとに解析すれば、
  逐次版と同じ path 単位の fail-closed 判定 (不在・非 blob・size 不一致) ができる。
- (P2) `ident.py:283-284` の `capture` → 直後の `verify_live` は同一 binding に対する二重検査で、後者を省いても受理集合は
  変わらない。既定は触らない (scope 外、実測で必要なら次 wave)。
- (P3) process 内 memo `(root, commit, path) → bytes` は git の content-addressing により安全。既定は導入しない
  (batch だけで足りるかを実測で決める)。
- (P4) この +30〜50 秒/test は計算ノード上でも同じ原因である (login profile からの推定。受入の A/B で確かめる)。

## 成果物

- 実装 diff (Codex author)、所有 test の更新/追加、変異 matrix (所有 test へ絞る)、
  login 単体 A/B (同 test の所要)、受入全走 1 走の wall と対象 module W (改修前分布との位置)、insight README、
  worklog / decisions fragment。

## 分割方針

- 実装子 1 本 (unit A: batch 化 + test)。正しさ防壁 (campaign lock authority の一部) に触るので段 2 プラン・段 3 敵対相談・
  段 6 レビュー 2 本は省かない。
