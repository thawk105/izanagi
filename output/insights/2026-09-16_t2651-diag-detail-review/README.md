# [T-2651] 診断本文保持の敵対レビューと変異 harness 本走

- wave: dev-wave-t2651-diag-detail-review (branch `worktree-dev-wave-t2651-diag-detail-review`)
- 基準: local main `d97c423bdd14e0b416cb4f585d350e6c2b251287` (着手直前)
- 対象: 直前 wave (worklog 1515) が着地させた 2 commit
  `affd2a105` (拒否時に condition gate の red record detail を失わせない) と
  `c185b9fd4` (診断本文の切り詰めで先頭と末尾の両方を残す)
- 変異走行時の repo HEAD: `f0b388a7f405173b2d9befe455a1056cea29e460`

## 1. この wave が何をしたか

直前 wave は段 3 のレンズを**走行前の plan と brief**に当てたため、着地した実装差分を見ていない。
変異 harness の本走も行っていない (前 wave insight §7・§8 が自ら「未実施」と記録している)。
本 wave はその 2 つの残件だけを閉じた。

- 段 3 のレンズを**着地実装差分そのもの**へ取り直した (異なるレンズ 2 本、read-only)
- 登録済み変異 M1-M3 / M5-M7 の harness 本走を行った

**実装差分は作っていない。** レンズ 2 本とも実装の must-fix を確認できなかったためである。

## 2. 研究前進としての位置づけ

本 wave は official 床値 campaign (T-1851 / T-2650) を**直接前進させない**。
本 wave の価値は間接的である — 床値 campaign が拒否停止したとき、gate 専用の isolate worktree
(`/scr`) が job 終了で消えた後も拒否本文が証拠として残るかどうかを支える機構について、
残っていたレビューと変異検証を閉じた。

この位置づけはレンズ luna の所見 P1 を受けて段 4 で訂正したものである。段 1 brief は当初
「official 床値 campaign を前進させる」と書いていた。

## 3. レビュー結果 — 実装の must-fix はゼロ

| レンズ | 攻撃面 | 結論 |
|---|---|---|
| sol | 正しさ境界と受理集合 (規律 2 への攻撃) | 受理集合を広げる反例・fail-closed を倒す到達可能な経路を確認できず |
| luna | 証拠の復元可能性と byte 予算の実効性 | 現行定数での byte 会計・slice 重複・`[-0:]` に実装 must-fix を確認できず |

**両者とも根拠の種別を「読解」と明記している。** read-only sandbox のため test を走らせられず、
実走による証明ではない。実走は親が行った (§6・§7)。

real と裁定した主な所見を挙げる。裁定の全文は `verbatim/s4-ruling.md`。

### 3.1 機構が実際に保存しているもの (luna E1)

上流 `condition_meaning_gate.py:1563-1576` が既に stderr を**末尾 500 bytes** へ切っている。
したがって driver が拒否本文へ運ぶのは**加工済み `evidence.detail` の全文**であって、
raw subprocess 出力の全文ではない。前 wave の commit message にある
「実 rc と実 stderr が復元できた」は、この区別を付けずに書かれている。

保存ログ `output/insights/2026-09-15/t1851-c3c-official-floor-run/evidence/999102-floor-driver.stderr`
の argv には `original=846 bytes` の切り詰め印が実在する。

### 3.2 sha256 が保証する範囲 (luna E2)

digest の対象は次の bytes である。

```python
shlex.join([detail]).encode("utf-8", errors="backslashreplace")
```

raw stderr でも raw argv でも、未引用の `detail` でもない。
**別途得た完全な detail 候補を同じ変換に通せば照合できる**が、両端からの全文復元、
失われた stderr 前半の照合、元 argv の再構成には使えない。
孤立 surrogate を含む入力では `backslashreplace` が非単射になるため、digest が保証する同一性は
あくまで**変換後 bytes**についてである。

### 3.3 拒否本文全体に上限は無い (luna B2)

`_CONDITION_DETAIL_LIMIT_BYTES` (4228 bytes = 実測 1057 × 4) は **1 record あたり**の予算である。
構造上限は 4 request × 2 arm = **8 record**、detail 合計で最大 **33,824 bytes**。
さらに理由一覧・record prefix・改行が加わる。全体への共通切り詰めは無い。
これは実機で 8 件を観測したという意味ではない。

### 3.4 「non-green はすべて拒否本文へ入る」は誤り (sol S3)

`supply=green / meaning=unestablished` の組は admission が**受理**するため拒否本文を作らない。
別の red によって family が拒否された場合には、その unestablished record も本文対象になる。
gate 本体の変更要求ではない。

### 3.5 rc 不変は無条件保証ではない (sol S4)

`BaseException` を捕捉しないという明示契約の帰結として、整形器が `SystemExit(0)` を送出すれば
rc=0 で抜けうる。ただし実際にそれを生成する経路は未発見であり、実装欠陥ではない。
「rc 不変」を無条件の保証として記載しない、という記録上の限定である。

### 3.6 nit (must-fix にしない)

- 切り詰め結果は shell token として可逆でない (luna N1)。shell token として解析する
  production consumer は未確認であり、成果物影響を確定できない
- 短文 surrogate は byte 判定で escape されるが返却値に残る (sol N1)
- 短文に digest が無いのは仕様どおり (luna N2)
- `test_s1_direct_comparison.py:345-361` は green 時に helper を呼ばないことの直接検査ではない
  (sol N2)。検査の射程の注記

## 4. 前 wave の記録への追記 erratum (luna W1)

前 wave insight `output/insights/2026-09-15/t1851-c3c-official-floor-run/README.md` §7 の
「3 回の実機走行で M1〜M3 と M5〜M7 が守る性質を production 経路で直接観測した」は過大である。

保存ログの照合で分かったこと。

- 1 回目 (`998882`) の保存拒否本文に digest は無い。「いずれも全文 sha256 の印つきだった」は不正確
- 3 回目 (`999102`) の digest は **argv の引用整形後全文**に対するもので、
  本 wave が検査している外側の detail digest ではない
- M2 / M3 / M5 / M6 は 3 走行のいずれでも発火していない。掲載された拒否 record は 3 回とも
  `BACKOFF_FIXED:supply-effectuation:preprocess-failed` の 1 件だけである

したがって 3 走行が production 経路で直接観測したのは **M1 が守る性質だけ**である。

**絶対規律 7 に従い、過去の判定は追記でのみ訂正した。** 前 wave の本文は書き換えず、
同 README の末尾へ追記 erratum を置いた。§7 が自ら「harness による kill 判定の代替ではない」
「未実施はそう書く」と記録している点は正しく、そこは訂正していない。

## 5. 変異事前登録 v2

### 5.1 anchor (実測で一致数 1 を確認)

| # | 変異の意図 | 行 |
|---|---|---|
| M1 | 拒否 message から detail を落とし reason code だけに戻す | 341 |
| M2 | red record が複数のとき 1 件目の detail だけ載せる | 341 |
| M3 | detail 整形が例外を送出しうる形にする | 352 |
| M5 | 切り詰め時に末尾を落とす | 291 |
| M6 | 切り詰め時に先頭を落とす | 290 |
| M7 | 省略 bytes 数または全文 sha256 の印を落とす | 283 |

**M4 は前 wave が単一理由性に絞れず取り下げ済みで、復活させていない。**
anchor の逐語は `mutation-final-spec.json` を正本とする。

### 5.2 runner の対象集合

`orchestrator/tests/test_s1_direct_comparison.py` **単独**とした。

`orchestrator/tests/test_s8b_oracle_manifest.py:88-89` は `s1_direct_comparison.py` の
live byte sha256 を golden 逐語で pin しており、同 file への変異を一律に赤にする。
`DW-M03` の「過剰決定なら冗長 gate と明記して単独変異の証拠から外す」に従い除外した。
**当該テストを無効化したのではない** — 受入全走では通常どおり走る。

この除外理由は**読解による存在の同定**であって、「repo 全体に masking が他に無いこと」の
証明ではない (sol B3)。構文を壊す変異なら hash 検査へ到達する前に停止しうるため、
「任意の変異が必ず同じ hash 理由で赤」という言い方も強すぎる。

### 5.3 kill と diagnostic sensitivity pin の分類

`DW-M03`「kill は受理集合か fail-closed 挙動が期待方向へ変わったときだけ数え、
診断文字列だけの赤を kill にしない」および `DW-M08`「受理集合を変えず構造化シグナルだけを
pin する変異は kill でなく diagnostic sensitivity pin へ別枠記録する」に照らし、
**6 変異すべてを diagnostic sensitivity pin に分類した。kill は 0 件である。**

M3 については親が消費側を読み直して裏取りした。M3 を当てると整形器の `RuntimeError` が
`DriverError` を置換して `_condition_records_for_genome` を抜けるが、消費側
(`s1_direct_comparison.py:1320-1327`) は `except DriverError: raise` に続けて
`except Exception` を持ち、`_is_transient_prepare_failure()` が `RuntimeError` に対して
`False` を返すため再送出する。`main()` (同 1409-1415) は `EXIT_REFUSED` を返す。
**終端 rc は変わらない。**

M3 が同時に pin しているのは「拒否が `DriverError` として届き、retry 分類器を迂回する」という
構造的性質であり、その性質が終端挙動を変える入力 (整形器が `OSError` 族を送出し、かつ
session 未開始) は現行実装では到達不能である (読解)。

**kill 0 件は失敗ではない。** 着地 commit が主張した「gate の受理集合・reason code 語彙・
admission 判定・rc・green 経路の bytes は変えていない」が、変異の側からも裏付けられたということである。
`DW-M02` の「所見ゼロを変異なしで緑と数えない」という要求は、6 変異の検出実測で満たしている。

### 5.4 単一理由性の注記

- **M1** は本文保持と、注入した割込みの伝播検査の**両方**を同時に壊す。
  「本文保持だけを壊す」という厳密な説明には収まらない。期待 node にはその両方が含まれる
- **M7** の 4 node は 4 性質の独立証明ではない。`omitted` node は算術比較より前の
  正規表現一致で止まるため、「省略数の誤りも検出した」とは数えない
- **M2** の fixture は両 arm が同じ `compiler-failed`・同じ detail であり、
  arm 間で detail を取り違える欠陥はこの fixture では識別できない
- **M5 / M6** は `omitted` が残存量から再計算されるため、計数・digest・予算まで
  独立に壊すとは数えない

## 6. 変異 matrix (実測)

走行は 2 段構成。`DW-M07` の「KILLED 期待で node 空の spec は起動前に中止するので probe は
全件 SURVIVED で登録し観測 node を集める」に従った。

### 6.1 probe (全件 SURVIVED 登録)

- spec: `mutation-probe-spec.json` (sha256 `ae9588f449db683626177d7e0528dfb1e56049c1c237371ee867ee009f23b9b8`)
- 出力: `mutation-probe-out.json` / sidecar `mutation-probe-attempt.json`
- baseline: **PASSED** (rc=0、`failed_nodes` 空)
- 結果: **MISMATCH 6 / SURVIVED 0 / TIMEOUT 0 / PARSE_ERROR 0**

SURVIVED 0 件は「登録した 6 変異がいずれも現行テストに検出された」ことを意味する。
観測 node の**件数と顔ぶれ**は段 2 plan の静的予測と完全に一致した。

**probe が必要だった理由は日本語 param の表記である。** plan は pytest の既定 escaping を
仮定して `共通.hh` と予測したが、harness が記録する正規化形は `/u5171/u901a.hh` だった。
`DW-M08` が「同形式へ正規化した記録 node との完全一致だけを KILLED とする」と定める以上、
静的予測のままでは本走を通せない。
本走 spec の `expected_nodes` は probe の `failed_nodes` から機械生成し、人手で書き写していない。

初回結果は消さず、本 insight と `mutation-probe-out.json` に残した (`DW-M02`)。

### 6.2 本走

- spec: `mutation-final-spec.json` (sha256 `d459ab2192366f520bc0acd025d5c9f746540c1e47293a2082ef78ade7b4cfb2`)
- 出力: `mutation-final-out.json` / sidecar `mutation-final-attempt.json`
- repo HEAD: `f0b388a7f405173b2d9befe455a1056cea29e460`
- runner: `python3 tools/run_tests.py --force-dispatch -q -rf orchestrator/tests/test_s1_direct_comparison.py`
  (harness が `-p no:cacheprovider` を付加)
- runner_mode: `dispatch` (計算ノード)

| 判定 | 件数 |
|---|---|
| baseline | **PASSED** (rc=0、31.93 s) |
| KILLED | **6** |
| matching (期待 node 完全一致) | **6** |
| SURVIVED | 0 |
| MISMATCH | 0 |
| TIMEOUT | 0 |
| PARSE_ERROR | 0 |

| # | 期待 node 数 | 判定 | 所要 |
|---|---|---|---|
| M1 | 7 | KILLED (完全一致) | 29.1 s |
| M2 | 3 | KILLED (完全一致) | 309.9 s (queue 待ちを含む) |
| M3 | 1 | KILLED (完全一致) | 30.9 s |
| M5 | 2 | KILLED (完全一致) | 36.0 s |
| M6 | 2 | KILLED (完全一致) | 33.5 s |
| M7 | 4 | KILLED (完全一致) | 29.8 s |

**分類は §5.3 のとおり、6 件すべて diagnostic sensitivity pin である。kill は 0 件。**
harness の `KILLED` は「期待した node 集合がちょうど赤になった」という検出の記録であり、
本 wave はそれを正しさ防壁の kill として数えない。

### 6.3 復元の検証

本走後、wave worktree の `git status --porcelain --untracked-files=all` は **0 行**。
`orchestrator/campaign/s1_direct_comparison.py` の sha256 は
`c7364f2da5decbd6b4d44041385edc60feaf9c83638b73f178cfe4c9adff1bbe` で、
`test_s8b_oracle_manifest.py:89` の golden pin と一致する。**byte 完全に復元された。**

## 7. 検査

| 検査 | 結果 |
|---|---|
| `check_wave_startup.py --mode fresh --forbid-worktree-handoff --external-handoff` | rc=0 |
| `check_codex_output.py` (plan / レンズ sol / レンズ luna) | 全 rc=0 |
| `check_ai_provenance.py --message-file` (段 4 commit / probe commit / 本記録 commit) | 全 rc=0 |
| `check_ai_provenance.py` 全史 (段 4 commit 後) | rc=0、10466 件、新規違反なし |
| 焦点走 baseline (`test_s1_direct_comparison.py` + `test_s8b_oracle_manifest.py`) | rc=0 (計算ノード dispatch `1110.nqsv`、Elapse 20 S) |
| `s8b_holdout_freeze search` (三軸語・placeholder 全 gate 走査) | rc=0、hit なし |
| 変異 probe | baseline PASSED・MISMATCH 6・SURVIVED 0 |
| 変異本走 | baseline PASSED・**KILLED 6 / matching 6**・SURVIVED 0・MISMATCH 0・TIMEOUT 0 |
| 変異後の復元 | porcelain 0 行・driver sha256 が golden pin と一致 |
| `check_docs.py` | 記録 commit 直前に実走 |
| `spool_fold.py --dry-run` | 記録 commit 直前に実走 |

受入全走は `DW-O12` に従い、記録 commit と段 8 の完了後に投入する。
緑の受入は現行 worklog の慣行どおり本文へ書かず、receipt を証拠とする。

## 8. 到達範囲と非保証

- 本 wave は **official 床値そのものを取得していない**
- レンズ 2 本の所見は**すべて読解**であり、実走による証明ではない。
  実走は親の焦点走・変異走行・受入全走だけである
- 6 変異の検出は**証拠復元可能性の十分条件ではない** (luna P2)。
  上流が stderr 前半を捨てても既存の assertion は成立し、中央に原因行が消える入力も
  両端・省略数・digest・予算という既存性質と両立する
- **重要行が省略された中央に入る確率は評価不能である** (luna B1)。
  1057 bytes は 1 回の観測に由来し、母集合を覆う標本ではない。低いとも言えない
- 次の性質は**未被覆**である (観察として記録。本 wave では登録を追加しない)
  - raw process 証拠から掲載本文までの全文保存
  - 省略した中央の重要行の復元
  - 4228 / 4229 bytes の厳密な境界
  - 長文を複数 record の拒否本文へ接続する経路
  - digest **値**の改変に対する検出力 (M7 は欄の削除だけを見る)
  - surrogate・引用境界・出力先 encoding
- 変異 runner を単独 file へ絞ったため、この結果は
  **通常の prepare 経路が実関数へ正しく接続することの検証にはならない** (sol B2)。
  通常の driver テストでは `_condition_records_for_genome` が autouse fixture で置換される

## 9. scope 外として実装しなかった real 所見 (裁定パッケージ候補)

ユーザーが「仮想リスク向けの gate・検査・台帳・一般化の追加は scope 外」と明示しているため、
次はいずれも real だが実装せず、新規 T も立てていない。

- 上流 `condition_meaning_gate` の 500 bytes 切り詰めによる raw stderr 前半の喪失 (luna E1)
- 同型欠陥を持つ兄弟 driver 14 箇所への横展開 (`backoff_sweep.py:225`、`p3_kickoff.py:94`、
  `p3_s4_loop_sort.py:137` ほか。前 wave が非展開と裁定済み)
- 未被覆 6 性質に対する変異・検査の新設 (luna)
- `_CONDITION_DETAIL_LIMIT_BYTES` の母集合に基づく再設計 (luna B1)

## 10. 逐語

- `verbatim/s1-brief.md` — 段 1 brief
- `verbatim/s2-plan.md` — 段 2 plan (codex read-only)
- `verbatim/s3-sol.md` / `verbatim/s3-luna.md` — 段 3 敵対レンズ 2 本
- `verbatim/s4-ruling.md` — 段 4 裁定
