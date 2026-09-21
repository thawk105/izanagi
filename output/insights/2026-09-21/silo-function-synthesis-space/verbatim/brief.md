# 段 1 brief — Silo の関数単位合成空間の設計 (2026-09-21 21:4x JST、基準 main 36fb14a3d)

- 研究前進: VLDB EA&B 案の P1 (差分分析 §4)。列挙し尽くせない空間 (LLM が関数本体を書く) を 1 つ定義し、有効候補率・reject の分類・LLM と random/sweep/BO/進化の同一空間比較を測れる状態にする。完了判定 = 設計 (insight) と「条件付き採用 + 実装前の必須条件」を decisions fragment に固定し、次 wave の Codex author が段階 C (骨格 patch・配線) を再設計なしで着手できること。
- scope: 設計だけ (docs-only: insight + decisions fragment + worklog fragment)。実装・build・計算投入はしない。仮想リスク向けの gate・検査・台帳・一般化の追加は scope 外。既存 gate の「新しい空間に合わせた置き換え」は空間の定義に必要な範囲だけ書く。
- 確定済みユーザー裁定: 裁定控え 項 3 (関数単位のコード空間を開く、#include / 関数 / 型追加禁止・3 file の制限を広げてよい、正しさゲートは不変)、項 4 (1 タスクの計算が 2 node 時間以上なら事前確認)、項 6 (失敗候補込みで公開可)、依頼文 (候補 = abort 後の待機・再試行、競合状態に応じた待機。validation・lock 取得周辺を含めるかは本 wave が判断)。
- 不変条件: 規律 1 (trace は compile 時除去、diff-of-diffs `assert_trace_diff_matches_head`)、規律 2 (anomaly 即 reject、検証を甘くする変異を採らない)、規律 3 (毎 iteration 検証 + 構造化フィードバック)、規律 6 (LLM 出力はデータ)、D127 (coder 由来 build は明示 opt-in)。D48 の読取禁止は trigger-gating 軸では緩めない。
- 手続きの位置: 軸オンボーディング (docs/axis-onboarding.md) の段階 A 出口 (人間承認 = 裁定控え 項 3) → 本 wave = 段階 B (軸定義シート + 3 レンズ敵対レビュー → 条件付き採用を D で固定)。関数単位 + 複数 hook + 自前状態は §4 の 2 型に収まらない第 3 型なので、§4 表の第 3 列の案も設計に含める (同節が改訂を D41 水準レビューに掛けると定める)。
- 成果物の形: insight `output/insights/2026-09-21/silo-function-synthesis-space/README.md` (依頼の返却物 (1)〜(5) + 軸定義シート + 見送り)、逐語は同 dir `verbatim/`。decisions fragment 1 件、worklog fragment 1 件。
- 分割方針: 段 2 = read-only codex 1 本が設計草稿を file:line 粒度で起草。段 3 = 3 レンズ (codex A: 正しさ・観測者効果・報酬ハック、codex B: 実装接続・表現・見積り、auditor role: 報酬ハック目視の立場) が草稿と本 brief を攻撃。段 4 = 裁定 (実装しないので 4→7→8→9)。段 4 で中心設計を替えたら、替えた版を同じレンズに焦点再レビューさせてから固定する (D1409 の教訓)。docs に数値・見積りを書くので段 7 前に独立 read-only レビュー 1 本を残す。
- 受入・実測環境: 本 wave の計算投入は受入全走だけ (Pegasus、login + 計算ノード dispatch、2 node 時間未満の見込み)。実験・試走は投げない。

## 暫定裁定 (親の provisional、段 3 の攻撃対象)

- (P1) 境界 = 方策と仕組みの分離。LLM が書くのは方策の関数 (abort 後に何をどれだけ待つか、lock 競合時に待つか中断するか) と方策専用の状態 (thread_local / 名前空間 scope の atomic) だけ。仕組み (CAS・lock bit・unlock・absent 検査・validation・tid 生成・writePhase・trace 発行・同じ txn の再試行) は人間が一度入れる骨格が持つ。
- (P2) validation と lock の仕組みは v1 で開かない。v1 は構成上直列化可能性を壊せない空間とし、verifier は毎回回す (規律 3) が、役割は「骨格・封じ込めの破れの検出」と無効候補の分類になる。「LLM が壊した候補を verifier が捕まえた数」は v1 では原理的に 0 で、その指標は仕組みを開く後続版の課題 (前提 = 差分分析 P0 の検出力測定) と明記する。
- (P3) lock 競合時の応答 (lockWriteSet の `expected.lock` 枝) は v1 に含める。方策は「待って再試行 / 中断」を返すだけで、CAS・記録・unlock は骨格。待ちの上限は骨格が持つ (deadlock は上限で abort に落ちる)。
- (P4) 置き場 = `cc/silo/transaction.cc` の名前空間 scope の EVOLVE-BLOCK 1 領域 (既に EVOLVE_BLOCK_SOURCES / ALLOWLIST 内、新 file・新 include 不要)。領域を CC ヘッダの include より前に置き、CC の大域 (Masstrees・epoch・CCBenchResults・FLAGS 等) が定義点で未宣言になるようにして、名前解決で封じ込める。`extern` / `asm` は字句で拒否。呼び出し側 (abort() と lockWriteSet) は marker の外の骨格。軸 macro 既定 0 で領域と呼び出し骨格が消え stock と preprocess 一致 (inert)。
- (P5) 観測 = 骨格が埋める const の文脈構造体 (abort 要因、この txn の再試行回数、read/write set の大きさ、競合位置、同じ lock での試行回数、時刻と clocks_per_us)。`result_` (計測カウンタ)・`thid_`・`quit_`・他の FLAGS・epoch・生 Tidword・tuple pointer / key は渡さない。方策が自前状態で事象列から率を推定することは許す (stock の Cicada 適応も run の commit 数を読む)。
- (P6) 探索の共通表現 = 「領域の C++ 本文」。identity は既存 source_digest (preprocess 後 hash) なので生成器を問わず同じ本文は同じ候補。random / sweep / BO は閉じた型付き方策 IR (有限・停止保証つき、C++ へ決定的に描画) の上で動き、IR は LLM 自由記述の部分集合。進化は IR 上 (非 LLM) と C++ 本文上 (LLM) の 2 種。IR の機械 sweep がオンボーディング段階 D (偵察) を兼ね、段階 E (LLM ループ) より先に走る。
- (P7) 接続 = 兄弟 driver `p3_s4_loop_policy.py` (quarantine / pipeline.evaluate / WAL / critic digest を再利用)、新 marker 用の検疫分岐、tool-less の coder role 新設 (`.claude/agents/` 変更はユーザー明示承認が要る)、auditor 機械 gate (コード片軸の既定)。
- (P8) 見積り (投入しない) の出所 = B-5 試走の固有費 217〜509 s / 候補 (中央値 498 s、write-heavy 1M/48/3 s/5 rep)、LLM 1 巡 10〜13 分 (t2797 insight §6.3)。

## 実アンカー表 (段 2 起草子へ渡す)

| 面 | アンカー |
|---|---|
| 現行 hole (backoff) | `patches/silo-backoff-fixed.patch` (backoff.hh の `backoff()` 内 1 文) |
| 現行 hole (trigger) | `patches/silo-backoff-trigger-gating-variant.patch` (transaction.cc の abort 要因記録と `abort()` の gate) |
| Silo の abort / retry | `external/ccbench/cc/silo/transaction.cc` の `abort()` / `lockWriteSet()` / `validationPhase()` / `writePhase()`、`external/ccbench/include/ycsb.hh` の `RETRY` ループ |
| 編集面・identity | `orchestrator/campaign/source_digest.py` の `EVOLVE_BLOCK_SOURCES` / `ALLOWLIST` / `assert_includes_match_head` / `assert_trace_diff_matches_head` |
| 検疫 | `orchestrator/campaign/p3_s4_loop.py` の `render_hole` / `quarantine`、`diff_quarantine.py`、`coder_effect_gate.py`、`backoff_hole_grammar.py` |
| build admission | `orchestrator/campaign/build_admission.py` (D127) |
| 正しさ workload | `orchestrator/campaign/pipeline.py` の `CorrectnessWorkload` / `S2_FLAGS` |
| 手続き | `docs/axis-onboarding.md` §2〜§5、`docs/phase3.md`「EVOLVE-BLOCK 機構」、D22/D23/D38/D41/D48/D127/D298/D1409/D1441/D2158 |
| 費用 | `output/insights/2026-09-20/t2797-b5-contrast/README.md` §6.3 / §8.2 |
