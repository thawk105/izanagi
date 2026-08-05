# 段 6 裁定 — 敵対レビュー 2 本 (A: NO-GO blocker 1 / must-fix 5、B: NO-GO blocker 1 / must-fix 4)

親が real/refuted・採否・scope を裁定する。**fix 実装子はこの文書だけを「何を直すか」の正本とする。**

## 親が新たに実測した真因 (レビュー 2 本とも見落とした)

親が段 6 で報告した誤検出 3 件の真因は、**merge commit を `git diff-tree -m` で各親と比較していた**
ことである。`-m` は「どれか 1 つの親と異なる path」をすべて列挙するため、merge が取り込んだ側の
内容が丸ごと「この commit の変更」になる。

- 実測: `14c13c22` の変更 path は `-m` で **123 件**、combined diff (`-c`) で **3 件**。
- 誤検出 3 件は **すべて merge commit** (`git rev-list --no-walk --merges` で確認)。
- 全体シミュレーション: 到達不能 127 commit に対し、`-m` = 報告 3 件、**combined = 報告 0 件**。
  (`simulate-merge-fix.py`。repo も実装も変更していない親の測定)

**この修正は履歴による抑止を一切足さないため、A-3 / B-4 が反対した「path 再利用の見逃し拡大」を
起こさない。** よって親が段 6 冒頭に出した P-1 の「main の履歴に一度も現れていない」案は**撤回する**。
A-3 / B-4 は real であり、撤回によって closed とする。

## 採用する fix (本 wave の scope)

### FIX-1 (blocker 相当・親実測) — merge commit は combined diff で評価する

- `changed_files()` を、親が 2 つ以上の commit では combined diff (`git diff-tree -c` 相当)、
  それ以外は現行どおりに分岐させる。root commit の扱いは維持する。
- **negative control を 1 本追加する**: 「main を取り込んだ merge commit が到達不能でも、
  取り込んだ側の内容を報告しない」。合成 repo で main 側の変更を merge した commit を
  到達不能にし、報告 0 件を要求する。
- 成果物影響: 直さないと稼働 repo で常時 3 件鳴り、監査が無視されるようになる (I1 違反)。

### FIX-2 (A-5 / A-9 / B-5) — 誤った安心を与えず、入口を fail-closed にする

- **tool の出力文言を改める。** 「失われた未 land 作業」という断定をやめ、
  「要確認の到達不能変更」とする。かつ **`--help` と 0 件時の出力に、この監査が
  検出しない範囲 (既存ファイルへの変更・削除・同名別内容・gitlink 更新) を 1 行で明示する。**
  これが A-2 / B-1 の「誤った安心」を、設計を変えずに閉じる唯一の手段である。
- **入口 `.claude/commands/cleanup-branches.md` に rc の扱いを明記する。**
  rc=0 のときだけ削除工程へ進み、rc≠0 なら削除を止めて §5 で報告する。
- **byte 予算**: 現在 3,981、実効上限 3,983。**安全義務からは 1 byte も削ってはならない**
  (B-6 が「今回の 3 削除は安全義務を摩耗させていない」と refuted しているので、
  これ以上削る余地は乏しい)。収まらなければ**実装を止めて報告すること。**
  親が裁定する。テストの期待値を緩めて予算を作ることは禁止。

### FIX-3 (A-10) — 非 UTF-8 path を rc=2 へ倒す

- git 出力の decode 失敗が素の traceback + rc=1 (= 「報告あり」と同じ) になる経路を塞ぐ。
  `errors="surrogateescape"` 等で受けるか、`UnicodeError` を捕捉して rc=2 にする。
- 成果物影響: 直さないと「実行不能」を「取り残しあり」と誤分類し、救出対象を誤る。

### FIX-4 (B-3) — 変異 spec の再照準

B-3 の静的判定は real である。次のとおり作り直す (**実装より先に spec を確定する**)。

- **M1 を取り下げる。** `rev-list --all` への置換は候補集合を増やさず減らすため、赤理由が
  複数になる。代わりに **M1' = `--no-reflogs` を外す**か、到達不能判定の行を
  「全 commit を候補にする」形へ変える案を fix 実装子が提案し、親が単一理由性を確認する。
- **M5 を再照準する。** 現行の `if lost_paths:` 無効化は fold include 正例も同時に落とす。
  **CLI 側の `if not findings:` を常真にする**位置へ移し、positive control の CLI assertion
  だけが赤になるようにする。
- **M6 を FIX-1 に対する変異へ差し替える。** combined 分岐を `-m` 固定へ戻す →
  FIX-1 で追加する merge negative control だけが赤。
- M2・M3・M4 は現行のまま維持する (B-3 の表でも単一理由性は成立)。
  ただし B-3 が「M2・M3 は誤った path-only オラクルを固定する」と述べる点は real であり、
  **これは FIX-2 の文言明示で「仕様どおりの限界」として扱う** (下記 scope 外へ送る)。

## 実装しない — 裁定パッケージでユーザーへ返す (scope 外の real 所見)

いずれも real と認めるが、**ユーザー裁定が定めた設計 (「到達不能 かつ 変更ファイルが main に不在」)
そのものを変える**ため、本 wave では実装しない。

- **A-2 / B-1 (blocker)**: path 存在ではなく blob / patch 同値性で判定する再定式化。
  既存ファイルへの未 land 変更・削除・同名別内容・submodule gitlink 更新を検出できるようになるが、
  検出器の定義・コスト・偽陽性プロファイルが変わる。FIX-2 で「検出しない範囲」を明示することで
  誤った安心だけは閉じる。
- **B-2**: 到達不能 graph の frontier / net delta 評価 (追加後に削除された中間物の誤報)。
- **A-4**: `docs/spool/` `docs/archive/` の無条件除外を、fold 済みの証明ベースへ変える。
- **A-6**: ref snapshot と fsck の非原子性 (並行 wave の増減で一時的な見逃し)。
- **A-11**: branch 削除・worktree prune・gc の前に必ず監査を走らせる配線。

## refuted として closed にする所見

- **A-7** (I5 読み取り専用違反の疑い) — refuted。実行する git command は読み取り専用のみ。
- **B-0** (positive control が恒真・自己オラクル) — refuted。
- **B-6** (入口の 3 削除が安全義務を摩耗させた疑い) — refuted。**よってこれ以上削らない。**
- **B-7** (純増検出力ゼロの疑い) — refuted。この監査だけが ref 外 commit を列挙する。

## A-8 (実行場所の分類) — 親が実測して closed

A-8 は「未計測なので `unknown` = dispatch-required 扱いになる」と指摘した。real だったので
親が `docs/pegasus-runbook.md` §7.0 の手順 (専用 scope の cgroup charged memory を sampling) で
実測した。

- 測定日 2026-08-05、worktree `dev-wave-cleanup-dangling-audit`、
  argv = `python3 tools/audit_dangling_commits.py`、繰り返し 3 回。
- 入力規模: 到達不能 commit 127、local branch 11、main tree path 8,954。
- 観測ピーク (3 回の最大) = **56,442,880 bytes = 53.8 MiB** (他 2 回は 29.7 / 29.1 MiB)。
- **certified peak = 53.8 + max(25%, 128 MiB) = 181.8 MiB。規範値 512 MiB 未満 → `local-ok`。**
- 参考: wall clock 2.9 秒、per-process ピーク RSS 23 MB (規約上の代理値にはしない)。
- **申し送り**: メモリは main tree の path 集合と branch tip 数で増える。branch 数や
  到達不能 commit 数が桁で増えたら再分類が要る (`tools/README.md` の命令 4)。

したがって入口から直接実行してよい。A-8 の「入口に sanctioned な実行場所を明記」は、
`local-ok` である以上追加の文言を要さないと裁定する (byte 予算の観点でも)。
