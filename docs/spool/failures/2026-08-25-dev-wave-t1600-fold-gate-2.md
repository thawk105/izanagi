---
schema: izanagi-spool-v1
ledger: failures
authored: 2026-08-25
wave: dev-wave-t1600-fold-gate
seq: 2
---

## 新規

### {{F:gate-failure-without-child-evidence}}. 関門が赤を出しても、子の rc も出力も理由に残らず原因を追えなかった [手順漏れ] [テスト代表性]

- 事象: [T-1600] の fold 関門が段 9 の実 land を止めたが、receipt に残った理由は
  `fold gate JUnit cannot be parsed: [Errno 2] No such file or directory: ...` だけだった。
  関門が起動した子 process の returncode も stdout も stderr も理由文字列に入らない設計で、
  隔離 tree は後始末で消えるため、**親は原因特定の一次資料を land 直後に失った**。
  関門は正しく赤を出したのに、なぜ赤かを人が追えない状態だった。
- 根本原因: infra 失敗の理由を組み立てる経路が例外の文言だけを転記し、子の実行結果を捨てていた。
  親も敵対レビュー 2 本も、**関門が緑/赤を正しく出すか**は検査したが、
  **赤のときに診断できるか**を検査項目に入れていなかった。
- 恒久対応: infra 失敗 (JUnit 不在・parse 失敗・node 集合不一致・timeout・起動失敗) の理由へ
  子の returncode と stdout/stderr の末尾を必ず含める。長さは有界 (各 500 byte)、
  端末制御 byte は可逆 escape、`omitted_bytes` で切り詰め量を明示する
  (`tools/dev_wave_land.py` の `_fold_gate_diagnostic_tail` / `_fold_gate_pytest_diagnostic`)。
- 再発検知: 子が JUnit を書かずに非零 rc で終わったとき、理由に rc と両出力と escape 済み
  制御 byte が入り、かつ全体が有界であることを要求する回帰テスト
  (`orchestrator/tests/test_dev_wave_land.py::test_fold_gate_missing_junit_reports_bounded_escaped_child_output`)。

## 再発

### F334

- **再発: 2026-08-25** — [T-1600] の fold 関門が、**自分自身の land を止めた**。
  受入全走は 15708 passed / 0 failed で緑、`main_before == main_after` で main は 1 bit も
  動いていない。関門が隔離 tree で起動する test runner が JUnit を書かずに終わっていた。
  原因は関門の子環境に立てた `PYTHONNOUSERSITE=1` で、この host の pytest 実体は user site に
  あるため module が解決できない (実測: 有り = rc1 `ModuleNotFoundError` / 無し = rc0)。
  **ambient 注入を塞ぐための防壁が、関門の実行系そのものを塞いでいた。**
  F334 との共通点は「機構が一度も実データで動かないまま完成扱いされた」点であり、
  land 前に自分で捕まえた分だけ被害は小さい (F334 は land 後 5 日間気付かれなかった)。
  **本 wave が足す新事実は、親が dogfood を「やったつもり」になれる形である。**
  親は時間予算を 3 回実測しており、その意味で実データを通していた。しかし実測は
  `tools/run_tests.py` 経由であり、**関門が本番で使う raw な argv と環境は一度も
  end-to-end で通していなかった**。道具を挟んだ実測は、本番経路の live dogfood にならない。
  恒久対応は F334 の規律を変えず、その具体形として
  「関門が本番で組み立てる argv と環境そのもので、隔離 tree 相当の構成から
  成果物 (JUnit) が実際に生成されることを要求する end-to-end テスト」を同じ commit に置いた
  (`orchestrator/tests/test_dev_wave_land.py::test_fold_gate_real_argv_environment_create_junit_in_gitless_tree`)。
  あわせて、最初の fix が `PYTHONNOUSERSITE` を定数で設定したまま直後に `env.pop` で
  打ち消す形を採り、既存 assertion 2 箇所が実子環境を守らない恒真な guard へ変わっていた。
  親が独立に見つけて定数から消し、forced 集合と実子 env の双方で不在を積極的に要求する形へ
  置き換えた。**恒真な関門を潰すための wave が、同型の穴を自分の中に作りかけた。**

### F24

- **再発: 2026-08-25** — 同一 wave 内で `tools/dev_wave_wait.py producer` と背景 until ループの
  偽完了が **40 回以上**起き、過去の再発記録 (2026-08-24 の 3 回) を桁違いに超えた。
  内訳は段 6 レビュー A の待ち手、焦点走 5 本、変異 probe の待ち手 3 回、変異穴 fix 子の待ち手
  2 回、変異本走の待ち手 30 回以上、時間予算 fix 子の待ち手 17 回。
  張り直すたびに十数秒で偽完了する状態が続き、待ちが実質的に機能しなかった。いずれも rc=0・出力ゼロ・`.done` 不在で戻り、実際には
  producer が `ps` / `pgrep -af` で生存して走行を続けていた。恒久対応 (`.done` 出現と producer 死の
  両方で判定し、待ち手の rc も通知も信じない) がそのまま効き、実害はゼロだった。
  **本 wave の追加事実は、生産者側を親の背景 job に結び付けるか否かで被害が変わる点である。**
  焦点走 2 回目は `run_tests.py` を親の背景 job として直接起動していたため、親側 job の消失で
  出力を丸ごと失い、計算ノード側の submission dir から回収する羽目になった (compute job 自体は
  生き残っていた)。以後の焦点走・変異走を `nohup setsid` + `.done` file の detach 方式へ
  切り替えたところ、待ち手が何度落ちても走行も成果物も失われなくなった。
  **教訓の形: 走行を親の背景 job に結び付けず、必ず detach + `.done` にする。**
