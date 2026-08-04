# [T-244] D121 P2 — 段 4 裁定 (実装しない)

```text
authority: none
default_effect: no-state-change
```

段 3 の敵対 2 レンズは**独立に NO-GO** を返した (レンズ A = BLOCKER 4、レンズ B = BLOCKER 3、
所見計 19 件)。親は全件を real/refuted に裁定し、**本 wave では実装しない**と決定する。
遷移は `4→7→8→9` (段 5・6 を飛ばす)。

## 決定 (1): 実装しない。決め手は 3 件である。

**第一に、依頼と親 brief の中心前提が実測で反証された。** 「payload の field も値も変更せずに
P2 の payload 射影面を閉じられる」という前提は成立しない。現行 production の critic payload
`harness_result.variant` は、却下経路で `p3_s4_loop.py:241` の
`"diffq-" + sha256(genome.canonical() + "|impl=" + predicate)[:12]`、build 到達時は
`pipeline.py:92` の `sha256(genome.canonical() + "|src=" + src_token)[:12]` であり、
どちらも preimage に候補述語 (= 5-bit wire の正準関数) を含む。候補 universe は 32 点しかないため
**この 12 hex は表引きで wire に一意復号できる**。親・レンズ A・レンズ B が独立に 32 点を静的列挙し、
**ID は 32/32 すべて一意、ID 中に自分自身の wire 字面が現れるものは 0/32** で一致した。

すなわち payload を不変に保ったまま書ける検査は「字面部分一致 tripwire」に限られ、それは
**現行 baseline の実漏洩に対して一度も発火しない**。これは D121 §7 P2 が名指しした恒真化そのもので
あり、`CLAUDE.md` 規律 6 の「恒真な保証 (謳うだけで発火しない assert)」に該当する。
land すれば「payload 面を閉じた」という誤った安心を作る。

**第二に、是正は親の裁量外の裁定 3 件に依存する。** (a) critic の recipient policy は D121 §8 択一 4
が「未解決」としてユーザーへ返した項目である。(b) auditor へ実効 diff と digest を渡してよいかは
D121 §4① の recipient matrix と現行実装が食い違っており、declassification の再定義が要る。
(c) 「IR schema SHA」の preimage (schema bytes / schema ID / emitter source / IR instance のどれか) が
未定義である。いずれも payload の field か値の変更を伴い、brief の不変条件 (1) が発火する。

**第三に、実装すると成果物を壊しうる。** `_invoke` 冒頭に fail-closed の raise を置くと、
現行の例外捕捉は provider 呼出し直前からなので generic `supervisor-error` になり
(`p3_autonomous_workload_trial.py:1231`)、さらに build mode では planner/coder 段での早期拒否時に
campaign の `reports/` が未生成のまま Layer-3 finalization が無条件実行され
(`同:1278`、`同:1147`)、terminal report を作れない経路が残る。no-build fixture テストではこの欠落を検出できない。

## 決定 (2): 親の provisional 裁定のうち 2 件を反証、1 件を縮小して維持する。

- **(P1) 反証。** 「auditor に diff と digest を渡してよい」は D121 §4① に反する。「diff を見せる以上
  digest は冗長」は recipient matrix を変更する根拠にならない。加えて段 2 案は同じ `preview_result` から
  取った値を「正解」として例外化しており、producer が実効値へ変われば検査の正解も同時に変わる
  **自己参照**である (F29 と同型)。
- **(P2) 反証 (方向は的中、脅威モデルは親が正しい)。** 段 2 プランの「現行 baseline は赤にならない」は
  字面モデルでのみ成立する。ただし**親の一般化「32 点 universe の digest は常に 5 bit 漏洩」は過大**で、
  正しくは `I(W;ID | 公開 codebook) ≤ H(W) ≤ 5 bit`。diffq 経路は写像が単射なので uniform な wire では
  5 bit 全部、`variant=None` の no-build や build 経路 (同一 source/compiler 文脈と無衝突が条件) では条件付きになる。
  この縮小形で採用する。
- **(P3) 循環を認めて維持不能。** 「payload は role 許可入力のみの関数」の「許可入力」を現行 key 集合と
  定義すると循環する — 秘密を許可 field の値へ符号化した瞬間、その値まで許可入力になる。
  正しい形は決定 (4) の indistinguishability 検査である。
- **(P4) 維持するが「安全の根拠」とは名乗らない。** auditor 入力 digest と verdict echo の内部名分離は
  保守性の hygiene であり、情報量を 1 bit も減らさない。

## 決定 (3): 名乗りの上限を固定する。

本 wave は実装差分ゼロであるから、**「P2 を閉じた」「P2 の部分実装」「非干渉検査を実装した」の
いずれも名乗らない。** P2 は引き続き **FAIL**、無条件義務 8 件のうち充足は P10 の 1 件のみ、
D114 の `MAX_APPROVED_GENERATIONS = 1` も不変である。
将来 実装する場合も、字面一致に留まる限り名乗れるのは
**「8c supervisor `_invoke` 経路の candidate-literal tripwire」**までであり、module 名は
`reflux_noninterference.py` ではなく `reflux_candidate_literal_tripwire.py` 系とする
(既存 `projection_guard.py:2` が同種の検査を「字面 tripwire」と正直に名乗っている前例に揃える)。

## 決定 (4): 推奨する正しい形を記録する (実装はしない)。

レンズ A の必須是正 2 を採る。secret `S` = 候補 wire、公開入力 `P` を定義し、
**`S` を変えて `P` を固定したとき provider へ渡る serialized sink bytes が同一であること**を検査する
(indistinguishability)。現行コードに対する予測は次で、これ自体が critic の漏洩を可視化する。

| role | `S` を変えたとき payload bytes は | 判定 |
|---|---|---|
| planner | 不変 (cap=1・generation 1 では whiteboard 空、metrics は None) | PASS |
| coder | 不変 (planner の direction 経由でのみ依存し wire に直接依存しない) | PASS |
| auditor | 変わる (diff を意図的に開示) | 明示 declassification が要る |
| critic | 変わる (`variant` 経由) | **FAIL — 裁定 (a) が決まるまで解けない** |

この検査は緑では land できない (critic が赤になる)。したがって**裁定が先**である。

## 決定 (5): 変異事前登録は行わない。

実装差分がないため `DW-M01` の事前登録対象がない。段 2 が提示した mutant 12 件も登録しない。
なお、そのうち **M3 / M5 / M6 / M11 は所有 A が driver を import しない契約の下で帰属が成立せず**、
**M8 / M9 / M10 は「新たな漏洩を作る」のではなく既存の可逆漏洩を字面へ展開するだけ**である
(レンズ B の指摘、real と裁定)。将来の実装 wave はこの表をそのまま流用してはならない。

## 決定 (6): 親の誤りを 1 件記録する。

段 1 brief の環境記述「login ノードで pytest」は**正本違反**である。`AGENTS.md` は
Pegasus ログインノードでの pytest を単一 nodeid も含めて一切禁じ、親が `tools/run_tests.py` 経由で
計算ノードへ dispatch すると定めている。本 wave は実装差分ゼロで pytest を走らせないため実害は
生じなかったが、brief 段階の誤りとして残す。

## 所見の裁定台帳 (19 件)

| # | 所見 | 裁定 |
|---|---|---|
| A-B1 / B-B1 | 現行 variant が可逆で 32 件すべて字面検査を通る | **real・採用**・scope 内 → 実装中止の決め手 1 |
| A-B2 / B-B2 | auditor 例外が D121 matrix に反し、CandidateMaterial が自己参照 | **real・採用** → 裁定 (b) へ |
| A-B3 | allowlist が「現行 field の写し」で critic policy 未裁定、定義が循環 | **real・採用** → (P3) 撤回 |
| A-B4 | schema closure は値の情報依存を制約せず残余容量が大きい | **real・採用** |
| B-B3 / A-M2 | 「IR schema SHA」の preimage が未定義、`IR_SCHEMA_ID_SHA256` は誤称 | **real・採用** → 裁定 (c) へ |
| A-M1 / B-M1 | payload 外の観測面が開いたまま、名乗りの上限 | **real・採用** → 決定 (3) |
| B-M2 | 拒否後の consumer 未確定、build mode で terminal report を作れない | **real・採用** → 実装中止の決め手 3 |
| A-M3 / B-M3 | mutant が直接コピー型に偏り、4 件は帰属不成立、cap=1 で history 結線が恒真 | **real・採用** → 決定 (5) |
| B-M4 | `noninterference` は過大な名乗り | **real・採用** → 決定 (3) |
| A-N1 | P4 の命名分離は hygiene で安全根拠ではない | **real・採用** → (P4) 縮小 |
| A-N2 | dict key 順序は `sort_keys=True` により現行経路では 0 bit | **real・採用** (情報として記録) |
| B-N1 | 既存 payload key assert を弱体化しない条件を明記すべき | **real・採用** → 将来 wave の条件 |
| B-N2 | auditor digest の内部命名分離は妥当 | **real・採用** |
| B-N3 | brief の環境記述が正本違反 | **real・採用** → 決定 (6) |
| 段 2 (A) | 「baseline は赤にならない → GO」 | **refuted** (字面モデルでのみ成立) |
| 親 (P1) | auditor へ diff + digest を渡してよい | **refuted** |
| 親 (P2) | 32 点 digest は常に 5 bit 漏洩 | **縮小して採用** (条件付き) |
| 親 (P3) | 許可入力 = 現行 key 集合 | **refuted** (循環) |
| 親 (P4) | 命名分離 | **維持・ただし安全根拠ではない** |

## 裁定パッケージ (ユーザー判断待ち)

| # | 択一 | 親の推奨 |
|---|---|---|
| U-1 | **critic の recipient policy** (D121 §8 択一 4 の再掲・具体化)。critic payload の `variant` は wire へ可逆であり、現状では critic が 5 bit を観測できる。(i) `variant` を origin scope の不透明 ID へ置換、(ii) critic を trusted 側へ再分類、(iii) 現状を受容残余として明記 | **(i)**。ただし受理集合と D51 provenance に波及するため D96 手続が要る |
| U-2 | **auditor の declassification 定義**。(i) raw IR から独立再生成した diff のみ許し digest は渡さない (D121 §4① どおり)、(ii) diff + digest の現状を明示的な declassification として会計する | **(ii)** — 現状 raw = 実効なので digest 単独の秘匿は恒真。ただし reflux-control 実装時に (i) へ戻す条件を同時に固定する |
| U-3 | **「IR schema SHA」の preimage**。schema bytes / `SCHEMA_ID` 文字列 / emitter source / 32 golden のどれを identity とするか | **emitter source + 32 golden の複合**。`SCHEMA_ID` 単独では emitter を変えても検出できない |
| U-4 | **本 wave の成果を実装 wave として再起票するか**。U-1〜U-3 が確定すれば決定 (4) の indistinguishability 検査を実装できる | **U-1〜U-3 の確定後に再起票**。確定前の literal tripwire 単独 land は恒真な保証になるため推奨しない |
| U-5 | **`docs/dev-wave/**` の予算が事実上飽和しており、段 8 の自己改善が実施不能である**。本 wave 開始時点の合計は 25,196 / 25,200 bytes で残り 4 bytes しかない。(i) 陳腐化した節を精査して空ける、(ii) L2 節をテスト・機械検査へ移して本文を削る、(iii) 現状維持 (自己改善を恒久的に停止する) | **(i)+(ii) の棚卸しを別タスクで行う**。予算値の引き上げは自己改善に含めず独立審査とする方針のため提案しない |

### 段 8 で撤回した改善候補 2 件 (U-5 が解けたら再投入する)

本 wave は実測に基づく改善候補を 2 件記録したが、**いずれも予算超過 (合計 +142 bytes、残 4 bytes) で
実施できず撤回した**。自己改善契約の「予算に収まらなければ変更を止めてユーザー裁定へ返す」に従う。
予算のために既存の安全義務を削って捻出することはしなかった。

1. **`DW-S01` (core.md) へ**: 「受入・実測の環境も確定する」に**テストの実行場所と dispatch 経路**を
   含める旨を足す。**実測根拠** — 本 wave の段 1 brief が「login ノードで pytest」と書き、正本違反
   だった。段 3 のレンズ B が MINOR として拾ったため実害は出なかったが、実装ありの wave なら
   段 5/6 まで気づかず手戻りになる。差分は約 70 bytes。
2. **`DW-S02` (workers.md) へ**: 「brief で定めた判定基準を prompt の問い方で狭めない」を足す。
   **実測根拠** — 親が段 2 の prompt に「**字面で**含むか」と書いたため、子は brief の (P3) が定めた
   関数的な判定基準ではなく字面部分一致で判定し、「現行 baseline は赤にならないので GO」という
   撤回対象の結論を返した。段 3 が是正したが、段 2 の 1 本が丸ごと弱い前提の上に立った。
   差分は約 72 bytes。

## 研究状態への影響

なし。本 wave は docs と逐語のみで、production 挙動、受理集合、certified 選択、材料レポート、
proof chain、凍結 bytes はいずれも不変である。実装差分がないため変異 matrix と受入全走は対象外。
