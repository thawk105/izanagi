# A-1 balanced5 sized 本走 — source 契約追補

- authority: preregistration-amendment
- default_effect: no-state-change
- study_id: paper-story-a1-20260901-balanced5-sized-v1
- 適用: 本追補を source binding へ含めて投入する sized study のすべての attempt。attempt 番号は pin しない (追補前の sized attempt は存在しない)。
- 根拠: D1986 項 5 (「試験運転専用の分岐を外す実装が閉じた時点で改めて諮る」)、D1323 (T-2081)、pilot の追補 (output/insights/2026-09-11/t2397-a1-source-amendment/README.md、SHA-256: 391e9425c0dec2ef33910b2112e7b1c5e5b650d6b6444c8c92285d5568a879c4)。
- この文書は投入前に固定する。試行結果を見て値・規則を変更しない。
- **本文書は投入の認可ではない。** 正式測定の認可は [T-1505] のとおり人間手番のままである。

## 保存する登録

元の登録は
output/insights/2026-09-13/paper-story-a1-balanced5-sized-preregistration/README.md
（SHA-256: 6047eff005fbd94bad8df0313124bd4ca037dedf0f2e3db05224d04ad34fd3c2）と
orchestrator/campaign/paper_story_a1_paired.v3-sized.json
（SHA-256: a6228bcd5d2db3eca45fed6e148ab7ba92dd4d179f60e9c9c4ed0ffcf4942f1a）である。
両者の bytes を保存する。study、3 workload、各 arm、規模、30 対、5-rep 配置、seed、
静定、競合検査、CV、無効・再走・利用制限、`formal=false` / `promotion_prohibited=true` は、
以下の source 条件以外変更しない。pilot の記録を書き換えず、本追補を pilot へ遡及適用しない。

## source 条件の追補

元の §6.1「CCBench は 511c9538… を canonical pin とし、追跡ファイルが汚れていないことを pilot と同じ
5 つの境界で要求する」と §6.3 項 16、および policy の ccbench_acceptance を、今回の実 build source について
pilot の追補と同文で追補する。

1. 起点 CCBench は 511c9538e4e8efa54b45cda62e72389ed3b706ec の canonical HEAD かつ tracked-clean とする。
   submit、compute preflight、driver 入口、artifact 確認の元 checkout 検査を維持する。
2. 実測 source は、この起点から既存 patchharness が隔離 checkout を作り、
   patches/silo-backoff-fixed.patch だけを適用して生成する。
   許す patch の SHA-256 は a5e0710c3f76744755b58ec66024c277daba00e49ce3cbf3d6d263cd7228580a。
3. 各 trace/perf build 直前は、実際に build へ渡す source について canonical HEAD と
   指定 patch の期待 materialization への一致を検査する。
   「patch 由来の tracked 差分があること」だけでは拒否せず、指定 patch 以外の差分は拒否する。
   この比較は既存の tree 比較の対象 (`.git` を除く tree) に限る。
4. 条件関門と両 arm の build は、同じ materializer context の実 source を使う。
   未 patch source で関門を代用せず、関門だけ patched で実 build を stock へ戻すこともしない。
5. source evidence は実態どおり記録する。patched tree を tracked-clean や未改変 stock と偽装しない。
   consumer は測定 source、build/admission、patch と本追補の束縛を検査する。

期待 materialization は、既存の独立 reference 生成と tree 比較を使う。任意の source 差分を許す契約ではない。
verifier anomaly は従来どおり即 reject。trace-enabled 検証と trace-disabled 性能測定を分離する。
stock 比較、全 arm の条件関門、T-2514 の拒否 detail 保存も維持する。

出所の判定は commit ID の確定可能性に置く (D1323)。すなわち元 checkout の HEAD が canonical pin かつ
tracked-clean であること、および build source が canonical pin + 指定 patch の期待 materialization と
一致することである。bytes 級の同一性検査は新設しない。元 checkout の untracked file は、凍結 policy の
`untracked_files_ignored: true` のとおり無視する。実測 source は pin から隔離 checkout として生成するため、
元 checkout の untracked file は実測 source へ入らない。

## 依存供給

gflags/glog は既存 job の pin 付き staging と dependency-prefix を条件関門にも渡す。
FetchContent 依存が必要な箇所は既存 hydrate/staging/prebuild を使い、
関門と build の実効 configure 条件を整合する。未使用 CMake 変数の警告を無視して関門を通さない。
これは実行材料の供給修正であり、arm の測定条件を変更しない。

## 機械可読の束縛

本追補は orchestrator/campaign/paper_story_a1_source.v2.json が `amendment` として SHA-256 で束縛し、
sized study の source binding に含める。pilot の契約 (paper_story_a1_source.v1.json) の bytes は変えない。

## 投入と結果の扱い

本追補と契約の実装が閉じても、投入は [T-1505] の認可の後に限る。旧 attempt を上書きせず、
bench 開始後の失敗や性能値を理由に再投入しない。
