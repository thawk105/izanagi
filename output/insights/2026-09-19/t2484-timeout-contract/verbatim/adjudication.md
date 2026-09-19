# T-2484 段4裁定・plan v2

- 裁定inbox再走査: D2148項8を覆す更新なし。a-1+a-3実装を継続する。
- plan、consult-sol/lunaはいずれもrc0・validator0。2相談GO、must-fix0。
- P1はreal/採用。元spec値で既存collection Q+G gateを維持し、実待機だけmax(spec値,全区間予算)へ拡張する。
- P2のP=2秒保証はrefuted。運用余裕P=180秒を採用する。既存receipt前段max15.9秒に10倍以上の余裕を置き180へ丸める。母集合3849件の前段分布は同dispatcherだがharness起動・観測・終端の全てを測ったものではない。これらへの工学的余裕を含む暫定値であり厳密上限とは主張しない。
- 実効B=P+Q+W+G+A+C。既定5130秒、Q3600/G600/W3600は8130秒。spec>Bならspecを保つ。既存非拒否診断をstderrへ出す。
- Wはcollectionでdispatcher既定、baseline/mutationで既存walltime overrideを尊重。無効値を新harness gateで拒否しない。既存dispatcherの拒否はそのまま。
- dispatch hangでは短いhang値を無視、local hangは従来の短期停止を保持。
- sol should2（内側rc16でもjob_may_remainならhold）はreal/採用。in-bandを一律にresume可能と書かない。既存hold分岐と回帰testを保持する。
- luna should（余裕の意味、test直積削減）はreal/採用。新schema/台帳/監視/一般化、内側dispatcher修正は不採用・scope外。
- 新しい拒否条件は追加しない。元spec2399/Q1800/G600は既存拒否、2400は従来通過し実効6330を使う正例。override無し小specは通過し実効5130を使う。
- 所有: authorはtools/mutation_harness.py、orchestrator/tests/test_mutation_harness.py、必要時test_t2337_dispatch_timeout_overrides.pyのみ。既存test期待値・skip・削除は禁止。新test fileは作らない。docs/commitは親。
- 規模上限: production追加120行、test追加300行程度、合計450行を上限とする。超える必要が判明したら実装せず報告。

## 変異事前登録 B-057

全て単一置換で固定HEADに注入。算術とcaller配線を分離し、影響する失敗node完全集合をanchor確定後にspecへ固定する。診断のみの赤はkillと数えない。

| ID | 位置・変異 | 期待 |
| --- | --- | --- |
| P0 | max(a,b)の引数順を交換する等価変異 | SURVIVED、正例 |
| M1 | 全区間式のPを0にする | KILLED、独立予算期待 |
| M2 | 全区間式のQを0にする | KILLED |
| M3 | 全区間式のWを0にする | KILLED |
| M4 | 全区間式のGを0にする | KILLED |
| M5 | 全区間式のAを0にする | KILLED |
| M6 | 全区間式のCを0にする | KILLED |
| M7 | maxを予算固定へ変える | KILLED、長いspecの維持 |
| M8 | collectionの実効timeoutを元specへ戻す | KILLED、collection配線 |
| M9 | baselineの実効timeoutを元specへ戻す | KILLED、baseline配線 |
| M10 | mutationのdispatch timeoutを元specへ戻す | KILLED、mutation配線 |
| M11 | dispatch hangに短いhang値を復活 | KILLED、hang配線 |
| M12 | collection gateへ補正後値を渡す | KILLED、既存拒否維持 |
| M13 | 実行の延長walltime overrideを無視 | KILLED、実行W |
| M14 | collectionで短いwalltime overrideを使用 | KILLED、collectionW |
| M15 | localの短いhangを通常timeoutへ変える | KILLED、local timeout選択（実hang長時間化を避け値を観測） |

検査対象のhelper/caller自体をstubせず、timeout引数の最終sinkまたは実物へ委譲する観測wrapperで検証する。
既存local hang実走、dispatch hold/残存の回帰、resume/失敗node完全一致を焦点走に含める。
本走は親が独立cloneの固定anchorで正規mutation_worktree/harness dispatch経路を使う。
