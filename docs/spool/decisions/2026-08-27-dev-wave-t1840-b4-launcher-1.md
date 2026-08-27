---
schema: izanagi-spool-v1
ledger: decisions
authored: 2026-08-27
wave: dev-wave-t1840-b4-launcher
seq: 1
---

## {{D:b4-certified-sink-chokepoint}}. B-4 の支配点は certified sink の合流点に置く

**決定 (親裁定):** D1033 が命じる「専用起動器と B-4 識別子による支配点」は、鋳造の 1 点だけでは
成立しない。**鋳造と、certified sink での消費の 2 点**で成立させる。sink 側の関門は
`orchestrator/campaign/wal.py` の COMMIT 分岐に置く。

**理由:**

- 段 3 の 2 レンズが独立に、`loop.run_campaign` と `pipeline.evaluate` が公開 API として
  関門の下にあることを file:line で示した。`CampaignConfig` は frozen だが `search_config` は
  可変の dict なので、通常の設定に識別語を後付けして直接 certified な成果物を作れた。
- COMMIT 分岐は、この 2 つの公開入口が**必ず通る唯一の合流点**である。入口ごとに関門を置くと、
  次に見つかる producer で同じ話を繰り返す。
- campaign lock が識別内容を持つため、cfg を受け取らない `wal.append` でも layout だけから
  B-4 かどうかを判定できる。
- 先例がある。certified sink の支配点を `wal.append` に置いた前例と同じ骨格である。

**発火条件:** lock が存在し、その識別内容が exact な識別語を持つときだけ。lock が無い campaign では
関門の本体を 1 行も実行しない。**識別語を持たない通常の測定の受理集合は 1 bit も変わらない。**

**却下した選択肢:**

- 鋳造の 1 点だけを支配点とする — 識別語を後付けした設定が別の producer から certified になる。
- 公開入口ごとに関門を置く — 次の producer で同じ穴が開く。

## {{D:b4-launch-record-is-overwritable}}. B-4 の起動記録は上書き可能にする

**決定 (親裁定):** 起動器が書く起動記録は、**同じ campaign に対して何度でも書き直せる**形にする。
一度しか書けない形は採らない。関門が要求するのは内容の一致であって、書かれた回数ではない。

**理由:**

- D1125 が「不可逆承認の token を測定の前提条件として新設しない」と定めている。
- D1124 が「同じ cell を何度でも測ってよい」「途中死した run の復旧に専用機構を要求しない」と
  定めている。一度しか書けない起動記録は、途中で落ちた走の測り直しを構造的に禁じる。
- 段 3 のレビューは一度限りの記録を薦めたが、上位の裁定と正面から衝突するため採らなかった。

**却下した選択肢:**

- 一度だけ書ける起動記録 — D1124 / D1125 と衝突する。

## {{D:b4-marker-mint-accepts-test-seal}}. 識別語の鋳造口は試験用の封印も受理する

**決定 (親裁定):** 識別語を作る入口は、production の封印と**試験用の封印の両方**を受理する。
production 限定にはしない。

**理由:**

- 標本を生む境界 (反復・駆動・certified sink・production factory) はすべて production の封印を
  要求する。試験用の封印で作った識別語付きの設定は、certified な標本を 1 つも作れない。
  **標本の受理集合は変わらない。**
- 鋳造口を production 限定にすると、campaign identity の golden を固定する検査すべてが
  実際に commit された受理記録を用意する必要があり、費用が跳ね上がる割に受理集合が変わらない。
- 段 6 のレビュー 2 本のうち 1 本は production 限定を薦め、もう 1 本は「意図的なら
  事前登録の文言をそう改めればよい」と代案を出した。後者を採った。

**帰結:** 事前登録の文言は「起動器だけが鋳造できる」ではなく
**「封印されていない識別語の作成を閉じた」**と書く。

**却下した選択肢:**

- 鋳造口を production 限定にする — 受理集合を変えずに検査費用だけを上げる。

## {{D:b4-introspection-is-a-non-guarantee}}. closure 内省による到達は非保証として明記する

**決定 (親裁定):** 起動器の封印と発行者へ、closure の内省を辿って到達できることは
**閉じられない**。閉じたと書かず、**非保証として明記する**。
内省を要しない素直な経路 (任意の封印を受け取る生成関数が module の属性として見えていた) は塞ぐ。

**理由:**

- Python では `__closure__` の走査を塞げない。module 属性を隠しても必ず辿れる。
- 同一 process からの属性書換えへの耐性は、既に隣接 module が非保証として列挙している。
  同じ枠に入る性質であり、新しく保証を謳うと恒真な保証になる。
- 塞げる経路と塞げない経路を分けずに「閉じた」と書くと、事前登録の正直さ要件に反する。

**却下した選択肢:**

- 内省経路も閉じたと書く — 実際には閉じられず、謳うだけの保証になる。
- 素直な経路も非保証で済ませる — 実際に塞げるものを塞がない理由がない。

## {{D:b4-lock-snapshot-and-explicit-absence}}. B-4 分類と receipt は同一 lock snapshot へ束縛し、不在は明示 digest で表す

**決定 (親裁定):** COMMIT sink は campaign.lock の同じ raw bytes snapshot を B-4 分類と receipt hash
検証に使う。lock 不在は receipt 自身の digest を fallback 権威にせず、issuer / sink 共通の固定
absence digest へ束縛する。decoded identity が exact dict で `search_config` key 自体を持たない valid lock は
非 B-4 と分類し、key が存在して型不正なら fail-closed にする。

**理由:** 独立 Codex focus が、分類時 markerless / 検証時 marked の二重読取、分類時 lock 不在 / 検証時
marked の fallback、decoded lock と directory basename の campaign id 差をそれぞれ実行可能な負例で示した。
同じ path を二度読むことも、receipt が自己申告した digest を sink observation の代用にすることも、
D1033 の支配点を構成しない。

**受理集合:** 最初から lockless + explicit absence receipt、valid markerless lock + exact receipt、valid non-B4
lock (`search_config` 無し) + exact receipt は受理する。**physical lock に束縛した receipt を発行後に lock を
消す旧経路だけを拒否へ狭める。** 同経路を残すと marked receipt を退避・復元して G4 を迂回できるため、
規律2と両立しない。

**却下した選択肢:** receipt 内 digest fallback の維持 — absence-to-marked bypass を再開する。
全 non-B4 lock の `search_config` 欠落を分類不能として拒否 — marker 無し通常走の受理集合を壊す。

**scope 外:** D1042 の一回性 token、D1043 の payload snapshot、D1050 の受理記録配置、COMMIT 後 relabel
(D1223) の実装、正式 B-4 実走。
