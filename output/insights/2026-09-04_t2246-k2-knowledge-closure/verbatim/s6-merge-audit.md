## 所見

1. **対象:** [orchestrator/campaign/p3_s4_loop.py:2174](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2246-k2-knowledge-closure/orchestrator/campaign/p3_s4_loop.py:2174)、[同:1979](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2246-k2-knowledge-closure/orchestrator/campaign/p3_s4_loop.py:1979)  
   **何が起きるか:** `--run-iteration` では `_campaign_cfg_for_site` が `main()` と `drive_iteration()` から計2回呼ばれる。ただし2回目は同一契約の再確認で、`bind_environment_contract` は同一値ならそのまま返す。  
   **成果物影響:** 現行では campaign ID・lock・knowledge receipt の bytes は変化せず、実効的な束縛遷移は1回だけ。  
   **重大度:** nit

must-fix / should-fix の所見はない。

## 合成箇所の判定

`--cc` の1箇所は意味的に成立する。

- `cfg` は `default_cfg()` の両分岐で構築された後、2174行目で site 契約を束縛され、knowledge campaign 準備より前に確定する。
- `_prepare_knowledge_campaign` は環境契約束縛済みの `cfg` に knowledge level/digest を加えて identity・receipt・projection を作るため、順序は正しい。
- `drive_iteration()` 内の再呼出しは上記 nit のとおり冪等で、異なる契約なら拒否される。
- `b4_reflux_ablation` の `default_cfg(..., b4_reflux_ablation=True, ...)` 経路と B4 marker 構築は残っており、`cfg` 構築は失われていない。
- `load_proposal_file` の production caller は `main()` の1件だけ。追加2引数は keyword-only・既定 `None` なので既存の直接呼出し規約も維持される。
- `layer3_report` の main 側変更は calibration floor 部分で、knowledge provenance の検証・射影 [layer3_report.py:802](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2246-k2-knowledge-closure/orchestrator/campaign/layer3_report.py:802) を変更していない。両テストファイルにも helper／fixture／test の二重定義はない。

## 裁定の充足

プラン v2:

1. **成立:** `declared_scope` / `retrieval_result` は optional、空 `sources` では両方必須で、`completed_empty ⇔ result_count == 0` と空 source の含意だけを強制している。
2. **成立:** 拡張 manifest のみ receipt v2、旧形はv1。旧 digestとreceipt全bytesは [test_knowledge_manifest.py:203](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2246-k2-knowledge-closure/orchestrator/tests/test_knowledge_manifest.py:203) のliteral goldenで固定されている。
3. **成立:** K2は `knowledge_input` と明示 `coder_role` の両方でのみ選択され、直接の片側指定は拒否、両省略は従来契約になる。manifestのみの従来flat経路も裁定どおり維持される。
4. **成立:** K2 wrapperは output schema検証後に `validate_output_semantics` へ渡される。
5. **成立:** `instruction_like_content_detected is True` は [p3_s4_loop.py:1828](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2246-k2-knowledge-closure/orchestrator/campaign/p3_s4_loop.py:1828) でfail-closedになる。
6. **成立:** tracked treeに `m07-control` はなく、[docs/agent-architecture.md:128](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2246-k2-knowledge-closure/docs/agent-architecture.md:128) にK2 consumer境界が反映されている。

明記する主張の境界:

1. **成立:** `completed_empty` が呼び手の宣言であり取得行為の証明ではない旨をreceiptの `declaration_status` に記録する。
2. **成立:** `selector` が記録上の宣言であり包含を強制しない旨も同じ欄に記録する。
3. **成立:** 検査対象がcampaign-bound projectionで、roleが実際に読んだ入力ではないことをagent architectureとrole契約に明記する。
4. **成立:** digest／識別子を維持してもreplay／resumeを主張しないことを実装commit `47e55de8f` の完了主張に明記している。
5. **成立:** K2 wrapperがconsumerを通った実成果物は0件であることを [docs/agent-architecture.md:143](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2246-k2-knowledge-closure/docs/agent-architecture.md:143) に明記する。

## 総括

最も危険な点は `_campaign_cfg_for_site` の二重呼出しだが、現実装では同一契約への冪等再確認であり成果物を変えない。  
競合箇所、近接自動merge、K2契約、Layer 3射影に受入を止める意味破れは見つからなかった。  
このmergeは受入へ進めてよい。  
検査は指定どおり静的のみで、pytestは実走していない。