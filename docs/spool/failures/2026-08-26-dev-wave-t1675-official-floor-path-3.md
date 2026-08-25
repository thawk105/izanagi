---
schema: izanagi-spool-v1
ledger: failures
authored: 2026-08-26
wave: dev-wave-t1675-official-floor-path
seq: 3
---

## 新規

### {{F:brief-missed-guard-in-read-docstring}}. 読んだ docstring に書かれていた防壁を、brief の閉塞列挙へ入れ損ねた [手順漏れ]

- 事象: 段 1 brief が床値 official の閉塞を 2 つ (入場鍵の衝突、seam 分類) と列挙したが、
  実際は 4 つあった。落としたのは
  (a) `orchestrator/campaign/s8b_floor_campaign.py` の `_assert_official_permitted` による
  core の無条件拒否と、(b) `output/s8b-freeze-budget-approvals/g1.json` の不在である。
  段 3 の敵対相談 2 本が独立に両方を指摘し、親が一次資料で確認して real と裁定した。
- 根本原因: 親は同 module の docstring
  「official mode の無条件拒否は private core 自体で行い、public wrapper の迂回を許さない」を
  **実際に読んでいた**が、seam と適格性の調査に注意が向いており、閉塞の列挙へ転記しなかった。
  読了と列挙が別の作業であることを踏まえた検査を持っていなかった。
  (b) は「下流が要求する成果物の実在」を確かめる手順が brief に無かったため。
- 恒久対応: memory `enumerate-blockers-by-walking-the-consumer-chain` — 「経路を開く」型の
  brief では、開こうとしている経路の入口から成果物が消費される所まで consumer を 1 段ずつ辿り、
  各段の拒否条件と要求成果物の実在を列挙してから scope を書く。
  拒否文言を grep するだけでは、成果物の不在 (b 型) を見つけられない。
- 再発検知: 「経路を開く」「gate を外す」型の wave の段 3 レンズに、
  「この経路が実際に通るために越える門を全部挙げよ。1 つでも別の理由で止まるなら名指しせよ」を
  必ず含める。本 wave ではこのレンズが実際に 2 件とも検出した。
