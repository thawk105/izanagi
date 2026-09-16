# 既裁定・一次資料の逐語射影 (親が 2026-09-17 に main 1042a1bc9 の現物から複写)

## 起票 — docs/archive/worklog-phase3-0816-587.md:535-537 (entry 587)

```
- [T-1209] **P2・新規**: T126 qualification の code identity は
  verifier では `core.py` しか含まず、`dsg/model/parse` の変更に反応しない。
  qualification 成果物が旧 correctness 実装を指し続ける。threat scope に含めるかを決める。
```

## 裁定 — docs/archive/worklog-phase3-0817-622.md:483-486 (entry 622)

```
- [T-1209] **P2・裁定済み (2026-08-17 /rulings 全件 第 5 回、含める)**: `dsg/model/parse` を
  T126 qualification の code identity へ含める。検証器の一部だけを見る同一性は主張を支えない
  (規律 3 の面)。**条件 = 過去の qualification 成果物は歴史記録として据え置き、以後の取得から
  新 identity を適用する。**
```

## 兄弟閉包の記録 — docs/decisions.md D442 (2026-08-16) 抜粋

```
## D442. enforcement source closure を exact 12 path へ広げ、verifier 実装を epoch へ束縛する (2026-08-16)
1. **閉包を exact 12 path にする。** `campaign_lock.CONTRACT_LOADER_RELATIVE_PATHS` へ
   `orchestrator/verifier/core.py` / `dsg.py` / `model.py` / `parse.py` を末尾へ加える。
...
- **別閉包は追随しない。** T126 qualification の code identity は verifier では `core.py` しか
  含まず、`dsg/model/parse` の変更に反応しない。
```

## 兄弟閉包の記録 — docs/decisions.md D473 (2026-08-17) 抜粋

```
## D473. enforcement source closure を exact 14 path へ広げ、verifier の dispatch 面と report 面を束縛する (2026-08-17)
1. **閉包を exact 14 path にする。** `campaign_lock.CONTRACT_LOADER_RELATIVE_PATHS` へ
   `orchestrator/verifier/__init__.py` と `orchestrator/verifier/report.py` をこの順で末尾へ加える。
...
4. **閉包の完全性を test-only の package census で守る。** 閉包は固定 exact list なので、
   verifier package へ module を 1 つ足して `__init__.py` の 1 行でそれを読ませれば、
   epoch を変えずに dispatch 先を差し替えられる。実 package directory を走査して
   `.py` が exact 8 件であり、うち 6 件が閉包 member、2 件が意図的除外であることを検査する。
   ...これは repo 不変条件のテストであって成果物の受理集合を変える gate ではない。
```

## 依頼 (command 引数、ユーザー発話) の逐語

```
[T-1209] T126 qualification の code identity へ dsg/model/parse を含める (2026-08-17 /rulings 全件 第 5
回で「含める」と裁定済み。条件 = 過去の qualification 成果物は歴史記録として据え置き、以後の取得から新 identity
を適用)。現物 orchestrator/qualification/contract.py の REQUIRED_CODE_IDENTITY_PATHS は qualification 配下だけで verifier
側が未収載。正本は entry 622 の持ち越し本文。orchestrator/qualification/ は [T-548] (entry 1578)
が直前に触ったので、着手直前の local main から fresh worktree を作り、起動時に編集面の重複検査を行う。Codex author (D95) +
変異事前登録。本題の identity 集合だけ。仮想リスク向けの gate・検査・台帳・一般化の追加は scope 外。規律 2 を緩めない。
```

## 親が実測した現物の事実 (2026-09-17、main 1042a1bc9)

- `orchestrator/qualification/contract.py:39-76` `REQUIRED_CODE_IDENTITY_PATHS` (frozenset、37 path)。verifier は `:75 "orchestrator/verifier/core.py"` のみ。
- `orchestrator/verifier/` の .py: `__init__.py` `__main__.py` `cli.py` `commit_receipt.py` `core.py` `dsg.py` `model.py` `parse.py` `report.py` (8 + `__main__`)。
  `core.py` は `.dsg` `.model` `.parse` `.commit_receipt` `.report` を import。
- `REQUIRED_CODE_IDENTITY_PATHS` の consumer: `contract.py:530` (`series_identity` の exact key set 検査)、`identity.py:140` (`verify_recorded_series_identity`)、
  `t126_driver.py:359` (`code_paths = tuple(sorted(...))`)、tests: `test_t126_pegasus_tools.py:704,980,1026,1085,1486,1487,1519,1522,1534,1547`、
  `test_t126_qualification_contract.py:21,76`、`test_t419_probe_causality.py:38,42`。
- fixture `_attempt` (`test_t126_pegasus_tools.py:970-1025`) は generic path を `fixture {relative}\n` で埋める。
- repo 内に `code_identity` を持つ committed JSON は 0 件。live qualification は未実施 (docs/phase3.md:1313)。
- contract.py の現 sha256 / blob の pin は repo 内 0 件。path pin は `orchestrator/campaign/campaign_lock.py:107,204` (contract loader 閉包、HEAD blob と disk の live 比較) のみ。
