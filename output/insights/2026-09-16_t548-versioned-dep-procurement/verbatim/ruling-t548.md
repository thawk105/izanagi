17. [T-1235] local 実行経路 = hold の停止対象に含めない (16 と対)。
18. [T-1212] 世代数の封印 = 択 (a) 現状維持。[T-1185] を追認して終端。
19. [T-548] gflags / glog = 択 (b) versioned な共通調達経路を新設。[T-585] と同 wave。
20. [T-580] admission receipt = 閉じる。[T-1207] と同じ閉包設計へ載せる。
21. [T-734] certified sink = source gate を課す。5 / 20 / 21 を 1 wave に束ねる。

- [T-548] **P2・裁定済み (2026-08-16 /rulings 全件 第 3 回、択 (b))**: gflags / glog は
  **versioned な共通調達経路を新設する**。他の 3 依存は FetchContent で versioned に取れており、
  2 本だけ機体固有の絶対 path に依存している非対称が原因である。択 (a) 共有 policy の locator を
  貼り替える案は貼り替え先が消えれば再発し、凍結証拠の再 binding という重い手続きも呼ぶ。
  択 (c) probe ごとの env seam は逃げ道が増えて再現性が下がる。[T-585] (機体固有 path 結合の
  除去) と同じ面なので同一 wave で閉じる。
