## 総括

このプランのまま実装へ進めるべきではない。最も重い欠陥は、凍結 spec と参照 artifact の意味的束縛がなく、caller が測定値・環境・統計集合を自己申告できる点である。
さらに live 環境、trace-disabled build、実際に exec された binary、raw 値の producer identity が機械的に証明されないため、汚染標本を `complete` として採用し、`D` を小さくできる。
`O_EXCL` は同じ path が残る間の二重作成しか防がず、削除・改名・内容改変・別 spec の別 path による選別再走を防がない。
一方、列挙済み欠測を 1 件でも検出したら全体未生成とする方針と、有限な upper が 1 以上なら clamp しない方針は妥当である。
静的検査のみであり、pytest は実走していない。緑とは判定しない。

## 所見

1. **重大: 凍結 spec は caller の自己申告を権威ある凍結へ昇格させている**

   **主張:** `path + expected_sha256` の両方を同じ caller が渡し、その spec 自身がセル集合、標本数、統計関数、環境、artifact を宣言する。HEAD に tracked であることは「結果を見る前の凍結」やユーザー裁定を証明しない。

   **根拠:** `plan.md:42-44` は path と期待 hash を API 引数にし、`plan.md:98-106` は全測定値を同じ spec に置く。`plan.md:115-125` の検査は bytes、hash、HEAD blob の一致までで、`source commit identity` の実値照合、freeze commit の時系列、ユーザー承認 receipt はない。逐語では、統計関数等はユーザー裁定事項であり、AI 候補を無裁定で凍結へ入れないとしている (`verbatim-prereg-s11.md:55-74`, `:79-89`)。

   **成果物影響:** caller は安定したセルだけの閉集合、小さい `sample_count`、`sample_max/v1`、長い実行時間などを自己整合した tracked spec に書ける。`closed_strata == planned strata` は両辺とも同じ自己申告 spec 由来なので通る。結果として sample max と `D` が小さくなり、材料側で有意判定が増える。

   **提案:** spec とは別のユーザー発行 freeze receipt を必須にし、spec SHA、freeze commit、統計関数 ID、閉じたセル集合、時間窓、承認者を束縛する。execute/finalize はその receipt がなくても動く設計にしない。現在 HEAD が freeze commit の子孫であることと、測定窓が承認後であることも検査する。

2. **重大: calibration、environment contract、build receipt は内容を使わない装飾的参照になっている**

   **主張:** plan は参照 artifact の bytes/hash を照合するだけで、spec 内の `perf_config`、環境値、binary、trace 宣言が参照 artifact の内容と一致することを定義していない。

   **根拠:** `plan.md:98-106` では provenance と実効値が別 field にあり、`plan.md:125` は calibration、contract、build receipt に「同じ path/hash 規則」を適用するだけである。対照的に既存コードは calibration を parse して env/clocks を照合する (`orchestrator/campaign/calibration_verify.py:81-141`)。contract hash から登録済み世代を解決する面も既にある (`orchestrator/campaign/env_contract.py:881-913`)。

   **成果物影響:** genuine な calibration artifact を参照しながら、spec には別の records、threads、workload、extime、reps を置ける。同様に genuine な contract/receipt を添えたまま別環境値や別 binary を測れる。静かな動作点を選べば `D` と床値が小さくなり、受理集合が拡大する。

   **提案:** 各 artifact を strict parse し、artifact から機械導出した projection と spec の実効値を完全一致させる。spec に値を重複保持する必要がない項目は artifact からのみ導出する。既存の calibration admission と contract registry を再利用する。

3. **重大: live 環境不一致が失敗として存在しない**

   **主張:** spec に `site` と `env_tag` はあるが、現在 site の resolver、現在 contract、runtime attestation との照合手順がない。失敗 status にも `environment_mismatch` がない。

   **根拠:** environment schema は `plan.md:99`、session 手順は binary hash、probe、measure、probe、append だけ (`plan.md:171-179`)。status 列挙 (`plan.md:185-196`) に環境不一致はない。逐語は同じ site resolver から env_tag を導出し、環境一致を確認するとしている (`verbatim-prereg-s11.md:60-66`, `:79-89`)。現物には live site resolver がある (`orchestrator/campaign/site_policy.py:66-85`)。

   **成果物影響:** 別 site、別 contract、異なる CPU/NUMA/clock の測定が有限値なら `complete` になる。より静かな環境なら `D` が小さくなり、有意判定が増える。これは「落ちた標本が静かに除外される」より悪く、本来落とすべき標本が成功扱いされる経路である。

   **提案:** window 予約前と各 session 直前に live site、authorized contract、runtime attestation、calibration binding を検証する。不一致は session record に `environment_mismatch` と実測 evidence を残し、全体を未生成にする。

4. **重大: fake 用注入 seam が authoritative raw の producer になれる**

   **主張:** 公開 `run_window` が `measure_fn`、`probe_fn`、`now_fn` をそのまま受け、fake と production の成果物を区別する capability や receipt がない。

   **根拠:** `plan.md:58-66` の公開 API と `plan.md:242`。テストは fake measure/probe/clock を正に使う (`plan.md:254-256`)。finalizer は raw から再計算するが、raw の取得元は検査しない (`plan.md:200-212`)。

   **成果物影響:** caller が両 candidate に同じ TPS、probe に `rc=1` と空出力、clock に窓内時刻を返せば `D=0` の正常 artifact を作れる。再計算は偽 raw から正しく 0 を再現するだけで、受理集合を最大に広げる。

   **提案:** pure state machine のテスト seam と authoritative writer を分離する。production launcher が発行した一回限りの measurement capability、実 runner identity、probe identity、clock source を session receipt に束縛し、finalizer は fake/test mode の artifact を候補床として拒否する。

5. **重大: `trace=False` と同一 artifact ID は実際に測った build を証明しない**

   **主張:** `trace is False` は spec 内の自己申告であり、build receipt の意味検証がない。同一 artifact ID の確認も識別子比較にすぎない。さらに path の hash 検査と exec は原子的でない。

   **根拠:** `plan.md:145-147`、テスト予定 `plan.md:282`。使用予定の `assert_binary_sha256` は path を開いて hash 後に閉じるだけである (`orchestrator/campaign/buildcache.py:598-611`)。build receipt の実 preimage には trace mode がある (`buildcache.py:1314-1318`) が、plan はそれを parse/bind しない。既存 trace 漏れ検査は `buildcache.py:3437-3464` にある。

   **成果物影響:** trace-enabled binary に対し spec だけ `false` と書いて通せる。hash 検査後、`measure_point` が exec する前に path を差し替えれば、candidate の片側だけ別 inodeを測ることもできる。診断 build 混入や片側差替えにより `D` は任意方向へ動き、小さくなる場合は有意判定が増える。

   **提案:** sanctioned build receipt を strict 検証し、receipt の `trace=false`、binary SHA、source、toolchain を実体へ束縛する。binary は no-follow で一度開き、held FD の inodeを hash し、その同じ inodeを exec する。candidate と reference の双方へ適用する。

6. **高: 連続標本を別の独立機会として数えない保証が発火しない**

   **主張:** window 内に複数の `sample_index` を作り、それぞれの `D` を上限統計へ渡す。`window_count` と `pair_sample_count` を別 field に表示するだけでは、連続標本を統計上の n へ数えることを防がない。

   **根拠:** plan は `(pair_id, sample_index)` を window 内で並べる (`plan.md:153-157`)。`plan.md:163` は件数を別 field にすると述べるだけである。逐語は同一 campaign の連続測定を独立機会として数えない (`verbatim-prereg-s11.md:125-130`)。

   **成果物影響:** 同じ熱・周波数・cache 状態にある back-to-back 標本を n 個として `sample_max` に入れると、時間分離した独立機会より長期ドリフトを捉えにくい。床値が小さくなり、有意判定が増える。

   **提案:** 独立機会を window/campaign ID と同一視するなら、各 pair は 1 window につき D を 1 件に制限する。複数 raw repeat は session reducer 内に閉じる。別設計なら、独立性を与える最小間隔と campaign 境界を凍結し、driver が機械的に検査する。

7. **重大: create-only は削除、改名、改変、別 path 再走を防がない**

   **主張:** `O_EXCL` が防ぐのは「同じ path がその時点で存在する場合の再作成」だけである。`O_APPEND` は他 process による truncate/overwrite を禁止しない。

   **根拠:** `plan.md:225-234`。テスト予定 `plan.md:288` は driver 自身が削除しないことしか示さない。finalizer はその時点の window bytes を読み、その hash を新しい summary に書くため、事前に編集された raw を独立した期待 hash と照合しない。

   **成果物影響:** 同じ path が残る 2 回目だけは測定前に `FileExistsError` となる。一方、高い `D` の artifact を削除・改名して再走する、別 spec で同じ時間窓に別 path を割り当てる、raw を両側同値へ書き換える、の各経路は残る。低い run だけを summary に採れば床値が小さくなる。

   **提案:** `(freeze receipt SHA, campaign_id, window_id)` を鍵とする durable な attempt registry を、成果物とは別の authority に一度だけ予約する。raw は immutable storage または独立 receipt へ seal し、finalizer はその固定 hash だけを読む。そこまでできないなら「削除・改名を防ぐ」という保証を撤回し、人間の採用検査が必要な証拠に格下げする。session ID は集合一致だけでなく、各 ID が exact 1 回であることも検査する。

8. **高: validation-only は実走禁止も測定認可も担保しない**

   **主張:** 安全な mode が存在しても、隣に無認可の execute mode が存在すれば実走禁止の保証にはならない。

   **根拠:** CLI は `--execute-window` を公開する (`plan.md:244-248`)。`plan.md:250` は「起動自体を人間の認可後の手番」とするだけで機械証拠を要求しない。D1453 は実走を凍結項目確定と測定認可の後に限定する (`verbatim-rulings.md:3-5`)。

   **成果物影響:** 凍結・認可前の実測でも、構造上は通常 artifact を生成する。後からその artifact を採用候補と誤認すると、結果を見た後の手順選択になり参照資格が壊れる。

   **提案:** spec とは別のユーザー発行 measurement-authorization receipt を execute 時に必須とし、spec SHA、freeze commit、window、campaign、実行者を束縛して一回だけ消費する。validation-only は receipt 不要、execute は receipt 不在時に output を確保する前に拒否する。

9. **中: 隠れた測定設定と恒真に近いテストが残る**

   **主張:** `require_complete_metrics` を明示するとしているが、spec schema にその出所がない。また、計画中の複数テストは宣言した field 同士を比較するだけで実体を検査しない。

   **根拠:** failure policy は `require_all_reps` までしか持たない (`plan.md:106`) が、adapter は `require_complete_metrics` を明示するとしている (`plan.md:240`)。現物の既定値は `False` (`orchestrator/calibrator/runner.py:1057-1070`)。恒真または片側だけの検査は以下である。

   - dataclass に default がない検査 (`plan.md:111`) は、値の凍結済み出所を証明しない。
   - `trace` field が `false` か (`plan.md:282`) は実 binary mode を見ない。
   - candidate artifact ID の等値 (`plan.md:145`) は実行 inode の等値を見ない。
   - closed strata と planned strata の一致 (`plan.md:219`) は、両方とも同じ caller spec 由来である。
   - file が残る場合の 2 回目失敗 (`plan.md:288`) は削除・改名後を試さない。
   - 件数 field の分離 (`plan.md:163`) は独立機会への算入を防がない。

   **成果物影響:** `require_complete_metrics` の選び方により欠測を許すか全件失敗するかが実装者判断になる。上記テストが緑でも、偽 raw、別環境、trace build、選別再走による小さい床値を防げない。

   **提案:** `require_complete_metrics` を裁定済み spec field または明文化した不変条件にする。semantic mismatch、fake direct API、live env mismatch、trace receipt mismatch、hash後のinode差替え、削除・改名後の再走、同一 window の別 spec、重複 session record、認可 receipt 不在を負例に追加する。

## 親 brief への反証

- **P1 は成立しない。** `BRIEF.md:44-45` は §5 の path/hash 表記を根拠にするが、§5 の該当欄は測定後の floor artifact の path/hash である (`docs/phase3-b4-reflux-ablation-preregistration.md:162`)。caller が渡す測定手順 spec の権威付けではない。tracked HEAD と hash の一致だけでは、事前凍結・裁定・採用者を証明しない。

- **P2 は文面と plan が矛盾する。** `BRIEF.md:46-47` は「driver に上限統計の実装を持たせない」とするが、plan は `sample_max/v1` と `max_over_closed_strata/v1` の実装 registry を新設する (`plan.md:214-217`)。さらに exact 統計関数は未裁定 (`plan.md:306-309`)。D1453 は driver 新設を裁定しただけで、この 2 関数を裁定していない。

- **P3 は必要条件しか満たさない。** CV 用 driver を流用しない判断は正しいが、低水準 `measure_point` と probe classifier を直結しても、live 環境、build receipt、producer identity、認可は閉じない。`BRIEF.md:48-49` から「正しい測定面になる」までは導けない。

- **P4 は誤り。** `BRIEF.md:50-51` の validation-only mode は実走禁止を担保しない。plan 自身が無 receipt の execute mode を公開している。安全な分岐の存在は危険な分岐の不在を含意しない。

- **不変条件のうち 3 件は plan で未達である。** trace-disabled は自己申告、create-only は削除・改名を防がず、同一 campaign の連続標本は名称を分けるだけで統計算入を防がない (`BRIEF.md:28-33`)。

- **「正本」表記が権威を過大化している。** アンカー表 `BRIEF.md:71` は §11.2 を正本と呼ぶが、射影された逐語は §11 全体を「未裁定の案であり規範ではない」と明記する (`verbatim-prereg-s11.md:1-10`, `:91-94`)。測る量などの現物事実と、sample max、標本数、出力方式の案を分ける必要がある。

- **probe アンカーの説明は実装と完全一致しない。** `BRIEF.md:70` の「rc=1 のみ競合なし」に対し、classifier は rc=0 の出力から自 PID だけを除いた結果が空なら空 list を返す (`orchestrator/calibrator/runner.py:359-376`)。成果物値への直接影響は小さいため nit だが、exact contract の説明としては誤りである。

- **D1266 の射程が広げられている。** `BRIEF.md:21-22` は D1266 を floor 発効・記入全般の根拠へ並べるが、射影では対象 driver と軸の記入者・レビュー者を `thawk105` に固定する範囲だけである (`verbatim-prereg-s11.md:78`)。driver が §5 を書かない結論自体は D1383 で支持されるが、D1266 はその一般根拠ではない。

- **DW-G05 の因果が過大である。** `BRIEF.md:55-57` は floor 未記入が材料レポートを 1 分類へ止めるように書く。しかし生成器は §5 を読まず無条件に floor 不在を渡すため、floor 行を埋めても正規経路は変わらない (`verbatim-prereg-s11.md:19-27`)。consumer 接続は別作業である (`verbatim-rulings.md:18-30`)。したがって本 driver 完成だけで Phase 3 の片翼が再開するという一般化は誤りである。

- **親独自の実測 count「未着地 wave 0 件」は再現可能性がない。** `BRIEF.md:79-80` に query、走査時刻、worktree/ref 一覧、hit 判定規則が残っていない。現在の worktree inventory には T-2136 に加え T-2169 measurement-surface-closure も存在するため、「0」を継続的不変条件にはできない。これらが意味的に重複するとの証拠まではないので、現段階では coordination nit だが、「text hit なし」から「変更面の競合なし」への一般化は過大である。

## 検査したが問題なしと判断した点

- 列挙済み status について、1 件でも非 complete、欠測、非有限値なら成功分だけで upper を計算せず全体未生成にする方針は安全側である (`plan.md:183-200`)。実装時は session ID の重複も拒否する必要がある。
- `p2_2` の `RECORDS/THREADS/EXTIME/REPS`、`p3_s4_loop.default_perf()`、`between_run_floor.SESSIONS=8` を直接 import・fallback する計画経路は見つからない。5 個の `PerfConfig` field を明示する方針も妥当である。
- candidate 2 session と reference 1 sessionを用い、同じ `reference_tps` を両 gain の分母にする式は正しい。別 reference や前回値への fallback を置かない点もよい。
- raw reps から session median、gain、`D` を再計算し、保存済み derived field を信用しない方針は正しい。ただし raw 自体の producer と不変性は別途閉じる必要がある。
- 有限な upper がちょうど 1 または 1 超なら `candidate_floor=null` とし、0.999 等へ clamp しない経路は plan とテスト予定に明記されている (`plan.md:221`, `:287`)。実装では有限入力同士の除算 overflow で生じる非有限 derived 値を serialization 前に明示的に未生成へ倒すべきである。
- 同じ exact path が残っている間の 2 回目については、`O_CREAT|O_EXCL` により測定前に失敗する設計になっている。これは create-only 全体ではなく、その狭い条件に限れば正しい。
- アンカー表の `PerfConfig:168`、`default_perf():1012`、`measure_point:1057`、`measure_point_floor:202`、`_write_out:255`、`p2_2` 定数 47-57、§11.2 の開始 918 は現物と一致した。