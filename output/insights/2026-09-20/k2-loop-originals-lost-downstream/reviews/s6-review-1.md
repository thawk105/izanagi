## 所見

以下、`README` はレビュー対象の `output/insights/2026-09-20/k2-loop-originals-lost-downstream/README.md` を指す。指定資料と repo 外の script 4 本は読めた。静的照合を実施し、pytest・再構成 script の再実行はしていない。

- **must-fix M1 — README §1、roundtrip 行・59–60 行：** roundtrip の「値のみ」「内容の一部」「無し」を裏づける走査結果が reconstruction-log に無く、宣言された走査対象にも roundtrip insight が含まれない。特に digest・lock・`start_wall` / `reverse_recommendations` の不在は、対象 path・時刻・確認方法を補わないと対応表の断定が実測範囲を越える。
- **must-fix M2 — README §2、B-6 (c) 行：** critic-3 の読取対象を bytes で再現できないものを digest だけに限定しているが、WAL も bytes 不一致、round 3 lock `f1ab4966…` も round 2 写し `fc7acaca…` と別物である。同 identity は lock 全体の同一性を保証しないため、限定文にも WAL・lock を含める必要がある。
- **must-fix M3 — README §2、B-6 (d) 行：** 「3 巡とも、pair 初投入でも stock 未達」の一次資料を pair WAL と evidence だけにして「完全に再検算できる」とするのは過大。pair 原本で検算できるのは pair 試行であり、3 巡の未達は各巡の記録・残存資料へ対応づける必要がある。
- **must-fix M4 — README §4、101 行・104–105 行：** 「派生物から組んだ入力は原本から組んだ入力と同じ」「provenance の強さは択 A と変わらない」は対象範囲が広すぎる。sha 一致で確認した loop_state / AO と、canonical 内容一致の WAL、原本 digest / lock の不在、未作成の次巡完全入力を分けなければ、A/B の比較が A に有利な過大保証になる。
- **must-fix M5 — worklog fragment 56 行：** 入力元をユーザー裁定としながら、次巡に「入力は派生物から組んだ」と無条件で記録させている。A 採用時の文と明記し、B/C では実際に選ばれた入力元を書く形にしないと、次の一手が裁定を先取りする。既存の `docs/worklog.md:2618` の T-2795 本文自体に欠落は認めなかった。
- **must-fix M6 — `materials/reconstruction-log.md:5`、§4・§5：** 「stdout の逐語」という説明と script 本文が一致しない。例えば `reconstruct_ao.py` は期待 sha を全桁出すが log は省略し、`wal_keyorder.py` の出力も日本語注釈付きの別形式へ編集されている。実出力の逐語と説明を分けるか、現状を「抜粋・要約」と明示しないと一次証拠の性質を誤認させる。
- **must-fix M7 — README §0・`reviews/s4-ruling.md` P1：** 記録 wave の roundtrip 判定は「原本消失、sha256 も無い」、続く影響説明も「値までしか遡れない」と無限定に書いている。「insight の記載範囲について正しく、矛盾しない」という整理は原文の結論まで正当化してしまう。「同 insight に未記載だったが、3 巡稿で記録が見つかり、この結論を補正する」と区別すべき。
- **nit — README §1、roundtrip WAL 行：** `round 2 planner-input-2.json` は所在の誤記。該当値を持つのは roundtrip の `materials/planner-input-2.json` であり、round 2 の materials には `planner-input-3.json` がある。
- **nit — README §4、109 行：** 「whiteboard の実測 (811,956)」は `current_perf` の実測とする。whiteboard は 5 field で throughput を含まない。

照合で問題を認めなかった事項は次のとおり。

- §1 の原本 sha256 先頭 8 桁と記載 bytes 数は、3 巡稿 §5.1 と全行一致した。
- round 2 の残存 bytes、round 2/3 AO・round 3 loop_state の再構成結果、round 3 WAL の canonical 一致、pair の現存区分は、親の log と対応する。round 2 lock / WAL と pair WAL は今回の sha256 読取りでも一致した。
- 候補 list の不在には list の path と棚卸し時刻、T-2795 session の不在には ListAgents の対象数と時刻が付いている。
- fig12 の実際の provenance は `docs/paper-story/figures/fig12_k2_manual_loop_dataflow.provenance.json`。`inputs` は流れ JSON・稿・role 定義 3 本で、campaign 原本への直接依存は無い。
- 再構成物を原本と呼ばないこと、digest 再描画が未実測であること、過去判定を無効化しないこと、verifier gate を維持することは一貫している。

## レンズ (b) の攻撃結果

- **択 A：説明への攻撃は成立、原本欠落を理由とする実行不能の攻撃は不成立。**  
  `p3_s4_loop.py:1270` の `k2_next_generation_inputs` は呼出し側の入力をコピーして診断を足し、`:1292` の `planner_context_payload` は whiteboard・K2 束縛・reflux 条件を検査する。`:1426` の値域検査にも旧 WAL・digest・lock bytes の読取りは無い。`drive_iteration` (`:2598`、特に `:2699` 以降) が読むのは渡された新 layout の checkpoint であり、旧 round 3 root は要求しない。`check_stop` (`:1341`) の walltime 制限とも整合する。  
  ただし sha 照合が証明するのは確認済みデータの同一性までで、失われた critic 読取対象の全面的再監査、次巡完全入力の正しい組立て、実送付を証明しない。これが M4 の成立理由。A は同 job stock 未達を解消した扱いにしておらず、この点の攻撃は不成立。

- **択 B：現状の「やらない理由」への攻撃は成立。**  
  B には、次系列の入力証拠を新しい stock 測定から原本まで辿れる利点がある。過去 3 巡の証拠が強くなるわけではないが、次系列が失われた過去証拠に依存する範囲は減るため、A と provenance が同じとは一括できない。逆に B の強い不利益は、予定していた critic-3 診断の還流を観測する系列を中断すること。`k2_next_generation_inputs` (`:1270`) は診断なしも許すので、B を拒否すべきコード上の理由は確認できない。研究目的次第で B を選ぶ合理性はある。

- **択 C：出所混在への攻撃は成立、C の技術的不成立という攻撃は不成立。**  
  critic-3 は 815,983 tps の走行を診断し、C の `current_perf` は別走の 811,956 tps になる。`k2_next_generation_inputs` (`:1270`) は両者の走行同一性を照合しないため、型が通ることは整合性の証明にならない。弱点は図の矢印の複雑化だけでなく、診断と基準測定の対応が変わること。一方、現存原本・現行 identity に近い評価を使う利点はあり、混在を明示した C を A より劣ると一律には言えない。

- **付随 1 項：scope 外という攻撃は不成立。**  
  README §4 P2 は、今回と同型の具体的な残存 worktree へ既存の `git worktree lock` を適用する提案であり、仮想リスク向けの新 gate・検査・台帳ではない。harness の入力・認証経路も変更しない。ただし lock は原本の写しではないため、§2 B-6 (d) の「写し・lock」は、写し作成も提案済みと読めない表現にするのがよい。

## 総括

**NO-GO。** 必須修正は **M1〜M7**：roundtrip 不在断定の根拠、B-6 (c)/(d) の検算範囲、A/B の provenance 比較、worklog の A 先取り、log の逐語表示、記録 wave との相違の扱い。

**択 A 自体を棄却する技術的根拠は見つからなかった。** 今回の NO-GO は、対応表と裁定パッケージが証拠の強さを正確に伝えるための文書修正に対するもの。