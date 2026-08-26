---
schema: izanagi-spool-v1
ledger: failures
authored: 2026-08-26
wave: dev-wave-t1719-nproc-parity
seq: 2
---

## 新規

### {{F:pipefail-grep-q-silently-skips-a-gate}}. `pipefail` 下の `| grep -q` が、一致していたのに関門を素通りさせた [恒真ゲート] [手順漏れ]

- 事象: `tools/pegasus/submit_t126_qualification.sh` の
  「assume-unchanged / skip-worktree のソースを禁じる」関門が非決定的に発火しなかった。
  対象 test は期待した診断文言ではなく後段の別の関門の文言で落ち、
  同じ test が別の走行では通っていた。
- 根本原因: 関門が `if git ls-files -v | grep -Eq '^[a-zS]'; then` と書かれ、
  script は `set -Eeuo pipefail` を持つ。`grep -q` は最初の一致で即座に終了するため、
  まだ書き込み中の `git` が SIGPIPE で死んで 141 を返す。`pipefail` により pipeline の
  終了コードが 141 になり、**一致していたのに `if` が偽になる**。
  親が login node で 5 回試し 5 回とも再現した
  (`seq 1 2000000 | grep -Eq "^1$"` が 5 回とも rc=141 で不一致判定)。
  素通りするかは出力量と scheduling に依存するので非決定的である。
- 恒久対応: {{D:study-env-parity-toward-production}} ではなく実体の修正で閉じた —
  `git ls-files -v` を単独実行して終了コードを明示的に捕まえ (非 0 なら fail-closed)、
  判定は here-string から `grep` させて producer process を作らない形にした。
  同型は repo に 3 箇所あるが発火が観測されたのは 1 箇所だけなので局所修復に留めた
  (`tools/pegasus/t126_qualification.sh` の `find ... -print -quit | grep -q .` は同型だが未観測、
  `tools/pegasus/certify_calibration.sh` は grep が file を直接読むので該当しない)。
- 再発検知: 関門の診断文言が stderr に出ることを要求する負例と、clean な repo で通過する正例。
  後段の別の関門で弾かれた場合は不合格とする。

### {{F:even-split-of-an-uneven-budget-kills-the-heavy-half}}. 仕事量が偏る 2 分割に予算を均等配分し、重い側が必ず殺された [計測汚染] [測定の交絡]

- 事象: 対測定の本走が `JUnit is missing or unsafe: child_returncode=-15` で止まった。
  stdout はテストが 100% まで到達しており、直後に子が SIGTERM されていた。
- 根本原因: arm の制限時間を shard へ均等に割っていた
  (`timeout = available / remaining_shards`)。2 つの shard の仕事量は均等でなく、
  重い側は軽い側の約 2 倍である。受領証の実数で計算すると、
  **3 つの arm すべてで重い shard の配分が自分の実測所要を下回っていた**
  (-1.9% / -11.5% / -11.3%)。arm 全体には 25% + 90 秒の余裕があったが、
  均等割りがそれを軽い shard へ寄せていた。先行する 3 走が通ったのは本走のノードが
  較正走より僅かに速かっただけで、一つの arm は配分 203.75 秒に対し実測 208.40 秒であり
  **最初から必ず殺される値**だった。
- 恒久対応: {{D:study-shard-budget-proportional}}。較正走の実測 per-shard 所要へ比例配分する。
- 再発検知: 均等割りなら重い shard が不足する非対称な合成 3 組で、
  比例配分では実測所要を下回らないことを検査する負例と、
  両 shard の相対余裕が一致することを検査する正例。

### {{F:tests-that-assert-the-environment-not-the-property}}. 守りたい性質でなく環境の偶然を assert する検査が、本番の動作点で非決定的に落ちた [テスト代表性] [計測汚染]

- 事象: 42 走すべての緑を要求する対測定の本走を 6 回投入し、到達走数 0 → 5 → 3 → 13 → 7 で
  毎回**別の 1 件**だけ落ちた。実測は測定走 33 回中 5 件 = 約 15%/走で、
  42 走を通す確率は 0.1% 未満だった。落ちた検査はいずれも単独走では緑だった。
- 根本原因: 落ちた 5 件はいずれも守りたい性質ではなく**環境の偶然**を主張していた。
  (a) 「いずれ両 thread が終わる」を `join(10)` で「10 秒以内」に書き換えていた、
  (b) 保証されていない hook の実行順序を期待していた、
  (c) 解放した fd 番号が再利用されるとき **OS が同じ整数を返すこと**を要求していた、
  (d) 子 process の応答期限を 0.05 秒の絶対 wall-clock で置いていた。
  この計算環境では `default_test_jobs` が計算ノードで cap 無しに全コア数を返すため、
  **本番受入もこの飽和状態で走る**。つまり測定固有ではなく本番が日常的に踏んでいる。
  親が受入 suite を静的走査したところ、小さい絶対時間・順序・識別子の一致を主張する候補は
  244 箇所 / 68 file あった (確定的で問題ない箇所を含む上限値)。
- 恒久対応: 観測した 5 件は性質を保ったまま実体を直した — 待ち上限は**残したまま**広げ
  (本物の deadlock は依然として捕まえる)、hook 順序は hookwrapper で**強制**へ変え
  (期待から事実へ)、fd は番号の一致に依存しない形にし、0.05 秒の grace は
  **論理時計**へ寄せて主題を保った。あわせて {{D:study-bounded-retry-of-red-cells}} で
  測定側を頑健化した (記録値は緑の走行からだけ取る)。
  **族全体の恒久対応は本 wave の scope 外**であり、244 箇所の分類と是正は所有 wave の判断に委ねる。
- 再発検知: 直した 4 件それぞれに、性質を保ったまま実時間・順序・識別子への依存が
  戻ったら落ちる検査を残した。測定側は「赤の走行の値が解析へ混入したら落ちる」負例を持つ。

### {{F:a-retry-feature-contradicted-a-validator-time-assumption}}. 「いつ起きるか」を変える機能が、検証器の暗黙の時系列前提と矛盾した [恒真ゲート]

- 事象: 測り直し機構を入れたところ、その新設検査 7 件が全部
  `receipt TMP capacity observation is invalid` で落ちた。
- 根本原因: 容量検査は従来「次の走行の前」にしか存在せず、最初の行が走行 1 だった。
  汎用の検証器はそれを `global_run_index <= 0` を拒否する形で固定していた。
  測り直しを入れると走行 0 の前にも容量検査が生じるが、完全性側の検証器は同じ行に
  走行 0 を要求する。**走行 0 を測り直すと、どう作っても受理されない受領証**になった。
- 恒久対応: 値域制約を生成器が実際に取りうる範囲へ直した
  (`0 <= index < expected_run_count`)。**受理集合は広がっていない** — 旧制約は上限が無く
  42 でも 999 でも通ったが、新制約は mode ごとの実走行数で挟む。内部整合の検査と
  「容量行の番号が対応する走行の番号と一致する」検査はいずれも維持した。
- 再発検知: 値域外の番号を持つ受領証が拒否される負例と、走行 0 の測り直しを含む受領証が
  受理される正例。
- 補足: この矛盾は fix 子が「test 側だけでは解消不能」と判断して
  **実装を変えずに報告して止まった**ことで表に出た。契約どおりの正しい停止である。

### {{F:relayed-a-ledger-number-from-memory-without-checking-lines}}. 台帳の F 番号を記憶から出し、行番号での照合を後回しにして他 session へ誤った案内をした [誤前提] [手順漏れ]

- 事象: 別 wave から受入の非帰属赤について相談を受け、2 点誤って答えた。
  (1) 相手が使っていた evidence_id を「別の F が正しい」と指摘したが、**相手が正しかった**。
  引用した逐語は相手の言う F の再発欄にあり、私が挙げた F はそこから分離された別型だった。
  (2) 「その F の署名は特定の 1 種類だけ」と述べたが、台帳本文は既に相手の署名 2 種を
  同じ F の再発として収容していた。私の記憶が初出の署名だけを保持していた。
- 根本原因: F 番号を記憶から出し、**行番号での照合を後回しにした**。
  台帳は再発追記で射程が広がるため、記憶の中の「その F の意味」は古くなる。
- 恒久対応: 既存の規律 (memory `ruling-lookup-discipline` と
  `primary-source-includes-failures-ledger`) の適用範囲を、**他 session へ番号を伝える場面**へ
  明示的に広げる。番号を口に出す前に該当節を開き、見出し行と再発欄の両方を読む。
- 再発検知: 相手が junit の本文まで読んで反証を返したことで判明した。
  伝える側が「行番号で照合した」と明言できない案内はしない。

## 再発

### F273

- **再発: 2026-08-26** — 別 wave ([T-1135]、branch `worktree-dev-wave-t1135-prereg-blockers`) が
  受入全走を 3 回連続で赤にし 4 回目で緑を得た。**本項は当該 wave の実測であり、
  緑の受領証が tested_tip を pin していたため彼らの land には入らなかった。引き継ぎを受けて記録する。**
  観測は 2026-08-26 03:41 JST の login node で、**受入待ち手 7 本・`run_tests.py` 16 本・
  codex 子 26 本が同時稼働**、load average 3.26 / 3.12 / 3.37。この密度で
  受入 3 走が赤 (12 → 1 → 10 件) 、4 走目が緑 (0 件) と非決定的だった。
  赤の署名 4 種はいずれも「子の起動・応答が期限に間に合わなかった形」で、
  `child.pid was not registered before deadline`、`NG: receipt truth table が不正`、
  subprocess 出力が空による `JSONDecodeError`、manifest 不出現による `assert (None is not None)`。
  誘発された snapshot 側の subdir は `0-948303.nqsv--bnode033`。
  独立の裏取りとして [T-1434] が同時間帯に `0-948349.nqsv--bnode053` で同じ因果を観測している。
  既載の再発は並行 launcher 数と load average の 1 分平均だけを記録していたが、
  **本件は待ち手・runner・codex 子の内訳を持つ**点が新しい。

### F480

- **再発: 2026-08-26** — 対測定の本走で
  `test_real_repo_serialization.py::test_receipt_memo_real_xdist_order_has_no_worker_payer` が
  1 件だけ落ちた。観測 trace は `['controller-hook', 'prewarm-controller', 'worker-hook',
  'finish-controller']` で、**守りたい性質 (worker が payer にならない) の assertion は
  すべて通っており**、落ちたのは worker の hook が controller の hook より先である、という
  順序の 1 行だけだった。単独走は 4.67 秒で緑。
  既載は「絶対 wall-clock を assert する検査」を型として記述していたが、
  **本件は実行順序を assert する検査であり、同じ「環境の偶然を assert する」族に属する**点が新しい。
  対応は削除ではなく強制で、合成 plugin の `pytest_collection_finish` を
  `hookwrapper=True, tryfirst=True` にして `yield` の前に記録することで、
  collection 完了が controller へ通知される前に記録が確定するようにした。
