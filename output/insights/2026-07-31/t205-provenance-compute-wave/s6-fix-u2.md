# 段 6 fix (U2 所有分) 完了報告 — Claude opus

**pytest は 1 度も走らせていない** (ログインノード `pegasus02`)。静的検査と純関数 probe のみ。

## 変更

- **`hooks/guard_bash.py`** (F1 = MF-1): `_provenance_entry` の戻り値を `(path, sanctioned)` に縮小し、
  `-m <非 provenance module>` の位置引数を**違反として返す枝を削除**。
  `_provenance_script_borrow(head, args) -> bool` を新設 — `-m <他 module>` の module_args 中に checker basename の
  非 option 引数が**どの位置にあっても** True (順序依存にすると sanctioned path を先頭に置くだけで迂回できる)。
  `_heavy_segment_violation` の判定順を「直接実行形の違反 → 借用があれば `_is_sanctioned` の早期 allow をしない →
  既存判定へ落とす」に変更。コメント 2 箇所を実装に合わせて訂正。
- **`test_hooks.py`**: 新規 `test_bash_login_allows_static_module_reads_of_provenance_script` (正例 5 形。
  **この網の穴が根因だったのでここが本体**) と `test_provenance_script_borrow_does_not_lend_sanctioned_status`
  (borrow 述語の単体 5 vector + 順序非依存の実効性検査)。F4: `_run()` を `pytest.main` 委譲へ
  (`test_check_ai_provenance.py` と同型)。
- **`test_pegasus_dispatch_compute.py`** (F2/F3): `test_dev_wave_check_maps_dispatch_infra_rc_off_provenance_reason`
  へ改名し、fake を `python3 -c` から `tmp_path/tools/check_fake_{infra,violation}.py` の実ファイルへ。
  `is not ReasonCode.PROVENANCE_FAILED` と「INFRA 名の member が存在しない」assert を追加し、
  trust root 検査が恒真でない事実 (受入全走 `874774.nqsv` の実測) を docstring に残した。

## 実測 (`GB.decide(cmd, site="PEGASUS_LOGIN")`)

| command | 段 5 (レビュー A) | **本 fix 後** |
|---|---|---|
| `python3 -m py_compile tools/check_ai_provenance.py` | DENY | **ALLOW** |
| `python3 -m json.tool tools/check_ai_provenance.py` | DENY | **ALLOW** |
| `python3 -m py_compile hooks/guard_bash.py tools/check_ai_provenance.py` | ALLOW | ALLOW (順序非依存) |
| `python3 -m coverage run tools/check_ai_provenance.py --range A..B` | ALLOW | ALLOW (**変わらず**) |
| `python3 /tmp/copy/check_ai_provenance.py --range A..B` | DENY | DENY |
| `python3 check_ai_provenance.py --range A..B` (cwd 相対) | DENY | DENY |
| `python3 -mpytest tools/check_ai_provenance.py` | DENY | DENY |

SUSPECT でも負例は全て DENY、COMPUTE では全形 ALLOW。既存正例 (`--message-file` 4 形、reader 6 形、sanctioned 4 形) も維持。

**変異帰属の実測** (repo 外 tmp に変異コピーを作り評価):
- **M13** (provenance 分岐を `_is_sanctioned` の後ろへ移動): 負例 7 形のうち `dash-m-pytest` **だけ**が ALLOW へ反転。
  新規正例 5 形は変異下でも ALLOW のまま = 帰属を汚さない。
- **F1 逆変異** (借用を再び違反に戻す): `-m py_compile <checker>` と `-m json.tool <checker>` が DENY へ =
  新規正例が退行を KILL する。

`CheckSpec` probe: 旧形 `(sys.executable, "-c", ...)` は `ValueError: fixed check script is outside the trust root` を
**再現**、新形は受理。`run_check_specs` 実走で rc=16 → `CHECK_FAILED` / rc=1 → `PROVENANCE_FAILED` を確認。

## 所有外への波及

`_provenance_entry` の arity 変更の呼出は 1 箇所のみ。削除した message literal の消費者は repo 内ゼロ。
旧テスト名の参照は insight と過去 job ログのみ (歴史記録)。`test_plain_runner_coverage.py` は緑のまま。
**親所有 docs への影響は訂正方向のみ** — `AGENTS.md` の「py_compile まで許される」、runbook と D105 の
「hook が閉じるのは綴り差だけ」は、本 fix で**初めて真になる**。

## 期待して赤くなる finding

**0 件。**

## 報告事項と親裁定

1. **`python3 -m coverage run <checker> --range …` は ALLOW のまま。** 借用抑止は「sanctioned を貸さない」だけで、
   coverage には既存の重い判定規則が無い。塞ぐには module の allowlist/denylist が要り、
   不採用にしたレビュー B 案と同型の列挙ドリフトを持ち込む。
   → **親裁定: 受容。** 段 5 以前から ALLOW であり新規欠陥ではない。repo 内 checker を起動する以上
   **第一層の site gate が効く**ので重い監査は起きない。runbook §7 / D105 の射程内。
2. `python3 -mpytest <checker> --message-file …` が許可 → **拒否**へ (受理集合の縮小)。
   → **親裁定: 受容。** 実用綴りではなく fail-closed 方向。
3. `_script_target` の第 1 非 option 引数昇格 (同じ穴が `python3 -mpytest tools/run_tests.py` に残る) は
   段 5 で親が scope 外と裁定済みのため未着手。→ **親裁定: 変更なし。worklog へ起票する。**
4. M13 実施時、変異下では新規 `test_provenance_script_borrow_does_not_lend_sanctioned_status` の末尾 assert も
   同時に赤くなる (原因は同一)。→ **親裁定: DW-M07 の anchor 再検証で期待 node 欄に追記する** (レビュー B の N3 と同型)。
