---
schema: izanagi-spool-v1
ledger: worklog
authored: 2026-08-26
wave: dev-wave-t1176-t1230-role-diagnosability
seq: 1
title: [T-1230] role 失敗の一次資料を report から指せるようにし、失敗を機械可読に分類した。[T-1176] の再試行は正しさゲートを緩めるため見送った (コード + テスト、branch worktree-dev-wave-t1176-t1230-role-diagnosability)
---

## 本文

- ユーザー指定の 3 件のうち **[T-1254] は既に閉じていた。** commit 5052e579 ([T-1229]) が
  `KeyError: 'build_start'` を構造化例外へ置換済みで、中断理由・利用可能 stage・abort
  レコードの reason / error / build_attempt_id が上へ返る。次の一手に残っていたのは
  stale carry-forward だった。
- **[T-1230] の defect は台帳の記述より広かった。** 台帳は「payload/envelope の path と hash は
  入るが raw が入らない」と書いていたが、実走すると `error_artifacts` は**空**だった。
  payload/envelope 枝は provider が artifact_root を持つ場合だけ発火するため、
  fixture 経路では 1 件も入らない。壊れた JSON が raw/ にそのまま残っていることも実物で確認した。
- **[T-1176] の再試行は実装しないと裁定した** ({{D:role-retry-deferred}})。ユーザー指示は
  「正しさゲートを緩めない範囲に限る」という条件付きであり、段 3 の敵対相談 2 本が独立に
  条件を満たせないと示した。最も重いのは、失敗 attempt を journal に残すと journal と report の
  1 対 1 対応が壊れ、最終 attempt だけを report へ置く形に変えると**非終端 attempt の
  payload validation receipt・provider artifact の bytes 検査・session isolation 証拠が
  検査対象から落ちる**ことである。certified 成果物の証明鎖に穴が開く。
  加えて再試行の効果が未測定である (実提供者の試行間独立性はコードにも実測にも無く、
  既存の実提供者 test はすべて 1 回しか invoke していない)。
- **段 3 の敵対相談が親の素朴な gate 案を恒真だと示した。** 「生応答が実在するのに pointer が
  無い event を拒否する」は、生応答を削除して `error_artifacts` を空にすると条件の両辺が
  偽になり検査へ入らない。構造化した `failure_phase` で「生応答が期待される段階か」を
  pin して初めて発火する ({{D:role-invalid-failure-phase}})。
- **段 6 の敵対レビュー 2 本が、塞いだつもりの穴が形を変えて残っていることを独立に示した。**
  値が空から `{"failure_phase": "pre-raw-write"}` に変わっただけで論理的には同じ欠落が残る。
  さらに (a) 参照先が run の権威 root に束縛されず無関係な file を指せる、
  (b) `lstat` と `read_bytes` が別の path 解決なので同じ bytes の symlink へ差し替えると
  通る、という 2 件も出た。3 件とも採用して修正した。
- **親の裁定の誤りを 1 件撤回した。** 段 4 で「この分類記録が再試行の是非を実測で裁定
  できるようにする」と書いたが、段 6 のレビューが正しく指摘したとおり得られるのは
  **失敗分類ごとの発生率**であって**救済率**ではない。発生率は必要条件だが十分ではない。
  救済率は実提供者を複数回叩く実験でしか得られない。
- **変異検査が、静的レビュー 2 本が両方見落とした検出力の穴を 2 件見つけた。**
  (1) file descriptor 経由の通常 file 検査を無効化しても既存のどのテストも赤にならなかった。
  symlink は別の負例が覆っていたが、symlink 以外の非通常 file を置く負例が無かった。
  負例を 1 件足した。(2) attempt の値 pin を 1 か所外しても、もう 1 か所の同じ pin が
  mask するため検出されなかった。実装の欠陥ではなく変異の狙いが実効 gate に
  当たっていないケースなので、両層同時変異へ狙い直して検出を確認した。
- **既存成果物への影響は実測で 0 件。** 受理集合を狭めたが、走査した journal 5 件に
  invalid role event は 0 件、trial report は 0 件だった。schema bump と移行は不要と裁定した。
- **段 2 が 6 回連続で失敗し、完成済み成果物 6 本と約 2 時間を失った。**
  F217 の再発だが今回は根本原因を特定した ({{F:codex-event-split-by-line-separator}})。
  起動側が子の stdout を `str.splitlines()` で分割しており、これは U+2028 / U+2029 でも
  分割する。この 2 文字は JSON 文字列内では正当な文字なので raw のまま出力される。
  リテラルで含む tracked file は repo 全体で 2 つあり、**どちらも本 wave の主編集面**
  だった。全 wave の invalid 率が 1142 attempt 中 25 件 (2%) なのに本 wave が 6/6 で
  失敗した理由である。該当行を無害化した写しを渡す回避で 7 回目に通った。
- **`--max-attempts` を上げる回避は逆効果だった。** 最終 attempt が accepted でも、
  それ以前に 1 つでも evidence 不備があれば job 全体が不採用になる。
  実測で attempt 3 が accepted かつ complete だったが job は不採用だった。3 倍の資源を
  使って同じ結果に着地した。既定の 1 のままが正しい。
- **変異走行に wave 自身の worktree を渡して rc=125 で止まった** ({{F:mutation-shared-tree-source-repo}})。
  投入直後に失敗していたが親が完了通知を待っており、約 4 時間の空転を招いた。
  ユーザーの指摘で気づいた。独立 clone を渡して解決した。
- 子は段 5・段 6 の全単位で pytest を 1 度も実走できなかった
  (`qstat -Q preflight rc=1`、計算ノードの socket 失敗)。
  **本 wave のテスト結果はすべて親の実測である。**

## 次の一手差分

### 完了

- [T-1230] invalid role event に `failure_phase` と生応答 pointer を必須化し、
  pointer を run の権威 root と invocation id から導出した期待 path へ束縛した。
  読取りは同一 file descriptor で行い差し替えを拒否する。
  remaining: none
  base: 055557b16858b0e5f620b2559352d1f9cd94b815c542ece57f85e6765b351c7f

- [T-1254] commit 5052e579 ([T-1229]) で既に閉じていることを確認した。
  本 wave の実装対象から外した。
  remaining: none
  base: a6060131295402d0219bc59ca3efa6a76da4be4d27a2aecfe75b83b7acff3321

### 更新

- [T-1176] **P2・ユーザー裁定待ち**: role 応答の JSON parse 失敗への再試行。
  段 3 の敵対相談 2 本が、素朴な実装は既存の正しさゲートを 4 系統で緩めると独立に示した。
  効果も未測定である。本 wave では実装せず、入れる場合の必須条件 10 件を
  {{D:role-retry-deferred}} に列挙した。先に取るべき実測は実提供者の試行間独立性である。
  base: b21085c79c2152276bfe995f934199773c95836e70eabf2075eaf26a91aabcab

### 新規

- {{T:launcher-splitlines-line-separator}} **P1・新規**: codex 子の成果物が
  U+2028 / U+2029 で全損する問題を恒久的に断つ。
  `orchestrator/codex_roles/events.py` の `parse_jsonl` が `str.splitlines()` を使っており、
  これは改行に加えて U+2028 / U+2029 でも分割する。この 2 文字は JSON 文字列内では
  escape 不要の正当な文字なので、子が該当文字を含む file を読むだけで
  **完成した成果物ごと破棄される**。`text.split("\n")` へ変えれば構造的に断てる。
  U+2028 / U+2029 を含む event 行を受理する負例テストを同時に足す。
  根本原因の実測は {{F:codex-event-split-by-line-separator}}。実装面のため Codex author が要る。

- {{T:mutation-source-repo-doc}} **P2・新規**: `DW-M05` へ
  「`tools/mutation_worktree.py --source-repo` には固定 commit の独立 clone を渡す」を足す。
  wave 自身の worktree を渡すと走行中に共有木の観測 bytes が変化して rc=125 で中止する。
  実測は {{F:mutation-shared-tree-source-repo}}。

- {{T:role-failure-phase-incidence}} **P2・新規**: {{D:role-invalid-failure-phase}} が
  記録するようになった `failure_phase` を実運用の journal から集計し、
  role / provider ごとの JSON 構文失敗の発生率を出す。
  これは {{D:role-retry-deferred}} が再試行の裁定に要求する 2 つの実測のうち 1 つである。
  もう 1 つ (救済率) は実提供者を同一 payload で複数回叩く実験が要り、別途起票する。
