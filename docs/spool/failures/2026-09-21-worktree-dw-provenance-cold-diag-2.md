---
schema: izanagi-spool-v1
ledger: failures
authored: 2026-09-21
wave: worktree-dw-provenance-cold-diag
seq: 2
---

## 再発

### F1

- **再発: 2026-09-21 (near miss、2 件)** — 受領証の再利用診断 wave の親が、(1) checker の版と実装形式 (旧形 / 中間形 / 新形) の対応表を**一次資料から機械で導出せず手で書いて** Codex author の prompt に埋め、probe がそれを忠実に実装した結果、T-2804 枝の 2 版 (`89a60a88…` / `65476daf…`) が新形に分類され、参考母集団 3 件の cause が誤った (親が後から checker の中身を実測して気づき、author 3 巡目で訂正。着地後の母集団の結論は不変)。(2) 同 wave の insight 初稿で「main の checker が変わった回数」を手元の commit 一覧から目で数えて 2 回と書いたが、reflog を読む probe で 3 回だった (T-2804 の land 2026-09-20 23:29:54 を見落とし。段 6 レビューが出所不足として指摘し、probe を 1 本足して訂正)。型はどちらも「一次資料から転写・導出せず手で書く」で 2026-09-20 の再発と同じ。恒久対応は変更なし — **prompt に載せる対応表・分類表は、子が一次資料から導出できる形で渡すか、親が導出した出力 file を射影する** (memory `ruling-literals-in-prompts-point-to-the-file` の族)。

### F75

- **再発: 2026-09-21 (near miss)** — 同 wave の親が、段 1 の前提実測と段 4 後の checker 系統の確認で read-only の診断 script (`.py` 3 本と `.sh` 1 本) を自分で書いて走らせた。repo へは入れず job dir と job tmp に置いたため `check_ai_provenance.py` の実装面契約には触れていないが、`.claude/commands/dev-wave.md` の凍結境界と memory `probe-must-not-enter-repo-without-codex-author` は「実行可能な probe / harness / script は所在を問わず Codex `role=author`」と定めており、判別条件 (2026-08-06 の再発で「親が実行可能ファイルを書くとき常に」へ拡張済み) に照らすと違反である。是正として親 script の出力は仮説に格下げし、確定値・分類・系統表はすべて Codex author が書いた probe 5 本の出力へ置き換え、親 script は `.txt` 逐語として insight に残した。恒久対応は F75 から変更なし。

