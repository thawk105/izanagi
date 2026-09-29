---
schema: izanagi-spool-v1
ledger: decisions
authored: 2026-09-30
wave: dev-wave-cleanup-skill-revision
seq: 2
---

## {{D:cleanup-stale-delete-default}}. `/cleanup-branches` は「残す対象」以外の古い・価値の小さい木と branch を、施錠・未取込でも repo 外へ退避してから消す

**決定 (ユーザー指示 2026-09-29 15:5x JST「main に取り込むものがない・取り込む価値が小さい・古いものはどんどん消して」
「cleanup branches スキルでやれるようにして」、21:4x JST「削除で失われていいコミットもある。hello world とか、研究に取り込む価値のない
ちょっとした検証やお試しコード」、22:5x JST「私がやらなければいけない仕事を増やさないで。cleanup-branches というスキルでやりなさい、今後も」
(cleanup 実行 session 経由の中継を、本 wave の session でユーザーが「やれば？」で採用) に基づく):**

- 既定を「消す対象を条件で選ぶ」から「残す対象を列挙し、他は消す」へ反転する。残すのは main / primary checkout、占有 (cwd・cmdline)、
  HEAD・tip が直近 (目安: 稼働 wave の開始以降か 6h 以内) に動いた木・branch、稼働 session の主題の木・branch (棚卸し後に起動した
  同系列の新 wave を含む)、現行 docs (phase doc・worklog 末尾の次の一手・decisions) が残す・保存と名指しした branch、land 中の wave の
  branch、稼働 wave の manifest (`child-worktrees.json`) に載る子木、棚卸し後の新規、原本の置き場 (insight が計測原本の所在と名指しする木と
  未追跡 `output/` の原本、`dev-wave-jobs/` の投入木を含む)。止まった wave の manifest は子木を保護しない。
- 残す対象以外は施錠・ahead>0・未着地・dirty・rescue 判定不能でも消す。損失ゼロは要件でない。
- 消す前に repo 外 `/work/1/SFC/tanab/dev-wave-jobs/cleanup-branches-<日付>/` へ退避する: ahead>0 の削除 branch の 1 本の bundle
  (`^main`、create + verify + list-heads 一致。ahead=0 は main にあるので bundle しない)、main に無い detached HEAD と submodule HEAD の
  木ごとの bundle、追跡差分 (`diff HEAD --binary`)、未追跡と `output/` 下の ignored の tar (件数照合、F1034)、submodule 内の差分・未追跡も同様。
  退避は安価なので既定で取るが、復元手順の検算までは要求しない (損失ゼロを要件にしないため)。
- 削除範囲は AI が Codex 2 役 (決定役・攻撃役の read-only consult) に掛けて決め、ユーザーへ確認・実行を回さない。
  land 中の wave の branch は残す。branch は名前と期待 tip の表で一括削除する。
- 施錠木は退避後に unlock する。land 調整役がいれば予告と OK を取る。撤去は、木を同じ file system のゴミ置き場へ mv
  (rename で数秒/本) → 全 mv 後に prune を 1 回 (調整役の PRUNE OK と dry-run 候補の同意集合との完全一致が条件) →
  実体を `cleanup_remove_dirs.py` へ 2 path ずつ背景で渡して消す (渡した全 path を同時に rm するので Lustre では多並列にしない)。
  全 job の終了 status と path 不在を確かめてから事後検査へ進む。Codex 経路は real prune をしないので mv も始めない。
- rescue gate (`check_branch_rescue.py --ledger-check`) の rc2 は削除を止めない。worktree 200 本超では `git worktree list` が
  tool の 8 秒上限を超えて必ず rc2 になるので、worktree 撤去後・branch 削除前に branch 候補だけで再走し、再び rc2 でも JSON を残して進む。
- 原本の置き場は tar の写しが SHA 一致でも消さない。写しへの移管は insight の所在更新を伴うので、cleanup 実行ではなく別 dev-wave が行う。
- 撤去・削除 script は対象を本文に名指しする。Claude Code の auto mode 判定に拒否されてもユーザーへ実行を回さず、
  名指しの形で再申請し、なお拒否なら迂回せず final で報告する。
- command の byte 予算を 7,437 から 9,064 へ上げる (完成本文 9,061 + 余白 3)。

**維持・supersede の対応:**

| 既存裁定 | supersede する文 | 維持する文 |
|---|---|---|
| D2197 | 経路 2 の条件 (i) 完了 entry、(ii) のうち locked checkout の除外、(iv) rescue gate の JSON を削除の前提とする部分 | 経路 1 (dev-wave 段 9)、bundle 退避、稼働 wave・棚卸し後の新規の除外、別の裁定が保持と名指しした対象を消さない、台帳転記を別 dev-wave へ引き渡す |
| D2042 | 決定「削除が成立する述語の連言と閾値は 1 つも変えない」(本決定は保持条件の列挙へ反転する)、安い条件のうち「foreign / locked / 所有不明の除外」「HEAD の古さ (目安 1h)」「worktree の HEAD の main 取込」、却下の「撤去を並列化する」のうち directory の実体削除 (本決定は mv 後の実体を 2 本ずつ並列に消す。detach・branch 削除・prune の直列は維持) | 安い条件 → 高い条件の評価順、全 surviving status の保存、破壊操作の直列化、ahead=0 の `-d` |
| D204 | — | /cleanup-branches を例外経路とする範囲、remote / push 境界 |

**理由:**
- 2026-09-29 の実走で、報告止まりの既定は worktree 223 本・branch 160 本超を残し、rescue gate が時間切れで必ず rc2、
  `git worktree list` が 7〜9 秒になった。ユーザーは報告止まりを拒み (「一覧に載せて報告するだけ？ゴミも？」)、スキルで消せるよう求めた。
  同日の手作業 (worktree 38 本撤去・施錠 7 本 unlock・branch 90 本削除・prune 59 件) で 223→167 本・`git worktree list` 1.7 秒になり、
  rescue gate が完走した (損失閉包 92 commit、全件 bundle 内)。
- 退避 (bundle・tar) は repo を変えず安価 (同日 119 本で約 50 分、tar 計 22 MB)。損失ゼロを要件にしない代わりに、戻せる形は既定で取る。
- 原本の置き場を残すのは、Codex 2 レンズ (決定役・攻撃役) が同日「insight が原本の所在として名指しする投入木は、tar 写しが SHA 一致でも
  原本 path を消すのは別問題」「登録だけ外す案は Git の再現手順と submodule を壊すので不可」と判断したためである。移管は所在記録の更新で、
  cleanup 実行の許可集合 (repo file を変えない) の外にある。
- mv 方式は同日の 3 回目の撤去で使った (50 本を名指しで mv、後で prune、実体は 2 本ずつ削除)。`cleanup_remove_dirs.py` への 1 本ずつの
  前景撤去は 1 本 75〜250 秒で、200 本規模では数時間かかる。rename は共有 git metadata を触らず、prune は 1 回に畳めるので、
  D2042 が並列化を禁じた detach・branch 削除・prune の直列性は保たれる (並列にするのは実体の削除だけ)。
- rescue gate の上限は tool を直さず手順で扱う。上限の変更は判定の受理集合を変え、worktree が減れば完走することを同日実測した。

**却下した選択肢:**
- `check_branch_rescue.py` の 8 秒上限を worktree 数に合わせて伸ばす — 受理集合の変更で、撤去後の再走で足りる。
- 旧予算 7,437 bytes へ圧縮して収める — §1 の読取 argv 規律・§3 の F26・§5 の push 失敗時手順などの安全義務を削ることになる (自己改善契約が禁じる)。
- 原本の置き場を写しへ移管してから cleanup 内で消す — insight の編集は cleanup の許可集合外。
