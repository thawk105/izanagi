単独段 dispatch: stage=fix; sandbox=workspace-write; parent=/work/1/SFC/tanab/izanagi/.codex/worktrees/t2797-eb-unit-b

必読事項の射影: (下記をすべて読む。読めなければ即停止し、読めなかった path を報告する)

- /work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2797-b5-effect-bundle/s5-author-B-prompt.md — **段 5 実装子 B の契約 (全文を継承する。所有 2 file・commit しない・テストを走らせない・docs を編集しない等の制約はすべてそのまま有効)**。読めなければ即停止
- /work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2797-b5-effect-bundle/codex/s5-author-B.md — 前回の実装子 B の報告 (知識解決を `NotImplementedError` で止めた理由)。読めなければ即停止
- /work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2797-b5-effect-bundle/s4-adjudication.md — 段 4 裁定 (D-3・D-4・MB1〜MB8)。読めなければ即停止
- /work/1/SFC/tanab/izanagi/.codex/worktrees/t2797-eb-unit-b/tools/b5_llm_round.py と orchestrator/tests/test_b5_llm_round.py — 所有 file (前回の成果、commit `f5554dca1`)。読めなければ即停止
- /work/1/SFC/tanab/izanagi/.codex/worktrees/t2797-eb-unit-b/orchestrator/campaign/knowledge_manifest.py — 参照のみ (`load_and_resolve_manifest`・`planner_projection`)。読めなければ即停止
- /work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2797-b5-contrast/llm_round.py — 試走版 (参照のみ、`knowledge_input()` の元)。読めなければ即停止

## 親の裁定 (前回の報告の問いへの回答)

前回の指示「tool は subprocess を起動しない」は、**tool 自身のコードが `subprocess` を import・呼出ししない**という意味だった。既存の `KM.load_and_resolve_manifest()` が内部で行う
読み取り専用の git 呼出し (blob 種別・raw bytes の取得) は、試走版と同じ既存関数の使用として許す。tool 側に subprocess の import・呼出し・新しい process 起動箇所を足さないことは引き続き守る。

## 作業 (fix B1)

1. `knowledge_input()` を試走版と同じ手順で完成させる: `KM.load_and_resolve_manifest(<--knowledge-manifest>, repo_root=<repo root>)` で解決し、`knowledge_manifest_sha256` が
   `396cd5594c3f22fb0d52476aa3eec51e62f26c5d3e81b1e25a5935697b73588e` と一致すること、`KM.planner_projection(resolved)` を `ensure_ascii=False, sort_keys=True, indent=2` の UTF-8 bytes にしたものが
   repo 内の照合先 `output/insights/2026-09-18/t2746-k2-loop-round2/materials/knowledge-input.json` の raw bytes と一致することを確かめ、不一致なら停止する (試走版と同じ fail-closed)。
   `NotImplementedError` を除く。
2. test の知識解決を通す: MB2・MB3・MB8 の test (`test_rejected_opportunity_preserves_evaluation_number`、`test_initial_and_inherited_inputs`、`test_registered_round1_prompt_golden`) が
   実物の resolver を通って変更箇所まで到達するようにする。manifest は repo に既にある実物を使う (例 `output/insights/2026-09-22/t2797-effect-bundle/bundle/knowledge-manifest-wal-only.json` は
   この木にはまだ無いので、test 内の一時 dir に試走と同じ内容 `{"knowledge_level":"K2","sources":[{"identity":{"commit":"2fa13a262a53b7f4e610a40a7a7af7f86fc9d621","path":"output/campaigns/p3-s4-loop-s4-autonomous-0b53a387/runs/wal.jsonl"},"kind":"repo_artifact","sha256":"2163b794fa3b1fce4de76a1b69262cadfc095bd986225a7266d6eacb6210a611"}]}`
   を書いて使う)。resolver・射影関数を stub しない。
3. golden (`test_registered_round1_prompt_golden`) で、試走 prompt に D-3 (1)〜(4) の `bytes.replace` を当てた期待値と tool の出力が一致するかを静的に追い、置換で表せない差が残るなら
   **tool を合わせず**報告に列挙する (期待値を tool の render で作らない)。

## 制約 (実装子 B の契約をすべて継承)

- **既存テストの期待値を変更しない。** 反転・緩和・skip・削除をしない。赤なら実装側が誤りとする。期待値が誤りなら実装を変えず報告して止める。
- **`git commit` を一度も実行しない。** 所有 2 file 以外を作成・編集しない。docs を編集しない。**テストを走らせない** (静的検査 `python3 -m py_compile` は可)。
- tool のコードに `subprocess` の import・呼出しを足さない。network・LLM・`ANTHROPIC_*` 環境変数に触れない。
- 予算が尽きそうなら、途中までの内容を下記の報告形式どおりに書いて終える。

## 報告形式

1. 変更した箇所 (関数名・行)
2. 知識解決の手順と、試走版との一致点・差分
3. 静的検査の結果 (実行したコマンドと rc)
4. MB2・MB3・MB8 が変更箇所へ到達する根拠と、golden の置換で表せない差 (あれば全部)
5. 未実走であることの明記と、親が走らせるべき nodeid / file の候補
最後に `## 総括` を置く。
