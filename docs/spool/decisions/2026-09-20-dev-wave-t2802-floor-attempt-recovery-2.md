---
schema: izanagi-spool-v1
ledger: decisions
authored: 2026-09-20
wave: dev-wave-t2802-floor-attempt-recovery
seq: 2
---

## {{D:floor-attempt-recovery-per-call-memo}}. floor attempt ledger の回復候補関数は呼び出し内 memo で claim 射影と main ledger の再読を 1 回にし、呼び出しを跨ぐ cache は持たない

**決定:** `s8b_holdout_admission._floor_attempt_recovery_candidate_locked` は、root lock 保持中の 1 呼び出しに閉じた
context (成功済み claim 射影の memo + main ledger 生行列の遅延 slot) を持つ。memo に入るのは marker equality まで通った
claim 射影だけで、hit でも marker の exact shape・schema・role・digest・attempt_id、attempt coverage、constructor、
marker 全体との equality (MUT-A2) は毎回行う。main ledger の生読取は従来の読取位置 (v1 / measurement-generation) に
初めて到達したときだけ行い同一呼び出し内で共有する (eager な先読みはしない)。走査順・filter・canonical filename・
identity 重複・A 行の marker 照合・completed 拒否 (MUT-A6)・error message は不変。既存 signature の 3 関数は context なしの
wrapper として残す。module 変数・class 属性・呼び出しを跨ぐ cache は持たない。

**理由:**
- 候補関数は attempt ごとに 1 回呼ばれ、既存 marker 全件と attempt ledger 全行を claim 文書 + main ledger から完全再導出
  していたため、attempt 数に対し二乗の claim 読取と main ledger 全読が生じていた (T-2766 の profile: 98 attempt で 9,604 回の
  再導出、代表 node 9.9 s 中 9.1 s、受入 48 worker では `test_s8b_floor_campaign.py` が worker 時間 2,368 s / 17,959 s)。
- 受理集合 (受理・拒否・message・発火順序) は「一呼出し中に読取対象・読取結果が安定した root」に対して不変である。
  main ledger と claim の書き手は全て同じ root lock の内側 (H:1909 / 2169 / 3168 / 3797、claim 公開 H:1760 / 2158 / 3786 /
  3171〜3173) なので、lock 保持中の再読は同じ結果を返す。差分 probe (変更前 module を別名 import し同じ root 状態で比較) で
  40 状態すべて一致、M1 形の一時変異 (memo hit で marker の値を信用) では 2 状態で不一致を検出した。
- eager な main 先読みは「target の coverage 不正 + main の末尾 LF 欠落」で最初の例外を変えるため採らない (段 3 相談 A)。
- 呼び出しを跨ぐ cache は失効・lock・受理集合・実測費用の設計を伴う別裁定であり、本 wave の局所修正の scope 外。

**却下した選択肢:**
- 参照実装を test 内に写して比較する — 変更後の共通 helper を両側が呼ぶため独立比較にならない。差分 probe は
  変更前 module の逐語 (job dir) を別名 module として load する wave 時 probe とし、repo の恒久 test は固定 literal で書く。
- A≠marker (H:5296)・target≠canonical_target (H:5304)・marker identity 重複 (H:5276) の削除を変異に含める —
  同 identity は同じ canonical 文書に再導出されるため静的 root では到達不能。production の防御は残し、変異にはしない。
- lock 契約外 (advisory lock を無視する書込み・一過性 I/O) への新 gate や再読 — 既存契約の限界として記録するに留める。

## {{D:floor-recovery-ab-measurement-contract}}. 修正前後の受入 shard 対比較は固定した 2 tree の隣接対で測り、D2068 の同一 tree 条件の充足や有意差は主張しない

**決定:** production 側の性能改善の効果は、A = 着手時 local main の clean worktree、B = 実装 commit だけを含む
wave worktree (記録 commit は測定後) から `IZANAGI_ACCEPTANCE_SHARDS=3 python3 tools/run_tests.py` を直接投入 (待ち手・lease・
merge なし) した隣接対 (A,B / B,A / A,B) 3 組で測る。一次指標は測定前に凍結した nodeid 完全集合 (`S_all`) の worker 秒合計
`F` の対差、判定は「3 対とも ΔF > 0 かつ中央値 ≥ 200 s」の実用閾値。両 tree の bytecode 条件は計算ノードの collect-only 1 走で
対称にし証跡を残す。無効走・無効対の規則、赤の分類 (infra / impl / unclassified)、有効 3 対での固定終了、12 走上限を
launcher・系列・集計器で強制する。

**理由:**
- T-2766 (D2164) の同一 SHA 型は env で条件を切り替える設計だった。code の変更は同一 SHA にできないため、条件別に SHA を
  固定した 2 tree の比較にする。これは D2068 の「同一 tree 内で方式を交互に測った対比較」を満たさない (path・pyc・page cache の
  差は残る) ので、採用判断の射程として明記する。
- 200 s はノイズから導いた閾値でなく実用上求める削減量。T-2766 の同一 code の隣接対でも floor の対差は 22 / −211 / 60 s と
  ±200 s 級に振れるため、有意差は主張しない。
- 一次指標の事後の部分集合選別は不可。補助 (`S_mid`、nodeid 対差の分布、`W_max`、`W_0`) は測定前に凍結した定義だけ。

**却下した選択肢:**
- 待ち手経由の実受入で測る — claim 直後の main 取り込みで tip が変わる (D2164)。
- 単発の前後比較や 12w 単独走の秒数からの換算 — 走間ノイズと同程度の効果量で、条件も違う (D2068、D2148 項 6・7)。
