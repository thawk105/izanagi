# 段 6 裁定 (親、2026-09-21 01:2x JST、レビュー = `s6-review.md`、NO-GO: must-fix 1 / nit 1)

## 所見 1 (B、must-fix) — real、採用、fix 1

新文 §3「`ls-files -o` の list と entry 数が一致しなければ撤去しない」は、一次資料 loss record §4「tar の**非 dir entry 数**が list 数を**下回れば**撤去せず rc=6」と
受理集合が異なる。tar は directory entry も数えるので、(i) 非 dir 71 + dir 1 = 72 で総数一致なら不足を見逃す (危険側)、(ii) 全 file を含む退避でも dir entry の分だけ総数が
list を超えて「一致」に失敗し誤停止する (安全側だが一次資料の条件ではない)。親の対応表 A2 が「一致」を「非 dir・不足時停止」と対応済みと扱ったのは誤り (親裁定への反証を採用)。
**放置時の成果物影響:** 引き渡す撤去手順が、不足した退避を受理しうる / 全対象を含む退避を拒否しうる。

fix: §3 の該当文を「`ls-files -o` の list 数を tar の非 dir entry 数が下回れば撤去しない (F1034)」へ (親 docs、+9 bytes)。予算のため §4「cleanup 前の status を保存し、」を
「§1 の status と比べ、」へ縮約 (−10 bytes、§1 が「§4 用に保存」を既に命じており「保存し」は重複、「比べ」は §4 の検査の意味を明確化)。SKILL.md overlay の「entry 数照合」は
「非 dir entry 数照合」へ (+8 bytes、余白 40)。(byte 数は焦点再レビュー nit 2 で訂正: 当初 +10 / +7・余白 48 と書いていた)pin 追随 (check_docs sha 定数 2 個、test_check_docs fixture literal 2 本・sha・bytes) は Codex fix 子 1 本 (段 5 契約継承、
既存 test の期待値不変)。failures fragment・reduction-table・worklog 草稿の引用を追随。

## 所見 2 (A/D、nit) — real、記録で対応

R6「`git log` で確認」は手段指定であり、新文は別手段の確認も許す。撤去集合の拡大は立証されない (main 包含確認・§2 取込条件・`action: keep` は残る) が、対応表・worklog の
「9 件すべて意味不変」は過大。→ 対応表と worklog を「8 件は意味不変の縮約、R6 は確認義務を保持し手段指定 (`git log` で) を落とした」に改める。本文は変えない (bytes 余白なし、
確認手段の限定は F51 / DW-O28 の tool 側にあり command の義務ではない)。

## 反証なし (採用): P1 配置、P2 F 参照、P4 overlay、T-2601 閉鎖、R1〜R5・R7〜R9、pin 整合 (6,201 / 3,052、NFC、超過入力 6,205)、helper 8 変異の増分 3/10/17/9/2/9/14/2 < 21。

## fix 後の再検証 (DW-O16 / DW-S06-C)

- 焦点再レビュー 1 本 (read-only、所見 1・2 の closed / partial / regressed 表を要求)。
- 変異 final は fix 最終 commit を anchor に (DW-M07)。probe (92263e53e) の観測 node は集合として流用し、final の MISMATCH 0 で再検証する。m1 / m3 の old anchor (command sha) は fix 後の値へ。
- 焦点走は fix 統合 commit 後の wave 木で 1 job。

## 追記 (01:29 JST) — fix 2: 稼働中だった cleanup session の final の罠を反映 (引数の明示 scope)

依頼が「稼働中の cleanup session (00:15 起動) の final が返す罠があれば文言に反映する (そのために待たない)」と定めた件。同 session は 00:20〜00:36 JST に完走し
(worktree 42 → 4 撤去、branch 4 削除、巻き添え 0)、final の罠として「**棚卸し後に lock 状態が変わる** — 実行中 (00:29) に /rulings session が submit-tree-pair を
F1034 同型の理由で locked にした。§2 高い条件の直前再確認に施錠の有無を含める (prune は locked を跳ばすが dir の rm はその前に済む)」を memory `cleanup-discipline`
(2026-09-21 節) に残していた。待たずに済んだので反映する。

fix 2 (親 docs): §2 高い条件「削除直前に §1 の status 空を再確認。」→「削除直前に status 空と非施錠を再確認。」(+4 bytes → 6,204 = 予算ちょうど、check_docs の判定は
`>` なので緑。「§1 の」を落とすのは、削除直前の再確認は新規取得の status であり §1 保存分との比較は §4 が担うため)。施錠の判定手段 (`git worktree list` の locked 表示 /
admin dir の `locked` file) は §2 安い条件の「locked … は inventory/report のみ」と F51 の流儀に従い本文へ書かない (余白 0)。SKILL.md overlay は変更なし
(command §2 を不可分に適用するため)。pin 追随は fix 子 2 巡目 (bytes assert 6_204、超過入力 padding 0)。fix 1・fix 2 をまとめて焦点再レビュー 1 本。

## 追記 (01:45 JST) — fix 3: 予算ちょうど (余白 0) は既存 test 契約と衝突する

fix 子 2 巡目 (pin 追随後の焦点走) が指示どおり停止して報告: `test_cleanup_command_leading_space_h2_is_rejected` は byte-neutral helper を使わず H2 の先頭に空白 1 byte を
足すので、本文 6,204 だと合成 repo の check_docs が「6205 bytes > 予算 6204 bytes」+「whole-file SHA-256 が契約と不一致」の 2 件を出し、期待違反件数 1 が崩れる
(本差分起因、期待値は変えない)。**新事実: command 本文は予算ちょうどにできず、helper 非利用の mutation test の分 (先頭空白 +1 byte) の余白が要る。** fix 3 (親 docs):
§5「remote branch の削除と main の push」→「remote branch 削除と main の push」(−3 bytes、意味同一) で 6,201 (余白 3 = 段 5 author 全件緑の実績値)。fix 2 の 1 文は保持。
docs commit `8901d6b62` (command sha c8db749b…)。fix 子 2 巡目の unit 終端 commit 7907abd8b (6,204 向け pin) は統合に使わない。fix 子 3 巡目で pin 追随。

## 追記 (02:17 JST) — 焦点再レビュー (`s6-rereview.md`): GO

所見 1 closed (§3 は非 dir entry 数 N < list 数 L で停止、N=L・N>L は拒否せず loss record §4 と一致。overlay も同条件)、所見 2 closed (対応表・worklog で「確認義務は保持、
手段指定の削除 1 件」に訂正済み)。fix 2 妥当 (棚卸し後の lock を見落とす経路を手順上塞ぐ、「§1 の」を落としても新規取得の status と読める、安い条件の locked 除外と時点が違い矛盾しない)、
fix 3 意味不変、R10 意味不変、退行なし、余白 0 の新事実は整合、F1034 supersede の要約は条件を保持。静的照合: command 6,201 / c8db749b…、SKILL 3,060 / 3cf0344d…、両方 NFC、
超過入力 6,205、先頭空白変異 6,202。新規 nit 2 (記録面のみ、本文・pin の変更なし): (1) worklog 草稿の巡数の混在 → 「本文修正 3 回、Codex fix 子 4 巡 (最終巡は監査)」に分け、
2 巡目 (pin 変更後の test 失敗で停止) と 2・3 巡目の証拠未受理を別々に書く。(2) 裁定・対応表の byte 算術 (fix 1 は §3 +9 / §4 −10 / overlay +8・余白 40) と削減見出しの件数 → 訂正。
