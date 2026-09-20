単独段 dispatch: stage=review; sandbox=read-only; parent=/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-paper-methods-ja-2026-09-20

必読事項の射影: 下記の絶対パスを読む。**読めなければ即停止し、読めなかった path を報告せよ。**
この停止規則は下記に列挙した射影 file にだけ掛かる。お前が自分で探した path が不在でも、
それを理由に検査全体を打ち切ってはならない (その path は「不在」と記録して先へ進め)。

- /work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-paper-methods-ja-2026-09-20/output/insights/2026-09-20/paper-methods-ja/methods.md (**レビュー対象 1**、本体論文の日本語方法節草稿 2026-09-20 版、221 行)
- /work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-paper-methods-ja-2026-09-20/output/insights/2026-09-20/paper-methods-ja/implementation.md (**レビュー対象 2**、実装対応メモ 2026-09-20 版、142 行。表 2 つと読み分け表を含む)
- /work/1/SFC/tanab/dev-wave-jobs/dev-wave-paper-methods-ja-2026-09-20/brief-s1.md (親の段 1 brief と provisional 裁定 (P1)(P2)。稿が従うべき scope と不変条件)
- /work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-paper-methods-ja-2026-09-20/output/insights/2026-09-10/paper-methods-ja/methods.md (前稿 2026-09-10 版、128 行。**凍結物・この wave では不変**。新稿が前稿から変えた点の妥当性を見る)
- /work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-paper-methods-ja-2026-09-20/output/insights/2026-09-10/paper-methods-ja/implementation.md (前稿の実装対応メモ、90 行。同上)
- /work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-paper-methods-ja-2026-09-20/docs/paper-story/2026-09-20.md (論文ストーリー 2026-09-20 版、488,927 bytes / 3,866 行 — **全文 `cat` しないこと**。読むのは §6 (行 2021〜2361) と §8 の exact claim (行 2723〜2807) だけでよい。`sed -n` で 80 行以内ずつ読め。certified の意味の正本)
- /work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-paper-methods-ja-2026-09-20/output/insights/2026-09-20/verify-phase-adopted-backoff/README.md (採用候補 2 genome の検証相の一次資料。§4.3 runner の所在が要点)
- /work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-paper-methods-ja-2026-09-20/output/insights/2026-09-19/a1-sized-attempt2/README.md (A-1 sized attempt-0002 の gate 拒否)
- /work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-paper-methods-ja-2026-09-20/output/insights/2026-09-20/t2792-a1-sized-rerun-authorization/README.md (A-1 認可 record の実装 wave)
- /work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-paper-methods-ja-2026-09-20/output/insights/2026-09-19/k2-loop-round3/README.md (K2 3 巡目)
- /work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-paper-methods-ja-2026-09-20/output/insights/2026-09-20/t2795-pair-launcher/README.md (K2 同 job stock 対照口の実装 wave)
- /work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-paper-methods-ja-2026-09-20/output/insights/2026-09-20/verifier-capacity/README.md (verifier の packed 配列化)
- /work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-paper-methods-ja-2026-09-20/output/insights/2026-09-19/mocc-witlight-arm-run/README.md (mocc 軽量 witness 4 arm)
- /work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-paper-methods-ja-2026-09-20/output/insights/2026-09-19/t2773-mocc-template-wave2/README.md (mocc 機械実証 wave 2)
- /work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-paper-methods-ja-2026-09-20/output/insights/2026-09-19/t2288-floor-pair-w1/README.md (B-4 床値 pair の w1)
- /work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-paper-methods-ja-2026-09-20/output/insights/2026-09-19/b10-tail-cohort2/README.md (B-10 右 tail 第 2 cohort)
- /work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-paper-methods-ja-2026-09-20/output/insights/2026-09-20/t2724-ax-delegated/README.md (凍結 v2 g1 の承認 A / active pointer X の発効)
- /work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-paper-methods-ja-2026-09-20/output/insights/2026-09-19_t1998-b7-fixed5-three-workload/certification.json (同一候補 fixed 5 µs の 3 workload 測定の権威 bytes)

**巨大 file の扱い (必ず守れ):** `docs/decisions.md` は 5,788,239 bytes / 69,178 行、`docs/failures.md` は約 2.8 MB、worklog の
archive は `docs/archive/worklog-phase3-09*.md` に 1 エントリ 1 file (本文は先頭 10〜40 行で残りは carry 行)。**全文 `cat` しては
ならない。** `grep -n "^## D<番号>\. "` で位置を出し `sed -n` で 60 行以内ずつ読め。稿が引く D のうち検算に要るのは D2108、D2114、
D2120 項 2・7、D2138、D2143、D2145、D2148 項 11・13、D2155、D2156、D2157、D2159、D2160、D2162、D2174 項 3、D2178、D2180、D2181、
D2182、D2183 である (`grep -n "^## D21[0-8][0-9]\. " docs/decisions.md` で位置が出る)。worklog entry は `grep -ln "^## 2026-09-[0-9]* (<番号>)"
docs/worklog.md docs/archive/worklog-phase3-09*.md` で file を出し、先頭 40 行だけ読め。

コードは `orchestrator/campaign/` と `orchestrator/verifier/` の該当 module を `grep -n "^def \|^class "` と `sed -n` で読め
(`paper_story_a2_certification.py` 5,253 行、`paper_story_a1_paired.py` 9,099 行、`p3_s4_loop.py` 3,410 行、`floor_pair_driver.py`
3,148 行、`b10_backoff_shape_sweep.py` 4,697 行は全文を読まない)。

この段では commit・push・file の書き込みを行わない。成果は最終メッセージの本文だけで返す
(read-only sandbox では `-o` の file を書けない。**出力は file に書かず、最終メッセージの本文に全文を書け**。親の launcher が保存する)。
pytest・build・測定は走らせない (sandbox に書込可能 tmp が無い。静的検査でよい。テスト実測は親が行う)。
予算が尽きそうなら、途中までの結論を下記の出力形式どおりに書いて終われ。無出力が最悪である。

## これは何のレビューか

これは自分たちのプロジェクト (izanagi) の論文用文書 2 本に対する設計レビューである。親 (Claude) が 2 本を書いた。この wave は
軽量版 (docs-only、実装面ゼロ、新規 file 2 本 + 記録 README のみ) で、段 2 plan と段 3 敵対相談は省いた。
**お前は D2148 項 11 が定める「一次資料から事実を再抽出する docs-only wave の段 6 read-only 独立レビュー 1 本」であり、下の
2 レンズを 1 本で担う。** 目的は、方法節が (1) 現行実装 (local main `fec4a8187`) と一致し、(2) 実装済みの機構と各実験で実際に
使った機構を区別し、(3) certified の意味を story 2026-09-20 版 §6 に揃え、(4) 過大主張・時点のずれ・母集合の取り違えを含まない
ことを独立に確かめることである。

親が実走した検査: `tools/check_docs.py` rc=0、稿が引く worklog entry 19 件と D 番号 36 件の見出し実在、稿が引く repo 内 path
(`docs/` `orchestrator/` `patches/` `tools/pegasus/` `output/`) の実在、hex (`fec4a8187` `b7f970dfa` `511c9538` `e9e477ca`) の
現物照合、`git status` が新規 dir 1 つ (untracked) だけであること。**親が一次資料で確かめて直した点** (レビューではここが直って
いるかを再確認せよ): verify fan-out は policy 3 本の `scheduler.nodes` が 5 だが A-2 / A-6 の取得済み attempt は 1 node で走った、
検証相は条件関門を通していない (identity 束縛のみ)、certification の outer status の判定順は `collect_results` の分岐順、K2 の両 role
組立て関数は `k2_next_generation_inputs`、凍結 v2 g1 は entry 1742 (D2180) で発効済みで story 2026-09-20 版の「未発効」は古い。

稿の作り方: 前稿 (2026-09-10 版) の 6 節構成を保ち (brief の (P1))、各節へ 09-10 以後の 7 機構 (A-1 sized policy v3 と 1 attempt
認可の投入経路 + 認可 record、A-2 / A-6 certification の受領証束縛、B-10 静的右 tail・待ち方 grid の事前登録と driver、採用候補
2 genome の検証相、K2 型付き critic 診断、mocc の trace-hook と witness、床値 pair protocol v3) と、story 未反映の着地 (entry
1716 / 1736 / 1742 / 1744 / 1745 / 1746) を足した。数値・図は転載しない (前稿の裁定を継承)。実装対応メモの「使用した走行」欄は
worklog entry / attempt id / request id で名指しする。

## レンズ A — 現行実装・一次資料との照合、実装済み / 使用の区別、母集合

1. **実装アンカーの実在と対応。** implementation.md の 2 つの表 (「主要記述とコードの対応」「09-10 以後の機構」) に書かれた
   module・関数・定数・schema 文字列・policy field・patch 名・job body 名が、現行 worktree に実在し、稿が書く役割と一致するか。
   少なくとも次を code で検算せよ: `paper_story_a2_certification.py` の `collect_results` の status 分岐順 (稿 methods §5 の
   「この順に判定する」) と `record_*_receipt` 3 関数・`_cell_source_binding_status`・`_validate_verify_fanout_hosts` (nodes − 1)；
   `paper_story_a1_paired.py` の `CLASSIFICATION_RULES` (3 値と述語)・`V3_SIZED_RERUN_AUTHORIZATIONS` (定数 1 件の構造)・
   `_assert_no_prior_v3_bench_start`・`run_authorize_rerun`・`_exact_materialization_destination`、policy `paper_story_a1_paired.v3-sized.json`
   の `formal` / `promotion_prohibited` / `result_authority`；`p3_s4_loop.py` の `_validate_k2_critic_diagnosis` (exact 6 field)・
   `planner_context_payload` の K2・非 B-4・reflux on 要求・`k2_next_generation_inputs`・`_run_stock_control_resolved`・`--stock-control`；
   `floor_pair_driver.py` の module docstring (D の式、証明しないことの列挙)・`SPEC_SCHEMA`・`run_window`・`finalize_floor`；
   `orchestrator/verifier/dsg.py` の `_PackedVersions` / `_PackedProducer` / `_build_compact_packed`；`orchestrator/verifier/core.py`
   `verify_trace_dir` の proof surface 要求；`b10_backoff_static_tail_formal.py` の `analyze_interval` / `analyze_cohort` の state 名；
   `b10_backoff_shape_sweep.py` の `holm_adjust`・`SHAPES`；`source_digest.py` の `-dD`；`condition_meaning_gate.py` の
   `evaluate_define_supply_effectuation` / `evaluate_define_runtime_meaning`；`orchestrator/critic/digest.py` の `load_rejections` 等
   3 関数 (前稿は `p3_s4_loop.py` に帰属させていた、新稿はこれを訂正と書く)；`layer3_report.py` の `_mechanism_view` と
   `certifying_input`。
2. **「使用した走行」欄の照合。** 各行の entry 番号・attempt id・request id・job 番号・件数 (30 verify / 候補 = 24 + 6、未完走 2 件 /
   候補、4 arm × 60 走の 0/60・0/60・1/60・1/60、30 check、120 記録、各 62 標本、3 job) を一次資料 README で検算せよ。「使用 0 件」と
   書いた 2 行 (A-1 認可 record、K2 stock 対照口) が一次資料と合うか。
3. **実装済み / 使用の区別が崩れている箇所。** methods.md の本文で、実装の存在を「使った」「走った」と読ませる文、逆に走った事実を
   実装の記述に混ぜている文を探せ。特に: 検証相の runner が repo 外であること、verifier の packed 配列が検証相の後に入ったこと、
   fan-out の node 数、A-1 の認可 record と attempt-0002 の未投入、K2 stock 対照口の未投入、mocc 計装が pin の祖先でないこと、
   軽量 witness が hook branch (CCBench 側) にあること、床値 pair の w2 / finalize 未走。
4. **母集合と射程。** 稿が「certified」「anomaly 0」「完走」「発効」「解除」と書く箇所で、母集合が広すぎないか (検証相を S-1 充足・
   B-8 取得と読ませていないか、outer `reject` を「3 workload とも退行」と読ませていないか、g1 発効を oracle 実走・「科学的に十分な床」と
   読ませていないか、witness の 0/60 を観測者効果の除去と読ませていないか、K2 3 巡目を「効いた」と読ませていないか)。
5. **件数・量化。** 「すべて」「だけ」「唯一」「初めて」「N 件」「7 機構」「19 件」「36 件」を原データから数え直せ。
6. **path と参照。** 稿が引く path・D 番号・T 番号・entry 番号が実在し、内容が稿の記述と合うか。行番号参照が無いことも確かめよ。
7. **凍結物の不変。** `git status --short` で、変更が `output/insights/2026-09-20/paper-methods-ja/` (新規、untracked) だけであること、
   前稿 2 本・story・README・results 稿・実装に差分が無いことを確かめよ。

## レンズ B — certified の意味、主張の強さ、時点、前稿との差分、scope

8. **certified の定義の §6 整合。** methods §1 の定義文を story §6 の「固定条件で certified な correctness の観測 (性能の判定ではない)」
   「certified は実際に build された bytes についての判定であり、要求した構成が build されたことは含意しない」「`src_token` の一致だけでは
   翻訳単位全体の意味の一致を保証しない」と突き合わせ、稿が広く書いている箇所・狭く書きすぎて §6 と矛盾する箇所を挙げよ。
   implementation.md の読み分け表の certified 行も同様。
9. **禁止句。** 「A-1 の値がある」「B-10 を閉じた」「再現されたので飽和しない」「mocc は第 2 成功例」「B-8 を取得した」「全走 anomaly
   ゼロ」「信頼度 1−εⁿ」「pin を前進させた」「K2 で改善した」「無人で回る」「任意 CC を合成できる」に相当する表現 (短縮形・言い換え
   を含む) が 2 本のどこにも無いこと。B-7 については D2174 項 3 の「限定付き充足」の限定 (単一 attempt・descriptive・非認証・反復間
   安定性は未判定) を落とさずに書いているか。
10. **時点語。** 「本稿の時点」「現行」「2026-09-XX に」「以降」が、基準 (local main `fec4a8187`、2026-09-20) と一致しているか。story
    2026-09-20 版 (main `b7f970dfa` 基準) の記述をそのまま写して、その後に古くなった状態語 (g1 未発効、B-7 昇格せず、認可 record 無し、
    stock 対照口無し) を稿が現在形で書いていないか。逆に、稼働中で未着地の wave (A-1 attempt-0002 の投入など) の内容を先取りして
    いないか。
11. **前稿との差分。** 前稿の記述のうち新稿で消えた・変わった箇所を列挙し、各々が (a) 一次資料で古くなった訂正、(b) 構成上の移動、
    (c) 根拠なく落とした、のどれかを判定せよ。(c) があれば must-fix。前稿の「実走・契約・未了の境界」節の B-4 の限界記述
    (writer は create-only、report の 4 分類は未実効、launcher は単一 arm) が新稿で落ちているなら、落としてよいかを一次資料で判定せよ。
12. **scope。** 英訳、新規実験、gate・検査・台帳の追加提案、隣接 docs (story・README・results 稿) の訂正が稿に混じっていないか。
    新しい主張 (性能優越・再現性・因果) を足していないか。

## 守らせる不変条件 (これを緩める所見は refuted として扱う)

- 凍結物 (前稿 2 本・story・results 稿・事前登録) は 1 byte も変えない。旧 attempt の判定を取り消さない。protocol status は成否宣告
  ではない (D12)。規律 7 (当時の判定と現行の主張を分ける)。
- 方法節に性能値・図を転載しない (前稿の裁定)。3 走行と A-1 attempt-0001 と B-7 fixed5 を pool しない (D1993 項 6)。2 cohort を合成
  しない (D2157)。
- 仮想リスク向けの gate・検査・台帳・一般化は scope 外。英訳・新規実験は scope 外。

## 出力形式 (この見出しをそのまま使う。見出しはすべて `##` の階層で書き、`###` を使わない)

## 所見

番号付き。各所見に `real / refuted`、`must-fix / should-fix / nit`、該当 file と節、一次資料の path または D 番号、対案 (訂正後の
文面) を書け。**所見ごとに、放置したときに論文の主張・分類・参照がどう変わるかを 1 行で書け** (書けない所見は nit)。

## 実装アンカー照合表

表 (稿の記述 → module / 関数 → 一致 / 不一致 / 不在)。

## 前稿から消えた・変わった記述の判定

表 (前稿の記述 → 新稿の扱い → (a)/(b)/(c))。

## 照合して一致を確認した範囲

所見ではなく、消極的な証拠として記録する。数値群・参照群を列挙せよ。

## GO / NO-GO

稿 2 本をこのまま凍結してよいか。NO-GO なら must-fix の一覧。

## 総括

10 行以内。最後の節は必ず `## 総括` (`#` を 2 個) とする。`### 総括` と書いてはならない。
