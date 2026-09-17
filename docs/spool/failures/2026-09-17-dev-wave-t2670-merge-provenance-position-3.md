---
schema: izanagi-spool-v1
ledger: failures
authored: 2026-09-17
wave: dev-wave-t2670-merge-provenance-position
seq: 3
---

## 新規

### {{F:merge-audit-before-commit-saw-nothing-new}}. 受入前 merge 段の全史監査が `--no-commit` 中の HEAD に対して走り、取り込んだ main の commit を一度も見ていなかった [恒真ゲート] [テスト代表性]

- 事象: `tools/dev_wave_wait.py acceptance` の受入前 merge 段は、`git merge --no-ff --no-commit main` の
  直後・`git commit` の前に全史 provenance 監査 (`merge-history-provenance`) を走らせていた。
  この時点の HEAD は wave tip のままなので、checker の既定監査 (`{policy} ∪ rev-list(policy..HEAD)`)
  の選択集合は claim 前の監査 (`preclaim-history-provenance`) と同一で、取り込んだ main の commit と
  merge commit 自身は入らない。F365 の恒久対応が「その merge 自身が新しく作る違反を捕まえる」と
  書いた監査は、導入以来その違反を一度も見ていなかった。main にだけ存在する違反 commit は受入全走
  (1 万件超) を消費した後、land の監査で初めて赤になる。
- 根本原因: 監査の位置を「merge 後」と呼び、checker が HEAD を pin する事実 (`_resolve_head`) と
  `--no-commit` が HEAD を動かさない事実を突き合わせなかった。既存 test は段の順序 (`_STAGES`) を
  `_FakeEffects` の期待列で pin していたが、監査が「取り込んだ commit を見る」ことは主張しておらず、
  位置の誤りを緑のまま通した。旧位置の監査は claim 前の監査と入力が同じで、差分 0 件の冗長呼び出し
  として費用だけ消えていた ([T-2670] が起票、D2044 項 5 が裁定)。
- 恒久対応: {{D:merge-history-provenance-after-commit}} — 監査を `git commit` 後 (HEAD の pin 取得直後)
  へ移し、赤でも merge commit を保持して所有 lease を解放し受入 command を投入しない契約に定めた。
  実 git の負例 `test_real_git_main_only_history_violation_blocks_acceptance_after_commit`
  (`orchestrator/tests/test_dev_wave_wait.py`) が、main にだけ存在する違反 commit を temp repo の
  偽 checker (`git merge-base --is-ancestor <sha> HEAD`) で赤にし、受入 command 0 回・lease の
  監査時存在と終了時不在・HEAD が 2 親 merge commit・違反 SHA の到達性を主張する。
- 再発検知: 同 test が「監査を commit 前へ戻す」変異 (M1) を runner 計数の主張で殺す
  (変異台帳は本 wave の insight)。fake の順序 pin だけでは検出しない。

## 再発

### F511

- **再発: 2026-09-17** — [T-2670] wave の親が D2044 項 5 の逐語を `awk '/^### 項 5 /...'` で切ったが、anchor を
  `## D2044` の範囲に限定せず file 先頭から当てたため、別の D の「項 5」(A-1 の本番測定の認可) を plan 子の必読資料として
  渡した。plan 子が現物と突き合わせて「逐語が本件に一致しない」と報告し、段 3 前に親が D2044 の範囲内で切り直した
  (near miss、実害なし。brief 本文に裁定の要旨があったため plan の実質は保たれた)。行範囲の代わりに見出し anchor を
  使っても、**上位見出しの範囲で絞らなければ同型がずれる**。切った直後の先頭見出しの目視で防げた。

### F1

- **再発: 2026-09-17 (near miss)** — [T-2670] wave の親が段 4 / 段 6 の裁定 file の見出し時刻を推定で書いた
  (段 4 を「22:10」、段 6 を「23:10」と書いたが、子の pid file の mtime と実装 commit の時刻から 21:52 頃 / 22:17 頃だった)。
  insight の verbatim へ写した後に `date` で気づき、実測値へ訂正して commit 前に閉じた。時刻も日付と同じく一次資料
  (file の mtime・commit 時刻) から取る。

## supersede 追記

- F206 **supersede: 2026-09-17** — 再発 2026-09-01 の型 (受入待ち手の `merge-history-provenance` 段が main 側の既知違反 entry 追加を `index-only member does not match HEAD` で実行不能にする) は、{{D:merge-history-provenance-after-commit}} で監査が `git commit` 後へ移り merge commit に entry が入るため起きなくなった (親の実 checker probe で旧位置 rc=2 → 新位置 rc=0 を実測)。`--ff-only` で揃える復旧手順は不要になり、台帳の内容規則と append-only 履歴検査はそのまま新位置で適用される。
- F365 **supersede: 2026-09-17** — 「merge 後・受入投入前」の全史監査は {{D:merge-history-provenance-after-commit}} で `git commit` 後 (HEAD = merge commit) へ移り、取り込んだ main の commit と merge commit 自身を選択集合に含める。この段の赤では `git merge --abort` を行わず merge commit を保持し、所有 lease の解放と受入 command 不投入だけを行う ({{F:merge-audit-before-commit-saw-nothing-new}})。
