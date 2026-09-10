# [T-316] build admission — dev-wave 逐語 (2026-08-02)

D125 の根拠になった相談・レビューの逐語。正本は `docs/decisions.md` の D125 と
`docs/worklog.md` の該当エントリで、本ディレクトリは一次資料を凍結するだけである。

| ファイル | 段 | 内容 |
|---|---|---|
| `s1-brief.md` | 1 | 親 brief。前提実測 7 件と provisional 裁定 (P1)〜(P4) |
| `s2-plan.md` | 2 | codex プラン起草 (read-only)。択一 3 案の file:line 実装計画 |
| `s3-lens-a-acceptance-set.md` | 3 | 敵対レンズ A — 受理集合と恒真な保証 |
| `s3-lens-b-scope.md` | 3 | 敵対レンズ B — 実効性・scope・層の取り残し (NO-GO) |
| `s3-lens-c-threat-model.md` | 3 | 敵対レンズ C — 脅威モデルの妥当性 (NO-GO) |
| `s4-ruling.md` | 4 | 親の裁定・plan v2・変異事前登録 |
| `s5-author-report.md` | 5 | 実装子の完了報告 |
| `s6-review-1-teeth.md` | 6 | 敵対レビュー 1 — gate は歯を持つか (F1〜F7) |
| `s6-review-2-regression.md` | 6 | 敵対レビュー 2 — 回帰・consumer 閉包 |
| `s6-fix-report.md` | 6 | fix の所見別 closed / partial / out-of-scope 対応表 |

## この wave が閉じたことと閉じていないこと

閉じた: 分類されていない source の build を materializer (`buildcache.build` / `build_v2`)、
`pipeline.evaluate()`、`loop.run_campaign()` の 3 層で既定拒否した。`CODER_DERIVED` は
driver CLI の明示 opt-in が要る。

閉じていない (主張しない): provenance は caller の自己申告であり source bytes から導出していない
([T-329])。admission は cache preimage・completion manifest・campaign preimage に入っておらず、
別 class の run から過去の `CODER_DERIVED` binary を cache hit で再利用できる ([T-330])。
既存 artifact は再分類していない ([T-331])。意味 gate (DSL/IR) と sandbox は本 wave の射程外。

## 段 3 レンズ A の初回失敗

レンズ A の初回投入は上流の安全分類器に拒否された (rc=1、出力 0 byte)。原因は prompt が
「gate を迂回する payload 文字列を具体的に書け」と exploit 構築を求めたことである。
攻撃コードを書かせず「どの構文クラスが現行のどの拒否分岐にも該当しないか」を分岐 file:line と
対応付けて列挙させる形へ書き直して再投入し、rc=0 で成立した (本ディレクトリの逐語は再投入版)。
