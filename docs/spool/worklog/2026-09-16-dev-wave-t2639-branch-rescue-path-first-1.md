---
schema: izanagi-spool-v1
ledger: worklog
authored: 2026-09-16
wave: dev-wave-t2639-branch-rescue-path-first
seq: 1
title: [T-2639] 救出検査の候補走査を一括化し spool の証明と未証明理由の伝達を足したが、受入全走が 10 走とも非帰属の赤で land できなかった (コード + テスト + docs、branch worktree-dev-wave-t2639-branch-rescue-path-first、変異 matrix = baseline 緑・11/11 KILLED・SURVIVED 0・MISMATCH 0・期待 node 完全一致)
---

## 本文

- 一次資料は `output/insights/2026-09-16_t2639-branch-rescue-path-first/`。子の逐語 12 本、
  変異 spec / 結果 3 本を置いた。実装 commit は `99125e783` (4 file、686 挿入 / 10 削除)。
- **依頼の前提 1 件が一次資料と食い違った。** 依頼は「対象 3 commit のうち 1 件が
  assessment-timeout」と書いたが、`docs/archive/worklog-phase3-0915-1506.md` は
  「削除で最後の根を失う **4 commit**、`not_landed=0`、**3 件を indeterminate のまま**」である。
  所要 114 秒 → 644 秒は一致した。一次資料を採った。
- **依頼が指した 4 commit の OID は回収できなかった。** 当該 `/cleanup-branches` 実行は docs のみで
  insight dir を残さず、worklog にも OID が無く、`docs/unreachable-object-ledger.md` は entry 0 件
  である。受入判定は再現可能な固定 corpus (2 branch の固定 OID と spool の正例・負例) に置き換えた。
- **親 brief の誤りを子とレビューが 5 件突いた。全件採用した。** M3 が blob 一致しか測っておらず
  四要素の正例実測として不足、121 倍は候補参照だけの局所比 (端から端では実測 2.3 倍)、symlink の
  object type は blob で通常ファイルとの差は mode、「rc=2 が削除 gate を止める」は
  `/cleanup-branches` §2 が rc を使わない事実と矛盾、「18 件取りこぼす」は「18 種類の状態」であって
  merge commit 18 個ではない。
- **段 6 レビューが scope を 1 つ増やさせた。** `check_branch_rescue.py` は子が出した unit ごとの
  証拠を捨て、集約理由と `report_sha256` しか返していなかった。hash から説明は復元できないので、
  速くしても spool を解決しても「何がなぜ未証明か」が人に届かない。未証明 unit の理由を運ぶ
  ({{D:rescue-carries-unproven-unit-reasons}})。判定・rc・完全性の値は 1 bit も変えていない。
- **fix は 3 巡かかった。** 1 巡目は「既存テストの期待値と衝突する」と報告して**正しく停止**した。
  衝突相手は本 wave が段 5 で足した自分のテストであり、`git show main:` で main に 0 件だと実測して
  射程を裁定し直した。2 巡目の到達証明 assert が payload の構造を推測で書いて赤になり、親が実構造を
  測って prompt へ貼り (`DW-O16`)、3 巡目で閉じた。
- **受入全走が 10 走とも赤で、receipt を 1 度も取れなかった。** 通過は毎回 23832〜23949、赤は
  1〜8 件で毎回顔ぶれが変わる。赤になった 9 種の test はいずれも本 wave が変更した
  `tools/check_branch_landed.py` / `tools/check_branch_rescue.py` を **0 回**参照し、単独再走は
  すべて緑だった。親の worktree は全走の前後とも status 0 行。機序は F300 に記録済みで、同日に
  別 wave が同機序で 5 走赤・6 走目で緑になっている。本 wave はその独立 2 例目である。
- **hold 登録を試みて撤回した。** `DW-O18` の手順どおり F300 を証拠に 4 node を登録し、登録簿自身の
  validator は通ったが、`test_flaky_test_holds_contract.py` が登録簿をちょうど 1 件・証拠 F57・
  再導入タスク t-1079・sha256 まで逐語で固定しているため赤になった。**この pin は wave が自分を
  緑にするために除外集合を広げることを防ぐ防壁である。** pin を書き換える側が誤りと裁定し撤回した。
  手順と契約テストの衝突は {{F:flaky-hold-registry-pinned-to-one}} として起票した。
- **land は行っていない。** 受入 receipt が無い以上 `tools/dev_wave_land.py` は main を 1 bit も
  進めない。迂回もしていない。branch は検証済みのまま残してある。
- 工数: codex 子 10 本 (plan 1・consult 2・author 2・review 2・fix 3、いずれも `gpt-6-astra` /
  `reasoning=medium`)。計算ノード job は焦点走 5 回、変異 24 回 (probe 12 + 本走 12)、受入 10 回。

## 次の一手差分

### 完了

- [T-2639] 候補走査の tagged batch 化 ({{D:spool-exact-state-positive-fallback}} と
  {{D:rescue-carries-unproven-unit-reasons}}) を実装し、変異 matrix と焦点走で検証した。
  固定 OID で子 process 2005 → 92 / 1190 → 244、所要 26.55 → 11.35 / 51.29 → 32.77 秒、
  判定と unit の理由内訳は完全一致。掃除コマンドの既定予算では判定不能 7 件の内訳が
  「時間切れ 7」から「実質的な理由 4 + 時間切れ 3」へ変わった。**rc は 2 のままである**
  (D1231 が「indeterminate があっても rc=0」を却下しているため、これは仕様どおり)。
  remaining: none
  base: ff164af55ea5ca140602b922bb68937e28c134a90b5aa377232ba0838d7b204b

### 新規

- {{T:branch-rescue-closure-enumeration-cost}} **P2・新規**: 救出検査の次の律速は closure 列挙と
  `_introduced_states` の per-parent diff である。固定 OID `559bcbc29c…` の改修後 32.77 秒のうち
  exact-tree-state は 15.67 秒、any-path 0.48 秒、ledger_corpus 0.27 秒、task_index 0.0 秒、
  verbatim 0 秒で、**残り約 16 秒がここ**にある。掃除コマンドの既定予算 (8 秒) で残る 3 件の
  `checker-timeout` はこれが原因。
- {{T:d922-truncation-positive-priority-ruling}} **P1・ユーザー裁定待ち**: 候補上限超過時に正例を
  優先して `landed` を返す現行実装と、D922 点 4 の逐語「打ち切りはすべて `indeterminate` へ倒す」が
  食い違う。D922 を書いた wave 自身が
  `test_history_match_at_candidate_33_wins_before_65_plus_truncation` で現行挙動を逐語固定している。
  どちらを正とするか。
- {{T:rescue-rc2-definition-conflict}} **P1・ユーザー裁定待ち**: `docs/unreachable-object-ledger.md`
  の rc 表は rc=2 を「timeout、上限超過、root 移動、期限算出不能、台帳 parse 不能などで技術的に
  不完全」と定義し **`indeterminate` verdict を挙げていない**。一方 D1231 の却下項は
  「`indeterminate` があっても rc=0」を却下している。実装は後者に従う。正本どうしの読みが割れている。
- {{T:main-side-revision-evidence-ruling}} **P1・ユーザー裁定待ち**: 「main 側が後から改版したので
  内容の喪失はない」という人手の判断を機械化するには、exact 証拠が無いケースに何を認めるかを
  決める必要がある。D922 の決定的証拠 (a)(b) の枠内では判定できない。証拠契約の変更である。
- {{T:spool-deletion-exact-proof-target}} **P2・新規**: 削除 spool fragment の exact 証明対象を
  required の不在と old blob の過去存在のどちらにするか。前者は main tip の不在だけで受理でき、
  後者は分岐前の共通履歴だけで成功しうる。
- {{T:rescue-child-deadline-headroom}} **P2・新規**: rescue の子 deadline と外側 subprocess timeout が
  同値で、Python 起動・JSON 出力の時間差により子の理由 JSON より先に親が kill しうる。
- {{T:flaky-hold-procedure-vs-contract-ruling}} **P1・ユーザー裁定待ち**: `DW-O18` の hold 登録手順と
  `test_flaky_test_holds_contract.py` の「登録簿はちょうど 1 件」pin が正面から衝突する
  ({{F:flaky-hold-registry-pinned-to-one}})。手順に従うと契約テストが赤くなり、契約テストを守ると
  手順を使えない。どちらも main に在り、どちらも自分の側では正しい。
- {{T:t2639-branch-land-blocked}} **P1・ユーザー裁定待ち**: 本 wave の branch
  `worktree-dev-wave-t2639-branch-rescue-path-first` (実装 commit `99125e783`) は検証を終えているが、
  受入全走が 10 走とも非帰属の赤で receipt を取れず land できていない。F300 の恒久対応が決まるまで
  同じ壁に当たる wave が続く。
