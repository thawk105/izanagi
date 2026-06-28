set terminal pngcairo size 900,540 noenhanced font "sans,11"
set output "backoff-sweep-read-heavy.png"
set title "backoff sweep — read-heavy (skew0.9, static vs none=8,450,806 / adaptive=1,919,103)"
set xlabel "static backoff magnitude (us)"
set ylabel "throughput (tps)"
set grid
set key outside right top
set y2label "abort rate (%)"
set y2tics
set ytics nomirror
set yrange [0:*]
set y2range [0:*]
set label "none=8,450,806" at graph 0.02,0.95
plot "backoff-sweep-read-heavy.dat" using 1:2 with linespoints axes x1y1 title "throughput (static)", \
     "backoff-sweep-read-heavy.dat" using 1:3 with linespoints axes x1y2 title "abort rate (static)"
