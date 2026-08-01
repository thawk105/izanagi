authority: none
default_effect: no-state-change

# T-126 qualification-first — focused re-review 3 裁定

## 判定

NO-GO。focused re-review 3 は exit 0、output validator rc=0 で完了したが、成果物 validity、
retry authority、crash closure に直接影響する反例 4 件を残した。親が該当する producer /
consumer / recovery 経路を再読し、4 件をすべて real と裁定する。

review 正本:

- `.codex/dev-wave-t126-qualification-jobs/s6-focused-review3-resume2/output.md`
- SHA-256:
  `ac6f3a7fb95ab5de97dbe9f70159c505c5ed86888351beea3325a7a179f35552`

## real finding

| ID | 裁定 | 成果物影響 / 次 wave の最小境界 |
|---|---|---|
| FR3-1 | real / HIGH | qsub 非 0 後に cancelled intent を再 claim すると、旧 `qsub.stdout` を `qsub.rc` 非 0 のまま bind できる。failed stdout を再利用せず、rc=0 の durable record または bind 前の exact scheduler proof だけを authority にする。 |
| FR3-2 | real / BLOCKER | job-result publisher の hard crash は `.create-*` を残すが、job trap は再実行せず collector は staging を一律拒否するため、scheduler terminal 後も final / failure のどちらにも閉じない。collector 単独で exact staging を回収・破棄して閉じる fixture が必要。 |
| FR3-3 | real / BLOCKER | canonical RC30 job-result が実在しても receipt の pointer を null にすれば canonical byte比較を迂回し、accounting / receipt / ledger を RC34 へ coherent rehashして retry authority を得られる。normal submission は canonical pointer と exact bytes を必須にする。 |
| FR3-4 | real / BLOCKER | terminal publisher が committed scratch でなく persistent worktree の `qualification.atomic_publish` を importする。submit 後の通常編集が未記録実行 bytes になり、import failure は job-result 不在の closure holeを作る。early trapを含め persistent import をゼロにする。 |

full / related suite の green は上記を refute しない。4 件の fixture が未収載であること自体が検出力の
不足であり、review が示した静的到達経路と矛盾しない。

## 3 巡上限と停止

`DW-O16` の fix / focused re-review は 3 巡を消費済みなので、第 4 fix は投じない。
`DW-O19` の mutation 本走は integrated commit 後に限られる一方、本 NO-GO は commit gate を
満たさない。したがって rejected dirty tree を commit して mutation を作る迂回はせず、既登録
M1〜M7 の本走、live qsub、collector、段 7〜9へ進まない。

pre-commit の計算ノード受入は、同一 patch SHA
`0febe2a7e5b8140db60bf34a92daf536145c8d8e3f46b4b9fbbd85fa5280af7a` に対して次だった。

- full: `3556 passed, 19 skipped`
- related: `578 passed, 9 skipped`
- bash / Codex agent / docs / diff / duplicate-key JSON checks: rc=0

これらは regression baseline として次 wave に渡すが、4 finding を閉じた証拠には数えない。

## 次 wave

新しい context の `$dev-wave T-126` で、上記 4 件だけを brief の must-fix として再開する。
latest main との実装重複は `tools/pegasus/policy.json` の T-139 設定だけなので、T-126 envelope と
T-139 `silo_ladder_rung1` の双方を保持する。4 件を閉じ、敵対 review、commit 後 mutation、
計算ノード受入、live qualification receipt が揃うまで production activation と T-126 完了を
主張しない。
