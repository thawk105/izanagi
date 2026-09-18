単独段 dispatch: stage=review; sandbox=read-only; parent=/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2674-t1998-results-doc

必読事項の射影:
- /work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2674-t1998-results-doc/docs/paper-story/results/2026-09-18-t1998-balanced-stock-inline-accepted.md — レビュー対象の統制稿 (新規、未 commit)。読めなければ即停止。
- /work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2674-t1998-results-doc/docs/paper-story/README.md — 「results 系列」節の表に足した 2026-09-18 の 1 行 (レビュー対象)。読めなければ即停止。
- /work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2674-t1998-results-doc/projection/README-results-series.md — results 系列の規則 (逐語)。読めなければ即停止。
- /work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2674-t1998-results-doc/projection/parent-brief.md — 親の段 1 brief (親自身も検査対象)。読めなければ即停止。
- /work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2674-t1998-results-doc/projection/D1874.md — 裁定 D1874 (逐語)。読めなければ即停止。
- /work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2674-t1998-results-doc/projection/D1993.md — 裁定 D1993 (逐語、項 6 が主)。読めなければ即停止。
- /work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2674-t1998-results-doc/projection/D2044-item3.md — 裁定 D2044 項 3 (逐語)。読めなければ即停止。
- /work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2674-t1998-results-doc/projection/D2120-item15.md — 裁定 D2120 項 15 (逐語)。読めなければ即停止。
- /work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2674-t1998-results-doc/docs/t1998-balanced-stock-inline-preregistration.md — 事前登録 v1 (一次資料)。読めなければ即停止。
- /work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2674-t1998-results-doc/output/insights/2026-09-13_t2557-balanced-stock-inline/README.md — 投入・回収・1 回目の解析。読めなければ即停止。
- /work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2674-t1998-results-doc/output/insights/2026-09-14_t2589-consumer-real-artifact-repair/README.md — consumer 是正と認証。読めなければ即停止。
- /work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2674-t1998-results-doc/output/insights/2026-09-15/t1998-landed-main-recheck/README.md — 着地後 main での再解析。読めなければ即停止。
- /work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2674-t1998-results-doc/docs/paper-story/results/2026-09-07-a2-certification-observed-positive.md — 同系列の既存の単独稿 (形の参照)。読めなければ即停止。
- /work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2674-t1998-results-doc/projection/wal-table-parent-derived.txt — 親が WAL から導出した表。読めなければ即停止。

## 依頼 (レンズ B: 過剰・削除、限定、過大主張、裁定整合)

あなたは read-only の敵対レビュー子である。書き込み可能な tmp は無いので pytest 緑は要求しない。静的検査だけでよい。
テストの実走は親が行う。予算が尽きそうなら途中結論を下の出力形式どおり書いて終われ (無出力が最悪)。

対象は docs のみの wave で、成果物は「[T-1998] balanced stock-inline 対の単独 results 稿」1 本と README の表 1 行である。
この稿は append-only の凍結物で、着地後は in-place で直せない。**着地前に、稿が言ってはいけないことを言っていないか、
言うべき限定を落としていないか、裁定と食い違っていないか、過剰な内容 (削るべきもの) が無いかを攻撃せよ。**
稿を守らず、検査せよ。親の brief (P1 / P2 の provisional 裁定を含む) も検査対象である。

ユーザー依頼の逐語 (稿の要件): 「[T-1998] balanced stock-inline 対 (2026-09-13 測定・2026-09-14 認証 accepted、improvement_percent 11.225375361916456、認可 D1874) の単独 results 稿を docs/paper-story/results/ 系列の規則 (docs/paper-story/README.md「results 系列」節) どおり書く (docs のみ) — 一次資料全体 (事前登録 v1、insights 4 dir、campaign WAL・権威 bytes・裁定) から作り直し、横断稿 results/2026-09-16-b7-three-run-materials.md で補完しない。権威 bytes・WAL・事前登録・裁定の対応が欠ける箇所は欠落として明記する。各 arm 5 標本の median 比であって A-1 の対差平均ではないこと、A-2 / A-6 とプールしないこと (D1993 項 6)、B-7 の要件充足ではないこと (D2044 項 3) を限定に書く。README の results 表へ 1 行足す。規律 2 を緩めない。本題の統制稿だけ。仮想リスク向けの gate・検査・台帳・一般化の追加は scope 外。」

攻撃観点:
1. **過大主張。** 稿のどの文が、一次資料が言っていないことを言うか (有意差・再現・最適量・機序・他 workload への転移・
   正しさの強さ・「証明」)。特に §2.4 (8 点表) と行 3 (2 µs) の扱い、§2.2 の abort 率・latency、§3 の限定 1〜20、
   §0 の「`accepted` は…という事実である」の言い方。
2. **裁定整合。** D1874 / D1993 項 6 / D2044 項 3 / D2120 項 15 / D12 / 絶対規律 7 の逐語と稿の記述が食い違う箇所。
   裁定の逐語より強い断定 (「決定」「確定」の語の濫用、裁定が言っていない帰結) を探す。
3. **落ちている限定。** 依頼が名指す 3 限定 (median 比 ≠ A-1 対差平均 / A-2・A-6 とプールしない / B-7 充足でない) が
   稿と README 行の両方に明示されているか。他に一次資料 (事前登録 §9、2026-09-13 README §6・§7、2026-09-14 README §2.3・§5、
   2026-09-15 README §5) が書く限定で稿が落としたものは無いか。
4. **事前登録前の生値 (D1874)。** 稿のどこかに 2026-09-07 の生値 (数値) が混ざっていないか。事前登録 §3 は数値を開示しているが
   稿は数値を書かない方針である — 方針が守られているか、方針自体が妥当か。
5. **8 点表 (親の P1)。** 事前登録 §2「残り 6 点を推定量へ代入しない」「argmax しない」と、8 点の値を表として載せることは
   両立するか。載せることで執筆者に事後選択を誘う害はあるか。載せるなら足りない注意書きは何か。削るべきか。
6. **正しさ検査条件 (親の P2)。** 「lock が束縛する pipeline.py blob の CorrectnessWorkload 既定値」を「束縛された code から
   導いた値」として書くのは妥当か。それは成果物の記録の代わりになるか、ならないか。書き分けは十分か。
7. **欠落節 (§4)。** 「対応が確かめられない箇所」として挙げた (a)〜(j) は本当に欠落か (稿が確かめていないだけで確かめられるものが
   混ざっていないか)。逆に、欠落なのに挙がっていないものは無いか。
8. **過剰・削除。** 稿に、results 系列の統制稿として不要な内容 (運用の物語、他 wave の経緯、機構の解説) が混ざっていないか。
   削っても稿の束縛が弱まらない部分を挙げる。README 行の長さ・内容は同系列の他行と釣り合うか。
9. **系列規則との整合。** append-only、1 file = 1 結果、一次資料からのみ、図の provenance、status の書き方 (D12)、
   LIVING_DOCS 対象外、basename 参照 — 稿と README 行が規則の逐語を満たすか。稿が「横断稿から引き継いでいない」と
   宣言することは規則上必要か、それとも余計か。
10. **研究前進。** この稿が論文の結果節に供給するものは何か、親の brief の「研究前進」の記述は一次資料で支持されるか。

出力形式 (Markdown、日本語):
- `## 所見` — 各所見に `must-fix` / `should-fix` / `nit` の重さ、稿の節の位置、問題の文、直し方の案 (逐語の代案)、根拠 (資料と節)。
  所見が無い観点は「観点 N: 所見なし (確かめた対象を列挙)」と書く。
- `## 親の brief への異議` — 親の P1 / P2 / 不変条件 / 研究前進で誤っている点 (無ければ「なし」と根拠)。
- `## 総括` — must-fix の件数、should-fix の件数、nit の件数、着地を止めるべきかの判定 (止める / 止めない) と 1 行の理由。
