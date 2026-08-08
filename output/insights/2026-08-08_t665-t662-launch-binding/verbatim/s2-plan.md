# 設計裁定パッケージ

静的読解だけで判定した。ファイル変更、pytest、checker、launcher、Codex 子の実走は一切行っていない。以下の「率」は実測率ではなく、識別条件ごとの構造的な取りこぼし率である。

結論を先に述べると、推奨は案 A。ただし、単なる DW-O01 のコマンド置換ではなく、`launch_kind` から docs を読んで値を導出し、別 worktree を表現できる manifest v2 と authority digest を備える A+ とする。生の `codex exec` を手で叩く経路は A でも検出できないため、dev-wave 内では契約違反として禁止する必要がある。

## 共通設計

### 権威の写像

model の唯一の正本は DW-O01 の権威行である。段 3 の 2 本だけが順に `gpt-5.6-sol`、`gpt-5.6-luna`、他段は `gpt-5.6-sol` と定める（`docs/dev-wave/operations.md:6-13`）。effort は worker 節に分散している。

| `launch_kind` | model の読取元 | effort の読取元 | 現行期待値 |
|---|---|---|---|
| `s02-plan` | DW-O01 の「他段」 | DW-S02 | sol / max |
| `s03-consult-0` | DW-O01 の段 3 第1値 | DW-S03 | sol / max |
| `s03-consult-1` | DW-O01 の段 3 第2値 | DW-S03 | luna / max |
| `s05-author` | DW-O01 の「他段」 | DW-S05-A | sol / high |
| `s06-review` | DW-O01 の「他段」 | DW-S06-A | sol / high |
| `s06-fix` | DW-O01 の「他段」 | DW-S05-A の全文継承 | sol / high |
| `s06-focus` | DW-O01 の「他段」 | DW-S06-C | sol / high |

根拠は `docs/dev-wave/workers.md:5-24`、`docs/dev-wave/workers.md:46-68`。fix が DW-S05-A を継承することは `docs/dev-wave/workers.md:52-63` と `.claude/commands/dev-wave.md:80-81` にある。

段 3 は「段→多重集合」ではなく、`launch_kind` で二つの lane を区別する。多重集合は、再投入や無関係セッションが混ざると「どの job がどちらの model だったか」を失うため、個別起動の検査キーには弱い。

### 二重正本を作らない実装形

新設するなら `tools/dev_waves/launch_contract.py` に次の責務だけを置く。

```text
load_authority(authority_root) -> AuthoritySnapshot
expected_for(snapshot, launch_kind) -> (model, reasoning)
```

この module の構造表には「launch kind → docs 節・段3の序数」だけを置き、`gpt-5.6-sol`、`gpt-5.6-luna`、`max`、`high` を期待値として直書きしない。値は毎回、DW-O01、DW-S02/S03/S05-A/S06-A/S06-C の可視本文から抽出する。

`tools/check_docs.py:264-327` の定数は docs の採用済み文面を pin する変更管理 gate であり、実起動値の正本にしてはならない。既存検査は DW-O01 の一意性・model slug の局在を検査し（`tools/check_docs.py:3436-3491`）、DW-S02/S03/S06-A/S06-C の effort literal を検査する（`tools/check_docs.py:3494-3554`）。実起動 checker は同じ docs bytes を読み、抽出結果と authority digest を使う。

これにより、両 gate が同じ docs 文字列を参照できる。`check_docs.py` の literal 定数を runtime expected value として import する設計は採らない。DW-S05-A を既存 literal pin の対象へ追加することもしないため、見送り済み [T-667] の再提案には当たらない。

### DW-O13 に対する field の択一

実起動値の権威 field は以下だけとする。

- `turn_context.payload.model`
- `turn_context.payload.effort`

既存 launcher もこの二つを要求値と比較している（`tools/codex_worker_launch.py:751-778`）。既存 ledger も最初の値を記録し、後続の `turn_context` が変われば `inconsistent_turn_context` として扱う（`tools/codex_worker_ledger.py:384-457`）。新 checker も「最初の一件」ではなく、選択した session の全 `turn_context` が同じ期待値であることを要求する。欠落・複数値・途中変更はいずれも赤とする。

`turn_context.payload.collaboration_mode.settings.model` と `.reasoning_effort` は別名で diagnostic に保存してよいが、fallback や実起動値には使わない。

- session 途中で model/effort が変わった場合、top-level の複数 `turn_context` が不一致になり赤となる。nested settings が初期値のままでも救済しない。
- multi-agent では nested settings が collaborator の既定・override を表し、現在の session の top-level pair と異なり得る。子を検査対象にするなら、その子自身の rollout と `launch_kind` を別に束縛する。
- nested 値を同じ `model` / `reasoning` 名で集計すると識別子が二義化するため、内部名も `collaboration_settings_model` 等に分離する。

これは CLI/runtime が記録した値の照合である。served model の attest は scope 外。

## 案 A — launcher 集約

### 触るファイルと行

- `docs/dev-wave/operations.md:6-13`
  - DW-O01 を `codex_worker_launch.py run-dev-wave` 経由へ置換。
  - 外側の `nohup setsid`、`.done`、exit code 判定は残す。
- `tools/codex_worker_launch.py:107-180`
  - receipt/manifest schema に `launch_kind`、authority digest、解決済み sessions root を追加。
- `tools/codex_worker_launch.py:519-643`
  - wave manifest を複数 worktree 対応 schema v2 にする。
- `tools/codex_worker_launch.py:751-845`
  - top-level field を唯一の actual とする現行検査を維持。nested field は診断専用。
- `tools/codex_worker_launch.py:1098-1157`
  - docs 由来の値だけで argv を組み立て、manifest entry に job ごとの repo identity を記録。
- `tools/codex_worker_launch.py:1374-1444`
  - receipt に authority snapshot を記録。現行 `model` / `reasoning` は「derived expectation」と定義する。
- `tools/codex_worker_launch.py:1480-1581`
  - child worktree の repo binding と authority root を分離。
- `tools/codex_worker_launch.py:2232-2417`
  - `check-receipt` が docs digest と sealed rollout の両方を再照合。
- `tools/codex_worker_launch.py:2463-2492`
  - CLI を拡張。
- `tools/codex_worker_launch.py:2575-2581`
  - `CODEX_HOME` 由来の既定 root を解決後に receipt へ固定。
- 新設 `tools/dev_waves/launch_contract.py`
  - docs parser と `launch_kind` routing。値の直書きは禁止。
- `tools/codex_worker_ledger.py:120-173`、`tools/codex_worker_ledger.py:265-340`
  - manifest v2 を ledger でも読めるようにする。
- `orchestrator/tests/test_codex_worker_launch.py:90-131`
  - stage 導出、別 worktree、nested field、session 途中変更の回帰を追加。
- 新設 `orchestrator/tests/test_dev_wave_launch_contract.py`
  - docs 抽出と lane routing の単体検査。

新しい docs ファイルは作らない。

### CLI 差分

後方互換を保つなら、現行 `run` とは別に次を設ける。

```text
run-dev-wave
  --launch-kind {s02-plan,s03-consult-0,s03-consult-1,
                 s05-author,s06-review,s06-fix,s06-focus}
  --authority-root <primary-wave-worktree>
  ...現行共通引数...
```

この mode では `--model` と `--reasoning` を受け付けない。現行 CLI は `--model` が sol 既定、`--reasoning` が必須であり（`tools/codex_worker_launch.py:2475-2478`）、このままでは stage3 lane 1 の指定漏れを防げない。

`--manifest`、`--receipt` は維持する。`--sessions-root` も維持し、未指定なら launcher と child が共有する `CODEX_HOME/sessions` を解決して receipt に記録する。現在は root を解決するが receipt field には残していない。

### 別 worktree の処理

現行 launcher は `cwd` が `repo_root` 配下であることを要求する（`tools/codex_worker_launch.py:1480-1484`）。さらに manifest header の `repo_root/base_commit` は全 job で一致しなければならない（`tools/codex_worker_launch.py:595-602`）。したがって、wave worktree と `dw-t181-fix3` のような sibling fix worktree を同じ現行 manifest には入れられない。

A を採るなら次のどちらかが必須である。

1. 推奨: manifest v2 で `repo_root/base_commit/cwd/launch_kind` を session entry 側へ移し、header は `wave_id` と authority snapshot に限定する。
2. 代案: worktree ごとに manifest を分け、段 7/9 で receipt 群を wave_id により集約する。

単に DW-O01 の文字列を launcher へ置換するだけでは、段 6 fix を閉じられない。

### DW-O01 から失われる／変わる機能

- launcher 自身は背景 detach と `.done` sidecar を提供しない。これを削ると段 3 の並列投入と確実な完了判定を失うため、外側の shell wrapper は残す。
- 現行 DW-O01 は `-o` の出力を直接残す。launcher は validator と rollout evidence が揃ったときだけ最終 output を公開し、失敗時は attempt output を artifact dir に残す（`tools/codex_worker_launch.py:1727-1762`）。consumer は「失敗時にも最終 `.md` がある」という前提を捨てる必要がある。
- 単一 log ではなく attempt ごとの stdout/stderr/receipt になる。
- resource limit、retry、process-group 検査が新たに適用される。workspace-write では複数 attempt が許されない（`tools/codex_worker_launch.py:1524-1529`）。
- prompt は command substitution でなく `--prompt-file` から読む。非空検査は launcher preflight に移る（`tools/codex_worker_launch.py:1534-1545`）。

### 取りこぼし

- launcher 経由の job: session ID を stdout `thread.started` から取り、filename と `session_meta.session_id` に結ぶため、値検査の構造的 FN は 0%（`tools/codex_worker_launch.py:679-690`、`tools/codex_worker_launch.py:732-748`）。
- 段 6 fix: manifest v2 または分割 manifest を実装すれば、cwd が別 worktree でも取りこぼさない。
- 段 3: `s03-consult-0/1` を明示するので、二つの model を個別に検査できる。
- `CODEX_HOME` 変更: launcher と child が同じ環境なら既定解決で捕捉する。明示 `--sessions-root` が誤っていれば evidence missing で赤。
- `--sessions-root` 相当が無い／rollout が別 root に出た場合: evidence が見つからず、その job 自体を受理しない。
- 親が手で raw `codex exec` を一回だけ起動した場合: launcher の外なので 100% 取りこぼす。guard は Codex subprocess に未配線である（`hooks/guard_bash.py:39-45`）。A 単独ではこの bypass を発見できない。
- worker 内の multi-agent 子:直接の dev-wave job として別 receipt を持たせない限り対象外。

### 誤検出

session ID、filename、`session_meta` の三点照合なので、無関係 session、別 wave、同一 worktree の手動再実行を値検査対象へ誤認する可能性はほぼない。UUID が重複する、または同じ UUID の rollout が複数 root にある場合は FP として採用せず、evidence invalid で赤にする。

同じ job-id/receipt path の再利用は既存 create-only 契約で停止する。これは誤帰属ではなく運用上の fail-closed。

### docs 予算

新 DW-O01 は概算 1,200〜1,500 bytes。現節は約 833 bytes なので純増は約 400〜700 bytes。aggregate 残 16 bytes、operations 個別残 71 bytesに収まらない。`.claude/commands/dev-wave.md` は変更不要だが、同 command の残も 43 bytesしかない。cap は `tools/check_docs.py:168-180`、aggregate ceiling は `tools/check_docs.py:254` と `tools/check_docs.py:3704-3708`。

したがって、案 A は **[T-664] の予算捻出が前提条件**。

### fail-closed と trust root

authority parse、rollout 発見、全 turn の一致、validator、receipt seal のどれかが赤なら、その job の output を公開せず段 2/3/5/6 で止める。段 9 まで誤値を持ち越さない。ただし raw bypass は止められない。

trust root は docs bytes、launcher/parser bytes、Codex stdout、rollout、manifest/receipt、および「DW-O01 以外で起動しない」という親の遵守。receipt は executable hash と rollout seal を持つが、同一 account は docs、launcher、rollout、receipt を削除・書換えできる。欺くには launcher を迂回するか、seal 前に対応する証拠を偽造するか、checker と証拠を同時に改変すればよい。

## 案 B — rollout 事後検査

### 触るファイルと行

- 新設 `tools/check_dev_wave_codex_launches.py`
  - wave selector、docs authority 読取、stage/value checker、JSON audit artifact を担当。
- `tools/codex_worker_ledger.py:135-173`
  - 既存 sessions-root/cwd/manifest selector を共有可能な parser API に分離。
- `tools/codex_worker_ledger.py:351-464`
  - `originator`、全 user message、nested collaboration settings を別名で取得。
- `tools/codex_worker_ledger.py:574-650`
  - 現行 prompt-prefix stage 分類と retry grouping を再利用。
- `tools/codex_worker_ledger.py:972-1145`
  - strict issue を checker から利用可能にする。
- `docs/dev-wave/core.md:87-100`
  - 段 7 冒頭で checker を実行し、赤なら記録・commit へ進まない契約を追加。
- 代わりに段 9 とするなら `docs/dev-wave/core.md:107-112`
  - `DW-O23` より前に実行する。line 112 の usage collection 後では遅い。
- 新設 `orchestrator/tests/test_check_dev_wave_codex_launches.py`
  - selector の FN/FP、stage3 multiset、別 cwd、複数 roots を固定。

起動側の `docs/dev-wave/operations.md:6-13` と launcher は変更しない。

### 走査対象の選定

優先順位は次のとおり。

1. `--sessions-root` を複数明示して全 root の和集合を走査する。未指定の既定 root は、coverage を証明できないため strict mode では赤にする。
2. `session_meta.timestamp` が wave 開始から最後の job 完了までの時間窓に入ること。
3. `session_meta.originator == "codex_exec"`。
4. 最初の user message が wave 固有 artifact root を含むこと。
5. 補助として、cwd が primary wave worktree または列挙済み child worktree と一致すること。

Claude 側の先例は `--cwd-under`、`--since`、`--until` を selector に含める（`tools/collect_wave_usage.py:42-65`）が、cwd だけでは段 6 fix を閉じない。既存 Codex ledger の非 manifest mode も cwd 部分一致に依存する（`tools/codex_worker_ledger.py:142-168`、`tools/codex_worker_ledger.py:1033-1059`）。

rollout は `-o` の出力 path を自動では持たない。現行 ledger が取得できるのは user message の本文である（`tools/codex_worker_ledger.py:459-464`）。したがって、成果物 path は prompt 自体に記載されている場合だけ selector に使える。DW-O02 は wave 専用 subdirectory の親成果物を絶対 path で prompt に渡す契約なので、有力な anchor ではある（`docs/dev-wave/operations.md:15-20`）が、全 raw 呼び出しへの機械保証ではない。

### 段への帰属

現行 ledger は prompt の最初の非空行だけを role regex と照合する（`tools/codex_worker_ledger.py:574-587`）。B ではこれを利用するが、分類不能・複数一致は赤にする。

段 3 は選択された完成 session がちょうど 2 本である場合だけ、actual model の多重集合を DW-O01 の二値と比較できる。retry や再実行で 3 本以上になった場合、値から lane を逆算せず赤にする。post-hoc の手入力 `--stage-map` は独立証拠でないため、正しさ gate の救済には使わない。

### 取りこぼし

- primary cwd のみ: 別 worktree の段 6 fix は 100%取りこぼす。
- prompt の wave artifact anchor または child cwd を併用: `dw-t181-fix3` 型も選択できるが、親が全 child cwd を列挙するか、prompt に wave path が残ることが条件。
- 段 3: ちょうど 2 本なら不正な多重集合を検出する。retry、再実行、同時 manual session が入ると個別 lane の帰属不能。
- raw の一回限り呼び出し: 同じ root・時間窓・originator・wave anchor を持てば捕捉する。anchor が無い、別 cwd、別 root なら取りこぼす。
- `CODEX_HOME` 変更: audit 時にその root が列挙されなければ、そこにある session を100%取りこぼす。
- `--sessions-root` 相当の記録がない場合: 現在の環境から既定 root は推測できるが、launch 時と同じだったことを証明できない。strict gate は coverage unknown で止めるべき。
- malformed/missing `session_meta` が selector 前に落ちる場合、その file が wave 所属か判定不能。全 root scanで壊れ file を一律赤にすると別 wave の破損まで巻き込むため、完全性と FP の両立ができない。

したがって全体の FN 率は上限不明であり、「選択済み session の値検査」は完全でも「母集団の選択」は完全でない。

### 誤検出

次をすべて満たす無関係 session は wave の子に誤認される。

- 同じ worktree または列挙 child worktree
- 同じ時間窓
- `originator=codex_exec`
- prompt が wave の brief、plan、patch、成果物 path を引用

ユーザーが同一 worktree で package を手動レビューした場合、別 wave が同じ worktree を再利用した場合、同一 wave を再走した場合が典型。originator は手動 `codex exec` も同値なので区別材料にならない。

### docs 予算、fail-closed、trust root

段 7または段 9への checker 契約は概算 350〜550 bytes の純増。core 個別 cap には入る可能性があるが、aggregate 残 16 bytesを超える。案 B も **[T-664] の予算捻出が前提条件**。

推奨位置は段 7 冒頭。ここなら赤で commit を止められる。段 9だけなら local main 取り込みは止められるが、誤った model/effort での費消、生成物利用、wave branch commit は既に起きている。

trust root は docs、checker、root/window/cwd selector、session metadata、prompt、rollout。すべて同一 account が書換え可能で、rollout の削除・移動、timestamp/cwd/originator/prompt の改変、別 root の指定だけで母集団を操作できる。三案中もっとも selector への信頼が大きい。

## 案 C — 宣言 + 事後照合

### 触るファイルと行

- `docs/dev-wave/operations.md:6-13`
  - spawn 前の declaration と launch-id を埋め込んだ prompt の使用を追加。
- `docs/dev-wave/core.md:107-112`
  - 段 9 の双方向 reconciliation を `DW-O23` 前に追加。
- 新設 `tools/dev_wave_codex_manifest.py`
  - `declare` / `seal` CLI。
- 新設 `tools/dev_waves/launch_manifest.py`
  - manifest schema、locking、create-only declaration、hash chain。
- 新設 `tools/dev_waves/launch_contract.py`
  - docs authority の抽出。
- 新設 `tools/check_dev_wave_codex_launches.py`
  - manifest と rollout の一対一照合。
- `tools/codex_worker_ledger.py:351-464`
  - launch-id、originator、全 turn context の読取を共有。
- 新設 `orchestrator/tests/test_dev_wave_codex_manifest.py`
- 新設 `orchestrator/tests/test_check_dev_wave_codex_launches.py`

現行 `CodexWorkerSessionManifest` は session ID を spawn 後に追加する schema であり、job entry は `job_id/attempt_index/session_id` だけである（`tools/codex_worker_launch.py:175-180`、`tools/codex_worker_launch.py:519-574`）。launcher が session を観測した後に書く（`tools/codex_worker_launch.py:1127-1157`）ため、C の事前宣言には流用せず、型名も分ける。

### manifest の形

wave artifact root 配下に一つの `codex-launches.jsonl` を置く。各 declaration は最低限次を持つ。

```text
launch_id, job_id, attempt_index, launch_kind,
declared_at, cwd, sessions_root,
prompt_path, prompt_sha256, output_path,
derived_model, derived_reasoning,
authority_root, authority_digest
```

`derived_model/reasoning` は docs から生成した cache であり、段 9で再導出して一致を要求する。manifest の値を正本にはしない。

`launch_id` を prompt の末尾に機械行として埋め込み、rollout の最初の user message と exact join する。段 3 は `s03-consult-0/1` を宣言するため、多重集合へ退化しない。

### 宣言漏れの検出

段 9では次の集合等価を要求する。

1. manifest の全 declaration に、exact 1件の `.done`、prompt、output、rollout がある。
2. wave job directory の全 `.done` に、exact 1件の declaration がある。
3. 全 selected rollout の launch-id が manifest にあり、重複しない。
4. fixed job は plan 1、consult-0/1 各1、実装 waveなら review 2。author/fix は段4/6で確定した job 集合と一致。
5. 全 declaration が記録した sessions root の和集合を走査する。
6. 時間窓内・`originator=codex_exec`・prompt に wave artifact root があるのに launch-id が無い session を orphan として赤にする。

DW-O01 の通常 wrapper に従い `.done` を作る undeclared job は 2 で捕捉できる。別 worktree の fix も declaration の cwd と prompt launch-id により捕捉できる。

ただし、親が wrapper、`.done`、wave path、declaration をすべて省いて raw `codex exec` を別 `CODEX_HOME` へ投じた場合は見つけられない。この漏れを機械的にゼロにするには declaration helper 自身が exec まで担う必要があり、その時点で C は実質的に A になる。

### 取りこぼし

- 宣言済み job: launch-id と root が正しければ構造的 FN 0%。
- 段 6 別 worktree: declaration に cwd/root を持つため FN 0%。
- 段 3: lane 単位で FN 0%。
- `CODEX_HOME` 変更: declaration helper と launch が同じ環境なら root を記録できる。宣言後に inline で変えれば rollout missing で赤。
- `.done` を持つ宣言漏れ: 双方向列挙で検出。
- manifest、`.done`、wave anchor をすべて持たない raw 手動起動: 100%取りこぼす。
- 未宣言の別 sessions root: root 自体を知る手段がなく取りこぼす。

### 誤検出

launch-id exact join だけなら FP はほぼない。orphan scan は、ユーザーが wave package を同一時間窓に手動で `codex exec` へ渡した場合、それを未宣言 job と判定する。これは「dev-wave に関係する manual call も宣言必須」と裁定するなら望ましい検出、許可するなら FP となる。

同じ worktree の無関係実行は、wave artifact path と launch-id が無ければ対象外。同一 wave の再実行は新しい launch-id/attempt_index を宣言すれば区別できる。

### docs 予算、fail-closed、trust root

DW-O01 の宣言契約と S09 の reconciliation で純増 800〜1,200 bytes 程度。operations の個別残 71 bytes、aggregate 残 16 bytesの双方を超える。案 C も **[T-664] の予算捻出が前提条件**。

declaration 作成失敗、docs parse 失敗、manifest lock/重複は spawn 前に止められる。actual 値の不一致、missing/orphan は段 9で local main 取り込みを止めるが、既に行った起動と生成物利用は取り消せない。段 7にも同じ checker を置けば commit 前に止められる。

trust root は docs、declaration helper、manifest、prompt、`.done`、checker、rollout。hash chain/create-only は事故・競合を抑えるが、同一 account は manifest と rollout の両方を再作成できる。欺くには declaration と rollout を整合して書換えるか、全 anchor を省いて未知 root へ raw 起動すればよい。

## 総括

### 比較表

| 案 | 構造的な取りこぼし率 | 誤検出 | docs 純増概算 | 実装規模概算（tests込） | fail-closed 位置 | trust root |
|---|---|---|---:|---:|---|---|
| A launcher | launcher 経由 0%。raw bypass はその呼出しの100%。全体率は bypass 規律次第 | UUID 三点照合なので極小。stale artifact は誤認でなく停止 | 400〜700 bytes | 800〜1,300 LOC | 各段の起動直後。raw bypass は止められない | docs + launcher/parser + stdout/rollout + receipt/manifest |
| B 事後走査 | 選択済み session は0%。未知 root・anchor無しは100%。母集団全体は上限不明 | 同 cwd/時間窓/manual/retry で非ゼロ | 350〜550 bytes | 600〜1,000 LOC | 段7推奨。段9のみなら land だけ停止 | docs + checker + selector + mutable session logs |
| C 宣言照合 | 宣言済み+launch-id は0%。全 anchor を省いた undeclared raw call は100% | exact join は極小。orphan scan は manual call を巻き込む | 800〜1,200 bytes | 1,000〜1,600 LOC | 宣言失敗は起動前、actual mismatch は段7/9 | docs + helper + manifest + prompt/.done + rollout |

三案とも aggregate 残 16 bytesに収まらず、**[T-664] の予算捻出が前提条件**。pytest、checker、launcher は実走していないため、実装規模と byte 数は静的概算である。

### 推奨

推奨は案 A+。`run-dev-wave --launch-kind` で caller から model/effort 指定権を除き、docs の同じ権威文字列から導出して、session ID で actual rollout を即時照合する。B は母集団選択が証明できず、C は宣言漏れを完全に閉じようとすると exec wrapper が必要になって A へ収束する。A 採用条件は、段 6 の sibling worktree を扱う manifest v2、authority root と child repo root の分離、外側 `.done` wrapper の維持、raw `codex exec` を dev-wave 契約違反にすることの四点である。

### 親 brief の誤りと判断した provisional

- **P2 は一部誤り。** 最終的な OS account は同じでも、trust root と欺瞞コストは同一ではない。A は exact session ID と sealed rollout を再計算する（`tools/codex_worker_launch.py:2288-2417`）。B は cwd/時間/prompt selector、C は宣言との双方向 join に依存する。trust の差は択一材料になる。
- **P3 は誤り。** A は「起動口を一つに書き換える」だけでは構造的に閉じない。Codex subprocess に hook は未配線で raw invocation を止められず（`hooks/guard_bash.py:39-45`）、現 manifest は単一 repo root を要求するため別 worktree fix と両立しない（`tools/codex_worker_launch.py:1480-1484`、`tools/codex_worker_launch.py:1565-1581`）。A+ の追加条件が必要。
- **P6 は結論が誤り。** 段 3 が二つの model を持つ事実は正しいが、「段→期待多重集合」は retry、再実行、無関係 session が混ざると job identity を失う。`launch_kind=s03-consult-0/1` と cardinality を分離すべきである。既存 ledger も retry を cwd+prompt hash で別管理しており（`tools/codex_worker_ledger.py:627-650`）、多重集合だけでは足りない。

P1、P4、P5 は上記の条件付きで妥当と判断する。

### ユーザー裁定に載せる択一

- **R1 — 基本方式**
  1. A+ launcher 集約（推奨）
  2. B rollout 事後走査
  3. C 宣言 + 事後照合

- **R2 — docs 権威の読み方**
  1. live docs を parseし、authority digest を receipt/manifest に固定（推奨）
  2. docs から生成した wave-local authority snapshot を使い、元 docs digest と毎回照合
  3. code に値を直書きする案は二重正本になるため不採用

- **R3 — 段 3 の識別**
  1. `s03-consult-0/1` を起動前に明示（推奨）
  2. wave close 時に exact 2件の多重集合だけを照合
  3. prompt の固定 lens marker から lane を導出

- **R4 — rollout の権威 field**
  1. 全 `turn_context.payload.{model,effort}` を権威とし、nested settings は診断専用（推奨）
  2. top-level を権威とした上で nested equality も必須にする
  3. nested settings を fallback にする案は二義化するため不採用

- **R5 — A の multi-worktree manifest**
  1. manifest v2 の session entry ごとに repo identity を持たせる（推奨）
  2. worktree ごとの manifest と段7/9の receipt 集約
  3. per-job receipt のみとし、wave-wide completeness は保証しない

- **R6 — raw 手動 invocation**
  1. dev-wave 内では禁止し、発見時は wave 停止（推奨）
  2. C の事前 declaration を行った呼出しだけ許可
  3. B の事後 selector に捕捉できた場合だけ許可

- **R7 — fail-closed の時点**
  1. A の job 即時 gate + 段7の receipt 集合再照合（推奨）
  2. 段7だけで commit 前に停止
  3. 段9だけで local main 取り込み前に停止

- **R8 — docs 予算**
  1. [T-664] で先に必要 byte を捻出してから実装（推奨）
  2. 同一実装 wave 内で意味等価な縮約と新契約を同時に行う
  3. docs 契約なしで code だけ追加する案は運用 gate が発火しないため不採用