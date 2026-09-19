# 次のK2実走計画 — 同機体・同jobのstock対照

D2148項3に従う将来計画。T-2783は入力経路の設計・実装であり、候補生成・評価・3巡目投入を行わない。
2026-09-10のrun-cardの実行主体、K2知識源、hole制約、正しさ規律を引き継ぎ、診断入力の追補と
次走のstock対照だけをここで規定する。旧カードの過去予算は新しい走行へ流用しない。

## 入力と送付

親は当該走行のjob rootと保存逐語を指定してcritic診断を選ぶ。同じcampaign IDでも別submit-treeに
異なる走行があるため、IDだけで選ばない。既存 `extract_critic_sections` で4節を抽出し、
`k2_critic_diagnosis` をwhiteboardとは別の兄弟keyとしてplannerとK2 coderへ同じ内容で渡す。
型と実際の組立て手順は `docs/phase3-s4b-runbook.md` のT-2783追補による。
保存した完全入力JSONとinline promptを当該job rootへ残し、診断の助言と留保の両方を送る。

過去のproposal-3（20）をそのまま再評価せず、診断入力を含めて次の提案を生成する。
候補10を正解にせず、既知値の再提案・診断の不採用もそのまま記録する。再抽選で未評価値を作らない。
診断未送達と20再提案は既往の二つの観測であり、因果関係は検証されていない。

## stock対照

- 同一計算ノード・同一scheduler job内で、候補とstock対照を別build・別runとして取得する。
- stock対照はSiloの適応backoff（stock枝、`BACK_OFF=1`）。固定backoff候補と同じCCBench pin、
  workload、thread/records、compiler、trace-disabled性能条件で揃える。`BACK_OFF=0` の追加armは要求しない。
- 両者の正しさはtrace-enabledの独立build/runで既存verifierを通す。anomalyが出た候補は即reject。
  性能値で救済せず、perf buildに診断計器を混ぜない。
- 既存 `tools/pegasus/p3_s4_loop_pegasus.sh` は候補の1評価口であり、同job stock pairの完成済みlauncher
  とは扱わない。実行担当は既存pipelineのstock評価口を用いる同job手順と、環境・依存・排他条件を確定する。
  T-2783ではそのlauncherを追加しない。
- 過去の20/25の非同時刻値はstock対照へ流用しない。whiteboardのsuccessを改善と読まず、
  `delta_pct=None` を維持する。同job対照だけでLLM固有優越や新CC構造の合成を証明したとはしない。

## 実走前に別途確定する予算

実行commit、生成回数、評価数、反復数、実行順序、時間・投入回数の予算は、実走の別依頼で確定する。
旧カードの「1評価・比較armなし」はこの計画に流用しない。本計画も実走認可ではない。
K0/K1・B-4・8cの固定入力・評価契約を変更しない。
