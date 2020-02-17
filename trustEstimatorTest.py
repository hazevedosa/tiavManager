# ------------------------
# Heb's first version.
# GDH - [20 2250 SET 2019]
# ------------------------


from trustEstimator import trustEstimator

T = 70
Pt = 1

TA = 1
FA = 0
Mi = 0
f = 0.5
p = 0.3
use = 0.7
initial = False


if __name__ == '__main__':

    Tr = []
    P = []
    fun_result = trustEstimator(T, Pt, TA, FA, Mi, f, p, use, initial)

    Tr.append(fun_result[0])
    P.append(fun_result[1])
    initial = False

    for i in range(12):
        fun_result = trustEstimator(Tr[-1], P[-1], TA, FA, Mi, f, p, use, initial)
        Tr.append(fun_result[0])
        P.append(fun_result[1])

    print(Tr)
    print(P)
