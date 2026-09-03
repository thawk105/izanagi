## 実装した内容

- 固定 ledger `raw-record-rejections.jsonl` と issuer の名前衝突 gate を追加。
- canonical JSONL event、排他追記、tail 切り捨て、単一 write、fsync を実装。
- post-validation rejection のみ記録し、失敗時は `IO_ERROR` を追加して rejection を維持。
- assembly に独立した ledger snapshot を付与。読み取り失敗は assembly 判定へ昇格しない。
- report に event、3 母数、`not_selected`、未解決 absent、履歴状態、但し書き付き件数と率を追加。
- hash chain、deferred 記録は未導入。`_publish_exact` と producer 非保証定数は未変更。

## 受理集合の変更前後

- 受理: 従来の成功検証列は不変。新たに ledger 自身、その配下、publication root を planned path とする入力だけを拒否へ狭めた。
- 拒否: 従来は戻り値だけだった post-validation rejection を耐久記録する。追記失敗でも成功へ転じず、`IO_ERROR` 付き rejection のまま返す。

## 追加・変更したテスト

- producer: canonical event、tail 修復、append failure、batch の検証順、invalid ledger の独立性を追加。
- 既存 deferred test に ledger 不生成を追加。
- issuer: 発行時と reload 時の exact、descendant、publication-root 衝突を追加。別名 leaf の既存正例は維持。
- material report: 既存 node 内へ event 復元、3 母数、`not_selected`、fragment、invalid ledger の各 scenario を統合。
- 関連 meta-test:
  - material report 全 node の exact golden は `test_real_repo_serialization.py`。新規 node を作らず、node 数を 27 のまま維持。
  - producer の mutation 一対一検査は `M01`〜`M18` が対象。既存 `M14` 名を維持し、新規 test は非 `Mxx`。
  - acceptance duration ledger の全体 coverage 制約は、新規 producer・issuer node に波及し得る。

## 実走の有無

**実装済み・未実走。**

`tools/run_tests.py` で新規 producer 5 nodeと issuer gate nodeを開始しようとしましたが、Pegasus の `qstat -Q` preflight が `rc=1`、runner は `rc=16`、`child_started=false` で pytest は開始されませんでした。

非 pytest の直接 probe は成功しました。canonical event、tail 修復、append failure、invalid ledger、201/201/201 と 202/202/201 の母数、fragment status を確認済みです。AST parse、module import、`git diff --check` も成功しています。

## 波及可能性の静的列挙

- producer caller は rejection の subtype と ledger の副作用を観測する。
- assembly consumer は rejection history field を追加で受け取る。
- material report の JSON・Markdown consumer は新しい `producer_rejections` と非保証文言の影響を受ける。
- 予約名と衝突する旧 publication は reload 時に新たに拒否され得る。
- 共有 fixture `_publication`、`_eligible_attempts`、`_planned` と material report の長寿命 fixture に依存する。
- 新規 test node は acceptance duration ledger の未登録 duration として扱われる可能性がある。
- `flock` の並行追記は裁定どおり diagnostic 扱いで、実走検査していない。

## 契約から外れた点

R-A〜R-F の実装内容からの逸脱はなし。

ただし指定された親 worktree は sandbox 上 read-only だったため、同じ `b20543ba4` を基点とする writable author worktree `/work/1/SFC/tanab/izanagi/.codex/worktrees/t2141-author` に変更を残しています。commit、add、merge、rebase、push は実行していません。

## 総括

- 指定された 6 file だけを変更。
- rejection ledger と consumer 復元経路を実装。
- 成功公開への反転枝と hash chain は未導入。
- `_publish_exact` と既存 producer 非保証は未変更。
- pytest は infrastructure failure により未実走。
- 差分は unstaged のまま author worktree に残している。