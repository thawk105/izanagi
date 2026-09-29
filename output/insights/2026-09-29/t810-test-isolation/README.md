# t810 coordinator の登録走査を撤去途中の管理 dir で止めない (2026-09-29)

- authority: none
- default_effect: no-state-change
- 依頼: `/work/1/SFC/tanab/tmp/git-maint-2026-09-29/md_4.txt` と、ユーザー追加指示「末尾の (任意) 本番の関数も直す案も実施する。
  これが本文の『本番の fail-closed 不変』『scope 外: t810_coordinator.py の本番』に優先する」
- wave: `dev-wave-t810-test-isolation`、基準 commit `8fe87f852`

## 症状

他 wave が worktree を撤去している途中、共有 git dir の `worktrees/<名前>/` に `modules` だけが残り
`gitdir` が無い状態が数分続く。この間に受入全走が走ると、`orchestrator/tests/test_t810_coordinator.py` の
live 3 node が `cannot read worktree registration: file is absent` で決定的に赤になる
(F633。再発 2026-08-26、09-21 ×2、09-27、09-29)。原因は
`tools/pegasus/t810_coordinator.py` の `repository_roots_from_git_identity` が全登録の `gitdir` を読み、
欠けた 1 件で止まること。同じ関数は本番の `prepare_group` と `coordinate` でも使われ、
他 wave の撤去中は計算ノードへの投入も止まる。

## 対象 3 件は実 repo が検証の本質 (テスト側の切り離しはしない)

| node | 検証していること | 実 repo が本質か |
|---|---|---|
| `test_prepare_group_rejects_forged_git_identity_before_any_mkdir` | caller が偽の roots を渡しても、coordinator の設置先 repo 内の work_root を mkdir 前に拒否する | はい |
| `test_prepare_group_rejects_self_consistent_foreign_git_identity_before_any_mkdir` | config の git identity まで整合させた別 repo に差し替えても、設置先の anchor が残って拒否する | はい |
| `test_prepare_group_accepts_external_root_with_anchor_union` | 本当に外部の root は受理され、設置先 anchor と caller roots の和が roots になる | はい (設置先 anchor の確認) |

3 件とも「coordinator が自分の設置場所 (`Path(__file__).parents[2]`) から anchor を導き、caller や config の
偽 identity では外せない」ことの検査である (D349)。既存の `hermetic_git_identity` fixture は
`resolve_git_identity` を差し替えるので、これに寄せると設置先からの導出が検査されなくなる。
D1101 も同じ理由で「全 node を hermetic にする」を却下している。したがって md_4 の方針
「実 repo が本質なら理由を書いて止める」に従い、3 件は live のまま残した。
共有 repo の状態への依存は、本番関数の修正で撤去途中の状態については外れる (次節)。

## 本番の変更 (ユーザー指示)

`repository_roots_from_git_identity` で、管理 dir の `gitdir` が不在 (open が FileNotFoundError) で、
かつ同じ管理 dir の `locked` が lstat で不在のときだけ、その管理 dir を飛ばす。

- `locked` が在る (通常 file・symlink・directory を問わない) → 従来どおり `cannot read worktree registration: file is absent` で拒否
- `locked` の lstat が FileNotFoundError 以外で失敗 → `cannot inspect worktree registration lock` で拒否
- symlink の gitdir、非 regular、読み中変化、非 UTF-8、解決不能、管理 dir が file (ENOTDIR) → 従来どおり拒否
- 空の gitdir を飛ばす既存の扱いは不変

md_4 の逐語案 (gitdir 不在なら一律に飛ばす) より狭い。`locked` を見る理由は次節の実測。

### 根拠: git と撤去 tool の書き込み順 (実測)

git 2.34.1、job dir 配下の一時 repo (非 submodule)、strace 各 1 回:

- `git worktree add`: 管理 dir 作成 → `locked` 作成 → 作業木 dir 作成 → `gitdir` 作成 → … → `locked` 削除
- `git worktree remove`: 作業木の `.git` 削除 → 作業木 dir 削除 → 管理 dir の `gitdir` 削除 → 残りの管理 file 削除
- `tools/dev_wave_cleanup.py` の撤去: unlock → 作業木を `shutil.rmtree` して不在を確認 → 管理 dir を削除

したがって観測した 3 経路 (git 2.34.1 の add / remove と `dev_wave_cleanup.py` の撤去) に限れば、「`gitdir` 不在かつ `locked` 不在」は
作業木がまだ作られていないか、既に消えた状態である。submodule 付きの木・Lustre 上の中断・move / repair / prune は実測していない。
add 途中の「`locked` あり・`gitdir` 無し」は作業木が在りうるので拒否に残した。

### 受理集合がどう変わるか (検査の意味は変わる)

- **広がる:** `gitdir` 不在かつ `locked` 不在の登録について、その作業木だった path の中の work_root / output_root を
  外部として受理する。従来は走査ごと拒否していた。D1101 が本番に `missing_ok` 相当を入れる案を
  「roots を減らす向き」として却下した判断を、ユーザー指示で改める (新しい D)。
- **除外できない残差:** 手で `gitdir` だけを消した生きた作業木は roots から落ちる。git 自身もそのような登録を
  prunable (生きていない) と扱う。
- **新しい攻撃窓ではないもの:** 列挙の後で add が始まった登録を飛ばす結果は、その管理 dir が列挙の直後に作られた場合と
  同じ roots であり、現行でも並行 session が取れる timing を超えない。
- 実測の範囲は上記 (2.34.1・add/remove・非 submodule・各 1 回)。`worktree move` / `repair` は `gitdir` を
  書き直すので一瞬空になりうるが、空の扱いは既存のまま。

## 残る停止窓 (本修正で消えないもの)

- add 途中 (`locked` あり・`gitdir` 無し) と読み中変化 (F670) は従来どおり拒否する。
  テストは既存の `_with_live_authority_retry` (3 回・sleep なし) で吸収し、本番の coordinator には再試行が無いので止まりうる。
- `docs/dev-wave/operations.md` の DW-O11 にある「受入の走行中は撤去を避ける」は、撤去途中の不在については理由が消えた。
  add と読み中変化の窓は残る。この文の改訂は本 wave の所有外なので、次の一手に登録した。

## 検証

いずれも実装 commit `83ac3f959` に対して行った。

- 焦点走 (wave 木、計算ノード request 36204.nqsv、Elapse 76 秒): `test_t810_coordinator.py`・`test_t810_pbs_wrapper.py`・
  `test_real_repo_serialization.py` で 193 passed・1 skipped・1 failed。赤の
  `test_real_repo_serialization.py::test_real_repo_writers_do_not_materialize_oracle_environment_candidates` は
  内部で呼ぶ `test_p3_s4_loop` の campaign lock identity 不一致で、lock identity の計算は変更 file を参照しない。
  同じ tip の単独再走 (下位 node 込み 2 件) は 2 passed で、非帰属とした。
- 変異 (独立 clone `HEAD=83ac3f959`、`tools/mutation_worktree.py` の束ね経路 1 job)。期待 node は probe
  (request 36268.nqsv、全件 SURVIVED 期待で観測) の赤 node 完全集合をそのまま登録し、final (request 36291.nqsv、
  Elapse 275 秒) で baseline 緑・6/6 KILLED:

  | ID | 置換 | 赤になった node (完全集合) |
  |---|---|---|
  | M1 skip 撤去 | lock 不在でも不在エラー | `skips_unlocked_missing_registration_file` |
  | M2 lock 無視 | gitdir 不在なら lock を見ず continue | `rejects_locked_missing_registration_file` の 3 param、`rejects_lock_stat_error` |
  | M3 symlink も skip | symlink gitdir を continue | `rejects_symlink_registration_file` |
  | M4 open 失敗を不在扱い | `_read_regular_bytes` の拒否を捕捉して None | `rejects_non_regular_registration_file`、`rejects_registration_changed_during_read`、`rejects_non_enoent_registration_open_error` |
  | M5 lock 確認不能を skip | lstat の非 ENOENT を continue | `rejects_lock_stat_error` |
  | M6 lstat → exists | lock 判定を `os.path.exists` に | `rejects_locked_missing_registration_file[broken_symlink]`、`rejects_lock_stat_error` |

  M4 で `rejects_non_enoent_registration_open_error` が赤になるのは文言差だけである (管理 dir が file だと続く lock 確認も
  ENOTDIR で拒否する)。M4 の受理集合の変化を示すのは非 regular と読み中変化の 2 node。live 3 node はどの変異でも赤にならなかった
  (独立 clone では他 wave の churn が無い)。
- 受入全走は記録 commit の後に行う (結果は land の受領証)。
