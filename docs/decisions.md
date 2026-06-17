# 設計判断の記録 (Decisions)

主要な設計判断と、その理由・却下した選択肢を記録する。「なぜこうしたか / なぜ別の道を選ばなかったか」を後から引けるようにするためのもの。

---

## D1. 最適化の粒度: パラメータ寄りスタート

**決定:** Phase 1-2 はパラメータ粒度 (a)、Phase 3 でコード移植 (b) を足す。アルゴリズム粒度 (c) はやらない。

**理由:**
- パラメータ粒度の生成 variant は「CCBench が元々持つ最適化フラグの組み合わせ」なので理屈上は全部正しいはず → trace verifier の検証に最適 (Phase 1 のゴールと噛み合う)
- 探索空間が有限で全探索すら可能 → LLM 探索の到達速度を全探索の最適と比較でき論文の図になる
- (a)→(b) の移行が論理的に繋がる

**却下した選択肢:**
- 最初からコード移植 (b) 主軸: 手広くやりすぎて評価器が固まる前に reward hack が湧き、失敗の切り分けができなくなる
- アルゴリズム粒度 (c): 自由度が高すぎて正しさが崩壊。CC では非推奨 (FunSearch 的アプローチは CC には重すぎる)

---

## D2. 完全な形式証明 (IDS式 Rocq) を初期スコープ外にする

**決定:** IDS の「正しさを後付けにしない」思想は採用するが、Rocq による完全な形式証明自体は初期スコープに入れない。

**理由:**
- IDS は 7 spec で平均 6.8時間・$106、Chapar CC の証明は 3,037行/79 lemma。重い
- Izanagi の variant は C++ の many-core ベンチ実装。これを Rocq で形式化するのは現実的に膨大
- 代わりに trace ベースの確率的検証 (Tier 1) + 既存テスト移植 (Tier 2) で実用的な確信度を得る

**採用したのは思想のみ:** 二相 verifier を「開発相でも正しさを誘導シグナルとして使う」に格上げ。完全な形式証明は roadmap の「将来拡張」に置く。

---

## D3. 二相 verifier を IDS式に格上げ

**決定:** 開発相の verifier も毎 iteration 回し、pass/fail でなく構造化フィードバック (なぜ壊れたか) を LLM に返す。

**理由:** IDS の ablation が決定的 — 構造化 Rocq 診断を単なる accept/reject に置き換えると全 spec が 3回中1回以下の成功に落ちた。「正しさシグナルを後付けにすると失敗する」「診断の中身が探索を導く」。

当初は「開発相=安く回帰検出、検証相=最後に厳密」という二相だったが、IDS の教訓で「開発相でも診断を返す」に修正した。

---

## D4. 観測者効果の分離 — `#ifdef` でコンパイルアウト

**決定:** トレース取得はランタイムフラグでなく `#ifdef TRACE` でコンパイル時に除去。正しさ検証 (trace-enabled) と性能計測 (trace-disabled) を別ビルド・別 run にする。

**理由:** トレース処理がランタイム分岐だと、false でも分岐予測ミス・命令キャッシュ汚染で性能に効く。これがあると「同じ CC でも variant が baseline に不当に負ける」。査読で必ず突かれる計測妥当性の穴を先に潰す。

**付随する規律:**
- 性能比較は variant も baseline も trace-disabled で揃える
- メタデータは「CC本来」と「検証専用」を区別、後者だけ `#ifdef` 隔離
- perf は trace-disabled build に当てる
- (採用) ビルド等価性の機械検証: 両ビルドで最終 DB 状態が一致するか比較

---

## D5. レコード数の自動キャリブレーションを別レイヤーに分離

**決定:** レコード数の決定を CC 探索とは別の calibrator が担当。cache miss 率の飽和点で決める。

**理由:** 実験パラメータの妥当性確保と CC 探索を混ぜると設計が濁る。見るべきは throughput でなく cache 利用率 (CCBench I1)。飽和点以降は時間を食うだけで測定値が変わらない。小さすぎると many-core の cache 競合が再現されない。

**注意:** 飽和点は thread 数依存。探索 thread 数を固定してからキャリブレーションする。

---

## D6. リポジトリ構成: submodule + パッチ運用

**決定:** Izanagi リポジトリ + CCBench を submodule。CCBench への改変は patches/ で管理し、実験後 git checkout でクリーンに戻す。

**理由:** CCBench を汚さない (還元差分が綺麗に切り出せる)、バージョン固定で再現可能、改変が明示的。

**還元スキーム:** CCBench のバグ等は output/insights/ に構造化レポートを吐き「還元判断: ユーザー確認待ち」を付ける。AI は構造化まで、上流 PR は人間が判断 (誤検出を防ぐ関所)。

---

## D7. サブエージェントの段階導入とツール権限による隔離

**決定:** Phase 1 では verifier と calibrator だけ実体化。残り (critic/profiler/planner/coder/auditor) は agent-architecture.md に仕様予約し、該当 Phase で生成。verifier には書き込み系ツールを与えない。

**理由:**
- 段階導入は ablation で各コンポーネントの効果を測るため (Jitskit の累積 ablation に倣う)
- verifier から書き込み権限を外すのは「検証役が実装を勝手に直す」事故を構造的に防ぐため。Jitskit が auditor を別エージェントにした「見張り役を最適化圧力から隔離する」をツール権限レベルで実装

**却下:** 最初から7体並べる → 探索が失敗したときどのロールのせいか切り分けられない。ECC (60 agents) のような規模は単一研究目的に過剰。

---

## D8. hooks は Python・最小限の2つだけ

**決定:** hooks は Python で実装し、(1) 観測者効果違反 (`#ifdef TRACE` 外への検証専用メタデータ書き込み) の警告、(2) verifier 迂回での性能数値更新の阻止、の2つだけ。

**理由:** オーケストレーション層が Python なので依存を増やさない。ECC は可搬性のため全 hook を Node.js + 大量に持つが、Izanagi は単一マシン・単一目的なので最小限。この2つは絶対規律1・2の機械的執行 (auditor の事後監査に加えた書き込み時点の第二防壁)。

---

## D9. Open-Ended Evolution は Phase 3.5 に予約

**決定:** OEE の完全機構は Phase 3.5。安い果実 (多様性保存・whiteboard) は初手から。

**理由:** OEE が意味を持つのはコード移植でアクション空間が開く Phase 3 以降。パラメータ空間は有限で OEE と相性が悪い。初手で入れると「LLM 誘導の進化ループ」と「OEE 機構」のどちらが効いたか切り分けられない。評価器が固まる前に最適化圧力を最大化する OEE を載せると reward hack が auditor の追いつかないペースで湧く。

**接続点:** 層3の多様性保存を完全な MAP-Elites/quality-diversity に格上げする形で入る。ablation で OEE 有り/無しを比較する。

---

## D10. 環境の二層戦略 — Mac devcontainer (開発層) と Linux 実機 (計測層)

**決定:** 開発は Mac + devcontainer、性能計測・calibration は Linux 実機。devcontainer は最小構成 (.devcontainer/ 参照) で初手から導入する。

**理由:**
- CCBench は Debian/Ubuntu 前提で macOS ネイティブではビルドできない。Mac で開発する以上、Linux コンテナは必須
- ただし Mac 上の Docker は VM 内 Linux であり、**HW PMU がパススルーされないため perf の LLC-load-misses が取れない** → calibrator の核心 (cache miss 飽和点) が動かない
- 性能数値も VM・virtiofs のオーバーヘッドで歪む。観測者効果の排除 (D4) と整合させるため、計測層は Linux 実機に分離する

**作業の割り当て:**
- 開発層 (Mac devcontainer): Phase 1 タスク0-3 (解剖・trace-hook・verifier・赤を出せる証明)、orchestrator の WAL/リカバリ。「機能の正しさ」の問題は全部ここで完結する
- 計測層 (Linux 実機): タスク4 (calibrator)、タスク5 の性能部分、Phase 2 以降の全ベンチ

**Apple Silicon の注意:** ネイティブコンテナは ARM64 Linux。CCBench が x86 intrinsics 等で ARM ビルド不可の場合、Rosetta で amd64 を回す逃げ道はあるがエミュレーションのため開発専用と割り切る (性能数値は一切無意味)。ARM64 ビルド可否はタスク0 の確認事項。

**Claude Code との接続:** 公式 devcontainer feature (ghcr.io/anthropics/devcontainer-features/claude-code) でコンテナ内に Claude Code を入れる。認証は named volume (~/.claude) で永続化。コンテナ内なら無人運転 (--dangerously-skip-permissions、非root必須) もホストを汚さない。参考: https://code.claude.com/docs/en/devcontainer

---

## D11. roadmap を living document にし、版歴を研究記録として保存する

**決定:** roadmap は Claude が改訂できる戦略文書とする。改訂時は旧版を docs/roadmap-history/ に凍結 (append-only、初期版は永久保存)、改訂理由を decisions.md に記録、大改訂はユーザー確認。絶対規律 (CLAUDE.md) のみ Claude 不可変の憲法として階層を分ける。

**理由:**
- 更新権限を明示しないと Claude は保守的に振る舞い、設計の歪みに気づいてもタスク消化に倒れる。「全体の絵の改善への挑戦」は明示的な許可と手順があって初めて起きる
- 版歴 = 設計仮説の変遷記録 = 論文の「当初Xと考えたがYが判明しZへ転換」という方法論 narrative の原料。Izanagi の差別化 (variant の採否理由の説明可能性) と同じ原理を研究自体に適用するもの
- 「初期版を消さず版を積む」は orchestrator-design の WAL/append-only 思想と同型 (roadmap の多版管理)
- 憲法 (不変) / 戦略 (版管理つき可変) / 戦術 (自由) の三層は、可変性の線引きを構造で示し、絶対規律が改訂の波で侵食されるのを防ぐ

---

## D12. 論文執筆は Izanagi のスコープ外 — 材料レポート (ARA 的 artifact) までを担い、執筆は別システムに委ねる

**決定:** Izanagi は研究成果物として **honest-by-construction な「材料レポート」(ARA 的 artifact)** の生成までを担う。論文の narrative 生成・推敲は Izanagi のスコープ外とし、別システム (ユーザーが自動執筆を試す) がそのレポートを消費する。構想メモとして本エントリを残し、実装は Phase 3.5 以降。Phase 1 では何も生成しない。

**背景:** ARA (arXiv 2604.24658, roadmap §7) が「物語 PDF でなく機械検証可能 artifact こそ一次研究対象」と主張し、その 5 要素が Izanagi の既存成果物とほぼ 1:1 で対応することから、「Izanagi に論文執筆までやらせるか」を検討した。結論は「執筆は外に出し、Izanagi は材料生成に徹する」。

**既存成果物 → ARA 5要素の対応 (論文のためでなく探索の正しさ・再現性・観測者効果分離のために既に必要 = スコープ追認であってスコープ拡大ではない):**
- exploration graph ← whiteboard memory (却下設計の蓄積) + decisions.md (却下選択肢つき) + roadmap 版歴 (CLAUDE.md「過去の版は絶対に消さない」)
- evidential grounding ← WAL (output/runs/、環境タグ必須) + noise floor 実測 + 中央値/CV/有意性 (§3.6)
- executable code spec ← patches/ + commit hash 固定 CCBench submodule + ビルド等価性の機械検証
- scientific logic 層 ← 層3「なぜ速いか」説明 (差別化の核心)
- native review ← verifier (G2 cycle 検出、構造化フィードバック、書き込み権限なし)

**なぜ執筆を外に出すか (採用根拠):**
1. **自己評価ハザードの構造的回避。** 論文には (A) 機械再生成可能な事実主張 (中央値/CV/noise floor/有意性、trace #N で G2 検出) と (B) 因果・優位性の解釈主張 (なぜ速いか/新規性) がある。差別化の核心 (層3) はまさに (B) = 本人の自己解釈で、最も検証が緩く reward hacking (規律2) の最弱環になる。執筆を別システムに分離すれば、claim authoring と claim adjudication の分離をシステム境界で無料で得られる (Izanagi 内に paper-writer と隔離 paper-auditor を作り込む必要がない)
2. **スコープが締まる (規律5)。** 「論文を書く第二の巨大システムが Izanagi の中に生える」膨張を回避
3. **得意/不得意の正直な切り分け。** Izanagi は evaluator 駆動・硬い正しさゲートのシステム。推敲・narrative は硬いゲートが効かず LLM が最も「盛れる」領域 = 外出しが原理的に正しい
4. **ARA 思想とより整合。** artifact が一次対象、下流が消費、という ARA の構図そのもの

**死守する不変条件 (これが崩れると分離が無意味になる):**
- **材料レポートは honest-by-construction であること。** LLM がキュレーションした「ハイライト集」でなく、**WAL + whiteboard の完全・決定論的な射影**であること。全 run 値・全 reject variant・noise floor・環境タグを漏れなく含む (生存者バイアスを残さない)。完全性こそが正直さの担保。これを守らないとチェリーピッキングが「何をレポートに載せるか」の上流に移動するだけ
- **事実(A)は機械コンパイル**し LLM の作文を通さない。**判定(B) (成功/新規性) をレポートに事実として焼き込まない** — レポートは証拠を並べるだけで勝敗を宣告しない
- **最上位判定** (研究として成功か / 新規性があるか / 評価器自身は信頼できるか) を**どのシステムであれ自動で閉じさせない**。評価器の妥当性を評価器の出力で論証する循環になるため、人間または独立手段に残す。CC の正しさを verifier 隔離で守った思想を、研究の正しさの判定で放棄しない

**段階:** Phase 1 = 本構想メモのみ (実装禁止、データ規律を論文向けに「盛る」改造も禁止 — データ規律は探索の正しさが決め、論文都合で歪めない)。Phase 2-3 = 生成はせず「生成可能な状態の基盤」だけ整える (WAL に環境タグ・noise floor・全 run 値を残す配線=§3.6(5) で予約済み、whiteboard に失敗を改竄不能・選択不能に残す規律の厳格化)。Phase 3.5 以降 = WAL/whiteboard を ARA 的レイアウトに並べ替える**薄い rollup/レンダラ**として材料レポート生成を解禁 (新しい推論・主張生成をするサブシステムではなく、既存構造化データの並べ替えに限定)。

**却下した案:** 「Izanagi が narrative 論文まで書く」案。ARA-fit が高く魅力的だが、自己解釈(B)の正しさという最弱問題を Izanagi 内部に抱え込み、評価器が固まる前 (Phase 1) に最も検証困難な層を載せることになる (D9 で OEE を後回しにしたのと同型の罠)。執筆を外に出す方が分離が clean。

**位置づけ:** これは協議合意による設計判断の記録 (roadmap 改訂セレモニーの対象外。版上げ・history 凍結はしない)。verifier 隔離 (D7) の思想を研究 artifact 層へ延長したもの。

---

## D13. 出力レイアウト — campaign 軸 + env 軸の二分、同一性は内容ハッシュ

**決定:** output/ を二軸に分ける。campaign スコープ (`output/campaigns/<campaign-id>/` = 入力 spec + 探索 config 単位、D12 射影の単位) と env スコープ (`output/env/<env-tag>/` = calibration/noise floor、入力非依存)。campaign-id は `<spec-slug>-<search-tag>-<cfg-hash8>` (可読プレフィクス + campaign を決める入力の正準シリアライズの内容ハッシュ)。詳細仕様は orchestrator-design.md「出力レイアウトと campaign 同一性」。

**理由:**
- 本システムは入力ワークロードごとに特化 CC を作る (roadmap §1) ので、出力を入力ごとに分離しないと複数 campaign の variants/runs/reports が単一グローバル名前空間で衝突する
- ただし calibration/noise floor は (env, thread数) ごとで入力非依存 (roadmap §4)。入力ごとにネストすると campaign 毎に再 calibration になり絶対規律4 違反 → env スコープに分離
- 内容ハッシュにより (a) クラッシュ再起動を跨いで同じ (spec,config) が同じ id に決まりリカバリが成立する (D)、(b) spec を編集して名前据え置きでも新 id になり古い WAL に比較不能な run を混ぜない (D12 honest-by-construction / §3.4 改竄識別)

**却下した選択肢:**
- **date 軸** (`output/<start_date>/...`): 起動時刻キーはクラッシュ後の別時刻再開で空ディレクトリを生みリプレイ対象を失う (D 破綻)。created-at は manifest 内 provenance に留める
- **git ブランチで campaign 分離**: 出力は生成データ (キャッシュバイナリ/trace/perf ログ、大半 gitignore) でソースでない。WAL リプレイ・D12 の全 reject variant 横断射影はブランチ跨ぎで横断クエリできない。コード変異の隔離は別途 worktree + patches/ で済んでいる (D6, Isolation I)
- **フラット維持** (`output/{variants,runs,...}`): campaign が世界に1個の前提。段階導入 (規律5) を理由に先送りも検討したが、campaign 同一性キーは WAL スキーマを書く Phase 1 タスク6 時点で必要 (リカバリが「どの campaign の WAL か」を要する) で、後で剥がすのが高い基盤スキーマ。キーの形だけ今正しくし、campaign GC 等の機械化は作らない (規律5 が禁じるのはコンポーネント早出しであって基盤スキーマの先送りではない)

**位置づけ:** 協議合意による設計判断の記録 (roadmap 改訂セレモニー対象外。版上げ・history 凍結はしない)。

---

## D14. trace のコンパイルアウトは `#if TRACE` で実装する (naive な `#ifdef TRACE` は観測者効果を漏らす)

**決定:** 絶対規律1 が要求する「trace をコンパイル時に消す」を CCBench 上で実装するとき、コード側は **`#if TRACE`** を使う (または cmake 側で値が 0 のとき `-DTRACE` を出さない)。CLAUDE.md の表記どおりの `#ifdef TRACE` を、CCBench の cmake 規約 (フラグを常に `-D<NAME>=<value>` で定義) のまま実装すると、`-DTRACE=0` でも `#ifdef TRACE` が**常に真**になり trace コードがコンパイルアウトされず、観測者効果が漏れて絶対規律1を破る。

**背景 (タスク0 解剖):** CCBench は最適化フラグを cmake CACHE 変数 → target-private `-D<NAME>=<value>` で**常に定義**する (`cmake/Options.cmake`, `ProtocolHelpers.cmake`)。既存の計測計装 `ADD_ANALYSIS` はこの規約のもと `#if ADD_ANALYSIS` (数値マクロ) として、struct フィールド・`rdtscp` 計測サイト・集計・表示の全軸を完全コンパイルアウトしており (runtime 分岐でない)、Izanagi の trace ビルドのほぼ完全な実装先例になる。ただし `ADD_ANALYSIS` が `#if` (常に定義される値) なのに対し CLAUDE.md は `#ifdef` と書いており、この差が罠。

**採用する実装:**
- コード側を **`#if TRACE`** に統一 (`ADD_ANALYSIS` と同規約)。`-DTRACE=0` が常に定義されても `#if TRACE` は偽で確実に消える。
- cmake は `CCBENCH_TRACE 0 CACHE STRING` を足し `ccbench_universal_definitions` 経由で `-DTRACE=<v>` を流す。correctness build = `-DTRACE=1`、perf build = 既定 `-DTRACE=0`。
- 代替: 「値 0 のとき `-D` を落とす」方式 (`INSERT_*_DELAY_MS` の空値 drop = `ccbench_normalize_options` に先例) を採れば `#ifdef` も使えるが、`#if TRACE` の方が単純で先例 (`ADD_ANALYSIS`) と一致するので推奨。
- **TRACE は `ADD_ANALYSIS`/`DEBUG_MSG` とは別マクロ**にし、variant の性能比較 genome (`#ShowOptParameters()` 由来) に絶対含めない。

**これは絶対規律1の変更ではない。** 絶対規律 (憲法) は不変。本エントリは「コンパイルアウトする」規律を CCBench のマクロ規約上で**正しく実現する手段**の確定 (実装詳細=戦術)。CLAUDE.md の `#ifdef TRACE` という語は「コンパイル時除去」の意であり、実装は `#if TRACE` で満たす。

**位置づけ:** 協議合意による設計判断の記録 (roadmap 改訂セレモニー対象外)。タスク1 (trace-hook) 実装の前提。
