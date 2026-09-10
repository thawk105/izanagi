# [T-945] 起動 gate の再開モード — 実測と再開手順

wave = `dev-wave-t945-resume-mode` / 2026-08-13 / branch = `worktree-dev-wave-t945-resume-mode`

## 1. 何が問題だったか

`DW-O20` は worktree の「作成・再開直後」に `tools/check_wave_startup.py` を走らせ非 0 なら停止せよと
定める。既定 mode (`fresh`) は点 1 で `HEAD == local main` を要求するため、**未 land の自 wave commit を
持ち `HEAD != local main` である間は必ず非 0 になる**。しかも NG 文面は
「local main と同じ commit から fresh worktree を作り直す」と誘導するので、文面どおり従うと
未 land の作業を捨てる。

一方 `--mode resume` は checker 初版から存在したが、条件を持たず点 1・点 2 (作業 branch)・
clean tree を無条件に素通ししていた。つまり「止まる既定」と「何も見ない bypass」の二択しかなかった。

## 2. 実測 (この wave で得た一次事実)

| 事実 | 実測方法 |
|---|---|
| `--mode resume` は commit `aaafa772` (T-153 の checker 初版) から存在する | `git log -L` |
| 旧 resume は点 1・点 2・clean tree を呼ばない | `check_repository` の `if mode == "fresh"` 枝 2 箇所 |
| `git rev-parse --git-path info/grafts` は**終端 symlink を解決した path** を返す | 最小再現 (dangling symlink を作り `--git-path` の出力と `lstat` を比較) |
| `refs/heads/main` を `refs/heads/work` への symbolic ref にすると `HEAD..refs/heads/main` が 0 になる | 変異テスト fixture の事前 assert |
| 同じ symbolic ref 偽装は **fresh の等式検査も通す** (両 `rev-parse` が同一 OID) | 段 6 レビュー C[8] → fresh 用の負例テストで固定 |
| repo 内に checker の自動 caller は 0 件 (呼び手は人間・AI の手動実行のみ) | 全文検索 (`check_wave_startup`, `check_repository(`) |

## 3. 是正後の契約

- `fresh` = 点 1 は `HEAD == local main`。
- `resume` = 点 1 を「local main を包含し 0 commit 遅れ」へ置換。ahead は無制限に許す。
- **それ以外の検査 (作業 branch、進行中操作なし、clean tree、submodule marker、handoff) は
  mode に依存せず必ず走る。**
- 未知 mode は CLI (`choices`) と Python API の双方で fail-closed。既定は `fresh` のまま。
- 包含は raw commit graph 上で判定する — `GIT_NO_REPLACE_OBJECTS=1` 固定、`info/grafts` の存在拒否
  (git common directory へ自前連結して終端 symlink を解決させない)、`refs/heads/main` の
  symbolic ref 拒否 (mode 共通)。
- 可視化 `describe_main_divergence` は fail-open のまま。gate はその戻り値・出力文字列を参照せず、
  例外時も診断文字列へ落として gate を必ず走らせる。

## 4. 中断した wave を gate を緩めずに再開する手順

`resume` が clean tree と main 包含を要求するようになったため、途中停止した worktree では
次の順で整えてから gate を通す。**gate を迂回しない。**

1. rebase / merge が進行中なら、まず完了または中止する。競合状態のまま退避しない。
2. 一時変異 (`DW-O19`) を掛けたファイルは正本 bytes へ復元する。変異を再開 payload として残さない。
3. worktree 内に handoff が残っていれば repo 外へ移す (背景 job は `--external-handoff` で検査する)。
4. commit できる完成分は wave branch の checkpoint commit にする。未完成分は
   `git stash push --include-untracked` か repo 外へ保存する。`pop` せず、gate 通過後に `apply` する。
5. local main が進んでいれば取り込む (`--ff-only` で揃わない場合は許可済みの統合手順に従う)。
   分岐を解けなければ**停止して親裁定へ戻す**。
6. clean な状態で `tools/check_wave_startup.py --mode resume` を通し、その後に退避分を戻す。

NG 文面自体がこの案内を持つ (「local main を取り込み、clean tree にしてから `--mode resume` を
再実行する」)。`DW-O20` は L2 単節予算 1000 bytes の制約があるため、手順の全文は本書を正本とする。

## 5. この gate が保証しないこと

`--help` と `OK:` 行に明記したとおり、checker は **wave identity・branch 所有・`--repo` の同一性を
認証しない**。clean で main を包含していても、それが「この wave の branch である」ことも
「自 wave の作業が失われていない」ことも保証しない。残る穴・非保証 7 件は worklog の
`startup-gate-residual-hardening` として裁定へ返した。
