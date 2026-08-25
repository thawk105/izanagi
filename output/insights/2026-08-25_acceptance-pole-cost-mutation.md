# 受入直列 pole の費用削減 — 変異台帳と検出力の実測

`authority: none` / `default_effect: no-state-change`

可変状態の正本は `docs/worklog.md` 末尾と現行 phase doc である。本文書は測定記録
(measurement record) であり、裁定台帳ではない。

- 起点: 段 4 裁定の変異事前登録 3 件 (すべて負例)。
- 測った checkout: branch `worktree-dev-wave-acceptance-pole-cost`、
  変異束縛 commit `16f99f18f91b96e51e10840995a75ca1f49ea563`。
- 変異 spec: `izanagi-dev-wave-mutation-spec/v1`、
  sha256 `91a92943b8e03b42a9713f05489a4e44319db6f03300fa0d85b700a7bdfe1df3`。
- probe spec: 同 schema、sha256
  `cd1a6d042d9537c0e67c2ef90b6dbede0de9710e5e9b8f06c36cbedbc4ba7943`。
- 実行環境: Pegasus 計算ノード dispatch (`--runner-mode dispatch --detached`)。
  runner argv は `python3 tools/run_tests.py orchestrator/tests/test_codex_reasoning_ab.py
  -q -rf --force-dispatch` に F95 由来の `--deselect` を 1 件加えた形で固定した。

---

## 1. 結果

baseline PASSED (458 passed, 2 skipped in 99.73s)。3 変異すべて KILLED で、
期待 node 集合と実測 node 集合は完全一致した。SURVIVED、MISMATCH、TIMEOUT、PARSE_ERROR は
いずれも 0 件である。

| ID | 単一変異 | 期待 node | 結果 |
|---|---|---|---|
| pole.m01 | 生成 session row 集合の一致検査を無効化 (M5) | `test_m5_generated_session_rows_require_set_equality` | KILLED |
| pole.m02 | `certification_scope` の `closed_world` を `False` にする | `test_material_report_certification_scope_is_exact_on_all_return_paths` | KILLED |
| pole.m03 | 例外経路後の `certification_scope` 付与を削除 | 同上 | KILLED |

---

## 2. F95 による再照準と、その補償

本 wave が変更した node
`orchestrator/tests/test_codex_reasoning_ab.py::test_verify_replays_complete_fake_codex_experiment`
は `REAL_REPO_SERIAL_NODES` に属する。F95 のとおり、変異 harness はこの種の node を期待 node として
表現できない (素の id で登録すると観測側が `@real-repo` 接尾辞付きになり MISMATCH、接尾辞付きで
登録すると preflight が「pytest collection に実在しない」で停止する)。恒久対応 T-417 は未実施で、
本 wave は F95 の 3 例目である。

F95 の台帳指示どおり runner argv へ
`--deselect orchestrator/tests/test_codex_reasoning_ab.py::test_verify_replays_complete_fake_codex_experiment`
を足し、期待集合を**非 real-repo の兄弟 node** へ再照準した。上表の 3 件はいずれも
`test_codex_reasoning_ab.py` 内の非 real-repo node である。

**この再照準は、本 wave の当の問い「memo 適用後も対象 node が自分の kill 義務を果たすか」を
測れない。** そこで親が別途、`DW-O19` の復元規律に従う直接注入で実測した。

- 注入した変異: pole.m01 と同一
  (`if sorted(actual_sessions) != sorted(expected_sessions):` → `if False:`、置換は file 内 1 箇所)。
- 注入後の `git diff --stat` が対象 1 file・1 行の単一変異であることを確認した。
- 対象 node 単体を計算ノードで実走し、**`1 failed in 56.45s`** を得た。失敗した assert は
  `assert "generated session row set mismatch" in "\n".join(tampered["failure_reasons"])` そのもので、
  memo 適用後もこの node が M5 を検出することを直接示す。
- 復元後、`git status --porcelain` 空・`git diff HEAD` 空を確認した。

### 2.1 拒否の冗長性 (kill の意味の但し書き)

M5 を無効化しても、tamper された manifest 自体は
`receipt canonical replay mismatch` と `rollout path mismatch` の 2 理由で拒否され続ける。
すなわち**受理集合の反転は起きず、変わるのは拒否理由の集合**である。
この node が pin しているのは拒否理由の同一性であり、`DW-M03` の言う
diagnostic sensitivity pin に近い。上表の pole.m01 の KILLED はこの但し書きつきで数えた。

---

## 3. 費用の実測 (paired A/B、各 2 走)

計算ノード dispatch で、同一 argv・同一 walltime・同一 task を用いて変更前後を各 2 回測った。

| 対象 | 変更前 run1 / run2 | 変更後 run1 / run2 |
|---|---|---|
| `test_verify_replays_complete_fake_codex_experiment` の call | 92.16 s / 92.56 s | 41.62 s / 41.59 s |
| `test_codex_reasoning_ab.py` 全体の wall | 192.18 s / 193.31 s | 143.16 s / 144.07 s |
| 件数 | 459 passed, 2 skipped | 459 passed, 2 skipped |

短縮量は node で約 50.8 秒、file で約 49.1 秒。変更前の 2 走の幅は 0.40 秒、
変更後は 0.03 秒で、いずれも短縮量に対して十分小さい。

**この focus 走の数値を受入全走の pole へそのまま引き算してはならない。** focus 走は
単一 process・非 xdist で、受入全走は 48 worker・loadgroup・別ノードである。参考として、
変更前の受入 artifact (`86d207bd.../shard-0/junit.xml`) では同 node が 94.2 秒で、
focus 走の 92.16 秒とは 2 秒の系統差がある。受入全走側の実測は本 wave の受入受領証が正本である。
