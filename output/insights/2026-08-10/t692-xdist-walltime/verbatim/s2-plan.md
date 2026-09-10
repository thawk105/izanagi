結論は、D63 の単一 `real-repo` groupを維持したまま、group 内の実行順を変えて二つの receipt 解決を重ねる案を推します。T-438 と R3 の s8c 3 node まで canonical group に収容しても、受入 wall は実測値ベースで約 **876 秒**まで下がる見込みです。

今回は read-only の静的調査だけで、変更・pytest 実走・緑判定はしていません。

## 653.50 秒の機序

これは待ちではなく、pytest session 内で二回目の production T-080 receipt 解決を別プロセスが丸ごと実行しています。

- 対象テストは子スクリプト内で production の `campaign.s8b_oracle_driver` だけを import し、`driver.main()` を呼びます。[test_s8b_oracle_driver.py:3040](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t692-r3-xdist-walltime/orchestrator/tests/test_s8b_oracle_driver.py:3040)
- `subprocess.run()` に `env=` がないため xdist run ID 自体は継承され得ますが、子は `real_repo_receipt_memo` を import も patch もしません。[test_s8b_oracle_driver.py:3063](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t692-r3-xdist-walltime/orchestrator/tests/test_s8b_oracle_driver.py:3063)
- session cache は `_session_cache_path()` が環境から自動注入される仕組みではありません。`real_repo_receipt()` が明示的に呼ばれた場合だけ参照されます。[real_repo_receipt_memo.py:89](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t692-r3-xdist-walltime/orchestrator/tests/real_repo_receipt_memo.py:89) [real_repo_receipt_memo.py:144](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t692-r3-xdist-walltime/orchestrator/tests/real_repo_receipt_memo.py:144)
- production resolver を memo へ向ける唯一の配線は `mock.patch.object(driver, "_resolve_t080_receipt", ...)` です。これは親 Python process の module object だけを変更し、exec された子には伝播しません。[real_repo_receipt_memo.py:171](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t692-r3-xdist-walltime/orchestrator/tests/real_repo_receipt_memo.py:171) [real_repo_receipt_memo.py:180](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t692-r3-xdist-walltime/orchestrator/tests/real_repo_receipt_memo.py:180)
- 子の `run_block()` は production `_resolve_t080_receipt()` を呼び、そこから直接 `verify_receipt()` に入ります。[s8b_oracle_driver.py:1056](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t692-r3-xdist-walltime/orchestrator/campaign/s8b_oracle_driver.py:1056) [s8b_oracle_driver.py:97](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t692-r3-xdist-walltime/orchestrator/campaign/s8b_oracle_driver.py:97)

したがって、653.50 秒側は session-cache の `flock` 待ちではありません。新 interpreter なので migration module の process-local blob cacheも空から始まります。

確定できないのは、653.50 秒のうち receipt 解決、子起動、I/O・CPU競合がそれぞれ何秒かという内訳です。ただし「共有 cache を待つだけ」ではなく、production verifier を独立に一回実行することはコード上確定です。

## 680.23 秒の機序

こちらは session cache 初期化 barrier です。

- 対象 node は明示的に `patch_driver_resolver()` を掛けてから `run_block()` に入ります。[test_s8b_binding_driftguards.py:248](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t692-r3-xdist-walltime/orchestrator/tests/test_s8b_binding_driftguards.py:248) [test_s8b_binding_driftguards.py:267](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t692-r3-xdist-walltime/orchestrator/tests/test_s8b_binding_driftguards.py:267)
- cache は xdist run ID と HEAD で共有されます。[real_repo_receipt_memo.py:98](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t692-r3-xdist-walltime/orchestrator/tests/real_repo_receipt_memo.py:98)
- 全 worker は同じ lock file に対して排他的 `flock` を取り、lock を保持したまま cache load、production 解決、保存まで行います。[real_repo_receipt_memo.py:150](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t692-r3-xdist-walltime/orchestrator/tests/real_repo_receipt_memo.py:150)
- 直列実験で先行 node が解決済みなら当該 node は 2.08 秒です。全走との差は `680.23 - 2.08 = 678.15` 秒で、固有処理ではありません。[s1-measurement.md:40](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t692-r3-xdist-walltime/s1-measurement.md:40)

従ってこの node が同期している対象は、「同じ xdist session の最初の production receipt 解決が終わり、pickle cache が公開されること」です。

ただし現存資料には lock owner の PID・node ID が記録されていません。当該 node 自身が lock ownerとして解決したのか、別 worker が ownerで当該 node が `flock` で待ったのかは区別できません。確定できるのは、680 秒が同じ cache 初期化 critical section に帰属し、node 固有の仕事量は約2秒だという点までです。

## 案1 — 同一 group 内の順序で二解決を重ねる（推奨）

### 変更箇所

1. [conftest.py:129](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t692-r3-xdist-walltime/orchestrator/tests/conftest.py:129) の `REAL_REPO_SERIAL_NODES` に以下を追加します。

   - `test_ruleops.py::test_real_checkout_independent_maximum_package_and_runner_preflight`
   - s8c candidate の3関数：
     - `test_candidate_freeze_matches_contract_and_generation_chain`
     - `test_candidate_is_not_effective_and_has_zero_satisfied_predicates`
     - `test_wave_files_do_not_contaminate_production_holdout_scan`

2. [test_ruleops.py:2032](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t692-r3-xdist-walltime/orchestrator/tests/test_ruleops.py:2032) の直接 decorator を削除します。残すと collection hook が既存 marker を検出して canonical marker を付けないためです。[conftest.py:246](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t692-r3-xdist-walltime/orchestrator/tests/conftest.py:246)

3. [test_ruleops.py:2036](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t692-r3-xdist-walltime/orchestrator/tests/test_ruleops.py:2036) の手書き before/after status を、[repo_tree_util.py:74](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t692-r3-xdist-walltime/orchestrator/tests/repo_tree_util.py:74) の `assert_repo_tree_unchanged()` で inventory action 全体を包む形へ変えます。これで `--untracked-files=all` を含む D63 の snapshot 契約も閉じます。

4. [test_s8c_preregistration_invariant.py:29](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t692-r3-xdist-walltime/orchestrator/tests/test_s8c_preregistration_invariant.py:29) の独自 group 定数と、[同:124](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t692-r3-xdist-walltime/orchestrator/tests/test_s8c_preregistration_invariant.py:124)、[同:190](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t692-r3-xdist-walltime/orchestrator/tests/test_s8c_preregistration_invariant.py:190)、[同:206](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t692-r3-xdist-walltime/orchestrator/tests/test_s8c_preregistration_invariant.py:206) の decorator を削除します。個別 test の git 処理や時間予算は変更しません。

5. [conftest.py:234](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t692-r3-xdist-walltime/orchestrator/tests/conftest.py:234) 付近に、次の collection 優先順を定数として置き、[同:241](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t692-r3-xdist-walltime/orchestrator/tests/conftest.py:241) の hook で stable reorder します。

   1. ungrouped の session-cache payer  
      `test_oracle_pipeline_contract_keyword_is_mandatory_positive_control`
   2. `real-repo` 内の独立 subprocess node  
      `test_cli_subprocess_returns_rc_2_on_gate_refused`
   3. `real-repo` 内の cache barrier  
      `test_run_block_broken_binding_manifest_refuses_and_writes_nothing`
   4. 残りは現行相対順を維持

これにより、canonical worker はまず独立 CLI 解決を実行します。同時に別 worker が共有 cache 解決を開始し、次の binding node が barrier になります。barrier 通過後にだけ `real-repo` の writer 群へ進むため、D63 の writer-reader 排他は弱まりません。

### wall 見積り

記号は次のとおりです。

- CLI独立解決 `C = 653.50`
- 共有 cache 完了の実測 proxy `M = 671.55`
- binding cache-hit 本体 `B = 2.08`
- 現行残り `R = 55.07`
- T-438 `H = 69.45`
- s8c candidate群 `S = 58.35`
- 現行 scheduler余剰 `δ = 1407.97 - 1388.80 = 19.17`

T-438 だけを canonical 化する場合：

- 順序変更なし：下界 `1388.80 + 69.45 = 1458.25` 秒
- 順序変更込みの projection：  
  `max(C,M) + B + R + H = 798.15` 秒
- `δ` を足した期待 wall：約 **817.32 秒**

R3 の s8c 3 node も canonical 化する推奨完全形：

- 順序変更なし：下界 `1388.80 + 69.45 + 58.35 = 1516.60` 秒
- cache が CLI 終了時までに用意される理想床：  
  `C + B + R + H + S = 838.45` 秒
- 現行671.55秒帯を cache-ready proxy にした projection：  
  `max(C,M) + B + R + H + S = 856.50` 秒
- `δ` を足した期待 wall：約 **875.67 秒**

つまり T-438 と s8c を単純に寄せるだけでは約128秒悪化しますが、二つの receipt 解決を重ねることで、最終的には現行1407.97秒から約532秒、37.8%短縮できます。

並行 wave が receipt 解決を短縮した場合、完全形の式は概ね  
`max(C', M') + 184.95 + δ` になります。二解決を重ねるため、短縮効果は二重加算ではなく遅い方の短縮量として現れます。

### 正しさと受理集合

- canonical group から外す node はありません。T-438 と s8c readerを追加するだけです。
- CLI・共有 payer・binding barrier の間は reader-reader です。writer は同じ group の barrier 後なので同時実行されません。
- production は0 byte不変です。既存テストの assertion も、T-438 の snapshotを共有D63 helperへ強化する以外は不変です。
- 収集 node の集合は「従来集合 + 新meta-test」だけであることを、group suffixを除いた node ID digestで照合します。
- s8c の3 nodeは同一 workerに残るため、session fixtureによる candidate commit 一回生成も維持されます。

## 案2 — runner が full suite 前に session cache を prewarmする

### 変更箇所

- [real_repo_receipt_memo.py:68](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t692-r3-xdist-walltime/orchestrator/tests/real_repo_receipt_memo.py:68) に runner生成の session UIDを受ける専用環境変数を追加。
- [tools/run_tests.py:367](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t692-r3-xdist-walltime/tools/run_tests.py:367) 付近に prewarm helperを追加。
- [tools/run_tests.py:1859](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t692-r3-xdist-walltime/tools/run_tests.py:1859) の pytest起動前に、full-suite shapeだけ一回解決し、同じ UIDをworkerへ継承。

D63上は pytest writer開始前の readなので安全です。cache keyには session UIDとHEADを残し、prewarm失敗は実解決へ黙って倒さずrunnerをfail-closedにすべきです。

完全R3形の見積りは、

`427.58 prewarm + 838.45 group + 19.17余剰 = 約1285.20秒`

です。約123秒しか短縮せず、runner・recording・dispatchの環境伝播面を増やします。案1より明確に劣るため不採用とします。

## 案3 — reader/shared・writer/exclusive の cross-worker flockへ置換

### 変更箇所

- 新規 `orchestrator/tests/real_repo_access_lock.py:1` に xdist run ID単位の reader/writer lockを実装。
- [conftest.py:126](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t692-r3-xdist-walltime/orchestrator/tests/conftest.py:126) の一集合を reader/writer二集合へ分類し、autouse fixtureで test setupからteardownまで `LOCK_SH` / `LOCK_EX` を保持。
- [test_real_repo_serialization.py:352](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t692-r3-xdist-walltime/orchestrator/tests/test_real_repo_serialization.py:352) に分類の独立goldenとlive排他試験を追加。

理論下界は  
`max(671.55, 653.50, 16534.55/48) = 671.55` 秒、現行余剰込みで約 **690.72秒**です。T-438とs8c readerも並行化できます。

ただしこれはD63の保証機構そのものを置き換えます。D63は bareな reader/writer group分割を明示的に却下しています。[decisions.md:2420](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t692-r3-xdist-walltime/docs/decisions.md:2420) 採るなら最低でも以下が必要です。

- reader-readerが実際に重なるlive control
- reader-writer、writer-writerが重ならないpositive control
- worker crash時のlock解放
- lock path不明・open失敗時のfail-closed
- subprocess存続中も親fixtureがlockを保持する検査
- reader/writer分類の完全一致golden
- lock無効化変異で競合を再現するnegative control

性能は最良ですが、分類漏れ一件で偽緑を作るため本waveでは落とします。

## 収集監査 meta-test

現行監査は canonical nodeについては positional `real-repo` 一個を厳密検査していますが、golden外では `mark["args"]` 内の `"real-repo"` しか見ません。[test_real_repo_serialization.py:419](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t692-r3-xdist-walltime/orchestrator/tests/test_real_repo_serialization.py:419) そのため `kwargs={"name":"real_repo"}` は見えません。[同:427](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t692-r3-xdist-walltime/orchestrator/tests/test_real_repo_serialization.py:427)

[test_real_repo_serialization.py:352](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t692-r3-xdist-walltime/orchestrator/tests/test_real_repo_serialization.py:352) を次のように強化します。

- 全 collected item の全 `xdist_group` markerを対象にする。
- 許容形を「positional文字列1個、kwargs空、marker最大1個」に固定。
- 独立 group-name goldenを完全一致で持つ。推奨案後は `real-repo` と `dev-waves-runtime` のみ。
- `REAL_REPO_SERIAL_NODES` と独立node goldenの一致、および全parameter instanceが exact canonical markerを一個持つことを維持。
- collection report上の優先node射影が `payer → CLI → barrier` であることを固定。
- 抽出述語をhelper化し、以下の合成負例が必ず赤になるpositive controlを加える。
  - `xdist_group(name="real_repo")`
  - `xdist_group("real_repo")`
  - `xdist_group(name="real-repo")`
  - group marker二個
  - 未登録group名
- [test_real_repo_serialization.py:585](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t692-r3-xdist-walltime/orchestrator/tests/test_real_repo_serialization.py:585) のlive scheduler controlに、同workerだけでなく group内実行順と、payer singleton / CLI groupの同時開始を記録する対照を足す。

## 親が行う検証

実装後に親が実走すべき順序です。

1. 収集監査とsynthetic scheduler control。
2. T-438、s8c 3 node、CLI、binding barrierの対象走。
3. `-n 2` と受入同形48 workerで、reader/writer競合の反復。
4. baselineと同じJUnit計測形で、次を確認。
   - `real_repo` と `s8c-preregistration-candidate` groupが消える
   - CLIがcanonical group先頭、bindingがその次
   - binding durationが約2秒、またはCLI終了までの残待ちだけになる
   - `real-repo` 直列和が約838〜857秒帯
5. JUnitを付けない正式な受入全走を別実行する。
6. marker kwargs、underscore名、優先順反転、canonical node削除、二重markerの変異が各meta-testに検出されることを確認する。
7. リポジトリ規律どおり関連検査、`check_codex_agents.py`、`check_docs.py`、commit後provenance監査を親が行う。

## やってはいけない案

- `_NPROC_CAP` や `default_test_jobs` の引き上げ：計算ノードでは既に affinity全数48 workerです。[run_tests.py:206](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t692-r3-xdist-walltime/tools/run_tests.py:206) [site_policy.py:122](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t692-r3-xdist-walltime/orchestrator/campaign/site_policy.py:122) `16534.55/48=344.47` より `real-repo=1388.80` が大きいため、worker増加では下界が動きません。
- `DEFAULT_WALLTIME` の単独引き上げ：2400秒の期限を延ばすだけで、1408秒の消費を縮めません。[dispatch_compute.py:28](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t692-r3-xdist-walltime/tools/pegasus/dispatch_compute.py:28)
- CLI nodeやreaderを別groupへ出すだけの案：writerとの相互排他が消え、D63違反です。
- 同一nodeへ二個目のgroup markerを足す案：xdistがgroup名を結合し、canonical groupとは別scopeになります。
- CLI子へmemo patchを持ち込んで速くする案：個別テスト内容の短縮であり本waveの所有外です。
- `_any_history_touches_path` やs8c git timeoutの変更：それぞれ並行waveの所有です。

## 総括

- **653.50秒:** production CLI子がtest支援memoを通らず、T-080 receiptをsession内で二回目に独立解決していることは確定。shared-cache待ちではない。653.50秒の細かな時間内訳は未確定。
- **680.23秒:** session-cacheの排他critical sectionへの同期で、固有処理は直列実測2.08秒。cache公開を待つnodeかlock owner自身かは既存資料では識別不能だが、同じcache初期化barrierへの帰属は確定。
- **推す案:** canonical groupを分割せず、`payer → CLI → binding barrier → 残り`へcollection順を固定し、T-438とs8c 3 nodeをcanonical化する。期待wallは約 **875.67秒**。T-438だけなら約 **817.32秒**。
- **却下:** serial prewarmは約1285秒で利得が小さい。reader/writer flock化は約691秒を狙えるがD63保証機構の置換リスクが大きい。並列度・walltime引き上げ、bareなgroup分割、排他解除は効果不足または正しさ違反。
- **親briefの誤り:** 実質的な誤りはない。P4は実測で確定した。M5の「653秒は二重払いか未検証」は今回コード経路で二重払いと確定した。補足として、現行meta-testは「golden一致しか見ない」わけではなくcanonical nodeのmarker形は厳密検査済みで、実際の穴はgolden外markerのkwargs・非canonical名の抽出にある。