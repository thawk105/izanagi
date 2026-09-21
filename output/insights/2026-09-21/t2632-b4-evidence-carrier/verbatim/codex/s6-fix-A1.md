**実装済み・未実走**です。指定の3ファイルだけを変更し、テスト・commit は実行していません。

**1. 変更前の挙動**

- A2：canonical 化できない proposal は、hash 計算の例外で評価前に停止していました。
- A3／A4：docstring が、退避ファイルによる停止と bootstrap 再実行拒否の条件を過大に説明していました。
- A7／B6：重複 mkdir、定数 import 漏れ、WAL 不在により、新設テスト11件が検査対象へ到達していませんでした。
- A7／B4：launcher 評価 stub の certified 出力に attempt ID と対応する start がありませんでした。

**2. 変更したファイル・箇所**

| ファイル | 関数・行と変更 |
|---|---|
| [p3_s4_loop.py](/work/1/SFC/tanab/izanagi/.codex/worktrees/t2632-unit-a/orchestrator/campaign/p3_s4_loop.py:3714) | `main:3714`：`B4ProtocolError` を mode に関係なく捕捉し、hash=null で継続 |
| 同上 | `_load_provenance:1558`、`_append_provenance_entry:1613`：docstring の条件だけを限定 |
| [test_p3_s4_loop.py](/work/1/SFC/tanab/izanagi/.codex/worktrees/t2632-unit-a/orchestrator/tests/test_p3_s4_loop.py:7239) | `_base_selected_commit:7239`、`test_base_provenance_keeps_all_attempt_records:7279`：定数 import |
| 同上 | `test_base_provenance_corrupt_report_stops:7377`：`exist_ok=True` |
| 同上 | `test_base_provenance_inputs_do_not_read_report:7487`：既存の空 admitted history helper を再利用 |
| 同上 | `test_main_provenance_noncanonical_proposal_hash_is_null:7561`：NaN proposal が実 `main` から評価へ進み、entry の hash が null になる回帰テスト |
| [test_p3_b4_closed_critic.py](/work/1/SFC/tanab/izanagi/.codex/worktrees/t2632-unit-a/orchestrator/tests/test_p3_b4_closed_critic.py:2744) | `fixture_synthesis:2744`：同一 attempt の start／commit を WAL に記録。既存の `records["commit"] = record.payload` に ID が載る形へ修正 |

**3. 静的検査**

| 実行コマンド | rc |
|---|---:|
| `PYTHONPYCACHEPREFIX=/tmp/t2632-fix-pycache python3 -m py_compile orchestrator/campaign/p3_s4_loop.py orchestrator/tests/test_p3_s4_loop.py orchestrator/tests/test_p3_b4_closed_critic.py` | 0 |
| `git diff --check` | 0 |
| `python3 - <<'PY' … PY` による AST 比較（基準 commit の assertion、stub 外、attempt gate、入力射影） | 0 |

**4. 既存テストの期待値の自己点検**

基準 `36fb14a3d` にある両テストファイルの全テストについて、assertion の AST が一致しました。今回、既存の期待 rc・例外期待・skip・parametrize は変更していません。

launcher ファイルは `fixture_synthesis` の本体を除いた AST が作業開始時の HEAD と一致しています。差分は指定の stub 出力に限定され、`launcher_positive=True`、variant、assertion は維持しています。本番 `_wal_attempt_provenance` も変更していません。

**5. 所有外への波及・meta-test**

- caller、sort／trigger、admission、lock、共有 fixture、docs は未変更です。
- 新設テストは既存 fixture を使用し、改名・新しい共有 fixture・xdist 分類はありません。
- namespace の呼出数、certified writer／B-4 wiring の producer 目録、perf closure、agent input AST 隔離、real-repo serialization の分類を静的に点検しました。今回の差分による目録更新は不要と判断しています。
- production ファイルは lock／projection closure に含まれます。変異実走では裁定どおり drift と KILL を区別する必要があります。
- `py_compile` のキャッシュは指定コマンドの `/tmp/t2632-fix-pycache` に生成しました。

**6. 親の焦点走候補**

以下は前回の失敗12件（破損テストの全8パラメータを含む）と新設1件を覆います。`-rfs` 付きの実走をお願いします。

```text
orchestrator/tests/test_p3_s4_loop.py::test_base_provenance_duplicate_reuses_selected_attempt
orchestrator/tests/test_p3_s4_loop.py::test_base_provenance_keeps_all_attempt_records
orchestrator/tests/test_p3_s4_loop.py::test_base_provenance_corrupt_report_stops
orchestrator/tests/test_p3_s4_loop.py::test_base_provenance_inputs_do_not_read_report
orchestrator/tests/test_p3_b4_closed_critic.py::test_launcher_positive_uses_real_factory_and_real_base_main_for_commit
orchestrator/tests/test_p3_s4_loop.py::test_main_provenance_noncanonical_proposal_hash_is_null
```

**7. 変異の位置・単一理由性**

位置は production の `p3_s4_loop.py` です。変異は実行していません。

| ID | fix 後の位置 | 静的な自己点検 |
|---|---|---|
| S15 | `main:3718` | 捕捉を外すと新設 NaN テストが評価前に停止。実 loader・hash・drive を通し、評価本体だけを stub |
| S4 | `_wal_attempt_provenance:1663` | 採用 commit と最新 start の ID は異なり、双方に有効な start がある。選択 ID／refs 比較が検出点 |
| S5 | 同 `:1688` | payload hash も形式検査は通るため、全 record の digest 比較が検出点 |
| S6 | 同 `:1684` | 同 attempt の verify 2件を保持する fixture。stage 圧縮による欠落を refs 比較で検出 |
| S8 | `_load_provenance:1583` | 後段 loader と重複あり。例外だけでは単一理由にならず、評価・認可未呼出し assertion で区別する |
| S13 | `drive_iteration:2971` | 後段 merge にも loader がある。評価前検査の欠落は評価・認可未呼出し assertion に照準 |
| S14 | `make_critic_digest:1166` | admitted campaign を用意済み。report 不在でも動く変異に限り、3状態の出力 bytes 比較が検出点 |

## 総括

裁定 §2 の4項を修正しました。静的検査は rc=0、**実装済み・未実走**です。テスト成功・変異 KILL は未確認で、commit は作成していません。