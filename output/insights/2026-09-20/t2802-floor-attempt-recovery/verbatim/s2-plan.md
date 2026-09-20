## 帰属の確認

以下の略号は、指定 worktree の現物を指す。行番号は変更前のもの。新規関数は挿入先の行番号を示す。

- **H** = [orchestrator/campaign/s8b_holdout_admission.py](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2802-floor-attempt-recovery/orchestrator/campaign/s8b_holdout_admission.py)
- **T** = [orchestrator/tests/test_s8b_holdout_admission.py](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2802-floor-attempt-recovery/orchestrator/tests/test_s8b_holdout_admission.py)
- **F** = [orchestrator/campaign/s8b_floor_campaign.py](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2802-floor-attempt-recovery/orchestrator/campaign/s8b_floor_campaign.py)
- **FT** = [orchestrator/tests/test_s8b_floor_campaign.py](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2802-floor-attempt-recovery/orchestrator/tests/test_s8b_floor_campaign.py)

**二乗の機序は確認できた。ただし代表 node の経路は measurement-generation であり、v1 の main 行ごとの `_claim_digest` は代表 node の直接の律速ではない。**

H:5230 の候補関数は、target を H:5236、各 marker を H:5270、各 A 行を H:5287 で完全再導出する。通常の第 i 回消費直前には既存 marker と A 行が各 i−1 件なので、N 回の呼出し数は `Σ(1+2(i−1))=N²`。98 回なら 9,604 回となり、提示 profile と一致する。

- v1：H:4690 で claim 読取、H:4737 で main ledger 全読、H:4740–4753 で**全 floor 行**の shape・key・digest を検査する。
- measurement-generation：H:4817 で claim 読取、H:4882→4940 の helper が H:4946 で main ledger 全読。該当 schema・role・digest の行を選び、該当行の shape は H:4885 で検査する。

代表 node `FT:10183::test_measure_runtime_error_records_launch_failure` の経路は次のとおり。

`FT:10192 _run_campaign` → `FT:819,851 _run_campaign_core` → `F:7923 reservation` → `F:7935 finalize` → `F:7942,7954 measure wrapper` → `F:6246,6293 _run_session` → `F:5992,6012 measure_attempt` → `H:4349 consume_attempt_ticket` → `H:4372,5320 candidate`。

reservation は H:1704 で `_MEASUREMENT_GENERATION_CLAIM_SCHEMA` を作り、finalize は H:1926–1930 で generation digest を state に設定する。そのため H:4398 の legacy 分岐には入らず、H:4410→4564 が `_MEASUREMENT_GENERATION_ATTEMPT_SCHEMA` の marker を作る。

## 設計

**既存 wrapper の signature を維持し、内部の memo 対応関数へ分割する。memo は候補関数のローカル変数だけとする。**

H:4670–4955 を次の責務へ分ける案を採る。

```python
# 既存 signature を維持。毎回、memo なしで完全再導出する。
def _canonical_floor_attempt_ledger_row(
    *, root: Path, marker: Mapping[str, object],
) -> dict[str, object]: ...

# 新規。H:4670 付近へ挿入。
def _canonical_floor_attempt_ledger_row_with_memo(
    *, root: Path, marker: Mapping[str, object],
    memo: dict | None,
) -> dict[str, object]: ...

# 新規。各 schema の既存 claim/main 検査を順序どおり移す。
def _derive_floor_attempt_claim_projection(
    *, root: Path, claim_digest: str, attempt_id: str,
) -> _FloorAttemptClaimProjection: ...

def _derive_measurement_generation_floor_attempt_claim_projection(
    *, root: Path, claim_digest: str, attempt_id: str,
) -> _FloorAttemptClaimProjection: ...

# 新規。H:4782 / 4921 の既存 constructor 呼出しを移す。
def _floor_attempt_document_from_projection(
    *, projection: _FloorAttemptClaimProjection, attempt_id: str,
) -> dict[str, object]: ...
```

`_FloorAttemptClaimProjection` は claim、canonical key、main、manifest SHA、attempt_ids、schema、および generation 経路の cell-effect/generation digest を保持する private なデータ型。module に cache インスタンスは置かない。保持した dict/list を変更しない。

処理順は以下とする。

1. schema dispatch と marker の exact shape・version・role・digest・attempt_id 検査を、H:4675–4689 / 4801–4816 と同じ順に毎回行う。
2. memo key は `(attempt_schema, claim_digest)`。候補関数内では schema が一つに固定されるが、内部 helper の衝突を避ける。
3. miss なら schema 別 projection helper を呼ぶ。**attempt_id を渡し、既存位置で coverage を検査してから main を読む。**
4. hit でも `attempt_id in projection.attempt_ids` を必ず検査する。
5. projection と今回の attempt_id から既存 constructor を呼び、今回の marker 全体との equality を毎回検査する。
6. **marker equality まで成功した projection だけ** memo に格納する。失敗・部分結果は保存しない。

H:5235 に空 memo を作り、H:5236、5270、5287 の三箇所だけ memo 対応 helper を使う。target が最初の memo 登録になり得る。走査順、filter、path・identity・A 行検査、最後の判定は変更しない。

H:4796 の generation 専用 helper も既存 signature の wrapper として残し、その専用 shape 検査を維持する。H:4940 `_measurement_generation_main_ledger_row` は変更不要。H:5052、5676、T:2197 の呼出しをそのまま保てる。

**先に全 claim/main を読み込む eager な index 化はしない。** target→marker 順→A 行順の最初の例外を変えないためである。

## 受理集合の対応表

ここでいう一致は、**一呼出し中に読取対象と読取結果が安定した root 状態**についての `(戻り値、例外型、str(exception))` の一致である。後述のとおり、lock を無視した同時変更や一過性 I/O 障害まで含む実行履歴の完全一致は保証できない。

| 検査 | 旧：発火位置 | 新：発火位置・維持方法 |
|---|---|---|
| target の先行検査 | H:5236 | 同じ最初の位置で memo 対応 helper。directory 列挙より先 |
| marker exact shape・schema・role | v1 H:4680–4687、generation H:4801–4810 | 内部 helper の毎回実行する前段。message をそのまま移す |
| digest / attempt_id の型・値 | H:4688–4689、4812–4816 | memo lookup より前に毎回実行 |
| claim 読取不能・非 canonical bytes | H:4690 / 4817→1346 | miss の同じ位置で同じ reader。reader の message を保存 |
| claim shape・key・digest/identity | H:4691–4719、4820–4859 | schema 別 projection helper に原順序で移す |
| attempt coverage | H:4720–4727、4871–4879 | miss は list の shape・重複・membership を原位置で検査。hit は今回の membership を同じ message で検査 |
| entry_kind・seams | H:4728–4734、4861–4869 | miss で原順序を維持。v1 は coverage 後、generation は coverage 前 |
| main ledger の bytes/JSON | H:4737 / 4946→1384 | miss で既存 `_read_ledger` を使用 |
| v1 main shape・key | H:4738–4753 | miss ごとに従来どおり全 floor 行を順番に検査。digest 不一致行も除外しない |
| main 行数≠1 | H:4754–4757、4951–4953 | 既存抽出と message を維持 |
| generation main shape | H:4885–4887 | 従来どおり一意に選択した行だけを検査 |
| manifest SHA・main≠expected_main | H:4759、4780–4781、4889、4917–4919 | projection 導出内で同じ順序・同じ値の出所を維持 |
| constructor による値検証 | H:4782→4613、4921→4564 | miss/hit とも既存 constructor を呼ぶ |
| marker≠expected／MUT-A2 | H:4791–4792、4933–4935 | 毎回実行。marker の field を projection に混入させない |
| directory 不在・unsafe entry | H:5255–5263 | 変更なし |
| marker bytes・対象 schema/role filter | H:5264–5269 | 変更なし。対象外でも bytes 読取は先に行う |
| 非 canonical file 名 | H:5271–5272 | 毎 marker、完全再導出後に変更なく検査 |
| marker identity 重複 | H:5276–5277 | 変更なし |
| A 行 filter・完全再導出 | H:5281–5287 | filter は変更せず、対象行は毎回 marker と同じ検査へ |
| A identity 重複 | H:5291–5292 | 変更なし |
| A 行の marker 不在 | H:5293–5295 | `floor attempt ledger row has no consume marker` を維持 |
| A 行≠marker | H:5296–5297 | `floor attempt ledger differs from its marker` を維持 |
| target 不在 | H:5300–5303 | 全検査終了後に `None` |
| target≠canonical_target | H:5304–5305 | 同じ比較・message |
| target の A 行あり | H:5306–5307 | completed 判定より先に `None` |
| completed／MUT-A6 | H:5308–5310 | `completed attempt cannot be reissued` を維持 |
| 正常 M+A− | H:5311 | canonical marker を返す |

**反証を試みた結果：**

- 「同 claim なら検査済み」として coverage まで省く案には反例がある。最初は正規 attempt、二件目は未登録 attempt なら、旧実装だけ H:4727 / 4879 で拒否する。本案は membership を毎回残す。
- v1 で coverage を main 導出後へ動かす案にも反例がある。未登録 attempt と壊れた main が併存すると、最初の message が変わる。本案の miss helper は attempt_id を受け取り、原順序を保つ。
- claim 固有の不正が二件目で初めて検出される静的状態はない。最初の利用時点で同じ不正が発火し、memo 登録前に候補関数を抜ける。成功した claim について省くのは、同じ入力に対して成功済みの検査だけである。
- v1 の全 floor 行検査は、最初の成功した projection 導出で全対象行を通る。hit で再走査を省いても、**検査対象行の集合は減らない**。generation 経路にこの全 floor 行 shape 検査を追加してはならない。旧実装が検査しない無関係行まで拒否する変更になる。
- target 不在でも先に全 marker/A 行を検査する挙動を維持する。早期 `None` は不可。

## lock 前提

H:699–726 の `_locked` は同じ lock inode に `LOCK_EX` を取得し、context 終了まで保持する。候補関数の通常呼出しは consume の H:4361、cut6 query の H:5340 の内側にある。

確認した main ledger 書込みは次の四箇所。

| 書込み | lock の根拠 |
|---|---|
| floor finalize H:1909 | H:1860 の `_locked(state.root)` 内 |
| oracle reservation H:2169 | H:2129 の `_locked(root)` 内 |
| R33 transaction apply H:3168 | H:3210 / 3472 経由。通常入口は H:3519–3522、4061–4062 の lock 内 |
| n-pilot reservation H:3797 | H:3757 の `_locked(root)` 内 |

claim の公開も floor H:1760、oracle H:2158、n-pilot H:3786 は各 reservation の同じ lock 内。**R33 は別経路**で、H:3171–3173 の `_r33_publish_exact` による claim 公開も上記 lock の内側にある。「claim は reservation の `_write_exclusive` だけで書く」という説明は不十分である。

P1 の限界も明記する。

- `_append_ledger`（H:1517）と `_write_exclusive`（H:1212）自体は lock を取得しない。
- `_recover_n_pilot_transactions_locked`（H:3191）や `_r33_apply_committed_transaction_locked`（H:3112）は呼出し側の lock 契約に依存する。
- journal writer は lock を取らないことが H:4362–4364 に明記されている。ただし本 memo の入力は journal ではなく、候補関数は受け取った `completed_attempt` を変更しない。
- advisory lock を無視した直接書込みや、一回目は成功し二回目だけ失敗する I/O は memo の有無で観測差を作れる。

したがって、**確認した通常 production 経路では P1 が成立するが、lock があらゆる書込み・障害を物理的に排除するという証明ではない。** 今回は新 gate を追加せず、この既存契約を前提にする。

## test 計画

追加位置は **T:2766 の既存 cut6 群直後**。補助 fixture は **T:1827 / 1895 付近**とする。既存 `_issued_cell` と既存期待値は変更しない。

1. **旧経路との比較用参照実装**

   `_floor_attempt_recovery_candidate_reference_locked` を test 内に置く。H:5236–5311 の現行走査・filter・判定を保存し、target、各 marker、各 A 行について memo なしの `_canonical_floor_attempt_ledger_row(root=..., marker=...)` を呼ぶ。結果は戻り値、または例外型と message 全文として比較する。共通 helper の誤りを見逃さないよう、下記負例には期待 message の固定 literal も置く。

2. **複数 attempt・複数 claim の正例**

   新規 `test_cut6_candidate_matches_reference_across_consumption_sequence`。T:1827 の構築方法を使う別 fixture `_issued_cells_for_recovery` から admissions 全体・schedule を返す。少なくとも二 cell、各 cell 二 planned attempt を含む消費列を作る。journal は各 consume 前に対応する start を追加する。

   各段階で、marker 不在、M+A−、M+A+ を新旧比較する。M+A− は T:1881 `_crash_floor_after_marker`、期待文書は T:1849 を使う。target 以外の claim と、同 claim の既存 marker が同時に存在する状態を含める。

3. **二件目以降の負例**

   新規 `test_cut6_candidate_rejects_later_marker_like_reference` を `claim-mismatch / extra-key / noncanonical-filename / attempt-not-covered` で parameterize。同 claim の正規 marker を先に通し、名前順でも二件目以降になる対象を選ぶ。新旧 message 全文と固定 literal を照合する。

   新規 `test_cut6_candidate_rejects_later_attempt_row_like_reference` は二件目以降の A 行の `campaign_run_id` 改竄、marker 不在、A identity 重複を扱う。単なる A 行改竄は H:5287 の完全再導出で先に拒否されるため、期待 message は通常 `…marker differs from claim and ledger` になる。H:5297 の message を無理に期待しない。

4. **順序・検査範囲の負例**

   新規 `test_cut6_candidate_preserves_claim_error_precedence`：未登録 attempt と main 不正を併置し、coverage が先に発火することを固定する。v1 の coverage→entry/seams と generation の entry/seams→coverage の違いも含める。

   新規 `test_cut6_candidate_preserves_main_validation_scope`：v1 は別 claim の floor 行 shape 不正も拒否、generation は無関係行の意味的 shape 不正を新たに拒否しない。ただし非 canonical ledger bytes は双方で拒否する。

   v1 は現行 `_issued_cell` では作れないため、旧 schema の claim/main/marker を明示的に構築する小さい別 fixture を追加する。v1 の claim v1/v2 と generation を parameterize する。

5. **memo の寿命・回数**

   新規 `test_cut6_projection_is_once_per_claim_per_call`。既存 reader を委譲して数え、candidate 一回につき各 claim 読取・main 読取が一回、marker 読取は全件であることを確認する。二回目の呼出しで再読され、呼出し間で改竄した claim が拒否されることも確認する。

既存 T:2633、2668、2676、2685、2699、2714、2729、2750 はそのまま維持する。今回は静的確認のみで、pytest の成否は報告しない。

## 変異候補

親の事前登録候補は以下の七件。すべて単独変異として扱う。

| 変異 | KILL を期待する node |
|---|---|
| memo hit 時、marker の `campaign_run_id` で expected を上書き | 新規 `test_cut6_candidate_rejects_later_marker_like_reference[claim-mismatch]` |
| memo hit 時、marker exact-key 検査を省き、extra key を比較前に捨てる | 同 `[extra-key]` |
| memo hit 時、attempt membership 検査を省く | 同 `[attempt-not-covered]` |
| canonical filename 比較 H:5271 を省く | 同 `[noncanonical-filename]` |
| A identity 重複検査 H:5291 を省く | 新規 A 行負例の duplicate parameter |
| main≠expected_main 検査 H:4780 / 4917 を省く | 新規 main 検査：shape・identity は正しく、`records` だけ claim と異なる行 |
| completed 拒否 H:5308 を省く | 既存 `test_cut6_completed_session_forbids_reissue_of_same_attempt`（T:2750） |

**等価変異一件、SURVIVED 期待：** A 行の二つの identity 要素を `str(...)` で包む処理（H:5289）を外す。canonical constructor の成功後は双方とも検証済み文字列なので、値と辞書 key は変わらない。

注意点：

- H:5296 の A≠marker 比較だけを消しても、同じ identity は同じ安定した claim/main から同じ canonical 文書に再導出されるため、静的 root では KILL できない可能性が高い。
- marker identity 重複も、同 identity の canonical path が一意で、別名なら先に H:5272 で拒否される。KILL 用には到達可能な **A identity 重複**を選ぶ。
- これらの防御的検査は production から削除しない。変異の KILL を成立させるために authority helper を偽装する test は採らない。

## 効果見積り

一呼出しについて、marker 数を k、A 行数を a、利用する claim 数を c、main ledger の読取費用を L、claim 読取費用を C とする。

- 旧：おおむね `(1+k+a)×(C+L+claim/main検査)`。
- 新：`c×(C+L+claim/main検査)` に、全 marker 読取、A ledger 全読、各文書の constructor・coverage・比較が残る。
- directory sort も残る。全 campaign では marker 読取・文書検証・A 行比較の二乗成分が残り、全体が線形化するわけではない。
- claim 数も attempt 数とともに増える条件では、projection 部分にも二乗性が残る。

提示 profile には `_read_canonical_document` と `_read_ledger` の**個別累積秒がない**。したがって、一回の C と L を別々の実測値としては見積もれない。得られるのは `9.1 s / 9,604 ≈ 0.95 ms` という、再導出以外の走査費用も含む混合平均だけである。

代表 fixture は FT:154–166 に十二 cell、FT:373 に既定八 session/cell がある。98 回なら新しい projection 導出回数は最大 `98×12=1,176` 回で、旧 9,604 回の約12.2%。混合平均をそのまま当てる粗い概算は約1.1秒で、ここに毎 marker の読取・構築・比較が残る。

したがって、**候補部分の作業仮説は約1〜3秒、代表 node 全体は約2〜4秒程度**と置く。ただし未測定の幅であり、「1秒未満」を受入条件や既成効果にはしない。

段5の単独 `--durations` は機能・所在確認、段6の焦点走と交互 A/B を効果確認とする。提示資料が指摘する login `/tmp` の fsync 差もあるため、login 単独秒から受入効果へ換算しない。

## A/B 改変点

参照 launcher は [run-measure.sh](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2766-pairing-ab/run-measure.sh)、系列は [run-series2.sh](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2766-pairing-ab/run-series2.sh)。改変版は本 wave の job dir に置く。

- `run-measure.sh:16–19` の固定 WT/TIP を条件別にする。A は `b7f970dfa` を完全 SHA に解決して固定した clean base worktree、B は完成した実装 tip に固定した wave worktree。
- `:39–43` の B 専用 pairing env 切替を削除する。両条件の env を一致させ、`IZANAGI_ACCEPTANCE_SHARDS=3` を維持する。
- `:74–78` の HEAD/clean 検査を選択した条件の SHA に対して実施。`:97–99` の終了後検査も条件別 SHA と照合し、不一致・dirty を無効走として扱う。
- `:93` の空 argv `python3 tools/run_tests.py` 直接投入を維持。待ち手、merge、warm-up は追加しない。
- `:126–144` の run metadata に選択 worktree と条件別期待 SHA を記録。成果物コピーと SHA256 照合（`:101–124`）、直列 lock（`:35–36`）を維持する。
- `run-series2.sh:11–15` の系列を本 wave の `A,B / B,A / A,B` に置き換える。無効対の扱い・走数上限は段4で固定し、結果を見て変更しない。
- 集計器は「A/B が同一 SHA」を要求する旧規則を、**A は固定 base、B は固定 implementation、各条件内では全反復同一 SHA**へ変更する。今回は異なるコードの比較であり、同一 SHA 比較とは記述しない。
- 一次指標を追加する。**三 shard の junit の testcase から、`orchestrator/tests/test_s8b_floor_campaign.py` に属する `time` を合算**する。top-level junit は重複加算しない。
- file 属性または検証済み classname 対応で対象を同定し、件数と testcase identity も保存する。B に追加した admission test の時間は floor 指標へ含めない。
- 対ごとの worker 秒差 `A−B`、率 `(A−B)/A`、それぞれの中央値と条件別中央値差を別量として出す。最遅 shard の JUnit wall は二次の記述指標。SHA、緑、成果物、逐次投入の検算も維持する。

## 総括

per-call memo は採用可能な局所案である。成立条件は、**成功済み claim/main 射影だけを保存し、marker 検査・attempt coverage・constructor・全体比較を毎回残すこと**。

計画上の修正点は三つある。代表 node は generation 経路、「1秒未満」は未確立、重複した防御検査の削除を必ず KILL できるとは限らない。実装では検査順序と message を固定し、到達可能な負例で変異を検証する。ファイル変更・テスト実行は行っていない。
