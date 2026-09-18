# 受入setup阻害の局所修正裁定

## 一次資料と限定

- 受入1: T1259 module fixtureのGit走査30秒timeoutが28件（status10 / ls-files18）。同一tipのfile単独は51 passed。
- 受入2: 同fixtureのls-files timeoutが1件。判定assertionには到達していない。再投入だけで閉じない。
- 独立診断 `codex/t1259-diagnosis.md` は、既存memo集合への30関数追加・独立golden追随・既存suffix helper補強を最小候補としてGO。I/O根因確定やtimeout必解消を意味しない。
- D1877のtimeout延長方針はD1936項43で本件限定変更済み。現行方針は実snapshotをmoduleごと1回とし各testへ独立copy、production timeoutと走査範囲を維持する。groupingで既存module fixtureの共有を同一worker上に保つ修正とする。新しいcacheや共有fixtureを作らない。
- D1008のP/S lock・access分類・marker・shard閉包を変えず、既存のprocess memo例外をこのconsumerへ適用する。T080の速度改善を目的にしたD1260の不採用を再実装せず、full wallの改善やnode秒削減を主張しない。

## 採用する最小範囲

1. conftest.pyのREAL_REPO_PROCESS_MEMO_NODESへ、T1259既存inventoryにある30関数を明示追加。prefix包括登録は禁止。現在の4関数は保持。
2. test_real_repo_serialization.pyの独立goldenへ同じ30関数を明示追加。これは配置契約変更に伴う表の追随であり、値をproduction集合から生成しない。
3. 既存suffix検査helperを独立goldenのmemo node全件に適用し、T1259だけstripする変異も検出する。既存の非memo/local-only対照は残す。

所有は上記2fileのみ。実装子は隔離Codex author。既存goldenへの30関数追加だけを期待値変更の明示範囲とし、他の期待値・timeout・skip/deselect・assertion削除は禁止する。
T1259本文・fixture・probe、real-repo inventory/access map、lock、shard allocator、duration台帳、本番pilotを変更しない。
実repo読取りやsnapshotをstubせず、全51ケースとdeepcopyを残す。所属変更で結果の受理・拒否を変えない。

## 変異事前登録（編集前）

- P: 無変異でT1259全51ケース、既存metaのcollection/lock/shard/suffix対照が通る。
- M9: memo集合だけからT1259の代表1関数を除く。独立golden一致で登録漏れを検出。既存inventory側を変えない。
- M10: memo集合は保ったまま、T1259だけsuffixをstripする条件へ変異。既存suffix helperの全memo検査で配置契約の破れを検出。
- E: conftestの該当説明コメントだけの等価変異は生存。

位置・期待nodeはauthorの差分から一意性を照合して本走前に固定する。判定はscheduler配置契約の感度であり、verifierのcorrectness killではない。元のM1〜M8の結果は対象pilot bytes不変を確認して保持する。
新helperの検出増分は旧helperでは見なかったT1259への実suffix変異で確認する。新規gate・台帳・一般化は追加しない。

### 正式走前の検出帰属補足

- M9はgolden一致が先に拒否し、その後のsuffix検査も同じ登録漏れを検出し得る。冗長な登録・配置検査として記録し、単一理由の独立kill証拠には数えない。
- M10は集合/goldenを維持して実suffix処理だけを変えるため、新helperの配置検出を確かめる主対照とする。
- 旧helper対照: M10と同時にhelperのmemo部分だけを変更前HEADの代表1関数検査へ戻し、SURVIVEDを期待する。golden34件と非memo/local-only対照は保持する。これは新旧検出増分の診断用変異で、採用するコードではない。両層変異として本走前に追加登録する。

## 逐語の既裁定

### D1936 項43 — 受入の実repo重複走査をmodule単位へ減らす

対象: T-2579。

**決定:** D1877の共有範囲固定・timeout延長方針を本件に限って変更し、実repo走査をmoduleごと1回へ減らして各testへ独立copyを渡す。未land案の既存real-repo inventory等への登録を使い、production timeoutと走査範囲は維持する。

**理由・採らない案:** 51回の取得直後にtest用値へ上書きしており重複走査に検査力が無い。取得処理がsiteを読まないので追加のsite偽装は課さない。未land案とD1877の衝突はこのユーザー裁定で限定解消する。
