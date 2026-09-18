# [T-2608] spool_fold の declared fold verifier 例外経路に code と sanitize 済み detail を載せた — INVALID_RUN 22 発火元の (label, kind) を fold の失敗出力から読めるようにする

`authority: none`
`default_effect: no-state-change`

2026-09-18。wave `dev-wave-t2608-fold-verifier-detail`、branch `worktree-dev-wave-t2608-fold-verifier-detail`。起点 local main
`c8e8dc06f33891aa2fd6345063b30ca11b52fe6d` (14:54 JST)、実装 commit `08aa6cf99`、記録前に local main
`ed4363204005c0c752730c2c36357e371744f330` を固定 SHA で取り込み (merge `ad1f68a8a`、15:36 JST、実装面の競合なし)。
可変状態の正本は worklog 末尾と現行 phase doc であり、本書ではない。

## 依頼と答え

依頼は「[T-2608] (P2、entry 1487) tools/spool_fold.py の declared fold verifier が例外経路で str(exc) だけを残すため、git_state.py の
ReasonCode.INVALID_RUN を投げる 22 箇所のどれが発火したか出力から判別できない (別 wave が rc=26 で踏み、git 所要 3.3 秒 / 予算 30 秒で
timeout 仮説を否定したが残る候補を絞れなかった)。是正は例外経路でも構造的拒否と同じ declared.detail を載せることだけ (拒否の判定・
受理集合は変えない)。正例 1・負例 1 を変異登録。Codex author (D95)。着手直前の local main から fresh worktree。本題の detail 搭載だけ。
仮想リスク向けの gate・検査・台帳・一般化の追加は scope 外」。

**答え: 閉じた。** `tools/spool_fold.py` の `verify_fold_commit_identity` の例外経路 1 箇所 (+6 行) と正例 test 1 本 (+20 行)。
拒否の判定 (TransactionError を投げる入力集合)・構造的拒否の文面・`from exc`・`git_state.py` / `schema.py` / `redaction.py` は不変。

## 機序 (現物、main c8e8dc06f = 実装後も同じ)

- `DevWavesError.__init__` (`tools/dev_waves/schema.py:101-106`) は `self.detail = sanitize_detail(detail)` を持つが
  `super().__init__(code.value)` なので `str(exc)` は `"invalid-run"` だけ。
- `tools/spool_fold.py` の例外経路 (実装前 3473-3474 行) は `raise TransactionError(f"declared fold verifier が失敗: {exc}")` で
  `exc.detail` を捨てていた。構造的拒否 (3475-3476 行) は `_fold_fail("wave-tip")` 等の短 token を `declared.detail` に載せる。
- `sanitize_detail` (`tools/dev_waves/redaction.py:155-168`) は Mapping を `ERROR_DETAIL_ALLOWLIST` (14 key) で redact する。
  `return_code` は allowlist 外なので落ちる。

## 是正 (差分は実装 commit 08aa6cf99 そのもの = `git show 08aa6cf99`。patch の写しは実装面と判定されるので insight に置かない)

- lazy import (既存の try/except 内) に `from tools.dev_waves.schema import DevWavesError` を追加。
- 例外経路: `exc` が `DevWavesError` なら
  `f"declared fold verifier が失敗: {exc.code.value} {json.dumps(exc.detail, ensure_ascii=False, sort_keys=True, separators=(',', ':'))}"`、
  それ以外は従来の `f"declared fold verifier が失敗: {exc}"`。どちらも `from exc`。
- 表示形式を JSON にした理由 (裁定 P1): 同 file の stderr JSON (`"error": str(exc)`) と同規約、key 順が決定的、allowlist のどの組でも
  表せる。外側の `json.dumps` が内側の引用符をエスケープするので stderr JSON は壊れない (レビュー A 検証)。

## 判別力の実測 (レビュー A・B が AST / grep で独立集計、親の数え直しと一致)

| 集計対象 | 値 |
|---|---:|
| `ReasonCode.INVALID_RUN` 生成箇所 (git_state.py 全体) | 22 |
| label / kind が両方リテラルの箇所 | 20 |
| その定数ペアの種類 | 16 |
| 動的ペアの生成箇所 (`("git", operation)` :209、`(label, "sha")` :227) | 2 |
| 動的式を別テンプレートとして含めた種類 | 18 |
| `git/timeout` (`_deadline` :57、`_left` :64、`_run` TimeoutExpired :205) | 3 |
| `fold-diff/record` (:783、:796) | 2 |
| `fold-parents/record` (:843、:854) | 2 |

親は当初「16 類」と書いたが、定数ペアだけの数で動的 2 発火元を含まない誤りだった (レビュー A・B の should、採用して訂正)。
22 箇所は file 全体の数で、fold wrapper から全部に到達するわけではない。同値の残余 3 類と `return_code` の allowlist 落ちは
依頼の scope 外 (是正は detail 搭載だけ) として記録のみ。

## 正例 test (`test_commit_identity_gate_exception_path_reports_declared_detail`)

- 健全な fold commit で `_assert_declared_fold` を通した後、`git symbolic-ref HEAD refs/heads/t2608-does-not-exist` で HEAD を
  dangling にし、`verify_fold_commit_identity` を呼ぶ。先行検査 (cat-file / diff-tree / rev-list / hash-object) は明示 SHA だけで
  HEAD を読まず、最初に HEAD を読むのが `verify_declared_fold_commit` の `_run(repo, "head")` (`git_state.py:1066`) →
  `git rev-parse --verify HEAD` rc=128 → `INVALID_RUN {"label": "git", "kind": "head", "return_code": 128}` → sanitize 後
  `{"kind":"head","label":"git"}`。message にこれが載ること、`__cause__` が `DevWavesError` で `detail` が同じ dict であることを assert。
- stub・monkeypatch なし (F649)。使い捨て repo で `rev-parse --verify HEAD` rc=128 / 明示 SHA の `cat-file` 成功を先に実測 (DW-G01)。
- 新 test は `_copy_real_canonical_family` に到達しないので `test_fold_gate_nodes_contract.py` の登録簿の対象外 (meta-test 13 passed で確認)。

## 段の記録

- 段 1 brief: verbatim/s4-ruling.md の前提 (HANDOFF の brief は job dir、要点は worklog)。(P1) JSON 形式、(P2) dangling HEAD。
- 段 2・3: 省略 (軽量版、択は P1/P2 の 2 点だけで brief で実測して確定)。
- 段 4 裁定: verbatim/s4-ruling.md (plan v2、変異登録 M0/M1/M2、15:12 の追記で DW-M03/M08 の分類に揃えた)。
- 段 5 Codex author (`gpt-6-astra` / medium、accepted): verbatim/s5-author.md。実装済み・未実走 (login guard が pytest 直呼びを拒否)。
  親が login の自走 harness で実走: focus-spool_fold-1.log (168 passed / 0 failed)、focus-fold_gate_nodes-1.log (13 passed)。
- 段 6 レビュー: A (正しさ境界・整合・実効性) = verbatim/s6-reviewA.md、B (過剰・削除) = verbatim/s6-reviewB.md。**両方 GO、must-fix 0。**
  採用 = 「16 類」の訂正、単一理由性の説明の訂正 (M1 は cause を維持するので赤理由は message の detail 欠落だけ)。
  不採用 (記録) = `__cause__` assert 2 本の削除 (nit)、M2 の省略、JSON → repr、レビュー 1 本化。実装 fix ゼロ。
- 変異 (spec = mutation-spec-final.json、sha256 `196bfb94962ace8c8091c0be1437d724e5c357f343db4e7096a46a5760a31458`):
  - M0 `m0-equivalent-json-kwarg-order` (positive、等価、SURVIVED 期待)
  - M1 `m1-diagnostic-pin-revert-to-str-exc` (negative、期待 node = 新 test。DW-M03/M08 により kill でなく diagnostic sensitivity pin の別枠 = 本題の証拠)
  - M2 `m2-fail-open-return-instead-of-raise` (negative、期待 node = 新 test、KILLED = 拒否継続の補助証拠)
  - login probe (自走 harness、注入 → 走 → `git checkout --` 復元 → clean 照合): probe-m0.log 168 passed、probe-m1.log は新 test 1 本だけ
    赤 (`declared fold verifier が失敗: invalid-run`、detail 無し)、probe-m2.log は新 test 1 本だけ赤 (`TransactionError を返さなかった`)。
  - 本走 (container `.codex/worktrees/t2608-mutcontainer` = 08aa6cf99、`--runner-mode dispatch --force-dispatch`、runner file =
    test_spool_fold.py + test_fold_gate_nodes_contract.py、15:35〜15:45 JST): baseline PASSED (38 秒、repo_head 08aa6cf99)、
    M0 SURVIVED、M1 KILLED (failed node = 新 test 1 本、diagnostic pin として kill 件数に加算しない)、M2 KILLED (failed node = 新 test
    1 本)、matching 3/3、MISMATCH 0。台帳 = mutation-ledger.json、attempt sidecar = mutation-attempt-1.json (collection 6 分、
    baseline 38 秒、変異 3 走 各約 1 分)。
- 検査: `git diff --check`、message-file 検査 rc=0、全史 provenance 監査 rc=0 (実装 commit 後 11,429 件、merge 後 11,451 件、新規違反なし)。

## 回収時の独立監査 (2026-09-18)

- 旧受入は `recovery/acceptance-final-1.done` のrc=70で終端。wait receiptのsuccessを受入緑とは扱わない。
  2回目は起動器testの10秒timeoutで1 failed / 25133 passed / 69 skipped。旧tip単独再走は
  `recovery/old-red-single.log` の1 passed。差分到達不能と非再現を確認し、新tipの受入とは区別する。
- `recovery/review-A.md` / `review-B.md` は独立read-only監査の逐語。両方GO・must-fix 0で実装修正なし。
  現行producerの固定語・operation・labelを追跡した範囲で生pathや子出力の追加はなく、拒否動作は不変。
- 既存変異をM0等価生存、M1診断感度、M2 fail-open検出として回収。実装2fileとproducer3fileは
  実走時08aa6cf99と旧tipで同一。再実走やland全経路の実証とは呼ばない。
- 着手時main b2037abfaから作った専用Codex worktreeへ、旧waveとunitを履歴ごと回収。
  不足していたphaseチェックは回収mergeに含めた。コード・テストは既存Codex authorの内容を保持する。

## land拒否の修復と自己改善

- 初回の `recovery/acceptance-1.json` は7a144e023に対するchild-green。しかし `recovery/land-1.json` は
  rc26 / landed-fold-owned-pathで拒否し、mainはb2037abfaのままだった。
- 原因は親が後付けした履歴保全merge ceb258ff7。両親がtrusted cutoffの祖先でなく、第二親との差分に
  FOLDED.mdのMが現れた。累積tree差分ゼロを根拠に採用したのは既存F266の再発である。
- 続いて「次wave禁止」を理由に修復せず終了したのはF946の再発。ユーザーの完遂・自己改善指示に従い継続した。
- 復旧merge 9c0300993の親はb2037abfa / 2b1015486 / 2975fcf6d。既存F266の一括mergeを使い、失敗履歴を取り込まない。
  本体2fileは旧受入tipと同一。自己改善063a743d6はDW-STOPとDW-O23の既存義務を明確化し、両Fへ再発を記録した。
- `recovery/v2-final-review.md` は固定tip063a743d6の独立静的レビュー。全7commitの選択親差分に拒否署名なし、
  安全義務保存、GO / must-fix 0。実走やland成功の代替ではない。
- 初回の修復相談は見出し形式でF43未受理、次の起動は未commit authority差で拒否された。どちらも緑と数えず、
  文書をcommitした後の上記レビューで独立再検証した。
- 旧逐語5fileは末尾空白だけを正規化。`recovery/whitespace-restoration.json` の行suffixと末尾改行有無で復元し、
  5fileとも原文hash・byte数一致を確認した。可視文字は変えていない。

## 残余 (scope 外、次の一手に起票しない)

- 同値 3 類 (`git/timeout` ×3、`fold-diff/record` ×2、`fold-parents/record` ×2) は detail でも区別できない。
- `return_code` は allowlist 外で落ちる (`git/<operation>` の rc は読めない)。
- 非 DevWavesError の例外は従来どおり `{exc}` 表示。
- 同型の `except ... as exc: raise TransactionError(f"...: {exc}")` は spool_fold.py 内に他にもあるが、独立 2 例の実害が無いので触らない (DW-G03)。
