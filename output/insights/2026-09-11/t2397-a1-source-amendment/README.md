# A-1 balanced5 pilot — attempt-0004 の source 契約追補

- authority: preregistration-amendment
- default_effect: no-state-change
- study_id: paper-story-a1-20260901-balanced5-pilot-v1
- 適用: 本追補をsource bindingへ含めて新しく投入するattempt-0004。
- 根拠: D1936項3、および契約整合案を提示した後のユーザー続行指示。
- この文書は投入前に固定する。試行結果を見て値・規則を変更しない。

## 保存する登録

元の登録は
output/insights/2026-09-01_paper-story-a1-balanced5-pilot-preregistration/README.md
（SHA-256: 8f8d2ad338a7a3193aaee8433c1495cef06b9520425251dd8bef89584ca626fc）と
orchestrator/campaign/paper_story_a1_paired.v3-pilot.json
（SHA-256: ed1c942f9d4bc24ab1bc6106caea672262c8634d32b022eca75b125811f7b825）である。
両者のbytesを保存する。study、3 workload、各arm、規模、60対、5-rep配置、seed、
静定、競合検査、CV、無効・再走・利用制限は、以下のsource条件以外変更しない。
過去attemptの記録を書き換えず、本追補を遡及適用しない。

## source 条件の追補

元の§6.1と§6.3項16、およびpolicyのccbench_acceptanceを、今回の実build sourceについて追補する。

1. 起点CCBenchは511c9538e4e8efa54b45cda62e72389ed3b706ecのcanonical HEADかつtracked-cleanとする。
   submit、compute preflight、driver入口、artifact確認の元checkout検査を維持する。
2. 実測sourceは、この起点から既存patchharnessが隔離checkoutを作り、
   patches/silo-backoff-fixed.patchだけを適用して生成する。
   許すpatchのSHA-256はa5e0710c3f76744755b58ec66024c277daba00e49ce3cbf3d6d263cd7228580a。
3. 各trace/perf build直前は、実際にbuildへ渡すsourceについてcanonical HEADと
   指定patchの期待materializationへの一致を検査する。
   「patch由来のtracked差分があること」だけでは拒否せず、指定patch以外の差分は拒否する。
4. 条件関門と両armのbuildは、同じmaterializer contextの実sourceを使う。
   未patch sourceで関門を代用せず、関門だけpatchedで実buildをstockへ戻すこともしない。
5. source evidenceは実態どおり記録する。patched treeをtracked-cleanや未改変stockと偽装しない。
   consumerは測定source、build/admission、patchと本追補の束縛を検査する。

期待materializationは、既存の独立reference生成とtree比較を使う。任意のsource差分を許す契約ではない。
verifier anomalyは従来どおり即reject。trace-enabled検証とtrace-disabled性能測定を分離する。
stock比較、全armの条件関門、T-2514の拒否detail保存も維持する。

## 依存供給

gflags/glogは既存jobのpin付きstagingとdependency-prefixを条件関門にも渡す。
FetchContent依存が必要な箇所は既存hydrate/staging/prebuildを使い、
関門とbuildの実効configure条件を整合する。未使用CMake変数の警告を無視して関門を通さない。
これは実行材料の供給修正であり、armの測定条件を変更しない。

## 投入と結果の扱い

二つの停止原因を実機で閉じ、関連検査と独立レビューを終えた後、既存submit経路から
登録済みpilotのattempt-0004だけを投入する。測定用checkoutには記録編集をしない。
旧attemptを上書きせず、bench開始後の失敗や性能値を理由に再投入しない。
本pilotから性能優劣を主張せず、旧登録のsizing-input-only制限を維持する。
