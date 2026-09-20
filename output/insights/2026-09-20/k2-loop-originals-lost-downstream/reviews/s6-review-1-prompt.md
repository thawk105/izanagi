単独段 dispatch: stage=review; sandbox=read-only; parent=/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-k2-loop-originals-lost-downstream

必読事項の射影:
- /work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-k2-loop-originals-lost-downstream/output/insights/2026-09-20/k2-loop-originals-lost-downstream/README.md — レビュー対象の本体 (対応表 §2、裁定パッケージ §4)。読めなければ即停止。
- /work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-k2-loop-originals-lost-downstream/output/insights/2026-09-20/k2-loop-originals-lost-downstream/materials/reconstruction-log.md — 親の実測の逐語 (sha256・bytes・再構成の結果)。読めなければ即停止。
- /work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-k2-loop-originals-lost-downstream/output/insights/2026-09-20/k2-loop-originals-lost-downstream/reviews/s1-brief.md — 段 1 brief (scope・不変条件・provisional 裁定 P1〜P3)。読めなければ即停止。
- /work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-k2-loop-originals-lost-downstream/output/insights/2026-09-20/k2-loop-originals-lost-downstream/reviews/s4-ruling.md — 段 4 裁定。読めなければ即停止。
- /work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-k2-loop-originals-lost-downstream/docs/spool/worklog/2026-09-20-dev-wave-k2-loop-originals-lost-downstream-1.md — worklog fragment ([T-2795] の更新文)。読めなければ即停止。
- /work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-k2-loop-originals-lost-downstream/docs/paper-story/results/2026-09-20-k2-manual-loop-three-rounds.md — 3 巡稿。§5.1 (原本の sha256 と bytes、消失前に再計算)、§2.1、§4 を照合に使う。読めなければ即停止。
- /work/1/SFC/tanab/dev-wave-jobs/dev-wave-k2-loop-originals-lost-downstream/refs/cleanup-backup-loss-record-README.verbatim.md — 事故を記録した別 wave (未 land) の insight README の逐語写し。損失表 §3 が前提。読めなければ即停止。
- /work/1/SFC/tanab/dev-wave-jobs/dev-wave-k2-loop-originals-lost-downstream/refs/cleanup-backup-loss-record-worklog-fragment.verbatim.md — 同 wave の worklog fragment (本 wave の起票元 T の本文)。読めなければ即停止。
- /work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-k2-loop-originals-lost-downstream/output/insights/2026-09-19/k2-loop-round3/README.md — round 3 の記録 (「診断が届いたか」「実測」「証拠の所在」節)。読めなければ即停止。
- /work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-k2-loop-originals-lost-downstream/output/insights/2026-09-19/k2-loop-round3/materials/run-summary.json — round 3 の派生物 (loop_state / bench / verify / wal_refs)。読めなければ即停止。
- /work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-k2-loop-originals-lost-downstream/orchestrator/campaign/p3_s4_loop.py — harness。`state_to_dict` / `save_loop_state` / `load_loop_state` / `drive_iteration` / `check_stop` と、`k2_next_generation_inputs` / `planner_context_payload` (4 巡目の射影入力に何が要るか) を読む。読めなければ即停止。
- /work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-k2-loop-originals-lost-downstream/docs/paper-story/2026-09-20.md — story。§8 の B-6 / B-9 だけ読む (`grep -n "B-6\. \|B-9\. "` で位置を引く)。読めなければ即停止。
- /work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-k2-loop-originals-lost-downstream/CLAUDE.md — 絶対規律 2・6・7。読めなければ即停止。

これは自分たちの研究記録 (docs-only) の設計レビューである。目的: 2026-09-20 19:25 JST に K2 手動 loop 3 巡の campaign 原本 (WAL・AO・loop_state・digest・campaign.lock・受領証) が
cleanup 事故で消失した前提で、親が (1) 論文ストーリーの主張ごとに「要る一次資料 / 残存資料 / 現在確認できる範囲 / 要る限定」を定めた対応表と、(2) 4 巡目の入力元の択 (A: round 3 の
repo 内派生物から射影を組む / B: 別走 / C: pair 走を直前巡にする) の裁定パッケージを書いた。実装面は無い (実装差分ゼロ)。親は使い捨て script 4 本を repo 外の job dir で実走し、
その stdout を `materials/reconstruction-log.md` に逐語で写した (親が実行済み。子は repo 外 file を読めない場合、その部分は「未検証 (読めず)」と書き、断定しない)。

read-only sandbox なので pytest 緑は要求しない。静的検査 (file を読んで照合する) でよい。テスト実測は親が行う。
**出力は file に書かず、最終メッセージの本文に全文を書け** (親の launcher が保存する)。予算が尽きそうなら途中結論を出力形式どおり書いて終われ (無出力が最悪)。

## レンズ (a) — 事実照合 (README §0・§1・§2 と materials/reconstruction-log.md、3 巡稿 §5.1、記録 wave README §3)

次を 1 件ずつ点検し、食い違いは file:行 (または表の行) を名指しして指摘せよ。

1. README §1 の表の各行の区分 (「bytes 一致」「内容同一」「値のみ」「内容の一部」「無し」「現存」) が、reconstruction-log の実測結果と 1 対 1 で対応しているか。実測に無い区分を書いていないか。
2. README に転記された sha256 の先頭 8 桁と bytes 数 (例: `917ba3d3…` 255 B、`804c62c7…` 34,017 B、`66d3e737…` 32,979 B、`fc7acaca…` 8,307 B、`eb8927b7…` 7,057 B、`ac12b80f…` 7,053 B) が
   3 巡稿 §5.1 の表と一致するか。1 文字でも違えば must-fix。
3. 不在の断定 (「無し」「repo に逐語 0 件」「候補 list に無い」「[T-2795] の session は無い」) に、走査した範囲と時刻が付いているか。付いていない不在断定は must-fix。
4. 「再構成物を原本と呼ばない」「WAL は内容同一まで (bytes 再構成不能)」「digest の再描画は未実測」が §0・§2・§4・§7 で一貫しているか。どこかで「復元」「再構成できる (WAL)」と滑っていないか。
5. 規律 7 (現行コードとの差・原本の不在だけを理由に過去の判定を無効化しない) と規律 2 (verifier certified の gate を緩めない) に反する文が無いか。逆に「provenance は消失前と同じ強さ」と読める文が無いか。
6. README §0 の「記録 wave の README の 2 文は当該 insight の記載範囲について正しいが 3 巡稿 §5.1 で埋まる」は、記録 wave README §3 の該当行 (roundtrip の「sha256 の記録も無し」、round 2 の「campaign.lock は照合不能」) の文脈で正しいか。
7. §2 の対応表で、story §8 B-6 / B-9 の本文が実際に依拠している一次資料 (story 本文が名指す path) と「要る一次資料」欄が食い違っていないか。fig12 の「原本非依存」は `figures/fig12_k2_manual_loop_dataflow.provenance.json` の `inputs` を読んで裏取りせよ (読めれば)。
8. worklog fragment の [T-2795] 更新文が、現行の T-2795 本文 (3 巡稿ではなく `docs/worklog.md` の entry 1754 の次の一手) を欠落なく含み、追記だけを足しているか。`base:` の sha256 は照合できないので触れなくてよい。

## レンズ (b) — 裁定パッケージ (README §4) を通してはいけない最も強い理由

1. 択 A (推奨) を採ってはいけない最も強い理由を作れ。特に (i) harness 側の入力組立て (`k2_next_generation_inputs` / `planner_context_payload` / whiteboard の値域検査) が、
   README §3 が列挙した入力 (whiteboard・current_perf・leading_indicators・knowledge_input・k2_critic_diagnosis・受領証 bytes・identity の lock) 以外に round 3 の原本 (WAL bytes・digest・
   campaign.lock の bytes) を要求する経路が無いか、code で確かめよ。(ii) 「round 3 の派生物は原本と sha 一致」が、4 巡目の provenance 主張として何を言えて何を言えないか。
   (iii) 3 巡稿・story の「同 job stock 対照は未達」との整合。
2. 択 B / 択 C の「やらない理由の最も強い形」が本当に最強か。より強い理由、または A より B / C を採るべき理由があれば書け。
3. 付随 1 項 (`submit-tree-pair` の `git worktree lock`) が、依頼の scope 外 (仮想リスク向けの gate・検査・台帳・一般化の追加) に当たるか。当たるなら理由、当たらないなら理由。
4. 攻撃が成立しなかった項目は正直にそう書け。全項目を無理に成立させるな。

## 出力形式 (見出しは全部 `##` の H2。`###` を使わない)

## 所見
- 各所見を `must-fix` / `nit` で分け、file:行 (または §番号・表の行) と、放置時に成果物 (対応表・裁定パッケージ・worklog の次の一手) の何が誤るかを 1 行で書く。所見ゼロならそう書く。
## レンズ (b) の攻撃結果
- 択 A / B / C / 付随 1 項ごとに「成立 / 不成立」とその根拠 (code の関数名・行を引く)。
## 総括
- GO / NO-GO と、NO-GO なら must-fix の一覧。最後の節は必ず `## 総括` (`#` を 2 個) とする。`### 総括` と書いてはならない。
