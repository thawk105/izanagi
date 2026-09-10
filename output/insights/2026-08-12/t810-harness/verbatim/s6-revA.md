結論は **NO-GO**。静的検査のみで、pytest は実行していない。

最も危険なのは、validator が分類に使う `attempt_receipt` と、`attempt_root` 内の実ファイルを結び付けていない点である。12 ノードを事後選択した forged `terminal_reduced` を rc=0 にできる。

## 所見

### 1. blocker — receipt と実ファイルが完全に分離している

CLI は request が指す任意の JSON を `attempt_receipt` として読みますが、`attempt_root` 内の `coordinator-receipt.jsonl` / `node-receipt.jsonl` は内容を一切読みません。[validate_t810.py:75](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t810-harness/tools/pegasus/validate_t810.py:75) [t810_validator.py:713](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t810-harness/orchestrator/campaign/t810_validator.py:713)

テスト自身が全 receipt ファイルへ `"fixture\n"` だけを書いて合格しており、この切断を実証しています。[test_t810_validator.py:114](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t810-harness/orchestrator/tests/test_t810_validator.py:114)

さらに `terminal_reduced` の脱落 slot は `completed is not True` なら execution 件数を検査しません。[t810_validator.py:664](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t810-harness/orchestrator/campaign/t810_validator.py:664)

具体的な破り方:

1. 13 slot 全部に canonical argv の execution 10 件を持つ外部 JSON を作る。
2. 選択から落としたい 1 slot だけ `completed=false`, `events=[]` とする。
3. `attempt_root` には先頭12 slotだけ measurements を置き、receipt ファイルの内容は任意にする。
4. `claimed_state="terminal_reduced"` とする。

コードは completed=12、started=12 と数え、13番目の execution を認識しながら、その measurements を要求せず合格できます。これは観測後に不利なノードを脱落扱いする経路です。

**成果物影響:** 13 ノードの実測から都合のよい12ノードを事後選択でき、`τ̂`・区間・結論 code・certified 選択を変更できる。

修正には、canonical な `attempt_root` 配下の receipt を stable-open して直接解析し、attempt nonce・slot id・receipt hash・measurements hash・estimate の入力集合を同一 chain に束縛する必要があります。

### 2. blocker — canonical forbidden roots は path が canonical ではない

production CLI は `canonical_forbidden_roots` を request から受け取ります。[validate_t810.py:78](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t810-harness/tools/pegasus/validate_t810.py:78)

validator が検査するのは3個の code 名だけで、path が次の正規位置かは照合しません。[t810_validator.py:860](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t810-harness/orchestrator/campaign/t810_validator.py:860)

- `<repo>/output`
- `<repo>/orchestrator/campaign/env_contract.py`
- `<repo>/orchestrator/campaign/env_contract_activations`

しかも checkout 外を指した finding と、その root の churn は非 blocking です。[t810_validator.py:878](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t810-harness/orchestrator/campaign/t810_validator.py:878) [t810_validator.py:917](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t810-harness/orchestrator/campaign/t810_validator.py:917)

例えば3 code をすべて静穏な外部 directory に向け、`repo/output` を外部 directory への symlink にしておけば、repository scan は symlink 本体しか記録せず、その target の churn は見ません。

**成果物影響:** calibration・activation・freeze/proof-chain の実体を変更しても validator の受理集合に残り、後続 consumer が異なる参照を読む。

production API からこの mapping を削除し、approved `repo_root` から exact path を内部導出すべきです。test injection が必要なら別の明示的な test-only seam に分離すべきです。

### 3. blocker — writable root と attempt/baseline/witness が束縛されていない

`make_t810_durable_root()` の戻り値は `.path` に落とされ、その後の書込み capability に使われません。[t810_validator.py:854](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t810-harness/orchestrator/campaign/t810_validator.py:854)

次の path はすべて caller 任意で、`writable_root` 配下である検査がありません。

- `attempt_root`
- `baseline`
- `pass-witness`

特に post validator の最終 scan 後、CLI が任意 path へ witness を書き、それ以上 repository を再走査せず rc=0 を返します。[validate_t810.py:86](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t810-harness/tools/pegasus/validate_t810.py:86)

具体例は、post の `--pass-witness` を未存在の `<repo>/output/new-pass.json` にすることです。scan 時点では存在せず、finalize が repository を変更した後に rc=0 になります。

また exact attempt tree を事前に `<repo>/output/...` に作り、宣言上の `writable_root` だけ外部にすれば、attempt 自体が repository 内でも pre/post とも通せます。

**成果物影響:** validator 自身または attempt が禁止領域へ artifact を流入させた状態で pass witness を発行し、proof chain が「静穏だった」と誤って証明する。

### 4. blocker — pre と post の lineage が閉じていない

post は構造が正しい任意の baseline JSON を読みますが、その baseline が成功した pre invocation の生成物である証拠を要求しません。[t810_validator.py:817](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t810-harness/orchestrator/campaign/t810_validator.py:817)

さらに pre の順序は:

1. baseline を create-only publish
2. pass witness を create-only publish
3. witness を consume

です。[validate_t810.py:84](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t810-harness/tools/pegasus/validate_t810.py:84)

したがって witness finalize が失敗して pre が rc=2 でも baseline は残ります。post はその baseline を、失敗した pre のものと知らずに受理できます。pre を実行せず、現在状態から同じ schema の baseline を作る経路も防いでいません。

**成果物影響:** pre gate が成功していない attempt を post 合格へ持ち込み、実際の投入前状態との差分を proof chain から消せる。

baseline envelope と pre witness に少なくとも preregistration digest、approval id、attempt nonce、pre invocation nonce、git identity、manifest/executable digestを封印し、post は同じ lineage の成功済み pre witness を必須にする必要があります。

### 5. blocker — “approved” git identity が caller の自己申告になっている

helper 単体の identity 比較はありますが、CLI では request と同様、caller が任意の `--approved-git-identity` JSON を選べます。[validate_t810.py:45](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t810-harness/tools/pegasus/validate_t810.py:45)

したがって置換 repo と、その repo から取得した identity JSON を同時に渡せば equality は恒真です。identity は preregistration approval receipt や別 authority の digest に束縛されていません。

また `validate_t810()` が最初に `repo_root.resolve()` してから `inspect_repository()` へ渡すため、`resolve_git_identity()` 内の「入力 `repo_root` 自体が symlink でない」という検査は迂回されています。[t810_validator.py:853](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t810-harness/orchestrator/campaign/t810_validator.py:853)

**成果物影響:** 承認された checkout とは別の HEAD・index・tracked bytes を基準状態として採用し、proof chain の repository 参照を差し替えられる。

GitIdentity は外部 authority に digest 束縛し、`repo_root` は resolve 前の入力も検査すべきです。

### 6. must-fix — join は5値を返すが、裁定どおりの分類ではない

良い点として、receipt 欠損・部分欠損は `incomplete_after_start` へ倒れます。`None` を event 不在とは読んでいません。[t810_validator.py:626](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t810-harness/orchestrator/campaign/t810_validator.py:626)

一方、成功状態の選択には caller の `claimed_state` を直接使用しています。[t810_validator.py:622](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t810-harness/orchestrator/campaign/t810_validator.py:622) これは裁定 §3 の「claimed state を分類に使わない」に反します。

実害は主に過剰拒否で、13 complete の証拠でも claimed が違えば `valid` ではなく `incomplete_after_start` になります。分類は receipt から一意に導出し、claimed state は最後に一致検査するだけにすべきです。

**成果物影響:** 同じ完全 receipt が caller の claimed 値だけで `valid` から `incomplete_after_start` に変わり、受理集合・attempt 台帳の終端状態が変わる。

### 7. must-fix — frozen presence matrix の大半を実装が読んでいない

`expected_attempt_layout()` が frozen matrix から実際に参照するのは `estimate` だけです。[t810_validator.py:694](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t810-harness/orchestrator/campaign/t810_validator.py:694)

次は凍結されているのに無視されています。

- `measurements`
- `node_receipts`
- `release_event`

関数は全状態で全13 slot の node receipt を無条件追加します。[t810_validator.py:701](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t810-harness/orchestrator/campaign/t810_validator.py:701) 一方、artifact の `pre_release_invalid` は `reached-slots-exact` です。[t810_prereg_v1.json:21](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t810-harness/tools/pegasus/policies/t810_prereg_v1.json:21)

親裁定の「all node receipt 完全」と artifact/protocol の「reached 分だけ」が矛盾したままなので、どちらを正とするか land 前に確定する必要もあります。

**成果物影響:** frozen artifact の digest を変えずに実装側だけで状態別ファイル受理集合を変更でき、正当な失敗 attempt が台帳から脱落するか、不足 artifact が受理される。

親の exact argv 配列追加方針は必要ですが、それだけでは不十分です。同型の穴が presence matrix と terminal FSM に残っています。exact argv は canonical attempt receipt の実 bytes と結び付いて初めて効力を持ちます。

### 8. must-fix — calibration symlink alias と bind mount を lexical path 比較で抜けられる

`output/env/<env>` が symlink の場合、calibration namespace の列挙はその env を単に skip します。[t810_validator.py:421](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t810-harness/orchestrator/campaign/t810_validator.py:421)

例えば:

```text
repo/output/env/pegasus -> /external/env
writable_root = /external/env/calibration
```

とすると、calibration root 集合は空のままです。後段の alias 検査も比較対象 root が無いため検出できません。

さらに repository と writable root の分離は `Path.is_relative_to()` だけなので、repo または `repo/output` の bind-mount alias は別 path として通ります。mount 検査も approved root と candidate が同じ writable pathなので、この alias を識別しません。

**成果物影響:** writable と認定された path 経由で calibration namespace や repository を変更し、後続 wildcard consumer の材料・環境参照を変えられる。

### 9. must-fix — 二重走査は pass witness 時点の snapshot を保証しない

各 tree は二回走査されますが、二回目終了後から result/witness 発行までに変更された場合の再検査がありません。[t810_validator.py:247](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t810-harness/orchestrator/campaign/t810_validator.py:247)

加えて:

- scan root 自身の dev/inode/ctime を inventory に保存しない。
- `_stat_fingerprint()` は `st_nlink` を見るが `FileRecord` には保存しないため、pre/post 間の hardlink 作成・削除は比較に出ない。
- linked worktree では `git_dir` だけを管理 tree として走査し、`common_dir` 全体は走査しない。
- `.git/objects` 全体を除外するため `objects/info/alternates` も落ちる。
- `_git()` が `GIT_DIR`、`GIT_INDEX_FILE`、`GIT_COMMON_DIR` 等の環境変数を sanitize しない。

mode は `FileRecord.mode` と index/status に入り、gitlink の HEAD/dirty も記録されています。しかし semantic closure と final seal の間にはまだ穴があります。

**成果物影響:** pass witness が指す snapshot と witness 発行時の実 repository/ref/alias 状態が異なり、proof chain の参照先が後から変わる。

### 10. nit

- executable が regular file であることは検査しますが、execute bit は要求しません。
- request と attempt receipt の JSON は duplicate-key rejection を使っていません。
- baseline の `os.write()` は short write を明示検査していません。
- exact `.claude/worktrees` は directory・symlink・file のいずれでも拒否しますが、別名 symlink から他 worktree を参照する場合は target を走査しません。

## dormant seal

現状の repository 内では dormant seal は閉じています。

- `Slice1ValidationResult` に launch/approval capability はない。
- `request_t810_launch()` は `run_authorized` の値にかかわらず必ず例外。
- validator/pass witness を launch へ変換する別 consumer は見つからない。
- `run_authorized=false` は loader と validator の両方で検査される。

ただし今後 pass witness consumer を追加する際、現行 witness は terminal state・preregistration digest・receipt digest を封印していないため、そのまま approval token にしてはいけません。

## 既存テストの検出力

各テストを通したまま構成できる破壊例です。

| test | 通したまま残せる破壊 |
|---|---|
| `test_m16_quiet...` | receipt と attempt file の切断、canonical root path 差替え |
| `test_pre_and_post...mode` | signature は維持し、wrapper の `mode` 分岐や request field で検査を選択 |
| `test_dormant_seal...` | `request_t810_launch` 以外に pass-witness→approval API を追加 |
| `test_terminal_reduced...` | 非 completed slot に10 execution を残す。現実装も該当 |
| `test_m1_m2_scan...` | `scan_tree` は維持し、`inspect_repository` だけ git 列挙へ変更 |
| `test_mode_change...` | `FileRecord.mode` を無効化しても tracked chmod は `git status` 差分で test が通る |
| `test_gitlink...` | submodule HEAD/common-dir semantic capture を落とす |
| `test_m9...` | claimed `valid` / `terminal_reduced` だけ優先する。test は claimed pre-release のみ |
| `test_m10...` | `None` は保守側にし、`{}` や coordinator/slots 部分欠損だけ event 不在扱い |
| `test_m11...` | realpath だけ比較し gitdir/common-dir を外す。または CLI authority を自己申告にする |
| `test_nested_worktree...` | exact path は拒否し、別名 symlink target を走査しない |
| `test_m12_empty_manifest...` | manifest 非空だけ維持し、slot 0 の恒真を導入 |
| `test_manifest_expected_digest...` | `""` だけ拒否し、`"auto"` 等で自己導出 |
| `test_manifest_rejects...` | unlisted symlink/socket、または別 namespace の extra を許す |
| `test_m14_activation_inventory...` | code 名だけ残し、実 path を空 directory に置換 |
| `test_m14_caller_cannot_omit...` |3 key は要求しつつ、3 value を任意 path のまま受理。現実装も該当 |
| `test_calibration_overlap...` | `_calibration_inventories()` 呼出しを削除。test は同関数を通っていない |
| `test_duplicate_round...` | argv/path/hash 照合を削除し、duplicate/zero gate だけ残す |
| `test_m15_pass_witness...` | CLI 側で「既存 witness があれば return 0」を追加。helper test は通る |

## 事前登録変異の静的予測

「意味上その保証を壊しながら全 test を通せるか」で判定しています。単純な一行削除が別の整合性エラーで赤になるだけの場合は KILLED と数えていません。

| 変異 | 静的予測 | 根拠 |
|---|---|---|
| M1 git `--exclude-standard` を走査源へ | **SURVIVED** | `scan_tree` を残し、`inspect_repository` の列挙だけ tracked＋非 ignored git source にできる。直接 test は helper しか見ない |
| M2 ignored directory で打切り | **KILLED** | `_scan_once` の directory 再帰を止めれば nested ignored file test が直接失敗 |
| M9 claimed state 優先 | **KILLED（狭い変異）** | 全 claimed state を優先する変異は既存 test が殺す。ただし valid/reduced だけ使う変異は生存し、現実装にも依存が残る |
| M10 receipt 欠損→event 不在 | **KILLED（`None` のみ）** | `None` は直接 test 済み。部分 object 欠損だけを不在扱いする変異は生存 |
| M11 identity equality 削除 | **KILLED（helper 内）** | distinct repo test が直接失敗。ただし production CLI の自己申告 authority は無検出 |
| M12 0件で全一致 | **SURVIVED（全保証として）** | manifest member 0 は殺すが、slot 0 の分類を直接 pin していない。複合変異の半分しか証明していない |
| M13 dormant seal を開く | **KILLED（既存 API）** | `request_t810_launch()` の正経路を開けば直接失敗。別 API 追加は生存 |
| M14 activation inventory を落とす | **SURVIVED（実効変異）** | code 名だけの空 inventoryを残せば既存集合 test は通り、実 path の churn を見なくできる |
| M15 既存 witness で合格 | **SURVIVED（CLI 変異）** | helper の create-only は殺すが、wrapper の既存 witness fast-path を試していない |
| M16 正規 attempt | **SURVIVED（期待どおり）** | 現正例は通る。ただし valid 1 topologyだけで、他4状態や alias/bind topology の過剰拒否は証明しない |

M1・M14 は素朴な一行削除なら内部の exact-set 検査などで赤になりますが、それは目的の gate が発火した証拠ではありません。DW-M03 の基準では過剰決定／別理由の kill です。

## 総括

**NO-GO。**

最も危険な穴は、**分類用 receipt が attempt directory の実 receipt・measurements・estimate に束縛されず、非 completed slot に実行記録を残したまま `terminal_reduced` を作れること**です。これにより、緑の validator を通しながら性能値の12ノード部分集合を事後選択できます。

land 前の最低条件は、receipt chain の実ファイル束縛、全出力 path の writable capability 束縛、pre/post lineage の封印、canonical forbidden path の内部導出です。