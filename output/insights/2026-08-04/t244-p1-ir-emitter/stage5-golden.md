指定の [reflux_ir_expected_goldens.py](/work/1/SFC/tanab/izanagi/.claude/worktrees/wave-t244-p1-ir-emitter/orchestrator/tests/reflux_ir_expected_goldens.py) だけを新規作成しました。commit・docs 編集は行っていません。

### 独立性

読んではならない以下の 6 対象は、一切読んでいません。

- `orchestrator/campaign/s8a_trigger_sweep.py`
- `output/campaigns/` 配下
- `output/s1-freeze/` 配下
- `orchestrator/tests/s1_expected_goldens.py`
- `orchestrator/campaign/p3_s4_loop_trigger_gating.py`
- `orchestrator/campaign/reflux_ir.py`

旧実装・campaign 記録・freeze からの転記や、生成スクリプトによる作成も行っていません。

### C++ 識別子の出典

骨格 patch から次を読み取りました。

- enum 型と対象 member: [patch:56](/work/1/SFC/tanab/izanagi/.claude/worktrees/wave-t244-p1-ir-emitter/patches/silo-backoff-trigger-gating-variant.patch:56)（56–64 行）
  - `IzanagiAbortReason`
  - `kUnset`
  - `kLockConflict`
  - `kUpdateAbsent`
  - `kReadValiTid`
  - `kReadValiLocked`
  - `kNodeVali`
- thread-local 要因変数: [patch:68](/work/1/SFC/tanab/izanagi/.claude/worktrees/wave-t244-p1-ir-emitter/patches/silo-backoff-trigger-gating-variant.patch:68)（68–69 行）
  - `izanagi_abort_reason_`
- 代入先変数: [patch:84](/work/1/SFC/tanab/izanagi/.claude/worktrees/wave-t244-p1-ir-emitter/patches/silo-backoff-trigger-gating-variant.patch:84)
  - `izanagi_gate_pass`

### 32 行の導出方法

1. `GATEABLE_REASONS` の定義順を bit 0～4 に固定。
2. mask 0～31 を昇順に列挙。
3. 各 bit を LSB-first で文字位置 0～4 に写し、5 文字の wire を手で記述。
4. 全 predicate の先頭を `kUnset` 項に固定。
5. 立っている bit の項だけを bit 0→4 の順で追加し、` || ` で連結して末尾へ `;` を付与。
6. 全ケースを関数・内包表記・書式化・変数参照のない literal tuple として直接記述。

### 検査結果

- `python3 -m py_compile orchestrator/tests/reflux_ir_expected_goldens.py`
  - exit 0
  - bytecode は一時ディレクトリへ出し、repo 内には残していません。
- `git diff --check`
  - exit 0
- 新規未追跡ファイル用の `git diff --no-index --check /dev/null ...`
  - 空白エラーなし
- 一時 AST 確認コード
  - `ast.literal_eval` 成功
  - 32 件
  - mask は 0～31 を過不足なく被覆
  - wire は 32 個すべて一意
  - predicate は 32 個すべて一意
  - wire の LSB-first 対応と predicate の項順も全件一致
- 最大物理行長
  - 401 文字。predicate は折り返していません。
- `git status --short`
  - `?? orchestrator/tests/reflux_ir_expected_goldens.py` のみ
- pytest は実行しておらず、緑とは報告しません。

### 所有外への波及可能性

- caller: 現時点では test 専用データ台帳であり、production caller はありません。
- shared fixture: fixture の追加・変更や `conftest.py` への波及はありません。
- consumer test: 後続所有者が作成する `orchestrator/tests/test_reflux_ir.py` が、32 点の wire・predicate 比較と要因順 drift 検査の consumer になる可能性があります。
- production: `orchestrator/campaign/**` からの import を明示的に禁止しているため、production 実行経路や campaign の受理集合には影響しません。

## 総括

規範仕様と骨格 patch だけから、独立した 32 点の literal golden 台帳を作成しました。変更は指定された新規ファイル 1 個だけで、構文・literal 性・全 mask 被覆・一意性・空白を確認済みです。