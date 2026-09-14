# [T-2470] create-only writer の作りかけ file が path を恒久的に塞ぐ穴

authority: none
default_effect: no-state-change

可変状態の正本は worklog 末尾と現行 phase doc であり、本書はその写しにしない。
wave branch `worktree-dev-wave-t2470-create-only-partial-write`、実装 commit `043af5dca`。

## 発見

試行台帳の起点と分類受領証を書く共有 create-only writer
(`orchestrator/campaign/trial_registry.py` の `_write_create_only`) は、`O_EXCL` で file を作った後
`os.write` / `os.fsync(fd)` / `os.fsync(parent_fd)` のいずれが失敗しても、作りかけの file を消さない。
壊れた bytes が canonical path を占有し、以後の呼び出しは
`[<gate>] create-only path already exists` で恒久的に拒否される。

段 6 レビュー由来の起票 (`docs/archive/worklog-phase3-0908-1378.md` の `[T-2470]`、一次資料は
`output/insights/2026-09-08/t2392-genesis-cli-entry/README.md`)。

## 影響する caller (親と段 2 子が独立に列挙、段 3 luna が再照合)

| caller | gate | 書き込み先 | production 入口 |
|---|---|---|---|
| `create_attempt_registry_genesis` | `attempt-registry-genesis` | `output/s8c-preregistration/attempt-registry.jsonl` | 同 module の CLI `genesis` 分岐 |
| `classify_attempt` | `attempt-classification-receipt` | `output/s8c-trial-registry/classification-receipts/<digest>.json` | `orchestrator/campaign/p3_autonomous_workload_trial.py` の `run_trial` |

`classify_attempt_failure` は別名で、production 呼び出しは 0 件。
`s8b_attempt_registry` / `attempt_registry_core` の同名 API は別実装であり、本 writer を使わない。

## この穴は可用性の穴であって、誤受理の穴ではない

親の段 1 brief は初版で「受領証を読む経路は無い」と書いたが**誤りで、自己訂正した**。
reader は実在する (`trial_registry.py` の `_assert_attempt_classification_receipts`) が、
`sha256(bytes)` を file 名と照合して落とすので、壊れた bytes が正当な受領証として受理されることはない。
さらに `classify_attempt` は受領証 file を書いてから台帳行を append するため、部分書き込み時は
台帳行が存在せず、壊れた file は孤児として誰からも参照されない。段 2 子も独立に同じ訂正を出した。

## 素朴な修正は現行より悪化する (段 3 sol の S-1、親が現物で裏取り)

「失敗したら無条件に消す」は、別 process が正当に追記した台帳ごと消しうる。成立の根拠は 3 点。

1. 台帳への追記は `_locked_attempt_registry_update` が台帳 file 自身へ `fcntl.flock(LOCK_EX)` を掛けて行う。
   一方 `_write_create_only` は lock を取らずに canonical path へ直接書く。両者は排他されない。
2. 追記側は起点が git に commit 済みであることを要求しない。
   `_assert_attempt_registry_history_append_only` は canonical path がどの commit にも無ければ
   `previous is None` を返すだけで拒否せず、呼び出し側は `history_tip is not None` で素通りさせる。
3. したがって、起点を全 bytes 書き終えてから `fsync` が失敗するまでの窓で、
   別 process が完全な起点を読んで start / seal を追記し fsync を完了できる。

**現行 main はこの時系列で file を残すので正しい。** 無条件撤去はその記録を消す。

真の部分書き込みでは同じ問題は起きない。台帳 parser は末尾改行を要求し
(`orchestrator/campaign/attempt_registry_core.py` の framing 検査)、起点も受領証も canonical JSON
1 行 + 改行の単一行なので、途中で切れた bytes には追記者が付かない。

## 採った修正と、閉じていない窓

撤去してよいのは「この呼び出しが作成し、かつ誰も触っていない file」だけとした。撤去の直前に
(1) この呼び出しが書いた総 bytes 数と `os.fstat(fd).st_size` の一致、
(2) 名前が指す `(st_dev, st_ino)` と作成した fd のそれの一致、を確かめ、両方満たすときだけ撤去する。
崩れていれば撤去せず元の失敗をそのまま送出する (= 現行と同じ挙動)。
`FileExistsError` の経路は撤去処理の外に置き、既存の完成物へ到達しないことを構造で担保した。

**照合と `unlink` の間の窓は閉じていない。** `fcntl.flock` を足せば閉じられるが、残る窓は隣接する
2 syscall の間であり、追記側はその手前に全 ref の履歴走査を挟む。D205 (プロトタイプであり production 級の
堅牢性は目標にしない) に従い、writer へ新しい lock 機構は足さなかった。設計判断は同 wave の
decisions fragment を参照。

## 段 3・6 の所見の帰結

- 段 3 sol: S-1 real・must-fix (上記)、S-3 / S-5 は記述訂正、S-2 / S-4 / S-6 は refuted、
  S-7 (外部 rename) / S-8 (close 失敗が診断を置換) は scope 外。
- 段 3 luna: L-1 real・must-fix (撤去条件を「1 byte でも書けた場合」に狭める変異が当初設計では生存する →
  注入点 `write_no_progress` を追加)、L-3 は (P1) の撤回・訂正、L-2 / L-4 / L-7 は nit、L-5 / L-6 は refuted。
- 段 6 sol / luna: **must-fix 0 件**。luna Q-5 が挙げた参照元 3 file は親が別途焦点走で緑を確認した。

### (P1) の撤回 (段 3 luna L-3 を採用)

親は段 1 で「既存 writer が自らの create-only 契約を満たしていない正しさ欠陥だから、D205/D730 の
『現行 claim への具体的影響が立証されない追加防御』除外に当たらない」と provisional に裁定した。
この一般論は近縁の `[T-1854]` (同じく分類受領証の durability、`docs/phase3.md` の見送り台帳で除外済み) と
どう違うのかを立証していない。**撤回する。** 本 wave を進める直接の根拠はユーザーの明示指示である。
一般的な堅牢化許可へ転用しない。

### 「部分書き込みの実発生は 0 件」とは言えない (段 3 luna L-7)

検索語を変えても対象 writer の実障害記録は出なかったが、それは検索不検出であって測定ではない。
起票の一次資料も障害ログではなくコード欠陥の記述である。実害不存在として一般化しない。

## 変異検査

2 pass で行った。nodeid は段 4 時点で存在しなかったため、`docs/dev-wave/mutation.md` の `DW-M07` に従い
probe → 本登録の順とした。

- probe (`mutation-spec-probe.json` / `mutation-ledger-probe.json`): 全 11 件を SURVIVED 期待で登録し、
  観測 node を集めた。結果は baseline PASSED・SURVIVED 0・全件 MISMATCH (= 全件検出)。
- 本走 (`mutation-spec.json` / `mutation-ledger.json`): 観測 node の完全集合を KILLED 期待で登録。
  結果は **baseline PASSED・KILLED 11・SURVIVED 0・MISMATCH 0・matching 11**。
  spec sha256 = `f2609aa097a5a5effad2eb59b4f3acf6dba63a65f6adc905ecd49ed9163c057e`、
  repo_head = `043af5dcac29e1c6981d436cea86bab0c3f0c881`。

**P1 (fsync 順序反転) と P2 (絶対 path での unlink) は受理集合を変えない構造 pin であり、
`DW-M08` に従い KILLED の数に数えない。** 段 6 luna の Q-6 も独立に同じ区別を要求した。
受理集合または fail-closed 挙動を変える変異は M1〜M9 の **9 件**で、全件 KILLED である。

### probe 走の erratum

probe の 1 回目 (`wrapper-attempt` 1) は 1 件目の後に rc=2 で中止した。原因は harness の欠陥ではなく、
**親が走行中に wave worktree へ段 7 の下書き file を書いたこと**である
(`DW-M05` の「変異中は親の編集を止める」に違反)。harness は各 runner 実行の前に untracked file を
検出して fail-closed で止まる。file を worktree 外へ退避して clean に戻し、`wrapper-attempt` 2 で
走り直した。1 回目の観測 (M1 が 10 node を殺した) は 2 回目と一致する。

## テストの実走 (親)

| 走行 | 範囲 | 結果 |
|---|---|---|
| 実装子の自走 | `orchestrator/tests/test_trial_registry.py` | 262 passed (login、1297 秒) |
| 焦点走 (計算ノード) | 裁定した consumer 13 file | 2313 passed / 8 skipped / 0 failed (135 秒、rc=0) |
| 焦点走 補完 (計算ノード) | 段 6 luna Q-5 の参照元 3 file | 237 passed (76 秒、rc=0) |
| 変異 baseline | `test_trial_registry.py` | PASSED (probe・本走とも) |

受入全走の結果は worklog エントリに書く。

## 逐語の正規化 (erratum)

`verbatim/s6-luna.md` は codex が markdown の強制改行として行末に半角空白 2 個を置いており、
`git diff --check` に抵触した。`DW-S07` が許す可逆最小正規化 (可視文字不変) として、行末空白だけを
除去した。復元は「該当 12 行の末尾へ半角空白 2 個を戻す」で足りる。

| 項目 | 値 |
|---|---|
| 原文 sha256 | `10b38ee7ecac730fc8009e13cb49d2b6e99128c1ed0a00c43e3652156512ab02` |
| 原文 byte 数 | 12943 |
| 正規化後 sha256 | `8654f118dfef0ce72514125de33dd05fef3be3ffc09e8142c681141cb884419e` |
| 正規化後 byte 数 | 12919 |
| 除去 byte 数 | 24 (12 行 x 半角空白 2 個) |
| 復元法 | `sed -i 's/$/  /'` を該当 12 行 (`受理の含意:` / `拒否の含意:` で始まる行) へ適用 |

他の逐語 file は抵触しなかった。

## CCBench 論文 / insight との関係

無関係。CCBench 本体ではなく orchestrator 側の台帳 writer の欠陥である。

## 還元判断

該当なし (上流 CCBench への還元対象ではない)。
