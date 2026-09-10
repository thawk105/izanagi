## 所見

1. [real] `output/insights/2026-08-24_t986-budget-approval-package/README.md:31-36,196-208`、`orchestrator/campaign/s8b_holdout_freeze.py:1392-1618`

   official eligible floor result は現物に存在しない。builder は result だけでなく同じ run directory の `manifest.json`、`journal.jsonl`、現行 build admission、統計整合、`eligible_for_refreeze=true` を要求する。ratify が approval・budget・pin を生成しても、この拒否は残る。成果物は3 path変わるが、実 repo に対する `build_v2_g1_candidate` の受理集合は空のままで、candidate の値は一つも生成されない。

2. [real] `orchestrator/campaign/s8b_holdout_admission.py:5018-5029,5056-5082,5147-5232,5335-5442`

   floor result 一式に加え、Git common directory 配下の共有 admission state が同じ campaign と完全一致しなければならない。必要なのは claims、consumed markers、lock、main ledger、attempt ledger、fresh v2 claims、空の nondefault seams、refreeze disqualification 不在である。共有 root 自体は実在するが、official result が無いため一致する campaign を選べず、現状で閉包成立を主張できない。ratify の受理集合はこの状態と独立なので、builder が落ちる状態でも approval gate だけ開く。

3. [real] `stage2-plan.md:37-58,180-184`、`orchestrator/campaign/s8b_holdout_freeze.py:1675-1685,1694-1696,1731-1736`

   ratify 直後は producer source が HEAD と異なる。一方 candidate の `generator` は実行中の worktree bytes ではなく captured HEAD blob から作られる。source は具体的な三軸 encoding を持たないよう固定されているため、closure scan もこの pin-only drift を捕捉しない。したがって floor 入力が揃えば builder は通りうるが、`generator.sha256` は pin 未設定の HEAD sourceを参照し、実際に実行した pin 設定済み source と食い違う。正しくするには exact 3 path を先に commit し、builder 側でも `SCRIPT_REL` の HEAD/worktree 一致を要求する必要がある。これは「ratify 1コマンド直後に安全に通る」と両立しない。

4. [real] `stage1-brief.md:77-78`、`stage2-plan.md:79-88`、`orchestrator/tests/s8b_v2_freeze_fixture.py:463-486`、`orchestrator/tests/test_s8b_holdout_freeze.py:1790-1839`

   既存 fixture だけでは CLI の生死確認にならない。fixture は approval・budget を直接書いて commit し、既存正例は `BUDGET_APPROVAL_SHA256` を monkeypatch している。計画した新規テストも最終的に loader と bytes を検査するだけで、ratify が編集した source を新 process が importし、その pin で builder が通る経路を検査しない。CLI の root 解決、source置換、再 import の mutant が残ってもテスト受理集合は緑になりうる。fixture を拡張し、CLI出力から新 process の builder までを接続する正例が必要である。

5. [real] `stage2-plan.md:60-88`、`orchestrator/tests/test_plain_runner_coverage.py:44-86`、`orchestrator/tests/README.md:114-140`

   新規 `test_s8b_budget_approval.py` に self-runner を付ける記述も、pytest-only allowlist を更新する記述もない。このままなら `test_every_test_file_is_self_runnable_or_allowlisted` が新規 file を拒否する。production 値は変わらないが、全テストの受理集合が赤になる。pytest fixture を多用する計画なので、`orchestrator/tests/README.md` の allowlist へ追加するのが狭い代案である。

6. [要確認] `stage2-plan.md:20-26,94-101,121-125`、`tools/issue_env_contract_activation.py:156-165`、`docs/pegasus-runbook.md:124-144`

   CLI の `repo固定 root` だけでは直接実行時の import path は確定しない。`tools/` 配下の script から `orchestrator` を importするなら、既存作法どおり `Path(__file__).resolve().parents[1]` を `sys.path` へ追加する必要がある。また Pegasus では裸の `python3` が3.9へ解決する実例があり、手動 tool は `python3.10` が正本である。相対 `tools/...` も cwd が REPO root の場合しか shell が解決できない。欠ければ approval・budget・pin は全て未変更のまま起動前に失敗する。docs に REPO root への移動と `python3.10` を明記すべきである。

7. [real] `docs/decisions.md:33371-33415,34397-34412,34626-34638,38805-38818`、`output/insights/2026-08-24_t986-budget-approval-package/README.md:141-179,196-208,225-238`

   「予算数値は未裁定」は真である。D964 は staged 運搬、D979 は生涯観測上限、D926 は official nonce束縛であり、2592/1296または2400/1200を承認していない。dossier は保留判断に必要な情報を持つが、正の operational approval を支持する根拠は持たず、両数値案を非推奨としている。したがって P3 の入力機構は作れても、現時点で推奨できるユーザー操作は「ratify」ではなく「保留」である。ユーザーが明示的に別裁定を与えた場合だけ、入力された budget 値が loader の受理集合へ入る。

## 端から端までの不足一覧

ratify が埋めるのは次の3成果物だけである。

- `output/s8b-freeze-budget-inputs/g1.json`
- `output/s8b-freeze-budget-approvals/g1.json`
- `s8b_holdout_freeze.py` の approval pin

その前提として、ユーザーの `total_bench_s`、rr20/rr80値、`approved_at`、TTY上の approver と hash確認も必要である。

ratify 後にも次が残る。

- official path規約を満たす eligible `result.json`
- 同一 run の `manifest.json` と `journal.jsonl`
- result、manifest、journal、protocol、v1、current build admission の完全整合
- 同一 campaign に束縛された共有 admission claims、両 ledger、consumed markers
- fresh・nondefault seamなし・disqualificationなしから再導出される eligibility
- floor protocol、known axes、design source、generator、および全 measurement closure path の HEAD blob整合
- producer sourceをHEADへ収容する人間の commit、または別 trust-root設計
- candidate 実行時の必須 `--floor-result` path。計画文書は `--budget` しか具体化していない
- generateまで行う場合は固定 candidate leafが未作成であること

現物では protocol・v1・known axes・generator・design sourceと submodule はHEADと一致している。一方 official floor bundleは不在である。よって本wave単独で「ユーザーの1コマンド後に builder が正しく通る」は到達不能である。

## 波及先

- `orchestrator/tests/test_plain_runner_coverage.py:44-86` と `orchestrator/tests/README.md:114-140`  
  新規 test file の集合を直接列挙する。計画への追加が必須。

- `orchestrator/tests/test_s8b_repo_scan_invariant.py:21-35`  
  実 repo の tracked・Git-visible untracked file 全体を production scannerへ渡す。新規 CLI、docs、test、ratify artifacts が検索母集合へ入る。

- `orchestrator/tests/test_s8c_preregistration_invariant.py:623-635`  
  `enumerate_repository_files(ROOT)` の全集合を再び holdout scanへ渡す。新規 fileに三軸 conjunctionが無いことが必要。

- `orchestrator/tests/test_campaign_import_invariant.py:994-1044,1078-1088,1227`  
  新規 Python toolと新規 docsを実 repo scan対象へ加える。import bootstrapと文書内コマンド表記が検査対象になる。

- `orchestrator/tests/test_campaign.py:5128-5178`  
  `tools/s8b_budget_approval.py` を含む全 production Pythonを AST parseする。

- `orchestrator/tests/output_snapshot_ignores.py:206-293,330-341` と `orchestrator/tests/test_real_repo_serialization.py:581-677,1019-1038`  
  approval・budget path は `.gitignore:17-28` で除外されず、生成後は Git-visible output snapshotの母集合へ入る。

- `orchestrator/tests/s8b_v2_freeze_fixture.py:348-495` と `orchestrator/tests/test_s8b_holdout_freeze.py:1597-1611,1762-1846,1909-1967`  
  loader、floor bundle、closure、candidate consumerの正本。ただし現状はCLI-produced pinを経由しない。

- `orchestrator/tests/test_frozen_artifacts.py:41-151,234-248`  
  exact 23 pathだけを列挙する。approval、budget、draftは追加対象でなく、この集合は変更不要である。

## 親の provisional 裁定の判定

- (P1) 不成立。approval gateを開く作用だけなら成立するが、ratify直後のdirty sourceを実行しながら candidateの `generator` は旧HEAD blobを指す。正確な端から端の条件では採用できない。狭い代案は、ratify後にexact 3 pathを人間がcommitしてからbuilderを起動し、`orchestrator/campaign/s8b_holdout_freeze.py:1731-1736` の前で `SCRIPT_REL` のHEAD/worktree一致を検査すること。1コマンドを維持するなら、`stage1-brief.md:54-55` の別data pin設計を裁定パッケージへ返す必要がある。

- (P2) 成立。draft instanceをrepo外へ置いても、tracked docsからdossierと再生成コマンドへ到達でき、draftはconsumer入力ではない。`--out` は絶対pathを推奨し、repo rootとsymlink境界を検査する条件付きでよい。

- (P3) 成立。ただし成立するのは「ユーザーが数値を自分で束縛する機構」であり、「現在、正の推奨値がある」という意味ではない。dossierは保留判断には十分だが、positive ratificationの根拠は未成立である。docsは§6と§8も明示的に読解導線へ含め、ratify例を「別途数値裁定済みの場合だけ」と表示すべきである。

## 総括

- ratifyはapproval、budget、pinの3点しか閉じない。
- official eligible floor resultと一致するrun bundleは現物に無い。
- live admission stateも選択するofficial campaignが無いため閉包を証明できない。
- P1はdirty producerとHEAD generator参照を食い違わせる。
- 既存fixtureはCLIからbuilderまでのproduction配線を証明しない。
- 新規test fileはplain-runner meta-testへの登録が抜けている。
- Pegasus向けcommandは`python3.10`、REPO root、import bootstrapを明示する必要がある。
- 数値未裁定という親の認識は正しく、現証拠の推奨は保留である。
- よって「1コマンドで承認成果物を作る」は実装可能だが、「1コマンド後にbuilderが正しく通る」は本wave単独では到達不能である。
- pytestやcandidate builderの実走はしておらず、本所見は指定範囲の静的読解による。