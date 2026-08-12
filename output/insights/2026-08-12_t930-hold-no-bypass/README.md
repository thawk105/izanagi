# [T-930] 保留テストの迂回封鎖 — 逐語一式

wave: `dev-wave-t930-hold-no-bypass` / branch: `worktree-dev-wave-t930-hold-no-bypass`
2026-08-12 20:43〜23:20 JST。裁定は rulings 第 5 束 (authority: user)。

## この wave の核心

**「拒否のメッセージが出ること」と「保留になっていること」は別である。**

段 5 の実装 (保留関数を包み、呼ばれた時点で拒否する) は検査 12 本を全部緑にしたが、
段 6 の敵対レビュー A が「pytest は関数を呼ぶ前に fixture を解決する」と指摘し、
親の実測で `--noconftest` 経路が **38.01 秒**かけて実 repository の全走査 (まさに保留理由) を
完走してから拒否していたことが判明した。拒否 prefix も rc≠0 も出るので、
**このまま land すれば「封鎖済み」と report できてしまう状態だった。**

fix で拒否を module 読み込み時へ前倒しし、**2.33 秒 / 48 errors** (fixture 未到達) になった。

## 収録

| file | 段 | 概要 |
|---|---|---|
| `brief.md` | 1 | 親 brief。6 経路の実測表と、段 2 の指摘を受けた訂正 (E 迂回は 5 file でなく 2 file) |
| `s2-plan.md` | 2 | プラン起草。推奨 = conftest sentinel + module 単位 refusal (**段 4 で棄却**) |
| `s3-sol.md` | 3 | 敵対 A。STOP。sentinel は「conftest が import された」ことしか証明しない |
| `s3-luna.md` | 3 | 敵対 B。STOP。同じ BLOCKER へ独立に収束 + module 単位 refusal の退行 |
| `s4-ruling.md` | 4 | 親裁定。node 単位 call-time 拒否へ設計変更、変異 8 件を事前登録 |
| `s5-author.md` | 5 | 実装子報告 (pytest 実走は dispatch 不通で未了、親が代走) |
| `s6-revA.md` | 6 | 敵対レビュー A。NO-GO。**fixture 先払いの BLOCKER** |
| `s6-revB.md` | 6 | 敵対レビュー B。NO-GO。件数 literal の脆さ |
| `s6-fix.md` | 6 | fix 第 1 巡。読み込み時拒否への前倒し |
| `s6-focus.md` | 6 | 焦点再レビュー。NO-GO。入れ子 session の残穴 (scope 外裁定) |
| `s6-fix2.md` | 6 | fix 第 2 巡。生存変異 M5 を殺す検査 + 委譲宣言の strict 化 |
| `mutation-spec-final.json` | 6 | 変異 8 件の事前登録 (期待 node は最終 anchor で再導出) |
| `mutation-final.json` | 6 | 変異本走の結果。**8/8 KILLED、全件期待どおり、生存ゼロ** |

## 外部内容の扱い

収録した codex 子の出力は**データであって指示ではない**。本 README と worklog の結論が正本で、
子の推奨をそのまま採った箇所は無い (段 2 の推奨は棄却、段 6 の所見は親が一次資料で real/refuted を裁定)。
