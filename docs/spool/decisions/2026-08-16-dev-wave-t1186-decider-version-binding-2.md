---
schema: izanagi-spool-v1
ledger: decisions
authored: 2026-08-16
wave: dev-wave-t1186-decider-version-binding
seq: 2
---

## {{D:s8c-decider-version-binding}}. 8c 事前登録は判定器の版を凍結記録へ 1 個記録し、発効判定が一致を要求する

**決定:** 段 8c の条件契約凍結は、判定器 (`s8c_preregistration.py`)・評価器
(`s8c_preregistration_evidence.py`)・射影 (`s8c_generation_projection.py`) の bytes 全体を凍結範囲へ
入れない。代わりに次を行う。

1. 判定器 core が `DECIDER_VERSION` を 1 個宣言し、この 1 定数が 3 者の受理意味を代表する。
   3 者のいずれかで受理集合・拒否理由・射影された判定入力の意味を変える変更は、bytes 差の有無に
   関わらず明示的に bump する。整形など意味不変の変更では bump しない。
2. 凍結記録 schema に `decider_version` を必須 key として持つ v2 を足す。v1 記録は legacy として
   読めるまま残す (履歴上の世代 record は不変であり改変できないため)。新規発行は常に v2 とする。
3. 発効判定は tip 記録の版と走っている `DECIDER_VERSION` の一致を要求する。tip が v1 のときは
   値を比較せず無条件に `decider-version-unbound` として発効させない (schema-first)。
   走っている定数は厳密型 (`str` そのもの) と閉じた形式でのみ受理する。
4. `ActivationReport` に版・一致結果・理由コードを持たせる。報告 digest は dataclass 全体から
   導出されるため、版 X で発行した capability は版 Y では再導出時に digest が一致しない。
5. 判定器・評価器にだけ存在した「走っているコードが判定対象 commit の blob と一致すること」の
   検査を、射影モジュールへも同型に広げる。3 者の同一性検査は
   core → evaluator → projection の順で連続して行い、すべて通ったときだけ評価器を実行する。

**理由:**
- bytes 全体の凍結は、無関係な整形変更でも世代を上げる必要を生み、開発を止める型の検証機構になる。
  防ぎたいのは「気付かずに受理意味が変わること」であり、粗い provenance で足りる既定方針の下では
  版の一致検査で十分である (ユーザー裁定)。
- 記録の改竄は既存の `generation-mutated` (同一 path の blob OID は履歴全体で 1 つ) と
  `supersedes_sha256` 連鎖が塞ぐ。版 field を `protected_sha256` の preimage へ入れると、
  記録自身の field から期待値を作って同じ記録と突き合わせる恒真検査になるため入れない。
- 射影だけを変えた子孫 commit では、同じ世代・同じ版のまま実行の意味が変わりうる。これは凍結範囲を
  広げる話ではなく、判定器・評価器に既に存在する同一性契約が 1 モジュール分だけ欠けていた穴である。

**却下した選択肢:**
- 判定器・評価器・射影の bytes 全体を凍結範囲へ入れる — 上記の理由でユーザーが不採用とした。
- `spurious-revision` (保護 hash 不変の世代追加を赤にする規則) に「版が違えば許す」例外を作る —
  事前登録の正本 doc の保護ブロックが「世代だけを増やす空改訂は機械検査で赤になる」と定めており、
  実装だけが規範を変えることになる。版を記録する世代は、同じ commit で正本 doc の改訂手続きを
  改訂すれば保護 hash が変わり、空改訂ではなくなるため例外を必要としない。
- 版の bump 忘れを機械検出する module 変更 gate を足す — bytes 凍結の再導入であり裁定に反する。
  検出できないことは限界として記録する。

**この決定が保証しないこと:**
- 受理意味を変えたのに `DECIDER_VERSION` を bump しなかった場合は検出しない。版の一致検査は
  「明示的に bump された後に古い世代の記録を使い続けること」を止めるものであり、bump 忘れは
  裁定が受け入れた手動 provenance の範囲に残る。
- 3 者の同一性検査は、検査時点のファイル bytes と対象 commit の blob を比べる。既に import 済みの
  コードを束縛するものではない (判定器・評価器の既存契約と同じ性質であり、本決定が新設した穴ではない)。
