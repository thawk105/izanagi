# [T-1641]+[T-755] checker report を受領証へ束縛した — 転記と証拠の鎖は別物である

- 日付: 2026-08-25
- wave: dev-wave-t1641-t755-report-binding (branch `worktree-dev-wave-t1641-t755-report-binding`)
- 起点の裁定: D779 (ユーザー裁定。択 (a)。TRACE=0 の値を正式材料へ上げる前に、pilot の final receipt と
  job-result が checker report の path・SHA-256・schema・guarantee を束縛する)
- 併せて閉じた項: [T-755] の残件 (pilot script が選んだ verifier interpreter の実体 path を receipt へ記録する)
- 一次資料: `output/insights/2026-08-24_t1582-mocc-trace0-pilot.md`、
  `output/insights/2026-08-25_t1584-trace0-identity-holes.md`、D779、D780
- 成果物 commit: `f52afa8a` (束縛の実装)、`6c7fe98c` (fix 第 1 巡)、`298b35e0` (fix 第 2 巡)、
  `98c6e6fd` (sidecar 単独改竄の負例)

## 1. 依頼された 4 項目は転記でしかなく、それだけでは D779 の理由を満たさない

D779 は「path・SHA-256・schema・guarantee を束縛せよ」と 4 つの field を名指している。素直に読むと
report の該当 field を受領証へ写す作業である。段 2 のプランもその形で起草した。

段 3 の敵対相談 2 本が、異なるレンズから同じ結論に到達した。**report が自分で名乗った schema と
guarantee を受領証へ写しても、「その検査が実際にその保証を与えた」ことにはならない。**
偽の report を所定の path に置けば、内容述語 (非空 schema、非空 guarantee、`result=pass`) は
すべて通る。SHA-256 は「偽の自己申告を含む bytes」を正確に束縛するだけである。

D779 の理由節はこう書いている — 「どの検査が何を保証したかを後から証拠の鎖として辿れず、
保証を名乗る根拠が受領証の外にある」。求められているのは鎖であって転記ではない。

**採った対応: report の名乗りを pilot が実際に渡した引数と照合する。**

| 照合 | report 側 | pilot の実引数 |
|---|---|---|
| commit 旧 | `old_oid` | `$BASE_OID` |
| commit 新 | `new_oid` | `$NEW_OID` |
| repo view | `repo` | `$BUILD_SOURCE` |
| compiler | `compiler.path` | `$CXX_PATH` |
| 対象 path | `expected_paths` | `["cc/mocc/transaction.cc"]` |

## 2. 実測が述語を 2 度書き換えた

### 2.1 checker は引数を正規化する — 素朴な文字列一致は必ず外れる

親が実 pair (`511c9538`→`058d0c4e`、`/usr/bin/g++-12`) で checker を実走したところ、
report の `compiler.path` は `/usr/bin/x86_64-linux-gnu-g++-12` だった。checker は
`--cxx` を `os.path.realpath(found)` へ (`tools/check_trace0_preprocess_identity.py:226`)、
`--repo` を `Path(os.path.realpath(repo))` へ (同 `:654`) 正規化している。
渡した値をそのまま比較する述語は、実 pilot でも偽陰性になりうる。照合は realpath 同士で行う。

**この 1 件は brief 段階で測っていなければ、段 6 か実 PBS まで露見しなかった。**

### 2.2 `os.path.realpath` は既定で存在確認をしない

段 6 の敵対レビューが突いた。`realpath` は既定で `strict=False` であり、
`$BUILD_SOURCE/does-not-exist/..` のような**辿れない path** も文字列上は正規化して一致する。
`strict=True` と、repo は directory・compiler は regular file という型検査を同じ lookup へ結合した。

## 3. 本 wave の中心的な発見 — 「不変な経路」を 1 本持たない照合は、対で差し替えられる

段 6 の敵対レビュー 2 本が**独立に同じ穴**を挙げた。

初版は、受領証 writer が自分の serialize した bytes の SHA-256 を sidecar ファイルへ書き、
shell の再計算と job-result 側の再計算をそれと照合する形にした。三者照合である。
しかし **sidecar は書き換え可能なファイルでしかない**。受領証と sidecar を辻褄を合わせて
同時に差し替えれば、三者すべてが差し替え後の値で一致し、照合を通過する。

同じ形の穴が 2 つ並んでいた。

| 穴 | 中身 |
|---|---|
| 受領証 SHA | writer が計算した値が可変ファイルにしか残らない |
| report / 受領証 / sidecar の読み取り | `islink` / `stat` / `open` が別々の pathname lookup で、検査した対象と実際に読む対象が同一だと保証されない |

**恒久対応は同じ形である — 検査と使用のあいだに、外から書き換えられない経路を 1 本通す。**

- 受領証 SHA: writer が stdout で自分の SHA を名乗り、shell が変数として捕まえる。以後の照合は
  すべてこの「writer が名乗った値」を基準にする。ファイルを経由しない。
- 読み取り: `os.open(..., O_NOFOLLOW)` で開き、**同一 fd** に対して `fstat` し、同じ fd から読む。

この環境で単なる理論上の心配ではない理由がある。T-1582 の attempt 2 は、**前の job が共有 hydrate
先へ残した build artifact** を次の job が検出して fail-closed した。同じ attempt directory を
別の書き手が触る事象は、この pilot で実際に起きている。

## 4. 変異が示した検出力の穴 — 「拒否される」と「その述語が拒否した」は違う

事前登録した M13 は「受領証を差し替える」変異だった。段 6 のレビューが指摘したとおり、
この入力は sidecar 側の照合が**先に**拒否するため、job-result 側の再計算述語を削除しても赤くならない。
拒否されること自体は変異の kill にならない。**その述語が単独で拒否理由になる入力**を作らなければ、
検出力は登録した数だけあるように見えて実際には無い。

対応として「shell が SHA を採った後・job-result writer の前」に差し替える tamper hook を足し、
job-result 側の述語だけが検出点になる node を分けた。

## 5. 受領証の版を上げた理由

`mocc-trace-pilot-receipt/v1` のままにすると、consumer から見て
「4 項目を持たない古い正常な受領証」と「改修後なのに束縛を欠く壊れた受領証」が同じ schema になる。
どちらを許しても片方を取り逃す。受領証と job-result をともに **/v2** へ上げ、
「v2 = report を束縛している」という識別子にした。pin 閉包は producer 1 箇所ずつだけで、
台帳・golden・テストに literal pin は無いことを実測で確認している。

## 6. 記録した限界 (直していない)

- **I/O 障害の残骸。** 検証は `open` の前に済ませているが、`open` 成功後の ENOSPC・quota 障害では
  部分的な受領証が残りうる。これは既存 2 writer に共通の性質であり、片方だけ atomic 化すると
  対が不揃いになるため本 wave では直していない。
- **interpreter path は provenance を閉じない。** 記録するのは名前であって、実行 bytes・version・
  checker の source bytes ではない。[T-755] の依頼 (実体 path の記録) は満たすが、
  これを producer 実体の同定と同じ保証として扱ってはならない。
- **防御的 invariant と独立 gate の区別。** 前段の相互排他的分岐で値が固定されている検査
  (TRACE=0 の checker rc、TRACE=1 の checker 状態など) は、単独変異で発火しない。
  独立 gate と防御的 invariant を分けて登録する規律は backlog に残る。

## 7. この wave では閉じない 3 件 (ユーザー裁定へ返す)

1. **既存 T-1582 の値は正式材料へ上がらない。** script の改修は将来の run にしか効かず、
   受領証 SHA `1a62ba3abb4d4253ec8fe0af6f8ce2938f5af2e7d59505c9e5dae7596ba60bee` の文書に
   4 項目は増えない。旧受領証を書き換えれば SHA と create-only の歴史性が壊れる。
   択一は (a) 改修後の script で再計測する、(b) D779 を改めて append-only の事後 attestation を
   認める。
2. **consumer 側に gate が無い。** producer が 4 項目を出しても、材料レポートを書く経路が
   従来どおり返り値だけを読めば D779 の関門は実効発火しない。加えて job-result が拒否されても
   `status=completed` の受領証は残るため、昇格側は受領証単体でなく
   受領証 × job-result × failure 不在の積で判定する必要がある。
3. **interpreter の bytes 級同定**は、D780 の別防壁 ([T-1642]/[T-1644]) と同じ閉包でだけ設計する。

## 8. 変異が示した第 2 の発見 — 自分の修理にも同じ形の穴が出た

段 6 の fix は受領証 SHA の照合を 3 点に増やした。親が変異を実走したところ、
**実効は 1 点だけ**だった。

| 照合 | 単独で消すと | 判定 |
|---|---|---|
| shell 側 (`mocc_trace_pilot.sh` の `RECEIPT_SHA != RECEIPT_WRITER_SHA`) | SURVIVED | 冗長。job-result writer が同じ差し替えを包含して捕まえる |
| job-result writer の受領証本体照合 | 1 node が赤 | **実効** |
| job-result writer の sidecar 照合 | SURVIVED | 検出力なし。既存負例が受領証本体も一緒に書き換えるため、手前の照合が先に拒否していた |

**この wave が最初に見つけた欠陥 (report の自己申告を写すだけでは鎖にならない) と同じ形が、
自分の修理にも出た。**「守っているつもりの層」は、単独で拒否理由になる入力を作って初めて確かめられる。

対応は 2 つに分けた。

- shell 側の冗長は仕様どおり (writer 側が包含する) で、単一理由の入力を作れない。
  `DW-M03` に従い**冗長 gate と明記して単独変異の証拠から外す** (SURVIVED 期待として登録)。
- sidecar 照合には単一理由の入力が作れる — 受領証本体を無傷のまま sidecar だけを書き換える。
  sidecar は成果物目録に載る公開記録なので、受領証と食い違ったまま job-result を書かないのが
  正しい挙動であり、実装は既にそうなっていた。足りなかったのはテストだけである (`98c6e6fd`)。

両層同時変異も登録し、3 node が赤くなることで層の分担を確認した。

## 9. 実測値

### 変異 matrix

- spec: `output/insights/2026-08-25_t1641-mutation-spec-final.json`
  (SHA-256 `3fe7a7ce0f7b25938ae2134502f1bf5bcf3598fcaa99dd00e11ee97f3f2a7bec`)
- 台帳: `output/insights/2026-08-25_t1641-mutation-ledger-final.json`
- HEAD: `98c6e6fd6a511ca7fb08ae197321820aa530fa78`
- **baseline PASSED・24 件登録・23 KILLED・SURVIVED 1 (登録どおりの冗長 gate)・MISMATCH 0・
  TIMEOUT 0・PARSE_ERROR 0**。24/24 が期待と一致。
- runner: `python3 tools/run_tests.py orchestrator/tests/test_mocc_trace_job_contract.py -q -rf`
  (local、`/usr/bin/python3.10`)

**erratum**: 本走の 1 回目は MISMATCH 3 件だった。期待 node の取りこぼしはゼロで、
観測 pass の後に足した `h1` node が 3 つの変異で追加で赤くなったためである。
現 HEAD の観測で登録し直して再走し、上記の結果を得た。1 回目の台帳は job dir に保全した。

### 焦点走 (親の実走)

| 巡 | 対象 | 結果 |
|---|---|---|
| 実装後 | `orchestrator/tests/test_mocc_trace_job_contract.py` | 39 passed (3.66s) |
| 実装後 | `orchestrator/tests/test_hooks.py` | 453 passed 1 skipped (4.23s) |
| fix 1 後 | 同上 test file | 48 passed (3.35s) |
| fix 2 後 | 同上 test file | 49 passed (3.62s) |
| sidecar node 追加後 | 同上 test file | 50 passed (3.39s) |

### 受入全走

(段 9 直前に記入)
