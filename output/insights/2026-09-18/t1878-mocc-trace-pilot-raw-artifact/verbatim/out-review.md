## 所見 (R-1 …)

以下、`I` は本 wave の `output/insights/2026-09-18/t1878-mocc-trace-pilot-raw-artifact/README.md`、`P` は `docs/paper-story/README.md`。射影ファイル名は指定された `projection/` 配下を指す。

**R-1 / 対象: I 冒頭・§1・§2・§5、P claim-evidence 系列 / 主張: 未特定という観測から、消失原因・保存履歴の断定へ進んでいる / 分類: must-fix**

根拠: I:75–76 は「worktree 撤去で失われ、commit も退避もされておらず」と断定する。I:11、41、P:187 にも同型の断定がある。一方、記録された確認は現在の path・branch の不在と `git log --all -- <path>` の結果である。これでは撤去による消失、過去の退避の有無、削除済み ref を含む過去全体までは確定しない。handoff:109–113 は消失への注意と清掃方針であり、この artifact の消失経緯を記録していない。

**放置時の影響:** C14a の「探索範囲内で未特定」が「消失し保存もされなかった」という未立証の履歴へ変わる。

是正案:

- 「どの ref にも一度も commit されていない」
  →「探索時点の `--all` 対象 ref から辿れる当該 path の履歴では該当 commit を確認できなかった」
- 「evidence dir にも退避されていない」
  →「evidence dir の今回の探索では退避物を特定できなかった」
- 「未特定の理由は『出力が投入 worktree 配下にあり、worktree 撤去で失われ、commit も退避もされておらず、当時の receipt が bytes を hash していなかった』である。」
  →「当時の script の出力先は投入 worktree 配下だった。今回、その出力先・git 履歴・退避先候補から raw を特定できなかった。消失原因や過去の保存履歴は確定していない。当時の receipt 生成処理には verifier.json の sha256 束縛が無かった。」
- 「記録へ落とされたのは insight 本文の JSON block と要約であり、raw bytes とその hash ではなかった。」
  →「確認できた insight には JSON block と要約があるが、今回の探索では raw bytes とその hash を特定できなかった。」

**R-2 / 対象: I §2、brief.md 段1実測 / 主張: 探索対象ディレクトリと、実際に本文を読んだ集合が混同されている / 分類: must-fix**

根拠: `search_934607.py.txt:19–20,30–53` は拡張子 allowlist、50 MiB 上限、symlink 除外を持つ。directory symlink は追跡せず、`lstat`・read の失敗も黙って除外する。`scanned` は read 成功前に増える。したがって I:43 の「全 text file」は正しくない。I:48–49 は未探索を依頼範囲外に限って列挙しており、範囲内の除外を落としている。

**放置時の影響:** C14a の未特定を支える探索が、指定ディレクトリ内の全ファイルを確認した結果として読まれる。

是正案:

- 「全 text file で `934607.nqsv` を grep」
  →「走査 script の拡張子・種別・サイズ条件を満たすファイルを本文検索」
- 「50 MB 超」→「50 MiB 超」
- 「依頼の範囲外であり、本 wave は走査していない。」
  →「以上は依頼範囲外として走査していない。範囲内でも、allowlist 外の拡張子（`.nqsv` 終端を除く）、50 MiB 超のファイル、symlink ファイルと directory symlink の参照先は本文検索していない。列挙・属性取得・読み取りに失敗した対象も検索できていない可能性があり、その件数は本 script では記録していない。名前の列挙は本文検索とは別である。」
- 「12,526 text file」
  →「本文読み取り試行のカウンタは12,526件（読み取り成功件数とは区別）」

**R-3 / 対象: I §2 #4–5、search-934607-result.txt、brief.md:23 / 主張: 保存された走査方法だけでは「完全表記0件」「全hitが数値偶然」を再確認できない / 分類: must-fix**

根拠: `search_934607.py.txt:54–58` は `b"934607"` の**最初の出現だけ**を `data.find(NEEDLE)` で取り出す。ファイル全体について `934607.nqsv` を判定しておらず、最初が数値偶然でも後続に完全表記があり得る。分類一覧は親の分類結果を示すが、その追加確認方法は射影に無い。

**放置時の影響:** ファイル単位の「最初の一致の分類」が「全本文で完全表記なし」という強い陰性結果へ変わる。

追加実測を要求せず、現資料に合わせる是正案:

- 「**完全表記 0 件**。数字 `934607` の hit 151 件は全て別 job … の数値偶然」
  →「保存した分類一覧では、evidence dir の151ファイルが `numeric-coincidence` に分類されている。ただし走査 script の表示は各ファイルの最初の一致周辺だけであり、これだけでは後続を含む完全表記の不在は確認できない。」
- brief の「evidence dir に `934607.nqsv` 完全表記 0 件」も同じ限定へ置換する。

親が別途全文検索していたなら、その既存実測の方法・結果を記すことで解消できる。

**R-4 / 対象: I §4 / 主張: D920 の引用が「投影どうし」から「別走行」へ広がっている / 分類: nit**

根拠: `claim-evidence-C14a-and-b-column-rule.md:8` は「同じ走行主体が書いた**投影どうしの一致**は、独立な裏取りとして数えない」。I:66 は「同一走行主体の**別走行**は裏取りにならず」としており、逐語も射程も異なる。

放置時の影響: 別観測を C14a の raw と取り違えないという正しい結論に、反復観測一般への根拠のない制限が混入する。

是正案:

「(D920: 同一走行主体の別走行は裏取りにならず、そもそも別の観測である)」
→「(これらは別 request の観測であり、934607.nqsv の raw bytes ではない)」

**R-5 / 対象: P:179–180、I §5、brief.md P1 / 主張: 個別記録の置き方はD1013違反ではないが、将来一般の運用規則まで追加している / 分類: nit**

根拠: D1013:8–9 が禁じるのは系列に「一項目だけを直した差分改訂」を新日付として置くこと。今回、matrix 新稿は作らず、日付付き insight と個別注記を置いている。D1013:33–34 の却下理由は「指し先がどの契約で正しいかが定まらない」「**新しい artifact 種別を足すときは** lifecycle を同時に定義する」。既存 insight を指す今回の所在記録を一律に禁止する文ではない。

ただし「一項目の後日談はここに日付付きで積む」は、T-1878に必要な個別処理を将来一般の規則へ拡張している。

放置時の影響: 所在調査の記録が、claim-evidence 系列の一般的な後継記録運用の新設として残る。

是正案:

「**凍結後に確定した後継記録 (腐らない入口)。** 稿は凍結物なので書き換えず、一項目の後日談はここに日付付きで積む
(一項目だけを直した新しい日付の稿は規則 2 が禁じる)。矛盾があればここが指す一次資料が勝つ。」

→「**C14a の所在調査の追記 (2026-09-18)。** 2026-08-26 稿は変更せず、今回の探索結果を以下に記録する。claim-evidence matrix の新稿ではない。」

brief の「新日付の claim-evidence file は D1013 規則 2 が禁じる」も、「**一項目だけを直した**新日付の claim-evidence file は」に限定する。

**R-6 / 対象: I §2 #5–6 / 主張: 分類の説明とrequest内訳に誤りがある / 分類: nit**

根拠: `search-934607-result.txt:200` の50 IDは g2-repro 43、pairの連番 `949961`〜`949967` の6、t1582の1である。I:45 の「pair 7 request」では合計51になる。probe `949555`・`949585` は別形式のpathとして同一覧:188–195にある。また handoff:77–90 は結果待ちと今後の作業を記す文書であり、I:44 の「いずれも insight 本文の転記」は当てはまらない。

放置時の影響: 探索結果の内訳と、各資料が持つ情報の性質を誤って伝える。

是正案:

- 「g2-repro 43 request、pair 7 request、t1582 の TRACE=0 `0:942177`」
  →「`.nqsv` 表記のID一覧では g2-repro 43、pair 6、t1582 1。probe形式のpathは別掲」
- 「**いずれも insight 本文の転記であって raw ではない**」
  →「分類一覧では handoff・insight等の写し・events の本文言及として整理されている」

**R-7 / 対象: brief.md:17、I §5・§6 / 主張: branch差分の走査から「稼働waveが特定節を編集中」は導けない / 分類: 記録**

根拠: `s5-diff.patch:140–157` の overlap script は `refs/heads/` と merge-baseからtipへのcommit済み差分を見る。稼働状態、未commitの作業木、編集節は確認しない。実行結果も本射影には無い。別の一次確認が存在しないとは断定しないが、提示資料では裏付けられない。

放置時の影響: 親の配置判断の理由が、未検証の他wave現況として凍結記録へ残る。

是正案:

「版系列の『最新スナップショット以後に確定したこと』節は稼働 wave [T-2775] が編集中 (項目数行と項目追加) なので触れない」
→「本件は C14a の所在記録なので、claim-evidence 系列節へ追記する」

また起点原文 `T-1878-original.md:1–3` には限定範囲等の詳細は無い。brief:3 の「依頼 (逐語要約)」は「依頼の要約（起点entryと今回の追加条件）」とすると出所が明確になる。追加条件自体は今回のレビュー依頼でも明示されている。

**R-8 / 対象: I §1・§3・§4 / 主張: 一部の行番号・補足命題は提示一次資料で支えられていない / 分類: nit**

根拠と是正案:

- `job-result.json` の生成は当時script:1100、`receipt_sha256` は1112。
  「同 script 1082-1099 行」→「同 script 1080–1115 行」。
- `ATTEMPT_DIR` の引用は変数を展開した要約。原文はscript:44–46の `JOB_STAGING_ROOT=...` と `ATTEMPT_DIR="$JOB_STAGING_ROOT/$PBS_JOBID"`。
  展開形の前に「変数展開すると」を付す。
- 実ディレクトリの `934607.nqsv` と `0:934607.nqsv` の区別は `$PBS_JOBID` の実値が必要。script:242–250 は両表記を正規化して比較する。
  P:186の `job-staging/934607.nqsv/` → `job-staging/$PBS_JOBID/` とし、request表記から導いた候補であることを明記する。
- I:25の「現行版は…」、I:56の `core.py` がpopする補足は、今回の射影では照合できず、本論にも不要。該当括弧内を削除する。
- pair.md は別request・別txn・別sourceを裏付けるが、`c284b507…` / `ff334773…`、probeの778,690 txn、C14aとのbinary bytes不一致は同資料に無い。
  「別 request・別 txn 数・別 binary」→「別 request の観測」。hash・probe txnの具体値は既存照合の出所を示すか削除する。

放置時の影響: 正しい中心結論の周囲に、再照合できない精密な出所・値が残る。

## 逐語照合の対照表 (命題 / 記録の文 / 一次資料の逐語 / 一致・不一致)

| 命題 | 記録の文 | 一次資料の逐語・位置 | 一致・不一致 |
|---|---|---|---|
| PBS・host・日付 | `934607.nqsv`、gen_S、2026-08-22、bnode050 | t755 insight:25–27「実行host: bnode050」「PBS request 934607.nqsv、gen_S、2026-08-22」 | 一致 |
| outer commit | `2efe6282ed22a694cdd7b38c641bedecc6d2e6d4` | t755 insight:18、handoff:8 | 一致 |
| ccbench OID | base `511c9538…` → new `ef9328a3…` | t755 insight:19–21、完全OIDとも一致 | 一致 |
| workload | 10000 / 48 / 0.9 / 50 / 0 / 10 / 3 | t755 insight:22–23 | 一致 |
| txn・判定 | 761,914、serializable、certified真、anomaly 0、cycles 0 | t755 insight:53–57、79–80 | 一致。ただし当時insightの記述として |
| verifier起動 | `<VERIFIER_PY> … --json --expected-commits 761914` | 当時script:934–936、t755 insight:31–40 | 一致。VERIFIER_PYの説明はjob側 |
| 2回のbytes一致 | 「一致 (と記述)」「hashは記録されていない」 | t755 insight:31–43「byte-for-byte一致」、hash記載なし | 同insightについて一致 |
| 投入worktree・5回目 | `dev-wave-t755-mocc-trace-execution`、5回目934607 | handoff:8–9、77 | 一致 |
| 出力先 | PBS_O_WORKDIR配下のjob-staging | 当時script:40–46、936 | 構造は一致。実PBS_JOBID表記はR-8 |
| manifest・receipt | 同じATTEMPT_DIR | 当時script:878、990 | 一致 |
| submit receipt | attempts/submissions/nonce | 当時submit:151–154、309 | 既定設定について一致 |
| `-o` / `-e` なし | 当時qsubに指定なし | 当時submit:199 `qsub_cmd=(qsub -v "$EXPORT_SPEC" "$JOB_SCRIPT")` | 一致 |
| PBS stdout/stderr | submit directoryへ落ちる | pair.md:62–65「PBS stdout/stderr が submit directory (= repo root) へ落ちる」 | 一致 |
| verifier hashなし | receiptはfilenameのみ | 当時script:1085 `"verifier_json": "verifier.json"`、pair.md:86–91 | 一致。receipt全体がhashを持たない意味にはしない |
| job-resultのhash | receiptのsha256を持つ | 当時script:1099–1112 | 命題一致、引用行範囲不足 |
| 欠落3キー | trace_dir、framing/permutation details | 当時report:98、122–125、129–131。cli:84は`result_to_dict`を直接使用。t755 block:45–85には無し | 一致 |
| 埋め込みhashを代用不可 | rawと同bytesではない | 上記3キー差分、cli:86のJSON出力 | 支持される |
| pairは別観測 | 949961 / 949963を流用しない | pair.md:110–111は756,277 / 740,190 txn。C14aは761,914 | 支持される |
| 消失・未退避 | 撤去で失われた、退避されていない | 現在の限定探索結果と一般的注意のみ | 不支持、R-1 |
| 完全表記0件 | evidence全textで0件 | scriptは最初の数字一致周辺のみ表示 | 提示方法では未立証、R-2・R-3 |

## 探索範囲の被覆 (依頼 (a)(b)(c) と §2 の対応、抜け)

| 依頼 | §2との対応 | 評価 |
|---|---|---|
| (a) insight 5群が名指すjob dir | #5の9 dir、#6の名前列挙 | scriptのROOTSと一致。ただし残るinsight群の全文は今回の指定資料に無く、「名指し先をすべて拾った」ことまでは独立確認できない |
| (b) evidence dir配下 | #4、script ROOTS末尾 | rootは含む。本文検索はR-2の条件付き部分集合 |
| (c) 当時script出力先 | #1 worktree、#2 git履歴、#3主checkout | scriptとの対応はある。#1の相対path確認は実行cwdの記録が無く、対象がrepo直下かは射影だけでは再確認できない |
| 補助確認 | #7 session tmp | handoff:79が名指すqstat logの置き場に対応する |

「探索していない範囲」には、範囲外の領域に加え、R-2の**範囲内の除外条件**を追記する必要がある。さらにraw JSON自体にrequest IDが必ず入るわけではないため、本文のID検索は改名されたコピーを網羅しない。名前列挙との併用で候補を探した、という限定が妥当である。

発見時の「pathとsha256」は今回は条件未成立であり、代替JSONのhashを埋める必要はない。日付付きinsightとREADME注記の2箇所は存在する。

## 総括

**must-fixはR-1〜R-3。** 中心結論「今回の探索ではrawとsha256を特定できなかった」は維持できるが、消失履歴・探索網羅性・完全表記の不在を強く断定した箇所は修正が必要である。

D1013は今回の個別注記を禁止していない。一般運用を新設する表現を外し、C14aの所在調査として残せばよい。pairの流用を誘う表現は認めず、P:193は明確に「別 request・別観測であり C14a の行に流用しない」としている。

`s5-diff.patch`の変更先5ファイルに、凍結claim-evidence・8月insight・pair receiptは含まれない。P:191の「判定値…と `[導出索引]` は…まま」、I:77–78の「判定の正否は本 wave の対象外」により、当時の判定を現行の正しさ認証へ昇格させても否定してもいない。正しさゲートの変更、新しい運用検査・台帳の追加もない。静的レビューのみ実施し、親の検査結果は本評価に含めていない。