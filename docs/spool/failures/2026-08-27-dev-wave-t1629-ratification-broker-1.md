---
schema: izanagi-spool-v1
ledger: failures
authored: 2026-08-27
wave: dev-wave-t1629-ratification-broker
seq: 1
---

## 新規

### {{F:openssl-rawin-needs-seekable-file}}. OpenSSL の一括署名は標準入力から読めず、回収コードは一度も動いていなかった [テスト代表性]

- 事象: 段 5 の broker で `openssl pkeyutl -sign -rawin` が rc=1 で落ち続けた。
  実装子は失敗 digest に混ざっていた `subprocess.run` の docstring を真因と判定したが誤りだった。
- 根本原因: この機体の OpenSSL 3.0.2 では `pkeyutl -sign -rawin` が**標準入力から読めない**。
  Ed25519 の一括署名がサイズの確定した実 file を要求するためで、親が手で再現した。

  ```text
  $ openssl pkeyutl -sign -rawin -inkey k.pem -in msg.bin -out sig.bin   -> rc=0, 64 bytes
  $ printf 'hello' | openssl pkeyutl -sign -rawin -inkey k.pem           -> rc=1
    Error: unable to determine file size for oneshot operation
    Public Key operation error
  ```

  `-in <path>` が必須である。**回収した元の実装も標準入力へ流す形だった。
  つまりあの broker は一度も緑になっていない。**
- 恒久対応: 署名対象を private な一時 file へ mode 0600 で書き、`-in <path>` で渡す。
  例外経路でも削除する。生成署名は 64 bytes の長さ検査だけでなく、
  捕捉済みの公開鍵で**実際に検証してから** transaction へ進む。
- 再発検知: 外部 command の入出力規約に依存する実装は、静的レビュー通過を closed と数えない。
  親が実機で 1 回動かすまで確かめる (`DW-O16`)。

### {{F:devtty-rplus-not-seekable}}. `/dev/tty` を `r+` かつバッファ付きで開くと Python が拒否する [テスト代表性]

- 事象: 承認プロンプトが常に `cannot open /dev/tty` で失敗し、broker のテスト 4 件が赤だった。
  テスト側の PTY の張り方 (`os.setsid()` + `TIOCSCTTY`) を疑ったが、そちらは正しかった。
- 根本原因: `open("/dev/tty", "r+", buffering=1)` は `BufferedRandom` を作り、
  これは seekable を要求する。tty はシークできない。親が実機で再現した。

  ```text
  CHILD: cannot open /dev/tty: File or stream is not seekable.
  ```

  読み取り専用 (`"rb"`) なら `setsid`+`TIOCSCTTY` 方式でも `pty.fork()` 方式でも成功する
  (親が両方式で実測)。
- 恒久対応: `getpass.unix_getpass` と同じ形にする。
  `os.open("/dev/tty", os.O_RDWR | os.O_NOCTTY)` で得た fd を `io.FileIO(fd, "w+")` で包み、
  さらに `io.TextIOWrapper` を被せる。生の `FileIO` は seekable を要求しない。
- 再発検知: file の open mode と buffering に依存する実装は実機で開くまで確かめる。
  上記 2 件は同じ型 (実行環境に依存する実装を静的レビューだけで closed にしない) である。

### {{F:broker-can-brick-the-gate-with-one-row}}. 書き手が検証子の規則を持たないと、不正な 1 行で gate が永久に閉じる [恒真ゲート]

- 事象: 段 6 の敵対レビュー 2 本が別々に 3 つの所見を出したが、帰結は同一だった。
  broker は「検証子なら拒否する行」を台帳へ commit できた。台帳は 1 行でも検証に落ちると
  全体が拒否されるので、**不正な行を 1 行足しただけで批准 gate が永久に閉じる。**
- 根本原因: 書き手 (broker) と読み手 (検証子) で規則が二重管理されていた。具体的には
  broker 側だけ Git hardening (replace refs / commit-graph / ambient 環境の無効化) が無く、
  40 桁以外の object ID を署名でき、現在 blob しか見ずに履歴の不正を検出しなかった。
- 恒久対応: **書き手は、これから書く行が読み手に受理されることを、読み手と同じ規則で
  確かめてから commit する。** 検証子の検査関数を import して再利用し、規則を書き直さない。
- 再発検知: 「書いた内容を後で厳格に検証する」機構を作るときは、
  書き手が読み手の規則を持っているかを設計時に確かめる。持っていなければ、
  書き手は必ず読み手が拒否する物を書ける。

### {{F:shared-fixture-importorskip-silently-skips}}. 共有 fixture の `importorskip` が約 1,102 node を黙って skip させる [恒真ゲート]

- 事象: 段 6 のレビューが、共有 fixture `ratified_enforcement_source` の
  暗号ライブラリ取得を `pytest.importorskip` にしていた点を指摘した。
  Git 不在は `pytest.fail` なのに、暗号ライブラリ不在だけ skip になっていた。
- 根本原因: 共有 fixture の依存欠落を skip にすると、依存が欠けた環境で
  **焦点走が大量 skip のまま rc=0 で完了しうる**。静的展開で該当 node は約 1,102 件。
  「批准 gate の回帰を検査せずに緑を報告する」形になる。
- 恒久対応: 直接 import か明示的な `pytest.fail` にする。
  失敗文言に「この fixture は batch で skip してはならない」理由を書く。
- 再発検知: 共有 fixture に `importorskip` を書かない。
  同 fixture 内の他の依存 (Git 等) がどう扱われているかと揃っているかを見る。

### {{F:parent-probe-py-in-insight-is-implementation-surface}}. 親が書いた probe を insight へ入れると実装面と判定され受入が赤になる [手順漏れ]

- 事象: 受入全走が `check_ai_provenance` で赤になった。
  `9e6e4ee93ca1 ...: 実装面に Codex role=author がない —
  paths=output/insights/2026-08-27_t1629-ratification-broker/verbatim/parent-check-ledger-pins.py`
- 根本原因: **`output/insights/` 配下でも `.py` は実装面と判定される。** 親が書いた
  照合 probe を「一次資料の保全」のつもりで insight へ入れたが、実装面は D95 により
  Codex `role=author` を要求する。親が書いた probe にはその trailer を付けられない。
  逐語 `.md` と結果 `.json` は実装面でないので同じ問題を起こさない。
- 恒久対応: **親が書いた probe は repo へ入れない。** 手順は散文で README へ書き、
  再現に要る値 (入力 path、判定式、期待値) を逐語で残す。
  実装面として残す価値があるなら Codex `role=author` に書かせて `tools/` か
  `orchestrator/tests/` へ置く (`DW-O17` の実装面 path 判定と同じ境界)。
- 再発検知: insight を作ったら `git ls-files <insight dir> | grep '\.py$'` が空であることを
  受入投入前に確かめる。既存 insight には `.py` を含むものがあるが、
  それらは Codex が書いた harness であり本件とは出所が違う。

## 再発

### F217

- **再発: 2026-08-26** ([T-1629] wave)。段 2 の plan 子が 2 回連続で
  `evidence_status=invalid` / `accepted=false` / `launcher_rc=1` になり、
  1290 秒 / 34 model call と 1521 秒 / 45 model call、あわせて約 47 分と約 9M token を失った。
  成果物は 38,497 / 30,414 bytes で完全 (`check_codex_output.py` rc=0、`## 総括` あり) だった。
  **親は最初 F540 (原因未特定の 3 つ目の型) と誤判定した。** 簡易 probe が重複キーを
  88 件報告していたのに、自作 probe の入れ子誤検出だと切り捨てたためである。
  真因は F217 そのもので、launcher と同じ strict parser を 1 行ずつ replay して確定した:
  `INVALID line 81: JSON key が重複: 'id'`。落ちた行は `type` が `item.started` の event で、
  その `item` object が `id` を 2 回持っていた (`item_42` と `exec-...`) 。
  `type` は `web_search` である。
  web_search 行は 1 回目 8 件・2 回目 6 件で、検索クエリは
  `https://www.rfc-editor.org/rfc/rfc8032` / `'TEST 1023'` /
  `'MESSAGE (length 1023 bytes)'` だった。
  **引き金は親の prompt が RFC との照合を子に求めたことである。**
  `DW-C01` の「子は Web 検索禁止」は**子の prompt には自動で入らない**ため、
  親が毎回書き写す必要があり、本 wave では書き落としていた。
  対応は 2 つ。全 prompt の先頭へ禁止を明記し、
  **検索したくなる動機そのものを消した** (RFC の実測結果を親が materials として与えた)。
  3 回目は web_search 0 件で成功した。
  **F540 の「receipt からは発火条件を特定できない」は、10 行の replay script で特定できる。**
  script を `materials/parent-diagnose-evidence-invalid.py` として保存した。

## supersede 追記

- F540 **supersede: 2026-08-27** — 「receipt からは発火条件を特定できない」は事後に特定できる。launcher と同じ strict parser を `attempt-*.events.jsonl` の各行へ replay すれば落ちる行が出る ([T-1629] wave で実測、真因は F217 だった)。invalid を見たら再発検知手順にこれを足す。
