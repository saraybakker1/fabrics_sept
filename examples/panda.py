import gym
import urdfenvs.panda_reacher  #pylint: disable=unused-import

from MotionPlanningGoal.staticSubGoal import StaticSubGoal
from MotionPlanningEnv.sphereObstacle import SphereObstacle
from forwardkinematics.urdfFks.pandaFk import PandaFk

import numpy as np
from fabrics.planner.parameterized_planner import ParameterizedFabricPlanner


def initalize_environment(render=True):
    """
    Initializes the simulation environment.

    Adds obstacles and goal visualizaion to the environment based and
    steps the simulation once.
    """
    env = gym.make("panda-reacher-acc-v0", dt=0.05, render=render)
    initial_observation = env.reset()
    # Definition of the obstacle.
    static_obst_dict = {
        "dim": 3,
        "type": "sphere",
        "geometry": {"position": [0.3, -0.5, 0.3], "radius": 0.1},
    }
    obst1 = SphereObstacle(name="staticObst", contentDict=static_obst_dict)
    static_obst_dict = {
        "dim": 3,
        "type": "sphere",
        "geometry": {"position": [-0.7, 0.0, 0.5], "radius": 0.1},
    }
    obst2 = SphereObstacle(name="staticObst", contentDict=static_obst_dict)
    # Definition of the goal.
    goal_dict = {
        "m": 3,
        "w": 1.0,
        "prime": True,
        "indices": [0, 1, 2],
        "parent_link": 0,
        "child_link": 7,
        "desired_position": [0.0, -0.8, 0.2],
        "epsilon": 0.05,
        "type": "staticSubGoal",
    }
    goal = StaticSubGoal(name="goal", contentDict=goal_dict)
    obstacles = (obst1, obst2)
    env.add_goal(goal)
    env.add_obstacle(obst1)
    env.add_obstacle(obst2)
    return (env, obstacles, goal, initial_observation)


def set_planner(goal: StaticSubGoal, degrees_of_freedom: int = 7):
    """
    Initializes the fabric planner for the panda robot.

    This function defines the forward kinematics for collision avoidance,
    and goal reaching. These components are fed into the fabrics planner.

    In the top section of this function, an example for optional reconfiguration
    can be found. Commented by default.

    Params
    ----------
    goal: StaticSubGoal
        The goal to the motion planning problem.
    degrees_of_freedom: int
        Degrees of freedom of the robot (default = 7)
    """


    ## Optional reconfiguration of the planner
    # base_inertia = 0.03
    # attractor_potential = "20 * ca.norm_2(x)**4"
    # damper = {
    #     "alpha_b": 0.5,
    #     "alpha_eta": 0.5,
    #     "alpha_shift": 0.5,
    #     "beta_distant": 0.01,
    #     "beta_close": 6.5,
    #     "radius_shift": 0.1,
    # }
    # planner = ParameterizedFabricPlanner(
    #     degrees_of_freedom,
    #     base_inertia=base_inertia,
    #     attractor_potential=attractor_potential,
    #     damper=damper,
    # )
    planner = ParameterizedFabricPlanner(degrees_of_freedom)
    q = planner.variables.position_variable()
    panda_fk = PandaFk()
    forward_kinematics = []
    for i in range(1, degrees_of_freedom):
        forward_kinematics.append(panda_fk.fk(q, i, positionOnly=True))
    forward_kinematics_end_effector = panda_fk.fk(
        q, goal.childLink(), positionOnly=True
    )
    forward_kinematics.append(forward_kinematics_end_effector)
    # The planner hides all the logic behind the function set_components.
    planner.set_components(
        forward_kinematics,
        forward_kinematics_end_effector,
        number_obstacles=2,
        goal=True,
    )
    planner.concretize()
    return planner


def run_panda_example(n_steps=5000, render=True):
    (env, obstacles, goal, initial_observation) = initalize_environment(
        render=render
    )
    ob = initial_observation
    obst1 = obstacles[0]
    obst2 = obstacles[1]
    planner = set_planner(goal)

    # Start the simulation
    print("Starting simulation")
    goal_position = np.array(goal.position())
    obst1_position = np.array(obst1.position())
    obst2_position = np.array(obst2.position())
    for _ in range(n_steps):
        action = planner.compute_action(
            q=ob["x"],
            qdot=ob["xdot"],
            x_goal=goal_position,
            x_obst_0=obst2_position,
            x_obst_1=obst1_position,
            radius_obst_0=np.array([obst1.radius()]),
            radius_obst_1=np.array([obst2.radius()]),
            radius_body=np.array([0.02]),
        )
        ob, *_ = env.step(action)
    return {}


if __name__ == "__main__":
    res = run_panda_example(n_steps=5000)
