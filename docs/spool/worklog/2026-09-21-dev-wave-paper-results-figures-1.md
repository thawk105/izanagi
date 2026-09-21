---
schema: izanagi-spool-v1
ledger: worklog
authored: 2026-09-21
wave: dev-wave-paper-results-figures
seq: 1
title: 論文結果節の図素材 2 枚を作った — fig14 は A-1 sized attempt-0002 の単独記述図 (fig9 と同形の兄弟、生成器を attempt 別 exact pin 表で拡張し fig9 の bytes と着地閉包は不変、variance_plan_breach を描く)、fig15 は stock mocc 軽量 witness 4 arm × 60 走の G2 signal 検出率・CP 区間・曝露量 (repo 外 5 file を SHA-256 束縛する新規生成器、稿 §2 の値の逐語) (コード + test + docs、branch worktree-dev-wave-paper-results-figures)
---

## 本文

- 依頼 (台帳 ID 未起票、作図依頼) を段 1〜7 まで進めて記録した (段 8 の自己改善と段 9 の受入・land はこの記録の後)。受理集合が変わる (A-1 生成器の breach 拒否を attempt 別にし、D1752 の pin 表に entry を足す) ので軽量版でも段 2 plan・段 3 相談 2 本・段 6 レビュー 2 本 + 焦点再レビューを残した。記録 = `output/insights/2026-09-21/paper-results-figures/README.md`。
- 依頼 (1) は D2194 項 6 (2) の「必要になれば単独図 (fig9 と同形、caption_source = 本稿) を先に作る」経路で、同日 07:2x のユーザー再裁定「fig9b (2 attempt 並記図) は作らない」とは矛盾しないと判断した (brief P1、相談 2 本とも同意)。
- 段 3 相談の must-fix 4 件を段 4 で採用: fig15 の限定 (非 certifying・曝露 ≠ 性能・非有意 ≠ 同等性・G2 signal ≠ 根因) を図中に描いて可視 Text で検査 (F872 型)、禁止句は caption と可視 Text の両方を走査、測定条件を caption に、曝露は稿の記録値を数値列で示し推論区間を新設しない (FIGURE_CONVENTIONS §2 の局所適用判断)。
- 段 6: 計算ノードの焦点走 (pytest) で新 test 4 件が赤 — `str(exc) == msg` の完全一致が pytest の assert 書き換えで崩れ、子の plain runner では緑だった (新しい失敗型の候補として段 8 で failures へ送る)。先頭行比較へ fix。レビューの must-fix 2 件 (plotting README の照合先の誤記、新節の F36 引用) は親の docs で直した。F36 引用は `DW-S07` 自身が「hash 自己参照は禁止（F36）」と引く先例があり一部 refuted、既存節 (fig9〜fig13 節、plotting README の 3 節、attempt-0002 稿、DW-S07) の同じ引き方は変えていない。
- 変異 final (dispatch、fix commit `fc6c4f836`) は KILLED 14 / SURVIVED 1 (等価対照) / MISMATCH 0。M8 (CP 上限の分位) は summary cp95 照合層との二重検出の過剰決定として単独変異の証拠から外した。
- 計算ノードは焦点走 2 回・変異 final 16 run・全史 provenance 監査・受入だけで、2026-09-21 の確認ライン (1 タスク 2 node 時間) を下回ると判断し確認は求めていない。
- 受入所要時間台帳は登録しない (login の collect-only で被覆 98.18%、余裕 2,459 node)。
- 工数: codex 子 10 本 (plan 1、consult 2、author 2、review 2、fix 2、focus 1、全て gpt-6-astra / medium)、read-only 調査子 1 本。wave の壁時計は開始 gate 20:46 JST → 記録 commit まで。受入全走と land の結果は本 entry には書けない (記録 commit の後に受入を投入するため)。

## 次の一手差分
