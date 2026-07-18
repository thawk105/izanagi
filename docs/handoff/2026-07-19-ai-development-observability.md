# AI 開発作業の統計記録 — task run 台帳と効率監査

- 目的: AI エージェントによる開発の時間・トークン・テスト・レビュー・手戻りを追記型で記録し、遅延原因の監査と作業ループ改善を可能にする
- 状態: 中断
- 最終更新: 2026-07-19 02:19 JST
- 基準コミット: 95ed6fe (計画作成時点。実装着手時に HEAD と作業ツリーを再確認)

## 着手条件

- 並行セッションの handoff と作業ツリーを再確認し、編集対象が競合しないこと。既存の backlog / test-hygiene
  3 計画とは独立だが、worklog・decisions・docs 地図・check_docs を同時編集するセッションとは直列化する
- 最初は 2 週間または 10 task run の pilot とし、全面的な強制や大規模な自動計装を先行しない
- 記録値は観察データであり、モデルの優劣や作業者評価へ単独利用しない。タスク難度、成果、手戻り、finding、
  所要時間を併記する

## 完了した中間成果

- ユーザーとの設計相談で配置方針を合意:
  - commit message は既存 `AI-Agent` provenance のまま。トークン・料金を trailer に追加しない
  - 生の作業統計は `docs/` でなく成果物・一次資料側に置く
  - commit ID を主キーにしない。commit 前の失敗、棄却案、待機、1 task 複数 commit を失わないよう
    `task_run_id` を主キーにし、commit は後続 event として関連付ける
- 推奨レイアウト案:

  ```text
  output/task-runs/
  ├── README.md
  ├── <task-run-id>/
  │   ├── task.json
  │   └── events.jsonl
  └── reports/
      └── <period>_task-efficiency.md
  ```

- 最小観測軸: lead / active / wait 時間、工程、agent run と取得可能な token、targeted/full test の回数・
  秒数・結果、red→green 周回、review の real/refuted finding、手戻り、関連 commit
- 実装・ファイル作成・正本改訂は未着手

## 未完の作業と次の一手

1. **既存契約との整合確認**
   - `output/README.md`、`docs/worklog.md` 冒頭、D35、D53、`docs/failures.md` の役割分担を再確認する
   - `output/task-runs/` が探索 campaign の proof-chain WAL と混同されない名称・説明にする。この台帳は
     開発プロセスの観測であり、fitness / correctness / benchmark の証拠ではない
   - Git 追跡方針を裁定する。推奨は task.json / events.jsonl / 集計 report を追跡し、秘密・セッション URL・
     prompt 本文・生ツール出力・料金情報は記録禁止。サイズ上限とローテーションも README に定める
2. **schema v1 の事前定義**
   - `task.json`: `schema_version`, `task_run_id`, `objective`, `task_class`, `started_at`, `base_commit`,
     `measurement_policy`。終了時に書き換える設計にせず、終了は event にする
   - `events.jsonl` 共通 envelope: `schema_version`, `task_run_id`, `seq`, `timestamp`, `event`,
     `measurement_source`。event ごとの必須 field と単位を固定する
   - 最小 event: `stage_start`, `stage_end`, `agent_run`, `test_run`, `wait`, `finding_summary`, `commit`,
     `rework`, `task_end`
   - token は `input_tokens`, `output_tokens`, `cached_tokens`, `total_tokens` を混同しない。製品面が開示しない
     場合は推測せず `null` + `measurement_source: not-exposed`。概算を許すなら実測値と別 field にする
   - 時刻は timezone 付き ISO 8601、時間は `duration_s`、test は targeted / full / static-check 等を分類する
   - objective や stage 名に機密・prompt 本文を入れない。session URL / ID は D53 と同様に永続記録しない
3. **append-only writer と validator の実装**
   - 置き場所は既存 CLI / tools の責務を調査して決める。最小 CLI は `start`, `event`, `finish`, `validate`
   - `task_run_id` は日付 + 安定 slug + 短いランダム/内容 ID とし、commit hash に依存させない
   - create-only の `task.json`、単調増加 `seq`、壊れた JSON 行・未知 schema・逆行 timestamp・重複 seq の
     fail-closed 検査を持たせる。既存行を書き換えず追記する
   - 複数プロセス追記の可能性を調査し、必要なら lock + flush/fsync、または writer 単一所有を契約化する
   - AI の自然言語自己申告だけに依存しない。取得可能な test duration / result / git hash は wrapper が実測する
4. **AI 作業導線への最小配線**
   - `CLAUDE.md` の絶対規律を膨らませず、作業開始・節目・終了の導線をどの正本へ置くかを判断する。
     推奨は `output/task-runs/README.md` を詳細正本、`CLAUDE.md` または委譲先には短いポインタだけ
   - class 1 の短い read-only 質問は記録対象外。class 2 / 3 のうち実装・長時間監査を pilot 対象にする
   - handoff は生きた進捗、worklog は末尾の集約と異常、task-run は統計イベント、と役割を重複させない
   - セッション正常終了時に `task_end` と関連 commit を記録し、worklog には task_run_id、主要集約値、
     異常だけを載せる。commit がない task も記録可能にする
5. **テスト効率の記録方法を実装**
   - targeted / full / docs-check / provenance-check を区別し、command 全文でなく安定した suite ID、duration、
     collected / passed / failed / skipped、exit status、trigger を記録する
   - `trigger` は `baseline`, `after-change`, `after-failure`, `final`, `review-fix` 等。これによりフルスイートの
     過剰実行と red→green 周回を後から再構成可能にする
   - test wrapper が既存 `tools/run_tests.py` の意味論や出力を変えないこと。記録不能でもテスト本体を
     fail-open にするか、台帳必須時だけ fail-closed にするかを明示裁定する
6. **集計器と最初の監査 report**
   - task ごとに `lead_time`, `active_time`, `wait_time`, stage 比率, test 時間比率, full-suite 回数,
     red→green 周回, rework, agent run 数, token 内訳, real/refuted finding を集計する
   - token/commit、行数/token を主 KPI にしない。推奨比較は同種 task 内での時間分解、テスト時間、手戻り、
     finding 実効密度。欠測率を必ず併記する
   - 10 task run または 2 週間後に「遅い上位 task と原因分類」「削れる工程」「削ってはいけない正しさ防壁」
     を `output/task-runs/reports/` に出し、ループ変更候補はユーザー裁定へ回す
7. **検証**
   - schema / writer / validator / aggregation の unit test を追加する
   - negative control: truncate 行、重複 seq、未知 event、負 duration、total 不整合、commit 前 event の許容、
     token 非開示、1 task 複数 commit を含め、validator が壊れた台帳を実際に赤くする
   - pilot fixture から集計値を手計算し一致を確認する。記録を有効化しても既存 test / campaign WAL /
     benchmark の結果や意味論が変わらないことを確認する
   - 関連テスト、`python3 tools/check_codex_agents.py`、`python3 tools/check_docs.py` を実行する
8. **文書化と完了処理**
   - 役割分担とデータ保持方針を `output/task-runs/README.md`、地図を `output/README.md` と
     `docs/README.md` に最小追記する
   - 運用変更の判断・却下案・pilot 再評価条件を `docs/decisions.md` に記録する
   - phase 作業として採用する場合は関連 phase checklist を実装と同じ commit で更新する
   - worklog に実装結果、test、pilot 開始条件、task_run_id を集約して本 handoff を削除する
   - commit 後に `python3 tools/check_ai_provenance.py`。push / PR は人間が行う

## 落とし穴・気づき

- commit ID 主キーでは、commit されなかった試行と commit 前の大半のコストが消え、生存者バイアスになる
- agent 数や token を減らすこと自体を目的化しない。正しさ gate、negative control、実 finding を削って見かけの
  効率を上げるのは reward hacking であり、CLAUDE.md 絶対規律 2 / 3 に反する
- wall-clock と active time を分ける。PBS queue、ユーザー裁定待ち、ツール approval、計測排他待ちを同じ
  「開発時間」に混ぜると改善先を誤る
- token は製品・モデル・cache・圧縮で定義が違う。`measurement_source` と欠測を保ち、異種製品間の単純比較をしない
- prompt、会話全文、session URL、個人情報、秘密、料金・利用枠は記録しない。目的は工程統計であり監視ログではない
- 開発 task-run 台帳は campaign WAL の correctness / fitness proof chain ではない。名称・validator・report で混同を防ぐ
- 計装自体が作業を遅くする可能性がある。pilot では記録オーバーヘッド (秒/操作数) も測り、便益がなければ縮小・撤去する
- 既存の可変状態正本は worklog 末尾と phase doc のまま。task-run は観測一次資料で、TODO や進捗正本にしない
