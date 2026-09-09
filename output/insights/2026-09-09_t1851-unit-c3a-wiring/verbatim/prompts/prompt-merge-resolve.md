単独段 dispatch: stage=author; sandbox=workspace-write; parent=/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1851-unit-c2

必読事項の射影 (いずれも絶対パス。読めなければ即停止し、その旨を出力に書いて終わること):

- 作業 root (書込み可、ここだけを編集する): `/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1851-unit-c2`
- 親の段 1 brief: `/home/SFC/tanab/.claude/jobs/460f7d58/tmp/t1851unitsel/s1-brief.md`
- 共通規律: `/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1851-unit-c2/CLAUDE.md`

# 段 author — 進行中の main 取り込みの競合 2 件を解く

作業 root では `git merge` が**進行中**で、次の 2 file が `UU` (both modified) で残っている。
**この 2 file の競合解決だけが仕事である。**

1. `orchestrator/tests/acceptance_duration_ledger.json` — 競合 53 hunk
2. `orchestrator/tests/test_backoff_extended_sweep.py` — 競合 1 hunk

## 親が実測した事実

- merge base は `931fd8fc5`。ours (wave 側 `38aed135f`) と theirs (local main `cbcdb6c91`)。
- 台帳: base→ours が +2386 行、base→theirs が +2117 行。**両側が別の nodeid を追加している。**
- sweep test: base→ours が +52 行、base→theirs が +620 行。**両側が test を追加している。**
- **wave 側の台帳追加分を再生成できる JUnit XML は残っていない** (親が
  `/work/1/SFC/tanab/dev-wave-jobs/` と旧 job dir を走査し、単位 C2 の受入 JUnit が
  不在であることを確認した)。したがって producer で当て直す道は取れない。

## 解き方

### 台帳 (`orchestrator/tests/acceptance_duration_ledger.json`)

**両側の entry を 1 件も落とさない厳密な和集合にする。**

- ours 側・theirs 側のどちらかに存在する nodeid は、**その duration 値を byte exact に保って**残す。
- 両側に同じ nodeid があり値が違う場合は **theirs (main 側) の値を採る**。理由を出力に書くこと。
- placeholder (`0.0` など) を新たに作ってはならない。**測っていない値を書かない。**
- 台帳の canonical 書式 (key 順序、`nodeid_count` などの集計 field、末尾改行) は
  producer `tools/update_acceptance_duration_ledger.py` が出す形に合わせる。
  集計 field は和集合の実数へ再計算する。
- 3 つの不変条件を**自分で検算して数値で報告**する。
  (a) ours 側 entry の欠落 0 件、(b) theirs 側 entry の欠落 0 件、
  (c) 既存 duration 値の変更は上記の重複 nodeid 分だけで、その件数と nodeid を列挙する。

### sweep test (`orchestrator/tests/test_backoff_extended_sweep.py`)

**両側が追加した test を両方残す和集合にする。** test の削除・改名・skip 化・assert の弱体化を
してはならない。import や module 定数が両側で衝突する場合は、意味を変えずに両方を成立させる。

## 検査 (自分で走らせて結果を数値で報告する)

作業 root は書込み可なので、次を実走して結果を報告すること。

- `python3 -m pytest orchestrator/tests/test_update_acceptance_duration_ledger.py -q`
  (24 node の想定。`PYTHONPATH=.` が要る場合は付ける)
- `python3 -m pytest orchestrator/tests/test_backoff_extended_sweep.py -q`
- `python3 -c "import json; json.load(open('orchestrator/tests/acceptance_duration_ledger.json'))"`
  相当の JSON 妥当性確認

赤が出たら**原因を書いて止まる**。テストを弱めて緑にしてはならない。
`--deselect` や skip で赤を隠さない。

## 禁止

- **commit しない。`git add` もしない。`git merge --abort` も `git reset` もしない。** 親が行う。
- 競合していない file を編集しない。`git status` で `UU` の 2 file 以外に差分を作らない。
- 台帳の凍結対象 suite の entry を触らない (producer の `--add-only` が凍結対象外だけを扱う理由と同じ)。
- docs (`docs/**`) を編集しない。
- 出力へ結合文字 U+0300〜U+036F を使わない。

## 出力形式

```
## 総括
(3-5 行。何をどう解いたか)

## 台帳の解き方と検算
(和集合の件数、欠落 0 の検算、値を変えた nodeid の列挙)

## sweep test の解き方

## 実走した検査の結果
(command と passed/failed の実数)

## 残った懸念
```
