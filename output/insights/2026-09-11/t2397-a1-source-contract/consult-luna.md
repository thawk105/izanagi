## 総括

**planの主要な阻害点はrealです。既存materializerでそのまま通せる、という反証は得られませんでした。** ただし「実装自体が不可能」ではなく、**現行の凍結契約とdriver限定scopeを同時に維持したままでは成立しない**、が正確です。

**real — 実buildにも未patch sourceが届く**

- `paper_story_a1_paired.py:7022` の`run_campaign()`は`ccbench_dir`を渡さない。
- `loop.py:351`の既定値は空文字。`buildcache.py:2493`で既定submoduleへ解決し、`:2663`でそのrootをconfigureへ渡す。
- `build_v2()`の任意のmaterialization descriptorは、この呼出しでは未指定。`:3060`付近の通常経路はpatchを生成・適用しない。

したがってbrief P1の「関門を実ビルドと同じpatchへ揃える」は、**実ビルド側へのpatch配線も欠けている**点を落としています。

**real — 既存patch適用とbalanced build検査が衝突する**

`patchharness.py:204`の適用はHEAD・indexを動かさず、tracked差分を作ります。`:247`の`applied()`は、その状態をbody終了まで保持します。

一方、`loop.py:755`のbalanced経路は`canonical_build_pin=cfg.ccbench_commit`を必ず渡します。[pipeline.py:1942](/work/1/SFC/tanab/izanagi/.codex/worktrees/dev-wave-t2397-a1-attempt4/orchestrator/campaign/pipeline.py:1942)は各trace/perf build直前に実際の`ccbench_dir`を検査し、`:1129`でtracked差分を拒否します。**cache hitでも、この検査が先です。**

**refuted — 他driverの既存成功経路をA-1へそのまま一般化できる**

`backoff_sweep.py:437`はstock checkoutと`applied()`を使い、campaign全体をpatch適用下で実行します。しかし`:484`の呼出しにはbalanced scheduleがありません。`loop.py:768`の通常経路は、balanced側のcanonical検査を要求しません。

D1917もこのpatch適用下のsource導出を説明していますが、対象はT-1998です（`docs/decisions.md:57577`）。A-1のstrict-clean契約との両立を証明しません。

**既存裁定の確認**

[D1936項3](/work/1/SFC/tanab/izanagi/.codex/worktrees/dev-wave-t2397-a1-attempt4/docs/decisions.md:58118)はpatch適用後sourceへの配線とattempt-0004を承認済みです。再承認を求める必要はありません。

ただし、同項にはbuild直前のtracked-clean条件をどう扱うかの明示がありません。事前登録`:216`は各build直前を含む5境界でcleanを要求し、`:248`はdirtyを無効条件としています。D1300（`docs/decisions.md:41778`）も、この受理集合を投入器の実装細部として変更しない判断です。**今回追った衝突が既に解決済みとは確認できません。**

**進められる最小配線**

- `paper_story_a1_paired.py:6901`で検証したdependency prefixを`:6993`から関門へ渡す。既存shellの供給は`:1331`、CLI転送は`:1343`。
- `buildcache.py:1922`のconfigure組立に合わせ、arm別flags・compiler・prefixを供給する。`BACKOFF_FIXED`自体は関門のrequested/default/stock生成に任せる。
- 既存checkout＋`applied()`を使い、同じpatched rootを関門とcampaignへ渡す。captureはroot参照なので、`condition_meaning_gate.py:807`のcapture後も評価終了までsourceを保持する。
- T-2514の`:6704`保存処理、`:6819`以降の全record・admission保存、全arm評価と元の拒否を維持する。

**推奨**

親へ返す最小裁定は一件です。**A-1の実build sourceについて、canonical HEADを維持しつつ既存固定patchだけを認可差分として扱う契約へ変更してよいか。** 認可patch以外の差分は拒否し、実sourceとの束縛を維持する案です。これは現行strict-cleanの変更なので、既存検査・事前登録・consumerとの整合を含む明示裁定が必要です。driver限定の修正として隠して実施できません。

別rootへの検査付替え、dirty拒否の削除、patch commitによるpin変更は推奨しません。

**未確認:** 修正後のconfigure・build・verify・attempt-0004の実効性。今回は静的検算のみで、編集・commit・submit・pytestは実施していません。親の196 passed／45.70秒とchecks緑は、実配線の証明には数えていません。