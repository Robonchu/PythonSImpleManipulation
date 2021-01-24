import numpy as np
import matplotlib.pyplot as plt
import matplotlib
from mpl_toolkits.mplot3d import Axes3D
from matplotlib import animation

# Link Angle Vector
a1 = [0, 0, 1]
a2 = [0, 1, 0]
a3 = [0, 1, 0]
a4 = [0, 1, 0]
a5 = [0, 0, 1]
a6 = [1, 0, 0]
a7 = [0, 0, 0]
## Gripper
a8 = [0, 0, 0]
a9 = [0, 0, 0]
a10 = [0, 0, 0]
a11 = [0, 0, 0]

# vector_list = [a1, a2, a3, a4, a5, a6, a7]
vector_list = [a1, a2, a3, a4, a5, a6, a7, a8, a9, a10, a11]

# Link Length
b1 = [0., 0., 0.06114]
b2 = [0., 0., 0.07042]
b3 = [0., 0., 0.1104]
b4 = [0., 0., 0.0960]
b5 = [0., -0.06639, 0.]
b6 = [0., 0., 0.07318]
b7 = [0.0436, 0., 0.]
## Gripper
b8 = [0, -0.02, 0.]
b9 = [0., 0.04, 0.]
b10 = [0.02, 0., 0.]
b11 = [0.0, -0.04, 0.]

# length_list = np.array([b1, b2, b3, b4, b5, b6, b7])
length_list = np.array([b1, b2, b3, b4, b5, b6, b7, b8, b9, b10, b11])


def skew_mat(vector):
    mat = np.zeros((3, 3))
    mat[0, 1] = -vector[2]
    mat[0, 2] = vector[1]
    mat[1, 0] = vector[2]
    mat[1, 2] = -vector[0]
    mat[2, 0] = -vector[1]
    mat[2, 1] = vector[0]
    return mat


def rodrigues(vector, angle):
    mat = np.eye(3) + skew_mat(vector) * np.sin(angle) + skew_mat(
        vector) @ skew_mat(vector) * (1.0 - np.cos(angle))
    return mat


def CalcFirstYawAngleByCircle(target_x, target_y, radius=0.06639):
    x_on_circle1 = radius * (target_x * radius + target_y *
                             np.sqrt(target_x**2 + target_y**2 - radius**2)
                             ) / (target_x**2 + target_y**2)
    x_on_circle2 = radius * (target_x * radius - target_y *
                             np.sqrt(target_x**2 + target_y**2 - radius**2)
                             ) / (target_x**2 + target_y**2)
    y_on_circle1 = radius * (target_y * radius - target_x *
                             np.sqrt(target_x**2 + target_y**2 - radius**2)
                             ) / (target_x**2 + target_y**2)
    y_on_circle2 = radius * (target_y * radius + target_x *
                             np.sqrt(target_x**2 + target_y**2 - radius**2)
                             ) / (target_x**2 + target_y**2)
    yaw1 = np.arctan2(-x_on_circle1, y_on_circle1)
    yaw2 = np.arctan2(-x_on_circle2, y_on_circle2)
    return yaw1, yaw2


def CalcFK(angle_list, vector_list, length_list, dof=6):
    calc_num = dof + 1
    pos = [0, 0, 0]
    R = np.eye(3)
    pos_list = [pos]
    R_list = [R]
    # Calculate Forward Kinematics
    for i in range(calc_num):
        pos = pos + R @ length_list[i].T
        R = R @ rodrigues(vector_list[i], angle_list[i])
        pos_list.append(pos)
        R_list.append(R)
    return pos, R, pos_list, R_list


def CalcJacobi(vector_list, pos_list, rot_list, dof=6):
    # memo: len(pos_list)= 6 or 7, vector_list = 6, rot_list = 6
    J = np.zeros((dof, dof))
    for i in range(dof):
        delta_angle = rot_list[i] @ vector_list[i]
        delta_pos = skew_mat(delta_angle) @ (pos_list[-1] - pos_list[i])
        J[3:, i] = delta_angle
        J[:3, i] = delta_pos
    return J


def CalcErr(target_pos, target_rot, current_pos, current_rot):
    R = target_rot - current_rot
    pos_err = np.square(target_pos - current_pos)
    theta = np.arccos((R[0, 0] + R[1, 1] + R[2, 2] - 1) / 2.0)
    ln_rot = theta / 2 * np.sin(theta) * np.array(
        [[R[2, 1] - R[1, 2]], [R[0, 2] - R[2, 0]], [R[1, 0] - R[0, 1]]])
    rot_err = np.square(ln_rot)
    return pos_err, rot_err


def CalcIK(angle_list,
           vector_list,
           length_list,
           target_pos,
           target_rot,
           threshold,
           max_itr=1000):
    alpha = 0.1

    for i in range(max_itr):
        # import pdb
        # pdb.set_trace()
        current_pos, current_rot, pos_list, rot_list = CalcFK(
            angle_list, vector_list, length_list)
        J = CalcJacobi(vector_list, pos_list[1:], rot_list[1:])
        pos_err, rot_err = CalcErr(target_pos, target_rot, current_pos,
                                   current_rot)
        err = np.concatenate([pos_err, rot_err[:, 0]])
        # import pdb
        # pdb.set_trace()
        if np.linalg.norm(err) < threshold:
            break
        delta_angle = alpha * (np.linalg.inv(J) @ err)
        # print(delta_angle)
        angle_list = np.array(angle_list) + np.concatenate([delta_angle, [0]])
    return angle_list


def move_points(angle_list, vector_list, length_list, target_poses,
                target_rots, threshold):
    angle_lists = []
    for target_pos, target_rot in zip(target_poses, target_rots):
        angle_list = CalcIK(angle_list[:7], vector_list, length_list,
                            target_pos, target_rot, threshold).copy()
        angle_lists.append(angle_list)
    return angle_lists


def make_target_points():
    pass


def rot_x(phi):
    r = np.array([[1., 0., 0], [0., np.cos(phi), -np.sin(phi)],
                  [0., np.sin(phi), np.cos(phi)]])
    return r


def rot_y(theta):
    r = np.array([[np.cos(theta), 0., np.sin(theta)], [0., 1., 0.],
                  [-np.sin(theta), 0., np.cos(theta)]])
    return r


def rot_z(psi):
    r = np.array([[np.cos(psi), -np.sin(psi), 0.],
                  [np.sin(psi), np.cos(psi), 0.], [0., 0., 1.]])
    return r


def CalcAnalyticalIK(target_pos,
                     target_yaw,
                     length_list,
                     mode='floor_grasping'):

    if mode == 'floor_grasping':
        yaw1, yaw2 = CalcFirstYawAngleByCircle(target_pos[0], target_pos[1])
        yaw1 += np.pi

        b1, b2, b3, b4, b5, b6, b7 = length_list[:7]
        # memo: This top_arm part coordinate is for floor graspoing.
        # This is a kind of gripper orientation constraint toward ground.
        top_arm = np.array([b6[2], b5[1], -b7[0]])

        # memo: Target position for Joint 4 from Joint 2
        # pre_target_pos = target_pos - (rot_z(yaw2) @ top_arm) - np.array(
        #     [0., 0, b1[2] + b2[2]])
        # rad1 = yaw2
        # rad5 = 0.
        # rad6 = -(target_yaw - yaw2)
        # # rad6 = (target_yaw - yaw2)
        pre_target_pos = target_pos - (rot_z(yaw1) @ top_arm) - np.array(
            [0., 0, b1[2] + b2[2]])
        rad1 = yaw1
        rad5 = 0.
        rad6 = -(target_yaw - yaw1)

        # rad6 = (target_yaw - yaw2)
        bottom_arm_length = np.sqrt(np.sum(np.square(pre_target_pos)))
        rad3 = np.arccos((np.square(bottom_arm_length) -
                          (b3[2]**2 + b4[2]**2)) / (2 * b3[2] * b4[2]))
        alpha = np.arcsin(b4[2] * np.sin(np.pi - rad3) / bottom_arm_length)
        rad2 = -np.arctan2(
            pre_target_pos[2],
            np.sqrt(pre_target_pos[0]**2 +
                    pre_target_pos[1]**2)) - alpha + np.pi / 2.
        import pdb

        rad4 = np.pi / 2. - rad3 - rad2
        pdb.set_trace()
        angle_list = np.array([rad1, rad2, rad3, rad4, rad5, rad6])
        return angle_list
    else:
        print('please set correct mode for IK')


def CalcJointAngles(target_poses, target_yaws, length_list, dof=6):
    point_num = len(target_poses)
    angles = np.zeros((point_num, dof))
    for i, (target_pos, target_yaw) in enumerate(zip(target_poses,
                                                     target_yaws)):
        angles[i] = CalcAnalyticalIK(target_pos, target_yaw, length_list)
    return angles


def AngleInterpolation(angles, num=100):
    # TODO(robonchu): modify it to array for more speedup
    interpolated_angles = []
    for i in range(len(angles) - 1):
        angle_gap = angles[i + 1] - angles[i]
        for j in range(num):
            interpolated_angles.append(angles[i] + j * angle_gap / num * 1.0)
    return interpolated_angles


def calc_joint1_angle(x, y, phi, psi, length_list):
    pos6_x = x - length_list[6][0] * np.cos(phi) * np.cos(psi)
    pos6_y = y - length_list[6][0] * np.sin(psi) * np.cos(phi)
    yaw1, yaw2 = CalcFirstYawAngleByCircle(pos6_x, pos6_y)
    yaw = yaw1 + np.pi
    return yaw
    # gamma = length_list[4][1]**2

    # import pdb
    # pdb.set_trace()
    # A = 1 + beta**2 / alpha**2
    # B = -2 * (gamma * beta / alpha)**2
    # C = (gamma / alpha)**2 - length_list[4][1]**2
    # y0 = (-B + np.sqrt(B**2 - 4 * A * C)) / (2 * A)
    # y1 = (-B - np.sqrt(B**2 - 4 * A * C)) / (2 * A)
    # tan0 = gamma / (alpha * y0) - beta / alpha
    # tan1 = gamma / (alpha * y1) - beta / alpha
    # import pdb
    # pdb.set_trace()


def calc_joint56_angle(angle1, theta, phi, psi):
    angle6 = np.arctan(np.tan(angle1 - psi) * np.sin(phi)) + theta
    angle5 = np.arctan(-np.sin(angle6 - theta) / np.tan(phi))
    return angle5, angle6
    import pdb
    pdb.set_trace()


def calc_pos4(vector_list, length_list, angle5, angle6, pos, theta, phi, psi):
    b1, b2, b3, b4, b5, b6, b7 = length_list[:7]
    Rw = rot_z(psi) @ rot_y(phi) @ rot_x(theta)
    R5inv = np.linalg.inv(rodrigues(vector_list[4], angle5))
    R6inv = np.linalg.inv(rodrigues(vector_list[5], angle6))
    z_offset = [0., 0., b1[2] + b2[2]]
    pos4 = pos - Rw @ b7.T - Rw @ R6inv @ b6.T - Rw @ R6inv @ R5inv @ b5.T - z_offset
    return pos4
    import pdb
    pdb.set_trace()


def calc_joint23_angle(pre_target_pos):
    bottom_arm_length = np.sqrt(np.sum(np.square(pre_target_pos)))
    angle3 = np.arccos((np.square(bottom_arm_length) - (b3[2]**2 + b4[2]**2)) /
                       (2 * b3[2] * b4[2]))
    alpha = np.arcsin(b4[2] * np.sin(np.pi - angle3) / bottom_arm_length)
    angle2 = -np.arctan2(pre_target_pos[2],
                         np.sqrt(pre_target_pos[0]**2 +
                                 pre_target_pos[1]**2)) - alpha + np.pi / 2.
    return angle2, angle3


def calc_joint4_angle(vector_list, angle1, angle2, angle3, angle5, angle6,
                      theta, phi, psi):
    Rw = rot_z(psi) @ rot_y(phi) @ rot_x(theta)
    R1inv = np.linalg.inv(rodrigues(vector_list[0], angle1))
    R2inv = np.linalg.inv(rodrigues(vector_list[1], angle2))
    R3inv = np.linalg.inv(rodrigues(vector_list[2], angle3))
    R5inv = np.linalg.inv(rodrigues(vector_list[4], angle5))
    R6inv = np.linalg.inv(rodrigues(vector_list[5], angle6))
    R4 = R3inv @ R2inv @ R1inv @ Rw @ R6inv @ R5inv
    angle4 = np.arctan2(R4[0, 2], R4[0, 0])
    return angle4
    import pdb
    pdb.set_trace()


# def CreatePathPoints(pos_waypoints, yaw_waypoints):
#     reso = 0.005
#     target_poses = []
#     for i in range(len(pos_waypoints)):
#         path = pos_waypoints[i + 1] - pos_waypoints[i]

#     pass

if __name__ == "__main__":
    # target_pos1 = np.array([0.21, -0.06639, 0.02])
    target_pos1 = np.array([0.21, 0, 0.02])
    target_rot1 = np.array([0., np.pi / 2.0, 0.])  # Rzyx->psi,phi,theta
    angle1 = calc_joint1_angle(
        target_pos1[0],
        target_pos1[1],
        target_rot1[1],
        target_rot1[2],
        length_list,
    )
    angle5, angle6 = calc_joint56_angle(angle1, target_rot1[0], target_rot1[1],
                                        target_rot1[2])
    pos4 = calc_pos4(vector_list, length_list, angle5, angle6, target_pos1,
                     target_rot1[0], target_rot1[1], target_rot1[2])
    angle2, angle3 = calc_joint23_angle(pos4)
    angle4 = calc_joint4_angle(vector_list, angle1, angle2, angle3, angle5,
                               angle6, target_rot1[0], target_rot1[1],
                               target_rot1[2])
    ang_list = [angle1, angle2, angle3, angle4, angle5, angle6]
    import pdb
    pdb.set_trace()

    # target_pos1 = np.array([0.18, 0, 0.02])
    # target_pos2 = np.array([0.18, 0.06, 0.02])
    # target_pos = np.array([0.24, 0, 0.02])

    # target_pos1 = np.array([0.24, -0.05, 0.02])
    # target_pos2 = np.array([0.24, 0.05, 0.02])
    # target_pos3 = np.array([0.19, 0.05, 0.02])
    # target_pos4 = np.array([0.19, -0.05, 0.02])
    # target_pos5 = np.array([0.24, -0.05, 0.02])
    # target_poses = [
    #     target_pos1, target_pos2, target_pos3, target_pos4, target_pos5
    # ]
    # target_yaw = 0.
    # target_yaws = [target_yaw, target_yaw, target_yaw, target_yaw, target_yaw]

    # target_pos1 = np.array([0.24, -0.05, 0.02])
    # target_poses = np.array([target_pos1, target_pos2])
    target_poses = np.array([target_pos1])
    target_yaw = 0.
    target_yaws = np.array([target_yaw] * len(target_poses))

    angles = CalcJointAngles(target_poses, target_yaws, length_list)
    interpolated_angles = AngleInterpolation(angles, 10)
    import pdb
    pdb.set_trace()
    angle_list = angles[-1]
    '''
    # please use yaw2 for myCobot
    # yaw1, yaw2 = CalcFirstYawAngleByCircle(0.15, 0)
    # yaw1, yaw2 = CalcFirstYawAngleByCircle(0.15, 0.06639)
    yaw1, yaw2 = CalcFirstYawAngleByCircle(target_pos[0], target_pos[1])

    # floor grasping mode
    # TODO(taku): please check the nega/posi for cos and sin
    top_arm = np.array([b6[2], b5[1], -b7[0]])
    pre_target_pos = target_pos - (rot_z(yaw2) @ top_arm)
    pre_target_pos = pre_target_pos - np.array([0., 0, b1[2] + b2[2]])
    ang6 = -(target_yaw - yaw2)
    ang5 = 0.
    ang1 = yaw2
    bottom_arm_length = np.sqrt(np.sum(np.square(pre_target_pos)))
    ang3 = np.arccos((np.square(bottom_arm_length) - (b3[2]**2 + b4[2]**2)) /
                     (2 * b3[2] * b4[2]))
    alpha = np.arcsin(b4[2] * np.sin(np.pi - ang3) / bottom_arm_length)
    ang2 = -np.arctan2(pre_target_pos[2],
                       np.sqrt(pre_target_pos[0]**2 +
                               pre_target_pos[1]**2)) - alpha + np.pi / 2.
    ang4 = np.pi / 2. - ang3 - ang2
    '''

    ARM_NUM = 7
    GRIPPER_NUM = 4
    TOTAL_NUM = ARM_NUM + GRIPPER_NUM

    # import pdb
    # pdb.set_trace()
    # Figureを追加
    fig = plt.figure(figsize=(8, 8))
    # 3DAxesを追加
    ax = fig.add_subplot(111, projection='3d')
    # Axesのタイトルを設定
    ax.set_title("myCobotSim", size=20)

    # 軸ラベルを設定
    ax.set_xlabel("x", size=10, color="black")
    ax.set_ylabel("y", size=10, color="black")
    ax.set_zlabel("z", size=10, color="black")

    ax.set_xlim3d(-0.1, 0.3)
    ax.set_ylim3d(-0.2, 0.2)
    ax.set_zlim3d(0, 0.4)
    # ax.set_zlim3d(-0.2, 0.4)

    ims = []
    for angle_list in interpolated_angles:
        angle_list = np.append(angle_list, [0, 0, 0, 0, 0])

        # import pdb
        # pdb.set_trace()

        pos = [0, 0, 0]
        R = np.eye(3)
        pos_list = [pos]
        R_list = [R]
        pos_x = [pos[0]]
        pos_y = [pos[1]]
        pos_z = [pos[2]]
        # Calculate Forward Kinematics
        for i in range(TOTAL_NUM):
            pos = pos + R @ length_list[i].T
            R = R @ rodrigues(vector_list[i], angle_list[i])
            pos_list.append(pos)
            R_list.append(R)
            pos_x.append(pos[0])
            pos_y.append(pos[1])
            pos_z.append(pos[2])

        # axs = ax.scatter(pos_x[:ARM_NUM],
        #                  pos_y[:ARM_NUM],
        #                  pos_z[:ARM_NUM],
        #                  color='red')
        # axs += ax.scatter(pos_x[ARM_NUM:],
        #                   pos_y[ARM_NUM:],
        #                   pos_z[ARM_NUM:],
        #                   color='green')
        for i in range(ARM_NUM):
            if i == 0:
                axs = ax.plot([pos_x[i], pos_x[i + 1]],
                              [pos_y[i], pos_y[i + 1]],
                              [pos_z[i], pos_z[i + 1]],
                              color='blue',
                              linewidth=10)
            else:
                axs += ax.plot([pos_x[i], pos_x[i + 1]],
                               [pos_y[i], pos_y[i + 1]],
                               [pos_z[i], pos_z[i + 1]],
                               color='blue')
        for i in range(ARM_NUM, TOTAL_NUM - 1):
            axs += ax.plot([pos_x[i], pos_x[i + 1]], [pos_y[i], pos_y[i + 1]],
                           [pos_z[i], pos_z[i + 1]],
                           color='green')
        axs += ax.plot([pos_x[ARM_NUM + 1], pos_x[TOTAL_NUM]],
                       [pos_y[ARM_NUM + 1], pos_y[TOTAL_NUM]],
                       [pos_z[ARM_NUM + 1], pos_z[TOTAL_NUM]],
                       color='green')

        # axs += ax.scatter(pos_x[:ARM_NUM],
        axs += ax.plot(pos_x[:ARM_NUM],
                       pos_y[:ARM_NUM],
                       pos_z[:ARM_NUM],
                       color='blue',
                       marker='o')

        # axs += ax.plot(pos_x[ARM_NUM:],
        #                pos_y[ARM_NUM:],
        #                pos_z[ARM_NUM:],
        #                color='green',
        #                marker='o')

        # target_poses
        axs += ax.plot(target_poses[:, 0],
                       target_poses[:, 1],
                       target_poses[:, 2],
                       color='red',
                       linestyle='dashed',
                       linewidth=1)

        ims.append(axs)

    ani = animation.ArtistAnimation(fig, ims, interval=50, repeat=True)
    ani.save('myCobotIKdemo.gif', writer='imagemagick')

    # ax.plot([pos_x[ARM_NUM], pos_x[ARM_NUM+1]], [pos_y[ARM_NUM], pos_y[ARM_NUM+1]], [pos_z[ARM_NUM], pos_z[ARM_NUM+1]], color='green')
    # for i in range(GRIPPER_NUM):
    #     ax.plot([pos_x[i], pos_x[i + 1]], [pos_y[i], pos_y[i + 1]],
    #             [pos_z[i], pos_z[i + 1]],
    #             color='blue')
    plt.show()
    """
    ARM_NUM = 7
    GRIPPER_NUM = 4
    TOTAL_NUM = ARM_NUM + GRIPPER_NUM

    # angle_list = [ang1, ang2, ang3, ang4, ang5, ang6, 0, 0, 0, 0, 0]
    angle_list = np.append(angle_list, [0, 0, 0, 0, 0])

    import pdb
    pdb.set_trace()

    pos = [0, 0, 0]
    R = np.eye(3)
    pos_list = [pos]
    R_list = [R]
    pos_x = [pos[0]]
    pos_y = [pos[1]]
    pos_z = [pos[2]]
    # Calculate Forward Kinematics
    for i in range(TOTAL_NUM):
        pos = pos + R @ length_list[i].T
        R = R @ rodrigues(vector_list[i], angle_list[i])
        pos_list.append(pos)
        R_list.append(R)
        pos_x.append(pos[0])
        pos_y.append(pos[1])
        pos_z.append(pos[2])

    import pdb
    pdb.set_trace()
    # Figureを追加
    fig = plt.figure(figsize=(8, 8))
    # 3DAxesを追加
    ax = fig.add_subplot(111, projection='3d')
    # Axesのタイトルを設定
    ax.set_title("myCobotSim", size=20)

    # 軸ラベルを設定
    ax.set_xlabel("x", size=10, color="black")
    ax.set_ylabel("y", size=10, color="black")
    ax.set_zlabel("z", size=10, color="black")

    ax.set_xlim3d(-0.1, 0.3)
    ax.set_ylim3d(-0.2, 0.2)
    ax.set_zlim3d(0, 0.4)

    ax.scatter(pos_x[:ARM_NUM], pos_y[:ARM_NUM], pos_z[:ARM_NUM], color='red')
    ax.scatter(pos_x[ARM_NUM:],
               pos_y[ARM_NUM:],
               pos_z[ARM_NUM:],
               color='green')
    for i in range(ARM_NUM):
        if i == 0:
            ax.plot([pos_x[i], pos_x[i + 1]], [pos_y[i], pos_y[i + 1]],
                    [pos_z[i], pos_z[i + 1]],
                    color='blue',
                    linewidth=10)
        else:
            ax.plot([pos_x[i], pos_x[i + 1]], [pos_y[i], pos_y[i + 1]],
                    [pos_z[i], pos_z[i + 1]],
                    color='blue')
    for i in range(ARM_NUM, TOTAL_NUM - 1):
        ax.plot([pos_x[i], pos_x[i + 1]], [pos_y[i], pos_y[i + 1]],
                [pos_z[i], pos_z[i + 1]],
                color='green')
    ax.plot([pos_x[ARM_NUM + 1], pos_x[TOTAL_NUM]],
            [pos_y[ARM_NUM + 1], pos_y[TOTAL_NUM]],
            [pos_z[ARM_NUM + 1], pos_z[TOTAL_NUM]],
            color='green')

    # ax.plot([pos_x[ARM_NUM], pos_x[ARM_NUM+1]], [pos_y[ARM_NUM], pos_y[ARM_NUM+1]], [pos_z[ARM_NUM], pos_z[ARM_NUM+1]], color='green')
    # for i in range(GRIPPER_NUM):
    #     ax.plot([pos_x[i], pos_x[i + 1]], [pos_y[i], pos_y[i + 1]],
    #             [pos_z[i], pos_z[i + 1]],
    #             color='blue')
    plt.show()
    """
"""
if __name__ == "__main__":
    ARM_NUM = 7
    GRIPPER_NUM = 4
    TOTAL_NUM = ARM_NUM + GRIPPER_NUM
    pos = [0, 0, 0]
    R = np.eye(3)
    # rad1 = np.random.rand() * np.pi / 2.0
    # rad2 = np.random.rand() * np.pi / 2.0
    # rad3 = np.random.rand() * np.pi / 2.0
    # rad4 = np.random.rand() * np.pi / 2.0
    # rad5 = np.random.rand() * np.pi / 2.0
    # rad6 = np.random.rand() * np.pi / 2.0

    # rad1 = 0.
    # rad2 = np.pi / 5.
    # rad3 = np.pi / 5
    # rad4 = -np.pi / 5 * 2
    # rad5 = 0.
    # rad6 = 0.

    rad1 = 0.
    rad2 = np.pi / 4.
    rad3 = np.pi / 2.
    rad4 = -np.pi / 4.0
    rad5 = 0.
    rad6 = 0.
    # angle_list = [rad1, rad2, rad3, rad4, rad5, rad6, 0]
    angle_list = [rad1, rad2, rad3, rad4, rad5, rad6, 0, 0, 0, 0, 0]
    pos, R, pos_list, R_list = CalcFK(angle_list, vector_list, length_list)
    import pdb
    pdb.set_trace()

    target_poses = []
    target_rots = []
    x_dis = 0.015
    reso = 0.001
    x_num = int(x_dis / reso)
    target_pos = pos.copy()
    target_rot = R.copy()
    for i in range(x_num):
        target_pos = target_pos.copy() - np.array([reso, 0, 0])
        target_poses.append(target_pos)
        target_rots.append(target_rot)
    import pdb
    pdb.set_trace()

    z_dis = 0.06
    # reso = 0.02
    z_num = int(z_dis / reso)
    for i in range(z_num):
        # import pdb
        # pdb.set_trace()
        target_pos = target_pos.copy() - np.array([0, 0, reso])
        target_poses.append(target_pos)
        target_rots.append(target_rot)

    threshold = 0.00001
    angle_lists = move_points(angle_list, vector_list, length_list,
                              target_poses, target_rots, threshold)
    angle_list = angle_lists[-1]
    '''
    # target_rot = np.eye(3)
    # target_pos = np.array([0.21766459, 0.06639, 0.28280459])
    target_rot = np.array([[0., 0.00000000e+00, 1.00000000e+00],
                           [0.00000000e+00, 1.00000000e+00, 0.00000000e+00],
                           [-1.00000000e+00, 0.00000000e+00, 0.]])
    target_pos = np.array([0.207, 0.06639, 0.09814234])
    threshold = 0.0001
    angle_list = CalcIK(angle_list[:7], vector_list, length_list, target_pos,
                        target_rot, threshold)

    target_rot = np.array([[0., 0.00000000e+00, 1.00000000e+00],
                           [0.00000000e+00, 1.00000000e+00, 0.00000000e+00],
                           [-1.00000000e+00, 0.00000000e+00, 0.]])
    target_pos = np.array([0.19, 0.06639, 0.09814234])
    threshold = 0.0001
    angle_list = CalcIK(angle_list[:7], vector_list, length_list, target_pos,
                        target_rot, threshold)

    target_rot = np.array([[0., 0.00000000e+00, 1.00000000e+00],
                           [0.00000000e+00, 1.00000000e+00, 0.00000000e+00],
                           [-1.00000000e+00, 0.00000000e+00, 0.]])
    target_pos = np.array([0.19, 0.06639, 0.08])
    threshold = 0.0001
    angle_list = CalcIK(angle_list[:7], vector_list, length_list, target_pos,
                        target_rot, threshold)

    target_rot = np.array([[0., 0.00000000e+00, 1.00000000e+00],
                           [0.00000000e+00, 1.00000000e+00, 0.00000000e+00],
                           [-1.00000000e+00, 0.00000000e+00, 0.]])
    target_pos = np.array([0.19, 0.06639, 0.07])
    threshold = 0.0001
    angle_list = CalcIK(angle_list[:7], vector_list, length_list, target_pos,
                        target_rot, threshold)

    target_rot = np.array([[0., 0.00000000e+00, 1.00000000e+00],
                           [0.00000000e+00, 1.00000000e+00, 0.00000000e+00],
                           [-1.00000000e+00, 0.00000000e+00, 0.]])
    target_pos = np.array([0.19, 0.06639, 0.06])
    threshold = 0.0001
    angle_list = CalcIK(angle_list[:7], vector_list, length_list, target_pos,
                        target_rot, threshold)

    target_rot = np.array([[0., 0.00000000e+00, 1.00000000e+00],
                           [0.00000000e+00, 1.00000000e+00, 0.00000000e+00],
                           [-1.00000000e+00, 0.00000000e+00, 0.]])
    target_pos = np.array([0.19, 0.06639, 0.04])
    threshold = 0.0001
    angle_list = CalcIK(angle_list[:7], vector_list, length_list, target_pos,
                        target_rot, threshold)

    # target_rot = np.array([[0., 0.00000000e+00, 1.00000000e+00],
    #                        [0.00000000e+00, 1.00000000e+00, 0.00000000e+00],
    #                        [-1.00000000e+00, 0.00000000e+00, 0.]])
    # target_pos = np.array([0.203, 0.06639, 0.09814234])
    # threshold = 0.00001
    # angle_list = CalcIK(angle_list[:7], vector_list, length_list, target_pos,
    #                     target_rot, threshold)

    # target_rot = np.array([[0., 0.00000000e+00, 1.00000000e+00],
    #                        [0.00000000e+00, 1.00000000e+00, 0.00000000e+00],
    #                        [-1.00000000e+00, 0.00000000e+00, 0.]])
    # target_pos = np.array([0.201, 0.06639, 0.09814234])
    # threshold = 0.00001
    # angle_list = CalcIK(angle_list[:7], vector_list, length_list, target_pos,
    #                     target_rot, threshold)
    '''

    import pdb
    pdb.set_trace()
    # angle_list = [rad1, rad2, rad3, rad4, rad5, rad6, 0, 0, 0, 0, 0]
    angle_list = np.insert(angle_list, -1, [0, 0, 0, 0])
    pos = [0, 0, 0]
    R = np.eye(3)
    pos_list = [pos]
    R_list = [R]
    pos_x = [pos[0]]
    pos_y = [pos[1]]
    pos_z = [pos[2]]
    # Calculate Forward Kinematics
    for i in range(TOTAL_NUM):
        pos = pos + R @ length_list[i].T
        R = R @ rodrigues(vector_list[i], angle_list[i])
        pos_list.append(pos)
        R_list.append(R)
        pos_x.append(pos[0])
        pos_y.append(pos[1])
        pos_z.append(pos[2])

    # Figureを追加
    fig = plt.figure(figsize=(8, 8))
    # 3DAxesを追加
    ax = fig.add_subplot(111, projection='3d')
    # Axesのタイトルを設定
    ax.set_title("myCobotSim", size=20)

    # 軸ラベルを設定
    ax.set_xlabel("x", size=10, color="black")
    ax.set_ylabel("y", size=10, color="black")
    ax.set_zlabel("z", size=10, color="black")

    ax.set_xlim3d(-0.3, 0.3)
    ax.set_ylim3d(-0.3, 0.3)
    ax.set_zlim3d(0, 0.6)

    ax.scatter(pos_x[:ARM_NUM], pos_y[:ARM_NUM], pos_z[:ARM_NUM], color='red')
    ax.scatter(pos_x[ARM_NUM:],
               pos_y[ARM_NUM:],
               pos_z[ARM_NUM:],
               color='green')
    for i in range(ARM_NUM):
        if i == 0:
            ax.plot([pos_x[i], pos_x[i + 1]], [pos_y[i], pos_y[i + 1]],
                    [pos_z[i], pos_z[i + 1]],
                    color='blue',
                    linewidth=10)
        else:
            ax.plot([pos_x[i], pos_x[i + 1]], [pos_y[i], pos_y[i + 1]],
                    [pos_z[i], pos_z[i + 1]],
                    color='blue')
    for i in range(ARM_NUM, TOTAL_NUM - 1):
        ax.plot([pos_x[i], pos_x[i + 1]], [pos_y[i], pos_y[i + 1]],
                [pos_z[i], pos_z[i + 1]],
                color='green')
    ax.plot([pos_x[ARM_NUM + 1], pos_x[TOTAL_NUM]],
            [pos_y[ARM_NUM + 1], pos_y[TOTAL_NUM]],
            [pos_z[ARM_NUM + 1], pos_z[TOTAL_NUM]],
            color='green')

    # ax.plot([pos_x[ARM_NUM], pos_x[ARM_NUM+1]], [pos_y[ARM_NUM], pos_y[ARM_NUM+1]], [pos_z[ARM_NUM], pos_z[ARM_NUM+1]], color='green')
    # for i in range(GRIPPER_NUM):
    #     ax.plot([pos_x[i], pos_x[i + 1]], [pos_y[i], pos_y[i + 1]],
    #             [pos_z[i], pos_z[i + 1]],
    #             color='blue')
    plt.show()
"""