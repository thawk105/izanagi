# 段 4 裁定 — [T-1907] v1 patch 別名凍結

入力: brief.md、plan.md (段 2)、consult-a.md (レンズ A: 裁定・scope・過大主張)、consult-b.md (レンズ B: 実効性・受入・変異)。
段 4 直前の再走査: rulings-inbox の最新は 2026-09-08 で本主題なし。local main e667c8c13 の decisions 末尾は D2065 で、D1281 / D1098 を改める裁定なし。

## 所見の裁定

| ID | 判定 | 採否 | scope | 裁定 |
|---|---|---|---|---|
| A-1 | real | 採用 | 内 (記録の文言) | brief の「再走による pin 破壊経路は既に閉じている」「止めている研究は無い」を撤回する。記録には「site 設定を通さない probe の 3 構成で旧 ID と不一致」と「現行 sweep / repro の通常 resume は旧 lock の admission 欠落と preimage 完全照合で拒否される (コード読解、実走なし)」を分けて書く。研究停止の有無は調べていないと書く。 |
| A-2 | real | 採用 | 内 (記録の文言) | brief F2 を訂正する。旧 WAL の先頭時刻は write-heavy / balanced が 2026-06-22、read-heavy が 2026-06-28 (UTC、親が `date -u -d` で再計算)。ホスト帰属と生成時の patch bytes は WAL / lock に記録が無く確定しない。 |
| A-3 | refuted | — | — | 凍結 bytes は f7a5444 (`4dfd3785b^` の blob、`git diff f7a5444 06d272b` は式 1 行だけ) で確定。 |
| A-4 | refuted | 一部採用 | 内 | 配線替え・新 pin は要求されない。README は既存警告の文面を書き換えず、新しい凍結小節だけを足し、その中で現行通常経路の挙動を限定表現で添える (「本題の凍結だけ」に最も近い形)。D1098 の理由全体を実現したとは報告しない。 |
| A-5 | 成立しない | 記録のみ | — | 受理集合・projection の変化経路なし。追加 reader (`p3_s4_loop.py:1222-1247`、`knowledge_manifest.py`、`backoff_requested_us.py:1062` 等) は insight の reader 表に補記する。 |
| A-6 | refuted | 採用 (記録の型) | 内 | M1 は「既存の IZANAGI_ token 在庫 gate が新 file に掛かることの確認」と記録し、凍結 bytes の検出力に数えない。 |
| B-1 | real | 採用 | 内 | `test_p3_b4_wiring_probe.py::test_source_and_test_are_the_only_non_output_worktree_changes` は git status を読むので、未 commit と変異中に赤、commit 済み clean では緑。変異 runner の node 集合から外し、冗長 gate として台帳に書く。受入全走は commit 済み clean で行う。`test_login_headroom.py:1602` は緑予測のまま受入で確かめる。 |
| B-2 | real | 採用 | 内 | 変異の runner node 集合を下記 8 node に固定し、検出力の主張はこの集合に限定する。観測 node が期待と食い違えば DW-M08 の probe として erratum を残して再登録する。 |
| B-3 | real | 採用 | 内 | M4 は「全文を空文字へ置換 (空 file 化)」とし、削除とは意味が違うことを台帳に明記する。 |
| B-4 | real | 採用 | 内 (記録の文言) | F5 は「記録時点で `git worktree list` に載る worktree (128 件列挙、自分を除く) を、committed = main...HEAD の名前、dirty = HEAD blob との bytes 比較、untracked = `patches/*.patch` の 3 方法で見て、`patches/` と凍結 3 file に触れる検出 0 件」と限定する。独立 clone・index だけの変更・将来の編集は観測外。T-2647 の残作業記述 (worklog / insight) は本 wave の編集面に触れない。 |
| B-5 | real | 採用 | 内 | commit を分ける。実装 commit (新 patch 1 本) は Codex `role=author` + Claude `role=integrator`/`manager`。docs commit (README・insight・spool) は Claude `role=author; scope=docs` + `role=manager`、実装面を含まないので Codex author は不要。trailer の正本は `docs/ai-provenance.md` で、commit 直前に読み直す (DW-O17)。 |
| B-6 | real (nit) | 採用 | 内 | 記録で ident.py の行番号を引くときは 140 (admission 不一致)、204 (admission 必須)、379 (preimage 完全照合)、484 (identity 照合の呼出し) を使う。 |
| B-7 | refuted | — | — | 実装子の手順 (subshell + noclobber + `git show <blob> >`) は維持。 |

scope 外で real な所見は無い。したがって裁定パッケージは作らない。

## プラン v2

1. **U1 (Codex author、workspace-write、単独):** `patches/silo-backoff-fixed-v1.patch` を blob `f7a54445764025112317151106712bb9d97678ab` の bytes そのもので新規作成する。検証は `sha256sum` = `35237d314df708c6a6cb6fece0a8a59cd199bb57337013f95f6ed50ea2a2f911`、`git hash-object` = f7a5444、`cmp` rc=0。他の file は編集しない。docs 編集・`git add`・`git commit` をしない。
2. **親 統合 (段 5 後):** `git status --porcelain --untracked-files=all` が新 file 1 本だけ、bytes 検証を親も再実行、保護対象 7 件の sha256 (plan の表) 不変を確認して実装 commit。
3. **段 6 (軽量版):** DW-C00 に従い review 子 2 本は省く。理由: 設計択一は本段で閉じ、実装は blob の bytes 複製で親の `cmp` / `git hash-object` が完全に検収でき、正しさ防壁・受理集合に触れない (A-5)。代わりに親が (a) bytes 検証、(b) 焦点走 = 下記 8 node + `test_p3_b4_wiring_probe.py` の当該 node + `test_login_headroom.py` の当該 node を commit 済み clean で実走、(c) 変異 matrix を実走する。
4. **README (親、docs commit):** `patches/README.md` の「hole の式は v2」節の直後・`BACKOFF_NOINLINE` 節の直前に凍結小節を足す。既存行は変えない。内容: 由来 (blob / sha256 / 導入 commit 4f7bb3c76 / 取得元 `4dfd3785b^`)、476a128 (初版) と同一でないこと、用途は歴史的 v1 ソースの参照と明示的な再適用に限ること、旧実験の完全再現・現行 consumer の v1 使用を保証しないこと、現行 patch・consumer・凍結物・WAL・ledger は不変、bytes を pin する検査は置いていないこと (依頼の scope 外指定)、現行 sweep / repro の通常 resume は旧 lock を拒否する (コード読解) ことの限定併記、根拠 D1098 / D1281。
5. **記録 (段 7):** insight `output/insights/2026-09-16/t1907-backoff-v1-patch-freeze/` (README + verbatim + 変異 spec / 台帳)、spool fragment は worklog (T-1907 を完了で閉じる) と decisions (v1 の同定・別名 path・配線替えなし・pin なしの設計判断)。
6. **受入・land (段 9):** docs commit 後に `tools/dev_wave_wait.py acceptance` で全走、child-green で land。

## 変異の事前登録 (DW-M01、実装前)

- 対象 commit: 実装 commit (新 patch 1 本だけを含む)。
- runner: `python3 tools/run_tests.py --force-dispatch` + 次の 8 node (完全集合)。
  - `orchestrator/tests/test_ccbench_spawn_sites.py::test_patch_define_inventory_matches_condition_gate_registry`
  - `orchestrator/tests/test_ccbench_spawn_sites.py::test_define_sink_cross_product_has_no_unreviewed_ungated_member`
  - `orchestrator/tests/test_ccbench_spawn_sites.py::test_define_sink_cross_product_rejects_synthetic_member_without_gate`
  - `orchestrator/tests/test_ccbench_spawn_sites.py::test_define_sink_cross_product_rejects_gate_with_only_one_arm`
  - `orchestrator/tests/test_ccbench_spawn_sites.py::test_define_sink_cross_product_does_not_defer_unlisted_member`
  - `orchestrator/tests/test_ccbench_spawn_sites.py::test_define_sink_cross_product_classifies_t2155_production_sinks_exactly`
  - `orchestrator/tests/test_ccbench_spawn_sites.py::test_define_sink_cross_product_t2520_certify_entry_removal`
  - `orchestrator/tests/test_p3_s4_loop.py::test_all_naked_izanagi_macro_patches_are_registered_or_allowlisted`
- 冗長 gate (runner 集合から除外、単独変異の証拠に数えない): `orchestrator/tests/test_p3_b4_wiring_probe.py::test_source_and_test_are_the_only_non_output_worktree_changes` (作業ツリーの非 output 変更を一律に拒否し、変異の意味を見ない)。

| ID | category | 置換 (file = `patches/silo-backoff-fixed-v1.patch`) | 期待 | 期待 node |
|---|---|---|---|---|
| M1-unregistered-izanagi-token | negative | 行 `+# izanagi: static backoff magnitude (us) to bypass Cicada's adaptive hill-climb.` の末尾に ` IZANAGI_FREEZE_PROBE` を足す | KILLED | `orchestrator/tests/test_p3_s4_loop.py::test_all_naked_izanagi_macro_patches_are_registered_or_allowlisted` |
| M2-formula-offset | negative | `+    double now_backoff = static_cast<double>(BACKOFF_FIXED);` → `+    double now_backoff = static_cast<double>(BACKOFF_FIXED) + 1.0;` | SURVIVED | なし |
| M4-empty-file | negative | 全文 → 空文字 (空 file 化。削除ではない) | SURVIVED | なし |

- M1 の意味: 新 file が既存の IZANAGI_ token 在庫 gate の走査対象に入ることの確認。凍結 bytes の正しさの検出力ではない (A-6)。
- M2 / M4 の意味: 式の改変・内容の喪失を、runner 集合内の既存テストは検出しない。依頼が bytes pin の追加を scope 外としたことの帰結として記録し、equivalent・合格とは呼ばない (DW-M04)。
- 見送り: M3 (476a128 全文へ置換) は M2 と同じ類 (macro 集合を変えない bytes 改変) で追加情報が無い。M5 (README の sha256 改変) は docs で実装面でない。
- 単一理由性 (F820) は実装 commit 後に確認する: M1 の token を読む他の test が runner 集合内に無いこと (`test_t2187_adaptive_const_probe.py:431` は固定の別 patch を読むので集合外かつ無反応)、anchor が新 file 内で 1 箇所であること。
- 期待赤は時間に依存しない (正規表現の全文走査だけ)。hang_risk なし。
