## 前提の検査

**wave worktree から silo/rr5 を 1 本投入する方針は成立します。ただし「実装差分なし」の見込みは修正が必要です。新しい attempt の記録が、既存の v1 コーパステストの対象集合を増やします。**

以下、行番号の略記は次を指します。

- **S** = [tools/pegasus/submit_certify.sh](tools/pegasus/submit_certify.sh)
- **J** = [tools/pegasus/certify_calibration.sh](tools/pegasus/certify_calibration.sh)
- **C** = [orchestrator/calibrator/cli.py](orchestrator/calibrator/cli.py)

今回の静的・読み取り検査では、`output/` を除く作業ツリーは clean。CCBench HEAD は gitlink と一致する `511c9538…`、gflags/glog も policy 指定 HEAD と一致し、両作業ツリーの status 出力は空でした。投入直前にも再確認してください。

投入条件と停止箇所は次のとおりです。

| 条件 | 根拠・停止箇所 |
|---|---|
| `--protocol silo --rratio 5` | S:40–49。不正値は exit 2 |
| `PEGASUS_EFFECTIVE_CLOCK_TOLERANCE_PCT` は未定義。空文字でも不可 | S:22–25、J:202–205 |
| third-party staging root と masstree/mimalloc/googletest が実ディレクトリで、各検査対象が symlink でない | S:52–65、J:186–201。存在確認だけでは pristine の保証にならず、コピー後の検証失敗は J:627–630 で exit 2 |
| job script、policy、非 symlink の calibration policy が存在し、policy が読める | S:67–98。exit 2 |
| HEAD が完全な commit ID、`output/` 以外が untracked を含め clean | S:104–113。exit 2 |
| submission directory を新規作成できる | S:125–133。既存なら exit 2。出力先・repo 外 scheduler 証拠領域への書込み権限と容量も必要 |
| `qstat -Q`、`pegasusinfo`、`rbudgetcheck`、`check_quota` が成功 | S:151–156、200–202。失敗は **exit 3**。本文の queue 状態・残高まで自動判定しているわけではない |
| queue が実行可能 | `docs/pegasus-runbook.md:349`。`DIS` / `INA` なら投入しない。親の `qstat` 空という観測だけでは queue の稼働を証明しない |
| gflags/glog が存在し pinned-clean | J:444–470、508–534。欠落・HEAD 不一致・dirty は exit 2 |
| CCBench submodule が実体化され、gitlink と一致し tracked-clean | J:632–636。これは shell assertion による停止で、必ずしも exit 2 ではない |

job 側にはさらに、PBS 環境・安全な ID・新規 `/scr` / job-staging directory（J:28–57）、nonce・比率・protocol（163–184）、60 秒以内の submit receipt（207–216）、allocation/start/hostname の束縛（349–369）、固定 `nm`（406–412）、Python 3.10 候補（437–440、592–595）、trace symbol 検査（701–707）、残り予約時間（850–854）、perf smoke（907–909）の exit 2 条件があります。これらを飛ばす投入経路は提案しません。

## プラン

1. **既存 launcher を、wave root を明示して 1 回だけ実行する。**

   ```bash
   bash /work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2515-rr5-accepted-calibration/tools/pegasus/submit_certify.sh \
     --repo-root /work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2515-rr5-accepted-calibration \
     --protocol silo \
     --rratio 5
   ```

   ユーザーが設定すべき追加の `IZANAGI_*` 環境変数はありません。launcher が nonce・rratio・明示 protocol を `qsub -v` で渡します（S:205–217）。`PBS_JOBID` / `PBS_O_WORKDIR` は scheduler が供給します。

   **`--attempts-root` は変更しないでください。** launcher は変更先へ submission を書けますが、job は `<repo>/output/env/pegasus/calibration/attempts/submissions/<nonce>` に固定して探します（S:125–129、J:208–216）。別の root を指定すると receipt 待ちで落ちます。`--job-script` も既定を使います。

2. **投入元と記録先を固定する。**

   `qsub` は指定 repo root に `cd` して呼ばれます（S:229）。job は `PBS_O_WORKDIR` を root とし（J:46）、CLI は実際に読み込んだ `cli.py` の所在から出力 root を決めます（C:183–189、830–834）。

   | 証拠 | wave root を選んだ場合 |
   |---|---|
   | submission | `<wave>/output/env/pegasus/calibration/attempts/submissions/<nonce>/` |
   | wrapper・build・scheduler 観測 | `<wave>/output/env/pegasus/calibration/job-staging/0:<ID>.nqsv/` |
   | calibrator attempt | `<wave>/output/env/pegasus/calibration/attempts/0_<ID>.nqsv/` |
   | accepted record | `<wave>/output/env/pegasus/calibration/registered/calibration-<sha16>.json` |
   | scheduler stdout/stderr | git common dir から導いた repo 外の `izanagi-job-evidence/calibration-certify/`（S:114–115、209–210） |

   主 checkout を root に選べば最初の四つは主 checkout 配下になります。wave の hydrate 済み staging は自動共有されません。

   source identity の再検査は **job 冒頭**です。dirty 検査は J:223–225、commit・script SHA・request・投入条件の照合は J:240–259。終了時まで全ソースを継続監視する仕組みではありません。したがって親の「走行中は `output/` 以外を触らない」は維持し、commit・checkout・worktree 削除・他セッションによる同一 root の編集も避けます。さらに、`output/` 内でも入力である third-party staging や当該 job の receipt を変更してはいけません。

3. **投入直後の可視性確認と、終端待ちを分ける。**

   投入直後は receipt の request ID で `qstat -f <ID>` を一度確認します。`0:` 接頭辞は除きます（J:264–265）。

   NQSV は `Current State = Queued`、`Execution Hosts(JSVNO):` の後続行、`Started Request Time = …` という形式を使います（J:320–340、runbook:185–188）。存在しない request でも rc=0 を返し、終了後約 5–6 秒で消えます。**qstat の rc や消失を完了判定に使いません**（runbook:182–194）。

   完了待ちは `tools/dev_wave_wait.py compute` を使い、request 固有の scheduler stderr を `--accounting-file` に指定します（runbook:1179–1224）。既定の内部確認間隔は **15 秒**です。親が別途 qstat を周期実行する必要はありません。

   この wrapper には最終 cleanup 後の done-marker がありません。`job-result.json` を最終完了 marker と誤認させず、未作成の request 固有 marker path と会計証拠を使って、会計の終端を待つ構成が適切です。親が marker を作ってはいけません。

   先行所要は 184 / 177 / 238 秒なので、約 240 秒を最初の進捗評価の目安にします。これは打切り期限ではありません。遅延時は build/cooldown 等の段階を確認し、要求枠 7200 秒と queue 待ちを考慮します。待ち手の既定上限は 21600 秒です。

4. **ファイルの出現順と成功判定を確認する。**

   - submission: preflight captures → `pre-submit.json` → qsub 結果 → `submit-receipt.json`（S:135–198、228–283）。
   - job-staging: submit receipt → allocation/topology/reservation → probe/build 証拠 → acquisition receipt → calibrate argv/stdout/stderr（J:218、265–396、842–848、934–958）。
   - attempts: calibrator 起動時に directory を作成（C:834–838）。通常の判定到達時は `candidate.json` または rejected `calibration.json` → `calibration.md` → `window-probes.json`（C:1021–1032）。
   - accepted: registered へ publish → `published-self-comparison.json` → attempt の `calibration.json` → `publish.json`（C:1067–1097）。
   - wrapper: 成功時の post probe → `job-result.json` → 非ゼロなら `failure.json` → cleanup（J:960–995）。

   **`job-result.json` と `failure.json` に単純な優先順位はありません。** 前者の `calibrate_rc` は calibrator の結果、後者は wrapper の失敗証拠です。rc=0 の job-result があっても、その後の cleanup や signal で failure が出る可能性があります。早期失敗なら job-result 自体がありません。終端会計・両 receipt・publish 証拠を併読します。

5. **accepted は CLI の判定・publish の結果として確認する。**

   `report.py:87–129` の条件は、TSC 実測、cooldown、全 subprocess と反復数、必須 counters/maxrss/L3、正の有効選択と cache-floor 警告なし、CV ≤ 0.05、全 window の単独性、前後 static profile 一致です。

   これに CLI の binary/trace、receipt、visibility、acquisition、clock 検査が加わります（C:852–905、1005–1017）。理由が空の場合だけ accepted を組み立てます。選択が `saturated=False` でも `lower_bound_selected=True` なら選択条件を満たせます（`report.py:115–119`）。

   publish は SHA256 名、exclusive write、no-replace rename または link/unlink、公開後 clock 自己照合を経ます（C:302–356、1037–1097）。親が candidate をコピーしたり JSON の status を変更したりすると、この経路を肩代わりしてしまいます。**手動 publish は不可**です。

   通常の品質却下では attempt に rejected `calibration.json`、Markdown、window probes が残ります。例外では rejected calibration または `rejection.json` が残り、candidate は除去されます（C:1101–1139）。公開後の失敗では registered が残る場合もあるため、「ファイルがある」だけで正常完了とは書きません。

6. **却下時は証拠を保存して裁定へ返す。**

   | 理由 | 許される対応 | 禁止する対応 |
   |---|---|---|
   | `selection-invalid` | 全点の miss/RSS/L3、選択フラグ、警告を記録 | 閾値・候補・選択 N の手動変更、旧却下の再認定 |
   | `within-run-cv-invalid` | 全反復・CV・外乱証拠を記録 | 都合の悪い反復削除、上限変更、通るまで無断再走 |
   | `reps-incomplete` / `required-metrics-missing` | subprocess/perf/timeout の失敗を特定 | 欠測補完、部分標本を accepted 化 |
   | cooldown / isolation / attestation / clock | 観測値と receipt を提示 | 許容幅拡大、単独性や probe の省略 |
   | source/binding/build/publish 失敗 | 操作・環境・実装の原因を切り分ける | receipt 修造、candidate の手動公開、上書き |

   本 wave は 1 本です。品質却下が再発したら brief:33 のとおり裁定へ返し、追加測定を自動で繰り返しません。

## 実装面の判定

変更予定は次のとおりです。

| ファイル | D95 の実装面 |
|---|---|
| job が生成する `registered/calibration-<sha16>.json` | 該当しない |
| 新 request の `attempts/`、`attempts/submissions/`、`job-staging/` の JSON・Markdown・生ログ | 該当しない |
| `output/insights/2026-09-16/t2515-rr5-calibration/README.md` | 該当しない |
| `docs/phase3.md:534–539` の取得状況 | 該当しない |
| `docs/spool/worklog/2026-09-16-dev-wave-t2515-rr5-accepted-calibration-1.md`、必要時の failures/decisions fragment | 該当しない |
| **`orchestrator/tests/test_env_attestation.py:1002–1022` のコーパス対象修正** | **該当する。Python の実装面** |
| テスト追加に伴い更新が必要となる `orchestrator/tests/acceptance_duration_ledger.json` | **該当する。orchestrator 配下の非 Markdown** |

**Codex author の実装子が必要です。** 修正対象は後述の歴史コーパス分類です。較正判定・選択規則・schema・旧記録・固定件数を変更する案ではありません。

実装子には、旧 v1 payload の全件発見・物理コピー一致・replay・既存関連文書の存在確認を保ち、新しい v2 attempt の Markdown 追加を旧コーパス増加と扱わない構造にするよう依頼します。新規 v2 文書追加を許容する正例と、旧資料の欠落・不正な旧 payload 追加を拒否する負例で検証します。単なる assertion 削除や golden 集合への新 attempt 追記は避けます。

修正は投入前に完了して clean にするか、job 終端後に行います。親の実走検査は `tools/run_tests.py` 経由とし、関連テスト、`check_codex_agents.py`、`check_docs.py`、commit 後の provenance 監査を実施します。本段では pytest を実行していません。

## 凍結 pin への影響

- **env_contract の pin は変わりません。**  
  `env_contract.py:253–279` は旧 753f / 94a4 の path と full SHA を明示し、g2 contract hash も固定しています（283–289）。registered への追加で自動切替は起きません。新 rr5 の取得と環境契約の更新は別です。

- **campaign lock も自動更新されません。**  
  `campaign_lock.py:157–170` の authority は環境契約 hash と loader の束縛です。`layer3_report.py:375–400` はその hash から既存 calibration pin を解決します。新 record の追加だけで既存 lock の意味は変わりません。

- **Layer3 の通常入口は registered 全件を再帰探索していません。**  
  `layer3_report.py:851–858` が渡すのは `…/calibration`。同:519 は直下 `*.json` だけで、registered の新ファイルは既存 contract pin に採用されない限り通常探索へ入りません。  
  明示的に registered を探索対象にする経路なら、同:597–611 の `(protocol, records, threads, workload)` 重複検査が関係します。現在 silo/rr5 accepted はなく、今回 1 件の追加は既存キーと衝突しません。先行 insight の衝突説明を、通常入口が registered 全件を読む説明へ一般化してはいけません。

- **`test_env_attestation.py` は、registered の追加と attempt の追加を分けて考える必要があります。**  
  固定 SHA の leaf テスト（1297–1319）は無影響です。一方、同:1011–1022 は `attempts/*/calibration.md` 全件を `_V1_CORPUS_DOCS` と比較します。静的に集合を照合したところ、**投入前から既に 6 件余分**でした：989271、995805、995806、998860、998863、998864。新しい通常 attempt はさらに 1 件増やします。これは pytest 実走結果ではなく、テスト本文と実ファイル集合の不一致です。

- **`test_pegasus_tools.py:772` の `glob + next` は選ぶファイルが変わりえます。ただし rr5 追加が直ちにテスト結果を変える構造ではありません。**  
  同:770–785 は選んだ record の `attestation_profile` だけを使い、clock tolerance を除去し CPU model を上書きします。workload、records、genome、quality は使いません。呼出し側は正常 SKU と近似 SKU の判定（821–845）、duplicate-key 拒否（848–873）です。  
  現存 7 件はいずれも physical/logical/affinity=48、SMT off、tolerance field ありでした。新 record でも profile がこの契約に適合することを確認します。**列挙順不変とは主張できませんが、rr5 であること自体を理由にこのテストを変更する必要はありません。**

- **duration ledger は calibration の pin ではありません。**  
  `acceptance_duration_ledger.json:10124`、14331–14332 は該当 nodeid の所要です。record 追加だけで更新しません。実装子が nodeid を追加した場合は既存運用に従い扱い、未測定値を実測として記入しません。

- **閉包へ追加する確認先:**  
  `pegasus_floor_scoping.py:77–84` も `lookup(ENV_TAG).calibration_ref` を読むため、自動切替しません。登録追加を理由に floor の動作点や凍結資料を変更しないでください。また記録範囲には、brief の成果物一覧から漏れている **`job-staging/` の生証拠と repo 外 scheduler 会計**を含めます。

## 残る不確実性

- 旧系列への probe は再走成功の予測材料です。新しい系列・CV・環境証拠が accepted 条件を満たす保証ではありません。
- 計算ノードの Python/perf、allocation、pristine 検査、公開ファイルシステムの動作は今回まだ実走していません。
- source identity は冒頭検査であり、走行中の変更を全面的に検出する保証はありません。
- 公開後の signal・post probe・cleanup 失敗では、accepted 公開物と wrapper 失敗が共存しえます（J:22–24、960–995）。
- v1 コーパステストの不一致は既存問題です。今回の追加で初めて生じた失敗と記録しないでください。

## 総括

wave root から既定 launcher で silo/rr5 を 1 本投入し、CLI の判定・publish と終端証拠を確認します。accepted なら取得記録と phase を更新し、却下なら変更せず裁定へ返します。

**P3「実装面なし」は成立しません。** 歴史コーパステストの対象分類を保守する実装子を追加してください。選択規則・品質ゲート・凍結 pin・旧却下記録を動かす必要はありません。