結論は **NO-GO** です。静的検査のみで、pytest は実行していません。

### 所見 1 — mask 31 の別名と whitespace により、同一 gate/ident ペアを受理できる

- 種別: 正しさ境界 / 失敗型再発
- 根拠:
  - [plan-out.md:29](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t532-name-mask-binding/plan-out.md:29) は「`g_lc+ua+rt+rl+nv`, `ident_all` の両方を許可」「configuration 固有の名称制限までは加えない」とする。
  - [trigger_gate_binding.py:115](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t532-name-mask-binding/orchestrator/campaign/trigger_gate_binding.py:115) は `text.strip()` 後の一致を受理する。
  - [s1_known_axes_freeze.py:612](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t532-name-mask-binding/orchestrator/campaign/s1_known_axes_freeze.py:612) は pairing を生文字列の `==` だけで比較し、[同:614](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t532-name-mask-binding/orchestrator/campaign/s1_known_axes_freeze.py:614) は名称の相違を要求しない。
- 発火シナリオ: `balanced.system_gate` と `balanced.ident_all` の両方を `name="ident_all"`、mask 31 とし、一方の述語だけ先頭に空白を付ける。`s1b_pairing.gate_on/gate_off` も両方 `ident_all` に合わせる。新 helper は両 record を正当とし、pairing は生文字列が空白分だけ異なるため通す。意味上同一の gate_on/gate_off が誤受理される。
- 重大度: must-fix
- 提案: `assert_s1b_pairing` で生文字列ではなく復元 mask を比較し、gate/ident の mask 同一を拒否する。mask 31 alias × 外側 whitespace の cross-record 負例を追加する。

### 所見 2 — `name` の非 `str` 値は比較演算を偽装して通過できる

- 種別: 正しさ境界
- 根拠:
  - [plan-out.md:110](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t532-name-mask-binding/plan-out.md:110) の引数は `name: object`。
  - [plan-out.md:122](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t532-name-mask-binding/plan-out.md:122) は「許可集合外なら拒否」だけで、型検査を規定していない。
  - schema 呼出しも [plan-out.md:160](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t532-name-mask-binding/plan-out.md:160) の `record.get("name")`。
  - predicate 側は [trigger_gate_binding.py:105](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t532-name-mask-binding/orchestrator/campaign/trigger_gate_binding.py:105) で exact `str` を要求している。比較偽装が実際の脅威であることは [test_s1_verify_extime_calibration.py:161](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t532-name-mask-binding/orchestrator/tests/test_s1_verify_extime_calibration.py:161) の `EqualToCanonicalPredicate` でも既に固定されている。
- 発火シナリオ: `__eq__` が `"g_rt"` に対して真を返し、`__hash__ = hash("g_rt")` とする非 `str` オブジェクトを `name` に置き、predicate を mask 4 にする。list/set いずれの membership 実装でも許可名と等価に見せられ、非文字列名が誤受理される。欠落・`None`・bytes は通常の membership なら拒否されるが、そのテストも計画にない。
- 重大度: must-fix
- 提案: membership 前に名前の型契約を固定する。`str` subclass を従来どおり許すなら、ユーザー定義 `__eq__` を使わず基底 `str` の内容で比較する。exact `str` に狭めるなら、それ自体が追加の受理集合変更なので明示裁定し、欠落・`None`・bytes・比較偽装・subclass を正負例へ入れる。

### 所見 3 — 過剰拒否の正例は実質 mask 4/8/31 しか固定していない

- 種別: 過剰拒否 / 失敗型再発
- 根拠:
  - [plan-out.md:33](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t532-name-mask-binding/plan-out.md:33) の現行6件は mask 4/8/31 のみ。
  - [plan-out.md:203](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t532-name-mask-binding/plan-out.md:203) の既存正例と [同:207](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t532-name-mask-binding/plan-out.md:207) の追加正例も同じ3 mask だけである。
  - [plan-out.md:184](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t532-name-mask-binding/plan-out.md:184) の全32件テストは predicate→mask 関数だけで、name 復元 helper を通らない。
  - 実 emitter は [s8a_trigger_sweep.py:242](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t532-name-mask-binding/orchestrator/campaign/s8a_trigger_sweep.py:242) で別 effective 集合の全部分集合を生成する。
- 発火シナリオ: `effective=("lock-conflict", "update-absent")` から得る正当な `name="g_lc+ua"`、mask 3 の predicate を渡す。helper を誤って「mask が 4/8/31 以外なら不一致」と実装しても、計画済み正例は全通過し、負例も予定どおり拒否される。その欠陥実装だけがこの正当入力を過剰拒否する。
- 重大度: must-fix
- 提案: helper または `_validate_schema` を通す mask 0〜31 の正例を追加する。mask 31 は通常名と `ident_all` の双方、外側 whitespace も含める。これは [failures.md:1894](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t532-name-mask-binding/docs/failures.md:1894) の「新設 gate には正例」を満たす最小補強である。

### 所見 4 — 完全文言一致の負例が恒偽変異の偽 kill になる

- 種別: 単一理由性 / 診断 / 失敗型再発
- 根拠:
  - [plan-out.md:127](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t532-name-mask-binding/plan-out.md:127) は workload・configuration・name・mask・期待名を含む完全診断を固定する。
  - 負例は [plan-out.md:218](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t532-name-mask-binding/plan-out.md:218) と [同:226](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t532-name-mask-binding/plan-out.md:226) で各6ケースを一つの nodeid 内で走査する。
  - production の順序は [s1_known_axes_freeze.py:722](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t532-name-mask-binding/orchestrator/campaign/s1_known_axes_freeze.py:722) の document 挿入順、[同:725](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t532-name-mask-binding/orchestrator/campaign/s1_known_axes_freeze.py:725) の `system_gate`→`ident_all` 順。
  - [failures.md:2588](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t532-name-mask-binding/docs/failures.md:2588) は、まさに「恒偽化すると最初の値で落ち、別 workload/configuration の完全一致負例も道連れ」と記録している。
- 発火シナリオ: name-mask 条件を「常に拒否」へ変異し、テスト入力では `read-heavy.ident_all` だけを改竄する。走査は先に正常な `balanced.system_gate` を拒否し、期待した read-heavy 診断とずれる。負例 node が赤になるが、狙った改竄を検査した結果ではなく偽 kill である。生成層でも ident_all 到達前の system_gate で同型が起きる。
- 重大度: must-fix
- 提案: 受理集合を検査する負例は例外型と安定 reason だけを見る。完全診断は helper 直呼びの診断専用テストへ分離し、mutation kill に数えない。`expected_names` は set ではなく固定順 tuple/list とする。

### 所見 5 — P1 は名前 emitter の単射性を検査せず、正引きの前提が恒真扱いになっている

- 種別: 正しさ境界 / 失敗型再発
- 根拠:
  - [plan-out.md:252](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t532-name-mask-binding/plan-out.md:252) は P1 を「正引きする方が短い」と支持する。
  - name は [s8a_trigger_sweep.py:121](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t532-name-mask-binding/orchestrator/campaign/s8a_trigger_sweep.py:121) の private `_ABBREV` と [同:227](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t532-name-mask-binding/orchestrator/campaign/s8a_trigger_sweep.py:227) の `subset_name` に依存する。
  - [plan-out.md:19](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t532-name-mask-binding/plan-out.md:19) が全32件で証明するのは predicate の一意性だけで、name の一意性ではない。
- 発火シナリオ: 将来 repin された emitter で `lock-conflict` と `update-absent` の略称がともに `ua` になると、mask 1 と mask 2 がともに `g_ua` になる。新 helper は同じ name を異なる2 predicate の双方で受理し、「name が指す mask」が一意でなくなる。
- 重大度: must-fix
- 提案: 全32 mask の通常名から name→mask index を構築し、重複を fail-closed にする。mask 31 の `ident_all` だけを明示 alias とする。逆文法パーサは不要で、正引き案を維持したまま塞げる。

### 所見 6 — (B)(C) は generator 編集の安全性を一般化できない

- 種別: 失敗型再発
- 根拠:
  - [brief.md:24](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t532-name-mask-binding/brief.md:24) は名称不明の「freeze 系8 test file」の緑だけを示す。
  - 凍結値は [known_axes_freeze.json:7](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t532-name-mask-binding/output/s1-freeze/known_axes_freeze.json:7) に generator hash を持ち、legacy は [s1_known_axes_freeze.py:746](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t532-name-mask-binding/orchestrator/campaign/s1_known_axes_freeze.py:746) で現物を再計算して不一致を拒否する。
  - active receipt があっても measurement は [s1_measurement_freeze.py:160](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t532-name-mask-binding/orchestrator/campaign/s1_measurement_freeze.py:160)、extime は [s1_verify_extime_calibration.py:202](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t532-name-mask-binding/orchestrator/campaign/s1_verify_extime_calibration.py:202) から legacy verifier を呼ぶ。plan 自身も [plan-out.md:248](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t532-name-mask-binding/plan-out.md:248) で legacy 成功を主張しないとしている。
  - これは [failures.md:435](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t532-name-mask-binding/docs/failures.md:435) の自己ハッシュ generator 事故と同型。
- 発火シナリオ: generator hash が一致する正当な freeze を基準に1行編集すると、T-080 adapter は通り得ても legacy `verify_document` は generator hash で拒否する。「8 file が緑」から「generator は自由に編集できる」へ一般化すると、この拒否面を見落とす。
- 重大度: should-fix
- 提案: 8ファイルの完全な一覧・command・到達経路を brief に固定し、結論を「T-080 active adapter の選択範囲では追加赤なし」に限定する。(C) の「legacy は呼ばれない」も oracle-driver active 経路だけの記述に狭める。

### 補足確認

- 検査削除については、計画された `_trigger_entries` / `_validate_schema` 直呼び負例には先行 membership・equality・pairing による偽 kill は見当たらない。問題は上記の恒偽変異時の診断依存である。
- 既存テストの期待値反転・緩和・skip・削除は plan 上確認できない。
- (D) は eager import なら実際に `s8a_trigger_sweep → pipeline → trigger_gate_binding` と循環する。ただし遅延 import なら回避可能なので、一般的な「import 不可能」という設計制約にはできない。現プランはその回避に依存しないため単独 blocker ではない。

## 総括

**NO-GO**。  
mask 31＋whitespace の誤受理、非 `str` 比較偽装、全32正例不足、偽 kill、名前単射性未検査が must-fix。  
特に所見1と4は既存の semantic pairing と F113 の既知失敗をそのまま再発させる。  
pytest は実行しておらず、緑は主張しない。