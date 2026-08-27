# 段 4 裁定 — [T-1629] D905 執行機構の回収と着地

親が段 2 plan、段 3 の 2 レンズ (sol = 検査の完全性、luna = 実効性と scope)、
および親自身の実測 M1〜M16 を突き合わせて裁定する。

## 0. 本 wave の核心 — 2 レンズが独立に到達した同じ限界

sol F2 と luna 所見 4 は、別のレンズから同じ結論に達した。

> **判定器とその呼び出し元は、判定対象の閉包の内側にある。呼び出し前に
> 「今動いている判定器の bytes が、以前に批准された bytes と同じか」を確かめる
> 外側の実行器が存在しない。**

したがって repo を編集できる主体は、鍵を一切持たなくても
`require_signed_ratification()` を無条件 return へ書き換えて commit すれば gate を消せる。
`capture_contract_loader_binding()` はその悪性 bytes を正直に hash して新しい authority に記録する。

**これは v1 から存在する構造であり、本 wave が新たに作る欠陥ではない** (sol F2 が明記)。
しかし D906 が署名対象へ「実行器と検査器の bytes」を含めよと書いているのは、まさにこの穴である。
回収 receipt の schema にはどちらも無い。

**裁定:** この限界は本 wave では閉じない。閉じるには repo の外に固定された実行器が要り、
それは本件より大きい別設計である。**したがって本 wave は D905 / D906 を
「満たした」と主張してはならない。** 主張してよい上限は §6 に書く。

## 1. 所見の real / refuted と採否

### real・採用 (本 wave で実装する)

| # | 所見 | 出所 | 対応 |
|---|---|---|---|
| R1 | 回収 u2 は main の DAG 修正より前の線形版で、shallow/graft 防御も無い | 親 M3 / plan A-2 / sol F3 | main の DAG kernel を共通化して書き直す |
| R2 | broker が `data=None` で子へ stdin を継承し、承認入力を食われる | 親 M4(a) / plan | `DEVNULL` 既定へ |
| R3 | broker が鍵と信頼根を自動生成する (TOFU) | 親 M13 / plan A-3 / sol F1 | 生成経路を全削除。信頼根不在なら fail-closed |
| R4 | broker が承認を tty から読まず、pipe の `y` を受ける | plan A-3 | `/dev/tty` からのみ読む |
| R5 | `--yes-i-have-read-this` が一度も読まれない死んだ flag | 親 / plan | 削除する |
| R6 | broker が AI 制御の source bytes を生で端末へ出し表示を偽装できる | plan A-3 | C0/ESC を escape して表示 |
| R7 | broker が既存 ledger の署名を検証せず、最終 LF も要求しない | plan A-3 | 両方検証する |
| R8 | broker が committed HEAD でなく worktree の trust/ledger を読む | plan A-3 | committed blob を読む |
| R9 | broker が append するだけで commit も CAS もしないので gate が開かない | luna 所見 3 | committed blob CAS + stage + commit まで transaction に含める |
| R10 | `source_commit` は存在確認だけで、その 27 blob が署名 digest と一致するか見ていない | plan A-2 / sol F6 | digest 一致 + reachability を検証する |
| R11 | 履歴検証が `O(M*N)` のスカラー倍算になり、受入全走を壊す | luna 所見 7 | 最終 chain の各行を 1 回だけ検証する `O(M+N)` 形へ |
| R12 | ledger blob / 行長 / 行数 / JSON nesting に上限が無い | plan A-2 | 上限を入れる |
| R13 | 信頼根 blob の履歴不変性を検査していない (空 ledger 中の差替えが無検出) | sol F1 / F3 | reachable 全史で信頼根 blob が一度だけ導入され不変であることを検証する |
| R14 | 回収 test に恒真なものが複数ある (runner 検出、merge 前提 assert、small-order R) | 親 M4(b) / plan A-1,A-2 | 書き直す |
| R15 | pin 閉包が M7 では不足 (独立 golden、位置スライス、逐語 25、test 名) | 親 M14 / plan B | 全部追随させる |
| R16 | fixture は synthetic repo に 27 closure blob を置かないと source binding の正例にならない | luna 所見 6 / sol F5 | synthetic repo へ 27 blob を commit してから署名する |
| R17 | 分岐した署名列は 1 本の chain へ合流できない | plan A-2 / sol F9 | fail-closed で拒否し、専用エラーにする |
| R18 | docs に exact 25 の逐語が production/test 双方に残る | 親 M14 / luna 所見 12 | 追随させる |
| R19 | D526 の主張上限を超える文言 (「人間署名」の断定) が plan にある | luna 所見 12 | §6 の文言に統一する |

### real・不採用 (scope 外。裁定パッケージでユーザーへ返す)

| # | 所見 | 理由 |
|---|---|---|
| S1 | 既存 lock の resume と certified artifact consumer が signed gate を素通りする (luna 所見 1 / sol F8 後半) | 閉じるには campaign.lock の authority へ signed receipt identity を記録する**schema 変更**が要る。これは凍結 artifact 形式の変更であり D956 が名指しする領域そのもの。本 wave の機構実装と同時にやるべきでない。**本 wave では素通りを実証する負例テストだけを入れ、閉じない。** |
| S2 | 外部の固定実行器が無い限り判定器自身を書き換えられる (sol F2 / luna 所見 4) | §0 のとおり別設計。D906 の「実行器と検査器の bytes を署名対象に含める」の実装方法をユーザー裁定へ返す。 |
| S3 | 鍵の紛失・交代・信頼根 rotation を schema が表現できない (sol F4) | 鍵運用のライフサイクル方針はユーザー決定。schema に epoch/key-id を足す形を提案として返す。 |
| S4 | 承認搬送と ratification window (luna 所見 2) | 「批准と official 起動の間に main を動かさない」を機構で強制するには lease が要る。運用条件として明記し、機構化はユーザー裁定へ。 |
| S5 | qualification lane へ signed gate を付けるか (luna 所見 9) | evidence-only lane の意味を変える。次 wave または裁定。 |
| S6 | `require_environment_contract=False` の免除経路 (sol F8 前半) | guided 分岐の意図的免除であり v1 専用。境界の確認結果を返すに留める。 |

### refuted

| # | 所見 | 判定根拠 |
|---|---|---|
| X1 | 親 M4(b) を「production 欠陥」とした親の帰属 | **refuted。** plan と親の再読が一致した。赤はテストの偽前提で止まっており production 行に到達していない。**test 欠陥である。** 親の M4 記述を訂正した (M16)。 |
| X2 | luna 所見 8「D956 が本件に適用され着手前 blocker になる」 | **refuted。§2 に理由と実測を書く。** |
| X3 | 親 (P8)「秘密鍵が AI の書ける領域外にあれば強さが決まる」 | **refuted** (plan C / sol F2)。鍵が安全でも、AI が broker か判定器を書き換えれば内容束縛が壊れる。(P8) を §6 の形へ差し替える。 |
| X4 | 親 M4「機構は端から端まで動く」 | **refuted** (luna 所見 5)。95 pass が保証するのは component 生死まで。M16 で撤回済み。 |
| X5 | 親 M12「閉包を広げても既存 artifact は 1 件も壊れない」 | **範囲不足だった。M15 で測り直し、結論は維持されたが根拠が変わった** (§2)。 |

## 2. D956 の適用可否 (luna 所見 8 への裁定)

**裁定: D956 は本件に適用されない。実装を進める。**

理由は 2 つある。

**(a) 主題が違う。** D956 の決定文は「**正式受入の gate** を足す実装は、強制ソース閉包の
exact 25 path を編集しない」である。正式受入 (受入全走の gate) と批准 (campaign 初期化の
authority) は別の機構である。本 wave が触るのは後者である。

**(b) D526 が本件について逆向きに既裁定である。** D526 は
「**比較処理と receipt 実装面は closure へ収載する**」と定めている。
判定器を閉包の外に置くと、AI が判定器を書き換えても批准が失効しないため機構が恒真化する。
D526 はその恒真化を避けるために収載を求めている。

**(c) D956 が挙げる代償は本件では発生しない (実測、M15)。**

| 母集合 | 件数 | closure map を持つ | 25 path (現行) を記録 |
|---|---:|---:|---:|
| tracked な campaign.lock | 32 | 0 | 0 |
| repo の `output/` を除く外部 campaign.lock | 1536 | 36 | **0** |

外部 36 件が記録しているのは 8 path (28 件) と 12 path (8 件) で、いずれも T1207 / T1287 より
前の epoch の遺物である。**現行 25 path 閉包に対して既に E1-stale であり、
本 wave が広げても新たに失効する certified campaign は 1 件も無い。**

この裁定は新 decision として記録する (§7)。**ユーザーがこの読みを否とするなら、
実装は revert 可能であり、その場合 §0 の限界がさらに大きくなるだけである。**

## 3. 実装 scope (プラン v2)

実装面は Codex `role=author` が書く。親は直接編集しない。所有は素集合。

- **単位 A — Ed25519 検証子** (`orchestrator/campaign/ed25519_verify.py`, `orchestrator/tests/test_ed25519_verify.py`)
  回収 production を採用し、テストを決定的な形へ書き直す。
  R14 の恒真 test を潰し、RFC 8032 の 4 ベクタ・固定 seed の differential・S+L・
  低位数公開鍵と低位数 R・全 3 引数の型規律を入れる。
  到達不能な二度目の parity 検査と冗長な曲線式検査は、**独立防壁として数えない旨をコメントで明示**し、
  変異事前登録から外す。
- **単位 B — 署名 receipt 検証子** (`orchestrator/campaign/enforcement_source_ratification_receipt.py` + test)
  R1 / R10 / R11 / R12 / R13 / R17 を実装する。
  main の `enforcement_source_ratification.py` から
  `_assert_full_history_repository` / `_reachable_commit_parents` / Git hardening を共通化し、
  **v1 の digest union と `_is_subsequence` は v2 へ流用しない**。
- **単位 C — broker** (`tools/ratification_broker.py` + test)
  R2〜R9 を実装する。**鍵生成と信頼根生成の経路を全削除する。**
  repo 内の copy は参照実装であり、運用 copy は AI が到達できない host に置く旨を
  module docstring と `hooks/README.md` に書く。
- **単位 D — 配線** (`campaign_lock.py`, `contract_loader_binding.py`, `artifact_admission.py` の逐語,
  `conftest.py`, pin を持つ全 test)
  閉包を 27 path へ広げ、`verify_ratified_contract_loader_binding` を v2 へ切り替える。
  R15 / R16 / R18 を実装する。**S1 の素通りは閉じないが、素通りが在ることを示す負例テストを入れる。**

D は A と B に依存するので、A・B の完了後に投入する。

## 4. 不変条件 (実装子へ渡す)

1. **AI は実 repo の信頼根も receipt 行も生成・編集しない。** 合成 repo 内は対象外。
2. 信頼根と v2 台帳は `hooks/` 配下に置く。実 repo のそれらは人間が一度だけ置く。
   **author はこの 2 file を作らない。**
3. 既存テストの期待値を変えない。例外は閉包 path 数の pin だけで、
   「閉包を広げたので追随」以外の理由では動かさない。
4. 免除経路への付け替えをしない。
5. 受入全走の所要を増やさない (R11 はこの制約から来ている)。
6. §6 の主張上限を超える文言を docstring・エラー文・docs へ書かない。

## 5. 完了条件 (ii) の扱い

broker は remote HEAD から digest を毎回計算するので、ユーザーの手番は
**「official 起動の直前に 1 コマンド」**へ縮む。64 hex の転記は残らない。
これは D905 が求めた形である。

ただし luna 所見 2 のとおり、**批准から official 起動までの間に閉包 27 file のどれかが変わると
receipt は機械的に拒否される** (fail-closed で安全側だが、承認は失効する)。
この非介在条件を機構で強制する lease は S4 として裁定へ返す。

起票する exact digest は land 後の main tip で親が実測して報告する。
**現時点の実測値は `dabeada30868a5f790b25b86a9f0a34fafb24946f0e73de48fb90d97d9332eb9` (25 path) だが、
閉包が 27 path になるので land 後は必ず変わる。**

## 6. 主張してよい上限 (D526 の範囲内。R19)

書いてよい:

> 現在の committed 信頼根の鍵で検証できる署名 receipt の集合と、要求された closure digest を
> 比較する。信頼根の秘密鍵は repo の外にあり、AI はそれを持たない。

書いてはいけない:

- 「人間が批准したことの機械的証明」
- 「AI が追記できない集合との比較」 (§0 のとおり、判定器自身を書き換えられるため無条件には言えない)
- 「D905 / D906 を満たした」

## 7. 記録する設計判断 (段 7 の decisions fragment)

- D956 は批准機構に適用されない (§2、M15 の実測付き)。
- 判定器が判定対象の内側にあるという構造的限界と、主張上限 (§0 / §6)。
- 分岐した署名列を fail-closed で拒否する (R17) ことと、その運用上の代償 (sol F9)。
- 信頼根と台帳を `hooks/` に置き、人間が一度だけ置く bootstrap 契約。
