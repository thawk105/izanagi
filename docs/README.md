# docs/ — 文書の地図

リポジトリの文書がどこにあるかの地図 (CLAUDE.md「主要ドキュメント」節から委譲、2026-07-11)。
毎セッション必読ではない — 文書の所在を引くときに読む。毎セッション使う正本 (worklog 末尾・
現行 phase doc) は CLAUDE.md「現在地」が指す。

## 大きい文書の引き方 (D35)

`decisions.md` は `grep -n "^## D"`、`glossary.md` は用語検索を索引にし、該当見出しから次の見出しまで
だけを読む。worklog 過去分、監査、insight、生ログも検索・tail・offset/limit で絞る。全文が必要な解析は
独立コンテキストまたは digest に委ね、メインコンテキストには構造化された結論だけを戻す。

## docs/

- `roadmap.md` — 設計の全体像と理由 (戦略)。全文必読は Phase 初回セッションと改訂時のみ、日常は節名で引く (冒頭「読み方」、D35)
- `decisions.md` — 設計判断と却下案 (D 番号)。`grep -n "^## D"` が目次 (引き方は直上の節)
- `phase1.md` / `phase2.md` — タスク分解 (完了・凍結)
- `phase3.md` — 現行 phase doc。チェックリストと must 表 = タスク粒度の完了状況の正本
- `phase3-main-experiment.md` — 主実験の事前登録
- `phase3-8b-restart-runbook.md` — 8b 再開 (床値実測 → freeze v2 再凍結 → oracle 実走) の手順・
  毎回の preflight・偽の赤の見分け・未実装段の正本。状態は持たない (状態は worklog 末尾)
- `phase3-8c-preregistration.md` — 段 8c 正式系列 (H1/H2 × on/off/swapped) の事前登録。
  発効条件・発効の判定手続き (条件充足の機械確認で自動発効、条件契約は hash 世代台帳で凍結)・
  全件報告の機械強制が現在どこまで効くかの正本 (D116、[T-327])
- `b10-backoff-shape-preregistration.md` — B-10「待ち方 / 待ち量の直交切り分け」の登録追試。
  平均を μ に固定した半幅 3 形 × 6 平均 × 3 workload × 独立 3 ブロックの grid、
  判定規則の機械可読 spec (符号反転 exact 検定・Holm・曝露 gate・欠測規則)、
  待機の物理残差の実測欄、発効条件と束縛の正本
- `b10-backoff-static-tail-preregistration.md` — B-10 の静的 backoff 右 tail (物理値 1000 マイクロ秒超、
  表現上限 9999) を記述的に特性化する事前登録 (D1813 第 2 段、[T-2500])。上限を起点に半オクターブで
  刻む 7 点格子と境界参照 1 点、literal で固定した動作点と測定順、abort 率の飽和を報告する述語
  (対数傾きの同時上下限による平坦/低下継続/判別不能の 3 分割と、上限まで続くことの要求)、
  域内非飽和を含む排他的な結末の集合、失敗条件、第 1 段の探索の全開示、
  本走 driver への束縛と投入前条件の正本
- `b10-backoff-static-tail-submission.md` — 上記本走を Pegasus へ投入し、3 workload の成果物を
  1 集団として報告するまでの操作手順の正本 ([T-2593])。走行種別 `t2500-tail-formal` の投入 argv、
  新 2 入力 (事前登録 commit・探索走 campaign) の前提条件、job の完走判定、集団報告の argv と
  保証しない範囲。格子・判定式は持たない (事前登録が正本)
- `dynamic-backoff-preregistration.md` — Silo 上の Cicada 型 adaptive backoff の 3 定数を動的化する変異
  (計数窓 / 適応刻み / 動的上限) の事前登録。7 腕、対内 log 比の判定式と等価域、H1〜H7、欠測規則、
  診断 run と認証の範囲、束縛の正本
- `backoff-counterfactual-preregistration.md` — adaptive backoff の反実仮想対照 ([T-2265]) の事前登録。
  3 値 step policy の腕、割当についての 1 窓先 ITT の定義式と符号、対称 log 等価域と TOST、
  主層と副次層、除外規則、12 seed の逐語一覧、検出力が仮定に条件付くこと、束縛と主張範囲の正本
- `backoff-policy-performance-preregistration.md` — step policy 腕の trace 無効な性能 ([T-2417]) の
  事前登録。3 腕の全 6 permutation で位置と一次持越しを均衡させる 18 block、対内 log 比の判定式と
  対称等価域、標準偏差の 2 参照級にもとづく反復数の根拠、構造違反と測定欠測を分ける規則、
  18 seed の逐語一覧、未認証であることの機械的隔離と自動撤回機構が無いことの明示、束縛の正本
- `backoff-policy-performance-preregistration-erratum-1.md` — 上記 v1 の正誤表 1。
  腕をまたぐ source bytes 一致と block をまたぐ binary identity 一定が、どちらも
  step policy の source 置換と build の非再現性ゆえに成立しえないことの実測と、
  identity 述語だけを訂正して「3 腕は互いに異なる」正の対照を足した記録。
  推定量・等価域・判定語・欠測規則・seed・巡回・block 数は v1 のまま
- `backoff-counterfactual-cohort2-preregistration.md` — 同じ機序を独立 cohort で測る事前登録
  ([T-2265])。時間 cap を実質無効化した count-closed 窓、割当を持たない terminal event、
  cohort 1 と推定対象が同一でないこと、terminal 非閉鎖と 0 commit の扱い、cohort 2 の 12 seed、
  割当整合性検査、認証の射程が既定 seed と 48 スレッドに限られることの正本
- `t1998-balanced-stock-inline-preregistration.md` — balanced の「無 backoff 対 静的 fixed 5 µs」
  1 対を現行 Pegasus 環境で測り直す事前登録 ([T-1998]、認可は D1874)。gitlink・環境契約 digest・
  job body script digest・arm 別 source digest の実値、測定時点と現行解析規則の 2 つの sha を
  別々に pin する束縛規則、事前登録前に取れた生値を主張へ入れないことの正本
- `b10-multinode-formal-run-design.md` — B-10 正式系列を複数ノードへ分散する設計 ([T-1905])。
  分散単位 4 案の判定、律速が正しさ検査であることと多重化が正しさ受領証の発行境界に当たる事実、
  投入前の必須修正、ユーザー裁定へ返す項目。**投入の承認ではない**
- `worklog.md` — 日誌。末尾エントリ = 可変状態の正本。書式とローテーションは同ファイル冒頭
- `spool/README.md` — 3 台帳へ書くための fragment 形式と fold の正本。並行セッションが同じ行末を
  奪い合わないよう、wave は fragment だけを書き、採番と追記は land が lock 内で一度だけ行う
- `ai-provenance.md` — commit ごとの AI 製品・モデル・推論深度・役割を記録する `AI-Agent` trailer 規約
- `failures.md` — 失敗台帳。起こした問題の型別索引と恒久対応の実体ポインタ (2026-07-13 新設。
  問題発生時は worklog と同時に追記、再発は既存エントリに「再発:」追記)
- `test-environment-coincidence-ledger.md` — 受入 suite の「環境の偶然を assert する検査」の
  分類と処置の正本 ([T-1848])。走査述語と母集合、7 クラスの判定手続き、直さないと判定した理由、
  寄与順が確定できない理由の算術を持つ。発端と機序は `failures.md` の F641
- `dev-wave/core.md` / `workers.md` / `mutation.md` / `operations.md` — `/dev-wave` 入口から
  段・条件ごとに読む living runbook。親段、worker 権限、変異、条件付き運用の正本
- `skill-self-improvement.md` — dev-wave / cleanup-branches / rulings 共通の自己改善 gate、
  routing、入口編集条件、command 別終端、検査・commit 境界
- `ruleops.md` / `ruleops-candidates.json` — test / insight の HEAD inventory、候補 package、
  人間裁定へ運ぶ retirement lifecycle の正本。削除安全や承認を自動判定しない
- `handoff/` — セッションの WAL (中断引き継ぎ + 並行セッションの宣言板。運用は同 README)
- `archive/` — 凍結記録 (監査台帳・worklog 過去分・凍結文書)。ファイル名は移動前と不変、規約は同 README
- `agent-architecture.md` — サブエージェント構成・製品別 adapter・権限・規律の正本
- `orchestrator-design.md` — orchestrator の ACID/WAL/排他、環境タグ
- `pegasus-runbook.md` — Pegasus の qlogin / PBS バッチ / module / 並列実行 / ストレージ運用手順
- `pegasus-node-variance-protocol.md` — ノード間性能差を測る新規 protocol の事前登録 ([T-810])。
  投入は同文書の 2 段階の承認 (第 1 段 = builder と生死確認、第 2 段 = 本走) を経たときだけ
  許される。land は承認ではない
- `ccbench-anatomy.md` — CCBench 構造調査
- `cc-diagnostics.md` — CC 調査の診断手順を症状から引く索引。非完走・ハング・進捗停止・デッドロックの
  疑いを、実装を読む事前選別と持続閉路で機構へ帰属する手順、その適用できない条件、既知の不足
- `axis-onboarding.md` — 変異軸オンボーディングの手順書
- `isolation-phenomena.md` — verifier が判定する serializability 異常 (G0/G1/G2) の分類
- `glossary.md` — 用語集 (用語を grep して該当項目だけ読む)
- `related-work/` — 関連研究 (README.md が本体 — 7.7 が主張軸別の調査状態と不在主張の成立条件の規則 +
  claim-survey/ 主張軸別の凍結棚卸し・監査 + shinka-deepdive.md 付録 + literature-map/ 文献マップ + notes/ 調査ノート)
- `paper-story/` — 論文ストーリーの横断合成 (日付付き凍結スナップショットを束ねる、詳細は同 README)
- `paper-story-backoff/` — adaptive backoff 単独論文 (2 本目) のストーリー。`paper-story/` と同じ凍結契約、
  正典は decisions / worklog / insights。本体論文との境界は同 README
- `roadmap-history/` — roadmap の版凍結置き場 (改訂セレモニーの正本 = 同 README)
- `phase3-t189-model-routing-preregistration.md` — model 経路 (sol / luna) 比較実験の事前登録。
  未解決点の処遇は D674 で確定済み。素材の到達状況 (task catalog・price snapshot) は同書 §13 と総括が正本
- `phase3-t189-task-catalog-classification.md` — 上記 §6.2 の task type 4 層の分類基準 (`t189-task-type/v1`)。
  D674 が独立分類者2名の署名を見送ったため、公開基準による自前分類の規則と限界を置く正本。
  分類結果の実体は `output/t189-routing-preregistration/task-type-classification-v1.json`
- `phase3-s*.md`・`phase3-8b-*.md`・`phase3-8c-*.md` — 現行 phase doc の従属文書 (段の設計書・手順書)。段ごとの内訳は phase3.md から辿る (段番号をここに列挙しない — 段の追加で腐るため)
- `freeze-permanent-design.md` — freeze 族の恒久設計の正本 ([T-080]、R1..R16 承認済み 2026-07-22)
- `calibration-freeze-authority-bundle-design.md` — 較正 (環境契約の活性化) と凍結 (ratified freeze の世代) を束ねる**上位層**の恒久設計 ([T-657] R3。段 0 実施中で status は `incomplete`、裁定の状態は同書 §12、正本の precedence 規則は同書 §1)。freeze 族**内部**の設計正本は `freeze-permanent-design.md` と `freeze-permanent-design-s2.md` の 2 件
- `env-contract-activation-prerequisites.md` — pegasus g1→g2 activation の必要条件・現在値・証拠・未充足理由・owner を引く日付付き readiness index。条件の意味と値の正本は同書が指す code / record / decision / fixture manifest
- `freeze-permanent-design-s2.md` — 第 2 設計段パッケージ (§13 の exact 化 + 変異事前登録候補。段完了で凍結する design 族。未了事項は同書冒頭の状態行が正本)
- `mutation-restore-durability-design.md` — 変異復元を grace 予算依存から journal + fsync + 再開時修復へ転換する設計 ([T-487] 起草。第一 slice = 使い捨て専有 worktree (`tools/mutation_worktree.py`) だけ実装済みで §9.1 の充足は 0/6。状態は同書冒頭、裁定軸は §9、着手範囲は §9.3 が正本)

## docs/ の外

- `AGENTS.md` — Codex 用の薄い作業入口。共有規律の正本 `CLAUDE.md` と現行正本へのポインタ
- `orchestrator/` — 探索・評価・campaign 駆動の Python 実装 (構成と安定核は `orchestrator/README.md` が正本)
- `patches/` — CCBench への意図的 patch (positive control・合成 variant・診断計器)。来歴は `patches/README.md` が正本
- `src/` — coder 向け仕様 (`coder-spec.md` §1-2 が現役、`coder-leakproof-context.md` = リーク遮断入力の正本)
- `output/` — 成果物 (campaigns/<id>/ と env/<tag>/ の二軸、D13 — 詳細 output/README.md)。insight は `output/insights/`。
  AI 開発作業の統計記録 (task-run 台帳、開発プロセス観測 — D66) は `output/task-runs/README.md` が詳細正本
- `tools/` — 運用スクリプト。**実行場所の契約 (Pegasus でどれをログインノードで走らせてよいか) は
  `tools/README.md` が入口、`docs/pegasus-runbook.md` §7.0 が規範の正本**。
  (`ruleops.py` = read-only inventory / 候補 package 検査 /
  `check_docs.py` = 文書 lint / `check_codex_agents.py` = Claude role と
  Codex adapter の本文・metadata・schema・policy parity、実行可否・発見可能性の fail-closed 検査 /
  `check_ai_provenance.py` = commit trailer 監査 / `codex_worker_launch.py` = dev-wave の codex 子を
  起動し、1 job につき 1 件の `receipt.json` (schema v3) を wave の job artifact directory (repo 外、
  所在は worklog と環境 runbook) へ書く producer。段・lane・model・effort・base commit・CLI 版・
  上限 (`limits`)・実測 (`actuals`)・打ち切り軸 (`stop_reason`) を持ち、**dev-wave の工数と失敗の
  一次資料**である (地図であって resource authority ではない。値の正本は receipt 自身) /
  `codex_worker_ledger.py` = codex rollout ログから
  worker の session/stage/token/終了分類/retry を決定的に集計する read-only 台帳 (T-179) /
  `claude_session_ledger.py` = claude session transcript から model call と raw token 交通量を
  母集団付きで集計する read-only 台帳 (D206。費用・課金・利用枠ではない)。**同一の canonical
  `message.id` は同一 model call とみなし、複数 transcript へ複製された replica を 1 回だけ計上する。**
  この同一性公理は外部 transcript 側では検証できないので、証明できない replica 疑いは fail-closed に
  倒す。dedup を経た report は `population.dedup_algorithm_version` を持ち、**版が違う report の
  token 値を直接比較しない** /
  `collect_wave_usage.py` = 上記台帳を wave ごとに 1 件の typed artifact として repo 外へ
  前向き収集する consumer (D220。operand と挙動の正本は同 tool の `--help`)。
  **先頭が `-` の project slug は `--project=<slug>` の等号形で渡す** (split 形は argparse が
  option 名と解釈する)。rc は `0`=収集できた / `3`=ログインノードと確証できたため規律により
  正当に走らなかった / `2`=argv 不正 / `1`=それ以外の故障。**収集は D220 により wave 完了 gate では
  ないので、rc が 0 以外でも既に完了した wave を失敗へ戻さない** — 呼び手は rc と artifact の
  `collection.status` を併読する /
  `plotting/` = campaign の論文品質作図、規約は `tools/plotting/FIGURE_CONVENTIONS.md`)
- `hooks/` — 正しさの最小第二防壁 (guard_write / guard_bash) + 別系統のコンテキスト衛生
  (guard_read)。詳細は同 README
- `.claude/agents/` — role 本文と Claude Code 固有の model/tools 契約 (現有一覧は ls が正本)
- `.codex/agents/` — Codex role adapter の現行状態・再開条件の正本 (D54〜D56、F16/F17)
- `.codex/role-adapters/` — 非自動発見の Codex adapter 定義 (稼働可否は `.codex/agents/README.md` が正本)
