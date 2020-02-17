from transforms3d import euler


angles = euler.quat2euler([0.6645, 0.0, 0.0, 0.7472])

print(angles)
