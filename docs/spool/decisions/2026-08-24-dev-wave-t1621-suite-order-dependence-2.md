---
schema: izanagi-spool-v1
ledger: decisions
authored: 2026-08-24
wave: dev-wave-t1621-suite-order-dependence
seq: 2
---

## {{D:order-dependence-control-uses-grouped-unit-reversal}}. 受入 suite の順序依存の負の対照は grouped work unit 内の反転で行う

**決定:** 受入 suite の順序依存を測る負の対照は、`xdist_group` marker を持つ node の
**work unit 内順序を反転する**方法だけを採る。ungrouped node の対照 (2 件を並べて AB / BA で走らせる形)
は採らない。

対照の妥当性条件を 3 つ置く。

1. **実行順を仮定しない。** 反転したことを junit XML の testcase 出現順で毎回検証し、
   検証できない走は `refuted` でなく `unmeasured` とする。
2. **positive control を必ず添える。** 同じ機構 (同一 group・argv 順・junit 突き合わせ) で、
   一時注入した既知の順序依存が実際に赤になることを示す。示せない負の結果は破棄する。
   一時注入は tracked file の一時変異 + 即時復元とし、復元 bytes を commit の blob と照合する。
3. **surface ごとに `detected` / `refuted` / `unmeasured` / `held-out` を集計する。**
   positive control が成功し `unmeasured` がゼロの surface にだけ否定的主張を限定する。

**理由:**

- D746 の並べ替えは **work unit 単位**である。unit を作り、unit ごとの所要合計で降順に並べ、
  unit 内の item は連続かつ元の相対順のまま展開する。**unit 内の相対順は保存される。**
- `--dist loadgroup` は ungrouped nodeid をそのまま scope 名にするため、ungrouped node は
  1 件 = 1 work unit になる。よって **「unit 内順序」が存在するのは `xdist_group` を持つ node だけ**であり、
  そこだけが D746 に摂動されずに残った面である。
- `tools/run_tests.py` は targeted 走にも既定で loadgroup を付け、受入の並べ替えは全走かどうかを
  見ずに loadgroup なら発火する。**ungrouped な 2 node を argv で逆に並べても、別 unit として
  所要降順へ潰される。** 「逆順で緑」が「同じ順を 2 回測った」でしかなくなる。
  段 3 の敵対 2 レンズが独立にこれを指摘し、親が実装で裏取りした。
- 全 node が同一 group なら work unit が 1 個になるので、argv 順がそのまま実行順になる。
  実測でも 72 node の junit 出現順が argv 順と完全一致した。
- 「全部緑だった」は、その測り方が実在する順序依存を検出できる証明が無ければ、
  検出力ゼロの手続きと区別できない。positive control はその区別を作る唯一の手段である。

**却下した選択肢:**

- **素の collection 順での全走** — 順序を素に戻す option は runner の閉じた許可表に無いため、
  受入形から targeted 形へ黙って降格し、恒久除外と preflight gate まで変わる。差が順序だけでなくなる。
- **scheduler を別の分配方式へ変えた対照** — 受入形では明示的に拒否される。
  targeted 形なら通るが、実 repo 利用 node の排他を失うため対照として不適格である。
- **worker 数を変えた対照** — 分割 topology、資源競合、process 分割が同時に変わり、
  差を順序へ単独帰属できない。login では job 数まで変わる。「実行 topology 感度」であって順序対照ではない。
- **全 suite を別順序で 1 回走らせる診断** — 順序を作る手段が受入面の編集を要し、
  かつ 1 順序あたり全走 1 回分の費用が掛かる。静的に絞った grouped 連鎖の反転より高価で射程も狭い。
- **静的棚卸しだけで閉じる** — 「静的に見つからなかった」を「存在しない」へ滑らせる。
  棚卸しは候補の生成手段であって、実在性の判定手段ではない。
