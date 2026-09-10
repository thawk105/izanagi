# 段 6 裁定 追補 2 — 期限契約を一般則で書き直す

fix 子が 2 回連続で、追補 1 と既存期待値の矛盾を突いて停止した。2 回とも子の判断は正しい。
原因は親が「どのテストを変えてよいか」を**個別列挙**したことである。
契約として書き、どの期待値が従うかは実装側が導く形に直す。

**この追補 2 は追補 1 の該当部分を上書きする。** 矛盾したら追補 2 が勝つ。

## 1. 期限契約 (一般則)

`retention.loss_possible_not_before` は**常に出す**。値は「この object が失われうる最も早い時刻」の
**下界**である。`deadline_status` はその下界の導出根拠を 3 値で示す。

| 値 | 条件 | `loss_possible_not_before` | rc |
|---|---|---|---|
| `determinate` | **この object 自身の mtime** と実効 prune 期限の両方を観測でき、下界を算術で導けた | mtime + 期限 | 0 |
| `conservative-floor` | 下界は立つが、object 固有の保持期間を観測できない。**いつ失われてもおかしくない** | assessment time | **0** |
| `indeterminate` | **下界そのものを立てられない** | 出さない (null) | **2** |

### `conservative-floor` に倒す事由 (網羅。これ以外を足さない)

1. object が packed、または loose-and-packed (pack の mtime は object 個別の到達不能時刻ではない)。
2. object が alternate ODB にしか無い。外部 ODB の保持契約を観測できない。
   `lower_bound_basis` は外部 ODB であることが分かる値にする。
3. prunable worktree が保持する root の期限
   (git 2.34.1 の `should_prune_worktree` を再現しないと決めた。追補 1 §2)。
4. `gc.pruneExpire` の値を安全に解釈できない (相対表現でも絶対時刻でもない、`never` 以外の未知形)。

### `indeterminate` に倒す事由 (これだけ。ここが唯一の rc=2 経路)

- object の storage を分類できない (`cat-file` が commit と答えない、応答が壊れている)。
- 走行中に stat が変化した (前後 2 回の照合が不一致)。
- 実効 gc config を読めない scope がある (追補なしで既定へ倒さない。追補 1 の A4)。
- assessment time 自体を確定できない。

**`gc.pruneExpire = never` は `determinate` である** (失われないので下界は「起こらない」)。
その場合の表現は実装が決めてよいが、`conservative-floor` に倒さないこと。

## 2. 期待値の変更許可 (一般則。個別列挙をやめる)

**この wave が本 wave 内で新規に作った次の 2 file については、上記 §1 の契約に合わせて
既存の期待値を変更してよい。**

- `orchestrator/tests/test_check_branch_rescue.py`
- `orchestrator/tests/test_branch_rescue_ledger.py`

理由: この 2 file は本 wave が段 5 で新設したもので、まだ land していない。
そこに書かれた期待値は**親が段 4 で与えた 2 値の期限契約を写したもの**であり、
親がその契約を §1 で変更した以上、追随するのが正しい。緩和ではなく再基底である。

**次は緩和にあたるので禁止する。**

- `determinate` の受理集合を広げること。特に pack の mtime や alternate の存在を
  object 個別の保持期間として使うこと。
- `indeterminate` の事由 (§1 の 4 つ) を `conservative-floor` へ倒すこと。
- rc=2 になるべき事由を rc=0 へ倒すこと。
- 上記 2 file **以外**の既存テストの期待値を変えること。
  (`orchestrator/tests/test_check_docs.py` の SHA 定数と `_SYNTHETIC_CLEANUP_COMMAND` の
  更新は pin の追随であり、期待値の緩和ではない。これは許可済み。)

変更した期待値は 1 件ずつ、報告の「## 1」に
「旧期待値 → 新期待値 → §1 のどの行に従ったか」を書くこと。

## 3. なお矛盾が残る場合

§1 の表と既存期待値がまだ両立しないものがあれば、**その 1 件だけを保留して他を全部直し**、
報告に「保留した期待値と、両立しない理由」を書くこと。
**全体を止めないこと。** 2 回連続で成果物ゼロになっており、これ以上は wave が進まない。

## 4. 変異事前登録 (追補 1 の m26 / m27 / m28 を置き換える)

| ID | 変異 | 期待 | 単一理由性 |
|---|---|---|---|
| m26 | packed の下界を pack mtime + 期限として `determinate` にする | KILLED | packed fixture の `deadline_status` と `loss_possible_not_before` |
| m27 | §1 の `indeterminate` 事由を `conservative-floor` へ倒す | KILLED | storage 分類不能 fixture で rc=2 を要求 |
| m28 | `conservative-floor` を rc=2 にする | KILLED | packed fixture で rc=0 を要求 |
| m29 | alternate-only を `determinate` にする | KILLED | alternate fixture の `lower_bound_basis` |
| m30 | `gc.pruneExpire = never` を `conservative-floor` へ倒す | KILLED | never fixture |

| ID | 正例 | 期待 |
|---|---|---|
| p07 | packed commit を含む非空閉包 | rc=0、`conservative-floor`、下界 = assessment time |
| p08 | prunable worktree root を持つ非空閉包 | rc=0、root の `classification == "time-limited"` |
| p09 | alternate-only commit | rc=0、`conservative-floor`、外部 ODB が分かる `lower_bound_basis` |
