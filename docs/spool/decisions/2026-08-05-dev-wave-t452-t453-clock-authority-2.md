---
schema: izanagi-spool-v1
ledger: decisions
authored: 2026-08-05
wave: dev-wave-t452-t453-clock-authority
seq: 2
---

## {{D:effective-clock-policy-authority}}. 実効クロック許容幅は独立 leaf module の単一定数を唯一の権威にする

**決定:** `attestation_profile.effective_clock.tolerance_pct` の権威を
`orchestrator/calibrator/effective_clock_policy.py` の
`EFFECTIVE_CLOCK_TOLERANCE_PCT: Final[float] = 2.0` ただ 1 つに置く。env 別の表・setter・fallback・
環境変数参照を持たせない。参照者は producer・loader・issuer・canonical consumer・取得時 self gate・
registry 不変条件・silo の 7 者で、いずれも module-qualified で参照し literal を直書きしない。
issuer の比較計算は独立実装のまま残し、共有するのは数値の権威だけとする (D155 決定 2 の相互裏取りを壊さない)。

観測側 (probe) は tolerance を**型として持たない**。`EffectiveClockProfile` は expected 専用として残し、
probe は `samples_mhz` / `method` / `governor` の 3 field だけを持つ observed 専用型を返す。
出力 schema は `pegasus-probe-output/v2` へ上げ、v1 は「clock key がちょうど 4 個かつ sentinel が
厳密に float `100.0`」の legacy parser で射影して履歴 replay を保つ。hash projection の版は
**parser の戻り値が持つ source schema から導出**し、呼出側が選べる自由引数にしない。

expected schema の上限は `<100.0` へ狭める。ただし **policy との完全一致は schema の責務にしない** —
旧 policy の artifact を履歴として parse できる余地を残し、完全一致は各 trust boundary が担う。

**理由:**
- 値域を狭めるだけでは publish 値を人が選べる構造が残る。`tol=100` は帯を `[0, 2*median]` にし、
  正の標本しか schema を通らないため実質恒真だった。恒真化は値域ではなく**権威の一元化と
  観測側から tolerance を構造的に取り除くこと**で塞ぐ。
- 「policy を持たない」を sentinel 数値でなく型で表せば、sentinel が expected 側へ漏れる経路が
  そもそも存在しなくなる。
- schema へ完全一致を入れると履歴 artifact が parse 不能になり、過去の試行台帳を読めなくなる。
  重複防壁 (loader / issuer / consumer / self gate) の側で担保するほうが、履歴の可読性と
  current admission の厳格さを両立できる。
- 実装順は **observed 型分離 → policy authority → trust closure** でなければならない。
  上限を先に狭めると probe の sentinel `100.0` がその瞬間に schema 違反になり、中間状態が緑にならない。

**却下した選択肢:**
- `env_contract.REGISTRY` の env_tag 別 field — env 追加担当者が特定環境だけ広げられ、
  同じ述語の意味が環境ごとに変わる。
- `CalibrationRef` への field 追加 — pin 更新者が policy も同時に書き換えられ、artifact 内の値と
  二重正本になる。
- artifact 内の `tolerance_pct` 自身を権威とする — 検査対象が自分の受理幅を宣言する自己署名構造で、
  これが元の欠陥そのものである。
- 環境変数 / shell / JSON 設定 — 投入 script・scheduler export・job script のいずれかが差し替えられる。
- CLI option を残して policy 一致値のみ受理する案 — 権威と誤認される入力面が残る。
- observed を共有型のまま `Optional` にする案・sentinel を明示化する案 — どちらも
  「policy を持たない」が構造的事実にならず、field を戻す変異を型で殺せない。

**保証しない範囲:** 固定するのは current admission における tolerance 値までである。
policy `2.0` かつ self-pass な JSON を合成すれば、git 直接追加・attempt 複製・pin だけの更新・
CLI 以外の producer から依然として登録できる。producer provenance の束縛
(content-addressed path の強制、publish receipt と policy source の束縛) は別の防壁として独立に設計する。
