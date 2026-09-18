## 評価の前提

`M:行` は指定の `mocc-transaction-e9e477ca.cc`、`plan:行` は `s2-plan-v2.md` を指す。指定資料を静的に検査した。編集・build・pytest・実走は行っていない。

結論は、**(a) の存在論証は条件付きで成立するが、現行 verifier と指定 producer の組合せでは、計画が期待する discriminator の識別結果に到達できない**。これは診断 patch のアルゴリズム上の問題とは別の、計画上の必須修正である。

## must-fix

**MF1 — 現行 verifier の X/P 存在条件を計画が取り落としている。**

- **根拠:** `orchestrator/verifier/model.py:77–82,450–467` は X/P の `evidence-present` を `integrity.clean()` の条件に含める。`core.py:53–59` が source assessment を接続する。一方、指定 M の validation／writePhase に X/P emitter はなく、plan:240,247 は D1686 の X/P patch を明示的に除外する。`--ccbench-root` を渡すだけでは計装は追加されない。source assessment が取得不能でも `unavailable` となり、同条件を満たさない。
- **成果物への影響:** cycle 無しは `indeterminate`、cycle 有りは `non-serializable` でも integrity は clean にならない（model.py:503–515）。discriminator は `:498–499,600–605` により `indeterminate` となり、腕 A の `supported`／`contradicted` と腕 B の「判定可能な 0/K」を予定どおり得られない。
- **是正案:** batch 前に producer と現行検査の適合を解決する。現スコープを維持するなら、取得可能なのは raw cycle と識別不能理由まで、と完了条件を下げる。識別結果を必須にするなら、X/P 計装を含む producer と discriminator の入力文法・束縛を両立させる設計へ戻す必要がある。**verifier の緩和、別 source を指すこと、X/P 行の除去による見かけの適合は不可。**

  後者は単純な patch 追加では済まない。discriminator の標準 trace parser は C/R/W/E 以外を拒否する（`:273–309`）。X/P が発火した走も保存・分類できる計画が必要である。I の不在は現行 X/P 存在 gate の直接条件ではないが、write-intent の実証済みとは書けない。

**MF2 — 親 brief の discriminator 対応表と「どちらも実装由来」は成立しない。plan §2 の訂正を親・insightへ反映する必要がある。**

- **根拠:** discriminator は W 行から `(key, version) → producer` を作り（`:284–298`）、rw reason の **reader version** で expected を引く（`:575–592`）。observed は L 行の producer（`:342–362`）。M:87 は保存済み `read.body_` を decode する。比較結果の上限は discriminator:648–653 に明示される。
- **成果物への影響:** 現状の対応表では、stamp の一致・不一致を (ii)／(i) の実行証拠へ誤って昇格し、D2114 が未確定とする原因分岐を誤って閉じる。
- **是正案:** 次の意味だけを採用する。

| 結論 | 言えること | 排除できないもの |
|---|---|---|
| `supported` | 報告対象の全 comparison で reader-version producer と stamp producer が一致 | (ii) 以外の機序、stamp 外の混合、hook の共通した誤投影、版順序仮定の不成立 |
| `contradicted` | 対象 comparison に producer 不一致がある | 実装の版／payload 不整合と hook の取り違えの区別。不一致が必ず「新版」であること |
| `indeterminate` | blocker により識別不能 | (i)／(ii) の肯定・否定 |
| `no-g2` | 有効入力で対象 cycle がない | 間隙の不存在、根因候補の否定 |

writer は**ローカル write body に stamp を置いてから共有 body へ memcpy**し、その後版を publish する（M:1165–1196）。したがって新版 stamp が旧 tidword と共存する区間は source 上存在する。S 行は publish 後の共有 stamp を確認するが（M:100–110,1197–1199）、reader が読んだ時刻の版と stamp を一括観測していない。

分岐 2 では、reader の版だけの誤記録は `contradicted`、版と witness の整合した誤帰属は `supported` と両立する。分岐 3 では、read-from が正しくても successor の版順序が誤れば `supported` と誤った rw 辺が両立する。**純粋な版順序仮定の誤りだけで stamp 不一致が必然的に生じるわけではない**が、`contradicted` も分岐 3 全体を検証するものではない。

**MF3 — 親 brief の「診断 0/K ⇒ 必要性確認 ⇒ この cell の根因」は撤回が必要。**

- **根拠:** 親 scope 2・完了判定に対し、plan:243,306–314 は二箇所同時変更と有限標本の限界を正しく指摘している。0/24 の片側95%上限は約0.117であり、ゼロ率の証明ではない。
- **成果物への影響:** 有限走の未再現を根因確定と誤記し、追加 abort による実行機会・競合・温度変化を候補機構の必要性と取り違える。
- **是正案:** 「名指し条件で診断変更後に未再現／検出率差を観測」に限定する。二箇所の寄与は分離できない。実 commit 数も曝露量として併記し、G2 が減った場合に処理機会の減少を無視しない。MF1 が未解消なら、判定不能走を0/Kの分母へ入れない。

## should

**S1 — P1 は成立するが、成立条件と tid 差1の条件を明文化する。**

- **根拠:** M:739,834–888,989–1039,1118–1131。
- **成果物への影響:** 条件を省くと、存在可能な順序を固定 cell の全試行や歴史的5件の実際の順序と誤認する。
- **是正案:** 次の被覆境界を順序論証に含める。

| 検査点 | 検算 |
|---|---|
| CLL sort／canonical mode | cold・RLL空・各 write set が別 key 一要素なら、各 CLL は初回施錠まで空。sort と順序修復は二者間の交差した read/write を禁止しない。 |
| W の y validation | R の y 施錠より前に版・counter 検査が済めば通る。以後、W は y を再検査しない。 |
| R の x validation | M:1010 が旧版を取得し、W の publish・x unlock 後に M:1024 が空き counter を取得する組合せを、既存検査は拒否しない。 |
| `max_rset_` | M:1038 は再取得した版を最大値に取り込むだけで、保存版との再比較ではない。W の新版を取り込んでも abort しない。 |
| commit | M:1215–1220 により両者が writePhase へ進める。旧 y を読んだ W→R、旧 x を読んだ R→W の rw cycle が成立する。 |

`NO_WAIT_LOCKING_IN_VALIDATION=1` は運用資料にあるが、指定 M にその条件分岐はない。lock 内部のマクロ効果は射影外で未確認。ただしこの存在例では**各 writer の施錠対象に競合 lock がない**ため、競合時の wait／no-wait の違いは例を排除しない。

`ThLocalEpoch` 更新は write lock 取得後、read validation 前（M:1003–1006）。同じ global epoch を採取する例は可能であり、更新自体は版・counter の一括検査にならない。R が M:1038 で W の `(e,t)` を最大版として取り込み、他の read/write 版・`mrctid_+1`・local epoch がそれを上回らず、桁あふれがなければ、R は `(e,t+1)` を選べる。**同 epoch・tid差1は可能な帰結であって必然ではない。**

幅について、R の版 load→counter load は、通常の最適化を仮定すれば比較・分岐を含む**数〜数十命令程度という概算**までである。逆アセンブル未確認なので測定値にはできない。W の publish→unlock には S 出力、残り write、E 出力、CLL 走査が挟まる（M:1197–1207）。したがって「数命令だけの窓」とは言えず、R の停止・再スケジュールも含めて上記順序は排除されない。

**S2 — (i) の発生と、(i) を持つ試行の commit を分ける。**

- **根拠:** M:280–364,1010–1038。
- **成果物への影響:** cold 読みの時間的重なりだけで commit 済み不整合を説明すると、validation が本来拒否する走まで根因証拠に数える。
- **是正案:** 本 cell で新規共有読取が cold loop に入る条件は、対象が local read/write set に未登録、RLL に不在、温度が閾値未満である、と記す。

旧 T0 のまま新 body を取得する候補では、M:322 の検査後に writer が施錠し、body copy が重なり、M:350 が publish 前の T0 を再読する必要がある。writer が先に lock を持っていれば loop 先頭で待機または abort する。

この **read loop の脱出自体は (ii) と独立**である。一方、同じ writer の更新に対して保存版T0のまま commit するには、通常の検査では次の区別になる。

- validation の版取得までに publish 済みなら版不一致で拒否。
- counter 検査時にも writer が保持中なら拒否。
- その二観測間に publish と unlock が済む場合が (ii)。

reader 自身も x を書く場合の counter 例外は一般的な救済にならない。自身の x lock を得るには外部 writer の解放を待つため、その更新版を先行する版比較が検出する。以上は正常な版進行・lock 動作を前提とした候補の検算である。

hot／RLL 読取は取得した lock が copy 中に保持される点で cold と異なる。ただし後の `lock()` は順序修復で既存 CLL を解放しうる（M:834–858）。「hot read は commit まで常に保持され、(ii) と無関係」とまでは一般化できない。

**S3 — 診断 patch は validation 再読＋cold abort に固定し、保証を attempt 単位に限定する。**

- **根拠:** plan:188–234、M:322–354,364,1059–1077。
- **成果物への影響:** retry と abort の選択で受理される snapshot、再試行、温度・RLL の履歴が変わり、G2率の解釈も変わる。
- **是正案:** plan の推奨である abort 案を採る。「同じ既存観測を固定した場合に追加拒否する」と記し、実行全体の commit 集合や件数の単調減少は主張しない。

validation 再読は、問題の unlock を観測した後に新版を検出する追加拒否である。cold retry は、stock が後の validation で拒否したはずの旧 snapshot を別 snapshot に取り直して commit する経路を持つため、厳密な「abort追加のみ」ではない。

retry の `continue` は既存の M:322 に戻り、M:331 の待機時 abort も残す。新しい lock 取得順序は導入しないが、既存経路にも待機・競合の継続があるので、無限 spin／starvation の不存在は証明できない。abort 案は追加待機を導入しない。

なお cold abort 案は M:364 の read-set 登録前に戻るため、対象 read は `construct_RLL()` の温度更新・失敗read登録の対象にならない。診断として直ちに不正ではないが、既存 validation abort と同じ適応挙動ではなく、率への介入として記録する。

## nit

**N1 — trace の行位置は壊さないが、integrity 実証済みとは言えない。**

- **根拠:** plan:238–240、M:1134–1205、parse.py:365–440、D1686。
- **影響:** 提案位置への挿入だけなら C/R/W/E の件数・連続性は変わらず、追加 abort は txid 採番前なので欠番を作らない。配置修正は不要。
- **是正案:** 「静的に framing を壊す変更なし、実 binary 未検証」と記す。元ファイルに `#line` はない。ただし MF1 対応で X/P patch を追加する場合は、この評価を再利用せず `#line` と検査位置を再確認する。X/P/I 違反0と emitter 不在は別である。

**N2 — 親の「実測した前提」は、実測・静的推論・仮説に分ける。**

- **根拠:** T-1892 results:110–143,164–179、運用事実、M:68–81,347–350,1165–1196、plan §2・§7。
- **影響:** plan の限定を採用すれば追加実装は不要。親の語彙を残すと、観測被覆を過大表示する。
- **是正案:** 以下のように分類する。

| 主張 | 評価 |
|---|---|
| 歴史的5件が長さ2・両辺rw・同epoch・tid差1 | 指定結果で確認できる観測事実。候補との形の整合まで。 |
| 5件が (a) で起きた | 未実測。版／counter の取得時刻は記録されていない。 |
| VAL_SIZE=4で64 byte、stampはid領域 | 運用投影の構造説明。今回のbinaryでの独立確認ではない。 |
| stampは原子的に読まれる | 整列だけでは copy の機械命令幅を確定できない。共有body copyと後段decodeを区別する。 |
| hot/cold の割合 | 未実測。アクセス頻度とMOCC温度は同一でない。 |
| 小valueほど発生しやすい／validation窓に無関係 | いずれも率について未実測。条件式にvalue sizeがないことまで。 |

**N3 — scope 0 の driver import 選択は妥当だが、副作用なしは未確認。**

- **根拠:** plan:120–160、parse.py:71、親の hydrate 失敗投影。
- **影響:** `source_digest` の import 成功だけでは、実際に失敗した推移依存の読込可能性を確認できない。いずれも後続 hydrate の失敗を成功に変えるものではないため、違いは主に早期診断の被覆である。
- **是正案:** driver import を維持し、実際の hydrate 呼出までの契約確認を行う。指定射影には driver 本体と import closure がないため、重い処理・副作用・import所要時間は未確認とする。`parse.py:71` を触らない判断は妥当であり、この局所的な interpreter 修正のために verifier を変更する必要はない。

## 総括

**must-fix は3件。**

(a) の順序論証は **成立**。cold・RLL空・競合しない write lock 取得等を満たす存在例であり、固定 cell や歴史的5件でその順序が実行されたことは未実測である。

**診断 patch は validation 再読＋cold abort 案を条件付き採用推奨。** ただし現行 verifier の X/P 存在条件との不適合を解決するまで、予定された識別結果・0/K評価を得る計画としては採用できない。

verifier／discriminator の受理集合は変更せず、G2のrc=1を保持する。T-1892の5/42とT-1943のno-g2は各旧束縛で保持し、今回の適合問題を理由に遡及して無効化しない。
