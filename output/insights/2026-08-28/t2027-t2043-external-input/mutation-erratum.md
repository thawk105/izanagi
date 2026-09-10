# 変異期待node集合 erratum

anchor `2e35a2596`、spec SHA `5f51152d...` の初回完走では baseline 6 passed、全6変異がrc=1、SURVIVED 0だったが、M1/M2/M8の期待node集合が不完全で `KILLED 3 / MISMATCH 3` になった。

- M1はschema pin除去という単一理由でschema分離nodeとbase A→B hit nodeが赤になった。
- M2はFetchContent inputのfilesystem誤分類という単一理由で分類nodeとroot canonicality nodeが赤になった。
- M8はreceipt発行時current-root forwarding除去という単一理由でissuer nodeとfloor統合nodeが赤になった。

診断文字列だけの追加赤ではなく、いずれも同じ受理条件を隣接consumerが独立に拒否した結果である。実測した完全集合をspecへ追記し、旧resultは削除せずrepo外job dirに保全する。再走はlocal main進行によるwrapper postcheck rc=125を避けるため、固定commitの独立cloneをsourceにする。
