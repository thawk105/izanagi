# 段 4 裁定と plan v2 — dev-wave-acceptance-gitbatch-20260908

親の裁定。段 2 plan (`artifacts/dev-wave-acceptance-gitbatch-20260908/plan.md`) を base に、段 3 の所見 (consult-A.md / consult-B.md) を
real / refuted、採用 / 不採用、scope 内 / 外で裁定し、差分だけを plan v2 として書く。plan v2 に書かれていない事項は plan (段 2) の記述が生きる。

## 1. 所見の裁定

| ID | 判定 | 採否 | 裁定 |
|---|---|---|---|
| A-01 | real | 採用 | (P1) は refuted。blob 取得は **`ls-tree` で path→OID を取り、OID で `cat-file --batch`、各 success header の OID を期待 OID と exact 照合**する (§2)。信頼境界: `/usr/bin/git` 実行体は信頼する (現行と同じ)。body の OID 再計算はしない |
| A-02 | real | 採用 | timeout は受理集合外の運用契約。batch 形の 2 呼び出し (ls-tree / cat-file --batch) の timeout は **`GIT_TIMEOUT_SECONDS * len(queries)`** とし、旧形 (62 process × 10 秒) の総許容量と揃える。単発 rev-parse は 10 秒のまま |
| A-03 / B-11 | real | 採用 (契約を狭める) | **受理集合と拒否集合は不変。拒否の優先順位 (どの path・どの理由が先に raise されるか) は契約外**とする。閉包は定数 tuple なので production では観測不能。NUL を含む path は `contract-loader-git-error` へ正規化 (fail-closed 側、専用 test 1 本)。この 2 点を decisions fragment に書く |
| A-04 / B-01 | real | 採用 | 見積りは ls-tree + oid 形で引き直す。fast path の capture は **4 process** (rev-parse --show-toplevel / rev-parse HEAD / ls-tree / cat-file --batch) |
| A-05 | real | 採用 | 負例を §4 のとおり追加。逆順 test は digest も同じ permutation にして OID 照合で拒否されることを要求。fake 到達 marker と exact argv を assert |
| A-06 / A-08 / A-09 | refuted | — | そのまま |
| A-07 | refuted (境界表は採用) | 採用 | ls-tree 形では **mode で拒否しない** (100644 / 100755 / 120000 いずれも type blob なら committed は受理、capture/live は disk reader が非 regular を拒否)。`-z` の raw path を unquote せず bytes で照合 |
| A-10 | real | scope 外 | (P2) は refuted (repo・disk 不変の前提下でだけ冗長)。触らない。brief の記述を訂正して記録 |
| A-11 | real | scope 外 | (P3) は refuted (root identity・object 可用性は content addressing の外)。導入しない。記録 |
| A-12 / P4 | 未立証 | — | 受入 A/B で判定。実走前に改善済みと書かない |
| B-02 | real | 採用 | 受入 A/B で最遅 shard wall・対象 module W・profiled node の所要を記録。timeout 件数は log から数える |
| B-03 | real | 採用 (主張の縮小) | W は 3 shard 合算 (24,247/(3×48) = 168 秒/shard 平均、wall 286〜350 と整合)。cumtime の和 38.7 > 36.4 は入れ子重複。**09-05 20:48 からの悪化の帰属は本 wave では主張しない** (module 最終 commit は 09-03、caller に 09-04〜06 の変更なし)。insight は「現在の費用構造と改修後の実測」だけを書く |
| B-04 | real | 採用 | 残り ≈ 11 秒 (disk 読取・fsync・tmp copy) は本 wave で減らない。下限として明記 |
| B-05 | real | 採用 | `test_artifact_admission.py:2377-2397` の `missing_blob` fake も追随。`test_layer3_report.py:70-84` の `_binding_from_recorded_head` は `_blob` 互換 wrapper のままで動くので必須変更ではない (任意で batch 化可) |
| B-06 | real | 採用 | 変異は §5 の 7 件を単独証拠、他は冗長 gate と明記 |
| B-07 | refuted | — | scope 膨張なし |
| B-08 | **real** | 採用 | 新規 test node は受入の台帳被覆率検査 (`test_acceptance_schedule_order.py::test_g5_real_ledger_covers_at_least_90_percent_of_real_collection`、余裕 1 node 未満) で赤になる。実装子が §6 の手順で `acceptance_duration_ledger.json` を更新し commit に含める |
| B-09 | real | scope 外 | 5 分到達は保証しない。次 wave の裁定パッケージ候補 (P2 / P3 / 他 module の逐次 git) を worklog の次の一手へ |
| B-10 | real | 採用 | 実装子 prompt に「commit → 焦点走」を明記 (§6) |

## 2. plan v2 の差分 (blob 取得の形)

段 2 plan の「stdin と path 表現」「batch output の解析」節を次で置き換える。他の節 (`_run_git` の `input_bytes` kwarg、ordered generator、`_blob` 互換 wrapper、
4 関数の非対称維持、`_head_commit` / `_require_commit` 不変、spawn site 1 か所) はそのまま。

1. 全 `relative` を `_relative_parts` で検査する (順序は tuple 順、最初の不正で raise — 優先順位は契約外)。encoded bytes に NUL があれば
   `contract-loader-git-error` (subprocess を起動しない)。
2. **`ls-tree`**: `_run_git(root, "ls-tree", "-r", "-z", commit, "--", *[f":(literal){relative}" for relative in unique_paths], timeout_seconds=GIT_TIMEOUT_SECONDS*len(unique_paths))`。
   出力を NUL で分割し、各 entry を `<mode> SP <type> SP <oid> TAB <raw path>` に exact 分割 (path は `os.fsencode(relative)` と bytes で照合、unquote しない)。
   期待 path に対して entry 不在 → `contract-loader-git-error` (missing)。期待外の entry / 重複 entry / type が `blob` 以外 (tree / commit) → `contract-loader-git-error`。
   mode は拒否理由にしない。結果は `relative → oid` の dict。
3. **`cat-file --batch`**: stdin に tuple 順 (重複を含む元の順) の `oid\n` を並べ、`_run_git(root, "cat-file", "--batch", input_bytes=..., timeout_seconds=GIT_TIMEOUT_SECONDS*len(queries))`。
   出力は offset 解析: header `<oid> SP <type> SP <size>\n` (3 field exact、oid は 40 hex かつ**期待 oid と exact 一致**、type は `blob` exact、size は非負 decimal)、
   body は size bytes、直後に protocol LF exact。`<obj> missing\n` / 未知 status / 途中 EOF / 余剰出力 → `contract-loader-git-error`。
   最後に offset == len(stdout) を要求。
4. generator は `(relative, blob_bytes)` を tuple 順に yield し、4 関数は段 2 plan のとおり path ごとに digest / disk を検査する。
5. `_run_git` の signature は `_run_git(root, *args, input_bytes=None, timeout_seconds=GIT_TIMEOUT_SECONDS)`。既存呼び出し (rev-parse 系) は無変更。
   `test_artifact_admission.py` の 2 fake (`redirected_git_view` 2329-2338、`missing_blob` 2377-2397) は `(root, *args, **kwargs)` で透過し、
   `missing_blob` の注入条件は「args が `("ls-tree", ...)` で始まる場合に、対象 path の entry を落とした出力を返す」または「`cat-file --batch` の
   stdin に対象 oid が含まれる場合に `<oid> missing\n` を返す」のどちらかへ書き換える (test の意図 = 1 path の blob 不在で admission が
   `git command` の message で拒否されること、を保つ)。

## 3. 不変条件 (段 1 から変更なし + 追加)

- 受理集合・拒否集合は不変。拒否の優先順位は契約外 (§1 A-03)。
- 62 path の集合・順序、campaign lock schema、digest の入力 bytes、呼び出し元 3 module、spawn site 台帳値 1、env 隔離、harden 引数は不変。
- clean input で `_read_regular_file_no_follow` が capture / live の全 path で呼ばれる。process 内 cache 無し。
- `contract_loader_binding.py` は closure の一員。**実装子は編集後に焦点走を回す前に親が commit する必要がある** → 実装子は自走 harness を
  「未 commit のため drift 赤が出る」前提で、drift 由来の赤 (`contract-loader-drift`) と自分の所有 test の結果を分けて報告する。
  親が patch を wave worktree へ適用・commit してから焦点走を実測する。

## 4. 所有 test (段 2 plan の 11 本に追加・修正)

追加 (すべて `orchestrator/tests/test_t671_source_binding.py`、raw bytes は実装 helper を使わず literal で組む):
- ls-tree 応答で期待 path の entry が無い / 期待外 entry が混じる / 同じ path が 2 回出る → `contract-loader-git-error`。
- ls-tree 応答の type が `tree` / `commit` → `contract-loader-git-error`。mode 100755 / 120000 で type blob → committed は受理 (正例)。
- batch header の oid が期待 oid と異なる (応答の入れ替え) → `contract-loader-git-error`。**逆順 test は記録 digest も同じ permutation にし、
  digest 一致だけでは通らないことを OID 照合で固定する。**
- size が負 / 非数字 / field 数が 2 または 4 / status が `dangling` → `contract-loader-git-error`。空 blob (size 0) と末尾 LF 無し blob は正例。
- `*` `?` `[` `:` を含む relative path が `:(literal)` で exact に引かれる正例 (fixture repo に実 file を置く)。NUL を含む path → `contract-loader-git-error`。
- fake `_run_git` に到達 marker (呼ばれた args の記録) を持たせ、public verifier 経由で ls-tree と cat-file --batch の両方に到達した exact argv を assert。
- process-count test: `_validated_root` を固定した capture が exact 3 process (rev-parse HEAD / ls-tree / cat-file --batch)、stdin が tuple 順の oid 62 行。
- timeout: batch 形の 2 呼び出しに `GIT_TIMEOUT_SECONDS * n` が渡ることを fake で assert (恒真でない形: n=1 と n=62 で値が変わる)。

## 5. 変異事前登録 (DW-M01、runner は所有 test `test_t671_source_binding.py` に絞る — D1712)

単独証拠 (期待 node は実装後に親が probe で確定する):
1. `_run_git` の `input=input_bytes` を削除 (stdin plumbing) → process-count / batch 正例。
2. batch header の oid 照合を削除 → 入れ替え test。
3. `_blob` 互換 wrapper を逐次 `cat-file blob` へ後退 → wrapper test。
4. header の `type == blob` 検査を削除 → non-blob test。
5. 全応答消費後の exact EOF 検査を削除 → extra-output test。
6. `verify_committed_contract_loader_binding` の digest 比較を削除 → committed mismatch test (所有 test 内の direct verifier)。
7. `verify_live_contract_loader_binding` の disk 比較を削除 → live dirty test。
冗長 gate (記録するが単独証拠に数えない): ls-tree の missing entry 検査削除 (batch 側の missing でも赤)、size 不足検査削除 (record LF 検査でも赤)、
`-z` 削除 (複数 test が赤)、query 順 reverse (複数 test が赤)。等価変異 1 件 (SURVIVED 期待、例: `tuple(x)` → `(*x,)`) を harness の正例として登録。

## 6. 実装子への必須事項 (段 5 prompt に転記)

- 編集は `orchestrator/campaign/contract_loader_binding.py`、`orchestrator/tests/test_t671_source_binding.py`、
  `orchestrator/tests/test_artifact_admission.py` (2 fake のみ)、`orchestrator/tests/campaign_lock_test_support.py` (batch 化)、
  `orchestrator/tests/acceptance_duration_ledger.json` (`--add-only` 生成物) に限る。`test_layer3_report.py` は任意。
- 新規 node の台帳登録: `python3 tools/run_tests.py orchestrator/tests/test_t671_source_binding.py --junitxml=<job dir の path>` →
  `python3 tools/update_acceptance_duration_ledger.py --add-only <その junit>`。手で JSON を書かない。
- 自走: `PYTHONPATH=. python3 orchestrator/tests/test_t671_source_binding.py` と、`python3 tools/run_tests.py <file>` の焦点走
  (`test_t671_source_binding.py` / `test_artifact_admission.py` / `test_ccbench_spawn_sites.py` / `test_layer3_report.py` /
  `test_acceptance_schedule_order.py` / `test_plain_runner_coverage.py`)。未 commit の drift 赤は分けて報告。
- commit しない。docs を書かない。既存 test の期待値を変えない (fake の signature 透過と注入条件の書き換えは例外で、意図を保つ)。
