# 段 4 裁定 — [T-2470] create-only writer の作りかけ file 撤去

親が段 2 プランと段 3 の 2 レンズ (sol=正しさ境界 / luna=整合・実効性) を裁定し、plan v2 と変異事前登録を確定する。
裁定 inbox 再走査 (2026-09-14): T-2470 に対する新しい裁定は decisions / failures / phase3 に 0 件。
local main は wave 開始 (7dc4ecc39) から 13 commit 進んだ。受入時に post-claim merge で取り込む。

## 所見の裁定

| ID | 判定 | 採否 | scope | 裁定 |
|---|---|---|---|---|
| S-1 | **real** | **採用 (must-fix)** | 内 | 親が現物で裏取りした。下記「S-1 の裏取り」参照。plan v1 のままでは、修正が新しい破壊経路を作る |
| S-2 | refuted | — | 内 | 通常 writer 同士では敗者が完成物を消せない。open と書き込み try の分離という**構造**で排除されている点を採用 |
| S-3 | real (説明訂正) | 採用 | 内 | DW-G05 の記述を訂正する。「放置＝可用性のみ」は S-1 を除外できていない。真の部分 bytes が正当な起点として通る攻撃は反証された (末尾改行検査) |
| S-4 | refuted | — | 内 | digest 検査に迂回経路はあるが、今回の部分 write では参照行が作られないので誤受理に至らない。根拠の言い換えを採用 |
| S-5 | real (nit) | 採用 (記述のみ) | 内 | 「同一引数の再試行」はテスト例であり受理集合そのものではない。記述を訂正する |
| S-6 | refuted | — | 内 | 通常の cleanup 失敗は元例外を保つ。`BaseException` を選ぶ理由も確認された |
| S-7 | **real** | **部分採用** | 外 (一般防御) / 内 (不変条件の実装) | 一般防御は足さない。ただし brief の不変条件「撤去してよいのはこの呼び出しが作成した file だけ」を実装が満たすことは scope 内であり、inode 照合はその実装である |
| S-8 | real (nit) | 不採用 | 外 | `os.close` 失敗が診断を置換するのは既存経路。今回の差分と無関係で成果物影響を書けない |
| L-1 | **real** | **採用 (must-fix)** | 内 | 撤去条件を `written > 0` に狭める変異が、計画の注入では生存する。注入点 `write_no_progress` を足して殺す |
| L-2 | real (nit) | 採用 | 内 | DW-O26 は変更した production **file** の consumer を要求する。4 file を焦点走へ追加する (所要は下記) |
| L-3 | **real (説明訂正)** | **採用** | 内 | (P1) の訂正。下記「(P1) の確定」参照 |
| L-4 | real (nit) | 採用 (記述のみ) | 内 | S-5 と同旨。分類側で恒久的に塞がるのは同一 payload の path であって slot 全体ではない |
| L-5 | refuted | — | 内 | 注入点が手前の I/O へ逸れる攻撃は破れなかった |
| L-6 | refuted | — | 内 | 登録 8 変異に見逃しは出なかった。ただし nodeid はまだ実在しない → DW-M07 の probe 手順に従う |
| L-7 | 半 real | 採用 (記述のみ) | 内 | caller 2 件に漏れなしは確定。「実発生 0 件」は検索不検出であって測定ではない。断定しない |

### 親自身の懸念の裁定

| 懸念 | 裁定 |
|---|---|
| 変異 8 (fsync 順序反転) を KILLED に数えてよいか | **数えない。** DW-M08 に従い、受理集合を変えない構造 pin は別枠へ記録する。テスト自体は残す |
| `test_create_only_success_preserves_bytes_and_fsync_order` は scope 内か | **scope 内。** brief の不変条件「成功経路の bytes・fsync 順序は不変」を守る検査であり、仮想リスク向けの追加ではない |
| 既存 genesis 負例への assertion 追加は「期待値変更」か | **当たらない。** 強化 (追加) だけを許し、反転・緩和・skip・削除は禁止する |
| 変異 4 (絶対 path unlink) の単一理由性 | 挙動差が symlink 差し替え時にしか出ないため、KILLED でなく**別枠の構造 pin**へ移す |
| 焦点走 10 file の所要 | 台帳実測で 1936 秒 (直列)。L-2 の 4 file 追加で 2979 秒。受入全走 15307 秒の 19%。並列走なら許容 |

## S-1 の裏取り (親が現物で確認)

sol の時系列は成立する。根拠:

1. `_locked_attempt_registry_update` (`trial_registry.py:2930`) は `fcntl.flock(fd, LOCK_EX)` を**台帳 file 自身**へ掛ける
   (`:2951`)。一方 `_write_create_only` は lock を取らずに canonical path へ直接書く。両者は排他されない。
2. 追記側は genesis が git に commit 済みであることを要求しない。
   `_assert_attempt_registry_history_append_only` (`:2587`) は全 ref を走査して `previous` を返すが、
   canonical path がどの commit にも無ければ `previous is None` を返すだけで拒否しない (`:2645`)。
   呼び出し側は `if history_tip is not None and ...` で None を素通りさせる (`:2981`)。
3. したがって A が genesis を全 bytes 書き終えてから `os.fsync` が失敗するまでの窓で、
   B が完全な genesis を読んで start / seal を追記し fsync を完了できる。
4. plan v1 の無条件 unlink は、その B の追記ごと台帳を消す。**現行 main はこの時系列で file を残すので正しい。**
   つまり plan v1 は現行より悪化する経路を作る。

真の部分書き込みでは同じ問題は起きない。台帳 parser は
`attempt_registry_core.py:1545` で `data.endswith(b"\n")` を要求し、genesis payload は canonical JSON 1 行 + 改行
なので、途中で切れた bytes は末尾改行を持たず、いかなる追記者も parse に失敗する。

## (P1) の確定 (L-3 を採用した訂正)

**本 wave を進める直接の根拠は、ユーザーの明示指示である** (逐語射影 §6)。
「既存 writer の欠陥だから D205/D730 の除外に当たらない」という親の初版の一般論は、T-1854 との区別を
立証していないので**撤回する**。D730 は見送り台帳へ滞留した項目を対象とする決定であり、全修正への
一律の実害 3 例要件ではない。この訂正を worklog へ書き、一般的な堅牢化許可へ転用しない。

## plan v2 (確定した実装)

変更してよい file は `orchestrator/campaign/trial_registry.py` と
`orchestrator/tests/test_trial_registry.py` の 2 つだけ。

### 実装

`_write_create_only` (`trial_registry.py:2433`) の内側 try に撤去処理を足す。

- `os.open(O_EXCL)` と `FileExistsError` 処理 (`:2447-2450`) は撤去処理の**外**に置く。
  「作成に成功した経路にしか入らない try」という構造で所有条件を担保し、所有 flag は作らない。
- 書き込みループで**この呼び出しが書いた総 bytes 数**を数える。
- `except BaseException:` で次を順に確かめ、**すべて満たすときだけ** `os.unlink(relative_path.name, dir_fd=parent_fd)` する。
  1. `os.fstat(fd).st_size` が、この呼び出しが書いた総 bytes 数と**等しい** (誰も追記していない)。
  2. `os.stat(relative_path.name, dir_fd=parent_fd, follow_symlinks=False)` の `(st_dev, st_ino)` が
     `os.fstat(fd)` のそれと**等しい** (name が別 inode に差し替わっていない)。
  条件が崩れていたら撤去せずそのまま元例外を送出する (= 現行 main と同じ挙動)。
- 撤去中に出た `OSError` は握って、末尾の裸の `raise` で**元の失敗原因**を再送出する。
- `Exception` ではなく `BaseException` を拾う (中断でも残骸を残さない)。
- 成功経路の bytes、`fsync(fd)` → `fsync(parent_fd)` の順序、送出例外型 `TrialRegistryError` は変えない。
- 外側の三段構え (`:2462` / `:2464` / `:2466`) は維持する。

**採用しない案 (明記する限界):**
- `fcntl.flock` の追加は**採用しない**。1 と 2 の照合と `unlink` の間には残余の窓があり、
  flock ならその窓も閉じられる。しかし残余の窓は隣接する 2 syscall の間であり、追記側は
  その手前に全 ref の git 履歴走査 (`rev-list --all` + 各 commit の tree 読み) を挟む。
  D205 (プロトタイプであり production 級の堅牢性は目標にしない) に照らして、この窓のために
  writer へ新しい lock 機構を足すことは採らない。**この限界は主張せず明記する。**
- staging + hard-link publish への作り替えは採用しない (scope 外)。
- 他 module の同名 writer への横展開は採用しない (族一般化には独立 2 例が要る)。
- S-7 の一般防御 (外部 rename に対する原子的保護) は採用しない。inode 照合は既に起きた差し替えを
  検出するだけで、照合と unlink の間の差し替えまでは防がない。

### テスト (すべて `orchestrator/tests/test_trial_registry.py`)

**正例 (parametrize、8 nodeid)**
`test_attempt_create_only_failure_removes_residue_and_allows_retry[<caller>-<point>]`
- caller ∈ {`genesis`, `classification`}
- point ∈ {`write`, `write_no_progress`, `file_fsync`, `directory_fsync`}
- 各 nodeid は「失敗注入 → 対象 file 不在 → **注入解除後に同一引数で再試行して成功**」まで完結させる。
- `write_no_progress` は `os.write` が `0` を返す経路 (`:2455` の "did not advance") を通す。L-1 の対策。
- `TrialRegistryError` の gate 文字列と `__cause__ is 注入した例外` を確認する。

**撤去条件の正例 2 本 (S-1 / S-7 対策。ユーザーが求めた「既存の完成物は消さない負例」の中核)**
- `test_attempt_create_only_keeps_file_extended_by_another_writer`
  genesis の `os.fsync` 注入の中で、**別 fd から台帳へ正当な追記**を行ってから失敗させる。
  対象 file が消えていないこと、追記分を含む bytes が完全に保たれること、元の失敗が伝わることを確かめる。
- `test_attempt_create_only_keeps_replaced_inode_at_same_name`
  `os.fsync` 注入の中で、作成した file を unlink して同名に**別 inode** の file を作ってから失敗させる。
  差し替わった file が消えていないことを確かめる。

**補助 3 本**
- `test_create_only_unlink_failure_preserves_original_error` — 撤去自体を `OSError` にしても `__cause__` が元の write エラーのまま
- `test_create_only_interrupt_removes_residue_and_allows_retry` — 部分 write 後の `KeyboardInterrupt`
- `test_create_only_success_preserves_bytes_and_fsync_order` — 成功経路の最終 bytes と fsync 順序 `[file, directory]`

**負例**
- 既存 `test_attempt_registry_genesis_is_closed_before_first_performance_observation` に
  拒否後の bytes 完全一致を**追加**する (強化のみ。反転・緩和・skip・削除は禁止)。
- 新規 `test_attempt_registry_classification_rejection_preserves_receipt_bytes` —
  正常分類 1 回 → 同一 capability・同一 kwargs で 2 回目 → `TrialRegistryError` かつ
  既存受領証の bytes が 1 bit も変わらないこと。
- 既存 `test_genesis_cli_rejects_second_creation_without_changing_bytes` は**変更しない**。焦点走に含める。

**既存テストの期待値は変更しない。** 変えないと通らない既存テストがあれば実装が誤りなので、
nodeid と理由を報告して止める。

## 変異事前登録 (DW-M01)

nodeid は実装前なので**まだ実在しない**。DW-M07 に従い、段 6 では
**(1) 全件 SURVIVED 期待の probe 走で観測 node を集め、(2) その完全集合で本登録して本走**する。
probe である旨と観測 node は台帳へ残す。以下は位置と単一理由の事前登録である。

### KILLED を期待する変異 (受理集合または fail-closed 挙動が期待方向へ変わる)

| # | 位置と書き換え | 単一理由 | 殺すはずの nodeid (probe で完全集合を確定) |
|---|---|---|---|
| M1 | 撤去処理の `os.unlink(...)` を削除 | 残骸が残り再試行が塞がる | `...allows_retry[genesis-write]` |
| M2 | `FileExistsError` handler の中にも撤去を足す | 既存の完成物を消す | 強化後の genesis 負例 / 新規 classification 負例 / 既存 CLI 負例 |
| M3 | `os.fsync(parent_fd)` を撤去対象 try の外へ移す | 親 fsync 失敗時に残骸が残る | `...allows_retry[genesis-directory_fsync]`, `[classification-directory_fsync]` |
| M4 | size 照合 (`st_size == 書いた bytes 数`) を削除 | 他者が追記した台帳を消す | `test_attempt_create_only_keeps_file_extended_by_another_writer` |
| M5 | inode 照合を削除 | 同名の別 inode を消す | `test_attempt_create_only_keeps_replaced_inode_at_same_name` |
| M6 | 撤去条件を `written > 0` に狭める | 進捗なし write 失敗で残骸が残る | `...allows_retry[genesis-write_no_progress]`, `[classification-write_no_progress]` |
| M7 | `except BaseException` を `except Exception` に変える | 中断で残骸が残る | `test_create_only_interrupt_removes_residue_and_allows_retry` |
| M8 | 撤去中の `except OSError` を握らず再送出する | 元の失敗原因が置き換わる | `test_create_only_unlink_failure_preserves_original_error` |
| M9 | 撤去処理末尾の裸の `raise` を削除 | 失敗が握り潰され成功に見える | `...allows_retry[genesis-write]` |

### 別枠 — 診断・構造 pin (KILLED 集計に数えない、DW-M08)

| # | 位置と書き換え | 理由 |
|---|---|---|
| P1 | `os.fsync(fd)` と `os.fsync(parent_fd)` の順序を反転 | 受理集合を変えない耐久性の pin |
| P2 | 撤去を `os.unlink(repository_root / relative_path)` (絶対 path) に変える | 挙動差は symlink 差し替え時にしか出ない構造 pin |

## 焦点走 file 集合 (DW-O26)

段 2 の 10 file + L-2 の 4 file = **14 file** (`orchestrator/tests/` 配下)。台帳実測の直列所要 2979 秒。

`test_trial_registry.py` / `test_attempt_registry_core_equivalence.py` /
`test_p3_autonomous_workload_trial.py` / `test_reflux_origin_binding.py` /
`test_reflux_originless_compatibility.py` / `test_autonomous_trial_completeness.py` /
`test_attempt_registry_core_s8b_profile.py` / `test_s8c_preregistration_predicates.py` /
`test_s8c_preregistration_core.py` / `test_s8c_preregistration_invariant.py` /
`test_holdout_observation.py` / `test_campaign.py` / `test_paper_story_a1_paired.py` /
`test_paper_story_a1_job_contract.py`

## 段 5 の分割

編集面は 1 production file + 1 test file で素集合に割れない。**実装子 1 本**とする。
段 6 は敵対レビュー 2 本 + fix + 変異 probe/本走 + 受入全走。
