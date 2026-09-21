# [T-2795] K2 同 job pair launcher と one-shot claim の整合を直した — 1 process・1 回の認可 / claim 所有期間で候補→stock を評価する driver へ (2026-09-21)

`authority: none` / `default_effect: no-state-change`

**種別:** 実装 wave (Codex author 2 単位 + fix 3 巡)。**実機の pair 投入は行っていない** (D2172 項 3 の予算再提示はユーザー手番)。
段 2 plan・段 3 敵対相談 2 本・段 6 敵対レビュー 2 本・fix 3 巡・焦点走 3 回・変異。逐語は `reviews/`。

- 日付: 2026-09-21 (JST)
- wave: `dev-wave-t2795-k2-pair-repair`、branch `worktree-dev-wave-t2795-k2-pair-repair`、着手時 local main `5efd69367b641b9bfbd6fb426478f66ae5762783` (開始 gate rc=0、乖離 0)
- 依頼: `verbatim/T-2795-repair-origin.md` (ユーザー、dev-wave 引数の逐語)。裁定 = D2187 (修復方向・claim leaf 不変・結合検査必須)、D2194 項 2 (4 巡目の入力元、投入は本 wave の外)、D2183 (launcher 契約)、D95
- job root (repo 外): `/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2795-k2-pair-repair/`

## 0. 一行で・主張すること・しないこと

**D2183 の pair launcher が Pegasus 契約 (`single_process=True`、reservation 必須) の one-shot campaign claim と両立しなかった問題 (D2187、F1019 の再発) を、
「1 回の認可・claim の所有期間で候補と stock を両評価する」driver 設計で直した。`loop.py` に認可 session を足し、`p3_s4_loop` の CLI を pair mode (1 process で候補→stock) にし、
job body を driver 1 起動へ変えた。claim leaf (`campaign_claim.py`) は bytes 不変で、2 つ目の process・session 無しの 2 回目は従来どおり `ClaimError` で拒否される。
F1019 の恒久対応として、site `PEGASUS_COMPUTE`・pegasus 契約・実 reservation・実 `acquire_claim`・実 layout / campaign lock / WAL / `pipeline.evaluate` を
`main()` から通す結合検査を追加した。**

**主張する。**

1. 修復は driver 側の設計変更だけで閉じており、claim leaf の受理集合・identity preimage・admission / verifier の受理集合・stock の成功条件 (certified ∧ 非 aborted ∧ `variant_id(stock genome)` ∧ BUILD_START の `src_token == STOCK`) は不変である。
2. 認可 session は同 process・同 sink が発行し束縛した未 close の個体に限り、契約 sha・campaign identity・protocol digest・declared_use_class・解決済み output root・claim root・claim path・claim file の record・reservation binding・required 契約の receipt を**毎回再計算して**照合したうえで claim 取得だけを省く。不一致は layout / lock / WAL / evaluate より前に拒否する。
3. 焦点走 3 回で consumer 回帰を実測した (100 赤 → 4 赤 → 0 赤、最終 2,015 passed / 5 skipped / 154.35 s、17 file)。
4. 変異は事前登録 22 本 (H 群) + commit 群 3 本で、帰属の条件 (単一理由性) は §5 に書いた実測で判定した。

**主張しない。**

- **実機で pair が成立したとは言わない。** Pegasus 上の production 1 走 (pair 再投入) と 4 巡目は本 wave では投入していない (ユーザーの予算再提示が前提、D2172 項 3)。
  実 compiler による STOCK 成立、実 checkout / patch と実 build の統合、bench の実測値はいずれも本 wave の成果に含まれない。
- **F1019 を全層で閉じたとは言わない。** 追加したのは「認可 / claim 結合の再発検査」であり、production 経路の 1 走は未実施である。
- **claim 防壁が任意の filesystem 改変に対して強くなったとは言わない。** 再利用時の record 照合は inode の連続性や確認後の改変不存在を証明しない (段 6 レビュー A の判定)。
- pid 検査の負例は `os.getpid` の差し替えによる模擬であり、実 fork による持出しは検査していない (pair mode は構造上 1 process)。

## 1. 変更の実体 (base `5efd69367` → tip、commit 4 本)

| commit | 内容 |
|---|---|
| `396c458ee` | A1: `loop.authorization_session()` と `run_campaign(..., authorization_session=)` / `_authorize_measurement` の session 経路、単体 test |
| `47b38fb06` | A2: CLI の pair mode、候補と stock の context / checkout 分離、job body の 1 起動、結合検査と負例 |
| `352d8a4f6` | fix1b + fix2: 静的目録に掛かる書き方の是正、初回例外の透過、job contract の pin 責務分離、attestation の合成観測、重複比較の削除 |
| `7bafad4a0` | fix3: 結合検査の perf preflight 代用の是正、fixture 断片の重複依存の解消 |

変更 file は 6 (`orchestrator/campaign/loop.py`、`orchestrator/campaign/p3_s4_loop.py`、`tools/pegasus/p3_s4_loop_pegasus.sh`、
`orchestrator/tests/test_campaign.py`、`orchestrator/tests/test_p3_s4_loop.py`、`orchestrator/tests/test_p3_s4_loop_job_contract.py`)、+1,229 / −201 行。
`orchestrator/campaign/campaign_claim.py` は sha256 `2e9c09328078378e4c9475f53e06cd338183373922ff2d83e5bcf218f7fd2dbd` のまま不変。

### 1.1 認可 session (`loop.py`)

- `authorization_session()` は context manager で、module-private の台帳に**発行個体の object identity** と発行 pid を記録する。exit で不可逆に close し、例外時も close する。
  同型のコピー・pickle は拒否する (`__copy__` / `__deepcopy__` / `__reduce_ex__`)。
- `run_campaign(..., authorization_session=None)` は keyword-only。**None のときは従来の呼出し順・receipt の object 同一性とも不変**で、既存の order assert を変更していない。
- 未束縛の session を渡した最初の呼出しは現行どおり `_authorize_measurement` を通り、**認可成功の直後** (perf preflight・layout・lock・evaluate より前) に束縛する。初回取得の例外は包まず透過する
  (`campaign_claim.ClaimError` は `ClaimError` のまま)。
- 束縛済みの session は §0 主張 2 の項目を再計算して照合し、`acquire_claim` だけを省く。`single_process=False` の契約では claim を作らない (従来どおり) が、契約・identity・root の束縛は同様に照合する。

### 1.2 CLI の pair mode (`p3_s4_loop.py`)

- pair mode = `--run-iteration <proposal> --stock-control` (+ `--isolate-worktree` 必須)。`--value` / `--emit-planner-context` / `--no-build` / `--b4-reflux-ablation` / `--b5-slot` /
  `--machine-generated-proposal` とは排他 (argparse 段階で rc=2、副作用前)。`--stock-control` 単独 (B-5 の slot 起動) は argv・挙動とも不変。
- 候補は従来の build_context (coder authority 付き)、stock は authority 無しの別 context と STOCK 専用 resolver・**別の pinned-clean checkout**。両 context の admission policy 一致を測定前に要求する。
- 1 つの `with loop.authorization_session() as session:` が候補 step と stock step を包み、非 None のときだけ下位へ転送する (非 pair 経路の `run_campaign` kwargs は exact 不変)。
- 候補が reject / abort / duplicate-skip / 通常例外でも stock を試行し、候補例外は stock の後に再送出する。rc は候補非零優先、候補 0 なら stock rc (0 は `certified-stock` のときだけ)。
  最後に `p3 S4 pair: candidate_rc=<X> stock_rc=<Y>` を driver が出す。pair 成立の判定は従来どおり WAL outcome に委ねる。

### 1.3 job body (`tools/pegasus/p3_s4_loop_pegasus.sh`)

- `IZANAGI_S4_STOCK_CONTROL=1` は proposal 起動に `--stock-control` を足した **driver 1 起動**だけになり、独立 stock 起動と shell 側の 2 段集約を削除した。driver の rc をそのまま返す。
- `=1` かつ proposal 無し (fixture) は prebuild / trap より前に rc=2 で拒否する。**これは `tools/pegasus/README.md` §7 が認めていた fixture 併用契約の縮小**であり、理由は
  「今回修復する production 入力は proposal で、fixture pair の新規対応は広げない」(段 6 裁定 B-B4)。未設定 / `0` の argv は bytes 不変。

## 2. D553 / D2183 への影響 (段 1 で明示し、段 4 で確定した内容)

- **D553 (sink-local な `single_process` 強制):** claim の取得は `loop.py` の sink に残る。single_process 契約下の `run_campaign` は「自分で claim を取る」か「同 process が同 sink で取った
  同 identity の claim を所有していることを claim file の record で再確認する」かのどちらかを通り、claim 無しで測定へ到達する経路は作っていない。
- **D464 (one-shot claim leaf):** leaf は bytes 不変。別 process・session 無しの 2 回目・別 identity は従来どおり拒否される。DEAD 再取得・rename / 退避・別 out_root は採らない。
- **D2183 (CLI 排他):** `--run-iteration` × `--stock-control` の組だけを pair mode として解除した。他の排他と stock 単独口は維持。job body の 2 process 形は 1 process に置換した。
  「同 campaign (同 identity・同 WAL)」と stock の成功条件は不変。

## 3. 相談・レビューと裁定 (段 3 / 段 6)

- 段 3 相談 A (sol、正しさ境界)・B (luna、実効性と過剰): いずれも条件付き支持。所見 10 件すべて real と裁定し採用 (`reviews/s4-adjudication.md`)。
  主要な採用点 = (i) `loop.py` / `p3_s4_loop.py` は 85 path の contract loader closure に入り、v2 campaign lock 作成時に live bytes = HEAD blob を要求するため、
  bytes を注入する変異は「変異の内容と無関係な赤」を生む (A-R1)。(ii) 結合正例は「両 arm の certified まで」を固定する (B-B1)。
  (iii) 冗長防御を独立 KILLED に数えない。(iv) 初回取得の例外は透過させる。(v) fixture pair の拒否は既存契約の縮小として記録する。
- 段 6 レビュー A / B: ともに NO-GO、新規 must-fix は同一 1 件 (変異 M4 の登録が「偽造 session の受理」を証明しない)。裁定と処置は `reviews/s6-adjudication.md`。
  M4 は「未発行・コピーの session を受理して新規束縛する」性質変異へ再登録し、M18 (session 転送) は字面 pin に限定して**実効性の証拠を commit 群 C1 (結合検査) に帰属**させた
  — 両 resolved 関数は `run_campaign` より前に `ensure_resumable_attempts` を呼んで campaign lock を作るため、lock を作らない挙動検査は成立しない (closure 照合と resumability は stub しない)。

## 4. 検査 (親の実測)

**焦点走 (計算ノード dispatch、`tools/run_tests.py --force-dispatch`)**

| 走 | 対象 | 結果 |
|---|---|---|
| 1 | 10 file (変更 test + 変更 production を参照する test) | rc=1、**100 赤** (job contract 72 / wiring probe 18 / 結合検査 3、内訳と原因は §3 と `reviews/s6-adjudication.md`) |
| 2 | 17 file (段 6 レビュー B-B3 で B-4 consumer 5 file と sort / trigger 2 file を追加) | rc=1、**4 赤** / 2,011 passed / 5 skipped / 153.91 s |
| 3 | 同 17 file | **rc=0、2,015 passed / 5 skipped / 154.35 s (全緑)** |

- 赤 (a) 静的目録の解消は、commit 後に `p3_b4_wiring_probe` の子と同じ処理を再現する script で親が実測した (JSON 1 行が返る)。
- 焦点走 1 の 100 赤はすべて実装起因 (既存赤ではない)。基準 commit での baseline 緑は変異 harness の baseline (下記) が別途示している。

**provenance**: 各統合 commit で `check_ai_provenance.py --message-file` rc=0、全史監査 12,262 → 12,264 件で新規違反なし。`check_docs.py` 違反なし。`spool_fold.py --dry-run` = `planned` (3 fragment)。

## 5. 変異 (事前登録 → 実測)

事前登録は段 4 (`reviews/s4-adjudication.md` §3) と段 6 の更新 (`reviews/s6-adjudication.md` §2)。**注入群 H** は固定 HEAD へ bytes を注入し、
**commit 群 C** は変異を焼いた commit を独立 clone に作って結合検査だけを走らせる (closure 照合が整合する)。

**A-R1 の実測 (帰属の前提):** `loop.py` / `p3_s4_loop.py` は `campaign_lock.CONTRACT_LOADER_RELATIVE_PATHS` (85 path) に入り、環境契約付き v2 campaign lock の作成時に
`capture_contract_loader_binding()` が live bytes = HEAD blob を要求する。等価変異 (comment 1 行) の probe で **114 node** が変異の内容と無関係に落ちることを実測し
(`test_p3_s4_loop.py` 81 / `test_campaign.py` 33)、注入群の対象集合から除外した。`--deselect` は param に `/` を含む nodeid に効かないため、
`test_run_one_iteration_preserves_outer_quarantine_rejection_order` はテスト名ごと除外した。除外後の baseline は緑 (1,136 passed / 3 skipped / 27.9 s)。

**commit 群 C (結合検査の検出力、独立 clone `cprobe-src` の HEAD `7bafad4a0` に変異を焼いた commit で `test_p3_s4_loop.py -k pair_main` を dispatch):**

| ID | 変異 | 実測 |
|---|---|---|
| C1 | stock の `run_campaign` へ認可 session を渡さない | rc=1、`test_pair_main_pegasus_real_claim_and_wal` と `test_pair_main_authorized_candidate_exception_stock_reuses_claim` が **`ClaimError: campaign claim は既に <pid> が所有している`** で赤 — 初投入 (`13339.nqsv`) と同型の失敗を検査が捕まえる |
| C2 | 束縛済み session でも claim を取り直す | rc=1、同じ 2 node が `ClaimError` で赤 |
| C3 | stock の bench を落とす (`do_bench=False`) | rc=1、3 node が `assert c.benches == [1] and c.builds == [(1, True), (1, False)]` で赤 |

**注入群 H (22 本、`mutation_worktree.py --runner-mode dispatch`、対象 = `test_campaign.py` / `test_p3_s4_loop.py` / `test_p3_s4_loop_job_contract.py` から drift node 114 と `test_run_one_iteration_preserves_outer_quarantine_rejection_order` を除外、spec sha256 `ef1ba814…`、rc=0、baseline PASSED):**

| ID | 変異 | 向き | 判定 | 殺した node 数 |
|---|---|---|---|---|
| m0-equivalence-comment | comment 1 行 (等価対照) | 正 | **SURVIVED** | 0 |
| m4-registry-accepts-unissued | 発行台帳の照合を外し、欠落時に新規束縛する (未発行・コピーの受理) | 負 | **KILLED** | 5 |
| m1-binding-mismatch-accepted | 再利用時の束縛照合 (契約 sha / identity / digest / use class / root) を外す | 負 | **KILLED** | 3 |
| m2-claim-record-not-rechecked | claim file の record 照合を外す | 負 | **KILLED** | 3 |
| m3-reservation-not-rechecked | reservation の再取得・再検査を外す | 負 | **KILLED** | 2 |
| m5-close-is-reversible | close を可逆にする (close 後の session を受理) | 負 | **KILLED** | 9 |
| m6-pid-not-checked | 発行 pid の照合を外す | 負 | **SURVIVED** | 0 |
| m7-receipt-not-rechecked | required 契約の receipt 再検算を外す | 負 | **KILLED** | 2 |
| m8-prewrite-validator-skipped | 再利用時の pre-write validator を呼ばない | 負 | **KILLED** | 1 |
| m9-binding-deferred | 束縛を認可直後でなく後段へ遅らせる | 負 | **KILLED** | 17 |
| m10-valid-reuse-rejected | 正しい束縛の再利用も拒否する (過剰拒否) | 正 | **KILLED** | 8 |
| m11-sessionless-skips-claim | session 無し経路で claim 取得を省く | 負 | **KILLED** | 13 |
| m12-pair-b5-not-rejected | pair × B-5 / machine-generated の拒否を外す | 負 | **KILLED** | 1 |
| m13-pair-candidate-optin-dropped | pair 候補の coder opt-in 必須を外す | 負 | **KILLED** | 1 |
| m14-stock-gets-candidate-context | stock に候補の build context (authority 付き) を渡す | 負 | **KILLED** | 7 |
| m15-stock-reuses-shared-tree | stock が候補と同じ共有 tree を使う (別 checkout を作らない) | 負 | **KILLED** | 8 |
| m16-candidate-exception-skips-stock | 候補の例外で stock を試さず即 raise する | 負 | **KILLED** | 2 |
| m17-stock-rc-overrides-candidate | 候補非零優先を外し stock rc を返す | 負 | **KILLED** | 2 |
| m18-session-not-forwarded-to-stock | stock の `run_campaign` へ session を渡さない | 負 | **KILLED** | 6 |
| m19-job-restores-second-driver | job body の pair argv を空にする (旧 2 起動へ戻す) | 負 | **KILLED** | 81 |
| m20-job-accepts-fixture-pair | job body の fixture + stock 拒否を外す | 負 | **KILLED** | 74 |
| m21-job-default-adds-stock | job body の既定でも `--stock-control` を足す (過剰) | 正 | **KILLED** | 6 |

**合計 20 KILLED / 2 SURVIVED。** SURVIVED は 2 本とも意図どおり:

- `m0` は等価対照 (comment だけの変更)。drift node を除外した対象集合が「内容非依存の赤」を拾わないことの witness でもある。
- `m6` は **冗長防御による survivor**。fix で保存 record の pid 比較を重複として削った後も、再利用の最後に `_AUTHORIZATION_SESSIONS.get(session) != (issued_pid, saved)` が同じ process 束縛を強制するため、発行 pid の比較を単独で外しても受理集合は広がらない (段 6 レビュー A-R3 / B-B2 が予告した冗長防御の型)。pid 束縛そのものの正例・負例は残っている。

DW-M01 の単一理由性は、各変異が殺した node が事前登録した性質の負例と一致することで確認した (例: `m4` は未発行 / コピー / close 後の 3 種、`m18` は session 転送の 6 param、`m19` / `m20` は job contract の静的検査群)。`m8` / `m12` / `m13` のように 1 node だけを殺す変異は、その node が当該性質の専用負例である。
## 6. 一次資料と正規化

- `verbatim/T-2795-repair-origin.md` (依頼の逐語)、`verbatim/{D2183,D2187,D464,D553,D2194-item2,F1019}.md` (裁定・failures の見出し単位の切出し)。
- `reviews/` — `s1-brief.md`、`s2-plan.md`、`s3-consult-A.md` / `s3-consult-B.md`、`s4-adjudication.md`、`s5-author-A1.md` / `s5-author-A2.md`、
  `s6-review-A.md` / `s6-review-B.md`、`s6-adjudication.md`、`s6-fix1.md` (正しい停止) / `s6-fix1b.md` / `s6-fix2.md` / `s6-fix3.md`。
- **可逆最小正規化 (DW-S07):** markdown の改行用の行末空白が `git diff --check` に抵触するため、4 file で行末の空白 / tab だけを除去した (可視文字不変)。
  原文 sha256 / bytes → 正規化後 sha256 / bytes:
  `reviews/s2-plan.md` `bf2feb97…` / 33,303 → `9f8127c6…` / 33,287、
  `reviews/s3-consult-A.md` `add281fe…` / 17,400 → `9a5890a2…` / 17,362、
  `reviews/s3-consult-B.md` `2b384fc8…` / 16,160 → `ad596295…` / 16,148、
  `reviews/s6-review-A.md` `e8a4bb1f…` / 9,364 → `8b24fd4b…` / 9,346。
  いずれも job root の原本と `diff -w -B` で一致 (rc=0 を実測)。復元は行末空白の再付与で、原本は job root に残る。
- job root (repo 外、複製しない): 変異 spec と結果 (`mutation-spec-{probe,final}.json`、`mutation-{probe2,final}-results.json`)、drift node 一覧 (`drift-nodes.txt`)、
  commit 群 probe の log (`cprobe-c{1,2,3}.log`)、焦点走 log (`focus-{1,2,3}.log`)、受入の受領証。

## 7. 段 8 (skill 自己改善) — 候補 2 件は予算超過で見送り

本 wave で観測した dev-wave の作法の候補は 2 件。いずれも該当 leaf 節への統合を試したが、**`docs/dev-wave/**` の L1.5 予算 (9,696 bytes) を超えたため撤回した**
(1 件目を入れた時点で 10,056 bytes、両方を最短形に縮めても 9,913 bytes)。`docs/skill-self-improvement.md` は「予算のために安全義務を削除・弱化しない」「予算値を上げる変更は
通常の自己改善に含めず独立審査」と定めるので、本 wave では候補の記録だけを行う。

1. **fix prompt の編集対象の区別** (`DW-S06-B` 想定): 「同 wave が今回作った未 land の test」と「main の tracked test」を区別して書く。区別が無いと子は
   「既存テストの期待値を変更しない」を正しく守って停止し、1 巡を失う (本 wave の fix1 が実例。変更 0 行で停止し、区別を明記した fix1b が rc=0)。
2. **closure 束縛 file の変異手順** (`DW-M04` 想定): 85 path closure に入る file を変異させる走は、等価変異 1 本で「内容非依存に落ちる node」を実測して対象集合から外す。
   `--deselect` は param に `/` を含む nodeid へ効かないので test 名で外す必要がある (本 wave で実測した 114 node + 1 node)。

どちらも failures / decisions へは送らない (新しい失敗型ではなく、既存節への手順追記に当たるため)。予算を見直す独立 wave が立った時に再提示する。

## 8. 受入全走 (`tools/dev_wave_wait.py acceptance --lease-optional`、門番付き)

| attempt | tested main / tip | 結果 |
|---|---|---|
| final-1 | 投入前検査で停止 | `stage=preflight-clean rc=2` — 親が insight の追記を未 commit のまま置いていた (main 73 commit の post-claim merge は成功)。commit 後に再投入 |
| final2-1 | `6496ab2dc` / `5496efe02` | rc=70、**赤 1** = `orchestrator/tests/test_codex_worker_launch.py::test_evidence_forced_stop_propagates_unknown_residual_to_sidecar` (`assert []`)。本 wave の変更 file と無関係の時間依存 test (evidence 猶予 0.3 s)、受入中の login load 20〜95。同 tip で同 file を単独再走 → **216 passed / 11.85 s**。負荷由来の flake と判定し再投入 (flaky hold 台帳への登録は本 wave の scope 外) |
| final3-1 | `eaeaeb388` / `3f76af758` | **rc=0、26,964 passed / 69 skipped、赤 0**、受領証 `acceptance-receipt-green.json` (job root) |
