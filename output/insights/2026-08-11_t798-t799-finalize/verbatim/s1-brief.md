# 段 1 brief — [T-798]/[T-799]/[T-820]/[T-821] 単一 finalize protocol

wave: `dev-wave-t798-t799-finalize` / branch `worktree-dev-wave-t798-t799-finalize`
worktree: `/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t798-t799-finalize`
設計入力: `output/insights/2026-08-11_t798-t799-fold-window/` (worklog 431)

## 確定済みユーザー裁定 (実装方向まで確定 — 非同値な択一へ戻さない)

- **[T-798] = 統合案** (worklog 433 / inbox §103): journal 新設 (a) と削除後ろ倒し (b) を別案にせず、
  既存 transaction state へ **phase と起源**を持たせ、**state 削除を postcondition 後**へ移し、
  **finalize は land だけが行う単一 protocol** にする。`validate_spool_tree` は phase から受理形を決め、
  受理表を fail-closed に固定する。
- **[T-799] = (a)** (同上): state へ land 起源・base・tested tip・rollback ref **+ plan 入力 closure の
  hash** を束縛する。束縛値は**申告値でなく観測値**とし、**`transaction_id` にも含める**。
  mutation 前に HEAD と照合する。(b) standalone apply 拒否は代替 lock-aware finalize command と
  セットのときのみ = **本 wave では採らない**。schema は**厳格側を既定**。
- **[T-820] = (a)** (inbox §105、未 land): `_load_rotate_limit` の `except Exception` を
  `BaseException` へ広げ `SpoolValidationError` へ畳む。
- **[T-821] = (a)** (inbox §105、未 land): `FOLDED.md` receipt へ **base / tested tip / wave ref** を足す。
- **4 件を 1 wave に束ねる** (§103 + §105、いずれも同じ state / receipt schema を触る)。

## scope

- **scope 内:** `tools/spool_fold.py`、`tools/dev_wave_land.py`、`orchestrator/tests/test_spool_fold.py`、
  `orchestrator/tests/test_dev_wave_land.py`、必要なら `docs/spool/README.md` の契約記述。
- **scope 外 (real でも実装しない):** [T-799] (b) の standalone 封鎖、[T-800]/[T-801] の rollback 細部、
  レンズ B の commit-first 方式、旧 v1 in-flight state の migration code (親推奨は (i) 拒否 = 追加 code 無し。
  **裁定パッケージ Q2-b は未裁定なので、v1 拒否は「厳格側を既定」の裁定から導かれる最小実装に留める**)。

## 段 1 前提実測 (裁定パッケージ Q6 の親推奨 (1)(6) を実走)

- **(1) post-commit crash (新規実測、`probe/probe_post_commit_crash.py`)。** 本番 land は
  `core.hooksPath=/dev/null` で hook を無効化するため、main ref を tight loop で監視する watcher から
  fold commit 直後に SIGKILL した (rc=-9)。**現行コードの残骸は完全に健全だった** —
  main HEAD = fold commit (親 = tested tip)、tree clean、canonical も fragment GC も **commit 済み**、
  state 無し。同 argv の land 再投入は rc=10 `stale-main`。
  → **現行の窓は commit で閉じている。** 削除を postcondition 後へ移すと
  「commit 済み・state 残存」という**新しい相を作る**ので、finalize 経路は必須の構成要素である
  (裁定パッケージの (b) 単独評価と一致)。**なお postcondition (`verify_declared_fold_commit` を含む) は
  1 つも走っていない** — 形の検証を受けていない fold commit が main に載りうる。
- **(6) 実 checker の archive 跨ぎ T 重複 (新規実測)。** `docs/worklog.md` 末尾へ archive 専有 ID
  `[T-013]` の新規項を実編集で 1 行足し、`python3 tools/check_docs.py` を実走したところ
  **rc=0「違反なし」**。復元後 sha256 一致・tree clean を確認済み。
  → 静的確認どおり**下流で止まらない**。[T-799] は帰属でなく**値**の問題である。

## 不変条件 (破ったら赤)

1. **受理集合を広げない (規律 2)。** state 存在時の `_discover` 受理は「全 target が after かつ
   全 GC 削除済み」の 1 形だけ。部分状態・第三状態・schema 不正・version 不一致は従来どおり拒否する。
   「state があれば内容を見て問題なければ通す」形にしない。
2. **fail-open にしない。** 新 field は省略可能として読まない。旧 v1 state は拒否する。
3. **束縛値は観測値。** land が渡す base / tested tip / wave ref は、束縛前に git で実体と照合する。
   照合できない値は束縛しない。
4. **finalize は land だけ。** standalone CLI は apply までで、state を消さない。
5. `verify_declared_fold_commit` の fold commit path 形状 (`_FOLD_MODIFIED_EXACT`) を変えない。
6. 段 5 の実装子は docs を編集せず commit しない。

## 成果物影響 (DW-G05)

実装しなければ、(i) fold の窓に落ちた 1 回について canonical 3 台帳・`FOLDED.md`・fragment GC が
反映済みで commit の無い tree が残り、正規復旧 CLI が rc=0 `noop` を返すため運用者が気づけない
(certified 選択の proof chain が main 履歴へ帰属しない)、(ii) 誤った採番入力の上で resume して
**重複 T 番号**を台帳に作れ、実 checker が rc=0 で通す (台帳 ID 保存則の破れ)、
(iii) fold commit がどの main 状態に対して採番されたかを台帳から言えない。

## 親の provisional 裁定 (攻撃対象)

- **(P1) 起源は plan 時に束縛する。** `plan_fold(repo, *, fold_date, origin=None)` とし、`origin`
  省略時は plan 対象 repo の HEAD / symbolic ref を自ら観測して `kind="standalone"` を作る。
  land は `kind="land"` + `base=locked_main` + `tested_tip` + `wave_ref` を渡し、plan_fold 側が
  git で実体照合してから束縛する。**理由: `FOLDED.md` receipt ([T-821]) の bytes は plan 時に
  確定する必要があり、land はその時点で 3 値をすべて握っている** (`land()` の plan_fold 呼出直前)。
  既存 103 箇所の `plan_fold` 呼出を変えずに済む。
- **(P2) 受理形の判定は phase field で行う。** state に `phase` (`applied` / `committed`) を持たせ、
  land は commit 成功後に `committed` へ書き換え、postcondition 全通過後に削除する。
  land の active-plan 分岐は `phase=applied` (main == tested_tip) と
  `phase=committed` (main が tested_tip の子の fold commit) の 2 形を受理し、後者は
  **再 apply も再 commit もせず postcondition と finalize だけ**を行う。
- **(P3) 入力 closure は plan_fold が読む入力の全集合で作る。** `docs/worklog.md`・`decisions.md`・
  `failures.md`・`phase3.md`・`docs/archive/README.md`・`docs/archive/worklog-*.md`・
  `docs/spool/FOLDED.md`・全 fragment・`WORKLOG_ROTATE_BYTES` の値。path→sha256 の正準 JSON を
  sha256 する。resume 時に再計算して不一致なら `TransactionError`。
- **(P4) 旧 v1 state は `_load_state` が version 2 以外を拒否する現行形をそのまま使う** (定数を 2 へ上げる)。
  移行 code は書かない。

## 並列分割方針

- 段 2: codex plan 1 本 (file:line 粒度)。
- 段 3: 敵対レンズ 2 本 (sol = 受理集合と fail-open、luna = 相遷移と復旧の完全性)。
- 段 5: 実装子 2 本に**所有を分離** — A = `tools/spool_fold.py` + `test_spool_fold.py`、
  B = `tools/dev_wave_land.py` + `test_dev_wave_land.py`。schema 契約は段 4 で固定して両者へ前渡しする。
- 段 6: 敵対レビュー 2 本 + fix + 変異 matrix + 受入全走 (lease 取得後)。

## 環境

- 実装・テスト・受入全走: Pegasus login node の本 worktree (計算ノード不要、`tools/run_tests.py`)。
- 受入 lease: `tools/dev_wave_wait.py acceptance` で claim (30 秒間隔)。
