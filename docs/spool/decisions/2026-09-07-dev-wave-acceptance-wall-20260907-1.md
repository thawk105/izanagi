---
schema: izanagi-spool-v1
ledger: decisions
authored: 2026-09-07
wave: dev-wave-acceptance-wall-20260907
seq: 1
---

## {{D:acceptance-wall-decomposition}}. 受入 wall は「最忙 worker のテスト実行時間 + 残差」で分解し、残差を collection と同一視しない

**決定:** 受入全走の所要を論じるときの分解は
`wall(shard) = 最忙 worker の TestReport duration 合計 + 残差` とする。
値は `report.json` の `worker_occupancy[gwN].duration_s` と junit の `testsuite@time` を
join して取る。**残差を collection の所要と同一視しない。**
残差には worker 起動、collection、`pytest_runtest_protocol` wrapper の lock 待ち、
scheduler gap、finalization が混ざる。

**理由:**
- `worker_occupancy.duration_s` は `pytest_runtest_logreport` で per-test の
  `report.duration` (setup / call / teardown) を積算したものであり、protocol 外の待ちを含まない。
  この定義を外して「worker の busy 時間」と読むと、残差の内訳を誤って collection へ帰属させる。
- 直近 3 日 約 77 走の中央値で、残差は shard-1 / shard-2 が 59.0 / 58.6 秒とほぼ一定、
  shard-0 だけ 102.0 秒だった。**一定でない以上、単一の固定費として扱えない。**
- D531 の「wall = 直列鎖 + 固定費 (約 26 秒)」は 2026-08-18 の値であり、
  固定費はその後 59 秒へ増えている。模型の形は生きているが定数は失効した。

**却下した選択肢:**
- 残差を丸ごと collection と呼ぶ — shard-0 の 102 秒を説明できない。
- `report.json` へ session timeline field を足して内訳を確定する — ユーザー裁定待ちの項目であり、
  独立な 3 者の実測 (48 並列 collection の直接計測、D1420、非 shard 走の対比) で
  collection の寄与は計装なしに述べられた。

## {{D:d711-cost-premise-expired}}. D711 の「固定費 12.86 秒」という費用前提は失効しており、collection 絞り込みの再検討はユーザー裁定に掛ける

**決定:** D711 の禁止 (各 shard が同一の全 collection を行ってから deselect する) は**維持する**。
ただし D711 の理由のうち費用前提は失効したことを記録し、絞り込みの採否は
**gate 2 の弱体化を許すかどうかのユーザー裁定**として返す。親は実装しない。

**理由:**
- D711 は「固定費が実測 12.86 秒しかないので、全 collection を K 回払っても費用はほぼ増えない」を
  理由の 1 つにしていた。現在の固定費は shard あたり約 59 秒で約 4.6 倍である。
- 48 プロセス同時 collection の実測は全 file 87.57 秒、自 shard 絞り込み 27.44 秒。
  D1420 は collection 単体を 51.7 秒と確定しており、別 wave の非 shard 対比でも
  collection/起動が 119 → 56 秒だった。**3 者独立に同じ向きである。**
- D711 のもう 1 つの理由「file を positional target へ渡す形は使えない」は再現した。
  ただし原因は positional target ではなく **collect する file 集合が部分集合であること**である。
  2 つの test file が、他の test module の import 副作用で `sys.path` に載る `orchestrator/` へ
  暗黙依存している。**この 2 file を自己完結させれば直る技術的欠陥であり、原理的な壁ではない。**
- **残る本質的な論点は 1 つ**である。gate 2 (全 shard の `observed_universe` 一致) は
  「collection plugin が file を 1 件落としても全員が同じ縮小集合に同意して緑になる」経路を断つ。
  絞り込みはこの二重化を弱める。これは正しさ防壁の変更であり、親の一存では決めない。

**却下した選択肢:**
- 費用前提が失効したことを理由に親が絞り込みを実装する — gate 2 の射程を変える。
- 費用前提の失効を記録しない — 次の担当者が同じ 3 通りの実測をやり直す。
- `--ignore` で positional target を保つ回避 — 実測で同じ `ModuleNotFoundError` になった。

## {{D:shared-fixture-cache-no-gain-on-simultaneous-miss}}. 消費者が同時に miss する fixture は、worker 跨ぎ共有では速くならない

**決定:** 高価な test fixture を worker 跨ぎで共有する案は、**消費者が時間的に散っている**ことを
先に示せた場合だけ採る。同時に miss する集合に対しては採らない。

**理由:**
- 同時 miss では、共有は「構築 B 秒」を「lock 待ち B 秒」へ置き換えるだけである。
  待ちは test の `call` 所要に計上されるので、wall も所要総和も動かない。
- `xdist` の LPT は所要の長い node を最初に固めて配るため、重い fixture の消費者は
  **構造的に同時 miss する**。
- t080 base (構築 70 秒 / 本体 4 秒 / 11 node) で実装して同一 command の A/B を行った結果、
  wall 99.80 → 98.92 秒、所要総和 909.6 → 932.6 秒で改善しなかった。
  実装は正しく動いており (fail-closed 2 分岐を repo 外 probe で確認)、
  効果が出ないのは構造的な理由である。
- 別 wave が grouping で得た「変化なし」も同じ構造で説明できる。寄せると 1 worker が
  直列に背負うだけで最忙 worker が改善しないためである。
- process 内 cache が既に「同一 worker 内の再利用」を賄っているので、worker 数を下げても差は出ない。

**却下した選択肢:**
- 効果を示せないまま共有 cache を land する — 規律 5 と成果物影響の要求に反する。
- 所要総和を効果指標にする — 待ち時間が計上されるため、構築回数の削減を検出できない。
- worker 数を下げて散らす — process 内 cache と同じ効果しか出ず、並列度を捨てる。

**次の一手として残す形:** base を collection 中に組む (prewarm)。固定費の窓に構築を重ねれば
test 段から消える。lock 待ちにならないのは test 開始前に完了しているからである。

## {{D:no-accept-set-widening-for-sub-percent-gain}}. wall の 0.1% のために受理集合を形式的にでも広げない

**決定:** 受入 gate の受理集合を広げうる変更は、**wall への効果が走間ばらつきを超える**ことを
示せた場合だけ採る。示せない場合は効果の大小によらず採らない。

**理由:**
- `tools/acceptance_shards.py` の collection hook で `_canonical_item` を 2 回から 1 回へ
  減らす変更を実装したが、旧測定では hook 全体が 0.375 秒であり効果は約 0.4 秒 = wall の 0.1% だった。
- 段 6 の敵対レビューが、この変更は「アクセスごとに値を変える Item に対する二時点検査」を
  失わせ、形式的に受理集合を広げると指摘した。現 repo に custom Item は無く悪用不能だが、
  0.1% の対価としては見合わない。
- 同レビューは、その変更に付けた回帰検査が (a) 両辺で同じ現行 renderer を呼ぶ恒真形であり、
  (b) worker から controller への本番集約経路を通らないことも指摘した。
  **証拠の質が担保できない変更を、効果の裏づけ無しに残さない。**

**却下した選択肢:**
- 検査を作り直して変更を残す — 0.4 秒のために検査 2 本を足すことになる。
- 悪用不能を理由にそのまま land する — 受理集合の向きの変更は効果で正当化する。
