# A-1 attempt-0004 前の source 契約衝突

> 以下は初回停止時の履歴である。その後、整合案への続行指示を受けて同じwaveを再開した。
> 新しいsource契約は output/insights/2026-09-11/t2397-a1-source-amendment/README.md。
> 再開のプランと相談は plan2.md / consult2-sol.md / consult2-luna.md。
> 初回の「裁定待ち」を現在の状態として読まない。

- authority: none
- default_effect: no-state-change
- 対象: T-2397 / T-2512 / T-2513、D1936 項3。
- 調査時点: local main d85bbb21196f503440ef9641e3dec095e3b43844。
- 段4で追加裁定待ち。実装、attempt-0004 投入、受入全走、main land は未実施。

## 発見

D1936 項3が承認した二原因の修正方向は維持する。ただし、関門だけでなく実 build にも
未 patch の source が届いていた。関門と実 build に同じ patch 適用後 source を渡すと、
登録済み pilot が各 build 直前に要求する tracked-clean と衝突する。

| 現物 | 事実 |
|---|---|
| paper_story_a1_paired.py の _require_v3_backoff_fixed_condition_gate | external/ccbench を capture し、configure_args を渡さない |
| 同 _run_measure_v3 | run_campaign に dependency_prefix は渡すが ccbench_dir は渡さない |
| loop.py の balanced 経路 | canonical_build_pin=cfg.ccbench_commit を常に渡す |
| pipeline.py の _build_one | 各 trace/perf build の前に、実際の ccbench_dir を _require_canonical_build_source_state へ渡す |
| 同検査 | HEAD の canonical pin 一致と tracked 差分ゼロを要求する |
| patchharness.checkout / applied | clean な隔離 checkout を作り、既存 patch の tracked 差分を body の期間保持する |
| buildcache.build_v2 | A-1 の通常経路に patch の自動適用はない |

canonical pin 511c9538e4e8efa54b45cda62e72389ed3b706ec の include/backoff.hh と
cmake/Options.cmake は固定量 decoder / BACKOFF_FIXED の供給定義を持たず、
patches/silo-backoff-fixed.patch が追加する。プランナーと敵対相談2本が git show で独立確認した。
他 driver の patch 適用下 campaign は、A-1 balanced 専用の canonical build 検査を要求しない。
成功例をそのまま A-1 へ流用できない。

## 事前登録との衝突

正本:

- docs/decisions.md の D1936 項3、D1300。
- output/insights/2026-09-01_paper-story-a1-balanced5-pilot-preregistration/README.md の §6.1 と §6.3。
- orchestrator/campaign/paper_story_a1_paired.v3-pilot.json の ccbench_acceptance と invalid_rules。
- output/insights/2026-09-09/t2397-a1-pilot-attempt-0003/README.md の §§6・9・10。

事前登録は各 build 直前を含む5境界で canonical HEAD と tracked-clean を要求し、dirty を無効とする。
D1300 はこれを実装細部でなく study の受理集合として扱う。
D1936 項3と attempt-0003 の記録には、実 build が未 patch であることと、その修正が
build 直前の tracked-clean に抵触することの解決は書かれていない。

## 段4裁定

1. 二つの既知原因（依存未供給・未 patch source）: real、D1936 の承認方向を維持。
2. build 側にも materialization がない: real。関門だけ修正しても測定対象と揃わない。
3. patch 適用後 source を現行 balanced build が拒否: real。既存経路による同値な解消案は未発見。
4. buildcache 内部の自動 patch 適用で救済される: refuted。
5. 同じ patch を使う通常 sweep の成功を A-1 へ一般化できる: refuted。
6. 親 brief の「driver / 関連テストだけで投入まで閉じる」: 前提不成立。

これは任意の仮想リスクではなく、指定された正例が実 build に到達しない契約衝突である。
DW-S04 / DW-STOP に従い、承認を不採用にせず追加裁定待ちへ戻す。段5 author は起動しない。
部分的な依存配線だけを実装して二原因閉鎖と扱わない。

## 必要な追加裁定は一件

推奨する方向は、A-1 の source 受理契約を
「実 build tree が canonical tracked-clean」から
「canonical tracked-clean を起点に、指定された既存固定 patch だけを適用した実 source」へ整合させること。
事前登録・policy・実 build 境界・consumer を同じ変更単位で整合させる承認が必要となる。

通す正例: 指定 canonical pin の clean 起点 + 指定 patch のみの source を、
同じ materializer context 内で条件関門と trace/perf build が読む。
拒否する負例: 指定 patch 以外の変更、source の取り違え、HEAD 不一致、verifier anomaly。
規律2、trace/perf 分離、stock 比較、全 arm の検査、T-2514 の detail 保存を維持する。

既存凍結 bytes と過去 attempt は保存する。新しい日付版の事前登録 / policy が必要になる場合は、
既存 study の attempt-0004 と同一視せず、登録済み study だけを投入する原則を維持する。
この契約調整と登録方式は未裁定であり、本記録を承認や新規登録の代わりにしない。

採らない案: 関門だけ patched にして build を stock に戻す、clean 検査だけ別 root に向ける、
dirty 拒否を単に削る、patch を commit して canonical pin を勝手に変える。

## 実行した検査と限界

- 変更前 A-1 関連ファイル: tools/run_tests.py 経由、196 passed in 45.70s、rc=0。
- build 境界の既存3 node: tools/run_tests.py 経由、計算ノード job 991688.nqsv、
  3 passed in 5.46s、child rc=0。clean 正例、pin / tracked drift 拒否、trace/perf wrapper を検査。
- check_codex_agents.py: rc=0、runtime activation blocked の既存契約を維持。
- check_docs.py: 変更前 rc=0。
- plan / consult 2本: 全て終了 rc=0、check_codex_output.py rc=0。

上記3 node は一時 fixture の既存検査であり、実 canonical checkout に patch を当てた live build の
測定ではない。実 patch と関門・build の関係は現行 production の静的追跡で確認した。
manager による実装 / probe の代筆、実 build、性能測定は行っていない。
受入全走と実装レビューは未実施で、完了や main land の根拠にしない。

## 所有・再開

T-2341 / T-2262 の実 worktree は未コミット差分なし、tip は main 祖先、main...HEAD の差分なし。
T-2341 の古い待ちプロセスは非接触。同名 A-1 worker は起動前不在。
durable measurement base には attempt-0001〜0003 と各 intent だけがあり、attempt-0004 は作っていない。

相談逐語は plan.md、consult-sol.md、consult-luna.md。
専用 handoff は /work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2397-a1-attempt4/handoff.md。
追加裁定後は既存 branch worktree-dev-wave-t2397-a1-attempt4 と成果物を再照合して再開する。

## dev-wave 改善候補

docs/skill-self-improvement.md を末尾で再読。候補はなし。
DW-S01 は既に実 build の前提検算を要求しているため、今回の見落としに新しい gate や手順を追加しない。
改善実装・次 wave・push はしていない。

## 還元判断

CCBench 上流の不具合ではなく A-1 の配線・事前登録契約の問題。上流への還元候補なし。

## 逐語の可逆な表示正規化

consult2の2資料だけ、git diff --checkが拒否したMarkdown行末spaceを表示版から除いた。
可視文字は不変。原文bytesは同名のoriginal.gzへ保存し、gzip -dcで完全復元できる。

| 原文 | bytes | SHA-256 |
|---|---:|---|
| consult2-sol.original.gzの展開結果 | 4758 | 682d3ff2653d623492b66c12e944ded097dd4a6398bffd9a0fb81cc02901e2ea |
| consult2-luna.original.gzの展開結果 | 7437 | f59804d9d1211d69fd973f379c57f3f40534fe4e46f8a5830e4c90503e78c738 |
