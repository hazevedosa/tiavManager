# ------------------------
# Heb's second version.
# GDH - [15 2250 OCT 2019]
# ------------------------


import numpy as np

def trustEstimator(T, Pt, TA, FA, Mi, f, p, use, initial):

    """
    Returns one interaction of the Kalman filter-based Trust Estimator

    Input Arguments:
    T  -- Current Trust score;
    Pt -- Current Trust score covariance;
    TA -- True Alarm binary indicator;
    FA -- False Alarm binary indicator;
    Mi -- Miss binary indicator;
    f  -- focus variable (1 - gaze);
    p  -- performance variable (points per sec, counting from the last car passing time);
    use  -- usage time percentage
    initial -- boolean variable indicating if the interaction is the initial or the subsequents. If initial == True, just add zeros to the other arguments.
    """

    # State-space mdel dimensions
    stateDim = 1
    obsDim = 3


    # State-space model matrix parameters
    A = np.array([1.001])

    B = np.array([0.39406, -0.47882, -0.56741])

    C = np.array([[0.0070117],
                  [0.004233],
                  [0.0092045]])

    N = 12

    # process noise / covariance computationnp.matmul(B, u)
    # Var_P_noise = 0.2478*0.2478
    Var_P_noise = 0.2478*0.2478
    # Mu_P_noise = 0
    Std_P_noise = np.sqrt(Var_P_noise)
    P_noise = Std_P_noise * np.random.normal(0, 1, (stateDim, N))

    Q = np.cov(P_noise)
    Q = np.array([Q])

    # observation (measurement) noise / covariance computation
    # Var_O_noise = np.array([[0.18412 * 0.18412],
    #                         [0.07010 * 0.07010],
    #                         [0.05748 * 0.05748]])
    Var_O_noise = np.array([[0.00018412 * 0.00018412],
                            [0.00007010 * 0.00007010],
                            [0.05748 * 0.05748]])
    # Mu_O_noise = 0
    Std_O_noise = np.sqrt(Var_O_noise)
    O_noise = Std_O_noise * np.random.normal(0, 1, (obsDim, N))

    R = np.cov(O_noise)

    # state array and covariance
    T = np.array([T])
    Pt = np.array([Pt])

    # inputs array
    u = np.array([[TA],
                  [FA],
                  [Mi]])

    # measurements array
    y = np.array([[f],
                  [p],
                  [use]])


    if initial == True: # first predicition, exclusively from the measurements
        Th_zero = np.array([[(f/C[0] + p/C[1] + use/C[2]) / 3.0]])
        Pt_zero = np.array([[1]])

        if Th_zero[0][0][0] > 100:
            Th_zero[0][0][0] = 100
        elif Th_zero[0][0][0] < 0:
            Th_zero[0][0][0] = 0

        return Th_zero, Pt_zero

    else: # following predictions, with the measurment - process sequence

        Pt = np.array([Pt])

        # measurement incorporation
        K = np.matmul(C, Pt)
        K = np.matmul(K, C.T) + R

        K = Pt @ (C.T) @ np.linalg.inv(K)

        T = np.array([T])
        # predicted measurement
        yh_ = C @ T

        # innovation
        innovation = y - yh_

        # estimates computation
        Th_ = T + K @ innovation
        Pt_ = Pt - K @ C @ Pt


        # model estimate
        Th = A @ Th_ + B @ u

        Pt = A @ Pt_
        Pt = np.array([Pt]) @ A.T + Q

        if Th[0][0][0] > 100:
            Th[0][0][0] = 100
        elif Th[0][0][0] < 0:
            Th[0][0][0] = 0


        return Th[0], Pt[0]
