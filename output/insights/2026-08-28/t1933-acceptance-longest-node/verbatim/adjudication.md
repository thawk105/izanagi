# T-1933 resume 段4裁定

## 結論

**実装しない。実装面0 byteで段5/6を省略し、段7へ進む。**

固定baselineは計算ノードでchild rc=0になったが、現物は旧ledgerの前提と異なり、snapshot 2 nodeは4.18秒/2.61秒、T-080本体2 nodeは86.57秒/51.93秒だった。全体最長140秒もscope外である。安全性と実益を同時に満たしてこの最長を下げる所有内候補は証明できない。

## real / refuted

- real: plan v2の0 byte結論。snapshot規則値をoptimized/referenceで共有する案、live再観測を省く案、D104のworker/session跨ぎcacheを再開する案は不採用。
- real: 無変更区間のsnapshot結果再利用は、状態不変を別に証明できれば必ずしもunsafeではない。しかし対象node合計が6.79秒で、除けるのはその一部だけ。86.57秒nodeもglobal 140秒nodeも変えないため実益gateで不採用。
- real: T-080のdistinct/default variantには分岐前の構造的共通prefixがある。これを「variant統合そのもの」としたplan表現は過剰なので撤回する。
- real: cached baseからconsumer repoへの全量copyは未計測候補。ただしCoWの利用可能性、独立inode、fallback、copy後の破壊的変異隔離、実効果が未証明で、安全な共有境界とは認定しない。production履歴走査も残るため段5へ送らない。
- real: fixed `-n 0` 4-node走は同一argv局所A/Bの基準にはなるが、17,639 nodeのacceptance critical pathを代表しない。
- refuted: 「安全な構造候補が一切ない」。安全化の余地と、実効的な最長短縮候補の成立は別である。
- refuted: ledger 79/50秒を現行A/Bのbaselineにすること。現行固定走で4.18/2.61秒となり条件metadataも一致しない。
- refuted: scope内snapshot短縮を受入全体の最長短縮と呼べること。global上位140/94秒はscope外で、0 byteでは短縮実績自体がない。

## P1 / P2

- P1はglobalにはrefuted。固定owned slice内最長という限定でも対象は86.57秒のT-080本体へ移った。
- P2は「安全化可能な小候補がある」までpartial。ただしlive再観測・独立性を守って意味のある短縮を示す境界はnot proven。

## plan v2

1. 対象2 test file、直接helper、production、ledger、runner、conftestを変更しない。
2. D104のcache/groupingを再開せず、optional rules注入、値源共有、case縮小、assertion変更をしない。
3. 段5 author、after timing、変異matrixは実装面0 byte契約により省略する。
4. negative resultを「scope内で安全かつ実効的な短縮案なし」と記録し、「最長短縮達成」とは書かない。
5. scope外のglobal最長、ledgerの測定条件不足、CoW clone候補は本waveで新規実装・新規計測せず専用記録へ分離する。

## 変異事前登録

実装面0 byteのためDW-M01 matrixは免除する。禁止案の一時変異も、採用実装が無いので実走しない。既存のsnapshot独立性、single exact reason、held/released、consumer 11 node固定は1 byteも変更しない。

## 成果物影響

- 実装しないため受理集合、assertion、certified選択、proof chain、凍結bytesは不変。
- 放置するのはテストwallだけであり、科学成果物の値・参照・受理集合は変わらない。
- したがってDW-G05上のmust-fixは0件。性能上のnegative resultを正確に記録して閉じる。
