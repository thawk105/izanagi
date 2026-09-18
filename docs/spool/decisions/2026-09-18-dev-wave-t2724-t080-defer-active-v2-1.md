---
schema: izanagi-spool-v1
ledger: decisions
authored: 2026-09-18
wave: dev-wave-t2724-t080-defer-active-v2
seq: 1
---

## {{D:t080-layer2-delegation-bound-to-live-validation}}. T-080 receipt の未知性層 2 は、同一 root・HEAD・世代で直前に成功した active v2 の full launch validation にだけ委譲し、receipt の他の検査と fail-closed は変えない

**決定 (ユーザー委任裁定 2026-09-18 = 択 A・設計 A-3 の実装形。裁定の記録は G wave の保存 commit `229982652` の fragment と裁定控え `rulings-inbox/2026-09-18-t2724-freeze-g1-chain-land-blocked-by-t080-receipt-live-scan.md`):**

1. **委譲の単位と署名。** `t080_freeze_migration._holdout_layer2_delegation(*, root, validation_head, launch_validated)` が委譲可否を決め、可なら full validation が保持する走査 report を返し、不可なら `None` を返す。`_verify_holdout_live_scan(root, holdout_doc, *, delegate_to=None, validation_head=None)` は report を得たときだけ zero-hit 判定 (`_assert_search_pass`) を課さず、凍結 doc との束縛 (rr80 / rr20 集合、`match_convention`、各 `candidate_id`、各 `unknownness_check.expressions`) は従来どおり課す。`verify_receipt(..., launch_validated=None)` と `static_gate_adapter(..., launch_validated=None)` は同じ helper を使う。refusal の prefix / reason (`holdout-freeze-verify: [holdout.unknownness_layer2] …`) は不変。
2. **発火条件 (全部が要る)。** (a) `type(launch_validated) is s8b_ratified_freeze.LaunchValidatedFreeze` (subclass・duck 型・`ReverifiedFreeze` は不可)、(b) `launch_validated.validation_root == Path(root).resolve()`、(c) `launch_validated.activation_head == validation_head == _capture_head(root)` かつ `launch_validated.ratified.activation_head` も同じ、(d) 同じ root の `resolve_active_generation(root)` が成功し、その HEAD・`generation_sha256`・`generation_number`・`generation_commit` が token の ratified と一致、(e) `launch_validated.search_digest == _enumeration_digest(root)`、(f) 凍結 doc 束縛が通る。1 つでも欠ければ委譲せず従来の live scan + zero-hit。skip flag・環境変数・引数による無条件免除は作らない。
3. **token は直前の validation のものに限り、campaign-start では再 launch も再走査もしない。** `LaunchValidatedFreeze` / `ReverifiedFreeze` に `validation_root` と `search_report` を追加し、`_launch_validate` の C2-4 完全一致・陽性対照・artifact 再捕捉の後に埋める。driver は receipt を launch 判定の**後**で 1 回解決し (v2 成功 = 直前の token 付き、loader / launch 失敗と v1 経路 = token なし)、campaign-start 前には同じ gate 時 token で委譲付きに再解決して `_t080_epoch_identity` の 4 要素を比較する (解決回数は成功経路で 2 回)。predicate は campaign-start 時点でも HEAD・active 世代・列挙集合 digest・凍結 doc 束縛を live で再照合するが、**列挙 digest は file 名集合の hash であり、gate 後に同名 file の内容を交換して hit を増減させる操作は捉えない。** これは launch 済みの同一 object だけを使い disk を再読しない既存契約 (E3b / A3-6、tracked test `test_v2_floor_disk_swap_after_launch_uses_same_validated_object` が固定) と同じ single-tenant 前提の残余であり、campaign-start で `launch_validate` や走査を再実行する形はこの契約と両立しない (走査は floor result の bytes を読む) ため採らない。gate 後に**新しい file** を足す操作は列挙 digest の不一致で通常走査へ戻り、zero-hit 失敗 → epoch 変化で拒否される。
4. **維持するもの。** receipt の履歴 (`inspect_receipt_history`)・静的検証 (artifact bytes / closure / derivation / ccbench gitlink)・epoch 束縛、`_make_gate_decision` の無条件集約、`_campaign_t080_value` の invalid 拒否、`clean_scan_digest` の official 床値起動証明 (D2077 step 7)、走査除外集合 (`EXCLUDED_PATHS`、`exempt_exact` の導出)、growth hold、G と入力 chain の bytes と履歴、人間 A / X の境界。v1 freeze path の `gate-check` は launch token を持たないので委譲しない (chain 有り木の v1 P3 は従来どおり拒否する)。
5. **到達範囲。** production では承認 A / pointer X (人間手番) の後にしか正例に到達しない。本決定時点の正例は合成 fixture (T-080 発行済み履歴 + G / A / X) の境界 test だけで、A / X 後の実測は無い。

**理由:**
- X1' (official 床値 run_dir) を含む木では、T-080 の live scan (zero-hit) と v2 の `launch_validate` (closure 由来 hit との完全一致、C2-4) が矛盾し、A / X を作っても oracle gate が refuse する (実測は G wave と本 wave の対照走: 焦点走 45 failed / 967 passed、P3 gate-check rc=2 refusals 4 件)。A-3 は矛盾する層 2 の責務だけを、承認・出所・occurrence・完全一致を検証済みの既存経路へ移し、他の検査を残す最小差分である。
- v2 の走査は v1 の prefix 除外を無効化し、検証済み hash と一致する active-chain と selector 証拠の exact path だけを免除する。免除 path はすべて v1 の除外 prefix 内にあるので、委譲は走査免除の拡大にならない (段 3 レンズ A-6)。
- 列挙 digest は名前集合の hash で内容交換を捉えない (段 3 レンズ A-1)。段 4 では campaign-start 前に validation を再実行する形を採ったが、段 6 の実測で既存 tracked test (E3b) と衝突し、走査だけの再検査も floor result を読むため同じ衝突を起こす (段 6 レビュー RA-1 / RB-2)。既存契約を優先し、鮮度は名前集合・HEAD・世代の再照合に限ると明記する。
- 初回 (launch 判定前) の receipt 解決を残す案は、履歴全検証を 1 回増やすだけで受理集合を安全側に変えない (段 3 の両レンズ)。

**却下した選択肢:**
- 自前で `search_repository(root)` を再走して束縛検査だけ行い zero-hit を C2-4 へ委ねる — 走査が 1 回増え、鮮度の問題 (A-1) も解決しない。
- 初回の委譲なし解決を残し launch 成功後に再解決する — 上記のとおり費用増だけ。
- `static_gate_adapter` へ driver から token を転送する — adapter は v1 freeze bytes が receipt と一致するときだけ発火し、その経路に launch token は存在しない (到達不能)。helper の共有だけに留める。
- skip flag / env / 引数による層 2 の無条件免除、走査除外の拡大、45 node の hold 登録、test の期待値緩和 — 規律 2 に反する (D2077、D2120 項 2 (d)、D532)。
- A-1 (承認済み世代の artifact から期待集合を導出) と A-2 (active v2 なら receipt を要求しない) — 裁定で却下済み (C2-4 の二重実装 / 置換範囲が広い)。

**研究状態への影響:** certified 選択・レポート・台帳の値は変えない。変わるのは「active v2 の full validation を直前に通した木で、receipt 層 2 の重複した zero-hit 判定を委譲する」の 1 形だけ。これにより chain + G を main に載せた後の oracle 実走 (W-5) が gate に到達できる前提が整う。
