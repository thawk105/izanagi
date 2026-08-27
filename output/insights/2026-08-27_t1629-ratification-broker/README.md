# [T-1629] 取り残された D905 執行機構を回収し、署名 receipt による批准 gate として着地させた

wave: `dev-wave-t1629-ratification-broker` / branch `worktree-dev-wave-t1629-ratification-broker`
base main: `e29084e0`

## 何を納めたか

enforcement closure 批准の執行経路を、**repo の外に置いた鍵で署名した receipt** を
committed 履歴から検証する形へ移した。D905 が定めた「AI が成りすませない実行主体の新設」である。

- `orchestrator/campaign/ed25519_verify.py` — RFC 8032 の検証子 (pure Python)。
  検証子を閉包の内側に置くため外部ライブラリに依存しない。
- `orchestrator/campaign/enforcement_source_ratification_receipt.py` — 署名 receipt の検証子。
  履歴は v1 の DAG kernel を再利用する。
- `tools/ratification_broker.py` — 人間が AI の到達できない host から使う**参照実装**。
- 閉包を 25 から 27 path へ広げ、批准 gate を v1 から v2 へ切り替えた。

**回収元は 3 本の codex worktree の untracked 7 file** で、いずれも detached HEAD `9463bcbc`、
locked、担当セッション不在だった。worktree を畳めば消える状態だったため、
着手直後に repo 外へ sha256 付きで退避した。

## 現時点の状態 (重要)

**実 repo の信頼根と台帳はまだ存在しない。したがって批准の受理集合は空である。**
certified な選択結果は 1 件も生成できない。これは land 前と同じ状態であり後退ではない。
gate が開くのは、人間が下記の bootstrap を行い、broker で最初の receipt に署名した時点である。

## 人間が一度だけ行う bootstrap

**AI が到達できない trusted host / account** で行う。逐語は
`verbatim/s5-broker-bootstrap-procedure.md` にある。要点だけ再掲する。

1. レビュー済みの broker と検証子を、その host の運用 path へ配置する。
   **repo 内の copy を運用に使ってはならない** — repo を編集できる主体が
   「人間に見せる差分」と「実際に署名する対象」を食い違わせられる。
2. `openssl genpkey -algorithm ED25519` で鍵を作る。mode 0600、repo の外に置く。
3. 公開鍵 (raw 32 bytes) から canonical JSON を作り、次の 2 file を repo へ exclusive-create する。
   - `hooks/enforcement-source-ratification-trust-root.v1.json`
     (`public_key_ed25519_base64` と `schema_version` の exact 2 key、末尾 LF ちょうど 1 個)
   - `hooks/enforcement-source-ratification-receipts.v2.jsonl` (0 byte)
4. その 2 file を commit する。**broker はこの 2 file を作らない。**
   不在なら fail-closed で停止し、手順を表示するだけである。

以後の批准は `python3 <運用 path>/ratification_broker.py --target <ssh-spec>:<repo>` を
official 起動の直前に 1 回実行する。**64 hex の転記は残らない。**

## 主張してよい上限 (D526)

> 現在の committed 信頼根の鍵で検証できる署名 receipt の集合と、要求された closure digest を
> 比較する。信頼根の秘密鍵は repo の外にあり、AI はそれを持たない。

**「人間が批准したことの機械的証明」とは書けない。**
判定器とその呼び出し元は判定対象の閉包の内側にあり、呼び出し前に
「今動いている判定器の bytes が以前に批准された bytes と同じか」を確かめる外側の実行器が無い。
これは v1 から存在する構造で、署名を足しても塞がらない。詳細は `verbatim/s4-ruling.md` の §0。

## 変異 matrix

| 項目 | 値 |
|---|---|
| baseline | PASSED (32.23 秒) |
| 登録 | 18 |
| KILLED | 18 |
| SURVIVED | 0 |
| MISMATCH | 0 |
| TIMEOUT | 0 |
| 期待 node 総数 | 56 (全件一致) |
| `repo_head` | `87532e9fe2e8b5f56a7bfd473f1a5ac9e76f22e5` |
| spec sha256 | `9f54b63339e5034d4aa2b17391b73f56f2933a27c0c40654770a9ae71694066a` |

**probe を先に回した価値がそのまま出た。** 事前登録では各変異の期待 node を 1 件と見積もって
いたが、実測では M03 が 8 件、M05 が 24 件を巻き込んでいた。期待 node は完全集合でなければ
ならないので、**probe 無しで本走していたら 4 件が MISMATCH で止まっていた。**

probe は `mutation-spec-probe.json` (全件 SURVIVED 期待)、本走は `mutation-spec.json`。
結果台帳は `mutation-ledger.json`。

**登録しなかった候補が 3 件ある。** 焦点再レビューが帰属を検算した結果である。

- broker の信頼根不在検査 — 段 6 で新設した検証子互換 preflight が同じ入力を先に弾くように
  なったため単独では殺せない。**防壁が二重になった結果**であり、通常の回帰テストに留めた。
- 承認端末の要求 — 早期 probe と実 read の二段構えで、単一置換では帰属しない。
- 特殊 file 形式 (gitlink) — mode 検査と blob load の両方が同じ入力を弾く。

## 受入全走と land 状態

**受入は赤 1 件を除いて緑である。** land はその 1 件で停止しており、裁定待ちである。

| 走 | 結果 |
|---|---|
| 1 回目 | `merge-message-provenance` で停止。自動合成が両親と異なる実装面を作ったため Codex `role=author` の merge message が要った |
| 2 回目 | `restart-required`。main の前進で待ち手 tool の bytes が変わった (取り込み merge は成立) |
| 3 回目 | `3 failed, 17762 passed, 61 skipped` |
| 4 回目 | **`1 failed, 17764 passed, 61 skipped`** |

3 回目の赤 3 件の帰属:

- **自分起因 2 件 → 直した。** 新規 test file の自走 harness 欠落と、
  閉包拡張で stale になった論文図の来歴記録 (再生成。**PNG はバイト同一**)。
- **非帰属 1 件 → 裁定へ。** `test_g5_real_ledger_covers_at_least_90_percent_of_real_collection` は
  **main 単独で赤** (`b9d21206` で 15912/17700 = 89.898305%)。
  peer session が**テスト node を 1 つも足さない wave** で同じ 1 件だけの赤を独立再現し、
  分母 17700 も一致した。**現時点で受入を通す全 wave が塞がっている。**

詳細と択一は `ruling-package.md`。台帳の全面再生成を実測した結果
(18 個の pin が壊れる、生成器は exact 所要値 pin が在る限り永久に使えない) も同文書にある。
照合手順は、台帳の `duration_seconds_by_nodeid` に対して
`test_t1574_changed_suite_ledger_node_delta_is_exact` の `removed` / `added` /
`expected_suite_node_sets` をそのまま当て、8 接頭辞ごとに
「件数 + sorted node を LF 連結した sha256」を再計算して比較する。
**照合 script 自体は repo へ入れない** — `output/insights/` 配下の `.py` は
実装面と判定され Codex `role=author` を要求するが、この probe は親が書いたものである。

## 監査の結果 (規律 6)

回収物は「素性の知れない外部入力」として扱い、取り込む前に独立監査した。
**real と裁定した欠陥は段 2〜3 で 19 件、段 6 のレビューで 18 件。refuted は 0 件。**

重いものは次の 5 つ。

1. **配線が丸ごと欠けていた** — broker は閉包 27 path を前提にしていたが main は 25 path。
   回収物だけでは 1 行も発火しない死んだコードだった。
2. **土台が古い** — T-1742 の DAG 修正は回収物の base の祖先ではなく、旧・線形版を持ち戻していた。
3. **broker が AI に `hooks/` への書込経路を与えていた** — `guard_bash.decide()` を
   副作用なしに静的評価した結果、鍵生成・broker 起動・承認の流し込み・`git add` が全部 ALLOW。
   broker は ssh 越しに書くため hooks の拒否も通り抜ける。信頼根が不在なら AI 自身の鍵が信頼根になる。
4. **署名が実質飾りだった** — `source_commit` は存在確認しかせず、
   その commit の closure が署名 digest と一致するかを見ていなかった。
5. **検証の計算量が二次だった** — 台帳 10 行で約 4.3 分、100 行で数時間の見積り。

## 実機でしか出ない本番欠陥 3 件

いずれも**回収コードに元からあり、あのコードは一度も緑になっていない**。

- OpenSSL 3.0.2 の `pkeyutl -sign -rawin` は標準入力から読めない (`-in <file>` が必須)。
- `open("/dev/tty", "r+", buffering=1)` は Python が拒否する (tty はシークできない)。
- broker と本体で閉包 tuple の順序が食い違っていた (実運用なら必ず拒否される)。

**codex 子は本 repo で pytest を実走できない** (実行場所判定が `qstat -Q` を叩き、
隔離環境は socket を拒否するため必ず `rc=16`)。段 5 の 4 子すべてが当たった。
以後テストは親が毎回実走し、赤の本文と原因を実測して子の prompt へ貼る運用に切り替えた。
**この切替が効いて上記 3 件が出た。**

## 一次資料

- 段 1 brief / 段 2 plan / 段 3 の 2 レンズ / 段 4 裁定 / 変異事前登録 /
  段 6 レビュー 2 本 / 段 6 裁定 / 焦点再レビュー = `verbatim/` 配下
- 親の実測 M1〜M22 = `verbatim/parent-measurements.txt`
- bootstrap 手順の逐語 = `verbatim/s5-broker-bootstrap-procedure.md`
