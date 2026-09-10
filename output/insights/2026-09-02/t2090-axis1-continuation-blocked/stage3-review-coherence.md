## 重大な所見

1. **quota 修正後も、既知の条件 1 失敗で各 leaf の最初の応答後に停止する。継続取得にはならない。**

   - file:line: [runner.py:2040](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2090-axis1-openalex-continuation/orchestrator/axis1_search/runner.py:2040) で page 条件の最初の失敗を取得し、quota 停止を優先した後、[runner.py:2160](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2090-axis1-openalex-continuation/orchestrator/axis1_search/runner.py:2160) で `blocked_on_ruling` を返す。次 cursor へ進む [runner.py:2249](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2090-axis1-openalex-continuation/orchestrator/axis1_search/runner.py:2249) には到達せず、後継 checkpoint も発行しない。baseline 自体が条件 1 を `interpreted_query_mismatch` としており、先行実測も 92/92 頁で同じ失敗を確認している。
   - 実効性: quota 失効修正により Q1 の page 1 は発行できるが、新窓で残量が十分なら直後に `blocked_on_ruling` となる。次セッションが旧 `000084` を再実行すると同じ page 1 を再発行し続ける。77 leaf の `--query-id` 起動も、多頁 leaf は最初の頁で止まる。
   - 成果物への変更: 「blocker は quota の自己施錠だけ」という前提を撤回し、T-2091 を取得継続の前提にする必要がある。[decisions-excerpts.md:33](/work/1/SFC/tanab/dev-wave-jobs/2026-09-01_t2090-axis1-openalex/decisions-excerpts.md:33)〜45 の D1207 も、構造的に壊れた述語のまま既存枝を継続せず amendment を先に行うよう要求している。条件を変えずに取得だけ続けるなら、それ自体が新たな裁定対象であり、本プランの範囲では閉じていない。正例テストにも、実在する `interpreted_query_mismatch` 応答後の状態を入れる必要がある。

2. **登録 commit への worktree 張り替えと、窓間の bundle 保存・復元手順が機械的に閉じていない。**

   - file:line: [plan.md:65](/work/1/SFC/tanab/dev-wave-jobs/2026-09-01_t2090-axis1-openalex/codex/plan.md:65) は同じ path で `d0ba65c01…` から `C_reg2` へ張り替えるだけとしている。一方、checkpoint は [probe-checkpoint-000170.json:2](/work/1/SFC/tanab/dev-wave-jobs/2026-09-01_t2090-axis1-openalex/probe-checkpoint-000170.json:2) の絶対 root を持ち、[run_axis1_search.py:122](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2090-axis1-openalex-continuation/tools/run_axis1_search.py:122) と [validator.py:1110](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2090-axis1-openalex-continuation/orchestrator/axis1_search/validator.py:1110) が厳密一致を要求する。
   - 実効性: 現在の旧 commit worktree では bundle 2,124 files が untracked だが、local main/C_reg2 側では同じ files が tracked である。単純な checkout は「untracked files would be overwritten」で止まる。また、この実行用 worktree は現在 `git worktree lock` されていない。さらに、各窓で増える evidence は事前に作る `C_reg2` には含められないため、worktree を消して `C_reg2` を再構成するだけでは最新 checkpoint を復元できない。
   - 成果物への変更: コード追加ではなく運用手順を補う必要がある。初回張り替え時の baseline byte 照合と安全な tracked/untracked 調停、worktree lock、各窓終了後の最新 bundle の独立した永続保存、次セッションでの「`C_reg2` の木を再構成 → 最新 bundle を同じ絶対 path へ復元 → manifest digest と main checker を再確認」を明記すべきである。

## 軽微な所見

- **4 file は「Q1 の旧 checkpoint を新 commit へ移行する案 A」全体の変更面であり、77 leaf 取得の最小面ではない。**

  - file:line: [run_axis1_search.py:115](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2090-axis1-openalex-continuation/tools/run_axis1_search.py:115)〜125 と [check_axis1_search.py:97](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2090-axis1-openalex-continuation/tools/check_axis1_search.py:97)〜107 は checkpoint を渡した場合だけ commit を比較する。
  - 実効性: `--query-id` で始める77 leafには両変更とも不要で、新しく発行される checkpoint は最初から `C_reg2` を持つ。必要なのは quota 失効を直す `runner.py` と、新旧 artifact 混在を受ける `validator.py` の2 fileである。
  - 成果物への変更: 77 leaf を先行させる最小案なら2 fileに縮められる。Q1も同じ wave で継ぐなら `run_axis1_search.py` が必要になる。`check_axis1_search.py` は正式な historical-checkpoint preflight も整合させる場合だけ必要で、HTTP 発行自体には不要である。

- **fail-closed とする異常時刻のテストがプランにない。**

  - file:line: [plan.md:19](/work/1/SFC/tanab/dev-wave-jobs/2026-09-01_t2090-axis1-openalex/codex/plan.md:19) と [plan.md:93](/work/1/SFC/tanab/dev-wave-jobs/2026-09-01_t2090-axis1-openalex/codex/plan.md:93) は欠落・parse不能・naive時刻・負の reset を失効扱いしないと約束するが、テスト節は期限内の正常値しか列挙していない。
  - 実効性: runtime state は [runner.py:651](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2090-axis1-openalex-continuation/orchestrator/axis1_search/runner.py:651) で読み込まれ、異常値の扱いを誤ると予約 gate を解除しうる。
  - 成果物への変更: 欠落、`Z`/offset付き、naive、parse不能、負値、時計巻き戻りを個別に固定した parameterized test を追加する。

- **file:line の照合結果は1件だけ不一致。**

  - 実効性: author が誤った helper を編集する可能性がある。
  - 成果物への変更: plan の参照行だけ修正すればよい。

| plan の参照 | 現物 | 判定 |
|---|---|---|
| `runner.py:230` | `QuotaObservation` | 一致 |
| `runner.py:651` | `_quota_from_mapping`。`_load_persisted_quota` は [runner.py:695](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2090-axis1-openalex-continuation/orchestrator/axis1_search/runner.py:695) | **不一致** |
| `runner.py:1625` | 初回 persisted quota load | 一致 |
| `runner.py:1685` | retry 前の再読 | 一致 |
| `runner.py:1765` | 応答 quota の観測 | 一致 |
| `runner.py:2103` | 応答後の予約 gate | 一致 |
| `runner.py:2269` | `_resume_from_checkpoint_impl` | 一致 |
| `runner.py:2299` | catalog request builder | 一致 |
| `runner.py:2381` | public `resume_from_checkpoint` | 一致 |
| `run_axis1_search.py:114/118/122/170` | checkpoint block、commit/root検査、resume 呼出し | すべて一致 |
| `validator.py:933/968/1085/1105/1110` | expected ID、bundle検査、checkpoint処理、commit/root検査 | すべて一致 |
| `check_axis1_search.py:97/103` | checkpoint preflight と commit 比較 | 一致 |
| `checkpoint.schema.json:1` | checkpoint v2 schema | 一致 |
| `runner.py:695/1243` | bundle quota と ledger prefix path | 一致 |

## 親 brief への所見

- [handoff.md:76](/work/1/SFC/tanab/dev-wave-jobs/2026-09-01_t2090-axis1-openalex/handoff.md:76) と [handoff.md:138](/work/1/SFC/tanab/dev-wave-jobs/2026-09-01_t2090-axis1-openalex/handoff.md:138) の「残る唯一の blocker」は、**最初の request 発行だけに限れば正しい**。複数頁・次セッションまで含む T-2090 の成果としては、条件1停止が残るため誤りである。成果物では「初回発行 blocker」と「継続取得 blocker」を分離すべきである。

- [handoff.md:135](/work/1/SFC/tanab/dev-wave-jobs/2026-09-01_t2090-axis1-openalex/handoff.md:135) の3点運用は、現時点の pristine baseline を一度検査するところまでは成立している。しかし、次窓の checkpoint bytes は登録 commit に含まれないため、「同じ path に登録 commit を再構成する」だけでは復旧しない。成果物に窓ごとの永続保存元と復元手順が必要である。

- [handoff.md:119](/work/1/SFC/tanab/dev-wave-jobs/2026-09-01_t2090-axis1-openalex/handoff.md:119) の「新事実4取り下げ」は妥当である。指定 baseline は `bundle_validation_complete=true`、`exact_identity_map=true`、`incomplete_checkpoint_counts={missing:79, not_run:77, present:0}` を返しており、main checker が部分 bundle を最後まで検査できるという訂正を確認した。

## 予算見積りの検算

- page size は [catalog.json:142](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2090-axis1-openalex-continuation/docs/related-work/claim-survey/2026-08-29-axis1-search-catalog.json:142)〜156 のとおり200。Q1 evidence は `declared_total=726`、`actual_count=200` なので `ceil(726/200)=4` 頁、残り3 requestという計算は正しい。

- 1窓96 requestは1件少ない。`remaining=1000-10n` とすると、96 request 後は40であり、`40-30>=10` なので97件目を発行できる。97件後に30となり停止する。したがって、すべて10 creditという仮定下の上限は**97 request**。ただし契約どおり、実運転は各応答 header を正本とし、この数字を gate に使ってはならない。

- 「77 leaf は最低77 request」は完走予算として誤り。catalog では Q3 と Q6 の37 leafずつ、計74 leafが独立第2走必須である。最低でも、

  `Q1残り3 + 単走3 leaf×1 + 複走74 leaf×2 = 154 request`

  となる。最低でも2窓が必要である。

- 既存の診断記録は78 leafの第1走相当で92頁を観測している。これを頁数が大きく変わらないという推定に使うと、baseline取得済み1頁を引いた第1走残り91頁に、第2走74〜85頁を足して**残り約165〜176 request、2窓程度**になる。これは推定であり、各 leaf の保存済み `meta.count` がないため確定値ではない。

- よって「5日以上」は、現存する92頁実測と74本の第2走義務からは支持されない。桁違いではないが、2窓推定に対して2倍以上大きい。なお現行 runner は条件1で各頁後に止まるため、T-2091未解決のままではこの完走予算自体を消費する経路がない。

## 検査したが問題を見つけられなかった面

- **最初の1 requestまでのコード経路:** historical checkpoint commit の限定移行と quota 失効判定を計画どおり実装し、worktreeの張り替えを安全に終えれば、Q1のpage 1を止める別のコード gateは見つからなかった。catalog digest、bundle root、run ID、完全 request、prefix ledger は既存証拠と整合している。

- **案Aのmixed-commit bundle:** 現 bundle のcheckpoint 169本、ledger 580本、page 593本はすべて旧 commit `d0ba65c…` で、checkpoint–ledger不一致0件、page–ledger不一致0件だった。現行 [validator.py:1105](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2090-axis1-openalex-continuation/orchestrator/axis1_search/validator.py:1105) は新 manifest と旧checkpointの混在を拒否するが、プラン記載のartifact単位検査へ置き換えれば、旧169本と新artifactの共存を妨げる別のschema条件は見つからなかった。全体 checker は `bundle_validation_complete=true` / `exact_identity_map=true` まで到達できる見込みである。ただし条件1により全体の `passed` と `axis_complete` はfalseのままである。

- **案B:** `exact_identity_map` は [validator.py:561](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2090-axis1-openalex-continuation/orchestrator/axis1_search/validator.py:561)〜627 の「catalog全IDについてstatus mapを生成したか」を意味し、2 bundle間の証拠統合を意味しない。新rootで77 leafだけを走らせても各bundleは独立にexact mapを持ち、`incomplete_checkpoint_counts`もbundleごとの値になる。`verify_bundle` は [validator.py:968](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2090-axis1-openalex-continuation/orchestrator/axis1_search/validator.py:968) でrootを1つしか受けず、checkpointも絶対root束縛なので、後から2 bundleを統合する実装経路はない。プランが案Bを退けた判断は妥当である。

- validatorのartifact単位束縛、既存schemaの維持、既存bytesを遡及更新しない方針には、scope外の新しい一般機構は見つからなかった。

## 総括

現プランは**要修正で、段5へそのまま渡せない**。quota失効とmixed-commit設計は、最初のrequest発行とbundle共存には有効である。しかし、既知の条件1失敗により最初の応答後にcheckpointなしで停止するため、D1183が要求する次セッション可能な継続取得を実現しない。

最小の再構成は次のとおり。

1. T-2091/D1207との矛盾を先に裁定する。
2. 77 leafのみなら変更面を `runner.py` と `validator.py` の2 fileへ縮める。
3. Q1も継ぐなら `run_axis1_search.py` を加え、正式preflight整合も成果物なら `check_axis1_search.py` も加える。
4. 同じ絶対pathのworktreeをロックし、各窓の最新bundleを登録commitとは別に永続保存・復元する手順を追加する。