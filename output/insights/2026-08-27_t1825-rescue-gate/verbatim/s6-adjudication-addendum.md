# 段 6 裁定 追補 — A5 の矛盾を解く

fix 子が `s6-adjudication.md` §2 (A5) と既存期待値の矛盾を正しく突いて停止した。
親の裁定に穴があったので、ここで解く。**この追補は `s6-adjudication.md` §2 を上書きする。**

## 何が矛盾していたか

- §2 は prunable worktree の期限を assessment time + `deadline_status: "indeterminate"` とした。
- 実装の rc 集約 (`tools/check_branch_rescue.py:1206, 1221`) は
  `deadline_status == "indeterminate"` が 1 つでもあれば「絵が不完全」として **rc=2** にする。
- 既存 test (`orchestrator/tests/test_check_branch_rescue.py:648`) は同じ prunable fixture に
  **rc=0** を固定している。

fix 子の停止は正しい。親が裁定し直す。

## 親の実測 (裁定の根拠)

現行の実装は **packed object も** 「assessment time を保守的 floor とし
`deadline_status: "indeterminate"` → rc=2」としている
(`orchestrator/tests/test_check_branch_rescue.py` の m10/m11 が rc=2 を固定)。

この convention が実データでどう働くかを親が測った。真の root 集合で喪失閉包に入る commit を
全 branch について列挙し、loose か packed かを数えた。

```
喪失閉包に入る commit: loose=16  packed=23  合計=39
```

**59% が packed。** つまり現行 convention では、実 repo の過半数の branch について
道具が rc=2 (絵を描けない) を返す。これは段 3 のレンズ B が否認し、段 4 §2.1 で
「常に止まる関門は迂回される」として設計を作り直した、まさにその失敗形である。

## 裁定 — 「今すぐ失われうる」は不完全ではなく、最も切迫した完全な答えである

`deadline_status` を **3 値**にする。

| 値 | 意味 | rc |
|---|---|---|
| `determinate` | その object 自身の mtime と実効 prune 期限から下界を導けた | 0 |
| `conservative-floor` | object 固有の mtime を得られないので下界は assessment time。**いつ失われてもおかしくない** | **0** |
| `indeterminate` | 下界そのものを立てられない (走行中の stat 変化、storage 分類不能、config 読取不能) | **2** |

- `conservative-floor` に倒す事由: packed / loose-and-packed、alternate のみに存在、
  prunable worktree root の期限 (git の `should_prune_worktree` を再現しない)、
  `gc.pruneExpire` の値を安全に解釈できない場合。
- **`conservative-floor` は完全な答えである。**「あなたはもう猶予が無いかもしれない」と
  言い切っており、判断に使える。fail-closed の向きは
  「何も言えない」ではなく「今すぐ失われうる」である。
- `indeterminate` は**本当に floor すら立たない**場合だけに残す。ここが唯一の rc=2 経路。

## 既存期待値の扱い (これは緩和ではない)

m10 / m11 の test は現在 packed に対し `rc == 2` と
`deadline_status == "indeterminate"` を固定している。これを
`rc == 0` と `deadline_status == "conservative-floor"` へ**親の裁定として変更する**。

- これはテストを甘くする変更ではない。m10 / m11 が守っていた本質
  「**pack の mtime を object の期限に流用して `determinate` にしてはならない**」は
  そのまま残る。`conservative-floor` は `determinate` ではない。
- 変更の理由は実測である (packed が実データの 59%)。
- `lower_bound_basis` は従来どおり出所を区別する
  (`assessment-time-conservative-floor` など)。

**fix 子への指示: この 2 つの期待値の変更だけは行ってよい。**
他のいかなる既存期待値も変えてはならない。

## 変異事前登録の追加

3 値化は新しい fail-open 経路を 1 本作る。必ず塞ぐ。

| ID | 位置 | 変異 | 期待 | 単一理由性 |
|---|---|---|---|---|
| m26 | 期限集約 | `conservative-floor` を `determinate` として扱う | KILLED | packed fixture の `deadline_status` と `lower_bound_basis` |
| m27 | 期限集約 | **本当に floor を立てられない場合を `conservative-floor` へ倒し rc=0 にする** | KILLED | storage 分類不能 fixture で rc=2 を要求 |
| m28 | 期限集約 | `conservative-floor` を rc=2 にする (現行の挙動へ戻す) | KILLED | packed fixture で rc=0 を要求 |

| ID | 正例 | 期待 |
|---|---|---|
| p07 | packed commit を含む非空閉包 | rc=0、`deadline_status == "conservative-floor"`、`loss_possible_not_before == assessment time` |
| p08 | prunable worktree root を持つ非空閉包 | rc=0、当該 root の `classification == "time-limited"` |

## この追補が変えないもの

- 段 4 §2.1 の rc の意味 (0 = 絵が完全 / 2 = 技術的に不完全 / 3 = 通知 / 64 = usage)。
- `not-landed` は内容であって技術的失敗ではない (rc=0)。
- `s6-adjudication.md` の §1、§3〜§8 と m18〜m25、p05〜p06 はそのまま有効。
