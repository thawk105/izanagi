# [T-1279] 層 3 材料レポートの生成元版 fallback — wave 記録

2026-08-17 JST / branch `worktree-dev-wave-t1279-layer3-head-outside-repo` / base = main `699c9cae`

ユーザー裁定 (2026-08-17 /rulings 全件 第 5 回、「厳密化しない」) の実装。
**repo 外 campaign でも失敗しない形にすることだけを要求し、値は campaign lock が束縛する既存 pin を
そのまま使ってよい。official 経路の受理集合を緩める向きへは進めない。**

## 何が壊れていたか

層 3 材料レポートの `meta.generated_from_head` は、呼び手が値を渡さないとき
campaign directory に対して `git rev-parse HEAD` を実行していた。8c 探索の build cell は
この経路を必ず通る。探索用 output root を repo 外へ置いた構成では、campaign の祖先に
git repository が無いことが機械的に強制されるため、この呼び出しは rc=128 で必ず失敗し、
レポート生成そのものが倒れていた。

## 成果物

| file | 内容 |
|---|---|
| `brief.md` | 段 1 brief。scope、不変条件、前提実測、provisional 裁定 (P1)-(P3)。 |
| `s4-adjudication.md` | 段 4 裁定。P1 の撤回、プラン v2、変異事前登録 M-1〜M-6。 |
| `s6-fix-ruling.md` | 段 6 レビュー裁定。must-fix 4 件、scope 外 2 件、親 brief の訂正。 |
| `verbatim/s2-plan.md` | 段 2 プラン (codex plan, reasoning=max)。P1 を反証した。 |
| `verbatim/s5-author.md` | 段 5 実装子の完了報告。 |
| `verbatim/s6-review-a.md` | 段 6 敵対レビュー A (正しさ境界と受理集合)。must-fix 3 件。 |
| `verbatim/s6-review-b.md` | 段 6 敵対レビュー B (検出力と整合)。must-fix 6 件。 |
| `verbatim/s6-fix1.md` | 段 6 fix 1 巡目 (certifying 入口の固定、fixture の pin 分離)。 |
| `verbatim/s6-fix2.md` | 段 6 fix 2 巡目 (前提 assert の書き換え)。 |
| `verbatim/s6-focus-review.md` | 段 6 焦点再レビュー。所見対応表、must-fix ゼロ。 |
| `mutation/mutation-spec-probe.json` | 変異 spec (probe、全件 SURVIVED 期待)。 |
| `mutation/mutation-result-probe.json` | probe 結果。8 変異すべてが赤を出し、観測 node を得た。 |
| `mutation/mutation-spec.json` | 本走 spec。期待 node は probe 観測から再導出した完全集合。 |
| `mutation/mutation-ledger.json` | **本走結果。baseline PASSED、8/8 KILLED、正例 1 SURVIVED、MISMATCH 0、TIMEOUT 0。** |

## 解決順 (確定形)

```
generated_from_head =
  1. 呼び手の明示引数            (あれば無変更で使う)
  2. campaign directory の git HEAD  (取れればこれ)
  3. campaign が生成器 source repo の外側 かつ lock が authority 付き v2 なら
     その contract_loader_commit
  4. それ以外は fail-closed で送出
```

受領証に束縛された certifying 入口では 3 を使わない。呼び手が値を渡さない場合は生成前に
campaign の git HEAD を要求するので、値も例外型も wave 前と同一である。

## 変異 matrix (本走)

| ID | 変異 | 期待 | 結果 |
|---|---|---|---|
| M01 | 呼び出しを wave 前の直呼びへ戻す | KILLED (焦点 1 + 8c E2E) | KILLED |
| M02 | lock pin を git HEAD より先に見る | KILLED (git 優先 + repo 内 fail-closed) | KILLED |
| M03 | source repo 内外の分岐を落とす | KILLED (repo 内 fail-closed) | KILLED |
| M04 | pin の代わりに環境契約 hash を返す | KILLED (焦点 1 + 8c E2E) | KILLED |
| M05 | authority 無しで零 pin へ退避する | KILLED (v1 fail-closed) | KILLED |
| M06 | 明示引数を無視する | KILLED (明示値優先) | KILLED |
| M07 | pin の代わりに source repo HEAD を返す | KILLED (焦点 1) | KILLED |
| M08 | certifying 入口の固定を外す | KILLED (certifying 拒否) | KILLED |
| M09 | 明示値を等価変換する (正例) | SURVIVED | SURVIVED |

M07 は、fixture の pin が source HEAD と同値だったために当初は生存しうる形だった。
段 6 の fix で pin を source HEAD と分離してから KILLED になっている。

## 親 brief の訂正

brief は「探索 campaign は機械的に必ず repo 外に置かれる」と書いたが、これは過大である。
探索用 output root の環境変数が未設定なら repo 内 `output/` へ落ちる。repo 外強制が働くのは
環境変数を設定した経路だけで、そこでは git 祖先を持つ path が機械的に拒否される。
両レビューが独立に反証した。修正の方向は変わらない。

## 環境由来の偽赤 1 件

段 6 fix 1 巡目は「祖先に `.git` が 1 つも無いこと」を前提 assert にしたが、この機械には
`/tmp/.git` という空 directory が残っており、pytest の一時 directory がその配下になるため
3 node が赤になった。空なので git repository としては無効で、レポート生成側の挙動は変わらない。
前提を「実際に git HEAD を取得できないこと」へ書き換えて解消した。
