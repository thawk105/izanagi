---
schema: izanagi-spool-v1
ledger: decisions
authored: 2026-08-26
wave: dev-wave-t1675-official-floor-path
seq: 2
---

## {{D:s8-official-approval-nonce}}. §8 承認束縛は D461 型 nonce 束縛を official 用に別系統で流用する

**決定 (ユーザー裁定):** 床値 official 走行を core が無条件拒否している理由である
「§8 (承認束縛方式) 未裁定」を、**D461 と同型の submission nonce 束縛**で解く。

- official 専用の zero-arity 引数と nonce env を、pilot 用とは**別系統**で追加する。
- 投入器が実行時に生成する submission nonce へ承認を束ね、job script が exact 一致を
  確かめたときだけ driver へ承認を 1 個 append する。不一致 (空文字を含む) は build と
  driver より前に fail-closed で止める。
- `tools/pegasus/floor_campaign.sh` は固定 official argv へ変更する。**mode の受け口は作らない**
  (D323 は不変)。job-result・失敗文言・guard・無条件拒否テスト・手順書を同じ変更単位で直す。
- submission receipt schema、admission の claim key 6 項目、refreeze 不適格 seam の 18 名集合、
  `_derive_refreeze_eligibility` の判定式は**変更しない**。

**この決定が保証すること**は「標準投入経路で、その新しい source commit と script blob を明示承認して
起動した」までである。次は保証しない — 承認者が人間であること (D356)、raw `qsub` や
Python API 直接呼出しを含む全経路、ユーザーが §8 変更束の内容を理解したこと、
役割横断の生涯観測数、staged 運搬の意味、床値の科学的妥当性。

**理由:**

- D461 が pilot で同型の問題を既に解いており、source commit・script blob・PBS job の照合が
  そのまま再利用できる。新しい artifact も schema も増えない。
- D323 が要求する「別の source commit と script blob hash での再投入」と最も狭く両立する。
  投入器と job 側が新しい source identity を照合するので、旧 pilot job を official として
  再解釈できないことが機械的に保たれる。
- 承認 bool は測定 seam ではないので 18 名集合へ入れない。pilot 承認と同様、
  seam 分類の対象外である control 引数として扱う。

**却下した選択肢:**

- **§8 実行計画 artifact と nonce を二重に束縛する** — 役割・cell・運搬まで承認対象を明示できるが、
  新しい artifact と schema を増やす。§8 の再凍結文書自身を明示的に書けば足りる範囲であり、
  機構を増やす筋ではない。
- **外部署名された承認 capsule** — 外部 trust root を要求する。D356 が人間性の保証を既に
  諦めている以上、対価に見合わない。
- **固定 official wrapper が承認を無条件 append する** — 承認 gate が恒真になり、
  未承認の投入で一回性 key を焼く。
- **core の無条件拒否を消して CLI 拒否だけ残す** — private core 直接呼出しが bypass になる。逆も同じ。
- **receipt へ `user_approved=true` を足す** — D356 が却下済み。
- **`result.json` の `approved` や `eligible_for_refreeze` を信頼根にする** — producer の
  自己申告であり D488 に反する。
- **承認検証を claim 予約より後へ置く** — 壊れた承認輸送で claim を create-only 消費しうる。
- **scheduler の hold/release だけを承認とする** — release 主体・source identity・nonce・
  実 driver argv との exact 照合が無く、標準経路外の不可視な bypass になる。
