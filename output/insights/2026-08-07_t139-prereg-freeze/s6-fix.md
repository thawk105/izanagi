# [T-139] 本走前置 — 段 6 fix の対応表 (2026-08-07)

```text
authority: none
default_effect: no-state-change
```

段 6 の敵対レビュー 2 本 (`s6-revA.md` / `s6-revB.md`、いずれも NO-GO) の must-fix に対する対応。
レビュー対象は substantive commit `f366de0e`。実装差分はゼロのままで、fix はすべて docs 本文の訂正である。

**本書には fix が 2 巡ある。**下の §「第 1 巡」の判定は、焦点再レビュー (`s6-refocus.md`、NO-GO) が
**`closed` の過大計上**だと指摘した。再レビューの独立判定 (closed 5 / partial 8 / regressed 3) を
受けて第 2 巡の fix を行った。**権威ある判定は §「第 2 巡」の表**であり、第 1 巡の表は
親が一度そう判断した記録として残す (書き換えない)。

## 第 1 巡 — レンズ A の must-fix (親の当初判定。過大計上を含む)

| # | 所見 | 対応 | 判定 |
|---|---|---|---|
| MF-1 | 軸 1 が空集合で排他でない (空集合は連結でもあるため `empty` と `unbounded_connected` に同時一致) | 軸 1 を first-match の順序表にし、`empty` を順 1 に置いた。`A>0` でも判別式が負なら空になることを明記 | closed |
| MF-2 | `D̄ < 0` (劣化版の方が速い) を `degradation_below_kappa` と誤分類する | 順 2 に `degradation_absent` を新設し、符号の偶然で `RF` が `(0,1)` に入る領域を分離した | closed |
| MF-3 | gate が承認済み core blob・fold 発効点・実 checkout を束縛しない | 条件を 7 つへ拡張。fold commit の子孫であること、追補が core の三つ組 (path・commit・digest) へ従属すること、`measurement_head` を署名から外し resolver が実 checkout から導出することを明記 | closed (文書契約として) |
| MF-3b | gate を満たしたまま規律を破る投入 (待機 0 秒・恒真な環境復帰指標・失敗の写像先付け替え) | 追補の「越えてはならない線」を新設。恒真化する指標・全域の許容範囲を禁じ、性能測定開始後の失敗を開始前へ写すことを禁じた。gate 条件 (v) が閉集合外の field を拒否する | closed |
| MF-4 | pilot を一意に実行する量が閉集合から落ちている (driver 引数・arm identity・seed と許容 schedule 集合・`J_max` と `J` 導出) | 追補 A へ `a07`〜`a12` を追加し、`q` / `C_w` の構成と weak null 較正の仕様も含めた | closed |
| MF-5 | 追補 B (旧 alpha) の締切が矛盾し、本走 raw を見た後に有意水準を選べる | 締切を **本走の投入前**へ統一 (header・§10・§14・§15)。verdict の直前ではない | closed |
| A4 nit | 追補の待機秒数は測定値を動かす | 「測定プロトコルの固定であり推定量の式は変えない。pilot 前に固定し pilot 後に変更しない」と明記 | closed |

## 第 1 巡 — レンズ B の must-fix (親の当初判定。過大計上を含む)

| # | 所見 | 対応 | 判定 |
|---|---|---|---|
| 1 | 「その履行として」が過大主張 (最厳格解釈は未達でユーザー裁定へ返してある) | roadmap の当該文を「同一の変更単位に置いたが、canonical 台帳と同一 commit に載る最厳格解釈は満たしておらず、差はユーザー裁定へ返してある」に訂正。先行 commit の message の「履行する」も本 fix commit の message で訂正する | closed |
| 2 | correctness anomaly の終端単位が食い違う (cluster vs 候補) | roadmap と D fragment を **候補の終端 reject** (D134 決定 (6) と同じ単位) へ統一 | closed |
| 3 | core に fold 後発効と独立 validator の唯一権威が無い | core §0 に発効点を、§7 に validator 唯一権威と消費側の入力制約を追加 | closed |
| 4 | workload block 順の条件が core にしか無い | roadmap と D fragment の順序均衡へ seed・許容集合・workload block 順を追加 | closed |
| 5 | κ の境界が数式 (`> 0`) と文章 (「20% 未満」) で違う | 「20% を**超えない** (`E[H_w] ≤ 0` の) workload では主張しない。ちょうど 20% は受理しない」へ訂正 | closed |
| 6 | 臨界値 `q` と `C_w` の構成が固定も委譲もされていない | §4 に「core は名前だけを固定し、数値と手続きは追補 A で確定する」を追加。追補 A に `a11` を新設 | closed |
| 7 | `J_max` と reserve の費用境界が未固定で追補にも無い | §6 を訂正し、追補 A に `a10` (`J_max`・26 割当ての内訳・`J` 導出手続き) を新設 | closed |
| 8 | 追補 B の期限と closed-schema の gate が矛盾 | 期限を本走投入前へ統一。gate 条件 (v) に「閉集合の外の field を持つ追補は解決に失敗する」を追加 | closed |
| 9 | roadmap 単独の読者に「機械 gate 未実装」の留保が届かない | roadmap の例外の末尾に「本例外の機械執行はまだ無い。本節だけを根拠に投入が機械的に阻止されていると記録してはならない」を追加 | closed |
| nit | README が `package.md` と core の双方を「正本」と呼ぶ | README を「裁定**前**の正本は `package.md`、裁定の**結果**の正本は worklog と core」へ書き分けた | closed |
| nit | 「データを 1 点も見る前」は対象データを限定すべき | 「本 study の pilot と本走のデータを 1 点も見る前 (既存の J=1 engineering screen は既に見ている)」へ訂正 | closed |

## partial のまま残すもの (scope 外。ユーザー裁定へ返す)

- **レンズ A MF-3 の trust root** — `measurement_head` を実 checkout から導出せよ、というのは文書上の
  要求であって機械保証ではない。resolver を実装するまで、別 checkout で測って別の head を記録する
  偽造は検出できない。core §15 の「この gate が保証しないこと」に既に書いてある。
  実装は producer wave の責務。
- **D134 の「同じ変更単位」の残差** — canonical 台帳と roadmap を同一 Git commit に載せることは
  `docs/spool` 規約下で不可能である。roadmap と D fragment の双方に差を明記し、
  `s4-adjudication.md` §4 でユーザー裁定へ返した。
- **レンズ B が指摘した裁定候補の粒度** — producer/qsub のどちらを第一 admission boundary にするかは
  残すが、受領証の三つ組と validator/consumer の権威境界は本決定と D162 が既に制約しているので
  再択一にしない。裁定候補は `s4-adjudication.md` §4 を訂正して整理する。

## regressed

なし。

---

## 第 2 巡 — 焦点再レビューの指摘への対応 (権威ある判定)

`s6-refocus.md` が第 1 巡を独立判定した結果は closed 5 / partial 8 / regressed 3 だった。
そのうち real なものへの対応と、親の最終判定は次のとおり。

| # | 再レビューの指摘 | 第 2 巡の対応 | 判定 |
|---|---|---|---|
| F1 | gate は承認済み blob を束縛しない。fold commit `F` の子孫で同 path を書き換えた blob を core と申告できる | gate 条件 (3) を新設 — `core_ref.sha256` が **`F:<canonical path>` の blob の digest** と一致することを要求した。`F` の同定も「本 study の決定を `docs/decisions.md` へ追記した main 上の fold commit。SHA は land 後に worklog へ記録する」と一意化した | closed |
| F2 | 追補が allowlist 止まりで、欠落 field を拒否しない | 条件 (5) を **exact-key** に強化 (全件必須・余剰禁止。欠落も余剰も解決失敗) | closed |
| F3 | 追補 B へ条件 (5) を「同型」適用すると `b01`/`b02` が拒否される | 条件 (5) に「`addendum_b` に適用するときは対応する閉集合 `b01`〜`b03` を基準にする」を明記 | closed |
| F4 | `a11` (`q` の構成) を追補へ出しながら「推論内容を固定した core」と主張するのは矛盾 | §0 を書き直し、**2 段階事前登録**であること、**core 単独では完結した事前登録ではない**ことを明記。D fragment 決定 (5) と roadmap も同じ表現へ揃えた | closed |
| F5 | `q` と累積 alpha の依存が未定。追補 B が pilot 後に `q` を動かせる | **primary 系列の有意水準を追補 A の `a13` へ移し**、追補 B は `q` に影響する量を一切持たないと明記した。primary の判定基準は pilot より前に完全に固定される | closed |
| F6 | `J_max` が §6 (未確定) と §11 (`8+2+13+3` 固定) で二重定義 | §11 を「上限 26 だけが固定。内訳は裁定時の目安であって確定値ではない。`J_max` は `a10` で確定」へ訂正 | closed |
| F7 | 「順 1 は軸 1 の非 `bounded` をすべて吸収する」は表自身と矛盾 (`A>0` の空集合は順 3) | 説明文を訂正。`D̄ = 0` が順 1 へ落ちること、`A>0` でも空集合がありうることを明記 | closed |
| F8 | `degradation_below_kappa` の説明が過大 (条件は「`inf H > 0` を認証できない」であって「劣化が κ 以下」ではない) | 説明を条件どおりに訂正 | closed |
| F9 | §10 の「正規の台帳根」が追補 B の閉集合に無い | `b03` (累積台帳を束縛する正規の根の同定方法) を新設 | closed |
| F10 | D162 決定 (4)(5) の「consumer が同一呼出し内で trusted validator を再実行」「単一 fd / snapshot」が落ちている | core §7 に決定 (3)(4)(5) の要求を明記 | closed |
| F11 | 順序均衡の「差 1 以内」が core にしかない | roadmap と D fragment を「差 1 以内」へ揃えた | closed |
| F12 | roadmap が追補 A / B と期限を述べない | roadmap の事前登録条件へ追補 A・追補 B と期限、承認済み bytes の要求を追記した | closed |
| F13 | README が core を「採択結果の正本」に含めるが core 自身は射影だと言う | README を「採択結果の正本は worklog と決定。core はそれを実走束縛の形へ射影した設計の正本」へ訂正 | closed |
| F14 | HEAD の commit message が「履行する」のまま | 本 fix commit の message で明示的に訂正する (下記) | closed |
| F15 | κ の境界 (`≤ 20%` は主張しない) が canonical worklog の「20% 未満」と食い違う | **worklog は書き換えない** (凍結記録)。本 wave の worklog fragment の `更新` 本文で、ちょうど 20% を受理しないことを明記して差を閉じる | closed |
| F16 | `measurement_head` の trust root が文書上の要求にとどまる | **partial のまま。**resolver を実装するまで機械保証にならない。core §15 の「保証しないこと」に明記済みで、実装は producer wave の責務 | partial (scope 外) |
| F17 | 待機 0 秒が禁止されていない | **partial のまま。**0 秒が不適切かは環境復帰指標 `a03` の許容範囲で決まる設計であり、秒数の下限を今ここで発明すると数値の捏造になる。`a03` の恒真化禁止が実効的な防壁である | partial (数値は追補 A) |
| F18 | 「全 must-fix closed」「regressed なし」という第 1 巡の自己判定が過大 | 本節の判定表で訂正した。第 1 巡の表は記録として残す | closed |

**regressed:** 第 1 巡で再レビューが `regressed` とした 3 件 (F4 / F5 / F6 に相当) は第 2 巡で閉じた。
第 2 巡で新たに regressed になった項目はない。
