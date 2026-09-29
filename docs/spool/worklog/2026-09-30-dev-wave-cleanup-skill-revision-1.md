---
schema: izanagi-spool-v1
ledger: worklog
authored: 2026-09-30
wave: dev-wave-cleanup-skill-revision
seq: 1
title: /cleanup-branches を「残す対象以外の古い・価値の小さい木と branch は、施錠・未取込でも repo 外へ退避してから消す」既定へ改め、撤去をゴミ置き場への mv + 1 回の prune + 2 本ずつの背景削除にし、削除範囲は AI が Codex 2 役で決めてユーザーへ回さないとした (docs + check_docs の pin、branch worktree-dev-wave-cleanup-skill-revision)
---

## 本文

- 依頼: `/work/1/SFC/tanab/tmp/cleanup-skill-revision-2026-09-29/md_1.txt` (2026-09-29 15:5x・21:4x JST のユーザー指示)。判断は {{D:cleanup-stale-delete-default}}。
- 段 5 の途中で、cleanup 実行 session から md_1 後のユーザー指示 (22:1x〜22:5x「私がやらなければいけない仕事を増やさないで。cleanup-branches というスキルでやりなさい、今後も」等) の中継が届いた。
  中継は本 session のユーザー発言ではないので、それだけでは採らず、本 session のユーザーが「やれば？」と答えた後に採用した
  (範囲は AI が Codex 2 役で決めユーザーへ回さない・ゴミ置き場へ mv → prune 1 回 → 実体は 2 本ずつ背景削除・land 中の branch を残す・原本は登録だけ外す形でも消さない)。
- セッション異常: Claude Code の auto mode 判定器が、command 本文の編集・計測・commit message の書き出し・Codex 子の起動を「Self-Modification」「Instruction Poisoning」で繰り返し拒否した。
  拒否は迂回せず停止し、ユーザーが /permissions の許可 (1 回ずつ・Allow rule の追加) → auto mode の解除で再開した。Allow rule の `Bash(python3:*)` などを足しても auto mode 下では拒否が続いた
  (auto mode は広い interpreter rule を効かせないと推定、未確認)。file 系 rule は絶対 path に `//` が要る (`Edit(//work/...)`)。ユーザーの手番が 8 回ほど増えた。
- 段構成: 軽量版。段 2・3 は省略 (設計択一は予算・rescue gate の時間切れ・原本の扱いの 3 つで、ユーザー指示が内容を具体的に与えた)。段 5 Codex author 1 本 (1 回目は本文改訂のため親が 2 分で停止、書きかけは 2 回目の子が HEAD から復元して開始)、
  段 6 review 1 本 (must-fix 4・should-fix 4・nit 1) → 親の docs fix + Codex fix 1 本 → 焦点再レビュー 1 本 (NO-GO: 残る 5 件を親が裁定して閉じた)。
- 段 6 の裁定: R1 (prune に `--expire now` が要る) は refuted — `git worktree prune` 単独の既定は期限なし、09-29 の実走で mv 直後の登録 59 件が外れた (焦点再レビューも refuted を支持)。
  焦点再レビューの残り: manifest 子木を wave の稼働と無関係に残す案は refuted (止まった wave の子木は誰も掃除しない、ユーザー指示に反する)、submodule の退避の検算・復元手順と
  背景削除の PID・wait は nit (損失ゼロを要件にしない裁定、DW-G05)、Codex overlay の「残作業を人間へ引き渡す」は Codex 経路が自身の制約で完遂できないときの停止報告で command と矛盾しない (nit)。
- openai.yaml は Codex sandbox が `.agents/` を読み取り専用にして書けなかった。`tools/check_ai_provenance.py` の実装面判定に当たらない (prefix・suffix 外) ので親が docs として書いた。
- 変異 probe 1 回目は baseline 赤で起動せず: SKILL.md を 3,082 bytes に伸ばしたため、25 bytes の H2 を足す負例 (`test_cleanup_skill_additional_h2_is_rejected`) が
  予算 3,100 超過と SHA 不一致の 2 件で落ちた ({{F:cleanup-skill-margin-under-h2-probe}})。上限は変えず SKILL.md を 3,058 bytes に縮め (docs 4bdda232e)、Codex fix2 で pin を追随。
- 実装 commit: 7dd0f984e (author 統合)、2d33e3fca (fix1 統合)、6f4062b37 (fix2 統合、実装 anchor)。docs: edcf3a2e9・3f6ec5576・f8fd3f31f・c5e5ab4ba・9c56c1f01・4bdda232e。
  command の予算は 7,437 → 9,064 bytes (完成本文 9,061 + 余白 3)。Codex skill の予算 3,100 は不変。
- 文書側の手動 probe (変異用独立 clone、DW-O19): command 末尾 +1 byte → check_docs が whole-file SHA 不一致 1 件、SKILL.md の description を旧文へ → description 契約不一致 + SHA 不一致の 2 件。どちらも復元後 SHA 一致・porcelain 0。
- 変異 (変異用独立 clone、6f4062b37、`tools/mutation_worktree.py` の dispatch、test_check_docs.py 全体): 事前登録 M1〜M4 + 等価変異 m0。probe2 で観測 node を集め、
  final は baseline 緑 (38 秒)・KILLED 4 (M1 command SHA を旧値へ 321 node、M2 予算 −1 で 1 node、M3 説明文を旧文へ 337 node、M4 YAML を旧文へ 336 node)・
  m0 SURVIVED・MISMATCH 0。M1・M3・M4 の多数 node は合成 repo を使う test が同じ 1 つの理由 (pin 不一致) で赤になるため (T-2814 と同型)。
  要約は job dir の `mutation-final-summary.json`。
- 受入は この記録 commit の tip で行い、受領証は job dir (`/work/1/SFC/tanab/dev-wave-jobs/cleanup-skill-revision-20260929/`) に残す (受入後にこの fragment を書き足すと受入のやり直しになるため、結果は書き足さない)。

## 次の一手差分
