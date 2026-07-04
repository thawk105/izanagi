# 論文ストーリーの横断合成 (2026-07-03 時点 / Phase 3 着手前)

**この文書の位置づけ:** 2026-07-03 時点 (Phase 2 完了・Phase 3 kickoff 進行中) での「論文で何を新規性として主張し、どういうストーリーで語るか」の横断合成。**凍結スナップショットであり更新しない** — Phase 3 主実験が成立すれば headline がそちらへ移動することが計画上確定しているため (phase3.md 後続段 6)。正典は roadmap.md §8 (ポジショニング)・decisions.md (設計判断)・worklog.md (時系列) で、本文書はそれらの導出物。矛盾があれば正典が勝つ。

**例外:** §5 の過大主張チェックリストのみ、執筆フェーズで消し込み式に運用してよい (解消条件を満たしたら `[x]` にして根拠を追記する)。

**生成方法:** 8 系統の並列読解 (roadmap / decisions / phase2+関連 insights / phase3 / worklog / 方法論文書群 [agent-architecture・orchestrator-design・CLAUDE.md 規律・hooks] / insights 全 17 件) + 独立コンテキストの欠落検査 1 段 (主張と証拠の対応・過大主張・見落とし素材)。数値は複数系統が一致したもののみ採録。

---

## 1. 何のプロジェクトか (一言)

CCBench (10 プロトコル × 最適化フラグ群) を素材コーパスに、**AI がワークロード特化の並行性制御 (CC) を自動合成するシステム**を作りながら、その過程自体を研究記録として残すプロジェクト。成果物は「新しい CC + **なぜ速いかの説明** + 試行錯誤の記録」の 3 点で、説明可能性が差別化の核。

## 2. ストーリー (3 幕構成)

物語の骨格は「当初仮説が反証されて主張が移動した過程」そのもの。

### 第 1 幕 (Phase 1) — 信頼できる評価器を先に建てる

- trace verifier (Adya DSG / G2 検出) の検出力を**二重に実証**: わざと壊した Silo (read validation 除去 patch) で 1310 G2 赤 / 無改変の本物 si で 3576 G2 赤 / 素の Silo は緑 →「verifier は計装の副作用でなく正しさそのものを見ている」。逆側は P2-0 の 8 genome 全緑で「緑を取りこぼさない」も対で実証。
- verify-the-verifier (敵対的検証) が「不正な trace で赤を隠せる」false-green の穴を検出 → verdict 3 値化 (indeterminate) で fails-closed に硬化。「pass/fail の verifier」から「integrity を主張の前提に置く verifier」への転換。
- calibration では「cache miss 率の飽和点を探す」前提が masstree の実測で崩壊 (木深化で単調上昇、膝が出ない) → 下限基準 (working set ≥ L3×K) へ方法論を書き換え (D15)。

### 第 2 幕 (Phase 2) — 当初仮説の反証と、価値の所在の発見

論文の心臓部。**対になる 2 つの結果**がある。

**否定的結果 (P2-5, D21/D29):** 当初の絵「LLM 誘導探索は全探索より速く収束する — これが論文の図になる」は反証された。silo のフラグ空間は実質 BACK_OFF=0 の 1 ビットで決まる自明空間で、「誘導が速い」図は評価器の優位を評価器の定義で論証する循環になると設計段階で判明 → 主成果を negative result + critic ablation に枠組み直し (ユーザー承認)。結果:

- LLM 誘導 (中立 critic 30 試行、replay = 新規計測ゼロ) は機械的勾配 (LLM なし貪欲) と有意差なし (確率優越 A=0.581)
- deceptive 構造 (write-heavy: BACK_OFF=1 が実 2 位) では貪欲より**有意に有害** (A=0.230、厳密 permutation p=2.52×10⁻⁴、Holm ×6 でも有意)。誤収束 8/12 = 「自信ある早期停止の負債」
- これは reward hacking (最適化圧力が正しさを攻撃する) の**鏡像** — 評価器側の過信が deceptive 信号下で負債になることの定量実証

**肯定的結果 (P2-4 backoff ケーススタディ, D18/D20):** critic の指標帰属 (「適応 backoff は abort を潰せているが IPC 崩壊 = over-throttling」) が、フラグ空間の**外**の新軸「backoff 量の静的固定」の合成を駆動し、certified serializable を保ったまま stock 最良を write-heavy +38.3% / balanced +11.3% 上回った (cross-run 再現・機序純度の分離まで敵対的検証済み)。stock の適応 (Cicada 型 hill-climbing) が grid 刻み 100us のせいで sweet spot 5-10us に物理的に到達不能で ~560us に駐車する (spin 87.3%) 構造欠陥まで実測で特定。機序は有用 IPC の分離 (BACKOFF_NOINLINE 計器、観測者効果 +0.76% = floor 内で inert) により「abort 半減が有用 IPC 不変のまま効いた = 純 spin 希釈の除去」と閉じた。

この対比から Phase 2 の結論 = **「フラグ探索は自明で LLM の出る幕がない。価値は空間の外への合成にある」**が確定。否定的結果は薄い結果ではなく「なぜコード合成 (Phase 3) が要るか」を定量的に動機づける要石 (keystone)。

### 第 3 幕 (Phase 3、進行中) — コード粒度の合成

EVOLVE-BLOCK マーカーで LLM (coder) の編集面を画定し、主実験を**事前登録形式**で固定済み:「LLM 合成 variant が certified のまま、フラグ空間最適 (P2-2 全探索 ground truth) を between-run noise floor 超で上回り、かつ 4 対照では到達できない」。4 対照 = (1) silo stock 最良 / (2) クロスプロトコル stock 最良 / (3) 同一編集面・同一予算のランダム変異 / (4) 人間が軸を命名し LLM なしで回す機械 sweep。(4) は「利得が機械 sweep で再現できるなら LLM 不要」という帰無仮説を正面から立てる設計。P2-5 の教訓 (機械ベースライン ablation・deceptive 検証・floor 採否・Holm 補正) を高い代償を払って得た方法論として継承する。

## 3. 新規性の主張 (強い順、実証状態つき)

1. **対象の空白** [ポジショニング]: single-node CC の serializability を対象にした AI 合成は先行なし。Jitskit (KV ストア)・IDS (分散 KV consistency) の系譜の 3 本目 (roadmap §8)。
2. **帰属駆動・コーパス駆動の合成** [b1 は実証済み・範囲限定]: ゼロから合成 (FunSearch 型、正しさ崩壊) でも完全証明付き (IDS、CC には重すぎる) でもなく、実証済みコーパスを土台に leading indicators の機序帰属が空間外の新軸を開く (b1 = P2-4 で実証、b2 移植は拡張予約 D32)。Polyjuice/CCaaLF が事前定義アクション空間内の配合探索なのに対し、**アクション空間自体を LLM が拡張する**点が質的な差。
3. **説明可能性** [限定スコープで実証]: policy table という数値の塊しか出せない先行に対し、「なぜ速いか」を機序 (有用 IPC 分離) まで言語化し、主張を WAL の run 値まで辿れる証拠連鎖 (forensic binding) で裏づける。
4. **否定的結果の定量化** [実証済み]: 「評価器の自信ある早期停止は deceptive 信号下で負債」+ オラクル天井 (2−k/N)・winner-tied set による否定的結果の構造的枠組み化。
5. **AI 主導研究の運用方法論** [実運用の記録あり]: 全主張への多エージェント敵対的反証 (積モデル破綻の自己検出 / p_lt 系統バイアス発見→確率優越への再校正 D29 / hooks over-claim の独立検出 D30)、noise floor の用途別二分 (D19)、fails-closed 化、信頼境界 (規律 6)、Phase 完了監査 (§3.7)。「訂正の訂正まで成果物に機械可読で残る」(p2-5-summary.json のキー構造) は誠実性の物理的実装。

**副産物** (単体でも書ける): CCBench 本体の潜在バグ 3 件を網羅探索が露呈し 2 件を上流還元 (WAL ftruncate XOR = PR #116 / ODR 違反 heap-overflow = PR #118)。「網羅的全探索は最適化探索であると同時にコーパスのバグ発見器」。oze の skew 病理 (グラフベース eager 検査の密競合グラフ非スケールの実例)。「realizable trace の全 cycle は必ず G2」定理 (isolation-phenomena.md)。

## 4. 見落とされがちな素材 (欠落検査の指摘)

執筆時に取りこぼしやすいと欠落検査が名指したもの:

- **isolation-phenomena.md** — G2 定理 (ww/wr は commit 順方向、逆走できるのは rw のみ → cycle は必ず rw を含む) + 「G1a/G1b は committed-only trace では観測不能」という trace 形式の観測限界。小さいが独立した理論的貢献の一次資料。
- **ccbench-anatomy.md** — 死にフラグの発見 (NO_WAIT_OF_TICTOC 等 3 種は #if 分岐が無く探索空間から除外)、Silo の trace 3 点が全て CC-native フィールドで trace 専用フィールド追加ゼロ (規律 1 を最小侵襲で満たせた根拠)、setThreadAffinity が as-built で死んでいる発見、全 protocol 探索空間見積 ≈258 バイナリ (cicada 2⁶ / oze 2⁷ = Phase 3 空間拡大候補の定量的由来)。
- **audit-2026-06-30.md** — 監査方法論の規模定量 (初回 10 次元 × 57 エージェント → confirmed 34 / partially 12 / refuted 1、以降 2 巡)。refuted の実例 (g++ 3 版実走で source_digest バイト一致 = 誤検出を実測で棄却) は「敵対監査は誇張も削る」の一次証拠。
- **phase1.md の trace 妥当性定量** — trace C 行数 = ベンチ commit_counts_ 完全一致 (327,918)、非 genesis read の 100% matchable・ORPHAN 0、perf build の trace シンボル 0。verifier の検出力実証とは別軸の「trace-hook 自体の健全性」。
- **.claude/agents/critic-experiment.md** — P2-5 リーク制御の一次資料 (最適解 literal の物理削除・guided.py 以外の閲覧禁止の実文面。tools=Bash のみ / model=opus)。
- **output/campaigns/p2-5-summary.json** — recalibration_2026_07_02 / correction_2026_07_03 がトップレベルキー = 統計訂正の履歴が成果物に機械可読で残る実例。
- **output/campaigns/p2-2-summary.md の read-heavy 行** — 自分の勝者主張にも floor を適用し「+0.5% は信用できる差でない」と書いた、選択的報告をしない規律の最小実例。
- **insights/2026-06-30_git-log-divergence** — 外部プロセス由来の履歴改変をエージェントが「自分が壊した」と誤認し破壊的修復に向かいかけた失敗モードの分析。§3.7/3.8 系の運用素材。
- **campaign-id 内容ハッシュは C1 drift と対で語る** — honest-by-construction な同一性 (spec 内容ハッシュ) が、submodule pin 前進で consumer 3 本を沈黙 skip させた実失敗 (C1) と、その恒久解 (dir 名 discover への統一)。「同一性の強さが可用性と衝突した」記録込みで初めて正直な主張になる。
- **文書一貫性の機構 = 運用方法論 (新規性 5) の一次素材 (2026-07-05 追記)** — 7/4 の docs 横断監査 (7 レンズ 54 エージェント、敵対検証つき) が確定矛盾 39 件 ≒ 根本原因約 10 個を検出 (`audit-2026-07-04-docs-consistency.json`)。定量観測された非対称: **状態の再掲 (CLAUDE.md 現在地・roadmap の現況主張・must 一覧の写し) が一次記録 (worklog + git) と衝突した全ケースで、誤っていたのは再掲側** — 状態の再掲は陳腐化するキャッシュである。ただし一次記録側も無謬ではない (worklog 自身にコミット帰属漏れ = 記録欠落が 1 件あった。監査 3 指摘) — その対策が節目ごと更新の handoff と追補運用で、正本側の信頼性も機構で支える。恒久対応 (7/5、worklog 参照) は計測対象システムに課している原理をエージェント運用層へ再帰適用したもの: (1) 可変状態の正本一元化 (ポインタは腐らない・キャッシュは腐る)、(2) `docs/handoff/` = **セッションの WAL** (突然死・中断からの再開をセッションごとの上書きファイルで担保。前夜のセッション突然死を生ログ採掘で救出した実費が導入の動機。並行セッションの宣言板を兼ねる)、(3) `tools/check_docs.py` = 決定的 lint (行番号参照・現況再掲の禁止パターン)。「WAL・内容ハッシュ同一性・偽 cache hit 封鎖 (D34) と同型の失敗が自分の文書運用に居座っていた」という再帰構造ごと語ると、AI 主導研究の運用方法論の章が具体機構 + 定量 + 失敗駆動の導入経緯で立つ。

## 5. 過大主張チェックリスト (執筆時に消し込む)

欠落検査が「そのまま書くと自前の監査記録・限界記載と矛盾する」と特定した項目。執筆フェーズで各項を確認し、解消条件を満たしたら `[x]` + 根拠を追記する。

- [ ] **「certified なまま +38%/+11%」の但し書き** — certified は検証 workload (tuple200/thread4/rmw=true) 上で、性能 workload (1m/thread48/rmw=0) の trace は未検証。correctness-inert は機序論証 (backoff は timing のみ) に依る外挿。headline には必ず条件を付ける。**解消条件: S2 (certify を perf workload に揃える) の消化。**
- [ ] **「verifier はツール権限で書き込み隔離」と書かない** — audit-2026-06-30 §4 が「Bash を持つ以上 sed -i 等で書ける、tool レベルの隔離は不成立」と裁定済み (2026-07-02 に宣言を honest 化)。正確な形 = 「専用書き込みツールの除去 + prompt 規律による禁止」。**恒久 (表現規律)。**
- [ ] **hooks を「実装済みの機械防壁」と書かない** — 敵対検証 2 巡で real 13 件 (critical 1 = 行連結 splice)、「テキスト検査に完全性を負わせる設計は原理的に破れる」を実証し、一次防壁 (source_digest / 観測者効果二重検査) へ責務再配置 (D30)。語れるのは「否定的結果込みの防壁設計事例」。**解消条件: 方針 A の配線 + 回帰テスト緑 (それでも「最小第二防壁」としてのみ)。**
- [ ] **「構造化 anomaly の自動還流」(ARA への優位) は設計であって実証ゼロ** — S4 配線 (verify-red → abort payload → load_rejections) は完了したが、赤が実際に variant 生成へ還流して探索を改善した実績は無い (赤が出るのは Phase 3)。IDS の「診断を accept/reject に落とすと劣化」ablation も借用のみで自前未実施。**解消条件: Phase 3 で赤→還流→改善の実例、可能なら還流 on/off ablation。**
- [ ] **「コーパス駆動」の実働範囲を明記** — 探索・合成が回ったのは silo 1 protocol + backoff 1 軸のみ。trace-hook は silo/si 以外に未移植 (S1) で他 protocol は verify 不能、クロスプロトコルは baseline 計測 (7 protocol) 止まり。**解消条件: S1 移植 + 空間拡大 (cicada/oze) の実走。**
- [ ] **P2-5 誘導アームのモデル素性を実験条件に明記** — critic-experiment = model: opus / tools: Bash のみ (frontmatter)。本文系文書に未記載のため、論文の再現性記述に必須。**恒久 (記載事項)。**
- [ ] **「統計的に裏打ちされた」の正確な形** — 有意性検定ではない。reps≈5 の Mann-Whitney は完全分離で常に p≈0.012 を返し無力。主防壁は between-run floor 丸め + floor〜1.5×floor 帯の cross-run 再現 + 証拠連鎖。**恒久 (表現規律)。**
- [ ] **「一晩 8 時間で約 1 万 run」は机上見積り** — CCBench VLDB 論文の「1 run 約 3 秒」からの試算で、この run レートを実証した記録は無い。実測値 (P2-2 の 24 評価等) と同列に書かない。**解消条件: 実測するか、見積りと明記。**
- [ ] **「AI が CC を合成し説明した、は新しい」の一般主張は Phase 3 まで留保** — 現時点で実証済みなのは silo 1 protocol 内 backoff 1 軸・contention 域 2 勝 1 敗 (read-heavy は −6.6% 純損)・単一動作点 (skew0.9/48thread/1m)。現在言えるのは「限定スコープでの最初の成立例」まで。**解消条件: Phase 3 主実験 (4 対照 headline) の成立。**
- [ ] **評価器の階層化 (Tier 0-3) を新規性として語らない** — 実体化済みは Tier 0 (ビルド/スモーク) と Tier 1 (trace verifier) のみ。Tier 2 (Hermitage 移植) は未着手、Tier 3 (形式検証) は初期スコープ外。**解消条件: Tier 2 着手、または「設計」と明記。**
- [ ] **中間 backoff 自体の単体新規性を主張しない** — contention management は数十年の蓄積 (D18 が明示的に線引き)。主張は「Izanagi 方法論のケーススタディ」+ 「Cicada 型適応の構造的 over-throttling の機序特定」まで。**恒久 (表現規律)。**

## 6. 一言でまとめると

論文の骨は —— **AI に CC を合成させたら、賢い探索は自明空間で役に立たず有害ですらなかった。価値は指標の機序帰属が探索空間の外に新軸を開くことにあり、それは正しさゲートを一度も緩めずに stock 超えを達成した。そしてこの結論自体が、全主張を敵対的検証にかける運用規律の産物である** —— という、否定的結果と肯定的結果が互いを支える構造。Phase 3 主実験が成立すれば headline はそちらに移り、本文書の実証群はその動機づけと方法論の実績になる。
