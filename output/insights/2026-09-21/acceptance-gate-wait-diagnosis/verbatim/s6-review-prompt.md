単独段 dispatch: stage=review; sandbox=read-only; parent=/work/1/SFC/tanab/izanagi/.claude/worktrees/t-lease-gate-wait-diagnosis

必読事項の射影 (読めなければ即停止):
- /work/1/SFC/tanab/izanagi/.claude/worktrees/t-lease-gate-wait-diagnosis/output/insights/2026-09-21/acceptance-gate-wait-diagnosis/README.md — **検査対象の本文**。
- /work/1/SFC/tanab/dev-wave-jobs/dev-wave-lease-gate-wait-diagnosis/probe-out/final.md — 数値の出所 (probe の最終走出力、逐語)。README の数表はこれと 1 対 1 で照合できなければならない。
- /work/1/SFC/tanab/dev-wave-jobs/dev-wave-lease-gate-wait-diagnosis/probe-out/final.stdout.txt — 最終走の生 stdout (self-check 4 件)。
- /home/SFC/tanab/.claude/jobs/c8e39534/tmp/s4-ruling.md — 段 4 裁定 (定義の正本。§2 前提 v2、§3 probe 仕様、§4 scope)。
- /home/SFC/tanab/.claude/jobs/c8e39534/tmp/brief.md — 段 1 brief (scope・不変条件・確定裁定)。
- /home/SFC/tanab/.claude/jobs/c8e39534/tmp/codex/s3-consult-out.md — 段 3 相談の所見 12 件。
- /home/SFC/tanab/.claude/jobs/c8e39534/tmp/codex/s6-fix1-out.md — fix1 の報告。
- /home/SFC/tanab/.claude/jobs/c8e39534/tmp/codex/s6-fix2-out.md — fix2 の報告。
- /home/SFC/tanab/.claude/jobs/c8e39534/tmp/codex/s6-fix3-out.md — fix3 の報告 (`--until` 導入、直近 20 の集合照合 jq 出力)。
- /home/SFC/tanab/.claude/jobs/c8e39534/tmp/codex/s6-fix4-out.md — fix4 の報告 (交差表)。
- /home/SFC/tanab/.claude/jobs/c8e39534/tmp/verbatim/memory-gate-facts.md — 門番の条件・jitter・leaders 判定の偽陽性・T-2610 の実測 (ユーザー裁定の正本、逐語)。
- /home/SFC/tanab/.claude/jobs/c8e39534/tmp/verbatim/D2148-item12.md — 「inbox の門番条件値・FIFO・自動再投入・追加 L2 節を丸ごと採用した裁定ではない」の逐語。
- /home/SFC/tanab/.claude/jobs/c8e39534/tmp/verbatim/D2185-gate-relax-line.md — 1 wave だけ上限 2 へ緩めた先例の逐語。
- /home/SFC/tanab/.claude/jobs/c8e39534/tmp/verbatim/DW-O27.md — acceptance は lease を待たない (D662) の逐語。
- /work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2610-fig10/gate-loop-final.log — README §4 の事例の生 log。
- /work/1/SFC/tanab/izanagi/.claude/worktrees/t-lease-gate-wait-diagnosis/output/insights/2026-09-21/acceptance-gate-wait-diagnosis/verbatim/gate_wait_probe.py.md — probe の逐語 (定義が実装と合っているかの照合用)。

## 役割

あなたは「受入門番の待ち時間診断」wave の段 6 敵対レビュー (read-only、reasoning=medium) である。**README 本文が検査対象**で、親 (Claude) が書いた。2 つのレンズを 1 本で担え。プランや本文を守る側に立つな。見つからなければ「見つからない」と書け。

書込み可能な tmp は無い。静的検査でよい。親が実行したテスト・本走をあなたの非実走で緑と記録しない。
**出力は file に書かず、最終メッセージの本文に全文を書け** (親の launcher が保存する)。予算が尽きそうなら途中結論を出力形式どおり書いて終われ。

### レンズ A — 数値・派生値・量化の照合 (DW-O16)

1. README §3 の全数表を `final.md` と 1 対 1 で照合せよ。値の写し間違い、単位 (秒 / 分)、丸め、n の取り違え、母集合の取り違え (直近 20 / 9/19 以降 / maxl ≤ 1 部分集合) を挙げよ。
2. 親が本文で自分で足し算した派生値を全部洗い出し、原データから再計算して一致を確かめよ。少なくとも次を検算せよ (他にもあれば挙げよ):
   - 「leaders 起因の閉門 1028 tick」「走行 ≤ 1 の 502 tick (推定 1003.0 分)」
   - 「部分文字列一致で 945 tick 中 470」「argv 先頭一致で 83 tick 中 32」
   - 「他に 3 本以上が待っていても開いた投入が 51 回 (17 + 13 + 12 + 4 + 2 + 1 + 2)」
   - §4 の「門番待ちは区間 1 と区間 2 の和 (約 64.6 分)」「50 分 21 秒」「14 分 13 秒」「168 分 27 秒」
   - §7 の「1 区間が 64%」(直近 20 の maxl=2 合計に対する最大寄与区間の割合)
3. 「すべて」「だけ」「〜に限る」「無かった」「0 件」型の量化を全部拾い、資料で裏が取れるか確かめよ。特に「lease directory に履歴が無い」「receipt に時刻 field が無い」「`~/.claude/jobs/` に門番 log は無かった」「門番 log の無い dir の走行は 1 本」「9/18 型の 5 本同時投入は無かった」。
4. §4 の T-2610 の 3 区間が生 log と一致するか (行番号で示せ)。時刻・tick 数・拒否回数・ok_load の内訳。
5. 定義 (§2) が probe の実装 (`gate_wait_probe.py.md`) と一致するか。特に区間分割の 600 秒、飢餓候補の条件、走行数の打切り補完、感度模型の基準 b0。**本文の説明と実装が食い違う箇所**を挙げよ。
6. self-check 4 件の期待値と実測が `final.stdout.txt` と一致し、README の記述と合っているか。

### レンズ B — 過剰・削除・裁定境界・言い過ぎ (DW-S03 の過剰・削除レンズ)

7. README が scope を超えていないか。診断のみ・実装 0 行・門番の閾値と周期と lease TTL は変えない・lease primitive と待ち手は変えない・gate / 台帳 / 一般化の追加は scope 外、という依頼と brief の線を越える記述 (実装の提案を既成事実にする書き方、採用済みのように読める書き方) を挙げよ。
8. §7 の裁定パッケージが D2148 項 12・D2185・DW-O27・記憶の正本と矛盾しないか。「既に裁定済み」と読める書き方、FIFO / slot 機構を現行制約内の数値変更と同列に見せる書き方、lease primitive・待ち手・TTL に触れる択が紛れていないか。択 A が「gate・台帳・一般化の追加」に当たるなら、そう明記されているか。
9. 因果の言い過ぎ: 閉門理由の分数配分・感度分析・時間帯の偏り・「記録と実態の不一致」の 3 候補を、観測と推定と仮定に正しく分けているか。「偽 leader が主因」と読める書き方が残っていないか。
10. 親の推奨 (A を先に、B は期間限定、C・D・別枠は採らない) が、この資料の範囲で言える強さか。強すぎる/弱すぎる箇所を挙げよ。
11. 抜けている限界・列。特に (a) 母集合が job dir の残存に依存すること、(b) 走行数の母集合が started/finished のある走行だけであること、(c) 直近 20 の帯が夜間に偏っていること、(d) 本 wave 自身の除外、が §8 に書かれているか。
12. 結論 (冒頭) と本文の食い違い、題の言い過ぎ。

## 出力形式

- `## 照合表` — README の数値のうち検算した項目を「本文の値 / 出所 (file と節) / 再計算値 / 一致・不一致」の行で出す (最低 25 行)。
- `## must-fix` — 放置すると成果物の値・受理集合・参照が変わる欠陥。`M<n>`、重要度、根拠 (file:節 または log の行)、直し方 1 行。
- `## should` / `## nit` — 同形式。
- `## GO / NO-GO` — README を記録してよいか。NO-GO ならその理由を 1 行。
- `## 総括` — 5 行以内。
