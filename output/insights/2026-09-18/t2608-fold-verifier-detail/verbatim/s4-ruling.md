# 段 4 裁定 — [T-2608] declared fold verifier 例外経路の detail 搭載 (2026-09-18)

段 2・3 は軽量版で省略 (択は P1/P2 の 2 点だけで、いずれも brief で実測して確定した)。
本文書が plan v2 の正本。親 brief は HANDOFF.md「段 1 brief」。

## 裁定

- (P1) 表示形式: **採用** = `json.dumps(exc.detail, ensure_ascii=False, sort_keys=True, separators=(",", ":"))`。
  理由: 同 file の stderr JSON 出力 (`tools/spool_fold.py` の `"transaction-error"` 行) と同規約、key 順が決定的、
  `ERROR_DETAIL_ALLOWLIST` 14 key のどの組でも表せる。`detail` が `None` なら `null`。
- (P2) 正例 test の実 trigger: **採用** = fold commit 作成後に HEAD を dangling symbolic ref にする。
  理由: `verify_fold_commit_identity` の先行検査 (cat-file / diff-tree / rev-list) は明示 SHA だけで HEAD を読まず、
  最初に HEAD を読むのは `verify_declared_fold_commit` の `_run(repo_root, "head")` (git_state.py:1066)。
  使い捨て repo で `rev-parse --verify HEAD` rc=128 を実測済み。stub を使わない (F649)。
- scope: `tools/spool_fold.py` の例外経路 1 箇所 + `orchestrator/tests/test_spool_fold.py` の test 1 本。
  `git_state.py` / `schema.py` / `redaction.py` は触らない。拒否の判定・受理集合は変えない。
- scope 外 (記録のみ): 22 箇所が (label, kind) で 16 類に縮約される残余、`return_code` の allowlist 落ち、
  非 DevWavesError 例外の表示、gate / 検査 / 台帳 / 一般化の追加。

## plan v2 (file:line 粒度)

### `tools/spool_fold.py`

1. `verify_fold_commit_identity` 内の lazy import (3419-3425 行) に `DevWavesError` を加える。
   `from tools.dev_waves.git_state import (FOLD_AUTHOR_IDENTITY, FOLD_COMMIT_MESSAGE, verify_declared_fold_commit)` と同じ
   try/except の中で `from tools.dev_waves.schema import DevWavesError` を行う (ImportError / AttributeError は既存の
   TransactionError 経路に乗せる)。
2. 3473-3474 行の `except BaseException as exc:` の本文を次にする (受理・拒否の含意は 2 文):
   - 拒否の含意: 例外が出たら従来どおり `TransactionError` を投げる (変わらない)。
   - 表示の含意: `exc` が `DevWavesError` なら message を
     `f"declared fold verifier が失敗: {exc.code.value} {json.dumps(exc.detail, ensure_ascii=False, sort_keys=True, separators=(',', ':'))}"`
     にし、それ以外は従来の `f"declared fold verifier が失敗: {exc}"` のまま。`from exc` は維持。
   - `json` は同 file で import 済み (3707 行で使用)。追加 import 不要。
3. 3475-3476 行 (`if not declared.ok: raise TransactionError(f"declared fold verifier が拒否: {declared.detail}")`) は 1 byte も変えない。

### `orchestrator/tests/test_spool_fold.py`

4. 既存 helper (`_repo`, `_fragment`, `_worklog_body`, `_plan_for_commit`, `_commit_applied_fold`, `_assert_declared_fold`,
   `_run_git`, `_transaction_raises`) だけで正例 test を 1 本足す。名前は
   `test_commit_identity_gate_exception_path_reports_declared_detail`。置き場は
   `test_commit_identity_gate_rejects_gc_status_only` の直後。
   手順: repo 作成 → fragment → plan → `_commit_applied_fold` で fold commit → `_assert_declared_fold(repo, plan, fold_commit)`
   (前提: 健全な状態では verifier が通る) → `_run_git(repo, "symbolic-ref", "HEAD", "refs/heads/t2608-does-not-exist")`
   → `_transaction_raises("declared fold verifier が失敗: invalid-run ", spool_fold.verify_fold_commit_identity, repo, plan, fold_commit=fold_commit)`
   → 返った exc の `str(exc)` に `'{"kind":"head","label":"git"}'` が含まれること、`exc.__cause__` が `DevWavesError` で
   `exc.__cause__.detail == {"kind": "head", "label": "git"}` であることを assert。
   期待値へ揮発 payload (SHA・tree hash) を焼き込まない。`_run_git` が `symbolic-ref` を通せない場合は
   `subprocess.run(["git", "-C", str(repo), "symbolic-ref", ...], check=True)` を直接使う (既存 test に同型あり)。
5. 実走: `python3 -m pytest orchestrator/tests/test_spool_fold.py -q -p no:cacheprovider` (file 単独) を子が実走し nodeid と件数を報告。

## 変異事前登録 (DW-M01)

- M0 (負例、SURVIVED 期待): 項 2 の `json.dumps(...)` の keyword 引数の並びを `sort_keys=True, ensure_ascii=False` の順に
  入れ替えるだけ (意味等価)。`test_spool_fold.py` 全緑が期待。
- M1 (正例、KILLED 期待): 項 2 を `raise TransactionError(f"declared fold verifier が失敗: {exc}") from exc` (現行 main と同じ) に戻す。
  赤は新 test 1 本だけ、理由は 1 つ (message に `invalid-run {"kind":"head","label":"git"}` が無い)。
- 単一理由性: 新 test は `verify_fold_commit_identity` を直接呼び message 文字列だけを assert する。同じ入力を前後・内側で
  拒否する層は無い (dangling HEAD は先行検査に掛からず、declared verifier の最初の git 呼出しで落ちる)。実装後に子の
  実走 log で「新 test 以外が緑」を確認する。

## 段 4 追記 — 変異登録の分類を DW-M03 / DW-M08 に揃える (2026-09-18 15:12 JST、author 起動後・変異走行前・結果を見る前)

- DW-M03「診断文字列だけの赤を kill にしない」、DW-M08「受理集合を変えず構造化シグナルだけを pin する変異は kill でなく
  diagnostic sensitivity pin へ別枠記録する」に従い、M1 (message を `{exc}` に戻す) は **KILLED ではなく diagnostic sensitivity pin**
  として別枠に記録する (期待: 新 test 1 本だけ赤、理由 = message に detail が無い)。
- 受理集合を変える変異として **M2 (正例、KILLED 期待)** を追加登録する: 例外経路を fail-open にする
  (`except BaseException as exc:` の本文を `return` に置換 = TransactionError を投げずに受理へ倒す)。期待 node = 新 test 1 本
  (`_transaction_raises` が「TransactionError を返さなかった」で AssertionError)。これが不変条件 (a)「例外経路は変わらず
  TransactionError を投げる」を新 test が pin していることの証拠になる。
- M0 (負例、SURVIVED 期待) は変更なし (等価変異、category は `positive`)。
- 走らせ方 (DW-M07 は起動直前に再読): 統合 commit 後、login で各変異を注入 → 自走 harness
  (`PYTHONPATH=. python3 orchestrator/tests/test_spool_fold.py`、`FAIL <name>:` 行) で赤 node を採る → `git checkout --` で復元し
  HEAD blob と照合 (DW-O19) → 観測 node を期待に入れた final spec 1 本 (M0 SURVIVED / M2 KILLED、M1 は期待 node 付きの
  diagnostic pin として同 spec に `negative` で載せ、`expected_status` は harness 契約上 KILLED と書くが記録では別枠) を
  container worktree (tested commit checkout、submodule 初期化済み) へ `--runner-mode dispatch --force-dispatch` で 1 走。
  `timeout_seconds` ≥ 4500。spec / out は job dir (checkout 外)。

## 段 6 レビュー B (過剰・削除レンズ) の裁定 (15:22 JST)

- GO、must-fix 0。採用 (docs 訂正のみ、実装差分なし):
  - **real / 採用**: 「16 類」の集計は定義が混ざっていた。正: 22 発火元 = (label, kind) の code 上の entry 18 (固定値ペア 16 種 +
    動的値 2 発火元: git_state.py:209 `kind=operation`、:227 `label=<label>`)。detail でも同値の残余 = `git/timeout` ×3
    (57・64・205)、`fold-diff/record` ×2 (783・796)、`fold-parents/record` ×2 (843・854)。HANDOFF / worklog はこの表現にする。
  - **real / 採用**: 単一理由性の説明を訂正 — 新 test は message 文字列 + `__cause__` 型 + `__cause__.detail` を assert する。
    M1 (message を `{exc}` に戻す) は cause を維持するので赤理由は「message に detail が無い」の 1 つ。M2 (`return`) は
    `_transaction_raises` が先に AssertionError を投げるので赤理由は「TransactionError を返さなかった」の 1 つ。
- 不採用 (記録): `__cause__` assert 2 本 + import の削除 (実 callee の sanitize 済み detail を名指しする証拠 = F649 の趣旨。
  受理集合に影響なし、nit)。M2 の省略 (拒否継続の補助証拠として 1 走分の費用で残す。M1 = 本題の証拠 (diagnostic pin、kill に
  数えない)、M2 = 拒否継続の補助証拠 (KILLED) と区別して記録)。JSON → repr の簡略化 (reviewer 自身が変更を推奨せず)。
  レビュー 2 本目の削減 (DW-S06-A は「実装 wave は必ず 2 本並列」の U 節で、親が本文で確認済み)。

## 段 6 レビュー A (正しさ境界・整合・実効性レンズ) の裁定 (15:25 JST)

- GO、must-fix 0。実装への所見なし。親資料への should 1 (「16 類」= B と同じ、独立集計 22 / 定数ペア 16 / 動的 2 / 18 式 /
  重複 3・2・2 が親の数え直しと一致) と nit 1 (単一理由性の説明 = B と同じ) → 両方 real / 採用 (docs 訂正、上と同じ)。
- 検証済みとして採る事実: (1) `.schema` 相対 import と絶対 import は同一 module、subclass も isinstance に含む、非 DevWavesError
  の分岐は従来どおり。(2) 現行 producer の detail は固定の診断語 / allowlist operation / 固定 label で、`return_code` は
  allowlist 外、stderr JSON は外側 json.dumps がエスケープ。sanitizer の一般保証は主張しない (scope 外)。(3) 新 test は
  先行検査を通過後、verifier の最初の git 操作 `head` で落ちる。(4) M2 は `_assert_declared_fold` 系 test を赤にしない
  (内側 verifier 直呼びで wrapper を通らない)。(5) `git grep -F 'declared fold verifier が失敗'` は実装 2 行 + 新 test 1 行のみ、
  land は message を `LandResult.reason` に格納するだけで parse しない (rc=26/27/30 は既存経路)、登録簿の対象外。
- 補足 (記録): 「22 箇所」は git_state.py 全体の数で、fold wrapper から全部に到達するわけではない (起票文も file 全体の数)。
- 結論: 実装 fix ゼロ → fix 子・焦点再レビューは起動しない。次 = 変異 (login probe → dispatch 1 走) と受入。

## 段 5 実装子への指示の要点

- 編集 file は上記 2 本だけ。docs 編集・commit・git add / stash / worktree は禁止。
- 現行の受理・拒否挙動を報告に明記: 例外経路は TransactionError (変わらない)、構造的拒否も TransactionError (変わらない)、
  変わるのは例外経路の message 本文だけ。
- 所有外 caller / consumer の静的列挙: `verify_fold_commit_identity` の呼び手 (`tools/spool_fold.py` 3495・3520、
  `tools/dev_wave_land.py` 5343)、`orchestrator/tests/test_dev_wave_land.py` の同名 stub (6271)。message 文字列を pin する
  既存 test の有無を grep で確認して報告。
