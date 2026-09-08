単独段 dispatch: stage=author; sandbox=workspace-write; parent=/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1851-unit-c2

必読事項の射影 (いずれも絶対パス。読めなければ即停止し、その旨を出力に書いて終わること):

- 作業 root (read でのみ使う): `/work/1/SFC/tanab/izanagi/.codex/worktrees/t1851-c2-mergeaudit`
- **自動 merge の結果 (HEAD 側 = 本 wave、もう一方 = local main 931fd8fc5)**: `/home/SFC/tanab/.claude/jobs/4ddc6923/tmp/t1851c2/merge/merged.py`
- **HEAD 側 (本 wave) の版**: `/home/SFC/tanab/.claude/jobs/4ddc6923/tmp/t1851c2/merge/ours.py`
- **main 側の版**: `/home/SFC/tanab/.claude/jobs/4ddc6923/tmp/t1851c2/merge/theirs.py`
- **共通祖先の版**: `/home/SFC/tanab/.claude/jobs/4ddc6923/tmp/t1851c2/merge/base.py`
- 共通規律: `/work/1/SFC/tanab/izanagi/.codex/worktrees/t1851-c2-mergeaudit/CLAUDE.md`

# 自動 merge が両側の意図を両方とも残しているかを監査する

`orchestrator/tests/test_ccbench_spawn_sites.py` は **local main の取り込みで両側が変更した
唯一の実装面 file** であり、git が競合なく自動 merge した。しかし
**競合なしの自動 merge でも意味的に壊れうる。** その監査があなたの仕事である。

**`git` を一切実行しない。commit しない。**
**追跡下の file を 1 つも変更しない。** 作業 root は読むだけに使う。

## 両側が何をしたか

- **HEAD 側 (本 wave)**: `_DEFERRED_GATE_MEMBERS` の `sink_lineno` を
  `s8b_floor_campaign.py` の行番号ずれに追随させた
  (`4715 -> 4707`、`8642 -> 8636`。台帳本体と鏡像 pin の対、計 4 箇所)。
  本 wave は同 production file から 14 行の helper を除去し数行を足している。
- **main 側**: 別 wave の変更 (内容は自分で読んで確かめること)。

## 監査すること

1. **両側の意図がどちらも残っているか。** 片側の変更が消えていないか。
2. **`_DEFERRED_GATE_MEMBERS` の期待集合の件数**が、両側の意図の和と一致するか。
   entry が黙って消えたり増えたりしていないか。
3. **行番号 pin の値**が、本 wave の追随後の値 (`4707` / `8636`) を保っているか。
   main 側が同じ entry を別の値へ変えていた場合は、**どちらが現物と一致するか**を
   `merged.py` からは判断できないので、**その旨を報告すること** (推測で決めない)。
4. `relative_path` / `owner` / `sink_kind` / `sink_scope` が両側とも保たれているか。
5. **自動 merge が hunk の境界で意味を混ぜていないか** (片側の行が別の entry へ紛れ込む型)。

## 出力

**file を 1 つも作れない。成果物は最終メッセージの本文へ全文を書くこと。**
予算が尽きそうなら**途中結論を出力形式どおりに書いて終わること** (無出力が最悪)。

## 禁止

- `git` を実行しない。commit しない。追跡下 file を変更しない。
- 走らせていないテストを緑と書かない。
- 出力に結合文字 U+0300〜U+036F を使わない。

## 出力形式 (この見出しをこの順で使う)

## base からの両側の差分 (それぞれ何をしたか)
## merged が両側の意図を保っているか
## 期待集合の件数 (base / ours / theirs / merged)
## 行番号 pin の値の確認
## 意味が混ざっている箇所 (無ければ「無し」)
## 総括
