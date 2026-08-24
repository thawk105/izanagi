静的レビューのみ実施した。read-only 契約に従い pytest は起動しておらず、緑は主張しない。

### 所見 1

- 主張: `DW-O28` は要求された義務句を列挙しているが、cleanup の完全な呼出し形と fail-closed 述語の極性が欠け、実行可能な義務になっていない。
- 具体的な破れ方: land 成功後に親が `/tmp` へ出て逐語どおり `python3 tools/dev_wave_cleanup.py` を実行すると script 自体を解決できず、main checkout へ出ても引数なしなので `len(argv) != 8` で rc=2 となる。また「dirt を確認できた」状態は「確認できなければ停止」には該当しない、と読む余地がある。
- 根拠: `docs/dev-wave/operations.md:191-196` は全義務句を含む一方、command は引数なし。tool は `--main-worktree`、`--wave-worktree`、`--wave-branch`、`--tested-wave-tip-sha` の exact 4 組を必須にする (`tools/dev_wave_cleanup.py:108-135`)。実際の安全述語は clean (`:422-430`)、ancestry (`:433-453`)、primary (`:493-511`)、fold state (`:520-526`)、unoccupied (`:383-419`) であり、本文の「確認できなければ」より狭い。
- **成果物影響:** checker が受理した正本どおりに動いても撤去の実行可否が「実行可能」から rc=2／path 不在へ変わり、別実装には dirty 等を受理する解釈余地が残る。
- 提案する対処: **実装で閉じる。** main worktree への `cd` または絶対 script pathと、4 引数を逐語化し、各述語を「unoccupied・clean・main の祖先・fold state 不在・primary・cwd 外」と正負込みで書く。exact pin と fixture も同時更新する。

### 所見 2

- 主張: cleanup の破壊開始後に失敗した場合、「理由を worklog へ書く」ための書込・commit 経路が状態機械に存在しない。
- 具体的な破れ方: directory、registry、branch の削除後に postcondition が失敗すると rc=30 `partial` になるが、wave worktree と branch は既に無い。段 7 の記録は終了済みで段 9 は終端なので、理由を canonical worklog へ残すには未規定の main 直接編集か、新 wave が必要になる。
- 根拠: worklog 義務は `docs/dev-wave/operations.md:196`。branch 削除後にも失敗可能な postcondition がある (`tools/dev_wave_cleanup.py:672-682`)。状態機械は記録を段 7、land と終端を段 9 に分ける (`.claude/commands/dev-wave.md:54-58`)。
- **成果物影響:** cleanup が `partial` でも台帳の worklog entry が 1 件欠落するか、main に未規定の dirt／commit が発生する。
- 提案する対処: **scope 外として裁定へ返す。** post-land 記録 commit を正式な段 9 遷移として許すか、worktree 外の durable receipt を作り、canonical worklog へ収容する明示経路を決める。

### 所見 3

- 主張: 入口上限 9,584 byte は現在は必要最小限だが、その値を独立 literal で固定する consumer test が無い。
- 具体的な破れ方: `TextLimit(9_584, 140)` を `TextLimit(10_000, 140)` に変えても現 command は 9,584 byteなので正例は通り、既存 `command_byte_over` 変異は `rulings.md` しか膨らませないため、D671 に反する余分な 416 byte の受理拡大を捕捉しない。
- 根拠: production 上限は `tools/check_docs.py:263-267`。入口は実測 9,584 byte、条件 27 行は 87 byte (`.claude/commands/dev-wave.md:116`) なので、旧実体 9,497 + 87 = 9,584 で最小。テストの byte-over は `rulings.md` を対象にする (`orchestrator/tests/test_check_docs.py:5960-5968`)。同 test file 内に `9_584`、`9584`、dev-wave の `COMMAND_LIMITS[...]` assertion は無い。D671 用の収容理由と増分は `ruling.md:12-15` に記録可能な形で存在する。
- **成果物影響:** 将来の checker 変更だけで入口の受理集合が 9,584 byte 以下から、例では 10,000 byte 以下へ拡大する。
- 提案する対処: **検査で閉じる。** `dev-wave.md` の上限が exact 9,584、実体も exact 9,584、9,585 が拒否されることを独立 literal test で固定する。

層については `DW-O28` が条件 27 の C edgeだけに所属し (`tools/check_docs.py:876-882`)、U edgeから L1/L1.5 を作る分類 (`:4731-4746`) では L2 になる。従って consult 時の実測 L1=10,624、L1.5=9,565 (`consult-luna.md:86`) は変わらず、上限10,625／9,566にも各1 byte残る。

### 所見 4

- 主張: `DW-O28` の現位置は裁定どおりだが、`DW-O27` より後という位置契約は checker に pin されていない。
- 具体的な破れ方: 695 byte の exact O28 blockをそのまま O27 より前へ移すと、本文 pin、registry、条件 edge、層分類はすべて不変で、既存の順序検査も発火しない。
- 根拠: 現在は O27 (`docs/dev-wave/operations.md:175`) の後に O28 (`:189`) があり、O28 は UTF-8 695 byte、1,000 byte上限まで305 byte。O25もO23より後 (`:153-165`)。checkerの順序対象は O23/O25 だけ (`tools/check_docs.py:5539-5559`)。
- **成果物影響:** **nit** — dispatch 受理集合、台帳、撤去の実行可否は変わらず、裁定された文書配置だけが破れる。
- 提案する対処: 配置を規範として維持するなら **検査で閉じる**。単なる編集上の配置なら nit として受理可能。

## 閉包照合

- production registry、条件27 target/trigger、`_OPERATION_NUMBERS`／`_ALL_OPERATIONS`非変更は閉じている (`tools/check_docs.py:725-725,746-765,793-795,868-909`)。
- production／checker／fixture の O28 はすべて695 byteで逐語一致した (`operations.md:189-196`、`check_docs.py:589-597`、`test_check_docs.py:179-187`)。
- fixture registry、renderer、L2 literal 2箇所も更新済み (`test_check_docs.py:203-215,873-920,2375-2383,2794-2822`)。
- 条件27削除・target変更、O28削除・heading-only・弱体化の変異と登録表がある (`test_check_docs.py:6338-6362,6549-6573,6835-7033,7208-7291`)。
- O28 内に fence、HTML comment、raw HTML は無い。raw/visible slice比較とraw HTML負例もある (`tools/check_docs.py:1796-1820`、`test_check_docs.py:8743-8794`)。
- `tools/dev_wave_land.py` は operations 全体で exact 1 件かつ O23 内だけで、O28 は再掲していない (`operations.md:155`、`check_docs.py:5763-5774`)。
- O28節または条件27行だけを削れば、registry/exact pinまたは条件contract/typed-edge閉包が必ず finding を出す。静的コード上、両削除変異が黙って通る経路はない。
- fixture の cleanup placeholder (`test_check_docs.py:813`) は新規 path reference の存在検査用で、既存検出力を落としてはいない。ただし hollow script でも path lint は通るため、実行意味を検証しない点は所見1に含めた。
- D204 は裁定された同一 invocation 限定の部分 supersede (`ruling.md:39-47`) で、tool も primary・ancestry・`branch -d` を強制する。D271 admission は独立に記録され (`:25-37`)、D279 の「先例にしない」へ依存する参照はない。

## 総括

(a) must-fix: ①完全なcleanup呼出しと述語極性、②partial後のworklog記録経路、③入口9,584 byteの独立pin。  
(b) この docs 変更は現状では land すべきでない。dispatch・exact pin・削除変異の閉包は強いが、正本どおりの撤去が実行不能になり得る。