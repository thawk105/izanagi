---
schema: izanagi-spool-v1
ledger: worklog
authored: 2026-09-18
wave: dev-wave-t2608-fold-verifier-detail
seq: 1
title: [T-2608] declared fold verifier の例外出力に sanitize 済み detail を保存し、旧 wave の実装を独立監査して回収した (コード + テスト + docs、branch codex/dev-wave-t2608-recovery、変異 = M0 SURVIVED・M1 diagnostic sensitivity pin・M2 KILLED)
---

## 本文

- ユーザー依頼は「[T-2608] (P2、entry 1487) tools/spool_fold.py の declared fold verifier が例外経路で str(exc) だけを残すため、
  git_state.py の ReasonCode.INVALID_RUN を投げる 22 箇所のどれが発火したか出力から判別できない (別 wave が rc=26 で踏み、git 所要
  3.3 秒 / 予算 30 秒で timeout 仮説を否定したが残る候補を絞れなかった)。是正は例外経路でも構造的拒否と同じ declared.detail を載せる
  ことだけ (拒否の判定・受理集合は変えない)。正例 1・負例 1 を変異登録。Codex author (D95)。着手直前の local main から fresh
  worktree。本題の detail 搭載だけ。仮想リスク向けの gate・検査・台帳・一般化の追加は scope 外」。
- **閉じた (実装 commit 08aa6cf99)。** 機序: `DevWavesError.__init__` (tools/dev_waves/schema.py) は `super().__init__(code.value)`
  なので `str(exc)` は `"invalid-run"` だけで、sanitize 済み `exc.detail` (`{"label": …, "kind": …}`) が `verify_fold_commit_identity`
  の `except BaseException` で捨てられていた。是正は同関数の例外経路 1 箇所: `exc` が `DevWavesError` なら message を
  `declared fold verifier が失敗: <code.value> <json.dumps(detail, sort_keys)>` にし、他の例外は従来の `{exc}` のまま。lazy import に
  `from tools.dev_waves.schema import DevWavesError` を足した (同じ try/except、ImportError は既存経路)。構造的拒否
  (`declared.ok == False`) の 2 行、`git_state.py` / `schema.py` / `redaction.py` は 1 byte も変えていない。
- 判別力の実測 (レビュー A・B が独立集計で一致): 22 発火元 (git_state.py 全体の数で、fold wrapper から全部に到達するわけではない)
  の (label, kind) は code 上 18 式 = 定数ペア 16 種 + 動的値 2 発火元 (`kind=operation`、`label=<label>`)。detail でも同値の
  残余は `git/timeout` ×3 (`_deadline` / `_left` / `_run` の TimeoutExpired)、`fold-diff/record` ×2、`fold-parents/record` ×2。
  `return_code` は `ERROR_DETAIL_ALLOWLIST` 外で落ちる。いずれも scope 外 (是正は detail 搭載だけ) として記録のみ。
- 正例 test `test_commit_identity_gate_exception_path_reports_declared_detail` (F649: stub なし): 健全な fold commit で
  `_assert_declared_fold` を通した後、HEAD を dangling symbolic ref にする。`verify_fold_commit_identity` の先行検査 (cat-file /
  diff-tree / rev-list / hash-object) は明示 SHA だけで HEAD を読まず、最初に HEAD を読むのが `verify_declared_fold_commit` の
  `_run(repo, "head")` なので rc=128 → `INVALID_RUN {"label": "git", "kind": "head", "return_code": 128}` → sanitize 後
  `{"kind":"head","label":"git"}` が message に載る。`__cause__` の型と `detail` も assert する (実 callee の名指し)。
  使い捨て repo で `rev-parse --verify HEAD` rc=128 を先に実測 (DW-G01)。
- 軽量版 + 段 6 レビュー 2 本 (DW-S06-A の U 節: 実装 wave は 2 本並列、fold verifier は land 経路の防壁)。段 2・3 は択が
  (P1) 表示形式 = JSON と (P2) 実 trigger = dangling HEAD の 2 点だけで brief で実測して確定したため省略。
  Codex author 1 本 (`gpt-6-astra` / medium、accepted、実装済み・未実走 = login guard が pytest 直呼びを拒否、実走は親)。
  レビュー A (正しさ境界・整合・実効性) / B (過剰・削除) は**両方 GO・must-fix 0**。採用 = 親資料の「16 類」の訂正 (上記) と
  単一理由性の説明の訂正 (M1 は cause を維持するので赤理由は message の detail 欠落だけ、M2 は `_transaction_raises` が先に
  AssertionError)。不採用 (記録) = `__cause__` assert 2 本の削除 (nit、実 callee の証拠として残す)、M2 の省略 (拒否継続の補助証拠
  として 1 走分で残す)、JSON → repr (reviewer 自身が変更を推奨せず)、レビュー 1 本化。実装 fix ゼロ → fix 子・焦点再レビューなし。
- 焦点走 (login、自走 harness): `test_spool_fold.py` 168 passed / 0 failed (新 test PASS)、consumer の meta-test
  `test_fold_gate_nodes_contract.py` 13 passed (新 test は `_copy_real_canonical_family` に到達せず登録簿の対象外)。
  `"declared fold verifier が失敗"` を pin する既存 test・docs は無し (git grep)。`tools/dev_wave_land.py` は message を
  `LandResult.reason` に格納するだけで parse しない (rc=26/27/30 は既存経路)。
- 変異 (login probe → dispatch 本走、container `.codex/worktrees/t2608-mutcontainer` = 08aa6cf99、spec sha256 `196bfb94…`):
  M0 = `json.dumps` の keyword 順入替 (等価、SURVIVED 期待)、M1 = 例外経路を `{exc}` に戻す (期待 node = 新 test、DW-M03/M08 により
  kill でなく **diagnostic sensitivity pin** の別枠、本題の証拠)、M2 = 例外経路を `return` に (fail-open、KILLED 期待、
  拒否継続の補助証拠)。login probe (自走 harness、注入 → 走 → `git checkout --` 復元 → clean 照合): M0 168 passed、M1 は新 test
  1 本だけ赤 (`declared fold verifier が失敗: invalid-run` で detail 無し)、M2 は新 test 1 本だけ赤 (`TransactionError を返さなかった`)。
  本走 (dispatch、15:35〜15:45 JST、collection 6 分 + baseline 38 秒 + 変異 3 走 各約 1 分): baseline PASSED (repo_head 08aa6cf99)、
  M0 SURVIVED、M1 KILLED (failed node = 新 test 1 本、diagnostic pin として kill 件数に加算しない)、M2 KILLED (failed node = 新 test
  1 本)、matching 3/3、MISMATCH 0。台帳 = `mutation-ledger.json` (insight)。
- 検査: `git diff --check`、message-file 検査 rc=0、全史 provenance 監査 rc=0 (11,429 件、新規違反なし。merge 後に再走)、
  `tools/check_docs.py`、`spool_fold.py --dry-run`、三軸語走査。旧受入の終端結果は下記の回収記録で補足する。
  記録の前に local main `ed4363204` を固定 SHA で取り込んだ (merge ad1f68a8a、実装面の競合なし)。
- 逐語・log・spec・変異台帳は `output/insights/2026-09-18/t2608-fold-verifier-detail/`。dev-wave 改善候補 0 (段 8 は無言通過)。
- 回収時に既存受入の終端を先に確認した。`acceptance-final-1.done` は70、wait receiptのsuccessはproducer終端だけ。
  1回目はF945 setup timeout 2件、2回目は起動器の `test_sigterm_ignoring_child_is_killed` が10秒timeoutで
  1 failed / 25133 passed / 69 skipped。旧受入を緑とせず、受入・landの重複起動をしなかった。
- 旧赤はfold検証経路に到達しない起動器testと確認し、同じ2b1015486で正規 `tools/run_tests.py` の単独再走を1回行った。
  rc=0、1 passed (23.74s)。非帰属・非再現と裁定した。新tipの受入を代替せず、旧F945署名による自動再投入scriptも流用しない。
- 着手時local main b2037abfaから専用Codex worktreeを作り、旧wave 2b1015486とunit 2975fcf6dを履歴ごと回収した。
  unitと旧統合08aa6cf99、同統合と旧tipのコード・テスト2fileは同一。新規実装修正は不要だった。
  独立read-only監査2本はGO / must-fix 0。規律2の拒否、実callee到達、sanitize後の現行producer値域、consumerを裏取りした。
  sanitizer一般のpath除去保証や、同値detailの原因識別を主張しない。欠けていたphaseチェックを回収mergeへ含めた。
- 回収資料は同insightの `recovery/`。旧tipの全史監査は11,460件、新規違反なし、既知違反56件
  (不可逆履歴53件・baseline後3件) を保持する。既知違反なしの緑とは報告しない。
- 回収tip ceb258ff7の正規焦点走 (spool_fold・fold_gate_nodes_contract・dev_wave_land) は548 passed / 1 skipped。
  変更test fileの正規単独走も168 passed (12.30s、6369.nqsv) で通過した。
  check_codex_agents、check_docs、spool dry-run、三軸語走査はrc=0。全史監査は11,465件、新規違反なし・既知56件。
  新規実装修正なしのため既存の変異証拠を保持し、記録commit後の受入で統合tipを検査する。

## 次の一手差分

### 完了

- [T-2608] declared fold verifier の例外経路に `code.value` + sanitize 済み `detail` (JSON) を載せた (実装 commit 08aa6cf99、
  正例 test 1 本、変異 M0 / M1 / M2 登録・実走)。残余 (同値 3 類、`return_code` の allowlist 落ち) は scope 外として記録のみ。
  remaining: none
  base: 6cf158da1747bd3ab33c94e085e7d8679e712f99ad714e6a4bcf303a4fe41f45
