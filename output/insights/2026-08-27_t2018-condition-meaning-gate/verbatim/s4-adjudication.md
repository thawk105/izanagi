# [T-2018] 段4裁定・plan v2

## 総括

段2 plan はそのまま採用しない。段3の両レンズが NO-GO とした7 blockerを裁定し、v1を
BACKOFF_FIXED 1軸の call-scoped driver-independent gateへ縮める。driver integrationは0であり、
現行EXTENDED_SWEEP_USの1000点は未保護のまま。凍結patch/ledger、符号化式、格子定数はscope外。

wave開始後にmainへlandしたD1198を段5前に取り込んだ。T-1999は裁定待ちではなく
「driver群へ義務化する」と裁定済み・実装待ちになった。ただしユーザーが本waveでdriver配線を
明示的にscope外とした境界は広げず、本waveは将来driverが独立に必須呼出しできるsupply armと
meaning armを実装する。driver配線は次のT-1999実装残件であり、本waveでは始めない。

## 所見裁定

1. define候補は9でなく8: real / 採用 / scope内。v1はBACKOFF_FIXEDだけ。残り7を対応済みと数えない。
2. marker block単体は実TU全体を保存しない: 懸念はreal。full-header instrumentation案はscope拡大なので不採用。
   代わりにproof kindを extracted applied-source decoder / standalone TU / finite pointwise witnessへ狭め、
   dynamic reachability、actual target TU、exact build inputを一切名乗らない。
3. stock -1はstandalone合成枝評価に入らない: real / 採用。v1 case domainを0以上のintへ限定する。
4. supply名集合だけではcache値からTU macro値への写像を示さない: real / 採用。
   source ownerを固定し、source_digestのeffective mappingを共有adapter経由で使い、要求値とexact一致させる。
   D1198に従い、これはmeaning armの前処理へ埋め込まず独立supply arm/evidence/reason codeにする。
5. source/Options/protocol CMakeのmixed snapshot: real / 採用。3入力を1回ずつ捕捉しhashをevidenceへ残す。
6. expected/observedを集合に潰すとcontext入替を通す: real / 採用。case x contextをpointwise float64 bits比較する。
   NaN/Infを拒否し、row identity/cardinalityをexact検査する。
7. fixtureと現行decoderの漂流: real / 採用。fixture holeは現行patch target-side marker blockとbyte一致を
   独立anchor testで固定する。F707 fixtureはsupply mapping 1行だけを欠く単一差にする。
8. JSON contractはproduction実在入力でない: real / 採用。JSON loaderと任意path/macro/result kindを廃止し、
   code-owned BACKOFF_FIXED contractだけを持つ。
9. gate名称が未配線には強い: 一部real。ユーザー要求のdriver-independent gateという語は維持するが、
   module/docstring/evidenceへdriver_integration=none、call-scopedを明記する。driver-integratedとは書かない。
10.既存marker parserとの重複: real / 採用。evolve_block.pyへ共有extractorを置き、
   sort_swo_oracleの公開wrapperを維持する。
11.timeout無し: real / 採用。既存B10 compiler probeの120秒境界より軽い単一TU compile/runへ同じ上限を継承し、
   timeout reasonを負例で固定する。親は関連test実走時の所要を記録する。
12.親実測のstart witness表: real。1000/2000/3000→0と3007→7は維持するが、
   1500/2500の列と未記録startをgoldenに使わない。pointwise fixtureは0/5/999/1000のcontext非依存点に閉じる。
13.上端999では閉じないという一般化: real / scope外。本axisを0..999へ制限すれば現符号化のfixed量は閉じるが、
   族全体は閉じない。格子/符号化を本waveで変更しない。
14.現1000点未保護: real / scope外。ただし主張上限とworklogへ必ず記録する。
15.変異anchor過剰決定: real / 採用。下記事前登録は1変異1焦点nodeへ再照準する。

## plan v2 exact ownership

実装workerが編集してよいのは次だけ。

- orchestrator/campaign/evolve_block.py (new)
- orchestrator/campaign/sort_swo_oracle.py (existing wrapper only)
- orchestrator/campaign/source_digest.py (effective define adapter only)
- orchestrator/campaign/condition_meaning_gate.py (new call-scoped gate)
- orchestrator/tests/test_condition_meaning_gate.py (new)
- orchestrator/tests/test_sort_swo_oracle.py (shared parser compatibility)
- orchestrator/tests/test_campaign.py (effective mapping boundary)
- orchestrator/tests/fixtures/condition_meaning_gate/** (new static fixtures)

実装workerはdocs/output/patches/ledger/driver/EXTENDED_SWEEP_USを編集しない。commitもしない。

## API /禁止署名

公開gateはBACKOFF_FIXED専用とし、supplyとmeaningを別の公開function・evidenceとして持つ。
単一の総合pass bitへ潰さない。少なくとも次を満たす。

- case valueはtype(value) is intかつvalue >= 0。boolを拒否。
- captured sourceのsilo-backoff-magnitude holeを実compilerで評価する。
- callerはpath、marker、macro、result kindを差し替えられない。
- supply armはeffective BACKOFF_FIXEDが要求値とexact一致しなければcompile前に拒否。
- meaning armはcaptured decoder、case/context、compilerだけから独立に再導出し、supply armの緑を
  meaningの緑として使わない。F718 testはsupply arm緑とmeaning arm赤を別々に固定する。
- expectedはcontext indexごとのcanonical float64 bits。集合比較は禁止。
- compiler/run rc、timeout、stderr、欠落/重複/未知row、NaN/Infをfails-closed。
- evidenceはsource/Options/protocol hash、hole hash、compiler identity/argv、observed pointwise bits、
  proof_kind、driver_integration=noneを持つ。

通る正例: BACKOFF_FIXED=5、start=1と2の両contextでobserved bitsが
double 5.0のcanonical bitsとpointwise一致する。

禁止する負例署名:

- F707: decoder/markerは正例とbyte一致、供給集合は非空だがBACKOFF_FIXED cache-to-TU mappingだけ不在。
  macro-not-suppliedでcompiler解決より前に拒否。
- wrong-RHS: BACKOFF_FIXEDが別cache名へ写る。supply-value-mismatchで拒否。
- F718: supply/marker/compilerを通し、BACKOFF_FIXED=1000のexpected 1000.0 bitsに対しobserved 0.0 bits。
  decoded-meaning-mismatchで拒否。
- uniform shift/comment decoy: gridが単射または正しい式文字列が存在してもpointwise mismatchで拒否。

## scope外裁定パッケージ

- T-1999: driver群への必須接続。D1198で裁定済みだが、本waveの明示scope外として次の実装残件に残す。
- 現行1000点の除去、0..999 domain制約、または1000以上を表現できる符号化への変更。
- patch/ledger/freeze bytesの変更。
- BACKOFF_FIXED以外7 macroのsemantic-shape別oracle一般化。
