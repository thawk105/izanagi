---
schema: izanagi-spool-v1
ledger: failures
authored: 2026-08-23
wave: dev-wave-launcher-budget-fixed-cost
seq: 3
---

## 新規

### {{F:guard-blind-to-subprocess-run}}. guard 拒否時に被験体が走る穴を、検査が構造的に見られていなかった [テスト代表性]

- 事象: `test_guard_bytes_mismatch_prevents_codex_popen` は guard bytes 不一致時に
  codex の起動が 0 件であることを検査していたが、`codex --version` が guard 検査より前に
  走っていた。被験体である caller 指定 codex が、guard に拒否される状況でも実行されていた。
- 根本原因: 検査が `subprocess.Popen` の spy で起動を数える一方、version は素の
  `subprocess.run` を使っていた。**検査の観測面に載らない経路で被験体が実行されていたため、
  穴が存在しても検査は緑を返し続けた。** 検査が弱かったのではなく、観測面が実装より狭かった。
- 顕在化の経路: 別の要求 (被験体を予算へ閉じ込めるため version を process group 起動へ変える)
  を満たした副作用として初めて赤くなった。**穴そのものは以前から存在した。**
- 恒久対応: {{D:launcher-three-interval-budget}} により guard 検査を version 取得より前へ移し、
  version を新規 session / process group で起動して残留子孫と終了を確認する。
  `orchestrator/tests/test_codex_worker_launch_budget.py::test_version_process_group_rejects_and_reaps_detached_child`
  が、version が子を fork して detach する負例を検出する。
- 再発検知: 変異 MUT-3 (version 所要を attempt でなく準備へ算入する) が 5 node で KILLED。
  被験体の実行を予算外へ逃がす変異が生き残らないことを実測で確認した。

### {{F:aggregate-smuggles-regime-term}}. 個別に排除した regime 固有の項が、集計値に埋め込まれて再侵入した [計測汚染]

- 事象: 親は「テストは偽 codex を使うので 240 MB hash はフレークの主要因でない」と訂正し、
  並行セッションへも明示的に伝えて同意を得た。その直後、**同じ hash を含む実走 1281 件の
  集計値 (準備 max 3.792 秒) を、偽 codex を使うテスト regime の予算 3 秒と直接比較する
  主張**が出た。個別事実としては排除できていたのに、それが埋め込まれた集計値の形で
  再侵入した。
- 根本原因: 「定性・構造の知見は環境を跨いで転移する」という一般則を、
  **何が転移して何が転移しないかを分けずに**適用した。集計値は構造ではない。
  分布のうち転移するのは裾の比 (max / p50) であって絶対値ではない。
- 恒久対応: 「tail 余裕」の記録書式を 5 項目とし、**regime を独立項目に昇格**させた
  (母集合 / **観測した regime が予算の適用対象と同じ regime か** / tail は max で見る /
  倍率は正例 2 倍以上 / 負例は逆で確実に発火する小さい値)。
  項目「母集合を書け」だけでは実際に止まらなかったため、
  「同じ regime か」を明示的な問いにした。memory `aggregates-smuggle-regime-specific-terms`。
- 再発検知: 記録に絶対値を書く場合は regime を同じ行に束ねる。束ねられない値は比で書く。

### {{F:single-layer-mutation-masked-by-second-gate}}. 単層だけの変異が第 2 層に mask され、注入実在でも SURVIVED した [恒真ゲート]

- 事象: 変異 probe で、準備 gate と最終化 gate をそれぞれ単層だけ恒偽にした MUT-1 / MUT-2 が
  `anchor_counts` 1・`injection_diff_sha256` あり (注入実在) にもかかわらず
  212 passed で SURVIVED した。とくに最終化は `_finalization_limit_reached` を丸ごと
  `False` にしても、**公開直前の別 gate** が発火して受理集合を守っていた。
- 根本原因: 親が変異を事前登録する際、gate が 2 層あることを確認していなかった。
  `DW-M01` は「同じ入力を拒否する層が前後に無いことをコードで確認する」ことを求めているが、
  親は 1 箇所を見つけた時点で登録した。
- 恒久対応: `DW-M02` に従い両層同時変異へ再照準し、probe 2 で観測 node を集めてから本走した。
  本走は baseline PASSED・MUT-1〜7 7/7 KILLED・SURVIVED 0・MISMATCH 0。
  probe 1 の結果は erratum として保全している
  (`dev-wave-jobs/dev-wave-launcher-budget-fixed-cost/mutation-probe-result-1.json`)。
- 再発検知: SURVIVED を equivalent と結論する前に、注入 diff の実在確認だけでなく
  **同じ入力を拒否する他層の全列挙**を行う。`DW-M04` の「注入なしを緑と報告しない」に
  「注入ありでも他層 mask を疑う」を対で運用する。
