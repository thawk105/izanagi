---
schema: izanagi-spool-v1
ledger: decisions
authored: 2026-08-17
wave: dev-wave-t190-failure-artifact
seq: 2
---

## {{D:launcher-diagnostics-sidecar}}. 受理集合を持つ producer の診断は、receipt を広げず独立 sidecar へ出す

**決定:** launcher のように受理判定を含む receipt を書く producer へ診断計装を足すときは、
receipt schema を広げず、同じ artifact dir へ独立した sidecar document を出す。
sidecar は checker authority にしない。receipt との対応は、**自分が receipt を公開できた run だけ**
`sealed` として exact bytes の SHA-256 を束縛し、公開競合の敗者は `foreign` と記録する。

診断は制御フローに副作用を持たせない。監視ループ中は in-memory の観測だけを行い、
ファイル I/O を増やさない。sidecar の書き込みは receipt 公開と全 late gate の後に行い、
**fsync しない** — 診断であって耐久性が要件ではなく、共有 FS の stall を
外側の test harness timeout へ持ち込まないためである。

**理由:**
- receipt の attempt / receipt field 集合は closed schema で、`accepted` の述語と
  外部 checker の期待に直結している。診断 field を混ぜると、観測を足すだけのつもりが
  受理集合の変更になる。絶対規律 2 の「正しさゲートを緩める変異」は、
  こういう「無害に見える追加」の形で入ってくる。
- 同じ path の receipt を 2 つの run が奪い合う経路が実在する。path と hash が一致しても
  同一 run の証明にはならない。**公開できたのが自分かどうか**が唯一の判別子である。
  これを記録しないと、別 run の receipt と診断を組み合わせた誤帰属が静かに成立する。
- 「値と述語を変えない」は「実時間上の受理集合を変えない」を含意しない。
  計装は wall gate より前に実時間を消費する。この 2 つを分けて宣言し、
  実時間側は保証しないと明記したうえで、追加の clock 取得と割り当てを最小にするのが正しい。

**却下した選択肢:**
- attempt record へ診断 field を足す — closed schema の変更であり、checker の外部期待と
  受理判定へ波及する。「診断を足すだけ」という説明と実態が食い違う。
- receipt の時計起点を動かして名前を揃える — 起点が version preflight を含むことは
  既存テストが明示 pin した意図的な不変条件であり、緩めれば規律 2 違反になる。
- 診断 write の失敗で launcher の rc を変える — 診断の障害が制御結果を汚染する。
  書けなかったことは stderr の 1 行で報告し、rc と receipt は不変にする。

## {{D:preserve-failing-test-artifacts-unconditionally}}. 失敗 artifact の退避は常時有効にし、環境変数の opt-in にしない

**決定:** 共有計算ノードでしか再現しないテストフレークの原因分離のために失敗時 artifact を
退避するときは、**退避を常時有効**にする。環境変数による有効化を設けない。
退避先の root も固定し、環境変数による上書きを設けない。

退避は原因判定に要る小集合 (receipt、診断 sidecar、attempt の stream と output、manifest) を
**先に**コピーし、残りを bundle 単位と run 単位の上限の範囲でコピーする。
退避処理の例外は捕捉し、**元の test failure を上書きしない。**

**理由:**
- opt-in は「肝心の走行で設定を忘れる」形で恒真化する。観測したいのは受入全走という
  年に何百回も回る自動化された経路であり、そこに人手の設定を挟むと機構は黙って沈黙する。
- 環境変数の上書きはこの repo の dispatch 経路では**そもそも計算ノードへ届かない。**
  test task の環境は閉じた allowlist で濾される。届かない knob を置くと、
  「設定したのに効かない」という新しい誤診断の種になる。
- 緑走行では 1 件も退避しないので、常時有効にしても定常コストは増えない。
  コストが出るのは既に失敗している走行だけである。
- 優先コピーは、容量上限に当たっても書き込みが失敗しても**原因判定の核が必ず残る**ことを保証する。
  これは「全部コピーできたときだけ役に立つ」設計との決定的な差である。

**却下した選択肢:**
- 環境変数 opt-in — 上記のとおり設定漏れが恒真化し、この repo では計算ノードへ届かない。
- `tmp_path` 全体の無差別コピー — 上限や容量エラーに当たったとき、
  何が残るかが運任せになる。優先順位を付けない退避は「残ったものがたまたま足りた」に依存する。
- 退避を非同期化して suite 後へ回す — 実装は重く、途中で job が落ちたときに何も残らない。
  優先コピーで同期のまま核を確保するほうが、同じ問題をより小さく解ける。
