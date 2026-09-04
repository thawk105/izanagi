## must-fix

1. **[real] lock helper の意味論は検査されるが、実 fixture がその lock を test 本体まで保持する配線は未検査。**  
   [plan:61](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2298-certified-evidence-lock/artifacts/stage2-plan-out.md:61) の全競合検査は helper を直接呼び、[plan:75](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2298-certified-evidence-lock/artifacts/stage2-plan-out.md:75) は wrapper が `"read"` / `"write"` を渡すことしか固定しない。例えば共通 fixture を次のように変異できる。

   ```python
   with _certified_evidence_lock_scope(...):
       metadataを読み evidence を復元
   # ここで unlock
   with ExitStack():
       yield evidence
   ```

   この変異では helper の正負例、wrapper-mode AST、writer 閉包 AST はすべて緑になり得る。現行では `yield` が lock 内にあることが安全性の本体である [test:1234](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2298-certified-evidence-lock/orchestrator/tests/test_p3_b4_raw_record_producer.py:1234)。

   修正案は、共通 fixture scope を実際に enter した状態で別 `os.open` の writer/readers が失敗する検査を加えること。少なくとも AST で「共通 scope の `yield` が lock context の内側」を固定する。

   **放置すると成果物:** M17/M18 の一時破壊を reader が観測し、受入の緑と certified 判定が実行順依存になる。

2. **[real] `evidence.json` の存在を seed 完了印にしているため、seed 失敗時には部分状態が公開される。**  
   プランは現在の `metadata_path.write_bytes(...)` を維持する [plan:19](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2298-certified-evidence-lock/artifacts/stage2-plan-out.md:19)、[test:1207](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2298-certified-evidence-lock/orchestrator/tests/test_p3_b4_raw_record_producer.py:1207)。`write_bytes` が `{` だけ書いて例外、または truncate 後に worker が終了すると、unlock 後の reader は `exists() == True` と判断して壊れた JSON を読む。metadata 作成前に seed が失敗した場合も、固定された `shared / "evidence"` に残骸が残り、再生成時の `home.mkdir(..., exist_ok=False)` が失敗し得る [test:355](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2298-certified-evidence-lock/orchestrator/tests/test_p3_b4_raw_record_producer.py:355)、[test:1191](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2298-certified-evidence-lock/orchestrator/tests/test_p3_b4_raw_record_producer.py:1191)。

   再現は metadata writer を「短い bytes を書いてから raise」するものへ差し替え、次の reader scope が seed を再試行できるか検査すればよい。unique staging root に seed を作り、同一 directory の一時 metadata を fsync 後に atomic rename して初めて ready とする設計が安全。

   **放置すると成果物:** 一度の seed 失敗で後続17 consumerも setup errorになり、受入の緑が失われる。

## nit

- **[refuted] 正常終了する参加者間では、`EX → UN → SH/EX` の非原子区間に壊れた状態を読む窓はない。**  
  metadata は seed EX 中に書かれ、reader は最終 `LOCK_SH` 取得後にだけ読む [plan:17](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2298-certified-evidence-lock/artifacts/stage2-plan-out.md:17)、[plan:22](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2298-certified-evidence-lock/artifacts/stage2-plan-out.md:22)。UN 後に M17/M18 writer が先に EX を取っても、reader はその復元と unlock まで待つ。別 `os.open` した競合 fd を使う方針 [plan:61](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2298-certified-evidence-lock/artifacts/stage2-plan-out.md:61) も、別 open-file description 間の競合を正しく検査している。

- **[real] SIGKILL 境界では M17/M18 の破壊状態が残る。**  
  M17 は receipt を上書きして Python `finally` で復元する [test:1621](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2298-certified-evidence-lock/orchestrator/tests/test_p3_b4_raw_record_producer.py:1621)、M18 も symlink 化後に `finally` で戻す [test:1652](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2298-certified-evidence-lock/orchestrator/tests/test_p3_b4_raw_record_producer.py:1652)。途中で process が終了すると kernel は EX を解放する一方、復元処理は走らないため、次の reader が破壊状態を読む。プランも既知限界として認識している [plan:121](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2298-certified-evidence-lock/artifacts/stage2-plan-out.md:121)。worker crash 自体を受入失敗とする契約なら許容可能だが、「次の test まで復旧」を要求するなら writer 二本を私有 copy に移す必要がある。

- **[refuted] producer 経由の追加 writer は、現在の certified seed では発火しない。**  
  seed は `terminal="commit"` [test:1191](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2298-certified-evidence-lock/orchestrator/tests/test_p3_b4_raw_record_producer.py:1191)。producer は execution-lock path を計算するが [producer:1596](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2298-certified-evidence-lock/orchestrator/campaign/p3_b4_raw_record_producer.py:1596)、`campaign_lock(...)` を取得するのは `terminal_record is None` の場合だけである [producer:1607](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2298-certified-evidence-lock/orchestrator/campaign/p3_b4_raw_record_producer.py:1607)。commit seed は terminal record を持つので、この分岐には入らない。

  WAL、campaign lock、receipt は `_snapshot_regular` による読取り [producer:448](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2298-certified-evidence-lock/orchestrator/campaign/p3_b4_raw_record_producer.py:448)。receipt 検証用の書込みは一時 directory [producer:1199](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2298-certified-evidence-lock/orchestrator/campaign/p3_b4_raw_record_producer.py:1199)、結果 artifact と rejection ledger は test 固有 publication root [producer:2085](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2298-certified-evidence-lock/orchestrator/campaign/p3_b4_raw_record_producer.py:2085)、[producer:663](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2298-certified-evidence-lock/orchestrator/campaign/p3_b4_raw_record_producer.py:663)。したがって他の15 consumer を writer に再分類する必要も、execution coordination file を seed 時に事前作成する必要もない。

- **[refuted、条件付き] AST 閉包検査は恒真ではなく、M17/M18 を捕捉できる。**  
  M17 の receiver は直接 `certified_evidence.on_receipt` [test:1621](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2298-certified-evidence-lock/orchestrator/tests/test_p3_b4_raw_record_producer.py:1621)。M18 は `Path(certified_evidence.admission.role_file)` を代入し、`with_name` 派生を rename/symlink/unlink する [test:1650](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2298-certified-evidence-lock/orchestrator/tests/test_p3_b4_raw_record_producer.py:1650)。代入先名への fixed-point taint 伝播を実装すれば両方捕捉できる。

  恒真になるのは、期待 writer 集合を検出結果そのものから生成する場合、または taint 起点を「現在 writer と宣言された引数」だけに限定する場合。プランは期待 map の明示列挙と両 fixture 名を起点にするので、その形は避けている [plan:74](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2298-certified-evidence-lock/artifacts/stage2-plan-out.md:74)。

  恒偽になるのは、任意の関数引数から返値へ taint を伝播する実装である。そうすると `_publish(..., certified_evidence)` の返値まで taint され、M01等の `Path(write.artifact_path).write_bytes(...)` [test:1318](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2298-certified-evidence-lock/orchestrator/tests/test_p3_b4_raw_record_producer.py:1318) が誤って writer になる。`Path`/属性/`with_name` の明示された導出だけを伝播し、`_publish`・`_assert_write` の返値を伝播しなければよい。

- **[real] AST 検査は direct mutation 限定で、helper 内へ隠した共有書込みは SURVIVED になる。**  
  プラン自身もこの限界を認めている [plan:81](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2298-certified-evidence-lock/artifacts/stage2-plan-out.md:81)。例えば将来 `corrupt_for_test(certified_evidence.on_receipt)` の内部で書けば、呼出し receiver に mutator 名がないので捕捉しない。現在の producer 閉包は上記の現物確認で安全だが、検査名とコメントには「対象 test 内の直接 path mutation の閉包」と明記すべき。

- **[real] 変異の kill 可否は次のとおり。**

  | 変異 | 判定 | 帰属 |
  |---|---|---|
  | (a) writer→SH | KILLED | writer保持中の reader NB 検査が固有に赤 |
  | (a-2) writer wrapper→read | KILLED | hard-coded wrapper-mode assertion が赤 |
  | (b) reader lockなし | KILLED | reader対writer負例に加え、seeded-reader の `LOCK_SH` 要求検査も赤。帰属は非一意 |
  | (c) M17/M18宣言なし | KILLED | 両fixture名をtaint起点にし、期待mapを固定した場合のみ閉包検査が赤 |
  | (d) double-checkなし | KILLED | EX取得直後に競合metadataを作る反例で seed callback が呼ばれ赤 |
  | (e) reader→EX | KILLED | 二reader正例と no-EX 検査の双方が赤。帰属は非一意 |

  表の根拠は [plan:87](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2298-certified-evidence-lock/artifacts/stage2-plan-out.md:87)。ただし、前述の「共通 fixture が helper を test 本体まで保持しない」変異は現状 SURVIVED である。

- **[refuted、波及あり] M17/M18 の引数名変更では node id は変わらない。**  
  関数名と decorator は変わらず [test:1605](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2298-certified-evidence-lock/orchestrator/tests/test_p3_b4_raw_record_producer.py:1605)、[test:1633](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2298-certified-evidence-lock/orchestrator/tests/test_p3_b4_raw_record_producer.py:1633)、台帳 key は fixture 引数ではなく `item.nodeid` から作られる [conftest:1512](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2298-certified-evidence-lock/orchestrator/tests/conftest.py:1512)。既存17 keyと正確な nodeid 指定の焦点走は不変。

  一方、新しい lock 検査6本は新規 node なので、file 全体を指定する焦点走の集合は増える。台帳に未登録の新規 node は unknown-cost fallback となる [conftest:1591](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2298-certified-evidence-lock/orchestrator/tests/conftest.py:1591)。親資料の「file単位 shard」前提では同じ shard に残るが、同 shard 内の順序と所要には波及する。

  実装後は、17関数の assertion 部分の diff、変更前後の collect-only nodeid集合、17 node の焦点走を明示的に照合すべき。これがプランの「期待値・受理集合を変えない」[plan:27](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2298-certified-evidence-lock/artifacts/stage2-plan-out.md:27) を実測へ落とす最小確認になる。

## 親 brief への指摘

- **[real] 「17 consumer 合計 ≈82秒」は、掲載された丸め値と一致しない。**  
  [rulings-verbatim:127](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2298-certified-evidence-lock/rulings-verbatim.md:127) のうち実際の17 consumerを加算すると **84.5秒**。各値の0.1秒丸めでは2.5秒差を説明できない。raw junit の再集計値を記すか「約85秒」へ直すべき。

- **[real] junit 合計を、そのまま lock の critical-path wall と一般化してはならない。**  
  fixture は setup 中に EX を取得し、teardownまで保持する [test:1178](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2298-certified-evidence-lock/orchestrator/tests/test_p3_b4_raw_record_producer.py:1178)。したがって各 node の total には取得待ちも保持時間も入るが、複数 worker の待ち区間は重なるため、17 total の合計は critical-path wall を二重計上し得る。84.5秒は現走の累積 lock-hold 時間の上界にはなるため「現走の保持仕事が258秒ではない」は支持するが、「鎖のwallが約82秒」とは言えない。鎖の wall は親が進めている timeline の取得・解放時刻で確定すべき。

- **[refuted] 「fixture 内の lock 待ちは setup に含まれ、`pytest_runtest_protocol` wrapper 外側の待ちは junit に含まれない」という境界は正しい。**  
  fixture の lock 取得は yield 前 [test:1188](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2298-certified-evidence-lock/orchestrator/tests/test_p3_b4_raw_record_producer.py:1188)。対して real-repo lock は protocol の `yield` より外で取得される [conftest:2073](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2298-certified-evidence-lock/orchestrator/tests/conftest.py:2073)。この区別を使った親 brief の P4 は妥当。

- **[refuted] `real_repo_fixture_lock` の流用却下は正しい。**  
  同 lock の資源は `parent` / `ccbench` のみ [conftest:928](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2298-certified-evidence-lock/orchestrator/tests/conftest.py:928)、identity は Git common-dir [conftest:992](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2298-certified-evidence-lock/orchestrator/tests/conftest.py:992)。pytest shared tmp の evidence inode とは別資源なので、自前 `fixture.lock` を残す provisional 裁定が正しい。

- **[real] 成果物欄の「writer 宣言 (marker)」は B2 と不整合。**  
  親 brief は marker と書く [handoff:51](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2298-certified-evidence-lock/handoff.md:51) 一方、採用プランは別 fixture [plan:31](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2298-certified-evidence-lock/artifacts/stage2-plan-out.md:31)。実装者の迷いを避けるため `certified_evidence_writer fixture` に直すべき。

## 総括

設計の中心である「seed EX + double-check → 明示 UN → reader SH / writer EX」は、正常な協調実行では正しい。producer の現物確認でも、commit seed に対する共有 path writer は M17/M18以外に増えない。

ただし、段2プランはまだ author-ready ではない。必須修正は、実 fixture の lock 保持範囲を検査することと、seed 完了印を transactional にすることの2点。指定変異(a)〜(e)自体は殺せるが、fixture-to-helper の配線切断は現テスト案を生き残る。read-only review のためテスト実走・変更は行っていない。