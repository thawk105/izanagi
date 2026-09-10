# [T-367] 段 4 裁定 — plan v2 と変異事前登録

基準 commit: 58cd6ff (local main 追従済み)。材料 = `brief.md`、
`/work/1/SFC/tanab/dev-wave-jobs/t367-qdel-guard/` の `stage2-plan.md` / `stage3-lensA.md` /
`stage3-lensB.md`。

## 1. 所見の裁定

両レンズが独立に同じ blocker を挙げた (A-1 / B-1) ため、real 確定として最優先で採る。

| # | 所見 | 判定 | 採否 | scope |
|---|---|---|---|---|
| A-1 / B-1 | request ID と state が非結合で、malformed rc=0 応答が RUN を QUE と誤判定させる | **real** (独立 2 例) | 採用 | 内 |
| A-2 前半 | request ID grammar が緩く `-` 始まりが option に化ける | real | 採用 (grammar 検査のみ) | 内 |
| A-2 後半 | discovery が job name 先頭 10 文字一致だけで旧 job を発見しうる | real | **不採用** | **外** → 裁定パッケージ |
| A-3 | qstat→qdel は非 atomic で TOCTOU が残る | real | 採用 (主張限定 + characterization test) | 内 |
| A-4 | gate 拒否後の孤児 job が mutation harness の source 復元と衝突する | real | **不採用** | **外** → 裁定パッケージ |
| A-5 / B-3 | P2 (one-shot) の根拠が事実誤認。transient で消せる QUE を孤児化する | **real** | 採用 (bounded retry) | 内 |
| A-5 P3 | END 履歴と矛盾する fresh QUE/HLD は UNKNOWN であるべき | real | 採用 | 内 |
| A-6 | 例外境界が自己矛盾。once-only と `attempted` の意味が曖昧 | real | 採用 | 内 |
| A-7 / B-7 | v2 据え置きでは guarded qdel の proof chain が成立しない | real | 採用 (`cleanup_policy` 必須化のみ。v3 昇格は外) | 内/外 |
| A-8 / B-9 | 親の実測 3 件の一般化が過大 | **real** | 採用 (brief 訂正) | 内 |
| A-9 | 4 callsite 閉包が機械的に固定されていない | real | 採用 (meta-test) | 内 |
| B-2 | fake scheduler の状態列で 2 テストが偽緑 (L1411 trusted 側 / L1480) | **real** | 採用 | 内 |
| B-4 | cleanup が既存 deadline の外へ最大 95 秒はみ出し観測不能 | real | 採用 (cleanup 絶対予算 + 所要記録) | 内 |
| B-5 | gate 許可後の qdel 失敗に残存警告がない | real | 採用 | 内 |
| B-6 | 自己適用が壊れた際の bootstrap 手順がない | real | 採用 (親の受入手順として) | 内 |
| B-8 | runbook §3/§8/rc=16 節が新契約と食い違う | real | 採用 (段 7 で親が docs 差分) | 内 |

### scope 外へ返す 2 件 (段 9 で裁定パッケージ化)

- **A-4 孤児 job の lifecycle。** 「UNKNOWN では殺さない」は裁定 (b) が受け入れた帰結であり、
  残る孤児の後始末 (unresolved-job lease、次回投入・source 復元・worktree 廃棄の停止、
  mutation harness との lifecycle 統合) は [T-368] と同じ束の新規設計である。本 wave で
  実装すると裁定されていない受理集合変更を既成事実にする。**本 wave は「殺さない」と
  「残存を人間に見せる」までを担い、reconciliation は返す。**
- **A-2 後半 discovery の同定強度と A-7 の v3 昇格。** 前者は request 発見の受理集合変更、
  後者は receipt schema の版管理で [T-366] と近接する。いずれも本裁定の射程外。

### P1 / P2 / P3 の最終裁定

- **(P1) 維持。** ただし根拠を訂正する。F47 の恒久対応は「qsub は人間の端末から」であって
  qdel 掃除ではない (A-5)。正確には「request 不在時の**保険的 cleanup を廃止する**」であり、
  「F47 と衝突しない」ではない。裁定文言「QUE/HLD/STG を示したときだけ」に従う。
- **(P2) 撤回。** 私の根拠 (immediate retry は可視性遅延用) は事実誤認だった —
  実コードは rc=0/request 不在で即 break し、retry するのは非ゼロ transient だけである
  (`dispatch_compute.py:1125`)。**transient 分類に限り bounded retry を採る。**
  permission・RUN・END・request 不在は即拒否で retry しない。裁定文言は「最後に得た fresh
  rc=0 観測が QUE/HLD」で満たされる。
- **(P3) 維持し強化。** END では qdel しない。加えて、監視ループが terminal END を観測した
  経路 (L1300) で fresh 観測が QUE/HLD を返した場合は矛盾として **UNKNOWN 扱い**にする。

## 2. plan v2 (段 2 plan からの差分だけを書く)

段 2 plan の骨格 — `_fresh_qstat_gated_qdel()` 新設、4 callsite 集約、`state_history` 不変、
receipt v2 据え置き、既存 14 テストの (a)(b)(c) 分類 — は採用する。次を差し替える。

1. **target-bound parser を新設する (A-1/B-1)。** gate は `_scheduler_state()` の全体走査を
   使わない。対象 request ID の block に束縛して state を取り、次をすべて満たすときだけ
   取消可能状態と判定する: (i) 正規化 ID がちょうど 1 件可視、(ii) その block の state が
   ちょうど 1 件、(iii) `Request State` と `Current State` が併存するなら正規化後に一致、
   (iv) 正規化結果が QUE または HLD (STG→QUE は既存正規化に合わせる)。
   複数 ID・複数 state・矛盾はすべて `UNKNOWN` として拒否する。
   **監視ループ側の `_scheduler_state()` は変更しない** (受理集合を変えないため)。
2. **request ID grammar を gate で検査する (A-2 前半)。** 正規化後の ID が
   `先頭英数字 + 許可文字` に合致しない場合は qstat も qdel も打たず `reason=malformed-request-id`。
   `--` separator は NQSV での挙動が未実測のため**導入しない**。
3. **transient 限定 bounded retry (A-5/B-3)。** `_classify_qstat_response()` が `transient` を
   返した場合だけ、既存 `immediate_qstat_attempts` と同じ上限 (既定 3) まで再試行する。
   `permission` は即拒否。rc=0 で不在・RUN・END・UNKNOWN も即拒否 (retry しない)。
4. **cleanup 絶対予算 (B-4)。** gate 呼び出し時に cleanup 開始時刻を取り、既定
   `cleanup_budget_s` (90 秒) を超えたら retry を止めて拒否する。receipt へ
   `cleanup_elapsed_s` を記録する。`_run` の per-command timeout は既存 30 秒のまま
   (per-command remaining timeout は作らない — 過剰実装)。
5. **END 履歴との矛盾 (P3 強化)。** gate に「監視ループが terminal END を観測済みか」を
   渡し、True のときは fresh が QUE/HLD でも `reason=terminal-history-conflict` で拒否する。
6. **例外境界と once-only (A-6)。** 判定部 (grammar 検査・qstat・parse) と実行部 (qdel) の
   例外境界を分離する。**qdel の結果を得た後は gate 側の例外でそれを上書きしない。**
   `attempted` は「qdel command の起動を要求した」の意味に固定し、成功可否は
   `returncode` / `exception` / `job_may_remain` で表す。
7. **qdel 失敗時の残存警告 (B-5)。** 許可後の qdel が rc≠0 または例外なら
   `job_may_remain=true` を receipt へ書き、見送り時と同じ人間向け残存警告を出す。
8. **`cleanup_policy` の必須化 (A-7/B-7)。** gate に到達した receipt は必ず
   `qdel.cleanup_policy = "fresh-qstat-gate/v1"` と `qdel.gate` object を持つ。
   これで「旧 unconditional 実装 / gate bypass」と区別できる。schema version は v2 のまま。
9. **TOCTOU の主張限定 (A-3)。** helper の docstring とテスト名で、保証は
   「**直前 snapshot が取消可能だったときだけ qdel を発行する**」であり
   「qdel 時点で RUN でない」ではないと明記する。QUE snapshot 後に RUN へ遷移する
   characterization test を置き、残余リスクを可視化する。
10. **テスト分類の穴 (B-2)。** L1411 trusted 側と L1480 に gate 用 state を明示追加し、
    暗黙 `DONE` (tuple 枯渇) で負例が通らないようにする。gate qstat 回数も固定する。
11. **caller 閉包の meta-test (A-9)。** `_best_effort_qdel` の production caller が
    gate helper 1 箇所だけであることを固定する meta-test を置く。

## 3. 変異事前登録 (`DW-M01`)

実装後に anchor (old 逐語) を確定し `DW-M07` で再検証する。受理集合を**縮小**する wave なので
過剰拒否を検出する正例 (M08) を必ず含める。

| ID | 種別 | 変異の意図 | 期待 |
|---|---|---|---|
| M01 | negative | gate の許可状態集合へ `RUN` を加える | RUN 非取消テストが KILLED |
| M02 | negative | **意味論版**: classification が `transient` でも stdout に対象 ID + QUE があれば success-visible として扱う | rc≠0 + ID + QUE 応答のテストが KILLED |
| M03 | negative | target-bound parser を全体走査へ戻す | mixed-block / 矛盾 state / bare `State` テストが KILLED |
| M04 | **diagnostic pin** | request 不在の `gate.reason` 語彙を変える | 受理集合を変えないため kill でなく診断感度 pin として別枠記録 (`DW-M08`) |
| M05 | negative | END 履歴矛盾の検査を外す | terminal-history-conflict テストが KILLED |
| M06 | negative | qdel 失敗時の `job_may_remain` を落とす | qdel 非ゼロ/例外テストが KILLED |
| M07 | negative | **multi-replacement**: cleanup 予算検査を 3 箇所すべて同時に外す | 予算超過テストが KILLED |
| M08 | **positive** | gate を常に拒否する (過剰拒否) | QUE / HLD / STG / `Current State` 単独の正例が KILLED |
| M09 | negative | request ID grammar 検査を外す | malformed ID テストが KILLED |
| M10 | negative | **alias 版**: `_best_effort_qdel` を別名へ束縛して呼ぶ caller を足す | caller 閉包 meta-test が KILLED |
| M11 | negative | qdel 後の once-only latch を外す | 二重 qdel / 結果喪失テストが KILLED |

各変異は「手前に同じ入力を拒否する検査がないこと」「赤理由が一つに絞れること」を
実装後にコードで確認してから走らせる。確認できない変異は登録を取り消し、実効 gate へ再照準する
(`DW-M01`、F28)。M02 / M07 / M10 の形は段 6 レビュー 2 の指摘 (表層変異では浅い KILL または生存)
を受けて実装前登録から差し替えた。M04 は受理集合を変えないため kill 集計から外し、
`DW-M08` の diagnostic sensitivity pin として別枠に記録する。

## 4. brief の訂正 (A-8/B-9)

- 「RUN 中に qdel を打つことを既存テストが実証」→ 正確には **fake scheduler が qdel command を
  観測した**ことの実証であり、実 NQSV が RUN job を削除する証拠ではない。実機 kill は未実測。
- production dispatch caller は `run_tests.py` だけでなく `tools/check_ai_provenance.py` もある。
- 成果物影響は 2 層に分ける。**現在の直接影響** = 開発テスト / provenance の transport receipt と
  受入証拠。**将来の影響** = [T-360] が task 追加の裁定を経てこの経路を再利用した場合の
  mutation trial。現行 task enum は `tests` / `provenance` の 2 つで campaign 本走は通らない。
- `mutation_harness` は dispatcher の HEAD blob SHA を runner identity に含めるため、
  **本変更後は旧 mutation ledger を `--resume` できない**。段 6 の変異は fresh に採る。

## 5. 受入手順 (B-6)

実装子の完了後、親は次の順で走らせる。前段が赤なら後段へ進まない。

1. `python3 -m py_compile tools/pegasus/dispatch_compute.py` (import 破損の早期検出)
2. `python3 tools/run_tests.py orchestrator/tests/test_pegasus_dispatch_compute.py -q`
3. 受入全走 + `python3 tools/check_docs.py`
4. 変異 matrix (fresh ledger)

rc=16 (dispatch infra failure) を受けたら、receipt の `outcome` / `qdel.gate` /
`qdel.job_may_remain` を確認し、旧 request の終了を `qstat` で確認するまで再投入しない。
