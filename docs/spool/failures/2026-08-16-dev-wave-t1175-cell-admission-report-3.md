---
schema: izanagi-spool-v1
ledger: failures
authored: 2026-08-16
wave: dev-wave-t1175-cell-admission-report
seq: 3
---

## 新規

### {{F:fabricated-task-notification}}. 背景 task の「完了」通知が producer 稼働中に発火し続けた [誤前提] [手順漏れ]

- 事象: 2026-08-16 の 1 セッション中に、背景 job の完了通知が **6 回以上**、
  対象が走行中のまま `status=completed / exit code 0` で届いた。出力は毎回空だった。
  具体例は 15:03 (待ち手、producer pid 2946493 が生存)、15:29 (待ち手、pid 3399788 が 47 秒経過で生存)、
  15:36 (テスト走行、計算ノードの job が RUN 中)、16:12〜16:14 (変異 matrix、`.done` 不在で
  記録済み変異 1/10)。形態は `dev_wave_wait.py` の待ち手、素の `until` ループ、`Monitor` の
  poll ループのいずれでも起きた。
- 根本原因: 通知そのものが producer の実状態と対応していない。
  **決定的な反証:** `tools/dev_wave_wait.py` の `wait_for_producer` は
  `done_file` と `artifact_file` の**両方が実在**するまで `RC_OK` を返さない構造である
  (producer 死亡後の grace loop で両ファイルを確認してから `_Outcome(RC_OK)`)。
  したがって「成果物ゼロで rc=0」は待ち手の返り値ではありえない。
  最初に立てた「rc を `| tail -N` へ通したため rc が消えた」という仮説は、
  パイプを外した 2 例目で同じ症状が出たことにより**反証された**。
- 波及の広さ: 通知を完了判定に使うと、走行中の成果物を「不在」と誤認して次段へ進むか、
  producer を二重投入する。本セッションでは待ち手を 2 度張り直し、
  変異 matrix でも 3 度空振りした。
- 恒久対応: 追加の機構は作らない。`docs/dev-wave/operations.md` の `DW-O01` が既に
  「完了は `.done` と exit code だけで判定し、grep も通知も判定にしない (通知は先行しうる)」と
  定めており、**正本は既に正しい。親の適用漏れである。**
  本エントリは同規則の実証記録として残す。
- 再発検知: 3 点照合 (成果物実在 + `.done` + producer 死) を通知のたびに行う。
  本セッションでは全件この照合で誤進行を防いだ。

### {{F:provenance-trailer-from-environment-default}}. 環境の既定 commit trailer 文言をそのまま使い provenance 規約に違反した [手順漏れ]

- 事象: 2026-08-16 14:40、wave branch へ local main を取り込む merge commit を作る際、
  trailer を `AI-Agent: claude-opus-5[1m] (Claude Code)` と書いた。
  `tools/check_ai_provenance.py` が新規違反 1 件として検出した
  (`AI-Agent の形式違反: product/model/reasoning/role の順と許可値を確認する`)。
- 根本原因: セッション環境の既定 commit 文言 (`Co-Authored-By` 形式) を trailer へ流用した。
  本 repo の規約は `product=<p>; model=<m>; reasoning=<r>; role=<role>[; scope=<s>]` の
  構造化 1 行を要求し、値は `[a-z0-9][a-z0-9._-]*` に収め、
  表示値は小文字化して非適合文字を `-` へ畳む (`claude-opus-5[1m]` → `claude-opus-5-1m`)。
- 波及の広さ: `AI-Agent-Correction` の forward correction 枠は既に消費済みで、
  新しい担い手を追加してはならないため、**訂正 commit で相殺できない**。
- 恒久対応: 未 land の wave branch だったので、branch を local main から作り直し、
  実装を線形に載せ直して欠陥 commit を除去した (検査の迂回ではなく原因の除去)。
  land 済み履歴で同じことが起きた場合は既知違反登録かユーザー裁定になる。
- 再発検知: commit 直後の `python3 tools/check_ai_provenance.py` を rc で判定する
  (パイプへ通さない)。本件はこの手順で land 前に検出できた。
