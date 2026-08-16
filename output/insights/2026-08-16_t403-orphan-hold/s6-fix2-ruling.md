# 段 6 fix 第 2 巡の裁定 — 焦点再レビューの停止所見

裁定時刻 2026-08-16 16:50 JST。対象 commit = `2f6e1af9`。DW-O16 の 3 巡上限のうち 2 巡目。

## 裁定

| 所見 | 判定 | 処理 |
|---|---|---|
| 二重の hold 書込み失敗後、orphan-stop sidecar が resume の gate にならない | **real・land 阻止** | **must-fix A / B** |
| must-fix 5 の残り (M6・P1a/P1b/P1d/P1e 未登録) | **real・非阻止** | 検証 backlog。worklog の新規項へ既に登録済み |
| fan-out 上位 report の診断不足 | **real・非阻止** | backlog (成果物の値を変えない) |
| docs の断定が強すぎる箇所 | **real** | 親が段 7 で修正する (下記) |
| latch/lock・signal 窓・保護範囲の記述 | **過大主張なし** | 変更しない |

**論拠 (親の判断):** 起きる条件は「孤児条件の成立」かつ「dispatcher と harness の hold 書込みが
同一原因で 2 度失敗」かつ「人間が rc=2 と sidecar を見ずに `--resume` する」の 3 条件で、
通常経路ではない。しかし成立したときの結果は、この wave が防ごうとしているもの
(台帳の記録と実行 bytes の不一致) そのものである。修正は小さく閉じ、既存の受理集合を
広げないので 2 巡目を投じる。

## must-fix A — orphan-stop sidecar を次回起動の fail-closed gate にする

`tools/mutation_harness.py`:

- 起動時 (fresh / `--resume` の**両方**)、`<--out>.orphan-stop.json` が存在するなら
  runner を 1 本も起動せず fail-closed で停止する。存在判定は既存の
  `_path_present_fail_closed` と同じ規律 (不在だけが False、判定不能は成立側)。
- 停止メッセージには sidecar path、`reason.hold_error`、復旧順序 (対象の不在・終端確認 →
  dirty path の復元 → clean/HEAD 確認 → hold と sidecar の手動削除) を出す。
- 自動削除・自動解除は実装しない。**hold file の有無に依存させない** — 二重書込み失敗の経路が
  この gate の存在理由である。
- 既存の hold file による停止経路は変えない。

## must-fix B — wrapper の orphan 分類を sidecar でも成立させる

`tools/mutation_worktree.py`:

- `orphan_hold` の判定を「container 内 hold file が存在する **または** `<--out>.orphan-stop.json`
  が存在する」へ広げる。通常経路と plan-only 例外 fallback の**両方**に適用する。
- これにより sidecar だけの停止でも `failure="orphan-hold"` が receipt に入り、
  復旧順序を先に出す案内が表示される。
- `_should_teardown` の契約は変えない (`orphan_hold` が True なら常に False)。

## 追加する変異事前登録

| id | 変異 | 期待 |
|---|---|---|
| M13 | harness の sidecar 起動 gate を削除 (wave 前の形) | KILLED |
| M14 | wrapper の orphan 分類から sidecar 項を落とす | KILLED |

期待 node は fix 後に `--junitxml` から完全集合を再導出する (DW-M08 / F33)。

## 親が段 7 で直す docs (焦点再レビューの指摘)

`docs/pegasus-runbook.md` §7.6 を次のとおり直す。

1. 「孤児として残る」→「孤児として**残り得る**」。署名は保守側であり false positive を許容する。
2. 「4 経路が fail-closed」と断定せず、hold file が書けなかった場合は sidecar が権威になることを書く。
3. harness が作る hold は `job_name` が null、timeout 経路では `request_id` と `submission_dir` も
   null になり得る。receipt → attempt sidecar → submission inventory の順で照合する。
4. 受入全走中に hold が立つと acceptance receipt は発行されない。受入 lease の解放と
   probe / evidence の掃除は別物である。
5. fan-out の上位 report は hold path・request ID・`hold_error` を転記しないので、
   preserved container から辿る必要がある。
6. dispatcher と harness の両方が hold を書けなかった場合は sidecar の `reason.hold_error` を見る。
   復旧後は hold と sidecar の**両方**を手で削除する。

## 変更しない

- 署名 `job_may_remain is True`、F47 の受理集合と文言、通常 ledger v4 / wrapper receipt v1 /
  dispatch receipt v2 の schema、qdel 経路の本数。
- 既存テストの期待値。
