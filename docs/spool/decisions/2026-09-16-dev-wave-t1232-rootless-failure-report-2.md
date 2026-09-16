---
schema: izanagi-spool-v1
ledger: decisions
authored: 2026-09-16
wave: dev-wave-t1232-rootless-failure-report
seq: 2
---

## {{D:failure-only-diagnostic-verification}}. failure-only report の独立検証は、成功集合を閉じた形について増やす非 certifying の診断経路で与える

**決定:**
1. standalone verifier `verify_autonomous_trial_files` に、明示 opt-in の非 certifying 診断検証経路を足す。
   発火条件は「flag が真」「campaign output root 未指定」「既存 2 免除 (`fatal_without_cells`、
   `failure_without_campaign`) に当たらない」の積とする。root を渡した呼出しは従来検証をそのまま実行し、
   flag による検査省略を認めない。
2. **この経路は standalone verifier の成功集合を増やす変更であると明示する。** opt-in であることと
   `certifying=false` であることを、受理集合不変の証拠に使わない。
3. 受理形は閉じた厳密一致の述語に限る。導出できない形は受理せず狭める (広げない)。
4. **欠けている束縛は素通りさせず、不在を report 側の事実と突き合わせて証明する。**
   「あれば検査、無ければ素通り」という presence 条件だけの分岐を書かない。
5. 戻り値の receipt は検証範囲の申告であり、署名ではない。root 束縛は `not-verified`、
   cross-binding は `not-established` と申告し、`campaigns/<ID>` 配下という包含関係を主張しない。
6. certifying 受入 `assert_trial_registry_acceptance`、producer、`verify_s8c_cross_binding` 本体、
   `assert_campaign_layer3_chain` 本体は変更しない。

**理由:**
- 対象 report (campaign identity を宣言した admission 失敗 cell を持つ failure-only report) は、
  root を与えても cross-binding が build population 要件で落とす。**受理を 1 つも増やさない案では、
  独立検証できるようにするという依頼を満たせない。** 成功集合が増えること自体が依頼の内容である。
- 規律 2 の射程は certified な結果を守る正しさゲートである。この経路は非 certifying で、
  certifying 受入は不変であり、段 3 で 3 方向からの bypass (admitted cell の流入、registry 受入の迂回、
  既存免除の暗黙拡大) を検査して反証した。
- 依頼が置いた歯止めは「束縛検査の**一律撤去**に広げない」である。閉じた述語・明示 opt-in・既定経路無改変は
  一律撤去に当たらない。
- D1460 は「層 3 の空走は受入限定で閉じ、より強い gate を全 verifier へ広げない」と決めた。
  本決定は standalone verifier に検証経路を足すものであり、D1460 が却下した拡張とは向きが逆で抵触しない。
- 束縛の不在を証明させるのは、救済対象の report が provider 成果物も raw 参照も持たないことがあるためである。
  既存検査をそのまま流用すると救済対象自身を落とし、条件分岐で飛ばすと fail-open になる。

**却下した選択肢:**
- **root 要求だけを外す** — 対象 report は root の有無と無関係に cross-binding で落ちるので効かない。
  また「root を省くと失われるのは path identity 束縛だけ」という前提は誤りだった。
- **従来の成功集合維持を必須として案を戻す** — 依頼を満たさない。
- **既存の role / provider 束縛検査をそのまま流用する** — 救済対象自身を落とす。
- **欠けている束縛を presence 条件で飛ばす** — fail-open になり、規律 2 に反する。
- **診断情報付きの形を受理する** — 生成器を mock せずに正例を作れず、受理を実走で裏取りできない。
- **正式 registered 系列まで回復させる** — publish 前の digest 検査で拒否されており、producer と digest 契約の
  一体改訂になる。依頼の scope 外。
