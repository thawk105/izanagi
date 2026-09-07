---
schema: izanagi-spool-v1
ledger: failures
authored: 2026-09-07
wave: dev-wave-acceptance-speedup-20260905
seq: 1
---

## 新規

### {{F:node-time-read-as-wall-time}}. node の所要時間を wall の増減として数えた [計測汚染]

- 事象: 受入高速化 wave で親が同じ取り違えを 2 回した。(1) collection の per-item
  `Path.resolve()` を削る効果を「1 shard あたり 87.6 秒」と書いたが、48 worker は並列なので
  **wall の節約は約 1.8 秒**だった。(2) 実 repo 全体の等価性テストを新設しない理由を
  「246 秒の 4 割を wall へ食い返す」と書いたが、marker 無しの 1 node を 48 worker へ配れば
  理想的な追加 load は**約 2.3 秒**であり、省略の理由として成立しなかった。
  いずれも段 6 の敵対レビューが一次資料で反証した。
- 根本原因: 並列実行される test の「全 node 時間の合計」と「最遅 worker の wall」を
  同じ単位として扱った。合計は CPU 予算、wall は臨界路であり、48 並列では 48 倍ずれる。
- 恒久対応: {{D:acceptance-floor-is-a-band-not-a-single-test}} が、受入の所要を論じるときに
  (a) 最長 node の分布、(b) 除去の反実仮想での残存最長 node、(c) 3 shard それぞれの wall と
  最遅 shard の identity、の 3 つの併記を義務づける。node 時間の合計を単独で
  wall の増減として書かない。
- 再発検知: 段 6 の有効性レンズの prompt に「node 時間を wall 増分と読み替えていないか」を
  攻撃面として明記する。本 wave の実例が反例集になる。

### {{F:call-site-count-read-as-test-count}}. grep の一致件数を test の本数として費用を見積もった [捏造/幻覚]

- 事象: 親が `grep -c "_real_output_snapshot()"` の 20 を「20 test が各 2 回 = 40 回」と読み、
  費用を 484 秒と見積もった。実際は 20 が call site の数であり、呼ぶ test は 10 本
  (parametrize 展開後 11〜12 nodeid)、呼び出しは **22 回で約 253 秒**だった。
  **約 1.8 倍の過大評価**であり、そのまま裁定・報告・brief に載った。
- 根本原因: 「1 test が 2 回呼ぶ」という構造を確かめずに、一致件数を test 数と同一視した。
  検算 (呼び出し元 test の列挙) を後から行ったが、そのとき数字を直さなかった。
- 恒久対応: 費用の見積りに grep の一致件数を使うときは、
  **呼び出し元の関数名を列挙して本数を数え直す**。本 wave では
  `output/insights/` の変異台帳に列挙結果を残す。
- 再発検知: 段 6 の有効性レンズが「見積りの母数がどう数えられたか」を必ず問う。

### {{F:assumed-registry-membership-without-checking}}. 実 repo を読む test は登録簿にあると仮定した [テスト代表性]

- 事象: 親が「実 repo に触る test は `xdist_group("real-repo")` で 1 worker に直列固定される」と
  裁定に書いたが、`_real_output_snapshot()` を呼ぶ 10 本は **1 本も
  `REAL_REPO_ACCESS_BY_NODE` に登録されていなかった** (同 file からの登録は ccbench build canary
  3 本のみ)。よって対象は直列固定されず 48 worker へ散っており、費用モデルの前提が崩れた。
- 根本原因: 登録簿の存在と marker 付与の条件は読んだが、**対象 node が実際に登録簿にあるかを
  照合しなかった。** 「実 repo を読む = 登録されている」は成り立たない。
- 恒久対応: 直列性・排他を前提にした見積りを書く前に、対象 nodeid を登録簿へ
  **実際に照合する** (`REAL_REPO_ACCESS_BY_NODE` の keys との集合演算)。
- 再発検知: 本 wave の {{D:acceptance-floor-is-a-band-not-a-single-test}} が要求する
  「node → worker 割当」の実測が、この仮定の誤りを毎回顕在化させる。

### {{F:speed-fix-traded-detection-power-silently}}. 高速化がキャッシュ経由で検出力を静かに下げた [恒真ゲート]

- 事象: 実 repo `output/` snapshot を git 索引経由へ変える実装が、初版で 3 つの経路から
  検出力を落としていた。(1) `assume-unchanged` / `skip-worktree` が立った tracked file は
  `git status` が黙るためキャッシュから永久に見えない、(2) キャッシュのキーが blob sha だけで
  path を含まず、`.gitattributes` の変換で同じ blob が異なる working bytes を持つ場合に衝突する、
  (3) `git status -z` の末尾 NUL を検査せず、rc=0 のまま切れた出力を正常受理する。
  **返り値は実 repo で参照オラクルと完全一致していたため、等価性の実測だけでは 3 件とも見えなかった。**
- 根本原因: 「現に一致する」ことを「常に一致する」ことの証拠として扱った。
  キャッシュは、キーが同一性を保存する場合にだけ健全であり、その前提を検査していなかった。
- 恒久対応: {{D:git-index-output-snapshot}} が、索引と設定だけで判定する
  5 つのフォールバック条件を fail-closed で義務づける。加えて repo の大きさに依存しない
  性能モデルのテストを常設し、初回 digest 回数・2 回目 0 回・別プロセスでの再 miss・
  git 起動回数・5 種のフォールバック条件での挙動 (変更が検出されること) を固定する。
- 再発検知: 上記の性能モデルテストは、静かなフォールバック (速くなったつもり) と
  検出力の低下 (速さのための緩め) の両方を赤にする。
