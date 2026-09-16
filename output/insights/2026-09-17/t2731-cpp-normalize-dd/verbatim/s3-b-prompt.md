単独段 dispatch: stage=consult; sandbox=read-only; parent=/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2731-cpp-normalize-dd/s1-brief.md

## 必読事項の射影

次の絶対パスを読む。**この射影に挙げた file が読めなければ即停止**する。これは射影 file 限定の
停止規則であり、自分が推測して探した path が不在でも停止理由にしない。

- `/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2731-cpp-normalize-dd/s1-brief.md`
  — 親 brief (scope、不変条件、前提実測 F-1〜F-4、(P1)(P2))。**brief 自身も検査対象**
- `/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2731-cpp-normalize-dd/s2-plan-prompt.md`
  — 段 2 の依頼 (親が plan 子に何を要求したか)
- `/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2731-cpp-normalize-dd/s2-plan-out.md`
  — 段 2 plan 子の起草 (検査対象)
- `/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2731-cpp-normalize-dd/verbatim-rulings.md`
  — 既裁定 (第 20 回 rulings 項 2)、F1016、D34、insight §8、親の前提実測 script と出力の逐語
- `/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2731-cpp-normalize-dd/orchestrator/campaign/source_digest.py`
  — 変更対象 (`_cpp_normalize` :1646-1676、`_normalize_contexts` :1686、`_dump_macros` / `_environment_macros` :1702-1745、`_merge_defines` :902、`_worktree_defines` / `_head_defines` :2071-2097、`compute` / `baseline` :2116 / :2212、`_trace_pair_diff` / `assert_trace_diff_matches_head` :2150-2210)
- `/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2731-cpp-normalize-dd/orchestrator/tests/test_campaign.py`
  — source_digest 系 test (:11040-11335、:11470 `_FAKE_BACKOFF_HH`、:11541 `_fake_ccbench_repo`、:11790-11910、:12169-12200、:12561-12600)
- `/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2731-cpp-normalize-dd/orchestrator/tests/test_ccbench_spawn_sites.py`
  — spawn site 登録簿 (:289 `_cpp_normalize: 1`)
- `/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2731-cpp-normalize-dd/orchestrator/tests/test_skip_classification.py`
  — 静的 call 数登録簿
- `/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2731-cpp-normalize-dd/tools/check_trace0_preprocess_identity.py`
  — `_cpp_normalize` の repo 外 consumer (:583-596)
- `/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2731-cpp-normalize-dd/docs/dev-wave/mutation.md`
  — 変異走行の契約 (DW-M01〜M08)
- `/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2630-scan-boundary-reach/mutation-spec.json`
  — T-2630 の 8 変異 spec (修正前の期待署名)
- `/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2731-cpp-normalize-dd/output/insights/2026-09-16/t2630-scan-boundary-reach/README.md`
  — F1016 の実測記録 (§3 測り方、§4 結果表、§9 再現 recipe)

上記以外に repo 内を読んでよい。`external/ccbench/` 配下、`tools/mutation_harness.py`、`orchestrator/campaign/campaign_lock.py`
(enforcement source の blob 束縛 :80-100)、`orchestrator/qualification/contract.py` (:60-80)、`orchestrator/tests/test_t671_source_binding.py`、
`orchestrator/campaign/mocc_trace_pair.py`、`tools/pegasus/mocc_trace_v1_policy.json`、`docs/decisions.md`、`docs/failures.md` は一次資料である。

## レンズ B — 整合・実効性・変異の帰属

plan を守らず検査する。**親 brief 自身も検査対象**である。消費側との整合、test / pin の連鎖、変異登録の帰属、scope の境界を攻める。

1. **consumer 取り残し。** `_cpp_normalize` / `_normalize_contexts` / `canonical_source_preimage_bytes` の全 consumer
   (repo 内 `git grep`、`tools/`、`hooks/`、docs の手順) を列挙し、plan が見ていないものを挙げる。
   `check_trace0_preprocess_identity.py` の report (normalized の sha256) を消費する `mocc_trace_pair.py` の validator が
   凍結値と live 比較していないか。docs (`docs/orchestrator-design.md` 等) に `-E -P` の記述があり是正が要るか
   (docs-only の整合は親が行う。列挙だけでよい)。
2. **pin の連鎖。** `source_digest.py` は campaign_lock / qualification contract / T-671 の enforcement source として
   HEAD blob で束縛される。修正 commit 後に赤になる test・受入経路 (contract-loader drift、`test_t671_source_binding`、
   `test_t126_pegasus_tools`)、および「commit 前に焦点走すると赤」の順序制約を列挙する。`test_ccbench_spawn_sites` の
   登録簿と `test_skip_classification` の call 数を plan の実装形が触るかを現物で判定する。
   `orchestrator/tests/acceptance_duration_ledger.json` に新 test の登録が要るか (`tools/run_tests.py` の契約)。
3. **変異登録の帰属 (DW-M01 / M03 / M04 / M08)。** plan の source-level 変異 (`-dD` を外す / prefix 剥がしを外す /
   `startswith` を恒真化 / comment-only) の各々について、(a) 期待 node が完全集合か、(b) 赤理由が一つに絞れるか
   (同じ入力を拒否する他層が無いか — 例: prefix 剥がしを外すと inert 供給形が赤になるが `test_source_digest_stock_roundtrip`
   も同時に赤になり、期待集合に入れるべきか)、(c) 修正前 HEAD で新 test のどの node が赤になるか (テスト強化の新旧両走、
   DW-M08 末尾)。T-2630 recipe v2 の期待署名 (M3b / M6 / M4 / M4b: 4 node、M3a: N1b+N2b、M1 / M2 / M0 不変) を
   carrier の変異内容と probe test の 4 node の主張から独立に導き、親と plan の予測と突き合わせる。
4. **recipe 再走の実効性。** probe branch (wave tip + `a519a7560` + `e35fb7c4e` の cherry-pick) で harness を走らせる形が、
   (a) probe test が期待どおり fix 後の `source_digest` を呼ぶか (import 経路)、(b) `mutation_harness` の固定 HEAD 束縛・
   `--expected-spec-sha256` の扱い、(c) 計算ノードの compiler (`compilers_for_current_site`、g++-13 系) で `-dD` の prefix 形が
   login と違っても stock 判定が保たれるか、(d) 所要 (T-2630 は 10 request 8 分 34 秒) と dispatch envelope
   (`timeout_seconds` 8100 / `hang_timeout_seconds` 3000、D612 の override) の整合、を検査する。
   **再走を省いて unit test だけで足りるという主張があるなら、その根拠と失うものを書く。**
5. **scope の境界。** 「本題の 1 箇所と consumer の整合だけ。gate・検査・台帳・一般化の追加は scope 外」に対し、plan が
   暗黙に新機構 (新 helper、新 registry、新 CLI flag、cache の新 API) を足していないか。足しているなら最小形を示す。
6. **親 brief への反論。** (P1)(P2)、F-1〜F-4、成果物・変更面の実アンカー (file:line)、受入・実測環境の指定を現物で検査し、
   食い違いを書く。無ければ「無し」。

## 禁止

- gate・検査・台帳・一般化の新設を提案しない。裁定 (a) を (b)(c)(d) に差し替える提案をしない。規律 2 を緩める方向を書かない。
- commit・push・file の書き込みをしない。テストの実走を成功条件にしない — **pytest 緑を要求しない。静的検査でよい。**
  親が実走する。実走していないものを緑と書かない。

## 出力形式

Markdown。次の H2 節をこの順で必ず置く。所見は 1 件ずつ `B-1`, `B-2`, … と番号を付け、各件に
**根拠 (file:line)**・**real と主張する理由**・**是正案 (scope 内 / scope 外)** を書く。

## 所見 (real 候補)
## consumer と pin の連鎖
## 変異登録の帰属 (source-level / recipe v2)
## recipe 再走の実効性
## 親 brief への反論
## 総括

予算が尽きそうなら、途中までの結論をこの出力形式どおりに書いて終える。**無出力が最悪である。**
