# Stage 6 所見裁定

## 採用する must-fix

1. ignored/excluded でも `.claude/worktrees/` / `.codex/worktrees/` は常時列挙し、Git admin との
   双方向束縛を検証する。target tree が foreign control-plane path または既存 ignored path と衝突する
   land も mutation 前に拒否する。既存の無関係な ignored cache 全体を dirt 扱いにはしない。
   未実装なら invalid/衝突 artifact を含む main を受理し、foreign 所有物を変更し得る。
2. common lock を shared mutable main/config/history/head の検査より前に nonblocking 取得する。
   未実装なら正常な loser が `busy` でなく transient tracked dirt の `rejected` となる。
3. handoff/worktree control-plane snapshot は pathname set だけでなく、検査を挟む前後の
   identity/binding を比較して replacement を fail-closed にする。未実装なら検査済み path と
   実際に例外受理した inode が食い違い得る。
4. local だけでなく include/worktree scope を含む effective Git config の filter/promisor を拒否し、
   lock 内で history/config を再検査する。merge failure 後の dirt と HEAD 観測不能は retryable な
   `not-landed` に潰さず non-retryable postcondition failure とする。未実装なら外部 filter child、
   partial main mutation、誤った再試行を受理境界へ入れる。
5. gitlink-changing A..T は初回 land 後に D16 sync を要求するが、同じ A/T/audited evidence のまま
   実 submodule が T と同期済みなら `already-landed` へ遷移できるようにする。未実装なら正当な
   gitlink wave を永久拒否するか、監査列を空にする laundering が必要になる。
6. audited 列の逆順、余分、同長別 commit を独立負例で固定する。未実装なら将来の set 比較への
   弱体化が監査 provenance を失わせても検出できない。
7. `test_real_repo_clean` の Stage 5 遷移用 6 finding allowance を削除する。親 docs は統合済みであり、
   残すと共通 land topology の coordinated deletion が green になる。
8. helper path は operations 全体でも O23 の exact 1 件だけに限定する。Codex adapter の共通 land
   文言を exact pin し、command/Skill に明白な別 helper・直接 ff mutation を足す負例を置く。
   未実装なら checker/test が第二の通常経路を同時に見逃す。
9. same-base E2E は winner land 後、loser が winner を取り込んだ exact tip に独立 acceptance step を
   束縛し、`tested_main=winner_tip` と新 A..T closure で再試行する。旧 base の evidence 流用を
   「再受入」と呼ばない。未実装なら dispatcher から再受入が落ちても E2E が green のままになる。

## 一部採用または scope 外

- 任意の ignored cache を dirt とする案は不採用。現 main に正規の Python cache 等があり、既存 strict
  cleanliness も ignored artifact を対象外にする。採用範囲は control-plane の常時検査と target collision。
- pathname 変更を完全に防ぐ長時間 FD/全 writer lock は不採用。協調 same-host manager の threat model
  内で、観測窓の前後 identity 比較と mutation 直前再検査までを必須とする。
- main/wave root rename、lock file unlink、悪意ある same-UID Git admin writer、cross-host flock は
  plan v2 どおり scope 外。
- O23 を段 5/6 の operation 集合から外す所見は成果物影響を示せないため backlog。今回の must-fix にしない。

## fix 単位

helper、land test、docs checker、checker test は failure taxonomy と共通 topology が相互依存するため、
一枚岩の Codex author fix 単位とする。所有はこの 4 file に限定し、親 docs は親が統合する。

## 焦点再レビュー後の第 2 fix 裁定

- #1 partial は採用。ignored directory record と target の単なる sibling は許可し、既存 ignored
  file/dir 自体を置換・包含する exact overlap だけ拒否する。無関係 sibling の拒否は正当 wave の
  受理集合を縮小する。
- #3 partial は採用。target/collision 検査後、mutation 直前に control snapshot を再取得し、
  先の snapshot と一致しなければ merge しない。
- #5 regressed は採用。A にあり T から削除された gitlink path も追跡し、残存 submodule worktree /
  nested Git metadata が消えるまで同じ evidence の `already-landed` を許可しない。
- #8 partial は採用。任意の prompt marker、`git -C <main>`、`python` / `python3`、相対 `./tools`
  の明白な別 land command を捕捉する。通常 prose を shell command と誤認しない負例/正例も置く。
- #9 partial は採用。synthetic acceptance は subprocess の実 command として winner/loser content、
  exact tip/tree、cleanliness を検査し receipt を返す。retry request は receipt の main/tip を消費する。
  加えて共通 S09 の「受入結果を固定してから helper」literal を checker が pin し、dispatcher から
  再受入を消す regression は docs test が検出する。
- handoff の親追記を fix 子の所有違反とする所見は refuted。fix 子完了後に親が追記した時系列差分であり、
  子の変更ファイル報告時点では所有 4 file だけだった。

## 第 2 焦点再レビュー後の第 3 fix 裁定

- gitlink→通常 file の mode change を A-only gitlink residual と誤認する所見は real。T tree に
  非-gitlink entry がある path は通常 file/dir の存在を許し、旧 submodule worktree identity と
  Git modules metadata だけが消えていることを要求する。純削除の厳格さは維持する。
- `python3 -u` / `git --no-pager` の通常 global option で別 land command checker を抜ける所見は real。
  command-like 行に対して interpreter/global option の個数・順序へ依存せず、land script token または
  `git ... merge ... --ff-only` token 列を検出する。普通の inline prose 正例は維持する。
- これは fix round 3/3 とする。以後新しい NO-GO が出ても fix を重ねず、`DW-O16` に従い親が
  mutation と DW-G05 で real/refuted を最終裁定する。

## fix 上限後の最終裁定

- gitlink pure deletion / normal blob/tree replacement は最終焦点レビューで closed。
- checker が `python3 -m py_compile tools/alternate_land.py` と
  `git rev-parse -- merge --ff-only` を command と誤認し得る所見は事実として real だが、
  現行 command/Skill に該当行はなく、共通 O23 path、Codex adapter literal、helper 唯一路は別 gate で
  exact pin 済みである。現 wave の local main、受入結果、台帳値、Claude/Codex route の受理集合は
  変わらないため DW-G05 により backlog とし、must-fix にはしない。
- 将来 land-named script の compile 例または Git argv sentinel を command/Skill に書く必要が生じた時点で、
  shell token parser への置換を独立 wave で扱う。現在の regex をさらに列挙修正しない。
- fix round は 3/3 で終了。以下は事前登録 mutation と親受入で検出力を裏取りする。
