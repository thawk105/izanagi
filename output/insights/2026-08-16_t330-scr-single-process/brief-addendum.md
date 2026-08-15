# 段 1 brief 追補 — F319 の実測 (段 2 プラン子はこれを持っていない)

親が段 2 投入後に発見した一次資料。**段 3 の両レンズはこれを必ず評価に含めること。**

## F319 (docs/failures.md の `### F319.` を開いて全文を読むこと)

2026-08-15 (T-330 裁定の 12 日後)、計算ノード `bnode030` と login の双方で実測:

- 共有 third-party cache の masstree は `git status --porcelain --untracked-files=all` が **0 行**、
  HEAD も凍結 pin と一致する一方、`git ls-files --others --ignored --exclude-standard` が
  **71 件**を返した (`config.h` 10,448 bytes、`libkohler_masstree_json.a` 2,466,846 bytes を含む)。
- 原因: CCBench の `external/ccbench/cmake/ThirdParty.cmake:66-77` が
  `WORKING_DIRECTORY "${masstree_SOURCE_DIR}"` で `bootstrap/configure/make/ar` を走らせ、
  **build が source tree の中へ生成物を吐く**。cache の 71 件は過去 build の残骸である。
- 影響: `config.h` は `.gitignore` 除外で Git 非管理のため **HEAD pin はその bytes を証明しない**。
  この経路を通った build の third-party identity 主張は成立しない。consumer は床値だけでなく
  Silo ladder correctness/gap job も含む。
- 恒久対応は**未実施**。実装は裁定へ返されている。
- 関連: worklog (560) (`docs/worklog.md` の `## 2026-08-15 (560)`) は、T-971 で
  「共有 checkout 上では oracle が解決できる」と観測されたのは **cache が汚染されていたから**だと
  結論している。また同 wave は job-local (`TMPDIR=/scr/$PBS_JOBID` 配下) の使い捨て checkout に対し
  configure が rc=0 / 5.520 秒で通ることを実測している。

## これが T-330 の判断に効く理由

T-277 段 1 brief の S4 は「未実装なら**共有永続領域の cache が跨ジョブで再利用され、build 起源と
単独性が台帳から読めない**」を害として挙げていた。F319 はその害が**実データで成立していること**を
2026-08-15 に確定させた (ただし対象は third-party source cache であり、
`s8b_floor_campaign.py:1953` 付近の `cache_root` (`s8b-build-cache`) そのものではない)。

## 両レンズへの追加設問

1. F319 の実測は、S4 (`/scr` へ cache_root の fresh namespace) を**正当化するか**、それとも
   別の恒久対応 (検査へ ignored 列挙を足す / job-local checkout) の方が正しいか。
   **S4 を入れても F319 の consumer (床値・Silo ladder) が救われないなら、それは何故か。**
2. F319 の恒久対応は既に別タスクの裁定待ちである。T-330 でこれに触ると、
   **他タスクの裁定対象を独断で supersede しないか** (T-1094 / T-1095 / worklog (560) を確認せよ)。
3. `cache_root` (build-variants) 側にも同型の汚染 (跨ジョブ残骸が identity から見えない) があるか。
   `orchestrator/campaign/buildcache.py` の cache hit 判定が、cache directory の実 bytes ではなく
   key と receipt だけを見ているなら、それは F319 と同型か、それとも D136 決定 (3)(4) の
   receipt 束縛で塞がれているか。**file:line で判定せよ。**
