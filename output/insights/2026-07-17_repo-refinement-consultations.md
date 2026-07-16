# 2026-07-17 リポジトリ棚卸し・リファインメント — 棚卸し裁定と codex 敵対相談 2 本の記録

- 実行: codex exec, model=gpt-5.6-sol, reasoning=max, sandbox=read-only, cwd=worktree (基準 b943447)。棚卸しは Claude workflow 9 レーン (sonnet, medium)
- 目的: ユーザー依頼「全ファイル棚卸し + 低価値物の掃除 (課題1) → 明瞭化・glossary 圧縮 (課題2) → docs 外の実態検査 (課題3) → docs への反映確認 (課題4) → docs リファイン (課題5)」の課題 1 裁定と、課題 2〜5 実行計画の敵対検証
- 本ファイルは相談 prompt と出力の逐語保存 (failures F20 対応: scratchpad にだけ置かない)。裁定も本ファイルに記録する

## 棚卸し (workflow 9 レーン) の結果と課題 1 の裁定

- 対象 = tracked 835 ファイル (output/ はディレクトリ/パターン単位のグループ判定を含む 305 判定)
- 判定: keep 303 / unsure 2 / **delete 候補 0**。unsure 2 件 (orchestrator/tests/test_codex_role_runtime.py と test_s8b_oracle_report.py の参照先実在) は親が tools/run_codex_role.py・orchestrator/campaign/s8b_oracle_report.py の実在を確認して keep 確定
- **課題 1 の裁定: 削除対象なし。** 全ファイルが (a) 現行文書からの参照、(b) 凍結契約 (docs/archive/・docs/roadmap-history/・output/insights の逐語 F20・s8b 裁定待ちパッケージ)、(c) parity 検査 (tools/check_codex_agents.py が .claude 13 role と .codex 13 adapter の全単射を fail-closed 検査)、(d) 成果物三本柱の試行台帳 (output/ の WAL・provenance・report・freeze・checkpoint)、のいずれかで保護されている。ジャンク (.pyc/.log/.tmp/.bak、孤児 fixture、orphan テスト) は grep・pytest --collect-only で 0 件
- レーン別の要点: docs 直下 22 = 全て地図掲載 + 被参照 5〜88 件 / docs サブディレクトリ 31 = README 契約と現物が完全一致 / campaign 75 = 全てに import・docs・output 実成果物のいずれか複数の参照 (s6_amendment_20260713_fence.py も failures.md F12 復旧手順の実体として現役) / tests 64 = collect 948 件エラーなし・orphan なし / output 538 = README の二軸契約内に全収容・残骸 0 / tools・hooks・src・patches 33 = 全て正本 README から来歴参照 / .claude・.codex 27 = parity 検査対象

## 相談 A/B の裁定 (親による real/refuted)

- **相談 A (掃除プラン攻撃): must-fix 8 + should 1、全件 real、refuted 0。** いずれも「削除基準の機械適用による誤削除」の攻撃シナリオで、棚卸しが delete 候補 0 を返したため実害は未然。採用した恒久事項: (1) 完了検査を check_docs + テストだけでなく git status 再確認 → check_codex_agents → check_docs → commit → check_ai_provenance の固定順に拡張、(2) テスト回帰比較は件数でなく node ID 集合 + 結果分類で行う、(3) check_docs.py の明示列挙対象不在 silent-skip (fail-open) は修正対象 (課題 3)、(4) output/ の keep 対象は WAL・insight・env に限らず campaign.lock・report・provenance・checkpoint (loop_state.json)・amendment replayer を含む artifact type で定義
- **相談 B (リファイン計画攻撃): must-fix 10 + should 3、全件 real、refuted 0。** 採用した実行前提: (1) freeze JSON の SHA 推移閉包 = no-edit 集合 (docs/phase3-main-experiment.md・docs/phase3-8b-descriptor-design.md + orchestrator 実装 11 本 + external/ccbench 2 本。編集は s8b 裁定・再凍結後に分離)、(2) 文書の権限分類 living / append-only / frozen snapshot / raw evidence / generated-copy を先に確定し、frozen・raw は課題 2/5 の文体修正対象外、(3) 課題 2 の前に docs 外 243 ファイルの read-only 主張監査を行い「嘘の台帳」を凍結してから文体に触る (監査対象の嘘を文体修正で消さない)、(4) glossary 圧縮は living docs / frozen / code / generated で層別した単語境界 grep を判断材料にし、統合後も全 surface form を見出しまたは別名行に逐語保持 (grep 索引契約の維持)、(5) 課題 4 は「実装 → 契約 owner → docs 地図ポインタ」の三列突合で docs→code の幽霊主張も検査、(6) 課題 5 の後に独立コンテキストの最終 diff レビュアを置く
- 反映後の実行順: 保護集合確定 → 主張監査 (read-only) → 課題 2 (living docs のみ) → 課題 3 (裁定 + 修正) → 課題 4 → 課題 5 → 独立最終レビュー → worklog 吸収・provenance 監査

以下、相談 2 本の prompt と出力の逐語。

---

## 相談 A prompt (逐語) — 掃除プラン攻撃

`````markdown
あなたは敵対的レビュアーです。以下の「リポジトリ掃除プラン」を攻撃してください。所見は各件について severity (must-fix / should / nit)、攻撃シナリオ (何がどう壊れるか具体的に)、根拠 (file:line または実在のファイルパス — cwd のリポジトリを実際に読んで確認すること)、提案 (どう直すか) の 4 点で構造化して返してください。誤っている前提、見落とされた参照関係、削除してはいけないものが削除候補になり得る穴を特に探してください。

## 背景

このリポジトリ (izanagi) は「ワークロード特化の並行性制御 (CC) を AI が合成・選択するシステム」。成果物は (1) certified な CC 選択結果、(2) proof chain 付き材料レポート、(3) 再現可能な試行台帳。docs/roadmap.md が戦略の正本、docs/worklog.md 末尾 + docs/phase3.md が可変状態の正本。現在 Phase 3 段 8b の floor protocol パッケージが「ユーザー裁定待ち」(output/insights/2026-07-16_s8b-floor-protocol-*)。

ユーザーの依頼: 「古すぎてもう参照されないであろう記録、コンテキスト価値の低い文章や、価値が低くてもう使わないと思われるプログラムはお掃除してください。roadmap.md を必ず考慮すること」。

## 掃除プラン (攻撃対象)

### 判断基準
1. 成果物三本柱 (certified 選択結果 / 材料レポート / 再現可能な試行台帳 = output/ の WAL・insight・env calibration) に属するもの = keep
2. 凍結契約があるもの = keep: docs/archive/ (凍結記録)、docs/roadmap-history/ (版凍結 = 研究記録、roadmap 冒頭)、output/insights/ の相談逐語 (failures F20)、s8b 裁定待ちパッケージ一式
3. external/ (CCBench submodule、D16/D18/D20)、patches/ (意図的 broken variant = positive control、合成 variant、診断計器) = keep
4. 削除候補 = 次を全て満たすもの: (a) CLAUDE.md / docs/README.md / roadmap / 現行 phase doc (phase3.md) / worklog 末尾のどこからも参照されない、(b) git grep で他ファイルからの参照がない、(c) 用途が消滅している (superseded・実験終了後の再生成可能な中間物・一時ファイル)
5. 迷ったら keep (git 履歴に残るとはいえ、削除は PR レビューで人間が最終確認)

### 手順
1. 9 レーン並列の棚卸し (docs 上位 / docs サブディレクトリ / orchestrator/campaign ×2 / orchestrator その他 / orchestrator/tests / output / tools+hooks+src+patches+トップ / .claude+.codex)。各ファイルの目的・最終 commit 日・被参照を収集し keep / delete_candidate / unsure を仮判定
2. 親が裁定して削除リストを確定
3. 削除候補ごとに独立エージェントが敵対検証 (「削除してはいけない理由」を探して refute を試みる)
4. git rm + dangling reference の修正 → tools/check_docs.py + orchestrator テスト (基準: 925 passed / 11 failed は ccbench submodule 未 checkout の環境要因) → コミット

### 私が既に認識しているリスク (これ以外の穴を重点的に)
- 削除による dangling reference (docs 間・コード内パス参照)
- output/s6-rounds (314 ファイル) の性質誤認 — 試行台帳なら keep、再生成可能な中間物なら削除候補
- テストの orphan 誤判定 (動的 import・fixture 経由の参照は grep で見えない)
- handoff / worklog の運用契約 (check_docs.py が形式を lint している) を壊す編集

リポジトリを実際に調べ、このプランの穴を突いてください。特に「基準 4 を機械的に適用すると誤って消えるが、実は価値があるもの」の具体例をファイルパス付きで挙げてください。
`````

## 相談 A 出力 (逐語)

`````markdown
## 結論

このまま `git rm` へ進むのは危険です。must-fix が 8 件あります。特に、基準 4 を文字列参照ベースで適用すると、実際に「参照なし・実験終了・再生成可能」に見える重要物が複数あります。

### 1. 成果物三本柱と `output/` の対応づけが狭すぎる

- severity: must-fix
- 攻撃シナリオ: `output/` の keep 対象を WAL・insight・env calibration に限定すると、材料レポート、identity の pre-image、provenance が「再生成可能な中間物」へ落ちる。具体的には [layer3_report.json:1](/home/SFC/tanab/github/izanagi/.claude/worktrees/repo-refinement/output/campaigns/p3-s8a-trigger-loop-s8a-trigger-autonomous-3f72ecd5/reports/layer3_report.json:1) は repo-relative path の直接参照が 0 件で、基準 4(a)(b) を満たし得る。しかしこれは Layer 3 の実成果物である。また各 `campaign.lock` は名前だけ見ると stale lock に見えるが、削除禁止の identity pre-image である。
- 根拠: roadmap は材料レポートを最終成果物として定義している [docs/roadmap.md:123](/home/SFC/tanab/github/izanagi/.claude/worktrees/repo-refinement/docs/roadmap.md:123)。`output/README.md` は `campaign.lock`・WAL・report/provenance・凍結 spec を proof chain の構成物としている [output/README.md:8](/home/SFC/tanab/github/izanagi/.claude/worktrees/repo-refinement/output/README.md:8)、[output/README.md:34](/home/SFC/tanab/github/izanagi/.claude/worktrees/repo-refinement/output/README.md:34)。さらに generator は、生成済み v1 report を再生成しない契約を明記している [layer3_report.py:16](/home/SFC/tanab/github/izanagi/.claude/worktrees/repo-refinement/orchestrator/campaign/layer3_report.py:16)。
- 提案: keep 基準を「WAL・insight・env」ではなく、`campaign.lock`、凍結 spec、WAL、variant/source identity、checkpoint、report、provenance、確定 verdict、予算台帳まで含む artifact type で定義する。`output/README.md:40` が明示する throwaway 生 trace・一時 binary・ローカル残骸だけを削除面にする。

### 2. 無参照の one-off program が、実は再現手順そのもの

- severity: must-fix
- 攻撃シナリオ: [s6_amendment_20260713_fence.py:2](/home/SFC/tanab/github/izanagi/.claude/worktrees/repo-refinement/orchestrator/campaign/s6_amendment_20260713_fence.py:2) はファイル名への外部参照がなく、実験も終了済みなので、基準 4 の典型的な delete candidate になる。削除すると、フェンス欠陥後の raw attempt 再分類と final 再導出を現在の checkout で再現できなくなる。残る JSON 台帳は「何が変わったか」は持つが、「どう機械再導出したか」を実行できない。
- 根拠: スクリプト自身が「追加呼び出しゼロの再分類」「冪等な再現手順」と明記する [s6_amendment_20260713_fence.py:4](/home/SFC/tanab/github/izanagi/.claude/worktrees/repo-refinement/orchestrator/campaign/s6_amendment_20260713_fence.py:4)、[s6_amendment_20260713_fence.py:16](/home/SFC/tanab/github/izanagi/.claude/worktrees/repo-refinement/orchestrator/campaign/s6_amendment_20260713_fence.py:16)。一方、[amendment-2026-07-13-fence.json:1](/home/SFC/tanab/github/izanagi/.claude/worktrees/repo-refinement/output/s6-rounds/amendment-2026-07-13-fence.json:1) は規則と旧 commit を記録するだけで、generator path/hash を持たない。
- 提案: この種の migration/amendment/replay script は試行台帳の一部として keep する。削除するなら、汎用 replayer への移植、generator の path/hash/commit 束縛、凍結 raw 入力からの byte-level 再現テストを先に成立させる。

### 3. `loop_state.json` は WAL ではないが、削除すると resume が fail-open する

- severity: must-fix
- 攻撃シナリオ: `loop_state.json` を「WAL から再生成できる checkpoint」と判断して削除すると、次回 resume で `load_loop_state()` が `None` を返し、新規状態として iteration・wall budget・reverse count・whiteboard が初期化される。既存 campaign に追加 iteration を流したり、予算を再開時に実質リセットしたりする。
- 根拠: checkpoint が無いと feedback loop が死ぬこと、WALとは別の planner 射影状態であることが明記されている [p3_s4_loop.py:324](/home/SFC/tanab/github/izanagi/.claude/worktrees/repo-refinement/orchestrator/campaign/p3_s4_loop.py:324)。不存在は正常な新規状態として扱われる [p3_s4_loop.py:416](/home/SFC/tanab/github/izanagi/.claude/worktrees/repo-refinement/orchestrator/campaign/p3_s4_loop.py:416)、[p3_s4_loop.py:727](/home/SFC/tanab/github/izanagi/.claude/worktrees/repo-refinement/orchestrator/campaign/p3_s4_loop.py:727)。実物にも iteration と whiteboard が残る [loop_state.json:1](/home/SFC/tanab/github/izanagi/.claude/worktrees/repo-refinement/output/campaigns/p3-s8a-trigger-loop-s8a-trigger-autonomous-3f72ecd5/loop_state.json:1)。roadmap も checkpoint・予算・再開の orchestrator 所有を自律性要件にしている [docs/roadmap.md:116](/home/SFC/tanab/github/izanagi/.claude/worktrees/repo-refinement/docs/roadmap.md:116)。
- 提案: `loop_state.json` は campaign が明示的に finalized され、かつ状態を WAL から完全再構成できる verifier がある場合だけ削除可能にする。現状は全件 keep。

### 4. `git grep` は動的発見・慣習的 entry point を参照として捉えない

- severity: must-fix
- 攻撃シナリオ: 文字列参照がないことを「consumer なし」と誤認する。実例は次のとおり。
  - `.codex/role-adapters/axis-proposer.json` は full path・basename とも外部 `git grep` 0 件だが、checker が role 名から path を動的生成する。
  - [verifier/__main__.py:2](/home/SFC/tanab/github/izanagi/.claude/worktrees/repo-refinement/orchestrator/verifier/__main__.py:2) は直接参照されないが、Python が `python -m verifier` で発見する。
  - [devcontainer-lock.json:3](/home/SFC/tanab/github/izanagi/.claude/worktrees/repo-refinement/.devcontainer/devcontainer-lock.json:3) は直接参照されないが、feature の resolved digest/integrity を保存している。
  - [tools/plotting/README.md:3](/home/SFC/tanab/github/izanagi/.claude/worktrees/repo-refinement/tools/plotting/README.md:3) は exact path 参照がないが、proof-chain 付き作図の実行手順である。
- 根拠: adapter path は実行時に生成される [spec.py:872](/home/SFC/tanab/github/izanagi/.claude/worktrees/repo-refinement/orchestrator/codex_roles/spec.py:872) うえ、全件一致が checker の契約である [check_codex_agents.py:216](/home/SFC/tanab/github/izanagi/.claude/worktrees/repo-refinement/tools/check_codex_agents.py:216)。verifier CLI も `python -m verifier` を公開面として記載する [cli.py:4](/home/SFC/tanab/github/izanagi/.claude/worktrees/repo-refinement/orchestrator/verifier/cli.py:4)。作図規約は新しい図種のコマンドを README に追加するよう要求する [FIGURE_CONVENTIONS.md:87](/home/SFC/tanab/github/izanagi/.claude/worktrees/repo-refinement/tools/plotting/FIGURE_CONVENTIONS.md:87)。
- 提案: file-level grep に加え、所有ディレクトリ、glob/discovery、`__main__`、README、lockfile、schema、manifest、conventional config を明示した retention manifest を作る。CLI smoke testと専用 checkerで消費面を検査する。

### 5. `check_docs.py` は重要文書の削除を fail-open で通す

- severity: must-fix
- 攻撃シナリオ: `LIVING_DOCS` に載る文書を削除し、参照側も「dangling reference 修正」として消すと、`check_docs.py` は削除された文書を黙って skip して成功する。root `README.md`、`output/README.md`、`orchestrator/README.md`、plotting README、output JSON はそもそも検査集合外である。
- 根拠: 必須候補は固定リストに列挙されている [check_docs.py:25](/home/SFC/tanab/github/izanagi/.claude/worktrees/repo-refinement/tools/check_docs.py:25) が、不存在時は `continue` する [check_docs.py:116](/home/SFC/tanab/github/izanagi/.claude/worktrees/repo-refinement/tools/check_docs.py:116)。パス実在性検査も living docs の行だけが対象である [check_docs.py:72](/home/SFC/tanab/github/izanagi/.claude/worktrees/repo-refinement/tools/check_docs.py:72)。
- 提案: 固定列挙の文書は不存在を即違反にする。別途、全 tracked Markdown/JSON の repository-relative path、Markdown link、campaign-relative artifact ref を検査する cleanup 専用 checker を追加する。

### 6. 完了検査がリポジトリの必須手順を満たしていない

- severity: must-fix
- 攻撃シナリオ: plan は `check_docs + orchestrator tests → commit` で終わるため、dormant adapter の欠損・byte driftや、commit trailer 欠落を見逃す。長い並列棚卸し後に `git status` を再確認しなければ、相談中に入った別差分を同じ commit に混ぜることもできる。
- 根拠: AGENTS は関連テストに加え `check_codex_agents.py` と `check_docs.py` を必須化し、commit 後に provenance 監査を要求する [AGENTS.md:26](/home/SFC/tanab/github/izanagi/.claude/worktrees/repo-refinement/AGENTS.md:26)。Codex adapter の正規検査も明記されている [.codex/agents/README.md:82](/home/SFC/tanab/github/izanagi/.claude/worktrees/repo-refinement/.codex/agents/README.md:82)。provenance は commit 後の全履歴監査が正本である [docs/ai-provenance.md:97](/home/SFC/tanab/github/izanagi/.claude/worktrees/repo-refinement/docs/ai-provenance.md:97)。
- 提案: 最終順序を「最新 `git status`/diff確認 → artifact検査 → 関連テスト → `check_codex_agents` → `check_docs` → worklog吸収・handoff削除 → commit → `check_ai_provenance`」に固定する。

### 7. `925 passed / 11 failed` は安全な回帰 oracle ではない

- severity: must-fix
- 攻撃シナリオ: 既知の11件が消え、新しい11件が失敗しても件数は同じである。テストファイルを削除して collection が減っても、別の parametrization 増加などで総数が一致し得る。さらに submodule 不在による失敗を既知 baseline とすると、実 CCBench 結線の破損が常にノイズへ埋まる。
- 根拠: 現 handoff はこの失敗 baseline を採用している [2026-07-17-repo-refinement.md:23](/home/SFC/tanab/github/izanagi/.claude/worktrees/repo-refinement/docs/handoff/2026-07-17-repo-refinement.md:23)。しかしテスト契約は、submodule 等が無い場合は FAIL ではなく明示 SKIP とする [orchestrator/tests/README.md:10](/home/SFC/tanab/github/izanagi/.claude/worktrees/repo-refinement/orchestrator/tests/README.md:10)、[orchestrator/tests/README.md:23](/home/SFC/tanab/github/izanagi/.claude/worktrees/repo-refinement/orchestrator/tests/README.md:23)。
- 提案: FAIL は 0 件を要求する。submodule を checkout できない環境では node ID と理由が固定された SKIP にする。前後で `pytest --collect-only` の node ID 集合、結果分類、skip理由を比較し、件数だけを比較しない。

### 8. 既存 proof chain の path/hash を全件再検証する工程がない

- severity: must-fix
- 攻撃シナリオ: layer3 report は campaign 内全 artifact の相対 path と SHA-256 を記録するが、cleanup 後に既存 report の参照先がまだ存在し hash が一致するかを検査する仕組みがない。別 campaign の provenance や report を削除しても、通常テストは新しい report を作るだけなので通り得る。
- 根拠: artifact refs は campaign 全ファイルから生成される [layer3_report.py:134](/home/SFC/tanab/github/izanagi/.claude/worktrees/repo-refinement/orchestrator/campaign/layer3_report.py:134)。実 report にも相対 path/hash が保存されている [layer3_report.json:1](/home/SFC/tanab/github/izanagi/.claude/worktrees/repo-refinement/output/campaigns/p3-s8a-trigger-sweep-read-heavy-sweep-654d5cd7/reports/layer3_report.json:1)。一方、実 campaign を使うテスト対象は一つだけである [test_layer3_report.py:17](/home/SFC/tanab/github/izanagi/.claude/worktrees/repo-refinement/orchestrator/tests/test_layer3_report.py:17)。
- 提案: 全 `output/campaigns/*` を巡回し、既存 material report の `artifact_refs`、provenance source、WAL、lock、freeze、env calibration の path/hash/schema を検証する `check_output_artifacts` 相当を削除前後に実行する。

### 9. 凍結族は `archive/` と `roadmap-history/` だけではない

- severity: should
- 攻撃シナリオ: `docs/paper-story/` の古い日付ファイルを「現行主張でなく、コンテキスト価値が低い」として index と一緒に削除できる。そこには旧過大主張の訂正根拠や、どの時点で何を主張できなかったかが残っており、論文執筆時の監査材料が失われる。
- 根拠: paper-story は時点ごとの凍結スナップショットで、上書きせず新版を追加する契約である [docs/paper-story/README.md:3](/home/SFC/tanab/github/izanagi/.claude/worktrees/repo-refinement/docs/paper-story/README.md:3)。実際、補助ノートには旧 p 値、gain、abort 半減という過大表示の訂正がある [notes-2026-07-10.md:10](/home/SFC/tanab/github/izanagi/.claude/worktrees/repo-refinement/docs/paper-story/notes-2026-07-10.md:10)。しかも `check_docs.py` は paper-story を凍結族として検査対象外にしている [check_docs.py:21](/home/SFC/tanab/github/izanagi/.claude/worktrees/repo-refinement/tools/check_docs.py:21)。
- 提案: protected set に `docs/paper-story/`、事前登録、`output/*-freeze/`、確定 report、amendment/replay、承認済み protocol を追加する。凍結物の削除は「参照なし」ではなく、明示的な tombstone とユーザー承認を条件にする。

削除候補には「参照が見つからない」という負の証明ではなく、少なくとも owner、動的 consumer、generator、入力、再生成コマンド、clean checkout での同値結果、artifact graph 検査結果を含む削除証明を要求すべきです。現行プランでは、特に material report・amendment replayer・checkpoint の三種類を誤削除する余地が残っています。`````

## 相談 B prompt (逐語) — リファイン計画攻撃

`````markdown
あなたは敵対的レビュアーです。以下の「リポジトリ リファインメント計画 (課題 2〜5)」を攻撃してください。所見は各件について severity (must-fix / should / nit)、攻撃シナリオ (何がどう壊れるか具体的に)、根拠 (file:line または実在のファイルパス — cwd のリポジトリを実際に読んで確認すること)、提案 (どう直すか) の 4 点で構造化して返してください。

## 背景

このリポジトリ (izanagi) は「ワークロード特化の並行性制御 (CC) を AI が合成・選択するシステム」。docs は日本語、コードは Python (orchestrator/hooks/tools) + C++ (CCBench submodule)。tools/check_docs.py が文書 lint、tools/check_codex_agents.py が .claude/agents と .codex adapter の parity 検査、hooks/ が書き込み防壁。docs/decisions.md は `grep -n "^## D"` を目次とする索引規約があり、docs/glossary.md は「用語を grep して該当項目だけ読む」運用。Phase 3 段 8b の floor protocol パッケージが「ユーザー裁定待ち」(output/insights/2026-07-16_s8b-floor-protocol-*) で、改変禁止。

ユーザーの依頼:
- 課題2: 分かりにくい文章・プログラムを洗練。ルー大柴のような英語混じり・造語を極力減らし、docs/glossary.md をなるべく圧縮する
- 課題3: docs 以外 (orchestrator/tools/hooks/src/patches/.claude/.codex) の嘘・間違い (実装と主張の齟齬) を検査・修正
- 課題4: docs 以外のプログラム・定義が docs に反映されているか確認し、未反映を反映
- 課題5: docs ディレクトリ全体をリファイン

## 計画 (攻撃対象)

### 課題2 の方針
- glossary.md の各用語について repo 全体の使用箇所を grep 集計し、(a) どこからも使われない用語は削除、(b) 同義・重複項目は統合、(c) 残す用語は定義を簡潔化
- docs 本文の「不必要な英語混じり」を日本語へ置換。ただし次は不変: コード識別子 (関数名・モジュール名・genome/variant 等の API 名)、agent 名 (.claude/agents のファイル名・role 名)、grep 索引規約 (decisions.md の `^## D`、worklog の `^## ` 日付見出し、handoff の「状態:」行)、CCBench 由来の術語、check_docs.py / check_codex_agents.py が検査する形式
- プログラムの明瞭化は挙動不変のリネーム・コメント改善・docstring 明確化に限定し、各コミットでテスト green を確認
- 裁定待ちの s8b 文書・凍結済み文書 (archive/, roadmap-history/, insights 逐語) は文体修正の対象外

### 課題3 の方針
- レーン分割 (campaign / calibrator+verifier / tests / tools+hooks / .claude+.codex+src) で「ファイル内の主張 (docstring・コメント・README) と実装の齟齬」を検査、所見を親が裁定して修正
- 過去の失敗型 (docs/failures.md) の F14「文書 claim と実装の齟齬」を攻撃面に含める

### 課題4 の方針
- docs/README.md の地図・phase3.md・orchestrator-design.md・agent-architecture.md に対し、実在のプログラム・agent・スクリプトが記載されているか突合し、欠落を docs へ反映

### 課題5 の方針
- 課題1〜4 の結果を踏まえ、docs の重複記述の除去 (可変状態の正本は worklog 末尾 + 現行 phase doc のみ、他文書へ再掲しない規約 D)、相互参照の整合、構成の整理
- check_docs.py green を維持

### 私が既に認識しているリスク (これ以外の穴を重点的に)
- 用語の改名・削除が hooks / check_* スクリプト / agent 定義の期待文字列を壊す
- 日本語化のやりすぎで専門用語の精度が落ちる (CC 分野の標準術語は英語のまま残すべき)
- glossary 圧縮で「専門外の読み手向け定義」という glossary の目的 (roadmap 冒頭) を毀損する
- docs の「重複除去」が「正本 + ポインタ」構造を誤解して正本側を消す

リポジトリを実際に調べ、この計画の穴を突いてください。特に「機械的に適用すると壊れる具体箇所」をファイルパス付きで挙げてください。
`````

## 相談 B 出力 (逐語)

`````markdown
結論: この計画はそのまま実行すると危険です。実査では 13 件（must-fix 10、should 3）を確認しました。`check_docs.py` と `check_codex_agents.py` は現在どちらも exit 0 ですが、それでも下記の実害が残っています。

### 1. s8b の保護対象がファイル名ではなく SHA の推移閉包になっている

- severity: must-fix
- 攻撃シナリオ: 「s8b 文書だけ除外」しても不十分。`phase3-main-experiment.md` や `genome.py` などのコメント・docstringを一文字直すだけで、既存 freeze の SHA 照合が失敗し、oracle gate に `known-axes-freeze-verify` 拒否が追加される。
- 根拠: holdout freeze は設計書と generator を SHA で固定している [holdout_freeze.json:5](/home/SFC/tanab/github/izanagi/.claude/worktrees/repo-refinement/output/s8b-freeze/holdout_freeze.json:5)。照合は worktree の byte 完全一致である [s8b_holdout_freeze.py:573](/home/SFC/tanab/github/izanagi/.claude/worktrees/repo-refinement/orchestrator/campaign/s8b_holdout_freeze.py:573)。さらに oracle gate は `known_axes_freeze` 自体を再検証する [s8b_oracle_driver.py:180](/home/SFC/tanab/github/izanagi/.claude/worktrees/repo-refinement/orchestrator/campaign/s8b_oracle_driver.py:180)。そこから `phase3-main-experiment.md`、`s6_sort_sweep.py` 等へ SHA 束縛が伸びる [known_axes_freeze.json:621](/home/SFC/tanab/github/izanagi/.claude/worktrees/repo-refinement/output/s1-freeze/known_axes_freeze.json:621)。
- 提案: 編集前に全 active freeze JSON から `{path, sha256}` を再帰抽出し、推移閉包を no-edit 集合にする。少なくとも現時点では `phase3-8b-descriptor-design.md`、`phase3-main-experiment.md` と campaign 実装 8 本が対象。これらの洗練はユーザー裁定と正規の再凍結後へ分離する。

### 2. 課題5で凍結除外が失効し、歴史記録を改竄できる

- severity: must-fix
- 攻撃シナリオ: 課題2では archive 等を除外していても、課題5の「docs 全体」で重複除去・文体修正を適用すると、完了 Phase、過去 worklog、論文スナップショット、事前登録の旧記述が書き換わる。監査証拠や HARKing 境界が消えるが、`check_docs.py` は多くを検査対象外にしているため緑になり得る。
- 根拠: phase1/2 は「訂正注記のみ」の凍結記録 [phase1.md:3](/home/SFC/tanab/github/izanagi/.claude/worktrees/repo-refinement/docs/phase1.md:3)。paper-story は上書き禁止で新スナップショット追加方式 [paper-story/README.md:8](/home/SFC/tanab/github/izanagi/.claude/worktrees/repo-refinement/docs/paper-story/README.md:8)。worklog の過去項目も凍結 [worklog.md:12](/home/SFC/tanab/github/izanagi/.claude/worktrees/repo-refinement/docs/worklog.md:12)。主実験事前登録も旧本文を消さず日付付き追記だけを重ねる契約 [phase3.md:80](/home/SFC/tanab/github/izanagi/.claude/worktrees/repo-refinement/docs/phase3.md:80)。
- 提案: 課題2〜5すべてに共通する保護表を先に作る。分類は「living・append-only・frozen snapshot・raw evidence・generated/binary」。許可操作を、living=編集可、append-only=追記のみ、frozen=訂正注記または新スナップショット、raw=不変、と固定する。

### 3. 課題2を課題3より先に行うと、監査対象の嘘を先に書き換える

- severity: must-fix
- 攻撃シナリオ: task 2 で docstring/comment を「明瞭化」した後に task 3 を走らせると、元の不正確な主張が消え、単なる文体修正として履歴に埋もれる。誤りの型・影響範囲・再発防止が記録されない。
- 根拠: F14 は、実際には無視される CLI フラグを遮断構成として記録した事故であり、`--help` による仕様確認後に訂正したもの [failures.md:125](/home/SFC/tanab/github/izanagi/.claude/worktrees/repo-refinement/docs/failures.md:125)。別 AI の作業物は採用前に差異を表出し、独立裏取りする契約でもある [CLAUDE.md:92](/home/SFC/tanab/github/izanagi/.claude/worktrees/repo-refinement/CLAUDE.md:92)。
- 提案: 順番を「保護集合確定 → task 3 の read-only claim 台帳作成 → 裁定 → 修正 → task 4 → task 2/5 の表現整理」に変える。変更前の `file:line・claim・consumer・根拠` を保存してから文体に触る。

### 4. task 3 のレーン分割に実在ファイルが丸ごと漏れている

- severity: must-fix
- 攻撃シナリオ: 現在のレーンでは `patches/` が完全に未割当。加えて `orchestrator/codex_roles/`、`critic/`、`reports/`、トップレベル entrypoint/README も campaign・calibrator・verifier のいずれにも明示的に入らない。「全件検査済み」と報告しても未検査面が残る。task 4 も「定義」を落としており、JSON Schema・catalog・manifest・prompt `.txt` が漏れる。
- 根拠: orchestrator 自身が critic、reports、トップレベル entrypoint を別構成要素としている [orchestrator/README.md:15](/home/SFC/tanab/github/izanagi/.claude/worktrees/repo-refinement/orchestrator/README.md:15)。`patches/` は correctness positive control と正当 variant の行き先を持つ [patches/README.md:1](/home/SFC/tanab/github/izanagi/.claude/worktrees/repo-refinement/patches/README.md:1)。実装契約は Python だけでなく [layer3_schema.json:1](/home/SFC/tanab/github/izanagi/.claude/worktrees/repo-refinement/orchestrator/campaign/layer3_schema.json:1)、[s8b_descriptor_schema.json:1](/home/SFC/tanab/github/izanagi/.claude/worktrees/repo-refinement/orchestrator/campaign/s8b_descriptor_schema.json:1)、[manifest.json:1](/home/SFC/tanab/github/izanagi/.claude/worktrees/repo-refinement/orchestrator/codex_roles/manifest.json:1) にもある。
- 提案: 手書きレーンではなく、ユーザー指定範囲への `git ls-files` から coverage manifest を生成し、全ファイルを「担当レーン・除外理由・検査種別」のどれかにちょうど一度割り当てる。`.py/.md/.json/.txt/.patch` を対象にする。

### 5. コメント・docstring・内部名はこのリポジトリでは挙動の一部

- severity: must-fix
- 攻撃シナリオ: コメント改善で `EVOLVE-BLOCK-BEGIN` を日本語化するとテンプレート抽出が失敗する。docstring 改訂は CLI help/stderr を変える。dataclass field のリネームは `asdict()` 経由の JSON schema を変える。いずれも「挙動不変」ではない。
- 根拠: EVOLVE-BLOCK はコメントから正規表現で抽出される [diff_quarantine.py:431](/home/SFC/tanab/github/izanagi/.claude/worktrees/repo-refinement/orchestrator/campaign/diff_quarantine.py:431)。`plot_backoff.py` は引数不足時に `__doc__` をそのまま stderr に出す [plot_backoff.py:239](/home/SFC/tanab/github/izanagi/.claude/worktrees/repo-refinement/tools/plotting/plot_backoff.py:239)。dataclass は成果物へ `asdict()` 射影される [s1_report.py:541](/home/SFC/tanab/github/izanagi/.claude/worktrees/repo-refinement/orchestrator/campaign/s1_report.py:541)、[s8b_oracle_driver.py:487](/home/SFC/tanab/github/izanagi/.claude/worktrees/repo-refinement/orchestrator/campaign/s8b_oracle_driver.py:487)。
- 提案: 「公開挙動」を import 名だけでなく、CLI help、stdout/stderr、exit code、JSON key/value、exception 名、dataclass field、marker、hash input、schema literal まで拡張する。リネーム前後の golden 出力比較と consumer 全検索を必須にする。

### 6. `check_docs.py green` は現在でも false-green を作れる

- severity: must-fix
- 攻撃シナリオ: task 5 で `LIVING_DOCS` の文書を削除・改名しても、checker は対象不在を `continue` で黙って飛ばす。見出しの意味矛盾や相対 Markdown link/anchor の破損も通る。同じ作業で checker 自身を弱めれば、その後の全 commit が緑になる。
- 根拠: checker 自身が意味的ずれは検出不能と明記している [check_docs.py:2](/home/SFC/tanab/github/izanagi/.claude/worktrees/repo-refinement/tools/check_docs.py:2)。さらに対象不在を実際に黙って skip する [check_docs.py:116](/home/SFC/tanab/github/izanagi/.claude/worktrees/repo-refinement/tools/check_docs.py:116)。これは「対象不在は fail に修正済み」とする F9 と食い違う [failures.md:88](/home/SFC/tanab/github/izanagi/.claude/worktrees/repo-refinement/docs/failures.md:88)。実例として 8b 文書の見出しは「項7〜8承認待ち」のままだが、直下では承認済みとする [phase3-8b-descriptor-design.md:269](/home/SFC/tanab/github/izanagi/.claude/worktrees/repo-refinement/docs/phase3-8b-descriptor-design.md:269)。それでも実行結果は `check_docs: 違反なし`。
- 提案: 大量編集前の独立 commit で checker を直す。明示列挙対象の不在を fail、相対リンクと anchor、引用した見出し名を検査し、各規則に「わざと壊す」mutation test を置く。checker 変更と、その緩和で初めて通る docs 変更を同じ commit に入れない。

### 7. 「tests green」は依存物 SKIP により統合破損を見逃す

- severity: must-fix
- 攻撃シナリオ: submodule が未初期化のままテストすると source-digest、EVOLVE-BLOCK、実 build 系が SKIP される。patch や marker を壊しても単体テストだけ緑になり、実 CCBench build で初めて失敗する。
- 根拠: テスト方針は submodule・実 Silo・gnuplot 不在時に該当検査を SKIP すると明記する [tests/README.md:10](/home/SFC/tanab/github/izanagi/.claude/worktrees/repo-refinement/orchestrator/tests/README.md:10)。source_digest/EVOLVE-BLOCK 系は submodule 初期化後だけ有効 [tests/README.md:23](/home/SFC/tanab/github/izanagi/.claude/worktrees/repo-refinement/orchestrator/tests/README.md:23)。この worktreeの `git submodule status` は先頭 `-` で未初期化。過去にも単体検査緑の生成物が実 build で壊れた F19 がある [failures.md:208](/home/SFC/tanab/github/izanagi/.claude/worktrees/repo-refinement/docs/failures.md:208)。
- 提案: baseline で pass/skip 件数を固定し、load-bearing test の SKIP を成功扱いしない。patch/program変更では submodule 初期化、`git apply --check`、代表実 build、freeze verify を必須にする。

### 8. claim と実装の二者突合だけでは「どちらが間違いか」を決められない

- severity: must-fix
- 攻撃シナリオ: README とコードが違うとき、README をコードへ合わせるだけで科学的なバグを正当化できる。実在例では「t 分布の 95% CI」という主張に対し、コードは中央値を中心に常時 `1.96·s/√n` を付けている。n=5 なら t₄ の 2.776 より約29%狭く、しかも平均の標準誤差式は中央値 CI ではない。
- 根拠: README は t 分布と主張する [plotting/README.md:31](/home/SFC/tanab/github/izanagi/.claude/worktrees/repo-refinement/tools/plotting/README.md:31)。規約は小標本で t 値を要求する [FIGURE_CONVENTIONS.md:30](/home/SFC/tanab/github/izanagi/.claude/worktrees/repo-refinement/tools/plotting/FIGURE_CONVENTIONS.md:30)。実装は全 n で 1.96、中心は median [plot_backoff.py:65](/home/SFC/tanab/github/izanagi/.claude/worktrees/repo-refinement/tools/plotting/plot_backoff.py:65)。既存 consumer test は CI 数学を検査していない [test_backoff_consumers.py:64](/home/SFC/tanab/github/izanagi/.claude/worktrees/repo-refinement/orchestrator/tests/test_backoff_consumers.py:64)。
- 提案: task 3 を「claim ↔ implementation」ではなく「承認済み設計・統計契約 ↔ implementation ↔ tests/出力」の三角突合にする。矛盾時の権威順位を先に決め、統計・セキュリティ・CLI は既知入力の期待値テストを追加する。F14 だけでなく F9/F15/F16/F17/F19 の型を coverage 表にする。

### 9. glossary の repo 全体 grep 件数は母集団が汚染される

- severity: must-fix
- 攻撃シナリオ: `.codex/role-adapters` は Claude role 本文を複製し、archive・相談逐語・生成物も同じ語を反復する。これらを live docs と同じ一票に数えると、生成物だけで使われる語を残し、表記揺れした現役用語を未使用として消す。短語は substring 誤爆も大きく、実査では `SI` が単純一致 4,120 件、単語境界付きでは 10 件だった。
- 根拠: glossary の対象読者・対象 corpus は docs/insights と定義される [glossary.md:1](/home/SFC/tanab/github/izanagi/.claude/worktrees/repo-refinement/docs/glossary.md:1)。Codex adapter は移植元本文を exact に埋め込む [codex agents README:21](/home/SFC/tanab/github/izanagi/.claude/worktrees/repo-refinement/.codex/agents/README.md:21)、checker も exact 1 回を要求する [check_codex_agents.py:257](/home/SFC/tanab/github/izanagi/.claude/worktrees/repo-refinement/tools/check_codex_agents.py:257)。archive は凍結記録で現役文書と別物 [archive/README.md:1](/home/SFC/tanab/github/izanagi/.claude/worktrees/repo-refinement/docs/archive/README.md:1)。
- 提案: 件数を living docs、読み物として残す frozen docs/insights、raw transcript、code/tests、generated copy に層別する。単語境界・大小文字・日本語/英語別名を使い、自動削除条件にはせず判断材料として出す。

### 10. 同義語統合で glossary の grep 索引そのものが壊れる

- severity: should
- 攻撃シナリオ: `DSG` を「直列化グラフ」へ統合して文字列 `DSG` を消すと、本文で `DSG` に遭遇した読者が規定どおり grep しても項目へ到達できない。圧縮には成功しても運用契約は破綻する。
- 根拠: glossary は「用語検索で該当見出しから次見出しまで読む」索引として使う [docs/README.md:7](/home/SFC/tanab/github/izanagi/.claude/worktrees/repo-refinement/docs/README.md:7)。各項目の表記形式も検索語を列挙する前提 [glossary.md:7](/home/SFC/tanab/github/izanagi/.claude/worktrees/repo-refinement/docs/glossary.md:7)。現行の DSG 項目は複数表記を同じ項目に残している [glossary.md:65](/home/SFC/tanab/github/izanagi/.claude/worktrees/repo-refinement/docs/glossary.md:65)。
- 提案: 統合後も、repo で観測した全 surface form を見出しまたは `別名:` に逐語保持する。各 surface form に `rg -F` を当て、同じ項目へ到達する lookup smoke test を作る。

### 11. task 4 の「全プログラムを4文書へ掲載」は正本配置を逆に壊す

- severity: should
- 攻撃シナリオ: 全ファイルを `docs/README.md` や phase3 に列挙すると、次の driver/agent 追加ですぐ腐る。一方、4文書しか見ないと `hooks/README.md`、`patches/README.md`、`.codex/agents/README.md`、plotting 規約など、本来の owner にある契約を取り落とす。
- 根拠: docs 地図は段別文書を列挙せず phase3 から辿る方針 [docs/README.md:36](/home/SFC/tanab/github/izanagi/.claude/worktrees/repo-refinement/docs/README.md:36)。agent の現有一覧も `ls` が正本 [docs/README.md:48](/home/SFC/tanab/github/izanagi/.claude/worktrees/repo-refinement/docs/README.md:48)。campaign driver も同じく `ls` が正本 [orchestrator/README.md:10](/home/SFC/tanab/github/izanagi/.claude/worktrees/repo-refinement/orchestrator/README.md:10)。
- 提案: 「実装ファイル → 契約 owner → docs 地図のポインタ」の三列対応表を作る。揮発的な個別一覧は owner 側または `ls` に委ね、docs には安定したカテゴリと責務だけを書く。突合は code→docs の欠落だけでなく docs→code の幽霊主張も検査する。

### 12. `docs/` には正本だけでなく未監査データが混在している

- severity: should
- 攻撃シナリオ: task 5 が「docs 全体」を同格に扱うと、未監査の文献マップや生成ノートを関連研究の正本へ統合し、LLM 由来の誤要約を読みやすい権威的文章へロンダリングする。
- 根拠: literature map は自ら「監査前のデータ成果物で、設計文書の正本ではない」と宣言する [literature-map/README.md:1](/home/SFC/tanab/github/izanagi/.claude/worktrees/repo-refinement/docs/related-work/literature-map/README.md:1)。採録前監査を要求し、監査後も生データとして残す契約 [literature-map/README.md:42](/home/SFC/tanab/github/izanagi/.claude/worktrees/repo-refinement/docs/related-work/literature-map/README.md:42)。
- 提案: 文書ごとに authority/evidence class を付ける。raw/generated は文体整備・統合対象外とし、正本への昇格は一次資料の再検証、provenance、real/refuted 裁定を別工程にする。

### 13. 親の自己裁定と終了ゲートがリポジトリ規律を満たさない

- severity: must-fix
- 攻撃シナリオ: 各レーンの所見を同じ親が修正・裁定し、その親が変更した checker で合格判定すると、互いに整合した弱い保証を自己承認できる。また計画は `check_docs.py` しか終了条件に挙げず、`.claude/.codex` 変更に必須の parity/provenance 監査を落としている。
- 根拠: 別 AI 作業物は独立コンテキストで敵対裏取りする契約 [CLAUDE.md:92](/home/SFC/tanab/github/izanagi/.claude/worktrees/repo-refinement/CLAUDE.md:92)。完了時は関連テスト、`check_codex_agents.py`、`check_docs.py`、commit 後の `check_ai_provenance.py` が必須 [AGENTS.md:26](/home/SFC/tanab/github/izanagi/.claude/worktrees/repo-refinement/AGENTS.md:26)。phase check、worklog、handoff の終了処理も規定される [CLAUDE.md:150](/home/SFC/tanab/github/izanagi/.claude/worktrees/repo-refinement/CLAUDE.md:150)。
- 提案: 発見者・修正者と別コンテキストの最終 diff reviewer を置き、各 finding を real/refuted/accepted-risk に再裁定する。終了条件へ必須3 checker、関連テストの pass/skip 内訳、freeze verifier、phase/worklog/handoff、commit 後 provenance 監査を明記する。

最優先の修正順は、`freeze の推移閉包確定 → scope manifest → checker/統合 positive control の修理 → task 3 read-only 監査 → 修正 → task 4 → mutable 文書だけ task 2/5` です。現在の順序で一括着手してはいけません。`````
