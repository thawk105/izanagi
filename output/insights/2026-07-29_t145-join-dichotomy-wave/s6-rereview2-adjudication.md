# T-145 段 6 焦点再レビュー 2 裁定

## 採用

- stale PGID signal は real must-fix。parent-side primary exception が発生しても、direct child が
  既にexit/reap済みなら `killpg(process.pid, ...)` を呼ばない。signal直前の
  `process.poll() is None` を所有条件にし、live session leaderだけを対象とする

成果物影響: exit済みchildのPID/PGIDを再利用後にsignalすると無関係なtest processを終了し、別nodeの
受入結果とmutation台帳を欠落させる。

## 不採用 / backlog

- output/result size limit は generic hardeningとしてrealだが、T-145 childは固定test moduleだけを
  importし、success fixtureのworker stdout/stderrはDEVNULL、例外値・temp path・requestもtestが
  bounded に生成する。M1〜M6の事前登録mutationも巨大stdout/tracebackを生成しない
- したがって「異常childが任意巨大出力を生成する」という前提はT-145の受理集合にない。専用FDや
  file-backed captureへの再設計と併せ、成果物契約を定める別taskへ送る。このwaveのKILL/SURVIVEを
  止めるmust-fixにはしない
- producer/parser結合controlはnit。pure parser controlをproducer結合の実証には数えず、real nodeが
  capability skipならproducer/parent mappingもNOT_RUNと記録する

## 第3修正の終了条件

- authorは stale PGID ownershipだけを修正し、production/docs/outputを触らない
- capability非依存parser control、long-path node、isolation meta-testを再走する
- これを3巡目の最終fixとし、以後は新たなscope拡張fixを重ねない
