# 段 4 裁定 — [T-2847] mutation-run (2026-09-23)

入力: brief.md、s2-plan.md (受理 rc=0)、codex/s3-consult-a.md (F01〜F09)、codex/s3-consult-b.md (B01〜B10)。裁定 inbox 再走査: 2026-09-23 full32/full33 に本 wave と食い違う裁定なし。

## 所見の裁定

| ID | 裁定 | 採否・反映 |
|---|---|---|
| P1 | real (F09 の限定つき) | mocc V25・V34、si V28・V29 は scope 外。V25 の停止は計装なしでも観測しうるが、期待 (完走 prefix が S) の検証に計装 (pin C の内容) が要るので外す。insight に理由を書く |
| P2〜P5 | real | そのまま。P2 の文言は F08 により「条件 gate の許可ドメインへ 14 macro を追加 (判定基準・patch 束縛は不変)」へ直す |
| F01 | real must-fix | 採用。発火診断 (下記 R2) を各 patch に入れ、起動器が ycsb run の stdout/stderr を保存する |
| F02 | real must-fix | 採用。V21 は「非空の先行 prefix があり、他の構造違反がないとき」に限定して期待を書く。発火取引の write 有無を診断に出す。lock の解放漏れは 1 thread の終端なので許容し、insight に書く |
| F03 | real must-fix | 採用。V20 は UPDATE の公開版だけを、lock=0・latest=1・absent=0・genesis より大きく・どの C/W 行にも出ない値に固定 (author が source で根拠を示す) |
| F04 | real must-fix | 採用。V26 は「read set に無く write set にある key の read で、返す bytes が buffer と異なる」、V27 は「二度目の update の入力と最終 buffer が異なる」を changed の条件にする |
| F05 | real should | 採用。V18・V35 は changed = 変異後 maxtid ≠ 元の計算値。V35 は加えて「maxtid ≤ 読んだ版の最大」を extra counter に出す。V18 は「maxtid ≤ 書く key の現版の最大」を extra に出す |
| F06 | real should | 採用。診断は relaxed atomic の加算だけで、出力は終了時 1 回 (R2)。race 区間に I/O を置かない |
| F07 | real should | 採用。stock が N/I の workload では、その workload の変異 verdict を「帰属不能」とする |
| F08 | real should | 採用 (P2 の文言訂正)。新 macro は裸マクロで `CCBENCH_` 外なので pipeline の genome から供給されない — 既存 14 本と同じ隔離 |
| F09 | real | P1・P5 を維持。P5 で直す場合は初回結果・誤りの source 根拠・修正後の別 run を分けて記録 |
| B01 | real must-fix | 採用。stock build は job ごと 1、stock run は job 内の各 workload ごと 1 |
| B02 | real must-fix | 採用。s8a の差し替え = buildcache.DEFAULT_CC/CXX・source_digest.resolve_evidence(cxx)・repo_output_root・ENV_TAG・subprocess 受動保存。admission の検査は弱めない |
| B03 | real must-fix | 採用。V21 の証人なし verify の argv・rc・verdict を結果 JSON の別欄 `no_witness_verifier` に保存 |
| B04 | real must-fix | 採用。job ごとに別の計測用 checkout (wave tip の detached worktree + submodule 初期化 + lock) |
| B05 | real should | 採用。s8a の CLK は driver 値 2100 のまま差し替えず、meta に記録 |
| B06 | real should | 採用。stock trace build は起動器が `_broken_build_and_verify` と同形の直 CMake (patch なし・macro なし・STOCK_G・TRACE=1・同 compiler・同依存物) で作る |
| B07 | real should | 採用。test の docstring の件数固定も同じ変更で直す |
| B08 | real should | 採用。変異 matrix は登録 test が殺せる 4 件に限る (下記)。inert・1 patch 1 機構・方向・stock 分離は source 差分と実走記録で確認する |
| B09 | real should | 採用。V24 は「未到達 (未発生)」として記録し盲点に数えない。V26・V27・V22・V35 は changed ≥ 1 かつ committed ≥ 1 のときだけ「盲点として certified」 |
| B10 | real nit | 採用。V18 と V35 は同時適用しない (各 patch 単独適用が前提) と README に書く |

## R1 — scope (確定)

新規 14 本 (slug・macro は s2-plan.md の表どおり。patch 名は `patches/broken-silo-<slug>.patch`、対照 V31・V32・V33 は `patches/control-silo-<slug>.patch`) と V08 trigger-misattr (s8a driver)。

## R2 — 発火診断 (全 14 patch 共通の契約)

- 各 patch の macro 有効時だけ、ファイル内 static の `std::atomic<uint64_t>` 3 個 (reached / changed / committed、必要なら extra) を relaxed で加算する。
  - reached = 変異枝に入った回数。changed = 変異が元コードと異なる挙動を実際に生んだ回数 (相談 A の「patch ごとの発火条件」表を正本とする)。committed = changed を 1 回以上含む取引のうち commit() が true を返した数 (thread_local の flag を begin() で落とし、changed で立て、commit 成功時に加算)。
- 出力は process 終了時に 1 回だけ、static object の destructor から stderr へ 1 行: `T2847_FIRED slug=<slug> reached=<n> changed=<n> committed=<n>[ <extra名>=<n> ...]`。文字列に `IZANAGI_` を含めない。
- race 区間 (lock 保持中・payload 複写と TID 再読の間) に I/O を置かない。加算は relaxed atomic のみ。
- 分類規則: 変異の効果が commit 履歴に現れる必要がある行は changed ≥ 1 かつ committed ≥ 1 でないと「未発生」。対照 V31・V32・V33 は changed ≥ 1 かつ commit 非空で「正しさを保つ対照として S」。

## R3 — workload (事前登録。変更しない)

共通 = ycsb_tuple_num 200・ycsb_zipf_skew 0.9・extime 1。`t/r/m/o` = thread_num / ycsb_rratio / ycsb_rmw / ycsb_max_ope。

| 記号 | t/r/m/o | 使う変異 |
|---|---|---|
| W1 | 4/50/false/5 | V17・V22・V35 |
| W2 | 4/0/false/5 | V18 |
| W3 | 1/0/false/1 | V19・V23 |
| W4 | 1/50/false/5 | V20・V24・V33 |
| W5 | 1/50/false/10 | V21・V26 |
| W6 | 1/0/false/10 | V27 |
| W7 | 4/50/true/5 | V31 |
| W8 | 1/0/false/5 | V32 |

## R4 — 期待 (事前登録。設計書 §4 + 相談所見。結果を見て変えない)

| V | 期待 (発火時) | 未発火時 | 分類の条件 |
|---|---|---|---|
| V17 | N (巡回) | S | 巡回が出れば「期待した層」、出なければ changed/committed で「未発生」か「盲点」を分ける |
| V18 | N (巡回) または I (version dup) | S | 同上 |
| V19 | I (version dup) | S | |
| V20 | I (orphan)。write_version_mismatch 等の他 counter が動けば「別の層」 | S | |
| V21 | 証人あり I・証人なし S (先行 prefix 非空・他違反なし) | 両方 S | changed = 省いた commit 数 |
| V22 | S (盲点) | S (未発生) | changed ≥ 1 ∧ committed ≥ 1 で盲点 |
| V23 | S (盲点) | S (未発生) | 同上 |
| V24 | S (未到達) | — | 常に「未発生 (未到達)」、盲点に数えない |
| V26 | S (盲点) | S (未発生) | changed ≥ 1 ∧ committed ≥ 1 |
| V27 | S (盲点) | S (未発生) | 同上 |
| V35 | S (盲点、TID 規則の違反) | S (未発生) | extra の規則違反 ≥ 1 ∧ committed ≥ 1 で盲点。N/I が出れば「別の層」 |
| V31 | S (対照) | — | N/I なら誤検出 |
| V32 | S、X/P = 0 (対照) | — | 同上 |
| V33 | S、commit 非空 (対照) | — | 同上 |
| V08 | s8a の checks どおり: 骨格 t4 = certified・保存則・構造ゼロ、t1 = abort 0、misattr t4 = verifier 緑のまま構造ゼロ検査が赤 | — | 盲点として certified (検査の歯は別の層) |

stock (各 job・各 workload) は S (certified)、X/P/I = 0、commit 非空。外れたら同 workload の変異は帰属不能。

## R5 — job 分割 (事前登録)

| job | 内容 | build | walltime |
|---|---|---|---|
| J1 | V17・V22・V35 (W1) + V18 (W2) + stock W1・W2 | 5 | 00:15:00 |
| J2 | V19・V23 (W3) + V20・V24 (W4) + stock W3・W4 | 5 | 00:15:00 |
| J3 | V33 (W4) + V21・V26 (W5) + stock W4・W5 | 4 | 00:15:00 |
| J4 | V27 (W6) + V31 (W7) + V32 (W8) + stock W6・W7・W8 | 4 | 00:15:00 |
| J5 | s8a (V08) | 2 | 00:15:00 |

計算ノードの使用見込み (job Elapse): 1 build + 数 run ≈ 40〜70 秒 (前回 s3・s5 = 2〜3 build で 134〜140 秒、s2 = 2 build・S2 規模の重い run で 209 秒) から、J1〜J4 各 200〜350 秒、J5 140〜240 秒、計 940〜1,640 秒 ≈ 0.26〜0.46 node 時間。開発の検査: 焦点走 (計算ノード) 3 回 × ≈ 60〜120 秒、変異 matrix 4 件 ≈ 0.1〜0.2、受入 2 回 ≈ 0.5 (1 回 ≈ 0.25 の実測単価) → ≈ 0.7〜0.8。合計 ≈ 1.0〜1.3 node 時間 < 2。walltime 上限でも J1〜J5 = 1.25 node 時間 + 検査 0.8 ≈ 2.05 なので、Elapse が見込みの 2 倍を超えた時点で止めて再見積りする。

## R6 — 変異 matrix (事前登録、段 6 で実走)

実装面 = patches 14 本、condition_meaning_gate.py の登録、test 3 本の表、patches/README.md。
- M1: `_DEFINE_SPECS` から新 macro 1 件 (例 IZANAGI_BREAK_READ_LOCK_CHECK) を削る → test_ccbench_spawn_sites の在庫照合と test_condition_meaning_gate の domain 固定が赤 (理由 = registry の欠落 1 つ)
- M2: `_CONDITIONAL_BRANCH_WITNESSES` から新 macro 1 件を削る → witness の patch 束縛 test が赤
- M3: patch 1 本の中の macro 名を 1 字変える (登録と不一致) → test_p3_s4_loop の未登録裸マクロ検査と在庫照合が赤
- M4: patch 1 本に同じ `#if <macro>` の site を 1 つ足す (site 数の虚偽) → branch 選択数 test が赤
期待 node は段 6 で実測の赤 node から確認し、帰属が 1 つの理由に絞れない node は記録する。

## R7 — 段 5 分割

- U-A (author): patch 6 本 (V17・V18・V19・V20・V21・V35)。所有 = `patches/broken-silo-{read-lock-check,no-write-tid-max,fixed-commit-version,published-version-mismatch,tail-commit-omission,no-read-tid-max}.patch`
- U-B (author): patch 8 本 (V22・V23・V24・V26・V27・V31・V32・V33)。所有 = `patches/broken-silo-{stale-read-payload,corrupt-write-payload,skip-node-validation,stale-read-own-write,repeat-update-buffer}.patch`、`patches/control-silo-{double-abort-backoff,reverse-write-order,conservative-abort}.patch`
- U-D (author、U-A・U-B と並列): 起動器 `launch_mutation_run.py` (unit worktree の `.t2847-launcher/` に書かせ、親が job dir へ退避)。所有 = `.t2847-launcher/`
- U-C (author、U-A・U-B の後): 登録 = `orchestrator/campaign/condition_meaning_gate.py`、`orchestrator/tests/test_condition_meaning_gate.py`、`orchestrator/tests/test_p3_s4_loop.py`、`orchestrator/tests/test_ccbench_spawn_sites.py`
- patches/README.md の節は親 (docs)。

## 計算の確認

見込み 1.0〜1.3 node 時間 (< 2) なので投入前の確認は不要 (D2212 項 4)。実測が見込みを大きく超えたら止めて確認する。
