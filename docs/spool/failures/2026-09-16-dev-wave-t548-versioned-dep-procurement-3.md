---
schema: izanagi-spool-v1
ledger: failures
authored: 2026-09-16
wave: dev-wave-t548-versioned-dep-procurement
seq: 3
---

## 新規

### {{F:stage1-consumer-enumeration-stale-by-stage5}}. 段 1 で採った consumer 列挙を段 5 まで持ち越し、その間に着地した新 consumer を落とした [手順漏れ] [ドリフト]

- 事象: 段 1 で旧 locator の読み手を列挙し (28 file)、段 4 の裁定に写した。段 5 の投入直前に
  main が 134 commit 進んでおり、その中に旧命令 `verify-deps` を呼ぶ新 consumer
  (`orchestrator/campaign/b4_binary_record.py`、別 wave が同日に着地) が入っていた。実装子が
  「裁定の一覧に無い読み手」として fail-closed で停止して初めて判明した。
- 根本原因: 列挙は採った時点の main の事実であり、wave が長いほど陳腐化する。midflight gate が
  「main より N commit 遅れ」を NOTE で出していたが、親はそれを「取り込む合図」とだけ読み、
  「裁定の列挙を採り直す合図」とは読まなかった。
- 恒久対応: 段 5 の投入直前 (midflight gate の直後) に、段 1 と同じ検索で consumer 列挙を採り直し、
  差があれば裁定へ追補する。取り込み (`--ff-only`) と列挙の再走を 1 手順にする。
- 再発検知: 実装子が「裁定の一覧に無い読み手を見つけた」と報告して止まったとき、まず main の進行量を疑う。

### {{F:ownership-split-by-filename-misses-fixture-coupling}}. 所有の素集合分割を file 名の重なりだけで判断し、共有 fixture 経由の結合を見落とした [手順漏れ]

- 事象: shell consumer (単位 B) と Python consumer (単位 C) を「編集する file 名が重ならない」ことを
  根拠に並列投入した。実際は T-126 の job body (B 所有) と `submission.py` (C 所有) が、
  同じ契約テスト file の共有 fixture (`_attempt` / `_submit_fixture` / `_install_job_dependency_marker`)
  へ結合しており、B は編集前に停止した。段 3 の相談も同じ粒度で「素集合に割れる」と判定していた。
- 根本原因: 結合は production file の consumer test の **fixture 単位**で起きる。file 一覧の重なりは
  その粗い近似でしかない。
- 恒久対応: 分割を決める前に、各単位が触る production file の consumer test を名前で引き
  (`git grep -ln "<file 名>" -- orchestrator/tests/`)、同じ test file を 2 単位が引くなら
  その file の所有を時点で切り替える (直列化) か、1 単位にまとめる。
- 再発検知: 実装子が「所有外 test の fixture を直す必要がある」と報告して止まったとき。

## 再発

### F370

- **再発: 2026-09-16** — 4 形で再発した。(a) `orchestrator/tests/test_ccbench_spawn_sites.py` が
  編集 file の subprocess **起動本数**と関数の**行番号**を固定していた。(b)
  `test_mocc_trace_job_contract.py` が policy の**値の本数**を関数名の数字 (`_emits_18_values_`) と
  assert で固定していた。(c) silo の凍結 evidence が job body と submitter の **sha256** を
  「現行 bytes と一致」で束縛していた。(d) 凍結 prereg
  `output/insights/2026-08-16_t1142-n-pilot-prereg/protocol-r33.json` が `tools/pegasus/oracle_n_pilot.sh` の
  **sha256** を記録し、test が現行 bytes と live 比較していた (受入で決定的に赤)。いずれも段 1 の pin 閉包
  (path 検索・key 検索) に出ず、
  実装後の実走で初めて出た。恒久対応 (memory `authoritative-closure-before-counting`) は brief の
  「N 箇所」断定に掛かる規則で、**編集する file を本数・行番号・bytes で固定するメタテスト**は
  射程外だった。追加の検索形は「編集する module / data file 名で `orchestrator/tests/` を逆引きし、
  hit した test の中身で pin の形 (本数・行番号・sha256) を読む」に加え、
  「**変更する file の変更前 sha256 を repo 全体 (`output/` 含む) で逆引きし、hit を live 比較する test が
  無いか読む**」。後者は (c)(d) を段 5 前に出せた (親が受入 2 回目の後に実測して確認)。

### F736

- **再発: 2026-09-16** — 2 回。(1) 「`verify-deps` を廃止せよ」と「既存テストの期待値を削るな」を
  同じ裁定に書き、廃止する命令の test 4 node の削除を許可し忘れて実装子が停止した。
  (2) 段 6 fix で、契約テストが mocc にも env 既定の解決行を要求しており、それが直すべき不具合
  そのものだったのに、期待値の置換を許可し忘れて fix 子が停止した。どちらも子の判断は正しい。
  F736 の恒久対応 (許可を列挙でなく契約で書く) を、親は読んでいたが適用しなかった —
  「受理集合を変える指示を子へ出す直前に、この wave で凍結済みの判定式を再読する」(`DW-O12`) を、
  自分が書いた禁止文にも掛ける必要がある。
