## 所見 1: qstat 修正だけでは bench 到達を保証できない

(a) 主張: plan の visibility 修正は F852 の既知障害を除去できる。ただし、同じ submit から bench までには未実測の scheduler、環境変数、外部 command 述語が残るため、「この変更後は実機で bench へ到達する」とは結論できない。

(b) 根拠:

| 段階 | 述語 | 根拠 | 実機到達性 |
|---|---|---|---|
| login preflight | study、policy、preregistration が固定済み | `paper_story_a1_paired.py:916-927,1604-1656,3218-3224` | F852 では qsub 後まで進んだため、当時の pilot では通過済み |
| Git / CCBench | HEAD 一致、親 tree clean、CCBench pin と tracked-clean | 同 `:2225-2278,3225-3229` | F852 で qsub が受理されたため通過済み |
| namespace | durable base、fresh attempt、prior bench 不在 | 同 `:2326-2344,3033-3061` | F852 では通過済み |
| qsub | rc=0、stderr が完全な空文字、stdout から request ID を一意に取得 | 同 `:3101-3138`、F852 `:3-10` | 最初の workload について通過済み |
| submission qstat | rc=0、空 stderr、一意な対象 ID、canonical state が QUE/RUN、一意な `gen_S@nqsv (Execution Queue)` | plan `:42-57,104` | RUN、PRR は実機逐語で到達可能。共有 parser は両方 `RUN` を返した。Queued は F852 `:8-10` に実測記録がある |
| group receipt | state が既存有限集合、queue が `gen_S` | `paper_story_a1_paired.py:2957-2991` | 新規の `RUN` / `QUE` は通る |
| compute job env | `PBS_JOBID`、`PBS_O_HOST`、`PBS_O_WORKDIR` が存在し、request ID、submit host、repo root と一致 | 同 `:3346-3376,6700-6708` | 投影資料に実機 env の逐語が無く、synthetic test だけ。未証明 |
| job-body allocation qstat | shell preflight が scheduler start、host 等を qstat から得る | `test_paper_story_a1_job_contract.py:1393-1399` | F852 型の未実測述語候補。positive stub は PBS-Pro 型の `exec_host` / `start_time` だが、実機逐語は `Execution Hosts(JSVNO)` と `Started Request Time` (`qstat-f-980043.nqsv.txt:34,50-51`) |
| runtime roots | compute site、HEAD 一致、clean tree、fresh roots、repo 外、非 `/scr` | `paper_story_a1_paired.py:4312-4380,6721-6735` | topology 上は到達可能だが実機証拠なし |
| dependency | dependency prefix が `/scr` 配下で妥当 | 同 `:6737-6739`、test `:1243-1257` | job body に依存。実機証拠なし |
| reservation | shell が 8 個の `IZANAGI_RESERVATION_*` を正しく生成 | 同 `:711-721,6740-6750`、test `:38-47,1673-1706` | allocation qstat の解釈に依存し、未証明 |
| runtime contract | Pegasus compute 解決、calibration、compiler/toolchain manifest | 同 `:6752-6765` | 投影資料内で実機通過は証明されていない |
| condition gate | checkout、C++ compiler、cmake、define supply/runtime meaning が全 green | 同 `:6598-6676,6829-6834` | bench より前。実機通過証拠なし |
| final pre-bench | single-tenant、両 arm build/verify、3 workload ready、期限内 barrier | 同 `:5964-6078,6837-6874` | 3 job 全ての成功が必要。未証明 |

bench は `run_campaign` の build/verify 後、`gated_balanced_executor` が `_v3_barrier_before_bench` を通した後に初めて original executor へ入る (`paper_story_a1_paired.py:6835-6874`; 構造テストは `test_paper_story_a1_job_contract.py:1896-1908`)。

特に job-body の qstat stub は `exec_host = ...` と `start_time = ...` しか返さない (`test_paper_story_a1_job_contract.py:1393-1399`)。実機逐語にはこの二つの field が無い。shell 本文は射影外なので、実装が実機形式も併受理するか確認できない。少なくともテスト代表性は F852 と同型である。

(c) 成果物への影響: この wave は「既知の login-side visibility blocker を除去した」とは言えるが、「A-1 が bench に到達する」とは言えない。親は少なくとも job body の allocation-qstat parser を scope と射影に加え、提示された実機逐語で preflight を通す検査を別 package または本 wave に含める必要がある。`PBS_O_HOST` と `PBS_O_WORKDIR` の実機逐語確認も必要である。

(d) 判定: **real**。実装不具合が確定しているのは F852 の visibility 部分であり、job-body 部分について確定しているのは「実機到達性が証明されていないこと」と「positive test が実機書式を代表していないこと」である。

## 所見 2: canonical `QUE` の実機正例が無い

(a) 主張: plan は producer の受理集合を `{QUE, RUN}` とするが、追加予定の実機正例は二つとも canonical `RUN` であり、`QUE` 経路を固定しない。

(b) 根拠:

- RUN 逐語は `Current State = Running` (`qstat-f-980043.nqsv.txt:7`)。
- PRR 逐語は `Current State = Pre-running` (`qstat-f-980062.nqsv.txt:7`)。
- 共有 leaf は両方を `RUN` へ写す (`scheduler_nqsv.py:55-59`)。
- plan の正例も RUN と PRR の二件だけである (`plan.md:118-120`)。
- 一方、D805 は実機で `Staging` と `Queued` が現れ、実測二語への過学習なら正常運用で fail-closed したと明記している (`D805.md:10-18`)。

(c) 成果物への影響: `QUE` を拒否する変異、`Queued` / `Staging` の正規化を壊す統合ミス、QUE 時だけ queue 抽出を失敗する実装が追加テストを生き残る。実測済みの Queued または Staging の全文 fixture を回収し、「receipt に `QUE` を記録する」正例を加えるべきである。実機 fixture が得られないからと `{RUN}` に狭める案は D805 の却下理由を再発させる。

(d) 判定: **real**。

## 所見 3: `_parse_qstat_terminal` を変更しない裁定は半分だけ正当

(a) 主張: 「共有 leaf の END 語彙へ接続しない」は正当だが、「`_parse_qstat_terminal` と visible terminal producer を何も変更しない」は、ユーザー依頼と D805 の原則を満たさない。

(b) 根拠:

変更しない側の最強の論拠は次の通りである。

- 提示された二つの実機逐語は非終端であり、visible END の実書式ではない (`plan.md:63-69`)。
- 実測済み終端形は request disappearance である (`brief.md:47,81-86`)。
- 共有 leaf の END 語彙は `completed`、`finished`、`post-running` 等を含み (`scheduler_nqsv.py:62-66`)、A-1 へ無条件に接続すると未実測の受理集合を増やす。
- 現行 schema の historical visible-terminal receipt を読む consumer が存在する (`paper_story_a1_paired.py:3705-3727`)。

変更すべき側の最強の論拠は次の通りである。

- ユーザー依頼と親 brief は `_observe_qstat_visibility` と `_parse_qstat_terminal` の両方を明示している (`brief.md:9-13,53-55`)。
- A-1 の parser は `job_state|State` と `exit_status|Exit Status` を要求し (`paper_story_a1_paired.py:305-310,547-564`)、提示された実機書式の `Current State` と、終了後消失という事実には合っていない。
- この parser は producer の生きた枝から呼ばれる (`paper_story_a1_paired.py:3776-3791`)。historical reader に限定されていない。
- D805 が terminal 側を触らなかった理由は「そちらは `Current State` 形式を既に受理している」ためである (`D805.md:28-29`)。A-1 の現行 parser は `Current State` を受理しないため、その例外理由をA-1へそのまま適用できない。
- 到達不能な PBS-Pro visible-terminal 枝を producer に残すこと自体が、D805 の「実形式の証拠を持たない受理枝を残さない」という却下理由 (`D805.md:23-29`) と衝突する。

推奨裁定は、共有 END 語彙への拡張ではなく、次のいずれかである。

1. 新規 producer は exact disappearance だけを終端形とし、visible `scheduler-end-state` producer 枝を無効化する。旧 parser は明示的な legacy receipt reader に隔離する。
2. visible terminal を新規 producer に残すなら、実機 visible END の逐語を取得してから parser と schema を設計する。

単に現行 parser を残す案は、依頼の「合わせる」を「実機ではその枝に入らないから放置する」と読み替えている。

(c) 成果物への影響: plan のままでは明示依頼の半分が未実施となり、PBS-Pro 型の未実測受理枝が production producer に残る。逆に shared END へ直結すると受理集合を根拠なく広げる。これは段4で明示裁定が必要である。

(d) 判定: **real**。plan の「END を増やさない」は支持するが、「一切変更しない」は支持しない。

## 所見 4: 共有 leaf import の source closure が閉じていない

(a) 主張: `orchestrator/scheduler_nqsv.py` を実行時依存に追加するなら、A-1 の source binding にも追加しなければならない。plan がこれを scope 外へ送るのは不整合である。

(b) 根拠:

- A-1 が証拠化する source 一覧は `SOURCE_RELATIVE_PATHS` から派生する (`paper_story_a1_paired.py:161-180,2090-2107`)。
- source binding は各列挙ファイルの Git blob OID と working SHA-256 を記録する (`paper_story_a1_paired.py:4383-4408`)。
- その binding は submit intent (`:2500-2502,3272-3274`)、measurement (`:6757-6760`)、final consumer (`:6471-6476`) に流れる。
- 現在の一覧に `orchestrator/scheduler_nqsv.py` は無い。
- shell と Python の一覧一致を固定する meta test がある (`test_paper_story_a1_job_contract.py:243-281`)。
- plan 自身も漏れを認識している (`plan.md:157,166`) が、変更しないとしている。

(c) 成果物への影響: 新しい parser は measurement の意味を決めるのに、source-routed evidence へ含まれない。完全に閉じるなら次を同一変更面に加える必要がある。

- `paper_story_a1_paired.py:161-180` の closure。
- `tools/pegasus/paper_story_a1_paired.sh` の同期一覧。
- `test_paper_story_a1_job_contract.py:24-62,243-281,386-409` の期待値と drift test。

shell は今回の射影に含まれていないため、現 author scope のまま安全に完了できない。親が射影と scope を広げるべきである。

(d) 判定: **real**。

## 所見 5: P4 の producer と consumer は完全には対称でない

(a) 主張: exact disappearance helper の導入は正しいが、現行 receipt schema では qstat stderr を consumer が再検査できず、submission visibility も raw stdout を再解析できない。

(b) 根拠:

- 現行 `_observe_scheduler_terminal` は rc と非空 stdout しか検査せず、stderr を見ていない (`paper_story_a1_paired.py:3750-3758`)。
- plan は producer に `stderr == ""` を要求する (`plan.md:79-87,94,106`)。
- しかし `scheduler_terminal` の schema には qstat stderr field が無い (`paper_story_a1_paired.py:3678-3688`)。consumer は stdout hash と exact signature までしか再検査できない (`:3690-3740`)。
- A-2 の先例は terminal observation に stderr を保存し、consumer が空文字を要求している (`paper_story_a2_certification.py:1213-1226`)。
- submission visibility receipt も raw qstat stdout、stderr、returncode を保持せず、正規化済み `state` と `queue` だけを保持する (`paper_story_a1_paired.py:2892-2898,2957-2991`)。

(c) 成果物への影響: plan の P4 は producer を締めるが、保存 receipt 単体から同じ述語を再現できない。「全層で exact NQSV disappearance を検査した」とは言えない。完全な対称性を要求するなら qstat argv、rc、stdout、stderr と hash を receipt に加える schema migration が必要で、これは本 scope を超える。schema を変えないなら「producer-only stderr gate、consumer は保存された stdout だけを再検査」という限界を明示裁定すべきである。

(d) 判定: **real**。

## 所見 6: 呼出し元と consumer の静的閉包が plan の編集表より広い

(a) 主張: plan の本文は多くを列挙しているが、編集表と親アンカー表だけでは全 propagation path を追えない。

(b) 根拠:

- visibility producer caller: `paper_story_a1_paired.py:3138,3285`。
- group submission validator: `:3202,3397,4033,6493,8384`。
- legacy acquisition validator caller: `:6526,6700,6964,8483`。
- terminal producer caller: `:4080,4275`。
- completion validator caller: `:6560,8342,8517`。
- V3 completion は `fake_completion` を組み立て、共通 validator へ投影する (`:8269-8352`)。
- shell job body も receipt の state と queue を検査することが meta test に固定されている (`test_paper_story_a1_job_contract.py:1233-1238`)。
- 親の A-2 先例アンカー `1113-1150` は、canonical state と receipt state の一致検査 `paper_story_a2_certification.py:1150-1178` を途中で切っている。
- 親の submit observation アンカー `2960-2990` は実際には `2957-2991`。これは行ずれだけなら nit だが、source closure と shell preflight の欠落は nit ではない。

(c) 成果物への影響: producer だけ直しても、V3 completion projection、final consumer、materializer、job body のどこで同じ receipt が再検査されるかをレビューし損ねる。直接編集不要な caller もあるが、テストと review matrix には全て含めるべきである。

(d) 判定: **real**。`2957` 対 `2960` の小さな行ずれだけは **nit**。

## 所見 7: 既存テストの赤予測は条件付きで不足している

(a) 主張: plan の狭い実装だけなら、予測した一件が主な既存赤であり、fixture 置換は期待値の改ざんではない。ただし、変更面を正しく閉じる場合は追加の既存テストが赤になる。

(b) 根拠:

- 現行の cwd test は PBS-Pro fixture を直接返す (`test_paper_story_a1_job_contract.py:2385-2404`)。実機限定 queue parser にすると赤になる。
- このテストの assertion は qsub の cwd と receipt shape (`:2411-2418`) であり、qstat fixture 自体は検査対象でない。実機 fixture への置換は正当。
- source closure を正しく追加すれば、exact set、長さ、shell 一覧一致を固定する `:243-281` が更新前には赤になる。
- visible terminal producer を無効化すれば、少なくとも次が赤になる。
  - `test_paper_story_a1_job_contract.py:899-994`
  - `test_paper_story_a1_paired.py:819-845`
  - 同 `:3406-3436`
  - 同 `:3439-3472`
- plan の追加 matrix には実機 canonical QUE 正例が無い (`plan.md:118-128`)。
- 新しく導入する submission qstat の空 stderr 条件、terminal qstat の空 stderr 条件にも明示的な負例が無い。
- job body の positive test は実機 NQSV ではなく `exec_host` / `start_time` stub を使う (`test_paper_story_a1_job_contract.py:1393-1399,1569-1579`)。

(c) 成果物への影響: 狭い plan だけを緑にするなら既存一件の fixture 置換で足りる可能性が高い。しかし、source closure と P3 を正しく処理するなら plan の「既存赤は一件」は不正確になる。追加テストには canonical QUE、qstat stderr、job-body allocation qstat の実機逐語を入れるべきである。

(d) 判定: テスト欠落は **real**。cwd test の fixture 置換で期待値を変えて緑にするという疑いは **refuted**。

## 所見 8: 共有 leaf import 自体に循環や重い初期化はない

(a) 主張: A-1 から `orchestrator.scheduler_nqsv` を import すること自体は安全である。問題は import graph ではなく source closure である。

(b) 根拠:

- `scheduler_nqsv.py` の import は `re`、`dataclasses`、`typing` だけ (`scheduler_nqsv.py:7-11`)。
- module-level 初期化は二つの regex と dataclass 定義のみ (`:14-29`)。
- campaign、dispatcher、A-1 への逆 import は無く、循環を作らない。
- A-2 は同じ campaign package から既に shared leaf を import している (`paper_story_a2_certification.py:36-39`)。
- A-1 の direct CLI は relative import 前に `__package__` と `sys.path` を調整する (`paper_story_a1_paired.py:36-38`)。

(c) 成果物への影響: 起動コストや初期化順を理由に shared import を避ける必要はない。通常 import と direct CLI の双方で既存 A-2 と同じ構造を使える。

(d) 判定: **refuted**。

## 総括

plan の visibility 修正は、提示された RUN / PRR 逐語に対しては有効で、F852 の既知 blocker を除去できる。ただし plan のままでは「bench まで到達する」「変更面が閉じた」とは言えない。

段4で必要な裁定は次の四点である。

1. job body の allocation-qstat parser を射影と scope に加え、実機の `Execution Hosts(JSVNO)` / `Started Request Time` 書式で preflight を検証する。
2. 実機 Queued または Staging の全文 fixture を追加し、canonical `QUE` の正例を固定する。
3. shared END 語彙は増やさず、新規 visible-terminal producer 枝を無効化するか、実機 visible END を取得するまで legacy reader に隔離する。
4. `scheduler_nqsv.py` を A-1 source closure と shell の同期一覧へ加える。qstat stderr と raw visibility stdoutまで receipt に保存するかは schema migration として明示裁定する。

pytest は実行しておらず、本所見は静的検査である。