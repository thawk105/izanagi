対象スクリプト1ファイルのみ修正しました。

- R-1: [reissue_floor_protocol.sh:23](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t657-t660-g2-activation/output/insights/2026-08-09_t657-t660-g2-activation/reissue_floor_protocol.sh:23)
  - cleanup 冒頭で `trap - EXIT` のみ解除。
  - 続けて `trap '' HUP INT TERM` とし、復元・検証・一時領域削除の完了まで再 signal を無視。
  - EXIT rc は trap 引数で保存しました。

- R-2: [reissue_floor_protocol.sh:41](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t657-t660-g2-activation/output/insights/2026-08-09_t657-t660-g2-activation/reissue_floor_protocol.sh:41)
  - HEAD 復元失敗時、backup の通常ファイル性と旧 SHA-256 を再検証。
  - target と同じ filesystem 内に一時ファイルを作り、copy・SHA 検証後に `mv` で原子的に復元。
  - [同:85](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t657-t660-g2-activation/output/insights/2026-08-09_t657-t660-g2-activation/reissue_floor_protocol.sh:85) で HEAD/index/worktree の blob 三者一致を最終検査。
  - 失敗時は [同:93](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t657-t660-g2-activation/output/insights/2026-08-09_t657-t660-g2-activation/reissue_floor_protocol.sh:93) で backup 絶対パスと期待 SHA-256 を stderr に表示。

- R-3: [reissue_floor_protocol.sh:115](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t657-t660-g2-activation/output/insights/2026-08-09_t657-t660-g2-activation/reissue_floor_protocol.sh:115)
  - shell 側で、空値を含め `PYTHONOPTIMIZE` が設定済みなら停止。
  - 5個すべての Python heredoc に `sys.flags.optimize != 0` の拒否を追加。
  - 全 `assert` を、具体的な不一致内容を stderr に出す `raise SystemExit(...)` へ置換。静的検索結果は `assert=0`、Python heredoc 5件、最適化 guard 5件です。

保存した性質:

- 旧/new SHA-256、774 bytes、g1 hash 1回、18 keys、差分 `{contract_sha256}` を維持。
- 冪等分岐、exact staged path 検査、message file → provenance preflight → `commit --only -F` → full-history 監査を維持。
- `freeze-protocol` の stdin は redirect していません。
- テスト期待値、skip、受理集合を変更していません。
- 他の caller・fixture・consumer test への変更はありません。既存の未追跡 worklog fragmentにも触れていません。

構文検査の逐語結果:

```text
$ bash -n output/insights/2026-08-09_t657-t660-g2-activation/reissue_floor_protocol.sh
stdout/stderr: なし
rc=0
```

## 総括

- R-1/R-2/R-3 を実装済み。
- tracked 差分は指定スクリプト1ファイルのみ。
- `git add`、commit、stash は未実施。
- スクリプト本体、freeze、pytest、provenance checker は未実走。
- したがって受入緑は主張しません。