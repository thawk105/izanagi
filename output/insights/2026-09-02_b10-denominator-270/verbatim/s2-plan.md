## 変更計画

行番号は編集前の現行 tree 基準。変更対象は 2 ファイルだけとし、`docs/paper-story/`、コード、テスト、script は変更しない。

1. [docs/archive/worklog-phase3-0902-1189.md:23](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2201-b10-denominator/docs/archive/worklog-phase3-0902-1189.md:23) の既存本文は変更しない。現行逐語は次のとおり。

```text
3. **`abort=0` から「異常終了なし」は導けない。** `build_start` 49 / `commit` 47 で、
   予定 294 反復に対し観測 287、**7 反復は実行されずに終わっている**。外側 job の壁時計
   打ち切りによるもので、検査の拒否ではない。その 2 変種は 45 cell に含まれない。
```

[同ファイル:451](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2201-b10-denominator/docs/archive/worklog-phase3-0902-1189.md:451) の EOF、既存「次の一手」の後へ次を追記する。新しい H2 は作らず、H3 とする。

```markdown
### 訂正注記 (2026-09-02)

上記の「予定 294 反復」は、開始済み 49 attempt に条件づけた事後の分母であり、
正式系列の完全性を開示する分母ではない。登録された 3 workload の組は
3 workload × 15 変種 × 6 verify 反復 = 270 枠で、完了記録は 197、未完了は 73 である。
したがって完全性は `登録枠 270 / 完了記録 197 / 未完了 73` と開示する。
`294 / 287 / 7` は開始済み attempt 条件付きの内訳としてのみ残す。

この追記は、過去の測定値、45 cell の `correctness_certified=true`、および
「トレース側だけで件数が減る切り捨ては起きていない」という判定を変更しない。
関連する追記訂正の全体は
`output/insights/2026-09-02_b10-missing-iterations-scope/README.md` §10 を参照する。
```

この位置なら `NEXT_ACTION_RE` は新しい H3 の直前で「次の一手」本文を閉じるため、既存の T-ID 集合と archive 境界遷移を変えない。

2. [docs/b10-multinode-formal-run-design.md:198](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2201-b10-denominator/docs/b10-multinode-formal-run-design.md:198) の §5.1 末尾を差し替える。

現行逐語:

```text
あわせて、一次資料が「未確認」と書いた観察も同じ機会に潰せる。1 反復の所要が 655 万件を超えると
175 秒前後で頭打ちになる件で、トレースが切り捨てられている可能性がある。切り捨てが起きていれば、
検査が実際に覆っている取引の割合が主張と食い違うので、正しさの主張に関わる。
```

置換案:

```text
一方、一次資料が「未確認」とした観察は、worklog エントリ 1189 で決着済みであり、
この測定の対象にしない。正式走系列 4 campaign の完了記録 287 反復はすべて
`certified=true` で、トレース側だけで件数が減る切り捨ては起きていなかった。
175 秒前後の「頭打ち」は試行数を横軸にした取り違えで、所要を説明したのは
committed txn 数だった。D295 の common-mode failure と個数を保存する破損という
非検出限界は閉じていない。本項で測るのは所要の内訳と資源だけであり、
トレース切り捨ての再確認ではない。
```

3. [同ファイル:243](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2201-b10-denominator/docs/b10-multinode-formal-run-design.md:243) の §6 (4)、集約レポート生成の説明直後かつ §6 (5) の前へ、次の報告様式を挿入する。

```text
この集約レポートで正式系列の完全性を開示するときは、登録された 3 workload の組
(write-heavy は完走した `e3de15eb` を採る) の
3 workload × 15 変種 × 6 verify 反復 = 270 枠を分母にし、
完了記録数と未完了枠数を併記する。既存 4 campaign の記録をこの様式へ写すと
`登録枠 270 / 完了記録 197 / 未完了 73` である。
開始済み 49 attempt に条件づけた `294 / 287 / 7` は、
正式系列の完全性の分母に使わない。
```

135 performance cell の集約と 270 verify 枠の完全性開示が別単位であることを、同じ report producer の説明内で固定できる。

4. [同ファイル:315](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2201-b10-denominator/docs/b10-multinode-formal-run-design.md:315) の §10 を差し替える。

現行逐語:

```text
- 1 反復 175 秒の頭打ちを確定値として使わない。トレース切り捨ての疑いが残っている。
```

置換案:

```text
- 1 反復 175 秒の頭打ちは確定値として使わない。この値は単一の測定から再現せず、
  頭打ちは試行数を横軸にした取り違えだった。正式走系列 4 campaign の完了記録
  287 反復では、トレース側だけで件数が減る切り捨ては起きていなかった
  (worklog エントリ 1189)。
```

## 派生記述の一覧

「出現箇所 全件」は、値を実際に主張または判断へ再利用する tracked 本文を対象とする。T-2202 自身、エントリ 1198、missing-scope insight の一覧、`verbatim/` 内の複製は自己参照になるため除外した。`docs/paper-story/` に該当する直接記述はない。

| # | 4 件への束ね方 | 出現箇所 | 値を出した母集団 | 欠測が掛かる位置 |
|---:|---|---|---|---|
| 1 | T-2191 の「70.0-87.0 マイクロ秒/commit」と「15 認証単位」 | [trace insight:179](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2201-b10-denominator/output/insights/2026-09-02_b10-trace-truncation/README.md:179)、[同:204](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2201-b10-denominator/output/insights/2026-09-02_b10-trace-truncation/README.md:204)、[1189:442](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2201-b10-denominator/docs/archive/worklog-phase3-0902-1189.md:442) | 単価は performance タグ 238 反復。内訳は write-heavy 75 + 75、balanced 70、read-heavy 18。15 認証単位は 1 workload の登録 15 変種を認証単位へ写した構造数で、回帰の標本数ではない。 | read-heavy 18 のうち 3 反復が、commit へ到達しなかった `constant-mu2` attempt の観測分。残る同 attempt の 2 performance 枠と未開始 11 変種分は回帰へ入らない。 |
| 2 | 「直列性検査 1 回 23 分」と、その優先順位・walltime 判断への利用 | [1187:9](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2201-b10-denominator/docs/archive/worklog-phase3-0902-1187.md:9)、[同:431](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2201-b10-denominator/docs/archive/worklog-phase3-0902-1187.md:431)、[1189:442](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2201-b10-denominator/docs/archive/worklog-phase3-0902-1189.md:442)、[D1485:46378](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2201-b10-denominator/docs/decisions.md:46378)、[D1489:46501](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2201-b10-denominator/docs/decisions.md:46501)、[同:46503](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2201-b10-denominator/docs/decisions.md:46503)、[A-6 insight:100](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2201-b10-denominator/output/insights/2026-09-02_paper-story-a6-certification/README.md:100) | read-heavy の 3 秒・高 commit 帯にある単回 verify 所要。`constant-mu2` の観測 3 反復は 1346.9-1465.6 秒の帯で、23 分記述の母集団に含まれる。D1489 はこの値から full-scale 10 回を 3.83 時間と見積もる。 | `constant-mu2` attempt は予定 5 performance 反復のうち 3 件だけ完了し、2 件に完了記録がない。未開始 11 変種もこの所要標本には入らない。 |
| 3 | read-heavy の「5 時間 5 分・3 変種」と「約 25 時間」の外挿 | [formal-run insight:150](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2201-b10-denominator/output/insights/2026-08-31_t1905-b10-formal-run/README.md:150)、[1186:14](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2201-b10-denominator/docs/archive/worklog-phase3-0902-1186.md:14)、[1187:9](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2201-b10-denominator/docs/archive/worklog-phase3-0902-1187.md:9)、[design:16](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2201-b10-denominator/docs/b10-multinode-formal-run-design.md:16)、[同:120](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2201-b10-denominator/docs/b10-multinode-formal-run-design.md:120)、[同:314](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2201-b10-denominator/docs/b10-multinode-formal-run-design.md:314)、[D1480:46276](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2201-b10-denominator/docs/decisions.md:46276)、[D1489:46501](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2201-b10-denominator/docs/decisions.md:46501)、[D1509:47044](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2201-b10-denominator/docs/decisions.md:47044)、[design insight:32](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2201-b10-denominator/output/insights/2026-09-02_t1905-b10-multinode-design/README.md:32)、[A-6 insight:100](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2201-b10-denominator/output/insights/2026-09-02_paper-story-a6-certification/README.md:100) | request `965996` の約 5 時間 5 分の job wall と、その時点で commit 済みだった 3 変種を `15 / 3` 倍した外挿。 | job wall には、commit へ到達しなかった 4 変種目の legacy 1 + performance 3 の処理時間も入る。一方、外挿の完了変種数は 3 のまま。4 変種目の残り 2 反復と未開始 11 変種 66 枠には完了記録がない。 |
| 4 | 正式走 insight の「read-heavy は 1690 万 commit」 | [formal-run insight:147](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2201-b10-denominator/output/insights/2026-08-31_t1905-b10-formal-run/README.md:147)、[1186:58](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2201-b10-denominator/docs/archive/worklog-phase3-0902-1186.md:58)、[1187:9](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2201-b10-denominator/docs/archive/worklog-phase3-0902-1187.md:9)、[1189:38](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2201-b10-denominator/docs/archive/worklog-phase3-0902-1189.md:38)、[trace insight:194](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2201-b10-denominator/output/insights/2026-09-02_b10-trace-truncation/README.md:194)、[同:200](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2201-b10-denominator/output/insights/2026-09-02_b10-trace-truncation/README.md:200)、[同:236](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2201-b10-denominator/output/insights/2026-09-02_b10-trace-truncation/README.md:236) | read-heavy の高 commit 帯にある 3 秒 performance 反復。未 commit の `constant-mu2` attempt の観測 3 件は 16.916M-16.938M、平均 16.928M commit で、1690 万への丸めに含まれる。 | 同 attempt の予定 5 件中 2 件が欠測。未開始 11 変種の値も存在せず、登録 15 変種全体の集計ではない。 |

## 親 provisional への評価

- (P1-a) 同意。archive への訂正注記追記は [docs/archive/README.md:3](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2201-b10-denominator/docs/archive/README.md:3) と [docs/worklog.md:60](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2201-b10-denominator/docs/worklog.md:60) が明示的に許す唯一の archive 変更であり、本文を直接読む経路に訂正を置ける。前例 0 件は注意材料だが禁止根拠ではない。EOF の H3 なら H2 full-match を増やさず、`NEXT_ACTION_RE` も既存「次の一手」を新 H3 の直前で閉じる。README の [索引行:3001](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2201-b10-denominator/docs/archive/README.md:3001) だけへの注記は、直接 archive へ入る読者へ届かない。

- (P1-b) 同意。ただし挿入位置は §7 や §10 より、正式 report producer を説明する §6 (4) 直後が適切である。設計文書は「次の正式系列」を直接対象とし、135 cell の集約と完全性の 270 verify 枠を同じ場所で区別できる。発効済み事前登録を変更せず、別 wave 所有の `docs/paper-story/` にも触れない。

- (P1-c) 同意。エントリ 1198 の正本は T-2191 を 1 件とし、その中で 238 反復回帰の単価と 15 認証単位を一緒に列挙している。したがって 5 語句は「T-2191 の 2 語句」+「23 分」+「5 時間と約 25 時間」+「1690 万 commit」の 4 件になる。ただし 15 認証単位は回帰推定値ではなく登録 15 変種の構造数であり、束ねる根拠は同じ派生記述に属することにある。

## 検査

赤くなりうるのは、archive H2 文法、日付付き entry の一意性、「次の一手」の抽出と保存則、archive README の索引整合、Markdown・Unicode・空白検査である。親は次を実行する。

```bash
git diff --check
git diff --unified=0 -- \
  docs/archive/worklog-phase3-0902-1189.md \
  docs/b10-multinode-formal-run-design.md

archive_bytes=$(git cat-file -s HEAD:docs/archive/worklog-phase3-0902-1189.md)
cmp \
  <(git show HEAD:docs/archive/worklog-phase3-0902-1189.md) \
  <(head -c "$archive_bytes" docs/archive/worklog-phase3-0902-1189.md)

if rg -n \
  'トレース切り捨ての疑いが残っている|トレースが切り捨てられている可能性がある' \
  docs/b10-multinode-formal-run-design.md; then
  exit 1
fi

rg -n '登録枠 270|270 枠|完了記録 197|未完了 73' \
  docs/archive/worklog-phase3-0902-1189.md \
  docs/b10-multinode-formal-run-design.md

if rg -nP '[\x{0300}-\x{036F}]' \
  docs/archive/worklog-phase3-0902-1189.md \
  docs/b10-multinode-formal-run-design.md; then
  exit 1
fi

python3 tools/check_docs.py
python3 tools/run_tests.py orchestrator/tests/test_check_docs.py -q -rf
python3 tools/check_codex_agents.py
```

commit 後に履歴監査も行う。

```bash
python3 tools/check_ai_provenance.py
```

本 plan 段では read-only のため検査は実走しておらず、緑とは報告しない。

## 総括

編集対象は archive エントリ 1189 と正式系列設計文書の 2 ファイルだけである。  
1189 は既存 bytes を保ち、EOF の H3 訂正注記で完全性を 270 / 197 / 73 へ直す。  
設計文書には 270 分母の報告様式を加え、§5.1 と §10 の古い切り捨て疑義を決着済み事実へ置換する。  
5 語句は T-2191 の 2 語句を 1 件に束ねて合計 4 件となる。  
測定値、45 cell の認証、正しさゲート、`docs/paper-story/` は変更しない。