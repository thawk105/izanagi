## 所見

1. **「正当に空」を証明せず、自己申告だけで空を通す**
   - **対象:** [s2-plan.md:9](/home/SFC/tanab/.claude/jobs/9a120ef8/tmp/wave-t2246/artifacts/t2246-k2-knowledge-closure/s2-plan.md:9)、[knowledge_manifest.py:301](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2246-k2-knowledge-closure/orchestrator/campaign/knowledge_manifest.py:301)、[p3_s4_loop.py:1093](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2246-k2-knowledge-closure/orchestrator/campaign/p3_s4_loop.py:1093)
   - **何が起きるか:** `completed_empty`、`result_count=0`、非空 selector はすべて manifest caller が記入する。`sources=[]` なら `resolve_live_sources` は取得処理を一度も行わず成功するため、未実行・取得失敗・意図的省略を `completed_empty` と偽れる。digest と WAL は偽れる宣言を固定するだけである。
   - **成果物影響:** 偽の正常空が receipt v2、campaign lock、BUILD_START、材料レポートへ正規値として残り、その K2 campaign を条件とする certified な最終選択まで受理しうる。
   - **重大度:** **must-fix**

2. **宣言範囲と投入 source の包含関係が検査不能で、取得件数と投入件数も混同している**
   - **対象:** [s2-plan.md:9](/home/SFC/tanab/.claude/jobs/9a120ef8/tmp/wave-t2246/artifacts/t2246-k2-knowledge-closure/s2-plan.md:9)、同 `:10`、`:54`、`:70`
   - **何が起きるか:** `selector` は任意の非空文字列で、plan は明示的に allowlist/membership gate にしない。したがって宣言外 source を `sources` に入れても、Git 実在性さえ通れば受理される。例の `"all-successfully-retrieved-sources"` も事前の投入範囲ではなく結果依存の万能指定である。また「取得結果件数」を「投入 source 件数」へ等置するため、取得後に一部だけ投入する正当な状態を表現できない。
   - **成果物影響:** 材料レポートが宣言範囲外の source を正規の投入源として引用でき、逆に取得集合と投入集合が異なる正当な試行は拒否または誤記録される。
   - **重大度:** **must-fix**

3. **K2 role の論理 output schema 全体を検査せず、入口の受理集合が role 契約より広い**
   - **対象:** [s2-plan.md:21](/home/SFC/tanab/.claude/jobs/9a120ef8/tmp/wave-t2246/artifacts/t2246-k2-knowledge-closure/s2-plan.md:21)–`:28`、[manifest.json:870](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2246-k2-knowledge-closure/orchestrator/codex_roles/manifest.json:870)、[policy.py:487](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2246-k2-knowledge-closure/orchestrator/codex_roles/policy.py:487)
   - **何が起きるか:** plan は wrapper と nested proposal の key closure、および index/重複だけを検査する。`validate_output_semantics` は `knowledge_use[].use` の存在・型・非空、item の未知 key、`classification`、`data_boundary_report` を検査しない。さらに role schema は `value` を integer とするが semantic validator は float も受ける。共有の `validate_schema_instance(..., spec.output_schema)` を呼ぶ計画もない。
   - **成果物影響:** role 契約に不適合な K2 出力から抽出した proposal が通常の build/verify/bench へ進み、候補判定自体は緑でも K2 role 契約を満たさない候補が certified 選択材料へ混入する。
   - **重大度:** **must-fix**

4. **明示された data-boundary anomaly と分類矛盾を読み捨てる**
   - **対象:** [s2-plan.md:28](/home/SFC/tanab/.claude/jobs/9a120ef8/tmp/wave-t2246/artifacts/t2246-k2-knowledge-closure/s2-plan.md:28)、同 `:141`、`:173`、[coder-v4-autonomous-k2.md:124](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2246-k2-knowledge-closure/.claude/agents/coder-v4-autonomous-k2.md:124)
   - **何が起きるか:** 型として正しい `instruction_like_content_detected=true` でも plan は真偽を検査せず proposal を続行する。また role が `known_result_conditioned_derivative` を返し、親 receipt が `de_novo` でも不一致を捨てる。role の申告で receipt を上書きしない点は正しいが、より強い親主張との矛盾まで無視してよいことにはならない。
   - **成果物影響:** role 自身が報告した入力汚染や非 de novo 性を抱えた候補が試行台帳・材料レポート・最終選択へ残りうる。少なくとも anomaly は即 reject、分類矛盾は上書きでなく fail-closed または保守的再分類が必要。
   - **重大度:** **must-fix**

5. **D1494 の閉じた分類集合を WAL consumer が強制しておらず、plan も温存する**
   - **対象:** [wal.py:893](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2246-k2-knowledge-closure/orchestrator/campaign/wal.py:893)–`:901`、[s2-plan.md:14](/home/SFC/tanab/.claude/jobs/9a120ef8/tmp/wave-t2246/artifacts/t2246-k2-knowledge-closure/s2-plan.md:14)–`:18`
   - **何が起きるか:** persisted receipt reader は任意の非空 `classification` と任意 bool の `de_novo_claim` を受理し、両者の整合も見ない。実際、[test_layer3_report.py:1894](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2246-k2-knowledge-closure/orchestrator/tests/test_layer3_report.py:1894)–`:1900` は `"alternate-valid-claim"` へ改変した receipt を WAL helper が再受理することを示す。v2 計画にも是正がない。
   - **成果物影響:** 3 literal 外または `de_novo_claim` と矛盾する受領証を BUILD_START と材料レポート参照へ組み込め、分類に基づく certified 主張を汚染する。
   - **重大度:** **must-fix**

6. **D1559 を事実上変更するのに、必要な再裁定がまだない**
   - **対象:** [brief.md:29](/home/SFC/tanab/.claude/jobs/9a120ef8/tmp/wave-t2246/brief.md:29)–`:36`、[s2-plan.md:19](/home/SFC/tanab/.claude/jobs/9a120ef8/tmp/wave-t2246/artifacts/t2246-k2-knowledge-closure/s2-plan.md:19)、同 `:70`、`:84`–`:97`、[rulings-verbatim.md:137](/home/SFC/tanab/.claude/jobs/9a120ef8/tmp/wave-t2246/rulings-verbatim.md:137)–`:169`
   - **何が起きるか:** D1559 は allowed scope を `canonical_manifest.sources` から射影し、新 receipt generation も却下した。plan は allowed scope を新 `declared_scope` へ移し、receipt v2 を追加する。一方、旧二配列は引き続き同じ concrete source 集合である。D1570 は追加記録を要求したが、D1559 の具体的な field mapping/version を逐語的には更新していない。
   - **成果物影響:** 同じ v3 材料レポート内で `declared_sources` の意味が既裁定と plan の説明で分裂し、consumer が誤った欄を allowed scope として扱いうる。段4での明示再裁定なしには採用不可。
   - **重大度:** **must-fix（裁定 blocker）**

## 恒真になる述語

- **`m07-control`: `injected_sources = declared_sources`** — plan `:197`–`:199` 自身が認めるとおり、[wal.py:850](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2246-k2-knowledge-closure/orchestrator/campaign/wal.py:850)–`:881` が両元集合の一致を先に強制するため、検証後の候補集合では常に同値になる。allowed scope と投入 source の差の証拠にはならない。
- **空 source 時の `knowledge_use` index/重複検査** — `sources=[]` かつ `knowledge_use=[]` では item loop が0回で、参照整合性述語は空集合上の全称として恒真になる。空 K2 の正例は consumer 到達性は示すが、index 検査の発火実績にはならない。
- **parser 通過後の `completed_empty ⇔ count=0 ⇔ len(sources)=0` の再確認** — raw manifest 境界では拒否述語として働くが、receipt→WAL→report は同じ manifest 値と digestを複写するだけである。後段反復は改変検出にはなるが、取得が本当に行われたことの独立証明にはならない。
- **宣言範囲と source の membership 検査** — 恒真以前に、plan にはこの述語自体が存在しない。

## 親 brief の誤り

1. **「D1570 により D1559 の二集合が異なり、恒真性が失効する」は誤り。** plan は `canonical_manifest.sources` と verified `sources` を従来どおり同じ concrete 集合として保つため、空時も両方 `[]` である。異なるのは新設する第三の値 `declared_scope` であり、D1559 の既存二集合に関する恒真性は残る。

2. **「実際に投入した知識源」は実測より強い。** D1559 の主張境界と T-2182 の記録が証明するのは「harness が解決・検証し、role 入力へ投影した source」であり、context 書込み成功・role への実配送・実読了ではない。brief `:18`–`:19` はこの限定付き表現へ訂正すべきである。

以下の実測主張は確認できた。

- 実 artifact の `knowledge_use` は0件。T-2182 の coder 出力は `proposal` 1 key のみ。
- 変更対象中、contract-loader closure member は `wal.py` だけ。
- `FROZEN_MANIFEST` 23件はすべて `output/` 配下で、変更対象は非 member。
- `--run-iteration` の proposal consumer は `load_proposal_file`。ただし K2 wrapper の live 到達実績はまだ0件である。

## 総括

最も危険なのは、取得を一度も行わず `completed_empty` を自己申告するだけで K2 の全 proof chain を作れる点である。  
既存の正しさ・identity・性能 gate の順序や閾値、D1493 の「Git 解決を WAL に入れない」境界への直接変更は見つからなかった。  
ただし K2 入口、receipt 分類、data-boundary anomaly の受理集合に複数の fail-open がある。  
**現行 plan は採用不可。上記 must-fix と D1559 の明示再裁定後に再検査が必要である。** 静的検査のみで、テストは実走していない。