# [T-2632] B-4 の適格な赤 precursor の在庫確保 — 本 wave では不成立

- authority: none
- default_effect: no-state-change

可変状態の正本ではない。可変状態の正本は `docs/worklog.md` 末尾と現行 phase doc である。
本書は wave `dev-wave-t2632-b4-red-precursor-stock` の一次資料を凍結したものである。

- 観測日時: 2026-09-16 15:46 JST
- 機体: `pegasus02` (login node、読み取りのみ)
- worktree: `/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2632-b4-red-precursor-stock`
- HEAD: `d97c423bdd14e0b416cb4f585d350e6c2b251287`

## 結論

**適格な赤 precursor の在庫は 0 件のままである。本 wave では 1 件も調達しなかった。**

**これは「適格な赤 precursor が構造的に得られない」という意味ではない。** 新しい正当な base
合成 campaign で自然な検疫赤が生じる可能性は否定していない。その live probe は実施していない。
本書が確定したのは、**今日この checkout で調達が成立しない理由**であって、供給の不可能性ではない。

到達範囲を 3 つに分けて読むこと。混同しない。

| 量 | 値 | 意味 |
|---|---|---|
| 適格性述語の第 1 項に該当する行 | 0 | `whiteboard.result == "rejected"` の行 |
| 全条件を満たす適格在庫 | 0 | 第 1 項に加え workload・bootstrap・参照点・digest 非汚染を満たす行 |
| `analysis_manifest` の成立 | 不成立 | 必要 201 行に対し適格 0 行 |

## 在庫の再計数 (親が現物で実測)

`git ls-files` で引ける `loop_state.json` は 3 件だけである。全木走査でも新しい供給源は無く、
hit した他の `loop_state.json` はすべて同じ 3 file の worktree 内複製だった。

```
--- output/campaigns/p3-s4-loop-s4-autonomous-0b53a387/loop_state.json
616a5a1d83a7881c90d37469f1fa69a117d72fb5cd6f54f18ff031b63f34279f
rows=4 rejected=0 fail=0 success=4 iteration=4
--- output/campaigns/p3-s5-sort-loop-s5-sort-autonomous-3be89e0d/loop_state.json
f89b8b7c1d46f17dd16b25c68069b46f69e9dd638dd9026e7a8e8d3ce1ec6cd8
rows=1 rejected=0 fail=0 success=1 iteration=2
--- output/campaigns/p3-s8a-trigger-loop-s8a-trigger-autonomous-3f72ecd5/loop_state.json
18d5e40bd4b4c8e6a4d09b8d4ac4b94c0ffb173b79092dfc7a6abe7e1aa2c79d
rows=2 rejected=0 fail=0 success=2 iteration=2
```

**合計 7 行。すべて `success`。`rejected` は 0 行、`fail` も 0 行。**
2026-09-14 の census (`output/insights/2026-09-14_t2547-b4-descriptive-erratum/census-verbatim.md`)
と一致する。**mtime は根拠にしない** (同 census が撤回済み)。

本書は前回 census を置き換えない。今回の差分は「再計数の一致」「既存 checkpoint の停止条件」
「新規開始条件の照合結果」「適格性 3 条件の照合結果」の 4 点だけである。

## 供給側 — なぜ今日 1 件も採れないか

### 既存 3 campaign からの回収はできない

適格性述語の第 1 項に該当する行が 0 だからである。回収可能数は 0。

### 既存 base campaign の単純継続はできない

`orchestrator/campaign/p3_s4_loop.py:164-165` が `MAX_ITER = 10` と `MAX_WALLTIME_S = 3600` を
置き、`:1265,:1271` が経過時間で `StopDecision(True, "budget-walltime")` を返す。
入口停止なら `run_one_iteration` を呼ばず `"ran": False` を返す (`:2488-2493`)。
base checkpoint の `start_wall` は 1 時間上限を大きく超えている。

**この停止は旧 state に限る。** checkpoint が不在なら `:2483-2485` が
`LoopState(start_wall=time.time())` で新しく始める。したがって
「既存 state の継続不可」を「新規 campaign も起動不可」へ広げてはならない。
checkpoint の時刻や予算を書き換えて再開する案は採らない。

### 新規 base campaign の起動経路は実在するが、本 wave では起動しない

`tools/pegasus/p3_s4_loop_pegasus.sh` が sanctioned な起動面である。必要な入力は
`IZANAGI_S4_REPO_ROOT` / `IZANAGI_S4_EXPECTED_HEAD` / `IZANAGI_S4_EVIDENCE_ROOT` /
`IZANAGI_S4_THIRDPARTY_SOURCE_ROOT` と、非 fixture 経路では `IZANAGI_S4_PROPOSAL_PATH`
(`:19-20`, `:95-96`, `:588-593`)。

起動しない理由は 3 つある。

1. **job body が AI worktree 配下の repository root を拒否する** (`:116-119`)。
   固定 SHA の専用 checkout が別途要る。この checkout はこの機体に現存しない
   (`/work/SFC/tanab/izanagi` は `/work/1/SFC/tanab/izanagi` への別名であって別 checkout ではない)。
2. **自然な proposal が要る。** 実 LLM は CLI が呼ばない。
   「実 LLM (planner/coder/critic) はメインセッションが spawn する」(`p3_s4_loop.py:2544`)。
   `--run-iteration` は spawn 済み role の構造化出力を受け取る口である (`:2567-2569`, `:2768`)。
3. **これは CC 合成 campaign の実行であって開発 wave の作業ではない。** 依頼は
   「本題の在庫確保だけ」であり、専用 checkout の新設・hydrate・qsub・単独性確保は
   その本題に含まれない。

## 適格性側 — ここが決定的

**仮に自然な検疫赤が 1 件出ても、今日は適格と確定できない。**
適格性述語の実装は `orchestrator/campaign/p3_b4_analysis_ledgers.py:922-936` にあり、
`calibrated_workload_member` / `bootstrap_member` / `reference_is_unique` を呼び手からの
真偽値として受け取る。型検査は `:337-338` の `type(value) is not bool` だけで、
**所属の真実性は機械検証されない。** よって「正直に真と認定できるか」を人間側で確かめる必要がある。
3 条件とも、今日は真にできない。

| 条件 | 判定 | 根拠 |
|---|---|---|
| `bootstrap_member` | **真にできない** | 事前登録 §6 が名指す publication root `output/b4-prerun-publication` が**不在**。`output/insights/2026-09-16_t2545-b4-publication-root/README.md` 自身が「事前固定した集合であることを証明したとは言わない」「publication の固定名成果物 5 種も `output/` 配下に 0 件」と明記する |
| `calibrated_workload_member` | **真にできない** | 事前登録 §5 の「校正済み `PerfConfig`」欄が**未記入**。現行 CLI は `perf = default_perf()` を渡す (`p3_s4_loop.py:2734`)。その `default_perf()` は「性能比較用 calibration ではない — 規律4」と自ら書く (`:1564-1566`) |
| `reference_is_unique` | **真にできない** | 共通参照点は祖先の certified snapshot の throughput receipt を `PerfConfig` と `env_tag` の一致で特定する必要がある (事前登録 §5.1.1 の共通参照点)。§5 の `env_tag` 欄が**未記入** |

**したがって供給側を仮に満たしても、適格在庫は 0 のままである。** 3 条件の整備はいずれも
別タスクであり、依頼の scope 外である。

なお、**§5 の「赤 precursor の母集合」欄が未記入であることは、これら 3 条件を偽とする理由には
ならない。** 同欄は適格判定と選択の**結果**を書く欄だからである (§5.1 の解除条件は
`analysis_manifest` の実在を記入条件としている)。親は当初この循環した論法を使っており、
段 2 と段 3 の両方がこれを倒した。**空欄を所属偽の証拠にしない。**

## 少数を得た場合に何が許されるか (裁定済み)

**D1986 項 4 が既に裁定している。** 「適格な行が必要数に満たない間は実施不可のまま走らせない。
選択関数と母集合の契約は変えない。少数の赤 precursor に対して許されるのは記述としての報告までで、
実験の実施と有意差の主張は起こさない。」

したがって在庫を急いで作る動機は無い。**T-2633 を再裁定待ちへ戻さない。**
`docs/archive/worklog-phase3-0916-1527.md` も同項を「裁定済み → 残件なし」として記録している。

## 採らなかった経路と、その理由

D1936 項 8 が明示的に不採用としたもの、および本 wave の禁止事項に当たるもの。

- **成功例への置換** — 赤の代わりに成功例を母集合へ入れること。
- **母集合を作るための追加基盤** — 赤を人工的に量産する仕組み、検疫を落としやすい proposal の
  生成器、fixture から母集合を合成する経路。
- **n の切り下げ** — 201 を小さくすること、少数でも実走してよいとすること。
- **供給源の変更** — `p3-s4-red-s4-red-consumer-9a1897c4` の rejections digest にある赤 3 件は、
  同 campaign が whiteboard を持たないため第 1 項を満たさない。1 件は `src_token=fixture` で
  合成ループの産物ですらない。供給源は合成ループ campaign の whiteboard のままとする。
- **`--no-build` 経路での赤生成** — 実装が「配線確認専用であり campaign の入力として受理しない」と
  明記する (`p3_s4_loop.py:2527-2529`)。ただしこれは凍結述語の独立した除外項ではなく、
  本 wave の運用判断である。
- **sort / trigger の赤の流用** — §5 の選択済み driver は `base (silo-backoff-magnitude)` であり、
  §5.1.1 は driver の差替えを `design_not_feasible` とする。
  (なお sort / trigger では oracle 拒否・auditor 拒否も同じ `record_diff_reject` 経路を通って
  `rejected` に写る。**記録上は diff-quarantine でも、原因は純粋な diff 検査に限らない。**
  この区別は base の読みには影響しないが、将来の読者が原因を誤読しないために記す。)

## 記録上の分類 — `rejected` と `fail` の違い

`project_whiteboard` の想定値は `success` (certified 緑) / `fail` (verify・liveness 赤) /
`rejected` (diff 検疫 reject) である (`p3_s4_loop.py:1178-1184`)。
base の `rejected` 書込みは 3 箇所すべてが `record_diff_reject` 経由である
(`:1877`, `:1899`, `:1911`)。verify・liveness 赤は `fail` になる (`:1792`, `:1968`)。

解析 adapter も同じ区別を保つ。`terminal_reason == "diff-quarantine"` かつ `REJECTED` なら
`B4BlockStatus.REJECTED`、それ以外の `ABORT` かつ `FAIL` なら `ABORTED`
(`p3_b4_analysis_adapter.py:497-508`)。

**これはアーム結果の写像であって、precursor の `fail` を適格な `rejected` に読み替える許可ではない。**

## 既存 gate の保証範囲 (限定して記す)

`p3_b4_analysis_ledgers.py:1071-1083` は `_attempt_is_eligible` で選別し、不足時に
`B4DesignNotFeasible`、充足時に先頭 201 行を返す。`p3_b4_prerun_issuer.py:835-843` が
その戻り値で拒否する。これらは恒真ではなく実際に分岐する。

**ただし保証するのは「入力述語・順序・件数・台帳整合性」までである。**
所属真偽値の根拠の正しさ、および未申告の予定 attempt が存在しないことは、単独では証明しない。

## 次の一手 — 誰が何をすれば在庫が 1 件増えるか

順序どおりに行う。1 と 2 は互いに独立で、3 は両方が揃ってから行う。

1. **封印済み prerun publication の発行。** 事前登録 §6 が名指す `output/b4-prerun-publication` へ
   bootstrap 集合を封印発行する。発行器は実在する (`orchestrator/campaign/p3_b4_prerun_issuer.py`)。
   これが済むまで `bootstrap_member` を真にできない。
2. **§5 の校正済み `PerfConfig` 欄と `env_tag` 欄の記入。** 対象動作点で再実測した artifact の
   path と hash を書く。既存の較正・床値タスク (T-2288 系) の完了が前提になる。
   これが済むまで `calibrated_workload_member` と `reference_is_unique` を真にできない。
3. **専用 checkout からの通常 base campaign の起動。** AI worktree 配下でない固定 SHA の checkout を
   用意し、hydrate 済み third-party source root と fresh evidence root を与え、
   メインセッションが spawn した planner-v4 / coder-v4-autonomous の自然な proposal を
   `IZANAGI_S4_PROPOSAL_PATH` へ渡して起動する。自然発生した diff 検疫 reject を回収する。
   **赤の発生自体は保証できない。** 既存 7 試行での自然発生率は 0/7 である。
4. **得られた少数の扱いは記述報告までに留める** (D1986 項 4)。実験の実施と有意差の主張は起こさない。

## 本書が閉じないこと

- **新しい通常 base campaign で自然な赤が生じるか。** live probe は未実施である。
  今回の読み取り結果をその成功・失敗の代用にしない。
- **自然発生率。** 既存 7 試行で 0/7 という観測はあるが、率の推定には足りない。
- **T-2632 は未達のまま残る。** 本 wave はこれを消さない。

## 収録物

| file | 内容 |
|---|---|
| `verbatim/stage1-brief.md` | 親の段 1 brief (訂正前。段 4 で倒れた完了条件を含む) |
| `verbatim/stage2-plan.md` | 段 2 plan (codex read-only) |
| `verbatim/stage3-sol.md` | 段 3 敵対相談 (正しさ境界と凍結契約) |
| `verbatim/stage3-luna.md` | 段 3 敵対相談 (裁定整合と実効性) |
| `verbatim/stage4-ruling.md` | 親の段 4 裁定 (所見 15 件の real / refuted と採否) |
