---
schema: izanagi-spool-v1
ledger: decisions
authored: 2026-09-02
wave: dev-wave-t2182-k2-arm-liveness
seq: 1
---

## {{D:knowledge-source-existence-at-producer}}. 知識源の実在検証は producer に置き、読み出し時に再検証しないと明記する

**決定:** 知識 manifest の受理判定のうち、closure 内 (`wal.py`) が持つのは manifest digest の
自己整合性と束縛欠落の拒否と identity 形状の検査までとする。Git object の実在と blob bytes の
一致は closure 外の producer が検証し、WAL 読み出し時に再検証しない。この限界を成果物と
台帳に明記する。

**理由:**

- 段 6 の敵対レビューが「実在しない commit から自己整合した provenance を作れば束縛検査が
  受理する」ことを静的 probe で示した。指摘は正しい。
- 閉じるには Git 解決を `wal.py` へ移す必要があり、新しい process 起動点の追加と
  enforcement source closure の所有範囲の変更を伴う。exact 24-path の意味を変える改訂に近い。
- WAL を読む時点で当該 commit が到達可能である保証がない。到達不能 commit の prune は
  repo 全体で自動的に起きる。読み出し時の Git 再解決を必須にすると正当な replay が将来落ちる。
- 規律 7 と D387 が既に「repo 内の挙動検査は、gate と検査を同じ主体が変更できる限り
  意図的な弱体化への完全な防壁ではない。この限界は主張せず明記する」と定めている。
  本件はその適用であって新しい例外ではない。

**却下した選択肢:**

- Git 解決を closure 内へ移す — closure の所有範囲を変え、読み出し時の commit 到達可能性に
  依存する検査を必須にする。効果が未実証のまま制約だけが増える。
- 限界を書かずに「受理判定を closure 内へ置いた」と記録する — 実態と食い違う。

## {{D:knowledge-receipt-classification-closed-set}}. 知識受領証の候補分類は閉集合とし de novo 主張との整合を要求する

**決定:** 受領証の分類欄は D1429 が定めた 3 分類に対応する 3 つの literal だけを受理し、
de novo でない分類に de novo の主張を組み合わせられないようにする。分類と de novo 主張は
generator の固定定数ではなく呼び手が宣言する入力とする。

**理由:**

- 任意の非空文字列を受理する形では、再現・選択と宣言しながら de novo を主張する受領証を作れる。
  D1429 が閉じた受理集合から de novo と軸発見を外すという境界が、成果物側で崩れる。
- 固定定数にすると、literal を含まない source を使った走行や既知結果に条件づけられた派生まで
  同じ分類になり、台帳の分類値が実走と食い違う。

**却下した選択肢:**

- 分類を campaign identity と WAL へ束縛する — identity は入力を束縛するものであって主張を
  束縛するものではない。同じ入力・同じ候補が分類を変えるだけで別 campaign になる。
- 分類の整合を検査しない — 主張境界が成果物側で保たれない。

## {{D:s4-loop-pegasus-port-is-separate}}. 段 4 loop のビルド系を Pegasus へ移植する作業は知識入力経路の実装から分ける

**決定:** 段 4 backoff loop の評価経路を Pegasus で通す作業は、知識水準の入力経路を作る作業とは
別のタスクとする。移植の前提 (専用 env タグ、calibration の取り直し、binding の固定、
provenance の追跡) が未了である事実を記録し、移植せずに `linux-baremetal` を使う選択肢と
併せて諮る。

**理由:**

- 実測で 8 件の阻害要因が順に現れた。1 つ外すと次が出る形であり、これは入力経路の生死確認では
  なく移植である。段 4 loop は `linux-baremetal` 向けに作られている。
- 環境で解けるもの (依存の事前ビルド、third-party の offline 配置、計算ノードでの実行) は
  job script 側で解けたが、condition gate の supply arm は preprocess で止まったままである。
- 移植を続けると、測定の意味を変える変更 (compiler の差し替え、pin の変更) へ踏み込む誘因が働く。
  入力経路の生死確認という当初の目的からも外れる。

**却下した選択肢:**

- 移植を続けて 1 本を通す — 本題の実装でも 1 本の走行でもない作業に予算を移す。
- ビルドを伴わない dry-pass で代替する — compile / identity / correctness gate へ到達せず、
  terminal verdict を得たと誤記する経路を作る。
