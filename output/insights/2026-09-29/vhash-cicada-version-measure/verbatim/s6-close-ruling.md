# 段 6 レビューの閉鎖裁定 (2026-09-29 05:3x JST、DW-O16)

- 焦点再レビュー 2 巡目 (codex/out/s6-focus2.md): G1〜G3 closed、F1 closed、F2 partial (実 binary の `.text`/`.rodata` は smoke 待ち)、他 closed 維持。
- 新所見 must-fix「deleted で失敗した read も deep/candidate/…read_zero に数える」: **real だが今回の成果物への影響なし → nit/backlog**。
  根拠: YCSB の操作は `Ope::{READ, WRITE, READ_MODIFY_WRITE}` だけ (external/ccbench/include/procedure.hh:8-12、patch の CicadaYcsbWorkload も同じ 3 種)。
  `VersionStatus::deleted` は `cpv()` の `OpType::DELETE` (delete_record 由来) でしか書かれず、本 wave の条件では生じない。
  一次資料の限界に「DELETE を含む workload (TPC-C 等) で使う前に、失敗 read を候補計数から外す」と記録する。
- nit: patch 内の空白行 2 箇所の trailing whitespace (unified diff の文脈行) は計測に無影響、不修正。
- 焦点再レビューは 2 巡で閉じる (上限 3 巡)。F2 は smoke の実測で確定し、不一致なら段 6 へ戻る。
- 変異 MUT-1〜8 は commit 44c37d6d8 に対して走らせる。
