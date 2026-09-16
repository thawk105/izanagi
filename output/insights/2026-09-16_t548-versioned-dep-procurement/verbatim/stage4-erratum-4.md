# 段 4 裁定 追補 4 (erratum-4) — 本数を固定した mocc 契約テストを単位 B へ足す

**正本の関係:** 追補 1〜3 に続く。衝突したら**番号の大きい追補が優先**する。

**発生:** 単位 B は job body 15 本の付け替えを完了したが、**また本数 pin のテストに当たって
停止した。B の判断は正しい** (所有外を触らず報告した)。

赤の実体 — `orchestrator/tests/test_mocc_trace_job_contract.py:233`:

- `test_mocc_trace_policy_parser_emits_18_values_and_rejects_duplicates` が
  `mocc_trace_v1_policy.json` の値を **18 個**と固定し、`values[12]` に compiler body sha、
  `values[17]` に policy 自身の sha256 を要求する。
- 同 test は `tools/pegasus/mocc_trace_pilot.sh` の
  `if [[ ${#policy_values[@]} -ne 18 ]]; then` という**字面**も要求する。
- 旧 locator 2 key を除いたので実装は **16 値**になった。

**追補 3 と同型の取りこぼしである。** 本数 pin は path 検索にも key 検索にも出ず、
**test 関数名の中の数字**としてしか現れない。

## 追補の決定

### (1) `orchestrator/tests/test_mocc_trace_job_contract.py` を単位 B の所有に足す

### (2) 直し方 — 実測した値に合わせる。検出力を落とさない

- 値の本数 **18 → 16**。`mocc_trace_pilot.sh` の `-ne 18` の字面も同じ値に揃える
  (同 shell は既に B の所有)。
- `values[12]` / `values[17]` の添字は、**parser を実際に走らせて出力の並びを読み、
  compiler body sha と policy sha256 が実際に何番目に出るかを測って**決める。
  **算術で 2 引いて済ませない。** 並びが変わっていないことを確かめたうえで添字を入れる。
- **assert を 1 つも消さない。** compiler body sha の中身の検査 (`{"gcc": ..., "g++": ...}`)、
  policy 自身の sha256 の検査、duplicate key 拒否の検査 (`duplicate JSON key: expected_cpu_model`)
  はすべて残す。
- **`_pilot_policy_parser_source()` が抜き出す parser の同一性検査を緩めない。**

### (3) test 関数の改名を明示的に許可する

関数名に `18` が入っているので **`..._emits_16_values_and_rejects_duplicates` へ改名してよい**。
これは削除ではなく改名であり、追補の本文が明示的に許可する。

- **改名は 1 関数だけ。** 他の関数名を変えない。
- 改名に伴い `orchestrator/tests/acceptance_duration_ledger.json` の旧 nodeid が
  stale になるが、同台帳は add-only なので**触らない** (`tools/update_acceptance_duration_ledger.py`
  が受入走行の junit から更新する)。

### (4) 残存の実測 (親が確認済み)

現行の単位 B worktree で `gflags_source_path` / `glog_source_path` / `verify-deps` を全走査した結果、
残っているのは次の 2 種だけである。**これ以外の未付け替え consumer は無い。**

- `orchestrator/tests/acceptance_duration_ledger.json` の削除済み nodeid 5 件
  (add-only 台帳なので放置する)。
- `orchestrator/tests/test_pegasus_thirdparty_fetch.py:909`
  `test_removed_verify_deps_command_is_rejected` — 廃止を検査する**意図的な負例**。

### (5) 段 8 候補 (追補 3 §3 に追加)

**本数 pin は test 関数名の中の数字としてしか現れない。**
段 1 の pin 閉包に「編集する data/設定 file の**要素数**を固定する test」を引く手順が要る。
本 wave では追補 3 (行番号 pin) と追補 4 (本数 pin) の 2 回、実装後の実走で初めて出た。
`git grep -nE "def test_.*_[0-9]+_(values|entries|members|sites)" -- orchestrator/tests/` の形が候補。
