---
schema: izanagi-spool-v1
ledger: worklog
authored: 2026-09-17
wave: dev-wave-t2647-fig8-readme-note
seq: 1
title: [T-2647] 本体論文の入口 README の stale 注記へ fig8 の成立を案内する 1 項を足し、「図は無い」の凍結記述は当時は真として残した — 下流 (results 稿・版・図・入口注記) が揃ったので [T-2647] を閉じる (docs のみ、branch worktree-dev-wave-t2647-fig8-readme-note、実装面ゼロ・変異 matrix 免除)
---

## 本文

- ユーザー依頼は「[T-2647] (P2、残件) `docs/paper-story/README.md` の『最新スナップショット以後に確定したこと』節へ、
  論文図 fig8 の成立を案内する 1 項を足す。版 2026-09-17.md §4 と results 稿 §3 限定 11 の『図は無い』は当時は真なので
  書き換えない (分類「当時は真、後続で古くなった記述」)。図の成立を性能認証・B-10 閉鎖・D2104 項 7 の再現 cohort
  解除に昇格させない。言い方は事前登録 §4.5 の固定表現に限る。着手直前の local main から fresh worktree を作る。
  docs のみ。規律 2 を緩めない。本題の案内追記だけ」。
- **閉じた。** 同節の項目数を 1 → 2 にし、既存の Silo 項の後へ fig8 の項を 1 つ足した。項は 4 要素 — (a) 事実
  (fig8 が 2026-09-17 に着地、実装 commit `4636181a9`・段 6 fix `ce39429d5`、3 成果物の着地 bytes の SHA-256、
  生成器、正本 = `figures/README.md` の fig8 節、記録 = `output/insights/2026-09-17/t2647-b10-tail-fig8/README.md`)、
  (b) 言い方 (事前登録 §4.5 の固定表現の逐語と禁止句)、(c) 図の成立で変わらないこと (`performance_certified: false`
  は不動・variant 採用の根拠にしない・B-10 も [T-2647] も閉じない・D2104 項 7 は解除されない — 同項は理由の一つに
  「結果を使う下流 (論文図) が未成立」を挙げるが決定は優先順位の判断で、D2120 項 16 (第 21 回裁定、本 wave の受入中に
  main へ着地) が「図の成立で理由の一部は変わったが主経路優先の理由が残るので保留を維持、図の成立は追加測定の必要性を
  示さない」と裁定した。走らせるなら D2050 の地位明記を満たす別 wave を新規に起票する・当時の実行全体の独立監査は
  未実施)、(d) 古くなった記述の所在 (版 §4 の表の「(未作成)」、
  同趣旨の「図は無い (§4)」は §0 前進 2 と §8 B-10、「未作成の予定仕様」は §10 段 3、results 稿 §0.3 と §3 限定 11。
  いずれも凍結物で書き換えない。同節の移管先 3 の「§4 (図は無い)」も版の内容説明として正しく変えない)。
- **F756 (注記自身が腐る) への対処として、項に base を紐づけた** — 着地 commit 2 本と PNG / PDF / provenance JSON の
  SHA-256 先頭 8 桁。後続 wave が同主題を進めるとき、この項の真偽を bytes で照合できる。
- **[T-2647] を閉じる判断は本 wave の裁定。** 原定義 (1512) は「否定的結論をどの図表・主張へ載せるかは未定」であり、
  下流は results 稿 (1563)・版 2026-09-17 (取り込み済み)・論文図 fig8 (1609)・両論文系列の入口注記 (1549 と本 wave) で
  揃った。1609-1610 版の定義が「残るのは」と名指した README の案内は本 wave が消化した。**この閉鎖は task の終端で
  あって、B-10 の完了・性能認証・D2104 項 7 の解除・同じ事前登録に対する第 2 cohort (T-2678、D2050) の地位のどれも
  意味しない** — 本 wave が README に書いた「変わらないこと」と同じである。
- 段構成は既定の軽量版・codex 子ゼロ (docs-only、設計択一なし・正しさ防壁に触れず・受理集合を変えない)。段 2・3・6 を
  省き、段 1 brief と段 4 裁定は job dir (`/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2647-fig8-readme-note/`) の
  `brief.md` / `handoff.md`。裁定 inbox 再走査: main 不動 (`38353207f`)、未 fold fragment に本題の裁定なし。
- 実測: 編集面重複ゼロ — 152 worktree の `docs/paper-story/README.md` の blob id は全て同 path の履歴上の版 (43 版) と
  一致 (未 commit 編集 0)、main 未着地の非 merge commit 0。README は check_docs の LIVING_DOCS 対象外で、whole-file を
  pin する test は 0 件 (DW-O08〜O10 不成立)。fig8 の provenance `outputs[].sha256` と実 file の一致を確認した。
- 起動: `EnterWorktree(name)` が「Could not read the repository git config」で失敗 → 手動 `git worktree add`
  (timeout 600 秒、殺さず完走) → `EnterWorktree(path)` → `dev_wave_submodule_init.py` rc=0 で 3 段とも初期化
  (`git submodule status --recursive` に `-` 接頭辞なし)。開始 gate fresh rc=0。
- 検査: `python3 tools/check_docs.py` 違反なし、`git diff --check` rc=0。受入全走は記録 commit を含む tip に対し
  land 前に投入し、child-green でなければ land しない (結果は land の受領証)。**final-1 は非帰属の赤 (rc=70)** — 14 件
  すべて setup の `subprocess.TimeoutExpired` (`git ls-files --others` 30 秒 × 10 = F945 型、`git archive` × 4 = 同根の
  共有 FS 飽和) で、赤の 2 file の焦点走は 269 passed (非再現)。fold と D2120 の 2 commit だけ進んだ main を固定 SHA で
  取り込み、D2120 項 16 の引用を同じ tip で注記に足してから投げ直した。
- 工数: codex 子 0 本。親の実測は blob 照合 1 走・check_docs 3 走・焦点走 1 走 (非再現確認)。

## 次の一手差分

### 完了

- [T-2647] 静的 backoff 右 tail 本走の判定を下流へ渡す — results 稿 (1563)・版 2026-09-17・論文図 fig8 (1609)・
  両論文系列の入口注記 (1549 と本 wave の README fig8 案内) が揃い、1609-1610 版が名指した最後の残件を消化した。
  言い方は事前登録 §4.5 の固定表現に限り、`performance_certified: false` は不動。B-10 の完了・性能認証・
  D2104 項 7 の解除 (D2120 項 16 が保留維持を裁定)・第 2 cohort (T-2678) の地位は本閉鎖と無関係である。
  remaining: none
  base: b30263c65549c2fb672f988c5215fcb84aaaf493191b34fec0359fa47aed1e95
