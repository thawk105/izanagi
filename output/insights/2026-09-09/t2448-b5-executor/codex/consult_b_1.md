## file:line の実在

1. `real` — 新規成果物の行参照はすべて現時点では実在しない予定行である。

   - 現在の `orchestrator/axis_b5_search/` は [__init__.py:1](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2448-b5-executor/orchestrator/axis_b5_search/__init__.py:1) と [catalog.py:1](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2448-b5-executor/orchestrator/axis_b5_search/catalog.py:1) だけで、`parsers.py`、`preflight.py`、`runner.py`、`anchor_registry.json`、3 schema、fixture directory、executor test は未実在である。
   - したがって [plan_1.md:7](/home/SFC/tanab/.claude/jobs/33fc4cd7/tmp/dev-wave-t2448-b5-executor/plan_1.md:7)、[plan_1.md:53](/home/SFC/tanab/.claude/jobs/33fc4cd7/tmp/dev-wave-t2448-b5-executor/plan_1.md:53)、[plan_1.md:122](/home/SFC/tanab/.claude/jobs/33fc4cd7/tmp/dev-wave-t2448-b5-executor/plan_1.md:122) などの範囲は locator ではなく見積りである。
   - 影響: 行番号を mutation anchor やレビュー対象指定に使うと、実装後のずれで別コードを指す。
   - 是正: 実装指示では関数名と exact replacement bytes を使い、行番号は完成後に振り直す。これは現段階では `nit`。

2. `real` — 軸 1 の `verify_registration` API を誤って写している。

   - 実物は [validator.py:749](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2448-b5-executor/orchestrator/axis1_search/validator.py:749) で、必須位置引数は `registration_commit, catalog_path, registration_paths`、`repo_root` は keyword-only である。
   - プランは [plan_1.md:56](/home/SFC/tanab/.claude/jobs/33fc4cd7/tmp/dev-wave-t2448-b5-executor/plan_1.md:56) で `verify_registration(registration_commit, repo_root)` としている。また軸 1 は `VerificationResult` を返すだけで、seal record を生成しない ([validator.py:820](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2448-b5-executor/orchestrator/axis1_search/validator.py:820))。
   - 影響: 写経すると TypeError、または schema が要求する seal record 不在で受入が赤になる。
   - 是正: B5 固有 API として設計し、軸 1 と「同じ」なのは Git blob 比較の一部だけと明記する。

3. `real` — 全走を起動する production surface が無い。

   - プランは leaf 単位の `run_leaf` までしか列挙していない ([plan_1.md:122](/home/SFC/tanab/.claude/jobs/33fc4cd7/tmp/dev-wave-t2448-b5-executor/plan_1.md:122)-[130](/home/SFC/tanab/.claude/jobs/33fc4cd7/tmp/dev-wave-t2448-b5-executor/plan_1.md:130))。
   - 凍結停止条件は索引順・query ID 辞書順で 1622 query、control、補助探索を全走することを要求する ([部分登録 §5.3:608](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2448-b5-executor/docs/related-work/claim-survey/2026-09-07-backoff-axis-b5-search-preregistration.md:608))。
   - 影響: leaf の単体試験は緑でも、実行記録を生成する入口がなく値は一件も得られない。
   - 是正: `runner.py` 内に登録全体を順序づけて走らせる公開入口を置くか、本 wave を「leaf evaluator」に改称し、実行器完成を主張しない。

4. `real` — live preflight の発行器と runner への証拠束縛がない。

   - 計画されているのは request builder、response classifier、既成 records の集約だけである ([plan_1.md:93](/home/SFC/tanab/.claude/jobs/33fc4cd7/tmp/dev-wave-t2448-b5-executor/plan_1.md:93)-[116](/home/SFC/tanab/.claude/jobs/33fc4cd7/tmp/dev-wave-t2448-b5-executor/plan_1.md:116))。
   - runner がどの create-only live record を検証するか、registration commit、30 member、run ID とどう結ぶかがない。軸 1 のように任意 `bool` を preflight として受ける先例 ([runner.py:1519](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2448-b5-executor/orchestrator/axis1_search/runner.py:1519)-[1523](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2448-b5-executor/orchestrator/axis1_search/runner.py:1523)) を写すと容易に迂回できる。
   - 影響: `passed=True` の合成値だけで、DBLP が `不達` でも本走 request を出せる。
   - 是正: production 入口は schema-valid な durable live record を自ら読み、exact member set と registration seal を照合する。object/bool 注入は test-only 関数に限定する。

5. `refuted` — その他の先例 locator は実在する。

   - parser dataclass は [parsers.py:14](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2448-b5-executor/orchestrator/axis1_search/parsers.py:14)、policy loader は [runner.py:292](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2448-b5-executor/orchestrator/axis1_search/runner.py:292)、provenance 判定は [check_ai_provenance.py:1536](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2448-b5-executor/tools/check_ai_provenance.py:1536)、self-run 判定は [test_plain_runner_coverage.py:35](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2448-b5-executor/orchestrator/tests/test_plain_runner_coverage.py:35) にある。
   - ただし [check_docs.py:6614](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2448-b5-executor/tools/check_docs.py:6614) は単なる `main` wrapper であり、プランの checker 説明を支える locator ではない。
   - 影響: 前者はなし。`check_docs.py:6614` の誤引用は `nit`。
   - 是正: docs path 検査の根拠は [check_docs.py:6673](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2448-b5-executor/tools/check_docs.py:6673)-[6740](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2448-b5-executor/tools/check_docs.py:6740) を指す。

## 凍結文との照合

1. `refuted` — page size、retry、host、member 数、lookup request 形は一致する。

   - page size は arXiv 200、OpenAlex 200、DBLP 100 ([部分登録 §3.3:245](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2448-b5-executor/docs/related-work/claim-survey/2026-09-07-backoff-axis-b5-search-preregistration.md:245)-[259](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2448-b5-executor/docs/related-work/claim-survey/2026-09-07-backoff-axis-b5-search-preregistration.md:259))。
   - retry は 3 回、3→6→12 秒 ([部分登録 §5.3:611](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2448-b5-executor/docs/related-work/claim-survey/2026-09-07-backoff-axis-b5-search-preregistration.md:611))。
   - member は 16 / 1 / 13 ([閉包登録 1/2 §2.4(a):167](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2448-b5-executor/docs/related-work/claim-survey/2026-09-08-backoff-axis-b5-closure-preregistration.md:167)-[171](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2448-b5-executor/docs/related-work/claim-survey/2026-09-08-backoff-axis-b5-closure-preregistration.md:171))。
   - lookup request 3 形も [閉包登録 1/2 §2.4(b):175](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2448-b5-executor/docs/related-work/claim-survey/2026-09-08-backoff-axis-b5-closure-preregistration.md:175)-[179](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2448-b5-executor/docs/related-work/claim-survey/2026-09-08-backoff-axis-b5-closure-preregistration.md:179) と一致する。
   - 影響: これらの定数には是正不要。

2. `real` — `G2-08` の主キーを誤記している。

   - プランは `1710.11258` を「主キー」とする ([plan_1.md:89](/home/SFC/tanab/.claude/jobs/33fc4cd7/tmp/dev-wave-t2448-b5-executor/plan_1.md:89))。
   - 凍結 record の主キーは DOI `10.1137/17M1154679` で、`1710.11258` は preprint alias である ([閉包記録 §1.2:76](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2448-b5-executor/docs/related-work/claim-survey/2026-09-08-backoff-axis-b5-closure-record.md:76)-[86](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2448-b5-executor/docs/related-work/claim-survey/2026-09-08-backoff-axis-b5-closure-record.md:86))。
   - 影響: alias record と索引 lookup key が混同され、実行記録の anchor identity が凍結 record と食い違う。
   - 是正: DOI を主キー、`1710.11258` を arXiv lookup key として別 field にする。

3. `real` — `PAGINATION` の値は逐語ではなく、軸 1 evaluator とも非互換である。

   - [plan_1.md:164](/home/SFC/tanab/.claude/jobs/33fc4cd7/tmp/dev-wave-t2448-b5-executor/plan_1.md:164)-[168](/home/SFC/tanab/.claude/jobs/33fc4cd7/tmp/dev-wave-t2448-b5-executor/plan_1.md:168) は `"start"` / `"cursor"` / `"f"` を pagination kind と呼ぶ。
   - 凍結文が固定するのは parameter 名と遷移であり、この内部 enum ではない。軸 1 validator が受ける kind は `"offset"` / `"cursor"` だけである ([validator.py:313](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2448-b5-executor/orchestrator/axis1_search/validator.py:313)-[335](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2448-b5-executor/orchestrator/axis1_search/validator.py:335))。
   - 影響: evaluator を写すと arXiv と DBLP の全 page が `pagination_kind_unknown` になる。
   - 是正: `POSITION_PARAMETER={"arxiv":"start","dblp":"f"}` と `PAGINATION_KIND={"arxiv":"offset","openalex":"cursor","dblp":"offset"}` を分ける。

4. `real` — 短い非最終 page を条件 2 でも落とすのは凍結文と違う。

   - プランは条件 2 に `silent_truncation` を置く ([plan_1.md:180](/home/SFC/tanab/.claude/jobs/33fc4cd7/tmp/dev-wave-t2448-b5-executor/plan_1.md:180)-[182](/home/SFC/tanab/.claude/jobs/33fc4cd7/tmp/dev-wave-t2448-b5-executor/plan_1.md:182))。
   - 凍結 §5.1 の条件 2 は位置連続性だけで、実要素数は条件 3 で判定する ([部分登録 §5.1:541](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2448-b5-executor/docs/related-work/claim-survey/2026-09-07-backoff-axis-b5-search-preregistration.md:541)-[550](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2448-b5-executor/docs/related-work/claim-survey/2026-09-07-backoff-axis-b5-search-preregistration.md:550))。
   - 影響: overall はどちらも未完走だが、実行記録の条件 2 が登録外の `否` になり、変異の帰属も二重になる。
   - 是正: 短 page は条件 3 だけで拒否する。

5. `real` — DBLP cutoff の実装が欠落している。

   - 凍結 §2.2 は全年取得後、`year <= 2026` を client 側で判定し、欠落は除外せず `要裁定` とする ([部分登録 §2.2:123](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2448-b5-executor/docs/related-work/claim-survey/2026-09-07-backoff-axis-b5-search-preregistration.md:123)-[127](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2448-b5-executor/docs/related-work/claim-survey/2026-09-07-backoff-axis-b5-search-preregistration.md:127))。
   - プランは year の parse と欠落保持だけで、2027 年以後を登録取得集合から外す処理を持たない ([plan_1.md:35](/home/SFC/tanab/.claude/jobs/33fc4cd7/tmp/dev-wave-t2448-b5-executor/plan_1.md:35)、[plan_1.md:174](/home/SFC/tanab/.claude/jobs/33fc4cd7/tmp/dev-wave-t2448-b5-executor/plan_1.md:174)-[200](/home/SFC/tanab/.claude/jobs/33fc4cd7/tmp/dev-wave-t2448-b5-executor/plan_1.md:200))。
   - 影響: DBLP の受理集合と unique count が cutoff 外 record を含み、RW3 の母集合が変わる。
   - 是正: raw occurrence は消さず、cutoff 判定と取得集合への採否を別 field で記録する。欠落・不正年は `要裁定` 側に残す。

6. `real` — content type、timeout、Accept header、redirect、retry 対象の値は凍結されていない。

   - 凍結条件 6 は「期待どおり」としか書かない ([部分登録 §5.1:562](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2448-b5-executor/docs/related-work/claim-survey/2026-09-07-backoff-axis-b5-search-preregistration.md:562)-[564](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2448-b5-executor/docs/related-work/claim-survey/2026-09-07-backoff-axis-b5-search-preregistration.md:564))。
   - プラン自身も content type、30 秒 timeout、retry 対象、redirect を未裁定と認める ([plan_1.md:392](/home/SFC/tanab/.claude/jobs/33fc4cd7/tmp/dev-wave-t2448-b5-executor/plan_1.md:392)-[401](/home/SFC/tanab/.claude/jobs/33fc4cd7/tmp/dev-wave-t2448-b5-executor/plan_1.md:401))。それにもかかわらず `RequestSpec` に exact Accept header を要求し ([plan_1.md:134](/home/SFC/tanab/.claude/jobs/33fc4cd7/tmp/dev-wave-t2448-b5-executor/plan_1.md:134))、未知 header の拒否 test まで予定している ([plan_1.md:367](/home/SFC/tanab/.claude/jobs/33fc4cd7/tmp/dev-wave-t2448-b5-executor/plan_1.md:367))。
   - 影響: author の便宜値が実行時受理集合を決め、後付け契約になる。
   - 是正: author 着手前にユーザー裁定へ返す。D1895 はこれらの値を供給していない。

7. `real` — OpenAlex 終端規則と DBLP の中間形は未解決のままである。

   - 凍結文は OpenAlex にも「位置 + 実要素数 == 総件数」を書くが cursor は加算不能 ([部分登録 §5.1:544](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2448-b5-executor/docs/related-work/claim-survey/2026-09-07-backoff-axis-b5-search-preregistration.md:544)-[552](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2448-b5-executor/docs/related-work/claim-survey/2026-09-07-backoff-axis-b5-search-preregistration.md:552))。プランの `next_cursor == null` と累積数規則は合理的だが逐語ではない ([plan_1.md:395](/home/SFC/tanab/.claude/jobs/33fc4cd7/tmp/dev-wave-t2448-b5-executor/plan_1.md:395))。
   - DBLP の `total > 0` だが exact DOI が無い応答も、凍結 3 値のどれにも分類されない ([閉包登録 1/2 §2.4(b):173](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2448-b5-executor/docs/related-work/claim-survey/2026-09-08-backoff-axis-b5-closure-preregistration.md:173)-[185](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2448-b5-executor/docs/related-work/claim-survey/2026-09-08-backoff-axis-b5-closure-preregistration.md:185))。
   - 影響: 同じ応答が実装裁量で `非収録` または `不達` になり、走行開始可否が変わる。
   - 是正: どちらも実装子へ選ばせず、裁定対象として停止する。

8. `real` — anchor 包含 control と 61 stream が実行器から落ちている。

   - lookup は収録確認であって包含 control ではない ([閉包登録 1/2 §2.4:157](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2448-b5-executor/docs/related-work/claim-survey/2026-09-08-backoff-axis-b5-closure-preregistration.md:157)-[165](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2448-b5-executor/docs/related-work/claim-survey/2026-09-08-backoff-axis-b5-closure-preregistration.md:165))。包含は検索後に各 member が登録枝の和集合へ入ったかを判定する ([同:189](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2448-b5-executor/docs/related-work/claim-survey/2026-09-08-backoff-axis-b5-closure-preregistration.md:189)-[202](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2448-b5-executor/docs/related-work/claim-survey/2026-09-08-backoff-axis-b5-closure-preregistration.md:202))。
   - プランは lookup preflight だけを実装し、包含 evaluator がない。また 61 stream を明示的に次 wave へ送る ([plan_1.md:404](/home/SFC/tanab/.claude/jobs/33fc4cd7/tmp/dev-wave-t2448-b5-executor/plan_1.md:404))。
   - 影響: `all(anchor control)` と補助探索完走を評価できず、RW3 は成立しない。
   - 是正: 本 wave を registration-only と明記するか、包含 evaluator、61 stream、axis-level 集約まで成果物へ戻す。

## 既存検査との衝突

1. `refuted` — `check_docs.py` への新規 schema/fixture 登録は不要である。

   - checker は列挙済み living docs と runbook を対象にし ([check_docs.py:145](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2448-b5-executor/tools/check_docs.py:145)-[169](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2448-b5-executor/tools/check_docs.py:169))、その文書内の path 実在性を検査する ([check_docs.py:6732](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2448-b5-executor/tools/check_docs.py:6732)-[6740](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2448-b5-executor/tools/check_docs.py:6740))。
   - 今回の新規 non-doc file を別 registry へ足す契約は見当たらない。
   - 影響: なし。凍結文へ path を追記しないという結論は正しい。
   - 是正: なし。

2. `refuted` — provenance 判定の理解は正しい。

   - `orchestrator/` 配下の非 Markdown/RST は実装面である ([check_ai_provenance.py:1536](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2448-b5-executor/tools/check_ai_provenance.py:1536)-[1549](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2448-b5-executor/tools/check_ai_provenance.py:1549))。
   - 影響: Python、JSON schema、fixture、test、台帳を含む commit に Codex author trailer が無ければ履歴監査が赤になる。
   - 是正: プランどおり D95 の Codex author 帰属を付ける。

3. `refuted` — `pytest.main([__file__])` なら README allowlist 追記は不要である。

   - self-run 判定は `__main__` 後方の `pytest.main` を signal として認識する ([test_plain_runner_coverage.py:25](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2448-b5-executor/orchestrator/tests/test_plain_runner_coverage.py:25)-[41](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2448-b5-executor/orchestrator/tests/test_plain_runner_coverage.py:41))。
   - 既存 B5 catalog test も同じ形式である ([test_axis_b5_search_catalog.py:636](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2448-b5-executor/orchestrator/tests/test_axis_b5_search_catalog.py:636))。
   - 影響: README へ追加すると逆に stale/self-runnable allowlist test が赤になる。
   - 是正: harness を維持し、README は触らない。

4. `real` — brief の「台帳欠落で受入が赤」は事実と違う。

   - 台帳 loader は不在・壊れた ledger を空 mapping として fail-soft に扱う ([conftest.py:1456](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2448-b5-executor/orchestrator/tests/conftest.py:1456)-[1477](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2448-b5-executor/orchestrator/tests/conftest.py:1477))。
   - 検査は全 node の exact 登録ではなく、real collection の 90% 以上という aggregate である ([test_acceptance_schedule_order.py:660](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2448-b5-executor/orchestrator/tests/test_acceptance_schedule_order.py:660)-[714](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2448-b5-executor/orchestrator/tests/test_acceptance_schedule_order.py:714))。
   - 現台帳は `nodeid_count=22157` ([acceptance_duration_ledger.json:22161](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2448-b5-executor/orchestrator/tests/acceptance_duration_ledger.json:22161))。
   - 影響: 台帳を更新しなくても新 test の欠落それ自体は個別赤にならず、brief の受入予測が誤る。aggregate 90% を跨げば別理由で赤になりうる。
   - 是正: 台帳を成果物に含めるなら、プランどおり緑 JUnit に `--add-only` を使う。README 変更は不要。

5. `refuted` — 現在確認できる repo-wide scan に B5 固有の追加登録はない。

   - `test_s8b_repo_scan_invariant.py` は全 repo を対象にするが、検出対象は YCSB の read-ratio、skew、RMW 三軸の同一 file 内 conjunction である ([s8b_holdout_freeze.py:68](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2448-b5-executor/orchestrator/campaign/s8b_holdout_freeze.py:68)-[79](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2448-b5-executor/orchestrator/campaign/s8b_holdout_freeze.py:79)、[test_s8b_repo_scan_invariant.py:21](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2448-b5-executor/orchestrator/tests/test_s8b_repo_scan_invariant.py:21)-[35](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2448-b5-executor/orchestrator/tests/test_s8b_repo_scan_invariant.py:35))。
   - 予定 B5 語彙や live fixture はこの三軸を含まない。
   - 影響: 現プランの名前・内容だけでは既知 hit allowlist の追加は不要。
   - 是正: 実装後の full test で確認するだけでよい。

## 実装量と削り方

`real` — 2 単位での完遂見積りは過小である。

軸 1 の実物は parser 395 行、runner 2455 行、validator 1901 行、checkpoint 668 行、runner test 2911 行、schema 1950 行で、fixture も 2361 行ある。合計は約 1.3 万行である。B5 は縮小しても次の規模になる。

- parser: 400〜500 行
- preflight: 450〜650 行
- runner/evaluator/output: 1400〜2200 行
- 3 schema と anchor registry: 800〜1300 行
- 約 40 test: 1500〜2500 行
- 25 fixture: minify しなければ数千行

合計は概ね 5500〜9000 authored lines と fixture bytes であり、2 author 単位では実装よりレビューと負例の整合が先に破れる。

registration preflight だけを閉じる最小化は次である。

| 削り方 | 残すもの | 失うもの |
|---|---|---|
| mutation 候補を #3/#5/#10 のみにする | production code、基本負例、registration seal | 実行記録値・受理集合・RW3 は失わない。開発時の弱体化検出範囲だけが狭くなる |
| parser fixture を minified な決定的 bytes にし、40 test を各条件の識別可能な正負例へ約 18 本に畳む | 3 parser、条件 1〜6、seal、schema | 実行記録値・RW3 は失わないが、索引別の診断バリエーションを失う |
| live preflight と `anchor_registry.json` を次 wave へ送る | parser、runner、schema、registration binder | registration §5.3(a) の技術的 rc=0 は作れるが、brief の 30 lookup 条件と §0(b) は失う |
| checkpoint、61 stream、包含 control を削る | leaf executor と registration seal | 実行記録の完走性とRW3を失う。後続追加で runner bytes が変わるため、今回の seal は最終 seal ではなくなる |

最後の行を削った状態で「B5 実行器完成」または「registration closure 完了」と書くのは不適切である。今 wave を本当に 2 単位へ収めるなら、成果物名を「registration-preflight prototype」に弱め、最終 seal は checkpoint と全 stream 実装後にやり直すべきである。

## 所有分割

1. `refuted` — 列挙された編集 path 自体は素集合である。

   - A は parser と fixture ([plan_1.md:461](/home/SFC/tanab/.claude/jobs/33fc4cd7/tmp/dev-wave-t2448-b5-executor/plan_1.md:461)-[466](/home/SFC/tanab/.claude/jobs/33fc4cd7/tmp/dev-wave-t2448-b5-executor/plan_1.md:466))。
   - B は registry、preflight、runner、schema、test、台帳 ([plan_1.md:468](/home/SFC/tanab/.claude/jobs/33fc4cd7/tmp/dev-wave-t2448-b5-executor/plan_1.md:468)-[477](/home/SFC/tanab/.claude/jobs/33fc4cd7/tmp/dev-wave-t2448-b5-executor/plan_1.md:477))。
   - `__init__.py` は双方とも触らず、台帳と schema は B だけである。
   - 影響: path-level merge collision はない。
   - 是正: export が必要と判明した場合の `__init__.py` 所有者を B と先に固定する。

2. `real` — 実装単位としては独立していない。

   - B の schema/test/preflight は A が後から確定する parse error code、dataclass fields、fixture exact set に依存する ([plan_1.md:450](/home/SFC/tanab/.claude/jobs/33fc4cd7/tmp/dev-wave-t2448-b5-executor/plan_1.md:450)-[459](/home/SFC/tanab/.claude/jobs/33fc4cd7/tmp/dev-wave-t2448-b5-executor/plan_1.md:459))。
   - brief は「各単位が自分の test」を要求するが ([brief.md:67](/home/SFC/tanab/.claude/jobs/33fc4cd7/tmp/dev-wave-t2448-b5-executor/brief.md:67)-[68](/home/SFC/tanab/.claude/jobs/33fc4cd7/tmp/dev-wave-t2448-b5-executor/brief.md:68))、A は test path を一つも所有しない。
   - 影響: 並列着手すると B が仮の型・fixture manifest で実装し、統合時に schema/test が赤になる。
   - 是正: A を先行完了させて immutable な型表、error-code enum、fixture manifest を渡す。並列性が必要なら A 専用 parser test file を別 path として所有させる。

## 変異の帰属

mutation harness は失敗 node 集合が expected node 集合と完全一致したときだけ `KILLED` とする ([mutation_harness.py:2097](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2448-b5-executor/tools/mutation_harness.py:2097)-[2099](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2448-b5-executor/tools/mutation_harness.py:2099))。したがって [plan_1.md:411](/home/SFC/tanab/.claude/jobs/33fc4cd7/tmp/dev-wave-t2448-b5-executor/plan_1.md:411)-[424](/home/SFC/tanab/.claude/jobs/33fc4cd7/tmp/dev-wave-t2448-b5-executor/plan_1.md:424) の「expected node を一つだけ」は、他 test も赤になる変異では成立しない。

| # | 判定 | 理由、影響、是正 |
|---:|---|---|
| 1 | `real`、登録しない | `actual_count` 変更は parser 値 test、短 page の条件 2/3、distinct total に波及する。赤集合が一意でない。索引別かつ直接 field だけを検査する別変異へ分割する |
| 2 | `real`、登録しない | fixed step と actual count の差を出すには短 page が必要で、その同じ入力を条件 3 が拒否する。実行受理は変わらない。parser の `position_out` 単独契約を測る場合だけ別候補にする |
| 3 | `refuted`、登録可 | 初回 `*` と `%2A` は catalog の `first_page_url` bytes で単独識別できる。影響は初回 OpenAlex request bytes。exact builder test 一本へ限定する |
| 4 | `real`、登録しない | catalog-only 再構築との完全比較が未知 host を先に拒否する ([plan_1.md:142](/home/SFC/tanab/.claude/jobs/33fc4cd7/tmp/dev-wave-t2448-b5-executor/plan_1.md:142)-[151](/home/SFC/tanab/.claude/jobs/33fc4cd7/tmp/dev-wave-t2448-b5-executor/plan_1.md:151))。suffix allowlist を緩めても production 受理集合が変わらない |
| 5 | `refuted`、登録可 | OQO 配列内の同一 child 反復は重複 JSON key ではなく、条件 1 の多重度だけが拒否理由になる。実行記録の条件 1 を直接検査する |
| 6 | `real`、登録しない | duplicate occurrence があれば distinct ID 数は occurrence 数より小さい。条件 3 が宣言総数を occurrence 数へ結ぶ限り、条件 5 も必ず拒否する。「C5 mismatch が出ない同数 fixture」は構成不能 |
| 7 | `real`、登録しない | occurrence 数と distinct 数の差を出すには duplicate が必要で、条件 4 が先に拒否する。overall rejection の帰属は条件 4/5 に分かれる |
| 8 | `real`、現 fixture では登録しない | 201 件の terminal page の total だけ変えると、条件 3 の最終式も同時に破れる。3 page とし、非最終 page だけ total を drift させ、最終 page は `400+1=401` にすれば条件 5 だけへ分離可能 |
| 9 | `real`、そのまま登録しない | delay tuple から 6 を削ると sleep 列と attempt 数を同時に変える。`6.0 -> 7.0` の置換なら timing だけへ帰属できる |
| 10 | `refuted`、登録可 | exact 30 member、29 `収録`、1 `不達` とすれば member count は通り、`all -> any` だけが開始可否を変える |
| 11 | `real`、登録しない | path set から fixture を削ると、exact directory scan がその fixture を extra として fail-closed にするか、registration 正例全体を赤にする。seal 弱体化を示さない。代わりに一つの non-catalog fixture の byte equality 比較だけを外す変異を使う |
| 12 | `real`、現方針では登録しない | automatic redirect 無効なら production transport は off-host final URL を返す前に 3xx を失敗させる。fake response だけを殺す dormant test になる。redirect 裁定後、production 到達可能なら再評価する |

安全に残せるのは #3、#5、#10。#8 は fixture を再設計すれば候補になる。

## 親 brief への反論

1. `real` — P1 の理由は現物と逆である。

   - 軸 1 の `FROZEN_PREDECESSOR_PATHS` は事前登録、実行記録、insight directory の三つだけで、`axis1_search/parsers.py` を含まない ([validator.py:20](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2448-b5-executor/orchestrator/axis1_search/validator.py:20)-[25](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2448-b5-executor/orchestrator/axis1_search/validator.py:25))。
   - B5 の予定 `REGISTERED_PATHS` にも軸 1 parser は無い ([plan_1.md:62](/home/SFC/tanab/.claude/jobs/33fc4cd7/tmp/dev-wave-t2448-b5-executor/plan_1.md:62)-[80](/home/SFC/tanab/.claude/jobs/33fc4cd7/tmp/dev-wave-t2448-b5-executor/plan_1.md:80))。
   - したがって import すると自動的に seal が結合するのではなく、軸 1 parser が変わっても B5 preflight が通る未束縛依存になる。
   - 影響: B5 の parser 意味論が無検出で変わり、実行記録値と受理集合が変わる。
   - 是正: 自前 parser という結論は維持できるが、理由を「B5 固有 field/API と未束縛依存の回避」に直す。import するならその path を B5 seal へ明示追加する。

2. `real` — P2 の「軸 1 runner は catalog policy を必ず読む」は誤りである。

   - 軸 1 は content type、page size、pagination、retry の全てに fallback を持つ ([runner.py:307](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2448-b5-executor/orchestrator/axis1_search/runner.py:307)-[357](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2448-b5-executor/orchestrator/axis1_search/runner.py:357))。
   - B5 catalog に `index_policies` がないこと自体は正しい ([catalog.py:435](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2448-b5-executor/orchestrator/axis_b5_search/catalog.py:435)-[462](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2448-b5-executor/orchestrator/axis_b5_search/catalog.py:462))。
   - 再利用不能の本当の理由は、軸 1 が `logical_queries` と別の RequestSpec/ParsedPage 契約を要求すること ([runner.py:360](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2448-b5-executor/orchestrator/axis1_search/runner.py:360)-[367](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2448-b5-executor/orchestrator/axis1_search/runner.py:367))、および B5 の `get_rows=="200"`、実要素数、全 header 保存が非互換なことである。
   - 影響: 誤った理由で写経範囲を決めると、fallback や軸 1 固有 API を混入させる。
   - 是正: P2 の結論は維持し、理由を catalog/API/完走述語の非互換へ置き換える。

3. `real` — P3 は registration closure を最終化できない。

   - 凍結文は窓をまたぐ実行に機械可読 checkpoint を要求する ([部分登録 §5.3:616](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2448-b5-executor/docs/related-work/claim-survey/2026-09-07-backoff-axis-b5-search-preregistration.md:616)-[617](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2448-b5-executor/docs/related-work/claim-survey/2026-09-07-backoff-axis-b5-search-preregistration.md:617))。
   - 軸 1 の先例だけでも checkpoint/WAL は 668 行あり、request 発行前 WAL、outcome unknown、resume action を扱う ([checkpoint.py:1](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2448-b5-executor/orchestrator/axis1_search/checkpoint.py:1)-[6](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2448-b5-executor/orchestrator/axis1_search/checkpoint.py:6)、[checkpoint.py:207](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2448-b5-executor/orchestrator/axis1_search/checkpoint.py:207)-[250](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2448-b5-executor/orchestrator/axis1_search/checkpoint.py:250))。
   - 影響: 中断後の再開で重複発行や欠落を判定できず、完走記録を作れない。後で runner へ足すと今回 seal した bytes が変わる。
   - 是正: P3 を scope 外にするなら今回の seal を「暫定」とし、最終 registration preflight は checkpoint 統合後に再実施する。

4. `real` — DW-O13 の DBLP 一般化が強すぎる。

   - brief は「DBLP 13 member は不達」と実測値のように書く ([brief.md:58](/home/SFC/tanab/.claude/jobs/33fc4cd7/tmp/dev-wave-t2448-b5-executor/brief.md:58)-[60](/home/SFC/tanab/.claude/jobs/33fc4cd7/tmp/dev-wave-t2448-b5-executor/brief.md:60))。
   - 凍結 record は anchor 固有 request を一件も送っておらず、共有 endpoint の probe からの外挿だと明記する ([閉包記録 §2:102](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2448-b5-executor/docs/related-work/claim-survey/2026-09-08-backoff-axis-b5-closure-record.md:102)-[106](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2448-b5-executor/docs/related-work/claim-survey/2026-09-08-backoff-axis-b5-closure-record.md:106)、[§6:243](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2448-b5-executor/docs/related-work/claim-survey/2026-09-08-backoff-axis-b5-closure-record.md:243)-[245](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2448-b5-executor/docs/related-work/claim-survey/2026-09-08-backoff-axis-b5-closure-record.md:245))。
   - 影響: live preflight の要求値を「構造的に到達不能」と誤認し、現在の 13 request を実行する意味を失わせる。
   - 是正: 「2026-09-07 の共有 endpoint probe は当該 host から `不達`。13 member の exact live 値は未観測」と書く。実行器は現在値を得て fail-closed にする。

5. `refuted` — D1895 から語彙を緩めない結論は正しいが、未登録 transport 値の決定権までは与えない。

   - D1895 の逐語は登録どおり走らせ、走行前の語彙 amendment を行わないことである ([rulings-verbatim.md:41](/home/SFC/tanab/.claude/jobs/33fc4cd7/tmp/dev-wave-t2448-b5-executor/rulings-verbatim.md:41)-[50](/home/SFC/tanab/.claude/jobs/33fc4cd7/tmp/dev-wave-t2448-b5-executor/rulings-verbatim.md:50))。
   - 影響: vocabulary、枝、cutoff を変えない点は維持されるが、timeout や content type を親の便宜で固定する根拠にはならない。
   - 是正: 未確定値は別のユーザー裁定へ返し、D1895 の射程として処理しない。

## 総括

段 2 プランはこのまま author へ渡せない。主要 blocker は次の六つである。

- DBLP cutoff 判定が無く受理集合が変わる。
- live preflight は発行器も durable 証拠束縛もなく、迂回可能である。
- anchor 包含 control、61 stream、全走入口、checkpoint がないため RW3 を評価できない。
- OpenAlex 終端、content type、timeout、Accept、redirect、DBLP 中間形が未裁定である。
- `PAGINATION` enum が軸 1 evaluator と非互換である。
- 2 単位に対して実装・fixture・test 量が過大である。

path 所有は素集合で、page size、retry、host、16/1/13 membership、lookup request 形は正しい。最低でも未裁定値を親の便宜で埋めず、成果物を registration-only の暫定段へ縮めるか、全実行面を追加して最終 seal を後ろへ移す必要がある。

本検証は指定どおり静的検査のみで、ファイル変更、git、pytest、network は行っていない。