# [T-781] 案 A 実装面素案

結論は、`qcat` により「指定 request に scheduler が spool した script bytes」の独立取得は実装可能です。ただし、これは「その request が現プロセス自身を起動した」ことを証明しません。したがって案 A 単独では A-1 を閉じず、現時点では official の無条件拒否を外さず設計メモに留めるのが妥当です。

補助的に既存 probe 成果物を読むと、計算ノードで `qcat` は利用でき、自 request の raw `PBS_JOBID=0:901499.nqsv` に対して rc=0 でした。一方、同じ job から別の所有 request の script も取得できています（[probe.log:3](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t781-spool-feasibility/probe/out/probe.log:3)、[probe.log:7](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t781-spool-feasibility/probe/out/probe.log:7)、[probe.log:48](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t781-spool-feasibility/probe/out/probe.log:48)）。

## 1. 証拠取得点

### 配置

取得処理は shell wrapper ではなく、`_run_campaign_core` から内部呼出しする scheduler 専用 helper に置きます。仮称は `orchestrator/campaign/s8b_floor_submission_admission.py` です。

理由は次のとおりです。

- shell wrapper の正規起動は [floor_campaign.sh:961](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t781-spool-feasibility/tools/pegasus/floor_campaign.sh:961) ですが、Python の private core は直接呼べます（[s8b_floor_campaign.py:2805](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t781-spool-feasibility/orchestrator/campaign/s8b_floor_campaign.py:2805)）。
- wrapper だけで検査すると、R-5 A-1 と同様に core 直呼びで検査全体が消えます（[package.md:161](/work/1/SFC/tanab/izanagi/output/insights/2026-08-11_t8b-restart-integration/package.md:161)）。
- helper の戻り値は同一 core 呼出し内だけで使う非直列化 snapshot とし、caller が渡せる `permit` 引数にはしません。

helper は caller から request ID、source commit、expected hash、command runner を受け取らず、production adapter が内部で以下を取得します。

```text
PBS_JOBID
  ├─ /opt/nec/nqsv/bin/qstat -f <正規化ID>
  └─ /opt/nec/nqsv/bin/qcat -i -b -n 100000 <raw ID>
```

### claim との順序

現行は pure validation の後、[s8b_floor_campaign.py:2948](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t781-spool-feasibility/orchestrator/campaign/s8b_floor_campaign.py:2948) から claim を作り、[同:2970](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t781-spool-feasibility/orchestrator/campaign/s8b_floor_campaign.py:2970) で `acquire_claim`、その後 [同:2989](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t781-spool-feasibility/orchestrator/campaign/s8b_floor_campaign.py:2989) から official preflight を行っています。これは B-1 の実在箇所です（[stage4-ruling.md:45](/work/1/SFC/tanab/izanagi/output/insights/2026-08-11_t8b-restart-integration/stage4-ruling.md:45)）。

仮実装時は次の順へ並べ替えます。

1. mode と official seam の拒否
2. protocol、`VerifiedFreeze`、execution receipt、reservation の read-only 検証
3. `started_at`、protocol SHA、run ID の導出
4. qstat/qcat、receipt、revision、committed wrapper の照合
5. `_floor_preflight_freeze_allowlist`
6. `_official_launch_preflight` の二回 clean scanと certificate のメモリ内構築
7. `acquire_claim`
8. run directory、certificate、journal の作成

したがって admission 失敗時には新しい claim leaf、run directory、certificate、journalを残しません。既存テストの「scan 失敗後も claim が残る」という期待（[test_s8b_floor_campaign.py:4082](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t781-spool-feasibility/orchestrator/tests/test_s8b_floor_campaign.py:4082)）は反転対象です。

ここで守れるのは「`acquire_claim` が最初の durable campaign mutation」という意味です。`qstat`、`qcat`、Git subprocess の起動まで副作用と数える字義どおりの B-1 とは両立しないため、契約文も durable state mutation と明記する必要があります。また shell wrapper は core 起動前に job-staging や依存 build を作るため、job 全体の書込みゼロまでは保証しません。

## 2. 照合対象と byte 正規化

authoritative な比較対象は User Attribute が指す commit の committed blob とします。

| 値 | 扱い |
|---|---|
| `qcat` stdout | scheduler が保持する raw spool observation |
| `<attribute commit>:tools/pegasus/floor_campaign.sh` | expected bytes |
| submission receipt の `source_commit` / `job_script_sha256` | 上記二者との整合確認。単独の authority にはしない |
| 実行中 `$0` | 既存 wrapper の defense-in-depth。sole predicate の authority にはしない |
| freeze allowlist | 別の conjunct。wrapper bytes の expected には使わない |

現行 wrapper は `$0`、receipt hash、committed blob を照合しています（[floor_campaign.sh:508](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t781-spool-feasibility/tools/pegasus/floor_campaign.sh:508)、[同:540](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t781-spool-feasibility/tools/pegasus/floor_campaign.sh:540)）。これは残しますが、`$0` は core 直呼び時には存在せず、caller が別 shell を起動できるため security credit は加えません。

`qcat` の末尾改行は次の exact 比較にします。

```python
expected_qcat_bytes = committed_blob + b"\n"

if returncode != 0:
    reject()
if stderr != b"":
    reject()
if stdout in {b"", b"\n"}:
    reject()
if stdout != expected_qcat_bytes:
    reject()
```

重要点は次のとおりです。

- `.rstrip(b"\n")` や `splitlines()` による正規化は禁止します。投入時点で末尾改行を持つ script と持たない script を同一視してしまいます。
- `stdout[:-1]` を使ってよいのは、末尾がちょうど追加分 1 byte であり、全体が `committed_blob + b"\n"` と一致した後だけです。
- HLD の「rc=0 かつ空相当」は非空 wrapper との exact 比較で必ず赤になります。診断を明確にするため空と `b"\n"` は明示拒否します。
- `-n 100000` による truncation を避けるため、committed wrapper の論理行数がこの上限より十分小さいことを先に要求し、上限到達時は拒否します。
- SHA-256 は snapshot や診断用に記録しても、受理判定自体は小さい script の exact byte equality にします。

freeze allowlist は [s8b_floor_campaign.py:1428](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t781-spool-feasibility/orchestrator/campaign/s8b_floor_campaign.py:1428) が構築し、許可 namespace も [同:1629](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t781-spool-feasibility/orchestrator/campaign/s8b_floor_campaign.py:1629) で限定されています。job script をこの allowlist に混ぜず、単一 admission predicate の別条件として合成します。

## 3. request ID の入手経路

現行 job は `PBS_JOBID` を必須にし、任意の `0:` prefix を含む形式を受理しています（[floor_campaign.sh:18](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t781-spool-feasibility/tools/pegasus/floor_campaign.sh:18)）。`qstat` では既に `${PBS_JOBID#0:}` を使用しています（[同:571](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t781-spool-feasibility/tools/pegasus/floor_campaign.sh:571)）。probe でも raw ID の `qstat -f` は失敗しているため（[probe.log:57](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t781-spool-feasibility/probe/out/probe.log:57)）、実装は次の二形を使い分けます。

- `qcat`: scheduler が投入した raw `PBS_JOBID`。probe 済みの `0:<id>` をそのまま渡す。
- `qstat`: `normalize_request_id()` と同じく先頭の `0:` だけを除く（[schema_v2.py:363](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t781-spool-feasibility/orchestrator/calibrator/schema_v2.py:363)）。

さらに qstat 出力の `Request ID`、receipt の `job_id`、reservation binding の job ID、RUN 状態、assigned host を相互照合します。request 名は `qalter -N` で変更可能なので一切使いません。

ただし、この値は偽装可能です。

- `PBS_JOBID` は scheduler が初期投入する環境変数ですが、子 process の caller は任意値で exec できます。
- reservation 側も `PBS_JOBID` と wrapper が export した環境変数を比較するだけです（[reservation.py:237](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t781-spool-feasibility/orchestrator/campaign/reservation.py:237)）。
- `qcat` は別の同一所有者 request も読めています。したがって qcat の引数は「self」ではなく「caller が名前を指定した所有 request」です。

相互照合は事故や一部の取り違えを閉じますが、すべて同じ caller-selected ID から導出できるため、現プロセスと scheduler request の非偽装な対応証明にはなりません。

## 4. User Attributes を revision authority にする案

### 実装点

現行 submit wrapper は clean `HEAD` を `SOURCE_COMMIT` にし（[submit_floor.sh:193](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t781-spool-feasibility/tools/pegasus/submit_floor.sh:193)）、qsub には nonce だけを渡しています（[同:410](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t781-spool-feasibility/tools/pegasus/submit_floor.sh:410)）。

revision authority として扱うなら、単なる自動転記ではなく次の形が必要です。

1. `submit_floor.sh --approved-source-commit <40hex>` を必須化し、既定値を持たせない。
2. 人間指定値が `SOURCE_COMMIT`、clean index/worktree と一致することを qsub 前に検査する。
3. qsub を次の形にする。

```bash
qsub -U "izanagi_source_commit=$APPROVED_SOURCE_COMMIT" \
     -v "$export_spec" \
     "$JOB_SCRIPT"
```

4. core 内の fixed qstat reader が `User Attributes:` 節から exact key `izanagi_source_commit` をちょうど一つ読む。
5. `attribute commit == receipt.source_commit == HEAD` を要求し、その commit の blobを expected wrapper bytes にする。
6. receipt schema は増やさない。既存 `source_commit` は scheduler attribute との一致確認に使う。

`SOURCE_COMMIT` を自動でそのまま `-U` に入れるだけでは、任意の clean HEAD が自己整合して通るという R-5 A-2を何も解決しません（[package.md:175](/work/1/SFC/tanab/izanagi/output/insights/2026-08-11_t8b-restart-integration/package.md:175)）。

### D86(3) の読み

User Attribute は Git 内の receipt ではなく scheduler の request record なので、D86(3) の「新しい Git launch receipt は作らない」（[decisions.md:3773](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t781-spool-feasibility/docs/decisions.md:3773)）には字義上は直接抵触しない、という読みが自然です。

ただし、次の区別が必要です。

- 属性は「この request に submitter がこの SHA を付けた」という revision assertion にはなる。
- 属性を置いた caller が人間か AI か、ユーザーがその revision を承認したかは証明しない。
- 属性の存在を authorization の証明と呼ぶと、submission artifact は記録にすぎないとする D86(8)（[decisions.md:3797](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t781-spool-feasibility/docs/decisions.md:3797)）に抵触する。

したがって「新 Git receipt ではない」は静的には支持できますが、「新しい revision authority として D86(3) の範囲内か」はユーザー裁定事項です。自動的に authorization と解釈してはいけません。

また、spool SHAや source commit を launch certificate/journalへ永続化して A-5 を閉じる場合は、certificate v1等を不変とする D86(4)と、certificate v2・ratified verifier 拡張を延期した D86(5)（[decisions.md:3777](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t781-spool-feasibility/docs/decisions.md:3777)、[同:3780](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t781-spool-feasibility/docs/decisions.md:3780)）を明示的に覆します。本素案には含めません。

## 5. 残る穴

1. **A-1 の兄弟 process 攻撃は閉じません。** 真正 floor request 内の兄弟は同じ `PBS_JOBID`、nonce、reservation 環境を再利用し、同じ qstat attributes と qcat bytes を得られます。先に core を起動すれば [s8b_floor_campaign.py:2970](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t781-spool-feasibility/orchestrator/campaign/s8b_floor_campaign.py:2970) の claim を正規 wrapper より先に獲得できます。claim は winner の PID を記録しますが、wrapper lineage は証明しません。

2. **private core の注入 seam は別途閉じる必要があります。** public `run_campaign` は 13 seam を拒否しますが（[s8b_floor_campaign.py:2772](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t781-spool-feasibility/orchestrator/campaign/s8b_floor_campaign.py:2772)）、private core は現在 `build_fn` しか拒否しません（[同:2822](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t781-spool-feasibility/orchestrator/campaign/s8b_floor_campaign.py:2822)）。official 解禁時は全 seam 拒否を core 自身へ移す必要があります。それでも、default seam の sibling 起動は残ります。

3. **Python 同一権限内の monkeypatch は防げません。** helper や guard を import 後に差し替えられる攻撃まで security boundary とするなら、D86(5) が延期した private permit型・AST pinまたは別 process/権限境界の再裁定が要ります。

4. **`VerifiedFreeze` の forge/mutation が残ります。** 公開 constructor と mutable `dict` を持ち（[s8b_freeze_io.py:30](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t781-spool-feasibility/orchestrator/campaign/s8b_freeze_io.py:30)）、core はその dict を直接使います（[s8b_floor_campaign.py:2881](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t781-spool-feasibility/orchestrator/campaign/s8b_floor_campaign.py:2881)）。stage 4 A-4 の未解決点です。

5. **下流 proof chain に残りません。** 現 launch certificate は freeze SHA、clean digest、protocol SHA、時刻、run ID の5値だけです（[s8b_floor_campaign.py:1759](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t781-spool-feasibility/orchestrator/campaign/s8b_floor_campaign.py:1759)）。request 消滅後は qcat/qstatを再取得できないため、downstream verifier は admitted result と自己整合な偽物を区別できません。これは R-5 A-5そのものです（[package.md:188](/work/1/SFC/tanab/izanagi/output/insights/2026-08-11_t8b-restart-integration/package.md:188)）。

6. **User Attribute は人間性を証明しません。** AI や無人 process が qsub できるなら同じ属性を設定できます。D87の「AI は qsub しない」は運用境界であって暗号学的防壁ではありません（[decisions.md:3825](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t781-spool-feasibility/docs/decisions.md:3825)）。

7. **NQSV R1.16 固有仕様への依存が残ります。** 末尾 1 byte追加、`-n` の表示範囲、User Attributes の表示形式が変われば fail-closed に倒す必要があります。

以上から、qcat は「caller-opened FD」という恒真化を除去しますが、A-1を「process lineage の欠落」として捉えると部分解決に留まります。これを承知で official を非空にするなら、D86(1)/(3)/(8) が意図した wrapper-only・人間指示の受理集合を「有効 request を指定できる同一所有者 process」まで広げる裁定が別途必要です。

## 6. file:line 変更素案と費用

| ファイル | 仮変更 | 概算 |
|---|---|---:|
| 新 `orchestrator/campaign/s8b_floor_submission_admission.py` | strict receipt/source 共通 leaf、qstat/qcat capture、attribute parser、exact bytes比較、非直列化 snapshot | 180–260行 |
| [s8b_floor_campaign.py:207](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t781-spool-feasibility/orchestrator/campaign/s8b_floor_campaign.py:207) | 無条件 guardを一回だけの official predicate 呼出しへ置換 | 30–50行 |
| [s8b_floor_campaign.py:2763](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t781-spool-feasibility/orchestrator/campaign/s8b_floor_campaign.py:2763) | 全 official seam 拒否を core にも適用 | 30–50行 |
| [s8b_floor_campaign.py:2881](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t781-spool-feasibility/orchestrator/campaign/s8b_floor_campaign.py:2881) | submission/spool/freeze preflightを claim 前へ移し、snapshotを後段で再利用 | 60–100行相当 |
| [s8b_floor_campaign.py:3544](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t781-spool-feasibility/orchestrator/campaign/s8b_floor_campaign.py:3544) | CLI 固定拒否を削除し、admission拒否だけ rc=2へ翻訳 | 15–25行 |
| [certified_writer_admission.py:177](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t781-spool-feasibility/orchestrator/campaign/certified_writer_admission.py:177) | receipt/source strict logicを共通 leafへ委譲。compute/calibration検査は維持 | 20–50行 |
| [submit_floor.sh:193](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t781-spool-feasibility/tools/pegasus/submit_floor.sh:193) | 明示 approved SHA の入力・HEAD照合 | 15–25行 |
| [submit_floor.sh:410](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t781-spool-feasibility/tools/pegasus/submit_floor.sh:410) | qsub に `-U izanagi_source_commit=...` を追加 | 5–10行 |
| [floor_campaign.sh:29](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t781-spool-feasibility/tools/pegasus/floor_campaign.sh:29) | qcat の authoritative 取得は置かない。既存 early static admission と `$0` 照合を defense-in-depth として維持 | 原則0行 |
| [s8b_freeze_io.py:30](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t781-spool-feasibility/orchestrator/campaign/s8b_freeze_io.py:30) | official 解禁まで進めるなら A-4 を閉じる immutable/deep-copy処理 | 40–80行 |

production 差分は案 A＋User Attributeだけで概ね350～550行です。A-3/A-4を同時に閉じ、既存 official test seamを移行するとテスト込みで900～1,400行程度になります。A-5を閉じる certificate/journal/ratified拡張は別に500～900行級で、D86(4)/(5)を覆す独立 waveです。

## 7. 新設テスト

主な test surface は次です。

- 新 `test_s8b_floor_submission_admission.py`
  - `committed_blob + b"\n"` の正例
  - rc非0、stderr非空、`b""`、`b"\n"`、末尾追加なし、2改行追加、途中・末尾改変
  - `.rstrip()` なら誤受理する fixture
  - `-n` 上限到達・timeout
  - User Attribute の欠落、重複、非40hex、request ID不一致
  - qcatは raw ID、qstatは `0:` 除去済みIDを受け取ること
  - PATH上の偽 `qcat` でなく absolute commandを使うこと

- [test_s8b_floor_campaign.py:1097](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t781-spool-feasibility/orchestrator/tests/test_s8b_floor_campaign.py:1097)
  - unconditional refusal testを admission拒否/正例へ置換
  - 全負例で claim leaf、run directory、certificate、journalが増えないこと
  - admissionが1回だけで snapshotを再利用すること
  - private core の全 official seam拒否
  - siblingが同じ scheduler evidenceを使える「既知 survivor」をテストで緑扱いせず明記

- [test_pegasus_floor_tools.py:1012](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t781-spool-feasibility/orchestrator/tests/test_pegasus_floor_tools.py:1012)
  - 現在の「nonce only」を `nonce + -U` の exact argv検査へ変更
  - [同:1148](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t781-spool-feasibility/orchestrator/tests/test_pegasus_floor_tools.py:1148) の実 submission argv期待を更新
  - [同:1426](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t781-spool-feasibility/orchestrator/tests/test_pegasus_floor_tools.py:1426) の実 NQSV qstat fixtureへ User Attributesを追加
  - approved SHA欠落・HEAD不一致が qsub前に停止すること

- [test_campaign.py:4824](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t781-spool-feasibility/orchestrator/tests/test_campaign.py:4824)
  - certified-writer preflight の silent/read-only、source drift、T126非回帰を維持

## 8. 必要な計算ノード実測

親が実装後に行うべき bounded 実測は次です。

1. 実 `floor_campaign.sh` を投入し、raw `PBS_JOBID` の qcat bytesが committed blob＋1改行と exact一致する。
2. 同 request の `qstat -f <0:除去ID>` が `izanagi_source_commit` を一意に返す。
3. 属性欠落・誤SHAの診断 requestが claim leaf作成前に rc=2で止まる。
4. 末尾改行あり/なしの2 scriptで可逆比較が成立し、`-n` 上限による切詰めを受理しない。
5. genuine floor job内の兄弟 processが同じ qcat/qstat証拠を取得できることを再確認し、A-1 survivorとして記録する。
6. private coreへ `measure_fn` 等を渡す攻撃が admission取得前に拒否される。
7. request END後に再取得不能であることを確認し、証拠非永続という A-5を再確認する。

本回答ではテスト、qsub、追加 probeを実行していません。既存の親 probe成果物だけを読みました。

## 総括

- `qcat` による scheduler spool bytes の独立取得と、committed blob＋1改行の可逆照合は実装可能。
- 取得は core 内部 helperで一度だけ行い、freeze preflightとともに `acquire_claim` より前へ移す。
- 最大の弱点は `PBS_JOBID` が caller-controlledで、真正 job内の兄弟 processも同じ証拠を得られるため A-1が閉じないこと。
- 案 A＋User Attributeは約350～550 production行だが、現状は guardを外さず設計メモに留めるのが妥当。