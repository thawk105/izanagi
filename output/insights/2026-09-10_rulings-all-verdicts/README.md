# 2026-09-10 rulings 全50項の裁定資料

## ユーザー裁定

全件索引と説明・推奨を提示した後、ユーザーは **「返答例通りで」** と回答した。
対象の返答例は次のとおり。

> 全件推奨どおり。実装は合成再開の経路から。⑥は不要設定の取り下げ案、⑯は保留への変更、
> ⑧は記述統計に限定。人間手番はそのまま残す。

裁定本文の正本は `docs/spool/decisions/2026-09-10-rulings-all-20260910-verdicts-1.md`
(fold後は `docs/decisions.md` の「全50項の裁定は合成再開を先にし、不要設定を取り下げ、
B5を保留し、B-4を記述統計へ限定する」)。50項の番号は会話の索引と一致する。
本資料はその経緯と参照先であり、追加の授権や新しい受入条件を作らない。

## 交差相談と採否

前のread-onlyターンで `claude -p` を3本実行した。索引検査B、推奨検査A、
未land資料等の追加推奨検査A2を分離し、材料はfile pathで渡した。
3本とも終了コード0で、本文として返された所見の全文を本dirへ保存した。
これらは相談の意見であって裁定の正本ではない。誤引用や親が採らなかった意見もそのまま残す。

- `consult-a.md`: 推奨の当否。pin更新に関係する期待値、tailの平坦外挿限界、
  契約テスト同時更新の指摘を採用した。D1912をA-1まで解決済みとする読みは採らなかった。
- `consult-b.md`: 索引漏れ・既裁定照合。既裁定/AI手番の分離とGit差0を採用した。
  T-2501はD1879/D1859、T-2101残余はD1897、T-1998はD1874で主題照合済みであり、
  D本文にT-ID文字列が無いだけでは未裁定としなかった。
  D1931の軸3停止をB5へ自動適用する解釈は不採用。B5の保留は今回の新しい裁定である。
- `consult-a2.md`: 未land資料の扱い等。D1877を変更すると明示すること、walltimeの整合が
  要求時間増加を伴うこと、fixture残存の作成元追跡も択一に含めることを採用した。
  B-4のAI委任をT-1998へ流用する提案は採らず、T-2557の人間手番を維持した。
  対象のsnapshotがsiteを読まない実物確認があるので、別fileの失敗例を理由とするsite偽装は採らない。

較正の不要define除去について、過去の別build間のbinary hash不一致は、同一条件での
define有無のbinary一致を反証しない。現行 `orchestrator/campaign/genome.py` の
`SILO_SPACE` に `BACKOFF_FIXED` は無い。shell表・argv・宣言・専用条件要求・test期待の
整合変更は必要だが、探索空間そのものから軸を削除することは本裁定の必要条件ではない。
未landのpatch materialize + receipt新shape案より、不要指定の取り下げを推し、ユーザーが採用した。

正式比較consumerの呼出しを `orchestrator/` と `tools/` のPython/Shellで検索した結果、
定義とtest呼出しだけだった。D1915のconsumer内部の必須照合は維持し、
存在未確認の公表入口へ新たな配線を作る提案は採らなかった。

## 資料の範囲

- local main基準は `e618883c2aba791edb7c2de71c0a6c18d311d915`、worklog末尾1424。
  前回の索引が読んだ末尾1394以降と、carryの実体、既裁定、phase、repo外handoff/inbox、
  稼働branchの未land資料を照合した。
- 主経路: `output/insights/2026-09-09_t2182-k2-eval-run/README.md`、
  `output/insights/2026-09-09_t2397-a1-pilot-attempt-0003/README.md`。
- B-4床値: D1855。母集合: worklog (1411) と
  `docs/phase3-b4-reflux-ablation-preregistration.md` の記述統計分岐。
- B5: `output/insights/2026-09-09_t2448-b5-executor/README.md`、D1895/D1926〜D1929。
- 遠隔検証: `output/insights/2026-09-09_t2486-ssh-cgroup-equivalence/README.md`。
- 静的非交差: D1914 と `output/insights/2026-09-10_t2539-backoff-validation-isolation/README.md`。
- Cicada: `output/insights/2026-09-10_t2536-cicada-axis-name/README.md`。
- tail: `output/insights/2026-09-10_t2266-formal-1000us/README.md`、
  `output/insights/2026-09-09_t2188-nonmonotonic-mechanism/README.md`。
- 未land T-1851: branch `worktree-dev-wave-t1851-unit-c2` の
  `output/insights/2026-09-09_t1851-unit-c3a-wiring/ruling-package.md` と
  `output/insights/2026-09-09_t1851-unit-c3b-floor-range/ruling-package.md`。
- 未land T-2515: branch `worktree-dev-wave-t2515-calib-rr95-rr5` の
  `docs/spool/decisions/2026-09-10-dev-wave-t2515-calib-rr95-rr5-4.md` と
  `docs/spool/worklog/2026-09-10-dev-wave-t2515-calib-rr95-rr5-3.md`。
- 未land T-2417: branch `worktree-dev-wave-t2417-policy-arm-perf` の
  `docs/spool/worklog/2026-09-08-dev-wave-t2417-policy-arm-perf-1.md`。

Gitの未push差は手元の追跡refとの比較で0だった。remote実体の再取得成功を意味しない。
この記録ではpush・remote branch操作・他waveのfragment編集を行わない。

## 記録と実行の区別

全50項を採用したことは、50項の実装が完了したことでも、条件付きの後続が解禁されたことでもない。
実装・文書追補・再凍結・測定はそれぞれの所有taskが決定範囲だけを実施する。
裁定で維持した人間手番をAIが代行せず、未land成果を本記録だけで受入済みにはしない。

## 記録の検査

- `python3 tools/check_codex_agents.py`: rc=0。
- `python3 tools/check_docs.py`: rc=0、違反なし。
- `python3 tools/spool_fold.py --dry-run`: rc=0、status=planned。
  68既存項を更新し、50項の裁定を1つのDの項1〜50として追記する計画を確認。
- 本記録はMarkdownのみ。実装・性能測定・pytestは行っていない。
- foldはdry-runだけで、canonical台帳へ直接追記していない。
