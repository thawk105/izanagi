---
schema: izanagi-spool-v1
ledger: decisions
authored: 2026-09-20
wave: dev-wave-t2807-b8-prerun
seq: 2
---

## {{D:t2807-b8-prerun-runner-and-bundle}}. B-8 の runner は事前登録 v1 の規則を機械適用する v5 とし、期待 identity は発効束 JSON から読む — 案 A の試走で identity を導出し、発効 commit と本走認可はユーザー再提示に委ねる

**決定 (2026-09-20 計算ノード試走に基づく親裁定、D2186 項 1 (6) の認可範囲内):**

1. **runner の形。** D2160 の runner v2 (repo 外) を B-8 の規則へ改版した v5 (2103 行、sha256 `4ff6652a365b952cba4deb23e2ae910ba863dabba4a107503c641c7a36863430`、Codex author + fix 2 巡、
   job dir に保全、repo へ入れない) を、B-8 の校正・本走・再検証・集計に使う runner とする。規則の写像: 校正 {6, 10} s・適格 = verifier wall ≤ 1800.0 s (§4.2)、
   対象の extime = 3 workload の適格集合の共通部分の最大値・空なら候補なし、予算 B(E) ≤ 14400 s と ∩ 内の段下げ (§7)、§6.1 の順序付き 3 値 (失格 → pass → 未確定)、
   §5 の bench 不再生成 (保全済み trace の初回 verifier 再開は維持: `verify --resume` は bench 失敗 = 終端 / verifier 起動済み = skip / 保全済み・未開始 = 復元して初回 verifier / 保全未完了 = 規約不適合の 4 分類)、§8 の既知結果台帳 (判定集合外の別節)、`prerun` サブコマンド (試走 = build と identity のみ)。流用機構 (setup / hydrate / toolchain / 単独性 /
   保全 → verifier / 計時 / 再検証 / 再開) は D2160 のまま。
2. **束縛。** 期待 identity は runner の定数に埋めず、発効束 JSON (追補 file、`--bundle`、schema `b8-effective-bundle/v1`) から読む。runner は規則 file (`--ruling` = 事前登録 v1 本文) と
   追補 file の両 sha256 を全 record に束縛し、`summarize` は許可集合で照合する。`calibrate` / `verify` / `reverify` は build 前後の両観測が期待値と一致しなければ fail-closed、
   `prerun` は期待値照合をせず観測を記録するだけ (build 前後の一致だけ検査)。
3. **解釈で固定した点 (段 6 の敵対レビュー 2 本 + 焦点 2 本で攻撃済み)。** (a) rc=3 の `indeterminate` verdict は完走した verdict であり §6.1 項 1 の「`serializable` でない」→ 失格 (§8 の明文)。
   (b) §5 の「bench 失敗が 1 件でもあれば pass にならない」は校正・本走を問わず、開始して失敗した bench に適用する (打ち切りの `not_run` は失敗でない)。校正で bench 失敗が出た cohort は
   本走を投入しない (pass になれない → §6.4 の新 cohort)。(c) 失格 (§6.1 項 1) は判定集合外 record の混入・ruling / bundle sha 不一致・規約不適合の有無に関わらず先に評価する (規律 2 の向き)。
   混入・不一致は pass を妨げ未確定へ落とすだけ。(d) job 段の失敗 record (identity 不一致・実行失敗) も規約不適合として開示し pass を妨げる。(e) 適格は certified を要求し、
   pass は本走 24 に要求して校正 verdict には要求しない (件数と理由を開示)。(f) 校正は anomaly を理由に残 extime を止めない (§7)。
4. **verifier hard timeout。** 校正 3600 s (§11 が校正の 3600 s timeout を想定)、本走 1800 s (§12 と D2186 項 1 (5) の「上限 1800 s」そのもの)、再検証 3600 s (§6.4、事前登録は値を置かず
   D2160 を継承)。当初案 (本走 3600 s) は親の追加解釈として改めた。判定の結果は変わらない (本走 1800 s で未完走 → 再検証 1 回で同じ verdict)。
5. **試走の結果 (既知結果台帳へ、判定集合外)。** template patch `31316713…` は現行 pin `e9e477ca1b55348ab4530de0b1cf663ce4555290` へ `patchharness.applied` (= `git apply`) で厳密に当たり、
   `p3_s4_loop.quarantine(write=True)` で gate 述語を hole へ書き、trace-enabled build (define 6 個、g++-11 Ubuntu 11.4.0) を計算ノードで通した。identity は
   **g_rl `src_token` = `source_bytes_sha256` = `b0f95b213e6d419cf31473a37c6be3246f9b0fefbd42ead2273d5ab7408a670d`、g_rt `a0219ce0b258e339ac6489cb5b17b3acb4158ce0d6087ca6098d1e408862f833`**
   (build 前後・login 事前照合・runner v3 / v4 / v5 の 6 record で全桁一致)。これを発効束の期待値にする。07-16 校正の g_rl `4608a96e…` (旧 pin) は期待値にせず履歴として併記する (規律 7)。
6. **発効束 draft。** §12 の全項目を insight §7.1 と `verbatim/b8-effective-bundle.draft.json` (sha256 `6063d5d8…`) に揃えた。runner が単独で揃えない項目 (pin と gitlink の一致・raw bytes の保存・
   node 種別 gen_S・保全先 `/work` の空き 81 TB・校正 walltime 03:30:00 の根拠 = 上限式 ≈ 10,340 s と D2160 校正最大 Elapse 4063 S × 3) は親が実測で補い、新しい機械 gate は足さない。
7. **委ねるもの。** 発効 commit (D 番号・日付・承認 commit、発効束 JSON を `effective` に) と本走の投入認可は、insight §7.2 の 1 行をユーザーが承認してから。発効前に校正・本走を始めない。
   論文ストーリー §8 B-8 の仕分け (2) の限定明記も発効時 (D2186 項 1 (2))。

**理由:**
- 期待 identity を runner 定数に埋めると、runner の sha256 自体が発効束の項目なので試走 → 発効で runner を 2 度変える。追補 file へ分けると規則 file (事前登録本文) と値 (発効束) の束縛が独立する (§12 の「規則 file と追補 file を分ける」)。
- 解釈 3 (a)〜(d) はすべて fail-closed の向きで、D2160 の規則 (rc=3 を数えない・bench attempt-2・混入で未確定) を B-8 へ持ち越すと §6.1 / §5 / §8 の明文に反する。author と 2 本のレビューが独立に指摘した。
- hard timeout は事前登録自身の数に揃えることで親の解釈を減らした。判定の結果に影響しないことは再検証 1 回の存在から言える。
- 試走を runner v3・v4・v5 で走らせたのは、fix 2 巡が prepare 経路を変えていないことの実測と、発効束の runner sha256 を最終版に揃えるため (各 36 秒)。

**却下した選択肢:**
- 期待 identity を runner 定数に埋める (D2160 の形) — 上記のとおり runner を 2 度変える。
- 本走 hard timeout 3600 s (校正上限の 2 倍) — 親の追加解釈で、事前登録の「上限 1800 s」と整合しない。
- bench 失敗の attempt-2 (D2160 の規則) — §5 に反する。
- 校正の bench 失敗を pass の障害にしない読み — §5 の文は verify の種別を限定しないので、緩い読みは結果を見る前でも採らない。
- 試走を login の事前照合で代替 — D2186 項 1 (6) は計算ノードでの build を含む試走を認可しており、login 値だけでは build 前後の一致を示せない。
