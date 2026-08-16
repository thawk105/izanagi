---
schema: izanagi-spool-v1
ledger: decisions
authored: 2026-08-16
wave: dev-wave-t419-seam-checknet
seq: 2
---

## {{D:activation-admission-artifact-faces}}. 世代を有効にする根拠を較正 artifact の 4 面へ広げ、方式名だけを発行時に限る

**決定:** 環境契約の後継判定を 2 層に分ける。構造判定 (`is_valid_successor` = 変わってよいのは
calibration の path と sha だけ) はそのまま残し、その後段に較正 artifact を読む admission を置く。
admission が要求するのは次の 4 面である。

1. **自己整合** — 記録された effective clock の全標本が、同じ列の中央値から `tolerance_pct` で
   作った帯に入ること。
2. **content-addressed path** — `calibration_ref.path` が
   `output/env/<env_tag>/calibration/registered/calibration-<sha256 先頭 16 桁>.json` であること。
3. **acquisition receipt の内部束縛** — 既存の型付き admission (qsub/PBS ID の一致、
   `pinned_clean`、`ht_off`、known-values、`quality.status`) が成立すること。
4. **取得方式名の実体一致** — `effective_clock.method` が現行 probe 定数と exact 一致すること。

**1〜3 は全遷移に適用し、4 は発行経路だけに適用する。** さらに 4 は、その遷移の後継が
**既存 chain でまだ一度も active になっていない場合だけ**に効かせる。

**理由:**

- 従来の根拠は `quality.status == accepted` という自己申告 1 語だけだった。1〜3 は同じ artifact の
  bytes から機械的に再計算でき、根拠を自己申告から独立再導出へ移せる。
- **4 を全遷移へ適用してはならない。** activation chain は読み込みのたびに過去の全遷移へ
  後継判定を再適用する。方式名は可変な現行 probe 定数との比較なので、probe を改良した時点で
  既に有効な過去の遷移が落ち、authority 全体が読めなくなる。これは D329 が取り除いた
  「probe の改良で過去の登録が構造的に通らなくなる」型そのものである。
  1〜3 は artifact の bytes だけから決まるため、いつ再生しても結果が変わらない。
- **4 を発行経路の全遷移へ適用してもいけない。** 発行 tool は既存記録を含む chain 全体を検証するため、
  記録が 2 本以上になった後に probe を改良すると新しい記録を一切発行できなくなる。
  「これから active にする世代を狭める」という要求は、後継が未 ever-active の場合に限る形で満たす。
- 実測 (本 wave): 登録済み第 2 世代の method は現行 probe 定数と一致し、第 1 世代は一致しない。
  正例と負例が実在の凍結 bytes で揃う。第 1 世代は自己整合にも失敗するため、
  方式名だけの単独負例には使わず、面ごとに 1 面だけを壊した合成 successor を使う。
- 拒否は面の名前 (`self-consistency` / `clock-method` / `content-address` /
  `acquisition-receipt`) を持つ例外で送出し、上位の `ActivationRecordError` に原因として連鎖させる。
  bool へ潰すと、止まった理由が運用者に届かない。

**却下した選択肢:**

- **歴史 resolver へ自己整合 gate を置く** — 実測で、この resolver は歴史成果物専用ではなく
  live campaign の COMMIT 監査・床値 admission・reflux closure を含む 6 consumer に載っている。
  唯一の自己不整合 artifact は現に active な第 1 世代なので、gate を置けば今日動いている経路が
  止まり、例外を置けば規律 2 を緩めた恒久例外になる。どちらも採らず、
  「新たに ever-active になる較正を止める」という前向きの形だけを実装した。
- **登録済み全世代を production の authority load で走査する** — 未 active 世代の異常だけで
  今日の起動が止まり、受理集合が変わる。走査の拡張は検査網 (テスト層) に置いた。
- **実行時 attestation の method 比較を実体一致へ変える** — D329 の反転であり、
  pegasus の全 attestation が即座に落ちる。別途ユーザー裁定へ返した。
- **共有 `_verify_entry_calibration` を admission から呼ぶ** — 同じ較正を 2 回読んで parse するため、
  acquisition receipt 面の拒否理由がもう一方の load に隠され、単一理由性が壊れる。
  admission 側で 1 回だけ読む形にした。共有関数自体は変更していない。

## {{D:floor-protocol-current-resolver}}. 床値 protocol の path を index authority から解決し、caller に選ばせない

**決定:** `certified_writer_admission` が持っていた床値 protocol の literal path を削除し、
既存の protocol index から**現行 env 契約の contract hash に一致する record を exact 1 件**返す
resolver 経由にする。resolver の引数は repository root だけで、path・contract hash・ccbench pin・
env tag を caller に渡させない。resolver は record (bytes と sha を持つ) を返し、admission は
**再読した bytes の SHA-256 を record と再照合してから**現行契約との検証へ進む。

**理由:**

- 呼び手が path を選べる形にすると、committed で safe な path であっても
  「未承認の別 protocol を admission の対象として選べる」受理拡大になる。
  引数を root だけにすれば、その面は構造的に作られない。
- **選択条件に ccbench pin を入れてはならない。** 実測: index の唯一の record の pin は
  `d706650c…` で、HEAD の gitlink `511c9538…` と一致しない。pin を条件に入れると今日 0 件になり、
  床値の受理経路が壊れる。
- index を走査した後に live filesystem から無照合で読み直す形は、走査と再読の間の差し替えを
  束縛しない。record が持つ sha との再照合でこれを閉じた。

**却下した選択肢:**

- **receipt に `protocol_path` と hash の field を足す** — 提出側が検証対象を選ぶ面を作る。
- **resolver に複数候補の拒否分岐を足して検出力として数える** — index が同一 contract hash の
  2 件目を上流で既に拒否しており、production では到達不能な等価変異になる。
  防御的に閉じるだけとし、テストと変異登録には数えない。
- **床値 path を持つ他 module と shell wrapper も同時に配線し直す** — 実投入経路の全層に及ぶため
  本 wave の scope を超える。literal が resolver の結果と一致することを固定する検査だけを置き、
  配線そのものは裁定パッケージへ返した。
