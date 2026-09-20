単独段 dispatch: stage=review; sandbox=read-only; parent=/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-k2-loop-fig12

必読事項の射影 (各 path を読めなければ即停止して、その旨だけを `## 総括` に書いて終わること):
- 親 brief: /work/1/SFC/tanab/dev-wave-jobs/dev-wave-k2-loop-fig12/s1-brief.md
- 段 4 裁定 (plan v2・JSON 内容の下書き・変異事前登録): /work/1/SFC/tanab/dev-wave-jobs/dev-wave-k2-loop-fig12/s4-adjudication.md
- 段 5 author の最終報告: /work/1/SFC/tanab/dev-wave-jobs/dev-wave-k2-loop-fig12/codex/s5-author.md
- 段 5 の統合 patch (レビュー対象の差分そのもの): /work/1/SFC/tanab/dev-wave-jobs/dev-wave-k2-loop-fig12/codex/s5-author.patch
- 生成器 (統合後の現物): /work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-k2-loop-fig12/tools/plotting/plot_k2_loop_flow.py
- 流れ JSON (統合後の現物): /work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-k2-loop-fig12/tools/plotting/k2_loop_flow_2026-09-20.json
- test (統合後の現物): /work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-k2-loop-fig12/orchestrator/tests/test_plot_k2_loop_flow.py
- 親が実データで生成した provenance (drawn_items・arrows・caption の現物): /work/1/SFC/tanab/dev-wave-jobs/dev-wave-k2-loop-fig12/scratch/fig12_k2_manual_loop_dataflow.provenance.json
- caption_source の稿 (図の全表示文字列の出所。§0.1 単位、§1.1 経路、§1.2 知識源、§1.4 役割と入力の型、§1.5 判定規則、§2.1 主表、§2.2 巡ごとの表、§2.3 届いた / 効いた、§2.4 規律 6、§2.5 正しさ、§3 限定): /work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-k2-loop-fig12/docs/paper-story/results/2026-09-20-k2-manual-loop-three-rounds.md
- role 定義 3 file: /work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-k2-loop-fig12/.claude/agents/planner-v4.md、/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-k2-loop-fig12/.claude/agents/coder-v4-autonomous-k2.md、/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-k2-loop-fig12/.claude/agents/critic.md
- 3 巡目の実入力 (key 集合と exact 6 field の現物): /work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-k2-loop-fig12/output/insights/2026-09-19/k2-loop-round3/materials/planner-input-4.json、/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-k2-loop-fig12/output/insights/2026-09-19/k2-loop-round3/materials/coder-input-4.json、/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-k2-loop-fig12/output/insights/2026-09-19/k2-loop-round3/materials/diagnosis-4.json
- 作図規約の正本: /work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-k2-loop-fig12/tools/plotting/FIGURE_CONVENTIONS.md

この「読めなければ即停止」は上の射影 file にだけ掛かる。自分で組み立てた path が不在でも停止せず、1 行書いて実在 file を探し直し、最後まで続けること。
**出力は file に書かず、最終メッセージの本文に全文を書け** (親の launcher が保存する)。書込可能 tmp が無いので pytest 緑は要求しない — 静的検査でよい。テスト実測は親が行う。予算が尽きそうなら途中結論を出力形式どおり書いて終われ (無出力が最悪)。

## 前置き — この依頼の性質

研究用 repo の**論文用の説明図 (matplotlib の模式図) の生成器・入力 JSON・単体 test** の敵対レビューである。セキュリティでも攻撃でもない。生成器は凍結済みの稿 (Markdown) から人が JSON へ写した「3 巡のデータフロー」を描くだけで、判定・値・認証を再計算しない。親 brief と段 4 裁定自身も検査対象である。

# 依頼 — レビュー B: 正しさ境界・整合・実効性 (稿との逐語照合を含む)

## レンズ B

1. **稿との逐語照合 (一次資料からの事実再抽出)**: provenance の `drawn_items` の**全文字列**と `arrows` の全 label、caption の全文を、稿の該当節と 1 件ずつ突き合わせ、表にする (列: 表示文字列 / 稿の出所 (節・表の行) / 一致・言い換え・**不一致**・**稿に無い**)。特に: (a) 巡ごとの planner の direction / magnitude、coder / proposal の値、既知値か否か、評価の有無、job id と preflight 拒否の job、critic の attribution / recommend、規律 6 の自己申告の形式、(b) 親の射影 key 集合 (planner 4 / coder 5、巡 3 の `k2_critic_diagnosis`)、diagnosis の 6 field 名、(c) 還流の矢印 (実測 2 回の from / to、診断 1 回の from / to、absent 3 本) が稿 §0.1・§2.2・§2.3 の記述と一致するか、(d) 日付 (proposal / evaluation) が §2.7 / §2.2 と一致するか、(e) role の遮断の記述 (planner / coder = tools なし、critic = legacy で Bash) が §1.4 と role 定義 frontmatter の両方と一致するか。
2. **正しさ境界**: 生成器が稿を読んで値・判定を再計算していないか (anchor の一意性検査と SHA-256 の記録だけが許される)。`certified` / `serializable` / `anomalies none` の描き方が「正しさ gate の意味」を超えて性能認証・候補間選択に読めないか。規律 1 (verify = trace-enabled / bench = trace-disabled の別 build) の描き分けが正しいか。
3. **拒否・受理の実効性**: 裁定 plan v2 §2〜§4 の拒否条件 (未知 / 不足 / 重複 key、enum、value の範囲と coder-proposal 一致、`evaluated` ⇔ `evaluation` 非 null、`not-a-round` の制約、arrow endpoint の実在、anchor の一意性、diagnosis_fields / planner_keys / coder_keys の完全一致、自由文の数量、caption_source path、role `tools_none` ⇔ frontmatter) が**すべて実装され、test が実体の関数を通して負例を 1 つずつ踏む**か。不足・恒真・重複を列挙する。
4. **layout check の実効性**: 矢印線分 × Text bbox の交差判定が本当に線分と矩形の交差を計算しているか (bbox 同士の近似で恒真・恒偽になっていないか)、曲線矢印を使っていれば線分近似の粒度、label Text と自線分の関係、`_publish_outputs` が check を保存前に呼ぶ経路、失敗時に file を残さない経路。
5. **provenance の閉包**: `inputs` (flow / caption_source / role_definition 3 本) と `generator` / `outputs` / `roles[].sha256` が実 bytes から計算され、test が独立に hashlib で照合するか。`drawn_items` の期待集合を生成器が JSON から組み立て保存前に照合するか、test が JSON から**独立に**期待集合を組んで provenance と照合するか。
6. **変異事前登録 (M1〜M10) の単一理由性**: 各変異について、位置 (関数) が一箇所か、同じ入力を前後・内側で拒否する層が無いか (あれば mask で SURVIVED になる)、kill する test の nodeid。author 報告の対応表を鵜呑みにせず現物で確かめる。
7. **meta-test 適合**: 自走 harness (`__main__` で `pytest.main`)、subprocess env の `PYTHONDONTWRITEBYTECODE`、test file の列挙・命名に制約を課す meta-test (plain_runner_coverage、bytecode guard、その他自分で洗い出す) に静的に適合するか。

## 出力形式 (最後の節は必ず `## 総括`。`#` を 2 個。`### 総括` と書いてはならない。見出しはすべて H2)

## 逐語照合表
1 の表 (全 drawn_items・全 arrow label・caption の各文)。不一致・稿に無いものは太字。
## 所見 (must-fix)
番号付き。各所見に file:line (統合後の現物の行番号)、根拠 (現物の引用 1〜3 行)、放置時に成果物 (図・provenance・README・受入) がどう変わるか 1 行、推奨 fix 1 行。
## 所見 (should)
同上。
## 所見 (nit)
同上、短く。
## 拒否条件の実装・test 対応表
裁定の各拒否条件 / 実装の関数:行 / 負例 test の nodeid / 恒真・不足の判定。
## 変異の単一理由性
M1〜M10 ごとの判定と根拠。
## 総括
GO / NO-GO と must-fix の件数、根拠を 5 行以内。
