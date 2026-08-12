## 総括

**NO-GO。**

blocker は C1〜C3 の 3 件。特に marker gate は `_discover()`・通常 `apply_fold()`・CLI resume の正規経路には結線されているが、malformed triple と、fragment と `after_bytes` が食い違う plan/state で迂回できる。テストは指示どおり実走していない。

## 所見

### C1 — severity: blocker — projection gate の trust root を caller が偽造できる

- **根拠:** `D291ApprovalPayload` を公開 export している [orchestrator/publication/__init__.py:5](</work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t793-pubcore-impl/orchestrator/publication/__init__.py:5>)。型は通常の public dataclass [orchestrator/publication/approval_d291.py:170](</work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t793-pubcore-impl/orchestrator/publication/approval_d291.py:170>)。`require_d291_projection_exact()` は型だけを確認し、caller が渡した `approved_values` と `value_projection` を権威として使う [orchestrator/publication/approval_d291.py:490](</work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t793-pubcore-impl/orchestrator/publication/approval_d291.py:490>)。
- **落ちる具体入力:** caller が `approved_values=(("p01.candidate_cap", Decimal("9")),)`、`value_projection=(("p01.candidate_cap", "p01.candidate_cap"),)` の偽 `D291ApprovalPayload` を構築し、`{"p01.candidate_cap": 9}` を渡す。`F_p` を一度も読まず成功する。
- **成果物影響:** 将来の追補 P の受理集合が D291 の固定 9 値から caller 選択値へ広がり、材料レポートが未承認の p01/p02 値を承認済みとして参照できる。

### C2 — severity: blocker — malformed/duplicate triple を握り潰すと marker gate が空集合になる

- **根拠:** duplicate field は `invalid=True` になる [orchestrator/publication/approval_guard.py:92](</work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t793-pubcore-impl/orchestrator/publication/approval_guard.py:92>)。`BlobRefError` も `pass` で捨てる [orchestrator/publication/approval_guard.py:65](</work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t793-pubcore-impl/orchestrator/publication/approval_guard.py:65>)。結果として ref が無ければ marker 走査は一度も発火しない [orchestrator/publication/approval_guard.py:116](</work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t793-pubcore-impl/orchestrator/publication/approval_guard.py:116>)。
- **落ちる具体入力:** marker 入り blob を正しく pin する `approved_blobs:` role に、同じ `sha256` 行をもう一度追加する。完全な正規 triple が先にあっても role 全体が黙って捨てられ、`require_resolved_approval_markers()` は成功する。
- **成果物影響:** canonical decisions の受理集合に marker 入り blob を指す曖昧な承認宣言が入り、材料レポートの承認参照が永続的に解決不能または consumer 依存になる。

### C3 — severity: blocker — direct plan / CLI resume は実際に書く `after_bytes` を常には検査しない

- **根拠:** `_plan_decision_payloads()` は、hash が合う decision fragment が一つでもあれば、その fragment だけを返す [tools/spool_fold.py:1072](</work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t793-pubcore-impl/tools/spool_fold.py:1072>)。`docs/decisions.md` の `after_bytes` を調べるのは fragment が欠落した場合だけ [tools/spool_fold.py:1095](</work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t793-pubcore-impl/tools/spool_fold.py:1095>)。その検査後に `after_bytes` を書く [tools/spool_fold.py:2354](</work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t793-pubcore-impl/tools/spool_fold.py:2354>)。state loader も after hash は確認するが fragment からの再導出はしない [tools/spool_fold.py:2254](</work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t793-pubcore-impl/tools/spool_fold.py:2254>)。
- **落ちる具体入力:** marker の無い既存 decision fragment の正しい receipt と、別途 marker 入り blob を承認する内容を追加した `docs/decisions.md` の `TargetChange.after_bytes` を組み合わせた `FoldPlan`。direct `apply_fold()` でも、その plan を state JSON にした CLI resume でも、fragment だけが検査され marker 入り `after_bytes` が書かれる。
- **成果物影響:** decisions の実受理集合が marker gate の検査集合より広くなり、材料レポートの承認参照へ unresolved blob を canonical に混入できる。

### C4 — severity: must-fix — report renderer が caller 作成の「承認状態」を D291 authority として出力する

- **根拠:** `ApprovalReport` と `D291RoleResolution` は通常の構築可能な dataclass [orchestrator/publication/report.py:34](</work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t793-pubcore-impl/orchestrator/publication/report.py:34>)、[orchestrator/publication/approval_d291.py:186](</work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t793-pubcore-impl/orchestrator/publication/approval_d291.py:186>)。renderer は role 名だけを検査し、caller の path/commit/sha256/status をコピーしつつ `approval_authority = canonical_decision_D291` を付ける [orchestrator/publication/report.py:199](</work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t793-pubcore-impl/orchestrator/publication/report.py:199>)。
- **落ちる具体入力:** exact 2 role について、任意の `BlobRef` と `approval_status="approved_by_canonical_decision"` を持つ偽 `ApprovalReport` を `approval_report_to_dict()` に渡す。
- **成果物影響:** 投入禁止自体は残るが、材料レポートの承認 path・commit・sha256 が未承認 blob へ差し替わる。

### C5 — severity: must-fix — supersession scan に明示的失効の false negative がある

- **根拠:** 日本語 pattern は実質 `D291` の直後に `を` が来る三表現だけ [orchestrator/publication/report.py:44](</work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t793-pubcore-impl/orchestrator/publication/report.py:44>)。非一致なら `none_found` となり [orchestrator/publication/report.py:106](</work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t793-pubcore-impl/orchestrator/publication/report.py:106>)、renderer は現在承認を断言する [orchestrator/publication/report.py:207](</work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t793-pubcore-impl/orchestrator/publication/report.py:207>)。
- **落ちる具体入力:** 後続 D999 の本文を `D291 の publication_core role の承認を失効させる。` とする。明示的失効だが pattern に一致しない。
- **成果物影響:** 材料レポートの `approval_status` が `not_asserted_after_supersession` にならず、失効済み blob を現在も承認済みと表示する。

### C6 — severity: must-fix — `F_p` の正例 fixture が SUT の定数を oracle にしている

- **根拠:** fixture は実装から import した `D291_FOLD_COMMIT` をそのまま `git show` に使う [orchestrator/tests/test_t793_approval_d291.py:26](</work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t793-pubcore-impl/orchestrator/tests/test_t793_approval_d291.py:26>)。実装の固定値は [orchestrator/publication/approval_d291.py:21](</work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t793-pubcore-impl/orchestrator/publication/approval_d291.py:21>)。
- **落ちる具体入力:** `D291_FOLD_COMMIT` を実在する子 commit `e7d918ed52a1a54aa153f4eb301fb013a114c953` へ変更する。この commit の `docs/decisions.md` bytes は `F_p` と同じで D291 は EOF 終端なので、現在の正例は追随して通る。
- **成果物影響:** 材料レポートの `trust_root_commit` が本来の fold commit 以外へ動き、将来の追補 P が参照すべき `core_ref.commit` と食い違う。

### C7 — severity: must-fix — D292 forbidden 負例の literal が parser に到達しない

- **根拠:** fixture は `ljust(17)` に加えて `" = "` を足す [orchestrator/tests/test_t793_approval_d291.py:227](</work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t793-pubcore-impl/orchestrator/tests/test_t793_approval_d291.py:227>)。canonical bytes は [docs/decisions.md:13570](</work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t793-pubcore-impl/docs/decisions.md:13570>)。
- **落ちる具体入力:** canonical `F_p` bytes。そのまま `_replace_once()` へ渡すと置換対象 0 件の `AssertionError` になり、禁止値を `allowed` にした parser 負例を実行できない。
- **成果物影響:** `pilot_submission` / `main_submission` の専用回帰証拠が成立せず、材料レポートの forbidden 値を守る独立検出層が欠ける。

### C8 — severity: nit — 既存赤 4 件の原因説明は方向は正しいが、修正案としては不十分

- **根拠:** real fixture は `tools/check_docs.py` だけを複製し、`tools/dev_waves/` を複製しない [orchestrator/tests/test_spool_fold.py:2943](</work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t793-pubcore-impl/orchestrator/tests/test_spool_fold.py:2943>)。`spool_fold` は複製先の同 file を動的実行する [tools/spool_fold.py:1870](</work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t793-pubcore-impl/tools/spool_fold.py:1870>)。その file は top-level `dev_waves` を import する [tools/check_docs.py:27](</work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t793-pubcore-impl/tools/check_docs.py:27>)。
- **落ちる具体入力:** `_copy_real_canonical_family()` が作る fixture で `plan_fold()` を呼ぶ指定 4 node。`_load_rotate_limit()` が `ModuleNotFoundError: dev_waves` を fail-closed に包む。
- **独立判定:** 「helper が dependency closure を複製していない」は正しい。ただし `spec_from_file_location()` は複製先 `tools/` を `sys.path` に追加しないため、directory をコピーするだけでは十分でない。import 経路も閉じるか、rotate limit の読取を `check_docs` 全 module import から分離する必要がある。
- **成果物影響:** T-793 の成果物値・受理集合は直接変わらない。既存 canonical-family 回帰の受入証拠だけが取得不能になるため nit とした。

## 発火を確認できた経路

- P4 は恒真拒否ではない。正例は public `read_publication_ledger()` を呼び [orchestrator/tests/test_t793_publication_ledger.py:78](</work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t793-pubcore-impl/orchestrator/tests/test_t793_publication_ledger.py:78>)、実装は regular-file 読取、JSONL parse、Git 履歴検査を経由する [orchestrator/publication/ledger.py:366](</work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t793-pubcore-impl/orchestrator/publication/ledger.py:366>)。
- D291 節終端は次の可視 `## ` または EOF であり、`D292` literal 依存ではない [orchestrator/publication/approval_d291.py:227](</work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t793-pubcore-impl/orchestrator/publication/approval_d291.py:227>)。
- `document_relations` は note を含む正規化後の節全体 hash を照合する [orchestrator/publication/approval_d291.py:293](</work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t793-pubcore-impl/orchestrator/publication/approval_d291.py:293>)。
- 正規 `_discover()` 経路は issue 化され、`plan_fold()` が拒否する [tools/spool_fold.py:1038](</work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t793-pubcore-impl/tools/spool_fold.py:1038>)、[tools/spool_fold.py:2007](</work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t793-pubcore-impl/tools/spool_fold.py:2007>)。
- 正規 direct apply と resume は canonical 書込み前に再検査する [tools/spool_fold.py:2341](</work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t793-pubcore-impl/tools/spool_fold.py:2341>)。CLI resume も stored plan を `apply_fold()` へ渡す [tools/spool_fold.py:2564](</work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t793-pubcore-impl/tools/spool_fold.py:2564>)。
- land は wave 側で `plan_fold()`、main 側で `apply_fold()` を呼ぶ [tools/dev_wave_land.py:2266](</work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t793-pubcore-impl/tools/dev_wave_land.py:2266>)、[tools/dev_wave_land.py:1839](</work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t793-pubcore-impl/tools/dev_wave_land.py:1839>)。
- D292 が禁じる success boolean・ready/admitted/can-submit API と `status: ready` は新 package に無い。`report` は常に両 submission を forbidden とする [orchestrator/publication/report.py:224](</work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t793-pubcore-impl/orchestrator/publication/report.py:224>)。

レビュー時点では pending spool fragment は未生成であるため、将来の段 7 fragment の byte 実体までは確認不能。ただし marker literal を含む実装・テスト・draft 自体は fold 入力ではなく、marker を含まない通常 fragment は `approved_blobs:` が無ければ新処理を即 return する [tools/spool_fold.py:1054](</work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t793-pubcore-impl/tools/spool_fold.py:1054>)。段 7 後、land 前に生成済み fragment bytes を再確認すべきである。

scope 外と裁定済みの source 本走 gate、予約 writer、追補 P 凍結、公表 validator/consumer は、本レビューでは実装要求へ戻さない。既存 R1〜R5 の裁定パッケージ候補のままとする。