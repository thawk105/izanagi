# 段 4 裁定 — [T-2273] 受入 shard-0 候補 (a) の実装 (2026-09-27)

入力: s1-brief.md、codex/s2-plan-out.md、codex/s3-consult-a-out.md (レンズ A、修正後 GO)、codex/s3-consult-b-out.md (レンズ B、修正後 GO)。
裁定 inbox 再走査 (14:5x JST、裁定書作成直後の `date` 実測 14:57:11): wave 開始 (14:27、main `ad114fba0`) 以後 local main は不変、新裁定なし。

## 所見の裁定

| 所見 | 裁定 | 扱い |
|---|---|---|
| A1 / B1 正例が実 builder の複製分岐と hook からの起動を通らない | real, must-fix | 採用。plan v2 §3 の T1 (本物の hook で起動・完成) と T2 (既存の実 builder test に helper 経由の観測) |
| A2 環境変数が入れ子 pytest 等へ継承される | real (環境変数案に対して) | 採用 = 環境変数を新設しない。path は既存 `_t080_join_shared_bases` と同じ識別子 (`str(ROOT)` と `PYTEST_XDIST_TESTRUNUID`) から builder 側で導出する。この変数の継承は既存の共有 base が既に同じ扱いで、新しい経路を足さない |
| A3 写しの時点差は session の受理「結果」を変えうる | real (意味の差として) | 採用 (記述のみ)。brief (P7) を「受理**規則**は不変。session 中の output/ の変更は fixture に反映されない (写しは configure_node 時の 1 時点)」へ訂正。D2242 段 4 A1 と同じ扱いで gate は足さず docstring に明記 |
| A4 発火順序を probe (tryfirst) と揃える | refuted (効果として) | 起動は早期 memo 起動の直後で差は ms 単位、import も probe と同じく thread 内。変更なし。thread 起動→実関数開始の所要は実受入で測らない (計器を足さない) |
| A5 join が無期限になりうる | real / 不採用 | 既存の早期 memo job と同じ無期限 join で揃える (受入は外側 dispatch の walltime が上限)。削除は finally で必ず試みる |
| A6 module 名・import 副作用 | real (未確認点として) | 採用 = 焦点走で controller の import 成功と写しの完成を実走確認 (T1 が本物の import を通す) |
| B2 `isinstance(config, pytest.Config)` の追加 | real | 採用 = 条件は `_early_memo_selected` を共用。既存の模擬 hook test (`_early_memo_cache_probe` 等、shard spec 付きで本物の hook を呼ぶもの) は新しい起動関数を局所的に no-op へ差し替える |
| B3 marker 3 種は過剰 | real | 採用 = 結果 file 1 つ (`result.json`、成功 / 失敗を atomic rename) |
| B4 E1 定数・B の早期 memo 超過の自動 infra 化 | real, must-fix | 採用 = 単位 P で追加 node 集合を投入前に login collection の A/B 差から固定。B の赤は自動分類しない (親が根拠付きで分類) |
| B5 計算量は約 2.6 node 時間超 | real | 採用。下の見積りでユーザー確認 |

## プラン v2

1. **controller (conftest.py):** `pytest_configure_node` の `_start_early_memo_job(node)` の直後、同じ `_early_memo_selected(node.config)` の分岐で `_start_t080_visible_output_snapshot(node)` を呼ぶ。session で 1 回だけ (config 属性に job を保持、2 回目以降は何もしない)。同期部分: `testrunuid` と repo root から dir `Path(tempfile.gettempdir()) / f"izanagi-t080-visible-output-{identity}"` (identity = `sha256(json.dumps([str(ROOT), run_id]))`、`_t080_join_shared_bases` と同じ式) を `mkdir(exist_ok=False)`。非 daemon thread で `importlib.import_module("orchestrator.tests.test_s8b_oracle_driver")`、`module.ROOT` と conftest の root の一致を確かめ、`module._copy_git_visible_output(module.ROOT, dir / "output")` を 1 回呼ぶ。終わりに `result.json` を pending → rename で置く (成功 `{"ok": true}`、失敗 `{"ok": false, "error": repr}`)。例外は job に保持。
2. **終了:** `_finish_memo_sessions` の終了列に `_finish_t080_visible_output_snapshot` を足す (early memo の後)。thread を join し、finally で dir を `shutil.rmtree` (存在すれば)。保持した例外を伝播。worker 全終了後に走る位置であることを確認する。
3. **builder (test_s8b_oracle_driver.py):** 1458 行を helper `_t080_copy_visible_output(destination)` に置換。helper: `PYTEST_XDIST_TESTRUNUID` があり上の dir が存在すれば `result.json` を 180 秒まで待ち (0.05 秒間隔)、`ok` なら `shutil.copytree(dir / "output", destination)`、失敗・超過は理由付きで例外。dir が無ければ従来の `_copy_git_visible_output(ROOT, destination)`。docstring に時点差 (A3) を書く。
4. **test (最小):**
   - T1 (新規 1 本): 小さい git repo (tracked / modified tracked / untracked / ignored / 除外 receipt) を test module の `ROOT` に差し替え、`tempfile.tempdir` を test 局所に、`_start_early_memo_job` を no-op に差し替えて、本物の conftest `pytest_configure_node` を 2 node 分呼ぶ。(a) helper を 1 度も呼ばずに `result.json` が `ok` で現れる (hook で起動)、(b) 実関数 spy (`wraps`) が 1 回・引数 (ROOT, dir/output)、(c) `PYTEST_XDIST_TESTRUNUID` を合わせて helper を 2 回呼び、間に source を変更しても両方が変更前の直接複製と同じ集合・bytes・mtime、(d) finish で dir が消える。
   - T2 (既存 `test_t080_shared_base_builds_real_builder_once_across_processes` に assert 1 つ): helper の呼出し回数 == builder の呼出し回数。
   - 既存の模擬 hook test の fixture で新起動関数を no-op 化 (B2)。既存の期待値は変えない。
5. **変えないもの:** `_copy_git_visible_output`・`_git_visible_output_paths` の本体、全件性の検査 2 か所、`_T080SharedBases` (get / close / lock / complete.json)、早期 memo の挙動、既存 test の期待値。

受理・拒否の含意 (署名形): 禁止 = 共有 session 下の builder が写しを経由せず実 repo の output/ を読むこと、写しを worker ごと・builder 開始時に作ること、写しと異なる集合・metadata を渡すこと。通る正例 = 同じ session の builder が、configure_node 時に実関数が 1 回作った写しから、変更前の直接複製と同じ集合・bytes・mtime を受け取る。

## 変異の事前登録 (DW-M01、単一理由性は実装後に確認し、成立しなければ再照準して erratum)

| ID | 位置 | 変異 | 期待 kill node |
|---|---|---|---|
| P0 | helper docstring | 1 語変更 (等価) | なし (SURVIVED) |
| M1 | builder 1458 相当 | helper でなく `_copy_git_visible_output(ROOT, root / "output")` を直接呼ぶ | T2 |
| M2 | helper の複製元 | 写しがあっても `_copy_git_visible_output(ROOT, destination)` で複製 | T1 (c) 変更後 bytes の混入 |
| M3 | helper の copytree | `copy_function=shutil.copy` | T1 (c) mtime 不一致 |
| M4 | controller の 1 回性 | node ごとに実関数を呼ぶ (job 保持を外す) | T1 (b) spy 2 回 (dir の mkdir 衝突で落ちる場合は再照準) |
| M5 | controller の写し生成 | 実関数の代わりに `shutil.copytree(ROOT / "output", dir / "output")` | T1 (b) spy 0 回 |
| M6 | 起動時点 | configure_node では起動せず helper の初回呼出しで起動 (builder 時に遅延) | T1 (a) |
| M7 | 終了 | finish で dir を消さない | T1 (d) |

## 計測の事前登録 (系列投入前に固定)

1. A = 測定開始時の local main の clean worktree (SHA 固定)、B = A + 本 wave の実装 commit (clean、SHA 固定)。記録 commit は測定後。
2. 順序 A,B / B,A / A,B の隣接 3 対を逐次投入。測定中は自分の他 job を走らせない (D357)。門番 = 他 session の受入 leader ≤ 1 ∧ load1 ≤ 60 (前回と同じ)。両 tree に同じ collect-only 温めを 1 回ずつ。
3. 有効性: 各走の 3 shard 緑、HEAD・clean の前後一致、条件内の collection と共通 node の shard 割付一致、A/B の collection 差は B の新規 test (T1) だけ (投入前に login collection で固定)。infra 由来の赤は根拠付きで分類しその対を同順序で取り直す。B の赤 (早期 memo 超過を含む) は自動で infra にせず、本実装の経路との関係を調べて分類する。実装由来なら直して系列を最初から。
4. 判定量: Δi = W_0(Ai) − W_0(Bi)、ri = Δi / W_0(Ai)。対差の中央値と対率の中央値を別々に報告。
5. **land 条件:** 3 対すべて Δi > 0 ∧ 対率中央値 ≥ 10 %。
6. **5 分判定 (別):** B の W_max (3 shard の最大) 3 走の中央値 ≤ 300 秒。各走の超過も併記。
7. 補助量 (判定に使わない): W_0・W_1・W_2・W_max、最遅 shard、shard-0 の O_max・L・O_max − L。写し待ちの直接計器は無く、足さない (不明と記す)。
8. 記録: land 達成 ∧ 5 分達成 → land。land 達成 ∧ 5 分未達 → 段階的改善として land し、「5 分未達、次は (b) = 発行 subprocess」と記録して止める。land 未達 → land しない (5 分の B 値は参考値)、次は (b) と記録して止める。判定不能は原因と有効対数を記録。

## 計算量見積り (job Elapse の実測単価)

前回 (D2242) の系列 29 shard job の Elapse 合計 8,333 秒 → 1 shard job 287 秒、受入 1 走 ≈ 862 秒 = 0.24 node 時間。

- 系列 6 走 (取り直しなし) 1.44 node 時間。前回並みの取り直し (10 走) なら 2.31 node 時間。
- 焦点走 2〜3 回 (1 回 ≈ 166〜303 秒) ≈ 0.2 node 時間、変異 (probe + final、8 変異 × 数 test、1 走 30〜40 秒 × 2 系列) ≈ 0.1〜0.3 node 時間、記録前の受入 1 回 0.24 node 時間。
- **合計 ≈ 2.0 (取り直しなし) 〜 3.1 node 時間 (前回並みの取り直し)。確認線 2 node 時間を越えるので、系列投入の前にユーザー確認を取る。**
- **ユーザー回答 (2026-09-27 15:0x JST、AskUserQuestion): 「3 対で投入 (推奨)」** = 上限の目安 約 3.1 node 時間、infra 失敗の取り直しは前回並み (4 走) まで、超えそうなら止めて再確認。

## 段 5 の分割

- 単位 L (実装): `orchestrator/tests/conftest.py`、`orchestrator/tests/test_s8b_oracle_driver.py`、既存の模擬 hook fixture の no-op 化に必要な test file (`orchestrator/tests/test_real_repo_serialization.py` 等、必要な行だけ)。Codex author、子 worktree。
- 単位 P (計測 probe): 前回 probe (`dev-wave-t2273-shard0-local-copy/probe/`) を本 wave 用に移植。job dir・slug の置換、E1 の追加 node を定数でなく投入前に固定する入力 file (`expected-added-nodes.json`) から読む形へ、B の赤を自動 infra 化しない、W_1・W_2・W_max と上の 4 通りの記録を出力。Codex author、子 worktree 内の scratch dir (`probe-t2273pi/`) に書かせ親が job dir へ退避。repo には入れない。
- 所有は素集合。
