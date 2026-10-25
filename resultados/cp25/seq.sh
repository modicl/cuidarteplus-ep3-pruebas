cd "C:/Users/Villa/Downloads/CodigoFuenteB/CodigoFuenteB/resultados/cp25"
for r in 1 2 3; do python run.py A $r; done
for r in 1 2 3; do python run.py B $r; done
python run.py C
python run.py E
python run.py F
python run.py G
echo SECUENCIA_COMPLETA
