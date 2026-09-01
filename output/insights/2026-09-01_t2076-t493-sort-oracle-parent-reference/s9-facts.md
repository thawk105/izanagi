# 相談のための実測事実 (親が測ったもの)

## 状況

T-493 の実装は完了し検証も緑だが、受入全走が **本 wave と無関係な既存の赤** で止まっており
land できない。赤の原因は下記の 1 点で、このホストで受入を回す全 wave を同時に止めている。

## 赤の実測

- 受入 attempt: `21 error, 5 failed, 19044 passed, 67 skipped`、rc=70、`claimed_main=24014bdb2`。
- 赤 26 件はすべて `orchestrator/tests/test_codex_reasoning_ab.py`。
- **main 単独で完全に再現する。** 独立 clone を `24014bdb2` (受入が claim したのと同じ main) へ
  checkout して同 file を走らせ、`26 failures = 5 failed + 21 errors` の同じ内訳を得た。
  したがって特定 wave の差分に帰属しない。flake でもない (決定的)。
- 赤の本文は 2 種類だけ。
  - `ValidationError: session 019fac6b-4f74-7a03-aa4d-8a9de22b352c rollout count is 0, expected 1`
  - `FileNotFoundError: /home/SFC/tanab/.codex/sessions/2026/07/29/rollout-2026-07-29T15-49-14-019faca2-...jsonl`
- 同時刻帯に別 wave 3 本 (t2027 / t1909 / t2075) が同じ件数で落ちている。

## 真因

- `tools/codex_reasoning_ab.py:196-208` の `_LEGACY_SESSION_IDS` と `_LEGACY_ROLLOUT_SHA256` が
  **repo 外の実 codex session 5 件** (POS / NEG / author / fix1 / fix2) を ID と rollout の
  SHA-256 で pin している。5 件とも **2026-07-29** のものである。
- テストは `_HISTORICAL_SESSIONS = Path("/home/SFC/tanab/.codex/sessions")` を実 corpus として読む。
- ホストの実状: `~/.codex/sessions/2026/` の下には `08` と `09` しか無い。**7 月分は消えている。**
  codex CLI 側の保持期間による剪定と見られる。
- `orchestrator/tests/test_codex_reasoning_ab.py:788-790` に既に
  `if not _HISTORICAL_SESSIONS.is_dir(): pytest.skip("historical rollout root is unavailable")`
  という guard がある。しかし判定が **根 directory の有無だけ** なので、根が在って中身の
  pin 対象が消えている今回の状態では skip にならず hard red になる。

## 復元可能性 (別セッションが 2026-09-01 に実測済み)

- `~/.codex/` に 7 月分の退避も別 session root も無い (`sessions` は 1 つだけ)。
- repo の `output/insights/2026-07-29_t153e-t15423-review-verbatim/` に在るのは
  **描画済み markdown 14 本だけで、生の `rollout-*.jsonl` を含まない**。
- `dev-wave-jobs/` にも写しは無い。
- **したがって「復元」は選択肢として成立しない。** pin の意味論を変える設計裁定になる。

## 制約

- `orchestrator/tests/flaky_test_holds.py` への hold 登録はできない。D697 の受理条件が
  「同一 tree で緑と赤の両方を観測」を要求するが、本件は決定的な赤である。
  また `DW-O18` は hold 登録に main 既存の F 番号を要求するが、同型の F は台帳に無い
  (F258 は SIGSEGV、F544 は `st_mode mismatch` で署名が違う)。
- 絶対規律 2 により、正しさゲートを緩める方向の変更は採れない。
  「テストを緩めて緑にする」経路は採らない。
- 実装面の変更は Codex `role=author` が書く。

## 親が現時点で持っている案

- **案 A**: 既存の skip guard を「根 directory の有無」から「pin された legacy session が実際に
  解決できるか」へ拡張し、解決できないときだけ skip する。repo が既に選んでいる
  skip-on-unavailable の型をそのまま正確にするもの。正例 (corpus が在るときは skip しない) を
  対で入れる。
- **案 B**: pin を現在入手可能な session へ張り替える。ID と SHA-256 が変わる。
- **案 C**: host 非依存になるよう corpus を repo 内へ持ち込む。ただし 7 月の生 rollout は
  失われているため、歴史的比較の中身そのものは再現できない。
- **案 D**: 何もせず、受入が通らない状態を受け入れる。

## もう 1 つの裁定事項 (T-2076)

同 wave で、D1271 が命じた「sort SWO oracle の基準 snapshot を候補から不可視な親側へ移す
最小実装」は **実装対象が既に存在しない** ことが判明した。T-1574 が D1271 起票日より前に
corpus を read-only arena へ移して閉じている。

生きている穴は「報告された関係行列が、その comparator の真の関係であること」の非保証で、
これは D825 が exact field で明記している。本 wave で 3 案を検討し、独立 2 レンズと親の
再測でいずれも不成立と判定した。

- 観測 fd へ内容 witness を足す — 候補が同じ fd の所有者で出所を作れない。
- broker が trap で引数と戻り値を採取する — trap も trusted callsite も候補と同じ翻訳単位にあり、
  呼出しの出所を証明しない。
- 比較ごとに `fork()` する — 候補文の引数評価が worker 親で起きるうえ、現行 seccomp は
  `clone` / `wait4` を許さず、filter は候補文より前に導入済みで積み増ししかできない。

成立しうるのは受理言語を検証済み IR へ縮め trusted interpreter で評価する案だけで、
これは受理集合と合成エージェントのインタフェースを変える大きな設計変更である。
