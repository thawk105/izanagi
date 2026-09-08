## 現況の読み

静的確認の結果、欠落箇所は job body の env-to-argv seam に限定できる。

- `refuse()` は [tools/pegasus/p3_s4_loop_pegasus.sh:12](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2182-k2-eval-wiring/tools/pegasus/p3_s4_loop_pegasus.sh:12) で定義され、実際に `exit 2` する。したがって新しい部分指定拒否も rc=2 になる。
- driver の四つの CLI は [orchestrator/campaign/p3_s4_loop.py:2299](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2182-k2-eval-wiring/orchestrator/campaign/p3_s4_loop.py:2299) から実装済み。
- manifest は driver の入口で解決され、classification と de-novo 宣言は receipt へ渡る。同じ設定が campaign identity と K2 proposal consumer に使われる。
- K2 coder consumer は [orchestrator/campaign/p3_s4_loop.py:2058](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2182-k2-eval-wiring/orchestrator/campaign/p3_s4_loop.py:2058) のとおり、`knowledge_input` と `coder_role` の同時指定を要求する。さらに [同:2473](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2182-k2-eval-wiring/orchestrator/campaign/p3_s4_loop.py:2473) では role が無いと `knowledge_input` を proposal loader へ渡さない。
- classification の三値制約と `de_novo_claim=true` の整合条件は [orchestrator/campaign/knowledge_manifest.py:524](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2182-k2-eval-wiring/orchestrator/campaign/knowledge_manifest.py:524) にある。これらの値域検査は driver 側に残す。
- job body の現行末尾は proposal と fixture の二分岐だけで、K2 argv は存在しない。

## 実装プラン (file:line 粒度)

### 1. job body の K2 env seam

[tools/pegasus/p3_s4_loop_pegasus.sh:53](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2182-k2-eval-wiring/tools/pegasus/p3_s4_loop_pegasus.sh:53)、現在の環境 sanitize と固定 export の直後、repository path 検査の前へ次のブロックを挿入する。

```bash
k2_env_names=(
  IZANAGI_S4_KNOWLEDGE_MANIFEST
  IZANAGI_S4_CODER_ROLE
  IZANAGI_S4_KNOWLEDGE_CLASSIFICATION
  IZANAGI_S4_KNOWLEDGE_DE_NOVO_CLAIM
)
k2_requested=false
for name in "${k2_env_names[@]}"; do
  if [[ -v $name ]]; then
    k2_requested=true
    break
  fi
done

k2_argv=()
if [[ "$k2_requested" == true ]]; then
  for name in "${k2_env_names[@]}"; do
    [[ -n "${!name:-}" ]] || refuse "missing K2 environment: $name"
  done
  [[ -n "${IZANAGI_S4_PROPOSAL_PATH:-}" ]] \
    || refuse "K2 environment requires IZANAGI_S4_PROPOSAL_PATH"
  k2_argv=(
    --knowledge-manifest "$IZANAGI_S4_KNOWLEDGE_MANIFEST"
    --coder-role "$IZANAGI_S4_CODER_ROLE"
    --knowledge-classification "$IZANAGI_S4_KNOWLEDGE_CLASSIFICATION"
    --knowledge-de-novo-claim "$IZANAGI_S4_KNOWLEDGE_DE_NOVO_CLAIM"
  )
fi
```

この位置なら既存の段順は次になる。

```text
required env → host gate → sanitize → K2 bundle preflight
→ path/HEAD/PIN → reservation → claim → gflags/glog → prebuild → driver
```

host gate は依然として K2 判定より先である。新しい拒否は trap 設置前なので、既存の早期拒否と同様に `compute-result.json` を生成しない。

K2 要素の順序は driver CLI の宣言順に固定する。

1. `IZANAGI_S4_KNOWLEDGE_MANIFEST` → `--knowledge-manifest`
2. `IZANAGI_S4_CODER_ROLE` → `--coder-role`
3. `IZANAGI_S4_KNOWLEDGE_CLASSIFICATION` → `--knowledge-classification`
4. `IZANAGI_S4_KNOWLEDGE_DE_NOVO_CLAIM` → `--knowledge-de-novo-claim`

値の whitelist は shell に複製しない。空値と組の欠落だけを job body が拒否し、role、classification、de-novo 整合、manifest 内容、proposal schema は既存 driver を正本とする。

### 2. 部分指定の拒否順

完全性検査を proposal 依存検査より先にする。

- manifest だけ: `missing K2 environment: IZANAGI_S4_CODER_ROLE`
- role だけ: `missing K2 environment: IZANAGI_S4_KNOWLEDGE_MANIFEST`
- manifest と role だけ: `missing K2 environment: IZANAGI_S4_KNOWLEDGE_CLASSIFICATION`
- manifest、role、classification だけ: `missing K2 environment: IZANAGI_S4_KNOWLEDGE_DE_NOVO_CLAIM`
- 四つすべてあるが proposal path が無いか空: `K2 environment requires IZANAGI_S4_PROPOSAL_PATH`
- K2 env が一つでも「設定済みだが空」: 当該名を `missing K2 environment` で拒否する
- K2 env がすべて未設定: 従来どおり proposal-only または fixture 経路を許す

`IZANAGI_S4_PROPOSAL_PATH` 単独は既存の非 K2 proposal 経路として維持する。proposal と `IZANAGI_S4_FIXTURE_VALUE` が同時指定された場合も、現行どおり proposal 分岐が優先されるため、新しい拒否は加えない。

### 3. proposal driver への挿入

[tools/pegasus/p3_s4_loop_pegasus.sh:535](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2182-k2-eval-wiring/tools/pegasus/p3_s4_loop_pegasus.sh:535) の proposal 分岐だけを次の形にする。

```bash
if [[ -n "${IZANAGI_S4_PROPOSAL_PATH:-}" ]]; then
  "$PY" -B -m orchestrator.campaign.p3_s4_loop \
    --allow-coder-derived-build \
    --isolate-worktree \
    --fetchcontent-prebuild-receipt "$prebuild_receipt" \
    "${k2_argv[@]}" \
    --run-iteration "$IZANAGI_S4_PROPOSAL_PATH"
else
  "$PY" -B -m orchestrator.campaign.p3_s4_loop \
    --allow-coder-derived-build \
    --isolate-worktree \
    --fetchcontent-prebuild-receipt "$prebuild_receipt" \
    --value "${IZANAGI_S4_FIXTURE_VALUE:-20}"
fi
```

空配列の `"${k2_argv[@]}"` は引数を一つも追加しないため、既存 proposal-only 経路を維持できる。fixture 分岐へ K2 argv を渡さないことも、K2 は proposal path 必須という前段拒否と一致する。

driver、`knowledge_manifest.py`、condition gate、screening driverは変更しない。

### 4. README §7

[tools/pegasus/README.md:319](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2182-k2-eval-wiring/tools/pegasus/README.md:319) の義務一覧へ、次を追加する。

- K2 env 四つは all-or-none の非空 bundle とし、一つでも設定された場合は `IZANAGI_S4_PROPOSAL_PATH` も必須。
- bundle は manifest、role、classification、de-novo の順で shell array に組み、proposal driver にだけ渡す。
- shell は値域を再定義せず、driver の既存 CLI、manifest parser、K2 consumer を最終判定とする。
- K2 env 未設定時の proposal-only と fixture の既存挙動は維持する。

[tools/pegasus/README.md:341](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2182-k2-eval-wiring/tools/pegasus/README.md:341) の driver argv 説明にも四つの任意 K2 flag と proposal-only 制約を追記する。

[tools/pegasus/README.md:350](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2182-k2-eval-wiring/tools/pegasus/README.md:350) の fence は、K2 正例を一つ示す次の一ブロックへ更新する。job script を含む `bash` fence はこれ一つだけ、`qsub` command は一物理行だけとし、`-o` と `-e` を保持する。

```bash
# admission-site: qsub-job-body
REPO_ROOT=/absolute/path/to/dedicated-checkout
EXPECTED_HEAD=$(git -C "$REPO_ROOT" rev-parse HEAD)
THIRDPARTY_SOURCE_ROOT=/absolute/path/from-hydrate-source_root
EVIDENCE_ROOT=/absolute/path/outside-all-repositories
ATTEMPT=unique-attempt-id
PROPOSAL_PATH=/absolute/path/to/proposal.json
KNOWLEDGE_MANIFEST=/absolute/path/to/knowledge-manifest.json
CODER_ROLE=coder-v4-autonomous-k2
KNOWLEDGE_CLASSIFICATION=reproduction_or_selection
KNOWLEDGE_DE_NOVO_CLAIM=false
mkdir -m 0700 "$EVIDENCE_ROOT/$ATTEMPT"
qsub -v IZANAGI_S4_REPO_ROOT="$REPO_ROOT",IZANAGI_S4_EXPECTED_HEAD="$EXPECTED_HEAD",IZANAGI_S4_EVIDENCE_ROOT="$EVIDENCE_ROOT/$ATTEMPT",IZANAGI_S4_THIRDPARTY_SOURCE_ROOT="$THIRDPARTY_SOURCE_ROOT",IZANAGI_S4_PROPOSAL_PATH="$PROPOSAL_PATH",IZANAGI_S4_KNOWLEDGE_MANIFEST="$KNOWLEDGE_MANIFEST",IZANAGI_S4_CODER_ROLE="$CODER_ROLE",IZANAGI_S4_KNOWLEDGE_CLASSIFICATION="$KNOWLEDGE_CLASSIFICATION",IZANAGI_S4_KNOWLEDGE_DE_NOVO_CLAIM="$KNOWLEDGE_DE_NOVO_CLAIM" -o "$EVIDENCE_ROOT/$ATTEMPT/job.stdout" -e "$EVIDENCE_ROOT/$ATTEMPT/job.stderr" tools/pegasus/p3_s4_loop_pegasus.sh
```

fence 後の説明は、非 K2 proposal は proposal path だけ、fixture は proposal path と K2 bundle の双方を省略する、と明記する。

## 壊れるテストと更新方針

### 直接壊れるもの

- [test_p3_s4_loop_job_contract.py:350](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2182-k2-eval-wiring/orchestrator/tests/test_p3_s4_loop_job_contract.py:350) の `"proposal"` 逐語 pin  
  `--fetchcontent-prebuild-receipt` と `--run-iteration` の間へ `"${k2_argv[@]}"` が入るため更新が必要。

- [同:580](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2182-k2-eval-wiring/orchestrator/tests/test_p3_s4_loop_job_contract.py:580) の `proposal` 変異登録  
  旧 fragment の出現数が 0 になる。新しい三行 fragment を固定し、receipt または K2 forwarding を除く変異が `job contract missing: proposal` の一理由で落ちるよう更新する。

`fixture` の逐語 pin、`test_fixture_driver_before_prebuild_is_rejected`、driver 二起動の検査は fixture 分岐を変えないため更新不要。

### 現状のままでは壊れないが強化が必要なもの

- [同:134](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2182-k2-eval-wiring/orchestrator/tests/test_p3_s4_loop_job_contract.py:134) の `_assert_static_job_contract`  
  env 名の順序、set 済み検出、非空完全性、proposal 必須、四引数の argv 順、proposal branch の array 展開を逐語 pin として追加する。

- [同:456](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2182-k2-eval-wiring/orchestrator/tests/test_p3_s4_loop_job_contract.py:456) の段順 marker  
  `k2_env_names=(` を bootstrap export より後、`repo=$(cd ...)` より前へ追加する。これにより K2 preflight が HEAD、reservation、build、prebuild より前であることを固定する。

- [同:507](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2182-k2-eval-wiring/orchestrator/tests/test_p3_s4_loop_job_contract.py:507) の refusal pin  
  `missing K2 environment: $name` と `K2 environment requires IZANAGI_S4_PROPOSAL_PATH` を既存 tuple に追加する。`refuse()` の `exit 2` pin は維持する。

- [同:1265](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2182-k2-eval-wiring/orchestrator/tests/test_p3_s4_loop_job_contract.py:1265) の README fence test  
  既存の「一ブロック、一 qsub 行、`-o`、`-e`」assert はすべて維持し、同じ command 行に proposal env と K2 env 四つが各一回あることを追加 assert する。

### 新しい負例と正例

K2 block だけを切り出して `bash -c` で実行する小さい harness を追加し、外部コマンドや本体 build を起動せず env 組合せと生成 argv を検査する。

この負例群が拒否できるのは、K2 env の欠落、設定済み空値、完全な K2 bundle に対する proposal path 欠落である。  
この負例群が拒否できないのは、manifest と proposal の内容、role と classification の値域、de-novo 宣言の意味整合であり、それらは既存 driver の CLI、parser、consumer に委ねる。

通る正例は、proposal path と四つの K2 env をすべて非空で渡し、生成された `k2_argv` が次と完全一致するケースにする。

```text
--knowledge-manifest
/absolute/knowledge.json
--coder-role
coder-v4-autonomous-k2
--knowledge-classification
reproduction_or_selection
--knowledge-de-novo-claim
false
```

既存期待値の反転、skip、削除、部分一致への弱化は行わない。

## 変異事前登録の候補

| 変異 | 狙う防壁 | 期待して赤になる nodeid |
|---|---|---|
| `[[ -v $name ]]` を非空検査へ変え、設定済み空 manifest を未設定扱いにする | set 済み空値も部分指定として拒否する境界 | `orchestrator/tests/test_p3_s4_loop_job_contract.py::test_k2_partial_environment_is_refused[empty-manifest]` |
| 完全性検査の `-n` を `-v` に変え、空 coder role を通す | 四 env がすべて非空であること | `orchestrator/tests/test_p3_s4_loop_job_contract.py::test_k2_partial_environment_is_refused[empty-coder-role]` |
| proposal path の `refuse` 行を `true` に変える | K2 bundle は proposal route だけで使えること | `orchestrator/tests/test_p3_s4_loop_job_contract.py::test_k2_partial_environment_is_refused[complete-k2-without-proposal]` |
| `k2_argv` 内で manifest pair と role pair の順序を交換する | 四引数の固定順と flag/env 対応 | `orchestrator/tests/test_p3_s4_loop_job_contract.py::test_complete_k2_environment_builds_ordered_argv` |
| proposal driver から `"${k2_argv[@]}"` を除く | 検証済み bundle が実際の driver argv へ届くこと | `orchestrator/tests/test_p3_s4_loop_job_contract.py::test_k2_argv_is_forwarded_only_to_proposal_driver` |

各変異の runner は表の単一 nodeid に絞る。ブロック全削除や env 名の一括置換は、段順、逐語 pin、複数負例を同時に赤くして単一理由にならないため候補から外す。

## 親 brief への異議

二点ある。

- [brief.md:58](/work/1/SFC/tanab/dev-wave-jobs/2026-09-09_t2182-k2-eval-wiring/brief.md:58) の P1 は manifest 起点の二条件だけで、role-only、classification-only、de-novo-only、設定済み空値を規定していない。P2 が四引数の明示伝送を要求する以上、四 env を all-or-none bundle とするところまで補う必要がある。
- [brief.md:73](/work/1/SFC/tanab/dev-wave-jobs/2026-09-09_t2182-k2-eval-wiring/brief.md:73) の「既存テストの期待値を変えない」は、同:37 の「逐語 pin を更新」と文字どおりには両立しない。本件では「防壁を反転、削除、skip、弱化しない」という意味に限定し、変更後のより強い逐語期待値へ更新するのが整合的である。

P1 の rc=2 については異議なし。現物の `refuse()` が `exit 2` であることを確認済みである。

## 総括

変更対象は job body、契約テスト、README の三ファイルだけで足りる。K2 env 四つを早期に all-or-none 検査し、proposal 分岐へ引用済み shell array として固定順で渡す。driver の CLI、受理集合、K2 consumer は変更せず、fixture と非 K2 proposal の既存経路も維持する。

指定どおり、ファイル変更、commit、pytest、Pegasus 投入は行っていない。