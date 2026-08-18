# [T-1286] / [T-1287] / [T-762] — COMMIT へ verifier 発行 receipt を要求し、新 lock を批准済み digest と比較し、ident の第 3 経路を塞いだ

2026-08-18、dev-wave `dev-wave-t1286-commit-receipt`、基準 main = `a160f4aa`
(wave 中に `c7f4a052` を取り込み)。
ユーザー裁定 (2026-08-17 /rulings 全件 第 5 回、索引 13 / 14 / 29) の実装。
索引 31 [T-1252] が「索引 13 の設計時に対象へ入れること」と明記しているため乗り合わせた。

逐語は `verbatim/`。段 1 brief、段 2 プラン、段 3 敵対 2 レンズ、段 4 裁定、段 5 実装子 3 本、
段 6 敵対レビュー 2 本と must-fix 巡を凍結した。

## 1. 本 wave の主要な発見 — 焦点走 1388 passed の下で門は開いていた

段 6 の敵対レビュー 2 本が**独立に同じ中核欠陥**へ到達した。実装は完了し、
親が実走した焦点走 23 file は 1388 passed / 0 failed だったが、その緑の下で

```
VerifyResult(trace_dir="never-read", serializable=True, n_txns=1)
```

を手で構築して issuer へ渡すだけで live receipt が発行できた。**trace parser も
verifier entrypoint も一度も呼ばれない。** 規律 2 が名指しする reward hacking の経路が、
「receipt を要求する」実装を入れた**後も**開いていた。

同型が 3 面あった。

| 面 | 攻撃 | 検出 |
|---|---|---|
| primary issuer | caller-built `VerifyResult` から capability を取得 | レンズ A |
| replay issuer | caller-built dict (`certified=true`) から replay evidence を発行 | レンズ A |
| capability 再利用 | 正常 trace を 1 回検証すれば任意 variant 用の receipt を量産 | レンズ B |

**教訓: 「receipt を要求する検査を足した」ことと「receipt が verifier 由来である」ことは別である。**
前者だけを実装してテストを書くと、テストも同じ caller-built 経路で receipt を作るため全緑になる。

## 2. 恒真の罠を実測で先回りした — live lock 32 件はすべて v1

段 1 で親が実測した。`output/campaigns/` の 30 件と
`output/insights/2026-08-04_wave-a-campaign-transport-smoke/evidence/` 配下の凍結 2 件、
**計 32 件すべてが v1 (`authority` が null)** であり、v2 certified lock は repo のどこにも無い。

`wal.py` の per-COMMIT contract 検査は v2 でも legacy key でもない lock で早期 return するため、
**live 32 件のどれでも 1 度も発火していなかった。** 新しい receipt gate を同じ v2 枝の内側へ
置いていれば、実装しても発火しない恒真な保証になっていた。
段 2 プランと段 3 の 2 レンズにこの事実を渡し、gate は lock version 分岐の**外**、
`wal.append` の prospective-record admission へ置いた。

この実測は [T-1287] の副作用評価にも効いた。批准台帳を 0 行のまま land すると新 certified lock
生成は fail-closed になるが、**v2 lock が 1 件も存在しないため live 影響はゼロ**である。

## 3. 「全 STAGE_COMMIT producer」は 5 件だった

段 2 と段 3 レンズ B が独立に同じ集合へ到達した。

| # | 場所 | sink |
|---|---|---|
| 1 | `pipeline.py` no-bench | campaign WAL |
| 2 | `pipeline.py` bench 済み | campaign WAL |
| 3 | `guided.py` `_log_eval` | campaign WAL |
| 4 | `pipeline.py` no-bench | qualification event ledger |
| 5 | `pipeline.py` bench 済み | qualification event ledger |

既存の AST gate は `pipeline.evaluate` 内の `wal.log` **2 箇所しか数えない**。
同じ関数内の `event_sink.emit` 2 箇所と `guided.py` の 1 箇所は gate の外だった。
支配点も 1 つでは足りず、`wal.append` (campaign WAL) と `QualificationEventSink.emit`
(qualification) の 2 つが要る。前者は後者を通らない。

既存の `len(commit_calls)==2` と `len==4` の assertion は**変えていない**。
それぞれ「`pipeline.evaluate` 内の WAL writer」「WAL 2 + qualification 2」という
別々の性質を pin しており、全 producer の 5 へ書き換えると既存診断の関数スコープを失う。
全数 census は別テストとして新設した。

## 4. 親 brief の誤りを 7 件撤回した

段 3 の 2 レンズが親自身の実測も攻撃対象にした結果である。

1. 「producer は 3 件」→ **5 件** (qualification emit 2 を落としていた)
2. 「`guided.py` の COMMIT は上流 assertion が守る」→ **誤り**。`cmd_evaluate` は
   `assert_complete` を経ない
3. 「pin は 2 本 + consumer 6 file」→ **production 3 + test/support 9 = 12 file**
4. 「live lock 30 件」→ **32 件** (凍結 2 件を落としていた)
5. 「順序は 762 → 1286 → 1287 → 1252」→ 撤回。批准は全 enforcement bytes 確定後
6. 「判定器候補に `s8b_oracle_judge.py`」→ 撤回。S8C exact 3 が正しい
7. 「[T-396] と編集面の重複なし」→ **撤回**。ただし後述のとおり着地結果では衝突しなかった

## 5. [T-1287] の批准 authority — レンズ A の勧告を部分 refuted した

レンズ A は「repo 内 JSONL 台帳は弱化した本人が同じ commit で批准行を足せるので自己批准を
防げない。D287 / D414 が repo 内 JSON を authority と認めていない。用意できなければ
T-1287 の機械保証を land せずユーザー裁定へ戻せ」と勧告した。

親は**脅威モデルの取り違え**と判定した。規律 2 が名指しする reward hacking の主体は
**AI 実装者**である。親は実測した — `hooks/` 配下への書き込みは Write でも Bash リダイレクトでも
**機械的に拒否される** (`guard_bash` が `hooks` を防護ツリーに含む)。
したがって台帳を `hooks/` 下に置けば AI 主体による自己批准は機械で塞がる。

残る制限は採用した。**これは hook 側の障壁であって暗号学的証明ではない。**
git を直接叩ける人間は追記できる。よって本 wave は「人間が批准したことの証明」を謳わない。
D287 / D414 が却下したのは「同一主体が書ける承認 JSON を**人間承認の authority** と見なすこと」で、
ここで必要な性質は「**AI が書けない**」であり、より弱く、実測で成立している。

外部 trust root と署名の要否は裁定パッケージへ返す。

## 6. 閉包は exact 14 → 25 path へ広げた

内訳は現行 14 + S8C 判定器 3 ([T-1252]) + 批准比較自身の自己保護 + 単位 B の receipt 実装面。

後ろ 2 つはレンズ A の [A-2] による。比較処理が閉包の外にあると**比較を改変して批准を迂回**でき、
receipt 実装面が外にあると**そこを弱化しても批准対象 digest が変わらない**。
段 6 レンズ B は exact 25・S8C exact 3・consumer 12 file のいずれも独立導出で一致した。

閉包と無関係な `14` (`approval_d291.py`、`test_s8c_preregistration_predicates.py`) は
別契約なので触っていない。

## 7. 偽 Git で批准台帳を合成できた

レンズ B の [RB-2]。批准台帳と closure の Git 呼び出しがどちらも `PATH` を許し、
`shutil.which("git")` の結果を無検証で実行していた。偽 Git を `PATH` 先頭に置けば、
**closure bytes も実台帳も変えずに**任意 digest を批准済みに見せられる。
repo に既存の hardening (`orchestrator/preregistration/blobref.py` の固定絶対 executable) が
あったのでそこへ寄せ、子環境から `PATH` を除いた。

## 8. 測定で判明した運用事実

- **closure member を編集したまま測ると `contract-loader-drift` で無関係な赤が大量に出る。**
  単位 B の初回測定 66 failed のうち **29 件がこれ**だった。commit して closure を再 pin すると
  37 failed へ落ちた。赤の帰属を誤らせるので、closure member を触る wave は
  必ず commit してから測る。
- **帰属を「触っていない file だから非帰属」で決めてはいけない。** must-fix 巡の副作用 8 件のうち
  2 件は本 wave が一度も触っていない `test_p3_autonomous_workload_trial.py` だった。
  main tip (`c7f4a052`) の checkout で走らせると **178 passed** であり、
  実測の結果 8 件すべて本 wave 帰属だった。実体は CLI subprocess の中で批准 gate が
  fail-closed になっていたことで、`ModuleNotFoundError` はその下流症状にすぎなかった。
- **[T-396] は plan と着地結果が食い違った。** T-396 の段 2 プランは
  `campaign_lock.py` の `CONTRACT_LOADER_RELATIVE_PATHS`、`contract_loader_binding.py`、
  `test_t671_source_binding.py` を編集する計画だったが、`b74bb80e` で land した差分は
  これらを 1 件も含まない。段 4 で「単位 C と衝突する」と裁定した前提は着地結果では
  成立せず、両側が触った file の積集合は空だった。
  **並行 wave との衝突判定は plan でなく着地差分で行う。**

## 9. scope 外として裁定パッケージへ返すもの

1. **layout 横断の一回限り。** 同じ lock bytes を 2 つの layout root へ置けば、各 WAL の
   消費済み集合は空なので同じ receipt が各 1 回通る。外部状態を持たない限り
   「全 layout 横断で一回限り」は証明できない。本 wave は **ledger 単位**を実装した。
   裁定文の「一回限り」をどちらで読むかの確認が要る。
2. **consumer 面の receipt 再検証。** `s1_report.py` / `tools/plotting/plot_backoff.py` /
   `p2_2_report.py` / `backoff_repro.py` は `STAGE_COMMIT` の存在だけで sample を採る。
   裁定は producer 面を名指しており、consumer 面は別裁定。
3. **外部 trust root / 署名の要否** (§5 の残余)。
4. 段 3 レンズ B の裁定パッケージ候補 4 件 (歴史 raw の型分離、qualification identity root の
   閉包収載、将来 `s8c_result_judge.py` の scope、hooks 文書の「COMMIT の唯一経路は
   `pipeline.evaluate()`」記述が `guided.py:141` と食い違う件)。

## 10. 変異 matrix — baseline PASSED・KILLED 9/9

`mutation-spec-final.json` / `mutation-out.json`。runner は焦点 9 file を
`--force-dispatch -n0 -rf` で回した。`-n0` は F346 (報告空間と collection 空間の
`@<group>` 不一致) を避けるためである。期待 node は probe 走 (全件 SURVIVED 期待) で
観測集合を集めてから完全集合として再登録した。

baseline PASSED (374 passed / 49.96s)、**KILLED 9 / SURVIVED 0 / MISMATCH 0 / TIMEOUT 0**。

9 変異はすべて **wave 前の実コードの形**を再現している。

| 変異 | wave 前の形 | 単独 killer |
|---|---|---|
| m1 receipt 要求を外す | 検査なし | 5 node |
| m2 消費済み集合の走査を落とす | 走査なし | `test_normal_wal_receipt_commits_and_duplicate_is_rejected` |
| m3 sink 側 lock digest を観測しない | receipt 自身との自己照合 (RA-1 の欠陥形) | `test_receipt_rejects_changed_lock_and_changed_payload_without_write` |
| m4 recovery の ABORT 限定を外す | 限定なし | `test_recovery_internal_writer_rejects_commit_before_write` |
| m5 批准比較の呼び出しを消す | 呼び出しなし | `test_new_certified_lock_rejects_unratified_closure_digest` ほか 1 |
| m6 批准判定を無条件受理へ倒す | 比較なし | `test_new_certified_lock_rejects_unratified_closure_digest` |
| m7 閉包を exact 14 へ戻す | exact 14 | 103 node |
| m8 判定器 3 module を閉包から外す | 未収載 | 89 node |
| m9 receipt 実装面を閉包から外す | 未収載 | 94 node |

m2・m3・m4・m6 は killer がちょうど 1 node で、**その門が守る性質を名指しするテストだけが落ちる**。
m3 は段 6 レンズ A が指摘した恒真 (lock 束縛の自己照合) の修正が実際に効いていることの直接証拠である。
m7・m8・m9 は閉包 consumer が広いため過剰決定であり、単独変異の精密な証拠としては扱わず
冗長 gate として記録する。

## 11. エージェント工数

codex 子 11 本 (plan 1・consult 2 + 失敗 2・author 3・fix 6・review 2)。
段 3 の 2 レンズは 13:31 に codex 認証の 401 で出力ゼロ即死し、prompt を変えて job-id を
変えることで再投入した (同一 prompt は「既存の完全な receipt は上書きできない」で rc=2)。
**codex 子は本 wave でも pytest を 1 件も実走できず**、測定は全巡 親が引き受けた。
