cd "C:/Users/Villa/Downloads/CodigoFuenteB/CodigoFuenteB/resultados"
Q="C:/Users/Villa/qa-browsers"
for spec in "pw1641:N:chromium,firefox,webkit,msedge" "pw1630:N-1:chromium,firefox,webkit"; do IFS=: read n l k <<< "$spec"; PLAYWRIGHT_BROWSERS_PATH="C:\Users\Villa\qa-browsers\br_$n" $Q/$n/Scripts/python cp18_nav.py $l $k; done
