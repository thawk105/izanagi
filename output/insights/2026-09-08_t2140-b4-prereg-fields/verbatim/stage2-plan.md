## プラン

行番号は編集前の現行版を基準とする。

1. [事前登録文書 161 行目](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2140-b4-prereg-fields/docs/phase3-b4-reflux-ablation-preregistration.md:161)を、改行を増やさず次の 1 行へ置換する。

```text
|primary outcome の演算定義 (純関数)|orchestrator/campaign/p3_b4_analysis_contract.py sha256=528ee2fa5795bf36fcd966bed47efb025b24a070c8c4e4303c8615957893d2a3; orchestrator/campaign/p3_b4_analysis_adapter.py sha256=cf056566a7bc2c23b0a5af14a537450fe4d160b042eda9df26fd41ad200cc0b6; orchestrator/campaign/p3_b4_analysis_ledgers.py sha256=71393e8d3ffc60e8af3421c1caf80abc1cf2395551173d96524b724ab5785cda; orchestrator/campaign/p3_b4_analysis_path.py sha256=eeb397fcf8cfebf454bdacc00af9943010b53b59c6cf64dcdded0acf3217ea86; orchestrator/campaign/p3_b4_analysis_prereg_consumer.py sha256=fe3aeb804fc09733434c8974500bba9f46cbd942e39bd33b2c6063134d96b31a|
```

順序は [`_SOURCE_CLOSURE_PATHS` 67–73 行](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2140-b4-prereg-fields/orchestrator/campaign/p3_b4_analysis_path.py:67)と一致する。158 行目の「対象 driver と軸」に倣い、各 pair を `; ` で区切り、`sha256=` を使う。ただし basename と暗黙の path root までは倣わない。primary outcome の解除条件は artifact の path と sha256 を要求しているため、basename だけでは規範を満たさない。また、値を複数行へ折り返すと表の行数検査が壊れ、`|` を pair の区切りに使うと 3 セル以上として拒否される。

2. §5 parser との整合を次の行で確認する。

   - [`_SECTION5_LABELS` 77–88 行](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2140-b4-prereg-fields/orchestrator/campaign/p3_b4_admission_record.py:77): データ行は exact 10 行。
   - 625–640 行: `## 5...` と `### 5.1...` を各 1 個要求。
   - 645–649 行: 非空行が header 2 行 + データ 10 行で、header は exact `|欄|値|` / `|---|---|`。
   - 653–657 行: 各行は先頭・末尾が `|`、内部の `|` 分割結果が exact 2 セル。
   - 658–666 行: whitespace strip、NFKC 正規化、label の重複禁止・集合一致。
   - 527–544 行: default-ignorable/Cf を拒否してから NFKC 正規化。
   - 114–121、667–673 行: 空値、`未記入` 等の sentinel、whole-value sentinel を拒否。
   - 674–688 行: 特殊な文法検査は model/prompt/projection 行だけで、primary outcome 行の path/hash の意味は検査しない。

   提案文字列自体には内部 `|`、sentinel、正規化で変化する文字がなく、primary 行単体の形は受理可能。ただし 159、162–167 行には `未記入` が残るため、§5 表全体の admission 検査は引き続き意図どおり拒否する。今回の記入だけで gate が緑になるとは扱わない。

3. hash の陳腐化は、§5.1 の projection 行に対する 244–245 行の運用を同様に適用する。新しい機械検査や規範追記は行わない。

   - 編集直前と commit 直前に 5 member 全件を再計算する。
   - 1 member でも変化していれば、5 pair 全体を現在の `_SOURCE_CLOSURE_PATHS` 順で原子的に再記入する。
   - 記入 commit 後に member が変わった場合、その登録値は陳腐化したものとして、実走前に後続 commit で更新する。
   - admission parser はこの行の path/hash の意味や live bytes との一致を検査しないため、parser 通過を freshness の証拠にしない。

4. §10 は、現行 822 行目の直後、824 行目の次 bullet より前へ次を追記する。既存記述は残す。

```text
  **追記 (2026-09-08、[T-2140])。** 上の現在地はその後変わった。§5.1.0 の先行 freeze、
  §5.1 (ii) の実測、同 (iii) の採否は完了し、§5 の「対象 driver と軸」欄は
  `base (silo-backoff-magnitude)` として記入済みである。したがって、上の「欄は埋められず」と
  本節後段の「対象 driver と軸の選定そのもの」は、現在の未決事項ではない。
  **本書がなお発効前であることは変わらない** — §5 の他の未記入欄と §6 の未充足条件が残るためである。
```

5. §11 の現物確認は取れなかった。`orchestrator/campaign/p3_b4_material_report.py` と `docs/worklog.md` は単独段 dispatch の必読射影外であり、今回の隔離条件では読めない。親が現物で「生成器が §5 から floor 入力を導出して評価器へ渡す」ことを確認できた場合に限り、次を適用する。

   現行 905 行目の直後、907 行目より前:

```text
**追記 (2026-09-08、worklog entry 1336)。** 上の現在地はその後変わった。現在の材料レポート生成器は
本書の §5 から評価器へ渡す floor 入力を導出する。したがって「本書を読まず」「無条件に floor 不在を
渡す」「floor 行を埋めるだけでは正規経路は変わらない」という記述は、現在の動作を表さない。
**この訂正は §5.1 の解除条件も §6 の前提条件も緩めず、`未記入` を有効な floor とみなさない。**
```

   現行 1092 行目の直後、1093 行目の次 bullet より前:

```text
  **追記 (2026-09-08、worklog entry 1336)。** 上の現在地はその後変わった。材料レポート生成器には、
  §5 から floor 入力を導出して評価器へ渡す接続が実装済みである。したがって「生成器は本書を読まない」
  「floor 接続は未実装」という現在地は解消済みである。**この事実だけで、権威ある floor 成果物、
  §5.1 の解除条件、または本書の他の発効条件が充足済みだという意味にはならない。**
```

## 触ってはいけない範囲

pin 対象は[事前登録文書 312 行目](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2140-b4-prereg-fields/docs/phase3-b4-reflux-ablation-preregistration.md:312)の `#### 5.1.1` から、§6 見出しの直前である596 行目まで。すなわち **312–596 行、両端を含む 285 行、21,833 bytes**。

この raw bytes の sha256 は次で、consumer の [47–49 行](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2140-b4-prereg-fields/orchestrator/campaign/p3_b4_analysis_prereg_consumer.py:47)と一致した。

```text
0ceab4cd064eb8ff6c5dba22364fff04a6d708de8acb9d9cde52115f0891df30
```

consumer は 301–345 行で該当 H4 から次の level 4 以下の heading 直前までを切り出す。analysis path 側も 380–413 行で同じ境界を抽出する。

計画した変更位置は 161 行目、822 行目直後、905 行目直後、1092 行目直後である。161 行目は 1 行置換なので行数を変えず、残りはすべて596 行目より後である。したがって 312–596 行には 1 byte も掛からない。

## 影響するテスト

親が走らせる pytest nodeid は、対象 file 全体を nodeid とするのが安全である。

- `orchestrator/tests/test_p3_b4_analysis_prereg_consumer.py`
- `orchestrator/tests/test_p3_b4_admission_record.py`
- `orchestrator/tests/test_p3_b4_material_report.py`

1 本目は射影文書 267 行目で存在が参照されている。後二者は射影外のため、今回その存在や個別 test function 名を確認できていない。親は収集前に実在確認し、特に material-report test で「§5 の floor 値を渡す／未記入は有効値にしない」node を含むことを確認すること。併せて docs-only の必須検査として `python3 tools/check_docs.py` を実行する。

この段では pytest を実走しておらず、緑とは報告しない。

## 総括

§5 primary outcome の exact 値、順序、5 件の live sha256、parser 整合、pin 範囲は静的に確定できた。編集は事前登録文書 1 file のみで、floor 行、§5.1、§5.1.1、コードには触れない。

所見として、§11 の訂正文だけは material-report 実装の現物確認が射影不足で未完了である。親が当該 source と worklog entry 1336 を確認してから、上記の条件付き文面を採用すべきである。