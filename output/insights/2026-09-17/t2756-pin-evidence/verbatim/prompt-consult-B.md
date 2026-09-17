単独段 dispatch: stage=consult; sandbox=read-only; parent=/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2756-pin-evidence

必読事項の射影:
- /home/SFC/tanab/.claude/jobs/99263204/tmp/wave/parent-brief.md — 親 brief (研究前進・scope・確定済み裁定・不変条件・段 1 実測・provisional 裁定 P1〜P5)。**親 brief 自身も検査対象**。読めなければ即停止。
- /home/SFC/tanab/.claude/jobs/99263204/tmp/wave/s2-plan.md — 段 2 plan (codex 起草、134 file の分類案を含む)。守るのではなく検査する対象。読めなければ即停止。
- /home/SFC/tanab/.claude/jobs/99263204/tmp/wave/pin-closure.tsv — 親が実測した pin 束縛 file の閉包 134 件 (path、4 形の出現数、行番号)。読めなければ即停止。
- /home/SFC/tanab/.claude/jobs/99263204/tmp/wave/insight-cross-protocol-s4-s6.md — 前 wave insight の §4 候補観測・§5 波及表の骨格 (13 行)・§6 準備 T。読めなければ即停止。
- /home/SFC/tanab/.claude/jobs/99263204/tmp/wave/D1603.md — 材料 (3) = 「承認済み定数への波及範囲」の定義。読めなければ即停止。
- /home/SFC/tanab/.claude/jobs/99263204/tmp/wave/D2114.md — 本 wave の起点裁定 (理由節に pin を束縛する物の列挙、規律 7 の適用、「D297 合格は SHA 束縛を内容ハッシュへ置換する承認にならない」)。読めなければ即停止。
- /home/SFC/tanab/.claude/jobs/99263204/tmp/wave/D2104-item13.md — 非 silo between-run 実測の保留と pin 再承認の手続き。読めなければ即停止。
- /home/SFC/tanab/.claude/jobs/99263204/tmp/wave/phase3-T167-row.md — 見送り台帳 [T-167] 行の現状 (提示先)。読めなければ即停止。
- /home/SFC/tanab/.claude/jobs/99263204/tmp/wave/spool-README.md — spool fragment の書式。読めなければ即停止。
- /work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2756-pin-evidence/CLAUDE.md — 絶対規律 7 (測定時点の事実と現行コードへの適合を分ける) の逐語。読めなければ即停止。
- /work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2756-pin-evidence/orchestrator/campaign/s8b_approved.py — `CCBENCH_FULL_SHA` と承認の意味 (docstring)。読めなければ即停止。
- /work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2756-pin-evidence/orchestrator/campaign/pin.py — `CURRENT_PIN` (7 桁) と歴史的 driver の扱い。読めなければ即停止。
- /work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2756-pin-evidence/tools/check_docs.py — docs 編集が当たる exact pin・byte 予算の所在。読めなければ即停止。

## 依頼 (レンズ B: 材料 (3) 波及表の完全性・分類の正しさ・提示形)

あなたは read-only の敵対検証子である。plan と親 brief を守らず、**整合・実効性 (波及表が再承認の判断材料として正確か) と正しさ境界 (規律 7・規律 2 の適用) を分けて**攻撃せよ。pytest の実走は不要 (静的検査でよい、親が実測する)。

攻撃対象:
1. **閉包の完全性。** 親の閉包は `git grep 511c953` (台帳 3 本・archive・spool・output/insights を除外) の 134 file である。(a) 除外した範囲のうち再承認の判断に要るもの (例: output/insights 内の凍結 evidence manifest `raw-manifest.json` の `current_pin`、docs/decisions.md 内で pin を「承認」した D の逐語) があれば挙げよ。(b) pin を 40 桁/7 桁以外の形で束縛する物 (例: `v1.1.0-126`、tree OID、`ccbench_commit` を含む campaign.lock の identity_preimage、sha256 で pin を含む file を束縛する manifest、submodule gitlink を読む test) を `git grep` で探し、閉包に無ければ列挙せよ (見つからなければ「見つからない」と書く)。(c) 逆に 134 file のうち pin を「束縛」していない (単なる言及・過去の記録) file を分類 E へ落とすべきかを判定せよ。
2. **分類の正しさ (全数)。** plan の分類案 (path → A〜G) を 1 file ずつ検算し、誤分類・根拠不足を列挙せよ。特に: `orchestrator/campaign/buildcache.py:1059` (docstring の「pin 更新時は再実測」は G か E か)、`p3_s4_loop.py:112` (D1936 の完全 40 桁 pin)、`silo_ladder_rung1*.py` / `patches/ledger.json` (patch の base_commit — pin 前進で patch の適用可否はどうなるか)、`tools/pegasus/mocc_trace_v1_policy.json:20-21` (base_oid=511c… / new_oid=e9e477… — pin 前進後に base==new になる policy の扱い)、`output/env/pegasus/calibration/registered/*.json` (較正 record の pin — 較正は新 pin で再取得が要るか、`orchestrator/campaign/env_contract.py` が record の何を固定するか)、`tools/known_violations/*.json` (provenance 台帳の pin 言及)、`orchestrator/tests/acceptance_duration_ledger.json`、`docs/paper-story/figures/*.provenance.json`。
3. **規律 7 の適用。** 親 brief P4 の結論「pin 前進は既存の certified 判定を無効化しない。新 pin で継続する系列だけが A〜C・F の更新を要する」を CLAUDE.md 規律 7 の逐語と D2114 の理由節に照らして検算せよ。無効化されないものと、新 pin で「再取得が要る」ものの境界が曖昧な層 (較正 record、凍結 floor、within-run floor 登録 D2083) を名指しし、それぞれ「保持 / 再取得 / 新登録 / erratum」のどれかを根拠つきで判定せよ。判定できないものは「ユーザー裁定へ返す候補」として文面を書け。
4. **見送り台帳への提示形 (P5)。** `docs/phase3.md` [T-167] 行への 1 行追記の逐語案を検算せよ: 承認語 (「承認」「前進可能」「合格したので」) を含まないか、check_docs.py の exact pin・byte 予算・「状態:」検出に当たらないか、同日に別 wave (t2757 / t2760) が同じ行を触る可能性。代案として insight 側だけに書き phase3.md を触らない選択の得失を 2 文で述べよ。
5. **成果物の骨格。** plan の insight 節構成が「再承認の判断材料」として読める順序か (材料 1→2→3 の順、限界と「本 wave が判定しないこと」の位置、verbatim の一覧)。decisions fragment の要否 (新しい設計判断があるか。無ければ worklog fragment だけ) を判定せよ。
6. **親の実測値の一般化。** 「134 file」「79 file」という数字を insight に書くときの条件 (除外範囲・4 形・日付・HEAD) が明記されているか、数字が main の進行で陳腐化する書き方になっていないか。

各所見は「所見 / 根拠 (file:line または射影名) / 正しさ境界 or 整合・実効性 / must-fix or nit / 推奨是正」の形で書け。予算が尽きそうなら途中結論を下の出力形式どおり書いて終われ (無出力が最悪)。

## 出力形式

Markdown。先頭に `## 総括` (10 行以内: must-fix 件数、nit 件数、誤分類の件数、閉包に足すべき file 数、P4/P5 への賛否、decisions fragment の要否)。続けて上の 1〜6 を見出しにして書き、最後に `## 訂正版の分類表 (差分だけ)` を置く (plan の分類と違う file だけ path → 訂正分類 → 根拠)。
