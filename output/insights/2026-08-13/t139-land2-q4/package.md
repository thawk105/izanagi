# 裁定パッケージ — [T-139] land 2 / Q4 組み替え scope (K1〜K5)

正本。wave `dev-wave-t139-land2-q4` が段 4 で確定させた、ユーザー手番の設計択一 5 件。

**前提:** 指示は「[T-139] land 2 を Q4 の組み替え scope で完了 land させる」だった。
本 wave はそれを実行しようとして、**裁定時点で未見だった事実 4 件**により実装しないと判断し、
`DW-S04` の定めどおり親が不採用にせず再裁定へ戻す。

**先に良い知らせ。** 先行 wave (worklog エントリ 470) が挙げた閂 2 件は**どちらも解消していた**。

- `a12` (事前 simulation) は完走した — R1 (a) の裁定どおり独立 wave が 2026-08-12 に実行し、
  pass artifact が repo に入っている。
- `a09` の serialization 問題は R2 (a) の「canonical を名乗らない」で回避できる — 敵対レンズも追認した。

**しかし別の閂が 3 本見つかった。** 以下はその報告と、進め方の選択肢である。

---

## 事実 1 — 承認済み契約が、まだ存在しない部品を必須引数にしている

**D234** が固定している契約はこうである。

```text
submit_pilot(*, binding: PreregBinding) -> submission_id
```

同じ decision は「`binding` が `resolve_effective_preregistration` から返っていない限り
**実行してはならない**」と書き、7 つの条件を課している。

**この `PreregBinding` と `resolve_effective_preregistration` が、pilot 投入前提の #6 そのもの**である。
そして #6 は Q1 / Q2 が先送りした層の下流にある。

つまり **「`submit_pilot` を作れ」という指示と「その引数を作るな」という指示が同時に効いている。**
恒真な gate かどうか以前に、承認済み API の必須引数が存在しない。

## 事実 2 — 「a12 が完走すれば恒真問題は解ける」という前回の見通しが外れた

R1 (a) を裁定したときの理由書にはこう書いてあった。

> 完走すれば正例が構成可能になり、R3 の恒真問題が自然に解消する。

**実測はこれを否定した。** `a12` の成果物自身が、こう宣言している。

```text
pilot_ready = false
remaining_unmet_pilot_prerequisites = [1, 4, 5, 6, 7, 8, 9]
```

`a12` の完走が満たすのは前提 **#3 だけ**で、#4〜#6 (受領証 schema の digest 束縛 /
approval manifest / resolver と receipt writer) は手つかずのまま残る。
だから `submit_pilot` が「通す」入力は依然として 1 つも存在せず、
**「正しく作った gate」と「中身を見ずに常に断る実装」を外から見分けられない。**

これは R3 (a)「受理集合が空の gate は land しない」が禁じた当のものである。
段 2 と段 3 の 3 子が独立にここへ到達し、レンズ A は
**「現在の scope の中で、この見分けのつかなさを消す設計は無い」**と断言した。

## 事実 3 — 同じ問いに、正反対の裁定が 2 つある

T-139 の Q1 / Q2 について、**選択肢が同じで結論が逆の裁定**が 2 つ記録されている。

| いつ | Q1 | Q2 |
|---|---|---|
| 2026-08-12 12:38 (第 2 束) | **機構を新設しない** | **機構を新設しない** |
| 2026-08-13 00:41 (第 7 束) | **(a) canonical decision を 1 本起こす** | **(a) 固定 envelope + namespaced projection** |

第 7 束は、第 2 束が却下した当の機構を選んでいる。
そして**本 wave への指示自身も両方を書いている** — Q1/Q2 を (a) としつつ
「D320 により承認機構は新設しない」とも書いている。

どちらが有効かで、この先の進め方が根本的に変わる。**親が一存で決められない。**

**【走行中の決着】** 受入 1 回目の後に取り込んだ main のエントリ 516 が、**第 7 束の読みで
[T-139] 項を確定させていた** — 「Q1 = (a) …。Q2 = (a) 固定 envelope + 役割別 namespaced
projection、alpha_reservation は exact 閉包に含めない。Q4 = (a) **裁定確定後に 1 session で
manifest + resolver + writer + validator + vectors を組む**。…
**次は Q1 の canonical decision 起草 → 投入経路 session。**」

**canonical 台帳が示すこの順序は、本 wave が実装可能性の側から独立に到達した順序と一致する。**
したがって K1 は「どちらが有効か」ではなく、**残った 1 点の確認**へ縮小する (下記)。

## 事実 4 — 前回の起票 R5 の前提が、現物と食い違っていた

R5 は `orchestrator/qualification/submission.py` の書き込みを
「単発 `os.write` で short-write 検査も read-back も持たない」としていた。

**現物を読むと、short-write ループも `fsync` も既にある。** 欠けているのは read-back 検証だけである。
R5 は「別タスクとして起票」で裁定済みなので進め方は変わらないが、起票の中身がずれている。

---

## K1. 「D320 により承認機構は新設しない」は、第 7 束 Q1/Q2 (a) にかかるか

**台帳側は既に決着している。** canonical worklog エントリ 516 が第 7 束の読みで確定させ、
順序は `Q1 の canonical decision → 投入経路 session` である。本 wave の実測もこれを支持する。
残るのは**指示に併記されていた 1 点の確認**だけである。

本 wave への指示は Q1/Q2 を (a) と書きつつ「**D320 により承認機構は新設しない**」とも書いていた。
この 2 つは、承認 manifest をどこまで作るかで衝突しうる。

- **(a) 第 7 束 Q1/Q2 (a) をそのまま実行する。D320 の但し書きは「bytes 級の凍結 pin を
  新設しない」の意味に留め、approval manifest そのものは作る** (親推奨)。
  **理由:** この順序でしか `submit_pilot` は D234 の承認済み契約どおりに作れない (事実 1)。
  D320 が見送るとしたのは論文主張に不要な粒度の provenance であって、
  **承認済み API の必須引数を作ることまで禁じてはいない。**
- (b) D320 を優先し approval manifest 系を作らない。
  → **その場合 pilot は構造的に永久に投入できない。** #4〜#6 が埋まらないので
  `submit_pilot` の受理集合は空のままで、ladder の実測は 1 本も取れない。
  これを受け入れる (= pilot 系列を畳む) なら一貫した判断だが、
  **「投入経路を作れ」という Q4 とは両立しない。**
- (c) 承認 manifest を「粗い provenance」水準まで簡略化して作る。
  → 親は評価できない。D320 の「粗い provenance で足りる」と D234 の 7 条件のどこで折り合うかは
  ユーザーの判断である。(c) を採るなら **D234 の (i)〜(vii) のどれを落とすか**を
  名指しで決める必要がある (落とすこと自体が受理集合を広げるため)。

## K2. Q4 の「1 session・同一 land」をどう扱うか

K1 が (a) なら、Q4 の 1 session 編成は前段 2 つが要るので成立しない。

- **(a) Q4 を「投入経路 wave」の定義として保持し、前段 2 wave の完了後に実行する** (親推奨)。
  Q4 の中身 (`submit_pilot` + driver + collector + 解除 decision + 束縛検査を同一 land) は
  そのまま正しい。**タイミングだけが早すぎた。**
- (b) scope を縮小し、schedule generator / PBS driver / collector だけを先に land する。
  → **親は反対する。** 敵対レンズ 2 本がそろって「発火点が無い」と判定した。
  呼ぶ側 (`submit_pilot`) が無いので、production では一度も動かないコードが増える。
  `DW-G04` (発火条件を書けない機能は設計メモに留める) に該当する。

## K3. 解除 decision を先に land してよいか

- **(a) 投入経路 wave と同一 land に据え置く** (親推奨)。
  Q4 の「解除 decision だけを先に land しない」を 1 bit も動かさない。
- (b) 先に land する。
  → 親は反対する。「止める文が canonical から消え、通す gate も未実装」という窓が開く。

**なお本 wave は解除 decision も投入経路も land しないので、この窓は開いていない。**

## K4. R5 の起票内容を是正するか

- **(a) 起票内容を「read-back 検証の欠落」へ是正する** (親推奨)。現物と一致させる。
- (b) そのままにする。
  → 親は反対する。存在しない欠陥を直す作業を後続 wave に渡すことになる。

## K5. 受入 lease の排他範囲を、他 wave の codex 子まで広げるか (走行中に実測した新規事項)

**事実。** 本 wave の受入全走を 2 回投入したところ、いずれも `test_codex_worker_launch.py` が
大量に赤になった (1 回目 10 件、2 回目 9 件、**落ちた node の集合は毎回異なる**)。
失敗の中身は `stop_reason='max_wall_clock_s'` = launcher の時間切れである。
**同ファイルの単独走は 114 passed / rc=0 / 6.80 秒で緑。**
走行中の並行 codex launcher 数は 5 本 → 8〜12 本と実測した。

これらのテストは実 launcher を spawn して wall-clock 上限つきで挙動を測る。
**受入 lease は他 wave の「受入走行」を排除するが、他 wave の「codex 子」は排除しない。**
この隙間が構造的に開いており、並行 wave が多い時間帯は受入が確率的に赤くなる。

- **(a) 現状維持。`DW-O18` の単独再走で切り分ける** (親推奨)。
  **理由:** 既に規律があり、本 wave はそれで正しく切り分けられた。
  lease の排他を広げると、codex 子を持つ全 wave が受入の間ブロックされ、並行度が大きく落ちる。
  実害は「受入 1 回あたり数分の切り分け作業」に留まる。
- (b) lease の排他範囲を codex 子まで広げる。
  → 並行度が落ちる。受入は 20 分級で、その間すべての wave の実装段が止まる。
- (c) 当該テスト群を負荷非依存な形へ作り替える (実 launcher を spawn しない)。
  → 受理集合が変わる。実 launcher の挙動を測る検出力を失う可能性があり、
  規律 2 の観点から親は一存で推奨しない。

---

## 本 wave が land したもの / しなかったもの

**land した:** 本裁定パッケージ、段 1〜4 の逐語、worklog / failures の記録。**実装面差分はゼロ。**

**land しなかった:** 解除 decision、`submit_pilot`、PBS driver、collector、束縛検査、
D264 のテスト期待値変更。

**pilot / 本走は依然として投入不可である。** ユーザー裁定は投入の禁止を解いたが、
D292 が要求する canonical decision がまだ台帳に無く、投入機構も存在しない。

## 次 wave への必須要件 (敵対レンズが実測した、落とすと壊れるもの)

投入経路 wave を立てるとき、次を brief に入れること。段 3 が実測で挙げた。

1. `a09` の seed を**省略せずに**逐語で固定する (64 文字 lowercase hex、ASCII として連結、
   `dec(j)`、raw digest 昇順、末尾 newline なし)。省略すると block 順と digest が変わる。
2. operational JSON の canonical serialization (exact key・配列順・UTF-8/LF・digest 対象 bytes) を
   固定する。固定しないと renderer の変異を帰属できない。
3. `submit_pilot` の署名は **D234 の `(*, binding: PreregBinding)` に合わせる**。
4. `FileRecord` と結果型の共有 API を先に決める (現物に無い)。
5. qsub 以外の注入境界を用意する (PBS・計算ノードを叩かずにテストできる形)。
6. 既存 Pegasus 資産と二重実装しない — qsub は `dispatch_compute.py` の `CommandRunner` 境界、
   durable writer は `qualification/submission.py` の protocol を再利用する。
7. `admission_registry.json` は **JSON key 単位**で追加する (行番号を実装契約にしない)。
8. 実装単位の所有を **file 単位**で素集合にする (directory 単位では衝突する)。
9. 既存固定テスト (`test_t139_preregistration_binding.py` / `test_t139_stress_check_simulation.py` /
   Pegasus 系) への波及を先に列挙する。
10. **D264 のテスト期待値は、実 binding の正例が通るまで変えない。**
