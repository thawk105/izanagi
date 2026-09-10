# 段4裁定

- real: 最新完了集合は相談中に1件増えた。旧6走の事実は保持し、2f3d23288242db9879936059107ffd32を追補する。最大shard wall397.021秒、gw8占有272.355秒、最後1worker tail2.610秒。
- real: shard開始時刻が違う。最大shardのdurationを受入全体の経過時間と呼ばない。
- real: 初期orchestrator copytreeの後に一部sourceを上書きする。まだ削減候補としての費用・意味保存は未実証。
- refuted: 明示validateの除去、異なる状態へのverifyの削減を安全な重複除去とみなす。反復検出を維持できないため不採用。
- 採用: 既存phase_pluginを改変せず、計算ノードの冷えたprocessで現行fixtureのphase費用を1回診断する。候補の実装より先に行う。
- 一次測定の範囲: 5 nodeを1 processで実行し、実helper発火回数と区間を記録。既存pluginの親process観測、子Python内部を含まない限界を明記。入れ子時間を二重計上しない。
- 見込みがあれば次に別D95 authorの使い捨てprobeへ。見込みがなければ実装なしで段7〜9へ進む。現段階では実装面差分0で変異対象なし。
- 規律2・fixture私有copy・反復検証・全正負検出・全collectionの受理集合を維持。t1259/conftestは所有外。
- 改善の採用条件はD104の同一allocation A-B/B-Aと実発火観測。今回の診断だけで改善効果を主張しない。
- 裁定inboxは起動後の新規更新なし。D1936項35を変更しない。

## 診断後の確定

- 990044.nqsv、bnode022、固定HEAD98a3d7c9e。5passed、pytest210.48秒、JUnit210.328秒、runner/dispatcher rc0、会計216秒。
- `_build_t080_stub_free_e2e_repo`2発火、81.1253/73.2786秒。全orchestrator copytree2発火、0.9863/0.8216秒。上書きされるファイルはこの全量の一部でしかない。
- 計装条件で全orchestratorコピーをゼロにする非現実的な場合でも、該当区間はbase構築の約1.2%以下。実際の削除候補はこれより小さい。48workerの費用やwallへは外挿しない。
- output複製30.3418/23.4245秒、子Python39.9497/40.1946秒が大きいが、前者はGit-visible検査実体、後者は実public検証と反復検出。削って検査を弱めない。
- 本waveの改善実装は不採用。安全な有効改善が不可能と結論しない。D104のA-B/B-Aは候補を採用しないため未実施、効果ゼロを統制実験で確定したとも主張しない。
- 新規probe、prewarm/cache、検査追加、実装差分は0。段5/6はdispatcherの4→7例外、変異は差分0免除。実repoの関連5nodeを実走済みで、記録後の受入全走は必ず実行する。
