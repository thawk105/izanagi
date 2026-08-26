---
schema: izanagi-spool-v1
ledger: worklog
authored: 2026-08-26
wave: dev-wave-merge-audit-necessity
seq: 3
title: 取り込みの合成監査は維持と裁定し、高速化案は必須経路と実行分類が閉じるまで実装しない (docs + 記録、branch worktree-dev-wave-merge-audit-necessity、実装面の差分ゼロ)
---

## 本文

- **ユーザー裁定への答え。** 「合成監査の必要性を確認し、あれば維持して高速化、
  なければ撤廃」に対し、**維持**と裁定した。根拠と訂正は {{D:merge-audit-stays}}。
  高速化は本 wave では実装せず、前提 3 点を条件として {{D:merge-audit-projection-requirements}}
  へ固定した。
- **親の当初主張が段 3 で 1 件反証された。** 親は「固有検出率 5 割超 (8/13〜15)」と
  ユーザーへ報告したが、3 件は同じ回に別の機構が赤を出す型だった。固有検出は最大 5 件。
  {{F:mechanism-credit-without-counterfactual}} に型として記録した。
  維持という結論自体は変わらない — 固有 5 件のうち 2 件は受入全走でも緑になる型である。
- **親の当初仮説「事前射影を厚くすれば監査子が速い」も現物で反証された。**
  射影が最も厚い走行 (diff 2 本 + merged source 4 本、repo 遮断) が 468 秒 / 28 model call、
  射影ゼロで親が探索範囲を 1 本に絞った走行が 320 秒 / 7 model call。
  段 2 の plan も独立に同じ結論を出し「因果は確定できない」と書いた。
  代替仮説 (対象 file 数・入力量・repo 遮断・wave 難度) を排除できないため、
  **短縮秒数は主張しない。**
- **段 3 が出した blocker 3 件を親が全件コードで裏取りした。** (a) 正規の main 取り込みは
  受入待ち手の post-claim merge で行われ、merge 直後に provenance が連続実行されるため
  親が割り込む停止点が無い。(b) 全 Python 母集合を走査する新規 script は Pegasus login で
  分類が要り、判定量は cgroup charged memory で最大 RSS は代理値にならない。
  親が挙げた既存 script の未登録運用は machine gate の被覆漏れであり、
  分類義務の撤回根拠にならない (レンズ A・B が独立に同じ判定)。(c) D697 決定 8 / D554 / D770 は
  別々の集合を発火条件にしており、運用文の 1 語へ畳めない。
- **本 wave で見つかった最大の高速化余地はユーザー裁定へ返した。** D770 は
  「staged merge のまま author 子を起動する経路は機械的に存在しない」ことを根拠に
  2 commit 分割を決めたが、後発の D785 がこの前提を撤去している
  (`tools/dev_waves/launch_authority.py` の mid-merge capability と、
  `tools/codex_worker_launch.py` が author かつ workspace-write のときだけ渡す条件を親が確認)。
  D785 の裁定文は D770 に言及しておらず supersede は未記録。承認済み裁定を親が覆さない契約に従い、
  新事実を添えて返す。実現すれば実装面が重なる取り込みのたびに commit 1 本と tree 照合が消え、
  監査子が報告だけでなくその場で修正できるようになる。
- **DW-G01 の生死確認は通した。** repo 外 probe で tracked Python 666 file の
  全 AST 走査を実測し 16 秒。ただし probe は全 AST を同時保持しており、
  既存の streaming 形 (1 file ずつ parse して捨てる) より重い。probe の値を実装の見積りに使わない。
- **合成監査の走行は台帳から機械集計できない。** job 名が wave ごとに異なり
  (merge-audit / stage9-merge-N / s9-merge-verify / recovery-merge-synthesis /
  mid-merge-codex-author)、機構に安定した識別子が無い。工数の数字はすべて下界である。
- **段 8 の自己改善は 1 件が byte 予算で入らず、裁定へ返した。**
  {{F:mechanism-credit-without-counterfactual}} の恒久対応を `DW-S01` の既存 1 文へ
  統合しようとしたが、L1 層の unique footprint 予算 (10,625 bytes) の余白は 70 bytes しかなく、
  圧縮版 (144 bytes) でも 10,699 bytes となり入らなかった。
  さらに圧縮すると「未照合を固有に数えない」という発効部を落とすことになり、
  予算のために安全義務を弱めない規律に反する。編集を撤回した。
  規律自体は failures 台帳の恒久対応・再発検知欄に残っている。
  予算の扱いは 989〜992 と同じくユーザー裁定へ返す。
- **エージェント工数**: codex 子 3 本 (plan 1 / consult 2)。すべて `gpt-5.6-sol` / `xhigh`。
  実装子・fix 子は「実装しない」裁定により起動していない。

## 次の一手差分

### 新規

- {{T:merge-audit-d770-supersede}} **P1・ユーザー裁定待ち**: 実装面が重なる main 取り込みを、
  D785 の mid-merge author 起動を使う 1 commit 手順へ戻すか。戻すなら D770 を supersede する
  決定が要る。本 wave が見つけた最大の高速化余地で、親の裏取り済み。
- {{T:merge-audit-projection-tool}} **P2・裁定待ち**: 合成監査の事前射影を決定的に生成する機構。
  {{D:merge-audit-projection-requirements}} の前提 3 点と必須要件 5 点を満たす設計を先に決める。
  必須経路への配線は受入待ち手の変更を伴い、実行分類はユーザー端末での実測を要する。
- {{T:merge-audit-stable-job-id}} **P3・新規**: 合成監査の子に安定した job 識別子を与え、
  receipt 台帳から機構の工数を機械集計できるようにする。現状は wave ごとに名前が違い、
  工数の数字が下界にしかならない。
