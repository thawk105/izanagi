---
schema: izanagi-spool-v1
ledger: failures
authored: 2026-09-30
wave: dev-wave-acceptance-critical-path
seq: 2
---

## 新規

### {{F:measurement-env-leaked-into-shared-template}}. 計測 wave の script の `PYTHONDONTWRITEBYTECODE=1` が受入門番の共有雛形へ写り、9/26〜29 の受入の多くが bytecode cache 冷で shard あたり約 1 分余計にかかった [ドリフト] [手順漏れ]

- 事象: 2026-09-26 に作った受入門番の共有雛形 `_shared-templates/run-acceptance-gated.sh` が、出自の t2273 系計測 wave の script から `export PYTHONDONTWRITEBYTECODE=1` を持ち越した。雛形を写した wave の受入では login collection も計算ノード worker も pyc を書かず、投入元 worktree の `orchestrator/tests/__pycache__` が冷のまま残り、計算ノードの collection (pre) が約 65 秒から約 130 秒に伸びた。9/26〜29 の 124 走で、request env にこの値がある 73 走のうち 67 走が冷。4 日間、気づかれなかった。
- 根本原因: 雛形の作成時に、写し元の行ごとに「計測の条件をそろえるための設定か、受入一般の設定か」を仕分けなかった。雛形のコメントは門番の閾値の変更だけを裁定事項として守り、環境変数の行は無審査で持ち越された。受入 report の pre は記録されていたが、日別推移を見る検査は無かった。
- 恒久対応: 雛形から export を外した ({{D:acceptance-template-no-dontwritebytecode}}、一次資料 `output/insights/2026-09-29/acceptance-critical-path/README.md`)。雛形に理由のコメントを 1 行置いた。memory `shared-template-must-not-carry-measurement-env` (共有雛形を作る・写すときは、写し元の環境変数の行を計測条件か受入一般かで仕分け、計測条件は持ち越さない)。
- 再発検知: 受入 shard の pre の二峰 (温 65〜80 / 冷 125〜140 秒) と、dispatch の `request.json` の env の `PYTHONDONTWRITEBYTECODE` の対応表 (一次資料 §2 の手順)。機械化は未実装。
