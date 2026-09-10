## 所見

1. **「正当に空」を検証する producer がなく、自己申告だけで空取得を成立させている。**
   - 対象: [s2-plan.md:9](</home/SFC/tanab/.claude/jobs/9a120ef8/tmp/wave-t2246/artifacts/t2246-k2-knowledge-closure/s2-plan.md:9>)、[同:203](</home/SFC/tanab/.claude/jobs/9a120ef8/tmp/wave-t2246/artifacts/t2246-k2-knowledge-closure/s2-plan.md:203>)、[knowledge_manifest.py:301](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2246-k2-knowledge-closure/orchestrator/campaign/knowledge_manifest.py:301)
   - 何が起きるか: production producer は manifest に列挙された `sources` を解決するだけで、`declared_scope` に対する取得を実行しない。任意の caller が `completed_empty` と書けば、実取得なしでも受理される。プラン自身も retrieval receipt 不在を認めている。
   - 成果物影響: 実取得をしていない campaign が v2 受領証、campaign lock、BUILD_START、材料レポートに `completed_empty` を記録し、K2 certified 最終選択の根拠になり得る。
   - 重大度: **must-fix（裁定パッケージ）**。trusted caller 宣言を「正当に空」の十分条件と裁定するか、実 retrieval producer/receipt を本題に含めるかを決める必要がある。

2. **`declared_scope` と実 `sources` の包含整合がなく、宣言外 source を同じ manifest に書ける。**
   - 対象: [s2-plan.md:9](</home/SFC/tanab/.claude/jobs/9a120ef8/tmp/wave-t2246/artifacts/t2246-k2-knowledge-closure/s2-plan.md:9>)、[同:54](</home/SFC/tanab/.claude/jobs/9a120ef8/tmp/wave-t2246/artifacts/t2246-k2-knowledge-closure/s2-plan.md:54>)、D1429 [rulings-verbatim.md:16](</home/SFC/tanab/.claude/jobs/9a120ef8/tmp/wave-t2246/rulings-verbatim.md:16>)
   - 何が起きるか: selector は意味を解釈しない自由文字列で、実 source が retrieval/injection scope 内かを検査しない。scope A と無関係な source B を、件数だけ整合させて投入できる。
   - 成果物影響: 受領証・WAL・材料レポートが「許可範囲 A」と「投入 B」を矛盾したまま束縛し、宣言外情報を使った候補を K2 条件付き選択へ混入できる。
   - 重大度: **must-fix（裁定パッケージ）**。一般 leak gate を足さずに、少なくとも同一 manifest 内の包含関係を機械判定可能にするか、「scope は非強制の説明」として certified 閉包の主張を弱める必要がある。

3. **知識水準と role/output contract を同一視しており、既存 K2 proposal の受理集合を暗黙に変える。**
   - 対象: [s2-plan.md:103](</home/SFC/tanab/.claude/jobs/9a120ef8/tmp/wave-t2246/artifacts/t2246-k2-knowledge-closure/s2-plan.md:103>)、[同:148](</home/SFC/tanab/.claude/jobs/9a120ef8/tmp/wave-t2246/artifacts/t2246-k2-knowledge-closure/s2-plan.md:148>)、[p3_s4_loop.py:2077](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2246-k2-knowledge-closure/orchestrator/campaign/p3_s4_loop.py:2077)、[T-2182 run-record.md:13](</work/1/SFC/tanab/izanagi/output/insights/2026-09-02_t2182-k2-arm-liveness/run-record.md:13>)
   - 何が起きるか: `knowledge_input is not None` だけで K2 wrapper を要求するが、K2 は入力条件であって role identity ではない。唯一の実 K2 走行は通常 `coder-v4-autonomous` の flattened proposal だった。同じ manifest/campaign identity でも、実装後はその形が拒否される。
   - 成果物影響: 旧 K2 proposal の受理集合が縮み、同じ `b6dde2ef` identity が時期により異なる output contract を意味する。
   - 重大度: **must-fix**。trusted な role/output-contract marker または別入口で分岐し、legacy K2 の扱いを明示すべきである。

4. **`validate_output_semantics` の「logical schema 検証済み」という前提を production path が満たさない。**
   - 対象: [policy.py:394](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2246-k2-knowledge-closure/orchestrator/codex_roles/policy.py:394)、[projection_guard.py:283](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2246-k2-knowledge-closure/orchestrator/campaign/projection_guard.py:283)、[s2-plan.md:21](</home/SFC/tanab/.claude/jobs/9a120ef8/tmp/wave-t2246/artifacts/t2246-k2-knowledge-closure/s2-plan.md:21>)
   - 何が起きるか: 現行 projection guard は key closure の検査で、プランも wrapper と nested `proposal` の exact keys しか具体化していない。role の full output schema を呼ぶ箇所がないため、`knowledge_use[].use` 欠落、無効な `classification`、不正な `data_boundary_report` が semantic validatorを通り得る。
   - 成果物影響: K2 role 契約に違反する output から抽出した候補値が build・正しさ・性能 gate へ進み、proposal の受理集合が role schema より広がる。
   - 重大度: **must-fix**。K2 helper で reviewed input/output schema を実際に検証してから semantic validator を呼ぶ必要がある。

5. **validator が見る入力は実 role input ではなく、loader が後から合成する二欄だけである。**
   - 対象: [s2-plan.md:107](</home/SFC/tanab/.claude/jobs/9a120ef8/tmp/wave-t2246/artifacts/t2246-k2-knowledge-closure/s2-plan.md:107>)、[manifest.json:754](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2246-k2-knowledge-closure/orchestrator/codex_roles/manifest.json:754)、[p3_s4_loop.py:2037](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2246-k2-knowledge-closure/orchestrator/campaign/p3_s4_loop.py:2037)、[T-2182 run-record.md:3](</work/1/SFC/tanab/izanagi/output/insights/2026-09-02_t2182-k2-arm-liveness/run-record.md:3>)
   - 何が起きるか: role schema は5欄を要求するが、プランは `knowledge_input` と `planner_direction` だけを再合成する。role が manifest A を見て出した `source_index=0` を、同数 source の manifest B と一緒に loader へ渡しても通る。actual coder input artifact/digest の束縛はない。
   - 成果物影響: accepted proposal の `knowledge_use` は A を指した自己申告なのに、受領証・WAL・材料レポートは B を投入源として記録できる。
   - 重大度: **must-fix（裁定パッケージ）**。実 role input の束縛を追加するか、検査対象は「actual role input」ではなく「loader 時点の再合成 projection」に限ると主張を下げる必要がある。

6. **D1559 の「二集合が不一致になる」という brief の説明は誤りで、裁定本文との衝突だけが残る。**
   - 対象: [brief.md:31](</home/SFC/tanab/.claude/jobs/9a120ef8/tmp/wave-t2246/brief.md:31>)、D1559 [rulings-verbatim.md:137](</home/SFC/tanab/.claude/jobs/9a120ef8/tmp/wave-t2246/rulings-verbatim.md:137>)、[wal.py:879](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2246-k2-knowledge-closure/orchestrator/campaign/wal.py:879)、[s2-plan.md:70](</home/SFC/tanab/.claude/jobs/9a120ef8/tmp/wave-t2246/artifacts/t2246-k2-knowledge-closure/s2-plan.md:70>)
   - 何が起きるか: プランは canonical `sources` と verified `sources` の一致検査を維持するため、T-2183 の `declared_sources` / `injected_sources` は空時も双方空である。不一致になるのは新 `declared_scope` と両配列である。一方、D1559 はなお canonical sources を「参照を許した範囲」と定義している。
   - 成果物影響: 同じ extended report を、D1559 に従う consumer は「許可範囲なし」、新プランに従う consumer は「非空の許可範囲あり」と解釈する。
   - 重大度: **must-fix**。D1559 は「既存二配列の一致は維持」「許可範囲の出所だけを新 `declared_scope` へ変更」として名指しで再裁定すべきである。

7. **既存 `b6dde2ef` は名前だけ維持され、production resume/replay と材料レポート生成はできない。**
   - 対象: [s2-plan.md:74](</home/SFC/tanab/.claude/jobs/9a120ef8/tmp/wave-t2246/artifacts/t2246-k2-knowledge-closure/s2-plan.md:74>)、[ident.py:350](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2246-k2-knowledge-closure/orchestrator/campaign/ident.py:350)、[同:390](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2246-k2-knowledge-closure/orchestrator/campaign/ident.py:390)、[layer3_report.py:1067](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2246-k2-knowledge-closure/orchestrator/campaign/layer3_report.py:1067)
   - 何が起きるか: 実 campaign は lock と v1 receipt だけで WAL がない。recorded `wal.py` SHA-256 は `518365…`, 現 HEAD は既に `e3ebcd…` であり、今回さらに `wal.py` を変える。production resume は `verify_against_lock` の live closure 検査で replay 前に落ちる。材料レポートも WAL 必須で生成不能。
   - 成果物影響: v1 receipt と digest `6d8674…406`、directory ID は保存されるが、既存 campaign に BUILD_START・試行台帳・材料レポートを後付けできない。
   - 重大度: **should-fix**。移行機構を足す必要はないが、「identity continuity ≠ resume continuity」をテスト名・insight・完了主張へ明記すべきである。

8. **`result_count == len(sources)` は取得件数と投入件数を同一視する過一般化である。**
   - 対象: [s2-plan.md:10](</home/SFC/tanab/.claude/jobs/9a120ef8/tmp/wave-t2246/artifacts/t2246-k2-knowledge-closure/s2-plan.md:10>)、[同:164](</home/SFC/tanab/.claude/jobs/9a120ef8/tmp/wave-t2246/artifacts/t2246-k2-knowledge-closure/s2-plan.md:164>)
   - 何が起きるか: scope は retrieval/injection を分ける一方、実績は一つの count と一つの source 配列しか持たない。3件取得して1件だけ投入した正当な状態を表せない。`completed_nonempty` は今回の「ゼロ取得を通す」欠陥を越えた一般化でもある。
   - 成果物影響: 正当な K2 manifest が入口で拒否されるか、取得件数を投入件数へ偽って受領証・WAL・レポートへ記録することになる。
   - 重大度: **should-fix**。empty-only 拡張に閉じるか、取得結果と投入 source の実績を別欄にする必要がある。

9. **既に閉じた検査の再実施と現行設計文書の更新漏れがある。**
   - 対象: [s2-plan.md:197](</home/SFC/tanab/.claude/jobs/9a120ef8/tmp/wave-t2246/artifacts/t2246-k2-knowledge-closure/s2-plan.md:197>)、[T-2183 README.md:65](</work/1/SFC/tanab/izanagi/output/insights/2026-09-03_t2183-knowledge-provenance/README.md:65>)、[agent-architecture.md:132](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2246-k2-knowledge-closure/docs/agent-architecture.md:132)
   - 何が起きるか: `m07-control` は T-2183 の `m02r` と同じ等価性を再確認するだけである。またプランは role 文書を直すが、current architecture の「consumer:null・未配線」は変更面に入っていない。
   - 成果物影響: certified 選択値や受理集合は変わらない。変異台帳へ既知の SURVIVED が一件増え、設計文書の参照だけが実装後も未配線と誤記する。
   - 重大度: **nit**。`m07-control` は削除し、architecture の現行記述だけ更新するのがよい。

変異候補 `m01`〜`m06` には、静的には別層の赤による mask は見つからない。いずれも contract-loader closure 外で、`m05` の範囲外 index は現行 output schema 自体では拒否されないため semantic predicate に帰属できる。ただし単一 node 性は未実測である。`m07-control` は mask ではなく意図的等価変異だが、T-2183 で実測済みである。

## 塞がったままの層

- **manifest producer — 塞がっている。** production 呼び手は [p3_s4_loop.py:1093](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2246-k2-knowledge-closure/orchestrator/campaign/p3_s4_loop.py:1093) から parser/resolver を呼ぶが、取得行為・scope 包含を検証する producer はない。
- **受領証 — プラン上は通る。** [knowledge_manifest.py:363](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2246-k2-knowledge-closure/orchestrator/campaign/knowledge_manifest.py:363) の v1 producer を v1/v2 分岐する変更が収載されている。ただし上流の自己申告問題をそのまま固定する。
- **campaign lock — 追加変更不要。** [p3_s4_loop.py:1118](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2246-k2-knowledge-closure/orchestrator/campaign/p3_s4_loop.py:1118) が manifest digest を identity に入れ、[wal.py:627](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2246-k2-knowledge-closure/orchestrator/campaign/wal.py:627) が読み出す。新 manifest 全体を digest 対象にするなら scope/result も束縛される。
- **WAL — プラン上は通る。** production append は [wal.py:1054](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2246-k2-knowledge-closure/orchestrator/campaign/wal.py:1054)、replay 検査は [同:1951](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2246-k2-knowledge-closure/orchestrator/campaign/wal.py:1951)。v2 shape を両方へ足す変更が収載済み。
- **材料レポート — プラン上は通る。** T-2183 の既存 producer [layer3_report.py:779](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2246-k2-knowledge-closure/orchestrator/campaign/layer3_report.py:779) と schema 実検査 [同:875](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2246-k2-knowledge-closure/orchestrator/campaign/layer3_report.py:875) を再利用する。アルゴリズム新設は不要というプラン判断は正しい。
- **proposal producer / contract selector — 塞がっている。** K2 role output を `proposal.json` の `coder` wrapperへ写す trusted producer と、どの role contract で生成したかの束縛がない。`knowledge_input != None` は代替にならない。
- **proposal 入口 — 部分的に通る。** 現在の production 呼び手は [p3_s4_loop.py:2077](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2246-k2-knowledge-closure/orchestrator/campaign/p3_s4_loop.py:2077)。プランどおり `_knowledge_input` を渡せば `--run-iteration --knowledge-manifest` で K2 helper へ到達するが、所見3・4が残る。
- **`validate_output_semantics` — 呼出しは新設されるが、入力・schema 前提が塞がっている。** 現 HEAD の production 呼び手はゼロ。プランの helper が唯一の呼び手になるが、actual role input の束縛と full logical schema 検証がないため、端から端まで束縛したとはまだ言えない。

## 親 brief の誤り

1. [brief.md:31](</home/SFC/tanab/.claude/jobs/9a120ef8/tmp/wave-t2246/brief.md:31>) の「D1570 で既存二段が不一致になる」は誤り。プランでは canonical/verified sources は引き続き一致し、不一致になるのは新 `declared_scope` と concrete sources である。
2. [brief.md:15](</home/SFC/tanab/.claude/jobs/9a120ef8/tmp/wave-t2246/brief.md:15>) の `load_proposal_file` を「K2 role の実出力経路」とする表現は過大。generic proposal の production reader ではあるが、K2 role wrapper がここを通った実成果物はゼロで、trusted proposal producer もコード化されていない。
3. [brief.md:11](</home/SFC/tanab/.claude/jobs/9a120ef8/tmp/wave-t2246/brief.md:11>) の「非空要求は3箇所」は scope 列挙として不完全。K2 role input schema の `minItems:1` が第四層にあり、proposal wrapper を拒否する projection guard も別の遮断層である。brief 後半と段2プランは後者を回収している。
4. `p3-s4-loop-s4-autonomous-b6dde2ef` は完全な実 campaign ではなく、受領証だけが成立した部分成果物である。[run-record.md:31](</work/1/SFC/tanab/izanagi/output/insights/2026-09-02_t2182-k2-arm-liveness/run-record.md:31>) のとおり WAL・候補束縛・terminal verdict は未成立で、材料レポートも存在しない。digest/ID 維持を replay 互換と読んではならない。
5. brief は「正当に空」を要件にするが、その正当性を誰が検証するかを定義していない。段2の実体は caller declaration であり、要件を満たしたことにはならない。

## 総括

最大の取りこぼしは、`completed_empty` と `declared_scope` が構造化された自己申告に留まり、実取得や scope 内投入を証明しない点である。  
proposal 側も呼出し点は作れるが、role/output contract の選択、full schema 検証、actual role input との束縛がなく、参照整合性は別入力に対して発火し得る。  
T-2183 の receipt→WAL→材料レポート機構は再利用でき、既存二配列を作り直す必要はない。D1559 の説明だけを正しく再裁定する必要がある。  
したがって段2プランは**このまま採用不可**。所見1〜6を段4で裁定・修正した後なら、中間の receipt→lock→WAL→report 部分は採用できる。  
pytest・変異は実走しておらず、以上は静的検査結果である。