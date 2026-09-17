# 段 4 裁定 — dev-wave-t2703-role-input-docs

main 再走査: b4631a92e から進みなし。裁定 inbox に本 wave へ届く新規更新なし。

## 所見の裁定 (real / refuted、採否)

| # | 出所 | 所見 | 判定 | 採否 |
|---|---|---|---|---|
| A1 | レンズ A | pin 閉包は 3 機構で閉じない — B-4 closed critic の receipt 再読 (`p3_b4_closed_critic.py` L1658 / L1679 live 比較、`_projection_paths` 閉包)、`p3_b4_raw_record_producer.py` の snapshot 照合、`claude_projected_provider.py` の role hash / 実効 prompt | real | 採用: pin 閉包表へ第 4 機構を足し、記録済み B-4 receipt が 0 件 (repo 内 `output/` を `role_file_sha256` で全数検索、hit は test dispatch receipt と selector-8b だけ) であることを insight へ記録。「受理集合・挙動不変」の無条件主張は撤回し「schema・検査規則・受理述語は不変、役割本文・prompt bytes・source sha・semantic digest は変わる」と限定 |
| A2 / B3 | 両レンズ | planner の凍結説明を全経路へ一般化している。T-2588 (K2 手動 loop) は 2 周目に 1 周目の実測を `current_perf` へ入れた (`materials/planner-input-2.json`)。runbook の `<baseline>` は固定規定でない | real | 採用: 凍結の記述は 8c 自動 trial (D410 決定 1) に限定し、手動 runbook 経路は「メインセッションが runbook に従って射影する (値の選び方は runbook 側)」とだけ書く。runbook へ凍結規則を新設しない (新しい運用規定の密輸になる) |
| A3 | レンズ A | D1860 (削除せず null) との関係の根拠不足 | real | 採用: decisions fragment に「D2104 項 4 に基づく後続の限定訂正。D1860 当時の判断は保持、前提 (planner 例に field が在る) は T-304 で消滅」を記録 |
| A4 | レンズ A | leakproof への追加文のうち「その走行の PerfConfig を用いる」は指示形。trigger-gating へ D 番号・内部関数名は不要 | real (部分) | 採用: inline 文書は記述形に限定し内部関数名・裁定番号・アーム名を置かない。role 本文の「設計根拠」節相当には既存様式どおり D 番号を残してよいが、関数名は書かない |
| A5 | レンズ A | hardware 行削除・critic-experiment・trigger-gating は scope 内 (refuted)。base coder 除外の十分性は判定不能 | — | P2 / P3 (理由修正) 採用。base coder は手動経路専用で機械凍結が無く、誤りの記述も無いので触らない (残件として開示) |
| A6 / B6 | 両レンズ | manifest / schema / template pin は不変、semantic digest と developer_instructions は変わる | refuted (攻撃) | plan のとおり |
| A7 / B7 / B8 | 両レンズ | M1 の単一 node 赤から単一原因は導けない。M2 は import 時拒否 | real | 採用: M1 を「3 role の追随漏れの集約検出」と登録し、M1a/M1b/M1c (planner / critic / coder のタプルを 1 つだけ除去) を追加して role ごとの追随が個別に load-bearing であることを観測する。M2 は個別 node でなく collection error (checker rc≠0 + `SOURCE_FILE_SHA256 drift` 診断) で判定し KILLED に数える |
| B1 | レンズ B | verify の説明は段 4b (legacy のみ) に限られ、sort / trigger-gating は `VERIFY_LEGACY_PLUS_S2` | real | 採用: Measurement Methodology に「段 4b = legacy の小規模 workload 1 rep、sort / trigger-gating 軸 = さらに S2 構成 (1m records / 48 threads / extime 3) の pass」を書く。旧文の 1m / 48 / extime3 は S2 verify の値だったと insight に記す |
| B2 / B4 | レンズ B | perf receipt が PerfConfig を差し替える / reject 世代が凍結 baseline を上書きする | refuted | 「初期 metrics 定数 (現行は全 null)」の表現を採る |
| B5 | レンズ B | consumer 閉包の完全証明はできない。check_docs は runbook を living-doc 検査へ登録 | 判定不能 | 焦点走 15 file (plan 14 + `test_p3_b4_raw_record_producer.py`) と check_docs / check_codex_agents を親が実走 |
| B9 | レンズ B | adapter 単独 commit にも実装 author 要件 (`check_ai_provenance.py` は `.codex/` を実装面) | real | 採用: docs 本文 + ledger + baseline + adapter を **1 つの整合 commit** にし、trailer は Codex author (ledger/baseline)・Codex reviewer・integrator (親: docs + render) を並記。insight / spool fragment は別 commit |
| B10 | レンズ B | fix 子の見出し欠落の再発防止 | 判定不能 | 全子の成果物を `check_codex_output.py` で受理検査 (実施中) |

## plan v2 (変更点だけ)

1. leakproof: plan の編集案を基に、(a) 記述形に統一、(b) 「calibrator が別の設定を確定した走行では…」は「性能比較に入る段では calibrator が決めた規模に差し替えられる (この文書の値は配線規模)」の記述形へ、(c) verify を軸別に書く (B1)、(d) skew0.9 の直感 (少数の hot key へ集中する高 contention) は残す、(e) 適用版 1 行は「2026-09-17 改訂。`p3_s4_loop.py` の `default_perf()` と一致」(関数名は file 名を伴う参照であり指示ではない)。
2. critic.md / critic-experiment.md: plan のとおり。適用版 1 行 + 恒等変換の注記。
3. planner-v4.md: L17 は「campaign の基準測定値 (`current_perf` / `leading_indicators`)」へ。入力節末尾に「適用版」+「8c 自動 trial では workload ごとに初期 metrics 定数 (現行は全 null) で 1 回射影して凍結し世代を跨いで更新しない (D410 決定 1)。手動 runbook ではメインセッションが runbook に従って射影する」。関数名は書かない。
4. trigger-gating.md L62-63: 「baseline は campaign (workload) ごとに 1 回射影した snapshot で、世代を跨いで更新されない (D410 決定 1)。これ以外の実験・偵察の数値は入力に存在しない」+ 適用版 1 行。
5. runbook 2 本: `last_delta_pct` 除去 + 適用版 2 行 (「凍結」の規定は書かない)。
6. ledger / baseline / adapter: plan のとおり。1 commit。
7. decisions fragment: D1860 との関係 (A3) と本 wave の射程を 1 決定に記録。

## 変異事前登録 (実装後に単一理由性を確認してから走らせる。baseline 緑が前提)

| ID | 変異 (1 箇所) | 期待 |
|---|---|---|
| M1 | `_extend_t2703_role_source_baseline(_PRE_WAVE_ORIGINLESS_BASELINE)` の呼出し 1 行を除去 | `test_reflux_originless_compatibility.py::test_originless_default_preserves_every_nonvolatile_leaf_and_closed_key_set` FAIL (3 role 集約)。`test_originless_harness_rebuild_is_deterministic_control` は PASS |
| M1a | helper 内の planner タプルだけ除去 | 同 node FAIL |
| M1b | helper 内の critic タプルだけ除去 | 同 node FAIL |
| M1c | helper 内の coder タプルだけ除去 | 同 node FAIL |
| M2 | ledger `critic` の sha を旧 `cd1c3652…` へ戻す | `tools/check_codex_agents.py` rc≠0 (`SOURCE_FILE_SHA256` drift)、`test_codex_agents.py` は collection error (個別 node に到達しない) — KILLED は checker rc と診断文で判定 |
| M0 | ledger の Reviewed コメント行の文言だけ変更 (等価) | 全 node PASS、checker rc=0 (SURVIVED 期待) |

harness: `tools/mutation_harness.py` を専用 container worktree で。runner argv は `test_reflux_originless_compatibility.py` + `test_codex_agents.py`。
