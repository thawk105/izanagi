# 段 1 brief — [T-1629] D905 執行機構 (署名 broker) の回収と着地

## scope

未 commit のまま 3 本の codex worktree に取り残された D905 実装 (Ed25519 検証子・署名 receipt
検証子・client 側 broker) を独立監査したうえで採否を決め、**配線まで含めて 1 本の wave として
着地させる**。完了条件は (i) D905 執行機構を生きた gate として着地させ、(ii) 批准対象の exact
digest を確定させて、内容の承認だけをユーザー gate として起票できる状態にすること。

**批准 receipt そのものを AI が 1 行も書かない。** 実 repo の台帳へは触れない
(合成 repo 内でテストが署名するのは対象外)。

## 確定済みユーザー裁定

- **D905 (2026-08-25):** 執行経路は「AI が成りすませない実行主体の新設」だけを採る。
  転記を人間手番に残す案・平文承認へ移す案はどちらも却下済み。
- **D906 (2026-08-25):** 署名鍵と発行権限は AI が書ける領域の外に置く。
  鍵が AI の書ける領域にあると「署名が増えただけの恒真な関門」になる。
- **D883 (2026-08-25) / 前 wave 裁定パッケージ:** 3 条件を同時に満たすには
  「AI が成りすませない実行主体が digest を計算する」以外に道が無い。
  **一度きりの人間 bootstrap は不可避**で、再設計の成果は反復手番を消すこと。
- **D526:** 主張の上限は「AI 実装者が追記できない集合との比較」まで。
  「人間が批准したことの機械的証明」と書いてはならない。
- **D95:** 実装面は Codex `role=author` が書く。親は直接編集しない。

## 不変条件 (緩めてはならない)

1. AI は receipt 行も trust root も実 repo へ書かない。生成もしない。
2. trust root は `hooks/` 配下に置く。**AI の書込が機械拒否される唯一の場所**である (M5)。
3. 受理集合を広げない。v1 で通っていた入力が v2 で落ちるのは許容 (強化)。逆は不可。
4. 免除経路 (`require_environment_contract=False` 等) への付け替えは採らない (規律 2、F498)。
5. D526 の主張上限を超える文言を docs・docstring・エラー文へ書かない。
6. 既存テストの期待値を変えない。落ちるなら実装側が誤り。
   例外は closure path 数の exact pin (M7) — 閉包を広げる以上、同じ変更で追随させる。

## 親が本セッションで実測した前提

- **M1.** main `e29084e0` の closure digest = `dabeada30868a5f790b25b86a9f0a34fafb24946f0e73de48fb90d97d9332eb9`
  (working tree と HEAD blob が一致)。批准済み集合 = `{db511c3d8411...}` の 1 件。**不一致 = 未批准。**
  `_committed_ratification_digests()` は 0.43 秒で正常終了する。**T-1647 が書いた障壁は解消済み。**
  → **成果物影響 (DW-G05): 本件が閉じない限り、official な新規 campaign 初期化は
  `ident.py:239` で全部 fail-closed のままで、certified 選択結果・proof chain は 1 件も新規生成できない。**
- **M2.** main の closure は **25 path**。回収した broker の `CLOSURE_PATHS` は **27 path**
  (`ed25519_verify.py` と `enforcement_source_ratification_receipt.py` を含む)。
  → **`campaign_lock.py` / `contract_loader_binding.py` を触る配線単位 (u3) が存在しない。
  回収物だけでは gate に一切繋がらない死んだコードである。**
- **M3.** T-1742 の履歴検査は main で `9885a156` / `9c1d49ef` により **DAG として修正済み**。
  この 2 commit は回収物の base `9463bcbc` の祖先では**ない**。
  回収した u2 は旧・線形版 (`log --reverse --full-history` + strict prefix + 1 commit 1 行) を
  使っており、**main が既に解いた欠陥を持ち戻している**。shallow clone 防御
  (`_assert_full_history_repository`) も持っていない。
- **M4 (DW-G01 生死確認).** 回収 7 file を worktree へ一時配置して焦点走 → **95 passed / 4 failed / 5.17 秒**。
  機構は端から端まで動く (pure-Python 検証子が `cryptography` の署名を実際に検証している)。
  赤 4 件の本文まで読んだ結果は 2 つとも**回収物の実欠陥**である。
  - broker 3 件: `_run(argv, data=None)` が `subprocess.run(input=None)` を呼ぶため
    子 process が親の stdin を継承し、`ssh` / `openssl` が**承認入力 `y` を食う**。
    その結果 `input()` が EOF を受け `answer=""` → `ratification declined`。**production 欠陥。**
  - receipt 1 件: merge テストの前提 assert (`merge_commit in history`) 自体が偽。
    git は blob が両親と同一な merge を prune するので、**production の
    `if blob.stdout == previous_raw: continue` 行に到達しない = 恒真テスト**。
    T-1742 の本命 (分岐した 2 本がそれぞれ 1 行足して合流) は検査すらされていない。
- **M5.** `hooks/` subtree は AI の Write/Edit/apply_patch と Bash 書込・削除・移動が機械拒否される
  (例外は exact `hooks/README.md`)。一方 `git add -- hooks/<file>` は止まらない (前 wave 実測)。
- **M6.** この機体に `cryptography` 3.4.8 / `PyNaCl` 1.5.0 / `openssl` 3.0.2 / `ssh-keygen` が実在。
  テスト側の署名者と differential 対照は確保できる (いずれも本番 closure の外)。
- **M7 (DW-O09 pin 閉包).** closure path の exact 逐語 tuple pin が
  `orchestrator/tests/test_t671_source_binding.py` の 4 箇所 (185 / 369 / 529 / 604)、
  呼び出し回数 pin が同 744。`orchestrator/tests/conftest.py:194` の
  `ratified_enforcement_source` fixture は v1 専用で、**v2 へ切り替えると
  この fixture に依存する real-repo テストが一斉に落ちる**。
- **M8.** 生きた消費者は `orchestrator/campaign/ident.py:239` の 1 本だけ。

## 親の provisional 裁定 — すべて攻撃対象

- **(P1) v1 gate を v2 signed receipt へ置換する** (AND 併存にしない)。
  AND にすると 64hex の転記が人間手番に残り、D905 が消そうとしたものが消えない。
  v2 ≥ v1 の強さは「trust root が `hooks/` にあり、人間が一度だけ置く」ことだけで担保される。
  ―― この含意が破れる経路を探せ。
- **(P2) broker は trust root を作らない。** 回収 u4 の auto-create (TOFU) 経路を削除する。
  現状 `tools/ratification_broker.py` は AI が実行でき、trust root が不在なら**AI 自身の鍵が
  信頼根になる**。これは D906 が名指しした恒真化そのものである。
  bootstrap は「人間が `hooks/` へ 1 file を置く一度きりの操作」へ分離する。
- **(P3) receipt 台帳も `hooks/` 配下へ移す** (回収案は `orchestrator/campaign/`)。
  署名があるので偽造はできないが、現案では AI が台帳へ garbage を追記して gate を
  永久に閉じられる (可用性攻撃)。`hooks/` なら書込自体が拒否される。
- **(P4) Ed25519 は pure-Python を維持する。** 検証子は closure の内側にあり、
  wheel 由来のバイナリは closure digest が覆わない。信頼鎖を批准 bytes の中へ閉じるため
  自前実装を採る。代償 (自前暗号) は RFC 8032 の公式 test vector と
  `cryptography` / `PyNaCl` との differential テスト (テスト側のみ) で相殺する。
- **(P5) u2 の履歴検査は main の DAG 実装を再利用する形へ書き直す。** 線形版は採らない。
  `_assert_full_history_repository` 相当の shallow clone 防御も持たせる。
- **(P6) broker の子 process 起動は `stdin=DEVNULL` を既定にし、承認入力は tty を要求する。**
  `--yes-i-have-read-this` は現在**宣言されているだけで一度も読まれない死んだ flag** である。
  実配線するか削除するかを決める。
- **(P7) 配線単位を新設する。** closure list +2 path、`contract_loader_binding` を v2 へ、
  `conftest.py` に署名 fixture、`test_t671_source_binding.py` の exact pin 追随。
- **(P8) 本機構の強さは「秘密鍵が AI の書ける領域の外にあるか」だけで決まる。**
  この計算機では AI は home 配下を自由に読み書きできる。したがって
  **ssh 搬送は装飾ではなく防壁そのもの**であり、broker は AI が触れない別マシンで動く前提でしか
  D906 を満たさない。同一機で動かす運用を許すなら、その時点で恒真化する。
  ―― この前提が現実の運用と食い違うなら裁定パッケージへ上げる。

## 成果物の形

コード + テスト (回収 3 単位の監査済み改訂 + 配線単位)、変異 matrix、受入全走の受領証、
worklog / decisions / failures fragment、**land 後に確定する批准対象 exact digest と
ユーザーへ渡す bootstrap 手順**、裁定パッケージ (P8 が食い違う場合)。

## 分割方針

段 2 = plan 子 1 本 (read-only)。段 3 = 敵対 2 レンズ並列
(A: 正しさ境界・偽造路・恒真化、B: 実効性・scope・親の実測値と P1〜P8 の一般化)。
段 5 = 所有素集合で 4 単位 (A: ed25519、B: receipt 検証子、C: broker、D: 配線)。
D は A/B に依存するので先行 2 単位の完了後に投入する。

## 変更面アンカー

| path:line | 役割 |
|---|---|
| `orchestrator/campaign/campaign_lock.py:29` | `CONTRACT_LOADER_RELATIVE_PATHS` (25 path) |
| `orchestrator/campaign/contract_loader_binding.py:387` | `verify_ratified_contract_loader_binding` |
| `orchestrator/campaign/enforcement_source_ratification.py:551` | `_committed_ratification_digests` (DAG 版・再利用元) |
| `orchestrator/campaign/enforcement_source_ratification.py:276` | `_assert_full_history_repository` |
| `orchestrator/campaign/enforcement_source_ratification.py:619` | `require_ratified_closure` (v1 gate) |
| `orchestrator/campaign/ident.py:239` | 生きた消費者 |
| `orchestrator/tests/conftest.py:194` | `ratified_enforcement_source` fixture (v1 専用) |
| `orchestrator/tests/test_t671_source_binding.py:185,369,529,604` | closure path の exact 逐語 pin |
| `orchestrator/tests/test_t671_source_binding.py:744` | 呼び出し回数 pin |
| `hooks/guard_write.py` `_protected_hooks` | `hooks/` subtree 拒否 |
| `hooks/enforcement-source-closure-ratifications.v1.jsonl` | v1 台帳 (1 行・`db511c3d…`) |
| `/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t1629-ratification-broker/recovered/` | 回収物 7 file (repo 外) |
