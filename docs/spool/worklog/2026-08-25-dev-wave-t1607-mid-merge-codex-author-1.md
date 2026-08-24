---
schema: izanagi-spool-v1
ledger: worklog
authored: 2026-08-25
wave: dev-wave-t1607-mid-merge-codex-author
seq: 1
title: [T-1607] mid-merge の作業木を Codex role=author へ委任できるようにした (コード + テスト、branch worktree-dev-wave-t1607-mid-merge-codex-author、変異 matrix = baseline PASSED・登録 13/一致 13・MISMATCH 0・KILLED 12・SURVIVED 1)
---

## 本文

- **起票文の因果が誤りだったので、brief の前に実測して訂正した。** 起票文と台帳 note は
  「authority-snapshot 検査が mid-merge・conflict マーカーありの working tree を拒否する」と
  述べるが、実装に mid-merge も conflict マーカーも判定材料として存在しない。独立 clone での
  5 ケース実測で、拒否述語は「live 呼出しで authority docs 2 file の working bytes が HEAD blob と
  一致すること」だけだと確定した。**authority docs を誰も触っていない mid-merge は fix 前から
  通っていた**し、競合なく自動 merge されただけでも落ちていた。
- 台帳件数も訂正した。起票文の「11 件」に対し、note に `親作成 merge のため Codex 著者とは
  記さない` を持つ entry は実測 7 件 (`KNOWN_PROVENANCE_VIOLATIONS` を実 import して計数、全体 53 件)。
- 設計は {{D:mid-merge-author-capability}} に記録した。**受理集合を実際に狭めるのは path 方向の
  条件ではなく stage 方向の限定である**、というのが本 wave の中心的な発見である。親は当初
  「merge の変更集合に入っている path だけ差異を許す」対案を立てたが、段 3 レンズ A の指摘を
  実測で裏取りして**取り下げた** — wave 側だけが変更した file でも条件が真になり、incoming が
  無変更でも手編集を素通しする (HEAD `f86b8e88` / MERGE_HEAD `d71b8c26` / merge base `d71b8c26`)。
- **段 2 が提案した negative control 5 本は全て差し替えた。** 段 3 レンズ A が「5 本とも
  無条件 skip 実装のまま緑になる」と指摘し、親が裁定で N1〜N8 を新規登録した。要石は
  `test_non_author_stage_in_mid_merge_is_rejected` で、変異 M4 (capability を無視する誤実装) を
  この 1 本ちょうどで殺す。
- **本 wave では目的を完全には閉じられない。** 段 3 レンズ B が第 2 の HEAD-byte gate を発見した。
  `tools/check_codex_hooks.py` の `_validate_pinned_guard_bytes` が guard 5 file と
  `.codex/hooks.json` を HEAD blob と比較しており、これらに触れる取り込みでは本 wave の修正後も
  委任できない。**段 1 brief の「launcher 側に他の clean-tree gate は無い」は誤りであり撤回する**
  (grep を `codex_worker_launch.py` 内に限ったため別 module の gate を見落とした)。
  残余を実測した: 2026-08-01 以降の main 4991 commit のうち authority docs を触るのは 83 件、
  guard 5 file + `.codex/hooks.json` を触るのは 30 件。前者を閉じ後者は残る。
  この gate は guard 自体の byte 同一性を守る正しさ防壁なので緩めない。
- 段 6 レビュー 2 本の裁定: must-fix 5 件を採用 (判定を loop 前へ、原子的 no-follow、サイズ上限、
  replacement object 無効化、実在する非 commit OID の検出テスト追加)。
  **RA2 (大文字 hex40 を受理しないのは裁定より狭い) は不採用**とした — 受理集合を広げる方向であり、
  Git は `MERGE_HEAD` へ lowercase しか書かない。裁定側を lowercase hex40 と明確化した。
- **変異 M11 (サイズ上限の除去) は生存した。** 読取り後に同一の上限検査がもう 1 つあり、
  前段を消しても後段が拾う mask である。両層同時変異 M11b で裏取りしたところ赤くなったが、
  赤の中身は**受理集合の変化ではない** — 上限を両方外しても切り詰めた内容は形式検査で拒否され、
  変わるのは例外メッセージだけだった。診断文字列だけの赤は kill に数えないため、
  サイズ上限は受理集合を変えない資源ガードと結論し、diagnostic sensitivity pin として別枠記録する。
  `test_merge_head_over_size_limit_is_rejected` は過剰決定である。
- 親の end-to-end 実測: wave branch の独立 clone で実際に競合マーカーの残る mid-merge を作り、
  `allow_mid_merge=False` は従来どおり拒否、`True` は受理して `authority_commit` が HEAD
  (`756c56e7`)、model / effort も HEAD 由来であることを確認した。
- 実装子と fix 子はいずれも計算ノード dispatch が `qstat -Q rc=1` で止まり、pytest を 1 本も
  実走できなかった。両者ともその事実を「実装済み・未実走」と正直に報告し、実走は親が代替した
  (2 file 合計 266 passed rc=0)。
- 段 3 レンズ A の A7 (rebase-merges / `git am` / `stash apply` へ緩和が漏れる) は実測で反証した。
  いずれも競合しても `MERGE_HEAD` を作らない。副産物として、stash 競合は `MERGE_HEAD` 無しで
  未解決 index を残すため、`git ls-files -u` を sentinel にする案が不適である追加根拠も得た。
- 本 wave 自身の作法の欠落を 1 件記録した (F37 の再発)。

## 次の一手差分

### 完了

- [T-1607] mid-merge の作業木を Codex `role=author` へ委任する正規経路を実装した。
  {{D:mid-merge-author-capability}} を採用し、negative control 8 本と変異 13 件を登録して
  matrix を完全一致で通した。第 2 の HEAD-byte gate に由来する残余は下記の新規項へ分離した。
  remaining: none
  base: 90f249a359cd651db60905776288514333ed978aab73a078845b8a05a1867ced

### 新規

- {{T:pinned-guard-mid-merge}} **P2・ユーザー裁定待ち**: `tools/check_codex_hooks.py` の
  pinned guard byte gate は、guard 5 file と `.codex/hooks.json` に触れる main 取り込みでは
  mid-merge 委任を引き続き拒否する。実測で 2026-08-01 以降 30 commit が該当する。
  緩めずに閉じるには「working guard を信用せず HEAD-pinned guard を実行する」別設計が要る。
  別 wave を起こすか fail-closed のまま運用するかを裁定する。
- {{T:frozen-authority-projection}} **P2・新規**: 子が読む規範は working tree であり凍結されていない。
  authority docs 2 file の 4 節だけが全文比較されており、merge 中はその比較も外れる。
  HEAD blob から作った凍結規範を子の governing input にし、working docs を編集対象データとして
  分離する設計を検討する。
- {{T:snapshot-spawn-toctou}} **P3・新規**: snapshot 取得から子の spawn までの間に authority docs を
  書き換えられる窓が残る (現行でも同じ窓がある)。凍結入力設計で同時に閉じる候補。
- {{T:launch-admission-provenance}} **P3・新規**: receipt は HEAD snapshot しか持たないため、
  後日「どの merge admission で通ったか」を再検証できない。記録には receipt schema の世代を
  上げるか closed な sidecar が要り、現行の shape / digest pin と衝突する。
