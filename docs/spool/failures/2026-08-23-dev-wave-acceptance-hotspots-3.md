---
schema: izanagi-spool-v1
ledger: failures
authored: 2026-08-23
wave: dev-wave-acceptance-hotspots
seq: 3
---

## 新規

### {{F:scandir-fail-open-siblings}}. 走査型 gate の 1 箇所だけを fail-closed にし、同型の兄弟 3 箇所を残した [恒真ゲート]

- 事象: (2026-08-23、段 6 の敵対レビューが指摘し親が現物で裏取り) 段 4 裁定は
  `_filesystem_file_set` の列挙失敗を握り潰さない形へ直すと決め、段 5 はそのとおり実装した。
  しかし同じ `tools/codex_reasoning_ab.py` の中に、同型の「列挙できない ⇒ 空 ⇒ 通す」が
  3 箇所残っていた。git closure の空判定 `any(path.rglob("*"))`、pseudo-ref 列挙の
  `git_dir.iterdir()`、`_metadata_manifest` の `root.rglob("*")` である。
  とくに 1 つ目は反転が明確で、`.git/logs` を列挙不能にすると
  「reflog closure is not empty」が出ない。新実装は root `.git` を枝刈りし、
  fsck も `--no-reflogs` なので、隠された reflog を見る層が 1 つも残らない。
- 根本原因: **裁定が「この関数の穴を塞ぐ」という単位で書かれ、「この gate が依存する走査すべて」
  という閉包で書かれていなかった。** 段 4 の pin 閉包検査は編集面の関数を起点に行ったため、
  同じ判定に寄与する別関数の走査 API が視野に入らなかった。段 5 の新設テストも
  `_filesystem_file_set` の `os.scandir` だけを観測するため、この反例では赤にならない。
- 恒久対応: {{D:scan-gate-fail-closed}} が 4 箇所すべてを共通 helper 経由へ統一し、
  閉包を「同じ判定へ寄与する全走査」で取ることを決めた。
  変異 M08 (closure 検査の列挙失敗を握り潰して空扱いに戻す) を登録し、KILLED を確認した。
- 再発検知: 走査型の防壁を直すときは、その gate の判定式が参照する値を作る**全走査**を
  参照関係で引き、`rglob` / `glob` / `iterdir` / `walk` の残存を数える。
  1 箇所を直したことをもって型が閉じたと報告しない。

### {{F:mutation-harness-cannot-pin-group-annotated-node}}. 変異 harness が xdist の group 注釈付き node を期待 node として表現できない [手順漏れ]

- 事象: (2026-08-23、変異本走の起動時) probe 相で観測した期待 node の 1 件が
  `...::test_stale_commit_graph_referencing_pruned_commit_is_rejected_and_manifested@real-repo`
  という形で、本走が
  `mutation harness aborted: 期待 node が pytest collection に実在しない` で rc=2 停止した。
- 根本原因: xdist は `FAILED` 行の node id 末尾へ `@<group>` を付けるが、
  `--collect-only` が出す id には付かない。harness の期待 node 実在検査は collection id と
  照合し、`_normalize_node` は `@<group>` を落とさない。したがって記録側と検査側で
  同じ node の表記が食い違い、group 注釈された node は期待 node として書けない。
  probe 相では期待 node が空だったため、この検査に触れず表面化しなかった。
- 恒久対応: 未実施。{{T:mutation-harness-group-annotated-expected-node}} として起票した。
  本 wave は該当 1 件を runner の `--deselect` で外し、理由を実行スクリプトへ書いて回避した。
  残る 6 件で当該変異の検出力は示せている。
- 再発検知: 期待 node に `]` より後ろの `@` を含む文字列があれば、本走の起動前に落ちる。
  probe 相の観測集合をそのまま本走の期待集合にする運用では、`REAL_REPO_SERIAL_NODES` など
  `xdist_group` が付く node を含む対象 file で必ず当たる。
