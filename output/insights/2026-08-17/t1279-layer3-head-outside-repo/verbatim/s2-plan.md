## 総括

- P1 の「明示値 → lock pin → 生成器 repo HEAD」は、official v2 campaign の値を変えうるため反証される。
- 修正版は「明示値 → 現行どおり campaign の Git HEAD → repo 外 v2 の lock pin → fail-closed」とする。
- repo 内では同じ `_git_head(campaign_dir)` を先に実行し、失敗時も lock へ退避しないため、値と受理集合をともに維持できる。
- 標準 8c 経路は `require_environment_contract=True` の既定値を通り、campaign.lock は必ず authority 付き v2 になる。
- `Path(__file__)` 起点の生成器 HEAD は packaging で不在または無関係な親 repo を拾いうるため採用しない。
- 修正は `layer3_report.py` 内に閉じ、public signature、返り値構造、schema、CLI、completeness gate は変更しない。
- 既存 `_git_head` monkeypatch は壊れないが回帰を隠すため除去し、lock pin の実値を検査する形へ変える。
- pytest は実行していない。以下は静的調査に基づく実装プランである。

## 1. P1 の実証

### 現行 official 値

[layer3_report.py:162-171](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1279-layer3-head-outside-repo/orchestrator/campaign/layer3_report.py:162) の `_git_head(campaign_dir)` は、campaign を起点に祖先 Git repository の HEAD を得る。`build_report` は同ファイル `416-445` で lock を読むが、`511` では lock を使わず、明示値が無い場合に `_git_head(campaign_dir)` を呼ぶ。

現在の代表的 official campaign と生成器 directory の双方で、静的確認時の値は次の同一値だった。

```text
699c9caedec83402d633f86342429bedf86f82a9
```

また、repo 内の `campaign.lock` は全件検索で 32 件、`schema_version` または `campaign-lock/v2` を含むものは 0 件だった。したがって現存する tracked official campaign は v1 であり、P1 の lock authority 分岐を通らず生成器 repo HEAD へ進むなら、現物については現在値と同じになる。

ただし、これは official 入力一般の不変性を証明しない。

### provisional P1 の反証

v2 lock の `contract_loader_commit` は、lock 作成時点の HEAD を [contract_loader_binding.py:324-337](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1279-layer3-head-outside-repo/orchestrator/campaign/contract_loader_binding.py:324) で取得し、`ident.py:469-484` で authority へ保存する。

したがって次の official 入力で値が変わる。

- v2 lock 作成時の HEAD を `H0` とする。
- その後 repository HEAD が `H1` へ進む。
- 明示 `generated_from_head` 無しで同じ campaign を再生成する。
- 現行実装は `H1` を返す。
- provisional P1 の lock-first は `H0` を返す。

`H0 != H1` なら明確な差であり、official 値不変に反する。よって lock-first 順序は採用できない。

修正版は、repo 内 campaign では従来と全く同じ `_git_head(campaign_dir)` を先に実行する。これが成功すれば値は構造的に同一であり、失敗しても repo 内なら元の例外を再送出するので受理集合も広がらない。

### 生成器自身の repository HEAD 案

`Path(__file__)` 自体は file なので `git -C` へ直接渡せず、最低でも `Path(__file__).resolve().parents[2]` のような directory 解決が必要になる。

| 配置 | 挙動 |
|---|---|
| 通常 checkout | `.git` directory が生きていれば成功する。 |
| linked worktree | 現 worktree の `.git` は gitdir を指す file だが、現環境では正常に worktree 固有 HEAD を返した。gitdir の移動・prune・破損、unborn HEAD、Git 不在では失敗する。 |
| 初期化済み submodule | submodule の `.git` file が有効なら submodule HEAD を返す。 |
| submodule metadata 欠落 | deinitialize、gitdir 消失、単なる directory copy では失敗する。外側 superproject が祖先なら、失敗せず外側の誤った HEAD を返す場合もある。 |
| editable install | checkout 実体を指す限り成功しうる。 |
| wheel・sdist 展開物 | 通常 `.git` が無いので失敗する。無関係な Git repository の配下へ install された場合は、その無関係な HEAD を拾いうる。 |
| zipapp・frozen package | `__file__` 起点が実 directory にならず失敗しうる。 |

厳密な top-level 照合は既に `contract_loader_binding.py:89-122` にあるが、これを report 時に再実行すると新しい厳密化になる。8c は v2 lock pin を既に持つため、生成器 repo HEAD fallback 自体を採用しない。

## 2. P2 の実証

標準 8c の呼び出し連鎖は次のとおり。

1. `p3_autonomous_workload_trial.py:3365-3373` が exploration run root を構成し、`3405-3424` から `run_trial` を呼ぶ。環境指定 exploration root は [layout.py:285-331](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1279-layer3-head-outside-repo/orchestrator/campaign/layout.py:285) で Git ancestor があれば拒否される。
2. `run_trial` は `2883-2891` で正式 `claude-headless` 経路の drive 注入を拒否し、`2893-2896` で標準 `trigger.drive_iteration` を選ぶ。
3. `_finish_trial` の `2109-2131` から `_run_workload` へ標準 drive が渡る。
4. `_run_workload:2461-2474` が environment contract を取得し、`_prepare_campaign_identity` へ渡す。`_campaign_for:669-674` は admission policy と environment contract を config に束縛する。
5. build 経路は `2479-2484` で `exploration_campaign_layout` を選ぶ。
6. `2754-2770` から `_drive_s8c_generation` を呼び、同関数 `1222-1239` が標準 trigger へ `_contract` と `_resolved_site` を渡す。
7. [p3_s4_loop_trigger_gating.py:802-820](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1279-layer3-head-outside-repo/orchestrator/campaign/p3_s4_loop_trigger_gating.py:802) は contract を再束縛し、`ident.ensure_resumable_attempts(..., admission_policy=...)` を呼ぶ。この呼び出しは `require_environment_contract` を明示していない。
8. [ident.py:419-430](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1279-layer3-head-outside-repo/orchestrator/campaign/ident.py:419) の実引数は、signature の既定 `require_environment_contract=True` で決まり、`426-429` から `ensure_campaign_identity` へ明示的に転送される。
9. `ensure_campaign_identity:469-484` は True 分岐で authority 付き v2 を作り、`488` で原子的に campaign.lock を獲得する。v1 を書くのは `485-487` の False 分岐だけである。
10. production で False を明示する全件は `guided.py:176-179,203-205` の guided exemption だけだった。8c からの呼び出しは無い。
11. さらに [autonomous_trial_completeness.py:344-365](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1279-layer3-head-outside-repo/orchestrator/campaign/autonomous_trial_completeness.py:344) が campaign-chain に v2 authority を必須とし、`2324` から実際にこの検査を呼ぶ。

結論として、成功可能な標準 8c exploration campaign の lock は v2 であり、v1 にはならない。`contract_loader_commit` は `campaign_lock.py:197-200` で lowercase hex40 と検証済みである。

したがって「v1 になりうる場合」の pin 候補列挙は条件不成立で対象なし。なお 8c の `ccbench_commit` は `pin.py:28` の 7 桁 `511c953` で、hex40/hex64 を満たさず、そもそも生成器 commit ではないため代用しない。

## 3. P3 の検討

layer3_report 側で閉じる案を採る。

| 呼び出し箇所 | `generated_from_head` | 穴の有無 |
|---|---|---|
| `p3_autonomous_workload_trial.py:1762-1766` → `render` | 省略 | 今回の実害箇所 |
| `layer3_report.py:624-634` `render` → `build_report` | optional を転送 | 呼び手が省略すれば同じ穴 |
| `layer3_report.py:535-583` `build_accepted_report` → `build_report` | optional を転送 | 将来 consumer が省略すれば同じ穴。現状 certified consumer 無し |
| `layer3_report.py:656-663` CLI `main` → `render` | option 未指定なら None | fallback 利用。ただし repo 外 path は `373-381` で先に拒否され、exploration 用 `output_root` も CLI に無い |
| `autonomous_trial_completeness.py:2100-2104` → `build_report` | `"0" * 40` を明示 | 穴なし。比較前に persisted 値を別途検証 |
| `layer3_report.py:669-670` | `__main__` が `main()` を呼ぶ | CLI caller はこれだけ |

呼び手側で直す場合、`_finalize_build_cell_admission` が campaign.lock を再読して pin を取り出し、`render` へ新引数を渡す必要がある。これは次の欠点を持つ。

- `layer3_report.py:444` が既に同じ lock を検証済みであり、読み取りと例外変換が重複する。
- `build_accepted_report`、直接 `render`、CLI の省略経路を取り残す。
- `test_p3_autonomous_workload_trial.py:2479,2580,2655` の `fake_render` signature も追随が必要になる。
- layer3 report の provenance 解決責務が producer 側へ漏れる。

一方、`build_report` 内なら検証済み `decoded_lock` をそのまま使え、全入口を一度に覆える。Python 外の CLI 呼び出しも全件検索したが、正本 docstring の起動例以外に wrapper や `-m` caller は無かった。

## 4. 実装プラン v1

### production

[layer3_report.py:162-172](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1279-layer3-head-outside-repo/orchestrator/campaign/layer3_report.py:162) の直後へ、値の選択だけを行う private helper を追加する。

```python
def _resolve_generated_from_head(
    campaign_dir: Path,
    decoded_lock: campaign_lock.DecodedCampaignLock,
    generated_from_head: Optional[str],
) -> str:
```

処理順は次のとおり。

1. `generated_from_head is not None` なら、その値を無変更で返す。
2. `_git_head(campaign_dir)` を現行どおり呼び、成功すればその値を返す。
3. 失敗時、`campaign_dir` が `_DEFAULT_OUTPUT_ROOT.parent` 配下、つまり生成器 source repo 内なら元の `Layer3ReportError` を再送出する。
4. source repo 外で、`decoded_lock.authority is not None` なら、検証済み `authority.contract_loader_commit` を返す。
5. authority が無い v1 なら元の `_git_head` 例外を再送出する。

`layer3_report.py:511` は ternary をこの helper 呼び出しへ置き換える。`decoded_lock` は `444` で既に得ているため、新しい読み取り、検証層、schema は追加しない。

### 維持する signature

以下は全て変更しない。

- `_git_head(campaign_dir: Path) -> str`
- `build_report(campaign_dir: Path, generated_from_head: Optional[str] = None, *, output_root: Optional[Path] = None) -> Dict[str, Any]`
- `build_accepted_report(...) -> Dict[str, Any]`
- `render(campaign_dir: Path, out_json: Path, generated_from_head: Optional[str] = None, *, output_root: Optional[Path] = None) -> Dict[str, Any]`
- `main(argv: Optional[Sequence[str]] = None) -> int`

返り値の key、型、schema version も変更しない。

### fail-closed を保つ条件

- malformed lock は `_read_campaign_lock:95-103` で従来どおり失敗。
- repo 内 campaign の Git 失敗は、v2 authority があっても fallback せず従来どおり失敗。
- repo 外 v1 で Git HEAD が取れなければ失敗。
- repo 外 v2 でも authority decode が失敗すれば失敗。
- `_resolve_campaign_dir:373-381` は変更せず、論理 `output_root` 無しの任意 repo 外 path は引き続き拒否。
- 明示値の新規 hex 検査は追加しない。既存 API は `"fixed"` などを受理しており、今回の厳密化対象ではない。8c の自動 fallback 値だけは decoder により hex40 になる。
- `autonomous_trial_completeness.py:2091-2098` の hex40/hex64 要求を維持する。

### 触らない箇所

- `p3_autonomous_workload_trial.py:1745-1766`: production caller は変更しない。
- `campaign_lock.py:167-241`: authority の既存検証で十分。
- `ident.py:419-500`: 8c lock は既に v2。
- `contract_loader_binding.py`: report 時の再検証や generator HEAD 取得を追加しない。
- `autonomous_trial_completeness.py:56,2086-2140`: hex 要求と比較射影を維持。
- `layer3_schema.json:9`: schema 変更不要。
- `layout.py:285-331`: exploration の repo 外強制を維持。
- CLI argument、決定論比較、admission gate、certifying 経路は変更しない。
- decisions の新設は不要。既存ユーザー裁定を parent の worklog fragment へ記録するだけとする。

## 5. consumer 追随の全件

`rg` と `orchestrator/**/*.py` の AST 全走を使い、`head` で切らず検索した。

public signature と返り値を変えないため、通常 consumer の機械的な追随は発生しない。ただし回帰を隠す test seam は更新する。

- `test_p3_autonomous_workload_trial.py:2368` の `_git_head` monkeypatch は位置引数 1 本のままでも動くが、新 fallback を迂回するため削除する。
- 同ファイル `2479,2580,2655` の `fake_render` は caller 側を変えないので変更不要。
- `test_ccbench_spawn_sites.py:78` は `_git_head` 内の subprocess site が 1 箇所であることを数える。新 helper は既存 `_git_head` を呼ぶだけなので変更不要。
- `autonomous_trial_completeness.py:2091-2098` は persisted 値を hex40/hex64 に限定する。lock の `contract_loader_commit` は hex40 なので追随不要。
- `autonomous_trial_completeness.py:2139` は比較時だけ field を除外するため変更不要。

テスト内の全直接 call は次のとおり。

- `test_layer3_report.py`
  - `build_report`: `429,513,539,575,599,623,642,658,673,694,707,729,747,769,836,1149,1237,1312,1324,1331,1341,1369,1378,1392,1429,1447,1465,1498,1505,1509,1536,1562,1575,1592,1605,1643,1652,1670`
  - `render`: `495,502,714,1179,1360,1361,1618,1636`
  - `build_accepted_report`: `793,818,853,877,936`
  - signature consumer: `701,704,804`
  - このうち head を省略する既存 call は `818` だけだが、unsealed receipt が `548-553` で先に拒否されるため fallback へ到達しない。
- `test_t126_qualification_artifacts.py`
  - `build_report`: `323,329,343,355,376`。全て明示値あり。
- `test_autonomous_trial_completeness.py`
  - `build_report`: `2313`。hex40 明示値あり。
- production の直接 call は P3 の表に挙げた 5 箇所だけだった。

## 6. テスト計画

自然な配置は [test_layer3_report.py:1659-1670](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1279-layer3-head-outside-repo/orchestrator/tests/test_layer3_report.py:1659) の既存 Git/fail-closed test 群である。

| 配置・test 名 | pin する契約 |
|---|---|
| `test_external_v2_campaign_uses_lock_authority_for_build_and_render` | `_campaign:179-210` を再利用し、Git HEAD 取得を失敗させる。`build_report` と `render` の双方が decoded `authority.contract_loader_commit` と完全一致することを検査。 |
| `test_git_backed_campaign_head_precedes_v2_lock_authority` | `_campaign` の親を一時 Git repo にして別 HEAD を作る。現在 Git HEAD と lock pin が異なる状態で、report が Git HEAD を選ぶことを検査。 |
| `test_source_repo_internal_git_failure_does_not_use_lock_authority` | source repo 内 path と v2 decoded lock を private resolver へ渡し、`_git_head` 失敗がそのまま送出されることを検査。official 受理集合不変の負例。 |
| `test_source_repo_external_v1_without_authority_stays_fail_closed` | v1 decoded lock と repo 外 path で、Git 失敗時に placeholder や他 fieldへ退避しないことを検査。 |
| `test_explicit_generated_from_head_still_wins` | `_git_head` を呼ばれたら失敗する spy にし、明示値が無変更で `meta` に入ることを検査。 |

既存の repo 外 exploration fixture は二系統ある。

- `test_layer3_report.py:179-210` の `_campaign` は source repo 外の `tmp_path/repo/output/campaigns/...` に、有効な v2 lock と WAL を作る。focused build/render test に再利用する。
- `test_p3_autonomous_workload_trial.py:2361-2465` の `test_three_workload_build_positive_admission_passes_real_layer3_chain` は `tmp_path/exploration/campaigns/...` を使う end-to-end fixture。`2364-2368` の comment と `_git_head` monkeypatch を削除し、各 persisted report の値が各 lock authority pin と一致する assertion を追加する。

既存 `test_layer3_report.py:1666-1670` は、`output_root` を明示しない裸の repo 外 path が引き続き `_resolve_campaign_dir` で拒否されることを pin するため残す。

親が実測する焦点対象は、新規 node、既存 3 workload node、`test_autonomous_trial_completeness.py::test_generated_from_head_mutation_is_rejected`。その後、関連 file 全体と `test_ccbench_spawn_sites.py`、`test_t126_qualification_artifacts.py` を `tools/run_tests.py` 経由で走らせる。ここでは未実走であり、緑とは報告しない。

## 7. 変異候補の下書き

| 変異内容 | 落ちるべき test node |
|---|---|
| `layer3_report.py:511` を wave 前の `generated_from_head if ... else _git_head(campaign_dir)` に戻す | `test_layer3_report.py::test_external_v2_campaign_uses_lock_authority_for_build_and_render`、`test_p3_autonomous_workload_trial.py::test_three_workload_build_positive_admission_passes_real_layer3_chain` |
| lock authority を campaign Git HEAD より先に選ぶ | `test_layer3_report.py::test_git_backed_campaign_head_precedes_v2_lock_authority` |
| repo 内外の分岐を除き、repo 内 `_git_head` 失敗にも authority fallback する | `test_layer3_report.py::test_source_repo_internal_git_failure_does_not_use_lock_authority` |
| `contract_loader_commit` の代わりに `environment_contract_sha256` を返す | `test_layer3_report.py::test_external_v2_campaign_uses_lock_authority_for_build_and_render`。hex64 自体は completeness を通りうるため、完全一致検査が必要。 |
| v1 で `ccbench_commit`、`"0" * 40`、生成器 HEAD のいずれかへ退避する | `test_layer3_report.py::test_source_repo_external_v1_without_authority_stays_fail_closed` |
| 明示 `generated_from_head` を無視して Git または lock を優先する | `test_layer3_report.py::test_explicit_generated_from_head_still_wins` |

read-only sandbox のため、実装・test 実行・文書更新は行っていない。