# 段 6 レビュー裁定 — dev-wave-t1629-ratification-broker

レビュー A (正しさ境界) が must-fix 10 件 + nit 2 件、レビュー B (検出力と波及) が
must-fix 4 件 + nit 3 件を出した。親が real/refuted と採否を裁定する。

## 通底する 1 つの発見

**A3 / A4 / A9 は別々の所見だが、帰結が同じである。**

> broker が「検証子なら拒否する行」を台帳へ commit できてしまう。
> 台帳は 1 行でも検証に落ちると全体が拒否されるので、
> **不正な行を 1 行足しただけで gate が永久に閉じる。**

これは本 wave の完了条件 (ii)「内容の承認だけをユーザー gate として起票できる状態」を
直接壊す。最初の批准が gate を壊したら成果物はゼロである。
したがって 3 件を 1 つの fix へまとめる: **broker は、これから書く行が検証子に受理されることを
検証子と同じ規則で確かめてから commit する。**

## 裁定表

| # | 出所 | 判定 | 扱い |
|---|---|---|---|
| A1 | 全史検査と履歴取得の間の TOCTOU | **real・scope 外** | v1 も同一構造であり、成立には検証中の repo 書換えが要る。段 4 の S2 (外部固定実行器) と同族。記録して裁定へ返す |
| A2 | 履歴 blob の総読込量が二次 | **real・採用** | 履歴 bytes・source batch・commit 数へ集約上限。R11 の主張はスカラー倍算回数に限定して書き直す |
| A3 | broker の Git が検証子と同じ hardening でない | **real・採用** | 下記 統合 fix |
| A4 | broker と検証子の wire contract 二重管理、64 桁 object ID | **real・採用** | 下記 統合 fix |
| A5 | 生成した署名を commit 前に検証しない、PATH と key path を信頼 | **real・採用** | 鍵を fd に固定し、生成署名を捕捉済み公開鍵で検証してから commit |
| A6 | source closure の tree mode を検査せず symlink source を流用できる | **real・採用** | source 27 path も `100644` / `100755` に限定する |
| A7 | 初回批准は内容を表示せず、Unicode control も素通し | **real・採用** | **人間の判断が入る唯一の場所なので表示の完全性が要**。初回も全 bytes を表示し、LF 以外は単射な ASCII 表現へ escape |
| A8 | fixture が binding と receipt を別 repo から作る | **real・採用** | `contract_loader_binding._REPO_ROOT` も合成 repo へ向ける |
| A9 | broker が current blob だけを見る | **real・採用** | 下記 統合 fix |
| A10 | 防壁風だが削除しても赤にならない検査 | **real・採用 (nit だが実施)** | 削除するか「独立防壁ではない」と明記。**防壁の数を実態より多く見せない**ため |
| A11 | M17 が実効 gate でなく冗長 preflight を測っている | **real・採用** | 変異 spec で再照準 |
| A12 | M10 の gitlink 帰属と decision 検査の除外理由が実装と不一致 | **real・採用** | 変異 spec を修正 |
| B1 | M10 の期待 node が収集 node と一致しない | **real・採用** | 変異 spec で非 parametrize node へ分割 |
| B2 | 共有 fixture が暗号依存欠落を skip に変える | **real・採用** | **約 1,102 node が黙って skip して rc=0 になりうる**。直接 import か `pytest.fail` へ |
| B3 | `hooks/README.md` に運用境界が未反映 | **real・採用** | 段 7 で親が書く (docs は親の担当) |
| B4 | 秘密鍵の漏えい検査が stdin しか見ていない | **real・採用** | argv・環境・remote Git 履歴と代表 encoding も検査 |
| B5 | 27-path sentinel が脱落を検出しない | **real・採用 (nit)** | 独立 tuple と production tuple を直接比較 |
| B6 | duration 台帳の旧 nodeid 10 件が stale | **real・採用 (nit)** | key を移行し**実測値はそのまま保持**。値を新造しない |
| B7 | phase doc に v1 前提が残る | **real・採用** | 段 7 で親が書く |

**refuted は 0 件。** レビュー 2 本はいずれも実装コードで裏取りされていた。

## fix の分割 (所有素集合・逐次投入)

- **fix-C5 (broker):** A3 / A4 / A5 / A7 / A9 / A10 の broker 分 / B4
  編集面 = `tools/ratification_broker.py`, `orchestrator/tests/test_ratification_broker.py`
- **fix-B2 (receipt 検証子):** A2 / A6 / A10 の receipt 分 / B5
  編集面 = `orchestrator/campaign/enforcement_source_ratification_receipt.py`,
  `orchestrator/tests/test_enforcement_source_ratification_receipt.py`
- **fix-D2 (配線と共有 fixture):** A8 / B2 / B6
  編集面 = `orchestrator/tests/conftest.py`,
  `orchestrator/tests/acceptance_duration_ledger.json`

## 親が段 7 で行う docs 追随

- `hooks/README.md` に broker の運用境界 (repo 内は参照実装、運用 copy は AI 非到達 host)、
  subprocess / Git の限界、append と commit の transaction、主張上限を書く (B3)
- 現行 phase doc の v1 前提を追随させる (B7)

## 変異事前登録の改訂 (DW-M07 に従い最終 commit で再 anchor)

- **M10** を symlink parameter だけに絞り、gitlink は object-type gate として別 ID にする (A12 / B1)
- **M17** を transaction 側の worktree blob 比較へ再照準する (A11)
- **M18 を追加**する: `ed25519_verify` の R 単位元拒否。
  段 4 の事前登録時点ではこの検査が存在しなかった (fix1 で親が裁定して新設した)。
  後段の部分群検査は単位元を通すため、単位元 R を捕まえるのは前段だけであり単一理由が成立する。
  期待 node = `test_rejects_small_order_r`
- **decision 検査**を変異候補へ戻す (A12。二重ではなくなったため)
