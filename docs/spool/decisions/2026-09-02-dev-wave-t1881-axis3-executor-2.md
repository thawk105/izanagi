---
schema: izanagi-spool-v1
ledger: decisions
authored: 2026-09-02
wave: dev-wave-t1881-axis3-executor
seq: 2
---

## {{D:seal-closure-scope}}. 登録封印の受理条件は列挙した closure の HEAD blob 一致に限る

**決定:** 文献検索の registration seal が受理条件に使ってよいのは、**封印対象として事前に列挙した
file の bytes だけ**である。具体的には実行器 source、schema、凍結入力と、catalog・parser fixture・
argv / phase contract の digest である。次の 2 つを受理条件に入れてはならない。

1. **repository 全体の HEAD 一致。** 封印の記録を commit すれば HEAD は必ず動く。HEAD 全体を
   条件にすると、封印が発行と同時に再利用不能になる。受理条件は列挙した各 file について
   作業ツリーの bytes と `HEAD:<path>` の blob が一致することとする。
2. **実行環境の digest。** python の実行 file、標準ライブラリ、site distribution の tree、
   loaded module 群を受理条件に入れると、無関係な環境更新だけで封印が腐り後続作業が止まる。
   interpreter の版と依存 package の版は**来歴として記録してよいが、一致を要求しない。**

**封印が排除するのは、列挙した closure の封印後 drift だけである。** それ以上を保証しない。
同一 UID による一括改変、remote attestation、CLI を起動した主体の人間性は保証範囲外であり、
成果物本文でその強度を超える主張をしない。

**理由:**

- 実測。封印対象 closure を commit した後に `register` を実走すると通るが、その記録を commit した
  時点で HEAD が動くため、HEAD 全体一致を条件にすると同じ封印を後続が使えない。凍結記録は
  land するために commit するので、この構造では封印が必ず 1 度で死ぬ。
- 実行環境まで焼き込む束縛は「登録と後続検証が同じ環境で行われた」ことしか言わず、第三者への
  独立保証にならない。内訳を封印に残さないため、環境が変わった後の第三者は再構成も原因特定も
  できない。守っている対象を 1 文で言えない束縛は受理 gate に置かない。
- 自分が生成した固定長 list の要素数を自分で数える検査 (`len(entries) != 7`) は恒真であり、
  closure の完全性を証明しない。保証として数えない。
- izanagi の既存方針と整合する。守るべきは測定の意味であって bytes ではなく、来歴は粗くてよい。
  **ただし「束縛を捨ててよい」という意味ではない** — 封印対象として列挙した closure の bytes 一致は
  受理条件として残す。狭めたのは対象範囲であって、束縛の強度ではない。

**却下した選択肢:**

- **HEAD 全体一致を残したまま、封印を毎回作り直す運用にする** — 記録を land するたびに封印が
  無効になるので、凍結物としての意味を失う。後続は必ず再登録から始めることになる。
- **環境 digest を warning に落として記録だけ残す** — 受理集合を変えない冗長 gate になり、
  「通った」ことを根拠にできない。記録として持つなら受理条件から明確に外す。
- **封印そのものを廃止する** — 実行器・schema・凍結入力の drift を検出する層が無くなる。
  封印は列挙した closure の drift を実際に排除しており、変異検査でも発火が確認できている。
