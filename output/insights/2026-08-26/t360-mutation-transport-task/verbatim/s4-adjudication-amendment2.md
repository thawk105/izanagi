# 段 6 レビュー後の裁定 (2026-08-26 07:00 JST)

`s4-adjudication.md` と `s4-adjudication-amendment.md` の修正。3 つあわせて段 4 裁定の正本とする。

## B-0. 親の裁定に内部矛盾があった (レビュー B 所見 1、real)

裁定 §3 は「bundled 経路は『task 経路の内側』という別文脈で `--attempt-out` を許す」と書いた。
一方、実装子 B への指示では「`--attempt-out` の dispatch 専用制約を緩めるな」と明示した。
**この 2 つは両立しない。** 実装子 B は指示どおり緩めておらず、実装は指示に忠実である。
誤っていたのは親の裁定文である。

結果として bundled 経路は次の二択になる。

- attempt pair を残す → wrapper が rc=125 で停止し ledger が出ない
- attempt pair を落とす → 走るが attempt 対応の証拠を失う (D131 #2 が要求するもの)

**裁定: 本 wave では緩めない。** attempt 契約を bundled 文脈だけで緩める設計
(task 内部からだけ立つ marker を設け、compute site と marker の両方が真のときだけ
local attempt recorder を許す) は、変異 harness の受理集合を変える。
D96 の手続 (受理集合を変える改修は decision 記録 + 境界テストを同じ変更単位で) を要し、
かつ「変異 harness / runner の契約を変えない」という本 wave の不変条件に触れる。
**ユーザー裁定へ返す。**

## B-1. D131 #2 は bundled 経路について閉じていない (レビュー B 所見 4、real)

上の帰結として、**bundled 経路は D131 #2 (永続 transport 証拠の attempt 対応) を満たさない**。
本 wave が納めるのは「束ねて走る transport」であって「attempt 対応証拠を備えた恒久 transport」
ではない。**worklog と decisions にこの限定を逐語で書く。**
「D842 を実装した」とだけ書いてはならない。

## B-2. D131 #1 も direct harness が残る限り閉じていない (レビュー B 所見 3、real)

裁定 §2 は「wrapper が共有 lock を持つので #1 の lock 面はここで閉じる」と書いたが、
同じ裁定で harness 直接起動を許している。**直接起動は wrapper の共有 lock を通らない。**
両立しない。**#1 は task 経路についてだけ閉じており、repo 全体では閉じていない。**
この限定も逐語で書く。

## B-3. 束ね効果の実測値は条件付きである (レビュー B 所見 9)

静的計数は次であり、レビュー B が file:line で裏取りした。

| 経路 | outer | collection | baseline | 変異 N 件 | 合計 |
|---|---:|---:|---:|---:|---:|
| 従来 (wrapper/harness dispatch) | 0 | 1 | 1 | N | N+2 |
| bundled + inner local | 1 | 0 | 0 | 0 | 1 |

**削減は eligible な入力に限る。** runner 実行経路を含む変異、selector を要する走行、
attempt 証拠を要する走行は eligible でない。
**「変異本走を 1 ジョブへ束ねた」と無条件に書いてはならない。**

## B-4. 私の「受理集合は同じ」は end-to-end では誤りだった (レビュー A 所見 5、real)

`s4-adjudication-amendment.md` A-1 に「hook 変更を見送っても受理集合は本 wave 以前と同じ」と
書いた。**hook 単体の判定集合については正しいが、end-to-end では誤りである。**
`generic` task を足したこと自体が、計算ノードで実行できるものの集合を明確に広げている。
訂正する。正しい主張は次の 2 つに分ける。

- hook の判定集合は本 wave で変えていない (hooks/ を 1 byte も触っていない)。
- dispatcher の受理集合は `generic` の追加により広がった。これは D895 の裁定に従った意図的な拡張であり、
  安全性は hook ではなく dispatcher の compute 限定 gate (二重 bnode gate) が担う。

## B-5. 段 6 fix 3 巡目で直すもの (DW-O16 の上限)

| # | 出所 | 内容 | 重大度 |
|---|---|---|---|
| F1 | A-2 / B-5 | argv policy の迂回: 短 option cluster (`-qkselected`)、`@argfile`、`-o addopts=...` | 正しさ防壁 |
| F2 | A-1 | 公開 `--job-run` 3 引数形が呼び出し側申告の hash を受理する | 正しさ防壁 |
| F3 | B-2 | mutation argv の構造検証が無く、`--runner-mode dispatch` が通って job を無駄にする | 受理集合 |
| F4 | A-3 / B-6 | `check_docs.py` の alias 検査が comprehension を通す | 実効性 |
| F5 | A-6 | legacy v1 正例テストが凍結集合自身を fixture にしている (恒真) | 実効性 |
| F6 | A-7 | hook 回帰テストが揮発する日本語診断文を固定している | nit |

F1 は最優先である。変異走行が裁定した test 集合の部分集合で走れば、
KILLED / SURVIVED と ledger 集計値が変わる。絶対規律 2 への直撃である。

## B-6. 直さず裁定へ返すもの

- B-0 の bundled marker 設計 (変異 harness の受理集合変更)
- D131 #1 の repo 全体での閉じ方 (direct harness の legacy lock)
- hook の綴り依存 (`amendment` A-1 のとおり実装不能)
- `DW-M07` の byte 予算に条件を収める方法 (現在は runbook 側に置いている)
- `env_allowlist` を最終 child env 全体の契約へ広げること
