## 変異カタログ

**以下は静的読解による設計上の期待であり、今回の実行結果ではない。** 対象は main `8fd2a2f5c`、CCBench pin `e9e477ca` の YCSB 経路。ファイル編集・テスト・build・bench は行っていない。

表中の source 略号は次の実ファイルを指す。行番号は patch 適用前の現行 source の位置である。

- **S** = `external/ccbench/cc/silo/transaction.cc`
- **M** = `external/ccbench/cc/mocc/transaction.cc`
- **SI** = `external/ccbench/cc/si/transaction.cc`
- **S / N / I / E**（verdict 列のみ）= `serializable` / `non-serializable` / `indeterminate` / `parse error`
- **復元対照** = 当該変更だけを戻した source と比較すること。並行走の操作列・schedule・件数まで同一になることは意味しない。
- **schedule 依存** = 異常を許す変更でも有限走で必ず発生するとは限らない。

正常な S の期待 S は、非空・完全な trace、他の integrity 違反なし、適切な source に基づく proof-surface assessment を前提とする。M の X/P 行は既存の `instr-mocc-lock-coverage.patch` を重ねた構成を前提とする。**素の pin の M は X/P 証明面が不足し、巡回なしでも I になる。**

既存 patch は指定どおり 16 本を個別行に残した。ただし、同じ機構の protocol 違い・条件違いは独立件数に水増ししない。例えば C01/C02、C03/C13、C04/C15/C16、C05/C14 はそれぞれ同族である。新規案を含む全 34 行は、これらを統合しても 20 以上の機構・意味の違いを持つ。

| ID | protocol | 既存再利用 or 新規 | 変更（既存記録は明示） | 外す／変える正しさ機構 | source の file:line | 期待される検出の層 | 期待 verdict | 発生条件 | 単一理由か | 帰属の確かめ方 |
|---|---|---|---|---|---|---|---|---|---|---|
| C01 | silo | 既存再利用 | `broken-silo-norw-validation.patch`：read 版変更時の abort を外す。**記録**：t4、50 keys、skew .9、rmw=true、max_ope=5、1秒で ON は G2 1310、OFF は certified。 | stale read の commit 防止 | S:453–460 | 巡回（G2） | N、未発生なら S | 共有 key の並行読み書き、t≥2。schedule 依存。t1 では通常発生しない。 | 主に巡回。全走の integrity clean は別確認 | 復元対照＋実際に変わった読版と閉路を raw R/W から導く |
| C02 | silo | 既存再利用 | `broken-silo-highkey-validation.patch`：C01 を key≥1000 に限定。**記録**：1m keys/t48/skew .9/rr50/rmw=false/max_ope10/3秒で G2 5、tuple200 の legacy 条件は certified。 | C01 と同じ。到達条件だけが異なる | S:453–460 | 巡回（G2） | N、対象外なら S | 高 key に競合が到達すること。schedule 依存 | C01 と同族 | 変更復元と、key<1000 の非発火対照 |
| C03 | silo | 既存再利用 | `broken-silo-lockskip-validation.patch`：非 INSERT の CAS 施錠を飛ばす。**記録**：t1 で cycle=0、X>0、I。 | writer の獲得被覆 | S:158–191、628–631 | X | t1 は I、巡回併発なら N | UPDATE が1回あれば t1 でも発火 | t1 で分離可能。多 thread は巡回・版重複もあり得る | 復元で X が消えることと、入口 lock 不在を照合 |
| C04 | silo | 既存再利用 | `broken-silo-early-unlock-validation.patch`：payload 更新前に版を publish して解錠。**記録**：入口でなく保持検査が発火。 | payload 更新までの lock 保持 | S:641–660 | X | I、巡回併発なら N | 非 INSERT 書込み。t1 でも保持違反を出せる | t1 は保持理由を分離可能 | 復元対照。入口 X=0 と保持 X>0 を区別 |
| C05 | silo | 既存再利用 | `broken-silo-permutation-erase.patch`：sort 後に1要素削除。README は `P size-changed` の検出実証を記載。 | write set の要素数保存 | S:408–432 | P | I、巡回併発なら N | 非空 write set。t1 でも可 | 小さい単発履歴なら P を分離可能 | 削除だけを戻し、sort 前後の要素数を照合 |
| C06 | silo | 既存再利用 | `broken-silo-permutation-swap.patch`：一方の record pointer を他方で上書き。README は size 不変で `P rcdptr-set-changed` と記載。 | record-pointer multiset 保存 | S:408–432 | P | 完成 trace は I が基本 | 異なる2要素以上。同一 pointer を二重施錠して abort／停止する可能性あり | P は独立に出るが、完走や他層の無発火は保証しない | 復元対照＋size と pointer multiset を別々に比較 |
| C07 | silo | 既存再利用 | `broken-silo-sort-nonswo.patch`：比較を `&a != &b` にする。**記録**：write set size≥16 で release/ASan とも hang。 | sort の strict weak ordering | S:408 | 検出なし=盲点（停止性）；破損時は P 等 | 完全な非空 prefix は S の場合あり。空なら I。停止自体に verdict はない | 多数の異なる書込み、max_ope≥16 が必要条件。UB の結果は保証不能 | 単一理由でない | comparator のみ復元。停止を巡回検出成功と数えない |
| C08 | silo | 既存再利用 | `broken-silo-trigger-misattr.patch`：lock conflict を node validation と誤記録。**記録**：misattr t4 は node-vali>0、verifier は緑のまま。 | abort 原因の意味的な正確性 | S:160–164 に骨格追加後 | 検出なし=盲点 | S | trigger 骨格＋集計計装、lock conflict。t1 非競合では未発火 | verdict は A の正誤を判定しない | 代入だけ復元。既存記録の原因分類を比較 |
| C09 | silo | 既存再利用 | `broken-silo-write-intent-erase.patch`：P 検査後に要素削除。**記録**：I 計装を持つ別 source では cycle=0、I のみで I。 | API が要求した write の完全性。C05 と欠落機構は同族だが観測位置が異なる | S:435–437 相当 | 現 pin は検出なし=盲点；記録は I | 現 pin の単純履歴は S | 非空 write set、t1・単発・blind write で分離。現 pin への patch 適用性は未確認 | 現 pin では I 行なし。複雑な履歴では他層もあり得る | 削除復元で要求 write が戻る。verdict は緑→緑もあり得る |
| C10 | silo | 既存再利用 | `broken-silo-write-intent-forge.patch`：先頭と同じ key/pointer の INSERT 要素を追加。**記録**：別 source の I 計装では I のみ。 | API が要求していない write の排除 | S:435–437、611–616 相当 | 現 pin は検出なし=盲点；記録は I | 単純履歴は S | 元の UPDATE が1個、t1。重複 W は同一 txn・同一版 | 他 txn の version dup とは異なる | 追加だけ復元。W 件数と API 意図を照合 |
| C11 | silo | 既存再利用 | `broken-silo-write-intent-opswap.patch`：UPDATE を DELETE に変更。**記録**：別 source の I 計装では missing/unexpected の I 2行。 | 操作種別と API 意図の一致 | S:435–437、612–614、668–686 相当 | 現 pin は検出なし=盲点；記録は I | 単発履歴は S | t1、1 key の単発 UPDATE。後続アクセスを除いて分離 | op は DSG で使われない。後続の失敗・停止は別 | op のみ復元。削除の有無は trace verdict 外で比較 |
| C12 | silo | 既存再利用 | `broken-silo-write-intent-ptrswap.patch`：2要素の pointer を交換。**記録**：別 source の I 計装では I 4行/txn。 | key と実 record の対応 | S:435–437、658–660 相当 | 現 pin は検出なし=盲点；記録は I | 条件を限定すれば S | t1、異なる2 key を同一 txn で更新。両方同じ commit 版になる | payload 誤配送は見えない。一般条件の単一理由性は未保証 | pointer 交換のみ復元。key ごとの実値との対応を確認 |
| C13 | mocc | 既存再利用 | `broken-mocc-lockskip-validation.patch`：validation の writer lock を飛ばす。**記録**：計装付き t1 は136,905 txn、X 1,927,227、cycle0/I；t4 は cycle3754/N。 | writer の獲得被覆。C03 同族 | M:990–1000 | X、巡回 | t1 I／競合時 N の可能性 | 計装付き、cold/default の書込み。hot でも canonical restore 後に欠落し得る | t1 は X 分離、多 thread は非単一 | 復元対照＋CLL と実 lock counter の対応 |
| C14 | mocc | 既存再利用 | `broken-mocc-permutation-erase.patch`：sort 後に pop。**記録**：P 221,097、全て size-changed、X0。 | 要素数保存。C05 同族 | M:990–991 | P | I | 計装付き、非空 write set。hot は削除要素の早期 lock が残り abort が増え得る | t1 の既存必須条件で分離実証 | pop のみ復元。P と commit 数を分けて評価 |
| C15 | mocc | 既存再利用 | `broken-mocc-early-unlock.patch`：入口検査後に解錠し、publish 検査後に直接再施錠。**記録**：t1 146,072 txn完走、入口0、保持2理由が各685,184。 | payload/publish までの lock 保持。C04 同族 | M:1158–1196 相当 | X | I、巡回併発なら N | 計装付き、balanced な既存 patch。t1 で分離 | t1 は保持2理由のみ | 復元対照。counter の均衡を壊す単純 unlock と混同しない |
| C16 | mocc | 既存再利用 | `broken-mocc-hot-update-unlock.patch`：hot update の早期 lock を外し、publish/abort 前で回復。**記録**：閾値0/t1 697,364 txn、X3理由各同数、P0/cycle0/I；閾値21/10は certified。 | hot 経路の lock 保持。C15 の経路別対照 | M:459、1069、1195 相当 | X | hot は I、cold/default は S | 計装付き、rratio=0、rmw=false、max_ope=1 の U に限定。t4 はschedule依存の併発あり | 保証は U のみ | 変更復元＋温度閾値0/21/10の到達対照 |
| C17 | silo | 新規 | validation 条件3の「他者が lock 中なら abort」を外し、版一致検査は残す。 | 他者の未 publish write と validation の競合排除 | S:465–473 | 巡回（G2） | N、未発生なら S | t≥2、各 txn が相手の書く key を読み、自分の別 key を施錠。双方が publish 前に検証する schedule | X/P は正常でも発生可能 | 条件3だけ復元。両者の genesis read による rw 2-cycle を手で導く |
| C18 | silo | 新規 | `tid_a` を `max_rset_` だけから作り、上書き対象の最大版を除く。 | key ごとの publish 版の単調増加 | S:567–579、191 | 巡回／version dup | 版逆転で閉路が出れば N、同版なら I、未発生なら S | rmw=false、異なる worker の履歴差。同一 epoch で古い worker が高版を上書きする schedule | 非単一。read set や mrctid が下限を補う場合は発火しない | 上書き前後の native 版を確認し復元。これは版順証拠の破損であり、閉路をそのまま実値履歴の異常証明としない |
| C19 | silo | 新規 | `maxtid` の epoch/tid を非 genesis の固定版にする。lock/latest ビット処理は維持する。 | 同一 key の版識別の一意性 | S:579–582 | version dup | I、巡回併発なら N | t1、同じ key への blind write を2 txn。競合不要 | この小履歴なら version dup を分離可能 | 固定化のみ復元。異なる txid の同一 key/版を照合 |
| C20 | silo | 新規 | native tuple へ publish する epoch/tid だけを、C/W に出した版と異なる未使用版にする。 | trace 版と実際に読む native 版の一致 | S:660、606–616 | orphan | I、巡回併発なら N | t1 の「書込み→別 txn の読込み」で可。未使用版を選び偶然の producer 一致を避ける | この小履歴は orphan のみ。W=C は維持される | native store の変更だけ復元し、R の版を産む W の不在を確認 |
| C21 | silo | 新規 | validation 成功後、`writePhase()` を呼ばずに commit 成功を返す fault を最後の txn だけで想定する。 | 成功 commit と trace/適用の対応 | S:706–709 | commit 証人 | 証人あり I、証人なしは残存 prefix が S の場合あり | 最後の成功 txn、先行完全 txn≥1。t1、非競合でも可 | 末尾・読取り専用で他の欠落理由を避ければ単一 | 呼出を復元。trace 外の成功件数と C 数の差が戻るか |
| C22 | silo | 新規 | read の二度目の TID を無条件に採用し、payload 再取得をせず retry を終える。 | payload と読版の整合した取得 | S:263–277 | 検出なし=盲点、場合により巡回 | 不整合値だけなら S | t≥2、payload copy と再読の間に更新。新 TID が validation まで維持される schedule | 古い stamp を残す変更とは異なる。別の依存異常は併発し得る | retry だけ復元。payload と stamp の食違いが消えるか。trace だけでは帰属不能 |
| C23 | silo | 新規 | memcpy する payload の一部を誤値にする。版・lock・read/write 集合は保持する。 | 書込み値の意味的正確性 | S:658–660 | 検出なし=盲点 | S | t1・単一 UPDATE で可。値の差が出る入力が必要 | 値以外を保存すれば単一 | payload 変更のみ復元。verdict は緑→緑で、値だけが戻る |
| C24 | silo | 新規 | node-map validation を外す。 | 範囲読みの構造変化・phantom 防止 | S:477–485、298–302、733–740 | 検出なし=盲点 | 現行 YCSB は S | YCSB は点読み/update のため対象機構に到達しない。phantom の実発生には範囲操作が必要 | YCSB 上の無発火は安全性一般の証明にならない | 復元しても YCSB 結果は同じ。範囲意味論は宣言範囲外と記載 |
| C25 | mocc | 新規 | canonical 順復元の解放・CLL 除去を飛ばし、逆順の lock を保持したまま追加獲得する。 | deadlock を避ける lock 順序 | M:834–888 | 検出なし=盲点 | 完全 prefix は S の場合あり、空なら I；停止自体の verdict なし | 計装付き、hot、t≥2、max_ope≥2、逆順アクセス。schedule 依存 | X は「必要な lock がない」を見るため、相互待機とは別 | canonical restore のみ復元。完了性と prefix の直列化可能性を区別 |
| C26 | silo | 新規 | own-write read の返却先を、その write buffer でなく旧 tuple payload にする。read set へは追加しない。 | read-your-writes | S:216–219 | 検出なし=盲点 | S | t1、同一 key の W→R、max_ope≥2。返却値の差が必要 | 外部依存グラフが同じでも局所意味論は壊れる | 返却先だけ復元。呼出側の値を比較。trace verdict は戻りを識別しない |
| C27 | silo | 新規 | 重複 update を無視する枝で、二度目の buffer 内容を誤って扱う。外部には最終 publish の1版だけを出す。 | 同一 txn 内の複数 write の値意味論 | S:529、547、611–616 | 検出なし=盲点 | S | 同じ key を複数回 update。YCSB の同一 worker 固定値では差が見えない場合あり | intermediate value の可視性を直接検出する行ではない | 重複処理のみ復元。異なる値を与えたときの最終値との対応で帰属 |
| C28 | si | 新規 | read の版選択で aborted/inflight の除外を外す。 | committed version だけを読む可視性規則 | SI:153–165 | parse 拒否 | E | v1 の C が1件でも出れば現状は検証不能。dirty read 自体は並行 update/abort が必要 | parser が先行。将来の orphan を現行検出と数えない | 選択条件復元で版の可視性は戻るが、v1 parse error は戻らない |
| C29 | si | 新規 | snapshot より新しい committed head に対する first-updater-wins abort を外す。 | snapshot 後の競合上書きの拒否 | SI:198–206 | parse 拒否 | E | t≥2、同じ key への競合更新。現行 parser では変更の有無を区別不能 | SI は元から write skew を許すので、それと混同しない | 当該 abort のみ復元。parse 成否を帰属指標にしない |
| C30 | si | 新規 | `publishMinQueuedCstamp()` を省き、GC の公開境界更新を欠落させる。 | reclamation に必要な queue 境界の公開 | SI:556–558、618–630 | parse 拒否；GC の結果自体は未確定 | C が出れば E。C 前に停止すれば判定不能 | GC が進む長さ・複数 thread。安全性違反か回収遅延かは GC 実装未読につき未確認 | 単一理由性を主張しない | 公開呼出だけ復元。現行 trace verdict で GC 正しさを評価しない |
| C31 | silo | 新規 | abort cleanup 後の backoff 呼出回数を有限の1回から2回へ変える。 | 再試行間隔のみ。CC 判定は維持 | S:27–47 | 検出なし=正しい | S | BACK_OFF 有効、abort があれば差が出る。非空で正常終了する走 | 正しさは保存。throughput・進行速度は変わる | 呼出回数のみ復元。両者 S が期待 |
| C32 | silo | 新規 | write set の順序を、全 worker 共通の逆向き全順序へ変更する。要素と SWO を保存する。 | lock 獲得順の選択のみ | S:408、145–193 | 検出なし=正しい | S | 同じ比較規則を全 worker に適用。異なる2 key 以上で差が出る | P/X と validation を保存 | comparator のみ復元。両者 S、P/X0 が期待 |
| C33 | silo | 新規 | validation 前に、特定の入力条件を満たす txn を保守的に追加 abort する。正常な cleanup 経路を通す。 | commit の許可集合を狭める | S:383、437–438、27–40 | 検出なし=正しい | S | 少なくとも一部 txn が commit する条件にする。t1でも可 | 全 abort にすると空 trace の I になるため対照条件を限定 | 追加 abort のみ復元。commit 部分履歴は両方直列化可能 |
| C34 | mocc | 新規 | 温度述語4箇所を `!(temp < threshold)` へ等価変形し、failed-verification fallback を保存する。 | hot/cold 選択述語の表現のみ | M:296、459、566、970 | 検出なし=正しい | 計装付き S；素の pin は I | 同じ整数型・引数、閾値境界を含む。rmw/threads 任意 | 論理等価なので意味の変化なし | 述語のみ復元。値ごとの真偽同値が独立根拠 |

既存記録の出典は `patches/README.md` の各 patch 節、特に C01/C02 は同ファイル:94–121、C05–C07 は:417–439、C08 は:443–477、C09–C12 は:506–531。M の既存4本は同ファイルの T-2294/T-2772 節による。今回 raw 実走 JSON を再監査したという意味ではない。

検出層の指定には **I、framing、genesis、missing txid** が含まれていないが、現行仕様の説明に必要なため本文では補っている。`model.py:503–515` は、非空なら**巡回ありを integrity 不良より優先して N**にする。従って X/P/orphan の行を、任意の多 thread 走で必ず I と断言してはいけない。

## 小履歴コーパス

記法は `g=(1,0)`、`v_i=(1,i)`、`Ti@v : R(x,u), W(y)` とする。W の版はその txn の commit 版。通常は txid を0始まりの密連番にし、C の宣言件数を実 R/W 件数と一致させ、E を付ける。key は説明用記号で、実形式では正しい hex に置換する。

各期待 verdict は、明記した破損以外の integrity が正常で、Silo の適切な proof-surface assessment が与えられることを前提とする。**手で求めた非巡回性だけから certified までを無条件に結論しない。** 以下の「被覆」は主として意味の被覆であり、既存 fixture と bytes が同一という意味ではない。

| ID | カテゴリ | 履歴（取引ごとの R/W と版） | 手で導いた辺（ww/wr/rw） | 期待 verdict と理由 | 既存 fixture で被覆済みか | 純増か |
|---|---|---|---|---|---|---|
| A01 | (a) 直列化可能 | T0@v1:W(x)；T1@v2:R(x,v1),W(y)；T2@v3:R(y,v2) | wr 0→1→2 | S。実行順0,1,2が直列順 | `g1_serial`、`g2_rmw_chain` が同種の連鎖を被覆。`g6_silo_serial_1thread` は実逐次対照 | 概念は既存、手製3段の独立説明として再利用 |
| A02 | (a) 直列化可能 | T0@v2:R(x,g)；T1@v1:W(x) | rw 0→1 のみ | S。commit stamp 順とは別に0,1と直列化できる | `g4_rw_no_cycle` | いいえ |
| A03 | (a) 直列化可能 | T0@v1:R(x,g)；T1@v2:R(y,g)。別 thread file に配置 | 辺なし | S。任意順で直列化可能 | `g3_readonly`。M 版の証明面条件は `g7_mocc_minimal_2thread` が別途被覆 | いいえ。改名・再配置対照の素材 |
| B01 | (b) write skew | T0@v1:R(y,g),W(x)；T1@v2:R(x,g),W(y) | rw 0→1、1→0 | N/G2。双方を相手より前に置く必要がある | `r1_write_skew`。実 negative の独立根拠は `r8_silo_broken_norw` | いいえ |
| B02 | (b) lost update | T0@v1:R(x,g),W(x)；T1@v2:R(x,g),W(x) | ww 0→1、rw 1→0。T0 の自己 rw は除外 | N/G2。T1 の初期版読みと write 順が両立しない | `r2_lost_update` | いいえ |
| B03 | (b) 長い巡回 | T0@v1:W(x),W(a)；T1@v2:R(a,v1),W(b)；T2@v3:R(b,v2),W(c)；T3@v4:R(c,v3),R(x,g) | wr 0→1→2→3、rw 3→0。短い閉路なし | N/G2、最短長4。直列順制約が環になる | `r9_dense_cycle4`。長3の別形は `r3_cycle3` | 長4は既存。任意長への同型拡張は設計上可能 |
| B04 | (b) 非最新版の直後版 | T0@v1:W(x)；T1@v2:R(x,v1),W(y)；T2@v3:W(x),R(y,g)；T3@v4:W(x) | ww 0→2→3、wr 0→1、rw 1→2、2→1 | N/G2。1↔2。rw を最新版T3へ誤接続すると閉路を失う | `r5_nonlatest_transitive` が同種。ww/wr/rw 混在は `r4_mixed_cycle` | 意味は既存、mutation に対応した手導出の明示 |
| B05 | (b) epoch を跨ぐ版順 | T0@(1,9):W(x)；T1@(2,1):W(x),R(y,g)；T2@(2,2):R(x,(1,9)),W(y) | ww 0→1、wr 0→2、rw 2→1、1→2 | N/G2。1↔2。epoch を捨てると x の順が反転し、2→1 を失って DAG になる | `r6_epoch_version_order`、`r7_epoch_rw_successor` | いいえ |
| B06 | (b) 非実行可能な分類対照 | T0@v1:R(y,v2),W(x)；T1@v2:R(x,v1),W(y) | wr 0→1、1→0。各 key に後続版なし、rw/wwなし | N/**G1c**。辺の定義上は wr の閉路。ただし相互に相手の未来版を読むため正常 producer の実行ではない | 22件にはなし。分類の合成辺単体 test は既存 | trace 入力として純増。正常 CC の異常再現とは数えない |
| C01 | (c) abort 不可視 | 実行：A が x を更新準備して abort；T0@v1:R(x,g)。trace はT0だけ | 辺なし | S。abort の局所 write は committed history に含まれない | 完全に同じ abort の対照 fixture はなし。射影結果は `g3_readonly` 相当 | abort 有無で同じ trace となる意味の対照が純増 |
| C02 | (c) abort 版の読込み | 実行：A が未 commit 版u=(1,7)を作り abort；T0@v8:R(x,u)。AのC/Wはなし | producer 不在で wr を導けない。後続Wもなし | I/orphan。直列化不能の閉路ではなく読版証拠の欠落 | `integrity_orphan` | oracle の意味は既存。abort 由来の説明が純増 |
| C03 | (c) 全 abort | 実行ではA,Bともabort。空の trace file、commit 証人0 | 節点・辺なし | I。非空の検証対象がない。空 DAG だから certified とはしない | 22件の fixture dir にはなし | はい |
| D01 | (d) 完全 frame の末尾欠落 | 実行：T0@v1:W(x)、T1@v2:W(y)。trace はT0だけ。証人を「なし／2」で対にする | 残存辺なし | 証人なし S、証人2なら I。txid0のみでは末尾欠落を内在的に推定できない | 22件にはなし | はい。証人の効き目を分離 |
| D02 | (d) 途中の txid 欠番 | T0@v1:W(x)、T2@v3:W(z) の完全 frame。独立なT1の frame を除去 | 辺なし | I/missing txid。外部証人なしでも0,2の穴が分かる | 22件にはなし | はい |
| D03 | (d) thread file 欠落 | thread0 にT0@v1:W(x)、thread1 にT1@v2:W(y)。後者の file 全体を除去 | 残存辺なし | 証人なし S、証人2なら I。thread file 欠落だけで常に欠番が出るわけではない | 22件にはなし | はい。末尾を所有する thread のケース |
| D04 | (d) E 行欠落 | T0@v1:W(x) のC/Wは正しく、Eだけ除去。証人1 | 辺なし | I/framing。commit 件数は一致しても終端保証がない | 22件にはなし。inline test 群と意味は重なる | fixture dir として純増 |
| D05 | (d) frame 内末尾欠落 | T0 のCはW2件を宣言。W(x)の後、W(y)とEが失われる。証人1 | 残存辺なし | I/framing。C件数証人だけでは R/W 完全性を保証しない | 22件にはなし。inline test 群と意味は重なる | fixture dir として純増 |
| D06 | (d) 証人一致と不一致 | 完全なT0@v1:W(x)、T1@v2:W(y)に、証人2／3を与える | 辺なし | 2ならS、3ならI。履歴 bytes が同じでも外部証拠が異なる | 22件にはなし | はい。証人を無視する実装を直接区別 |
| E01 | (e) genesis 読み | T0@v1:R(x,g)。x の producer は存在しない | 辺なし | S。初期値は明示的に許される producer 不在 | `g3_readonly` 等 | いいえ |
| E02 | (e) genesis への commit | T0@g:W(x)；T1@v1:R(x,g) | producer がいるので wr 0→1 | I/genesis commit。番兵へ commit しており、辺が非巡回でも認証不可 | `m1_commit_at_genesis` | いいえ。wrを落とさないことも期待に含める |
| E03 | (e) 番兵より前の commit | T0@(0,9):W(x) | 辺なし | I/genesis commit。`(0,9)<(1,0)` | `m1_commit_at_genesis` は同じ違反族。境界値としては別 | はい、境界の純増 |
| F01 | (f) 読み→書き | T0@v1:R(x,g),W(x)；T1@v2:R(x,v1),W(x) | wr/ww 0→1。自己辺なし | S。逐次RMW | `g2_rmw_chain` | いいえ |
| F02 | (f) 二重書き | T0@v1:W(x),W(x)；T1@v2:R(x,v1)。CのW件数は2 | wr 0→1。同一 txn の x は1版だけ。自己 ww なし | S。異なる txn の version dup ではない。中間値はこの表現にない | 専用fixtureなし。`g5_silo_real_prefix` の偶発的多重操作を独立根拠にしない | はい |
| F03 | (f) 二重読み | T0@v1:W(x)；T1@v2:R(x,v1),R(x,v1)。CのR件数は2 | wr 0→1を1本。平行重複を増やさない | S。読版が同じなので順序制約は増えない | 専用fixtureなし。`g5_silo_real_prefix` の偶発被覆のみ | はい |
| F04 | (f) 書き→読み | API履歴 T0:W(x),R-own(x)。producer の射影はT0@v1:W(x)、R-ownは追加されない。T1@v2:R(x,v1) | wr 0→1 | S。own-readは外部依存ではない。ただし返却値の正しさまでは分からない | 専用fixtureなし | はい |
| F05 | (f) 異なる txn の同版書き | T0@v1:W(x)；T1@v1:W(x) | 版から一意の producer を決められず、正常な ww 順を導けない | I/version dup。F02との違いはwriterが別txnであること | `m2_version_dup` | いいえ。F02との対が重要 |
| F06 | (f) 異なる版の二重読み | T0@v1:W(x)；T1@v2:W(x)；T2@v3:R(x,v1),R(x,v2) | ww 0→1、wr 0→2・1→2、rw 2→1 | N/G2。T2をT1の前後両方に置く必要がある | 22件に専用fixtureなし | はい |

F02 は parser/DSG の表現能力を試す合成入力であり、現行 Silo が二度の update ごとに W 行を出すとの主張ではない。S:529 は既存 write-set 要素があれば追加を飛ばし、S:611–616 は最終 write set を出す。F04 も、own-read の API 操作と trace の R 行を混同しないために両方を記した。

将来 fixture を追加する場合、**現行 `test_capacity_all_fixture_results_match_frozen_baseline` は trace を持つ fixture dir の集合を22件に固定しているため、追加だけでは通らず凍結一覧との整合更新が必要**である（`s1-facts.md` §D）。

## verifier 側の壊れ方との対応

「殺す」は、手で決めた期待と変異実装の結果が異なることを意味する。verdict が同じでも、分類や辺の違いを期待に含めなければ殺せないものを分けた。新しい gate・checker・台帳の導入提案ではなく、上記コーパスの識別力の整理である。

| verifier 側の壊れ方 | 対応する案 | verifier 外の根拠／識別点 | 限界・既存被覆 |
|---|---|---|---|
| 常に serializable | B01、B02、B03 | 手導出した閉路が存在する | 実データ側は `r8_silo_broken_norw` が独立に被覆 |
| 常に non-serializable | A01–A03 | 明示的な直列順、または辺がない | 実データ側は `g6_silo_serial_1thread` |
| 分類器が常に G2 | **B06** | 閉路の辺が wr のみなので G1c。**verdictだけでなく分類を比較する必要がある** | 正常な実行可能 YCSB trace だけでは区別不能。G0枝全体の被覆ではない。既存の合成 `CycleEdge` test も別にある |
| 版比較が epoch を無視 | B05 | `(1,9)<(2,1)`。tidだけなら x の版順が逆転し、閉路が消える | `r6_epoch_version_order` / `r7_epoch_rw_successor` と同種 |
| 長さ4以上の巡回を無視 | B03 | 短い閉路を持たない4-cycleを手で固定 | 現行は `r9_dense_cycle4` が被覆。D799当時の「未被覆」を現状へそのまま転記しない |
| framing violation を常に0 | D04 | R/W件数・commit件数は一致し、Eだけがない。唯一の不備を消すと偽緑 | D05も使えるが複数framing理由を併発させる |
| fixture hash／dir名で既知結果を返す | A01とB01等の**未登録の同型表現** | keyの全単射改名、密なtxidの置換、対応するthread配置変更で、手導出したグラフの同型性を保つ | 固定された有限コーパスだけでは任意のlookup実装を排除不能。既知hashだけを覚えた具体的変異への対照に限る |
| rw を直後版でなく最新版へ張る | B04 | 正しい1→2が1→3に置き換わると1↔2の閉路が消える | `r5_nonlatest_transitive` と同種。wwによる到達性があるから常に同じ結果、とはならない |
| rw があれば即 non-serializable | A02 | rwは1本あるが閉路なし | `g4_rw_no_cycle` |
| rw生成を全て落とす | B01 | 2本のrw以外に閉路を作る辺がない | `r1_write_skew` |
| ww生成を落とす | B02 | 0→1のwwがなければ1→0だけとなる | `g5_silo_real_prefix` はwwが別型と重なるため、この変異を区別しない場合がある |
| wr生成を落とす | B03 | 連鎖を結ぶwrを失えば3→0だけになる | B06も分類を含めて有効 |
| commit証人を無視する | D01、D06 | 同じ完全prefixに外部件数差だけを与える | D01では証人なしがS、ありがIという対が重要 |
| 全thread fileが存在すると仮定する | D03 | 観測prefixの密連番だけでは、末尾を持つfileの消失を検出できない | 外部証人なしでは、この情報不足を正常なverifierにも解消できない |
| missing txidを無視する | D02 | 独立keyなのでorphanやcycleは出ず、0,2の穴だけが残る | 22件のfixture dirでは未被覆 |
| orphanをgenesis扱いする | C02 | `(1,7)`のproducerが存在しない。番兵gとは異なる | `integrity_orphan` |
| 全producer不在をorphanにする | E01 | gは初期版として許される | genesis読取りを持つ既存緑で被覆 |
| 同一txnの多重writeを別版／version dup扱い | F02、F05の対 | F02はwriter1個、F05はwriter2個 | `m2_version_dup`だけではF02の誤検出を防げない |
| 二重readで辺を重複計上する | F03 | 制約は0→1の1個のみ | verdictは変わらない場合がある。辺数・集合まで期待に含める必要 |
| RMWの自己辺を作る | F01 | 自己のwriteは取引間の順序制約ではない | `g2_rmw_chain` |
| 二重readの後半だけを残す | F06 | 古い版読みのrw 2→1を失うと偽緑になる | 専用小履歴として純増 |
| genesis commitを許す | E02、E03 | commit版が予約された番兵以下 | `m1_commit_at_genesis`は主にE02 |
| gを読めばproducer探索を省く | E02 | 不正入力でも実在するT0→T1のwrを落とすべきでない | genesis integrityは残るのでverdictだけでは殺せない。辺も比較する |
| 空traceをserializable認証する | C03 | 検証対象txnが0件 | 空DAGの非巡回性と認証を分離 |
| X／Pを無視する | C03–C06、C13–C16の小さい完走条件 | t1・cycle0で証拠違反だけを残す | 小履歴カテゴリ表外の既存 `m3_mocc_lock_coverage` / `m4_mocc_permutation` が再利用可能 |
| abort原因Aの誤記録を見逃す | C08 | Aは集計でありverdict対象外 | **殺す対象のverifierバグではない**。宣言範囲外の対照 |
| 値破損／中間値可視性／phantom／livenessを緑にする | C07、C22–C27、F02/F04 | R/W版射影が同じなら、その外側の性質を判別できない | **verifierの欠陥とはしない**。phantomは既存 `p1_phantom_skew` が限界を固定 |

## 未確認・判断が割れる点

- **必読ファイルはすべて読めた。** Silo の validation・lockWriteSet・writePhase・TID生成・read retry・abort・GC、Mocc の validation・lock/CLL/RLL・writePhase・read retry・abort・GC、SI のsnapshot版選択・first-updater-wins・commit・abort・GC呼出を確認した。SI のGC内部実装は許可された読取範囲に含まれず、C30の安全性／回収遅延の帰結は未確認である。
- **34行は34個の独立な機構ではない。** 既存16本を各1行にする要請と、同機構を重複計数しない要請を両立するため、既存行を残して同族を明記した。C09はC05との欠落機構の重複もあるが、Pの前後という証拠到達性の違いを示す再利用資産として残した。
- **既存I検出の4本は現行pinのI検出証拠ではない。** `patches/README.md:506–531` はI計装が別sourceにあることを明記し、現行S:435–437にもI照合はない。`model.py:79–84`のcertification条件はX/Pであり、Iのsource evidence不在だけでは緑を止めない。
- Moccの既存X/P期待は既存計装patchを含む構成に束縛される。今回そのpatch本文は読取許可対象に含まれていないため、検査本文の逐語確認はしていない。説明・発火条件は必読READMEとbroken patchのcontextから確認した。素のM sourceにX/Pがないことは直接確認した。
- **巡回とintegrity違反が同時にあるとNになる。** 「XならI」「orphanならI」は巡回なし条件付きである。Mocc lockskipの既存t4記録は、まさにこの併発を示す。
- C01/C02/C17/C18/C22/C25の異常発生はschedule依存である。C03/C04等も多threadでは単一理由性を保証しない。復元対照が示すのは機構との関連であり、異なる並行走の結果差だけから唯一原因と断言しない。
- C18は版順の前提を壊すため、出たDSG閉路を「実payload履歴が非直列化可能」と直結させない。版逆転・版衝突・巡回・未発火を分ける必要がある。
- C07はUBと停止を含み、通常のverdictの4択に収まらない。完走しない実行にNを割り当てたり、既存timeoutをDSG検出成功に数えたりしない。
- **中間書きの他txnへの可視性を、現行YCSB sourceの1変更で確実に作り、しかもX/P等を発火させない案は未確定。** F02は中間値を表せない事実の対照であり、C27は局所の複数write意味論の対照に限定した。早期publishで無理に実現すると、C04等の保持違反やpayload/stamp不整合と混ざる。
- SIは最初のv1 C行でparse拒否される（`parse.py:321–330`、SI:539–552）。C28–C30を現行verifierのG2/orphan/GC検出力の件数に含めない。過去のSI 3,576 G2やSilo 1,310 G2は当時の記録として保持し、現行parserとの差を理由に無効化しない。
- `fixtures/README.md`には長4巡回について「どのfixtureも担っていない」というD799由来の記述と、現行`r9_dense_cycle4`の一覧が併存している。現状の被覆は後者を採り、前者は当時の緑赤対の限界として読む。
- source evidenceの存在は前処理条件・到達可能性・実際の発火を証明しない（`model.py:233–243`）。また`g5_silo_real_prefix`のgolden期待を、verifier外で独立に決まったoracleとして数えない。
- traceの値非記録、abort不可視、predicate不可視という限界は、同じ射影を持つ異なる実行を区別できないという情報上の制約である。abort版読みがorphanになる場合も、「abortしたwriterを特定した」とまでは言えない。

## 総括

- 既存16本を残し、新規18案を加えた34行の設計案とした。同機構の条件違いは独立件数に水増ししていない。
- 検出期待を、G2巡回、integrity・証拠不足、宣言範囲外、正しさを保つ対照に分けた。
- 正しい対照はbackoff、全順序変更、保守的abort、等価温度述語の4案を用意した。
- 小履歴は各カテゴリ3〜6行とし、辺・版・欠落箇所から期待を手で説明した。
- 純増の中心は欠損trace、同一txnの多重操作、非G2分類対照と、外部commit証人の有無の対である。
- SIの現行v1拒否、Moccの計装前提、I計装のpin外という制約を検出実績から分離した。
- 緑は観測された点読み書きの版履歴と証拠条件に対する判定であり、値・phantom・公平性・未観測実行の保証ではない。
- 本文は設計のみであり、実trace取得・変異実走・fixture実装・容量実測は行っていない。