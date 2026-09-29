---
schema: izanagi-spool-v1
ledger: worklog
authored: 2026-09-29
wave: dev-wave-vhash-motivation-evidence
seq: 1
title: VHash 論文の動機づけ — 長い tx が版の回収を止める問題の根拠を製品の公式文書 48 件と論文から集め、研究側の版・GC の症状の数値はすべて固定 snapshot の読み手の実験で、本案が縮める長い read-write tx の大きさの数値は読んだ範囲に無いと分けた (docs-only、insight + fragment、branch worktree-dev-wave-vhash-motivation-evidence)
---

## 本文

- 依頼: 並行 VHash wave の md_27 (`/work/1/SFC/tanab/tmp/vhash-2026-09-29/md_27.txt`)。ユーザー就寝中の背景 job。一次資料 `output/insights/2026-09-29/vhash-motivation-evidence/README.md`。対応する既存 item は main の「次の一手」に無かった (「GC を縛る」「動機づけ」「問題の実在」で検索、local main `8fe87f852`)。
- 段構成: 軽量版 (docs-only、実装面ゼロ)。段 2・3 と段 5・変異 matrix は省略。調査子 3 本 (Claude general-purpose、sonnet 明示、Web 使用) が製品 (R1 = PostgreSQL・MySQL・Aurora、R2 = Oracle・SQL Server・MongoDB・分散 DB) と研究 (R3) を分担し、親が逐語・数値 28 点と SHA-256 1 点を保存原文と照合 (全一致)。段 6 は Codex の read-only レビュー 1 本と焦点再レビュー 1 本。
- 段 4 の裁定: (P1) md_1 と重なる論文は機構を md_1 参照にとどめ、症状の大きさの数値だけを足す。(P2) 企業の障害報告・blog は根拠に入れない (資料の階層が違う。限界として一次資料 §1.3 に書いた)。
- 素材: 研究側の動機づけ実験 (Steam・vDriver・SAP HANA・LeanStore) は長い側がすべて固定 snapshot の読み手だった。本案の前進は固定 snapshot を対象にしないので、これらの数値を本案が縮める痛みとして引けない。長い read-write tx や何もせず待つ tx を原因に含めるのは製品の公式文書だけで、数値を持たない。論文の動機づけ節では「長い tx には種類があり本案が縮めるのは一部」と同じ段落で書き、その大きさは評価の実験で自分で示す必要がある (新規 item)。
- 素材: vDriver §5.2.1 の最大の版の列の長さは `pdftotext` では "104" になるが、`pdftohtml -xml` で "4" が 10 pt・3 単位上の別要素だったので 10⁴ と確定した。
- 段 6 レビューの所見: must-fix 2 件 (M1 が途中版の剪定と矛盾する言い過ぎ、prepared tx を「結果が確定済み」と書いた誤り)・should-fix 7 件・nit 1 件をすべて real として README を直した。棄却なし。
- 焦点再レビュー (1 巡): 前回の 10 件はすべて closed、新しい must-fix 0 件、新しい should-fix 3 件 (研究側の「すべて C1」の範囲、C1 と C2 を分けて書く文書の数え方、Oracle の保持保証の扱い) で NO-GO。3 件とも real として親が直し、引用した原文 5 か所を保存原文で照合した (全一致)。must-fix が無く文言の範囲の修正だけなので 2 巡目は起動しなかった。逐語は一次資料の `verbatim/`。
- 規律 6: MongoDB の manual の頁に AI 向けの誘導文 ("For AI agents: a documentation index is available at …") があった。調査子は従わず記録し、一次資料 §7 に書いた。
- 取得の異常: dev.mysql.com は curl に HTTP 403 (bot 判定) を返し、Internet Archive の保存物を読んだ (原本との一致は未確認)。SAP HANA の公式頁は本文の無い SPA 殻で取得できなかった。Sirin ほか ICDE 2021・Diva・HTAPBench・Psaroudakis ほか・CH-benCHmark の論文本文も取得できなかった。
- 異常と救出: 背景 job の `EnterWorktree(name)` が「Could not read the repository git config」で失敗 → 手動 `git worktree add -b` (Lustre で約 30 分、「システムコール割り込み」の警告が出たが rc=0) → `EnterWorktree(path)` で入った。`dev_wave_submodule_init.py` は 1 回目 `update-no-fetch` で rc=1、再走で OK。汎用子の起動は model 未指定だと `guard_agent` が拒否する (sonnet を明示して通った)。
- 受入: 受入全走はこの記録 commit の tip で行い、受領証は job dir (`/home/SFC/tanab/.claude/jobs/cb3a78aa/tmp/`) に残す (受入後にこの fragment を書き足すと受入のやり直しになるため、結果は書き足さない)。

## 次の一手差分

### 新規

- {{T:vhash-long-rw-tx-horizon-evidence}} **P2・新規**: VHash 論文の動機づけの根拠の穴を埋める。本案が縮める「読み取りを続ける長い read-write tx」が回収境界をどれだけ止めるかの数値は、外部の資料 (製品の公式文書 48 件と研究 10 本の読んだ範囲) に無い。評価の実験で、長い側がこの型の負荷で回収境界の遅れ・生存版数・版の列の長さを測る。stock Cicada では 1000 操作の長い update tx がほぼ commit しなかった (md_2) ので、長い tx が完走する負荷の作り方から要る。詳細は `output/insights/2026-09-29/vhash-motivation-evidence/README.md` §4.2・§8。
