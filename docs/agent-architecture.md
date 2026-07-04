# サブエージェント・アーキテクチャ

Claude Code のサブエージェント (`.claude/agents/*.md`) と hooks の構成、および段階導入計画。

設計の出発点は Jitskit と IDS のマルチエージェント構成。それを Claude Code のネイティブ機能に写像する。ECC からは「tools/model を明示してロールを権限で縛る」「hook で規律を機械執行する」運用パターンを借りた (ECC の規模そのものは反面教師)。

---

## 段階導入の原則

サブエージェントは Phase ごとに必要なものだけ足す。最初から全部並べない。理由は decisions.md D7 — ablation で各ロールの効果を測るため、また探索失敗時の切り分けのため。

```
Phase 1: verifier, calibrator           (実体化済み)
Phase 2: + critic (P2-3), profiler (P2-4) (実体化済み)
Phase 3: + planner, coder, auditor       (仕様予約)
Phase 3.5: (OEE。新規ロールは不要、層3の選択ロジックを格上げ)
```

Phase 3 のロール (planner/coder/auditor) は、本ドキュメントに仕様を予約してある。該当 Phase に来たとき、この仕様に従って `.claude/agents/*.md` を生成する。**今は作らない。** (Phase 1-2 のロール = verifier/calibrator/critic/profiler は実体化済み。)

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
- **派生:** ablation 用の中立版 `critic-experiment` (P2-5 誘導アーム専用。リーク制御のため最適解の literal な事前知識を物理削除した版) は P2-5 限定で使用した。D21 参照

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

### coder (Phase 3・仕様予約)

- **役割:** planner のプランを CCBench コードへの diff (EVOLVE-BLOCK 内) に落とす。他 CC の最適化を移植する
- **tools:** コード読み書き、ビルド
- **model:** 強いモデル
- **規律:** 検証用情報を出すときは `#ifdef TRACE` に隔離する。CC のデータ構造に検証専用フィールドを常駐させない (絶対規律1)。移植時は最適化カタログ (前提/効果/競合) を参照して前提条件を満たすか確認する
- **⚠ kickoff の確定制約は本節でなく `docs/phase3.md` + D22/D23/D24/D30 を正典とする** (本節は Phase 3 着手前の予約仕様で、kickoff 設計を反映していない)。coder.md を生成するときは最低限: (1) 編集面は EVOLVE-BLOCK の `#if` 枝内の straight-line code のみ (#include/型/マクロ定義の追加禁止、閉じた領域制約)、(2) COMMIT を書く唯一の経路は `pipeline.evaluate()`、(3) 勝ち筋値・機序説明のリーク制御 (P2-5/D21 の Phase 3 版、phase3.md 残存リスク)、(4) hooks は方針 A で最小第二防壁 = 正しさ/identity の担保は一次防壁 (source_digest / 観測者効果二重検査) にある、を織り込む
- **駆動方式の環境制約 (worklog 2026-06-29 から昇格):** この環境には **headless の claude CLI が無い**。roadmap §3.8 の「ループ主導権は orchestrator、LLM は iteration 単位で fresh に呼ぶ」を実装するとき、orchestrator が CLI を子プロセスとして呼ぶ形は取れない。P2-5 誘導アームは「各試行を fresh サブエージェント (本会話を見ない) が `guided.py` を Bash で駆動する」形で迂回した — coder ループも同系の駆動 (fresh サブエージェント + Python ハーネスの Bash 駆動) を前提に設計する。

### auditor (Phase 3・仕様予約)

- **役割:** N iteration ごとに variant を監査し、verifier が見逃した不変条件違反 (reward hack) を見つけてテストを追加する (Jitskit の auditor)
- **tools:** コード読み取り、テスト追加の書き込み
- **model:** 強いモデル (adversarial な reasoning が要る)
- **規律:** 最適化を担当するエージェント (planner/coder) とコンテキストを分離する。見張り役が最適化圧力に毒されないため。CC 版の reward hack ギャラリー (related-work.md の Jitskit 節, Appendix B の CC 翻訳) を参照する

> **Phase 3 設計時の参考: Google eng-practices** (github.com/google/eng-practices)。コードレビュー規範を reviewer 側と author 側の両方向で定義している。Izanagi の coder = author / auditor = reviewer に写像でき、coder の「レビューしやすい diff (EVOLVE-BLOCK を最小に、意図を明示)」と auditor の「何を見るか」のチェックリストの原料になる。**今は参照しない (Phase 3 で auditor/coder の `.md` を書くとき具体化する)。**

---

## hooks (方針 A の最小第二防壁・Python)

ECC のように大量に持たない。`.claude/settings.json` の PreToolUse に配線済みの 2 つだけ (D30/D33)。auditor の事後監査に加えた「書き込み時点の第二防壁」であり、**テキスト内容の検査には完全性を負わせない** (2 巡の敵対検証で「テキスト検査に C++/shell の完全性を負わせる設計は原理的に破れる」と実証済み — 責務再配置の経緯は D30/D33)。

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
