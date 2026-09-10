---
schema: izanagi-spool-v1
ledger: decisions
authored: 2026-09-11
wave: dev-wave-t2397-a1-attempt4
seq: 1
---

## {{D:a1-fixed-patch-source}}. A-1 attempt-0004 は canonical clean 起点と指定固定 patch の実 source を区別する

**決定:** D1936項3を進めるため、A-1のsource受理契約を
「canonical cleanの起点＋指定既存patchだけを適用した実source」へ整合する。
関門と実buildは同じsourceを使い、各build直前にその実sourceを独立期待materializationと照合する。
元checkoutのcanonical HEAD/clean検査、任意追加差分の拒否、verifier anomalyの即rejectは維持する。

**ユーザー指示との関係:** 親がこの整合案（事前登録・policy・build検査・consumerを一体で整合）を
具体的に提示して続行可否を尋ねた後、ユーザーは「仕事続けろよ」と指示した。
親は直前の整合案での続行指示として受け取り、その旨を報告して再開した。
この指示を規律2の緩和や任意dirty sourceの承認としては扱わない。

旧balanced5 pilotのpolicy/preregistration bytesと過去attemptは保存し、source条件だけを
投入前の別追補へ記録する。study、arm、規模、60対、配置、seed、統計、品質・再走・利用制限は変えない。
対象は登録済みpilotのattempt-0004。既存submit・complete・materializeの経路を使う。

**理由:**

- 前回の関門は未patch sourceを検査していたうえ、A-1の実buildにも未patch sourceが届いていた。
- 同じpatched sourceを渡すだけでは、balanced経路のbuild直前tracked-clean要求が正例を拒否する。
  指定patchによる差分と任意追加差分を区別するsource契約の整合が必要だった。
- gflags/glog prefixだけでなくconfigure時のFetchContent供給も既存部品で接続しないと、
  計算ノードで依存取得が停止する。実buildの追加defineをexact argv consumerへ同時に反映する。
- 既存materializer、独立期待tree比較、SourceEvidence、admission、source_bindingが利用できる。
  新しいsource生成系やWAL台帳を作る必要はない。

**採らない案:**

- 関門だけpatchedにしてbuildをstockへ戻す、clean検査だけ別rootへ向ける、dirty拒否を削除する。
- 旧policyをメモリ内で書き換えて旧hashを名乗る、過去attemptを再ラベルする。
- root inode防壁・readonly化・新WAL検査receipt・全実装closureの一律拡大。
  本体実装に必要な既存束縛と局所修正に限定し、仮想risk向けの一般化を足さない。
