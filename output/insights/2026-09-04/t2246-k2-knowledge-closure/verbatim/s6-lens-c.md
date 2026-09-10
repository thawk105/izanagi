## 所見

1. K2 manifest 付きの既存 flattened proposal 経路が維持されていない

   - 対象: [p3_s4_loop.py](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2246-k2-knowledge-closure/orchestrator/campaign/p3_s4_loop.py:1792)、[p3_s4_loop.py](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2246-k2-knowledge-closure/orchestrator/campaign/p3_s4_loop.py:2097)、[p3_s4_loop.py](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2246-k2-knowledge-closure/orchestrator/campaign/p3_s4_loop.py:2137)
   - 何が起きるか: `main` は `--knowledge-manifest` があれば、`--coder-role` の有無にかかわらず `knowledge_input` を loader へ渡す。したがって従来の `--knowledge-manifest ... --run-iteration flattened.json` は `knowledge_input != None` / `coder_role == None` となり、片側指定として拒否される。両引数を省略した直接関数テストは、この production 経路を覆っていない。
   - 成果物影響: 唯一実績のある generic role + flattened proposal の K2 経路が proposal admission 前に停止し、候補・WAL・terminal verdict を生成できない。receipt-only の部分 campaign は先に作られ得る。
   - 重大度: **must-fix**

2. duplicate JSON key により anomaly の fail-closed 分岐を迂回できる

   - 対象: [p3_s4_loop.py](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2246-k2-knowledge-closure/orchestrator/campaign/p3_s4_loop.py:1768)、[p3_s4_loop.py](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2246-k2-knowledge-closure/orchestrator/campaign/p3_s4_loop.py:1740)、既存の厳格 parser は [events.py](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2246-k2-knowledge-closure/orchestrator/codex_roles/events.py:373)
   - 何が起きるか: proposal file は通常の `json.load` で読み、duplicate key を拒否しない。たとえば同じ `data_boundary_report` 内に `instruction_like_content_detected: true`、続けて同名の `false` を置くと、前者が消えて schema・anomaly・semantic のすべてを通る。
   - 成果物影響: raw role 出力が instruction-like anomaly を含めて報告していても候補が correctness・identity・性能ゲートへ進み、最終的に certified 候補となり得る。
   - 重大度: **must-fix**

3. D1559 の再裁定が正本へ反映されず、現コードと decisions が矛盾している

   - 対象: [docs/decisions.md](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2246-k2-knowledge-closure/docs/decisions.md:48082)、[docs/decisions.md](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2246-k2-knowledge-closure/docs/decisions.md:48118)
   - 何が起きるか: decisions は依然として knowledge provenance を4欄固定とし、「参照を許した範囲」を `canonical_manifest.sources` から射影すると定めている。実装は6欄の拡張形を持ち、許可範囲を `declared_scope` に移している。裁定 A6 の「decisions へ記録する」が未実装である。
   - 成果物影響: 材料レポートの `declared_scope` と `declared_sources` の意味を正本どおりに監査できず、後続 consumer が新欄を余分なものとして拒否・除去するか、concrete sources を許可範囲として誤読し得る。
   - 重大度: **must-fix**

4. architecture 更新と、主張境界5点中2点の成果物記録が欠落している

   - 対象: [docs/agent-architecture.md](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2246-k2-knowledge-closure/docs/agent-architecture.md:131)、[coder-v4-autonomous-k2.md](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2246-k2-knowledge-closure/.claude/agents/coder-v4-autonomous-k2.md:124)、[s5-author.md](/home/SFC/tanab/.claude/jobs/9a120ef8/tmp/wave-t2246/artifacts/t2246-k2-knowledge-closure/s5-author.md:123)
   - 何が起きるか: architecture は今も `consumer: null`・自動発火なし・未配線と記す。また、「既存 K2 campaign は digest/ID のみ維持し replay/resume を主張しない」「K2 wrapper が loader を通った実成果物は0件」という2境界が変更成果物へ記録されていない。
   - 成果物影響: 参照文書が実際の validator 発火面を逆に説明し、配線実装を発火実績や replay 互換性として過大に報告できる。
   - 重大度: **must-fix**

静的確認では、旧2-key manifest の optional key は [knowledge_manifest.py](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2246-k2-knowledge-closure/orchestrator/campaign/knowledge_manifest.py:117) で省略され、正規化は同ファイル389行目の `sort_keys=True` を維持する。保存済み v1 manifest を再正規化した bytes は一致し、digest は指定どおり `6d867422…406`、v1 receipt 全体も byte-for-byte 一致した。

拡張形については、空の scope 配列、負値、bool、未知 status は producer/WAL/schema で拒否される。巨大な非負整数には上限がなく受理されるが、裁定が要求した2つの含意には違反しない。K0/K1、sort、trigger-gating の loader 本体、ならびに correctness・identity・性能ゲートの定義・順序・閾値には差分がない。既存テストの反転・緩和・skip・削除・xfail 化もなく、差分は追加のみである。pytest は実走していない。

未 commit 中の `wal.py` については、contract-loader capture が disk/HEAD 不一致で停止するため、certified artifact admission と材料レポート生成は `current-closure-unavailable` で拒否される。一方 `HISTORICAL_RAW` と直接の `wal.replay()` はこの live-closure gate を通らず、後者は現行 WAL validator で旧 v1 を読む。commit 後は live closure が再び取得可能になり、記録 closure と現 closure の相違自体は D1163 により拒否理由にならない。

## 裁定との差

- プラン v2 第3点: function-level の片側拒否は入ったが、production `main` で marker 不在の既存 flattened K2 経路を維持できていない。
- プラン v2 第6点: `m07-control` は登録されていないが、`docs/agent-architecture.md` の更新がない。
- A6: D1559 の改訂が `docs/decisions.md` に入っていない。
- 主張境界5点のうち、`completed_empty`、selector、campaign-bound projection の3点は入った。既存 campaign の replay/resume 非主張と、wrapper 実成果物0件の2点は欠落している。
- 不採用機構について、実取得の証明、scope/source 包含判定、受領証分類の WAL 側閉集合強制、role 分類と受領証分類の矛盾拒否は見つからなかった。

## 恒真になる述語

- [projection_guard.py](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2246-k2-knowledge-closure/orchestrator/campaign/projection_guard.py:324) が K2 wrapper と nested proposal の exact key 集合を先に検査するため、直後の output schema にある同じ2階層の required/additionalProperties 判定は常に通る。schema の型・enum・`knowledge_use` item 検査は恒真ではない。
- output schema 通過後に実行される [policy.py](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2246-k2-knowledge-closure/orchestrator/codex_roles/policy.py:487) の proposal object、axis、confidence、value の型・1..1000 判定は常に通る。implementation 文法・value一致、source index 上限、index重複は発火可能である。
- 同じく `knowledge_use` の array 性と各 `source_index` の integer/nonnegative 部分は schema 通過後には恒真。`source_index < len(sources)` は入力依存なので恒真ではない。
- [wal.py](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2246-k2-knowledge-closure/orchestrator/campaign/wal.py:879) の scope/result 再検査は、863行目の `_knowledge_manifest_digest` が同じ値を既に検査しているため拒否不能。
- [wal.py](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2246-k2-knowledge-closure/orchestrator/campaign/wal.py:1072) の receipt scope/result 再検査も、996行目および scope 順序検査後なので拒否不能。
- 拡張 schema の各 `if` にある `required: ["declared_sources"]` / `["injected_sources"]` は、外側ですでに両方 required のため恒真。
- 明示的な新述語ではないが、材料レポートの `declared_sources == injected_sources` は [wal.py](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2246-k2-knowledge-closure/orchestrator/campaign/wal.py:1044) の既存一致検査により producer 経路では恒真のままである。

## 総括

最も危険なのは、既存唯一の K2 flattened 経路を `main` が片側 marker として拒否し、受理集合を意図せず縮めた点である。  
加えて通常の `json.load` により、新設した anomaly gate は duplicate key で迂回できる。  
旧 v1 bytes、他アーム、既存ゲート、既存テスト期待値は維持されている。  
ただし4件の must-fix と裁定正本の矛盾が残るため、この実装を現状のまま段7へ進めてはならない。