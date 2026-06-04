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
