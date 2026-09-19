---
schema: izanagi-spool-v1
ledger: decisions
authored: 2026-09-19
wave: worktree-dev-wave-b5-generator-contrast-prereg
seq: 2
---

## {{D:b5-generator-contrast-prereg-v1}}. B-5 生成器対照の事前登録 v1 を別 file に作り、主張の形・評価数予算・score・判定順を結果を見る前に固定する

**決定:** 2026-09-19 のユーザー決定 (固定 backoff hole の内で LLM (K2 loop) / ランダム変異 / 機械 sweep の
3 生成器を同一予算で比べる事前登録の**作成だけ**を認可、本走と D1409 の条件変更は不認可) に従い、
`docs/b5-generator-contrast-preregistration.md` (v1、未発効) を新設した。`docs/phase3-main-experiment.md` と
paper-story は編集しない (D1012 の作法)。設計の骨子:

- 主張の形は D1067 の条件付き優越に限る。失敗条件 (c) の成立を正当な結末として事前に固定し、headline・D52 の
  休眠・「非列挙」の定義 (D1409、D1441) を変えない。
- 予算単位は評価数 B = 10 (verifier の anomaly reject も消費)、原提案上限 A = 30。D39 決定 2 から継承するのは
  数値だけで、A/B 分離・3600 秒撤去・収束停止の不適用は本走認可時に確認する実質改訂と明記。
- 候補集合は 3 arm 共通の整数 µs 1..1000 (Tier 1 文法 + 値域 + 帰属整合)。random は離散 log-uniform
  (SHA-256 counter stream)、sweep-matched は `EXTENDED_SWEEP_US` ∩ [1,1000] の 28 点を hash 順に B 点。
- 評価経路は 3 arm とも `p3_s4_loop` の hole literal 経路、較正済み動作点 (1M / 48 / 3 s / 5 reps)。
  session = 既存 bench 経路 (5 rep、最大 3 round の品質再測定、rep 完走要求)、不安定は品質欠測。
- score = endpoint の独立再計測 5 session の median (絶対 tps)。certified 無しの系列は block stock の median
  (fallback)。anomaly は値単位で workload 内の全 arm・全系列の endpoint 資格を奪う。
- 判定 = 系列番号で対にした log 比の片側 exact 符号反転 permutation、Holm 族 6、2 対照への連言。
  等価域は stock CV と 3 % の大きい方、endpoint CV は精度 gate (2 倍超で判定不能)。fallback 対を除く副解析を
  登録し、fallback 対が 2 以上なら副解析を報告値にする。結末は 規約不適合 → 判定不能 → 優越 → 同等 (c) →
  逆向きの記述的差 → 判定不能 の順で一意に決め、両 arm の certified 系列が 6 未満なら「生成不成立」。
- 既存機構の照合: 文法・帰属整合は実装不要。較正動作点の CLI、session 契約の束縛、B/A 台帳と停止の不適用、
  重複の fresh 評価、exact correctness 経路、系列開始 stock、random 生成器、sweep の hash 順 B 点、
  解析 consumer は**実装が要る**。本 wave では実装しない。
- 費用は 1773 論理 session (探索 1080 + 系列開始 stock 108 + endpoint 再計測 540 + block stock 45)、百時間級。
  総実行 wall の上限は試走後に本走認可で決め、本書では固定しない。

**理由:**
- 前回 (D1012) は適格軸が無く正本化を見送った。今回はユーザーが編集面を固定 backoff hole に定め、主張を
  D1067 の形に狭めたので、拘束力ある文書を別 file に置ける。ただし本走の認可は無いので発効 commit と分ける。
- 本 hole の受理域は 1000 点で完全列挙可能である。前回の三すくみ (有限対照と非列挙軸の両立) は、必要性を
  要求しない条件付き比較に限れば前提にならない。これは D1409 / D1441 の解消ではない。
- K2 手動 loop の性能構成は配線規模 (100k / 4 / 1 s / 2 rep) に固定され、`drive_iteration` は単一 layout で
  入口停止し、同一 genome は WAL から復元される。事前登録はこれらを「実装が要る」と正直に載せ、運用だけで
  本走できるとは書かない。
- 段 3 の敵対相談 2 本が、session 成立条件 (bench の品質再測定)、同値 anomaly の波及、共有 stock と
  exact 検定の交換可能性、不安定性と判定不能の優先順位、endpoint CV による等価域の膨張を指摘した。いずれも
  親が設計で閉じた (ユーザー承認で代替しない)。

**却下した選択肢:**
- `docs/phase3-main-experiment.md` へ追記する — D1012 の作法に反し、発火 commit 前の正本化になる。
- 探索 job ごとに stock を対測定する (1080 session) — 費用が倍になり、規律 4 に反する。系列開始 stock 1 本と
  block stock で代替した。
- endpoint 専用の floor session (540) — score の 5 session で CV を出せる。等価域には入れず精度 gate に使う。
- anomaly を −100 % の性能値へ変換する — 正しさの失敗を任意尺度の性能差にする。fallback と (a) 記録で扱う。
- 系列数を n = 9 に縮める — 本 v1 には置かない。採るなら結果を見る前に別仕様として固定する。
- K0 (知識なし LLM) arm を足す — 3 arm の認可範囲外。知識の非対称は限界として明記する。
