---
schema: izanagi-spool-v1
ledger: failures
authored: 2026-08-04
wave: wave-t340-thirdparty-fetch
seq: 3
---

## 新規

### {{F:empty-dir-untracked-fixture}}. 事前登録変異のテストが空 directory を untracked file とみなしていた [テスト代表性]

- 事象: 変異 M6 (`--untracked-files=all` を落とす) を殺すテストが、fixture で
  `(source / "untracked" / "payload").mkdir(parents=True)` と**空 directory だけ**を作っていた。
  git は空 directory を追跡も列挙もしないため、`git status --porcelain --untracked-files=all` の
  出力は空のままになり、**実装の正誤と無関係に**期待した rc が出なかった。
  親の受入全走で赤として顕在化し、別 repo での実測 (空 dir → 出力ゼロ、実ファイル → `??` 行) で
  原因を確定した。段 6 の敵対レビュー 2 本も独立に同じ欠陥を指摘した。
- 根本原因: 「dirty な worktree」を作るつもりで、git が可視化する単位 (blob) ではなく
  filesystem の単位 (directory) を作った。fixture が意図した入力を作れているかを、
  変異注入前の baseline で確認していなかった。
- 恒久対応: 変異 harness (`tools/mutation_harness.py`) の baseline 走行が
  fail-closed で先に走る契約 (DW-M05) と、DW-M03 の「fixture が単一理由か確認する」義務。
  本件は baseline ではなく変異本走で顕在化したため、**fixture の入力が実際に効いているかを
  変異前に確認する**という読み方を本エントリで顕在化する。
- 再発検知: 事前登録した変異の本走で `SURVIVED` / 期待外の赤理由が出たら fixture を疑う。

### {{F:commit-during-acceptance-run}}. 受入全走の実行中に親が commit し、HEAD 束縛テストを自分で赤くした [計測汚染]

- 事象: 段 7 の docs commit 直後に受入全走を投入し、**走行中に段 8 の commit を作った**。
  `test_s8b_oracle_driver.py::test_real_freeze_gate_lists_floor_and_budget_null@real-repo` が
  `validation_head` の不一致で赤になった。値は「テスト開始時の HEAD」対「段 8 commit 後の HEAD」で、
  差分の中身とは無関係である。単独再走は 1 passed で再現しなかった。
- 根本原因: 全走を待ち時間とみなし、その間に別の段の作業 (docs 編集と commit) を進めた。
  受入全走は **repo の状態を測る計測**であり、走行中の HEAD 変更は外乱である。
  計算ノードへ dispatch する形なので「自分の worktree を触っても影響しない」と誤認しやすい。
- 恒久対応: `DW-O18` の親テスト契約 (cwd を repo root にし、再現しない赤を差分へ帰属しない) に加え、
  **受入全走の投入から結果取得までは commit・stage・tracked file の編集を行わない**という
  読み方を本エントリで顕在化する。段を跨ぐ待ち時間には repo 外の作業だけを置く。
- 再発検知: 赤の内容が `*_head` / `HEAD` / commit hash の不一致なら、まず自分の走行中 commit を疑う。
  `git reflog` の時刻と job の Started/Ended を突き合わせれば確定できる。

### {{F:mutation-masked-by-outer-verify}}. 内側検証の変異を外側の一括再検証が mask した [恒真ゲート]

- 事象: 事前登録した変異 M15 (publish 直後の再検証と rollback を落とす) が本走で **SURVIVED**
  (rc=0、赤ゼロ) した。実装の `_hydrate` は per-item の publish 後検証に加えて、
  末尾で全 destination をまとめて再検証する。したがって内側を落としても**同じ例外が外側から
  上がり、rc と stderr には差が出ない**。実際に消える挙動は「publish 済み destination を
  rollback して消す」ことだけで、テストはそれを状態として見ていなかった。
- 根本原因: 事前登録の時点で「どの層が実効 gate か」を確認せず、変異位置だけを登録した。
  DW-M01 が要求する「手前に同じ入力を拒否する検査がないことをコードで確認する」を、
  **手前ではなく後ろにある冗長層**について行っていなかった。
- 恒久対応: DW-M02 の再照準手続き — 生存したらまず他層の mask を疑い、実効 gate へ再照準して
  両層同時変異まで裏取りする。本件では rollback を状態 assert するようテストを強化し、
  M15 (単層) と M15C (両層同時) の双方で KILLED を実測した。初回の SURVIVED は
  erratum として台帳に残す。
- 再発検知: 変異本走の `SURVIVED` を equivalent と即断せず、同じ検査を行う他層の有無を
  実コードで数える。逐語は `output/insights/2026-08-04_t340-thirdparty-fetch/`。
