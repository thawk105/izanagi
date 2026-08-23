---
schema: izanagi-spool-v1
ledger: decisions
authored: 2026-08-23
wave: dev-wave-acceptance-schedule-order
seq: 2
---

## {{D:acceptance-duration-order}}. 受入全走の work unit を所要降順へ並べ替える

**決定:** collection の最後に work unit を所要降順へ並べ替える。順序だけを変え、収集集合は
1 件も変えない。所要は repo へ commit した `orchestrator/tests/acceptance_duration_ledger.json`
から引く。scheduler class・argv・`pytest.ini`・xdist の option は 1 つも変えない。

実装は次の 8 点を満たす。

1. 並べ替えは既存 collection wrapper の post-yield で行う。xdist の worker 側 hook が
   nodeid へ `@group` を付けた後の最終 nodeid を見る。
2. work unit の切り出しは `LoadGroupScheduling._split_scope` と exact 一致させる
   (`nodeid.rfind("@") > nodeid.rfind("]")` の guard を含む)。
3. **未知 unit の擬似 cost は「この collection で既知な unit の cost 降順の第 96 位」。**
   96 は 48 worker x 2 = `schedule()` の初期同期配布の窓である。
4. tie-break は元の unit index。unit 内の相対順は保つ。
5. 台帳が不在・破損・上限 (16 MiB) 超過・部分欠落・読取不能でも順序の質だけが落ちる。
   既知 0 件なら完全 no-op。台帳を選択・skip・予算・受理判定の入力にしない。
6. 発火は loadgroup 走に限る。worker では xdist が `config.option.dist` を `"no"` へ
   書き換えるので `config.getvalue("loadgroup")` で判定する。
   早期停止 (`-x`/`--maxfail`/stepwise)、明示 order (`--ff`/`--nf`/`--lf`)、
   非実行 flag、`--trace`、`--no-loadscope-reorder` のある走では並べ替えない。
7. 台帳は controller が 1 度だけ読み `workerinput` で配る。worker は file を再読しない。
   controller が読まない走では key を配らず、worker は key の不在を「台帳なし」として受理する。
   **並べ替えが有効な worker で key が無い場合だけ** fail-closed で拒否する。
8. identity 検査は `assert` ではなく明示拒否 (`python -O` で消えないため)。

**理由:**

- `LoadScopeScheduling.schedule()` は collection 順の `OrderedDict` を workqueue にし
  `popitem(last=False)` で FIFO 消費する。**collection の順序がそのまま投入順**である。
- 前 wave の一次資料で xdist の割当を event driven に再現したところ、実既定
  (件数降順の安定 sort + `_reschedule` の先取り緩衝) が 155.3 秒、所要降順が 111.8 秒だった。
  **差 43.5 秒**は固定 duration 上の反実仮想であり、実測 wall の予測ではない。
- **利得は「重い unit が先頭 96 の同期配布窓に入る」ことに依存する。** それ以降は worker が
  非同期に取りに来るため、重い unit が窓の外にあると 1 台が連続で抱え込む
  (実測で 1 worker が 81.7 + 60.2 + 60.2 = 202 秒を直列に抱え、最速 worker は 109.5 秒で遊んだ)。
  未知既定を先頭寄せにするとまさにこれが起きる。第 96 位案は欠落 1.3% で 111.8 秒、
  先頭案は 166.2 秒だった。
- 値の精度は要らない。各 unit の所要が `2^(-2..2)` 倍ずれても makespan は変わらない。
  **要るのは順位だけ**なので、台帳は毎走更新しなくてよい (欠落 10% でも 111.9 秒)。
- 台帳が空・読めない場合の下限は「現状維持」である。

**却下した選択肢:**

- **custom scheduler** — D390 / D393 が実効 scheduler を exact 型 `LoadGroupScheduling` に
  束縛しており、受入 receipt が拒否する。collection 並べ替えが唯一の経路である。
- **`config.option.loadscopereorder` の無効化** — 不要。collection を所要降順にすれば、
  後段の件数安定 sort を通しても同じ 111.8 秒になる (差 0.0 秒)。
  現在の複数 item unit が 3 個 (103.0 / 103.0 / 14.9 秒) で、件数上位と所要上位が一致するため。
  **この等価性は group 構成に依存する**ので、実装は後段 sort に耐えることを前提に置く。
- **file 粒度の unit** — 最大 file が 420.8 秒あり、makespan の床が上がって逆効果。
- **低価値テストの削除** — {{D:acceptance-test-deletion-null}} を参照。
- **shard 分割** — 前 wave が queue 待ちで総所要が負けると実測済み。

**保証しないこと:** 順序を変えれば、順序依存のテストは緑と赤が入れ替わりうる。
ただし**順序非依存は本 repo の受入が既に要求している前提**である
(`-n 48` で 48 worker へ任意に散らされ、xdist 自身も既定で件数降順に並べ替えている)。
本 wave はその前提をより強く踏む。潜在的な順序依存があれば受入全走が赤になって露見する。

## {{D:acceptance-test-deletion-null}}. 受入の高速化手段としてテスト削除を採らない

**決定:** 「価値の低いテストを削除して受入を速くする」は採らない。削除 0 件で閉じる。

**理由 (すべて 1 走 14467 件 / 直列総和 5364.9 秒の実測):**

- 所要 0.01 秒未満が **7750 件で合計 15.1 秒**。48 並列の wall 換算で 0.31 秒。
  **全テストの 54% を消しても wall は 0.3 秒しか縮まない。** 中央値は 0.005 秒である。
- {{D:acceptance-duration-order}} を入れると makespan が work 下界と一致するので、
  **削減した直列秒数の 1/48 しか wall に効かない。**
- 床がある。排他鎖 `s8c-preregistration-candidate` が 102.98 秒なので、
  直列総和が 4943 秒 (= 48 x 102.98) を下回ると鎖が律速になる。現在 5364.9 秒なので
  **削減で得られる余地は最大でも 422 秒 = wall 8.8 秒**である。
- 高コスト側を実ファイルで確認したが、削除できるものは 1 件もなかった。すべて
  「同じ前置きを何度も払っている」型で、正しい対処は削除ではなく共有化である。

**限界:** この結論は**テストの実行 work についてだけ**成立する。各 ungrouped test は
1 work unit でもあるので、削除は unit 送信・`worker_collection.index()`・完了 event・
`_pending_of` の再走査・collection 処理も減らす。これらは 15.1 秒に含まれておらず、
未解明の残余 61.3 秒の一部でありうる。**「安いテストを減らしても wall に効かない」は未証明**である。

**却下した選択肢:**

- 所要だけで削除候補を決める — subsume を証明できない削除は検出力を落とす。
- parametrize 族 (総 work の 30.5%、1175 族) の一括削減 — 本 wave の scope 外。
  batch 化・fixture 共有・真の subsume 調査として別途起票する。
