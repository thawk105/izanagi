---
schema: izanagi-spool-v1
ledger: decisions
authored: 2026-08-29
wave: dev-wave-t2067-floor-selection-rule
seq: 1
---

## {{D:floor-selection-earliest-eligible}}. 床値の選択規則は最早の適格 run とし、適格性の権威は再導出 bit に置く

**決定:** D1243 の選択規則を `earliest-eligible-official-run-id/v1` として実装する。同一
`(env_tag, proto8)` namespace の official floor result のうち、path の起動時刻が最小の適格な run
だけを g1 candidate へ渡せる。

適格性の判定は earlier result の自己申告 `eligible_for_refreeze` を読まず、共有 admission 台帳から
再導出する bit を権威とする。導出できない earlier は fail-closed で拒否する。namespace の絞り込みは
path の `proto8` だけで行い、earlier の内容から `protocol_sha256` を読まない。

**理由:**
- 自己申告を集合 membership の権威にすると、選ばれなかった run の 1 field を後から書き換えるだけで
  required run が動く。値を見た後の選択を閉じるという D1243 の目的を果たさない。
- 再導出 bit は既存の admission inspector が持つ機構であり、新しい台帳を作らずに済む。
  D1243 が禁じた署名・nonce・一回性台帳の新設に当たらない。
- 起動時刻は launch certificate 発行時点で確定するため値盲である。
- `proto8` 衝突は過剰包含 (拒否側) に倒れるため安全側である。内容を読む方式より自己申告面が小さい。

**却下した選択肢:**
- 最も早い result.json をそのまま必須にする — D1124 の再発である。resume した run は official path
  に result.json を書きつつ適格ではなく、resume は D1124 が守った途中死からの復旧経路である。
  これを競合に数えると「1 度落ちたらその protocol では二度と強い主張ができない」停止構造が
  artifact 側で復活する。同 D の逐語は、この型の厳密さが床値実測を 5 日停止させた実害を記録する。
- 最新の適格 run を使う — 値を見ながら run を足し、望む run が勝つまで停止時刻を選べる。
- 最初に発行された launch certificate で固定する — 途中死から測り直せず D1124 の実用目的を失う。
- 導出不能な earlier を不適格として読み飛ばす — 攻撃者が作りたい状態そのものを受理する。

## {{D:floor-selection-layer-placement}}. 床値選択の強制は candidate と launch に置き、loader は投影だけを検査する

**決定:** 選択 identity の検査は g1 candidate 生成時と `_launch_validate` の current 分岐にだけ置く。
静的 loader (`_verify_generation_semantics`) には投影 equality だけを置き、current build admission
policy を持ち込まない。historical reverify には選択規則を課さない。

candidate では selected の launch certificate を検証し、`started_utc` と path 起動時刻の秒一致を
要求する。これは全史検証が既に持つ同じ束縛の再利用であり、新機構ではない。

**理由:**
- loader に選択検査を入れると、candidate 側 validator が current policy を無条件に使うため、
  historical reverify が recorded semantics を選ぶ前に落ちる。規律 7 と D1245 に反する。
- 過去の g1 は規則制定前の成果物であり、現行コードとの差だけを無効化理由にしない (規律 7)。
- candidate 側の投影 equality は構造上恒真である。candidate の floor は検証関数の戻り値そのもので、
  非恒真なのは手作り generation を受ける批准側だけである。
- 起動時刻を検証しなければ、path の時刻はただの名前であり選択規則は装飾にとどまる。

**却下した選択肢:**
- generation document へ選択規則 field を足す — 単一 legal 値で dispatch を伴わなければ文字列存在
  検査にすぎず (D1242 が否定した型)、dispatch を伴えば汎用の選択規則 framework への第一歩になる。
- frozen generator blob の版文字列を exact 1 回検査する — 同じ理由。未使用リテラルでも通る。
- namespace 全体の tree と worktree の exact 一致を要求する — selected より後の未追跡 run 1 件で
  既存 consumer を止める過剰拒否であり、成果物の値も参照も変わらない。
- 手作り凍結オブジェクトを渡す経路まで層を重ねる — 型契約が任意コードへの偽造耐性を主張しておらず、
  一述語だけの部分強化にとどまる。

## {{D:floor-selection-claim-ceiling}}. 選択規則の実装だけでは non-certifying 上限を解除しない

**決定:** 本規則が landed しても D1241 の advisory / non-certifying 上限は維持する。追加で主張して
よいのは、(a) 導出適格性が真のより早い run が在るとき他を candidate へ渡すと拒否される、
(b) selected の path 起動時刻が launch certificate と秒一致する、(c) g1 の凍結床値が記録された
source の投影と一致する、の 3 点だけである。

**理由:**
- 値を見た後により早い run を削除してから凍結を作る経路は、台帳・署名を禁じた条件では閉じられない。
  現在の集合検査は「今ある集合」しか証明しない。
- 静的 loader は選択規則を強制しないため、そこだけを通る consumer の公開物は規則準拠を主張できない。
- 世代 2 以降は選択・投影の対象外であり、後続世代は床値と source を独立に変更できる。
- 起動証明書は整合的に再構成できるため、path 起動時刻は実時間順の証明にならない。

**却下した選択肢:**
- 規則の実装をもって上限を解除する — 上の 4 点が残るため過大主張になる。
- 上限を維持したまま残余を記録しない — 後続の着手者が同じ検討を繰り返す。
