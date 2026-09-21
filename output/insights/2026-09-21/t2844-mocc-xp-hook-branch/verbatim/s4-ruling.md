# 段 4 裁定 — dev-wave-t2844-mocc-xp-hook-branch (2026-09-21 21:09 JST 起草 = date 実測 21:09:41、親)

入力: brief `s1-brief.md`、段 2 plan `prev/s2-plan.md` (流用)、段 3 レンズ A `codex/s3-consult-A.md` (20:57:12〜21:03:44、rc=0、22,456 byte)、
レンズ B `codex/s3-consult-B2.md` (20:59:13〜21:04:44、rc=0、21,819 byte。初回 `s3-consult-B` は親の prompt の path 誤りで子が fail-closed 停止)。
裁定 inbox: wave 開始 (20:44) 以後の更新 0 件、local main は 36fb14a3d のまま。

## 1. 所見の裁定

| 所見 | real / refuted | 採否 | 扱い |
|---|---|---|---|
| A-M1 旧 14 check の all_pass は負例の単一理由性を示さない | real | 採用 (縮小形) | 新 check key は足さない。候補 JSON の各 run の公開 record に `other_integrity_clean` を載せ (値だけ、判定に使わない)、材料の主張は「所定の X/P が発火し verdict が indeterminate」に限る。単一理由性は、JSON の直交違反数 (X 負例の P 件数・P 負例の X 件数) と `other_integrity_clean` が示す範囲でだけ書く |
| A-M2 正規化 objdump + D297 は `.text` bytes 一致の代替ではない | real (brief の説明の誤り) | 説明の訂正だけ採用。bytes 検査の追加は不採用 | brief (P2) の「`.text` は既存の正規化 objdump 比較 + D297 が担う」を撤回し「TRACE=0 の証拠は D297 (正本) + 既存 `_trace0_record` の nm / strings / 正規化逆アセンブル一致 (補助)。`.text` bytes 一致は主張しない」に改める。**やらない理由の最も強い反論 (レンズ A):** D1687 は補助 witness として `.text` の一致を compute JSON に記録すると書き、T-2294 は bytes 一致を login の別実測で支えていたので、候補には bytes 証拠が無くなる。**それでも採らない理由:** T-2294 の compute JSON 自体が正規化逆アセンブル一致を D1687 の compute 側 witness として記録した先例であり、D1603 の材料 (2) は D297 の結果である。rip 相対の変位は正規化後も operand に残るので `.rodata` のずれは差として出る。レンズ B も追加必須を refuted。依頼の「本題の実装だけ」に従い、bytes 一致は材料に書かない (主張の縮小で閉じる) |
| A-S1 / B-S3 目標 blob・可搬 patch・実 C の内容束縛を残す | real | 採用 | driver が実走前に「C の blob = BASE + 候補 patch の再構成 blob」を照合し、不一致なら build 前に停止 (fail-closed)。JSON に C の parent 列・tree・raw diff・両 blob を記録し、consumer test が親の固定期待値と BASE + 候補 patch の再構成から独立に照合する。親は C 作成時に目標 `e393efbf…` と照合する |
| A-S2 / B-S2 条件表 13 の「旧 JSON に全入力 field が実在」は誤り | real | 採用 (記録の訂正) | `_other_integrity_clean` と touch set の生値は driver 内の実測入力で、公開 JSON には判定と一部だけが残る。brief 条件表 13 を訂正する (本裁定が訂正の正本) |
| A-S3 同サイズ pointer 置換・多重度変更の対照 | real | 採用 (静的に閉じる) | 候補 source が旧計装から指定 3 箇所だけ違う (容器は `unordered_multiset`、`unordered_set` ではない) ことを source 契約 test で byte 一致で固定する。動的証拠は perm-erase の size 違反までと材料に明記する。新 runtime 走は足さない |
| A-S4 / B-S5 変異案の修正 | real | 採用 | §4 の事前登録に反映 (hot・21 key・`.text` bytes の変異は登録しない。併発赤は記録し、hash 不一致だけを意味検査の kill に数えない) |
| A-N1 P 抑止変異の具体化 | real | 採用 | §4 に具体的な置換として登録 |
| B-M1 段 6 で C の message を直したときの証拠更新順序 | real | 採用 | §3 の手順 |
| B-S1 21 key → 縮小、hot 2 走・`.text` bytes の削除 | real | 採用 (さらに縮小) | 候補固有の check key は 0 本。識別の 2 条件 (親 = BASE ちょうど 1 本、raw diff = transaction.cc 1 件・通常 file・mode 不変) と blob 束縛は実走前の fail-closed 停止条件にし、観測値を JSON に記録する。check は旧 `compute_checks()` を無変更で使い 14 key のまま |
| B-S4 波及表に policy epoch の集合外 consumer を具体名で補う | real | 採用 (記録) | insight の波及表に t2304 §0〜§3 の具体名を併記し、旧証拠の保持と新 main での実行可能性を分ける |
| B-N1 plan の行番号 | real | 採用 (記録) | 波及表は path と定数名で書き、文書間の行番号参照をしない |
| レンズ A の P9 (生死確認を driver 前に) / レンズ B の P9 支持 | real (価値はある) | 変更して採用 | login の `cmake --build` は guard が重い処理として拒否し、build だけの既存 CLI も無い。独立の build 経路は新設せず、**compute 本走の最初の build (TRACE=1 stock) を生死確認とする**。失敗したら author A の patch を直して C を作り直す (§3 の OID 変更手順)。**やらない理由の最も強い反論:** driver 完成後に build 失敗が出ると C・固定期待値・consumer をまとめて作り直す。**それでも採る理由:** 変更は旧計装 (T-2294 で `-Werror` build 済み) からの 3 行で、`std::unordered_multiset<const void*>` の `insert` / `size` / `operator==` は標準で成立する。作り直しは C の再 commit (1 分) と固定期待値の fix 子 1 本で済む |
| その他 (refuted / 不成立) | refuted | — | hash 衝突による P の偽緑、`<unordered_set>` 不足、certified ⇒ gate 真の推論の誤り、旧 14 key の恒真化、hot 省略による偽 certified 経路、候補 mode の pin 前進先取り、C 必須 test、登録簿の追随 — いずれも両レンズとも不成立 |

## 2. プラン v2 (plan §1〜§9 をこの形に縮小して確定)

**(P1) 候補:** plan §1 どおり。`patches/instr-mocc-lock-coverage-pin-candidate.patch` (BASE 基準、transaction.cc だけ、+64 行 / −0 行)。BASE への適用結果 = blob `e393efbfd5fad7bbe05117b43669ccc0f44abb6a`。
位置付け = branch C の可搬な再現資料。producer に重ねる第二の正本にせず、C checkout に重ねない。旧 `instr-mocc-lock-coverage.patch` は旧命題 (BASE + patch) の証拠として bytes 不変。

**(P2) driver 候補 mode (`orchestrator/campaign/s3_mocc_lock_coverage.py`):**
- `--candidate-oid <40 桁小文字 hex>` を足す。無指定の legacy mode は argv・既定値・挙動・JSON schema/path を 1 byte も変えない (`PIN`・`CHECK_KEYS`・`INSTRUMENTATION_PATCH`・既存 helper の signature も不変)。
- 候補 mode の出力は既定 `output/env/pegasus/calibration/s3_mocc_xp_pin_candidate.json`、schema `s3-mocc-xp-pin-candidate/v1`。旧 JSON 3 本 (`s3_mocc_lock_coverage.json`、`s3_mocc_mutation_proof.json`、`s3_mocc_template_proof.json`) の path へは書かない (指定されたら拒否)。
- **実走前の fail-closed 停止 (build 前):** (a) `rev-parse --verify <oid>^{commit}` が同じ 40 hex、(b) `rev-list --parents -n 1` の親列 = `[PIN]` ちょうど、(c) `diff-tree -r --raw --no-renames PIN <oid>` = 1 件だけで、status `M`、mode `100644 → 100644`、path `cc/mocc/transaction.cc`、(d) `checkout(PIN)` に候補 patch を厳密適用した source の blob = (c) の新 blob。git は既存 `_run_checked` を通す (新しい subprocess site を作らない)。判定は git 出力を受け取る純関数にし、git を呼ぶ薄い wrapper と分ける。
- **実走行列 = 旧 6 走と同じ:** stock_single / stock_high = `checkout(C)` + `assert_pinned_clean(source, C)`、patch なし、TRACE=1。lockskip (single/high)・perm_erase_single・early_unlock_single = `checkout(C)` + 各 broken patch だけ (`_apply_owned_patch`)、既存 macro と condition gate。verifier の root は各 build の source。
- **TRACE=0:** BASE (`checkout(PIN)`、patch なし) と C (`checkout(C)`、patch なし) を等長の build dir 名で build し既存 `_trace0_record` で比較。dir 名は旧 test の固定 (`scratch / "trace0-base"` と `scratch / "trace0-inst"` が source 中に各 1 回、`base-trace0` / `patched-trace0` 不在) に抵触しない等長の別名 (例 `trace0-pin0` / `trace0-cand`)。
- **check:** 旧 `compute_checks()` を無変更で呼ぶ (14 key、`CHECK_KEYS`)。`patch_relatives` = (候補 patch、lockskip、permutation-erase、early-unlock)、touch set は候補 patch の再構成時と各負例の適用時の実測。
- **JSON (候補 mode):** schema、env_tag、site、`ccbench_commit` = C、`base_commit` = PIN、`candidate` = {oid, parents, tree, raw_diff, base_blob, candidate_blob, reconstructed_blob, candidate_source_sha256, patch {path, sha256}}、genome、clocks_per_us、toolchain、policy {path, sha256}、patches (候補 + 負例 3 本の path / sha256)、workloads、condition_gates、`diagnostic_build_admission` (既存 `non_admissible_materializer` の `_build_variant`)、trace0、runs (公開 record + `other_integrity_clean`)、checks、all_pass。
- materializer / spawn inventory / build authority / condition gate の登録簿は変えない (新しい `"--build"` 関数・subprocess site・macro を作らない)。

**(P3)/(P4)** brief どおり。C の trailer は §3。

**(P5) test (`orchestrator/tests/test_mocc_xp_pin_candidate.py` 新設、旧 test file の bytes は不変):**
1. `test_candidate_source_contract` — BASE + 候補 patch が、BASE + 旧計装の適用結果から指定 3 箇所だけ変えた source と byte 一致。include 行列が BASE と同一。`std::unordered_multiset<const void*>` が 2 箇所、`std::multiset` と `#include <set>` が 0。`include/trace.hh` (BASE) が `<unordered_set>` を include。既存の X/P 構造 helper を候補 source にも当てる。候補 source の blob / sha256 が固定値。実走 3 本の broken patch が候補 source に厳密適用で当たる。
2. `test_candidate_trace0_logical_rows` — 既存 helper で BASE と候補の TRACE=0 論理行列が一致。
3. `test_candidate_identity_checks` — 識別の純関数が正例 (親 `[PIN]`、1 件の M・100644→100644・transaction.cc、blob 一致) を受理し、孫 (親 ≠ PIN)・複数親・追加 path・mode 変更・status A/D・blob 不一致を各 1 条件だけ壊した入力で拒否。
4. `test_candidate_mode_source_routing` — 重い外部境界 (依存物準備・build・実行・verifier の subprocess) だけを差し替え、候補 mode の配線を検査: 正例と TRACE=0 候補側は C の checkout で計装 patch なし、負例は C + 対応 broken patch 1 本だけ、TRACE=0 比較相手は PIN、verifier root は build した source、旧 JSON path の拒否、blob 不一致で build 前に停止。識別・配線のロジック自体は差し替えない (実体を名指す)。
5. `test_candidate_json_is_bound` — commit した候補 JSON の consumer: schema、all_pass、checks = `CHECK_KEYS` 全真、`ccbench_commit` / `candidate.oid` / tree / 親列 / raw diff / 両 blob が親の固定期待値と一致、test 内で BASE + 候補 patch から再計算した blob とも一致、patch の sha256 が現 file と一致、6 run 名、各 run の `other_integrity_clean` の存在、NON_ADMISSIBLE、toolchain。consumer 関数に 1 文字改変の JSON 写しを渡すと拒否する対照を含む。
self-run harness は旧 test file と同じ `_run()` 形 (`test_plain_runner_coverage.py` の要求)。

**(P6)** I 面は不足として記録。**(P7)** brief どおり (job dir `run-d297.sh`)。負例は rc=1 に加えて stderr の「include 行文字列（順序込み）が不一致」を確認する。**(P8)** 45 件 = 追随 15・据置 29・衝突 1 (新規 2 件は据置)、集合外依存を具体名で併記。

## 3. C の作成・trailer・OID 変更時の手順

- trailer (実寄与どおり、`docs/ai-provenance.md`): `role=author` (codex gpt-6-astra medium、author A)、`role=reviewer` (codex gpt-6-astra medium = 段 3 レンズ A が候補の 3 行差分と意味論を独立に点検し採否に寄与。段 6 のレビューも同一構成なので同じ 1 行で覆う)、`role=manager` (claude claude-opus-5-1m xhigh)。
- 順序: author A → 親が blob を目標と照合 → `mk-C-commit.sh` で C を commit・bundle・verify → C の OID / tree / blob を author B に渡す → B → 統合 commit → compute 本走 (C) → D297 3 本 + 負例 (C) → 段 6。
- **段 6 で C の message / 内容を直す場合:** 旧 OID の証拠 (log・bundle) を job dir の `superseded-<旧OID先頭8桁>/` に保持し、最終 C で D297 と識別を取り直し、**compute も最終 C で再走**し、B の固定期待値を fix 子で更新し、bundle・fetch を最終 OID に揃える。JSON の `ccbench_commit` だけを書き換えることはしない。
- 保全: 最終 C → 自己完結 bundle の verify / sha256 → 主 checkout の submodule git dir へ非 force で branch を fetch → ref / OID 照合 → wave 撤去。fetch は段 6 で C が確定した後、wave worktree の撤去より前に行う。

## 4. 変異の事前登録 (実装前。置換の逐語 anchor と期待 node は実装後に login self-run で確定し、段 6 の本走前に固定する)

| id | 対象 | 変異の意図 | 期待 | 主 killer 見込み |
|---|---|---|---|---|
| MP1 | 候補 patch | 宣言 1 箇所の `unordered_multiset` → `unordered_set` | KILLED | source_contract (併発: json_is_bound の blob) |
| MP2 | 候補 patch | `+#line 17` → `+#line 18` | KILLED | trace0_logical_rows (併発: source_contract / blob) |
| MP3 | 候補 patch | P の比較 `if (post != pre)` 相当を `if (false)` に | KILLED | source_contract (X/P 構造 helper) |
| MP4 | 候補 patch | X 入口検査の条件を恒偽に | KILLED | source_contract (X/P 構造 helper) |
| MD1 | driver | 親列検査を「PIN を含む」に緩める | KILLED | identity_checks (複数親の拒否) |
| MD2 | driver | raw diff 検査を「transaction.cc を含む」に緩める | KILLED | identity_checks (追加 path の拒否) |
| MD3 | driver | mode 検査を外す | KILLED | identity_checks (mode 変更の拒否) |
| MD4 | driver | blob 束縛の停止を外す | KILLED | identity_checks / source_routing (blob 不一致) |
| MD5 | driver | 候補 mode の正例で旧計装 patch を C に重ねる | KILLED | source_routing |
| MD6 | driver | 候補 mode の負例で broken patch を当てない | KILLED | source_routing |
| MD7 | driver | TRACE=0 の比較相手を PIN でなく C にする | KILLED | source_routing |
| MD8 | driver | verifier root を build した source 以外にする | KILLED | source_routing |
| MD9 | driver | 旧 JSON path の拒否を外す | KILLED | source_routing |
| MJ1 | 候補 JSON | `ccbench_commit` を 1 文字変える | KILLED | json_is_bound |
| MJ2 | 候補 JSON | `candidate.reconstructed_blob` を 1 文字変える | KILLED | json_is_bound |

hot・21 key・`.text` bytes の変異は登録しない (実装しない検査)。各変異の失敗 node 集合は全部記録し、主 killer の単独失敗を意味上の kill として別記する (DW-M03 / M08)。

## 5. 分割と所有

| 単位 | 所有 path | 入力 |
|---|---|---|
| author A (worktree `.codex/worktrees/t2844-author-a`) | `patches/instr-mocc-lock-coverage-pin-candidate.patch` のみ | 本裁定 §2 (P1)、BASE 逐語、旧計装 patch |
| 親 | C の commit・branch・bundle・fetch、compute 本走、D297、候補 JSON の commit、insight・fragment | — |
| author B (worktree `.codex/worktrees/t2844-author-b`、A の patch を統合した wave HEAD から) | `orchestrator/campaign/s3_mocc_lock_coverage.py`、`orchestrator/tests/test_mocc_xp_pin_candidate.py` (新設)、`patches/README.md` (候補 patch の節) | 本裁定 §2、C の OID / tree / blob / parent |

規模上限: author B の差分は driver +250 行・test +500 行程度を目安とし、大きく超えたら理由を報告させる。
