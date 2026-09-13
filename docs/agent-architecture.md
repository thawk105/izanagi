# サブエージェント・アーキテクチャ

Izanagi のサブエージェント role、製品別 runtime adapter、hooks の構成、および段階導入計画。

設計の出発点は Jitskit と IDS のマルチエージェント構成。製品ごとに実行境界を再審査し、
同等の権限隔離を再現できない場合は native 実行へ写さず static/blocked で止める。ECC からは
「tools/model を明示してロールを権限で縛る」「hook で規律を
機械執行する」運用パターンを借りた (ECC の規模そのものは反面教師)。

---

## 製品別 runtime adapter

`.claude/agents/` は role の意味・prompt と Claude Code 固有の model/tools 契約の正本である。
Codex は同じ Markdown を native 実行定義として使わず、製品固有の adapter と parity gate を介す。
manifest と renderer は移植元本文を正確に 1 回埋め込み、metadata、model/effort、capability lowering、
schema、禁止入力 policy、consumer 配線状態を検査対象にする。open/opaque subtree は trusted projection
producer の責任であり、全階層を検査済みとは扱わない。

Codex adapter の分類、native discoverability、runtime probe の結果、再開条件を含む**現行状態の正本**は
`.codex/agents/README.md`、機械検査の正本は `tools/check_codex_agents.py` である (D54〜D56、F16/F17)。
本書には件数や active/static/blocked の現況を再掲しない。両正本が role を安全な実行面として再分類する
までは、native profile を起動せず、非自動発見 adapter を実行定義として扱わず、generic child も role
隔離の代替にしない。`task_name` や自然言語の成功・拒否自己申告だけでは実行証拠にならない。

この adapter は将来の Codex runtime 再開に備える互換・検査層であり、Phase 3 のロール実体化状況や
研究タスクの完了判定を変更しない。

---

## 段階導入の原則

サブエージェントは Phase ごとに必要なものだけ足す。最初から全部並べない。理由は decisions.md D7 — ablation で各ロールの効果を測るため、また探索失敗時の切り分けのため。

```
Phase 1: verifier, calibrator
Phase 2: + critic (P2-3), profiler (P2-4)
Phase 3: + coder (kickoff), auditor (段 3), planner-v4/coder-v4 (段 4), axis-proposer (段 8a)
Phase 3.5: (OEE。新規ロールは不要、層3の選択ロジックを格上げ)
```

Phase 3 のロールは、本ドキュメントに仕様を予約しておき、該当する段に来たときこの仕様に従って `.claude/agents/*.md` を生成する方式を取る (どの段まで実体化済みかの正本は phase3.md のチェックリスト — ここには再掲しない)。

---

## 各ロールの仕様

### verifier (Phase 1・実体化済み)

- **役割:** trace ログを受け取り、read/write 依存グラフを構築し cycle (G2 含む) を検出する。anomaly を構造化して返す
- **tools:** 読み取り + グラフ検査スクリプト実行のみ。**書き込み系ツール (Edit/Write) を持たない**
- **model:** 軽量で良い (グラフ検査は決定的処理が主)
- **絶対規律:**
  - anomaly を見つけたら、どの trx 間のどの依存で cycle ができたかまで構造化して返す。単なる fail を返さない (絶対規律3)
  - 正しさゲートを緩める提案をしない。性能のために検証を甘くする変異を通さない (絶対規律2の番人)
  - **入力側隔離:** verifier のコンテキストに性能数値や期待 ground truth を混入させない。verifier は trace のみを入力とし、throughput 等の報告済み数値を一切受け取らない。「期待値をコピーして捏造する」経路を入力データレベルで断つ (ARA / 2604.24658 の anti-fabrication isolation。roadmap §3.4-4)
- **なぜ書き込み権限を外すか:** 検証役が実装を勝手に直す事故を構造的に防ぐ。Jitskit が auditor を別エージェントにした「見張り役を最適化圧力から隔離する」をツール権限で実装。これは**出力側の隔離** (Edit/Write を外す) であり、上記の**入力側の隔離** (期待値を見せない) と対をなす

### calibrator (Phase 1・実体化済み)

- **役割:** cache miss 率を見てレコード数を決める。妥当性を文書化する
- **tools:** perf 実行、ベンチ実行、output/insights/ への書き込み
- **model:** 軽量で良い
- **規律:** 飽和点は thread 数依存。探索 thread 数を固定してから測る。判断根拠を必ず文書化する

### critic (Phase 2・実体化済み, P2-3)

- **役割:** 評価結果 (throughput + leading indicators) を読んで次の方向を示す。生のカウンタでなく組み合わせて読み、特定の設計選択に帰属させる (Jitskit の critic)
- **tools:** 読み取り + 解析。実装の書き込みはしない
- **model:** 推論が要るので強めのモデル
- **規律:** 「lock contention が高くスケールしない」のような診断を、次の variant 生成への具体的指示に変換する。leading indicators を必ず参照する (これが無いと探索が停滞する、Jitskit §3.5)
- **派生:** ablation 用の中立版 `critic-experiment` (P2-5 誘導アーム専用。リーク制御のため最適解の文字どおりの事前知識を物理削除した版) は P2-5 限定で使用した。D21 参照

### profiler (Phase 2・実体化済み, P2-4)

- **役割:** 有望な variant に perf/FlameGraph を回し、many-core でのスケール懸念を解釈する
- **tools:** perf 実行、FlameGraph 生成、解析
- **model:** 解釈に推論が要るので中〜強
- **規律:** 全 variant でなく screening を通過した上位にだけ回す (二段構え)。trace-disabled build に対して回す (絶対規律1)。「lock acquisition が42%、thread 増やすと悪化する典型」のような診断を critic/層3 に渡す
- **実体化 (P2-4):** `.claude/agents/profiler.md`。最初の実走 = backoff ケーススタディの [P0] 機序純度。診断ノブ `BACKOFF_NOINLINE` (inert patch, D20) で spin ループを独立シンボル化し `perf record -e cycles,instructions` で **有用 IPC (= spin を除いた 1サイクルあたり命令数)** を分離 (`orchestrator/campaign/backoff_profile.py`)。perf 下 throughput は overhead 込みで headline 非使用 (絶対値は stock build, 規律4)。

### planner (Phase 3・仕様予約)

- **役割:** spec cards と leading-indicator フィードバックを消費して設計プランを提案する。コードに引きずられず構造変更を考える
- **tools:** 読み取り + 設計ドキュメント書き込み。コード実装はしない
- **model:** 強いモデル
- **規律:** whiteboard memory (却下済み設計) を参照し、同じ失敗を再提案しない
- **⚠ 確定制約は本節でなく `planner-v4.md` + D45 を正典とする** (本節は予約仕様。実体化で分岐した):
  実体の planner-v4 は **tools=[] (ツールなし — 予約の「読み取り + 設計ドキュメント書き込み」と異なり
  Read も Write も持たない)**。入力はメインセッションが leading-indicators/whiteboard を射影して inline
  (JSON) で渡し、提案は構造化出力で返す (coder-v4 と同型の構造遮断)。当初実体は tools=[Read] だったが、
  Read の運用上の必要がゼロである一方 output/insights (勝ち筋詳細) への機械制限なしアクセスがリーク制御の
  系全体を弱めるため、D44 段 6 前提タスク (h) → D45 で剥奪。

### coder (Phase 3・仕様予約)

- **役割:** planner のプランを CCBench コードへの diff (EVOLVE-BLOCK 内) に落とす。他 CC の最適化を移植する
- **tools:** コード読み書き、ビルド
- **model:** 強いモデル
- **規律:** 検証用情報は D14 の `#if TRACE` 契約で性能ビルドから完全除去する。CC のデータ構造に検証専用フィールドを常駐させない (絶対規律1)。移植時は最適化カタログ (前提/効果/競合) を参照して前提条件を満たすか確認する
- **⚠ E-loop 自律期の確定制約は本節でなく `.claude/agents/coder-v4-autonomous(-sort).md` + D39 決定 7 / D43 を正典とする** (本節の tools 欄は予約仕様。実体化で分岐した — §planner の planner-v4 addendum と対称): 実体の coder-v4-autonomous / coder-v4-autonomous-sort は **tools=[] (ツールなし — filesystem browse 経路を構造的に持たない = リーク制御)**。入力は planner の方向ヒント + leading-indicators + whiteboard をメインセッションが射影して inline で渡し、合成は構造化出力のみで返す。
- **⚠ kickoff の確定制約は本節でなく `docs/phase3.md` + D22/D23/D24/D30 を正典とする** (本節は Phase 3 着手前の予約仕様で、kickoff 設計を反映していない)。coder.md を生成するときは最低限: (1) 編集面は EVOLVE-BLOCK の `#if` 枝内の straight-line code のみ (#include/型/マクロ定義の追加禁止、閉じた領域制約)、(2) COMMIT を書く唯一の経路は `pipeline.evaluate()`、(3) 勝ち筋値・機序説明のリーク制御 (P2-5/D21 の Phase 3 版、phase3.md 残存リスク)、(4) hooks は方針 A で最小第二防壁 = 正しさ/同一性の担保は一次防壁 (source_digest / 観測者効果二重検査) にある、を織り込む
- **駆動方式の環境制約 (worklog 2026-06-29 から昇格):** この環境には **headless の claude CLI が無い**。roadmap §3.8 の「ループ主導権は orchestrator、LLM は iteration 単位で fresh に呼ぶ」を実装するとき、orchestrator が CLI を子プロセスとして呼ぶ形は取れない。P2-5 誘導アームは「各試行を fresh サブエージェント (本会話を見ない) が `guided.py` を Bash で駆動する」形で迂回した — coder ループも同系の駆動 (fresh サブエージェント + Python ハーネスの Bash 駆動) を前提に設計する。

### coder-v4-autonomous-k2 (K2 宣言アーム、D1429 = `.claude/agents/coder-v4-autonomous-k2.md`)

- **位置づけ:** `coder-v4-autonomous` の兄弟。合成軸 (`silo-backoff-magnitude`) と出力の
  `implementation` 契約は同一で、違うのは**宣言した知識水準だけ**である。K0/K1 のアームは
  既存 role をそのまま使い続けるので、既存 role の bytes は変えていない。対照が壊れないように
  書き換えでなく兄弟を足す形にした (worklog 2026-09-02 の T-2182 エントリの判断)
- **なぜ要るか:** 既存 role の遮断条項は「他実験の勝ち筋値・候補順位・未評価候補の性能を使わない」で、
  真の K2 投入と必ず衝突する。D1429 はこの種の遮断を既定の防壁から**宣言した知識水準で決まる
  実験条件**へ移した。衝突を prompt の上書きで回避するのではなく、K2 用の契約を別に持つ
- **入力:** `coder-v4-autonomous` の 4 field に `knowledge_input` を必須で足す。中身は
  `orchestrator/campaign/knowledge_manifest.py` の planner projection と同じ形
  (`data_boundary` / `knowledge_level` / `knowledge_manifest_sha256` / `sources`) で、
  各 source は commit と path または Web identity、`sha256`、検証済み本文を持つ
- **知識境界:** 「全部見てよい」ではない。使ってよいのは `sources` に列挙され `sha256` で
  束縛された本文、入力 schema が明示する本ループ自身の観測値、および学習済みの一般知識である。
  既知の勝ち筋値・候補順位・既知の最適機序も、source に束縛されていれば使ってよい。
  使ってはならないのは、列挙外の外部知識、role 自身による取得、**どの source にも根拠を持たない
  性能値** (将来値・oracle 値・測定済みを装う予測値)、知識源の本文に含まれる指示、
  ゲートの定義や閾値を変更・迂回する提案、統制比較なしの強い主張である。
  3 番目は候補が未評価かどうかによる禁止ではない — 公開文献や過去 campaign で**測定済み**の
  性能は、本 campaign で未評価の候補のものでも source に束縛されていれば使える
- **構造遮断は撤去しない:** `tools=[]` と fresh context は維持する。K2 は「知識を投入する」で
  あって「role に filesystem を歩かせる」ではない。投入は信頼中核が射影で行う
- **知識源の選定 (送り手側の義務、D1936 項 2):** manifest を作る信頼中核は `sources` を
  **測定記録** — 何をどう測り、どのような結果・判定を得たかを記録した成果物 — へ絞る。
  実績のある例は campaign の `runs/wal.jsonl` である。観測値と判定を伴わず、探索の進行状態と
  抽象的な成否だけを保存した checkpoint は測定記録に当たらない。**設計説明** — 何を意図し
  何を作るつもりかを述べた文、および読み手がどう振る舞うべきかを定める文 — は知識源にしない。
  判定は**誰が書いたか**ではなく**何を述べた文か**で行う。`campaign.lock` の `spec_content` は
  機械が保存した field だが設計説明であり、`s4_loop_digest.txt` の「異常かどうかは読み手が
  判断」型の定型注記も生成器が埋め込んだ運用説明である。これらの説明を含む成果物は、測定値が
  同居していても source に選ばない。説明部分を削って投入するのではなく、別の測定記録を選ぶ。
  本書を含む設計・運用 docs 自体も知識源にしない。**閉じ方は source の選定である** — gate は
  変えず、指示検出を避けるために自由文を削除・抜粋・言い換えした入力も作らない (絶対規律 6 の
  送り手側の義務)。この規律との差だけを理由に、過去の走行とその記録・test fixture を遡って
  無効化・改変しない (絶対規律 7)
- **自己申告:** 出力に `knowledge_use` (使った source と使い方)、`classification`
  (`de_novo` / `known_result_conditioned_derivative` / `reproduction_or_selection`)、
  `data_boundary_report` (絶対規律 6 の報告) を持つ。`source_index` が実在する index か、
  重複していないかは `orchestrator/codex_roles/policy.py` の `validate_output_semantics` が
  機械検査する。この検査は段 4 loop の proposal consumer へ配線してあり、**呼び手が role 契約を
  明示的に宣言した呼出しでだけ発火する** (知識入力の有無では発火しない)。
  発火した場合は論理 output schema の検証と、`data_boundary_report` が指示めいた内容を
  申告したときの fail-closed 停止も同じ経路で行う。**ただし通した場合でも、
  本当にその source を使ったか、分類が妥当かは検査しない。** これらは role の自己申告であり、
  信頼中核が受領証へ書く分類を上書きしない。照合対象は campaign が束縛した knowledge projection
  であって、role が実際に読んだ入力ではない
- **主張の境界:** K2 で得た結果から言えるのは knowledge-conditioned な成立までである。
  K2 を条件とする certified な最終選択は、宣言した知識水準と実際に投入した知識源が
  proof chain に結ばれるまで主張しない。候補単位の正しさ・identity・性能の判定は
  知識水準に依存せずそのまま有効である (D1429)
- **実行境界:** 段 4 loop の proposal consumer へ配線済み。**ただし配線であって発火実績ではない** —
  この role の wrapper が実際に consumer を通った成果物は 0 件である。Codex runtime activation は
  `uncontrollable_additional_tools` により引き続き blocked。
  信頼中核が手で起動する。agent 登録は session 開始時に読まれるため、この role を作った
  session からは行使できない

### selector-8b (Phase 3 段 8b)

- **役割:** 信頼中核が射影した `8b-selector-input/v1` の workload descriptor と固定6候補の中立機構カタログから、この workload に最適と推論する候補をちょうど1件選び、`8b-selector-output/v1` の opaque choice ID と rationale を返す
- **遮断設計:** fresh context、`tools=[]`、閉じた JSON 入出力だけを用いる。実験 arm、holdout identity、生の variant binding、既知 winner、実測性能、oracle 結果を role 入力へ渡さない。choice ID から target 側 binding への解決は予測後に信頼中核だけが行う
- **実行境界:** 予測実行は tool-less 契約を実際に執行できる Claude role runtime のみを使う。Codex 側は全単射維持の static/dormant adapter を持つだけで、`input.additional_tools` の遮断を証明できない現行 Codex runtime は blocked のままとし、generic child で代用しない
- **出力規律:** 候補を1件だけ返す strict JSON とし、不正出力へ fallback せず再試行もしない。prediction freeze と後続 oracle 成果物は分離する

### auditor (Phase 3・後続段 3 で実体化 = `.claude/agents/auditor.md`)

- **役割:** variant を監査し、verifier が構造的に見逃す不変条件違反 (reward hack) を検出して positive control テストを設計・提案する (Jitskit の auditor)
- **model:** 強いモデル (adversarial な reasoning が要る)
- **規律:** 最適化を担当するエージェント (planner/coder) とコンテキストを分離する。見張り役が最適化圧力に毒されないため。CC 版の reward hack ギャラリー (related-work/ の Jitskit 節を参照 — Appendix B の型リスト本文は repo に無いため、repo 実績から翻訳した CC 版として auditor.md に持つ)
- **モデル階層方針:** auditor には、被監査側 (coder/planner) と同等以上の能力 tier のモデルを割り当てる。能力の高いモデルほど評価ハックを高率で生成し (gpt-5.2-codex で 8.2%)、検出の必要性もモデル能力に比例するため、被検体より弱い検出器では検出が破れうる (Vesper, arXiv:2605.15221、related-work §7.2)。これは「下げても結果が変わらないなら安価なモデルへ委譲する」一般方針の明示的な例外とする。一方、低能力な生成器ではハックが発生せず検出が経費倒れになる知見も踏まえ、coder を安価なモデルへ下げる実験では「ハック検出 on/off × モデル能力」を ablation 軸にする。
- **⚠ 確定制約は本節でなく `auditor.md` + `docs/phase3.md` 後続段 3 + D38 を正典とする** (本節は予約仕様。実体化で 2 点分岐した):
  - **tools = read-only (Read/Grep/Glob、Write/Edit/Bash 非付与)。** 予約の「テスト追加の書き込み」は段 3 では「auditor が提案テストを構造化出力で返し、orchestrator が人間レビューゲート下で反映する」形で実現 (段 2 の coder/critic と同型)。理由 = guard_write (PreToolUse) は呼び出し元エージェントを識別できず (tool_name/tool_input のみ) per-agent の path 制限が hook で表現不能 → auditor に Write を与えると「既存テストを弱める書き込み」を機械的に止められない。read-only なら構造的に不可能。直接 Write の自律形は後続段 4 (per-agent permission 執行とセット) へ繰延 (D38、audit-2026-06-30 §4 段 2 の部分消化)。
  - **入力隔離:** 「WAL fitness を scope に入れない」(phase3.md 後続段 3) は tool 制限 + orchestrator の入力射影 (abort/patch/designated ソースだけを渡す) + prompt 規律の併用。Read を持つため完全な構造隔離ではない (正直に auditor.md/D38 に記録)。

> **Phase 3 設計時の参考: Google eng-practices** (github.com/google/eng-practices)。コードレビュー規範を reviewer 側と author 側の両方向で定義している。Izanagi の coder = author / auditor = reviewer に写像でき、auditor の「何を見るか」チェックリストの原料 (二層基準・reviewer の 5 観点) を auditor.md に翻訳済み。

### axis-proposer (Phase 3 段 8a で実体化 = `.claude/agents/axis-proposer.md`、設計 D47)

- **役割:** critic の機序帰属を入力に「次の変異軸候補 (EVOLVE-BLOCK hole の位置と骨格)」を構造化提案する。axis-onboarding.md §1 の段階 A の実体化。下流は人間承認 gate → 段階 B (シートの独立再導出 + 敵対レビュー)。B〜F のゲートは一切短縮しない。提案の採用判断はしない (それは D 偵察の出口 = 人間判断)
- **tools = [] (ツールなし)。** planner-v4 (D45)・coder-v4 (D39 決定 7) と同型の構造遮断。入力は信頼中核が前渡しする: critic 機序帰属の**二層射影** (勝ち筋の値は落とし診断数値は保持。recommend は丸ごと除外、attribution 出典優先) + EVOLVE_BLOCK ソースの stock 抜粋 (全 mapped 領域に機械的一致、裁量選定不可) + 編集面の地図 (開通・未開通対称、効きやすさの手がかりなし)。死んだ軸は生死の二値のみ (機序帰属も流さない)
- **model:** 強いモデル (機序からの軸合成 = P2-4 で LLM の実証済み価値とされた推論)
- **出力:** 構造化提案のみ (軸定義シート §2 の提案版の部分集合、候補 1〜3 件)。fails-closed はフィールド存在検査のみ — 恒真検出は人間 gate の意味判断 (既知限界、D47 必須条件 2)。埋まらない欄は unknowns に落とす (規律 3)
- **規律:** 提案は untrusted データ (規律 6、axis-onboarding §2 の「軸提案が LLM 由来のとき」が受け皿)。provenance 三点セット (raw critic 出力 / 射影版入力 / 対応表) を凍結し事後検証可能にする。8a 由来軸は当面「探索補助」に限定 — 段 6 headline の対象軸にしない (事前登録の命名固定と原理的に非両立、D47 決定 5)
- **確定制約の正典 = D47** (採用条件・射影の二層規律・出口基準・却下案)。本節は常設定義の要約。配管の現状 (critic 帰属の非永続化・whiteboard 物理防壁) は `orchestrator/campaign/p3_s4_loop.py` を参照

---

## hooks (方針 A の最小第二防壁・Python)

ECC のように大量に持たない。正しさの第二防壁は `guard_write` / `guard_bash` の 2 本 (D30/D33) で、
**テキスト内容の検査には完全性を負わせない**。これらとは別系統のコンテキスト衛生として
`guard_read` を 1 本持ち、Claude の PreToolUse には合計 3 本を配線する。現行の責務・配線・既知限界は
`hooks/README.md` が正本。

Codex には未配線 (D54〜D56)。tool input と継承 tool surface が Claude と異なるため、設定だけを複製せず、
製品別 adapter と parity test を作ってから配線する。正しさ防壁の第三の論理 hook は追加しない
(`guard_read` は正しさ防壁ではない)。

### guard_write (PreToolUse: Write|Edit|MultiEdit|NotebookEdit)
- proof-chain 成果物 (WAL / campaign.lock / build-variants 等) への直接書き込みを拒否 (規律2 = verifier 迂回の阻止)
- variant の編集面を EVOLVE-BLOCK の designated ソースに限定 (D24)

### guard_bash (PreToolUse: Bash)
- 同等の書き込みを Bash 経由で行う経路を遮断

旧設計の hook 1 (「`#ifdef TRACE` の外への検証専用メタデータ書き込みを警告」= payload テキスト検査) は **D33 で物理削除した**。規律1 (観測者効果) の内容検査は一次防壁 (source_digest の preprocess 後ハッシュ・#include HEAD 固定・diff-of-diffs) が担う。実装と known-limitation は `hooks/README.md`、経緯は phase3.md タスク3 (H3) と D30/D33/D34。

---

## 将来予約: instinct 的学習機構 (Phase 3.5 以降)

ECC の continuous-learning v2 (セッションからパターンを抽出して再利用可能な skill にする) は、Jitskit の whiteboard memory の進化形として参考になる。

ただし初手では入れない。これは探索が回り始めてからの最適化で、Phase 1-2 では過剰。whiteboard memory (却下した設計の蓄積、output/insights/ と統合) のレベルで十分。Phase 3.5 で OEE を入れるときに、instinct 的な「成功パターンの抽出と再利用」を whiteboard に接続することを検討する。
