# 段 1 brief — [T-2662] path 参照の抑止判定 (helper と本番) の真偽表と D248 の意味

**研究前進 (土台)**: `/cleanup-branches` の必須 gate である到達不能 commit 監査
(`tools/audit_dangling_commits.py`) は、wave の成果物を持つ到達不能 commit を「repo 外に同一実体が
あり、その path が main の landed 内容から参照されている」ときだけ抑止する (D247 条件 5、D248 の境界)。
その参照判定に 2 実装がある — テストが同値の対照に使う helper `_has_bounded_path_reference()`
(出現の左右 1 byte を見る) と本番 `_bounded_path_reference_matches()` (探索根の出現から最初の境界 byte
までを token として `in patterns` で見る)。path 内部に境界 byte を含む候補で両者が割れることは
D2039 が指摘したが、真偽表は未取得で、どちらが D248 の意味かも未確定である。止めているのは
「同値テスト `test_bounded_path_reference_single_scan_matches_legacy_boundary_semantics` の候補集合が
境界 byte を含む path を持たず、同値主張の射程が不明」という状態であり、最小差分は**真偽表と結論の
insight** (実装差分ゼロ) である。

**scope**: (1) 同じ候補集合 (空白・改行・括弧・引用符・tab・非 ASCII を path 内部に含む候補、および
境界 byte を含まない対照) で helper と本番の真偽表を取る。(2) 実在 path を対照にする — 本番探索根
`/work/1/SFC/tanab/dev-wave-jobs` に実在する境界 byte 入り path 6 件 (段 1 で実測、後述) と、main の
landed 内容が引用符で参照する実在 job dir (`orchestrator/manual_probes/test_t2397_a1_source.py` の
`dev-wave-t2397-a1-attempt4`) を陽性対照にする。(3) D248 の意味を確定し、向き (helper へ揃える /
本番を維持) を決める。成果物への影響: 本 wave は certified 選択・レポート・台帳の値を変えず、
抑止集合 (findings) も変えない。差が実在 path で発火しうるかを確定するだけである。

**確定済みユーザー裁定**: **D2104 項 25** (第 20 回 /rulings、wave 開始時は branch
`worktree-rulings-all-20260917` の commit ad12ba35b の fragment だったが、段 4 直前の再走査で main
b4631a92e に fold 済みと確認し、worktree へ ff-only で取り込んだ): 「同じ候補集合で helper と本番の
真偽表を取り、実在 path を対照にして D248 の意味を確定してから向きを決める (AI 実測先行)。暫定は
本番側 (狭い判定) を維持する」。理由: D248 は候補 path 内部の境界 byte の探索方式まで明記しない。
抑止を増やす向きは fail-open なので暫定は狭い側。**D248** (境界 byte を列挙し未知 byte は延長扱い、fail-safe は報告が残る側)、
**D2039** (差の存在の記録、抑止を広げない不変条件)、**D2040** (境界規則を緩めて条件 5 を発火させる
案の却下)。worklog 正本は entry 1596 の [T-2662] 項 (裁定済み → 実測手番)。

**段 1 で実測した前提**:
- 本番探索根 `/work/1/SFC/tanab/dev-wave-jobs` (top 1240 entries) の `find` で、名前に境界 byte を含む
  entry は **6 件**: 空白入り dir 4 件 (`g2 clean scan Ω` ×2、`a much longer root with spaces Ω` ×2、
  配下 file 合計 467)、`[?]*` を含む file 1 件、`:(glob)` を含む file 1 件。いずれも
  `dev-wave-suite-floor-recheck/measure/run2/.../pytest-of-tanab/` 配下の pytest tmp 残骸。
  改行・tab・引用符・backtick・`{}`・`<>` を含む実在 path は 0 件。
- 陽性対照の job dir `dev-wave-t2397-a1-attempt4` は実在し、main の landed 内容が `Path("...")` の
  引用符付きで祖先 dir を参照している (D2040 の記述どおり)。

**割れうる前提 (親の provisional 裁定・攻撃対象)**:
- **(P1) 差は一方向である。** 本番 True ⇒ helper True が成り立ち、逆は path 内部に境界 byte がある
  ときだけ破れる。つまり helper ⊇ 本番 (helper のほうが抑止が広い)。
- **(P2) D248 の意味は本番側である。** D248 は「pattern の出現が path として完結しているか」を
  境界 byte の列挙で決め、fail-safe を「報告が残る側」に置く。内部に境界 byte を含む path は、
  landed 内容の中で「その byte で切れた token」と区別できないので、完結した参照とは数えない
  (= 報告が残る) のが D248 の向きである。helper 側へ揃えると抑止が増え、裁定の「暫定は本番側」と
  D2039/D2040 の「抑止を広げない」に反する。
- **(P3) 実在 path での発火は今日 0 件だが構造的に 0 ではない。** 6 件の実在 path は pytest tmp
  残骸で、到達不能 commit の blob と bytes 一致する見込みは薄い。しかし監査は候補を bytes 一致で
  選ぶので、将来の候補が境界 byte 入り path を持つ可能性は排除できない。
- **(P4) 真偽表の候補集合は chunk 境界も含める。** 本番は 1 MiB chunk で走査するので、境界 byte
  以外にも「pattern が chunk 境界を跨ぐ」型で helper と割れる可能性を同じ表で潰す。
- **(P5) 本 wave は実装しない。** 裁定成果物は真偽表と結論の insight であり、helper を本番へ揃える
  変更 (テスト側の狭め) は次 wave の候補として worklog に載せる。

**不変条件**: 監査の抑止集合を広げない。D247 の 5 条件・D248 の境界 byte 列挙・D957 の開示義務は
不変。本番の判定を変えない (実装差分ゼロ)。probe は repo へ commit せず、Codex `role=author` が
worktree 内へ書き、親が job dir へ退避して login node で実走する。

**成果物の形**: `output/insights/2026-09-17/t2662-bounded-reference-truth-table/` に brief・裁定・
真偽表 (逐語)・レビュー・README (結論)。spool fragment は worklog 1 本と decisions 1 本 (D248 の
意味の確定と向き)。

**並列分割方針**: 既定の軽量版。設計択一は裁定が「暫定は本番側・抑止を広げない」で束縛済みなので
段 2・3 は省く。段 5 は Codex author 1 本 (probe)、段 6 は真偽表と結論に対する敵対レビュー 2 本
(レンズ A: 候補集合の完全性と実在 path 対照の妥当性、レンズ B: D248 の意味の解釈と向きの結論)。

**受入・実測環境**: login node (probe は pure Python、数秒)。受入全走は免除しない。
