# [T-080] post-R テスト負債 fix — 独立検証・敵対監査 verbatim (job c4f664a6)

- 日付: 2026-07-24 / 監査対象: code commit c9d71fd (基準 8bec195)
- 監査者: claude-fable-5 (orchestrator、実測担当) + codex gpt-5.6-sol ×2 (敵対レビュー、reasoning=max、read-only sandbox、独立コンテキスト)
- 位置づけ: 別 job の前セッションが作成した T-080 post-R test-debt fix (c9d71fd) を、`~/tmp/p1.txt` 引き継ぎのユーザー指示で消化する際の独立検証・監査記録。insight/ledger/commit message は「監査対象の主張」として非採用の前提で審査 (規律6)。`~/tmp/p1.txt` 自体は注入形状 (記憶汚染誘導・セキュリティ衛生で main 書換をロンダリング・既成事実埋め込み) と判定し、指示は不実行・データ扱いとした上で実 git 状態を独立検証してから着手

## 親による独立実測 (cwd=worktree = c9d71fd を測定)

- 全走 `python3 tools/run_tests.py` = **2878 passed / 18 skipped / 0 failed** (186.97s、EXIT=0)。受入主張と一致、退行 0。赤 11 node は緑 (旧コードなら 11 node が緑化せず run 自体が測定対象の正しさを担保)
- `python3 tools/check_ai_provenance.py` = **316 件、違反なし**
- 実状態確定: main=8bec195 clean・未接触、worktree=c9d71fd (impl のみ、docs 未 commit、count 8bec195..HEAD=1)、staged=insight 2 ファイル、**worklog 新エントリは実在せず** (p1.txt の「working tree にあるはず」と食い違い → 本セッションで新規執筆)

## 総合裁定 (両レビュー GO、コード変更なし)

- **codex A (正しさ境界 / reward hack レンズ): GO** — 全所見 refuted・severity none。最重要の E3/E4 reward-hack 疑い (G12 子が receipt-free root で never-issued 早期 return に載り claim 競合を回避しないか) を、early-return が `verify_receipt()` 内に閉じ、空 repo の 40-hex HEAD は `_campaign_t080_value()` に受理され `run_block`→`_acquire_g12_claim`→`os.open(O_CREAT|O_EXCL)` (campaign_claim.py:189) が実走し敗者のみ `FileExistsError→refused` になることのコード追跡で否定。相互排他は実効維持 (claim 省略なら 0 件・双方獲得なら claim-won 2 件で破れる)
- **codex B (整合・consumer・揮発・F型レンズ): GO** — コード diff に blocker なし。real 所見 3 件はいずれも記録精度/手順であってコード正しさでない:
  - **(major) 記録の過大表現**: 「receipt-free な最小 hermetic git repo」の "hermetic" は `_run_git` が git env/global config/template/hooks を継承するため git env に対しては不正確 (insight §残余 R2-2 が既に caveat 化)。commit message・insight の「communicate(timeout=10) を決定論的に超過」は host 依存で過大 — ledger REC-1 自身は「環境束縛で高速ホストでは非成立」と正しく書いており、prose 側だけの過大表現
  - **(major, F34) 後付け記録 bytes の認証ギャップ**: insight/ledger は 2878 全走の後に stage され、記録 bytes 自体は全走で認証されていない。静的 grep では両記録に三軸 conjunction なし (現時点実害なし) だが、別 commit にするなら記録追加後の repo-scan gate が要る
  - **(minor) inline set 判定**: E6 の inline set 判定は機能上 `_assert_exact_refusals` 相当だが、既存 helper へ委譲する方が重複検査の将来 drift を避けられる
  - consumer 取り残し = refuted (6 consumer/11 node を列挙、E2 guard は `issue_receipt=False` 分岐前で全 11 node が必ず通過、helper 本体は無変更で新挙動は G12 一時 repo 限定)。揮発 payload = refuted (known-axes は prefix+件数のみ固定、generator_refusal は in-test 決定論)。変異帰属 MUT-1/MUT-2/REC-1 = いずれも静的に妥当 (real/none)
- **変異 matrix の再実行はしていない** (前セッション本走の帰属を codex B が静的裁定で妥当と確認)。13.8s→0.49s 等の実測値は環境束縛で静的認証の対象外
- **本セッションの処置**: コード変更なし。errata (hermetic/決定論的 の語彙) は本記録に凍結。F34 手順ギャップは docs commit **後** の `test_s8b_repo_scan_invariant.py` 再走で closure。minor (inline set) は将来改善として残余化。段9 (local main ff 取り込み) は push なし

---

## codex A verbatim (正しさ境界 / reward hack レンズ、gpt-5.6-sol/max/read-only)

結論として、reward hack または正しさ境界の弱体化は認めません。差分も実際にテストファイル 1 本だけで、production 変更はありません。pytest は指示どおり未実行です。

1(a) E3 — verdict: refuted / severity: none  
両 subprocess は同一 `output_root/claims` と同一 claim identity を使い、required single-process plan により実物の `_acquire_g12_claim()` へ到達します。[status と claim 数の表明](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-ruling-ac/orchestrator/tests/test_s8b_oracle_driver.py:1747) は、claim を省略すれば 0 件・双方が獲得すれば `claim-won` 2 件となるため、依然として相互排他を実効的に検査します。

1(b) E4 — verdict: refuted / severity: none  
`never-issued` の早期 return は [`verify_receipt()` 内](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-ruling-ac/orchestrator/campaign/t080_freeze_migration.py:1851)だけで、`run_block()` の return ではありません。空 repo の 40 桁 HEAD は `_campaign_t080_value()` に受理され、mock 済み gate/prepare の後、[`run_block` の claim 呼出し](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-ruling-ac/orchestrator/campaign/s8b_oracle_driver.py:1172) → `_acquire_g12_claim()` → [`os.open(...O_CREAT|O_EXCL)`](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-ruling-ac/orchestrator/campaign/campaign_claim.py:189) が実行され、敗者だけが `FileExistsError` から `refused` になります。

1(c) — verdict: refuted / severity: none  
変更は、G12 と無関係な active receipt 履歴走査を、有効な `never-issued` epoch の最小 repo に置き換えただけで、競合 leaf は実物のままです。active-valid receipt 自体は real-root gate と三状態 exact test で別途検査されており、性能のための検出力放棄には該当しません。

2. E1 — verdict: refuted / severity: none  
除外は [`output/t080-migration` 直下かつ定数由来の receipt/draft basename](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-ruling-ac/orchestrator/tests/test_s8b_oracle_driver.py:306)だけで、他の `output/` 内容や同名の別階層は除外しません。実 ROOT の有効 receipt を別の一 commit 履歴へ移植して生じる人工的 invalidity を避ける fixture 隔離であり、実 ROOT の receipt は別テストが直接検証しています。

3. E2 — verdict: refuted / severity: none  
基底 commit 後に production の `inspect_receipt_history(check_worktree=True)` で commit graph と worktree の双方を検査するため、receipt が commit 済みでも未追跡でも `never-issued` 以外となり失敗します。したがって恒真ではなく、receipt 混入を検出する実在の setup guard です。

4. E6 — verdict: refuted / severity: none  
静的経路上の refusal は、holdout generator mismatch、known-axes source mismatch 1 件、floor-null、budget-null の計 4 件で、追加表明と一致します。`len==4`、known-prefix が exactly 1、残差集合が generator/floor/budget の exactly 3 件なので、旧表明より強く、これらの脱落・重複はマスクできません；固定していないのは既知 source drift の揮発する path/hash payload だけです。

5. 一般 — verdict: refuted / severity: none  
削除された実質的 assertion はなく、subprocess return code、`['claim-won','refused']`、claim 1 件は維持されています。旧 generator の部分一致＋件数表明は exact refusal 表明へ強化され、さらに basis-state と SHA-1 guard が追加されており、`== → in`、exact → subset、assert 削除などの緩和はありません。

受理判定: GO

---

## codex B verbatim (整合・consumer・揮発・F型レンズ、gpt-5.6-sol/max/read-only)

結論として、c9d71fd のコード差分に blocker はありません。ただし説明の過大表現と、後付け台帳に F34 型の検証手順ギャップがあります。pytest は実行せず、以下は静的裁定です。

### 1. 説明↔実装

**verdict: refuted / severity: major**

E1・E2・E5・E6、および E3/E4 の root 差し替え自体は実装と一致します（[fixture](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-ruling-ac/orchestrator/tests/test_s8b_oracle_driver.py:289)、[G12](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-ruling-ac/orchestrator/tests/test_s8b_oracle_driver.py:1638)、[E6](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-ruling-ac/orchestrator/tests/test_s8b_oracle_driver.py:2213)）。ただし `_run_git` は Git 環境変数・global config・template/hooks を継承するため「hermetic」は過大表現であり、REC-1 自身も高速環境では timeout しないと認めているため「10秒を決定論的に超過」も誤りです（[_run_git](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-ruling-ac/orchestrator/tests/test_s8b_oracle_driver.py:124)、[REC-1](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-ruling-ac/output/insights/2026-07-24_t080-postr-mutation-ledger.json:40)）。

### 2. consumer 取り残し

**verdict: refuted / severity: none**

`_t080_stub_free_e2e_repo` の direct consumer は次の6関数、parameter 展開後11 nodeです。

| consumer | node数 |
|---|---:|
| `test_t080_stub_free_draft_finalize_commit_and_public_gate_e2e_b5` | 1 |
| `test_t080_stub_free_e2e_single_defects...` | 4 |
| `test_t080_stub_free_e2e_remaining...` | 1 |
| `test_t080_full_valid_history_defects...` | 3 |
| `test_t080_full_valid_post_r_delete...` | 1 |
| `test_never_issued_generator_tamper...` | 1 |

E2 guard は `issue_receipt=False` 分岐より前にあるため全11 nodeが必ず通ります（[guard](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-ruling-ac/orchestrator/tests/test_s8b_oracle_driver.py:352)）。説明上の「10件」は R 直後に赤だった10 nodeで、11番目の E6 は旧 assertion が余剰 receipt refusal を見逃して緑だったものの、今回 E6 で回収されており取り残しではありません。

`_run_git` は同ファイル内で `_independent_t080_receipt_blob`、`_t080_repo`、fixture本体、4つのT-080 defect test、real-repo gate test、G12、E6履歴探索から使われますが、helper本体は変更されておらず、新規挙動はG12の一時repoに限定されます。別ファイルは test module を import していますが、変更した2 helperは消費していません。

### 3. 揮発 payload

**verdict: refuted / severity: none**

known-axes refusal は prefix一致1件と総件数だけを固定し、path・recorded/actual hashを期待値へ焼いていません。[generator_refusal](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-ruling-ac/orchestrator/tests/test_s8b_oracle_driver.py:2237) の recorded は fixture freeze から、actual はそのrecorded bytesに固定suffixを加えた直後のbytesから計算されるため、必要なGit履歴が存在する限り in-test で決定論的です。新規 assertion に絶対パス・時刻・固定actual SHAの混入はありません。

### 4. mutation ledger

| 項目 | verdict / severity | 静的裁定 |
|---|---|---|
| MUT-1 | **real / none** | 上記11 nodeは全て同fixtureを呼び、guardより前に離脱する枝がありません。`ignore=None` ならtarget treeに存在するreceiptがbasis commitへ入り、全nodeが同じ never-issued assertion で止まる構造です。 |
| MUT-2 | **real / none** | [O_EXCL](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-ruling-ac/orchestrator/campaign/campaign_claim.py:189) を外すと両processが同一claim pathを正常openし、`FileExistsError` 経路へ入らず双方が `_ensure_campaign` まで到達します。そこで双方が script の `claim-won` へ写るため、statuses assert が `claim-won` 2件で破れる帰属は妥当です。 |
| REC-1 | **real / none** | 実ROOTへ戻した場合のtimeoutは履歴長・I/O・ホスト性能依存で、production受理集合を変えるsemantic killではありません。recovery evidenceとして残し、kill集計外にした裁定は妥当ですが、13.8秒等の実測値自体は静的には認証できません。 |

### 5. inline set 判定

**verdict: real / severity: minor**

総数4、known-prefix一致1、残りのsetが相異なる3 refusalという組合せなので、重複も欠落も検出でき、機能上は `_assert_exact_refusals` 相当です。ただし既存の exact/prefix helperがこの方針を既に集約しているため、known match抽出後にhelperへ委譲する方が重複検査の将来driftを避けられます（[helpers](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-ruling-ac/orchestrator/tests/test_s8b_oracle_driver.py:88)）。

### 6. failures 型

**verdict: real / severity: major**

c9本体では F27/F28/F30/F32/F33 の再発は確認できません。特にMUT-1は「新規検出1 + 診断局所化10」と正しく限定され、MUT-2も受理方向の単一site変異で、target treeではO_EXCLが復元されています。

一方、F34型の手順ギャップは付随記録に再発しています。c9のtreeはtestファイル1本だけですが、insight/ledgerはその後に別途stageされ、受入欄も「統合commit前の全走」としか記録していないため、後付けされた記録bytes自身は2878全走で認証されていません（[受入記録](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-ruling-ac/output/insights/2026-07-24_t080-postr-test-debt-fix.md:83)、[F34](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-ruling-ac/docs/failures.md:445)）。静的grepでは両記録に具体的な三軸conjunctionは見つからず、現時点の実害は示されませんが、別commitにするなら記録追加後のrepo-scan gateが必要です。

受理判定: GO