## 所見

**欠陥2件の同定と腕間比較を残す境界は妥当です。欠陥1は hash で解決した契約の prefix を使い、欠陥2は案Aで局所修正することを推奨します。** ただし「受理集合は変わらない」「D1876が撤去を直接認可している」という説明は避けるべきです。根拠は以下に示します。

これは静的検査の所見です。編集・テスト実行・実成果物の再解析は行っておらず、今回の効果量も読んでいません。

## 欠陥同定の検証

**欠陥1は正しく同定されています。** consumer は先頭2語を固定し、その直後だけを実行対象として扱います。一方、事前登録は Pegasus 契約を固定しており、登録簿は空 prefix を正当な値としています。契約どおりの直起動が拒否される実装です。根拠：[t1998_stock_inline_pair.py:635](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2589-consumer-real-artifact-repair/orchestrator/campaign/t1998_stock_inline_pair.py:635)、[env_contract.py:106](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2589-consumer-real-artifact-repair/orchestrator/campaign/env_contract.py:106)、[事前登録.md:84](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2589-consumer-real-artifact-repair/docs/t1998-balanced-stock-inline-preregistration.md:84)。

**欠陥2も正しく同定されています。** producer は3キーの identity 射影に `version` を加えた別の manifest を hash しますが、WAL の `toolchain` には identity 射影を記録します。consumer の等式は異なる入力の hash を比較しています。環境差や JSON の整形差が原因ではありません。根拠：[buildcache.py:1243](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2589-consumer-real-artifact-repair/orchestrator/campaign/buildcache.py:1243)、[buildcache.py:2518](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2589-consumer-real-artifact-repair/orchestrator/campaign/buildcache.py:2518)、[pipeline.py:2062](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2589-consumer-real-artifact-repair/orchestrator/campaign/pipeline.py:2062)。

**腕間比較は欠陥ではありません。** 両 arm が記録した、同じ意味の full-version digest 同士を比較しています。腕内再導出とは独立して残すべき検査です。今回これが通ったことは親の実測記録に依拠します。根拠：[t1998_stock_inline_pair.py:1280](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2589-consumer-real-artifact-repair/orchestrator/campaign/t1998_stock_inline_pair.py:1280)、[実測README.md:114](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2589-consumer-real-artifact-repair/output/insights/2026-09-13_t2557-balanced-stock-inline/README.md:114)。

指定範囲の静的照合では、第3の実成果物非互換は見つかりませんでした。親の「2件だけを無効化して受理に到達」という観測とも整合します。ただし、これは将来の全成果物について欠陥不存在を証明するものではありません。根拠：[実測README.md:134](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2589-consumer-real-artifact-repair/output/insights/2026-09-13_t2557-balanced-stock-inline/README.md:134)。

合成 fixture が両方を隠したという説明も妥当です。fixture は実 producer と異なる `version` 入り manifest を自己 hash し、run command に固定 prefix を付けています。根拠：[test_t1998_stock_inline_pair.py:97](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2589-consumer-real-artifact-repair/orchestrator/tests/test_t1998_stock_inline_pair.py:97)、[同:345](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2589-consumer-real-artifact-repair/orchestrator/tests/test_t1998_stock_inline_pair.py:345)。

## 欠陥1の是正

**親案は最小かつ十分です。** 既存の `_arm_decision` に渡される digest を用い、次の値を既存 helper の要求 prefix に渡せば足ります。

```python
env_contract.resolve_by_contract_sha256(
    environment_contract_sha256
).contract.numactl
```

返り値は契約そのものではなく `GenerationEntry` なので、`.contract` が必要です。digest は campaign lock と arm の commit に既に照合されています。根拠：[env_contract.py:881](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2589-consumer-real-artifact-repair/orchestrator/campaign/env_contract.py:881)、[t1998_stock_inline_pair.py:739](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2589-consumer-real-artifact-repair/orchestrator/campaign/t1998_stock_inline_pair.py:739)、[同:1138](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2589-consumer-real-artifact-repair/orchestrator/campaign/t1998_stock_inline_pair.py:1138)。

空 prefix なら先頭語、非空なら厳密一致した prefix の直後を実行対象とするだけです。その語と configure の build directory 配下の実行ファイルとの一致検査は残ります。したがって、任意の wrapper や「引数中に期待 binary があればよい」という受理には広がりません。根拠：[t1998_stock_inline_pair.py:638](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2589-consumer-real-artifact-repair/orchestrator/campaign/t1998_stock_inline_pair.py:638)、[同:802](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2589-consumer-real-artifact-repair/orchestrator/campaign/t1998_stock_inline_pair.py:802)。

`lookup(env_tag)` は現在有効な契約を返します。hash 解決は全世代から記録された契約を選び、未知・非一意・一度も有効化されていない契約を拒否します。Pegasus の現行2世代は calibration だけが異なり prefix は同じですが、**同じ prefix が得られることと、測定時の契約に束縛されることは別です。** 過去成果物の解析には hash 解決が適切です。根拠：[env_contract.py:270](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2589-consumer-real-artifact-repair/orchestrator/campaign/env_contract.py:270)、[同:792](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2589-consumer-real-artifact-repair/orchestrator/campaign/env_contract.py:792)、[同:881](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2589-consumer-real-artifact-repair/orchestrator/campaign/env_contract.py:881)。

`linux-baremetal` の登録値は既存 literal と同じなので、契約が正常に解決される限り、**欠陥1に関する prefix／実行対象判定は不変**です。consumer 全体については案Aでも受理集合が変わるため、「1 bitも変わらない」とは言えません。また、v1の環境 pin は引き続き Pegasus です。根拠：[env_contract.py:292](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2589-consumer-real-artifact-repair/orchestrator/campaign/env_contract.py:292)、[事前登録.md:145](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2589-consumer-real-artifact-repair/docs/t1998-balanced-stock-inline-preregistration.md:145)。

空 prefix の literal 固定や2種類の prefix の無条件許可は、契約との対応を失います。親案より小さく、同じ意味を保つ案はありません。D924の趣旨にも hash 解決が合います。根拠：[verbatim-rulings.md:49](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2589-consumer-repair/verbatim-rulings.md:49)。

## 欠陥2の是正

| 案 | 評価 |
|---|---|
| **A** | **推奨。** 誤った腕内再導出だけを撤去する。manifest の存在、digest の形式、腕間の manifest／digest 一致、`result.toolchain` 一致は残す。 |
| B | full manifest の再検証は可能になるが、今回存在しない証拠を producer に追加し、再測定する変更になる。本件で要求する強い理由はない。 |
| C | 非推奨。再測定に加え、意図された full-version digest の意味を変え、腕間比較が捉える情報も減らす。 |
| D | Aより良い局所案はない。欠落した `version` を現在の環境から再観測しても、測定時の証拠にはならない。 |

根拠：[t1998_stock_inline_pair.py:882](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2589-consumer-real-artifact-repair/orchestrator/campaign/t1998_stock_inline_pair.py:882)、[同:1280](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2589-consumer-real-artifact-repair/orchestrator/campaign/t1998_stock_inline_pair.py:1280)、[pipeline.py:2065](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2589-consumer-real-artifact-repair/orchestrator/campaign/pipeline.py:2065)、[実測README.md:104](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2589-consumer-real-artifact-repair/output/insights/2026-09-13_t2557-balanced-stock-inline/README.md:104)。

Aの非保証範囲は、既存の説明箇所に次のように明記すれば十分です。

> consumer は記録された full-version digest の腕間一致を確認する。full-version manifest が成果物にないため、digest の再計算、および記録された identity 射影との暗号学的な対応は検証しない。

これは、両腕の digest を同じ別値に置き換えた場合、この検査では拒否できなくなることも含みます。既存の共有 digest 変異テストは、誤った等式を仕様化しているため、その期待を維持してはいけません。fixture の2射影を producer に合わせ、腕間 drift の拒否は残すのが局所的な修正です。根拠：[test_t1998_stock_inline_pair.py:980](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2589-consumer-real-artifact-repair/orchestrator/tests/test_t1998_stock_inline_pair.py:980)、[同:990](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2589-consumer-real-artifact-repair/orchestrator/tests/test_t1998_stock_inline_pair.py:990)。

D1876は「保証しない範囲を明記する」という扱いの前例です。ただし、その決定は検査を追加せず現状維持するものであり、既存検査の撤去を直接認可した前例ではありません。根拠：[verbatim-rulings.md:52](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2589-consumer-repair/verbatim-rulings.md:52)。

## 規律2の評価

**提示された局所修正の範囲では、案Aは規律2に抵触しないと判断します。** ただし、「一度も成立していない」「§6にない」という理由だけでは不十分です。過剰な代理条件でも正しさ防壁に触れる場合があることはD144が示しています。根拠：[verbatim-rulings.md:15](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2589-consumer-repair/verbatim-rulings.md:15)。

本件で決定的なのは、撤去対象が producer の証拠の意味を取り違えた等式であり、**anomaly を出した variant や非 serializable な実行を許す変更ではない**ことです。認証済み campaign の admission、全記録の anomaly／verdict 検査、abort 拒否は残ります。事前登録§7も規律2との接続を anomaly の即 reject として明記しています。根拠：[t1998_stock_inline_pair.py:1003](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2589-consumer-real-artifact-repair/orchestrator/campaign/t1998_stock_inline_pair.py:1003)、[同:1205](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2589-consumer-real-artifact-repair/orchestrator/campaign/t1998_stock_inline_pair.py:1205)、[事前登録.md:183](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2589-consumer-real-artifact-repair/docs/t1998-balanced-stock-inline-preregistration.md:183)。

producer 側にも、各 build の identity／full version と事前観測との一致、および trace/perf 間一致の検査が存在し、Aでは変更されません。ただし、それを consumer による保存済み全文の再検証と同一視してはいけません。根拠：[buildcache.py:2502](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2589-consumer-real-artifact-repair/orchestrator/campaign/buildcache.py:2502)、[pipeline.py:2040](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2589-consumer-real-artifact-repair/orchestrator/campaign/pipeline.py:2040)。

Aは形式的には拒否述語の撤去であり、受理集合を広げます。正確な説明は、**事前登録の identity と推定規則、実行の正しさ検査を維持して、誤った証拠照合を除く**、です。§1の2つの sha は事前登録文書の bytes を束縛しており、consumer の全述語を固定する hash ではありません。文書と2定数を維持することは妥当ですが、それだけで修正の正当性を証明するわけではありません。根拠：[事前登録.md:18](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2589-consumer-real-artifact-repair/docs/t1998-balanced-stock-inline-preregistration.md:18)、[同:162](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2589-consumer-real-artifact-repair/docs/t1998-balanced-stock-inline-preregistration.md:162)。

## 総括

**親案の欠陥1修正と案Aを採用するのが適切です。** producer・事前登録bytes・2つのsha定数は維持し、consumer の2箇所と対応する既存fixture／説明だけを直す範囲で足ります。腕間比較は残し、全文digestの再検証を保証しないことを明記してください。根拠：[t1998_stock_inline_pair.py:635](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2589-consumer-real-artifact-repair/orchestrator/campaign/t1998_stock_inline_pair.py:635)、[同:895](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2589-consumer-real-artifact-repair/orchestrator/campaign/t1998_stock_inline_pair.py:895)、[同:1280](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2589-consumer-real-artifact-repair/orchestrator/campaign/t1998_stock_inline_pair.py:1280)。

本所見は修正案への静的評価であり、修正版consumerの受理やpytest成功を報告するものではありません。