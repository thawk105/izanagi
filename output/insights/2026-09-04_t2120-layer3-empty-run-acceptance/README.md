# [T-2120] 層 3 の空走は受入で既に閉じていた — 実装しないと裁定した wave の一次資料

- 基準 commit: `764fdf202` (local main、wave branch `worktree-dev-wave-t2120-layer3-empty-run-acceptance`)
- 実装面の差分: 0 (docs のみ)。変異 matrix は免除、受入全走は実施 (結果は worklog)
- 裁定の正本: D1460 (受入限定で閉じる、全 verifier へ広げない)。本 wave はこれを覆さない
- 同 dir の逐語: `brief.md` (段 1)、`s2-plan.md` (段 2、codex read-only xhigh)、`s3-sol.md` / `s3-luna.md`
  (段 3、codex read-only xhigh、2 レンズ)、`s4-ruling.md` (段 4)

## 何を確かめたか

D1460 は「producer と standalone verifier に残る層 3 空走について、受入限定で閉じる」と定めた。
worklog の持ち越し項 (entry 1184) はこれを「実装待ち」と記していたが、受入
`assert_trial_registry_acceptance` (`orchestrator/campaign/trial_registry.py:5675`〜) で、層 3 の鎖
`assert_campaign_layer3_chain` が実体 `_fresh_layer3_for_comparison` (実 `layer3_report.build_report`) を
1 度も通らずに受領証発行へ達する report の形は、現行 tree に存在しない。

受入で起こりうる空走 3 形と、それぞれが止まる位置 (file:line は基準 commit の現物):

| 形 | 止まる位置 | 出所 |
|---|---|---|
| campaign 無し失敗 cell (producer の exact fallback) | 鎖は `autonomous_trial_completeness.py:4879-4884` で `continue` するが、受入は鎖の後 `trial_registry.py:6080-6085` で `[campaign-chain] campaignless failure fallback bypassed Layer-3 validation` の hard failure | T-2075 (D1289) が実装、変異 5/5 KILLED |
| campaign 付き admission 失敗 cell (materialized admission failure) | **鎖の前。** 受入が呼ぶ `assert_execution_digest_chain` (`trial_registry.py:5995-6003`) が、registered launch (受入は `trial_registry.py:5825-5840` で launch_admission を登録済み derivation と一致要求) では腕 digest 検査を必須にし、failure decision かつ exact campaignless fallback でない cell を `autonomous_trial_completeness.py:1137-1142` "cell admission failure projection is not exact" で拒否する。producer の failure cell は descriptor / campaign identity / 診断 key を持つため key 集合が fallback と異なり、必ずここで止まる | 段 3 レンズ A の所見 1、親が現物で検算 |
| 致命的 zero-cell (`do_build=True`, `cells=[]`) | measurement-target prepass `trial_registry.py:5557-5561` で `[campaign-chain] do_build=True requires a non-empty report.cells list` | 段 2 plan の brief 補正 |

補助: 全 6 件が campaign-backed build 扱いの束で layer3 report が欠けると、鎖より前の
`trial_registry.py:5632-5648` `[measurement-target] complete build bundle requires exactly 6 readable layer3 reports` が止める。
鎖の後の `trial_registry.py:6086-6094` (persisted report 不在の post-check) は T-2075 が「効いている機構として
数えない」とした位置で、本 wave でもその判断は正しい (到達する安定 artifact が無い)。

## なぜ実装しないか

- 段 2 plan の主案 (鎖が実体検証済み campaign ID を返し、受入が campaign identity 付き build cell 全件との
  一致を要求) も対案 (受入側で failure decision の cell を bypass 扱いにする述語型) も、上表のとおり候補入力が
  鎖の前で拒否されるため**現行の受入では 1 度も発火しない恒真 gate** になる。
- 変更前に受理され変更後に拒否される report の集合は空。受理集合・成果物の値・参照は 1 bit も変わらない。
- 到達不能な gate を足すことは、依頼が scope 外とした「仮想リスク向けの gate・検査の追加」であり、
  DW-G04 (発火条件を満たす既存 artifact を書けない条件付き機能は実装しない) にも当たる。
- 到達させるために手前の腕 digest 検査を緩める・順序を変えることは、producer と standalone verifier が共有する
  verifier の変更になり D1460 の「受入限定」を越える。採らない。

## brief の誤り (段 2 / 段 3 が現物で覆した 3 点)

1. campaign 付き admission 失敗 cell が「鎖まで到達し post-check で止まる」という因果は誤り。鎖の前の
   arm-digest-chain で止まる (上表)。結論 (拒否される) は正しかったが理由が違った。
2. zero-cell の最初の拒否位置は `trial_registry.py:6015-6018` ではなく prepass `:5557-5561`。
3. 「2 production module を bytes で pin」は誤り。`paper_story_a1_paired.py:167-173` の
   `NON_CERTIFYING_SOURCE_RELATIVE_PATHS` に入るのは `trial_registry.py` だけで、方式も固定 digest でなく
   実行時 HEAD の blob OID と working bytes から binding を再生成する live tree 追随型
   (`:4379-4404`、`:7195-7219`、`test_paper_story_a1_job_contract.py:386-409`)。

## 段 3 の集計

- レンズ A (sol、正しさ境界・恒真性): 所見 7、real 5 / refuted 2。最重要は所見 1 (鎖前の拒否)。
- レンズ B (luna、整合・実効性): 所見 8、real 6 / refuted 2。plan の負例 fixture が producer 実在形
  (診断 key、critic count=1、accounting) にならない点 (所見 1) は、所見 A1 の傍証 (key 集合の差) でもある。
  D863 の機械 readiness (C09 evaluator) が本 wave で変わらない点 (所見 7) は scope 外で、別項の所有。
- 両レンズが一致した点: 受理集合は 3 形とも既に閉じている。pin は live tree 追随型。戻り値追加は producer /
  standalone を変えない (実装しないので不要)。

## scope 外として残すもの

- campaign 付き admission 失敗 cell を実際に止めている arm-digest-chain の拒否 message
  "cell admission failure projection is not exact" には、受入・単体いずれのテストも無い
  (`grep -rn "projection is not exact" orchestrator/tests/` は 0 件)。既存機構の被覆追加は本題 (空走の閉鎖)
  と別の変更単位なので、worklog の次の一手へ P3 として残す。

## 編集面重複の実測 (DW-O20 起動時要求)

worktree 70 root を全走査 (unreadable 0)。T-524 wave が `trial_registry.py` を未 commit で編集中だったが、
merge-base `c6a94ec99` 基準の hunk は `+6193,37` / `+6360,6` (commit 済み) と `+6347,2` (未 commit) で、
鎖区間 6021〜6096 は同 base で不変。本 wave は実装面の差分ゼロなので統合対象自体が無い。
