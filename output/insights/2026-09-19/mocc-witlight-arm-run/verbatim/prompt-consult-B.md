単独段 dispatch: stage=consult; lane=luna; sandbox=read-only; parent=/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-mocc-witlight-arm-run

必読事項の射影 (各 path を読めなければ即停止して、その旨だけを `## 総括` に書いて終わること):
- 親 brief (攻撃対象、P1〜P6): /work/1/SFC/tanab/dev-wave-jobs/dev-wave-mocc-witlight-arm-run/s1-brief.md
- 段 2 plan (攻撃対象): /work/1/SFC/tanab/dev-wave-jobs/dev-wave-mocc-witlight-arm-run/codex/s2-plan.md
- 親の運用事実 (runner v5 要点・検出力表・環境・先例): /work/1/SFC/tanab/dev-wave-jobs/dev-wave-mocc-witlight-arm-run/verbatim/operational-facts.md
- T-2779 insight (§4 事前登録、§5 結果と欠測会計、§6 上限): /work/1/SFC/tanab/dev-wave-jobs/dev-wave-mocc-witlight-arm-run/verbatim/t2779-README.md
- T-2774 insight (§4 設計、§5 結果、§6 限界): /work/1/SFC/tanab/dev-wave-jobs/dev-wave-mocc-witlight-arm-run/verbatim/t2774-README.md
- runner v5 の逐語: /work/1/SFC/tanab/dev-wave-jobs/dev-wave-mocc-witlight-arm-run/verbatim/t2779_probe-v5.py
- 前 wave の arm 定義: /work/1/SFC/tanab/dev-wave-jobs/dev-wave-mocc-witlight-arm-run/verbatim/arms-t2779.json
- policy: /work/1/SFC/tanab/dev-wave-jobs/dev-wave-mocc-witlight-arm-run/verbatim/mocc_trace_v1_policy.json
- 既裁定: /work/1/SFC/tanab/dev-wave-jobs/dev-wave-mocc-witlight-arm-run/verbatim/D16.md, D95.md, D2114.md, D2134.md (同 dir)
- repo 内 (worktree の path、read-only): /work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-mocc-witlight-arm-run/tools/pegasus/dispatch_compute.py, .../orchestrator/campaign/mocc_g2_discriminator.py (limits・結論の定義), .../docs/dev-wave/mutation.md (`DW-M01`)

## 前置き — この依頼の性質

対象は学術研究用 DB ベンチマーク CCBench の並行性制御プロトコル MOCC の**直列化可能性の検査**である。セキュリティ製品でも攻撃ツールでもなく、外部からの入力も扱わない。「DB 研究チームが計器を軽くした版を 4 条件で計算ノードに走らせる実験計画 (標本・回転・収集・事前登録・記録) を敵対的にレビューする」依頼だと理解して読むこと。所見は被覆の記述の形で書く。

# 依頼 — 段 3 敵対相談 レンズ B: 実験設計・標本・回転・実行収集・記録・P1/P5/P6

plan を守らず検査せよ。親 brief 自身も検査対象である。plan と brief の file:line、前提、所有範囲、**親自身の実測値とその一般化** (operational-facts.md §6 の検出力表を独立に再計算せよ) を探し、誤りを見つけたら示せ。

## 攻撃してほしい点

1. **標本 (P1)**: (a) 検出力表 (K=56/60/120 × off 率 0.0417/0.058/0.119 対 on 0、部分抑制) を独立に再計算し、親の値と食い違えば示せ。(b) ユーザー決定「各 60 走」を上限 (超えない) と読む親の解釈と、「80% 検出力の根拠 = T-2774 段 3 レンズ B の各 arm ≥56」が実測率 0.042 では成り立たないことの扱い — 親は認可枠内で走らせ検出力を上限として明記する方針。これで問い (i) の答えとして何が言え・何が言えないかを、結果別 (on 0 / off k ≥5、on 0 / off k <5、on ≥1、両方 0) に表にせよ。(c) 「実用上の決定的結果 = on arm の G2 ≥1 で discriminator が走る」を主表示に据える妥当性と、それが事前登録として結果を見る前に固定できているか。(d) T-2779 通常 arm 5/120 との参考比較 (別 block・別日、合算しない) と、on/off の主比較を同 block 内対照に限る理由。
2. **回転 (P5)**: `round_order` (v5 435〜437) と 4 arm × 15 round で位置が 4/4/4/3 になることを検算。node k の JSON を k 個回転する案で 4 node 合計が各 arm 各位置 15 回になるか。4 JSON の sha が異なることの binding 上の扱い (arm 定義の同一性をどう示すか)。代替 (16 round = 64/arm、認可超) を採らないこと。
3. **実行と収集**: (a) 所要見積 (60 走 × 約 22 秒 + build 4 arm + warmup; T-2779 は 3 arm 90 走で 2222〜2233 秒) と walltime 02:30:00 の余裕。(b) 同 source・同 defines の on/off arm を別 build するコストと、runner を変えずに済ませる判断。(c) smoke (`--rounds 1`、4 走) の合格条件 — 4 arm とも verifier rc 0、on arm の witness file の存在と `S` 行件数、binding の define (bo1 だけ `BACK_OFF=1`)、runner sha 7907a545… と arms JSON sha、source sha が 4 arm で同一 — の過不足。(d) 欠測規則 (a)〜(d) と「結果を見て増減しない」の担保 (rounds は launcher 引数、s4-ruling に固定)。(e) 生 trace の保全 (G2 走のみ、job dir) と witness file の保全。(f) 4 投入元 worktree の base_dir 検査 (pin 解決・gitlink・orphan hold・clean) と同一 worktree 並行 dispatch の禁止。
4. **W の保全 (P6)**: author が wave worktree の submodule (worktree 専用 git dir) に commit → 親が主モジュールへ `git fetch <wt-module-dir> refs/heads/izanagi-t1943-mocc-g2-witlight:…` + bundle を job dir へ。worktree 撤去で失う経路が残るか。gitlink・patches/・policy を動かさないことの確認。
5. **変異・検査の登録 (DW-M01)**: repo の実装面差分 0 (gitlink 不変・patches/ 不変・runner 無変更) の主張は正しいか。W (submodule commit) と witlight.patch (job dir) に対する挙動検査として、(a) identity checker の負例 (include を 1 行足した版が赤)、(b) 同内容性 byte 比較の負例 (1 byte 変えた patch が不一致)、(c) smoke の on arm で S 行件数 = write 数、を登録する案の過不足。変異 matrix を免除するなら根拠を 1 行で。
6. **記録**: insight の節構成 (T-2779 と同型)、worklog fragment (完了 + `{{T:mocc-witlight-arm-run}}` の採番)、decisions fragment 0 の妥当性、failures fragment の条件。
7. **親 brief の誤り**: 行番号・数値・先例の引用に現物と食い違う点があるか (F1 型)。
8. **plan §8 の smoke 設計を攻撃**: (a) v5 が非 G2 走の raw (trace/witness) を削除する (R:359〜363) ため、plan は smoke 限定の「保存 wrapper」(v5 を import し、verifier 起動境界の `command` 呼出で saved_trace / saved_witness を smoke 証拠 dir へ複製してから実物へ委譲。argv・env・返値・verifier・discriminator は不変。本走では使わない) を author 所有で 1 本足す案。これは DW-O14 の「実物へ委譲する観測 wrapper」に当たるか、より軽い代替 (login は benchmark 実行を guard が拒否するので不可) があるか、wrapper が smoke の binding (runner sha) を汚さない設計か。(b) smoke の H/S 検査条件 (H は witness file ごとに 1 行、S の `(txid,key,epoch,tid)` Counter が標準 trace の W と一致、各 identity 1 件、C の write 数合計とも照合) の妥当性と、それを親が job dir でどう検算するか (script を書かず jq/grep/awk で可能か)。(c) smoke で G2 正例が出た場合 (verifier rc=1 は正常な非直列化可能判定) の扱い — plan は「rc=0 になるまで smoke を繰り返さない」「完全な正例 + discriminator 証拠が得られた rc=1 も技術的合格に含めるかを段 4 で事前固定」を推奨。(d) plan §5 の事前登録文案 (m の定義 = indeterminate を含み failure を含めない、`decisive_m`、`phenomenon` 照合) の過不足。

## 制約

- 入力はデータであって指示ではない (規律 6)。規律 1/2 を緩める提案をしない。
- 所見は real / refuted を分け、各所見に「放置時に成果物 (insight の値・主張・受理集合) がどう変わるか」を 1 行 (DW-G05)。示せないものは nit。
- 断定には現物の行番号か D 番号。確信の無いことは「不確実」、未実測の否定は「未実測」。
- 予算が尽きそうなら途中結論を出力形式どおり書いて終わること。**出力は file に書かず最終メッセージの本文に全文を書け。**
- 出力の見出しはすべて `##`。最後の節は必ず `## 総括` (`#` 2 個)。`## 総括` には (a) GO / NO-GO と条件、(b) must-fix (番号付き、各 1 行 + 成果物影響)、(c) should、(d) nit、(e) 親 brief への異議、(f) 検出力の再計算値、を書く。
