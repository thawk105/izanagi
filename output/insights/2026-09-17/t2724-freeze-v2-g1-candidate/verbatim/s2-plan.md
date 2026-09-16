## 前提の検算 (N1〜N7・P1〜P5)

指定された射影はすべて読めた。以下は実行計画であり、file 作成・編集・commit・pytest・candidate 生成は実施していない。現在の HEAD は `1042a1bc95057fa03117d504cfa2b0fafaae60d0`、`git status --short` の出力は空だった。

行番号の略記は次の repo 相対 file を指す。

- **HF**: `orchestrator/campaign/s8b_holdout_freeze.py`
- **EV**: `orchestrator/campaign/s8b_floor_evacuation.py`
- **RF**: `orchestrator/campaign/s8b_ratified_freeze.py`
- **HA**: `orchestrator/campaign/s8b_holdout_admission.py`
- **FS**: `orchestrator/campaign/s8b_floor_stats.py`
- **AR**: `orchestrator/campaign/s8b_attempt_registry.py`

| 前提 | 検算結果 |
|---|---|
| N1 | 正しい。candidate 固定 path は HF:49、2114。世代 path は RF:89 の別 namespace。`hooks/guard_write.py:314` は freeze namespace への直接 Write/Edit を拒否する。 |
| N2 | 正しい。HF:2049 は budget 本体を読み、承認文書の `budget` と canonical 比較する。入力 file は現木に不在。fixture の path は `orchestrator/tests/s8b_v2_freeze_fixture.py:881`。 |
| N3 | 正しい。HF:2084 は v1 を deepcopy。除外は HF:45 の freeze namespace のみ。該当 test は `test_s8c_preregistration_invariant.py:623`、hold 登録は `growth_test_holds.py:241`、`correctness_gate=True` は同:58。hold は clean scan 自体を免除しない。 |
| N4 | 部分的に再実測済み。原本 namespace は指定 run 1 件、run_dir は指定 5 file、result hash は `b111831e9d002b523b57b0096a04bf03bb86b9b01fb5418511909f8ed4075620`。固定退避先は不在、手動 bundle の `MANIFEST.json` は存在した。無人・108 file 全件 hash 一致はこの段では再確認していない。 |
| N5 | CLI 実在は正しい。ただし**現在の最初の拒否は `no-active-ratified-freeze`**。`s8b_oracle_manifest.py:1122` が active freeze を先に読む。そこを通った後、`s8b_oracle_spec.py:23,185` の未承認 pin により `no-approved-spec` となる。 |
| N6 | 正しい。実装記録は `docs/archive/worklog-phase3-0811-416-417.md:599`、stale 本文は `docs/archive/worklog-phase3-0825-944.md:194`。 |
| N7 | 表現を限定する。赤になるのは**X1 の成果物を含む checkout／branch**であり、既存の全 branch が一斉に赤になるわけではない。main への導入後、その成果物を継承する branch は赤になる。clean scan 本体は `s8b_launch_cert.py` ではなく `s8b_floor_campaign.py:5515`。 |

| provisional | 評価 |
|---|---|
| P1 | docs と chain の land 分離、X1 保存による将来 topology は成立する。ただし **D2077 step 4 の「当該 holdout 集合の official 走行を打ち切ると決めてから restore」まで満たしたとはいえない**。保存 branch は main の汚染を防ぐが、この判断を代替しない。 |
| P2 | 対象 root は正しい。実行経路は T-2698 木へ `EnterWorktree(path)` で移って cwd 既定を使う案を推奨する。別木からの `--repo-root` は guard 通過未実測。 |
| P3 | wrapper 不要は妥当。「呼び手」は operator、「呼出し入口」は CLI、と分けて記述する。CLI 自体を主体と書かない。 |
| P4 | 妥当。canonical bytes は **UTF-8・改行なし**。承認文書を新規発行する作業ではなく、既承認 `budget` の抽出である。 |
| P5 | 妥当。生成 CLI の ROOT は module 所在に由来するため、chain 木の module を実行する必要がある。cwd だけ変えて別木の script を指定しない。 |

最大の未解決点は P1 と D2077 step 4 の整合である。以下の restore 以降は、打ち切り決定、または隔離した候補作成に関する明示的な扱いが確定した場合の手順とする。「main へまだ載せないから D2077 を満たす」とは記録しない。

## producer の入力要件 (現物)

**chain 木内の必須入力**

| 入力 | 必要性・根拠 |
|---|---|
| `output/s8b-freeze/holdout_freeze.json` | 必須。worktree bytes の固定 hash・schema・holdout 集合を検証する。HF:2036。workload 定義はこの file を参照し、本文へ転記しない。 |
| `output/s8b-freeze/floor_protocol.json` | 必須。worktree と captured HEAD blob の一致、canonical hash、registry 契約との整合を要求する。HF:1390。 |
| `output/s8b-freeze-budget-approvals/g1.json` | 必須。固定 pin、canonical bytes、scope、承認者、日時、budget schema を検証する。HF:1310。現物 hash と pin の一致は本段で確認した。 |
| `output/s8b-freeze-budget-inputs/g1.json` | `--budget` で渡す本体。承認文書全体ではない。HF:2049。 |
| run_dir の `result.json` | 必須。official path 文法、protocol、統計、binary 記録、eligibility の検証対象。HF:1422、1630。 |
| 同 `manifest.json` | 必須。raw hash と result の参照、cells、schedule、binary 記録、perf evidence を照合。HF:1530。 |
| 同 `journal.jsonl` | 必須。session 列を result と比較し、attempt lifecycle・計測 binary hash を導出。HF:1579。 |
| 同 `launch_certificate.json` | 必須。HF:1666、1961。selected run の証明書を no-follow で読む。 |
| 同 `result.md` | **producer の直接入力としては不要**。namespace 全体の保存対象として restore・commit する。三軸 hit があれば closure に入る。HF:1978。 |
| v1 の `known_axes_freeze`、`generator`、`design_source` が指す HEAD blobs | 必須。HF:2013、2070。generator は HF 自身の固定 path。known axes は v1 の記録 hash と一致が必要。 |
| `external/ccbench` checkout | repository scan のため必要。HF:382 がここで `_tracked_regular_files` を呼ぶ。未初期化のまま進めない。 |
| その他の列挙対象 file | scan 時に読める必要がある。tracked regular files と、ignore されない untracked regular files。HF:352、370、482。 |

run_dir は次の固定相対位置を使う。

```text
output/env/pegasus/calibration/s8b-floor-official/20260916T111925Z-2c8cf9be/
```

**binary／claim の扱い**

- `output/env/pegasus/binaries/<sha256>` の実体は、この candidate producer 経路では不要。HF:1499 以降は portable record を `validate_portable_binary_record` に渡す。`s8b_binary_admission.py:324` は receipt・subject・proof・record の整合を検証し、同:442 では record の binary hash と receipt を比較する。`store_path` を開いて実 binary を hash する経路ではない。
- `output/claims/<run_id>.claim` も不要。HA inspector が読む claim は共有 admission root 内の cell claim であり、この run-directory claim ではない。
- submission directory、job staging、binary build directory も producer 入力ではない。
- したがって **本 wave の candidate 生成のために binaries／claims を手動 bundle から chain 木へ複製する必要はない**。将来の実走 consumer に対する保存価値とは区別する。binary store は `.gitignore:20` で除外済み。

**共有 admission root の必須入力**

同じ Git common dir を共有する worktree を使う。別 clone へのコピーでは、この条件を満たさない。root 導出は HA:620。

```text
<git common dir>/izanagi/s8b-holdout-admission-v1/
```

| 配下の入力 | 読む場所・条件 |
|---|---|
| `ledger.lock` | 必須。既存 inode を read-only open して shared lock。HA:730、6191。 |
| `claims/`、`consumed/` | 現方式の run でも directory 存在を要求。HA:6187。 |
| `ledger.jsonl` | 必須。run に属する admission rows を抽出。HA:6225。 |
| `measurement-generation-claims/<digest>.claim` | 本 run の各 cell の durable claim。HA:6364。 |
| `measurement-generation-consumed/<claim-digest>-<attempt-id-hash>.json` | 計測済み attempt の marker。HA:4640、6697。未消費 retry 枠の marker は必須ではない。 |
| `attempt-ledger.jsonl` | 本 run では必須。marker と attempt rows の対応を検査。HA:6732。 |
| `refreeze-disqualifications/` | 不在は許容。存在すれば全 entry を検査し、当該 run の resume marker を照合。HA:6003。 |
| `floor-attempt-registries/<freeze-sha>/<protocol-sha>/registry.jsonl` | **v5 result なので必須**。FS:1155、AR:893、1050。記録 prefix のみならず現在の registry 全体を replay してから prefix を照合する。 |
| `floor-attempt-registry-receipts/classification-claims/<address>.json` | terminal replay の classification claim。AR:1324、1950、2040。 |
| `floor-attempt-registry-receipts/<receipt-sha>.json` | classification receipt。AR:1357、1967。 |
| 同 `terminal-evidence/<sha>.json` | registry の各 terminal が指す evidence。AR:1160、1501。 |
| 同 `external-evidence/<sha>.json` | terminal の classification が指す外部 evidence。AR:1169、1563。 |

共有台帳は本 wave で生成・補修・再構成しない。欠落は入力不足として扱う。手動 run-backup の存在は、この live authority の代替にならない。

**環境契約と build policy**

- `env_contract.py:668` は `orchestrator/campaign/env_contract_activations/` の activation records を読み、active 全行の calibration を検証する。同:636。
- 現木の activation file は `00000001.json`。read-only lookup で確認した active calibration は次の 2 file。
  - `output/env/pegasus/calibration/registered/calibration-753f535a8d024727.json`
  - `output/env/linux-baremetal/calibration/calibration_t48_skew0p9_rr50_rmw0.json`
- calibration の実体読込み・hash 照合は `calibration_verify.py:81`。pegasus だけを運ぶ縮小 checkout は避け、base の tracked tree を維持する。
- `resolve_current_build_admission_policy()` は `build_admission.py:500,510`。入力は `.pin.CURRENT_PIN`、schema、authority kind、`GeneratorId`／`ReviewId` registry。外部 policy JSON や binary 実体は読まない。

**launch certificate の束縛**

`s8b_launch_cert.py:50` は exact keys、schema、hash 形式、v1 hash、protocol hash、run ID、UTC 開始時刻と run ID の秒一致を検証する。candidate 生成時には **現在の clean scan digest を再計算して証明書と比較しない**。それを行えば、戻した成果物自身が hit して拒否されるためである。

## D2077 各 step の実行手順

1. **wrapper 終了を確定する。**
   T-2698 README の完走記録に加え、親が実行直前に writer 不在・job 終端を確認する。本段の再確認対象は file 状態のみで、無人状態を保証していない。

2. **T-2698 worktree へ session を切り替える。**

   ```text
   EnterWorktree(/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2698-official-floor-resubmit)
   ```

   その木で、単一 command として実行する。

   ```bash
   python3 -m orchestrator.campaign.s8b_floor_evacuation evacuate --env-tag pegasus
   ```

   CLI の root 既定は cwd。EV:270。別木から `--repo-root` を渡す経路は使用可能性の候補に留め、guard 回避目的では使わない。

3. **退避結果を確認する。**
   EV:152 は namespace 直下の全 entry を累積 bundle に保存し、検証・公開後、EV:233 付近で各 run と空 namespace を削除する。submissions、claims、binaries は削除範囲外。

   固定 bundle は次の形になる。

   ```text
   <git common dir>/izanagi/s8b-floor-evacuation/pegasus/
     manifest.json
     payload/
       output/env/pegasus/calibration/s8b-floor-official/<全 run>/...
   ```

   EV:34 の `_safe` は祖先を含む symlink を拒否。EV:64 の inventory は ordinary directory/file のみ受理。EV:111 の `_validate` は top-level 2 entry、schema・namespace・env、run 文法、directory 集合、file hash、宣言 run 外 payload の不在を検証する。手動 bundle をこの位置へそのまま置かない。

4. **打ち切り判断を確定する。**
   D2077 step 4 は restore より前。P1 の保存 branch 案がこの順序の例外を意味するかは、親の consult／裁定で明示する。main への導入判断だけを後置して、既裁定の順序を満たしたことにはしない。

5. **chain worktree を base から作り、その木へ切り替える。**
   保存 branch は `freeze-g1-chain-t2724`。既存同名 branch があれば上書きせず状態を確認する。submodule を初期化し、namespace が不在または空であることを確認する。

6. **chain 木で全体 restore。**

   ```bash
   python3 -m orchestrator.campaign.s8b_floor_evacuation restore --env-tag pegasus
   ```

   EV:243 は非空 destination を拒否し、bundle を検証した staging から namespace 全体を戻す。bundle は残る。run／時刻／proto8 を選ぶ操作はしない。

7. **X1 → generate → X2。**
   以下の節の順序を守る。戻した木で official 床値の新規起動はしない。wave 木へは docs だけを戻し、chain commits を land 集合へ入れない。

## X1 commit

追加集合は、restore された run_dir の全 5 file と budget 入力の計 6 file。namespace に別 run が見つかった場合は、5 file 前提で選別せず全体を再評価する。

budget 入力は既存承認 JSON の `budget` を抽出し、HF:233 と同じ規則で直列化する。

```python
json.dumps(
    approval["budget"],
    ensure_ascii=False,
    sort_keys=True,
    separators=(",", ":"),
    allow_nan=False,
).encode("utf-8")
```

**末尾改行は付けない。** `docs/s8b-budget-approval-user-turn.md` §5 の「両者は 1 byte も違ってはいけない」は承認文書全体との raw 一致ではなく、現コードでは抽出した budget の canonical 一致である。

本段で原本 5 file を `holdout_conjunction_hits` に渡した結果は、両 holdout とも次の 3 file のみだった。

```text
journal.jsonl
manifest.json
result.json
```

`result.md` と `launch_certificate.json` は hit しなかった。T-2698 README の記録と一致する。

それでも `result.md` を含めて保存する。将来 bytes が異なる場合に hit すれば、HF:1989 の専用 6 path に含まれないため、captured HEAD blob と worktree bytes の一致が必要になる。X1 に含めることで、その条件を満たせる。

commit 前に explicit path staging と staged diff を確認し、無関係 file を混ぜない。message 案：

```text
Record official floor inputs for freeze v2 g1 candidate

Preserve the restored official namespace and the approved budget projection
on the saved candidate chain.

AI-Agent: product=<実際の寄与者>; model=<表示値>; reasoning=<表示値>; role=integrator
```

trailer の placeholder は実値へ置換する。推測せず、非表示なら `not-exposed`、確認不能なら `unknown`。本計画が実質的に採用された場合の researcher 寄与も、親が `docs/ai-provenance.md:19,66` に従って記録する。AI が関与する X1 に `AI-Agent: none` は使わない。

X1 の SHA を取得し、以後 generate まで HEAD を進めない。

## generate と X2 commit

chain 木の module を、次の argv で実行する。

```bash
python3 -m orchestrator.campaign.s8b_holdout_freeze generate-v2-candidate --floor-result output/env/pegasus/calibration/s8b-floor-official/20260916T111925Z-2c8cf9be/result.json --budget output/s8b-freeze-budget-inputs/g1.json
```

`--output` 既定は次の固定 path。別 path は HF:2114 で拒否される。

```text
output/s8b-freeze-candidates/holdout_freeze.v2.g1.json
```

HF:2032 が HEAD を捕捉するため `frozen_at_head=X1`。HF:2127 は no-follow directory traversal、`O_EXCL`、fsync による create-only 書込みを行う。既存 candidate を自動削除して再生成しない。

| 拒否 | 切り分け |
|---|---|
| `floor-selection-rule-mismatch` | 同 env・同 proto8 の earlier result に適格 run がある。namespace の一部を消して通さない。HF:1940。 |
| `floor-selection-eligibility-underivable` | earlier run の manifest／journal／共有 admission から適格性を導出できない。選択対象外として無視しない。HF:1825。 |
| `floor-admission-unverifiable` | sibling file、共有 root／lock／ledger／registry などの欠落・読取り不能。手動 backup で authority を捏造しない。 |
| `floor-admission-mismatch` | result・manifest・journal・claim・marker・ledger・registry replay の不一致。末尾 reason を保持して調査する。 |
| `budget-approval-*` | 承認 pin、raw canonical、scope、budget 抽出を確認。pin や承認数値は変更しない。 |
| `measurement_closure` 関連 | 専用 path 外 hit が X1 にない、または worktree と blob が違う。走査対象を狭めず原因 file を特定する。 |
| `eligible_for_refreeze` 関連 | FS:1143 の live derived 値との不一致と、HF:1653 の true 要求を区別する。自己申告だけでは通らない。 |
| `floor-launch-certificate-invalid` | 証明書の欠落、hash、run ID、UTC 秒束縛を確認する。 |
| create-only 拒否 | 既存 leaf／symlink／directory 状態を確認。既存候補を上書きしない。 |

成功後は candidate の sha256、X1、入力 hash、producer rc、branch を記録する。三軸を含む candidate 全文や scan 全出力を insight に複製しない。

X2 は candidate **1 file の追加のみ**。

```text
Generate freeze v2 g1 candidate from committed official floor inputs

AI-Agent: product=<実際の寄与者>; model=<表示値>; reasoning=<表示値>; role=integrator
```

X2 は世代導入 commit G ではない。candidate namespace の保存 commit である。

## candidate の静的検証

親が chain 木で実施する read-only 検証は次の範囲とする。Python は `-B` または `PYTHONDONTWRITEBYTECODE=1` を使い、検証用 file を新設しない。

1. **bytes／schema**
   candidate を読み、HF `_canonical_bytes(parsed)==raw`、sha256、RF `_parse_generation_document(raw, 1)` を確認する。RF:900 は strict JSON・exact top-level schema・世代番号までであり、批准検証の代替ではない。

2. **入力との対応**
   `frozen_at_head==X1`、v1 hash、floor source hash、protocol hash、承認 budget の canonical 一致、floor の diagnostics 除外投影を確認する。HF:1351、2070、2084。

3. **blob 条件の部分検査**
   source records は X1 blobs と照合する。closure entries は X1 に存在し、記録 hash・worktree bytes と一致することを確認する。将来 G が X1 の直子で同じ入力を保持する場合の必要条件までを示す。

4. **未発効確認**
   chain 木と wave 木の各々で `resolve_active_generation(root)` を呼び、**`RatifiedFreezeError.reason=="no-active"` を期待する**。「no-active を返す」のではなく例外送出である。RF:1365。別 reason を未発効成功扱いしない。

   あわせて base からの `output/s8b-freeze/` diff が空、namespace の untracked がなく、現物 bytes が開始時から不変であることを確認する。HEAD 純粋な resolver の結果だけで worktree 全 bytes 不変を代替しない。

5. **全体 scan**

   ```bash
   python3 -B -m orchestrator.campaign.s8b_holdout_freeze search
   ```

   chain 木では **rc=1 が期待**。HF:2239 は report 出力後に zero-hit を要求する。期待 hit は run の 3 file と candidate の計 4 path。これは専用 6 path の部分集合である。

   追加 hit がなければ `measurement_closure=[]` が期待される。`result.md` の現物については非 hit を確認済みだが、chain 全体の scan は未実施。path 集合・rc・陽性対照件数だけを安全な射影として保存する。

`_verify_generation_semantics` は実在 G と active resolution を前提とするので、現在の candidate に対して批准成功として実行できない。偽の `ActiveResolution` を作って合格扱いしない。`load_ratified_freeze` も未発効状態では成功しない。

## 批准 topology と main への帰結

将来の履歴構造は次のように記述できる。これは topology の説明であり、本 wave に世代・approval・pointer 作成を含めない。

```text
X0 ─ X1 ─ X2     candidate 保存 branch
      └─ G      将来の世代導入 branch
```

- **V1a**: G は非 merge、親がちょうど X1、candidate 内の `frozen_at_head=X1`。RF:1001。G には AI trailer が必要で、`none` は拒否。RF:573。
- X2 の上に G を作ると `G^=X2` となり不一致。X1 を保存していれば、X1 から別 branch を作る余地が残る。
- **V1d**: floor protocol／floor source／measurement closure は G tree に存在し、記録 hash が一致すること。H tree にも存在し、worktree bytes が H blob と一致し、H までの履歴で異なる bytes が一度も現れないこと。RF:1036。
- `_immutable_introductions` は `rev-list(H)` 全 DAG の各 blob が absent または同じ OID であることを要求する。RF:488。通常 merge で G の ancestry を保存し、同 path に別 bytes の履歴を混ぜなければ成立しうる。merge しただけで自動的に満たされる保証ではない。
- 世代 G の introduction は一意でなければならない。RF:1186。G の cherry-pick／squash は親や導入履歴を変えるため、この保存案の代替にしない。

将来の A／X は、それぞれ非 merge・H ancestry・raw と parsed の双方で逐語 `AI-Agent: none` が必要。RF:541、558。さらに A は approval 1 件追加のみ、X は pointer 1 件追加のみ、`X^==A`。RF:1276。

D1578 のとおり `A^==Q` は未実装で、代わりに `A^==G` を要求しない。既存の部分適合を完全適合と記録しない。

main への帰結は、`s8b_floor_campaign.py:5515` → HF:370 → HF `search_repository` の実経路で裏付けられる。走査は現在の checkout の tracked と ignore されない untracked を対象とする。X1 の run file、X2 の candidate は除外外なので、これらを保持する main とその派生 branch では official 起動証明が拒否される。

## docs 変更案 (逐語)

以下は本文の置換案。runbook の既存 H3 見出しレベルは維持する。

**W-3 見出し本文**

```text
W-3. freeze v2 g1 候補の生成と人間承認手番
```

**W-3 本文**

```text
- **現状:** `s8b_holdout_freeze.py generate-v2-candidate` は実装済みである。
  official floor result と、その sibling manifest・journal・launch certificate、
  live admission 台帳、既承認 budget を検証して未発効の g1 候補を生成する。
- `--budget` には承認文書全体でなく、その `budget` と canonical 一致する budget 本体を渡す。
  入力文書は `output/s8b-freeze-budget-inputs/g1.json` に置く。
- **候補 path:** `output/s8b-freeze-candidates/holdout_freeze.v2.g1.json`。
  producer はこの固定 path に create-only で書く。
  **世代文書 path:** `output/s8b-freeze/holdout_freeze.v2.g1.json`。
  候補の保存と世代の導入・承認・active pointer の発効は別の手番である。
- official 成果物の退避・再配置・commit・候補生成は W-2 の一方向の順序に従う。
  候補を生成しただけでは active freeze は成立しない。
- **残る手番:** official 走行の打ち切りと候補採用の判断、および世代導入後の
  人間承認 A → active pointer X の別 commit。producer の新設は不要である。
```

**W-4 本文**

```text
- `s8b_oracle_manifest.py build-approved --output PATH` CLI は実装済みである。
  呼び手は operator とし、承認済み active freeze と reviewed spec が揃った後に実行する。
  このための wrapper script は新設しない。
- 現在は active freeze がなく `no-active-ratified-freeze` で拒否する。
  また `s8b_oracle_spec.APPROVED_SPEC_SHA256 = None` のため、
  active freeze 成立後も spec 承認までは `no-approved-spec` で fail-closed する。
- `s8b_oracle_driver.py run-block` は `--manifest` を必須で取る。
  CLI の存在は oracle 実走の認可や前提成立を意味しない。
```

**§5 R-3 行**

```text
| R-3 (W-3 + W-4 の分割) | **裁定済み・実装済み。** [T-750] は producer identity・budget authority とも (a) で裁定し、2026-08-11 に producer と manifest CLI を実装した (worklog 405 / 417)。残るのは実データによる候補生成、凍結の人間承認手番、および reviewed spec の承認である。 |
```

candidate 生成成功後に記録する場合は、この行の「実データによる候補生成」を完了形へ更新する。未実行の現在から成功を記載しない。

**worklog 更新本文**

```text
- [T-750] **P2・裁定済み・実装済み → 実凍結の人間判断待ち**: producer identity・budget authority は 2026-08-11 にともに (a) で裁定し、freeze v2 g1 producer と oracle manifest CLI は実装済み。残件は official 走行の打ち切り・g1 の床の採用・chain の main 導入と承認 A → pointer X の判断、および reviewed spec の承認。候補生成の実施結果と所在は今回の一次資料を参照する。
```

文面変更なので action は `carry` ではなく **`更新`**。他の未変更 item は暗黙 carry に任せる。

fragment 骨格は次のとおり。コード枠内の H3 は spool 文法上必要な action 見出しである。

```markdown
---
schema: izanagi-spool-v1
ledger: worklog
authored: 2026-09-17
wave: dev-wave-t2724-freeze-v2-g1-candidate
seq: 1
title: freeze v2 g1 候補の所在と残る人間判断を整理する
---

## 本文

- chain の land 分離と D2077 step 4 の扱いについて、親が実際に採用した判断を記録する。
- operator による既存 CLI の利用を {{D:oracle-manifest-operator}} に記録する。

## 次の一手差分

### 更新

- [T-750] **P2・裁定済み・実装済み → 実凍結の人間判断待ち**: <上記更新本文>
  base: <land 先 local main の実体 item の sha256>
```

`base` は `docs/spool/worklog/README.md` に従い、carry 鎖の実体について取得する。lookup は次の既存入口を使い、値を推測しない。

```bash
python3 tools/spool_fold.py --base-digest '[T-750]'
```

**decisions fragment 候補**

```markdown
---
schema: izanagi-spool-v1
ledger: decisions
authored: 2026-09-17
wave: dev-wave-t2724-freeze-v2-g1-candidate
seq: 2
---

## {{D:freeze-g1-chain-preservation}}. g1 候補の入力 chain を docs の land 集合から分離する

**決定:** X1 と X2 は保存 branch `freeze-g1-chain-t2724` に保持し、
本 wave の land 集合には含めない。wave worktree は文書と三軸を含まない一次資料に限定する。
この分離を D2077 step 4 の打ち切り判断の代替にはしない。

**理由:** main への入力成果物の導入は official clean scan を赤にする。
X1 を保存すれば、将来の世代導入 commit G を X1 の直子とする topology を維持できる。

**却下した選択肢:** chain を docs と同時に main へ導入する —
未確定の打ち切り判断を先取りするため。

## {{D:oracle-manifest-operator}}. oracle manifest は operator が既存 CLI から生成する

**決定:** W-4 の呼び手は operator、入口は既存の `build-approved` CLI とする。
wrapper script は新設しない。

**理由:** CLI は実装済みであり、残る前提は active freeze と reviewed spec の承認である。

**却下した選択肢:** wrapper の新設 —
現在の不足を解消せず、承認済み入力も存在しないため。
```

これらは親が採用した判断を記録する候補であり、未裁定の例外承認を「決定」として補わない。

## 裁定パッケージの骨格

冒頭に candidate hash、X1、X2、branch、入力 result hash、producer 実行結果、静的検証の到達範囲を置く。candidate 全文は添付せず所在を参照する。

| 裁定事項 | 親の推奨案として置く内容 | 根拠・限定 |
|---|---|---|
| (a) chain を main へ載せるか | **docs のみを先に land。chain の導入は official 打ち切り判断と一体で明示承認する。** | X1 を含む checkout では clean scan が赤になる。加えて D2077 step 4 は restore 前の判断なので、隔離候補作成との整合を先に確定する。 |
| (b) A → X の人間 commit へ進むか | **(a)(c) と実 candidate 検証が揃った後に進む。** | 今回は未発効 candidate まで。G の親、A/X の exact diff と trailer を別手番で満たす。W-4 の spec 承認は別の未解決条件。 |
| (c) この床を g1 に採用するか | **「配線下限が支配した、この 1 走行の床」として採用を推奨する案。** | rr20 は `35,817.945`、rr80 は `46,065.78`。stock 中央値はそれぞれ `1,193,931.5`、`1,535,526.0`。いずれも 0.03 倍で、全 pair の実測 `u_noise` は下限未満。between-run 安定性は未実測で、保証に含めない。 |
| (d) growth hold 解除時の赤をどう扱うか | **帰結を明記して受容するかを判断し、本 wave では hold・test・除外を変更しない。** | chain 成果物が存在すれば全 repo zero-hit test は解除時に赤になる。現在の skip を correctness 合格と表現しない。 |

(c) の数値は T-2698 README §3、1 走行・between-run の限界は同 §7 に対応する。`eligible_for_refreeze=true` 単独を採用根拠にせず、producer の live 再検証結果を併記する。

## リスクと未確定点

- **D2077 step 4 の扱いが最優先。** 保存 branch は隔離の仕組みであって、打ち切り裁定そのものではない。現在の依頼と既裁定の関係を親の consult で明記する必要がある。
- **guard 通過は未実測。** EV は内部で `git -C <root>`、`shutil`、rename を使用する。過去に Python script が通ったという memory は、この command の許可実測ではない。拒否時に別経路で迂回しない。
- **退避は原本を変更する。** 成功後、T-2698 の run と namespace が消える。submissions／claims／binaries はそのまま残る。途中失敗なら部分削除や耐久 backup 残留の可能性を例外本文と現物で確認する。EV:152。
- **restore 後の status。** 通常は official run 5 file が untracked として現れる。短縮表示では directory 1 行の場合があるため `--untracked-files=all` で確認する。budget 作成後は計 6 file、X1 後は clean、generate 後は candidate 1 file が期待。
- **untracked も scan 対象。** HF:370。candidate 全文、result 複製、三軸入り log を chain／wave の untracked に置くと新たな hit になる。
- **earlier-run 判定の範囲。** HF:1825 は同 env・同 proto8・selected より前の時刻だけを見る。現原本 namespace は 1 run と確認したが、固定 bundle が後から累積されれば restore 結果も変わる。対象を間引かない。
- **submodule。** HF:382 が直接列挙するのは `external/ccbench` の tracked regular files。nested gitlink 自体は除外され、ここから再帰走査しない。ただし未初期化時の親 repo への Git 探索を正常な列挙と扱わず、chain 木で正しい submodule checkout を確保する。
- **共有台帳の現在状態への依存。** v5 replay は terminal／external／classification evidence まで要求する。原本 5 file と binary backup だけでは再現できない。同一 bytes の台帳再構成を検出できない既知限界も残る。
- **静的確認と完了検査を区別する。** 本段では原本 file 集合・hash・局所 conjunction・budget pin・registry lookup を確認した。producer、全 repo scan、批准 resolver、pytest は実行していない。親の変更後検査は既存の `tools/run_tests.py`、docs／provenance checker の運用に従い、未実施結果を緑と記載しない。
- **budget 手順書の現況欄も古い。** `docs/s8b-budget-approval-user-turn.md` §2 の「承認不在／pin=None」は現物と異なる。本計画では既承認 artifact を authority とし、同文書 §5 の抽出手順を使う。承認のやり直しは不要。

## 総括

既存 producer で候補を作る技術経路は揃っている。binary 実体・run claim の追加複製は不要だが、共有 admission 台帳と v5 attempt registry の evidence 一式は必須である。budget は改行なし canonical bytes、X1 は入力 6 file、X2 は candidate 1 file とする。

修正が必要なのは、**保存 branch だけでは D2077 の restore 前の打ち切り条件を満たしたことにならない点**、W-4 の現在の先行拒否が `no-active-ratified-freeze` である点、clean scan の影響が成果物を含む branch に限られる点である。この整理を確定したうえで、隔離 chain の生成と docs のみの land を進める。