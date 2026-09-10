## 停止点の全列挙

新規 bundle root は呼出側が作成する必要はない。親は「存在せず、親 directory に書込み可能な絶対 path」を選ぶだけでよい。CLI の registration preflight 後、runner 自身が `mkdir(parents=True)` するため、新規 root で落ちない（[run_axis1_search.py:127](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2090-openalex-fetch/tools/run_axis1_search.py:127)、[runner.py:1603](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2090-openalex-fetch/orchestrator/axis1_search/runner.py:1603)）。

1 leaf の経路は次のとおり。

1. CLI が `--query-id` を受け、checkpoint が無ければ `run_leaf` を呼ぶ（[run_axis1_search.py:38](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2090-openalex-fetch/tools/run_axis1_search.py:38)、[run_axis1_search.py:157](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2090-openalex-fetch/tools/run_axis1_search.py:157)）。
2. registration は `HEAD == registration_commit`、登録 path の clean、catalog blob、旧凍結物を検査する（[validator.py:749](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2090-openalex-fetch/orchestrator/axis1_search/validator.py:749)）。
3. runner が bundle root、`state/runtime.json`、WAL directory を順次自動作成する（[runner.py:1608](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2090-openalex-fetch/orchestrator/axis1_search/runner.py:1608)、[runner.py:629](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2090-openalex-fetch/orchestrator/axis1_search/runner.py:629)、[checkpoint.py:121](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2090-openalex-fetch/orchestrator/axis1_search/checkpoint.py:121)）。
4. 各頁で request を catalog から再生成して一致を確認し、WAL の `prepared`、host limiter、`issued`、HTTP、gzip 生応答、response digest、quota をこの順で保存する（[runner.py:1655](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2090-openalex-fetch/orchestrator/axis1_search/runner.py:1655)、[runner.py:1761](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2090-openalex-fetch/orchestrator/axis1_search/runner.py:1761)）。
5. parse と条件 1〜6 の評価後、累積 ledger と page evidence を書く。page evidence は URL、各 WAL 時刻、本文 SHA-256 を持つ（[runner.py:1985](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2090-openalex-fetch/orchestrator/axis1_search/runner.py:1985)、[runner.py:2070](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2090-openalex-fetch/orchestrator/axis1_search/runner.py:2070)、[runner.py:1022](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2090-openalex-fetch/orchestrator/axis1_search/runner.py:1022)）。
6. cursor があれば次頁へ進む。終端なら leaf 条件を評価し、74 leaf は `pass_complete` checkpoint、残る4 leaf は `branch_complete` になる（[runner.py:2189](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2090-openalex-fetch/orchestrator/axis1_search/runner.py:2189)）。
7. 通常の return 前には `manifest.json` と `MANIFEST.sha256` を再生成する。checkpoint は manifest より先に create-only で書かれる（[runner.py:1107](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2090-openalex-fetch/orchestrator/axis1_search/runner.py:1107)、[checkpoint.py:596](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2090-openalex-fetch/orchestrator/axis1_search/checkpoint.py:596)）。

完走以外の状態は次のとおり。

| 状態 | 発火条件 | checkpoint | OpenAlex |
|---|---|---|---|
| preflight failure、状態なし | HEAD 不一致、dirty 登録 path、catalog 不一致など。HTTP 前に CLI rc=2（[run_axis1_search.py:127](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2090-openalex-fetch/tools/run_axis1_search.py:127)） | なし | 発火する |
| `paused_quota` / `quota_reserve` | 頁発行前または retry 前に quota 予約を満たさない（[runner.py:1666](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2090-openalex-fetch/orchestrator/axis1_search/runner.py:1666)、[runner.py:1707](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2090-openalex-fetch/orchestrator/axis1_search/runner.py:1707)） | `continue_cursor` | 発火する |
| `paused_quota` / `quota_reserve` | 成功頁の後、次 cursor はあるが残量不足（[runner.py:2123](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2090-openalex-fetch/orchestrator/axis1_search/runner.py:2123)） | `continue_cursor` | 発火する |
| `paused_quota` / `http_status_429` | HTTP 429。retry を続けず停止（[runner.py:1932](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2090-openalex-fetch/orchestrator/axis1_search/runner.py:1932)） | `continue_cursor` | 発火する。reset header が無ければ待ち期限を自己判定できない |
| `paused_quota` / `page_limit` | 内部 API の `max_pages` 到達（[runner.py:1656](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2090-openalex-fetch/orchestrator/axis1_search/runner.py:1656)、[runner.py:2272](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2090-openalex-fetch/orchestrator/axis1_search/runner.py:2272)） | なし | production CLI からは発火しない |
| `outcome_unknown` | 429 以外の非200、通信失敗、応答過大などが retry 後も解消しない（[runner.py:1932](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2090-openalex-fetch/orchestrator/axis1_search/runner.py:1932)） | `restart_branch` | 発火する |
| `outcome_unknown` / `parse_error` | parser 自体が例外を送出（[runner.py:1985](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2090-openalex-fetch/orchestrator/axis1_search/runner.py:1985)） | **なし** | 通常の不正 JSON は値として処理されるため稀だが、経路は存在する |
| `blocked_on_ruling` | 成功応答の頁条件 1〜6 のいずれかが偽（[runner.py:2061](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2090-openalex-fetch/orchestrator/axis1_search/runner.py:2061)、[runner.py:2181](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2090-openalex-fetch/orchestrator/axis1_search/runner.py:2181)） | **なし** | 発火する |
| `blocked_on_ruling` | 終端後の leaf 条件、総数、shard、pass digest が偽（[runner.py:2206](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2090-openalex-fetch/orchestrator/axis1_search/runner.py:2206)） | **なし** | 発火する |
| `pass_complete` | 独立2走必須 leaf の pass 1 が正常終端（[runner.py:2217](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2090-openalex-fetch/orchestrator/axis1_search/runner.py:2217)） | `start_independent_pass` | 74 leaf で正常に発火する。leaf 完走ではない |
| `not_started` | validator が「page evidence も対応 checkpoint もない」と導出（[validator.py:1707](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2090-openalex-fetch/orchestrator/axis1_search/validator.py:1707)） | なし | 未起動 leaf で発火する |
| `outcome_unknown` | evidence はあるが完了 pass も対応 checkpoint もない場合に validator が導出（[validator.py:1714](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2090-openalex-fetch/orchestrator/axis1_search/validator.py:1714)） | なし | 中断や checkpoint 無しの失敗で発火する |
| `not_run` | runner の状態ではない。validator は `not_started` と `not_run=true` を出す（[validator.py:1757](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2090-openalex-fetch/orchestrator/axis1_search/validator.py:1757)） | なし | 発火する |
| `prepared` / `issued` / `response_stored` / `parsed` | WAL の中間状態。process がその地点で死んだ場合に残る（[checkpoint.py:25](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2090-openalex-fetch/orchestrator/axis1_search/checkpoint.py:25)） | 自動生成されない | 発火しうる |
| `superseded` | schema 上の手動・後継 checkpoint 状態 | runner は生成しない | 本 wave では発火しない |
| `not_applicable` | 宣言的除外 | runner は生成しない | OpenAlex leaf では発火しない |

OpenAlex で実際に起きうる頁条件の停止理由は、条件1の `interpreted_query_mismatch`、条件2の `position_mismatch` / `silent_truncation` / `cursor_parent_mismatch`、条件3の total・capacity・件数不一致、条件4の work ID・occurrence・日付行不正、条件5の total drift・distinct ID・shard・第2走 digest 不一致、条件6の parse・content type・final URL・証拠不完全である（[validator.py:273](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2090-openalex-fetch/orchestrator/axis1_search/validator.py:273)、[validator.py:469](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2090-openalex-fetch/orchestrator/axis1_search/validator.py:469)）。

## 所見 (must-fix)

1. **段2の S1 は異なる応答の時刻と reset を混ぜる。** プランは `observed_at_utc` と `reset_seconds` が同じ応答由来だと置く（[stage2-plan.md:38](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2090-openalex-fetch/artifacts/stage2-plan.md:38)）。しかし `_merge_quota` は観測時刻を常に新応答へ更新し、欠けた reset は旧応答から継承する（[runner.py:688](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2090-openalex-fetch/orchestrator/axis1_search/runner.py:688)）。例えば旧 `reset=10`、新しい200応答が `remaining=35` だが reset 無しなら、新時刻+10秒で発行を許してしまう。これは brief の「reset が無い観測は停止」という不変条件に反する（[brief.md:108](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2090-openalex-fetch/brief.md:108)）。`reset_seconds` を現在の応答から欠けたまま引き継がないか、時刻との同一応答束縛を別途保つ必要がある。

   成果物影響: quota gate の受理集合が意図せず広がり、予約30 credit 内へ request を出す証拠 bundleを生成しうる。

2. **production argv の catalog path は repo 相対の逐語値でなければならない。** CLI と preflight は絶対 catalog path を受理するが、page evidence schema は `docs/related-work/claim-survey/2026-09-02-axis1-search-catalog.json` という相対文字列を const で要求する（[axis1_search_page_evidence.schema.json:104](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2090-openalex-fetch/orchestrator/schemas/axis1_search_page_evidence.schema.json:104)）。旧走行でも絶対 path のため取得後に拒否されている（[2026-08-30-axis1-search-execution.md:216](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2090-openalex-fetch/docs/related-work/claim-survey/2026-08-30-axis1-search-execution.md:216)）。さらに `run-id` は CLI では無検査だが schema は英数字開始の `[A-Za-z0-9._-]*` を要求する（[axis1_search_page_evidence.schema.json:110](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2090-openalex-fetch/orchestrator/schemas/axis1_search_page_evidence.schema.json:110)）。段2は S2 argv を書いていないため、同じ失敗を防げない。

   成果物影響: HTTP と raw evidence は取得できても、bundle checker の受理集合から全 page evidence が外れる。

3. **78 leaf の driver は実在しない。** production CLI は `--query-id` 1個または checkpoint 1個だけを処理する（[run_axis1_search.py:44](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2090-openalex-fetch/tools/run_axis1_search.py:44)）。repo 内に OpenAlex leaf 一括実行器はない。親は catalog から78 IDを列挙し、78回起動する必要がある。また CLI は `branch_complete` 以外を一律 rc=3 にする（[run_axis1_search.py:177](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2090-openalex-fetch/tools/run_axis1_search.py:177)）。74 leaf の正常な pass 1 は `pass_complete` / rc=3 なので、`set -e` 型 loop は最初の sharded leaf で停止する。rc ではなく JSON の `state` を読む driver 手順が必要である。

   成果物影響: 放置すると最大でも初期数 leaf だけが取得され、残りが `not_started` の partial bundle になる。

4. **「閉じて次窓で再開」は通常の branch tip からはできない。** checkpoint の `registration_commit` は resume 時に runner へそのまま渡され（[runner.py:2329](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2090-openalex-fetch/orchestrator/axis1_search/runner.py:2329)）、preflight は祖先到達性でなく `HEAD == registration_commit` を要求する（[validator.py:766](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2090-openalex-fetch/orchestrator/axis1_search/validator.py:766)）。partial bundle と実行記録を後続 commit にした時点で、その tip からは再開不能である。P3 の「land 後 main の祖先ならよい」は不十分で、entry 1169 と同じく登録 commit を detach した木、同じ bundle 絶対 path、完全な bundle 復元が必要である。

   成果物影響: checkpoint を記録しても、通常の次 wave では preflight が HTTP 0 本で止まり、証拠集合を増やせない。

5. **quota 以外の停止には再開点が無い。** `blocked_on_ruling` は page/leaf evidence と manifest を残すが checkpoint を書かない（[runner.py:2181](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2090-openalex-fetch/orchestrator/axis1_search/runner.py:2181)）。parser 例外の `outcome_unknown` も checkpoint が無い（[runner.py:2046](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2090-openalex-fetch/orchestrator/axis1_search/runner.py:2046)）。親の「残 leaf 数と再開点」は、`paused_quota` と HTTP/transport の `restart_branch` にだけ成立する。実行記録は「checkpoint 無しの hard stop」を別に数える必要がある。

   成果物影響: 全未完走 leaf が再開可能であるかのように記録すると、実在しない参照先を持つ実行記録になる。

6. **OpenAlex pass 1 だけの bundle checker は成功しない。** checker は catalog 全263 leaf と aggregate を評価し、evidence/checkpoint がない leaf を `not_started` とする（[validator.py:1507](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2090-openalex-fetch/orchestrator/axis1_search/validator.py:1507)）。さらに74 OpenAlex leaf は pass 2 未実行なので未完走である。`bundle_validation_complete=true` は得られても、`passed=false`、`retrieval_complete=false`、`axis_complete=false` になる（[validator.py:1806](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2090-openalex-fetch/orchestrator/axis1_search/validator.py:1806)）。この非zeroを想定した検査・記録手順が必要である。

   成果物影響: bundle の digest・schema が健全でも完走受理集合には入らず、軸1は `RW1` のままである。

7. **S3 の記録項目が契約より狭い。** URL・時刻・digest・残 leaf だけでは足りない。凍結実行記録は、作成日、入力 path/commit/digest、cutoff（[claim-survey/README.md:14](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2090-openalex-fetch/docs/related-work/claim-survey/README.md:14)）、leaf ごとの ID・全 occurrence・distinct 数・2種類の digest・頁件数・quota・条件別結果（[2026-08-29-axis1-search-amendment.md:478](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2090-openalex-fetch/docs/related-work/claim-survey/2026-08-29-axis1-search-amendment.md:478)）、順序非依存条件1を使った旨と不一致面（[amendment-2026-09-02.md:163](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2090-openalex-fetch/materials/amendment-2026-09-02.md:163)）、母集合の外、checker の全 status、manifest SHA-256 を持つ必要がある。新しい実行記録を `claim-survey/README.md` の一覧へ追加する手順も brief にない。

   成果物影響: bundle bytes が正しくても、凍結記録から取得条件・判定・manifest を復元できず、参照可能な実行証拠として不完全になる。

## 所見 (nit / backlog)

- entry 1169 の「最低154 request」は算術誤りで、78 pass 1 + 74 pass 2 = 最低152 request である（[worklog-1169.md:26](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2090-openalex-fetch/materials/worklog-1169.md:26)）。成果物影響: 最低予算が2 request 過大になるが、2窓以上という結論は変わらない。

- generic な `output/README.md` は HTTP本文全文を保存しないとする一方（[output/README.md:86](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2090-openalex-fetch/output/README.md:86)）、個別 amendment と runner/validator は gzip 本文保存と再parseを要求する。個別凍結契約を優先すれば本走は可能だが、文書上の矛盾は後続で解消すべきである。成果物影響: cleanup が generic 規則を適用すると raw evidence が失われ、bundle が `raw_path_set_mismatch` になる。

- 強制終了時の WAL recovery は状態を分類するだけで、自動 checkpoint 化しない（[checkpoint.py:207](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2090-openalex-fetch/orchestrator/axis1_search/checkpoint.py:207)）。`response_stored` 後に死ぬと未参照 raw が残り、manifest/checker を壊しうる。成果物影響: 正常な quota return 以外の中断では手動修復なしに受理可能 bundleへ戻せない。

- `previous_checkpoint` は path・bytes・digest の型だけ検査され、参照先を再読して digest を照合しない（[checkpoint.py:428](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2090-openalex-fetch/orchestrator/axis1_search/checkpoint.py:428)）。成果物影響: 現 checkpoint 単体の再開性は変わらないが、checkpoint 履歴の参照鎖は manifest 以外から独立検証できない。

## 独立 2 走の起動方法

2走目は `--query-id` の再実行ではない。pass 1 が成功すると runner が `state=pass_complete`、`resume_action=start_independent_pass` の checkpoint を作り、selected request の `target_pass_number` を2にする（[runner.py:2217](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2090-openalex-fetch/orchestrator/axis1_search/runner.py:2217)、[runner.py:1430](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2090-openalex-fetch/orchestrator/axis1_search/runner.py:1430)）。resume 側がこの値を `pass_number` に渡す（[runner.py:2305](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2090-openalex-fetch/orchestrator/axis1_search/runner.py:2305)）。

未来の SHA と checkpoint 番号以外は具体化できる。実際の argv は checkpoint 内 `canonical_runner_argv` の逐語値であり、形は次である。

```text
python3 tools/run_axis1_search.py
  --registration-commit <S1を含む40桁C_reg>
  --catalog docs/related-work/claim-survey/2026-09-02-axis1-search-catalog.json
  --bundle /work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2090-openalex-fetch/output/insights/<新規path>/bundle
  --run-id t2090-openalex-20260903
  --checkpoint /work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2090-openalex-fetch/output/insights/<新規path>/bundle/checkpoints/000001.json
```

`--run-id` は checkpoint の `requests.start_independent_pass.target_run_id` と同じ値でなければ CLI が拒否する（[run_axis1_search.py:117](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2090-openalex-fetch/tools/run_axis1_search.py:117)）。`--query-id` を再実行すると `pass_number=1` から始まり、独立 pass 2 にはならない（[runner.py:2351](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2090-openalex-fetch/orchestrator/axis1_search/runner.py:2351)）。

## 費用と窓の見積り

catalog が持つのは結果件数ではなく query program の本数である。OpenAlex は Q3が37 leaf、Q6が37 leaf、非shardの Q1/Q2/Q4/Q5 が4 leaf、合計78である（[catalog JSON:81](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2090-openalex-fetch/docs/related-work/claim-survey/2026-09-02-axis1-search-catalog.json:81)）。頁サイズは200（[catalog JSON:142](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2090-openalex-fetch/docs/related-work/claim-survey/2026-09-02-axis1-search-catalog.json:142)）。

各 leaf の実件数を `N_i` とすると pass 1 request 数は、

```text
R1 = Σ max(1, ceil(N_i / 200))
```

である。catalog に `N_i` は無いため、静的に証明できるのは最低78 requestだけで、有限上限は導けない。

旧同型 query の実測92頁を最良推定に使うと、pass 1 は約92 requestであり、残り96 requestの窓に4 requestの余裕で収まる。したがって判定は次の二層になる。

- 計画推定: **92 ≤ 96 なので1窓に収まる。**
- 契約上の保証: **できない。** 現在の件数増加または5回以上の追加頁・retryで窓を越える。

92 request 推定時の壁時計下限は、

```text
78 leaf × 3.1秒 + 92頁 × 1.0秒 = 333.8秒
```

すなわち約5分34秒。静的最低78頁なら319.8秒、96 requestまで使うなら337.8秒、約5分38秒である。HTTP latency、gzip・fsync、manifest再計算、retry backoffは別途加わる。

推定上は窓が尽きないため「何 leaf 分」は該当しない。仮に総 request が97なら、旧平均での粗い換算は `floor(96 × 78 / 97) = 77 leaf` だが、catalog に leaf別件数と実行順が無いので厳密な停止 leaf は不明である。

## 再開点が本当に再開に使えるか

結論は「bundle 全体と実行環境を維持する限り使える。ただし checkpoint 単体や通常の後続 tip からは使えない」である。

- bundle root: checkpoint に渡した文字列を保存し、CLI と validator は解決後 path の一致を要求する（[runner.py:1454](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2090-openalex-fetch/orchestrator/axis1_search/runner.py:1454)、[validator.py:1209](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2090-openalex-fetch/orchestrator/axis1_search/validator.py:1209)）。初回から絶対 path を使うべきである。
- registration commit: exact HEAD が必要。main の祖先として残るだけでは不足する。
- catalog path: digest に加え、page evidence の逐語相対 path const に従う必要がある。repo root を cwd にして相対 pathを渡す。
- completed prefix: resume は checkpoint の ledger digestを再計算し、過去 page evidence が次 page番号まで全部あることを確認する（[runner.py:1246](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2090-openalex-fetch/orchestrator/axis1_search/runner.py:1246)）。
- quota: 再開判断は checkpoint 内の複製でなく、bundle の `state/runtime.json` を読む。checkpoint、ledger、pages、raw、WAL、runtime の一式が必要である。
- manifest: 正常な resume/return 後に再生成されるため、前窓の凍結実行記録が参照した manifest SHA は変わる。窓ごとの旧 digest を残すなら、その bundle 状態を commitで保存し、新窓では新しい凍結実行記録を追加する必要がある。

したがって親の「再開点を記録して閉じる」は、そのままでは実行手順になっていない。partial 成果物を commitした後は、entry 1169 と同じく、C_reg を exact HEAD にした同じ絶対 worktree pathへ bundle 全体を復元する手順まで記録して初めて再開可能である。

## 総括

段2プランはそのまま author 段へ渡せない。最優先の修正は、quota merge が過去の reset と新しい観測時刻を結合しないことを保証すること。その後、親の S2/S3 手順へ次を明記する必要がある。

- repo root を cwd とし、catalog は固定の相対 path、bundle は未作成の絶対 path、schema適合 run IDを使う。
- 78 leaf は78回起動し、rc=3ではなく JSON state を判定する。
- `pass_complete` は正常な pass 1 完了であり、74 leaf はまだ leaf未完走である。
- quota以外の停止には checkpoint が無い場合がある。
- checker は OpenAlex pass 1だけでは `passed=false` が正しい。
- 次窓の再開には exact C_reg HEAD、同じ bundle絶対 path、bundle全体の復元が必要。
- 実行記録は inherited §10、manifest SHA、checker status、README導線まで持つ。

検査は指定どおり静的に行い、pytest・HTTP実走はしておらず、緑とは報告しない。