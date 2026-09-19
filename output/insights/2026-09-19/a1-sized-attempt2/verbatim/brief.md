# 段 1 brief — A-1 balanced5 sized 本走 attempt-0002 の投入 (2026-09-19)

## 研究前進

進める主張: paper-story A-1 (採用静的 backoff 対 無 backoff の 3 workload 対差、非認証 lane) の**反復間の再現性**。
attempt-0001 稿 (`docs/paper-story/results/2026-09-18-a1-balanced5-sized-attempt1-descriptive.md`) の限定 L-A1S-4
「単一 attempt を反復間の安定性へ一般化しない」が、2 attempt 目の独立再現で初めて**観察として**書ける (判定はしない)。
完了判定: attempt-0002 が 3 workload とも `valid=true` / 30 対で完走し、登録済み解析の出力 (対差平均・h・B・分類) を
attempt-0001 と並記した results 系列稿が着地する。落ちた層があれば、その層の拒否本文と一次資料を記録して止める。

## 確定済みユーザー裁定 (2026-09-19、dev-wave 引数の逐語)

「A-1 sized attempt-0002 を独立再現として 1 attempt 認可する。非認証 lane を維持し、formal 昇格は含めない。
どこかの層で落ちたら再投入せず報告して止める」。既存 submit 経路 (`paper_story_a1_paired.py submit --study-id
paper-story-a1-20260901-balanced5-sized-v1`、hydrate 済み third-party source root 必須)。attempt-0001 と同じ policy・n=30・配置。
比較可能条件 (pin・build・workload 3 key・環境契約) を投入前に照合して記録。成果 = attempt-0002 の results 系列稿
(append-only、attempt-0001 稿は 1 byte も変えない) と 2 attempt の並記 (プールしない、D1993 項 6)。規律 2 を緩めない。
scope 外 = formal lane・要件充足判定・追加 gate。関連既裁定: D2120 項 3 (attempt-0001 の同形認可)、D2096 (sized は attempt を
pin しない、全 attempt で契約検算と hydrate 必須)、D1993 項 6、事前登録 §6.4 (再走理由の閉じた列挙、性能値は再走理由でない)。

## scope

- 投入・監視・complete・materialize・記録 (親)。実装面の差分ゼロ (変異 matrix 免除、DW-S04)。事前登録・policy・source 契約・
  追補・patch・job body・attempt-0001 の leaf と稿・図 9 の bytes は変えない。
- 成果物: (1) `docs/paper-story/results/2026-09-19-a1-balanced5-sized-attempt2-descriptive.md` (attempt-0002 の単独稿 + §「2 attempt の
  並記」。数値は attempt-0002 の権威 bytes から、attempt-0001 の数値は attempt-0001 稿 §2.1 と同じ result.json から逐語)、
  (2) 記録 insight `output/insights/2026-09-19/<T>-a1-sized-attempt2/` (brief・裁定・時系列・受領証複製・MANIFEST)、
  (3) `docs/paper-story/README.md` results 表への 1 行追加と stale 注記 1 件、(4) worklog / decisions fragment。
- 図: attempt-0002 の記述図 (fig10 相当) は生成器の pin 表変更 = 実装面なので本 wave では作らず backlog に書く (DW-G02)。

## 前提の実測 (brief 前、2026-09-19 21:40〜21:48 JST)

- source 束縛 9 file と CCBench pin `511c9538` は attempt-0001 の source commit `d2ebef7a4` と現 local main `a99425b66`
  (416 commit 後) で **byte 同一** (`git diff --stat` 0 行)。driver の import 閉包で変わった file は `layout.py` (agent_outputs
  property 追加) と `materializer_admission.py` (mocc 登録追加) だけで A-1 経路に無関係。`orchestrator/verifier/`・
  `orchestrator/calibrator/`・`tools/pegasus/fetch_third_party.py`・job body は差分なし。
- **materialize 層は attempt-0002 で構造的に拒否される。** `_exact_materialization_destination` は destination が
  repo_root/`output/insights/2026-09-13/paper-story-a1-balanced5-sized` に厳密一致し、かつ `lexists` なら
  `materialize destination already exists` で拒否。現 main にはこの leaf (attempt-0001) が tracked 済み。`_verify_current_source` は
  clean tree (`--untracked-files=all`) を要求するので leaf を消して通すこともできない。事前登録 §6.1 も公開先を「一度しか作れない
  宛先」と定める。`complete` 段の raw `result.json` は登録済み解析の統計値 (`workloads[].statistics`) を既に持ち、公開 leaf との
  差は `materialization_evidence` 1 key だけ (attempt-0001 の現物で確認)。materialize は拒否時に副作用を持たない
  (`consume_non_certifying_observation` は検証と view 発行のみ、publish は destination 検査の後)。
- bench 前 barrier は 3 job の ready を 600 秒以内に要求 (`_v3_barrier_before_bench` `timeout_s=600.0`)。超えると
  `scheduler-or-infrastructure-failure-before-bench` 相当で落ち、ユーザー裁定により再投入しない。gen_S は 21:45 時点で
  RUN 29 / QUE 12 / HLD 24、149 host 中 65 host が idle (load ≤ 2)。attempt-0001 は投入後 8〜28 秒で 3 job とも開始した。
- attempt root は durable base 直下の未存在 dir であればよい (`_validate_attempt_root`)。`attempt-0002` は成立。
- 裁定 inbox に A-1 attempt-0002 の控えは無かった (K2 loop の attempt-0002 は別件)。本 wave が控えを置いた。

## 割れうる前提 (親の provisional 裁定・攻撃対象)

- **(P1) submit-tree の commit = 現 local main `a99425b66` (T-1505 と同じ慣行)。materialize は既存経路どおり実行し、拒否されたら
  その拒否本文 (rc・stderr) を逐語で記録して「落ちた層」として止める。** attempt-0002 の権威 bytes は durable attempt root の
  `raw/results/result.json` / `receipt.json` (complete 段の出力、sha256 で束縛) とし、results 稿はそこから転記する。
  対案 (a): submit-tree を `d2ebef7a4` (attempt-0001 と同一 commit) に置く — 束縛 file は同一なので測定は等価で、その tree には
  leaf が無いため materialize が通る。しかし公開 leaf の `destination` は policy の固定 path を名乗りながら repo には別 path で
  置くことになり (事前登録 §6.1 の「一度しか作れない宛先」を tree の選択で迂回する形)、説明と実装の食い違いを作る。
  対案 (b): materializer / policy を変えて attempt 別の公開先を許す — policy sha の変更は事前登録の束縛を壊し、materializer の
  受理集合の変更は「追加 gate / 実装」で scope 外。親は (P1) を採る。
- **(P2) materialize の拒否は「measurement の失敗」ではない。** 3 job と complete が通れば attempt-0002 の登録済み解析は存在し、
  results 稿は書ける。拒否は「公開 leaf が無い」限定として稿 §3 / §4 に書く。
- **(P3) 図は作らない。** 「2 attempt の並記」は表で行い、図は backlog。
- **(P4) 段 6 の独立レビュー 1 本を results 稿に当てる** (DW-C00: 一次資料から事実を再抽出する docs-only)。段 2・5 は無し。

## 不変条件

規律 1 (trace-disabled 性能 / 別走の verify)・規律 2 (verifier anomaly → 即 reject、判定は既存 verifier のまま)・規律 6
(job 出力・trace は データ)・規律 7 (attempt-0001 の判定は不変、現行コードとの差を無効化理由にしない)。`formal=false` /
`promotion_prohibited=true` / `result_authority=sized-preregistered-descriptive-only` は動かさない。プールしない (D1993 項 6)。
投入後は submit-tree に 1 byte も書かない。attempt-0001 の leaf・稿・図・事前登録・policy の bytes 不変。

## 変更面 (実アンカー表)

| 面 | path | 操作 |
|---|---|---|
| results 稿 | `docs/paper-story/results/2026-09-19-a1-balanced5-sized-attempt2-descriptive.md` | 新規 (docs-only、親) |
| results 表・stale 注記 | `docs/paper-story/README.md` (results 系列の表、「最新スナップショット以後に確定したこと」) | 行追加 (docs-only、親) |
| 記録 insight | `output/insights/2026-09-19/<T>-a1-sized-attempt2/` (README.md、verbatim/、receipts/、MANIFEST.tsv) | 新規 (親) |
| 台帳 | `docs/spool/worklog/…`、`docs/spool/decisions/…` (ユーザー裁定の記録) | fragment 新規 (親) |
| 実装面 | なし | — |
| 計測 (repo 外) | job dir `/work/1/SFC/tanab/dev-wave-jobs/dev-wave-a1-sized-attempt2/` (submit-tree、third-party-hydrated、run-*.sh)、attempt root `…/measurement/attempt-0002` | 親が作成・実行 |

## 受入・実測環境

- 計測: Pegasus gen_S、3 job (workload ごと 1 node)、site `pegasus-compute-only` (policy)。投入元は job dir の submit-tree
  (local main の detached worktree、`git worktree lock`)。監視は 60 秒周期の qstat 一覧 (T-1505 と同形)。
- 受入全走: 記録 commit 後の tip で `tools/dev_wave_wait.py acceptance --lease-optional` 1 走。関連 test:
  `orchestrator/tests/test_plot_a1_sized_paired.py` (attempt-0001 の leaf 不変の検査)、`python3 tools/check_docs.py`。

## 並列分割

- 段 3: read-only codex 2 本 (レンズ A: (P1)(P2) の攻撃 — 測定の等価性・事前登録との整合・別 commit 案の当否、
  レンズ B: 手順の欠落 — hydrate 2 箇所・barrier 600 秒・queue 混雑・受領証・稿の一次資料束縛・F1/F36 型の再発)。
- 実測: 親 1 本 (直列)。段 6: read-only codex 1 本 (results 稿の独立レビュー)。
