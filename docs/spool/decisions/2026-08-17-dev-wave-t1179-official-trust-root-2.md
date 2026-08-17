---
schema: izanagi-spool-v1
ledger: decisions
authored: 2026-08-17
wave: dev-wave-t1179-official-trust-root
seq: 2
---

## {{D:durable-admission-trust-root}}. official 解禁の信頼根は durable admission 台帳に置き、買えたものを狭く書く

**決定:** floor の `eligible_for_refreeze` は producer の自己申告のまま残すが、**下流の信頼根には
しない**。floor cell claim を `s8b-holdout-cell-claim/v2` へ上げ、eligibility を決める事実
(fresh か resume か、非既定 seam 集合) を測定前に create-only で共有 admission 台帳へ刻む。
fresh 発行後の resume は claim を書き換えず、create-only の run-wide marker で表す。
live inspector は claim と marker から eligibility を**必ず**再導出し、共有 live verifier は
artifact の申告値と**双方向で**照合して、不一致を `refreeze-eligibility-mismatch` で拒否する。
**どちらの値も他方で上書きしない。** 比較を optional 引数にせず、callsite が省いて検出力を
消せる形を作らない。

**この決定が買っているものを狭く書く。** durable 側が与えるのは (i) 測定前に create-only で
共有 store へ置かれる事前 commitment、(ii) 生成後 artifact の書換と resume 後の付け替えの検出、
(iii) 台帳と artifact が食い違うときの下流拒否の 3 つだけである。
**同一 interpreter 内の module 属性差し替え (= 任意コード実行) への耐性は主張しない。**
台帳へ書く値を算出するのは producer 自身であり、その分類器を書き換えられれば台帳も一緒に嘘をつく。
module docstring の既知限界はこの形へ狭めて**残す**。消してはならない。

**理由:**
- ユーザー裁定が「信頼根は下流が再検証できる durable receipt 側」と定めた。対する
  「clean process 実行 + code identity 封印」は、同一利用者が自分を欺くのを防ぐ形であり、
  粗い provenance で足りる既定方針から最も遠い。
- 台帳記録は測定**前**、artifact の bit は測定**後**に書かれる。時点の差が事前 commitment の
  性質を与え、後から都合よく付け替える経路を検出可能にする。
- seam 名の閉集合を contract 側に置き、admission が受領 list をその閉集合に対して検証する。
  producer 側の分類器だけを書き換えて名前を捏造・欠落させる型はこれで落ちる。
- v1 claim には情報が無い。**欠落を推測で埋めず derived false へ倒す** ので、
  受理集合は厳しい側へ縮む。

**却下した選択肢:**
- **admission が実引数から独立に再分類する** — admission は呼び出しの実引数を見られないので
  実現手段が無い。段 2 プランも段 3 レンズも独立に同じ結論に達した。
- **basis を portable receipt / ledger projection の bytes へ入れる** — artifact 単体からの
  offline 再検証を可能にするが、receipt schema の bump が凍結 bytes の pin 閉包を巻き込む。
  本決定の経路は live 台帳照合であり、offline 再検証は今日の消費者の形ではない。残余は正直に記録する。
- **oracle driver / report 層へ直接の refusal 検査を足す** — 両層は ratified freeze の下流で、
  本決定が硬化する ratified consumer を経由して推移的に塞がれる。別の被覆 wave の仕事とする。

## {{D:finalize-pending-not-a-resume}}. M-finalize-pending は eligibility の観点で resume として扱わない

**決定:** terminal 書込後・権威 artifact 公開前で止まった run の「公開だけを再開する」経路は、
eligibility を再計算する resume として扱わない。この経路が公開する bytes は元の run が自ら
算出した staged bytes であり、**bytes の完全一致が要求される**ので、resume を eligible へ
洗浄する余地が構造的に無い。したがって resume marker の発行対象にしない。

**ただし本 wave はこの分離を実装していない。** 現行 main は、この経路の再開が
`staged bytes が再計算と不一致` で拒否されることを既存テストで固定している。
分離を入れると、その main 由来の期待値を変えることになる。本決定は方向の記録であり、
実装は crash 復帰の裁定 (手順書 §5 R-5) と同じ裁定単位で扱う。

**理由:**
- 段 2 プランは「finalize-pending だけが記録を迂回しないよう marker を前に置く」としたが、
  迂回の懸念は bytes 完全一致で既に塞がっている。前置きは正当な公開を殺す副作用の方が大きい。
- 一方で、この挙動は本 wave が持ち込んだ回帰ではなく main の既存挙動である。
  「回帰の修正」として黙って受理集合を変えてはならない。

**却下した選択肢:**
- **回帰として即修正する** — 段 6 の焦点再レビューがそう主張したが、一次資料 (main 自身の
  テスト) が反証した。検証せずに fix を投げた結果、main 由来の期待値を書き換える差分が
  1 巡ぶん無駄になった。
- **現状を正常として記録だけする** — 袋小路の実在を薄める。手順書 §3.6 に crash 点分類として
  明記し、択一を裁定へ返す形を採る。
