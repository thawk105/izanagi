---
schema: izanagi-spool-v1
ledger: decisions
authored: 2026-09-20
wave: worktree-dev-wave-b8-longrun-verify-prereg
seq: 2
---

## {{D:b8-longrun-verify-prereg-v1}}. B-8 の事前登録 v1 を別 file に作り、対象の 2 案と推奨・「種」・「長時間」・判定規則を結果を見る前に固定する — 発効・試走・本走は認可しない

**決定:** 論文ストーリー 2026-09-20 §8 の B-8 (種を変えた長時間実行による最終候補の検証、未取得) を取得する
ための事前登録 v1 を `docs/b8-final-candidate-longrun-verify-preregistration.md` (未発効、台帳 ID 未起票) として
新設した。B-5 の事前登録 (D2158) と同型の別 file で、`docs/phase3-main-experiment.md` と paper-story は編集しない。
設計の骨子:

- **対象は 2 案を並記し、択一は発効時に D 番号で記録する。** 案 A (推奨) = S-1 の最終候補 = 系側 gate 構成
  g_rl (balanced / read-heavy) / g_rt (write-heavy)、gate 述語は `output/s1-freeze/known_axes_freeze.json` の逐語、
  1 対象 = 24 verify。案 B = 採用静的 backoff 2 genome (fixed-5 / fixed-10、D2160 の候補)、48 verify。推奨の理由は
  (1) 論文ストーリーの仕分けが「対象 ≠ S-1 最終候補」を B-8 未取得の理由に数えるので案 B では B-8 にならない、
  (2) S-1b の variant は独立反復 × 長 extime の検証を一度も受けていない (S-1 直接比較 report が「独立な検証相を
  持たない」と明記)、(3) 案 B は D2160 で 30 verify / 候補 (3 s) を持つ。案 B を選ぶ正当条件 = 現行 pin で案 A の
  build・identity が成立しない、またはユーザーが B-8 の「最終候補」を再定義する。
- **「種を変えた」= S-1 事前登録 層 2 の登録定義** (各反復が新 process で自己シード。CCBench の `Xoroshiro128Plus::init()`
  は `std::random_device` の 32 bit 値 1 つから s[0]・s[1] を作り、`YcsbWorkload` は worker thread ごとに構築される。
  seed の CLI flag は無く値は出力に出ない)。記録は rep-id・PID・開始時刻・argv・node・binary sha・identity・trace 規模。
  seed 注入の実装は前提条件にしない (D16 の別変更単位、identity が候補と別 bytes になる)。
- **「長時間」= 1 走の extime が開発相・D2160 の 3 s より長いこと (≥ 6 s)。** 値は校正 {6, 10} s 昇順で決め、適格 =
  完走 ∧ serializable ∧ certified ∧ anomaly 0 ∧ identity 一致 ∧ verifier wall ≤ 1800 s、未完走は `indeterminate`、
  3 workload の共通部分の最大値、空なら「候補なし」で本走を投入せず **3 s へ丸めない**。系列長 (反復数) での代替、
  verifier 容量改善を前提条件にした 10 s 固定、上限撤廃は採らない。現行 verifier では 6 s が見込み (D2160 の校正で
  6 s は 3 workload とも完走、10 s は balanced SIGKILL・write-heavy hard timeout)。
- **判定は D2160 項 3・5 を継承**: 判定集合 = 本走 ∪ 校正完走 verdict、失格 (anomaly ≥ 1、再走なし) / pass (24 枠
  全完走・certified・anomaly 0・identity 一致、判定集合 anomaly 0) / 未確定。本走の未完走は同一 trace の再検証 1 回。
  anomaly は witness cycle・依存の種類・trx 識別子を逐語で insight に残す (規律 3)。失格時は S-1b (案 A) または
  A-2 / T-1998 / A-6 (案 B) の記述へ限定を**追記**し、既存記録の bytes は変えない (規律 7)。
- **予算** = 本走 24 verify の dispatch Elapse 和 ≤ 4 h / 対象 (校正は別欄)。見込みが超えれば 1 段下げ、6 s でも超えれば
  投入しない。案 B・6 s・1 候補の算術は ≈ 13,000 s (3.6 h)、trace 保全は ≈ 37 GB / 対象 (zstd)。
- **統計文は反例を作ってから書いた。** 1−εⁿ、「長さ 2 倍 = 露出 2 倍」、「累計 72 s = 72 s の走」、「自己シードは
  全部異なる」の 4 文は反例が作れたので書かず、条件・仮定として登録した。
- **主張しないこと**: 性能値 (規律 1)、1−εⁿ、「serializable が示された」、S-1 (iv 付属) の充足、既存 certified の昇格、
  長さ・反復の効能、他環境への転移。「B-8 を取得した」と書けるのは、対象・種・長時間の各定義が論文ストーリーの
  仕分けを満たすことをユーザーが発効時に確認した場合だけ。
- **既存機構の照合**: verifier は 6 s で成立しうる。D2160 の runner (Codex author、repo 外) は fixed 2 genome 専用で
  **改版が要る**。案 A の現行 pin での厳密適用・trace-enabled build・identity 導出は**未実測**で発効前の試走が要る
  (template patch の `patch -F0 --dry-run` は transaction.cc の全 hunk が当たる)。本 wave では実装しない。

**理由:**
- 論文ストーリーの仕分けが B-8 未取得の 3 理由 (対象・種・長さ) を挙げた以上、3 要件の操作的定義を結果を見る前に
  文書で固定しないと、検証相を再走しても「取得」と書けない状態が続く。
- 「種」は S-1 の登録定義を持つのに対し、仕分け (2) はそれより厳しい読みをしている。本書で定義を明示し、認めるか
  どうかを発効時の確認事項にすることで、結果を見た後に定義を動かす余地を無くす。
- 「長時間」は S-1 自身が 07-16 校正で 3 s に確定した値でもある。B-8 の別登録として「3 s より長い」を要求し、
  丸めを禁じることで、verifier 容量が足りないときに 3 s を「長時間」と言い換える経路を閉じる。
- 校正で extime を決める形にすれば、進行中の verifier 容量改善 (別 wave) を前提条件にせずに、着地していれば 10 s を
  自動的に採れる。

**却下した選択肢:**
- 対象を 1 案に固定する — 論文ストーリーの仕分けと案 A の build 未実測の両方を発効前に解く必要があり、
  どちらに転ぶかで対象が変わる。択と推奨を登録し、発効時に択一を D で記録する方が正直である。
- seed 注入を前提条件にする — 上記のとおり別変更単位で、候補の identity を変える。
- extime 3 s のまま反復数を増やす — 1 走内でだけ進む状態を捕まえず、仕分け (3) を満たさない。
- verifier wall の上限を撤廃する — write-heavy 10 s は 3600 s でも終わらず、正しさの情報を増やさない。
- `docs/phase3-main-experiment.md` へ追記する — 凍結 source で追記できない (D2160 項 6) うえ、D1012 の作法にも反する。

**研究状態への影響:** certified 選択・レポート・台帳の値は変えない。変わるのは、B-8 を取得するための規則が
発効前の文書として 1 本存在し、発効時の確認事項 7 点が明示されたことである。
