# [T-2803] の起点 (逐語)

## worklog entry 1722 の次の一手 (`docs/archive/worklog-phase3-0920-1722.md`)

```
- [T-2803] **P2・新規**: 受領証 (D2045) の attributes fingerprint が index の全 path の
  祖先 directory 集合に依存し、新 insight dir を足す commit を跨ぐと全 partition で失効する (直近 60 main commit の 50 %)。実在する
  `.gitattributes` だけを束縛するなど、tip の directory 集合に依存しない形を設計して cold 率を下げる。判定は不変であること。
```

## dev-wave 引数 (ユーザー依頼、2026-09-20)

```
[T-2803] (P2・新規、entry 1722、D2045 の再訪) 全史 provenance 監査の受領証 (`tools/check_ai_provenance.py`、D2045) の attributes
fingerprint が index の全 path の祖先 directory 集合に依存し、新 insight dir を足す commit を跨ぐと全 partition で失効する (直近 60 main
commit の 50%、land ではほぼ毎回 cold = login 88 秒 / 受領証あり 14.9 秒) 件を直す。実在する `.gitattributes` だけを束縛するなど tip の
directory 集合に依存しない形を設計し、Codex author (D95) で実装、判定 (違反集合) が不変であることを正例・負例 (gitattributes
の変更は失効させる) の変異で示す。cold 率の低下は同一 commit 列で前後を実測して記録し、「50% → x%」を時間短縮率と読み替えない。着手直前の
local main から fresh worktree。一次資料 `output/insights/2026-09-20/t2609-t2656-provenance-cost/`。規律 2
を緩めない。本題だけ。仮想リスク向けの gate・検査・台帳・一般化の追加は scope 外。
```
