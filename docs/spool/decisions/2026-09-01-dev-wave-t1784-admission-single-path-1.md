---
schema: izanagi-spool-v1
ledger: decisions
authored: 2026-09-01
wave: dev-wave-t1784-admission-single-path
seq: 1
---

## {{D:admission-required-path-per-driver}}. 受理記録の正となる置き場所は driver ごとの要求 path 1 本とする

**決定:** D1050 が命じた「正となる置き場所を 1 本に固定する」を、**`driver_kind` の全域写像として
1 本**と読んで実装する。検証器 `verify_b4_admission_record` は、解決後の repository-relative path が
その driver に対応する 3 literal のいずれかと一致しない record を、内容によらず拒否する。
関門は `driver_kind` の閉集合検査より後、record bytes の読み込み・HEAD blob 照合・schema 検査・
文書 binding 検査より**前**に置く。

**理由:**

- 事前登録 §10 は逐語で「その版へ束縛した admission record を **driver ごとに発行する**」と定める。
- record schema は projection 期待値を単一値として持ち、検証器は driver 別の live 値と照合する。
  全 driver 共通の 1 file にすると schema 昇格を伴うが、D998 は「schema 昇格は gate を 1 bit も
  強くしない」として同種の案を既に却下している。
- D1050 の趣旨は本数ではなく**選択可能性**を閉じることである。path が `driver_kind` の全域関数なら、
  運用者に選ぶ余地は無い。
- 関門を後段へ置くと、非要求 path が「HEAD にない」「schema 違反」など内容側の理由で先に落ち、
  置き場所関門の失敗署名が不安定になる。前段へ置くと、repo 外・欠落・symlink・非 regular の
  既存拒否署名を壊す。

**却下した選択肢:**

- 全 driver で単一 file とし record に 3 値を持たせる — schema 昇格を要し、1 driver の閉包変更で
  共有 record の再発行が必要になる。
- 呼び手や CLI 側にも独立の関門を置く — 3 呼び手すべてが中央検証器へ収束しており、二重化は
  受理集合を 1 bit も変えない。

## {{D:admission-required-path-naming-not-normative}}. 要求 path の定数は事前登録の正本を名乗らない

**決定:** 上記の関門に使う定数名・例外文言・テスト名から `canonical` と `contract` を外し、
`_REQUIRED_ADMISSION_RECORD_REPOSITORY_PATH_BY_DRIVER` と
`record repository path is not the path required for driver_kind` とする。
module docstring には、この関門が**証明しないこと**を逐語で列挙する — 要求 path にある record の
内容が正しいとは限らないこと、**この module の mapping が事前登録された正本であるとは限らないこと**、
driver をまたいで単一 path であるとは限らないこと、mapping や record を書き換える commit を
防がないこと、Git の外で先に結果を知る経路を塞がないこと。

**理由:**

- 事前登録文書は record の置き場所を定めていない。実装が literal path を先に固定したうえで
  `canonical` (正本) と名乗ると、後から文書側がその path に合わせる義務を負い、
  D1000 が警戒する「実装が事前登録の内容を支配する」構造と同型になる。
- 名前を「検証器がこの driver_kind に要求する path」に留めれば、実装は自分が要求する条件を
  述べるだけで、事前登録の内容を先取りしない。文書側が別の path を定めたときは実装が従う。
- D1000 は「検査していないことを検査したと読める名前」を規律 2 違反と同等に扱う。
  この規律を、検査範囲だけでなく**規範の出所**にも適用した。

**却下した選択肢:**

- 実装を止め、path 名を人間が文書または裁定で先に固定するまで待つ — D1050 は既にユーザー裁定で
  決着しており、残るのは実装形の選択である。命名と docstring で非正本性を明示すれば、
  実装が文書を支配する構造は生じない。
- 名前をそのままにして docstring だけで断る — 名前が主張を越えたまま残る。
