---
schema: izanagi-spool-v1
ledger: decisions
authored: 2026-09-16
wave: dev-wave-t2559-accept-floor
seq: 2
---

## {{D:accept-floor-is-shard0-t080}}. 受入短縮の対象を shard-0 の t080 e2e へ実測で改める

**決定:** 受入全走で 5 分上限を超えているのは **shard-0 だけ**であり、その床は
`orchestrator/tests/test_s8b_oracle_driver.py` の t080 e2e 群であると記録する。
D1918 が定めた「最遅 shard は shard-2、床は xdist group `p3-b4-material-report`」は
**2026-09-16 時点で失効している**。以後の受入短縮タスクはこの対象を起点にする。

**理由:**

- 2026-09-16 の直近 7 走の `junit.xml` の `testsuite time` 中央値は shard-0 = 325.5 秒、
  shard-1 = 229.8 秒、shard-2 = 236.6 秒である。300 秒を超えるのは shard-0 だけだった。
- shard-0 の内訳 (中央値) は pre 約 65 秒 + disp 29.6 秒 + test span 231.0 秒で、
  span と最長単体 node (222.51 秒) の差は 8.49 秒しかない。**span は最長 node で決まっている。**
- `p3-b4-material-report` group は現在 shard-1 の最忙 worker (169.5 秒) であり、最遅ではない。
- t080 系 38 node の所要総和は 2611.1 秒で、shard-0 の node 所要総和の 32% を占める
  (junit の所要は待ちを含むので CPU 時間ではない)。次点の非 t080 node は 161.1 秒である。
- 対象を実測で選ぶことは、受入短縮についての既存のユーザー裁定が明示的に求めている。

**却下した選択肢:**

- D1918 の記述をそのまま使う — 一次資料が最遅 shard の identity の変化を示している。
- 最長 node 1 本だけを名指しする — 200〜222 秒の t080 が 10 本並んでおり、1 本を消しても
  次の t080 が床になる。D1714 が同型の誤りを既に否定している。

## {{D:t080-fixture-index-speedup-not-now}}. t080 fixture の index 化高速案は現時点で採らない

**決定:** t080 e2e の base 構築を速くする 3 案 —
(A) 複製する git 可視 output を固定 whitelist へ限定する、
(B) 実 repo の object store 全体を alternates で借りる、
(C) 必要 blob だけを fixture 内へ移送して独立 index を組む —
を**いずれも採らない**。意味を変えない圧縮設定の変更も採らない。

**理由:**

- **(A) は受理集合を変える。** 非除外 output の任意の可視 file に三軸 conjunction が入ると、
  現行は fixture へ複製され発行 subprocess の production scan が拒否する。whitelist はこの拒否経路を
  消す。既存の未知性負例は fixture 作成**後**に root 直下へ file を置く形なので、この脱落を検出しない。
  known-axes 側にも同型がある (glob に一致する追加候補を隠すと複数候補拒否が消える)。規律 2 に反する。
- **(B) は観測を変え、既存 assert が検出しない。** 実 repo にあり fixture に無い recorded commit が
  alternates 経由で見えると、ancestry が `missing-commit` から `not-ancestor` へ変わりうる。
  report の独立検算は 17 observation のうち先頭 15 件しか覆わず、report と verifier は同じ
  object store を見るため一致してしまう。貸出元の prune で借り手が object を失う risk もある。
- **(C) は効果の符号が未確認である。** 親の実測では、現行 `git add -A` の 79.33〜191.30 秒に対し
  既存 blob OID の `update-index --index-info` は 0.03〜0.04 秒 + `write-tree` 0.60 秒 +
  `commit-tree` 0.01 秒だった。しかしこの下限は実 repo の object store を fixture へ見せることで
  成立しており、(B) と同じ問題を持つ。自己完結化には 660 MB の pack 化が要り、削減分を食う見込みで
  ある (未測定)。効果を先に測り未確認のまま実装しないという既存のユーザー裁定に従う。
- **圧縮設定は意味不変だが時間効果が確認できない。** `core.compression=0` と
  `+core.looseCompression=0` は 3 方式とも tree OID が同一だったが、所要は round 1 で +2.99 /
  +18.68 秒、round 2 で −18.81 / −19.30 秒と符号が反転した。
- **login node の単発測定は根拠にならない。** 同一内容の `output/` 複製が 20.64〜571.40 秒 (28 倍) に
  振れた。受入高速化の判断に使う測定は、同一 tree 内で方式を交互に測った対比較に限る。
- **(C) を採っても成長比例は断てない。** 全件列挙・全件配置・全件 scan・base→test コピーが残る。
  係数削減であって、件数依存を除く変更ではない。

**却下した選択肢:**

- 効果未確認のまま (C) を land する — 受入全走は共有資源であり、単発 A/B では目標の 25.5 秒を
  走間変動から分離できない (同日 n=103 の代表 node 分布は幅 283.9 秒、中央値から最小への
  自然変動だけで 29.0 秒ある)。
- テストを削除・保留登録して速くする — D747 と、保留を既定の答えにしないというユーザー裁定に反する。
- 「成長比例を断った」と記録する — どの案も全件処理を残すので事実に反する。
