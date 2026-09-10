# 段 4 裁定 — dev-wave-t725-t694-lease-clean

親が全所見を real / refuted、採用 / 不採用、scope 内 / 外へ裁定する。**親自身の実測を根拠にし、
子の報告を額面で採らない。** 実測はすべて本 worktree (`e447b87b` 取り込み後) で行った。

## 親が行った実測 (裁定の一次資料)

| # | 実測 | 結果 |
|---|---|---|
| E1 | `git log -1 --format='%h parents=%p' ce46e128` (待ち手が作った実在 merge commit) | `parents=b2d785eb 4aedcf46` — **second parent が取り込んだ main SHA を構造的に記録している** |
| E2 | `python3 tools/check_ai_provenance.py --help` | `--message-file` が実在する |
| E3 | `docs/ai-provenance.md` 「commit 前の確認」 | 正本の通常列は「message file → **`--message-file` rc=0** → `commit -F` → 既定 full-history 監査」 |
| E4 | `time python3 tools/check_ai_provenance.py --message-file <probe>` | **0.097 秒・local 実行 (dispatch なし)**、rc=1 で形式違反を検出。`_message_has_ai_agent` より厳格 |
| E5 | `git status --porcelain` の 4 変種 (既定 / `-uall` / `--ignore-submodules=none` / 両方) | clean な本 worktree では 4 変種とも 0 行。偽赤の実在は確認できず |
| E6 | `git submodule status --recursive` | `external/ccbench` は初期化済み clean、`third_party/shirakami` は未初期化。`--ignore-submodules=none` でも 0 行 |
| E7 | `orchestrator/tests/test_dev_wave_wait.py:2146` | 二重 signal の既存テストは `_cleanup_after_claim` を直接呼ぶ。`_cleanup_lifecycle` の ownership 消費 (804 行) と mask 設定 (763 行) の間の窓は覆っていない |

## レンズ A の所見

### A-1 「F191 点 1 は未充足」 → **refuted (害の主張)。docs 1 行だけ採用**

E1 が決定的である。待ち手は `git merge --no-ff --no-commit main` → `git commit -F` で
merge commit を作るので、**取り込んだ main SHA は second parent として commit object に
不可変に記録される**。message 本文の placeholder 置換より強く、かつ改竄不能である。
レンズ A の「古い SHA を記録しても通過する」という害は成立しない。

ただし F191 の逐語と実装が食い違うのは事実なので、**F191 の恒久対応へ erratum を 1 行**足す
(点 1 は message への SHA 差し込みではなく merge commit の parent で充足する)。scope 内 (docs)。

### A-2 「F191 点 2 の provenance preflight が不在」 → **real。採用 (scope 内)**

E2〜E4 で裏が取れた。正本 (`docs/ai-provenance.md`) は commit 前に
`check_ai_provenance.py --message-file` の rc=0 を要求するが、待ち手は
`git commit --dry-run -F` と `_message_has_ai_agent` (行頭 `AI-Agent:` の存在のみ) しか見ない。
E4 のとおり checker は形式違反を実際に落とす。これは F191 点 2 の「provenance preflight」
そのものであり、**親 brief の「点 2 は実装済み」は誤りだった。撤回する。**

成果物影響: provenance 不正な merge commit を作ってから 20〜40 分の受入を走らせ、
land 時の全史監査で初めて赤になる。受入 1 走と lease 窓を丸ごと失う。

### A-3 / B-04 「述語が untracked・submodule を見逃す」 → **real。採用 (P2 を改訂)**

F191 の逐語は option なしの `git status --porcelain` (untracked を含む) である。
親 brief の `--untracked-files=no` はその狭め方であり、根拠を書いていなかった。
また `tools/run_tests.py:1552` と `tools/dev_wave_land.py:816` はいずれも
`--ignore-submodules=none` を明示している。**述語をこの 2 つへ揃える。**

**改訂後の P2**: 述語は `git status --porcelain --ignore-submodules=none` (untracked を含む)。

E5・E6 のとおり、clean な wave worktree では 4 変種とも 0 行であり、偽赤の実在は確認できなかった
(job artifact は repo 外、`output/pegasus-dispatch/` は `.gitignore` 対象)。

**併せて `_identity_preflight` (claim 前) の述語も同一へ揃える。** 揃えないと
「preflight は通るが prerun で落ちる」非対称ができ、最大 7,200 秒待ってから lease を消費して
落ちる最悪経路を新設してしまう。同一にすれば、汚れた木は **claim 前に rc=2 で・lease を
消費せずに**落ちる。これが偽赤コストの主な緩和策である。

運用上の帰結 (docs へ明記する): 受入の前に untracked を commit するか `.gitignore` する。

### A-4 / B-01 / B-02 「単発 status は TOCTOU、走行中は覆わない、運用と衝突」 → **real。分割裁定**

3 件とも real である。ただし**成立する主張の範囲**を正確に切る。

- **採用 (scope 内)**: 本 wave の成果を「投入瞬間の一致を保証する」と書かない。
  worklog・§7.3・F191 erratum には**「claim から投入までの窓の dirty を閉じる。走行中の
  変更は覆わない」**と正直形で書く (規律 3 整合)。`CLAUDE.md` 進め方 9 の
  「待機中に文書を進める」との衝突についても、**待機中の文書は repo 外 (`dev-wave-jobs/`) か
  別 worktree へ書く**という運用を §7.3 へ明記する。
- **裁定へ (scope 外)**: 受入対象 worktree の write-quiescence、使い捨て受入 worktree、
  走行後の tree fingerprint 検査。いずれも受入の実行形態そのものを変える設計択一であり、
  T-725 の「安全配線 3 点」の外側にある。裁定パッケージ §1 へ。

### A-5 「実 Git 負例と held-self 負例が不足」 → **real。採用**

追加テストを増やす (下の plan v2 §4)。

### A-6 「待ち手を迂回する受入経路が実在する」 → **real。scope 外 → 裁定へ**

`tools/run_tests.py:505` は引数なし起動を acceptance shape と判定する。
本 wave の gate は待ち手経由の層しか覆わない。scope 拡大はしない (親 brief の裁定どおり)。
裁定パッケージ §2 へ。

### A-7 「brief の land 被覆の説明が不正確」 → **real。採用 (docs 訂正)**

`tools/dev_wave_land.py` は lock 内で wave worktree の clean も検査する。
brief の「wave 側は tested_tip の SHA 一致で見る」は不正確だった。訂正する。
ただし**純増検出力は残る** — 受入時にだけ存在し受入後に除去された編集は、
status も SHA も一致するため land では捕まらない。レンズ A も「純増ゼロの反例は確認できなかった」
と明記している。

## レンズ B の所見

### B-03 「§7.3 の rc / release 文言が不足」 → **real。採用**

レンズ B の提案文をほぼそのまま採る (述語は A-3 の裁定に合わせて置換する)。

### B-05 「behind>0 経路も dirty でありうる。P4 の説明が誤り」 → **real。採用**

正しい。`git merge --no-ff --no-commit` + `git commit` は index を commit するのであって、
merge と無関係な**未 stage の tracked 編集は commit されず残る**。段 2 プランの
「behind>0 は構造上 clean」という説明は誤りである (親 brief の同趣旨の記述も撤回する)。
**gate の配置自体は両経路無条件で正しい**ので実装は変わらないが、
**behind>0 + merge 後 dirty の負例を必ず追加する** (説明の誤りを検査で固定する)。

### B-06 「signal + finally は『確実な release』と等価でない」 → **部分 real。分割裁定**

- **refuted の部分**: SIGKILL と host 停止は **shell の `trap` でも捕捉できない**。
  T-694 が求めた「`trap` による確実な release」は trap 相当の保証であり、Python の
  signal handler + `finally` はこれを満たす。ここを未達とはしない。
- **real の部分**: E7 のとおり `_cleanup_lifecycle` は ownership を `NONE` にしてから
  `_cleanup_after_claim` へ入り、mask を張るのはその内側である。この 2 行の間に 2 発目の
  signal が入ると cleanup が中断し、再入は ownership 消費済みで no-op になる。lease が
  TTL 2,400 秒まで残留する。既存テスト (2146 行) はこの窓を覆っていない。
  **scope 外 → 裁定へ** (µs 窓・TTL 有界であり、修正は lease state machine の mask 順序の
  作り替えになる。DW-G02 の blocker 限定に従い 1 cycle 後へ送る)。裁定パッケージ §3 へ。
- **採用 (docs)**: SIGKILL / 二重 signal / cleanup setup 失敗の既知限界を §7.3 へ明記する。

### B-07 「周期は固定 30 秒ではなく 30〜120 秒」 → **refuted。docs 1 行だけ採用**

T-694 が挙げた害は「周期が待ち札 TTL 300 秒を超える実装が現れると順番を失い続ける」である。
`_MIN_ACCEPTANCE_POLL_SECONDS = 30` / 上限 120 の policy range は**この害を構造的に排除している**
(300 秒超は rc=2 で起動前に落ちる)。要件は実質充足。docs へ
「T-694 の『周期固定』は policy range 30〜120・既定 30 で充足」と 1 行記録する。

### B-06 の nit (旧 `run-acceptance.sh` の残存) → **不採用 (現行 consumer 未確認)**

レンズ B 自身が nit と判定している。実稼働 inventory の確認は別作業。

## 撤回する親 brief の主張

1. 「F191 点 2 は実装済み」 → **撤回** (A-2)。provenance preflight は不在だった。
2. 「点 1 はより厳しい形なので充足」 → **理由を差し替え** (A-1)。理由は「merge commit の
   second parent が SHA を記録するから」であって「変更 byte が少ないから」ではない。
3. 「behind>0 経路は merge commit 直後なので構造上 clean」 → **撤回** (B-05)。
4. 「land は wave 側を tested_tip の SHA 一致で見る」 → **訂正** (A-7)。lock 内で clean も見る。
5. 「[T-694] は残差ゼロ」 → **訂正**。実装要件は充足だが、`_cleanup_lifecycle` の二重 signal 窓
   という別の real 所見が出た (裁定へ)。docs 側の残差もある。
6. 「述語は `--untracked-files=no`」 → **改訂** (A-3)。

## plan v2 (実装子へ渡す確定 scope)

1. **`_identity_preflight` の clean 述語を変更** (`tools/dev_wave_wait.py:552`)。
   `("git", "status", "--porcelain", "--ignore-submodules=none")` とする。
   stage 名 `preflight-clean`・rc=2 は変えない。
2. **merge 経路へ provenance preflight を追加**。`_validated_message_copy` の後、
   `git commit --dry-run -F` の**前**に
   `(sys.executable, str(repo / "tools" / "check_ai_provenance.py"), "--message-file", <message>)`
   を `_run_capture` で実行する。stage 名 `merge-message-provenance`。
   非 0 なら `_StageFailure` → 既存経路で `merge --abort` + release。
3. **`prerun-clean` stage を追加**。`commit-head-postcheck` の後、
   `acceptance-command argv=` の出力より前。**両経路に無条件で適用**する。
   argv は 1 と一字一句同一。`stdout` が非空なら `_StageFailure("prerun-clean")` (rc=70)。
   ACQUIRED は release、HELD_SELF は保持 (既存 `_cleanup_lifecycle` に載せる。cleanup は変更しない)。
   失敗時は検出した path を stderr へ出す。
4. **テスト**。段 2 プランの「7 定義 8 case」の更新を採る。加えて `_STAGES` へ
   `prerun-clean` と `merge-message-provenance` を追加し、次の負例・正例を新設する。
   - 正例: clean で受入 command が投入され、release されない
   - 負例 a: claim 後に tracked dirty → command 不投入・rc=70・stage=`prerun-clean`・release される
   - 負例 b: **untracked のみ** dirty → 同上 (述語改訂の固定)
   - 負例 c: **behind>0 で merge 後に tracked dirty が残る** → 同上 (B-05 の固定)
   - 負例 d: **`held-self` + dirty** → command 不投入・rc=70・**release しない**
   - 負例 e: `AI-Agent:` 行はあるが形式違反の message → `merge-message-provenance` で
     rc=70・merge abort + release (`_message_has_ai_agent` と `git commit --dry-run` は通る fixture)
   - 負例 f: preflight 段で **untracked のみ** dirty → rc=2・stage=`preflight-clean`・**claim しない**
   - 実 git 1 本: 実 git の worktree で tracked dirty にして投入されないことを確認
5. **docs (親が書く)**: §7.3 へ B-03 の文言 + 改訂後の述語 + 「待機中の文書は repo 外か別 worktree へ」
   + 既知限界 (走行中は覆わない / SIGKILL / 二重 signal)。F191 の恒久対応へ erratum 3 行
   (点 1 は merge parent で充足 / 点 3 の述語 / 覆う窓の正直形)。

**scope 外 (実装しない)**: worktree quiescence、使い捨て受入 worktree、走行後 fingerprint、
`run_tests.py` 側の同等 gate、`_cleanup_lifecycle` の mask 順序、`--owned-path` の default-open、
fencing token、holder の invocation 識別。

## 変異事前登録 (DW-M01)

受理集合を縮小する wave なので、**過剰拒否を検出する正例側の変異 (M6) も登録する**。
各変異は「同じ入力を拒否する層が前後に無い」ことを確認済み。

| ID | 変異 (wave 前の実コードの形を含む) | 単一理由性の確認 | 期待 |
|---|---|---|---|
| M1 | `prerun-clean` の `raise _StageFailure` を削除する (= wave 前の形。検査なし) | 負例 a の fixture は preflight 時 clean・prerun 時 dirty。他層に dirty を拒否する段はない | KILLED (負例 a/b/c/d) |
| M2 | `if prerun_status.stdout:` を `if False:` にする (恒真化) | 同上 | KILLED (負例 a) |
| M3 | `_identity_preflight` の述語を `--untracked-files=no` へ戻す (= wave 前の形) | 負例 f は untracked のみ dirty。緩めると preflight を通過し prerun で rc=70/stage=`prerun-clean` になる。rc が 2→70 へ、lease 消費が無→有へ変わるので `DW-M03` の「fail-closed 挙動が期待方向へ変わった」に該当 | KILLED (負例 f、rc と stage を exact 検査) |
| M4 | `check_ai_provenance --message-file` の呼出しを削除する (= wave 前の形) | 負例 e の message は `AI-Agent:` 行を持ち `git commit --dry-run` も通る。checker だけが落とす | KILLED (負例 e) |
| M5 | `prerun-clean` を `behind == 0` のときだけ実行する | 負例 c は behind>0 で merge 後 dirty。他層は拒否しない | KILLED (負例 c) |
| M6 | `if prerun_status.stdout:` を `if True:` にする (**過剰拒否**) | 正例は clean な木。承認外の拒否を検出する | KILLED (正例) |

harness は `tools/mutation_harness.py` を使う (`DW-M05`)。runner の argv には
**`--force-dispatch` を必ず入れる**。

## 裁定パッケージ (ユーザーへ返す。本 wave では実装しない)

### §1 受入対象 worktree の quiescence — 走行中の変更を覆うか

**問題**: 本 wave の gate は claim〜投入の窓しか覆わない。受入 command は 20〜40 分走り、
その間の tracked 変更は覆われない。`CLAUDE.md` 進め方 9 は待機中の文書作業を親へ指示しており、
運用そのものが writer を生む。

- (a) 現状維持 + 正直形の明記 (本 wave が実施する範囲)。走行中は覆わないと書く
- (b) 走行後の `git status` / tree fingerprint 検査を足す。走行後も dirty なら赤。
  走行中だけ汚れて戻された場合は覆わない
- (c) 受入を使い捨て worktree (固定 commit の checkout) で走らせる。完全に覆えるが、
  受入の実行形態と land の tested_tip 束縛を作り替える必要がある

**親の推奨は (b)**。(c) は本質的だが受入経路全体の作り替えになり、[T-725] の射程を超える。
(b) は既存 `_tree_and_submodules_fingerprint` を通常経路でも使う小改造で、
「走行後も残る汚れ」という実害のある型を閉じる。

**成果物影響**: 実装しない場合、緑の受入結果が land された tip を測ったとは言い切れないまま
worklog・レポートへ記録され続ける。

### §2 待ち手を迂回する受入経路

**問題**: `tools/run_tests.py` は引数なし起動を acceptance shape と判定し、待ち手を経由しない
受入が実在する (2026-08-12 に waiter deadlock を迂回した実例)。本 wave の gate は掛からない。

- (a) 待ち手経由だけを権威ある dev-wave 受入と定義し、直接走の結果は台帳へ記録不可とする
- (b) `run_tests.py` の acceptance shape 経路にも同等の clean gate を置く
- (c) 現状維持

**親の推奨は (a)**。(b) は稼働中の全 wave の受入へ即座に効き、blast radius が大きい。
(a) は docs の定義変更だけで、記録の意味を正しくできる。

**成果物影響**: 実装しない場合、clean 検査を経ていない受入結果が台帳へ入りうる。

### §3 `_cleanup_lifecycle` の二重 signal 窓

**問題**: ownership を `NONE` にしてから mask を張るまでの間に 2 発目の signal が入ると
cleanup が中断し、再入は no-op になって lease が TTL 2,400 秒まで残留する。

- (a) 現状維持 + 既知限界の明記 (本 wave が docs だけ実施)
- (b) `_cleanup_lifecycle` の入口で mask を張り、ownership 消費をその内側へ移す
- (c) 外部 watchdog / fencing で lease 残留を回収する

**親の推奨は (b)**。窓は µs で TTL 有界だが、T-694 が求めた「確実な release」の唯一残る欠けである。
ただし lease state machine の mask 順序を作り替えるため、既存 signal テスト 6 本を伴う独立 wave が要る。

**成果物影響**: 実装しない場合、稀に lease が最大 2,400 秒残留し、その間の他 wave の受入が遅れる。

### §4 (レンズ B より) `--owned-path` の default-open、fencing token、holder の invocation 識別

レンズ B の整理 (選択肢・推奨・成果物影響) をそのまま採る。親の推奨も同じ
(それぞれ「明示 opt-in の場合だけ続行」「世代 token」「invocation UUID」)。
いずれも本 wave の scope 外。
