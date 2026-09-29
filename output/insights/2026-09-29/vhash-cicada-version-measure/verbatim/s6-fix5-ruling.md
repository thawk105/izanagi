# 段 6 fix 5 巡目の裁定 (2026-09-29 07:2x JST)

入力: codex/out/s6-focus3.md (焦点再レビュー 3 本目、fix3+fix4 全体、NO-GO、must-fix 1)。base = fix 4 統合 commit bf7e134ea。
H1〜H3・J2〜J6 closed。J1 partial (下記 K1)。should (256 要素配列の worker 上限) は一次資料の適用範囲に「総 worker ≤ 256、今回 48」と書いて閉じる (K2 で実行時検査も足す)。

| # | 所見 | 判定 | fix |
|---|---|---|---|
| K1 | 移設後の MinRts 公開計測が「cicadaLeaderWork() の前後で MinRts の値が変わったときだけ」記録し、同値の再公開 (長い tx で境界が止まっている間の公開) を落とす。境界年齢の標本が消え、公開間隔が合算される | real、must-fix (待機型条件の中心の現象) | 公開の判定を値の変化でなく公開イベントそのものにする。stock の cicadaLeaderWork() (util.cc:281-323) は全 worker の GCFlag が 1 のときだけ MinWts/MinRts を store し、直後に全 GCFlag を 0 に戻す。leader 自身の GCFlag[0] は leader thread の mainte() でしか 1 にならず、leaderWork() の実行中には変わらない。したがって `leaderWork()` で「呼び出し前 GCFlag[0]==1 かつ呼び出し後 GCFlag[0]==0」を公開ありと判定し、そのとき MinRts (公開値) と rdtscp で境界年齢・公開間隔を記録する。値が同じ公開も 1 件と数える。採時点は store 直後でなく関数復帰後 (flag を戻す 48 回の store を含む) であることを patch comment と一次資料の限界に書く |
| K2 | 固定長 256 の統計配列に総 worker 数の実行時上限検査が無い | real、should | 計器が有効なとき、総 worker 数 (TotalThreadNum) が配列長を超えたら起動時に明示的に終了する (既定 build に影響しない位置で) |

test: K1 の判定条件 (GCFlag[0] の前後) が patch に在ることを文字列で固定する test と、既定前処理一致 test の維持。
変異の事前登録の追加:
- MUT-10 (K1): 公開判定を「MinRts の値が変わったとき」へ戻す → K1 の固定 test が KILLED
