<!-- 段 6 焦点再レビュー (DW-O16)。段 6 レビューと同じ Claude の read-only 子 (general-purpose、model=opus) に、訂正後の README・fragment・NORMALIZATION.md を点検させた最終報告の逐語。harness が各行に付けた 2 字下げだけを除いた。 -->

## 対応表

対象は未 commit の作業ツリーで、README (`output/insights/2026-09-21/r29-items4-9-diagnosis/README.md`)、fragment (`docs/spool/worklog/2026-09-21-dev-wave-r29-items4-9-diagnosis-1.md`)、`verbatim/NORMALIZATION.md`、新しい写し 2 本を見た。行番号は訂正後の版の値。

| 前回所見 | 状態 | 根拠 |
|---|---|---|
| 1 fragment の工数行 (must-fix) | closed | fragment:33–34 は「codex 子 = plan 1 + consult 1 … 段 6 review の codex 子は利用上限で出力 0 (不受理、再試行せず)、段 6 は Claude の read-only 子 1 本 (opus) が代行」と改めた。fragment:18–22、README:5、README:215–216 も同じ内容で揃っている。D582 (`docs/decisions.md:23485`「codex 子の即死は … 即時エスカレーション」) と先例 entry 1800 (`docs/worklog.md:2714,2716`) は実在する。`hooks/guard_agent.py:3,78–79` (model 未指定の Agent 呼び出しを止める) も実在する。 |
| 2 plan 由来の引用 2 件と二重記録の費用 | closed | README:79–81 と :87 は計算ノード側の経路を `run_tests.py:1296–1299` → allowlist `dispatch_compute.py:123–126` → `run_tests.py:2682` / `:2690–2694` に直した。README:88 は `orchestrator/tests/conftest.py:1936–1948` (`_growth_holds_opted_in`) に直した。README:93–94 は二重記録を既存の marker が防ぐ旨に直した。いずれも現物と一致した。行番号の細部は新規所見 N2 を参照。 |
| 3 t2810 の held 診断 job | closed | README:49–50 で定義から held 診断 job を除いた。README:58 は t2810 = 2 / 1 / 1〜2、README:62 は計 9 / 11〜20。README:64–65 で除外の理由と「数えると 10 / 10〜20」を明記した。README:66 の仮定から held を外した。§0:14、§6:180–181、§7:197、題名、fragment:7 と :51 も揃っている。 |
| 4 上下限の範囲 | closed | README:15、:44 (「本節の『既存走』は計算ノード焦点 job に限る」)、:69–70、:197、fragment:52 に明記した。README:70 の引用先 `t2797-b5-contrast/README.md` §4 は 83–93 行で、前回根拠とした 90 行を含む。 |
| 5 T-2737 は D2194 項 8 の根拠例 | closed | README:27、:159–161、fragment:24 と :42 に追記した。`docs/archive/worklog-phase3-0920-1695.md:1,3–4` (見出しと 1 項目) と `docs/decisions.md:69801` の理由欄の記述は一致する。索引 `final-index.md` に T-2820 / D2194 / 1695 の hit が 0 であることは前回確認済み。 |
| 6 「88 %」の分母 | closed | README:23「固定費の 88 % (1,066 秒、うち待ち 1,050 秒) … wall で見ると S07 は 1,336 秒の 81 %」。README:187 と fragment:28 も「固定費の 88 % (wall では 81 %)」。題名と fragment:55 は「うち 1 本が 1,066 秒」。 |
| 7 待ちの帯の定義・再提示の目安・根拠の強さ | closed | 待ちの帯: README:139–141 で ≥ 300 秒 (12 / 27、337〜1,020 秒) と 17 分前後 (3 本) を分けた。M3 費用欄: README:181 で量を揃えた (固定費 18〜26 秒、S07 は固定費 1,066 秒で待ち 1,050 秒)。根拠の強さ: README:187–189 に「見積りの無い状態での判断」と明記した。蹴った帰結: README:191 は 337〜1,020 秒 / 1,050 秒。再提示の目安: README:192 を「≥ 300 秒が 2 wave 以上」と定義した。fragment:29–30、:56–57 も同じ内容。 |
| 8 S01 − S10 の 27 秒 | closed | README:163–164「node・時刻・順序が交絡した値で、どれにも帰属できない」。 |
| 9 contract/ の正規化が未記録 | partial | NORMALIZATION.md:6–19 に節と表を足した。表の値は下の再検算ですべて一致した。ただし同 file の冒頭:3「次の写しは行末の空白 (space / tab) だけを削った」が残っており、直下の contract/ 節 (末尾空行の削除) と食い違う (N1)。 |
| 10 `/tmp/.git` の根拠 | closed | README:20 と :107 に、親の `ls -ld` 出力 (makiart、9 月 7 日 18:07、size 6) と段 6 の 15:42:07 の再観測、F457 を記載した。`_has_git_ancestor` は `orchestrator/campaign/layout.py:312` に実在する。 |
| 11 D2194 項 8 の引用 | closed | README:155–156 は要旨の書き方に改めた。内側の「production file を変えた wave は inventory test 4 群を参照関係に依らず焦点走に含める」は D2194 項 8 の決定文 (`decisions.md` の項 8 決定行) の逐語と一致する。 |
| 12 「残る分 = RUN 128 秒」 | closed | README:22–23 と :136 は「pytest 合計 120.42 秒〜RUN 128 秒」「消せるのは最大でこの固定費」「RUN との差の一部は束ねれば消える」。README:134–135 は差 7.6 秒の中身を書いた。 |
| 13 title と [T-2832] | title は closed、[T-2832] の判断は妥当 | fragment:7 に [T-2843] を足した。[T-2832] の状態文「実現手段の決定待ち ([T-2842] の計測後)」は訂正後も偽にならない。計測は済み、決定は [T-2842] の再提示に移っただけなので、触らない判断は妥当である。ただし §9 表 (README:235) の理由「D2206 の記録 wave が持つ状態」は所有の規則ではない。実質の理由は「文言が引き続き真で、base の競合を避けられる」であり、書き方は nit。 |
| 14〜16 (refuted) | 維持 | README:161 と fragment:42–43 に「本 wave による DW-O26 改訂ではない」を追記した。 |

## 再検算

| 値 | README / fragment の値 | 再計算 (原データ) | 一致 |
|---|---|---|---|
| t2810 の集合走 / 置換上限 / 残件 | 2 / 1 / 1〜2 | focus_runs_table.md の t2810 計算ノード job 3 本から focus-held-1 を除いて 2。min(2−0, 2−1) = 1、max(0, 2−1) = 1、上端 k − s = 2 | 一致 |
| 置換上限の計 | 9 | 1+0+2+1+1+2+2 = 9 | 一致 |
| 残件の計 | 11〜20 | 下限 2+0+3+0+1+0+5 = 11、上限 3+0+5+1+2+2+7 = 20 | 一致 |
| held 診断 job を数えた場合 | 10 / 10〜20 | t2810 を 3 / 2 / 0〜2 とすると 10 / 10〜20 | 一致 |
| S07 の wall 比 | 81 % | 1,081 / 1,336 = 80.9 % | 一致 |
| 固定費比 / 待ち | 88 % (1,066、うち待ち 1,050) | 1,066 / 1,208 = 88.2 %、S07 の待ち 1,050 (Created 14:59:39 → Started 15:17:09)。待ちだけの比 (86.9 %) は本文に書いていない | 一致 |
| 残る分 | pytest 合計 120.42 秒〜RUN 128 秒 | 4.85+5.21+5.17+78.84+7.24+13.40+5.71 = 120.42、RUN 6+6+6+80+9+15+6 = 128 | 一致 |
| 前回の待ち ≥ 300 秒 | 27 本中 12 本、337〜1,020 秒 | 前回 focus_runs_table.md の計算ノード 27 本の待ちが 379 / 689 / 413 / 669 / 1007 / 384 / 715 / 577 / 375 / 1020 / 1020 / 337 の 12 本。最小 337、最大 1,020。前回 README:41 とも一致 | 一致 |
| 前回の 17 分前後 | 3 本 (1,007 / 1,020 / 1,020) | walldecomp focus-2 1007、residue f2 1020、f4 1020 | 一致 |
| `run_tests.py:1296–1299` | `_dispatch_environment` が task_run_id を外し AUTO_RECORD=0 を設定 | 1296 は `pop(_TASK_RUN_ID_ENV)`、1297 は SIDECAR、1298 は RUNS_ROOT、1299 は `[_TASK_RUN_AUTO_RECORD_ENV] = "0"` | 一致 |
| `run_tests.py:2682` | pytest command を組む | `cmd = _build_pytest_command(...)` | 一致 |
| `run_tests.py:2690–2694` | `subprocess.call` | 2690 は `if not task_run_id:`、2691 は `== "0"`、2692–2694 は `subprocess.call, cmd, cwd=_REPO` | 一致 |
| `dispatch_compute.py:123–126` | tests allowlist で転送 | 123–124 はコメント、125 は SIDECAR、126 は AUTO_RECORD。計算ノード側は task_run_id を 1844 で外し、allowlist 内の 2 変数は 1848–1850 で保つ | 一致 (README:94 の「123–125 のコメント」は N2) |
| `orchestrator/tests/conftest.py:1936–1948` | token 検査 | `_growth_holds_opted_in`、exact token 以外は `UsageError` | 一致 |
| NORMALIZATION の contract/ 表 (7 file × 原本 / 写しの sha256・bytes = 28 値) | NORMALIZATION.md:13–19 | job dir の `verbatim/contract/` と repo の写しを sha256sum / wc -c で取得し、全値一致。写しは git 上で無変更 | 一致 |
| entry 1695 | T-2737 の受入赤 3 件 | `worklog-phase3-0920-1695.md:1` の見出しは「[T-2737] … 受入で出た define 目録の赤」、:4 は「`test_ccbench_spawn_sites.py` の define 目録 3 件で赤」 | 一致 |
| D2194 項 8 の理由欄 | 「entry 1695 (`test_ccbench_spawn_sites.py` の受入赤 3 件) で再発」 | `docs/decisions.md:69801` の該当句 | 一致 |
| t2797 の login 実走の引用 | 同 insight §4 | §4 は 83–93 行、該当は 90・92 行 | 一致 |
| 段 6 の件数 | must-fix 1 / should 6 / nit 6 / refuted 3 | 前回所見 1 / 2–7 / 8–13 / 14–16 | 一致 |
| `verbatim/prompt-s6-review.md` | 依頼の写し | job dir の `codex/prompt-s6-review.md` と cmp で一致 | 一致 |

## 新規所見

- **N1 real / nit — NORMALIZATION.md:3 の冒頭文が古いまま残っている。**
  - 見出しは「行末空白と末尾空行」に改めたが、冒頭文は「次の写しは行末の空白 (space / tab) だけを削った」のままである。
  - 直下の contract/ 節 (:6–9、末尾空行 1 byte の削除) と食い違う。
  - 訂正案: 「measure/ と s3-consult.md は行末の空白だけを、contract/ は末尾の空行 1 行だけを削った」。
  - 放置時の影響: 冒頭文だけ読むと、contract/ の写しの正規化の型を誤認する。
- **N2 real / nit — README:94 の行番号がずれている。**
  - 「`dispatch_compute.py:123–125` のコメント」とあるが、コメントは 123–124 で、125 は `_TASK_RUN_SIDECAR_ENV`。
  - 前回報告の所見 2 (c) 自身の書き方が出所である。README:80 の「123–126」(allowlist の範囲) は正しい。
- **N3 判定不能 / nit — `verbatim/s6-review-claude.md` の「逐語」表示に、引用符の差がある。**
  - ヘッダは「2 字下げだけを除いた」と書く。しかし写しでは次の 2 か所が直線引用符 (`"` と `'`) になっている。
    - 所見 1 の “You’ve hit your usage limit …”
    - 所見 2 (c) の “The marker keeps …”
  - 前回こちらが送った本文では曲線引用符 (“ ” ’) だった。写しの曲線引用符は 0 字。
  - 親が受け取った時点で変換済みだったかは、こちらから判定できない。変換が親側なら、ヘッダに書き足すか元に戻す。
  - 他の構成は送った本文と一致する (5 節、所見 16 件、表の行)。
- **N4 real / nit — fragment の本文が長い。**
  - fragment の本文 (:12–34) は 23 行ある。`docs/worklog.md` 冒頭は、監査の要約を「レンズ数・real/refuted 数・最重要 1〜3 件・一次資料ポインタの 10〜15 行」としている。
  - 段 6 の段落 (:18–22) は insight §9 の対応内容 (t2810 の除外、引用 2 件) を再掲している。
  - 「NO-GO と件数と §9 へのポインタ」に縮められる。任意。
- **refuted — 訂正で新しく生じた誤り・README と fragment の不一致は見つからなかった。**
  - 旧値 (「最大 10」「10〜20」「費用の 88 %」「長待ち 3 本」「ノード間の差」「:1260」「held 1 を含む」、root 相対の `conftest.py`) は、§9 の対応表と「数えると 10 / 10〜20」の注記以外には残っていない。
  - README の題名・§0・§2・§6・§7 と fragment の題名・本文・[T-2842] / [T-2843] の数値と表現は互いに一致する。
  - README:81「以後の main の差分は docs のみ」: d99c556df..bea98c67d で docs と output/insights 以外に変わったのは `.claude/commands/next-tasks.md` だけで、引用したコードの行には影響しない。

## 判定

**GO** (must-fix 0、新規は nit 3 件と判定不能の nit 1 件)。

## 総括

- 前回所見の対応: 1〜8、10〜12 は closed。9 は partial (NORMALIZATION.md の冒頭文の食い違いだけが残る)。13 は title が closed で、[T-2832] を触らない判断は妥当 (理由の書き方だけ nit)。
- 訂正で足した派生値はすべて原データと一致した。置換上限 9、残件 11〜20、t2810 の 2 / 1 / 1〜2、wall 比 81 %、固定費比 88 %、120.42〜128 秒、前回の 12 / 27 (337〜1,020 秒) と 3 本、contract/ の sha256・bytes 28 値、entry 1695 と D2194 項 8 の理由欄。
- 引用したコード行 (`run_tests.py:1296–1299` / `:2682` / `:2690–2694`、`dispatch_compute.py:123–126`、`orchestrator/tests/conftest.py:1936–1948`) も現物と一致した。
- 訂正による退行や、README と fragment の不一致は無い。
- 残りの nit は任意で、直すなら次の 4 件: NORMALIZATION.md:3 の冒頭文、README:94 の 123–124、段 6 レビュー写しの引用符の注記、fragment 本文の短縮。
- fragment を書き換えたので、記録 commit の前に `python3 tools/check_docs.py` と `python3 tools/spool_fold.py --dry-run` を訂正後の木で通し直すこと (README §10 は未記入)。
- この点検は読み取りと再計算だけで行い、編集・テスト・dispatch はしていない。
