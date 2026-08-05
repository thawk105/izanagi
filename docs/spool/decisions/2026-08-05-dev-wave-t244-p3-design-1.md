---
schema: izanagi-spool-v1
ledger: decisions
authored: 2026-08-05
wave: dev-wave-t244-p3-design
seq: 1
---

## {{D:t244-p3-design-package}}. [T-244] P3 の (1)(2)(3) は設計裁定パッケージとして起草し、実装 wave は起票しない — bootstrap と世代移行が不可分だと実測し、単一候補 batch の恒真化と予算 root の非同一性を固定する

**背景:** worklog (200) のユーザー裁定は、[T-244] P3 の裁定パッケージ 5 件のうち (4)(5) を確定し、
**(1) origin authority の実体化・(2) production runtime bootstrap と authority 世代移行の主体・契約・
(3) 結線先と batch 形状は、設計 wave が推奨付きパッケージを起草して返す**と定めた。本 D はその
設計 wave の判断である。逐語と裁定パッケージ本体の正本 =
`output/insights/2026-08-05_t244-p3-design/` (README が §9 に択一 10 件を持つ正本)。

**決定 (1): 本 wave は実装せず、推奨付き裁定パッケージを成果物とする。** 依頼が設計起草である以上
これは前提どおりだが、あわせて**設計案をそのまま実装 wave として起票してはならない**と裁定する。
段 3 の敵対 2 レンズが独立に NO-GO を返し、決め手は 4 点である。(a) DW-G04 の発火 gate を満たす
既存 artifact path も計測 ID も書けない — 設計案が挙げた「現行 baseline で発火する検査」10 件のうち
正例は将来形の 1 件だけで、残りは現在系を拒否する検査である。(b) DW-G01 の生死実験が先行して
いない。(c) 受理集合の変更が 4 面 (production 初期化・authority generation schema・reservation
event・report v3 / completeness) 同時で、D96 の同一変更単位が 1 wave に収まらない。(d) 予算 root の
同一性が repo 内の検査だけでは原理的に閉じない (決定 4)。

**決定 (2): 承認済み裁定の前提が動いていたことを記録する (実測)。** D163 が見た ledger は v1 で、
間に P4 wave が land して v2 になった。**前パッケージが引く file:line はすべて stale である。**
そのうえで D163 決定 2 は現 v2 でも成立するが、理由はより強い — production runtime の初期化は
入口の欠落ではなく `_initialize_locked` 冒頭の**明示的な禁止**である。したがって解消は入口追加では
足りず、「誰が・何を根拠に禁止を解除できるか」という**受理集合の変更**を伴う。
さらに D163 の「runtime を消せば新品になる」は現 v2 production には**当たらない** — 現在は消すと
単に起動不能になる。「削除後に新品」は fixture 経路と、将来 provisioning を素朴な
`absent ⇒ genesis` にした場合の危険であり、この区別を設計要件として固定する。

**決定 (3): bootstrap と authority 世代移行は不可分だと固定する (実測)。** runtime genesis は
authority registry の全 entry をその場で焼き込み、読み出しは authority blob の完全一致と entry
件数の一致を要求する。origin を後から足す event 型は存在しない。**最初の genesis が、その runtime で
今後存在しうる origin 集合を永久に固定する。** よって世代移行を決めずに最初の genesis を打つことを
禁じる。推奨形は epoch router (世代ごとに runtime epoch を分け、新世代は追加 origin だけを持ち、
旧 epoch と counter を保持する) であり、累積 authority 全体を毎世代 genesis し直す案は旧 origin の
counter reset か現行 event / hash model に無い imported-terminal genesis を要するため却下する。

**決定 (4): 予算 root の同一性は本設計では閉じないと明記する。** runtime root の git-common-dir 束縛が
塞ぐのは**同一 clone 内の worktree 回避だけ**であり、別 clone・pointer ごとの全削除・履歴書換えでは
予算 root を作り直せる。外部の append-only anchor が無い限り同一 UID の協調削除は防げない。
これは設計の穴ではなく repo 内検査の原理的限界であり、名乗りの限定か外部 anchor の導入かを
ユーザー裁定へ返す。**「予算が新品にならない」と一般化してはならない。**

**決定 (5): 単一候補 × replicate の batch を「候補 batch」と記録することを禁じる。** P4 wave 以降、
batch の distinct 制約は候補平文でなく commitment に掛かり、commitment preimage が query / replicate
ordinal を含むため、**同一候補 1 点の反復でも合法な batch になる**。しかし ledger の `cardinality` は
member row 数であって候補数ではない。そのまま記録すると将来の P4 consumer が候補 1 点を候補
2 点以上と誤認する。散文で「反 oracle 性は満たさない」と断るだけでは機械的な誤認を防げないため、
`member_row_count` と `distinct_candidate_count` を別 field とし、後者が 1 の記録を P4 / 軸 (iii) の
証拠として受理不能にすることを推奨形とする。記録してよい名乗りは「ledger transaction batch」までとする。

**決定 (6): 親の provisional 裁定 3 件を反証として記録する。** (a) 「単一候補 × R replicate の第 1 段が
予算束縛を実体化する」は**撤回する** — 予算 counter が動くのは batch commit 受理時だけで、それを
呼ぶ production caller は存在しない。実測が示したのは「ledger の受理規則上そういう batch が作れる」
ことに留まる。(b) 「authority 世代移行は既存型を適用し新機構を発明しない」は言い過ぎで、流用できるのは
record 構造・承認連鎖・tombstone・transition allowlist の型までであり、epoch route・世代跨ぎの
cell 一意性・累積予算は origin 固有に作る必要がある。(c) manifest field の preimage 分類は
「既存 3」ではなく**「既存 2」**である — CCBench commit OID は manifest が full 40-hex を要求するのに
対し現行 pin は 7 文字 prefix であり、そのままでは preimage にできない (段 2 と両レンズが独立に指摘)。

**決定 (7): preimage の trust root は捕捉 commit の名前付き artifact の raw blob bytes とし、
非自己参照 topology を必須条件にする。** コードから導出する案 (source hash・runtime 定数の JSON 化) は
import closure の漏れ・実装差依存・「実装を実装自身で証明する」自己参照のため trust root にしない。
捕捉 commit は authority record 自身を含まない commit でなければならない。

**決定 (8): 名乗りの上限。** 本 wave が名乗ってよいのは「(1)(2)(3) について推奨付きの設計裁定
パッケージを起草した」までである。本設計を**実装しても**名乗ってよいのは「承認済み authority 世代に
対する production provisioning と、非認定 pilot における single-candidate × reserved-replicate の
producer liveness / 配線」までとする。P3 充足・部分 P3・P4・軸 (iii)・P7・物理 query floor の証明・
多世代開放・certified 選択・cap 引上げのいずれも名乗らない。**P3 は依然 FAIL、D114 の上限 1 と
D166 の P4 FAIL も不変**である。

**理由:** (1) の帰結が (2)(3) の形を決めるため 3 件は同一 wave で扱う必要があり、実際に
「preimage を artifact bytes にする」判断が世代移行の transition table と cell 一意性の設計を規定した。
一方、実装へ進める条件は揃っていない — 発火 gate の正例が無く、生死実験も先行しておらず、
受理集合の変更が 1 wave に収まらない。ここで部分実装すると、D147 が却下した「未結線のまま leaf だけ
land する」と D164 が却下した「発火しない検査を防壁として記録する」の両方を同時に踏む。

**却下した選択肢:**
- 未裁定部分を親の裁量で決めて実装する — D121 却下案 (b)「未裁定設計の既成事実化」と同型で、
  D147 / D153 / D163 が同じ理由で却下している。
- 単一候補 × replicate の batch を「batch freeze を結線した」と記録して発火証拠にする —
  予算が減る production path が存在せず、`cardinality` の意味を候補数へ読み替える誤導になる。
- 全機構 (authority schema・provisioning・epoch router・reservation FSM・driver 改修・report v3・
  sidecar) を一括実装してから正例を作る — DW-G01 の生死実験先行に反し、1 wave で安全に閉じない。
- 予算 root の非同一性を未記載のまま provisioning を解禁する — 解禁した瞬間に予算 root の
  作り直しが成立し、D147 が停止理由とした穴の再演になる。

**研究状態への影響:** なし。本 wave は docs と逐語のみで、production 挙動・受理集合・certified 選択・
材料レポート・試行台帳・proof chain・凍結 bytes はいずれも不変である。実装差分が無いため
変異 matrix と実装後の受入全走は対象外。
